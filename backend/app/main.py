"""Punto de entrada de la API de PGAC (Página de Gestión de Actas Corporativas).

Ejecución en desarrollo::

    uvicorn app.main:app --reload --port 8000

Documentación interactiva disponible en ``/docs`` (Swagger UI) y ``/redoc``.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.endpoints.actas import ENCABEZADOS_EXPUESTOS
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import PluriActasError
from app.db.init_db import init_db
from app.db.session import engine, verificar_conexion_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("pgac")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa la base de datos y registra el arranque del servicio."""
    if settings.auto_create_tables:
        try:
            init_db()
        except Exception:  # pragma: no cover - aviso temprano de configuración
            logger.exception(
                "No se pudo preparar la base de datos. Revisa DATABASE_URL y, si usas "
                "PostgreSQL, instala el driver con: pip install -r requirements-postgres.txt"
            )
            raise

    # Verificar conectividad con la base de datos (con reintentos para PostgreSQL
    # que todavía esté arrancando en Docker).
    if not verificar_conexion_db():
        logger.warning(
            "La base de datos no está disponible. La API seguirá funcionando "
            "pero las operaciones de persistencia fallarán hasta que se restablezca "
            "la conexión."
        )

    logger.info(
        "%s v%s iniciado | entorno=%s | IA=%s",
        settings.app_name,
        settings.app_version,
        settings.environment,
        settings.proveedor_ia_configurado,
    )
    yield
    logger.info("Servicio detenido.")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "PGAC", "url": "https://pgac.example"},
    license_info={"name": "Uso interno - PGAC"},
)

# CORS: el frontend de Vite consume la API desde otro puerto en desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=ENCABEZADOS_EXPUESTOS,
)


# ---------------------------------------------------------------------------
# Manejo uniforme de errores
# ---------------------------------------------------------------------------
@app.exception_handler(PluriActasError)
async def manejar_error_dominio(request: Request, exc: PluriActasError) -> JSONResponse:
    """Traduce las excepciones de negocio a respuestas JSON con su código HTTP."""
    return JSONResponse(
        status_code=exc.codigo_http,
        content={"detail": exc.mensaje, "detalle": exc.detalle},
    )


@app.exception_handler(RequestValidationError)
async def manejar_error_validacion(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Devuelve los errores de validación del formulario de forma legible."""
    errores: List[Dict[str, str]] = [
        {
            "campo": ".".join(str(parte) for parte in error.get("loc", [])),
            "mensaje": str(error.get("msg")),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Los datos enviados no son válidos. Revisa los campos señalados.",
            "errores": errores,
        },
    )


@app.exception_handler(Exception)
async def manejar_error_inesperado(
    request: Request, exc: Exception
) -> JSONResponse:
    """Manejador global de errores inesperados (500).

    Nunca expone detalles de la pila al cliente; solo registra internamente
    y devuelve un mensaje genérico.
    """
    logger.exception("Error inesperado procesando %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor. El incidente ha sido registrado.",
            "tipo": type(exc).__name__,
        },
    )


# ---------------------------------------------------------------------------
# Rutas de sistema
# ---------------------------------------------------------------------------
@app.get("/", tags=["Sistema"], summary="Información del servicio")
def raiz() -> Dict[str, Any]:
    """Identificación del servicio y enlaces útiles."""
    return {
        "aplicacion": settings.app_name,
        "descripcion": settings.app_description,
        "version": settings.app_version,
        "documentacion": {"swagger": "/docs", "redoc": "/redoc"},
        "api": settings.api_v1_prefix,
    }


@app.get("/health", tags=["Sistema"], summary="Estado de la plataforma")
def salud() -> Dict[str, Any]:
    """Comprueba la conectividad con la base de datos y el proveedor de IA activo."""
    estado: Dict[str, Any] = {
        "aplicacion": settings.app_name,
        "version": settings.app_version,
        "entorno": settings.environment,
        "proveedor_ia": settings.proveedor_ia_configurado,
    }
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        estado["base_de_datos"] = "disponible"
    except Exception as exc:  # pragma: no cover - depende del entorno
        logger.warning("Base de datos no disponible: %s", exc)
        estado["base_de_datos"] = "no disponible"
    return estado


app.include_router(api_router, prefix=settings.api_v1_prefix)
