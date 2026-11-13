"""Endpoints de administración de actas (versiones y caducidad).

Se publican bajo ``/api/v1/administracion`` en un router propio, separado de
``/actas`` para no colisionar con ``GET /actas/{acta_id}`` (que interpretaría
cualquier segmento como un identificador numérico).

Control de acceso (RBAC): las consultas requieren rol ``revisor`` o superior y
las operaciones que modifican el documento (restaurar versión, fijar caducidad)
requieren ``capturista`` o superior, registrando el cambio en la bitácora.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import (
    RequiereCapturista,
    RequiereRevisor,
    RequiereSuperAdministrador,
    get_db,
    registrar_bitacora,
)
from app.db.session import get_db
from app.models.acta import Acta
from app.models.usuario import BitacoraCambios
from app.schemas.acta import (
    ActaRead,
    CaducidadRequest,
    ReasignarEmpresaActaRequest,
    ResumenAdministracion,
    VersionActaDetalle,
    VersionActaResumen,
    VigenciaActa,
)
from app.services import administracion
from app.services.tenant_access import alcance_empresa, obtener_acta_autorizada
from app.services.auth_service import obtener_administrador_empresa

router = APIRouter(prefix="/administracion", tags=["Administración"])


@router.patch(
    "/actas/{acta_id}/empresa",
    response_model=ActaRead,
    summary="Asignar un acta en cuarentena a una empresa (SuperAdministrador).",
)
def reasignar_empresa_acta(
    acta_id: int,
    payload: ReasignarEmpresaActaRequest,
    usuario_actual: RequiereSuperAdministrador,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Asigna explícitamente registros históricos sin empresa a un tenant activo."""
    administrador = obtener_administrador_empresa(db, payload.codigo_empresa)
    if administrador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una empresa activa con ese código.",
        )
    acta = db.query(Acta).filter(
        Acta.id == acta_id,
        Acta.empresa_codigo.is_(None),
    ).first()
    if acta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un acta en cuarentena con ese identificador.",
        )

    acta.empresa_codigo = administrador.codigo_empresa
    db.query(BitacoraCambios).filter(
        BitacoraCambios.entidad == "actas",
        BitacoraCambios.entidad_id == acta_id,
        BitacoraCambios.empresa_codigo.is_(None),
    ).update(
        {"empresa_codigo": administrador.codigo_empresa},
        synchronize_session=False,
    )
    db.commit()
    db.refresh(acta)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="reasignar_empresa",
        entidad="actas",
        entidad_id=acta_id,
        datos_antes={"empresa_codigo": None},
        datos_despues={"empresa_codigo": administrador.codigo_empresa},
        empresa_codigo=administrador.codigo_empresa,
    )
    return ActaRead.model_validate(acta)


# ---------------------------------------------------------------------------
# Visión global
# ---------------------------------------------------------------------------
@router.get(
    "/resumen",
    response_model=ResumenAdministracion,
    summary="Estadísticas globales: actas, versiones y estado de vigencia",
)
def resumen(
    usuario_actual: RequiereRevisor,
    db: Session = Depends(get_db),
) -> ResumenAdministracion:
    """Totales por estatus y clasificación de caducidad de todo el repositorio."""
    return ResumenAdministracion(
        **administracion.resumen_administracion(db, alcance_empresa(usuario_actual))
    )


@router.get(
    "/vigencia",
    response_model=List[VigenciaActa],
    summary="Actas clasificadas por vigencia (vencidas primero)",
)
def por_vigencia(
    usuario_actual: RequiereRevisor,
    estado: Optional[str] = Query(
        None,
        description="Filtro: vencida | por_vencer | vigente | sin_fecha",
    ),
    limite: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[VigenciaActa]:
    """Lista las actas ordenadas por prioridad de atención: vencidas al inicio."""
    actas = administracion.actas_por_vigencia(
        db, estado=estado, limite=limite, alcance=alcance_empresa(usuario_actual)
    )
    return [VigenciaActa.model_validate(acta) for acta in actas]


# ---------------------------------------------------------------------------
# Historial de versiones
# ---------------------------------------------------------------------------
@router.get(
    "/versiones/{acta_id}",
    response_model=List[VersionActaResumen],
    summary="Historial de versiones de un acta (más reciente primero)",
)
def listar_versiones(
    usuario_actual: RequiereRevisor,
    acta_id: int,
    db: Session = Depends(get_db),
) -> List[VersionActaResumen]:
    """Devuelve el listado de instantáneas registradas para el acta indicado."""
    obtener_acta_autorizada(db, acta_id, usuario_actual)
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
    usuario_actual: RequiereRevisor,
    acta_id: int,
    numero: int,
    db: Session = Depends(get_db),
) -> VersionActaDetalle:
    """Recupera el retrato completo del acta tal como quedó en esa versión."""
    acta = obtener_acta_autorizada(db, acta_id, usuario_actual)
    version = administracion.obtener_version(db, acta_id, numero)
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
    usuario_actual: RequiereCapturista,
    acta_id: int,
    numero: int,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Copia el contenido de la versión indicada sobre el acta actual.

    El historial nunca retrocede: al restaurar se emite una versión nueva con el
    contenido recuperado, de modo que la auditoría completa queda intacta.
    """
    obtener_acta_autorizada(db, acta_id, usuario_actual)
    acta = administracion.restaurar_version(db, acta_id, numero)
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="restaurar_version",
        entidad="actas",
        entidad_id=acta_id,
        datos_despues={"version_restaurada": numero, "version_actual": acta.version},
    )
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
    usuario_actual: RequiereCapturista,
    acta_id: int,
    payload: CaducidadRequest,
    db: Session = Depends(get_db),
) -> ActaRead:
    """Actualiza la vigencia del acta y registra el cambio como nueva versión.

    Enviar ``fecha_caducidad`` vacío elimina el plazo (el acta queda sin
    caducidad) y deja constancia del motivo en el historial.
    """
    obtener_acta_autorizada(db, acta_id, usuario_actual)
    acta = administracion.fijar_caducidad(
        db, acta_id, payload.fecha_caducidad, payload.motivo
    )
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="fijar_caducidad",
        entidad="actas",
        entidad_id=acta_id,
        datos_despues={
            "fecha_caducidad": str(acta.fecha_caducidad) if acta.fecha_caducidad else None,
            "motivo": payload.motivo,
        },
    )
    return ActaRead.model_validate(acta)