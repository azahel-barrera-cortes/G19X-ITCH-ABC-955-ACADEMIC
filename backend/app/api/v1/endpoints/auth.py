"""Endpoints de autenticación: registro de usuarios, login y perfil."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import (
    RequiereSuperAdministrador,
    UsuarioActual,
    UsuarioOpcional,
    get_db,
    obtener_usuario_actual,
    registrar_bitacora,
)
from app.core import security
from app.core.config import settings
from app.core.exceptions import DatosActaInvalidosError
from app.models.usuario import Usuario
from app.schemas.acta import ApiMensaje
from app.schemas.usuario import (
    PerfilActualizar,
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
    generar_codigo_empresa,
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

    * **Primer usuario del sistema** (base vacía): se crea como ``SuperAdministrador``
      para poder arrancar la plataforma con acceso total.
    * **Autoregistro anónimo**: el rol se fuerza a ``capturista`` (el mínimo
      privilegio), sin importar el rol solicitado. Un SuperAdministrador o
      Administrador puede elevarlo después desde ``PUT /auth/users/{id}``.
    * **Administrador autenticado**: puede asignar cualquier rol válido.
    """
    total_usuarios = db.query(Usuario).count()
    if total_usuarios == 0:
        datos.rol = "SuperAdministrador"
    elif not (solicitante and solicitante.rol in ("SuperAdministrador", "Administrador")):
        datos.rol = "capturista"
    usuario = crear_usuario(db, datos)
    return usuario_desde_respuesta(usuario)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión y obtener un JWT de acceso.",
)
def login(
    datos: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    """Autentica al usuario y devuelve un token de acceso (JWT)."""
    usuario = autenticar_usuario(db, datos.email, datos.password)
    if not usuario:
        usuario_inactivo = db.query(Usuario).filter(Usuario.email == datos.email).first()
        if (
            usuario_inactivo
            and not usuario_inactivo.activo
            and security.verify_password(datos.password, usuario_inactivo.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo. Comunícate con tu administrador.",
            )
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
    registrar_bitacora(
        db,
        usuario=usuario,
        accion="iniciar_sesion",
        entidad="sesiones",
        entidad_id=usuario.id,
        datos_despues={"email": usuario.email, "rol": usuario.rol},
        request=request,
    )
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Obtener el perfil del usuario autenticado.",
)
def perfil(
    usuario_actual: UsuarioActual,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Devuelve los datos del usuario y completa el código de un Administrador legado."""
    if usuario_actual.rol == "Administrador" and not usuario_actual.codigo_empresa:
        usuario_actual.codigo_empresa = generar_codigo_empresa(db)
        db.commit()
        db.refresh(usuario_actual)
    return usuario_desde_respuesta(usuario_actual)


@router.post(
    "/me/codigo-empresa",
    response_model=UsuarioRespuesta,
    summary="Obtener o generar el código de empresa del Administrador.",
)
def codigo_empresa(
    usuario_actual: UsuarioActual,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Garantiza un código empresarial para el Administrador autenticado."""
    if usuario_actual.rol != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el Administrador puede consultar el código de su empresa.",
        )
    if not usuario_actual.codigo_empresa:
        usuario_actual.codigo_empresa = generar_codigo_empresa(db)
        db.commit()
        db.refresh(usuario_actual)
    return usuario_desde_respuesta(usuario_actual)


@router.post(
    "/logout",
    response_model=ApiMensaje,
    summary="Registrar el cierre de sesión del usuario autenticado.",
)
def logout(
    request: Request,
    usuario_actual: UsuarioActual,
    db: Session = Depends(get_db),
) -> ApiMensaje:
    """Registra el cierre voluntario antes de invalidar la sesión en el cliente."""
    registrar_bitacora(
        db,
        usuario=usuario_actual,
        accion="cerrar_sesion",
        entidad="sesiones",
        entidad_id=usuario_actual.id,
        datos_antes={"email": usuario_actual.email, "rol": usuario_actual.rol},
        request=request,
    )
    return ApiMensaje(mensaje="Sesión cerrada correctamente.", detalle=None)


@router.put(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Actualizar el perfil del usuario autenticado.",
)
def actualizar_perfil(
    usuario_actual: UsuarioActual,
    cambios: PerfilActualizar,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Actualiza los datos del usuario autenticado."""
    if cambios.nombre_completo is not None:
        usuario_actual.nombre_completo = cambios.nombre_completo
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
    summary="Listar usuarios (solo SuperAdministrador).",
)
def listar_usuarios(
    _super_admin: RequiereSuperAdministrador,
    db: Session = Depends(get_db),
) -> List[UsuarioRespuesta]:
    """Devuelve todos los usuarios registrados al SuperAdministrador."""
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
    _super_admin: RequiereSuperAdministrador,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Actualiza un usuario existente; solo el SuperAdministrador puede hacerlo."""
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise DatosActaInvalidosError(
            "Usuario no encontrado.",
            detalle=f"No existe un usuario con el identificador {user_id}.",
        )
    if cambios.nombre_completo is not None:
        usuario.nombre_completo = cambios.nombre_completo
    if cambios.rol is not None:
        if usuario.id == _super_admin.id and cambios.rol != "SuperAdministrador":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No puedes cambiar el rol del SuperAdministrador actual.",
            )
        if cambios.rol == "SuperAdministrador" and usuario.id != _super_admin.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El rol SuperAdministrador pertenece únicamente al usuario actual.",
            )
        if cambios.rol not in security.ROLES_VALIDOS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Rol no válido. Roles permitidos: {', '.join(security.ROLES_VALIDOS)}.",
            )
        usuario.rol = cambios.rol
        if cambios.rol == "Administrador" and not usuario.codigo_empresa:
            usuario.codigo_empresa = generar_codigo_empresa(db)
        elif cambios.rol != "Administrador":
            usuario.codigo_empresa = None
    if cambios.activo is not None:
        usuario.activo = cambios.activo
    if cambios.password is not None:
        usuario.password_hash = security.hash_password(cambios.password)
    db.commit()
    db.refresh(usuario)
    return usuario_desde_respuesta(usuario)


@router.delete(
    "/users/{user_id}",
    response_model=ApiMensaje,
    summary="Eliminar un usuario (solo SuperAdministrador).",
)
def eliminar_usuario(
    user_id: int,
    _super_admin: RequiereSuperAdministrador,
    db: Session = Depends(get_db),
) -> ApiMensaje:
    """Elimina un usuario, excepto al SuperAdministrador de la sesión actual."""
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise DatosActaInvalidosError(
            "Usuario no encontrado.",
            detalle=f"No existe un usuario con el identificador {user_id}.",
        )
    if usuario.id == _super_admin.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No puedes eliminar tu propio usuario.",
        )
    db.delete(usuario)
    db.commit()
    return ApiMensaje(mensaje="Usuario eliminado correctamente.")
