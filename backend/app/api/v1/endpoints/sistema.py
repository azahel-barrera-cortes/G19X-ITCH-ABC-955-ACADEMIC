"""Endpoints de sistema dentro de la API versionada.

Se publican bajo ``/api/v1/sistema`` para que el frontend pueda consultarlos a
través del mismo proxy que el resto de la API (``/health`` en la raíz se reserva
para los sondeos de infraestructura).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.services.ai_service import catalogo_proveedores

router = APIRouter(prefix="/sistema", tags=["Sistema"])


@router.get("/estado", summary="Estado del backend (base de datos y proveedor de IA)")
def estado() -> Dict[str, Any]:
    """Informa si la base de datos responde y qué proveedor de IA está activo."""
    proveedor = settings.proveedor_ia_configurado
    datos: Dict[str, Any] = {
        "aplicacion": settings.app_name,
        "version": settings.app_version,
        "entorno": settings.environment,
        "proveedor_ia": proveedor,
        "ia_habilitada": proveedor != "plantillas",
        "modelo_ia": settings.modelo_ia_activo,
        "streaming_habilitado": settings.ai_stream,
        "proveedores": catalogo_proveedores(settings),
    }
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        datos["base_de_datos"] = "disponible"
    except Exception as exc:  # pragma: no cover - depende del entorno
        datos["base_de_datos"] = "no disponible"
        datos["detalle_base_de_datos"] = str(exc)
    return datos
