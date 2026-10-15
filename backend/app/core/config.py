"""Configuración central de PGAC (Página de Gestión de Actas Corporativas)."""

Todos los valores pueden sobrescribirse mediante variables de entorno o a través
del archivo ``backend/.env`` (ver ``.env.example``). Se utiliza ``pydantic-settings``
para que la configuración esté tipada y validada en el arranque.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py  ->  parents[2] == carpeta `backend/`
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Parámetros de ejecución de la API, la base de datos, el PDF y la IA."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicación ---------------------------------------------------------
    app_name: str = "GICORP / PluriActas"
    app_description: str = (
        "Plataforma de Generación Inteligente de Actas Corporativas: redacción "
        "asistida por IA, validación de consistencia y exportación determinista a PDF."
    )
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Base de datos ------------------------------------------------------
    # Producción: postgresql+psycopg://usuario:clave@host:5432/pluriactas
    # Desarrollo: sqlite:///./pluriactas.db   (no requiere servidor)
    database_url: str = "sqlite:///./pluriactas.db"
    auto_create_tables: bool = True
    sql_echo: bool = False

    # --- Maquetado del PDF (ReportLab) --------------------------------------
    margen_cm: float = 2.5
    incluir_numeracion_paginas: bool = True
    pie_confidencialidad: str = (
        "Documento confidencial generado electrónicamente por GICORP / PluriActas. "
        "Su contenido es informativo y no sustituye la revisión de un abogado corporativo."
    )

    # --- Inteligencia Artificial -------------------------------------------
    # auto | azure_openai | gemini | plantillas
    ai_provider: str = "auto"
    ai_allow_fallback: bool = True
    ai_timeout_seconds: float = 45.0
    ai_temperature: float = 0.2
    ai_max_tokens: int = 1500
    # Robustez y rendimiento
    ai_max_reintentos: int = 3          # intentos por proveedor (con backoff exponencial)
    ai_max_concurrency: int = 4         # acuerdos redactados en paralelo
    ai_stream: bool = True              # expone el endpoint SSE de redacción en vivo
    ai_json_mode: bool = True           # fuerza JSON estructurado en el proveedor
    ai_verificar_fidelidad: bool = True # audita que el texto no invente cifras
    ai_max_clausulas_por_llamada: int = 3  # >1 agrupa acuerdos en una sola petición
    # Proveedor genérico compatible con OpenAI (OpenAI, Ollama, Groq, LM Studio,
    # DeepSeek, vLLM…). Permite ejecutar un LLM 100 % local, sin enviar el acta a
    # terceros, lo que resulta ideal para información societaria confidencial.
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-10-21"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    # --- Derivados ----------------------------------------------------------
    @property
    def cors_origins_list(self) -> List[str]:
        """Orígenes CORS como lista, ignorando entradas vacías."""
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]

    @property
    def es_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def proveedor_ia_configurado(self) -> str:
        """Proveedor de IA realmente utilizable según las credenciales presentes.

        Devuelve ``plantillas`` cuando no hay credenciales o cuando el proveedor
        solicitado no está correctamente configurado; de ese modo la plataforma
        nunca queda inoperante por falta de un servicio externo.
        """
        solicitado = (self.ai_provider or "auto").strip().lower()

        tiene_azure = bool(self.azure_openai_endpoint and self.azure_openai_api_key)
        tiene_gemini = bool(self.gemini_api_key)
        tiene_compatible = bool(self.ai_base_url and self.ai_model)

        if solicitado == "azure_openai":
            return "azure_openai" if tiene_azure else "plantillas"
        if solicitado == "gemini":
            return "gemini" if tiene_gemini else "plantillas"
        if solicitado == "openai_compatible":
            return "openai_compatible" if tiene_compatible else "plantillas"
        if solicitado == "plantillas":
            return "plantillas"

        # auto (o valor desconocido): prioriza Azure OpenAI, luego Gemini y por
        # último cualquier endpoint compatible con OpenAI (incluido un LLM local).
        if tiene_azure:
            return "azure_openai"
        if tiene_gemini:
            return "gemini"
        if tiene_compatible:
            return "openai_compatible"
        return "plantillas"

    @property
    def proveedor_ia_alterno(self) -> str:
        """Proveedor de respaldo para el segundo nivel de degradación.

        Si el principal falla se intenta el siguiente proveedor con credenciales
        disponibles; cuando no hay alternativa devuelve ``plantillas``.
        """
        principal = self.proveedor_ia_configurado
        disponibles = [
            nombre
            for nombre, credenciales in (
                ("azure_openai", bool(self.azure_openai_endpoint and self.azure_openai_api_key)),
                ("gemini", bool(self.gemini_api_key)),
                ("openai_compatible", bool(self.ai_base_url and self.ai_model)),
            )
            if credenciales and nombre != principal
        ]
        return disponibles[0] if disponibles else "plantillas"

    @property
    def modelo_ia_activo(self) -> str:
        """Nombre del modelo que se usará con el proveedor principal."""
        proveedor = self.proveedor_ia_configurado
        if proveedor == "azure_openai":
            return self.azure_openai_deployment
        if proveedor == "gemini":
            return self.gemini_model
        if proveedor == "openai_compatible":
            return self.ai_model
        return "plantillas-legales"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada) de la aplicación."""
    return Settings()


settings = get_settings()
