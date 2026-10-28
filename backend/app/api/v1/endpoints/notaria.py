"""API de integración para notarías.

Endpoints de terceros que permiten a una notaría consultar, validar y
descargar actas corporativas generadas por PGAC, usando una clave de API
o un token JWT con rol de revisor o superior.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import RequiereRevisor, UsuarioActual, get_db, registrar_bitacora
from app.db.session import get_db
from app.models.acta import Acta
from app.schemas.acta import ActaResumen

router = APIRouter(prefix="/notaria", tags=["Integración Notaría"])


@router.get(
    "/actas",
    response_model=List[ActaResumen],
    summary="Listar actas disponibles para integración notarial (revisor+).",
)
def listar_actas_notaria(
    usuario_actual: RequiereRevisor,
    db: Session = Depends(get_db),
    sociedad: Optional[str] = Query(None, description="Filtrar por razón social"),
    estatus: Optional[str] = Query(None, description="Filtrar por estatus del acta"),
    limite: int = Query(50, ge=1, le=200),
    desplazamiento: int = Query(0, ge=0),
) -> List[ActaResumen]:
    """Devuelve un resumen de actas para consulta por una notaría."""
    from sqlalchemy import or_, select

    consulta = db.query(Acta)
    if sociedad:
        consulta = consulta.filter(Acta.sociedad.ilike(f"%{sociedad}%"))
    if estatus:
        consulta = consulta.filter(Acta.estatus == estatus)
    resultados = (
        consulta.order_by(Acta.created_at.desc())
        .offset(desplazamiento)
        .limit(limite)
        .all()
    )
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="consultar_notaria",
        entidad="actas",
        datos_despues={"filtros": {"sociedad": sociedad, "estatus": estatus}},
    )
    return [ActaResumen.model_validate(a) for a in resultados]


@router.get(
    "/actas/{acta_id}",
    summary="Obtener metadatos de un acta para validación notarial.",
)
def obtener_acta_notaria(
    usuario_actual: RequiereRevisor,
    acta_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Devuelve los metadatos públicos de un acta sin el contenido completo."""
    acta = db.query(Acta).filter(Acta.id == acta_id).first()
    if not acta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Acta {acta_id} no encontrada.",
        )
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="validar_notaria",
        entidad="actas",
        entidad_id=acta_id,
    )
    return {
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
        "firma_electronica": acta.firma_electronica,
        "usar_info_empresa": acta.usar_info_empresa,
    }