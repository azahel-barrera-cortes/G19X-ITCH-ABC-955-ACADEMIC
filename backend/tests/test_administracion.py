"""Pruebas de administración de actas: historial de versiones y caducidad."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.core.config import Settings
from app.models.acta import DIAS_AVISO_CADUCIDAD, Acta
from app.models.enums import EstatusActa
from app.schemas.acta import ActaActualizarRequest, ActaRedaccionRequest
from app.services import acta_service, administracion
from app.services.ai_service import crear_servicio_ia


def _payload(payload_acta: dict) -> ActaRedaccionRequest:
    datos = {k: v for k, v in payload_acta.items() if k != "guardar"}
    return ActaRedaccionRequest(**datos)


def _servicio_plantillas():
    return crear_servicio_ia(
        Settings(
            ai_provider="plantillas",
            azure_openai_endpoint="",
            azure_openai_api_key="",
            gemini_api_key="",
        )
    )


def _crear(sesion, payload_acta: dict) -> Acta:
    payload = _payload(payload_acta)
    borrador = acta_service.redactar(payload, _servicio_plantillas())
    return acta_service.crear_acta(sesion, payload, borrador)


def _acta_transitoria(folio: str = "PGAC-2026-9001", **campos: Any) -> Acta:
    """Acta sin persistir para probar solo la clasificación de vigencia."""
    base = {
        "folio": folio,
        "sociedad": "Sociedad de Prueba",
        "tipo_asamblea": "ordinaria",
        "fecha": date.today(),
        "lugar": "Domicilio social",
        "presidente": "Presidenta",
        "secretario": "Secretario",
    }
    return Acta(**{**base, **campos})


# ---------------------------------------------------------------------------
# Caducidad: clasificación
# ---------------------------------------------------------------------------
def test_acta_sin_fecha_es_sin_fecha() -> None:
    acta = _acta_transitoria()
    assert acta.estado_caducidad == "sin_fecha"
    assert acta.dias_para_caducar is None


def test_clasificacion_vigente_por_vencer_y_vencida() -> None:
    hoy = date.today()
    casos = [
        (hoy + timedelta(days=DIAS_AVISO_CADUCIDAD + 10), "vigente"),
        (hoy + timedelta(days=DIAS_AVISO_CADUCIDAD), "por_vencer"),  # en el límite
        (hoy, "por_vencer"),  # vence hoy
        (hoy - timedelta(days=1), "vencida"),
    ]
    for fecha_esperada, estado_esperado in casos:
        acta = _acta_transitoria(fecha_caducidad=fecha_esperada)
        assert acta.estado_caducidad == estado_esperado, fecha_esperada


# ---------------------------------------------------------------------------
# Caducidad: persistencia vía servicio
# ---------------------------------------------------------------------------
def test_fijar_caducidad_incrementa_version_y_registra(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)
    version_inicial = int(acta.version or 1)

    nueva = date.today() + timedelta(days=365)
    actualizada = administracion.fijar_caducidad(sesion, acta.id, nueva, "Vigencia anual acordada")

    assert actualizada.fecha_caducidad == nueva
    assert actualizada.motivo_caducidad == "Vigencia anual acordada"
    assert int(actualizada.version) == version_inicial + 1
    # El cambio queda como versión nueva con su motivo.
    motivos = [v.motivo for v in administracion.listar_versiones(sesion, acta.id)]
    assert any("Caducidad actualizada" in motivo for motivo in motivos)

def test_quitar_caducidad_deja_sin_fecha(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)
    administracion.fijar_caducidad(sesion, acta.id, date.today() + timedelta(days=10))
    quitada = administracion.fijar_caducidad(sesion, acta.id, None, "Plazo eliminado")

    assert quitada.fecha_caducidad is None
    assert quitada.estado_caducidad == "sin_fecha"


def test_resumen_administracion_contiene_totales(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)
    administracion.fijar_caducidad(sesion, acta.id, date.today() - timedelta(days=1))

    resumen = administracion.resumen_administracion(sesion)

    assert resumen["total_actas"] == 1
    assert resumen["total_versiones"] >= 2  # creación + caducidad
    assert resumen["vigencia"]["vencidas"] == 1
    assert resumen["vigencia"]["sin_fecha"] == 0
    assert resumen["vigencia"]["dias_aviso"] == DIAS_AVISO_CADUCIDAD
    assert "borrador" in resumen["por_estatus"]


def test_actas_por_vigencia_ordena_vencidas_primero(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)
    hoy = date.today()
    administracion.fijar_caducidad(sesion, acta.id, hoy - timedelta(days=30))  # vencida

    vencidas = administracion.actas_por_vigencia(sesion, estado="vencida")
    assert len(vencidas) == 1
    assert vencidas[0].estado_caducidad == "vencida"

    # Con el filtro de "vigente" no debe aparecer la vencida.
    assert administracion.actas_por_vigencia(sesion, estado="vigente") == []


def test_fijar_caducidad_en_acta_inexistente_lanza_404(sesion) -> None:
    from app.core.exceptions import ActaNoEncontradaError

    try:
        administracion.fijar_caducidad(sesion, 999999, date.today())
    except ActaNoEncontradaError:
        return
    raise AssertionError("Se esperaba ActaNoEncontradaError")


# ---------------------------------------------------------------------------
# Historial de versiones
# ---------------------------------------------------------------------------
def test_crear_acta_registra_version_1(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)

    versiones = administracion.listar_versiones(sesion, acta.id)

    assert len(versiones) == 1
    assert versiones[0].version == 1
    assert versiones[0].motivo == "Creación del acta"
    assert versiones[0].estatus == EstatusActa.BORRADOR.value
    # La instantánea conserva los datos sustantivos.
    contenido = versiones[0].contenido
    assert contenido["sociedad"] == acta.sociedad
    assert contenido["folio"] == acta.folio
    assert isinstance(contenido["acuerdos"], list) and contenido["acuerdos"]


def test_actualizar_acta_genera_nueva_version(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)
    datos = {
        **_payload(payload_acta).model_dump(mode="json"),
        "motivo_cambio": "Ajuste de lugar",
    }

    actualizado = acta_service.actualizar_acta(sesion, acta.id, ActaActualizarRequest(**datos))

    assert int(actualizado.version) == 2
    versiones = administracion.listar_versiones(sesion, acta.id)
    assert len(versiones) == 2
    assert any("Ajuste de lugar" in v.motivo for v in versiones)


def test_restaurar_version_emite_version_nueva(sesion, payload_acta: dict) -> None:
    acta = _crear(sesion, payload_acta)
    lugar_original = acta.lugar
    datos = {
        **_payload(payload_acta).model_dump(mode="json"),
        "motivo_cambio": "Cambio de sede",
    }
    acta_service.actualizar_acta(sesion, acta.id, ActaActualizarRequest(**datos))

    restaurada = administracion.restaurar_version(sesion, acta.id, 1)

    assert int(restaurada.version) == 3  # el historial siempre avanza
    assert restaurada.lugar == lugar_original
    assert len(administracion.listar_versiones(sesion, acta.id)) == 3


def test_restaurar_version_inexistente_lanza_404(sesion, payload_acta: dict) -> None:
    from app.core.exceptions import ActaNoEncontradaError

    acta = _crear(sesion, payload_acta)
    try:
        administracion.restaurar_version(sesion, acta.id, 99)
    except ActaNoEncontradaError:
        return
    raise AssertionError("Se esperaba ActaNoEncontradaError")
