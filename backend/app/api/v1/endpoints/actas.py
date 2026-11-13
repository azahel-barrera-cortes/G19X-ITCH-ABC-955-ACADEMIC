"""Endpoints del módulo de actas corporativas.

Se exponen dos rutas principales:

* ``POST /api/v1/actas/redactar``      -> borrador con IA + validación (JSON).
* ``POST /api/v1/actas/generar-pdf``   -> vista previa no persistida.

El resto del recurso cubre el flujo de revisión, el historial y el PDF final
disponible después de la aprobación legal.
"""

from __future__ import annotations

import io
import json
from typing import Any, Iterator, List, Mapping, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import (
    RequiereAbogado,
    RequiereAdmin,
    RequiereCapturista,
    RequiereRevisor,
    UsuarioActual,
    get_db,
    registrar_bitacora,
)
from app.core import security
from app.core.catalogos import catalogos as obtener_catalogos_dominio
from app.core.config import settings
from app.db.session import get_db
from app.models.acta import Acta
from app.models.enums import EstatusActa
from app.schemas.acta import (
    ActaActualizarRequest,
    ActaGenerarPdfRequest,
    ActaRead,
    AnalisisRevisionActa,
    ActaRedaccionRequest,
    ActaRedaccionResponse,
    ActaResumen,
    ApiMensaje,
    CatalogosResponse,
    DecisionFlujoRequest,
    ValidacionActa,
)
from app.services import acta_service
from app.services.ai_service import crear_servicio_ia
from app.services.tenant_access import (
    alcance_empresa,
    obtener_acta_autorizada,
)

router = APIRouter(prefix="/actas", tags=["Actas"])

ENCABEZADOS_EXPUESTOS = [
    "Content-Disposition",
    "X-Acta-Folio",
    "X-Acta-Id",
    "X-Acta-Version",
    "X-Acta-Paginas",
    "X-Acta-Guardada",
    "X-IA-Proveedor",
    "X-IA-Habilitada",
    "X-IA-Advertencias",
    "X-Validacion-Puntaje",
]


def _ascii(valor: Any) -> str:
    """Convierte un texto a ASCII seguro para encabezados HTTP."""
    return str(valor or "").encode("ascii", "ignore").decode("ascii")


def _respuesta_pdf(pdf: bytes, metadatos: Mapping[str, Any]) -> StreamingResponse:
    """Empaqueta los bytes del PDF con las cabeceras de trazabilidad del acta."""
    nombre = str(metadatos.get("nombre_archivo") or "acta.pdf")
    encabezados = {
        "Content-Disposition": (
            f'attachment; filename="{_ascii(nombre)}"; ' f"filename*=UTF-8''{quote(nombre, safe='')}"
        ),
        "Content-Length": str(len(pdf)),
        "X-Acta-Folio": _ascii(metadatos.get("folio")),
        "X-Acta-Id": _ascii(metadatos.get("acta_id")),
        "X-Acta-Version": _ascii(metadatos.get("version", 1)),
        "X-Acta-Paginas": _ascii(metadatos.get("paginas", 1)),
        "X-Acta-Guardada": "true" if metadatos.get("guardada") else "false",
        "X-IA-Proveedor": _ascii(metadatos.get("proveedor_ia") or "plantillas"),
        "X-IA-Habilitada": "true" if metadatos.get("ia_habilitada") else "false",
        "X-Validacion-Puntaje": _ascii(metadatos.get("puntaje_validacion")),
    }
    advertencias = metadatos.get("advertencias") or []
    if advertencias:
        encabezados["X-IA-Advertencias"] = _ascii(" | ".join(str(a) for a in advertencias))[:400]

    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf", headers=encabezados)

# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------
@router.get(
    "/catalogos",
    response_model=CatalogosResponse,
    summary="Catálogos del formulario (tipos de asamblea, mayorías, caracteres y estatus)",
)
def obtener_catalogos() -> CatalogosResponse:
    """Devuelve las opciones con las que el frontend puebla el formulario."""
    datos = obtener_catalogos_dominio()
    proveedor = settings.proveedor_ia_configurado
    return CatalogosResponse(**datos, proveedor_ia=proveedor, ia_habilitada=proveedor != "plantillas")


def _evento_sse(evento: str, datos: Mapping[str, Any]) -> str:
    """Empaqueta un evento del flujo SSE en el formato que espera ``EventSource``."""
    return f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Redacción y generación
# ---------------------------------------------------------------------------
@router.post(
    "/redactar",
    response_model=ActaRedaccionResponse,
    summary="Generar borrador del acta con IA (sin persistir ni exportar)",
)
def redactar_acta(
    payload: ActaRedaccionRequest,
    _usuario: UsuarioActual,
    db: Session = Depends(get_db),
) -> ActaRedaccionResponse:
    """Redacta las cláusulas legales y valida la consistencia del acta."""
    return acta_service.respuesta_redaccion(db, payload)


@router.post(
    "/redactar-stream",
    summary="Redactar un acuerdo en vivo (SSE) para mostrar el texto mientras se genera",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Flujo de eventos con fragmentos de la cláusula y el resultado final.",
        }
    },
)
def redactar_stream(
    payload: ActaRedaccionRequest,
    _usuario: UsuarioActual,
) -> StreamingResponse:
    """Genera la cláusula del primer acuerdo y la transmite fragmento a fragmento.

    Es útil para que el usuario vea la redacción en curso en lugar de esperar a que
    termine. Si no hay proveedor de IA configurado se responde con un único evento
    ``error`` explicando que debe activarse un proveedor (o usar plantillas).
    """
    servicio = crear_servicio_ia()

    if not payload.acuerdos:
        return _evento_sse("error", {"mensaje": "El acta no contiene acuerdos que redactar."})

    acuerdo = payload.acuerdos[0]
    contexto = servicio.construir_contexto(payload, acuerdo)

    def generar() -> Iterator[str]:
        yield _evento_sse(
            "inicio",
            {
                "acuerdo": acuerdo.numero,
                "titulo": acuerdo.titulo,
                "proveedor": servicio.proveedor.value,
                "ia_habilitada": servicio.ia_habilitada,
            },
        )
        acumulado: List[str] = []
        try:
            for fragmento in servicio.transmitir_redaccion(acuerdo, contexto, payload.instrucciones_adicionales):
                acumulado.append(fragmento)
                yield _evento_sse("fragmento", {"texto": fragmento})
        except Exception as exc:  # pragma: no cover - red de seguridad del flujo
            yield _evento_sse("error", {"mensaje": f"Fallo al redactar: {exc}"})

        texto = "".join(acumulado).strip()
        if not texto:
            yield _evento_sse(
                "error",
                {
                    "mensaje": (
                        "No hay un proveedor de IA configurado. Define las credenciales "
                        "correspondientes en backend/.env (Azure OpenAI, Gemini o un endpoint "
                        "compatible con OpenAI) o deja que el sistema use las plantillas legales."
                    )
                },
            )
            return

        yield _evento_sse("fin", {"texto": texto, "proveedor": servicio.proveedor.value})

    return StreamingResponse(
        generar(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/generar-pdf",
    summary="Redactar y descargar el acta en PDF (endpoint principal)",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Archivo PDF del acta con el texto legal y la hoja de firmas.",
        }
    },
)
def generar_pdf(
    payload: ActaGenerarPdfRequest,
    usuario_actual: UsuarioActual,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Genera una vista previa no persistida; el PDF final se emite tras aprobar."""
    if payload.guardar or payload.actualizar_acta_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El PDF final solo puede generarse desde un acta aprobada por el Abogado.",
        )
    datos_antes = None
    pdf, metadatos = acta_service.generar_pdf(payload, db)
    if metadatos["guardada"]:
        registrar_bitacora(
            db,
            usuario=usuario_actual,
            accion="actualizar" if payload.actualizar_acta_id else "crear",
            entidad="actas",
            entidad_id=metadatos["acta_id"],
            datos_antes=datos_antes,
            datos_despues={
                "folio": metadatos["folio"],
                "version": metadatos["version"],
                "estatus": metadatos.get("estatus") or "desconocido",
                "proveedor_ia": metadatos["proveedor_ia"],
            },
        )
    else:
        registrar_bitacora(
            db,
            usuario=usuario_actual,
            accion="generar_con_ia",
            entidad="actas",
            datos_despues={
                "folio": metadatos["folio"],
                "proveedor_ia": metadatos["proveedor_ia"],
                "guardada": False,
            },
        )
    return _respuesta_pdf(pdf, metadatos)


# ---------------------------------------------------------------------------
# CRUD del historial
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=ActaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear y guardar un acta (sin descargar PDF)",
)
def crear_acta(
    payload: ActaGenerarPdfRequest,
    usuario_actual: RequiereCapturista,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Persiste el acta como pendiente de revisión, sin emitir el PDF final."""
    alcance = alcance_empresa(usuario_actual)
    if not alcance.global_ and not alcance.codigo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta no está vinculada a una empresa.",
        )
    solicitud = payload.model_copy(
        update={
            "creado_por": usuario_actual.email,
            "estatus": "en_revision",
        }
    )
    borrador = acta_service.redactar(solicitud)
    modelo = acta_service.crear_acta(
        db,
        solicitud,
        borrador,
        empresa_codigo=alcance.codigo,
    )
    modelo.estado_flujo = "revision"
    db.commit()
    db.refresh(modelo)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="crear",
        entidad="actas",
        entidad_id=modelo.id,
        datos_despues={
            "folio": modelo.folio,
            "sociedad": modelo.sociedad,
            "estado_flujo": modelo.estado_flujo,
        },
    )
    return ActaRead.model_validate(modelo)


@router.get(
    "",
    response_model=List[ActaResumen],
    summary="Listar el historial de actas con filtros",
)
def listar_actas(
    usuario_actual: RequiereRevisor,
    sociedad: Optional[str] = Query(None, description="Filtro parcial por razón social"),
    tipo_asamblea: Optional[str] = Query(None, description="Tipo de asamblea"),
    estatus: Optional[str] = Query(None, description="Estatus del ciclo de vida"),
    texto: Optional[str] = Query(None, description="Búsqueda por folio, sociedad o título"),
    limite: int = Query(50, ge=1, le=200, description="Registros por página"),
    desplazamiento: int = Query(0, ge=0, description="Registros a omitir"),
    db: Session = Depends(get_db),
) -> List[ActaResumen]:
    """Lista las actas almacenadas, de la más reciente a la más antigua."""
    actas = acta_service.listar_actas(
        db,
        sociedad=sociedad,
        tipo_asamblea=tipo_asamblea,
        estatus=estatus,
        texto=texto,
        limite=limite,
        desplazamiento=desplazamiento,
        alcance=alcance_empresa(usuario_actual),
    )
    return [ActaResumen.model_validate(acta) for acta in actas]

# ---------------------------------------------------------------------------
# Consulta y mantenimiento de un acta concreta
# ---------------------------------------------------------------------------
@router.get(
    "/bandeja",
    response_model=List[ActaRead],
    summary="Listar actas de la bandeja correspondiente al rol",
)
def listar_bandeja_actas(
    usuario_actual: UsuarioActual,
    db: Session = Depends(get_db),
) -> List[ActaRead]:
    """Devuelve solo actas propias o pendientes de la etapa del usuario."""
    actas = acta_service.listar_bandeja(
        db,
        rol=usuario_actual.rol,
        email=usuario_actual.email,
        alcance=alcance_empresa(usuario_actual),
    )
    return [ActaRead.model_validate(acta) for acta in actas]


@router.get("/{acta_id}", response_model=ActaRead, summary="Obtener un acta por identificador")
def obtener_acta(
    usuario_actual: UsuarioActual,
    acta_id: int,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Devuelve el acta a los revisores o a su Capturista autor."""
    acta = obtener_acta_autorizada(db, acta_id, usuario_actual)
    if (
        not security.tiene_nivel_minimo(usuario_actual.rol, "revisor")
        and acta.creado_por != usuario_actual.email
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes consultar actas que tú hayas creado.",
        )
    return ActaRead.model_validate(acta)


@router.put(
    "/{acta_id}",
    response_model=ActaRead,
    summary="Reemplazar el contenido de un acta e incrementar su versión",
)
def actualizar_acta(
    usuario_actual: RequiereCapturista,
    acta_id: int,
    payload: ActaActualizarRequest,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Actualiza el acta según la semántica de PUT (reemplazo completo).

    Con ``regenerar_con_ia=true`` se vuelve a redactar con el proveedor de IA
    configurado; en caso contrario se reutilizan las cláusulas ya guardadas y solo
    se completan con plantillas locales las que falten.
    """
    datos_antes = obtener_acta_autorizada(db, acta_id, usuario_actual)
    if usuario_actual.rol != "capturista":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el Capturista autor puede corregir el contenido del acta.",
        )
    if datos_antes.creado_por != usuario_actual.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes corregir actas que tú hayas creado.",
        )
    if datos_antes.estado_flujo != "con_errores":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El acta solo se puede editar cuando fue devuelta con errores.",
        )
    tipo_actual = getattr(datos_antes.tipo_asamblea, "value", datos_antes.tipo_asamblea)
    tipo_propuesto = getattr(payload.tipo_asamblea, "value", payload.tipo_asamblea)
    if payload.sociedad != datos_antes.sociedad or tipo_propuesto != tipo_actual:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede modificar el nombre de la sociedad ni el tipo del acta.",
        )
    modelo = acta_service.actualizar_acta(db, acta_id, payload)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="actualizar",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={
            "folio": datos_antes.folio,
            "sociedad": datos_antes.sociedad,
            "estatus": datos_antes.estatus,
            "version": datos_antes.version,
        },
        datos_despues={
            "folio": modelo.folio,
            "sociedad": modelo.sociedad,
            "estatus": modelo.estatus,
            "version": modelo.version,
        },
    )
    return ActaRead.model_validate(modelo)


@router.post(
    "/{acta_id}/decision",
    response_model=ActaRead,
    summary="Aprobar o devolver un acta según la etapa de revisión",
)
def decidir_acta(
    usuario_actual: UsuarioActual,
    acta_id: int,
    payload: DecisionFlujoRequest,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Registra la revisión del Revisor o la decisión final del Abogado."""
    acta = obtener_acta_autorizada(db, acta_id, usuario_actual)
    estado_anterior = acta.estado_flujo
    try:
        actualizada = acta_service.decidir_flujo(
            db,
            acta,
            rol=usuario_actual.rol,
            usuario=usuario_actual.email,
            accion=payload.accion,
            comentario=payload.comentario,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion=f"acta_{payload.accion}",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={"estado_flujo": estado_anterior},
        datos_despues={
            "estado_flujo": actualizada.estado_flujo,
            "comentario": payload.comentario,
            "version": actualizada.version,
        },
    )
    return ActaRead.model_validate(actualizada)


@router.post(
    "/{acta_id}/analizar-revision",
    response_model=AnalisisRevisionActa,
    summary="Analizar un acta y sus cambios para apoyar la revisión humana",
)
def analizar_revision_acta(
    usuario_actual: UsuarioActual,
    acta_id: int,
    db: Session = Depends(get_db),
) -> AnalisisRevisionActa:
    """Analiza el acta vigente sin modificar su contenido ni su etapa de flujo."""
    if usuario_actual.rol not in {"revisor", "abogado_responsable"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el Revisor o el Abogado Responsable pueden analizar un acta.",
        )

    acta = obtener_acta_autorizada(db, acta_id, usuario_actual)
    if usuario_actual.rol == "revisor" and acta.estado_flujo != "revision":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El análisis del Revisor solo está disponible durante la etapa de revisión.",
        )
    if usuario_actual.rol == "abogado_responsable" and acta.estado_flujo not in {
        "abogado",
        "aprobada",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El análisis del Abogado solo está disponible en su etapa o después de aprobar.",
        )

    resultado = acta_service.analizar_revision_acta_almacenada(db, acta_id)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="analizar_revision",
        entidad="actas",
        entidad_id=acta_id,
        datos_despues={
            "version_actual": resultado.version_actual,
            "version_comparada": resultado.version_comparada,
            "cambios_detectados": len(resultado.cambios),
            "generado_por_ia": resultado.validacion.generado_por_ia,
        },
    )
    return resultado


@router.post(
    "/{acta_id}/reenviar",
    response_model=ActaRead,
    summary="Enviar una corrección a la etapa que devolvió el acta",
)
def reenviar_acta(
    usuario_actual: RequiereCapturista,
    acta_id: int,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Permite al autor reenviar una corrección después de guardar su versión."""
    if usuario_actual.rol != "capturista":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el Capturista puede reenviar una corrección.",
        )
    acta = obtener_acta_autorizada(db, acta_id, usuario_actual)
    if acta.creado_por != usuario_actual.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes reenviar actas que tú hayas creado.",
        )
    estado_anterior = acta.estado_flujo
    try:
        actualizada = acta_service.reenviar_correccion(
            db, acta, usuario=usuario_actual.email
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="reenviar_revision",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={"estado_flujo": estado_anterior},
        datos_despues={
            "estado_flujo": actualizada.estado_flujo,
            "version": actualizada.version,
        },
    )
    return ActaRead.model_validate(actualizada)


@router.patch(
    "/{acta_id}/estatus",
    response_model=ActaRead,
    summary="Cambiar el estatus del acta (borrador, revisión, aprobada, firmada, archivada)",
)
def actualizar_estatus(
    usuario_actual: RequiereAbogado,
    acta_id: int,
    estatus: str = Query(..., description="Nuevo estatus del acta"),
    db: Session = Depends(get_db),
) -> ActaRead:
    """Registra solo los estados posteriores a la aprobación final."""
    if estatus not in {estado.value for estado in EstatusActa}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El estatus «{estatus}» no es válido.",
        )
    if estatus not in ("firmada", "archivada"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Las etapas de revisión y aprobación se gestionan desde sus bandejas.",
        )
    datos_antes = obtener_acta_autorizada(db, acta_id, usuario_actual)
    if datos_antes.estado_flujo != "aprobada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El acta requiere aprobación final antes de cambiar su estado de cierre.",
        )
    modelo = acta_service.actualizar_estatus(db, acta_id, estatus)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="cambiar_estatus",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={"estatus": datos_antes.estatus},
        datos_despues={"estatus": modelo.estatus},
    )
    return ActaRead.model_validate(modelo)


@router.get(
    "/{acta_id}/pdf",
    summary="Descargar nuevamente el PDF de un acta almacenada",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}}},
)
def descargar_pdf(
    usuario_actual: RequiereAbogado,
    acta_id: int,
    incluir_tabla_asistentes: bool = Query(True),
    incluir_hoja_firmas: bool = Query(True),
    incluir_anexo_validacion: bool = Query(False),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Regenera el documento desde la base de datos, sin invocar a la IA."""
    acta = obtener_acta_autorizada(db, acta_id, usuario_actual)
    if acta.estado_flujo != "aprobada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El PDF final estará disponible cuando el Abogado apruebe el acta.",
        )
    pdf, metadatos = acta_service.pdf_de_acta(
        acta,
        {
            "incluir_tabla_asistentes": incluir_tabla_asistentes,
            "incluir_hoja_firmas": incluir_hoja_firmas,
            "incluir_anexo_validacion": incluir_anexo_validacion,
        },
    )
    return _respuesta_pdf(pdf, metadatos)


@router.post(
    "/{acta_id}/validar",
    response_model=ValidacionActa,
    summary="Volver a validar la consistencia del acta",
)
def validar_acta(
    usuario_actual: RequiereAbogado,
    acta_id: int,
    db: Session = Depends(get_db),
) -> ValidacionActa:
    """Ejecuta la validación (IA + reglas) y guarda el resultado en el acta."""
    datos_antes = obtener_acta_autorizada(db, acta_id, usuario_actual)
    resultado = acta_service.validar_acta_almacenada(db, acta_id)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="validar",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={"estatus": datos_antes.estatus},
        datos_despues={
            "estatus": datos_antes.estatus,
            "puntaje_validacion": resultado.puntaje,
        },
    )
    return resultado


@router.delete("/{acta_id}", response_model=ApiMensaje, summary="Eliminar un acta")
def eliminar_acta(
    usuario_actual: RequiereAdmin,
    acta_id: int,
    db: Session = Depends(get_db),
) -> ApiMensaje:
    """Borra el acta del historial y confirma el folio eliminado."""
    datos_antes = obtener_acta_autorizada(db, acta_id, usuario_actual)
    folio = acta_service.eliminar_acta(db, acta_id)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="eliminar",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={"folio": datos_antes.folio, "sociedad": datos_antes.sociedad},
        empresa_codigo=datos_antes.empresa_codigo,
    )
    return ApiMensaje(mensaje=f"El acta {folio} fue eliminada.", detalle=None)


