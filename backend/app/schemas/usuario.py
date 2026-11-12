"""Esquemas Pydantic para usuarios, autenticación y roles."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    """Datos compartidos de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    nombre_completo: str = Field(min_length=3, max_length=200)
    rol: str = Field(
        ...,
        description="Rol del usuario: Administrador, capturista, revisor o abogado_responsable.",
    )
    activo: bool = True
    codigo_empresa: Optional[str] = None
    empresa_codigo: Optional[str] = None


class UsuarioCrear(UsuarioBase):
    """Petición de creación de usuario."""

    password: str = Field(min_length=6, max_length=128)


class InformacionEmpresa(BaseModel):
    """Información empresarial compartida por el Administrador y su empresa."""

    model_config = ConfigDict(from_attributes=True)

    nombre_sociedad: Optional[str] = Field(default=None, max_length=200)
    rfc_sociedad: Optional[str] = Field(default=None, max_length=13)
    tipo_sociedad: Optional[str] = Field(default=None, max_length=60)
    logo_empresa: Optional[str] = None
    firma_electronica: bool = False
    usar_info_empresa: bool = False


class InformacionEmpresaActualizar(InformacionEmpresa):
    """Información empresarial que el Administrador debe completar al guardar."""

    nombre_sociedad: str = Field(min_length=1, max_length=200)
    tipo_sociedad: str = Field(min_length=1, max_length=60)


class PerfilActualizar(BaseModel):
    """Lo único que un usuario puede cambiar de sí mismo."""

    nombre_completo: Optional[str] = Field(default=None, min_length=3, max_length=200)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class UsuarioActualizar(BaseModel):
    """Petición de actualización parcial de usuario."""

    nombre_completo: Optional[str] = Field(default=None, min_length=3, max_length=200)
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class UsuarioRespuesta(UsuarioBase):
    """Respuesta del usuario sin el hash de contraseña."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Token(BaseModel):
    """Respuesta de autenticación con el JWT de acceso."""

    access_token: str
    token_type: str = "bearer"


class TokenDatos(BaseModel):
    """Claims extraídos de un token válido."""

    email: Optional[str] = None
    rol: Optional[str] = None
    usuario_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Credenciales de inicio de sesión."""

    email: EmailStr
    password: str


class SolicitudResetPassword(BaseModel):
    """Petición de recuperación de contraseña (pública)."""

    email: EmailStr


class ConfirmarResetPassword(BaseModel):
    """Confirmación de recuperación con el token recibido."""

    token: str = Field(min_length=10, max_length=128)
    nuevo_password: str = Field(min_length=6, max_length=128)


class BitacoraCambiosRespuesta(BaseModel):
    """Entrada de la bitácora de cambios expuesta por la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int]
    usuario_nombre: Optional[str] = None
    usuario_rol: Optional[str] = None
    accion: str
    entidad: str
    entidad_id: Optional[int]
    datos_antes: Optional[Any]
    datos_despues: Optional[Any]
    ip_origen: Optional[str]
    user_agent: Optional[str]
    created_at: Optional[datetime]