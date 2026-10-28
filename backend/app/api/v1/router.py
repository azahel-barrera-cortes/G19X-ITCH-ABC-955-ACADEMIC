"""Router principal de la API v1.

Agrupa los *routers* de cada módulo funcional. Para añadir un módulo nuevo
(p. ej. sociedades o usuarios) basta con importarlo e incluirlo aquí.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    actas,
    administracion,
    asistente,
    auth,
    bitacora,
    expediente,
    notaria,
    sistema,
)

api_router = APIRouter()
api_router.include_router(sistema.router)
# El módulo de administración se registra antes que /actas para que sus rutas
# explícitas (/administracion/...) no queden interpretadas como {acta_id}.
api_router.include_router(administracion.router)
api_router.include_router(auth.router)
api_router.include_router(bitacora.router)
api_router.include_router(asistente.router)
api_router.include_router(actas.router)
api_router.include_router(expediente.router)
api_router.include_router(notaria.router)

__all__ = ["api_router"]
