"""Modelo SQLAlchemy de usuarios y roles para el control de acceso (RBAC)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Usuario(Base):
    """Usuario autenticado de la plataforma con un rol asignado.

    Roles: Administrador, capturista, revisor, abogado_responsable.
    """

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    rol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Token de recuperación de contraseña (válido 1 hora)
    reset_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relación con la bitácora de cambios.
    bitacora: Mapped[list["BitacoraCambios"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario id={self.id} email={self.email!r} rol={self.rol!r}>"


class BitacoraCambios(Base):
    """Registro de auditoría de quién modificó qué y cuándo.

    Se escribe automáticamente al crear, actualizar o eliminar un acta,
    capturando el usuario, el rol, la acción, el objetivo y los datos anteriores/nuevos.
    """

    __tablename__ = "bitacora_cambios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidad: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidad_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    datos_antes: Mapped[Optional[dict]] = mapped_column(JSON, default=None, nullable=True)
    datos_despues: Mapped[Optional[dict]] = mapped_column(JSON, default=None, nullable=True)
    ip_origen: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped[Optional["Usuario"]] = relationship(back_populates="bitacora")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BitacoraCambios id={self.id} accion={self.accion!r} entidad={self.entidad!r}>"