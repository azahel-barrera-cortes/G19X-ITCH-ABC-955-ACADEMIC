"""Endpoints del módulo de actas corporativas.

Se exponen dos rutas principales:

* ``POST /api/v1/actas/redactar``      -> borrador con IA + validación (JSON).
* ``POST /api/v1/actas/generar-pdf``   -> redacción + persistencia + PDF binario.

El resto del recurso cubre el CRUD del historial, la regeneración del PDF y la
validación de consistencia de actas ya guardadas.
"""

from __future__ import annotations

import io
import json
from typing import Any, Iterator, List, Mapping, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.catalogos import catalogos as obtener_catalogos_dominio
from app.core.config import settings
from app.db.session import get_db
from app.schemas.acta import (
    ActaActualizarRequest,
    ActaGenerarPdfRequest,
    ActaRead,
    ActaRedaccionRequest,
    ActaRedaccionResponse,
    ActaResumen,
    ApiMensaje,
    CatalogosResponse,
    ValidacionActa,
)
from app.services import acta_service
from app.services.ai_service import crear_servicio_ia

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
def redactar_stream(payload: ActaRedaccionRequest) -> StreamingResponse:
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
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Solicita la redacción a la IA, compila el PDF con ReportLab y lo retorna."""
    pdf, metadatos = acta_service.generar_pdf(payload, db)
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
    db: Session = Depends(get_db),
) -> ActaRead:
    """Persiste el acta aplicando la redacción asistida configurada."""
    borrador = acta_service.redactar(payload)
    modelo = acta_service.crear_acta(db, payload, borrador)
    return ActaRead.model_validate(modelo)


@router.get(
    "",
    response_model=List[ActaResumen],
    summary="Listar el historial de actas con filtros",
)
def listar_actas(
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
    )
    return [ActaResumen.model_validate(acta) for acta in actas]

# ---------------------------------------------------------------------------
# Consulta y mantenimiento de un acta concreta
# ---------------------------------------------------------------------------
@router.get("/{acta_id}", response_model=ActaRead, summary="Obtener un acta por identificador")
def obtener_acta(acta_id: int, db: Session = Depends(get_db)) -> ActaRead:
    """Devuelve el acta completa, incluidas sus cláusulas y su validación."""
    return ActaRead.model_validate(acta_service.obtener_acta(db, acta_id))


@router.put(
    "/{acta_id}",
    response_model=ActaRead,
    summary="Reemplazar el contenido de un acta e incrementar su versión",
)
def actualizar_acta(
    acta_id: int,
    payload: ActaActualizarRequest,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Actualiza el acta según la semántica de PUT (reemplazo completo).

    Con ``regenerar_con_ia=true`` se vuelve a redactar con el proveedor de IA
    configurado; en caso contrario se reutilizan las cláusulas ya guardadas y solo
    se completan con plantillas locales las que falten.
    """
    modelo = acta_service.actualizar_acta(db, acta_id, payload)
    return ActaRead.model_validate(modelo)


@router.patch(
    "/{acta_id}/estatus",
    response_model=ActaRead,
    summary="Cambiar el estatus del acta (borrador, revisión, aprobada, firmada, archivada)",
)
def actualizar_estatus(
    acta_id: int,
    estatus: str = Query(..., description="Nuevo estatus del acta"),
    db: Session = Depends(get_db),
) -> ActaRead:
    """Avanza el acta dentro de su ciclo de vida documental."""
    return ActaRead.model_validate(acta_service.actualizar_estatus(db, acta_id, estatus))


@router.get(
    "/{acta_id}/pdf",
    summary="Descargar nuevamente el PDF de un acta almacenada",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}}},
)
def descargar_pdf(
    acta_id: int,
    incluir_tabla_asistentes: bool = Query(True),
    incluir_hoja_firmas: bool = Query(True),
    incluir_anexo_validacion: bool = Query(False),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Regenera el documento desde la base de datos, sin invocar a la IA."""
    acta = acta_service.obtener_acta(db, acta_id)
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
def validar_acta(acta_id: int, db: Session = Depends(get_db)) -> ValidacionActa:
    """Ejecuta la validación (IA + reglas) y guarda el resultado en el acta."""
    return acta_service.validar_acta_almacenada(db, acta_id)


@router.delete("/{acta_id}", response_model=ApiMensaje, summary="Eliminar un acta")
def eliminar_acta(acta_id: int, db: Session = Depends(get_db)) -> ApiMensaje:
    """Borra el acta del historial y confirma el folio eliminado."""
    folio = acta_service.eliminar_acta(db, acta_id)
    return ApiMensaje(mensaje=f"El acta {folio} fue eliminada.", detalle=None)


