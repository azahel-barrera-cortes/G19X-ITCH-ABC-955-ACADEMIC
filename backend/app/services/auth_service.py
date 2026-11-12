"""Servicio de autenticación: registro, login y obtención de usuario actual."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
    import secrets

    token = secrets.token_urlsafe(32)
    usuario.reset_token = token
    usuario.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=60)
    db.commit()
    db.refresh(usuario)
    return token


def verificar_y_consumir_token(token: str, db: Session) -> Optional[Usuario]:
    """Verifica que un token de recuperación es válido; lo consume en caso afirmativo."""
    from app.models.usuario import Usuario

    usuario = db.query(Usuario).filter(Usuario.reset_token == token).first()
    if not usuario or not usuario.reset_token_expires:
        return None
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if now > usuario.reset_token_expires:
        usuario.reset_token = None
        usuario.reset_token_expires = None
        db.commit()
        return None
    # Consumir: el token solo se puede usar una vez.
    usuario.reset_token = None
    usuario.reset_token_expires = None
    db.commit()
    return usuario


def actualizar_password_por_token(
    db: Session, token: str, nuevo_password: str
) -> Optional[Usuario]:
    """Actualiza la contraseña de un usuario si el token es válido."""
    usuario = verificar_y_consumir_token(token, db)
    if usuario is None:
        return None
    usuario.password_hash = security.hash_password(nuevo_password)
    db.commit()
    db.refresh(usuario)
    return usuario