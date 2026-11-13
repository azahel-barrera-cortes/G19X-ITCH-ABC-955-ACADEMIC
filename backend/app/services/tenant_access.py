"""Helpers de alcance por empresa para actas y datos relacionados."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import false, select
from sqlalchemy.orm import Session

from app.models.acta import Acta
from app.models.usuario import Usuario


@dataclass(frozen=True)
class AlcanceEmpresa:
    """Alcance de consulta derivado del usuario autenticado."""

    codigo: str | None
    global_: bool = False


def alcance_empresa(usuario: Usuario | None) -> AlcanceEmpresa:
    if usuario is None:
        return AlcanceEmpresa(codigo=None)
    if usuario.rol == "SuperAdministrador":
        return AlcanceEmpresa(codigo=None, global_=True)
    codigo = (
        usuario.codigo_empresa
        if usuario.rol == "Administrador"
        else usuario.empresa_codigo
    )
    return AlcanceEmpresa(codigo=codigo or None)


def filtrar_por_empresa(consulta: Any, alcance: AlcanceEmpresa, columna: Any) -> Any:
    """Aplica filtro fail-closed; solo SuperAdministrador tiene alcance global."""
    if alcance.global_:
        return consulta
    if not alcance.codigo:
        return consulta.where(false())
    return consulta.where(columna == alcance.codigo)


def obtener_acta_autorizada(
    db: Session, acta_id: int, usuario: Usuario
) -> Acta:
    """Obtiene un acta del tenant actual; oculta IDs ajenos como no encontrados."""
    consulta = filtrar_por_empresa(
        select(Acta).where(Acta.id == acta_id),
        alcance_empresa(usuario),
        Acta.empresa_codigo,
    )
    acta = db.scalar(consulta)
    if acta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un acta con el identificador {acta_id}.",
        )
    return acta
