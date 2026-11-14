"""Pruebas de integración de la API (FastAPI + SQLite temporal)."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.models.usuario import BitacoraCambios


def test_health_reporta_servicio_y_base_de_datos(cliente: TestClient) -> None:
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["base_de_datos"] == "disponible"
    assert cuerpo["proveedor_ia"] == "plantillas"


def test_endpoints_sin_uso_de_notaria_y_expediente_no_estan_publicados(
    cliente: TestClient,
) -> None:
    assert cliente.get("/api/v1/notaria/actas").status_code == 404
    assert cliente.get("/api/v1/expediente/1/zip").status_code == 404


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

    assert respuesta.status_code == 409
    creada = cliente.post("/api/v1/actas", json=payload_acta)
    assert creada.status_code == 201, creada.text
    acta = creada.json()
    assert acta["estado_flujo"] == "revision"

    pdf_prematuro = cliente.get(f"/api/v1/actas/{acta['id']}/pdf")
    assert pdf_prematuro.status_code == 409
    revisada = cliente.post(
        f"/api/v1/actas/{acta['id']}/decision",
        json={"accion": "aprobar"},
    )
    assert revisada.status_code == 200
    assert revisada.json()["estado_flujo"] == "abogado"
    aprobada = cliente.post(
        f"/api/v1/actas/{acta['id']}/decision",
        json={"accion": "aprobar"},
    )
    assert aprobada.status_code == 200
    assert aprobada.json()["estado_flujo"] == "aprobada"
    respuesta = cliente.get(f"/api/v1/actas/{acta['id']}/pdf")
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

    # El acta aprobada quedó persistida y su folio se refleja en el historial.
    listado = cliente.get("/api/v1/actas")
    assert listado.status_code == 200
    assert len(listado.json()) == 1
    assert listado.json()[0]["folio"] == acta["folio"]


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
    assert acta["estatus"] == "en_revision"
    assert acta["estado_flujo"] == "revision"

    # Consultar
    detalle = cliente.get(f"/api/v1/actas/{acta_id}")
    assert detalle.status_code == 200
    assert detalle.json()["clausulas"]["encabezado"]

    # Un administrador no puede saltarse la etapa de corrección del Capturista.
    datos = dict(payload_acta)
    datos["titulo"] = "Aumento de capital (revisado)"
    actualizada = cliente.put(f"/api/v1/actas/{acta_id}", json=datos)
    assert actualizada.status_code == 403
    assert cliente.get(f"/api/v1/actas/{acta_id}").json()["version"] == 1

    # Solo una decisión del Revisor seguida por la del Abogado aprueba el acta.
    estatus = cliente.patch(
        f"/api/v1/actas/{acta_id}/estatus", params={"estatus": "aprobada"}
    )
    assert estatus.status_code == 409
    cliente.post(f"/api/v1/actas/{acta_id}/decision", json={"accion": "aprobar"})
    estatus = cliente.post(f"/api/v1/actas/{acta_id}/decision", json={"accion": "aprobar"})
    assert estatus.status_code == 200
    assert estatus.json()["estatus"] == "aprobada"

    # Regenerar PDF desde la base de datos
    pdf = cliente.get(f"/api/v1/actas/{acta_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert pdf.headers["X-Acta-Version"] == "1"


    # Volver a validar
    validacion = cliente.post(f"/api/v1/actas/{acta_id}/validar")
    assert validacion.status_code == 200
    assert 0 <= validacion.json()["puntaje"] <= 100

    # Eliminar
    borrado = cliente.delete(f"/api/v1/actas/{acta_id}")
    assert borrado.status_code == 200
    assert acta["folio"] in borrado.json()["mensaje"]
    assert cliente.get(f"/api/v1/actas/{acta_id}").status_code == 404


def test_flujo_revisor_abogado_y_correcciones_por_capturista(
    cliente: TestClient, sesion: Any, payload_acta: Dict[str, Any]
) -> None:
    from app.core import security
    from app.models.usuario import Usuario

    usuarios = {
        "captura": ("captura-flujo@pgac.com", "capturista"),
        "revision": ("revision-flujo@pgac.com", "revisor"),
        "abogado": ("abogado-flujo@pgac.com", "abogado_responsable"),
    }
    empresa_codigo = sesion.query(Usuario).filter_by(email="admin@pgac.com").one().codigo_empresa
    cabeceras = {}
    try:
        for clave, (email, rol) in usuarios.items():
            sesion.query(Usuario).filter(Usuario.email == email).delete()
            sesion.add(
                Usuario(
                    email=email,
                    nombre_completo=f"Usuario {clave}",
                    rol=rol,
                    password_hash=security.hash_password("clave-flujo-123"),
                    activo=True,
                    empresa_codigo=empresa_codigo,
                )
            )
        sesion.commit()
        for clave, (email, _rol) in usuarios.items():
            login = cliente.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "clave-flujo-123"},
            )
            assert login.status_code == 200, login.text
            cabeceras[clave] = {
                "Authorization": f"Bearer {login.json()['access_token']}"
            }

        creada = cliente.post(
            "/api/v1/actas", json=payload_acta, headers=cabeceras["captura"]
        )
        assert creada.status_code == 201, creada.text
        acta_id = creada.json()["id"]
        assert creada.json()["creado_por"] == usuarios["captura"][0]

        analisis_inicial = cliente.post(
            f"/api/v1/actas/{acta_id}/analizar-revision",
            headers=cabeceras["revision"],
        )
        assert analisis_inicial.status_code == 200, analisis_inicial.text
        assert analisis_inicial.json()["version_actual"] == 1
        assert analisis_inicial.json()["version_comparada"] is None
        assert analisis_inicial.json()["cambios"] == []
        assert cliente.post(
            f"/api/v1/actas/{acta_id}/analizar-revision",
            headers=cabeceras["captura"],
        ).status_code == 403

        bandeja_revisor = cliente.get(
            "/api/v1/actas/bandeja", headers=cabeceras["revision"]
        )
        assert [acta["id"] for acta in bandeja_revisor.json()] == [acta_id]
        devuelta = cliente.post(
            f"/api/v1/actas/{acta_id}/decision",
            json={"accion": "devolver", "comentario": "Corregir la fecha de convocatoria."},
            headers=cabeceras["revision"],
        )
        assert devuelta.status_code == 200
        assert devuelta.json()["estado_flujo"] == "con_errores"

        bandeja_capturista = cliente.get(
            "/api/v1/actas/bandeja", headers=cabeceras["captura"]
        )
        assert bandeja_capturista.json()[0]["comentario_revision"] == (
            "Corregir la fecha de convocatoria."
        )
        cambios = dict(payload_acta)
        cambios["convocatoria_fecha"] = "2026-03-01"
        cambios["motivo_cambio"] = "Corrección solicitada por el Revisor"
        actualizada = cliente.put(
            f"/api/v1/actas/{acta_id}", json=cambios, headers=cabeceras["captura"]
        )
        assert actualizada.status_code == 200, actualizada.text
        assert actualizada.json()["version"] == 2
        reenviada = cliente.post(
            f"/api/v1/actas/{acta_id}/reenviar", headers=cabeceras["captura"]
        )
        assert reenviada.status_code == 200
        assert reenviada.json()["estado_flujo"] == "revision"
        analisis_corregido = cliente.post(
            f"/api/v1/actas/{acta_id}/analizar-revision",
            headers=cabeceras["revision"],
        )
        assert analisis_corregido.status_code == 200, analisis_corregido.text
        assert analisis_corregido.json()["version_comparada"] == 1
        assert "Fecha de convocatoria" in analisis_corregido.json()["cambios"]

        revisada = cliente.post(
            f"/api/v1/actas/{acta_id}/decision",
            json={"accion": "aprobar"},
            headers=cabeceras["revision"],
        )
        assert revisada.json()["estado_flujo"] == "abogado"
        assert cliente.post(
            f"/api/v1/actas/{acta_id}/analizar-revision",
            headers=cabeceras["revision"],
        ).status_code == 409
        analisis_abogado = cliente.post(
            f"/api/v1/actas/{acta_id}/analizar-revision",
            headers=cabeceras["abogado"],
        )
        assert analisis_abogado.status_code == 200, analisis_abogado.text
        assert analisis_abogado.json()["version_comparada"] == 1

        devuelta_por_abogado = cliente.post(
            f"/api/v1/actas/{acta_id}/decision",
            json={"accion": "devolver", "comentario": "Agregar el fundamento estatutario."},
            headers=cabeceras["abogado"],
        )
        assert devuelta_por_abogado.json()["estado_flujo"] == "con_errores"
        assert devuelta_por_abogado.json()["historial_revision"][-1]["etapa"] == "abogado"
        acta_devuelta = cliente.get(
            "/api/v1/actas/bandeja", headers=cabeceras["captura"]
        ).json()[0]
        assert acta_devuelta["comentario_revision"] == "Agregar el fundamento estatutario."
        assert cliente.get(
            f"/api/v1/actas/{acta_id}/pdf", headers=cabeceras["abogado"]
        ).status_code == 409

        segunda_correccion = cliente.put(
            f"/api/v1/actas/{acta_id}",
            json={**cambios, "titulo": "Acta con fundamento estatutario"},
            headers=cabeceras["captura"],
        )
        assert segunda_correccion.status_code == 200
        assert segunda_correccion.json()["version"] == 3
        reenviada_al_abogado = cliente.post(
            f"/api/v1/actas/{acta_id}/reenviar",
            headers=cabeceras["captura"],
        )
        assert reenviada_al_abogado.status_code == 200
        assert reenviada_al_abogado.json()["estado_flujo"] == "abogado"
        analisis_segunda_correccion = cliente.post(
            f"/api/v1/actas/{acta_id}/analizar-revision",
            headers=cabeceras["abogado"],
        )
        assert analisis_segunda_correccion.status_code == 200, analisis_segunda_correccion.text
        assert analisis_segunda_correccion.json()["version_comparada"] == 2
        assert "Título" in analisis_segunda_correccion.json()["cambios"]
        bandeja_revisor = cliente.get(
            "/api/v1/actas/bandeja", headers=cabeceras["revision"]
        )
        assert all(acta["id"] != acta_id for acta in bandeja_revisor.json())
        bandeja_abogado = cliente.get(
            "/api/v1/actas/bandeja", headers=cabeceras["abogado"]
        )
        assert any(
            acta["id"] == acta_id and acta["version"] == 3
            for acta in bandeja_abogado.json()
        )
        aprobada = cliente.post(
            f"/api/v1/actas/{acta_id}/decision",
            json={"accion": "aprobar"},
            headers=cabeceras["abogado"],
        )
        assert aprobada.status_code == 200
        assert aprobada.json()["estado_flujo"] == "aprobada"
        biblioteca = cliente.get("/api/v1/actas", headers=cabeceras["abogado"])
        assert biblioteca.status_code == 200
        assert any(
            acta["id"] == acta_id and acta["estado_flujo"] == "aprobada"
            for acta in biblioteca.json()
        )
        pdf_final = cliente.get(
            f"/api/v1/actas/{acta_id}/pdf", headers=cabeceras["abogado"]
        )
        assert pdf_final.status_code == 200
        assert pdf_final.content.startswith(b"%PDF")

        versiones = cliente.get(
            f"/api/v1/administracion/versiones/{acta_id}",
            headers=cabeceras["abogado"],
        )
        assert versiones.status_code == 200
        assert [version["version"] for version in versiones.json()] == [3, 2, 1]
    finally:
        for email, _rol in usuarios.values():
            sesion.query(Usuario).filter(Usuario.email == email).delete()
        sesion.commit()


def test_consultar_acta_normaliza_datos_especificos_nulos(
    cliente_autenticado: TestClient,
    payload_acta: Dict[str, Any],
    sesion: Any,
) -> None:
    from app.models.acta import Acta

    creada = cliente_autenticado.post("/api/v1/actas", json=payload_acta)
    assert creada.status_code == 201, creada.text

    acta = sesion.get(Acta, creada.json()["id"])
    assert acta is not None
    acta.datos_especificos = None
    acta.datos_asistente = None
    sesion.commit()

    detalle = cliente_autenticado.get(f"/api/v1/actas/{acta.id}")
    assert detalle.status_code == 200, detalle.text
    assert detalle.json()["datos_especificos"] == {}
    assert detalle.json()["datos_asistente"] == {}


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


def test_creacion_acta_registra_si_se_genero_con_ia(
    cliente_autenticado: TestClient,
    payload_acta: Dict[str, Any],
    sesion: Any,
) -> None:
    respuesta = cliente_autenticado.post("/api/v1/actas", json=payload_acta)
    assert respuesta.status_code == 201, respuesta.text

    evento = (
        sesion.query(BitacoraCambios)
        .filter(
            BitacoraCambios.entidad == "actas",
            BitacoraCambios.entidad_id == respuesta.json()["id"],
            BitacoraCambios.accion == "crear",
        )
        .order_by(BitacoraCambios.id.desc())
        .first()
    )
    assert evento is not None
    assert evento.datos_despues["folio"] == respuesta.json()["folio"]
    assert evento.datos_despues["generado_con_ia"] is False
