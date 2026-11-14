"""Regresión de aislamiento empresarial en consultas y operaciones de actas."""

from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient


def _crear_usuario(sesion, email: str, rol: str, empresa: str | None) -> None:
    from app.core import security
    from app.models.usuario import Usuario

    sesion.add(
        Usuario(
            email=email,
            nombre_completo=email,
            rol=rol,
            password_hash=security.hash_password("clave-prueba-123"),
            activo=True,
            codigo_empresa=empresa if rol == "Administrador" else None,
            empresa_codigo=empresa if rol != "Administrador" else None,
        )
    )
    sesion.commit()


def _iniciar_sesion(cliente: TestClient, email: str) -> Dict[str, str]:
    respuesta = cliente.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "clave-prueba-123"},
    )
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def test_actas_y_datos_relacionados_quedan_aislados_por_empresa(
    cliente_anonimo: TestClient,
    admin_token: str,
    sesion: Any,
    payload_acta: Dict[str, Any],
) -> None:
    from app.models.usuario import Usuario

    admin_a = sesion.query(Usuario).filter_by(email="admin@pgac.com").one()
    empresa_a = admin_a.codigo_empresa
    empresa_b = "PGAC-TENANT-B"
    email_b = "admin-tenant-b@pgac.com"
    email_b_revisor = "revisor-tenant-b@pgac.com"
    email_super = "super-tenant-test@pgac.com"
    _crear_usuario(sesion, email_b, "Administrador", empresa_b)
    _crear_usuario(sesion, email_b_revisor, "revisor", empresa_b)
    _crear_usuario(sesion, email_super, "SuperAdministrador", None)
    headers_a = {"Authorization": f"Bearer {admin_token}"}
    headers_b = _iniciar_sesion(cliente_anonimo, email_b)
    headers_b_revisor = _iniciar_sesion(cliente_anonimo, email_b_revisor)
    headers_super = _iniciar_sesion(cliente_anonimo, email_super)

    try:
        acta_a = cliente_anonimo.post(
            "/api/v1/actas", json=payload_acta, headers=headers_a
        ).json()
        acta_b = cliente_anonimo.post(
            "/api/v1/actas", json=payload_acta, headers=headers_b
        ).json()
        assert acta_a["id"] != acta_b["id"]

        listado_b = cliente_anonimo.get("/api/v1/actas", headers=headers_b)
        assert listado_b.status_code == 200
        assert [acta["id"] for acta in listado_b.json()] == [acta_b["id"]]
        assert [
            acta["id"]
            for acta in cliente_anonimo.get(
                "/api/v1/actas/bandeja", headers=headers_b
            ).json()
        ] == [acta_b["id"]]
        assert cliente_anonimo.get(
            f"/api/v1/actas/{acta_a['id']}", headers=headers_b
        ).status_code == 404

        version_paths = (
            f"/api/v1/administracion/versiones/{acta_a['id']}",
            f"/api/v1/administracion/versiones/{acta_a['id']}/1",
        )
        for path in version_paths:
            assert cliente_anonimo.get(path, headers=headers_b).status_code == 404

        assert cliente_anonimo.put(
            f"/api/v1/actas/{acta_a['id']}",
            json=payload_acta,
            headers=headers_b,
        ).status_code == 404
        for path, body in (
            (
                f"/api/v1/actas/{acta_a['id']}/decision",
                {"accion": "aprobar"},
            ),
            (f"/api/v1/actas/{acta_a['id']}/validar", None),
        ):
            assert cliente_anonimo.post(
                path, json=body, headers=headers_b
            ).status_code == 404
        assert cliente_anonimo.post(
            f"/api/v1/actas/{acta_a['id']}/analizar-revision",
            headers=headers_b_revisor,
        ).status_code == 404
        assert cliente_anonimo.delete(
            f"/api/v1/actas/{acta_a['id']}", headers=headers_b
        ).status_code == 404

        resumen_b = cliente_anonimo.get(
            "/api/v1/administracion/resumen", headers=headers_b
        )
        assert resumen_b.status_code == 200
        assert resumen_b.json()["total_actas"] == 1
        bitacora_b = cliente_anonimo.get("/api/v1/bitacora", headers=headers_b)
        assert bitacora_b.status_code == 200
        assert all(
            entrada["entidad_id"] != acta_a["id"]
            for entrada in bitacora_b.json()
            if entrada["entidad"] == "actas"
        )

        respuesta_chat = cliente_anonimo.post(
            "/api/v1/asistente/chat",
            json={"mensaje": f"Estatus del acta {acta_a['id']}"},
            headers=headers_b,
        )
        assert respuesta_chat.status_code == 200
        assert respuesta_chat.json().get("acta") is None
        assert acta_a["folio"] not in respuesta_chat.text

        todas = cliente_anonimo.get("/api/v1/actas", headers=headers_super)
        assert {acta["id"] for acta in todas.json()} >= {
            acta_a["id"],
            acta_b["id"],
        }

        # Los datos históricos ambiguos permanecen en cuarentena para empresas.
        from app.db.init_db import _asignar_empresa_a_registros_historicos
        from app.models.acta import Acta
        from app.models.usuario import BitacoraCambios

        registro_ambiguo = sesion.get(Acta, acta_a["id"])
        registro_vinculable = sesion.get(Acta, acta_b["id"])
        assert registro_ambiguo is not None
        assert registro_vinculable is not None
        registro_ambiguo.empresa_codigo = None
        registro_ambiguo.creado_por = "autor-historico-no-vinculado"
        registro_vinculable.empresa_codigo = None
        registro_vinculable.creado_por = email_b
        sesion.query(BitacoraCambios).filter(
            BitacoraCambios.entidad == "actas",
            BitacoraCambios.entidad_id == acta_a["id"],
        ).update({"empresa_codigo": None}, synchronize_session=False)
        sesion.commit()
        _asignar_empresa_a_registros_historicos()

        sesion.refresh(registro_vinculable)
        assert registro_vinculable.empresa_codigo == empresa_b
        assert cliente_anonimo.get(
            f"/api/v1/actas/{acta_a['id']}", headers=headers_a
        ).status_code == 404
        bitacora_cuarentena = cliente_anonimo.get(
            "/api/v1/bitacora", headers=headers_a
        )
        assert all(
            entrada["entidad_id"] != acta_a["id"]
            for entrada in bitacora_cuarentena.json()
            if entrada["entidad"] == "actas"
        )
        assert cliente_anonimo.get(
            f"/api/v1/actas/{acta_b['id']}", headers=headers_b
        ).status_code == 200
        assert cliente_anonimo.get(
            f"/api/v1/actas/{acta_a['id']}", headers=headers_super
        ).status_code == 200
        reasignada_sin_permiso = cliente_anonimo.patch(
            f"/api/v1/administracion/actas/{acta_a['id']}/empresa",
            json={"codigo_empresa": empresa_a},
            headers=headers_a,
        )
        assert reasignada_sin_permiso.status_code == 403
        reasignada = cliente_anonimo.patch(
            f"/api/v1/administracion/actas/{acta_a['id']}/empresa",
            json={"codigo_empresa": empresa_a},
            headers=headers_super,
        )
        assert reasignada.status_code == 200, reasignada.text
        assert cliente_anonimo.get(
            f"/api/v1/actas/{acta_a['id']}", headers=headers_a
        ).status_code == 200
        bitacora_reasignada = cliente_anonimo.get(
            "/api/v1/bitacora", headers=headers_a
        )
        assert any(
            entrada["entidad_id"] == acta_a["id"]
            and entrada["accion"] == "reasignar_empresa"
            for entrada in bitacora_reasignada.json()
        )
    finally:
        sesion.query(Usuario).filter(
            Usuario.email.in_((email_b, email_b_revisor, email_super))
        ).delete(synchronize_session=False)
        sesion.commit()


def test_sesiones_del_asistente_pertenecen_al_usuario_y_empresa(
    cliente_anonimo: TestClient,
    admin_token: str,
    sesion: Any,
    payload_acta: Dict[str, Any],
) -> None:
    from app.models.usuario import Usuario

    admin = sesion.query(Usuario).filter_by(email="admin@pgac.com").one()
    empresa_b = "PGAC-SESSION-B"
    email_b = "admin-session-b@pgac.com"
    _crear_usuario(sesion, email_b, "Administrador", empresa_b)
    headers_a = {"Authorization": f"Bearer {admin_token}"}
    headers_b = _iniciar_sesion(cliente_anonimo, email_b)

    try:
        acta = cliente_anonimo.post(
            "/api/v1/actas", json=payload_acta, headers=headers_a
        ).json()
        inicio = cliente_anonimo.post(
            "/api/v1/asistente/chat",
            json={
                "mensaje": "Quiero cambiar el lugar",
                "acta_id": acta["id"],
                "modo": "edicion",
            },
            headers=headers_a,
        )
        assert inicio.status_code == 200, inicio.text
        sesion_id = inicio.json()["sesion_id"]

        ajena = cliente_anonimo.post(
            "/api/v1/asistente/chat",
            json={
                "mensaje": "Av. Paseo de la Reforma 500",
                "acta_id": acta["id"],
                "sesion_id": sesion_id,
                "modo": "edicion",
            },
            headers=headers_b,
        )
        assert ajena.status_code == 200, ajena.text
        assert "no pertenece a tu cuenta" in ajena.json()["respuesta"]
        assert ajena.json()["cambios_propuestos"] is None
    finally:
        sesion.query(Usuario).filter(Usuario.email == email_b).delete()
        sesion.commit()


def test_usuario_sin_empresa_no_recibe_acceso_global(
    cliente_anonimo: TestClient,
    admin_token: str,
    sesion: Any,
    payload_acta: Dict[str, Any],
) -> None:
    from app.models.usuario import Usuario

    email = "revisor-sin-empresa@pgac.com"
    _crear_usuario(sesion, email, "revisor", None)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_sin_empresa = _iniciar_sesion(cliente_anonimo, email)
    try:
        acta = cliente_anonimo.post(
            "/api/v1/actas", json=payload_acta, headers=headers_admin
        ).json()
        assert cliente_anonimo.get(
            f"/api/v1/actas/{acta['id']}", headers=headers_sin_empresa
        ).status_code == 404
        assert cliente_anonimo.get(
            "/api/v1/actas", headers=headers_sin_empresa
        ).json() == []
        resumen = cliente_anonimo.get(
            "/api/v1/administracion/resumen", headers=headers_sin_empresa
        )
        assert resumen.status_code == 200
        assert resumen.json()["total_actas"] == 0
    finally:
        sesion.query(Usuario).filter(Usuario.email == email).delete()
        sesion.commit()
