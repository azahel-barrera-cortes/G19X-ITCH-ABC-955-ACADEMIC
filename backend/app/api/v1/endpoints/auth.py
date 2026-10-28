"""Endpoints de autenticación: registro de usuarios, login y perfil."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import RequiereAdmin, UsuarioActual, UsuarioOpcional, get_db, obtener_usuario_actual
from app.core import security
from app.core.config import settings
from app.core.exceptions import DatosActaInvalidosError
from app.models.usuario import Usuario
from app.schemas.acta import ApiMensaje
from app.schemas.usuario import (
    ConfirmarResetPassword,
    LoginRequest,
    SolicitudResetPassword,
    Token,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
    UsuarioBase,
)
from app.services.auth_service import (
    autenticar_usuario,
    crear_usuario,
    usuario_desde_respuesta,
    crear_token_reinicio_password,
    actualizar_password_por_token,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario (público; el rol lo controla el servidor)",
)
def registrar_usuario(
    datos: UsuarioCrear,
    solicitante: UsuarioOpcional,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Crea un nuevo usuario aplicando reglas de rol seguras:

    * **Primer usuario del sistema** (base vacía): se crea como ``Administrador``
      para poder arrancar la plataforma.
    * **Autoregistro anónimo**: el rol se fuerza a ``capturista`` (el mínimo
      privilegio), sin importar el rol solicitado. Un Administrador puede
      elevarlo después desde ``PUT /auth/users/{id}``.
    * **Administrador autenticado**: puede asignar cualquier rol válido.
    """
    total_usuarios = db.query(Usuario).count()
    if total_usuarios == 0:
        datos.rol = "Administrador"
    elif not (solicitante and solicitante.rol == "Administrador"):
        datos.rol = "capturista"
    usuario = crear_usuario(db, datos)
    return usuario_desde_respuesta(usuario)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión y obtener un JWT de acceso.",
)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """Autentica al usuario y devuelve un token de acceso (JWT)."""
    usuario = autenticar_usuario(db, datos.email, datos.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = security.crear_token_acceso(
        {
            "sub": usuario.email,
            "rol": usuario.rol,
            "usuario_id": usuario.id,
        }
    )
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Obtener el perfil del usuario autenticado.",
)
def perfil(usuario_actual: UsuarioActual) -> UsuarioRespuesta:
    """Devuelve los datos del usuario que envió el token."""
    return usuario_desde_respuesta(usuario_actual)


@router.put(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Actualizar el perfil del usuario autenticado.",
)
def actualizar_perfil(
    usuario_actual: UsuarioActual,
    cambios: UsuarioActualizar,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Actualiza los datos del usuario autenticado."""
    if cambios.nombre_completo is not None:
        usuario_actual.nombre_completo = cambios.nombre_completo
    if cambios.rol is not None:
        if cambios.rol not in security.ROLES_VALIDOS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Rol no válido. Roles permitidos: {', '.join(security.ROLES_VALIDOS)}.",
            )
        usuario_actual.rol = cambios.rol
    if cambios.activo is not None:
        usuario_actual.activo = cambios.activo
    if cambios.password is not None:
        usuario_actual.password_hash = security.hash_password(cambios.password)
    db.commit()
    db.refresh(usuario_actual)
    return usuario_desde_respuesta(usuario_actual)


@router.post(
    "/reset-password",
    response_model=ApiMensaje,
    summary="Solicitar recuperación de contraseña (público).",
)
def solicitar_reset_password(
    datos: SolicitudResetPassword,
    db: Session = Depends(get_db),
) -> ApiMensaje:
    """Genera un token temporal (1 hora) para recuperar la contraseña.

    Por seguridad la respuesta es idéntica exista o no el correo. Mientras no
    haya servicio de correo configurado, en modo ``DEBUG`` el token se devuelve
    en ``detalle`` para poder probar el flujo de extremo a extremo.
    """
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == datos.email, Usuario.activo.is_(True))
        .first()
    )
    token = crear_token_reinicio_password(usuario, db) if usuario else None
    detalle = f"Token de desarrollo: {token}" if (token and settings.debug) else None
    return ApiMensaje(
        mensaje="Si el correo está registrado, se generó un token de recuperación.",
        detalle=detalle,
    )


@router.post(
    "/reset-password/confirm",
    response_model=Token,
    summary="Confirmar recuperación de contraseña con token.",
)
def confirmar_reset_password(
    datos: ConfirmarResetPassword,
    db: Session = Depends(get_db),
) -> Token:
    """Confirma el cambio de contraseña usando el token de recuperación."""
    usuario = actualizar_password_por_token(db, datos.token, datos.nuevo_password)
    if usuario is None:
        raise DatosActaInvalidosError(
            "El enlace de recuperación no es válido o ha expirado.",
            detalle="El token de recuperación no es válido o ha expirado.",
        )
    token_nuevo = security.crear_token_acceso(
        {"sub": usuario.email, "rol": usuario.rol, "usuario_id": usuario.id}
    )
    return Token(access_token=token_nuevo)


@router.get(
    "/users",
    response_model=List[UsuarioRespuesta],
    summary="Listar usuarios (solo Admin).",
)
def listar_usuarios(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(RequiereAdmin),
) -> List[UsuarioRespuesta]:
    """Devuelve todos los usuarios registrados."""
    usuarios = db.query(Usuario).order_by(Usuario.email).all()
    return [usuario_desde_respuesta(u) for u in usuarios]


@router.put(
    "/users/{user_id}",
    response_model=UsuarioRespuesta,
    summary="Actualizar un usuario (solo Admin).",
)
def actualizar_usuario(
    user_id: int,
    cambios: UsuarioActualizar,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(RequiereAdmin),
) -> UsuarioRespuesta:
    """Actualiza los datos de un usuario existente."""
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise DatosActaInvalidosError(
            "Usuario no encontrado.",
            detalle=f"No existe un usuario con el identificador {user_id}.",
        )
    if cambios.nombre_completo is not None:
        usuario.nombre_completo = cambios.nombre_completo
    if cambios.rol is not None:
        if cambios.rol not in security.ROLES_VALIDOS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Rol no válido. Roles permitidos: {', '.join(security.ROLES_VALIDOS)}.",
            )
        usuario.rol = cambios.rol
    if cambios.activo is not None:
        usuario.activo = cambios.activo
    if cambios.password is not None:
        usuario.password_hash = security.hash_password(cambios.password)
    db.commit()
    db.refresh(usuario)
    return usuario_desde_respuesta(usuario)