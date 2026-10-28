"""Pruebas de integración de la API (FastAPI + SQLite temporal)."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from fastapi.testclient import TestClient
from pypdf import PdfReader


def test_health_reporta_servicio_y_base_de_datos(cliente: TestClient) -> None:
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["base_de_datos"] == "disponible"
    assert cuerpo["proveedor_ia"] == "plantillas"


def test_catalogos_del_formulario(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/actas/catalogos")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["tipos_asamblea"]) >= 8
    assert len(cuerpo["tipos_mayoria"]) >= 4
    assert any(item["valor"] == "extraordinaria" for item in cuerpo["tipos_asamblea"])
    assert cuerpo["ia_habilitada"] is False


def test_redactar_devuelve_clausulas_y_validacion(
    cliente_autenticado: TestClient, payload_acta: Dict[str, Any]
) -> None:
    cliente = cliente_autenticado
    respuesta = cliente.post("/api/v1/actas/redactar", json=payload_acta)
    assert respuesta.status_code == 200, respuesta.text

    cuerpo = respuesta.json()
    assert cuerpo["clausulas"]["encabezado"]
    assert cuerpo["clausulas"]["cuerpo"]
    assert len(cuerpo["acuerdos"]) == 2
    assert cuerpo["acuerdos"][0]["clausula_legal"]
    assert cuerpo["validacion"]["puntaje"] >= 90
    assert cuerpo["proveedor_ia"] == "plantillas"


def test_generar_pdf_guarda_el_acta_y_retorna_el_archivo(
    cliente_autenticado: TestClient, payload_acta: Dict[str, Any]
) -> None:
    cliente = cliente_autenticado
    respuesta = cliente.post("/api/v1/actas/generar-pdf", json=payload_acta)

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["content-type"] == "application/pdf"
    assert respuesta.content.startswith(b"%PDF")
    assert respuesta.headers["X-Acta-Folio"].startswith("PGAC-")
    assert respuesta.headers["X-Acta-Guardada"] == "true"
    assert "attachment" in respuesta.headers["content-disposition"]

    texto = "\n".join(
        pagina.extract_text() or "" for pagina in PdfReader(BytesIO(respuesta.content)).pages
    )
    assert "ACTA DE ASAMBLEA GENERAL EXTRAORDINARIA" in texto

    # El acta quedó persistida y su folio se refleja en el historial.
    listado = cliente.get("/api/v1/actas")
    assert listado.status_code == 200
    assert len(listado.json()) == 1
    assert listado.json()[0]["folio"] == respuesta.headers["X-Acta-Folio"]


def test_generar_pdf_sin_guardar_no_persiste(
    cliente_autenticado: TestClient, payload_acta: Dict[str, Any]
) -> None:
    cliente = cliente_autenticado
    datos = dict(payload_acta)
    datos["guardar"] = False
    respuesta = cliente.post("/api/v1/actas/generar-pdf", json=datos)

    assert respuesta.status_code == 200
    assert respuesta.headers["X-Acta-Guardada"] == "false"
    assert cliente.get("/api/v1/actas").json() == []


def test_crud_completo_del_acta(cliente_autenticado: TestClient, payload_acta: Dict[str, Any]) -> None:
    cliente = cliente_autenticado
    # Crear
    respuesta = cliente.post("/api/v1/actas", json=payload_acta)
    assert respuesta.status_code == 201, respuesta.text
    acta = respuesta.json()
    acta_id = acta["id"]
    assert acta["version"] == 1
    assert acta["estatus"] == "borrador"

    # Consultar
    detalle = cliente.get(f"/api/v1/actas/{acta_id}")
    assert detalle.status_code == 200
    assert detalle.json()["clausulas"]["encabezado"]

    # Actualizar (PUT) -> nueva versión
    datos = dict(payload_acta)
    datos["titulo"] = "Aumento de capital (revisado)"
    actualizada = cliente.put(f"/api/v1/actas/{acta_id}", json=datos)
    assert actualizada.status_code == 200, actualizada.text
    assert actualizada.json()["version"] == 2
    assert actualizada.json()["titulo"].endswith("(revisado)")

    # Cambiar estatus (PATCH)
    estatus = cliente.patch(
        f"/api/v1/actas/{acta_id}/estatus", params={"estatus": "aprobada"}
    )
    assert estatus.status_code == 200
    assert estatus.json()["estatus"] == "aprobada"

    # Regenerar PDF desde la base de datos
    pdf = cliente.get(f"/api/v1/actas/{acta_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert pdf.headers["X-Acta-Version"] == "2"

    # Volver a validar
    validacion = cliente.post(f"/api/v1/actas/{acta_id}/validar")
    assert validacion.status_code == 200
    assert 0 <= validacion.json()["puntaje"] <= 100

    # Eliminar
    borrado = cliente.delete(f"/api/v1/actas/{acta_id}")
    assert borrado.status_code == 200
    assert acta["folio"] in borrado.json()["mensaje"]
    assert cliente.get(f"/api/v1/actas/{acta_id}").status_code == 404


def test_acta_inexistente_devuelve_404(cliente_autenticado: TestClient) -> None:
    assert cliente_autenticado.get("/api/v1/actas/999999").status_code == 404


def test_estatus_invalido_devuelve_422(cliente_autenticado: TestClient, payload_acta: Dict[str, Any]) -> None:
    cliente = cliente_autenticado
    acta = cliente.post("/api/v1/actas", json=payload_acta).json()
    respuesta = cliente.patch(
        f"/api/v1/actas/{acta['id']}/estatus", params={"estatus": "inventado"}
    )
    assert respuesta.status_code == 422


def test_formulario_invalido_devuelve_422_con_detalle(
    cliente_autenticado: TestClient, payload_acta: Dict[str, Any]
) -> None:
    cliente = cliente_autenticado
    datos = dict(payload_acta)
    datos["acuerdos"] = []
    datos["asistentes"] = []

    respuesta = cliente.post("/api/v1/actas/redactar", json=datos)
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert "no son válidos" in cuerpo["detail"]
    assert cuerpo["errores"]
