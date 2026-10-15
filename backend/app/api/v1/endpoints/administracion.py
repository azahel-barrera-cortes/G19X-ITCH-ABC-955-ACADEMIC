"""Endpoints de administración de actas (versiones y caducidad).

Se publican bajo ``/api/v1/administracion`` en un router propio, separado de
``/actas`` para no colisionar con ``GET /actas/{acta_id}`` (que interpretaría
cualquier segmento como un identificador numérico).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.acta import (
    ActaRead,
    CaducidadRequest,
    ResumenAdministracion,
    VersionActaDetalle,
    VersionActaResumen,
    VigenciaActa,
)
from app.services import acta_service, administracion

router = APIRouter(prefix="/administracion", tags=["Administración"])


# ---------------------------------------------------------------------------
# Visión global
# ---------------------------------------------------------------------------
@router.get(
    "/resumen",
    response_model=ResumenAdministracion,
    summary="Estadísticas globales: actas, versiones y estado de vigencia",
)
def resumen(db: Session = Depends(get_db)) -> ResumenAdministracion:
    """Totales por estatus y clasificación de caducidad de todo el repositorio."""
    return ResumenAdministracion(**administracion.resumen_administracion(db))


@router.get(
    "/vigencia",
    response_model=List[VigenciaActa],
    summary="Actas clasificadas por vigencia (vencidas primero)",
)
def por_vigencia(
    estado: Optional[str] = Query(
        None,
        description="Filtro: vencida | por_vencer | vigente | sin_fecha",
    ),
    limite: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[VigenciaActa]:
    """Lista las actas ordenadas por prioridad de atención: vencidas al inicio."""
    actas = administracion.actas_por_vigencia(db, estado=estado, limite=limite)
    return [VigenciaActa.model_validate(acta) for acta in actas]


# ---------------------------------------------------------------------------
# Historial de versiones
# ---------------------------------------------------------------------------
@router.get(
    "/versiones/{acta_id}",
    response_model=List[VersionActaResumen],
    summary="Historial de versiones de un acta (más reciente primero)",
)
def listar_versiones(acta_id: int, db: Session = Depends(get_db)) -> List[VersionActaResumen]:
    """Devuelve el listado de instantáneas registradas para el acta indicado."""
    return [
        VersionActaResumen.model_validate(version)
        for version in administracion.listar_versiones(db, acta_id)
    ]


@router.get(
    "/versiones/{acta_id}/{numero}",
    response_model=VersionActaDetalle,
    summary="Contenido completo de una versión concreta",
)
def detalle_version(
    acta_id: int, numero: int, db: Session = Depends(get_db)
) -> VersionActaDetalle:
    """Recupera el retrato completo del acta tal como quedó en esa versión."""
    version = administracion.obtener_version(db, acta_id, numero)
    acta = acta_service.obtener_acta(db, acta_id)
    # Se construye un dict explícito: `version.__dict__` incluye el estado interno
    # de SQLAlchemy (`_sa_instance_state`), que Pydantic no puede serializar.
    return VersionActaDetalle(
        id=version.id,
        acta_id=version.acta_id,
        version=version.version,
        motivo=version.motivo,
        estatus=version.estatus,
        created_at=version.created_at,
        contenido=version.contenido or {},
        vigente=int(acta.version or 1) == int(version.version),
    )


@router.post(
    "/versiones/{acta_id}/{numero}/restaurar",
    response_model=ActaRead,
    summary="Restaurar una versión anterior (genera una versión nueva)",
)
def restaurar(
    acta_id: int, numero: int, db: Session = Depends(get_db)
) -> ActaRead:
    """Copia el contenido de la versión indicada sobre el acta actual.

    El historial nunca retrocede: al restaurar se emite una versión nueva con el
    contenido recuperado, de modo que la auditoría completa queda intacta.
    """
    acta = administracion.restaurar_version(db, acta_id, numero)
    return ActaRead.model_validate(acta)


# ---------------------------------------------------------------------------
# Caducidad
# ---------------------------------------------------------------------------
@router.put(
    "/caducidad/{acta_id}",
    response_model=ActaRead,
    summary="Fijar, ampliar o quitar la fecha de caducidad de un acta",
)
def fijar_caducidad(
    acta_id: int,
    payload: CaducidadRequest,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Actualiza la vigencia del acta y registra el cambio como nueva versión.

    Enviar ``fecha_caducidad`` vacío elimina el plazo (el acta queda sin
    caducidad) y deja constancia del motivo en el historial.
    """
    acta = administracion.fijar_caducidad(
        db, acta_id, payload.fecha_caducidad, payload.motivo
    )
    return ActaRead.model_validate(acta)