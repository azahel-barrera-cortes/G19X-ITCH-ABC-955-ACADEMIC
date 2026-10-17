"""Acceso a la base de datos: motor, fábrica de sesiones y dependencia FastAPI."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchModuleError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Número de reintentos al conectar con la base de datos (útil si PostgreSQL
# todavía está arrancando cuando inicia la aplicación).
DB_CONNECT_REINTENTOS = 3
DB_CONNECT_ESPERA_SEGUNDOS = 2


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


def verificar_conexion_db() -> bool:
    """Comprueba que se puede abrir una conexión con la base de datos.

    Reintenta automáticamente si la base de datos aún no está disponible
    (por ejemplo, PostgreSQL arrancando en Docker).
    """
    from sqlalchemy import text

    ultimo_error: Optional[Exception] = None
    for intento in range(1, DB_CONNECT_REINTENTOS + 1):
        try:
            with engine.connect() as conexion:
                conexion.execute(text("SELECT 1"))
            logger.info("Conexión a base de datos verificada (intento %d)", intento)
            return True
        except OperationalError as exc:
            ultimo_error = exc
            logger.warning(
                "Intento %d/%d de conexión a base de datos falló: %s",
                intento,
                DB_CONNECT_REINTENTOS,
                exc,
            )
            if intento < DB_CONNECT_REINTENTOS:
                time.sleep(DB_CONNECT_ESPERA_SEGUNDOS)
    logger.error(
        "No se pudo conectar a la base de datos tras %d intentos: %s",
        DB_CONNECT_REINTENTOS,
        ultimo_error,
    )
    return False


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: entrega una sesión y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
