"""Creación de la estructura de base de datos al arrancar la aplicación.

Para un despliegue productivo se recomienda migrar a Alembic; mientras tanto,
``AUTO_CREATE_TABLES=true`` mantiene la plataforma lista para usarse desde la
primera ejecución (útil en desarrollo y pruebas).
"""

from __future__ import annotations

import logging

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.core.config import settings
from app.core import security
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Crea las tablas declaradas por los modelos si aún no existen."""
    # Importa los modelos para que se registren en Base.metadata.
    from app import models  # noqa: F401  (efecto secundario necesario)

    Base.metadata.create_all(bind=engine)
    _aplicar_migraciones_ligeras()
    _crear_super_administrador_inicial()
    logger.info("Estructura de base de datos verificada (%d tablas)", len(Base.metadata.tables))


def _crear_super_administrador_inicial() -> None:
    """Crea un Super Administrador inicial si la base de datos está vacía.

    Garantiza que el sistema nunca quede huérfano: siempre existirá al menos
    un usuario con acceso total para iniciar la plataforma. Las credenciales
    se leen de las variables de entorno SEED_ADMIN_*.
    """
    from sqlalchemy.orm import Session
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        total = db.query(Usuario).count()
        if total == 0:
            usuario = Usuario(
                email=settings.seed_admin_email,
                nombre_completo=settings.seed_admin_nombre,
                rol="SuperAdministrador",
                password_hash=security.hash_password(settings.seed_admin_password),
                activo=True,
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
            logger.info(
                "Super Administrador inicial creado: %s (rol=%s)",
                usuario.email,
                usuario.rol,
            )
    finally:
        db.close()


# Columnas añadidas después de la primera versión, que ``create_all`` no agrega
# a tablas ya existentes (hasta que el proyecto adopte Alembic).
_COLUMNAS_NUEVAS = {
    "actas": (
        ("fecha_caducidad", "DATE"),
        ("motivo_caducidad", "VARCHAR(300)"),
        ("creado_por", "VARCHAR(150)"),
        ("tipo_sociedad", "VARCHAR(60)"),
        ("datos_especificos", "JSON"),
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
        ("codigo_empresa", "VARCHAR(32)"),
        ("empresa_codigo", "VARCHAR(32)"),
        ("nombre_sociedad", "VARCHAR(200)"),
        ("rfc_sociedad", "VARCHAR(13)"),
        ("tipo_sociedad", "VARCHAR(60)"),
        ("logo_empresa", "TEXT"),
        ("firma_electronica", "BOOLEAN DEFAULT 0"),
        ("usar_info_empresa", "BOOLEAN DEFAULT 0"),
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

    _asignar_codigos_empresa()


def _asignar_codigos_empresa() -> None:
    """Completa códigos para Administradores creados antes de esta migración."""
    from app.services.auth_service import generar_codigo_empresa

    db = SessionLocal()
    try:
        administradores = (
            db.query(Usuario)
            .filter(Usuario.rol == "Administrador", Usuario.codigo_empresa.is_(None))
            .all()
        )
        for administrador in administradores:
            administrador.codigo_empresa = generar_codigo_empresa(db)
        if administradores:
            db.commit()
            logger.info("Códigos de empresa asignados: %d", len(administradores))
    finally:
        db.close()
