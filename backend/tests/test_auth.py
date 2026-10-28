"""Pruebas de autenticación, control de acceso por roles (RBAC) y recuperación
de contraseña.

Se usa un cliente anónimo propio (sin encabezado Authorization) para probar el
registro público y el login, sin interferir con ``cliente_autenticado``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.models.usuario import Usuario

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


def test_admin_autenticado_puede_asignar_cualquier_rol(cliente_autenticado, sesion) -> None:
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
    finally:
        _borrar_usuario(sesion, "revisor@pgac.com")


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
def test_flujo_recuperacion_de_password(cliente_anonimo, cliente_autenticado, sesion) -> None:
    _crear_usuario(sesion, "olvidadizo@pgac.com", "capturista")
    try:
        solicitud = cliente_anonimo.post(
            "/api/v1/auth/reset-password", json={"email": "olvidadizo@pgac.com"}
        )
        assert solicitud.status_code == 200, solicitud.text
        # En modo DEBUG el token viaja en `detalle` para probar el flujo.
        detalle = solicitud.json().get("detalle") or ""
        assert detalle.startswith("Token de desarrollo: ")
        token = detalle.replace("Token de desarrollo: ", "")

        confirmacion = cliente_anonimo.post(
            "/api/v1/auth/reset-password/confirm",
            json={"token": token, "nuevo_password": "clave-nueva-9"},
        )
        assert confirmacion.status_code == 200, confirmacion.text

        login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": "olvidadizo@pgac.com", "password": "clave-nueva-9"},
        )
        assert login.status_code == 200
    finally:
        _borrar_usuario(sesion, "olvidadizo@pgac.com")


def test_reset_password_no_revela_si_el_correo_existe(cliente_anonimo) -> None:
    respuesta = cliente_anonimo.post(
        "/api/v1/auth/reset-password", json={"email": "inexistente@pgac.com"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["detalle"] is None


def test_token_de_recuperacion_invalido_devuelve_422(cliente_anonimo) -> None:
    respuesta = cliente_anonimo.post(
        "/api/v1/auth/reset-password/confirm",
        json={"token": "token-inventado-123", "nuevo_password": "clave-nueva-9"},
    )
    assert respuesta.status_code == 422

