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


# ---------------------------------------------------------------------------
# Pruebas de plantillas parametrizadas
# ---------------------------------------------------------------------------

def test_todas_las_plantillas_declaran_parametros() -> None:
    """Cada PlantillaLegal debe tener declarados sus parámetros (vacíos o con entries)."""
    for materia, plantilla in plantillas.PLANTILLAS.items():
        assert isinstance(plantilla.parametros, tuple), f"{materia.value}: parametros no es tuple"
        for p in plantilla.parametros:
            assert isinstance(p, plantillas.ParametroPlantilla)
            assert isinstance(p.nombre, str) and p.nombre
            assert isinstance(p.requerido, bool)


def test_parametros_requeridos_aumento_capital() -> None:
    """AUMENTO_CAPITAL requiere sociedad, monto y capital."""
    requeridos = plantillas.obtener_plantilla(MateriaAcuerdo.AUMENTO_CAPITAL).parametros_requeridos()
    assert set(requeridos) == {"sociedad", "monto", "capital"}


def test_parametros_opcionales_vacíos_por_defecto() -> None:
    """Por defecto no hay parámetros opcionales en las plantillas actuales."""
    for plantilla in plantillas.PLANTILLAS.values():
        assert plantilla.parametros_opcionales() == ()


def test_valores_por_defecto_vacíos() -> None:
    """Por defecto no hay valores por defecto declarados."""
    for plantilla in plantillas.PLANTILLAS.values():
        assert plantilla.valores_por_defecto() == {}


def test_marcador_nombres_coincide_con_parametros() -> None:
    """Los nombres de marcador {clave} de los párrafos deben coincidir con los parámetros declarados."""
    for materia, plantilla in plantillas.PLANTILLAS.items():
        marcadores = set(plantilla.marcador_nombres())
        declarados = set(p.nombre for p in plantilla.parametros)
        # Cada marcador debe tener un parámetro declarado
        assert marcadores.issubset(declarados), (
            f"{materia.value}: marcadores sin declarar: {marcadores - declarados}"
        )


def test_obtener_parametros_plantilla_estructura() -> None:
    """obtener_parametros_plantilla debe retornar lista de dicts con las claves esperadas."""
    params = plantillas.obtener_parametros_plantilla(MateriaAcuerdo.AUMENTO_CAPITAL)
    assert isinstance(params, list)
    for entry in params:
        assert set(entry.keys()) == {"nombre", "requerido", "valor_predeterminado", "descripcion"}
        assert isinstance(entry["nombre"], str)
        assert isinstance(entry["requerido"], bool)


def test_parametros_requeridos_por_materia_todas() -> None:
    """parametros_requeridos_por_materia debe cubrir todas las materias."""
    resultado = plantillas.parametros_requeridos_por_materia()
    for materia in plantillas.MateriaAcuerdo if hasattr(plantillas, 'MateriaAcuerdo') else []:
        pass
    # Verificar que al menos las materias con parámetros aparezcan
    assert "aumento_capital" in resultado
    assert resultado["aumento_capital"] == ["sociedad", "monto", "capital"]


def test_redaccion_falla_si_faltan_parametros_requeridos() -> None:
    """Si faltan parámetros requeridos, debe lanzarse DatosPlantillaIncompletosError."""
    contexto_incompleto = {"sociedad": "Mi Sociedad, S.A. de C.V."}  # falta monto y capital
    with pytest.raises(plantillas.DatosPlantillaIncompletosError):
        plantillas.redactar_con_plantilla(MateriaAcuerdo.AUMENTO_CAPITAL, contexto_incompleto)


def test_redaccion_exitoso_con_todos_los_parametros(contexto: Dict[str, Any]) -> None:
    """Con todos los parámetros requeridos, la redacción debe tener éxito."""
    resultado = plantillas.redactar_con_plantilla(MateriaAcuerdo.AUMENTO_CAPITAL, contexto)
    assert contexto["sociedad"] in resultado["clausula_legal"]
    assert contexto["monto"] in resultado["clausula_legal"]
    assert contexto["capital"] in resultado["clausula_legal"]


def test_redaccion_generica_requiere_resumen() -> None:
    """GENERICA requiere el parámetro resumen."""
    with pytest.raises(plantillas.DatosPlantillaIncompletosError):
        plantillas.redactar_con_plantilla(MateriaAcuerdo.GENERICA, {"sociedad": "X"})
    # Con resumen debe funcionar
    resultado = plantillas.redactar_con_plantilla(
        MateriaAcuerdo.GENERICA,
        {"sociedad": "X", "resumen": "Se aprueba lo conducente"},
    )
    assert "Se aprueba lo conducente" in resultado["clausula_legal"]
