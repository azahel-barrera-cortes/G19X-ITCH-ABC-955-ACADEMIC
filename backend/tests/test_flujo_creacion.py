"""Pruebas del flujo guiado de creación (acompañamiento + PDF + control)."""
from __future__ import annotations


def _flujo_completo(cliente) -> dict:
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "Quiero crear un acta"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] == "catalogo_tipos"
    assert d["tipos_acta"], "Debe ofrecer el catálogo con descripciones"
    assert d["sesion_id"]
    sesion = d["sesion_id"]

    # Elige tipo específico -> pide primer dato.
    r = cliente.post("/api/v1/asistente/chat",
                     json={"mensaje": "ordinaria", "sesion_id": sesion})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] == "crear"
    sesion = d.get("sesion_id") or sesion

    pasos = [
        "Comercializadora del Norte, S.A. de C.V.",
        "15 de marzo de 2026",
        "Av. Paseo de la Reforma 1234, Ciudad de México",
        "Ana María Ruiz Salazar",
        "Carlos Peña Domínguez",
        "Ana María Ruiz Salazar 50000, Carlos Peña Domínguez 20000",
        "1. Aprobación de estados financieros; 2. Nombramiento de administradores",
    ]
    ultimo = None
    for paso in pasos:
        r = cliente.post("/api/v1/asistente/chat",
                         json={"mensaje": paso, "sesion_id": sesion,
                               "autor": "capturista_demo"})
        assert r.status_code == 200, r.text
        ultimo = r.json()
        sesion = ultimo.get("sesion_id") or sesion
    return ultimo


def test_catalogo_si_no_sabe_que_acta(cliente_autenticado):
    cliente = cliente_autenticado
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "No sé qué acta crear"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] in ("catalogo_tipos", "crear")
    assert "ordinaria" in r.text.lower() or d.get("tipos_acta")


def test_creacion_guiada_genera_pdf_y_control(cliente_autenticado):
    cliente = cliente_autenticado
    ultimo = _flujo_completo(cliente)
    assert ultimo["intencion"] == "crear"
    control = ultimo.get("control_acta")
    assert control, "Debe devolver el control del acta generada"
    assert control["folio"] and control["acta_id"]
    assert control["creado_por"] == "capturista_demo"
    assert control["pdf_descarga"], "Debe indicar la descarga del PDF"
    assert ultimo.get("texto_organizado"), "Debe devolver el texto organizado"

    # El PDF se descarga desde el control.
    r = cliente.get(control["pdf_descarga"])
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"

    # El control persiste: fecha, autor, caducidad y versión.
    r = cliente.get(f"/api/v1/actas/{control['acta_id']}")
    assert r.status_code == 200, r.text
    acta = r.json()
    assert acta["folio"] == control["folio"]
    assert acta["version"] >= 1
    assert acta["creado_por"] == "capturista_demo"
    assert acta["created_at"]


def test_creacion_directa_con_tipo(cliente_autenticado):
    cliente = cliente_autenticado
    r = cliente.post("/api/v1/asistente/chat",
                     json={"mensaje": "Crea un acta de aumento de capital"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] == "crear"
    assert d["tipo_asamblea"] == "aumento_capital"
    assert d["campo_solicitado"] == "sociedad"
