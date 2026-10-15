"""Capa de proveedores de LLM: transporte, reintentos y streaming.

Esta capa aísla **cómo** se habla con el modelo (HTTP, credenciales, reintentos,
formato de respuesta) de **qué** se le pide (los *prompts*, que viven en
``ai_service``). Así es posible añadir proveedores nuevos sin tocar la lógica
legal.

Proveedores implementados:

* ``azure_openai``      — Azure OpenAI (chat completions con ``api-key``).
* ``gemini``            — Google Gemini (``generateContent`` / SSE).
* ``openai_compatible`` — cualquier API compatible con OpenAI mediante
  ``Authorization: Bearer``: OpenAI, Ollama (`http://localhost:11434/v1`),
  Groq, DeepSeek, LM Studio, vLLM… Esto permite usar un **LLM 100 % local** y no
  enviar información societaria confidencial a terceros.

Características de robustez:

* **Reintentos** con backoff exponencial y *jitter* en errores transitorios
  (408/409/425/429/5xx y fallos de red); nunca se reintenta un 400/401/403 porque
  son errores permanentes.
* **Degradación del modo JSON**: si el despliegue rechaza ``response_format`` o
  ``responseMimeType``, se reintenta una vez sin ellos y se extrae el JSON del
  texto resultante.
* **Streaming**: ``chat_stream`` entrega el texto por fragmentos para mostrarlo en
  vivo en la interfaz (SSE).
"""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Códigos HTTP que sí conviene reintentar (el resto son permanentes).
CODIGOS_REINTENTABLES = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
ESPERA_BASE = 0.9      # segundos del primer backoff
ESPERA_MAXIMA = 8.0    # techo del backoff


class ErrorLLM(Exception):
    """Fallo al comunicarse con un proveedor de LLM."""

    def __init__(
        self,
        mensaje: str,
        *,
        proveedor: str,
        permanente: bool = False,
        intentos: int = 1,
        causa: Optional[BaseException] = None,
    ) -> None:
        super().__init__(mensaje)
        self.proveedor = proveedor
        self.permanente = permanente
        self.intentos = intentos
        self.causa = causa


@dataclass
class ResultadoLLM:
    """Respuesta de un proveedor junto con su información de ejecución."""

    texto: str
    proveedor: str
    modelo: str
    latencia_ms: int = 0
    reintentos: int = 0
    tokens_prompt: Optional[int] = None
    tokens_salida: Optional[int] = None
    json_mode: bool = True

    def a_dict(self) -> Dict[str, Any]:
        """Representación serializable (se persiste en ``meta_ia`` del acta)."""
        return {
            "proveedor": self.proveedor,
            "modelo": self.modelo,
            "latencia_ms": self.latencia_ms,
            "reintentos": self.reintentos,
            "tokens_prompt": self.tokens_prompt,
            "tokens_salida": self.tokens_salida,
            "json_mode": self.json_mode,
        }

def _dormir(intento: int) -> None:
    """Espera entre reintentos con backoff exponencial y *jitter* aleatorio."""
    espera = min(ESPERA_BASE * (2 ** (intento - 1)), ESPERA_MAXIMA)
    time.sleep(espera + random.uniform(0, 0.35))


def _con_reintentos(
    operacion: Any,
    *,
    proveedor: str,
    max_intentos: int,
) -> Any:
    """Ejecuta ``operacion(intento)`` reintentando solo errores transitorios.

    Devuelve el valor producido por la operación; lanza :class:`ErrorLLM` cuando se
    agotan los intentos o cuando el error es permanente.
    """
    ultimo: Optional[BaseException] = None

    for intento in range(1, max(1, max_intentos) + 1):
        try:
            return operacion(intento)
        except httpx.HTTPStatusError as exc:
            estado = exc.response.status_code
            if estado not in CODIGOS_REINTENTABLES:
                # 400/401/403/404/422: reintentar no sirve.
                raise ErrorLLM(
                    f"El proveedor {proveedor} rechazó la solicitud (HTTP {estado}): "
                    f"{exc.response.text[:300]}",
                    proveedor=proveedor,
                    permanente=True,
                    intentos=intento,
                    causa=exc,
                ) from exc
            ultimo = exc
            logger.warning(
                "Proveedor %s respondió HTTP %s (intento %s/%s); se reintenta.",
                proveedor,
                estado,
                intento,
                max_intentos,
            )
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            ultimo = exc
            logger.warning(
                "Fallo de red con %s (intento %s/%s): %s",
                proveedor,
                intento,
                max_intentos,
                type(exc).__name__,
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            # Respuesta con estructura inesperada: no se reintenta.
            raise ErrorLLM(
                f"Respuesta inesperada del proveedor {proveedor}: {type(exc).__name__}.",
                proveedor=proveedor,
                permanente=True,
                intentos=intento,
                causa=exc,
            ) from exc

        if intento < max_intentos:
            _dormir(intento)

    raise ErrorLLM(
        f"El proveedor {proveedor} no respondió tras {max_intentos} intentos "
        f"({type(ultimo).__name__ if ultimo else 'error desconocido'}).",
        proveedor=proveedor,
        permanente=False,
        intentos=max_intentos,
        causa=ultimo,
    )

class ProveedorLLM:
    """Implementación genérica HTTP de un proveedor de *chat completions*.

    Las subclases solo describen **cómo** construir la petición y **dónde** leer el
    texto de la respuesta; los reintentos, el modo JSON, los tiempos de espera y el
    streaming se resuelven aquí una sola vez.
    """

    nombre: str = "generico"
    soporta_json = True
    soporta_stream = True

    def __init__(self, config: Settings) -> None:
        self.config = config

    # ------------------------------------------------------- descripción HTTP
    @property
    def modelo(self) -> str:  # pragma: no cover - sobrescrito
        return "desconocido"

    def _url(self) -> str:  # pragma: no cover - sobrescrito
        raise NotImplementedError

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _params(self) -> Dict[str, Any]:
        return {}

    def _cuerpo(
        self, sistema: str, usuario: str, *, json_mode: bool, max_tokens: int, stream: bool
    ) -> Dict[str, Any]:  # pragma: no cover - sobrescrito
        raise NotImplementedError

    def _leer_texto(self, datos: Dict[str, Any]) -> str:  # pragma: no cover
        raise NotImplementedError

    def _leer_delta(self, datos: Dict[str, Any]) -> str:  # pragma: no cover
        raise NotImplementedError

    def _leer_uso(self, datos: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
        """Tokens de entrada y salida, cuando el proveedor los informa."""
        uso = datos.get("usage") or datos.get("usageMetadata") or {}
        entrada = uso.get("prompt_tokens") or uso.get("promptTokenCount")
        salida = uso.get("completion_tokens") or uso.get("candidatesTokenCount")
        return entrada, salida

    def _cliente(self) -> httpx.Client:
        """Cliente HTTP con tiempos de espera explícitos (lectura = ``AI_TIMEOUT``).

        Se usa el cliente **síncrono** porque todo el servicio de IA se invoca desde
        handlers ``def`` de FastAPI (que ya corren en un *threadpool*); anidar un
        event loop obligaría a hacer la API entera asíncrona sin beneficio real.
        """
        limite = httpx.Timeout(
            connect=10.0,
            read=float(self.config.ai_timeout_seconds),
            write=30.0,
            pool=10.0,
        )
        return httpx.Client(timeout=limite, follow_redirects=True)

    # ----------------------------------------------------------- operaciones
    def chat(
        self,
        sistema: str,
        usuario: str,
        *,
        json_mode: Optional[bool] = None,
        max_tokens: Optional[int] = None,
    ) -> ResultadoLLM:
        """Envía el par de mensajes y devuelve el texto con su trazabilidad."""
        usar_json = self.config.ai_json_mode if json_mode is None else json_mode
        if not self.soporta_json:
            usar_json = False
        limite = max_tokens or self.config.ai_max_tokens
        inicio = time.perf_counter()
        reintentos_previos = 0

        def intentar(cliente: httpx.Client, forzar_json: bool) -> ResultadoLLM:
            def operacion(_intento: int) -> ResultadoLLM:
                respuesta = cliente.post(
                    self._url(),
                    headers=self._headers(),
                    params=self._params(),
                    json=self._cuerpo(
                        sistema,
                        usuario,
                        json_mode=forzar_json,
                        max_tokens=limite,
                        stream=False,
                    ),
                )
                respuesta.raise_for_status()
                datos = respuesta.json()
                entrada, salida = self._leer_uso(datos)
                return ResultadoLLM(
                    texto=self._leer_texto(datos),
                    proveedor=self.nombre,
                    modelo=self.modelo,
                    latencia_ms=int((time.perf_counter() - inicio) * 1000),
                    reintentos=reintentos_previos,
                    tokens_prompt=entrada,
                    tokens_salida=salida,
                    json_mode=forzar_json,
                )

            return _con_reintentos(
                operacion,
                proveedor=self.nombre,
                max_intentos=self.config.ai_max_reintentos,
            )

        with self._cliente() as cliente:
            try:
                return intentar(cliente, usar_json)
            except ErrorLLM as error:
                # Segundo intento sin modo JSON: algunos despliegues no lo soportan.
                if usar_json and error.permanente and "400" in str(error):
                    logger.warning(
                        "El proveedor %s no aceptó el modo JSON; se reintenta en texto libre.",
                        self.nombre,
                    )
                    reintentos_previos = error.intentos
                    return intentar(cliente, False)
                raise

    def chat_stream(
        self,
        sistema: str,
        usuario: str,
        *,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Entrega el texto por fragmentos (SSE) para mostrarlo en vivo."""
        if not self.soporta_stream:
            resultado = self.chat(sistema, usuario, json_mode=False, max_tokens=max_tokens)
            yield from trocear(resultado.texto)
            return

        limite = max_tokens or self.config.ai_max_tokens
        cuerpo = self._cuerpo(sistema, usuario, json_mode=False, max_tokens=limite, stream=True)

        with self._cliente() as cliente:
            with cliente.stream(
                "POST",
                self._url(),
                headers=self._headers(),
                params=self._params(),
                json=cuerpo,
            ) as respuesta:
                respuesta.raise_for_status()
                for linea in respuesta.iter_lines():
                    fragmento = _leer_linea_sse(linea, self._leer_delta)
                    if fragmento:
                        yield fragmento

def trocear(texto: str, tamano: int = 24) -> List[str]:
    """Parte un texto en fragmentos (para simular *streaming* del modo plantillas)."""
    if not texto:
        return []
    piezas = texto.split(" ")
    fragmentos: List[str] = []
    actual: List[str] = []
    longitud = 0
    for palabra in piezas:
        actual.append(palabra)
        longitud += len(palabra) + 1
        if longitud >= tamano:
            fragmentos.append(" ".join(actual) + " ")
            actual = []
            longitud = 0
    if actual:
        fragmentos.append(" ".join(actual))
    return fragmentos


def _leer_linea_sse(linea: str, lector: Any) -> str:
    """Extrae el fragmento de texto de una línea ``data: {...}`` de un flujo SSE."""
    if not linea or not linea.startswith("data:"):
        return ""
    carga = linea[5:].strip()
    if not carga or carga == "[DONE]":
        return ""
    try:
        datos = json.loads(carga)
    except json.JSONDecodeError:
        return ""
    try:
        return lector(datos) or ""
    except (KeyError, IndexError, TypeError, AttributeError):
        return ""


# ---------------------------------------------------------------------------
# Proveedores concretos
# ---------------------------------------------------------------------------
class ProveedorAzureOpenAI(ProveedorLLM):
    """Azure OpenAI — ``/openai/deployments/{deployment}/chat/completions``."""

    nombre = "azure_openai"

    @property
    def modelo(self) -> str:
        return self.config.azure_openai_deployment

    def _url(self) -> str:
        return (
            f"{self.config.azure_openai_endpoint.rstrip('/')}/openai/deployments/"
            f"{self.config.azure_openai_deployment}/chat/completions"
        )

    def _headers(self) -> Dict[str, str]:
        return {"api-key": self.config.azure_openai_api_key, "Content-Type": "application/json"}

    def _params(self) -> Dict[str, Any]:
        return {"api-version": self.config.azure_openai_api_version}

    def _cuerpo(self, sistema, usuario, *, json_mode, max_tokens, stream) -> Dict[str, Any]:
        cuerpo: Dict[str, Any] = {
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            "temperature": self.config.ai_temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            cuerpo["response_format"] = {"type": "json_object"}
        if stream:
            cuerpo["stream"] = True
        return cuerpo

    def _leer_texto(self, datos: Dict[str, Any]) -> str:
        return datos["choices"][0]["message"]["content"]

    def _leer_delta(self, datos: Dict[str, Any]) -> str:
        return (datos["choices"][0].get("delta") or {}).get("content") or ""


class ProveedorOpenAICompatible(ProveedorLLM):
    """Cualquier API compatible con OpenAI (OpenAI, Ollama, Groq, LM Studio…).

    Solo se requiere ``AI_BASE_URL`` y ``AI_MODEL``; ``AI_API_KEY`` es opcional
    para que funcione con un servidor local como Ollama o LM Studio.
    """

    nombre = "openai_compatible"

    @property
    def modelo(self) -> str:
        return self.config.ai_model

    def _url(self) -> str:
        return f"{self.config.ai_base_url.rstrip('/')}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        cabeceras = {"Content-Type": "application/json"}
        if self.config.ai_api_key:
            cabeceras["Authorization"] = f"Bearer {self.config.ai_api_key}"
        return cabeceras

    def _cuerpo(self, sistema, usuario, *, json_mode, max_tokens, stream) -> Dict[str, Any]:
        cuerpo: Dict[str, Any] = {
            "model": self.config.ai_model,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            "temperature": self.config.ai_temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            cuerpo["response_format"] = {"type": "json_object"}
        if stream:
            cuerpo["stream"] = True
        return cuerpo

    def _leer_texto(self, datos: Dict[str, Any]) -> str:
        return datos["choices"][0]["message"]["content"]

    def _leer_delta(self, datos: Dict[str, Any]) -> str:
        return (datos["choices"][0].get("delta") or {}).get("content") or ""

class ProveedorGemini(ProveedorLLM):
    """Google Gemini — ``generateContent`` (y ``streamGenerateContent`` para SSE)."""

    nombre = "gemini"

    @property
    def modelo(self) -> str:
        return self.config.gemini_model

    def _url(self) -> str:
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.config.gemini_model}:generateContent"
        )

    def _headers(self) -> Dict[str, str]:
        return {"x-goog-api-key": self.config.gemini_api_key, "Content-Type": "application/json"}

    def _cuerpo(self, sistema, usuario, *, json_mode, max_tokens, stream) -> Dict[str, Any]:
        configuracion: Dict[str, Any] = {
            "temperature": self.config.ai_temperature,
            "maxOutputTokens": max_tokens,
        }
        if json_mode:
            configuracion["responseMimeType"] = "application/json"
        return {
            "systemInstruction": {"parts": [{"text": sistema}]},
            "contents": [{"role": "user", "parts": [{"text": usuario}]}],
            "generationConfig": configuracion,
        }

    def _leer_texto(self, datos: Dict[str, Any]) -> str:
        return datos["candidates"][0]["content"]["parts"][0]["text"]

    def _leer_delta(self, datos: Dict[str, Any]) -> str:
        partes = datos["candidates"][0].get("content", {}).get("parts") or []
        return "".join(parte.get("text") or "" for parte in partes)

    def chat_stream(
        self, sistema: str, usuario: str, *, max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """Gemini transmite por SSE con ``alt=sse`` en lugar de ``stream: true``."""
        limite = max_tokens or self.config.ai_max_tokens
        cuerpo = self._cuerpo(sistema, usuario, json_mode=False, max_tokens=limite, stream=True)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.config.gemini_model}:streamGenerateContent"
        )

        with self._cliente() as cliente:
            with cliente.stream(
                "POST",
                url,
                headers=self._headers(),
                params={"alt": "sse"},
                json=cuerpo,
            ) as respuesta:
                respuesta.raise_for_status()
                for linea in respuesta.iter_lines():
                    fragmento = _leer_linea_sse(linea, self._leer_delta)
                    if fragmento:
                        yield fragmento


# ---------------------------------------------------------------------------
# Fábrica
# ---------------------------------------------------------------------------
CLASES_PROVEEDOR: Dict[str, type[ProveedorLLM]] = {
    "azure_openai": ProveedorAzureOpenAI,
    "openai_compatible": ProveedorOpenAICompatible,
    "gemini": ProveedorGemini,
}


def crear_proveedor(nombre: str, config: Settings) -> Optional[ProveedorLLM]:
    """Crea el proveedor indicado; ``None`` cuando corresponde a plantillas.

    Devuelve ``None`` si el nombre es ``plantillas`` o si falta alguna credencial,
    de modo que quien invoca pueda degradar a la redacción determinista.
    """
    clase = CLASES_PROVEEDOR.get((nombre or "").strip().lower())
    if clase is None:
        return None

    # Verificación temprana de credenciales por proveedor.
    if clase is ProveedorAzureOpenAI and not (
        config.azure_openai_endpoint and config.azure_openai_api_key
    ):
        return None
    if clase is ProveedorGemini and not config.gemini_api_key:
        return None
    if clase is ProveedorOpenAICompatible and not (config.ai_base_url and config.ai_model):
        return None

    return clase(config)


def catalogo_proveedores(config: Settings) -> List[Dict[str, Any]]:
    """Describe la disponibilidad de cada proveedor (para el endpoint de estado)."""
    return [
        {
            "nombre": "azure_openai",
            "modelo": config.azure_openai_deployment,
            "disponible": bool(config.azure_openai_endpoint and config.azure_openai_api_key),
        },
        {
            "nombre": "gemini",
            "modelo": config.gemini_model,
            "disponible": bool(config.gemini_api_key),
        },
        {
            "nombre": "openai_compatible",
            "modelo": config.ai_model or "(AI_MODEL sin definir)",
            "disponible": bool(config.ai_base_url and config.ai_model),
        },
        {
            "nombre": "plantillas",
            "modelo": "plantillas-legales",
            "disponible": True,
        },
    ]