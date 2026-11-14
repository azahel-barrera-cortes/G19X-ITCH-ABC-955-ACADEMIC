"""Endpoints de autenticación: registro de usuarios, login y perfil."""

from __future__ import annotations

import logging

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
    InformacionEmpresa,
    InformacionEmpresaActualizar,
)
from app.services.auth_service import (
    autenticar_usuario,
    crear_usuario,
    usuario_desde_respuesta,
    generar_codigo_empresa,
    crear_token_reinicio_password,
    invalidar_token_reinicio_password,
    actualizar_password_usuario,
    actualizar_password_por_token,
    obtener_administrador_empresa,
)
from app.services import email_service

logger = logging.getLogger(__name__)

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
    request: Request,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Crea un nuevo usuario aplicando reglas de rol seguras:

    * **Primer usuario del sistema** (base vacía): se crea como ``SuperAdministrador``
      para poder arrancar la plataforma con acceso total.
    * **Autoregistro anónimo**: acepta ``capturista``, ``revisor`` o
      ``abogado_responsable`` y exige un código perteneciente a un Administrador
      activo.
    * **Administrador autenticado**: puede asignar cualquier rol válido.
    """
    total_usuarios = db.query(Usuario).count()
    if total_usuarios == 0:
        datos.rol = "SuperAdministrador"
    elif solicitante and solicitante.rol == "Administrador":
        roles_empresa = ("capturista", "revisor", "abogado_responsable")
        if datos.rol not in roles_empresa:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El Administrador solo puede crear capturistas, revisores o abogados responsables.",
            )
        if not solicitante.codigo_empresa:
            solicitante.codigo_empresa = generar_codigo_empresa(db)
            db.commit()
            db.refresh(solicitante)
        datos.codigo_empresa = solicitante.codigo_empresa
    elif not (solicitante and solicitante.rol == "SuperAdministrador"):
        roles_publicos = ("capturista", "revisor", "abogado_responsable")
        if datos.rol not in roles_publicos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El rol de registro debe ser capturista, revisor o abogado_responsable.",
            )
        if not datos.codigo_empresa:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El código de empresa es obligatorio para el registro.",
            )
        datos.codigo_empresa = datos.codigo_empresa.strip().upper()
        if not obtener_administrador_empresa(db, datos.codigo_empresa):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El código de empresa no existe o no está activo.",
            )
    usuario = crear_usuario(db, datos)
    registrar_bitacora(
        db,
        usuario=solicitante,
        accion="crear",
        entidad="usuarios",
        entidad_id=usuario.id,
        datos_despues={
            "email": usuario.email,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol,
            "registrado_por": "usuario autenticado" if solicitante else "autoregistro",
        },
        request=request,
        empresa_codigo=usuario.empresa_codigo or usuario.codigo_empresa,
    )
    return usuario_desde_respuesta(usuario)


def _administrador_de_empresa(db: Session, usuario: Usuario) -> Usuario:
    if usuario.rol == "Administrador":
        return usuario
    if not usuario.empresa_codigo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no tiene una empresa vinculada.",
        )
    administrador = obtener_administrador_empresa(db, usuario.empresa_codigo)
    if not administrador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el Administrador de la empresa vinculada.",
        )
    return administrador


@router.get(
    "/me/empresa",
    response_model=InformacionEmpresa,
    summary="Obtener la información empresarial vinculada.",
)
def informacion_empresa(
    usuario_actual: UsuarioActual,
    db: Session = Depends(get_db),
) -> InformacionEmpresa:
    administrador = _administrador_de_empresa(db, usuario_actual)
    return InformacionEmpresa.model_validate(administrador)


@router.put(
    "/me/empresa",
    response_model=InformacionEmpresa,
    summary="Actualizar la información empresarial (solo Administrador).",
)
def actualizar_informacion_empresa(
    cambios: InformacionEmpresaActualizar,
    usuario_actual: UsuarioActual,
    request: Request,
    db: Session = Depends(get_db),
) -> InformacionEmpresa:
    if usuario_actual.rol != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el Administrador puede modificar la información empresarial.",
        )
    datos_antes = {}
    datos_despues = {}
    for campo, valor in cambios.model_dump().items():
        anterior = getattr(usuario_actual, campo)
        if anterior != valor:
            datos_antes[campo] = bool(anterior) if campo == "logo_empresa" else anterior
            datos_despues[campo] = bool(valor) if campo == "logo_empresa" else valor
        setattr(usuario_actual, campo, valor)
    db.commit()
    db.refresh(usuario_actual)
    if datos_despues:
        registrar_bitacora(
            db,
            usuario=usuario_actual,
            accion="actualizar",
            entidad="empresas",
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            request=request,
            empresa_codigo=usuario_actual.codigo_empresa,
        )
    return InformacionEmpresa.model_validate(usuario_actual)


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
            "token_version": usuario.token_version,
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
    request: Request,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Actualiza los datos del usuario autenticado."""
    nombre_anterior = usuario_actual.nombre_completo
    nombre_cambiado = (
        cambios.nombre_completo is not None
        and cambios.nombre_completo != nombre_anterior
    )
    password_actualizada = cambios.password is not None
    if cambios.nombre_completo is not None:
        usuario_actual.nombre_completo = cambios.nombre_completo
    if password_actualizada:
        actualizar_password_usuario(usuario_actual, cambios.password)
    db.commit()
    db.refresh(usuario_actual)
    if nombre_cambiado or password_actualizada:
        registrar_bitacora(
            db,
            usuario=usuario_actual,
            accion="actualizar",
            entidad="usuarios",
            entidad_id=usuario_actual.id,
            datos_antes={"nombre_completo": nombre_anterior},
            datos_despues={
                "nombre_completo": usuario_actual.nombre_completo,
                "password_actualizada": password_actualizada,
            },
            request=request,
        )
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
    """Envía un token temporal, sin revelar si el correo está registrado."""
    if not email_service.correo_configurado():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "La recuperación por correo aún no está configurada. "
                "Contacta al administrador del sistema."
            ),
        )

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == datos.email, Usuario.activo.is_(True))
        .first()
    )
    if usuario:
        token = crear_token_reinicio_password(usuario, db)
        try:
            email_service.enviar_correo_recuperacion(usuario.email, token)
        except email_service.ErrorEnvioCorreo:
            logger.exception(
                "Falló el envío de recuperación para usuario_id=%s", usuario.id
            )
            invalidar_token_reinicio_password(usuario.id, token, db)

    return ApiMensaje(
        mensaje=(
            "Si el correo está registrado, recibirás instrucciones para recuperar "
            "tu contraseña."
        ),
        detalle=None,
    )


@router.post(
    "/reset-password/confirm",
    response_model=ApiMensaje,
    summary="Confirmar recuperación de contraseña con token.",
)
def confirmar_reset_password(
    datos: ConfirmarResetPassword,
    request: Request,
    db: Session = Depends(get_db),
) -> ApiMensaje:
    """Confirma el cambio de contraseña usando el token de recuperación."""
    usuario = actualizar_password_por_token(db, datos.token, datos.nuevo_password)
    if usuario is None:
        raise DatosActaInvalidosError(
            "El enlace de recuperación no es válido o ha expirado.",
            detalle="El token de recuperación no es válido o ha expirado.",
        )
    registrar_bitacora(
        db,
        usuario=usuario,
        accion="cambiar_password",
        entidad="usuarios",
        entidad_id=usuario.id,
        datos_despues={"password_actualizada": True},
        request=request,
    )
    return ApiMensaje(
        mensaje="Contraseña actualizada. Ya puedes iniciar sesión.",
        detalle=None,
    )


@router.get(
    "/users",
    response_model=List[UsuarioRespuesta],
    summary="Listar usuarios del sistema o de la empresa del Administrador.",
)
def listar_usuarios(
    usuario_actual: UsuarioActual,
    request: Request,
    db: Session = Depends(get_db),
) -> List[UsuarioRespuesta]:
    """SuperAdministrador ve todos los usuarios; Administrador, solo su empresa."""
    consulta = db.query(Usuario)
    if usuario_actual.rol == "Administrador":
        if not usuario_actual.codigo_empresa:
            usuario_actual.codigo_empresa = generar_codigo_empresa(db)
            db.commit()
            db.refresh(usuario_actual)
            registrar_bitacora(
                db,
                usuario=usuario_actual,
                accion="crear_codigo_empresa",
                entidad="empresas",
                datos_despues={"codigo_empresa": usuario_actual.codigo_empresa},
                request=request,
                empresa_codigo=usuario_actual.codigo_empresa,
            )
        consulta = consulta.filter(
            Usuario.empresa_codigo == usuario_actual.codigo_empresa,
            Usuario.rol.in_(("capturista", "revisor", "abogado_responsable")),
        )
    elif usuario_actual.rol != "SuperAdministrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere el rol 'Administrador' o 'SuperAdministrador'.",
        )
    usuarios = consulta.order_by(Usuario.email).all()
    return [usuario_desde_respuesta(u) for u in usuarios]


@router.put(
    "/users/{user_id}",
    response_model=UsuarioRespuesta,
    summary="Actualizar un usuario (solo Admin).",
)
def actualizar_usuario(
    user_id: int,
    cambios: UsuarioActualizar,
    usuario_actual: UsuarioActual,
    request: Request,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    """Actualiza un usuario globalmente o dentro de la empresa del Administrador."""
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise DatosActaInvalidosError(
            "Usuario no encontrado.",
            detalle=f"No existe un usuario con el identificador {user_id}.",
        )
    es_super_admin = usuario_actual.rol == "SuperAdministrador"
    if not es_super_admin:
        if usuario_actual.rol != "Administrador":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requiere el rol 'Administrador' o 'SuperAdministrador'.",
            )
        if (
            not usuario_actual.codigo_empresa
            or usuario.empresa_codigo != usuario_actual.codigo_empresa
            or usuario.rol not in ("capturista", "revisor", "abogado_responsable")
        ):
            raise DatosActaInvalidosError(
                "Usuario no encontrado.",
                detalle=f"No existe un usuario con el identificador {user_id}.",
            )
        if cambios.rol is not None and cambios.rol not in (
            "capturista",
            "revisor",
            "abogado_responsable",
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El Administrador solo puede asignar capturista, revisor o abogado_responsable.",
            )

    datos_antes = {
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol,
        "activo": usuario.activo,
    }
    if cambios.nombre_completo is not None:
        usuario.nombre_completo = cambios.nombre_completo
    if cambios.rol is not None:
        if usuario.id == usuario_actual.id and cambios.rol != "SuperAdministrador":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No puedes cambiar el rol del SuperAdministrador actual.",
            )
        if cambios.rol == "SuperAdministrador" and usuario.id != usuario_actual.id:
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
        actualizar_password_usuario(usuario, cambios.password)
    db.commit()
    db.refresh(usuario)
    datos_despues = {
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol,
        "activo": usuario.activo,
        "password_actualizada": cambios.password is not None,
    }
    datos_actualizados = {
        clave: valor
        for clave, valor in datos_despues.items()
        if clave != "password_actualizada"
    }
    if datos_antes != datos_actualizados or cambios.password is not None:
        registrar_bitacora(
            db,
            usuario=usuario_actual,
            accion="actualizar",
            entidad="usuarios",
            entidad_id=usuario.id,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            request=request,
            empresa_codigo=usuario.empresa_codigo or usuario.codigo_empresa,
        )
    return usuario_desde_respuesta(usuario)


@router.delete(
    "/users/{user_id}",
    response_model=ApiMensaje,
    summary="Eliminar un usuario (solo SuperAdministrador).",
)
def eliminar_usuario(
    user_id: int,
    _super_admin: RequiereSuperAdministrador,
    request: Request,
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
    datos_antes = {
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol,
    }
    empresa_codigo = usuario.empresa_codigo or usuario.codigo_empresa
    db.delete(usuario)
    db.commit()
    registrar_bitacora(
        db,
        usuario=_super_admin,
        accion="eliminar",
        entidad="usuarios",
        entidad_id=user_id,
        datos_antes=datos_antes,
        datos_despues={"eliminado": True},
        request=request,
        empresa_codigo=empresa_codigo,
    )
    return ApiMensaje(mensaje="Usuario eliminado correctamente.")
