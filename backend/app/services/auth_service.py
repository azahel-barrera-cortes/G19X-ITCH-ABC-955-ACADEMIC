"""Servicio de autenticación: registro, login y obtención de usuario actual."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import string
from typing import Optional

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import DatosActaInvalidosError
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCrear, UsuarioRespuesta


def generar_codigo_empresa(db: Session) -> str:
    """Genera un código corto y único para un Administrador de empresa."""
    caracteres = string.ascii_uppercase + string.digits
    for _ in range(10):
        codigo = "PGAC-" + "".join(secrets.choice(caracteres) for _ in range(10))
        if not db.query(Usuario).filter(Usuario.codigo_empresa == codigo).first():
            return codigo
    raise DatosActaInvalidosError(
        "No se pudo generar el código de la empresa.",
        detalle="Se agotaron los intentos para generar un código único.",
    )


def autenticar_usuario(db: Session, email: str, password: str) -> Optional[Usuario]:
    """Devuelve el usuario si las credenciales son válidas, o None."""
    usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.activo.is_(True)).first()
    if not usuario:
        return None
    if not security.verify_password(password, usuario.password_hash):
        return None
    if security.pwd_context.needs_update(usuario.password_hash):
        usuario.password_hash = security.hash_password(password)
        db.commit()
    return usuario


def crear_usuario(db: Session, datos: UsuarioCrear) -> Usuario:
    """Crea un nuevo usuario. Lanza error si el email ya existe."""
    existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existente:
        raise DatosActaInvalidosError(
            "El correo electrónico ya está registrado.",
            detalle=f"Ya existe un usuario con el email {datos.email}.",
        )
    if datos.rol not in security.ROLES_VALIDOS:
        raise DatosActaInvalidosError(
            "Rol no válido.",
            detalle=f"Roles permitidos: {', '.join(security.ROLES_VALIDOS)}.",
        )
    usuario = Usuario(
        email=datos.email,
        nombre_completo=datos.nombre_completo,
        rol=datos.rol,
        password_hash=security.hash_password(datos.password),
        activo=datos.activo,
        codigo_empresa=generar_codigo_empresa(db) if datos.rol == "Administrador" else None,
        empresa_codigo=datos.codigo_empresa if datos.rol != "Administrador" else None,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def obtener_administrador_empresa(db: Session, codigo: str) -> Optional[Usuario]:
    """Busca el Administrador propietario de un código empresarial."""
    return (
        db.query(Usuario)
        .filter(
            Usuario.rol == "Administrador",
            Usuario.codigo_empresa == codigo,
            Usuario.activo.is_(True),
        )
        .first()
    )


def usuario_desde_respuesta(usuario: Usuario) -> UsuarioRespuesta:
    """Convierte un modelo ORM en el esquema de respuesta."""
    return UsuarioRespuesta.model_validate(usuario)


def crear_token_reinicio_password(usuario: Usuario, db: Session) -> str:
    """Crea un token único y temporal para recuperación de contraseña."""
    token = secrets.token_urlsafe(32)
    usuario.reset_token = hashlib.sha256(token.encode("utf-8")).hexdigest()
    usuario.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=60)
    db.commit()
    db.refresh(usuario)
    return token


def invalidar_token_reinicio_password(
    usuario_id: int, token: str, db: Session
) -> bool:
    """Invalida el token solo si sigue siendo el token enviado por correo."""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    actualizados = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id, Usuario.reset_token == token_hash)
        .update(
            {Usuario.reset_token: None, Usuario.reset_token_expires: None},
            synchronize_session=False,
        )
    )
    if actualizados:
        db.commit()
    return bool(actualizados)


def actualizar_password_usuario(usuario: Usuario, nuevo_password: str) -> None:
    """Actualiza una contraseña e invalida tokens de recuperación y sesiones."""
    usuario.password_hash = security.hash_password(nuevo_password)
    usuario.reset_token = None
    usuario.reset_token_expires = None
    usuario.token_version += 1


def actualizar_password_por_token(
    db: Session, token: str, nuevo_password: str
) -> Optional[Usuario]:
    """Actualiza la contraseña y consume el token en una sola operación atómica."""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    usuario_id = (
        db.query(Usuario.id)
        .filter(
            Usuario.reset_token == token_hash,
            Usuario.reset_token_expires > ahora,
            Usuario.activo.is_(True),
        )
        .scalar()
    )
    if usuario_id is None:
        return None

    actualizados = (
        db.query(Usuario)
        .filter(
            Usuario.id == usuario_id,
            Usuario.reset_token == token_hash,
            Usuario.reset_token_expires > ahora,
            Usuario.activo.is_(True),
        )
        .update(
            {
                Usuario.password_hash: security.hash_password(nuevo_password),
                Usuario.token_version: Usuario.token_version + 1,
                Usuario.reset_token: None,
                Usuario.reset_token_expires: None,
            },
            synchronize_session=False,
        )
    )
    if not actualizados:
        db.rollback()
        return None
    db.commit()
    return db.get(Usuario, usuario_id)