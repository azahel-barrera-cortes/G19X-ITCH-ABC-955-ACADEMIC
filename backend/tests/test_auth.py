"""Pruebas de autenticación, control de acceso por roles (RBAC) y recuperación
de contraseña.

Se usa un cliente anónimo propio (sin encabezado Authorization) para probar el
registro público y el login, sin interferir con ``cliente_autenticado``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.models.usuario import Usuario
from app.services import email_service
from app.services.auth_service import crear_token_reinicio_password

ADMIN_EMAIL = "admin@pgac.com"
ADMIN_PWD = "clave-segura-123"


@pytest.fixture()
def cliente_anonimo() -> TestClient:
    """Cliente HTTP sin credenciales (independiente del cliente compartido)."""
    from app.main import app

    with TestClient(app) as cliente_pruebas:
        yield cliente_pruebas


def _crear_usuario(sesion, email: str, rol: str, password: str = "secreto-1") -> Usuario:
    """Persiste un usuario de prueba con el rol indicado."""
    sesion.query(Usuario).filter(Usuario.email == email).delete()
    usuario = Usuario(
        email=email,
        nombre_completo="Usuario de Prueba",
        rol=rol,
        password_hash=security.hash_password(password),
        activo=True,
    )
    sesion.add(usuario)
    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def _borrar_usuario(sesion, email: str) -> None:
    sesion.query(Usuario).filter(Usuario.email == email).delete()
    sesion.commit()


def _restablecer_admin(sesion) -> None:
    """Recrea el administrador que usa el fixture ``cliente_autenticado``."""
    _crear_usuario(sesion, ADMIN_EMAIL, "Administrador", ADMIN_PWD)



# ---------------------------------------------------------------------------
# Registro público y arranque del sistema
# ---------------------------------------------------------------------------
def test_primer_usuario_se_crea_como_administrador(cliente_anonimo, sesion) -> None:
    """Con la base vacía, el primer registro arranca la plataforma como admin."""
    sesion.query(Usuario).delete()
    sesion.commit()
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "primero@pgac.com",
                "nombre_completo": "Primer Usuario",
                "rol": "capturista",  # se ignora: el primero siempre es admin
                "password": "secreto-1",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["rol"] == "Administrador"
    finally:
        _borrar_usuario(sesion, "primero@pgac.com")
        _restablecer_admin(sesion)


def test_autoregistro_anonimo_fuerza_rol_capturista(cliente_anonimo, cliente_autenticado, sesion) -> None:
    """Un visitante no puede elevarse el rol: siempre queda como capturista."""
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "visitante@pgac.com",
                "nombre_completo": "Visitante Anonimo",
                "rol": "Administrador",  # intento de escalación: debe ignorarse
                "password": "secreto-1",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["rol"] == "capturista"
    finally:
        _borrar_usuario(sesion, "visitante@pgac.com")


def test_admin_autenticado_crea_usuario_en_su_empresa(cliente_autenticado, sesion) -> None:
    try:
        respuesta = cliente_autenticado.post(
            "/api/v1/auth/registro",
            json={
                "email": "revisor@pgac.com",
                "nombre_completo": "Revisor Designado",
                "rol": "revisor",
                "password": "secreto-1",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["rol"] == "revisor"
        assert respuesta.json()["empresa_codigo"].startswith("PGAC-")
    finally:
        _borrar_usuario(sesion, "revisor@pgac.com")


def test_admin_no_puede_crear_otro_administrador(cliente_autenticado, sesion) -> None:
    try:
        respuesta = cliente_autenticado.post(
            "/api/v1/auth/registro",
            json={
                "email": "admin-empresa@pgac.com",
                "nombre_completo": "Administrador de Empresa",
                "rol": "Administrador",
                "password": "secreto-1",
            },
        )
        assert respuesta.status_code == 422, respuesta.text
    finally:
        _borrar_usuario(sesion, "admin-empresa@pgac.com")


def test_superadministrador_creando_administrador_genera_codigo(
    cliente_anonimo, sesion
) -> None:
    super_usuario = _crear_usuario(
        sesion, "super-crea-admin@pgac.com", "SuperAdministrador"
    )
    try:
        login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": super_usuario.email, "password": "secreto-1"},
        )
        assert login.status_code == 200, login.text
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "admin-desde-super@pgac.com",
                "nombre_completo": "Administrador desde SuperAdmin",
                "rol": "Administrador",
                "password": "secreto-1",
            },
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["codigo_empresa"].startswith("PGAC-")
    finally:
        _borrar_usuario(sesion, "admin-desde-super@pgac.com")
        _borrar_usuario(sesion, "super-crea-admin@pgac.com")


def test_admin_solo_gestiona_usuarios_de_su_empresa(cliente_anonimo, sesion) -> None:
    admin_email = "admin-usuarios@pgac.com"
    super_email = "super-usuarios@pgac.com"
    admin_usuario = _crear_usuario(sesion, admin_email, "Administrador", "secreto-1")
    admin_usuario.codigo_empresa = "PGAC-EMPRESA-A"
    usuario_empresa = _crear_usuario(sesion, "empleado-a@pgac.com", "capturista")
    usuario_empresa.empresa_codigo = admin_usuario.codigo_empresa
    usuario_rol_no_permitido = _crear_usuario(
        sesion, "empleado-admin@pgac.com", "Administrador"
    )
    usuario_rol_no_permitido.empresa_codigo = admin_usuario.codigo_empresa
    usuario_otra_empresa = _crear_usuario(sesion, "empleado-b@pgac.com", "revisor")
    usuario_otra_empresa.empresa_codigo = "PGAC-EMPRESA-B"
    super_usuario = _crear_usuario(sesion, super_email, "SuperAdministrador", "secreto-1")
    sesion.commit()

    try:
        admin_login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": "secreto-1"},
        )
        super_login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": super_email, "password": "secreto-1"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        super_headers = {"Authorization": f"Bearer {super_login.json()['access_token']}"}

        listado_admin = cliente_anonimo.get("/api/v1/auth/users", headers=admin_headers)
        listado_super = cliente_anonimo.get("/api/v1/auth/users", headers=super_headers)
        actualizacion_admin = cliente_anonimo.put(
            f"/api/v1/auth/users/{usuario_empresa.id}",
            json={"activo": False},
            headers=admin_headers,
        )
        actualizacion_otra_empresa = cliente_anonimo.put(
            f"/api/v1/auth/users/{usuario_otra_empresa.id}",
            json={"activo": False},
            headers=admin_headers,
        )
        actualizacion_rol_no_permitido = cliente_anonimo.put(
            f"/api/v1/auth/users/{usuario_rol_no_permitido.id}",
            json={"activo": False},
            headers=admin_headers,
        )
        promocion_admin = cliente_anonimo.put(
            f"/api/v1/auth/users/{usuario_empresa.id}",
            json={"rol": "Administrador"},
            headers=admin_headers,
        )
        asignacion_super_admin = cliente_anonimo.put(
            f"/api/v1/auth/users/{usuario_empresa.id}",
            json={"rol": "SuperAdministrador"},
            headers=super_headers,
        )
        cambio_super_admin_actual = cliente_anonimo.put(
            f"/api/v1/auth/users/{super_usuario.id}",
            json={"rol": "Administrador"},
            headers=super_headers,
        )

        assert listado_admin.status_code == 200
        assert [usuario["email"] for usuario in listado_admin.json()] == ["empleado-a@pgac.com"]
        assert listado_super.status_code == 200
        assert {usuario["email"] for usuario in listado_super.json()} >= {
            admin_email,
            "empleado-a@pgac.com",
            "empleado-b@pgac.com",
            super_email,
        }
        assert actualizacion_admin.status_code == 200
        assert actualizacion_otra_empresa.status_code == 422
        assert actualizacion_rol_no_permitido.status_code == 422
        assert promocion_admin.status_code == 422
        assert asignacion_super_admin.status_code == 422
        assert cambio_super_admin_actual.status_code == 422
    finally:
        _borrar_usuario(sesion, admin_email)
        _borrar_usuario(sesion, "empleado-a@pgac.com")
        _borrar_usuario(sesion, "empleado-admin@pgac.com")
        _borrar_usuario(sesion, "empleado-b@pgac.com")
        _borrar_usuario(sesion, super_email)


def test_registro_con_email_duplicado_devuelve_422(cliente_anonimo, cliente_autenticado) -> None:
    respuesta = cliente_anonimo.post(
        "/api/v1/auth/registro",
        json={
            "email": ADMIN_EMAIL,
            "nombre_completo": "Otro Usuario",
            "rol": "capturista",
            "password": "secreto-1",
        },
    )
    assert respuesta.status_code == 422


# ---------------------------------------------------------------------------
# Login y perfil
# ---------------------------------------------------------------------------
def test_login_devuelve_token_y_perfil(cliente_anonimo, cliente_autenticado) -> None:
    login = cliente_anonimo.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PWD},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    perfil = cliente_anonimo.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert perfil.status_code == 200
    assert perfil.json()["email"] == ADMIN_EMAIL
    assert perfil.json()["rol"] == "Administrador"


def test_login_con_password_incorrecta_devuelve_401(cliente_anonimo, cliente_autenticado) -> None:
    respuesta = cliente_anonimo.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "incorrecta"},
    )
    assert respuesta.status_code == 401


# ---------------------------------------------------------------------------
# RBAC sobre los endpoints de actas
# ---------------------------------------------------------------------------
def test_capturista_no_puede_listar_ni_eliminar_actas(
    cliente_anonimo, cliente_autenticado, sesion, payload_acta
) -> None:
    _crear_usuario(sesion, "capturista@pgac.com", "capturista")
    try:
        login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": "capturista@pgac.com", "password": "secreto-1"},
        )
        token = login.json()["access_token"]
        cabeceras = {"Authorization": f"Bearer {token}"}

        # Puede redactar (rol mínimo: autenticado)…
        redaccion = cliente_anonimo.post(
            "/api/v1/actas/redactar", json=payload_acta, headers=cabeceras
        )
        assert redaccion.status_code == 200, redaccion.text

        # …pero no listar el historial (requiere revisor)…
        assert cliente_anonimo.get("/api/v1/actas", headers=cabeceras).status_code == 403

        # …ni eliminar (requiere Administrador).
        assert cliente_anonimo.delete("/api/v1/actas/1", headers=cabeceras).status_code == 403
    finally:
        _borrar_usuario(sesion, "capturista@pgac.com")


def test_sin_token_los_endpoints_protegidos_devuelven_401(cliente_anonimo) -> None:
    assert cliente_anonimo.get("/api/v1/actas").status_code == 401
    assert cliente_anonimo.get("/api/v1/administracion/resumen").status_code == 401
    assert cliente_anonimo.post(
        "/api/v1/asistente/chat", json={"mensaje": "hola"}
    ).status_code == 401


# ---------------------------------------------------------------------------
# Recuperación de contraseña
# ---------------------------------------------------------------------------
def test_flujo_recuperacion_de_password(
    cliente_anonimo, cliente_autenticado, sesion, monkeypatch
) -> None:
    email = "olvidadizo@pgac.com"
    _crear_usuario(sesion, email, "capturista")
    correos_enviados = []
    monkeypatch.setattr(email_service, "correo_configurado", lambda: True)
    monkeypatch.setattr(
        email_service,
        "enviar_correo_recuperacion",
        lambda destinatario, token: correos_enviados.append((destinatario, token)),
    )
    try:
        inicio = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "secreto-1"},
        )
        token_anterior = inicio.json()["access_token"]
        solicitud = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": email}
        )
        assert solicitud.status_code == 200, solicitud.text
        assert solicitud.json()["detalle"] is None
        assert correos_enviados[0][0] == email
        token = correos_enviados[0][1]
        usuario = sesion.query(Usuario).filter(Usuario.email == email).one()
        assert usuario.reset_token == hashlib.sha256(token.encode("utf-8")).hexdigest()

        confirmacion = cliente_anonimo.post(
            "/api/v1/auth/reset-password/confirm",
            json={"token": token, "nuevo_password": "clave-nueva-9"},
        )
        assert confirmacion.status_code == 200, confirmacion.text
        assert "access_token" not in confirmacion.json()
        assert usuario.reset_token is None
        assert usuario.token_version == 1
        assert cliente_anonimo.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_anterior}"},
        ).status_code == 401
        assert cliente_anonimo.post(
            "/api/v1/auth/reset-password/confirm",
            json={"token": token, "nuevo_password": "clave-nueva-9"},
        ).status_code == 422

        login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "clave-nueva-9"},
        )
        assert login.status_code == 200
    finally:
        _borrar_usuario(sesion, email)


def test_reset_password_superadministrador_usa_el_correo_registrado(
    cliente_anonimo, sesion, monkeypatch
) -> None:
    email = "super-reset@pgac.com"
    _crear_usuario(sesion, email, "SuperAdministrador")
    destinatarios = []
    monkeypatch.setattr(email_service, "correo_configurado", lambda: True)
    monkeypatch.setattr(
        email_service,
        "enviar_correo_recuperacion",
        lambda destinatario, _token: destinatarios.append(destinatario),
    )
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": email}
        )
        assert respuesta.status_code == 200
        assert destinatarios == [email]
    finally:
        _borrar_usuario(sesion, email)


def test_reset_password_no_revela_si_el_correo_existe(
    cliente_anonimo, sesion, monkeypatch
) -> None:
    email = "registrado-reset@pgac.com"
    _crear_usuario(sesion, email, "capturista")
    enviados = []
    monkeypatch.setattr(email_service, "correo_configurado", lambda: True)
    monkeypatch.setattr(
        email_service,
        "enviar_correo_recuperacion",
        lambda destinatario, _token: enviados.append(destinatario),
    )
    try:
        registrada = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": email}
        )
        inexistente = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": "inexistente@pgac.com"}
        )
        assert registrada.status_code == inexistente.status_code == 200
        assert registrada.json() == inexistente.json()
        assert enviados == [email]
    finally:
        _borrar_usuario(sesion, email)


def test_reset_password_expirado_no_cambia_la_contrasena(
    cliente_anonimo, sesion, monkeypatch
) -> None:
    email = "expirado-reset@pgac.com"
    usuario = _crear_usuario(sesion, email, "capturista")
    correos_enviados = []
    monkeypatch.setattr(email_service, "correo_configurado", lambda: True)
    monkeypatch.setattr(
        email_service,
        "enviar_correo_recuperacion",
        lambda destinatario, token: correos_enviados.append(token),
    )
    try:
        solicitud = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": email}
        )
        assert solicitud.status_code == 200
        usuario.reset_token_expires = datetime.now(timezone.utc) - timedelta(minutes=1)
        sesion.commit()

        confirmacion = cliente_anonimo.post(
            "/api/v1/auth/reset-password/confirm",
            json={"token": correos_enviados[0], "nuevo_password": "clave-nueva-9"},
        )
        assert confirmacion.status_code == 422
        assert security.verify_password("secreto-1", usuario.password_hash)
    finally:
        _borrar_usuario(sesion, email)


def test_reset_password_sin_configuracion_no_crea_token(
    cliente_anonimo, sesion, monkeypatch
) -> None:
    email = "sin-smtp@pgac.com"
    usuario = _crear_usuario(sesion, email, "capturista")
    monkeypatch.setattr(email_service, "correo_configurado", lambda: False)
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": email}
        )
        assert respuesta.status_code == 503
        sesion.refresh(usuario)
        assert usuario.reset_token is None
    finally:
        _borrar_usuario(sesion, email)


def test_cambio_password_desde_perfil_invalida_tokens_pendientes_y_sesiones(
    cliente_anonimo, sesion
) -> None:
    email = "cambio-perfil@pgac.com"
    usuario = _crear_usuario(sesion, email, "capturista")
    try:
        crear_token_reinicio_password(usuario, sesion)
        inicio = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "secreto-1"},
        )
        token_anterior = inicio.json()["access_token"]
        cambio = cliente_anonimo.put(
            "/api/v1/auth/me",
            json={"password": "clave-nueva-9"},
            headers={"Authorization": f"Bearer {token_anterior}"},
        )
        assert cambio.status_code == 200, cambio.text
        sesion.refresh(usuario)
        assert usuario.reset_token is None
        assert usuario.reset_token_expires is None
        assert usuario.token_version == 1
        assert cliente_anonimo.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_anterior}"},
        ).status_code == 401

        nuevo_inicio = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "clave-nueva-9"},
        )
        assert nuevo_inicio.status_code == 200
    finally:
        _borrar_usuario(sesion, email)


def test_reset_password_invalida_token_si_falla_el_envio(
    cliente_anonimo, sesion, monkeypatch
) -> None:
    email = "fallo-smtp@pgac.com"
    usuario = _crear_usuario(sesion, email, "capturista")
    monkeypatch.setattr(email_service, "correo_configurado", lambda: True)

    def fallar_envio(_destinatario, _token):
        raise email_service.ErrorEnvioCorreo("Error SMTP simulado.")

    monkeypatch.setattr(email_service, "enviar_correo_recuperacion", fallar_envio)
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": email}
        )
        assert respuesta.status_code == 200
        sesion.refresh(usuario)
        assert usuario.reset_token is None
        assert usuario.reset_token_expires is None
    finally:
        _borrar_usuario(sesion, email)


def test_token_de_recuperacion_invalido_devuelve_422(cliente_anonimo) -> None:
    respuesta = cliente_anonimo.post(
        "/api/v1/auth/reset-password/confirm",
        json={"token": "token-inventado-123", "nuevo_password": "clave-nueva-9"},
    )
    assert respuesta.status_code == 422


def test_capturista_no_puede_elevarse_por_me(cliente_anonimo, cliente_autenticado, sesion) -> None:
    _crear_usuario(sesion, "capturista@pgac.com", "capturista")
    try:
        login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": "capturista@pgac.com", "password": "secreto-1"},
        )
        cabeceras = {"Authorization": f"Bearer {login.json()['access_token']}"}
        r = cliente_anonimo.put(
            "/api/v1/auth/me",
            json={"rol": "Administrador", "activo": True},
            headers=cabeceras,
        )
        assert r.status_code == 200, r.text
        assert r.json()["rol"] == "capturista"
    finally:
        _borrar_usuario(sesion, "capturista@pgac.com")
