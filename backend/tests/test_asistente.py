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


def test_edicion_asistida_propone_cambios_sin_guardarlos(cliente_autenticado, payload_acta):
    cliente = cliente_autenticado
    acta = _crear_acta(cliente, payload_acta)

    r = cliente.post(
        "/api/v1/asistente/chat",
        json={
            "mensaje": "Quiero cambiar el lugar",
            "acta_id": acta["id"],
            "modo": "edicion",
        },
    )
    assert r.status_code == 200, r.text
    inicio = r.json()
    assert inicio["campo_solicitado"] == "lugar"

    r = cliente.post(
        "/api/v1/asistente/chat",
        json={
            "mensaje": "Av. Paseo de la Reforma 500, Ciudad de México",
            "acta_id": acta["id"],
            "sesion_id": inicio["sesion_id"],
            "modo": "edicion",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["cambios_propuestos"]["lugar"] == "Av. Paseo de la Reforma 500, Ciudad de México"
    assert cliente.get(f"/api/v1/actas/{acta['id']}").json()["lugar"] == acta["lugar"]


def test_chat_general_ofrece_abrir_edicion_asistida(cliente_autenticado, payload_acta):
    cliente = cliente_autenticado
    acta = _crear_acta(cliente, payload_acta)

    respuesta = cliente.post(
        "/api/v1/asistente/chat",
        json={"mensaje": f"Quiero editar el acta {acta['id']}"},
    )
    assert respuesta.status_code == 200, respuesta.text
    accion = respuesta.json()["acciones"][0]
    assert accion["accion"] == "editar_acta"
    assert accion["acta_id"] == acta["id"]

def test_capturista_no_cambia_estatus_por_chat(cliente_anonimo, cliente_autenticado, sesion, payload_acta):
    from app.core import security
    from app.models.usuario import Usuario
    sesion.query(Usuario).filter(Usuario.email == "capturista@pgac.com").delete()
    sesion.add(Usuario(email="capturista@pgac.com", nombre_completo="Usuario de Prueba", rol="capturista", password_hash=security.hash_password("secreto-1"), activo=True))
    sesion.commit()
    try:
        acta = _crear_acta(cliente_autenticado, payload_acta)
        login = cliente_anonimo.post("/api/v1/auth/login", json={"email": "capturista@pgac.com", "password": "secreto-1"})
        cabeceras = {"Authorization": f"Bearer {login.json()['access_token']}"}
        r = cliente_anonimo.post("/api/v1/asistente/chat", json={"mensaje": f"Pasa el acta {acta['id']} a revision"}, headers=cabeceras)
        assert "Tu rol no permite" in r.json()["respuesta"]
        sigue = cliente_autenticado.get(f"/api/v1/actas/{acta['id']}").json()
        assert sigue["estatus"] == acta["estatus"]
    finally:
        sesion.query(Usuario).filter(Usuario.email == "capturista@pgac.com").delete()
        sesion.commit()
