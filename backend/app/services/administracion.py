"""Servicio de administración de actas: historial de versiones y caducidad.

Resuelve dos necesidades de gobernanza documental sobre el repositorio de actas:

* **Historial de versiones.** Cada vez que se crea o actualiza un acta se guarda
  una instantánea inmutable (:class:`ActaVersion`) con el contenido completo y el
  motivo del cambio. Permite auditar qué cambió y restaurar versiones previas.
* **Caducidad.** Permite fijar, ampliar o quitar la vigencia de un acta y
  clasificar el expediente como ``sin_fecha``, ``vigente``, ``por_vencer`` o
  ``vencida`` (con ``DIAS_AVISO_CADUCIDAD`` de anticipación).

Esta capa solo toca el repositorio: no redacta ni compila el documento, con lo que
se conserva la separación de responsabilidades exigida por el proyecto.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ActaNoEncontradaError
from app.models.acta import DIAS_AVISO_CADUCIDAD, Acta, ActaVersion
from app.models.enums import EstatusActa

logger = logging.getLogger(__name__)

__all__ = [
    "DIAS_AVISO_CADUCIDAD",
    "contenido_del_acta",
    "registrar_version",
    "listar_versiones",
    "obtener_version",
    "restaurar_version",
    "fijar_caducidad",
    "resumen_administracion",
    "actas_por_vigencia",
]

# Campos del acta que se conservan en cada instantánea de versión.
_CAMPOS_INSTANTANEA = (
    "sociedad",
    "rfc_sociedad",
    "tipo_asamblea",
    "titulo",
    "fecha",
    "lugar",
    "convocatoria_fecha",
    "capital_social",
    "acciones_totales",
    "capital_presente",
    "quorum_porcentaje",
    "presidente",
    "secretario",
    "asistentes",
    "orden_del_dia",
    "acuerdos",
    "clausulas",
    "texto_legal",
    "observaciones",
    "validacion_ia",
    "proveedor_ia",
    "estatus",
    "fecha_caducidad",
    "version",
)


def _a_json(valor: Any) -> Any:
    """Convierte enums, fechas y horas a primitivos JSON-serializables."""
    if hasattr(valor, "value") and not isinstance(valor, (str, int, float, bool)):
        valor = valor.value
    if hasattr(valor, "isoformat") and not isinstance(valor, str):
        return valor.isoformat()
    return valor


def contenido_del_acta(acta: Acta) -> Dict[str, Any]:
    """Serializa los campos relevantes del acta para guardarlos en una versión.

    Se descartan ``id`` y las marcas temporales: la instantánea debe ser un
    retrato del contenido, no del registro.
    """
    datos: Dict[str, Any] = {
        campo: _a_json(getattr(acta, campo, None)) for campo in _CAMPOS_INSTANTANEA
    }
    datos["folio"] = acta.folio
    return datos


def registrar_version(db: Session, acta: Acta, motivo: str, creado_por: Optional[str] = None) -> ActaVersion:
    """Guarda una instantánea del acta en su versión actual.

    Idempotente por diseño: si ya existe una instantánea para ``(acta, versión)``
    se conserva la original, que representa el momento exacto de la emisión.
    """
    existente = db.scalar(
        select(ActaVersion).where(
            ActaVersion.acta_id == acta.id,
            ActaVersion.version == int(acta.version or 1),
        )
    )
    if existente is not None:
        return existente

    version = ActaVersion(
        acta_id=acta.id,
        version=int(acta.version or 1),
        contenido=contenido_del_acta(acta),
        motivo=str(motivo)[:300],
        estatus=str(getattr(acta.estatus, "value", acta.estatus) or EstatusActa.BORRADOR.value),
        creado_por=creado_por or getattr(acta, "creado_por", None),
    )
    db.add(version)
    logger.info(
        "Versión %s registrada para el acta %s (%s)",
        version.version,
        acta.folio,
        version.motivo,
    )
    return version


# ---------------------------------------------------------------------------
# Consulta del historial
# ---------------------------------------------------------------------------
def listar_versiones(db: Session, acta_id: int) -> List[ActaVersion]:
    """Historial completo de una acta, de la más reciente a la más antigua."""
    if db.get(Acta, acta_id) is None:
        raise ActaNoEncontradaError(f"No existe un acta con el identificador {acta_id}.")

    consulta = (
        select(ActaVersion)
        .where(ActaVersion.acta_id == acta_id)
        .order_by(ActaVersion.version.desc(), ActaVersion.id.desc())
    )
    return list(db.scalars(consulta))


def obtener_version(db: Session, acta_id: int, numero: int) -> ActaVersion:
    """Recupera una versión concreta o lanza el error de no encontrada."""
    acta = db.get(Acta, acta_id)
    if acta is None:
        raise ActaNoEncontradaError(f"No existe un acta con el identificador {acta_id}.")

    version = db.scalar(
        select(ActaVersion).where(
            ActaVersion.acta_id == acta_id,
            ActaVersion.version == numero,
        )
    )
    if version is None:
        raise ActaNoEncontradaError(
            f"El acta {acta.folio} no tiene registrada la versión {numero}."
        )
    return version


def restaurar_version(db: Session, acta_id: int, numero: int) -> Acta:
    """Copia el contenido de una versión anterior sobre el acta actual.

    Genera **una versión nueva** (no retrocede el contador) para conservar la
    trazabilidad completa del expediente: el historial siempre avanza.
    """
    version = obtener_version(db, acta_id, numero)
    acta = db.get(Acta, acta_id)
    assert acta is not None  # obtener_version ya validó su existencia

    if int(acta.version or 1) == numero:
        return acta  # restaurar la versión vigente no tiene efecto

    for campo, valor in (version.contenido or {}).items():
        if campo in ("folio", "version"):
            continue
        if campo in ("fecha", "convocatoria_fecha"):
            valor = date.fromisoformat(valor) if valor else None
        setattr(acta, campo, valor)

    acta.version = int(acta.version or 1) + 1
    registrar_version(db, acta, f"Restauración desde la versión {numero}")
    db.commit()
    db.refresh(acta)
    logger.info(
        "Acta %s restaurada desde la versión %s (ahora v%s)",
        acta.folio,
        numero,
        acta.version,
    )
    return acta


# ---------------------------------------------------------------------------
# Caducidad
# ---------------------------------------------------------------------------
def fijar_caducidad(
    db: Session,
    acta_id: int,
    fecha_caducidad: Optional[date],
    motivo: Optional[str] = None,
) -> Acta:
    """Fija (o quita, con ``fecha_caducidad=None``) la vigencia del acta."""
    acta = db.get(Acta, acta_id)
    if acta is None:
        raise ActaNoEncontradaError(f"No existe un acta con el identificador {acta_id}.")

    acta.fecha_caducidad = fecha_caducidad
    acta.motivo_caducidad = motivo
    # El cambio de vigencia es un dato de gobernanza: queda como versión nueva.
    acta.version = int(acta.version or 1) + 1

    if fecha_caducidad is None:
        detalle = "sin fecha de caducidad"
    else:
        detalle = f"vigente hasta {fecha_caducidad.isoformat()}"
    registrar_version(db, acta, f"Caducidad actualizada: {detalle}")

    db.commit()
    db.refresh(acta)
    logger.info("Caducidad del acta %s: %s", acta.folio, detalle)
    return acta


# ---------------------------------------------------------------------------
# Visión global del repositorio
# ---------------------------------------------------------------------------
def resumen_administracion(db: Session) -> Dict[str, Any]:
    """Estadísticas globales del repositorio para el panel de administración."""
    por_estatus: Dict[str, int] = {estatus.value: 0 for estatus in EstatusActa}
    for valor, cantidad in db.execute(
        select(Acta.estatus, func.count(Acta.id)).group_by(Acta.estatus)
    ):
        por_estatus[str(getattr(valor, "value", valor))] = int(cantidad)

    hoy = date.today()
    por_vencer_hasta = hoy + timedelta(days=DIAS_AVISO_CADUCIDAD)

    con_fecha = db.scalar(
        select(func.count(Acta.id)).where(Acta.fecha_caducidad.is_not(None))
    ) or 0
    vencidas = db.scalar(
        select(func.count(Acta.id)).where(
            Acta.fecha_caducidad.is_not(None), Acta.fecha_caducidad < hoy
        )
    ) or 0
    por_vencer = db.scalar(
        select(func.count(Acta.id)).where(
            Acta.fecha_caducidad >= hoy, Acta.fecha_caducidad <= por_vencer_hasta
        )
    ) or 0
    total = db.scalar(select(func.count(Acta.id))) or 0
    total_versiones = db.scalar(select(func.count(ActaVersion.id))) or 0

    return {
        "total_actas": int(total),
        "total_versiones": int(total_versiones),
        "por_estatus": por_estatus,
        "vigencia": {
            # Vigentes = con fecha futura fuera de la ventana de aviso.
            "vigentes": int(con_fecha) - int(vencidas) - int(por_vencer),
            "por_vencer": int(por_vencer),
            "vencidas": int(vencidas),
            "sin_fecha": int(total) - int(con_fecha),
            "dias_aviso": DIAS_AVISO_CADUCIDAD,
        },
    }


def actas_por_vigencia(
    db: Session,
    *,
    estado: Optional[str] = None,
    limite: int = 100,
) -> List[Acta]:
    """Lista actas filtradas por su clasificación de vigencia.

    ``estado`` acepta ``vigente``, ``por_vencer``, ``vencida`` o ``sin_fecha``;
    con ``None`` devuelve todas, vencidas primero (prioridad de atención).
    """
    hoy = date.today()
    consulta = select(Acta)

    if estado == "vencida":
        consulta = consulta.where(
            Acta.fecha_caducidad.is_not(None), Acta.fecha_caducidad < hoy
        )
    elif estado == "por_vencer":
        consulta = consulta.where(
            Acta.fecha_caducidad >= hoy,
            Acta.fecha_caducidad <= hoy + timedelta(days=DIAS_AVISO_CADUCIDAD),
        )
    elif estado == "vigente":
        consulta = consulta.where(
            Acta.fecha_caducidad > hoy + timedelta(days=DIAS_AVISO_CADUCIDAD)
        )
    elif estado == "sin_fecha":
        consulta = consulta.where(Acta.fecha_caducidad.is_(None))

    # Vencidas primero; dentro de cada grupo, por vencimiento más próximo.
    consulta = consulta.order_by(Acta.fecha_caducidad.is_(None), Acta.fecha_caducidad)
    return list(db.scalars(consulta.limit(max(1, min(limite, 200)))))