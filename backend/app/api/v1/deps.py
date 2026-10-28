"""Dependencias de autenticación y autorización (RBAC) para los endpoints de la API."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import PluriActasError
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import TokenDatos

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")

# Variante opcional: no lanza 401 cuando falta el token (p. ej. registro público).
oauth2_opcional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", scheme_name="JWT", auto_error=False
)


async def obtener_usuario_actual(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> Usuario:
    """Devuelve el usuario autenticado a partir del JWT, o lanza 401."""
    credenciales_excepcion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decodificar_token(token)
        if payload is None:
            raise credenciales_excepcion
        email: str = payload.get("sub")
        if email is None:
            raise credenciales_excepcion
        token_datos = TokenDatos(email=email, rol=payload.get("rol"), usuario_id=payload.get("usuario_id"))
    except JWTError:
        raise credenciales_excepcion

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.activo:
        raise credenciales_excepcion
    return usuario


async def obtener_usuario_opcional(
    token: Annotated[Optional[str], Depends(oauth2_opcional)],
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    """Devuelve el usuario autenticado si hay token válido; ``None`` en caso contrario.

    Se usa en endpoints públicos cuyo comportamiento mejora cuando el llamador
    está autenticado (por ejemplo, el registro: un Administrador puede asignar
    cualquier rol, mientras que un visitante anónimo solo obtiene ``capturista``).
    """
    if not token:
        return None
    payload = security.decodificar_token(token)
    if not payload:
        return None
    email = payload.get("sub")
    if not email:
        return None
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.activo:
        return None
    return usuario


def requiere_rol(rol_minimo: str):
    """Devuelve una dependencia que exige al usuario tener al menos ``rol_minimo``.

    Niveles: capturista < revisor < abogado_responsable < Administrador.
    """

    def _verificador(usuario: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Usuario:
        if not security.tiene_nivel_minimo(usuario.rol, rol_minimo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Se requiere el rol '{rol_minimo}' o superior. "
                    f"Rol actual: '{usuario.rol}'."
                ),
            )
        return usuario

    return _verificador


# Dependencias reutilizables por rol.
UsuarioActual = Annotated[Usuario, Depends(obtener_usuario_actual)]
UsuarioOpcional = Annotated[Optional[Usuario], Depends(obtener_usuario_opcional)]
RequiereCapturista = Annotated[Usuario, Depends(requiere_rol("capturista"))]
RequiereRevisor = Annotated[Usuario, Depends(requiere_rol("revisor"))]
RequiereAbogado = Annotated[Usuario, Depends(requiere_rol("abogado_responsable"))]
RequiereAdmin = Annotated[Usuario, Depends(requiere_rol("Administrador"))]


def registrar_bitacora(
    db: Session,
    *,
    usuario: Optional[Usuario],
    accion: str,
    entidad: str,
    entidad_id: Optional[int] = None,
    datos_antes: Optional[dict] = None,
    datos_despues: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    """Escribe una entrada en la bitácora de cambios."""
    from app.models.usuario import BitacoraCambios

    entrada = BitacoraCambios(
        usuario_id=usuario.id if usuario else None,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        datos_antes=datos_antes,
        datos_despues=datos_despues,
        ip_origen=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(entrada)
    db.commit()