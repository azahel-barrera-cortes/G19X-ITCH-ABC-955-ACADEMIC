"""Utilidades de seguridad: hash de contraseñas, generación y validación de JWT.

Roles soportados:
- Administrador: acceso total a todos los endpoints.
- capturista: puede crear, leer y editar actas propias.
- revisor: puede leer todas las actas y cambiar su estatus.
- abogado_responsable: puede leer todas las actas, aprobarlas y firmarlas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de ``password``."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba que ``plain_password`` coincida con ``hashed_password``."""
    return pwd_context.verify(plain_password, hashed_password)


def crear_token_acceso(datos: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un JWT de acceso con los claims indicados."""
    para_codificar = datos.copy()
    expiracion = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    para_codificar.update({"exp": expiracion})
    return jwt.encode(para_codificar, settings.secret_key, algorithm=settings.algorithm)


def decodificar_token(token: str) -> Optional[dict[str, Any]]:
    """Decodifica un JWT y devuelve su payload, o ``None`` si es inválido/expiró."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


# Roles válidos del sistema.
ROLES_VALIDOS = ("Administrador", "capturista", "revisor", "abogado_responsable")

# Acceso mínimo por rol (número mayor = más permisos).
NIVEL_ROL = {
    "capturista": 1,
    "revisor": 2,
    "abogado_responsable": 3,
    "Administrador": 4,
}


def tiene_nivel_minimo(rol: str, minimo: str) -> bool:
    """Devuelve True si ``rol`` tiene al menos el nivel de ``minimo``."""
    return NIVEL_ROL.get(rol, 0) >= NIVEL_ROL.get(minimo, 0)