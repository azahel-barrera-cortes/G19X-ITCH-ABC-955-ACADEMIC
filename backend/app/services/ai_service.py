"""Servicio de Inteligencia Artificial: redacción de cláusulas y validación.

Responsabilidad única: transformar *datos estructurados del acta* en *texto legal*
y en *hallazgos de consistencia*. El maquetado del PDF no ocurre aquí (corresponde
a ``pdf_generator``), cumpliendo la separación exigida por el proyecto.

Proveedores soportados:

* ``azure_openai`` - API de Azure OpenAI (chat completions).
* ``gemini``       - Google Gemini (generateContent).
* ``plantillas``   - redacción determinista local (sin servicios externos).

El servicio degrada automáticamente a plantillas cuando no hay credenciales o
cuando el proveedor falla, y deja constancia de ello en ``advertencias``.
"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Any, Dict, Iterator, List, Mapping, Optional

from app.core import formato
from app.core.catalogos import (
    articulo_quorum,
    etiqueta_mayoria,
    etiqueta_tipo_asamblea,
    porcentaje_requerido_mayoria,
)
from app.core.config import Settings, settings as settings_global
from app.models.enums import (
    MateriaAcuerdo,
    ProveedorIA,
    SeveridadHallazgo,
    TipoAsamblea,
    TipoMayoria,
)
from app.schemas.acta import Acuerdo, ActaBase, Hallazgo, ValidacionActa
from app.services import plantillas_legales as plantillas
from app.services.llm_providers import (
    ErrorLLM,
    ResultadoLLM,
    trocear,
    catalogo_proveedores,
    crear_proveedor,
)

__all__ = [
    "AIService",
    "crear_servicio_ia",
    "extraer_json",
    "cifras_no_sustentadas",
    "catalogo_proveedores",
    "PROMPT_SISTEMA_REDACCION",
    "PROMPT_SISTEMA_VALIDACION",
    "PATRON_CIFRAS",
    "PATRON_ARTICULOS",
]

logger = logging.getLogger(__name__)

CATALOGO_MATERIAS = ", ".join(materia.value for materia in MateriaAcuerdo)

# --- Auditoría de fidelidad -------------------------------------------------
# El modelo puede alucinar cifras. Estas expresiones permiten detectar números que
# no aparecen en los datos capturados por el usuario y reportarlos como advertencia
# en lugar de dejarlos pasar como si fueran ciertos.
PATRON_CIFRAS = re.compile(r"\d[\d,.\s]*\d|\d")
# Referencias normativas del tipo "artículo 182" o "artículos 7 y 8 de la LGSM".
PATRON_ARTICULOS = re.compile(
    r"art[íi]culos?\s+[\dº°\s,.\-yynº°a-záéíóúñ]+", re.IGNORECASE
)

PROMPT_SISTEMA_REDACCION = f"""Eres un abogado corporativo mexicano, especialista en derecho societario
(Ley General de Sociedades Mercantiles) y en la redacción de actas de asamblea.

Reglas obligatorias:
1. Redacta en español jurídico formal, en tercera persona, sin viñetas ni markdown.
2. Divide el texto en párrafos numerados con ordinales: PRIMERO.-, SEGUNDO.-, TERCERO.- ...
3. Cita los artículos aplicables de la Ley General de Sociedades Mercantiles.
4. NO inventes hechos, montos, fechas, nombres ni cifras: utiliza únicamente los datos del contexto.
5. Conserva íntegro el contenido sustantivo del resumen del acuerdo proporcionado por el usuario.
6. No agregues comentarios, notas ni aclaraciones fuera del JSON solicitado.
7. Responde EXCLUSIVAMENTE con un objeto JSON válido con esta forma:
{{
  "titulo": "título breve de la cláusula",
  "materia": "una de: {CATALOGO_MATERIAS}",
  "clausula_legal": "texto completo de la cláusula, con \\n entre párrafos",
  "fundamento_legal": "artículos y ordenamiento en que se funda"
}}"""

PROMPT_SISTEMA_VALIDACION = """Eres un revisor legal corporativo mexicano. Analizas la consistencia formal
y legal de un acta de asamblea antes de su firma y protocolización.

Reglas obligatorias:
1. Revisa: quórum y capital representado, convocatoria previa, designación de presidente y secretario,
   escrutadores, correlación entre orden del día y acuerdos, mayorías aplicables, fundamentos legales
   invocados y datos faltantes.
2. Sé estricto pero no inventes hechos ni supongas documentos que no se te proporcionaron.
3. Responde EXCLUSIVAMENTE con un objeto JSON válido con esta forma:
{
  "puntaje": 0,
  "consistencia": "resumen ejecutivo en una o dos frases",
  "hallazgos": [
    {"severidad": "critico|advertencia|informativo", "campo": "campo o sección", "mensaje": "descripción", "sugerencia": "acción concreta"}
  ],
  "recomendaciones": ["acción recomendada antes de la firma"]
}
4. "puntaje" es un número de 0 a 100 que refleja la consistencia global del acta.
5. Si no hay hallazgos, devuelve la lista vacía."""


def extraer_json(texto: Optional[str]) -> Optional[Dict[str, Any]]:
    """Extrae el primer objeto JSON válido contenido en ``texto``.

    Tolerante a bloques de código markdown ```json ... ``` y a texto adicional
    alrededor del objeto. Devuelve ``None`` si no se puede interpretar.
    """
    if not texto:
        return None

    limpio = texto.strip()
    if limpio.startswith("```"):
        # Elimina las vallas de markdown manteniendo el contenido interno.
        limpio = limpio.strip("`")
        if limpio.lower().startswith("json"):
            limpio = limpio[4:]
        limpio = limpio.strip()

    inicio = limpio.find("{")
    fin = limpio.rfind("}")
    if inicio == -1 or fin <= inicio:
        return None

    candidato = limpio[inicio : fin + 1]
    for intento in (candidato, candidato.replace("\n", " ")):
        try:
            datos = json.loads(intento)
            return datos if isinstance(datos, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def _severidad(valor: Any) -> SeveridadHallazgo:
    """Convierte texto libre en una severidad válida del dominio."""
    try:
        return SeveridadHallazgo(str(valor).strip().lower())
    except ValueError:
        return SeveridadHallazgo.INFORMATIVO


def _puntaje(valor: Any, predeterminado: float = 80.0) -> float:
    """Normaliza el puntaje devuelto por el modelo al rango 0-100."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return predeterminado
    return max(0.0, min(100.0, round(numero, 2)))


def _normalizar_cifra(texto: str) -> str:
    """Reduce una cifra a una forma comparable (sin separadores de miles)."""
    return re.sub(r"[,\s]", "", texto).rstrip(".,")


def cifras_no_sustentadas(texto: str, contexto: Mapping[str, str]) -> List[str]:
    """Cifras del texto generado que no aparecen en los datos del acta.

    Se ignoran los números que forman parte de una referencia a un artículo de la
    LGSM (p. ej. «artículo 182»), ya que provienen del conocimiento jurídico del
    modelo y no de los datos capturados.
    """
    if not texto:
        return []

    permitidas = {
        _normalizar_cifra(cifra)
        for valor in contexto.values()
        for cifra in PATRON_CIFRAS.findall(str(valor))
    }
    # Todo número presente en el contexto del acuerdo es legítimo.
    permitidas |= {_normalizar_cifra(str(valor)) for valor in contexto.values()}

    # Se eliminan las referencias normativas antes de comparar.
    limpio = PATRON_ARTICULOS.sub(" ", texto)

    sospechosas: List[str] = []
    for coincidencia in PATRON_CIFRAS.findall(limpio):
        cifra = _normalizar_cifra(coincidencia)
        if not cifra or cifra in permitidas:
            continue
        if cifra not in sospechosas:
            sospechosas.append(cifra)
    return sospechosas


# Tipos de asamblea que se rigen por el artículo 182 de la LGSM (extraordinarias).
TIPOS_EXTRAORDINARIOS = frozenset(
    {
        TipoAsamblea.EXTRAORDINARIA.value,
        TipoAsamblea.MIXTA.value,
        TipoAsamblea.AUMENTO_CAPITAL.value,
        TipoAsamblea.REDUCCION_CAPITAL.value,
        TipoAsamblea.FUSION.value,
        TipoAsamblea.ESCISION.value,
        TipoAsamblea.DISOLUCION_LIQUIDACION.value,
    }
)

class AIService:
    """Servicio de redacción y validación con degradación controlada.

    Uso típico::

        servicio = AIService()
        acuerdos = servicio.redactar_acuerdos(acta, instrucciones="...")
        validacion = servicio.validar_acta(acta)
    """

    def __init__(self, config: Optional[Settings] = None) -> None:
        self.config = config or settings_global
        self.proveedor = ProveedorIA(self.config.proveedor_ia_configurado)
        self.advertencias: List[str] = []
        # Trazabilidad de cada llamada al modelo (se expone en la respuesta y el PDF).
        self.llamadas: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ estado
    @property
    def ia_habilitada(self) -> bool:
        """``True`` cuando hay un proveedor de LLM realmente configurado."""
        return self.proveedor is not ProveedorIA.PLANTILLAS

    # -------------------------------------------------------------- redacción
    def redactar_acuerdos(
        self,
        acta: ActaBase,
        instrucciones: Optional[str] = None,
    ) -> List[Acuerdo]:
        """Devuelve los acuerdos con su cláusula legal redactada.

        Se conserva el resto de los datos del acuerdo (título, resumen, votación) y
        se completan ``materia``, ``clausula_legal``, ``fundamento_legal`` y la
        bandera ``generado_por_ia``.
        """
        enriquecidos: List[Acuerdo] = []

        for acuerdo in acta.acuerdos:
            materia = acuerdo.materia or plantillas.detectar_materia(
                f"{acuerdo.titulo} {acuerdo.resumen}", acta.tipo_asamblea
            )
            contexto = self.construir_contexto(acta, acuerdo)

            redaccion: Optional[Dict[str, Any]] = None
            if self.ia_habilitada:
                redaccion = self._redactar_con_llm(acuerdo, contexto, instrucciones)
            if redaccion is None:
                # Ruta determinista: plantillas legales locales.
                redaccion = plantillas.redactar_con_plantilla(materia, contexto)
                redaccion["generado_por_ia"] = False

            enriquecidos.append(
                Acuerdo(
                    **{
                        **acuerdo.model_dump(),
                        "materia": redaccion.get("materia") or materia,
                        "clausula_legal": redaccion.get("clausula_legal"),
                        "fundamento_legal": redaccion.get("fundamento_legal"),
                        "generado_por_ia": bool(redaccion.get("generado_por_ia", False)),
                    }
                )
            )

        return enriquecidos

    def _redactar_con_llm(
        self,
        acuerdo: Acuerdo,
        contexto: Mapping[str, str],
        instrucciones: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Pide al proveedor la cláusula de un acuerdo y normaliza su respuesta.

        Devuelve ``None`` si el proveedor no está disponible o si su respuesta no es
        utilizable, para que quien llama degrade a las plantillas legales locales.
        """
        if not self.ia_habilitada:
            return None

        usuario = self._prompt_usuario_redaccion(acuerdo, contexto, instrucciones)
        resultado = self._consultar_llm(PROMPT_SISTEMA_REDACCION, usuario)
        if resultado is None:
            return None

        materia = acuerdo.materia or plantillas.detectar_materia(
            f"{acuerdo.titulo} {acuerdo.resumen}", ""
        )
        datos = self._interpretar_redaccion(resultado, acuerdo, materia)
        if datos is None:
            self.advertencias.append(
                f"El proveedor de IA no produjo una cláusula utilizable para el acuerdo "
                f"{acuerdo.numero}; se usó la plantilla legal local."
            )
            return None

        # Auditoría de fidelidad: el modelo no debe inventar cifras.
        if self.config.ai_verificar_fidelidad:
            contexto_total = {**contexto, "resumen": acuerdo.resumen}
            inventadas = cifras_no_sustentadas(
                str(datos.get("clausula_legal") or ""), contexto_total
            )
            if inventadas:
                self.advertencias.append(
                    f"El acuerdo {acuerdo.numero} menciona cifras que no aparecen en los datos "
                    f"capturados ({', '.join(inventadas)}). Verifícalas antes de firmar."
                )

        return datos

    # ---------------------------------------------------------------- contexto
    def construir_contexto(
        self, acta: ActaBase, acuerdo: Optional[Acuerdo] = None
    ) -> Dict[str, str]:
        """Valores que alimentan las plantillas legales y el *prompt* del LLM."""
        votacion = acuerdo.votacion if acuerdo else None
        mayoria = etiqueta_mayoria(votacion.tipo_mayoria) if votacion else ""
        acciones_computadas = formato.acciones(votacion.acciones_a_favor) if votacion else ""

        return {
            "sociedad": acta.sociedad,
            "rfc_sociedad": acta.rfc_sociedad or "",
            "tipo_sociedad": acta.tipo_sociedad or "",
            "tipo_asamblea": str(acta.tipo_asamblea),
            "tipo_asamblea_texto": etiqueta_tipo_asamblea(acta.tipo_asamblea),
            "fecha": formato.fecha_larga(acta.fecha),
            "fecha_larga": formato.fecha_con_dia(acta.fecha),
            "hora": formato.hora_larga(acta.hora),
            "lugar": acta.lugar,
            "presidente": acta.presidente,
            "secretario": acta.secretario,
            "capital": formato.moneda(acta.capital_social),
            "monto": formato.moneda(acta.capital_presente),
            "acciones": acciones_computadas,
            "acciones_presentes": formato.acciones(
                acta.capital_presente or acta.acciones_totales
            ),
            "quorum": formato.porcentaje(acta.quorum_porcentaje),
            "mayoria": mayoria,
            "titulo_acuerdo": acuerdo.titulo if acuerdo else "",
            "resumen": acuerdo.resumen if acuerdo else "",
            "numero_acuerdo": str(acuerdo.numero) if acuerdo else "",
        }

    # ------------------------------------------------------- prompts de usuario
    def _prompt_usuario_redaccion(
        self,
        acuerdo: Acuerdo,
        contexto: Mapping[str, str],
        instrucciones: Optional[str],
    ) -> str:
        """Construye el *prompt* de usuario con el contexto completo del acuerdo."""
        plantilla = plantillas.obtener_plantilla(
            acuerdo.materia or plantillas.detectar_materia(f"{acuerdo.titulo} {acuerdo.resumen}")
        )
        votacion = acuerdo.votacion
        if votacion:
            detalle_votacion = (
                f"{etiqueta_mayoria(votacion.tipo_mayoria)}; acciones a favor: "
                f"{formato.acciones(votacion.acciones_a_favor)}; en contra: "
                f"{formato.acciones(votacion.acciones_en_contra)}; abstenciones: "
                f"{formato.acciones(votacion.abstenciones)}"
            )
        else:
            detalle_votacion = "no se registró votación detallada"

        lineas = [
            "DATOS DE LA ASAMBLEA",
            f"- Sociedad: {contexto['sociedad']} (RFC: {contexto['rfc_sociedad'] or 'no proporcionado'})",
            f"- Tipo de asamblea: {contexto['tipo_asamblea_texto']}",
            f"- Fecha y hora: {contexto['fecha_larga']}, {contexto['hora']}",
            f"- Lugar: {contexto['lugar']}",
            f"- Capital social: {contexto['capital']}; acciones representadas: {contexto['acciones_presentes']}",
            f"- Quórum declarado: {contexto['quorum']}",
            f"- Presidente: {contexto['presidente']}; Secretario: {contexto['secretario']}",
            "",
            f"ACUERDO {acuerdo.numero}: {acuerdo.titulo}",
            f"- Materia detectada: {plantilla.materia.value}",
            f"- Resumen redactado por el usuario: {acuerdo.resumen}",
            f"- Votación: {detalle_votacion}",
            "",
            "REDACCIÓN DE REFERENCIA (puedes mejorarla, respetando el contenido sustantivo)",
            f"- Acción aprobada: {plantilla.accion}",
            f"- Fundamento sugerido: {', '.join(plantilla.articulos)} de la Ley General de Sociedades Mercantiles",
            "",
            "OTRAS MATERIAS DISPONIBLES (referencia de estilo y fundamentos)",
            *plantillas.plantillas_para_prompt(),
        ]
        if instrucciones:
            lineas += ["", f"INSTRUCCIONES ADICIONALES DEL USUARIO: {instrucciones}"]

        lineas += [
            "",
            "Redacta la cláusula legal de este acuerdo y devuelve únicamente el JSON solicitado.",
        ]
        return "\n".join(lineas)

    def _prompt_usuario_validacion(self, acta: ActaBase) -> str:
        """Construye el *prompt* de validación con un resumen estructurado del acta."""
        asistentes = "\n".join(
            f"  · {a.nombre} ({a.caracter}"
            f"{', ' + a.cargo if a.cargo else ''}) - {formato.acciones(a.acciones)} acciones, "
            f"{formato.porcentaje(a.porcentaje_capital)}"
            for a in acta.asistentes
        )
        orden = "\n".join(f"  {p.numero}. {p.titulo}" for p in acta.orden_del_dia)
        acuerdos = "\n".join(
            f"  {a.numero}. {a.titulo} | resumen: {a.resumen} | mayoría: "
            f"{etiqueta_mayoria(a.votacion.tipo_mayoria) if a.votacion else 'no registrada'} | "
            f"aprobado: {'sí' if (a.votacion.aprobado if a.votacion else True) else 'no'}"
            for a in acta.acuerdos
        )

        return "\n".join(
            [
                "DATOS DEL ACTA A REVISAR",
                f"- Sociedad: {acta.sociedad} (RFC: {acta.rfc_sociedad or 'no proporcionado'})",
                f"- Tipo de asamblea: {etiqueta_tipo_asamblea(acta.tipo_asamblea)}",
                f"- Fecha y hora: {formato.fecha_con_dia(acta.fecha)}, {formato.hora_larga(acta.hora)}",
                f"- Lugar: {acta.lugar}",
                f"- Convocatoria: {formato.fecha_larga(acta.convocatoria_fecha)} por "
                f"{acta.convocatoria_quien or 'no indicado'} mediante "
                f"{acta.convocatoria_medio or 'no indicado'}",
                f"- Capital social: {formato.moneda(acta.capital_social)}",
                f"- Capital representado: {formato.moneda(acta.capital_presente)}",
                f"- Quórum: {formato.porcentaje(acta.quorum_porcentaje)}",
                f"- Presidente: {acta.presidente}; Secretario: {acta.secretario}",
                "- Asistentes:",
                asistentes or "  (sin asistentes registrados)",
                "- Orden del día:",
                orden,
                "- Acuerdos:",
                acuerdos,
                f"- Observaciones: {acta.observaciones or 'ninguna'}",
                "",
                "Devuelve únicamente el JSON de validación solicitado.",
            ]
        )

    # -------------------------------------------------- integración con el LLM
    def _interpretar_redaccion(
        self,
        resultado: ResultadoLLM,
        acuerdo: Acuerdo,
        materia: MateriaAcuerdo,
    ) -> Optional[Dict[str, Any]]:
        """Convierte la respuesta del modelo en los campos del acuerdo.

        Tolera respuestas en JSON (preferido) y en texto plano, y completa con la
        plantilla local lo que el modelo no haya informado.
        """
        plantilla = plantillas.obtener_plantilla(acuerdo.materia or materia)
        fundamento_predeterminado = (
            ", ".join(plantilla.articulos) + " de la Ley General de Sociedades Mercantiles"
        )
        datos = extraer_json(resultado.texto)

        if not datos:
            # El modelo respondió en texto libre: se acepta como cláusula si tiene cuerpo.
            texto = (resultado.texto or "").strip()
            if len(texto) < 40:
                return None
            return {
                "materia": plantilla.materia.value,
                "titulo": plantilla.titulo,
                "clausula_legal": texto,
                "fundamento_legal": fundamento_predeterminado,
                "generado_por_ia": True,
                "meta_ia": resultado.a_dict(),
            }

        clausula = str(datos.get("clausula_legal") or "").strip()
        if len(clausula) < 40:
            return None

        return {
            "materia": str(datos.get("materia") or plantilla.materia.value),
            "titulo": str(datos.get("titulo") or plantilla.titulo),
            "clausula_legal": clausula,
            "fundamento_legal": str(datos.get("fundamento_legal") or fundamento_predeterminado),
            "generado_por_ia": True,
            "meta_ia": resultado.a_dict(),
        }

    # ------------------------------------------------ cadena de proveedores
    @property
    def cadena_proveedores(self) -> List[str]:
        """Orden de intento: proveedor principal y, si falla, el alterno."""
        cadena = [str(self.proveedor.value)]
        if self.config.ai_allow_fallback:
            alterno = self.config.proveedor_ia_alterno
            if alterno != "plantillas" and alterno not in cadena:
                cadena.append(alterno)
        return cadena

    def _consultar_llm(
        self,
        sistema: str,
        usuario: str,
        *,
        json_mode: bool = True,
        max_tokens: Optional[int] = None,
    ) -> Optional[ResultadoLLM]:
        """Consulta los proveedores en cascada y registra la trazabilidad.

        Devuelve ``None`` cuando ningún proveedor responde; en ese caso quien
        invoca debe degradar a las plantillas legales deterministas.
        """
        if not self.ia_habilitada:
            return None

        for nombre in self.cadena_proveedores:
            proveedor = crear_proveedor(nombre, self.config)
            if proveedor is None:
                continue
            try:
                resultado = proveedor.chat(
                    sistema, usuario, json_mode=json_mode, max_tokens=max_tokens
                )
            except ErrorLLM as error:
                detalle = (
                    f"El proveedor de IA «{nombre}» no estuvo disponible "
                    f"({error.intentos} intento(s)"
                    f"{', error permanente' if error.permanente else ''}). "
                    "Se intenta el siguiente nivel de la cadena."
                )
                logger.warning("%s Detalle: %s", detalle, error)
                self.advertencias.append(detalle)
                continue
            except Exception as exc:  # pragma: no cover - salvaguarda final
                logger.exception("Error inesperado al consultar el proveedor %s", nombre)
                self.advertencias.append(
                    f"Error inesperado con el proveedor «{nombre}» ({type(exc).__name__})."
                )
                continue

            self.llamadas.append(resultado.a_dict())
            if resultado.reintentos:
                self.advertencias.append(
                    f"El proveedor «{nombre}» requirió {resultado.reintentos} reintento(s) "
                    "por errores transitorios."
                )
            return resultado

        self.advertencias.append(
            "Ningún proveedor de IA respondió; se redactó con las plantillas legales locales."
        )
        return None

    def _transmitir_llm(
        self, sistema: str, usuario: str, *, max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """Transmite la redacción del primer proveedor disponible (SSE).

        Si un proveedor falla **antes** de emitir texto se prueba el siguiente; si
        ya se emitió contenido, se corta el flujo para no duplicar párrafos.
        """
        if not self.ia_habilitada:
            return

        for nombre in self.cadena_proveedores:
            proveedor = crear_proveedor(nombre, self.config)
            if proveedor is None:
                continue

            emitido = False
            try:
                for fragmento in proveedor.chat_stream(
                    sistema, usuario, max_tokens=max_tokens
                ):
                    emitido = True
                    yield fragmento
            except ErrorLLM as error:
                self.advertencias.append(
                    f"El proveedor «{nombre}» interrumpió la redacción en vivo "
                    f"({error.intentos} intento(s))."
                )
                if emitido:
                    return
                continue
            except Exception as exc:  # pragma: no cover - salvaguarda final
                logger.exception("Fallo de streaming con el proveedor %s", nombre)
                self.advertencias.append(
                    f"Fallo de streaming con el proveedor «{nombre}» ({type(exc).__name__})."
                )
                if emitido:
                    return
                continue

            self.llamadas.append({"proveedor": nombre, "modelo": proveedor.modelo, "stream": True})
            return

    # ------------------------------------------------ streaming público (SSE)
    def transmitir_redaccion(
        self,
        acuerdo: Acuerdo,
        contexto: Mapping[str, str],
        instrucciones: Optional[str] = None,
    ) -> Iterator[str]:
        """Genera la cláusula de un acuerdo y entrega los fragmentos en orden.

        Cuando no hay IA configurada se apoya en la plantilla legal local y la
        transmite troceada, de modo que la interfaz nunca queda esperando en vano.
        """
        if self.ia_habilitada:
            usuario = self._prompt_usuario_redaccion(acuerdo, contexto, instrucciones)
            yield from self._transmitir_llm(PROMPT_SISTEMA_REDACCION, usuario)
            return

        materia = acuerdo.materia or plantillas.detectar_materia(
            f"{acuerdo.titulo} {acuerdo.resumen}", ""
        )
        redaccion = plantillas.redactar_con_plantilla(materia, dict(contexto))
        self.advertencias.append(
            "No hay proveedor de IA configurado: la redacción en vivo se generó con las "
            "plantillas legales locales."
        )
        yield from trocear(str(redaccion.get("clausula_legal") or ""))

    # -------------------------------------------------------------- validación
    def validar_acta(
        self,
        acta: ActaBase,
        clausulas: Optional[Mapping[str, str]] = None,
    ) -> ValidacionActa:
        """Valida la consistencia documental del acta.

        Siempre ejecuta las reglas deterministas locales; si hay IA disponible,
        combina el resultado con el del modelo para enriquecer los hallazgos.
        """
        base = self._validar_con_reglas(acta, clausulas)
        if not self.ia_habilitada:
            return base

        respuesta = self._consultar_llm(
            PROMPT_SISTEMA_VALIDACION, self._prompt_usuario_validacion(acta)
        )
        if respuesta is None:
            return base

        # ``_consultar_llm`` devuelve un ``ResultadoLLM``; el JSON va en su texto.
        datos = extraer_json(respuesta.texto)
        if not datos:
            return base
        return self._combinar_validaciones(base, datos)

    def _combinar_validaciones(
        self, base: ValidacionActa, datos: Mapping[str, Any]
    ) -> ValidacionActa:
        """Fusiona la validación por reglas con la devuelta por el LLM."""
        hallazgos: List[Hallazgo] = list(base.hallazgos)

        for crudo in datos.get("hallazgos") or []:
            if not isinstance(crudo, Mapping) or not crudo.get("mensaje"):
                continue
            hallazgos.append(
                Hallazgo(
                    severidad=_severidad(crudo.get("severidad")),
                    campo=str(crudo.get("campo") or "general"),
                    mensaje=str(crudo["mensaje"]),
                    sugerencia=str(crudo["sugerencia"]) if crudo.get("sugerencia") else None,
                )
            )

        recomendaciones = list(base.recomendaciones)
        for recomendacion in datos.get("recomendaciones") or []:
            texto = str(recomendacion).strip()
            if texto and texto not in recomendaciones:
                recomendaciones.append(texto)

        return ValidacionActa(
            puntaje=_puntaje(datos.get("puntaje"), base.puntaje),
            consistencia=str(datos.get("consistencia") or base.consistencia),
            hallazgos=hallazgos,
            recomendaciones=recomendaciones,
            proveedor=self.proveedor,
            generado_por_ia=True,
        )

    # ----------------------------------------------------- reglas deterministas
    def _validar_con_reglas(
        self, acta: ActaBase, clausulas: Optional[Mapping[str, str]] = None
    ) -> ValidacionActa:
        """Validación local (sin IA) de la consistencia formal y legal del acta."""
        hallazgos: List[Hallazgo] = []
        tipo = str(acta.tipo_asamblea)
        es_consejo = tipo == TipoAsamblea.SESION_CONSEJO.value
        quorum = acta.quorum_porcentaje or 0.0
        suma_asistentes = sum(a.porcentaje_capital or 0 for a in acta.asistentes)

        # 1) Quórum legal (arts. 189, 190 y 191 LGSM) --------------------------
        if not es_consejo and acta.capital_presente is not None:
            if quorum < 50:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.CRITICO,
                        campo="quorum_porcentaje",
                        mensaje=(
                            "El capital representado "
                            f"({formato.porcentaje(quorum)}) es inferior al 50% exigido para sesionar."
                        ),
                        sugerencia=(
                            "Celebra la asamblea en segunda convocatoria (art. 191 LGSM) o recaba la "
                            "representación accionaria faltante antes de la firma."
                        ),
                    )
                )
            elif quorum < 75 and tipo in TIPOS_EXTRAORDINARIOS:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.ADVERTENCIA,
                        campo="quorum_porcentaje",
                        mensaje=(
                            "La asamblea extraordinaria de primera convocatoria exige el 75% del "
                            f"capital social y se registró {formato.porcentaje(quorum)}."
                        ),
                        sugerencia=(
                            "Acredita que se trata de segunda convocatoria (art. 191 LGSM) o documenta "
                            "el porcentaje efectivamente representado."
                        ),
                    )
                )

        # 2) Datos de capital incompletos --------------------------------------
        if not es_consejo and acta.capital_social and acta.capital_presente is None:
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.ADVERTENCIA,
                    campo="capital_presente",
                    mensaje=(
                        "Se registró el capital social pero no el capital representado, por lo que el "
                        "quórum no puede cuantificarse."
                    ),
                    sugerencia=(
                        "Captura el importe o el número de acciones representadas en la asamblea."
                    ),
                )
            )

        # 3) Coherencia entre quórum declarado y suma de asistentes ------------
        if suma_asistentes and quorum and abs(suma_asistentes - quorum) > 1.0:
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.ADVERTENCIA,
                    campo="asistentes",
                    mensaje=(
                        "La suma de porcentajes de los asistentes "
                        f"({formato.porcentaje(suma_asistentes)}) no coincide con el quórum declarado "
                        f"({formato.porcentaje(quorum)})."
                    ),
                    sugerencia="Revisa la tenencia accionaria contra el libro de registro de acciones.",
                )
            )

        # 4) Convocatoria previa (arts. 186 y 187 LGSM) ------------------------
        if not es_consejo and tipo != TipoAsamblea.CONSTITUTIVA.value and not acta.convocatoria_fecha:
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.ADVERTENCIA,
                    campo="convocatoria_fecha",
                    mensaje=(
                        "No se registró la convocatoria previa, requisito de validez de la asamblea "
                        "conforme a los artículos 186 y 187 de la Ley General de Sociedades Mercantiles."
                    ),
                    sugerencia=(
                        "Captura la fecha de publicación de la convocatoria en el sistema electrónico "
                        "de la Secretaría de Economía y su cédula de publicación."
                    ),
                )
            )
        medio = (acta.convocatoria_medio or "").lower()
        if medio and "electr" not in medio:
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.INFORMATIVO,
                    campo="convocatoria_medio",
                    mensaje=(
                        f"El medio de convocatoria declarado es «{acta.convocatoria_medio}»; la ley prevé "
                        "la publicación en el sistema electrónico de la Secretaría de Economía."
                    ),
                    sugerencia="Verifica que la convocatoria cumpla con el artículo 186 de la LGSM.",
                )
            )

        # 5) Integración de la mesa directiva y asistentes ---------------------
        if len(acta.asistentes) < 2:
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.INFORMATIVO,
                    campo="asistentes",
                    mensaje="El acta debería consignar cuando menos a un presidente y a un secretario.",
                    sugerencia=(
                        "Agrega a los asistentes que fungirán como presidente, secretario y escrutadores."
                    ),
                )
            )

        nombres = [a.nombre.lower() for a in acta.asistentes]
        for campo, persona in (("presidente", acta.presidente), ("secretario", acta.secretario)):
            if persona and persona.lower() not in nombres:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.INFORMATIVO,
                        campo=campo,
                        mensaje=(
                            f"«{persona}» funge como {campo} pero no aparece en la lista de asistentes."
                        ),
                        sugerencia="Inclúyelo en la tabla de asistentes para que la firma sea congruente.",
                    )
                )
        if not any(a.es_escrutador for a in acta.asistentes) and tipo in TIPOS_EXTRAORDINARIOS:
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.INFORMATIVO,
                    campo="asistentes",
                    mensaje="No se designaron escrutadores para el cómputo de los votos.",
                    sugerencia="Designa al menos un escrutador y hazlo constar en el acta.",
                )
            )
        if acta.asistentes and not any(a.firma for a in acta.asistentes):
            hallazgos.append(
                Hallazgo(
                    severidad=SeveridadHallazgo.ADVERTENCIA,
                    campo="asistentes",
                    mensaje="Ningún asistente está marcado para firmar el acta.",
                    sugerencia="Marca cuando menos a los asistentes con derecho a voto para la hoja de firmas.",
                )
            )

        return self._cerrar_validacion(acta, hallazgos, clausulas)

    def _cerrar_validacion(
        self,
        acta: ActaBase,
        hallazgos: List[Hallazgo],
        clausulas: Optional[Mapping[str, str]] = None,
    ) -> ValidacionActa:
        """Aplica las reglas sobre los acuerdos y calcula el puntaje final."""
        tipo = str(acta.tipo_asamblea)
        titulos_orden = {punto.titulo.strip().lower() for punto in acta.orden_del_dia}
        acciones_totales = acta.capital_presente or acta.acciones_totales or 0

        # 6) Correspondencia entre orden del día y acuerdos --------------------
        for acuerdo in acta.acuerdos:
            if acuerdo.titulo.strip().lower() not in titulos_orden:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.ADVERTENCIA,
                        campo=f"acuerdos.{acuerdo.numero}",
                        mensaje=(
                            f"El acuerdo «{acuerdo.titulo}» no corresponde a ningún punto del orden del día."
                        ),
                        sugerencia=(
                            "Incorpora el asunto al orden del día y constata que se aprobó el punto "
                            "antes de someterlo a votación (art. 179 LGSM)."
                        ),
                    )
                )

            # 7) Cláusula legal / fundamento faltante --------------------------
            if not (acuerdo.clausula_legal or "").strip():
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.ADVERTENCIA,
                        campo=f"acuerdos.{acuerdo.numero}.clausula_legal",
                        mensaje=f"El acuerdo «{acuerdo.titulo}» no tiene cláusula legal redactada.",
                        sugerencia="Genera el borrador con IA o transcribe la cláusula antes de firmar.",
                    )
                )
            if not (acuerdo.fundamento_legal or "").strip():
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.INFORMATIVO,
                        campo=f"acuerdos.{acuerdo.numero}.fundamento_legal",
                        mensaje=f"El acuerdo «{acuerdo.titulo}» no invoca expresamente sus fundamentos legales.",
                        sugerencia="Añade los artículos de la LGSM o de los estatutos aplicables.",
                    )
                )

            # 8) Resultado de la votación --------------------------------------
            votacion = acuerdo.votacion
            if votacion is None:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.ADVERTENCIA,
                        campo=f"acuerdos.{acuerdo.numero}.votacion",
                        mensaje=f"No se registró la votación del acuerdo «{acuerdo.titulo}».",
                        sugerencia="Captura el sentido de la votación y las acciones computadas.",
                    )
                )
                continue

            if not votacion.aprobado:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.CRITICO,
                        campo=f"acuerdos.{acuerdo.numero}.votacion",
                        mensaje=f"El acuerdo «{acuerdo.titulo}» está marcado como no aprobado.",
                        sugerencia="Corrige el resultado de la votación o retira el acuerdo del acta.",
                    )
                )

            requerido = votacion.porcentaje_requerido or porcentaje_requerido_mayoria(
                votacion.tipo_mayoria
            )
            if requerido and acciones_totales:
                porcentaje_favor = votacion.acciones_a_favor / acciones_totales * 100
                if votacion.aprobado and porcentaje_favor + 0.01 < requerido:
                    hallazgos.append(
                        Hallazgo(
                            severidad=SeveridadHallazgo.ADVERTENCIA,
                            campo=f"acuerdos.{acuerdo.numero}.votacion",
                            mensaje=(
                                f"El acuerdo «{acuerdo.titulo}» se declara aprobado con "
                                f"{formato.porcentaje(porcentaje_favor)} a favor, cuando la mayoría "
                                f"requerida es {formato.porcentaje(requerido)}."
                            ),
                            sugerencia="Ajusta la mayoría declarada o la base de cómputo de las acciones.",
                        )
                    )

            if tipo in TIPOS_EXTRAORDINARIOS and votacion.tipo_mayoria == TipoMayoria.MAYORIA_SIMPLE:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.INFORMATIVO,
                        campo=f"acuerdos.{acuerdo.numero}.votacion",
                        mensaje=(
                            f"En asamblea extraordinaria el acuerdo «{acuerdo.titulo}» se aprobó por mayoría "
                            "simple; verifica que no se trate de un supuesto del artículo 182 de la LGSM."
                        ),
                        sugerencia="Usa mayoría calificada cuando el acuerdo implique reforma estatutaria.",
                    )
                )

        return self._construir_validacion(
            hallazgos,
            acta=acta,
            clausulas=clausulas,
        )

    def _construir_validacion(
        self,
        hallazgos: List[Hallazgo],
        acta: Optional[ActaBase] = None,
        clausulas: Optional[Mapping[str, str]] = None,
    ) -> ValidacionActa:
        """Calcula el puntaje, el resumen ejecutivo y las recomendaciones finales."""
        pesos = {
            SeveridadHallazgo.CRITICO.value: 15.0,
            SeveridadHallazgo.ADVERTENCIA.value: 7.0,
            SeveridadHallazgo.INFORMATIVO.value: 2.0,
        }
        penalizacion = sum(pesos.get(str(hallazgo.severidad), 2.0) for hallazgo in hallazgos)
        puntaje = max(0.0, min(100.0, round(100.0 - penalizacion, 2)))

        criticos = sum(1 for h in hallazgos if str(h.severidad) == SeveridadHallazgo.CRITICO.value)
        advertencias = sum(
            1 for h in hallazgos if str(h.severidad) == SeveridadHallazgo.ADVERTENCIA.value
        )
        informativos = sum(
            1 for h in hallazgos if str(h.severidad) == SeveridadHallazgo.INFORMATIVO.value
        )

        if puntaje >= 90:
            resumen = "El acta es consistente: no se detectaron incumplimientos formales relevantes."
        elif puntaje >= 70:
            resumen = (
                "El acta es consistente en lo general, con observaciones que conviene atender "
                "antes de la firma."
            )
        elif puntaje >= 45:
            resumen = (
                "Se detectaron inconsistencias que deben corregirse antes de someter el acta a firma."
            )
        else:
            resumen = (
                "El acta presenta hallazgos críticos; no se recomienda su firma ni protocolización "
                "en el estado actual."
            )
        resumen += (
            f" Se registraron {criticos} hallazgo(s) crítico(s), {advertencias} advertencia(s) y "
            f"{informativos} observación(es) informativa(s)."
        )

        # Piezas del documento que no pudieron verificarse.
        if clausulas is not None:
            faltantes = [clave for clave in ("encabezado", "declaracion_quorum", "cierre") if not clausulas.get(clave)]
            if faltantes:
                hallazgos.append(
                    Hallazgo(
                        severidad=SeveridadHallazgo.INFORMATIVO,
                        campo="clausulas",
                        mensaje=f"No se generaron las secciones: {', '.join(faltantes)}.",
                        sugerencia="Vuelve a ejecutar la redacción del acta antes de exportar el PDF.",
                    )
                )

        recomendaciones: List[str] = [
            "Coteja los datos societarios contra el acta constitutiva, los estatutos vigentes y el "
            "libro de registro de acciones antes de la firma.",
            "Conserva las constancias de la convocatoria y los poderes de los representantes como "
            "anexos del expediente del acta.",
            "Somete el acta a revisión de un abogado corporativo y, cuando proceda, a protocolización "
            "ante fedatario público e inscripción en el Registro Público de Comercio.",
        ]
        if criticos:
            recomendaciones.insert(
                0,
                "Atiende primero los hallazgos críticos: sin corregirlos el acta puede ser impugnable.",
            )
        if acta is not None and acta.capital_social and not acta.capital_presente:
            recomendaciones.append(
                "Cuantifica el capital representado para acreditar el quórum en el propio texto del acta."
            )

        return ValidacionActa(
            puntaje=puntaje,
            consistencia=resumen,
            hallazgos=hallazgos,
            recomendaciones=recomendaciones,
            proveedor=self.proveedor,
            generado_por_ia=False,
        )


def crear_servicio_ia(config: Optional[Settings] = None) -> AIService:
    """Fábrica del servicio de IA: facilita sustituirlo en pruebas o tareas puntuales."""
    return AIService(config)










