"""Endpoints de la bitácora de cambios (auditoría)."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import RequiereRevisor, get_db
from app.models.usuario import BitacoraCambios
from app.schemas.usuario import BitacoraCambiosRespuesta
from app.services.tenant_access import alcance_empresa, filtrar_por_empresa

router = APIRouter(prefix="/bitacora", tags=["Bitácora de cambios"])


@router.get(
    "",
    response_model=List[BitacoraCambiosRespuesta],
    summary="Listar entradas de la bitácora de cambios (revisor+).",
)
def listar_bitacora(
    usuario_actual: RequiereRevisor,
    db: Session = Depends(get_db),
    accion: Optional[str] = Query(None, description="Filtrar por acción (crear, actualizar, eliminar)"),
    entidad: Optional[str] = Query(None, description="Filtrar por entidad (actas, usuarios)"),
    limite: int = Query(100, ge=1, le=500),
    desplazamiento: int = Query(0, ge=0),
) -> List[BitacoraCambiosRespuesta]:
    """Lista las entradas de la bitácora con filtros opcionales."""
    consulta = db.query(BitacoraCambios)
    consulta = filtrar_por_empresa(
        consulta, alcance_empresa(usuario_actual), BitacoraCambios.empresa_codigo
    )
    if accion:
        consulta = consulta.filter(BitacoraCambios.accion == accion)
    if entidad:
        consulta = consulta.filter(BitacoraCambios.entidad == entidad)
    resultados = (
        consulta.order_by(BitacoraCambios.created_at.desc())
        .offset(desplazamiento)
        .limit(limite)
        .all()
    )
    return [BitacoraCambiosRespuesta.model_validate(r) for r in resultados]


@router.get(
    "/{entrada_id}",
    response_model=BitacoraCambiosRespuesta,
    summary="Obtener una entrada concreta de la bitácora.",
)
def obtener_entrada(
    usuario_actual: RequiereRevisor,
    entrada_id: int,
    db: Session = Depends(get_db),
) -> BitacoraCambiosRespuesta:
    """Devuelve una entrada de auditoría por su identificador."""
    consulta = db.query(BitacoraCambios).filter(BitacoraCambios.id == entrada_id)
    consulta = filtrar_por_empresa(
        consulta, alcance_empresa(usuario_actual), BitacoraCambios.empresa_codigo
    )
    entrada = consulta.first()
    if not entrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entrada de bitácora {entrada_id} no encontrada.",
        )
    return BitacoraCambiosRespuesta.model_validate(entrada)