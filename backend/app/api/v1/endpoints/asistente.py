"""Endpoints del Asistente IA interno de actas administrativas.

Expone el chat bajo /api/v1/asistente sin dependencias externas.
El chat requiere un usuario autenticado: desde la conversación se pueden crear
actas y cambiar su estatus, por lo que no puede quedar abierto al público.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps import UsuarioActual, get_db
from app.db.session import get_db
from app.services.auth_service import obtener_administrador_empresa
from app.services import asistente as motor

router = APIRouter(prefix="/asistente", tags=["Asistente IA"])


class AsistenteChatRequest(BaseModel):
    """Mensaje del usuario al asistente (con sesión guiada de creación)."""

    mensaje: str = Field(min_length=1, max_length=2000)
    folio: Optional[str] = Field(default=None, max_length=40)
    acta_id: Optional[int] = Field(default=None, ge=1)
    sesion_id: Optional[str] = Field(default=None, max_length=32)
    autor: Optional[str] = Field(default=None, max_length=150)
    modo: Literal["general", "edicion"] = "general"


class AccionChat(BaseModel):
    etiqueta: str
    accion: str
    acta_id: Optional[int] = None
    estatus: Optional[str] = None


class AsistenteChatResponse(BaseModel):
    respuesta: str
    intencion: str
    tema_valido: bool = True
    acta: Optional[Dict[str, Any]] = None
    validacion: Optional[Dict[str, Any]] = None
    resumen: Optional[Dict[str, Any]] = None
    versiones: Optional[List[Dict[str, Any]]] = None
    acciones: List[AccionChat] = Field(default_factory=list)
    requiere_acta: bool = False
    texto_borrador: Optional[str] = None
    fundamento: Optional[str] = None
    # Flujo guiado de creación: sesión, catálogo, control y PDF.
    sesion_id: Optional[str] = None
    tipo_asamblea: Optional[str] = None
    campo_solicitado: Optional[str] = None
    datos_recolectados: Optional[Dict[str, Any]] = None
    progreso: Optional[Dict[str, Any]] = None
    tipos_acta: Optional[List[Dict[str, Any]]] = None
    control_acta: Optional[Dict[str, Any]] = None
    acta_id: Optional[int] = None
    folio: Optional[str] = None
    pdf_descarga: Optional[str] = None
    texto_organizado: Optional[str] = None
    campos_edicion: Optional[List[Dict[str, str]]] = None
    cambios_propuestos: Optional[Dict[str, Any]] = None
    confirmacion_creacion: bool = False
    resumen_creacion: Optional[Dict[str, Any]] = None
    catalogo_completo_disponible: bool = False


@router.post("/chat", response_model=AsistenteChatResponse, summary="Conversar con el asistente")
def chatear(
    payload: AsistenteChatRequest,
    _usuario: UsuarioActual,
    db: Session = Depends(get_db),
) -> AsistenteChatResponse:
    """Procesa un mensaje: creación guiada, validación, estatus y versiones."""
    administrador = (
        obtener_administrador_empresa(
            db, _usuario.empresa_codigo or _usuario.codigo_empresa
        )
        if (_usuario.empresa_codigo or _usuario.codigo_empresa)
        else None
    )
    empresa = None
    if administrador:
        empresa = {
            "sociedad": administrador.nombre_sociedad,
            "rfc_sociedad": administrador.rfc_sociedad,
            "tipo_sociedad": administrador.tipo_sociedad,
            "logo_empresa": administrador.logo_empresa,
            "usar_info_empresa": administrador.usar_info_empresa,
        }
    resultado = motor.procesar_mensaje(
        db, payload.mensaje, payload.folio, payload.acta_id,
        payload.sesion_id, usuario=_usuario, empresa=empresa, modo=payload.modo,
    )
    return AsistenteChatResponse(**resultado)


@router.get("/ayuda", summary="Capacidades del asistente")
def ayuda() -> Dict[str, Any]:
    """Texto de ayuda y ejemplos de preguntas validas."""
    return {"descripcion": motor.texto_ayuda(), "sugerencias": motor.SUGERENCIAS}
