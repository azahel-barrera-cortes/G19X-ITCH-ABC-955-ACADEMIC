"""Clase base declarativa de SQLAlchemy 2.0 para todos los modelos."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa; agrupa los metadatos y las tablas del proyecto."""

    def __repr__(self) -> str:  # pragma: no cover - apoyo para depuración
        pk = getattr(self, "id", None)
        return f"<{type(self).__name__} id={pk}>"
