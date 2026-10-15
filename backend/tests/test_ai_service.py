"""Pruebas del servicio de IA en modo plantillas (sin servicios externos)."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, List, Optional

import pytest

from app.core.config import Settings
from app.schemas.acta import ActaRedaccionRequest
from app.services import ai_service as modulo
from app.services.ai_service import (
    AIService,
    cifras_no_sustentadas,
    crear_servicio_ia,
    extraer_json,
)
from app.services.llm_providers import (
    ErrorLLM,
    ResultadoLLM,
    catalogo_proveedores,
    crear_proveedor,
)


def _sin_guardar(payload: dict) -> dict:
    """El formulario de las pruebas incluye ``guardar``, que no pertenece al acta."""
    return {clave: valor for clave, valor in payload.items() if clave != "guardar"}


def _config_plantillas() -> Settings:
    return Settings(
        ai_provider="plantillas",
        azure_openai_endpoint="",
        azure_openai_api_key="",
        gemini_api_key="",
    )


@pytest.fixture()
def acta(payload_acta: dict) -> ActaRedaccionRequest:
    return ActaRedaccionRequest(**_sin_guardar(payload_acta))


def test_sin_credenciales_usa_plantillas() -> None:
    servicio = AIService(
        Settings(
            ai_provider="auto",
            azure_openai_endpoint="",
            azure_openai_api_key="",
            gemini_api_key="",
        )
    )
    assert servicio.ia_habilitada is False
    assert servicio.proveedor.value == "plantillas"


def test_detecta_proveedor_azure() -> None:
    servicio = AIService(
        Settings(
            ai_provider="auto",
            azure_openai_endpoint="https://ejemplo.openai.azure.com",
            azure_openai_api_key="clave-de-prueba",
            gemini_api_key="",
        )
    )
    assert servicio.proveedor.value == "azure_openai"
    assert servicio.ia_habilitada is True


def test_redactar_acuerdos_completa_las_clausulas(acta: ActaRedaccionRequest) -> None:
    servicio = crear_servicio_ia(_config_plantillas())
    acuerdos = servicio.redactar_acuerdos(acta)

    assert len(acuerdos) == len(acta.acuerdos)
    for acuerdo in acuerdos:
        assert acuerdo.clausula_legal
        assert "Ley General de Sociedades Mercantiles" in (acuerdo.fundamento_legal or "")
        assert acuerdo.generado_por_ia is False
        assert acuerdo.resumen  # el contenido del usuario se conserva


def test_detecta_la_materia_del_acuerdo_de_capital(acta: ActaRedaccionRequest) -> None:
    servicio = crear_servicio_ia(_config_plantillas())
    acuerdos = servicio.redactar_acuerdos(acta)
    assert acuerdos[0].materia == "aumento_capital"


def test_validacion_de_acta_completa_es_alta(acta: ActaRedaccionRequest) -> None:
    servicio = crear_servicio_ia(_config_plantillas())
    acuerdos = servicio.redactar_acuerdos(acta)
    con_clausulas = acta.model_copy(update={"acuerdos": acuerdos})

    validacion = servicio.validar_acta(con_clausulas)

    assert 0 <= validacion.puntaje <= 100
    assert validacion.puntaje >= 95
    assert validacion.generado_por_ia is False
    assert validacion.recomendaciones


def test_validacion_marca_quorum_critico(payload_quorum_insuficiente: dict) -> None:
    acta = ActaRedaccionRequest(**_sin_guardar(payload_quorum_insuficiente))
    validacion = crear_servicio_ia(_config_plantillas()).validar_acta(acta)

    criticos = [h for h in validacion.hallazgos if h.severidad == "critico"]
    assert criticos, "Se esperaba al menos un hallazgo crítico por quórum insuficiente"
    assert any(h.campo == "quorum_porcentaje" for h in criticos)
    assert any(h.campo == "convocatoria_fecha" for h in validacion.hallazgos)
    assert validacion.puntaje < 100


def test_extraer_json_con_vallas_markdown() -> None:
    texto = 'Respuesta:\n```json\n{"puntaje": 90, "consistencia": "ok"}\n```'
    datos = extraer_json(texto)
    assert datos is not None and datos["puntaje"] == 90


def test_extraer_json_sin_json_devuelve_none() -> None:
    assert extraer_json("respuesta sin estructura") is None
    assert extraer_json(None) is None


# ===========================================================================
# Capa de proveedores de LLM
# ===========================================================================
def test_config_sin_credenciales_usa_plantillas() -> None:
    config = Settings(
        ai_provider="auto",
        azure_openai_endpoint="",
        azure_openai_api_key="",
        gemini_api_key="",
        ai_base_url="",
        ai_model="",
        ai_api_key="",
    )
    assert config.proveedor_ia_configurado == "plantillas"
    assert config.modelo_ia_activo == "plantillas-legales"


def test_config_prioriza_azure_sobre_gemini() -> None:
    config = Settings(
        ai_provider="auto",
        azure_openai_endpoint="https://ejemplo.openai.azure.com",
        azure_openai_api_key="clave",
        gemini_api_key="clave-gemini",
        ai_base_url="",
        ai_model="",
        ai_api_key="",
    )
    assert config.proveedor_ia_configurado == "azure_openai"
    assert config.modelo_ia_activo == "gpt-4o"


def test_config_detecta_endpoint_local_compatible() -> None:
    """Un LLM local (Ollama/LM Studio) debe habilitarse sin clave de API."""
    config = Settings(
        ai_provider="auto",
        azure_openai_endpoint="",
        azure_openai_api_key="",
        gemini_api_key="",
        ai_base_url="http://localhost:11434/v1",
        ai_model="llama3.1:8b",
        ai_api_key="",
    )
    assert config.proveedor_ia_configurado == "openai_compatible"
    assert crear_proveedor("openai_compatible", config) is not None


def test_crear_proveedor_sin_credenciales_devuelve_none() -> None:
    vacio = Settings(
        azure_openai_endpoint="",
        azure_openai_api_key="",
        gemini_api_key="",
        ai_base_url="",
        ai_model="",
        ai_api_key="",
    )
    assert crear_proveedor("azure_openai", vacio) is None
    assert crear_proveedor("gemini", vacio) is None
    assert crear_proveedor("openai_compatible", vacio) is None
    assert crear_proveedor("plantillas", vacio) is None


def test_catalogo_de_proveedores_informa_disponibilidad() -> None:
    catalogo = catalogo_proveedores(_config_plantillas())
    por_nombre = {item["nombre"]: item for item in catalogo}
    assert set(por_nombre) == {
        "azure_openai",
        "gemini",
        "openai_compatible",
        "plantillas",
    }
    assert por_nombre["plantillas"]["disponible"] is True


# ===========================================================================
# Proveedor simulado: verifica la redacción con IA sin salir a la red
# ===========================================================================
class ProveedorFalso:
    """Proveedor mínimo que sustituye a un LLM real en las pruebas."""

    nombre = "azure_openai"
    modelo = "modelo-de-prueba"

    def __init__(self, texto: str, *, falla: bool = False) -> None:
        self.texto = texto
        self.falla = falla
        self.llamadas = 0

    def chat(
        self,
        sistema: str,
        usuario: str,
        *,
        json_mode: bool = True,
        max_tokens: Optional[int] = None,
    ) -> ResultadoLLM:
        self.llamadas += 1
        if self.falla:
            raise ErrorLLM("Proveedor no disponible", proveedor=self.nombre, intentos=3)
        return ResultadoLLM(
            texto=self.texto,
            proveedor=self.nombre,
            modelo=self.modelo,
            latencia_ms=1,
            tokens_prompt=10,
            tokens_salida=20,
        )

    def chat_stream(
        self, sistema: str, usuario: str, *, max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        for palabra in self.texto.split(" "):
            yield palabra + " "


def _config_con_azure() -> Settings:
    return Settings(
        ai_provider="azure_openai",
        azure_openai_endpoint="https://ejemplo.openai.azure.com",
        azure_openai_api_key="clave-de-prueba",
        gemini_api_key="",
        ai_base_url="",
        ai_model="",
        ai_api_key="",
    )


def _con_proveedor(monkeypatch: pytest.MonkeyPatch, proveedor: ProveedorFalso) -> AIService:
    monkeypatch.setattr(modulo, "crear_proveedor", lambda nombre, config: proveedor)
    return AIService(_config_con_azure())


def test_redaccion_con_llm_marca_generado_por_ia(
    monkeypatch: pytest.MonkeyPatch, payload_acta: Dict[str, Any]
) -> None:
    respuesta = json.dumps(
        {
            "titulo": "Aumento de capital social",
            "materia": "aumento_capital",
            "clausula_legal": (
                "PRIMERO.- Los socios acuerdan aumentar el capital social, conforme al "
                "artículo 182 de la Ley General de Sociedades Mercantiles."
            ),
            "fundamento_legal": "Artículo 182 LGSM",
        }
    )
    servicio = _con_proveedor(monkeypatch, ProveedorFalso(respuesta))
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))

    acuerdos = servicio.redactar_acuerdos(acta)

    assert all(acuerdo.generado_por_ia for acuerdo in acuerdos)
    assert "artículo 182" in acuerdos[0].clausula_legal
    assert servicio.llamadas, "Debe registrarse la trazabilidad de las llamadas al modelo"


def test_degradacion_a_plantillas_cuando_el_proveedor_falla(
    monkeypatch: pytest.MonkeyPatch, payload_acta: Dict[str, Any]
) -> None:
    """Si el LLM falla, el acta debe salir igual con plantillas y una advertencia."""
    servicio = _con_proveedor(monkeypatch, ProveedorFalso("", falla=True))
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))

    acuerdos = servicio.redactar_acuerdos(acta)

    assert len(acuerdos) == len(acta.acuerdos)
    assert all(not acuerdo.generado_por_ia for acuerdo in acuerdos)
    assert all(acuerdo.clausula_legal for acuerdo in acuerdos)
    assert servicio.advertencias, "La degradación debe quedar registrada como advertencia"


def test_validacion_con_llm_combina_hallazgos(
    monkeypatch: pytest.MonkeyPatch, payload_acta: Dict[str, Any]
) -> None:
    respuesta = json.dumps(
        {
            "puntaje": 71.5,
            "consistencia": "Requiere ajustes menores.",
            "hallazgos": [
                {
                    "severidad": "advertencia",
                    "campo": "convocatoria",
                    "mensaje": "Conviene anexar la cédula de publicación.",
                    "sugerencia": "Adjuntar el documento.",
                }
            ],
            "recomendaciones": ["Anexar la cédula de convocatoria."],
        }
    )
    servicio = _con_proveedor(monkeypatch, ProveedorFalso(respuesta))
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))

    validacion = servicio.validar_acta(acta)

    assert validacion.generado_por_ia is True
    assert validacion.puntaje == 71.5
    assert any(h.campo == "convocatoria" for h in validacion.hallazgos)
    assert "Anexar la cédula de convocatoria." in validacion.recomendaciones


def test_streaming_devuelve_fragmentos(
    monkeypatch: pytest.MonkeyPatch, payload_acta: Dict[str, Any]
) -> None:
    servicio = _con_proveedor(monkeypatch, ProveedorFalso("PRIMERO.- Se aprueba el acuerdo."))
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))
    acuerdo = acta.acuerdos[0]

    fragmentos = list(
        servicio.transmitir_redaccion(acuerdo, servicio.construir_contexto(acta, acuerdo))
    )

    assert len(fragmentos) > 1
    assert "".join(fragmentos).startswith("PRIMERO")


def test_streaming_sin_ia_usa_plantillas(payload_acta: Dict[str, Any]) -> None:
    """Sin proveedor configurado el streaming responde con la plantilla local."""
    servicio = crear_servicio_ia(_config_plantillas())
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))
    acuerdo = acta.acuerdos[0]

    texto = "".join(
        servicio.transmitir_redaccion(acuerdo, servicio.construir_contexto(acta, acuerdo))
    )

    assert len(texto) > 80
    assert any("plantillas legales locales" in a for a in servicio.advertencias)


# ===========================================================================
# Auditoría de fidelidad (el modelo no debe inventar cifras)
# ===========================================================================
def test_cifras_no_sustentadas_detecta_invenciones() -> None:
    contexto = {"capital": "$100,000.00"}
    inventadas = cifras_no_sustentadas("El capital aumenta a $500,000.00 pesos.", contexto)
    assert inventadas, "Debe detectar la cifra que no está en los datos capturados"


def test_cifras_no_sustentadas_acepta_las_del_contexto() -> None:
    contexto = {"capital": "$100,000.00"}
    assert cifras_no_sustentadas("El capital social asciende a $100,000.00 pesos.", contexto) == []


def test_cifras_no_sustentadas_ignora_articles_de_la_lgsm() -> None:
    """'artículo 182' no es una cifra inventada: proviene de la ley, no del acta."""
    contexto = {"capital": "$100,000.00"}
    texto = "Conforme a los artículos 182 y 186 de la Ley General de Sociedades Mercantiles."
    assert cifras_no_sustentadas(texto, contexto) == []


def test_advertencia_por_cifra_inventada(
    monkeypatch: pytest.MonkeyPatch, payload_acta: Dict[str, Any]
) -> None:
    respuesta = json.dumps(
        {
            "titulo": "Aumento de capital",
            "materia": "aumento_capital",
            "clausula_legal": (
                "PRIMERO.- Los socios acuerdan aumentar el capital social en $987,654.00 "
                "pesos, de conformidad con el artículo 182 de la LGSM."
            ),
            "fundamento_legal": "Artículo 182 LGSM",
        }
    )
    servicio = _con_proveedor(monkeypatch, ProveedorFalso(respuesta))
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))

    servicio.redactar_acuerdos(acta)

    assert any("no aparecen en los datos" in a for a in servicio.advertencias)


def test_sin_auditoria_de_fidelidad_no_avisa(
    monkeypatch: pytest.MonkeyPatch, payload_acta: Dict[str, Any]
) -> None:
    """Con la verificación desactivada no deben generarse advertencias de cifras."""
    respuesta = json.dumps(
        {
            "titulo": "Aumento de capital",
            "materia": "aumento_capital",
            "clausula_legal": "PRIMERO.- El capital aumenta $987,654.00 pesos (artículo 182 LGSM).",
            "fundamento_legal": "Artículo 182 LGSM",
        }
    )
    monkeypatch.setattr(modulo, "crear_proveedor", lambda n, c: ProveedorFalso(respuesta))
    servicio = AIService(_config_con_azure())
    servicio.config.ai_verificar_fidelidad = False
    acta = ActaRedaccionRequest(**_sin_guardar(payload_acta))

    servicio.redactar_acuerdos(acta)

    assert not any("no aparecen en los datos" in a for a in servicio.advertencias)
