"""Pruebas del motor de plantillas legales (ruta determinista, sin IA)."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from app.models.enums import MateriaAcuerdo
from app.services import plantillas_legales as plantillas


def test_todas_las_materias_tienen_plantilla() -> None:
    """Cada materia del dominio debe tener una plantilla de respaldo."""
    for materia in MateriaAcuerdo:
        assert materia in plantillas.PLANTILLAS, f"Falta la plantilla de {materia.value}"


def test_detecta_materia_por_palabras_clave() -> None:
    materia = plantillas.detectar_materia(
        "Aumentar el capital social mediante la suscripción de nuevas acciones"
    )
    assert materia is MateriaAcuerdo.AUMENTO_CAPITAL


def test_detecta_materia_por_tipo_de_asamblea() -> None:
    """Sin coincidencias textuales se usa la presunción del tipo de asamblea."""
    materia = plantillas.detectar_materia("Asunto general", "aumento_capital")
    assert materia is MateriaAcuerdo.AUMENTO_CAPITAL


def test_deteccion_sin_pistas_devuelve_generica() -> None:
    assert plantillas.detectar_materia("Se aprueba lo conducente") is MateriaAcuerdo.GENERICA


@pytest.fixture()
def contexto() -> Dict[str, Any]:
    return {
        "sociedad": "Comercializadora del Norte, S.A. de C.V.",
        "resumen": "Aumentar el capital social en $50,000.00",
        "mayoria": "Unanimidad",
        "acciones": "80,000",
        "capital": "$100,000.00",
        "monto": "$50,000.00",
    }


def test_redaccion_incluye_ordinales_y_fundamento(contexto: Dict[str, Any]) -> None:
    resultado = plantillas.redactar_con_plantilla(MateriaAcuerdo.AUMENTO_CAPITAL, contexto)
    clausula = resultado["clausula_legal"]

    assert "Ley General de Sociedades Mercantiles" in clausula
    assert "PRIMERO.-" in clausula
    assert "SEGUNDO.-" in clausula
    assert contexto["sociedad"] in clausula
    assert "$50,000.00" in clausula
    assert resultado["materia"] == "aumento_capital"
    assert resultado["fundamento_legal"].endswith(
        "de la Ley General de Sociedades Mercantiles"
    )


def test_formatear_tolera_claves_ausentes() -> None:
    """Un marcador sin valor no debe romper la redacción del acta."""
    assert plantillas.formatear("Hola {nombre}{desconocido}", {"nombre": "Ana"}) == "Hola Ana"


def test_textos_fijos_disponibles() -> None:
    for clave in ("encabezado", "declaracion_quorum", "cierre", "declaracion_protocolizacion"):
        assert clave in plantillas.TEXTOS_FIJOS
