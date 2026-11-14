"""Asistente conversacional interno de actas (IA sin dependencias externas).

Funciona en cualquier PC sin internet ni API keys: puerta tematica,
intenciones por reglas, redaccion LGSM con plantillas y validacion
determinista. Lee el estatus real desde la BD, nunca lo inventa.

Además acompaña la CREACIÓN guiada del acta: si el usuario pide un acta en
específico le pide los datos necesarios; si no sabe qué acta crear le ofrece
el catálogo con descripciones; al completar envía el borrador a revisión y
devuelve el control (folio, fecha, autor, caducidad y versión).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.catalogos import (
    acta_aplicable,
    etiqueta_tipo_asamblea,
    ordenamiento_sociedad,
    requisitos_acta,
)
from app.core import security
from app.models.acta import Acta
from app.models.enums import EstatusActa
from app.schemas.acta import ActaGenerarPdfRequest
from app.services import administracion, plantillas_legales
from app.services.acta_service import (
    actualizar_estatus,
    crear_acta,
    redactar,
    validar_acta_almacenada,
)
from app.services.flujo_creacion import (
    TIPOS_GUIA,
    construir_payload_desde_sesion,
    campos_requeridos_para_sesion,
    crear_sesion,
    detectar_tipo_en_texto,
    extraer_datos,
    obtener_sesion,
    reiniciar_sesion,
    siguiente_faltante,
)
from app.services.tenant_access import (
    alcance_empresa,
    filtrar_por_empresa,
)

logger = logging.getLogger(__name__)

DIAS_HABILES_LIMITE_ATRASO = 5

__all__ = [
    "es_tema_valido", "detectar_intencion", "extraer_folio",
    "extraer_id", "procesar_mensaje", "texto_ayuda", "SUGERENCIAS",
    "TIPOS_GUIA",
]

PALABRAS_TEMA = (
    "acta", "actas", "asamblea", "consejo", "acuerdo", "acuerdos",
    "clausula", "quorum", "mayoria", "votacion", "folio", "estatus",
    "borrador", "revision", "aprobada", "aprobado", "firmada", "firmar",
    "archivada", "version", "versiones", "vigencia", "caducidad",
    "vencida", "validar", "validacion", "consistencia", "redactar",
    "redaccion", "lgsm", "sociedad", "estatutos", "capital", "acciones",
    "accionista", "presidente", "secretario", "escrutador", "comisario",
    "convocatoria", "orden del dia", "aumento", "reduccion", "fusion",
    "escision", "disolucion", "liquidacion", "protocolizar", "fedatario",
    "notario", "ordinaria", "extraordinaria", "constitutiva", "mixta",
    "restaurar", "historial", "hallazgo", "puntaje", "estado", "ayuda",
    "crear", "crea", "generar", "genera", "nueva", "nuevo", "necesito",
    "quiero", "elaborar", "hazme", "cual", "cuales", "tipos", "opciones",
    "elegir", "escoger", "editar", "modificar", "pdf", "descargar",
    "descarga", "cancelar", "tiempo", "duracion", "dias", "habiles",
    "atraso", "atrasada", "atrasadas", "retraso", "retrasada", "demora",
)

PALABRAS_FUERA = (
    "futbol", "mundial", "receta", "cocina", "videojuego", "pelicula",
    "cancion", "horoscopo", "bitcoin", "cripto", "dieta",
)

MENSAJE_FUERA = (
    "Solo puedo ayudarte con temas de actas administrativas y corporativas "
    "(redaccion, validacion, aprobacion, estatus y versiones). "
    "Ejemplos: «Estatus de PGAC-2026-0001», «Valida el acta 1», "
    "«Redacta un aumento de capital»."
)

SUGERENCIAS = [
    "Quiero crear un acta",
    "Qué tipos de acta hay?",
    "Crear acta ordinaria",
    "Estatus de PGAC-2026-0001",
    "Valida el acta 1",
    "Cuantas actas hay por estatus?",
    "Qué actas llevan más de 5 días hábiles?",
    "Cuanto tarda en promedio la aprobación?",
    "Versiones del acta 1",
    "Ayuda",
]

ORDEN_ESTATUS = ["borrador", "en_revision", "aprobada", "firmada", "archivada"]
PATRON_FOLIO = re.compile(r"PGAC-\d{4}-\d{1,6}", re.IGNORECASE)


def _norm(t: str) -> str:
    if not t:
        return ""
    d = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def es_tema_valido(mensaje: str) -> bool:
    norm = _norm(mensaje or "")
    if not norm.strip():
        return False
    if any(_norm(p) in norm for p in PALABRAS_FUERA):
        if not any(k in norm for k in ("acta", "asamblea", "acuerdo", "folio")):
            return False
    return any(_norm(t) in norm for t in PALABRAS_TEMA)


def detectar_intencion(mensaje: str) -> str:
    n = _norm(mensaje or "")
    if any(k in n for k in (
        "atrasad", "atraso", "retrasad", "retraso", "demora", "tiempo promedio",
        "tiempo de aprobacion", "tiempo en revision", "dias habiles",
        "cuanto tarda", "cuanto tiempo",
    )) or (
        "tiempo" in n
        and any(etapa in n for etapa in ("revision", "abogado", "aprobacion", "correccion"))
    ):
        return "tiempos"
    if any(k in n for k in ("restaurar", "recuperar version", "volver a la version")):
        return "restaurar"
    if any(k in n for k in ("editar", "modificar", "modifica", "cambiar", "cambia")) and (
        extraer_folio(mensaje) or extraer_id(mensaje)
    ):
        return "editar"
    if any(k in n for k in ("cancelar", "olvida", "empezar de nuevo", "reiniciar")):
        return "cancelar_creacion"
    if any(k in n for k in ("que tipos hay", "que actas hay", "cuales actas",
                            "tipos de acta", "que acta", "cual acta",
                            "no se que acta", "no se cual", "ayudame a elegir",
                            "opciones de acta", "catalogo de actas")):
        return "catalogo_tipos"
    # Crear/generar ACTA completa -> flujo guiado. OJO: «redacta un acuerdo»
    # es solo un borrador de cláusula (intención redactar), no el acta entera.
    es_borrador_acuerdo = any(k in n for k in ("redacta", "redaccion", "redactar",
                                               "escribe", "genera un acuerdo",
                                               "acuerdo de", "clausula"))
    if not es_borrador_acuerdo:
        if (any(k in n for k in ("crear acta", "crea un acta", "creame un acta",
                                 "generar acta", "genera un acta", "nueva acta",
                                 "nuevo acta", "quiero un acta", "necesito un acta",
                                 "elaborar acta", "hazme un acta", "quiero crear",
                                 "crear un acta"))
                or (detectar_tipo_en_texto(mensaje) is not None
                    and "acta" in n)):
            return "crear"
    if any(k in n for k in ("validar", "valida", "consistencia", "hallazgo", "puntaje")):
        return "validar"
    if any(k in n for k in ("redacta", "redaccion", "redactar", "escribe", "genera un acuerdo")):
        return "redactar"
    if (any(k in n for k in ("aprueba", "aprobar", "aprobada", "aprobado", "autoriza",
                             "pasa a", "pasala a", "pasalo a", "cambia el estatus",
                             "cambiar estatus", "firmar", "firmada", "firmado",
                             "archivar", "archivada", "archivarla"))
            or re.search(r"\bpasa\b.*\bacta\b", n)
            or re.search(r"\ba\s+(revision|aprobada|firmada|archivada)\b", n)):
        return "aprobar"
    if any(k in n for k in ("vencida", "vigencia", "caducidad", "por vencer",
                            "cuantas actas", "resumen", "estadistica", "totales", "cuantas hay")):
        return "resumen"
    if re.search(r"\bversiones?\b", n) or "historial" in n or "que cambio" in n:
        return "versiones"
    if any(k in n for k in ("estatus", "estado", "en que va", "como va", "donde esta",
                            "busca el acta", "muestrame el acta", "muestra el acta")):
        return "estatus"
    if any(k in n for k in ("ayuda", "que puedes hacer", "que sabes hacer", "como funciona", "ejemplos")):
        return "ayuda"
    if extraer_folio(mensaje) or re.search(r"\bacta\s+\d+\b", n):
        return "estatus"
    return "ayuda"


def extraer_folio(mensaje: str) -> Optional[str]:
    m = PATRON_FOLIO.search(mensaje or "")
    return m.group(0).upper() if m else None


def extraer_id(mensaje: str) -> Optional[int]:
    m = re.search(r"\bacta\s+(?:numero\s+|n\.?\s*)?(\d{1,6})\b", _norm(mensaje or ""))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def extraer_num_version(mensaje: str) -> Optional[int]:
    m = re.search(r"version\s+(\d{1,4})", _norm(mensaje or ""))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def extraer_estatus_destino(mensaje: str) -> Optional[str]:
    n = _norm(mensaje or "")
    if re.search(r"\ba\s+revision\b", n) or "en revision" in n:
        return "en_revision"
    for est in EstatusActa:
        if _norm(est.value) in n or _norm(est.value.replace("_", " ")) in n:
            return est.value
    if "revision" in n:
        return "en_revision"
    if "protocoliz" in n:
        return "archivada"
    return None


def _buscar(
    db: Session,
    folio: Optional[str],
    acta_id: Optional[int],
    usuario=None,
) -> Optional[Acta]:
    consulta = filtrar_por_empresa(
        select(Acta), alcance_empresa(usuario), Acta.empresa_codigo
    )
    if acta_id is not None:
        return db.scalar(consulta.where(Acta.id == acta_id))
    if folio:
        return db.scalar(
            consulta.where(func.upper(Acta.folio) == folio.upper())
        )
    return None


def _linea(acta: Acta) -> str:
    tipo = etiqueta_tipo_asamblea(getattr(acta, "tipo_asamblea", ""))
    estatus = str(getattr(acta.estatus, "value", acta.estatus))
    return (f"{acta.folio} | {acta.sociedad} | {tipo} | estatus "
            f"{estatus} | v{acta.version} | vigencia {acta.estado_caducidad}")


def _dato_acta(acta: Acta) -> Dict[str, Any]:
    return {"id": acta.id, "folio": acta.folio, "sociedad": acta.sociedad,
            "estatus": str(getattr(acta.estatus, "value", acta.estatus)),
            "version": int(acta.version or 1),
            "tipo_asamblea": str(getattr(acta.tipo_asamblea, "value", acta.tipo_asamblea)),
            "fecha": acta.fecha.isoformat() if getattr(acta, "fecha", None) else None,
            "creado_por": getattr(acta, "creado_por", None)}


def _fecha_evento(valor: Any) -> Optional[date]:
    if isinstance(valor, datetime):
        return valor.date()
    if not isinstance(valor, str) or not valor.strip():
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _dias_habiles_entre(inicio: Optional[date], fin: date) -> int:
    if inicio is None or inicio >= fin:
        return 0
    dias = 0
    fecha = inicio
    while fecha < fin:
        fecha += timedelta(days=1)
        if fecha.weekday() < 5:
            dias += 1
    return dias


def _inicio_etapa(acta: Acta) -> Optional[date]:
    for evento in reversed(acta.historial_revision or []):
        if (
            isinstance(evento, dict)
            and evento.get("estado_resultante") == acta.estado_flujo
        ):
            fecha = _fecha_evento(evento.get("creado_en"))
            if fecha:
                return fecha
    return _fecha_evento(acta.created_at)


def _resumen_tiempos(db: Session, alcance, usuario, mensaje: str) -> Dict[str, Any]:
    hoy = datetime.now(timezone.utc).date()
    estados_activos = {"revision", "abogado", "con_errores"}
    texto = _norm(mensaje)
    if "revision" in texto:
        estados_filtro = {"revision"}
    elif any(palabra in texto for palabra in ("abogado", "aprobacion")):
        estados_filtro = {"abogado"}
    elif any(palabra in texto for palabra in ("correccion", "devuelta", "devueltas")):
        estados_filtro = {"con_errores"}
    elif getattr(usuario, "rol", None) == "revisor":
        estados_filtro = {"revision"}
    elif getattr(usuario, "rol", None) == "abogado_responsable":
        estados_filtro = {"abogado"}
    else:
        estados_filtro = estados_activos

    consulta = filtrar_por_empresa(
        select(Acta), alcance, Acta.empresa_codigo
    )
    actas = list(db.scalars(consulta))
    atrasadas = []
    tiempos_aprobacion = []
    for acta in actas:
        estado = str(getattr(acta.estado_flujo, "value", acta.estado_flujo))
        if estado in estados_filtro:
            dias = _dias_habiles_entre(_inicio_etapa(acta), hoy)
            if dias > DIAS_HABILES_LIMITE_ATRASO:
                atrasadas.append((dias, acta))
        if estado == "aprobada":
            evento_aprobacion = next(
                (
                    evento
                    for evento in reversed(acta.historial_revision or [])
                    if isinstance(evento, dict)
                    and evento.get("estado_resultante") == "aprobada"
                ),
                None,
            )
            fecha_aprobacion = (
                _fecha_evento(evento_aprobacion.get("creado_en"))
                if evento_aprobacion
                else None
            )
            fecha_creacion = _fecha_evento(acta.created_at)
            if fecha_creacion and fecha_aprobacion:
                tiempos_aprobacion.append(
                    _dias_habiles_entre(fecha_creacion, fecha_aprobacion)
                )

    atrasadas.sort(key=lambda elemento: elemento[0], reverse=True)
    lineas = [
        "Umbral de atraso: más de %s días hábiles (lunes a viernes; no se descuentan feriados)."
        % DIAS_HABILES_LIMITE_ATRASO,
        "Actas atrasadas en la etapa consultada: %s." % len(atrasadas),
    ]
    for dias, acta in atrasadas[:5]:
        lineas.append(
            "- %s · %s · %s días hábiles."
            % (acta.folio, acta.estado_flujo, dias)
        )
    if not atrasadas:
        lineas.append("No hay actas que superen el umbral en la etapa consultada.")
    if tiempos_aprobacion:
        promedio = sum(tiempos_aprobacion) / len(tiempos_aprobacion)
        lineas.append(
            "Tiempo promedio de creación a aprobación: %.1f días hábiles (%s actas aprobadas)."
            % (promedio, len(tiempos_aprobacion))
        )
    else:
        lineas.append("Aún no hay suficientes actas aprobadas con historial para calcular el promedio.")
    return {
        "respuesta": "\n".join(lineas),
        "intencion": "tiempos",
        "tema_valido": True,
    }


def _respuesta_sesion(sesion, texto, faltante_extra=None):
    falt = faltante_extra or siguiente_faltante(sesion)
    datos = sesion.get("datos", {})
    hechos = sum(1 for v in datos.values() if v not in (None, "", [], {}))
    campos = campos_requeridos_para_sesion(sesion)
    marco = ordenamiento_sociedad(datos.get("tipo_sociedad"))
    requisitos = requisitos_acta(
        str(sesion.get("tipo_asamblea") or "ordinaria"),
        datos.get("tipo_sociedad"),
    )
    if falt and falt["clave"] in {requisito["clave"] for requisito in requisitos}:
        texto = (
            f"{texto}\n\nMarco referencial: {marco}. "
            f"El acta será un borrador documental y debe revisarse con un abogado o notario "
            f"antes de firmarse, protocolizarse o inscribirse."
        )
    base = {"respuesta": texto, "intencion": "crear", "tema_valido": True,
            "sesion_id": sesion["sesion_id"],
            "tipo_asamblea": sesion.get("tipo_asamblea"),
            "tipo_sociedad": datos.get("tipo_sociedad"),
            "marco_normativo": marco,
            "datos_recolectados": datos,
            "progreso": {"completados": hechos, "total": len(campos)}}
    if falt is not None:
        base["campo_solicitado"] = falt["clave"]
    return base


def _respuesta_confirmacion_creacion(sesion, texto=None):
    base = _respuesta_sesion(
        sesion,
        texto
        or "Revisa los datos recopilados. Si son correctos, confirma para enviar el acta a revisión; también puedes indicar qué campo deseas corregir.",
        None,
    )
    datos = sesion.get("datos", {})
    etiquetas = {
        campo["clave"]: campo["etiqueta"]
        for campo in campos_requeridos_para_sesion(sesion)
    }
    resumen = {"tipo_asamblea": etiqueta_tipo_asamblea(sesion.get("tipo_asamblea") or "")}
    for campo in campos_requeridos_para_sesion(sesion):
        valor = datos.get(campo["clave"])
        if valor not in (None, "", [], {}):
            resumen[etiquetas[campo["clave"]]] = valor
    if datos.get("rfc_sociedad"):
        resumen["RFC de la sociedad"] = datos["rfc_sociedad"]
    base["confirmacion_creacion"] = True
    base["resumen_creacion"] = resumen
    return base


def _campo_para_cambiar(mensaje, sesion):
    texto = _norm(mensaje)
    for campo in sorted(
        campos_requeridos_para_sesion(sesion),
        key=lambda item: len(item["etiqueta"]),
        reverse=True,
    ):
        clave = _norm(campo["clave"].replace("_", " "))
        etiqueta = _norm(campo["etiqueta"])
        if clave in texto or etiqueta in texto:
            return campo
    return None


def _es_confirmacion_creacion(mensaje):
    texto = _norm(mensaje)
    return texto.strip(" .!") in {
        "confirmar",
        "confirmo",
        "acepto",
        "si",
        "si enviar a revision",
        "enviar a revision",
        "confirmar y enviar a revision",
        "confirmo y enviar a revision",
    }


def _es_cancelacion_creacion(mensaje):
    texto = _norm(mensaje or "").strip()
    return bool(
        re.fullmatch(
            r"(?:por favor\s+)?cancelar(?:\s+(?:el\s+|la\s+)?(?:proceso|creacion))?[.!?\s]*",
            texto,
        )
        or texto in {"detener", "reiniciar", "empezar de nuevo"}
    )


def _solicita_catalogo_completo(mensaje):
    texto = _norm(mensaje or "")
    return any(
        frase in texto
        for frase in (
            "ver todos los tipos",
            "todos los tipos de acta",
            "catalogo completo",
            "ver catalogo",
            "que tipos de acta hay",
            "que tipos hay",
            "que actas hay",
        )
    )


def _respuesta_catalogo(sesion, completo=False):
    recomendados = {"ordinaria", "extraordinaria", "aumento_capital", "sesion_consejo"}
    tipos = (
        TIPOS_GUIA
        if completo
        else [tipo for tipo in TIPOS_GUIA if tipo["valor"] in recomendados]
    )
    return {
        "respuesta": (
            "Estos son los tipos disponibles. Elige uno para continuar."
            if completo
            else "¿Qué tipo necesitas? Elige una opción o escribe el asunto principal y te orientaré."
        ),
        "intencion": "catalogo_tipos",
        "tema_valido": True,
        "sesion_id": sesion["sesion_id"],
        "tipos_acta": tipos,
        "catalogo_completo_disponible": not completo,
    }


def _cerrar_y_generar(db, sesion, autor):
    try:
        payload_dict = construir_payload_desde_sesion(sesion)
        payload_dict["datos_asistente"] = {
            "tipo_asamblea": sesion.get("tipo_asamblea"),
            "datos": dict(sesion.get("datos") or {}),
            "respuestas": list(sesion.get("respuestas") or []),
        }
        payload_dict["creado_por"] = (autor or "asistente").strip()[:150] or "asistente"
        payload_dict["estatus"] = EstatusActa.EN_REVISION.value
        solicitud = ActaGenerarPdfRequest(**payload_dict)
        borrador = redactar(solicitud)
        acta = crear_acta(
            db,
            solicitud,
            borrador,
            empresa_codigo=sesion.get("empresa_codigo"),
        )
        acta.estado_flujo = "revision"
        db.commit()
        db.refresh(acta)
        reiniciar_sesion(
            sesion.get("sesion_id"),
            usuario_id=sesion.get("usuario_id"),
            empresa_codigo=sesion.get("empresa_codigo"),
        )
        control = {"folio": acta.folio, "acta_id": acta.id,
            "version": acta.version,
            "fecha_acta": payload_dict.get("fecha"),
            "fecha_creacion": acta.created_at.isoformat() if getattr(acta, "created_at", None) else None,
            "creado_por": payload_dict.get("creado_por"),
            "fecha_caducidad": acta.fecha_caducidad.isoformat() if acta.fecha_caducidad else None,
            "estado_caducidad": acta.estado_caducidad,
            "estado_flujo": acta.estado_flujo}
        texto_org = str(acta.texto_legal or "")[:4000]
        tipo_txt = etiqueta_tipo_asamblea(payload_dict.get("tipo_asamblea") or "")
        respuesta = (
            "Acta %s creada y enviada a revisión.\nCONTROL: folio %s | fecha %s | "
            "creada %s | por %s | v%s | estado: En revisión\n\nTEXTO:\n%s\n\n"
            "El PDF final estará disponible después de la aprobación del Abogado."
            % (
                tipo_txt,
                control["folio"],
                control["fecha_acta"],
                control["fecha_creacion"],
                control["creado_por"],
                control["version"],
                texto_org,
            )
        )
        return {"respuesta": respuesta, "intencion": "crear", "tema_valido": True,
                "acta": _dato_acta(acta),
                "control_acta": control, "acta_id": control["acta_id"],
                "folio": control["folio"], "texto_organizado": texto_org,
                "acciones": [{"etiqueta": "Ver actas", "accion": "ir_mis_actas"}],
                "_evento_auditoria": {
                    "accion": "crear",
                    "entidad": "actas",
                    "entidad_id": acta.id,
                    "datos_despues": {
                        "folio": acta.folio,
                        "sociedad": acta.sociedad,
                        "estado_flujo": acta.estado_flujo,
                        "version": acta.version,
                        "proveedor_ia": acta.proveedor_ia,
                        "generado_con_ia": bool(
                            solicitud.generar_clausulas
                            and acta.proveedor_ia != "plantillas"
                        ),
                    },
                }}
    except Exception as exc:
        logger.exception("Fallo generar acta desde asistente")
        falt = siguiente_faltante(sesion)
        return _respuesta_sesion(sesion, "No pude generarla: %s. %s"
                                 % (str(exc)[:300], falt["pregunta"] if falt else ""), falt)


def texto_ayuda() -> str:
    return ("Soy el Asistente de Actas de PGAC. "
            "Te acompano a CREAR el acta paso a paso: dime Quiero crear un acta. "
            "Si no sabes cual crear te muestro los tipos con su descripcion. "
            "Antes de enviarla podras revisar y corregir los datos. El borrador pasa a revision; "
            "el PDF final se habilita despues de la aprobacion del Abogado. Tambien valido, "
            "informo estatus, tiempos por etapa, actas atrasadas (mas de 5 dias habiles) "
            "y versiones. Prueba: Quiero crear un acta.")


def _puede_avanzar(origen: str, destino: str) -> bool:
    try:
        return ORDEN_ESTATUS.index(destino) >= ORDEN_ESTATUS.index(origen)
    except ValueError:
        return False


_PATRON_MONTO = re.compile(r"\$?\s*(\d[\d,]*(?:\.\d{1,2})?)")


def _extraer_monto_texto(mensaje: str) -> Optional[str]:
    """Extrae la primera cifra del mensaje con formato monetario, si existe."""
    coincidencia = _PATRON_MONTO.search(mensaje or "")
    if not coincidencia:
        return None
    crudo = coincidencia.group(1).replace(",", "")
    try:
        from app.core import formato

        return formato.moneda(float(crudo))
    except (ValueError, TypeError):
        return None


_CAMPOS_EDICION = [
    {"clave": "titulo", "etiqueta": "Título", "tipo": "texto",
     "alias": ("titulo", "nombre del acta")},
    {"clave": "fecha", "etiqueta": "Fecha de celebración", "tipo": "fecha",
     "alias": ("fecha", "dia de la asamblea")},
    {"clave": "hora", "etiqueta": "Hora", "tipo": "hora",
     "alias": ("hora",)},
    {"clave": "lugar", "etiqueta": "Lugar", "tipo": "texto",
     "alias": ("lugar", "domicilio")},
    {"clave": "rfc_sociedad", "etiqueta": "RFC de la sociedad", "tipo": "texto",
     "alias": ("rfc",)},
    {"clave": "convocatoria_fecha", "etiqueta": "Fecha de convocatoria", "tipo": "fecha",
     "alias": ("convocatoria", "fecha de convocatoria")},
    {"clave": "convocatoria_medio", "etiqueta": "Medio de convocatoria", "tipo": "texto",
     "alias": ("medio de convocatoria",)},
    {"clave": "convocatoria_quien", "etiqueta": "Responsable de la convocatoria", "tipo": "texto",
     "alias": ("responsable de la convocatoria", "quien convoco")},
    {"clave": "capital_social", "etiqueta": "Capital social", "tipo": "numero",
     "alias": ("capital social",)},
    {"clave": "acciones_totales", "etiqueta": "Acciones totales", "tipo": "numero",
     "alias": ("acciones totales", "total de acciones")},
    {"clave": "capital_presente", "etiqueta": "Capital presente", "tipo": "numero",
     "alias": ("capital presente",)},
    {"clave": "quorum_porcentaje", "etiqueta": "Porcentaje de quórum", "tipo": "numero",
     "alias": ("quorum", "porcentaje de quorum")},
    {"clave": "presidente", "etiqueta": "Presidente", "tipo": "texto",
     "alias": ("presidente",)},
    {"clave": "secretario", "etiqueta": "Secretario", "tipo": "texto",
     "alias": ("secretario",)},
    {"clave": "observaciones", "etiqueta": "Observaciones", "tipo": "texto",
     "alias": ("observaciones",)},
]
_SESIONES_EDICION: Dict[str, Dict[str, Any]] = {}


def _opciones_edicion(acta: Acta) -> List[Dict[str, str]]:
    opciones = [
        {"clave": campo["clave"], "etiqueta": campo["etiqueta"]}
        for campo in _CAMPOS_EDICION
    ]
    for clave, valor in (acta.datos_especificos or {}).items():
        if isinstance(valor, (str, int, float, bool)):
            opciones.append({
                "clave": "datos_especificos." + str(clave),
                "etiqueta": str(clave).replace("_", " ").capitalize(),
            })
    return opciones


def _resolver_campo_edicion(texto: str, acta: Acta) -> Optional[str]:
    valor = _norm(texto).strip()
    opciones = _opciones_edicion(acta)
    for opcion in opciones:
        if valor == _norm(opcion["clave"]) or valor == _norm(opcion["etiqueta"]):
            return opcion["clave"]
    for campo in sorted(_CAMPOS_EDICION, key=lambda item: len(item["clave"]), reverse=True):
        if any(_norm(alias) in valor for alias in campo["alias"]):
            return campo["clave"]
    for opcion in opciones:
        if opcion["clave"].startswith("datos_especificos.") and _norm(opcion["etiqueta"]) in valor:
            return opcion["clave"]
    return None


def _cambio_edicion(campo: str, texto: str) -> tuple[Optional[Any], Optional[str]]:
    valor = texto.strip()
    if not valor:
        return None, "Escribe el nuevo valor para continuar."
    definicion = next((item for item in _CAMPOS_EDICION if item["clave"] == campo), None)
    tipo = definicion["tipo"] if definicion else "texto"
    if tipo == "fecha":
        fecha = extraer_datos(valor, "fecha").get("fecha")
        if fecha is None:
            return None, "No reconocí la fecha. Indícala, por ejemplo, como 15 de marzo de 2026."
        return fecha, None
    if tipo == "hora":
        coincidencia = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", valor)
        if coincidencia is None:
            return None, "Indica la hora con formato HH:MM, por ejemplo 10:30."
        return f"{int(coincidencia.group(1)):02d}:{coincidencia.group(2)}", None
    if tipo == "numero":
        coincidencia = re.search(r"-?\d[\d,]*(?:\.\d+)?", valor)
        if coincidencia is None:
            return None, "Indica un valor numérico."
        try:
            return float(coincidencia.group(0).replace(",", "")), None
        except ValueError:
            return None, "No pude interpretar ese valor numérico."
    return valor, None


def _respuesta_edicion(sesion: Dict[str, Any], texto: str) -> Dict[str, Any]:
    acta = sesion["acta"]
    campo_actual = sesion.get("campo_actual")
    cambios = sesion["cambios"]
    if campo_actual:
        valor, error = _cambio_edicion(campo_actual, texto)
        if error:
            respuesta = error
        else:
            if campo_actual.startswith("datos_especificos."):
                clave = campo_actual.split(".", 1)[1]
                cambios.setdefault("datos_especificos", dict(acta.datos_especificos or {}))
                cambios["datos_especificos"][clave] = valor
            else:
                cambios[campo_actual] = valor
            sesion["campo_actual"] = None
            etiqueta = next(
                (item["etiqueta"] for item in _opciones_edicion(acta)
                 if item["clave"] == campo_actual),
                campo_actual,
            )
            respuesta = (
                f"Preparé el cambio de «{etiqueta}». Puedes elegir otro campo o aplicar "
                "los cambios al formulario para revisarlos y guardar una nueva versión."
            )
    else:
        if texto.strip() and texto.strip().lower() not in ("iniciar", "comenzar", "editar"):
            campo = _resolver_campo_edicion(texto, acta)
            if campo:
                sesion["campo_actual"] = campo
                etiqueta = next(
                    (item["etiqueta"] for item in _opciones_edicion(acta)
                     if item["clave"] == campo),
                    campo,
                )
                respuesta = f"¿Cuál es el nuevo valor de «{etiqueta}»?"
            elif any(palabra in _norm(texto) for palabra in ("sociedad", "tipo de acta", "tipo asamblea")):
                respuesta = "El tipo de acta y la sociedad no se pueden cambiar. Elige otro campo de la lista."
            else:
                respuesta = "Elige un campo de la lista para indicarme qué deseas modificar."
        else:
            respuesta = "¿Qué campo deseas modificar? El tipo de acta y la sociedad permanecen bloqueados."

    return {
        "respuesta": respuesta,
        "intencion": "editar",
        "tema_valido": True,
        "sesion_id": sesion["sesion_id"],
        "acta_id": acta.id,
        "campo_solicitado": sesion.get("campo_actual"),
        "campos_edicion": _opciones_edicion(acta) if not sesion.get("campo_actual") else [],
        "cambios_propuestos": cambios,
    }


def _procesar_edicion(
    db: Session,
    mensaje: str,
    acta_id: Optional[int],
    sesion_id: Optional[str],
    usuario=None,
) -> Dict[str, Any]:
    sesion = _SESIONES_EDICION.get(sesion_id) if sesion_id else None
    alcance = alcance_empresa(usuario)
    if sesion is not None and (
        sesion.get("usuario_id") != getattr(usuario, "id", None)
        or sesion.get("empresa_codigo") != alcance.codigo
    ):
        return {
            "respuesta": "La sesión de edición no existe o no pertenece a tu cuenta.",
            "intencion": "editar",
            "tema_valido": True,
        }
    if sesion and acta_id and sesion["acta"].id != acta_id:
        return {
            "respuesta": "La sesión de edición no corresponde al acta indicada.",
            "intencion": "editar",
            "tema_valido": True,
        }
    if sesion is None:
        acta = _buscar(db, None, acta_id, usuario)
        if acta is None:
            return {
                "respuesta": "No encontré el acta para editar. Verifica su identificador.",
                "intencion": "editar",
                "tema_valido": True,
            }
        sesion_id = uuid4().hex[:12]
        sesion = {
            "sesion_id": sesion_id,
            "acta": acta,
            "campo_actual": None,
            "cambios": {},
            "usuario_id": getattr(usuario, "id", None),
            "empresa_codigo": alcance.codigo,
        }
        _SESIONES_EDICION[sesion_id] = sesion
    return _respuesta_edicion(sesion, mensaje)


def _redactar_libre(mensaje: str) -> Dict[str, Any]:
    from app.models.enums import MateriaAcuerdo

    materia = plantillas_legales.detectar_materia(mensaje)
    plantilla = plantillas_legales.obtener_plantilla(materia)
    contexto = {"sociedad": "la sociedad", "resumen": mensaje.strip(),
                "mayoria": "la mayoria aplicable",
                "acciones": "las acciones presentes"}
    # Si el mensaje trae una cifra («aumento de capital por 500000») se usa para
    # cubrir los parámetros monetarios de la plantilla detectada.
    monto = _extraer_monto_texto(mensaje)
    if monto:
        contexto.setdefault("monto", monto)
        contexto.setdefault("capital", monto)
    try:
        red = plantillas_legales.redactar_con_plantilla(materia, contexto)
    except plantillas_legales.DatosPlantillaIncompletosError:
        # Faltan datos para la materia detectada: se degrada a la plantilla
        # genérica (solo requiere `resumen`) en lugar de romper el chat.
        materia = MateriaAcuerdo.GENERICA
        plantilla = plantillas_legales.obtener_plantilla(materia)
        red = plantillas_legales.redactar_con_plantilla(materia, contexto)
    texto = ("Borrador con fundamento en " + red["fundamento_legal"]
             + ":\n\n" + red["clausula_legal"]
             + "\n\nAdaptalo con datos reales en Generar acta.")
    return {"respuesta": texto, "intencion": "redactar",
            "acciones": [{"etiqueta": "Ir a generar acta", "accion": "ir_generar"}],
            "texto_borrador": red["clausula_legal"],
            "fundamento": red["fundamento_legal"], "materia": red["materia"],
            "titulo_sugerido": plantilla.titulo}


def _flujo_creacion(db, texto, sesion_id, autor, empresa=None, usuario=None):
    alcance = alcance_empresa(usuario)
    owner_id = getattr(usuario, "id", None)
    ses = (
        obtener_sesion(
            sesion_id,
            usuario_id=owner_id,
            empresa_codigo=alcance.codigo,
        )
        if sesion_id
        else None
    )
    if ses is not None:
        if (
            empresa
            and empresa.get("usar_info_empresa")
            and ses.get("etapa") not in ("confirmacion", "correccion")
        ):
            ses.setdefault("datos", {}).update({
                clave: valor for clave, valor in empresa.items() if valor not in (None, "")
            })
        if ses.get("etapa") == "confirmacion":
            if _es_confirmacion_creacion(texto):
                return _cerrar_y_generar(db, ses, autor)
            campo = _campo_para_cambiar(texto, ses)
            if campo and any(
                palabra in _norm(texto)
                for palabra in ("cambiar", "corregir", "editar", "modificar")
            ):
                ses["etapa"] = "correccion"
                ses["campo_edicion"] = campo["clave"]
                return _respuesta_sesion(
                    ses,
                    "De acuerdo. Proporciona el nuevo valor para %s.\n\n%s"
                    % (campo["etiqueta"], campo["pregunta"]),
                    campo,
                )
            return _respuesta_confirmacion_creacion(
                ses,
                "Para continuar, confirma el envío a revisión o indica qué dato deseas cambiar.",
            )
        if ses.get("etapa") == "correccion":
            clave = ses.get("campo_edicion")
            nuevos = extraer_datos(texto, clave)
            if not nuevos or clave not in nuevos:
                campo = next(
                    (
                        item
                        for item in campos_requeridos_para_sesion(ses)
                        if item["clave"] == clave
                    ),
                    None,
                )
                return _respuesta_sesion(
                    ses,
                    "No pude identificar ese valor. %s"
                    % (campo["pregunta"] if campo else "Intenta de nuevo."),
                    campo,
                )
            if clave == "tipo_sociedad" and not acta_aplicable(
                nuevos["tipo_sociedad"], ses.get("tipo_asamblea") or "ordinaria"
            ):
                campo = next(
                    item
                    for item in campos_requeridos_para_sesion(ses)
                    if item["clave"] == clave
                )
                return _respuesta_sesion(
                    ses,
                    "Ese tipo societario no permite el acta seleccionada. Proporciona otro tipo de sociedad compatible.",
                    campo,
                )
            ses["datos"].update(nuevos)
            ses.setdefault("respuestas", []).append({
                "campo": clave,
                "pregunta": "¿Qué valor debe usarse para %s?" % clave.replace("_", " "),
                "respuesta": texto,
            })
            ses.pop("campo_edicion", None)
            ses["etapa"] = "confirmacion"
            return _respuesta_confirmacion_creacion(
                ses, "Dato actualizado. Revisa el resumen antes de confirmar el envío."
            )
        # Si aún no hay tipo (venía del catálogo), el mensaje es la elección.
        if not ses.get("tipo_asamblea"):
            if _solicita_catalogo_completo(texto):
                return _respuesta_catalogo(ses, completo=True)
            elegido = detectar_tipo_en_texto(texto)
            if elegido:
                ses["tipo_asamblea"] = elegido
                ses["etapa"] = "datos"
                ses.setdefault("respuestas", []).append({
                    "campo": "tipo_asamblea",
                    "pregunta": "¿Qué tipo de acta quieres crear?",
                    "respuesta": texto,
                })
                etiqueta = etiqueta_tipo_asamblea(elegido)
                falt = siguiente_faltante(ses)
                return _respuesta_sesion(ses, "Perfecto, creamos %s paso a paso.\n\n%s"
                                         % (etiqueta, falt["pregunta"]), falt)
            return _respuesta_catalogo(ses)
        nuevo = detectar_tipo_en_texto(texto)
        if nuevo and len((texto or "").strip()) < 40:
            ses["tipo_asamblea"] = nuevo
            ses["etapa"] = "datos"
        falt = siguiente_faltante(ses)
        if falt is not None:
            nuevos = extraer_datos(texto, falt["clave"])
            if nuevos:
                if falt["clave"] == "tipo_sociedad" and not acta_aplicable(
                    nuevos["tipo_sociedad"], ses.get("tipo_asamblea") or "ordinaria"
                ):
                    return _respuesta_sesion(
                        ses,
                        "Ese tipo societario no permite el acta seleccionada en el catálogo jurídico. "
                        "Elige otro tipo de sociedad compatible o cancela para seleccionar otra acta.",
                        falt,
                    )
                ses["datos"].update(nuevos)
                ses.setdefault("respuestas", []).append({
                    "campo": falt["clave"],
                    "pregunta": falt["pregunta"],
                    "respuesta": texto,
                })
                falt2 = siguiente_faltante(ses)
                if falt2 is None:
                    ses["etapa"] = "confirmacion"
                    return _respuesta_confirmacion_creacion(
                        ses,
                        "Ya reuní la información necesaria. Revisa el resumen y confirma antes de enviar el acta a revisión.",
                    )
                etiqueta = etiqueta_tipo_asamblea(ses.get("tipo_asamblea") or "")
                return _respuesta_sesion(ses, "Anotado. Seguimos con %s.\n\n%s"
                                         % (etiqueta, falt2["pregunta"]), falt2)
            return _respuesta_sesion(ses, "No entendi ese dato para %s. %s Ejemplo: %s"
                                     % (falt["etiqueta"], falt["pregunta"], falt.get("ejemplo", "")), falt)
        if siguiente_faltante(ses) is None:
            ses["etapa"] = "confirmacion"
            return _respuesta_confirmacion_creacion(ses)
        return _respuesta_sesion(ses, texto)
    tipo = detectar_tipo_en_texto(texto)
    if tipo is None:
        # No sabe qué acta crear (o no dijo el tipo) -> catálogo con descripciones.
        ses2 = crear_sesion(
            None, usuario_id=owner_id, empresa_codigo=alcance.codigo
        )
        if empresa and empresa.get("usar_info_empresa"):
            ses2["datos"].update({
                clave: valor for clave, valor in empresa.items() if valor not in (None, "")
            })
        return _respuesta_catalogo(ses2, completo=_solicita_catalogo_completo(texto))
    ses3 = crear_sesion(
        tipo or "ordinaria",
        usuario_id=owner_id,
        empresa_codigo=alcance.codigo,
    )
    ses3.setdefault("respuestas", []).append({
        "campo": "tipo_asamblea",
        "pregunta": "¿Qué tipo de acta quieres crear?",
        "respuesta": texto,
    })
    if empresa and empresa.get("usar_info_empresa"):
        ses3["datos"].update({
            clave: valor for clave, valor in empresa.items() if valor not in (None, "")
        })
    etiqueta = etiqueta_tipo_asamblea(tipo or "ordinaria")
    falt = siguiente_faltante(ses3)
    return _respuesta_sesion(ses3, "Creamos %s paso a paso. Sesion %s.\n\n%s"
                             % (etiqueta, ses3["sesion_id"], falt["pregunta"]), falt)


def procesar_mensaje(db: Session, mensaje: str, folio: Optional[str] = None,
                      acta_id: Optional[int] = None, sesion_id: Optional[str] = None,
                      autor: Optional[str] = None, usuario=None, empresa=None,
                      modo: str = "general") -> Dict[str, Any]:
    texto = (mensaje or "").strip()
    alcance = alcance_empresa(usuario)
    if modo == "edicion":
        return _procesar_edicion(db, texto, acta_id, sesion_id, usuario)
    if _es_cancelacion_creacion(texto):
        reiniciar_sesion(
            sesion_id,
            usuario_id=getattr(usuario, "id", None),
            empresa_codigo=alcance.codigo,
        )
        return {
            "respuesta": "Creación cancelada. Cuando quieras empezar de nuevo, escribe «Quiero un acta».",
            "intencion": "cancelar_creacion",
            "tema_valido": True,
        }
    if empresa is None and detectar_intencion(texto) == "crear":
        return {
            "respuesta": "No se ha asignado empresa",
            "intencion": "crear",
            "tema_valido": True,
        }
    # Sesión de creación en curso (incluye catálogo->elección de tipo).
    if sesion_id and obtener_sesion(
        sesion_id,
        usuario_id=getattr(usuario, "id", None),
        empresa_codigo=alcance.codigo,
    ) is not None:
        autor_efectivo = (usuario.email if usuario is not None else None) or autor
        return _flujo_creacion(
            db, texto, sesion_id, autor_efectivo, empresa, usuario
        )
    if not es_tema_valido(texto):
        return {"respuesta": MENSAJE_FUERA, "intencion": "fuera_de_tema",
                "tema_valido": False,
                "acciones": [{"etiqueta": "Ver ayuda", "accion": "ayuda"}]}
    inten = detectar_intencion(texto)
    if inten in ("crear", "catalogo_tipos", "cancelar_creacion"):
        if inten == "cancelar_creacion":
            if sesion_id:
                reiniciar_sesion(
                    sesion_id,
                    usuario_id=getattr(usuario, "id", None),
                    empresa_codigo=alcance.codigo,
                )
            return {"respuesta": "Creación cancelada. Dime «Quiero crear un acta» cuando quieras empezar.",
                    "intencion": "cancelar_creacion", "tema_valido": True}
        autor_efectivo = (usuario.email if usuario is not None else None) or autor
        return _flujo_creacion(
            db, texto, sesion_id, autor_efectivo, empresa, usuario
        )
    fol = folio or extraer_folio(texto)
    aid = acta_id if acta_id is not None else extraer_id(texto)
    if inten == "ayuda":
        return {"respuesta": texto_ayuda(), "intencion": "ayuda",
                "tema_valido": True,
                "acciones": [{"etiqueta": "Ver resumen", "accion": "resumen"}]}
    if inten == "resumen":
        r = administracion.resumen_administracion(db, alcance)
        lin = ["Total actas: %s (versiones: %s)." % (r["total_actas"], r["total_versiones"]),
               "Por estatus:"]
        lin += ["  - %s: %s" % (k, v) for k, v in r["por_estatus"].items()]
        v = r["vigencia"]
        lin.append("Vigencia: %s vigentes, %s por vencer, %s vencidas, %s sin fecha."
                   % (v["vigentes"], v["por_vencer"], v["vencidas"], v["sin_fecha"]))
        if v["vencidas"]:
            venc = administracion.actas_por_vigencia(
                db, estado="vencida", limite=5, alcance=alcance
            )
            lin.append("Vencidas: " + "; ".join(_linea(a) for a in venc))
        return {"respuesta": "\n".join(lin), "intencion": "resumen",
                "tema_valido": True, "resumen": r,
                "acciones": [{"etiqueta": "Ver administracion", "accion": "ir_admin"}]}
    if inten == "tiempos":
        return _resumen_tiempos(db, alcance, usuario, texto)
    if inten == "redactar" and fol is None and aid is None:
        out = _redactar_libre(texto)
        out["tema_valido"] = True
        return out
    acta = _buscar(db, fol, aid, usuario)
    if acta is None:
        if fol or aid:
            ref = fol or ("id %s" % aid)
            return {"respuesta": ("No encontre el acta " + str(ref) + ". Verifica el folio "
                                  "PGAC-AAAA-0001 o el id. Pideme el resumen general."),
                    "intencion": inten, "tema_valido": True,
                    "acciones": [{"etiqueta": "Ver resumen", "accion": "resumen"}]}
        if inten == "redactar":
            out = _redactar_libre(texto)
            out["tema_valido"] = True
            return out
        return {"respuesta": ("De que acta hablamos? Dame el folio (PGAC-2026-0001) "
                              "o el id (acta 1)."),
                "intencion": inten, "tema_valido": True, "requiere_acta": True,
                "acciones": [{"etiqueta": "Ver resumen", "accion": "resumen"}]}
    dato = _dato_acta(acta)
    if inten == "editar":
        return {
            "respuesta": (
                f"Encontré {acta.folio}. Al abrir el editor podrás revisar los datos originales "
                "recopilados por el asistente y pedirle cambios antes de guardar una nueva versión."
            ),
            "intencion": "editar",
            "tema_valido": True,
            "acta": dato,
            "acciones": [{
                "etiqueta": "Abrir edición asistida",
                "accion": "editar_acta",
                "acta_id": acta.id,
            }],
        }
    if inten == "estatus":
        resp = ("El acta " + _linea(acta) + ". Titulo: "
                + str(acta.titulo or "(sin titulo)") + ". Acuerdos: "
                + str(len(acta.acuerdos or [])) + ".")
        return {"respuesta": resp, "intencion": "estatus", "tema_valido": True,
                "acta": dato,
                "acciones": [{"etiqueta": "Validar", "accion": "validar", "acta_id": acta.id},
                             {"etiqueta": "Versiones", "accion": "versiones", "acta_id": acta.id}]}
    if inten == "validar":
        val = validar_acta_almacenada(db, acta.id)
        crit = sum(1 for h in val.hallazgos if str(h.severidad) == "critico")
        adv = sum(1 for h in val.hallazgos if str(h.severidad) == "advertencia")
        resp = ("Validacion de %s: puntaje %s/100. %s Criticos: %s. Advertencias: %s."
                % (acta.folio, val.puntaje, val.consistencia, crit, adv))
        for h in val.hallazgos[:5]:
            resp += "\n- [%s] %s" % (h.severidad, h.mensaje)
            if h.sugerencia:
                resp += " Sugerencia: " + h.sugerencia
        return {"respuesta": resp, "intencion": "validar", "tema_valido": True,
                "acta": _dato_acta(acta), "validacion": val.model_dump(mode="json"),
                "acciones": [{"etiqueta": "Versiones", "accion": "versiones", "acta_id": acta.id}],
                "_evento_auditoria": {
                    "accion": "validar",
                    "entidad": "actas",
                    "entidad_id": acta.id,
                    "datos_despues": {"puntaje_validacion": val.puntaje},
                }}
    if inten == "aprobar":
        if not (
            usuario is not None
            and security.tiene_nivel_minimo(usuario.rol, "abogado_responsable")
        ):
            return {
                "respuesta": "Tu rol no permite cambiar el estatus de actas.",
                "intencion": "aprobar",
                "tema_valido": True,
                "acta": _dato_acta(acta),
            }
        destino = extraer_estatus_destino(texto)
        origen = str(getattr(acta.estatus, "value", acta.estatus))
        if destino is None:
            return {"respuesta": ("El acta %s esta en %s. A que estatus la paso? "
                                  "Opciones: en_revision, aprobada, firmada, archivada."
                                  % (acta.folio, origen)),
                    "intencion": "aprobar", "tema_valido": True, "acta": dato,
                    "acciones": [{"etiqueta": "Pasar a revision", "accion": "aprobar",
                                  "acta_id": acta.id, "estatus": "en_revision"}]}
        if destino == "en_revision" and acta.estado_flujo == "revision":
            return {
                "respuesta": f"El acta {acta.folio} ya está en la bandeja del Revisor.",
                "intencion": "aprobar",
                "tema_valido": True,
                "acta": dato,
            }
        if destino in ("en_revision", "aprobada", "borrador"):
            if destino == "aprobada":
                val = validar_acta_almacenada(db, acta.id)
                criticos = [h for h in val.hallazgos if str(h.severidad) == "critico"]
                if criticos:
                    return {
                        "respuesta": (
                            "No puedo aprobar esta acta: tiene hallazgos críticos. "
                            + "; ".join(h.mensaje for h in criticos)[:400]
                        ),
                        "intencion": "aprobar",
                        "tema_valido": True,
                        "acta": _dato_acta(acta),
                        "validacion": val.model_dump(mode="json"),
                    }
            return {
                "respuesta": (
                    "Las decisiones de revisión y aprobación deben hacerse desde las bandejas "
                    "«Revisión de actas» o «Aprobación de actas» para conservar el flujo y la bitácora."
                ),
                "intencion": "aprobar",
                "tema_valido": True,
                "acta": dato,
            }
        if acta.estado_flujo != "aprobada":
            return {
                "respuesta": (
                    "El PDF y los cambios de cierre solo están disponibles después de la "
                    "aprobación final del Abogado."
                ),
                "intencion": "aprobar",
                "tema_valido": True,
                "acta": dato,
            }
        if not _puede_avanzar(origen, destino):
            return {"respuesta": ("No puedo retroceder %s de %s a %s. El flujo solo avanza: %s."
                                  % (acta.folio, origen, destino, " > ".join(ORDEN_ESTATUS))),
                    "intencion": "aprobar", "tema_valido": True, "acta": dato}
        if destino in ("aprobada", "firmada", "archivada"):
            val = validar_acta_almacenada(db, acta.id)
            crit = [h for h in val.hallazgos if str(h.severidad) == "critico"]
            if crit:
                det = "; ".join(h.mensaje for h in crit)[:400]
                return {"respuesta": ("No puedo pasar %s a %s: tiene %s hallazgo(s) critico(s). "
                                      "Corrige: %s" % (acta.folio, destino, len(crit), det)),
                        "intencion": "aprobar", "tema_valido": True,
                        "acta": _dato_acta(acta), "validacion": val.model_dump(mode="json")}
        acta2 = actualizar_estatus(db, acta.id, destino)
        administracion.registrar_version(db, acta2, "Estatus a %s desde asistente" % destino)
        db.commit()
        db.refresh(acta2)
        return {"respuesta": ("Listo: %s ahora esta en %s (version %s)."
                              % (acta2.folio, destino, acta2.version)),
                "intencion": "aprobar", "tema_valido": True, "acta": _dato_acta(acta2),
                "acciones": [{"etiqueta": "Validar", "accion": "validar", "acta_id": acta2.id}],
                "_evento_auditoria": {
                    "accion": "cambiar_estatus",
                    "entidad": "actas",
                    "entidad_id": acta2.id,
                    "datos_antes": {"estatus": origen},
                    "datos_despues": {
                        "estatus": destino,
                        "version": acta2.version,
                    },
                }}
    if inten == "versiones":
        hist = administracion.listar_versiones(db, acta.id)
        lin = ["Historial de %s (%s versiones):" % (acta.folio, len(hist))]
        for v in hist[:8]:
            lin.append("  - v%s: %s [%s]" % (v.version, v.motivo, v.estatus))
        return {"respuesta": "\n".join(lin), "intencion": "versiones",
                "tema_valido": True, "acta": dato,
                "versiones": [{"version": v.version, "motivo": v.motivo,
                               "estatus": v.estatus} for v in hist],
                "acciones": [{"etiqueta": "Validar", "accion": "validar", "acta_id": acta.id}]}
    if inten == "restaurar":
        num = extraer_num_version(texto)
        if num is None:
            return {"respuesta": ("Que version restauro? Ejemplo: restaura %s a la version 1."
                                  % acta.folio),
                    "intencion": "restaurar", "tema_valido": True, "acta": dato}
        if not (usuario is not None and security.tiene_nivel_minimo(usuario.rol, "abogado_responsable")):
            return {"respuesta": "Tu rol no permite restaurar versiones.",
                    "intencion": "restaurar", "tema_valido": True, "acta": dato}
        version_actual = int(acta.version or 1)
        try:
            acta2 = administracion.restaurar_version(db, acta.id, num)
        except Exception as exc:
            return {"respuesta": "No pude restaurar: %s" % exc,
                    "intencion": "restaurar", "tema_valido": True, "acta": dato}
        return {"respuesta": ("Restaurada la version %s de %s: ahora es la version %s."
                              % (num, acta2.folio, acta2.version)),
                "intencion": "restaurar", "tema_valido": True, "acta": _dato_acta(acta2),
                "_evento_auditoria": {
                    "accion": "restaurar_version",
                    "entidad": "actas",
                    "entidad_id": acta2.id,
                    "datos_antes": {"version": version_actual},
                    "datos_despues": {
                        "version_restaurada": num,
                        "version": acta2.version,
                    },
                }}
    out = _redactar_libre(texto)
    out["tema_valido"] = True
    out["acta"] = dato
    return out


