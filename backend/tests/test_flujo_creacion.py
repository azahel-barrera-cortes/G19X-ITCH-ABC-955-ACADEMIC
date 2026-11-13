"""Pruebas del flujo guiado de creación (asistente + revisión + control)."""
from __future__ import annotations

import pytest


def _flujo_completo(cliente, confirmar: bool = True) -> dict:
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "Quiero crear un acta"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] in ("catalogo_tipos", "crear")
    if d["intencion"] == "catalogo_tipos":
        assert d["tipos_acta"], "Debe ofrecer el catálogo con descripciones"
        assert d["sesion_id"]
    else:
        assert d.get("sesion_id")
    sesion = d["sesion_id"]

    if d["intencion"] == "catalogo_tipos":
        # Elige tipo específico -> pide primer dato.
        r = cliente.post("/api/v1/asistente/chat",
                         json={"mensaje": "ordinaria", "sesion_id": sesion})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["intencion"] == "crear"
        sesion = d.get("sesion_id") or sesion

    pasos = [
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
    respuestas_especificas = {"ejercicio_social": "ejercicio social 2025"}
    while ultimo and not ultimo.get("control_acta") and ultimo.get("campo_solicitado"):
        respuesta = respuestas_especificas.get(
            ultimo["campo_solicitado"],
            f"Información de prueba para {ultimo['campo_solicitado']}",
        )
        r = cliente.post(
            "/api/v1/asistente/chat",
            json={"mensaje": respuesta, "sesion_id": sesion, "autor": "capturista_demo"},
        )
        assert r.status_code == 200, r.text
        ultimo = r.json()
        sesion = ultimo.get("sesion_id") or sesion
    if ultimo and ultimo.get("confirmacion_creacion") and confirmar:
        r = cliente.post(
            "/api/v1/asistente/chat",
            json={
                "mensaje": "Confirmar y enviar a revisión",
                "sesion_id": ultimo["sesion_id"],
                "autor": "capturista_demo",
            },
        )
        assert r.status_code == 200, r.text
        ultimo = r.json()
    return ultimo


def _asignar_empresa_demo(sesion) -> None:
    from app.models.usuario import Usuario

    administrador = sesion.query(Usuario).filter_by(email="admin@pgac.com").one()
    administrador.codigo_empresa = "PGAC-EMPRESA-PRUEBA"
    administrador.nombre_sociedad = "Empresa de prueba, S.A. de C.V."
    administrador.tipo_sociedad = "sociedad_anonima_capital_variable"
    administrador.usar_info_empresa = True
    sesion.commit()


@pytest.fixture()
def cliente_capturista(cliente_autenticado, admin_token, sesion):
    from app.core import security
    from app.models.usuario import Usuario

    email = "capturista_demo@pgac.com"
    password = "clave-segura-123"
    sesion.add(
        Usuario(
            email=email,
            nombre_completo="Capturista de prueba",
            rol="capturista",
            password_hash=security.hash_password(password),
            activo=True,
            empresa_codigo="PGAC-EMPRESA-PRUEBA",
        )
    )
    sesion.commit()
    login = cliente_autenticado.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    cliente_autenticado.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    try:
        yield cliente_autenticado
    finally:
        usuario = sesion.query(Usuario).filter_by(email=email).one_or_none()
        if usuario:
            sesion.delete(usuario)
            sesion.commit()
        cliente_autenticado.headers["Authorization"] = f"Bearer {admin_token}"


def test_catalogo_si_no_sabe_que_acta(cliente_autenticado):
    cliente = cliente_autenticado
    r = cliente.post("/api/v1/asistente/chat", json={"mensaje": "No sé qué acta crear"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] in ("catalogo_tipos", "crear")
    assert "ordinaria" in r.text.lower() or d.get("tipos_acta")


def test_catalogo_inicial_breve_y_completo_solo_a_peticion(cliente_autenticado):
    from app.services.flujo_creacion import TIPOS_GUIA

    r = cliente_autenticado.post(
        "/api/v1/asistente/chat", json={"mensaje": "Quiero un acta"}
    )
    assert r.status_code == 200, r.text
    inicial = r.json()
    assert inicial["intencion"] == "catalogo_tipos"
    assert len(inicial["tipos_acta"]) == 4
    assert inicial["catalogo_completo_disponible"] is True
    assert len(inicial["respuesta"]) < 140

    r = cliente_autenticado.post(
        "/api/v1/asistente/chat",
        json={
            "mensaje": "Ver todos los tipos",
            "sesion_id": inicial["sesion_id"],
        },
    )
    assert r.status_code == 200, r.text
    completo = r.json()
    assert completo["catalogo_completo_disponible"] is False
    assert len(completo["tipos_acta"]) == len(TIPOS_GUIA)
    assert len(completo["respuesta"]) < 100


def test_cancelar_con_puntuacion_no_repite_catalogo(cliente_autenticado):
    inicio = cliente_autenticado.post(
        "/api/v1/asistente/chat", json={"mensaje": "Quiero un acta"}
    )
    assert inicio.status_code == 200, inicio.text

    cancelacion = cliente_autenticado.post(
        "/api/v1/asistente/chat",
        json={"mensaje": "Cancelar.", "sesion_id": inicio.json()["sesion_id"]},
    )
    assert cancelacion.status_code == 200, cancelacion.text
    datos = cancelacion.json()
    assert datos["intencion"] == "cancelar_creacion"
    assert "cancelada" in datos["respuesta"].lower()
    assert not datos.get("tipos_acta")
    assert not datos.get("catalogo_completo_disponible", False)


def test_cancelar_sin_sesion_no_muestra_catalogo(cliente_autenticado):
    respuesta = cliente_autenticado.post(
        "/api/v1/asistente/chat", json={"mensaje": "Cancelar"}
    )
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert datos["intencion"] == "cancelar_creacion"
    assert not datos.get("tipos_acta")


def test_creacion_guiada_envia_a_revision_sin_generar_pdf_final(cliente_capturista, sesion):
    from app.models.acta import Acta

    cliente = cliente_capturista
    email = "capturista_demo@pgac.com"
    _asignar_empresa_demo(sesion)
    ultimo = _flujo_completo(cliente)
    assert ultimo["intencion"] == "crear"
    control = ultimo.get("control_acta")
    assert control, "Debe devolver el control del acta generada"
    assert control["folio"] and control["acta_id"]
    assert control["creado_por"] == email
    assert control["estado_flujo"] == "revision"
    acta_guardada = sesion.get(Acta, control["acta_id"])
    assert acta_guardada is not None
    assert acta_guardada.empresa_codigo == "PGAC-EMPRESA-PRUEBA"
    assert not control.get("pdf_descarga"), "El PDF final requiere aprobación del Abogado"
    assert ultimo.get("texto_organizado"), "Debe devolver el texto organizado"

    # El control persiste: fecha, autor, caducidad y versión.
    r = cliente.get(f"/api/v1/actas/{control['acta_id']}")
    assert r.status_code == 200, r.text
    acta = r.json()
    assert acta["folio"] == control["folio"]
    assert acta["version"] >= 1
    assert acta["creado_por"] == email
    assert acta["created_at"]
    assert acta["estado_flujo"] == "revision"
    assert acta["datos_asistente"]["tipo_asamblea"] == "ordinaria"
    assert acta["datos_asistente"]["datos"]["sociedad"] == "Empresa de prueba, S.A. de C.V."
    assert cliente.get(f"/api/v1/actas/{control['acta_id']}/pdf").status_code == 403
    assert any(
        respuesta["campo"] == "fecha"
        and respuesta["respuesta"] == "15 de marzo de 2026"
        for respuesta in acta["datos_asistente"]["respuestas"]
    )

    cambios = dict(acta)
    cambios["lugar"] = "Av. Paseo de la Reforma 500, Ciudad de México"
    cambios["motivo_cambio"] = "Edición asistida"
    actualizada = cliente.put(
        f"/api/v1/actas/{acta['id']}",
        json=cambios,
    )
    assert actualizada.status_code == 409, actualizada.text


def test_creacion_guiada_revisa_y_permite_corregir_antes_de_enviar(cliente_capturista, sesion):
    from app.models.acta import Acta

    cliente = cliente_capturista
    _asignar_empresa_demo(sesion)
    resumen = _flujo_completo(cliente, confirmar=False)

    assert resumen["confirmacion_creacion"] is True
    assert resumen["resumen_creacion"]["sociedad (razon social)"] == "Empresa de prueba, S.A. de C.V."
    assert sesion.query(Acta).count() == 0

    corregir = cliente.post(
        "/api/v1/asistente/chat",
        json={
            "mensaje": "Cambiar la fecha",
            "sesion_id": resumen["sesion_id"],
        },
    )
    assert corregir.status_code == 200, corregir.text
    assert corregir.json()["campo_solicitado"] == "fecha"

    nueva_fecha = cliente.post(
        "/api/v1/asistente/chat",
        json={
            "mensaje": "22 de marzo de 2026",
            "sesion_id": resumen["sesion_id"],
        },
    )
    assert nueva_fecha.status_code == 200, nueva_fecha.text
    assert nueva_fecha.json()["confirmacion_creacion"] is True

    enviada = cliente.post(
        "/api/v1/asistente/chat",
        json={
            "mensaje": "Confirmar y enviar a revisión",
            "sesion_id": resumen["sesion_id"],
        },
    )
    assert enviada.status_code == 200, enviada.text
    control = enviada.json()["control_acta"]
    assert control["fecha_acta"] == "2026-03-22"
    assert sesion.get(Acta, control["acta_id"]).fecha.isoformat() == "2026-03-22"


def test_creacion_directa_con_tipo(cliente_autenticado, sesion):
    cliente = cliente_autenticado
    _asignar_empresa_demo(sesion)
    r = cliente.post("/api/v1/asistente/chat",
                     json={"mensaje": "Crea un acta de aumento de capital"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["intencion"] == "crear"
    assert d["tipo_asamblea"] == "aumento_capital"
    assert d["campo_solicitado"] == "fecha"
