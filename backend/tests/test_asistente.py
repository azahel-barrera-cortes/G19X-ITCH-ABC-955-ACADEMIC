"""Pruebas del Asistente IA interno (sin servicios externos)."""

from __future__ import annotations


def _sin_guardar(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k != "guardar"}


def _crear_acta(cliente, payload_acta: dict) -> dict:
    r = cliente.post("/api/v1/actas", json=_sin_guardar(payload_acta))
    assert r.status_code in (200, 201), r.text
    return r.json()


def test_puerta_tematica_rechaza_fuera_de_tema(cliente_autenticado):
    cliente = cliente_autenticado
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "Quien gano el mundial de futbol?"})
    assert r.status_code == 200
    d = r.json()
    assert d["tema_valido"] is False
    assert "actas" in d["respuesta"].lower()


def test_ayuda_y_sugerencias(cliente_autenticado):
    cliente = cliente_autenticado
    r = cliente.get("/api/v1/asistente/ayuda")
    assert r.status_code == 200
    assert r.json()["sugerencias"]


def test_redactar_libre_con_fundamento(cliente_autenticado):
    cliente = cliente_autenticado
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "Redacta un acuerdo de aumento de capital por 500000"})
    assert r.status_code == 200
    d = r.json()
    assert d["intencion"] == "redactar"
    assert "Ley General de Sociedades Mercantiles" in d["respuesta"]
    assert d["texto_borrador"]


def test_estatus_valida_aprueba_y_versiones(cliente_autenticado, payload_acta):
    cliente = cliente_autenticado
    acta = _crear_acta(cliente, payload_acta)
    folio = acta["folio"]
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": f"Estatus de {folio}"})
    assert r.status_code == 200
    assert r.json()["acta"]["folio"] == folio
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": f"Valida el acta {acta['id']}"})
    assert r.status_code == 200
    assert r.json()["intencion"] == "validar"
    assert r.json()["validacion"]["puntaje"] >= 0
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": f"Pasa el acta {acta['id']} a revision"})
    assert r.status_code == 200
    assert "en_revision" in r.json()["respuesta"] or r.json()["acta"]["estatus"] == "en_revision"
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": f"Versiones del acta {acta['id']}"})
    assert r.status_code == 200
    assert r.json()["versiones"]


def test_no_aprueba_con_criticos(cliente_autenticado, payload_quorum_insuficiente):
    cliente = cliente_autenticado
    acta = _crear_acta(cliente, payload_quorum_insuficiente)
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": f"Pasa el acta {acta['id']} a aprobada"})
    assert r.status_code == 200
    d = r.json()
    assert "No puedo" in d["respuesta"] or "critico" in d["respuesta"].lower()


def test_resumen_general(cliente_autenticado, payload_acta):
    cliente = cliente_autenticado
    _crear_acta(cliente, payload_acta)
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "Cuantas actas hay por estatus?"})
    assert r.status_code == 200
    assert r.json()["intencion"] == "resumen"
    assert r.json()["resumen"]["total_actas"] >= 1
