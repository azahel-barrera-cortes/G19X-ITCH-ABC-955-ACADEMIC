"""Endpoint de exportación a expediente ZIP.

Genera un archivo ZIP que contiene el PDF del acta y sus metadatos,
listo para ser entregado al expediente corporativo o a una notaría.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import RequiereCapturista, UsuarioActual, get_db, registrar_bitacora
from app.db.session import get_db
from app.models.acta import Acta
from app.services import acta_service

router = APIRouter(prefix="/expediente", tags=["Expediente ZIP"])


@router.get(
    "/{acta_id}/zip",
    summary="Exportar el expediente de un acta como ZIP (PDF + metadatos JSON).",
)
def exportar_expediente_zip(
    usuario_actual: RequiereCapturista,
    acta_id: int,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Crea un ZIP con el PDF del acta y un fichero de metadatos JSON."""
    acta = db.query(Acta).filter(Acta.id == acta_id).first()
    if not acta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Acta {acta_id} no encontrada.",
        )

    # Registrar en la bitácora de cambios.
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="exportar_zip",
        entidad="actas",
        entidad_id=acta_id,
        datos_despues={"folio": acta.folio, "sociedad": acta.sociedad},
    )

    # Generar el PDF del acta.
    pdf_bytes, metadatos = acta_service.pdf_de_acta(
        acta,
        {
            "incluir_tabla_asistentes": True,
            "incluir_hoja_firmas": True,
            "incluir_anexo_validacion": False,
        },
    )

    # Construir metadatos JSON del expediente.
    metadatos_expediente = {
        "exportado_en": datetime.now(timezone.utc).isoformat(),
        "exportado_por": {
            "id": usuario_actual.id,
            "email": usuario_actual.email,
            "rol": usuario_actual.rol,
        },
        "acta": {
            "id": acta.id,
            "folio": acta.folio,
            "version": acta.version,
            "sociedad": acta.sociedad,
            "rfc_sociedad": acta.rfc_sociedad,
            "tipo_sociedad": acta.tipo_sociedad,
            "tipo_asamblea": str(acta.tipo_asamblea),
            "titulo": acta.titulo,
            "fecha": str(acta.fecha),
            "lugar": acta.lugar,
            "estatus": acta.estatus,
            "creado_por": acta.creado_por,
            "created_at": str(acta.created_at) if acta.created_at else None,
            "updated_at": str(acta.updated_at) if acta.updated_at else None,
        },
        "pdf": {
            "nombre_archivo": metadatos.get("nombre_archivo", "acta.pdf"),
            "tamaño_bytes": len(pdf_bytes),
            "paginas": metadatos.get("paginas", 1),
            "proveedor_ia": str(metadatos.get("proveedor_ia", "plantillas")),
        },
    }

    # Empaquetar en ZIP en memoria.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(metadatos["nombre_archivo"], pdf_bytes)
        zf.writestr(
            "metadatos.json",
            __import__("json").dumps(metadatos_expediente, indent=2, ensure_ascii=False),
        )
    buffer.seek(0)

    nombre_zip = f"expediente_{acta.folio.replace('/', '_')}.zip"
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_zip}"',
            "X-Expediente-Folio": acta.folio,
        },
    )