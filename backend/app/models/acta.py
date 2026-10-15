"""Modelo SQLAlchemy del acta corporativa.

El acta guarda tanto los datos capturados en el formulario como el resultado del
procesamiento: cláusulas redactadas por IA/plantillas, validación de consistencia
y el texto legal consolidado. Las colecciones (asistentes, orden del día y
acuerdos) se almacenan como JSON para mantener el esquema flexible y portable
entre PostgreSQL y SQLite.

Además incorpora dos mecanismos de gobernanza documental:

* ``fecha_caducidad`` — vigencia declarada del acta (opcional) a partir de la
  cual el expediente se considera vencido; ver ``app.services.administracion``.
* :class:`ActaVersion` — copia fiel de cada versión emitida, para auditar qué
  cambió entre revisiones.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import (
    EstatusActa,
    ProveedorIA,
    TipoAsamblea,
    enum_column,
)

__all__ = ["Acta", "ActaVersion", "DIAS_AVISO_CADUCIDAD"]

# Anticipación con la que una acta vigente pasa a clasificarse como «por vencer».
DIAS_AVISO_CADUCIDAD = 30


class Acta(Base):
    """Acta corporativa (asamblea de accionistas o sesión de consejo)."""

    __tablename__ = "actas"

    # --- Identificación -----------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # --- Datos generales ----------------------------------------------------
    sociedad: Mapped[str] = mapped_column(String(200), index=True)
    rfc_sociedad: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    tipo_asamblea: Mapped[TipoAsamblea] = mapped_column(
        enum_column(TipoAsamblea, "tipo_asamblea"), index=True
    )
    titulo: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    hora: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    lugar: Mapped[str] = mapped_column(String(300))

    # --- Convocatoria -------------------------------------------------------
    convocatoria_fecha: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    convocatoria_medio: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    convocatoria_quien: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # --- Capital y quórum ---------------------------------------------------
    capital_social: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    acciones_totales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capital_presente: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quorum_porcentaje: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --- Mesa directiva y asistentes ---------------------------------------
    presidente: Mapped[str] = mapped_column(String(150))
    secretario: Mapped[str] = mapped_column(String(150))
    asistentes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    # --- Cuerpo del acta ----------------------------------------------------
    orden_del_dia: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    acuerdos: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    clausulas: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)
    texto_legal: Mapped[str] = mapped_column(Text, default="")
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Trazabilidad -------------------------------------------------------
    validacion_ia: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    proveedor_ia: Mapped[str] = mapped_column(String(40), default=ProveedorIA.PLANTILLAS.value)
    estatus: Mapped[EstatusActa] = mapped_column(
        enum_column(EstatusActa, "estatus_acta"), default=EstatusActa.BORRADOR, index=True
    )
    # --- Control de autoría (quién la realizó; listo para integración de usuarios)
    creado_por: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)

    # --- Gobernanza: vigencia ----------------------------------------------
    fecha_caducidad: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    motivo_caducidad: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    # Autor de la versión (quién la realizó; hoy el asistente/usuario anónimo,
    # mañana el usuario autenticado tras la integración de usuarios).

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Versiones históricas ----------------------------------------------
    versiones: Mapped[List["ActaVersion"]] = relationship(
        back_populates="acta",
        cascade="all, delete-orphan",
        order_by="ActaVersion.version.desc()",
        passive_deletes=True,
    )

    # --- Utilidades ---------------------------------------------------------
    @property
    def total_asistentes(self) -> int:
        """Número de asistentes registrados (usado en la maquetación del PDF)."""
        return len(self.asistentes or [])

    @property
    def dias_para_caducar(self) -> Optional[int]:
        """Días restantes de vigencia; negativos si ya venció.

        Devuelve ``None`` cuando el acta no tiene caducidad declarada (sin plazo).
        """
        if self.fecha_caducidad is None:
            return None
        return (self.fecha_caducidad - datetime.utcnow().date()).days

    @property
    def estado_caducidad(self) -> str:
        """``sin_fecha``, ``vigente``, ``por_vencer`` o ``vencida``."""
        dias = self.dias_para_caducar
        if dias is None:
            return "sin_fecha"
        if dias < 0:
            return "vencida"
        if dias <= DIAS_AVISO_CADUCIDAD:
            return "por_vencer"
        return "vigente"

    def __repr__(self) -> str:  # pragma: no cover - apoyo para depuración
        return f"<Acta folio={self.folio!r} sociedad={self.sociedad!r} version={self.version}>"


class ActaVersion(Base):
    """Instantánea inmutable de una versión emitida de un acta.

    Se registra en la creación y en cada actualización (PUT o regeneración con
    IA), conservando el contenido completo del acta en ese momento. Permite al
    administrador auditar el historial aunque el acta actual haya cambiado.
    Se elimina en cascada junto con su acta.
    """

    __tablename__ = "actas_versiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    acta_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("actas.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Contenido completo del acta tal como quedó en esta versión (JSON portable).
    contenido: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Contexto de la modificación: por qué se emitió esta versión.
    motivo: Mapped[str] = mapped_column(String(300), default="Creación del acta")
    estatus: Mapped[str] = mapped_column(String(40), default=EstatusActa.BORRADOR.value)
    # Quién la realizó (hoy texto libre/asistente; mañana FK a usuarios).
    creado_por: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    acta: Mapped["Acta"] = relationship(back_populates="versiones")

    def __repr__(self) -> str:  # pragma: no cover - apoyo para depuración
        return f"<ActaVersion acta_id={self.acta_id} version={self.version}>"
