"""Creación de la estructura de base de datos al arrancar la aplicación.

Para un despliegue productivo se recomienda migrar a Alembic; mientras tanto,
``AUTO_CREATE_TABLES=true`` mantiene la plataforma lista para usarse desde la
primera ejecución (útil en desarrollo y pruebas).
"""

from __future__ import annotations

import logging

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Crea las tablas declaradas por los modelos si aún no existen."""
    # Importa los modelos para que se registren en Base.metadata.
    from app import models  # noqa: F401  (efecto secundario necesario)

    Base.metadata.create_all(bind=engine)
    _aplicar_migraciones_ligeras()
    logger.info("Estructura de base de datos verificada (%d tablas)", len(Base.metadata.tables))


# Columnas añadidas después de la primera versión, que ``create_all`` no agrega
# a tablas ya existentes (hasta que el proyecto adopte Alembic).
_COLUMNAS_NUEVAS = {
    "actas": (
        ("fecha_caducidad", "DATE"),
        ("motivo_caducidad", "VARCHAR(300)"),
        ("creado_por", "VARCHAR(150)"),
        ("tipo_sociedad", "VARCHAR(60)"),
        ("logo_empresa", "TEXT"),
        ("firma_electronica", "BOOLEAN DEFAULT 0"),
        ("usar_info_empresa", "BOOLEAN DEFAULT 0"),
    ),
    "actas_versiones": (
        ("creado_por", "VARCHAR(150)"),
    ),
    "usuarios": (
        ("reset_token", "VARCHAR(128)"),
        ("reset_token_expires", "DATETIME"),
    ),
}


def _aplicar_migraciones_ligeras() -> None:
    """Agrega columnas faltantes a bases de datos creadas con versiones previas."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    with engine.begin() as conexion:
        for tabla, columnas in _COLUMNAS_NUEVAS.items():
            existentes = {columna["name"] for columna in inspector.get_columns(tabla)} if tabla in inspector.get_table_names() else set()
            for nombre, tipo in columnas:
                if nombre not in existentes:
                    conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))
                    logger.info("Columna %s.%s agregada por migración ligera", tabla, nombre)
