"""Acceso a la base de datos: motor, fábrica de sesiones y dependencia FastAPI."""

from __future__ import annotations

import logging
from typing import Any, Dict, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


def _crear_engine() -> Engine:
    """Crea el motor SQLAlchemy según ``DATABASE_URL``.

    - SQLite (desarrollo/pruebas): desactiva la verificación de hilo porque el
      servidor asíncrono de FastAPI reutiliza la sesión entre hilos.
    - PostgreSQL (producción): requiere el driver indicado en
      ``requirements-postgres.txt``; si falta, se lanza un error explicativo.
    """
    opciones: Dict[str, Any] = {
        "pool_pre_ping": True,
        "echo": settings.sql_echo,
    }
    if settings.es_sqlite:
        opciones["connect_args"] = {"check_same_thread": False}

    try:
        return create_engine(settings.database_url, **opciones)
    except (ModuleNotFoundError, NoSuchModuleError) as exc:  # driver ausente
        raise RuntimeError(
            "No se pudo inicializar el motor de base de datos para "
            f"'{settings.database_url}'. Si usas PostgreSQL instala el driver con: "
            "pip install -r requirements-postgres.txt"
        ) from exc


engine: Engine = _crear_engine()
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: entrega una sesión y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
