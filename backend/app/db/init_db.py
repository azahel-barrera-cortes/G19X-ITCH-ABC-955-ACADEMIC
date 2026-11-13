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
        ("empresa_codigo", "VARCHAR(32)"),
        ("tipo_sociedad", "VARCHAR(60)"),
        ("datos_especificos", "JSON"),
        ("datos_asistente", "JSON"),
        ("estado_flujo", "VARCHAR(30) DEFAULT 'revision'"),
        ("comentario_revision", "TEXT"),
        ("historial_revision", "JSON"),
        ("logo_empresa", "TEXT"),
        ("usar_info_empresa", "BOOLEAN DEFAULT 0"),
    ),
    "actas_versiones": (
        ("creado_por", "VARCHAR(150)"),
    ),
    "usuarios": (
        ("reset_token", "VARCHAR(128)"),
        ("reset_token_expires", "DATETIME"),
        ("token_version", "INTEGER NOT NULL DEFAULT 0"),
        ("codigo_empresa", "VARCHAR(32)"),
        ("empresa_codigo", "VARCHAR(32)"),
        ("nombre_sociedad", "VARCHAR(200)"),
        ("rfc_sociedad", "VARCHAR(13)"),
        ("tipo_sociedad", "VARCHAR(60)"),
        ("logo_empresa", "TEXT"),
        ("usar_info_empresa", "BOOLEAN DEFAULT 0"),
    ),
    "bitacora_cambios": (
        ("empresa_codigo", "VARCHAR(32)"),
    ),
}


def _aplicar_migraciones_ligeras() -> None:
    """Agrega columnas faltantes a bases de datos creadas con versiones previas."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    requiere_backfill_empresa = False
    with engine.begin() as conexion:
        for tabla, columnas in _COLUMNAS_NUEVAS.items():
            existentes = {columna["name"] for columna in inspector.get_columns(tabla)} if tabla in inspector.get_table_names() else set()
            for nombre, tipo in columnas:
                if nombre not in existentes:
                    if tabla == "actas" and nombre == "empresa_codigo":
                        requiere_backfill_empresa = True
                    conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))
                    logger.info("Columna %s.%s agregada por migración ligera", tabla, nombre)
                    if tabla == "actas" and nombre == "estado_flujo":
                        conexion.execute(
                            text(
                                "UPDATE actas SET estado_flujo = CASE "
                                "WHEN estatus IN ('aprobada', 'firmada', 'archivada') THEN 'aprobada' "
                                "WHEN estatus = 'en_revision' THEN 'revision' "
                                "ELSE 'borrador' END"
                            )
                        )
        conexion.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_actas_empresa_codigo "
                "ON actas (empresa_codigo)"
            )
        )
        conexion.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_bitacora_cambios_empresa_codigo "
                "ON bitacora_cambios (empresa_codigo)"
            )
        )

    _asignar_codigos_empresa()
    if requiere_backfill_empresa:
        _asignar_empresa_a_registros_historicos()


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


def _asignar_empresa_a_registros_historicos() -> None:
    """Backfills only records tied to an exact account; ambiguous rows stay quarantined."""
    from sqlalchemy import text

    with engine.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE actas SET empresa_codigo = ("
                "SELECT CASE WHEN usuarios.rol = 'Administrador' "
                "THEN usuarios.codigo_empresa ELSE usuarios.empresa_codigo END "
                "FROM usuarios WHERE lower(usuarios.email) = lower(actas.creado_por)"
                ") WHERE empresa_codigo IS NULL AND creado_por IS NOT NULL AND EXISTS ("
                "SELECT 1 FROM usuarios WHERE lower(usuarios.email) = lower(actas.creado_por) "
                "AND CASE WHEN usuarios.rol = 'Administrador' "
                "THEN usuarios.codigo_empresa ELSE usuarios.empresa_codigo END IS NOT NULL)"
            )
        )
        conexion.execute(
            text(
                "UPDATE bitacora_cambios SET empresa_codigo = ("
                "SELECT actas.empresa_codigo FROM actas "
                "WHERE bitacora_cambios.entidad = 'actas' "
                "AND actas.id = bitacora_cambios.entidad_id"
                ") WHERE empresa_codigo IS NULL AND entidad = 'actas' "
                "AND EXISTS (SELECT 1 FROM actas WHERE actas.id = bitacora_cambios.entidad_id "
                "AND actas.empresa_codigo IS NOT NULL)"
            )
        )
        conexion.execute(
            text(
                "UPDATE bitacora_cambios SET empresa_codigo = ("
                "SELECT CASE WHEN usuarios.rol = 'Administrador' "
                "THEN usuarios.codigo_empresa ELSE usuarios.empresa_codigo END "
                "FROM usuarios WHERE usuarios.id = bitacora_cambios.usuario_id"
                ") WHERE empresa_codigo IS NULL AND usuario_id IS NOT NULL "
                "AND entidad != 'actas' AND EXISTS ("
                "SELECT 1 FROM usuarios WHERE usuarios.id = bitacora_cambios.usuario_id "
                "AND CASE WHEN usuarios.rol = 'Administrador' "
                "THEN usuarios.codigo_empresa ELSE usuarios.empresa_codigo END IS NOT NULL)"
            )
        )
