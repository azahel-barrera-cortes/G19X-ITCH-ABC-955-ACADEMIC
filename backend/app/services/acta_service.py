"""Orquestación del ciclo de vida del acta (servicio de aplicación).

Coordina los tres servicios especializados sin mezclar responsabilidades:

* ``ai_service``      -> redacción del texto legal y validación de consistencia.
* ``pdf_generator``   -> maquetado determinista del PDF con ReportLab.
* ``acta_service``    -> composición de las cláusulas del documento, persistencia
  en base de datos y armado del diccionario que consume el generador de PDF.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import formato
from app.core.catalogos import (
    CARACTERES_ASISTENTE,
    articulo_quorum,
    etiqueta_mayoria,
    etiqueta_tipo_asamblea,
)
from app.core.config import Settings, settings
from app.core.exceptions import ActaNoEncontradaError, DatosActaInvalidosError
from app.models.acta import Acta
from app.models.enums import EstatusActa, ProveedorIA, TipoAsamblea
from app.schemas.acta import (
    Acuerdo,
    ActaActualizarRequest,
    ActaBase,
    ActaGenerarPdfRequest,
    ActaRead,
    ActaRedaccionRequest,
    ActaRedaccionResponse,
    ActaResumen,
    ValidacionActa,
)
from app.services import plantillas_legales as plantillas
from app.services.ai_service import AIService, crear_servicio_ia
from app.services.administracion import registrar_version
from app.services.pdf_generator import build_acta_pdf, nombre_archivo_acta

logger = logging.getLogger(__name__)

PREFIJO_FOLIO = "PGAC"

# Orden de las claves de las cláusulas fijas del acta.
CLAVES_FIJAS = (
    "encabezado",
    "declaracion_quorum",
    "declaracion_instalacion",
    "cierre",
    "declaracion_protocolizacion",
)


# ---------------------------------------------------------------------------
# Etiquetas y descripciones para el documento
# ---------------------------------------------------------------------------
def etiqueta_caracter(valor: Any) -> str:
    """Etiqueta legible del carácter del asistente."""
    for item in CARACTERES_ASISTENTE:
        if item["valor"] == str(valor):
            return str(item["etiqueta"])
    return str(valor or "").replace("_", " ").capitalize()


def titulo_documento(payload: ActaBase) -> str:
    """Encabezado del documento, p. ej. ``ACTA DE ASAMBLEA GENERAL EXTRAORDINARIA``."""
    etiqueta = etiqueta_tipo_asamblea(payload.tipo_asamblea)
    if str(payload.tipo_asamblea) == TipoAsamblea.SESION_CONSEJO.value:
        return etiqueta.upper()
    return f"ACTA DE {etiqueta.upper()}"


def descripcion_convocatoria(payload: ActaBase) -> str:
    """Texto de la convocatoria para el cuadro de datos generales."""
    partes: List[str] = []
    if payload.convocatoria_quien:
        partes.append(f"Convocada por {payload.convocatoria_quien}")
    if payload.convocatoria_medio:
        partes.append(f"mediante {payload.convocatoria_medio}")
    if payload.convocatoria_fecha:
        partes.append(f"de fecha {formato.fecha_larga(payload.convocatoria_fecha)}")
    if not partes:
        return "Sin convocatoria registrada"
    return ", ".join(partes)


def descripcion_votacion(votacion: Any) -> str:
    """Resumen textual del resultado de la votación de un acuerdo."""
    if not votacion:
        return "No se registró votación expresa."
    resultado = "Aprobado" if votacion.aprobado else "No aprobado"
    detalle = (
        f"A favor: {formato.acciones(votacion.acciones_a_favor)}; "
        f"en contra: {formato.acciones(votacion.acciones_en_contra)}; "
        f"abstenciones: {formato.acciones(votacion.abstenciones)}"
    )
    comentario = f" Comentario: {votacion.comentario}" if votacion.comentario else ""
    return f"{resultado}. {detalle}.{comentario}"


def generar_folio(db: Session, fecha: Optional[date] = None) -> str:
    """Folio consecutivo por año con el formato ``PGAC-AAAA-0001``."""
    anio = (fecha or date.today()).year
    prefijo = f"{PREFIJO_FOLIO}-{anio}-"
    total = db.scalar(select(func.count(Acta.id)).where(Acta.folio.like(f"{prefijo}%"))) or 0
    return f"{prefijo}{total + 1:04d}"

# ---------------------------------------------------------------------------
# Redacción y composición del documento
# ---------------------------------------------------------------------------
def componer_clausulas(acta: ActaBase, acuerdos: Sequence[Acuerdo]) -> Dict[str, str]:
    """Compone las cláusulas fijas del acta y el texto legal consolidado."""
    contexto = {
        "lugar": acta.lugar,
        "hora": formato.hora_larga(acta.hora),
        "fecha_larga": formato.fecha_con_dia(acta.fecha),
        "sociedad": acta.sociedad,
        "tipo_asamblea_texto": etiqueta_tipo_asamblea(acta.tipo_asamblea),
        "quien_convoca": acta.convocatoria_quien or "el órgano de administración",
        "medio_convocatoria": acta.convocatoria_medio or "convocatoria escrita",
        "fecha_convocatoria": formato.fecha_larga(acta.convocatoria_fecha),
        "acciones_presentes": formato.acciones(acta.capital_presente or acta.acciones_totales),
        "quorum": formato.porcentaje(acta.quorum_porcentaje),
        "articulo_quorum": articulo_quorum(str(acta.tipo_asamblea)),
    }

    clausulas = {
        clave: plantillas.formatear(plantillas.TEXTOS_FIJOS[clave], contexto)
        for clave in CLAVES_FIJAS
        if clave in plantillas.TEXTOS_FIJOS
    }

    # Texto legal consolidado: se usa en la vista previa del frontend y como
    # respaldo del expediente electrónico del acta.
    bloques: List[str] = [
        clausulas.get("encabezado", ""),
        clausulas.get("declaracion_quorum", ""),
        clausulas.get("declaracion_instalacion", ""),
    ]
    for acuerdo in acuerdos:
        bloques.append(f"ACUERDO {acuerdo.numero}. {acuerdo.titulo}")
        bloques.append(acuerdo.clausula_legal or acuerdo.resumen)
        if acuerdo.fundamento_legal:
            bloques.append(f"Fundamento legal: {acuerdo.fundamento_legal}")
    bloques.extend([clausulas.get("cierre", ""), clausulas.get("declaracion_protocolizacion", "")])

    clausulas["cuerpo"] = "\n".join(bloque for bloque in bloques if bloque and bloque.strip())
    return clausulas


def redactar(payload: ActaRedaccionRequest, ia: Optional[AIService] = None) -> Dict[str, Any]:
    """Ejecuta la redacción asistida (y la validación) y devuelve el borrador.

    El diccionario resultante contiene ``acuerdos``, ``clausulas``, ``texto_legal``,
    ``validacion``, ``proveedor``, ``ia_habilitada`` y ``advertencias``.
    """
    servicio = ia or crear_servicio_ia()

    acuerdos: List[Acuerdo] = list(payload.acuerdos)
    if payload.generar_clausulas:
        acuerdos = servicio.redactar_acuerdos(payload, payload.instrucciones_adicionales)

    clausulas = componer_clausulas(payload, acuerdos)

    validacion: Optional[ValidacionActa] = None
    if payload.incluir_validacion:
        # La validación debe analizar los acuerdos YA redactados (con cláusula y
        # fundamento), de lo contrario reportaría faltantes inexistentes.
        acta_validada = payload.model_copy(update={"acuerdos": acuerdos})
        validacion = servicio.validar_acta(acta_validada, clausulas)

    return {
        "acuerdos": acuerdos,
        "clausulas": clausulas,
        "texto_legal": clausulas.get("cuerpo", ""),
        "validacion": validacion,
        "proveedor": servicio.proveedor,
        "ia_habilitada": servicio.ia_habilitada,
        "advertencias": list(servicio.advertencias),
    }

def construir_documento(
    payload: ActaGenerarPdfRequest,
    *,
    folio: str,
    acuerdos: Sequence[Acuerdo],
    clausulas: Mapping[str, str],
    validacion: Optional[ValidacionActa] = None,
    meta: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Arma el diccionario de datos que consume :func:`build_acta_pdf`."""
    version = int((meta or {}).get("version", 1))
    estatus = str((meta or {}).get("estatus", EstatusActa.BORRADOR.value))
    proveedor = str((meta or {}).get("proveedor_ia", ProveedorIA.PLANTILLAS.value))

    asistentes = [
        {
            "nombre": asistente.nombre,
            "caracter": etiqueta_caracter(asistente.caracter),
            "cargo": asistente.cargo,
            "acciones": formato.acciones(asistente.acciones),
            "porcentaje": (
                formato.porcentaje(asistente.porcentaje_capital)
                if asistente.porcentaje_capital is not None
                else "—"
            ),
            "firma": asistente.firma,
        }
        for asistente in payload.asistentes
    ]

    acuerdos_documento = [
        {
            "numero": acuerdo.numero,
            "titulo": acuerdo.titulo,
            "resumen": acuerdo.resumen,
            "clausula_legal": acuerdo.clausula_legal,
            "fundamento_legal": acuerdo.fundamento_legal,
            "materia": acuerdo.materia,
            "mayoria_texto": (
                etiqueta_mayoria(acuerdo.votacion.tipo_mayoria)
                if acuerdo.votacion
                else "No registrada"
            ),
            "votacion_texto": descripcion_votacion(acuerdo.votacion),
            "aprobado": bool(acuerdo.votacion.aprobado) if acuerdo.votacion else True,
        }
        for acuerdo in acuerdos
    ]

    return {
        "folio": folio,
        "sociedad": payload.sociedad,
        "rfc_sociedad": payload.rfc_sociedad,
        "tipo_asamblea_texto": etiqueta_tipo_asamblea(payload.tipo_asamblea),
        "titulo_documento": titulo_documento(payload),
        "subtitulo_documento": (
            f"Celebrada el {formato.fecha_con_dia(payload.fecha)} en {payload.lugar} · "
            f"Acta {folio} · versión {version} · estatus {estatus}"
        ),
        "fecha_texto": formato.fecha_con_dia(payload.fecha),
        "hora_texto": formato.hora_larga(payload.hora),
        "lugar": payload.lugar,
        "convocatoria_texto": descripcion_convocatoria(payload),
        "capital_social_texto": formato.moneda(payload.capital_social),
        "capital_presente_texto": formato.moneda(payload.capital_presente),
        "acciones_totales_texto": formato.acciones(payload.acciones_totales),
        "quorum_texto": formato.porcentaje(payload.quorum_porcentaje),
        "presidente": payload.presidente,
        "secretario": payload.secretario,
        "asistentes": asistentes,
        "orden_del_dia": [
            {"numero": punto.numero, "titulo": punto.titulo, "descripcion": punto.descripcion}
            for punto in payload.orden_del_dia
        ],
        "acuerdos": acuerdos_documento,
        "clausulas": dict(clausulas),
        "observaciones": payload.observaciones,
        "validacion": validacion.model_dump(mode="json") if validacion else None,
        "opciones": {
            "incluir_tabla_asistentes": payload.incluir_tabla_asistentes,
            "incluir_hoja_firmas": payload.incluir_hoja_firmas,
            "incluir_anexo_validacion": payload.incluir_anexo_validacion,
            "numerar_paginas": settings.incluir_numeracion_paginas,
        },
        "meta": {
            "generado_en": formato.marca_tiempo(),
            "version": version,
            "estatus": estatus,
            "proveedor_ia": proveedor,
        },
        "pie_confidencialidad": settings.pie_confidencialidad,
        "margen_cm": settings.margen_cm,
    }

# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------
def _valor(valor: Any) -> Any:
    """Valor literal de un enum (o el propio valor si ya es una cadena)."""
    return getattr(valor, "value", valor)


def _volcar_payload(
    modelo: Acta,
    payload: ActaBase,
    borrador: Mapping[str, Any],
    *,
    incluir_estatus: bool = True,
) -> None:
    """Copia los datos del formulario y el borrador redactado al modelo ORM."""
    modelo.sociedad = payload.sociedad
    modelo.rfc_sociedad = payload.rfc_sociedad
    modelo.tipo_asamblea = _valor(payload.tipo_asamblea)
    modelo.titulo = payload.titulo
    modelo.fecha = payload.fecha
    modelo.hora = payload.hora
    modelo.lugar = payload.lugar
    modelo.convocatoria_fecha = payload.convocatoria_fecha
    modelo.convocatoria_medio = payload.convocatoria_medio
    modelo.convocatoria_quien = payload.convocatoria_quien
    modelo.capital_social = payload.capital_social
    modelo.acciones_totales = payload.acciones_totales
    modelo.capital_presente = payload.capital_presente
    modelo.quorum_porcentaje = payload.quorum_porcentaje
    modelo.presidente = payload.presidente
    modelo.secretario = payload.secretario

    modelo.asistentes = [asistente.model_dump(mode="json") for asistente in payload.asistentes]
    modelo.orden_del_dia = [punto.model_dump(mode="json") for punto in payload.orden_del_dia]
    modelo.acuerdos = [acuerdo.model_dump(mode="json") for acuerdo in borrador["acuerdos"]]
    modelo.clausulas = dict(borrador["clausulas"])
    modelo.texto_legal = str(borrador["texto_legal"])
    modelo.observaciones = payload.observaciones

    validacion = borrador.get("validacion")
    modelo.validacion_ia = validacion.model_dump(mode="json") if validacion else None
    modelo.proveedor_ia = str(_valor(borrador["proveedor"]))
    # Autor: si el payload trae creado_por (flujo asistente) se conserva;
    # listo para que mañana sea el usuario autenticado.
    creado_por = getattr(payload, "creado_por", None)
    if creado_por:
        modelo.creado_por = str(creado_por)[:150]

    if incluir_estatus:
        modelo.estatus = str(_valor(payload.estatus))


def crear_acta(db: Session, payload: ActaBase, borrador: Mapping[str, Any]) -> Acta:
    """Inserta el acta con folio consecutivo, reintentando ante colisiones."""
    for intento in range(3):
        modelo = Acta(folio=generar_folio(db, payload.fecha), version=1)
        _volcar_payload(modelo, payload, borrador)
        db.add(modelo)
        try:
            db.commit()
        except IntegrityError:  # folio tomado por otra transacción simultánea
            db.rollback()
            logger.warning("Folio duplicado al crear el acta; reintento %d/3", intento + 1)
            continue
        db.refresh(modelo)
        registrar_version(db, modelo, "Creación del acta")
        db.commit()
        db.refresh(modelo)
        logger.info("Acta %s creada (id=%s)", modelo.folio, modelo.id)
        return modelo
    raise RuntimeError("No fue posible asignar un folio único al acta.")


def contar_paginas(pdf: bytes) -> int:
    """Cuenta las páginas del PDF generado mediante sus objetos ``/Type /Page``."""
    return max(1, len(re.findall(rb"/Type\s*/Page(?![s])", pdf)))

# ---------------------------------------------------------------------------
# Flujo principal: redactar -> (persistir) -> compilar PDF
# ---------------------------------------------------------------------------
def generar_pdf(
    payload: ActaGenerarPdfRequest,
    db: Session,
    ia: Optional[AIService] = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """Redacta el acta, opcionalmente la guarda y compila su PDF.

    Devuelve ``(pdf_bytes, metadatos)``. Los metadatos se publican como
    encabezados HTTP en ``POST /api/v1/actas/generar-pdf``.
    """
    borrador = redactar(payload, ia)
    acta: Optional[Acta] = None
    version = 1
    estatus = str(_valor(payload.estatus))

    if payload.actualizar_acta_id:
        # Regeneración sobre un acta existente: incrementa versión y pasa a revisión.
        acta = obtener_acta(db, payload.actualizar_acta_id)
        _volcar_payload(acta, payload, borrador, incluir_estatus=False)
        acta.version = int(acta.version or 1) + 1
        if _valor(acta.estatus) == EstatusActa.BORRADOR.value:
            acta.estatus = EstatusActa.EN_REVISION.value
        registrar_version(db, acta, "Regeneración del documento (PDF)")
        db.commit()
        db.refresh(acta)
        folio, version, estatus = acta.folio, int(acta.version), str(_valor(acta.estatus))
    elif payload.guardar:
        acta = crear_acta(db, payload, borrador)
        folio, version, estatus = acta.folio, int(acta.version), str(_valor(acta.estatus))
    else:
        # Borrador sin persistir: se propone el folio siguiente de la serie.
        folio = generar_folio(db, payload.fecha)

    documento = construir_documento(
        payload,
        folio=folio,
        acuerdos=borrador["acuerdos"],
        clausulas=borrador["clausulas"],
        validacion=borrador["validacion"],
        meta={
            "version": version,
            "estatus": estatus,
            "proveedor_ia": str(_valor(borrador["proveedor"])),
        },
    )
    pdf = build_acta_pdf(documento)

    validacion = borrador["validacion"]
    metadatos: Dict[str, Any] = {
        "folio": folio,
        "acta_id": getattr(acta, "id", None),
        "version": version,
        "nombre_archivo": nombre_archivo_acta(
            folio, payload.sociedad, formato.fecha_iso(payload.fecha)
        ),
        "bytes": len(pdf),
        "paginas": contar_paginas(pdf),
        "proveedor_ia": str(_valor(borrador["proveedor"])),
        "puntaje_validacion": validacion.puntaje if validacion else None,
        "guardada": acta is not None,
        "ia_habilitada": bool(borrador["ia_habilitada"]),
        "advertencias": borrador["advertencias"],
    }
    return pdf, metadatos


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------
def obtener_acta(db: Session, acta_id: int) -> Acta:
    """Recupera un acta por su identificador o lanza :class:`ActaNoEncontradaError`."""
    acta = db.get(Acta, acta_id)
    if acta is None:
        raise ActaNoEncontradaError(f"No existe un acta con el identificador {acta_id}.")
    return acta


def listar_actas(
    db: Session,
    *,
    sociedad: Optional[str] = None,
    tipo_asamblea: Optional[str] = None,
    estatus: Optional[str] = None,
    texto: Optional[str] = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> List[Acta]:
    """Lista actas con filtros opcionales y paginación simple."""
    consulta = select(Acta).order_by(Acta.fecha.desc(), Acta.id.desc())

    if sociedad:
        consulta = consulta.where(Acta.sociedad.ilike(f"%{sociedad.strip()}%"))
    if tipo_asamblea:
        consulta = consulta.where(Acta.tipo_asamblea == tipo_asamblea)
    if estatus:
        consulta = consulta.where(Acta.estatus == estatus)
    if texto:
        patron = f"%{texto.strip()}%"
        consulta = consulta.where(
            or_(Acta.folio.ilike(patron), Acta.sociedad.ilike(patron), Acta.titulo.ilike(patron))
        )

    return list(db.scalars(consulta.limit(max(1, min(limite, 200))).offset(max(0, desplazamiento))))

# ---------------------------------------------------------------------------
# Regeneración de PDF y actualización de actas existentes
# ---------------------------------------------------------------------------
def payload_desde_acta(
    acta: Acta, opciones: Optional[Mapping[str, Any]] = None
) -> ActaGenerarPdfRequest:
    """Reconstruye la petición de PDF a partir de un acta almacenada."""
    opciones = opciones or {}
    return ActaGenerarPdfRequest(
        sociedad=acta.sociedad,
        rfc_sociedad=acta.rfc_sociedad,
        tipo_asamblea=str(_valor(acta.tipo_asamblea)),
        titulo=acta.titulo,
        fecha=acta.fecha,
        hora=acta.hora,
        lugar=acta.lugar,
        convocatoria_fecha=acta.convocatoria_fecha,
        convocatoria_medio=acta.convocatoria_medio,
        convocatoria_quien=acta.convocatoria_quien,
        capital_social=acta.capital_social,
        acciones_totales=acta.acciones_totales,
        capital_presente=acta.capital_presente,
        quorum_porcentaje=acta.quorum_porcentaje,
        presidente=acta.presidente,
        secretario=acta.secretario,
        asistentes=list(acta.asistentes or []),
        orden_del_dia=list(acta.orden_del_dia or []),
        acuerdos=list(acta.acuerdos or []),
        observaciones=acta.observaciones,
        estatus=str(_valor(acta.estatus)),
        # Sin IA ni persistencia: se reutiliza exactamente el contenido guardado.
        generar_clausulas=False,
        incluir_validacion=False,
        guardar=False,
        incluir_tabla_asistentes=bool(opciones.get("incluir_tabla_asistentes", True)),
        incluir_hoja_firmas=bool(opciones.get("incluir_hoja_firmas", True)),
        incluir_anexo_validacion=bool(opciones.get("incluir_anexo_validacion", False)),
    )


def pdf_de_acta(
    acta: Acta, opciones: Optional[Mapping[str, Any]] = None
) -> Tuple[bytes, Dict[str, Any]]:
    """Regenera el PDF de un acta almacenada sin volver a invocar a la IA."""
    payload = payload_desde_acta(acta, opciones)
    acuerdos = [Acuerdo(**datos) for datos in (acta.acuerdos or [])]
    clausulas = dict(acta.clausulas or {})
    if not clausulas:
        clausulas = componer_clausulas(payload, acuerdos)

    validacion = ValidacionActa(**acta.validacion_ia) if acta.validacion_ia else None
    documento = construir_documento(
        payload,
        folio=acta.folio,
        acuerdos=acuerdos,
        clausulas=clausulas,
        validacion=validacion,
        meta={
            "version": int(acta.version or 1),
            "estatus": str(_valor(acta.estatus)),
            "proveedor_ia": acta.proveedor_ia or ProveedorIA.PLANTILLAS.value,
        },
    )
    pdf = build_acta_pdf(documento)

    metadatos: Dict[str, Any] = {
        "folio": acta.folio,
        "acta_id": acta.id,
        "version": int(acta.version or 1),
        "nombre_archivo": nombre_archivo_acta(
            acta.folio, acta.sociedad, formato.fecha_iso(acta.fecha)
        ),
        "bytes": len(pdf),
        "paginas": contar_paginas(pdf),
        "proveedor_ia": acta.proveedor_ia or ProveedorIA.PLANTILLAS.value,
        "puntaje_validacion": validacion.puntaje if validacion else None,
        "guardada": True,
        "ia_habilitada": False,
        "advertencias": [],
    }
    return pdf, metadatos

def _borrador_local(
    payload: ActaBase, clausulas_previas: Mapping[int, Mapping[str, Any]]
) -> Dict[str, Any]:
    """Completa las cláusulas faltantes con plantillas locales (sin IA).

    Reutiliza la redacción guardada de cada acuerdo (por número) y solo genera
    texto nuevo para los acuerdos que lleguen sin cláusula.
    """
    servicio = crear_servicio_ia(Settings(ai_provider=ProveedorIA.PLANTILLAS.value))
    acuerdos: List[Acuerdo] = []

    for acuerdo in payload.acuerdos:
        if not (acuerdo.clausula_legal or "").strip():
            previo = clausulas_previas.get(acuerdo.numero)
            if previo and previo.get("clausula_legal"):
                acuerdo = acuerdo.model_copy(
                    update={
                        "materia": previo.get("materia") or acuerdo.materia,
                        "clausula_legal": previo.get("clausula_legal"),
                        "fundamento_legal": previo.get("fundamento_legal"),
                    }
                )
            else:
                materia = acuerdo.materia or plantillas.detectar_materia(
                    f"{acuerdo.titulo} {acuerdo.resumen}", payload.tipo_asamblea
                )
                contexto = servicio.construir_contexto(payload, acuerdo)
                redaccion = plantillas.redactar_con_plantilla(materia, contexto)
                acuerdo = acuerdo.model_copy(
                    update={
                        "materia": redaccion["materia"],
                        "clausula_legal": redaccion["clausula_legal"],
                        "fundamento_legal": redaccion["fundamento_legal"],
                    }
                )
        acuerdos.append(acuerdo)

    clausulas = componer_clausulas(payload, acuerdos)
    return {
        "acuerdos": acuerdos,
        "clausulas": clausulas,
        "texto_legal": clausulas.get("cuerpo", ""),
        "validacion": servicio.validar_acta(payload, clausulas),
        "proveedor": ProveedorIA.PLANTILLAS,
        "ia_habilitada": False,
        "advertencias": [],
    }


def actualizar_acta(
    db: Session,
    acta_id: int,
    payload: ActaActualizarRequest,
    ia: Optional[AIService] = None,
) -> Acta:
    """Reemplaza el contenido del acta (PUT) e incrementa su versión."""
    acta = obtener_acta(db, acta_id)

    if payload.regenerar_con_ia:
        solicitud = ActaRedaccionRequest(
            **payload.model_dump(exclude={"regenerar_con_ia", "motivo_cambio"})
        )
        borrador = redactar(solicitud, ia)
    else:
        previas = {
            int(datos.get("numero", 0)): datos for datos in (acta.acuerdos or [])
        }
        borrador = _borrador_local(payload, previas)

    # El estatus solo cambia si el cliente lo envió expresamente en el PUT.
    _volcar_payload(
        acta,
        payload,
        borrador,
        incluir_estatus="estatus" in payload.model_fields_set,
    )
    acta.version = int(acta.version or 1) + 1
    registrar_version(
        db,
        acta,
        payload.motivo_cambio or "Actualización del contenido del acta",
    )
    db.commit()
    db.refresh(acta)
    logger.info("Acta %s actualizada a la versión %s", acta.folio, acta.version)
    return acta

def eliminar_acta(db: Session, acta_id: int) -> str:
    """Elimina el acta y devuelve el folio borrado (para el mensaje de respuesta)."""
    acta = obtener_acta(db, acta_id)
    folio = acta.folio
    db.delete(acta)
    db.commit()
    logger.info("Acta %s eliminada", folio)
    return folio


def actualizar_estatus(db: Session, acta_id: int, estatus: str) -> Acta:
    """Cambia el estatus del acta dentro de su ciclo de vida."""
    acta = obtener_acta(db, acta_id)
    try:
        nuevo = EstatusActa(_valor(estatus))
    except ValueError as exc:
        permitidos = ", ".join(item.value for item in EstatusActa)
        raise DatosActaInvalidosError(
            f"El estatus «{estatus}» no es válido.", detalle=f"Valores permitidos: {permitidos}."
        ) from exc

    acta.estatus = nuevo.value
    db.commit()
    db.refresh(acta)
    return acta


def validar_acta_almacenada(
    db: Session, acta_id: int, ia: Optional[AIService] = None
) -> ValidacionActa:
    """Vuelve a validar un acta almacenada y guarda el resultado en ella."""
    acta = obtener_acta(db, acta_id)
    servicio = ia or crear_servicio_ia()
    validacion = servicio.validar_acta(payload_desde_acta(acta), dict(acta.clausulas or {}))
    acta.validacion_ia = validacion.model_dump(mode="json")
    db.commit()
    db.refresh(acta)
    return validacion


def respuesta_redaccion(
    db: Session, payload: ActaRedaccionRequest, ia: Optional[AIService] = None
) -> ActaRedaccionResponse:
    """Ejecuta la redacción asistida y arma la respuesta del endpoint de borrador."""
    borrador = redactar(payload, ia)
    return ActaRedaccionResponse(
        folio=generar_folio(db, payload.fecha),
        sociedad=payload.sociedad,
        tipo_asamblea=str(_valor(payload.tipo_asamblea)),
        clausulas=borrador["clausulas"],
        acuerdos=borrador["acuerdos"],
        texto_legal=borrador["texto_legal"],
        validacion=borrador["validacion"],
        proveedor_ia=str(_valor(borrador["proveedor"])),
        ia_habilitada=bool(borrador["ia_habilitada"]),
        advertencias=borrador["advertencias"],
    )







