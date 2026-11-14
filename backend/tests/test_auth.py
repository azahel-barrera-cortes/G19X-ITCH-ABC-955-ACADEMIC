"""Pruebas de autenticación, control de acceso por roles (RBAC) y recuperación
de contraseña.

Se usa un cliente anónimo propio (sin encabezado Authorization) para probar el
registro público y el login, sin interferir con ``cliente_autenticado``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from passlib.context import CryptContext
from fastapi.testclient import TestClient

from app.core import security
from app.models.usuario import BitacoraCambios, Usuario
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
def test_primer_usuario_se_crea_como_superadministrador(cliente_anonimo, sesion) -> None:
    """Con la base vacía, el primer registro arranca la plataforma como superadmin."""
    sesion.query(Usuario).delete()
    sesion.commit()
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "primero@pgac.com",
                "nombre_completo": "Primer Usuario",
                "rol": "capturista",  # se ignora: el primero siempre es admin
                "password": "clave-segura-123",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["rol"] == "SuperAdministrador"
    finally:
        _borrar_usuario(sesion, "primero@pgac.com")
        _restablecer_admin(sesion)


def test_autoregistro_anonimo_rechaza_rol_privilegiado(cliente_anonimo, sesion) -> None:
    """Un visitante no puede registrarse con un rol reservado."""
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "visitante@pgac.com",
                "nombre_completo": "Visitante Anonimo",
                "rol": "Administrador",  # intento de escalación: debe ignorarse
                "password": "clave-segura-123",
            },
        )
        assert respuesta.status_code == 422, respuesta.text
    finally:
        _borrar_usuario(sesion, "visitante@pgac.com")


def test_autoregistro_anonimo_vincula_usuario_a_empresa(cliente_anonimo, sesion) -> None:
    email_admin = "admin-registro@pgac.com"
    codigo_empresa = "PGAC-EMPRESA-REGISTRO"
    admin = _crear_usuario(sesion, email_admin, "Administrador")
    admin.codigo_empresa = codigo_empresa
    sesion.commit()
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "capturista-registrado@pgac.com",
                "nombre_completo": "Capturista Registrado",
                "rol": "capturista",
                "codigo_empresa": codigo_empresa,
                "password": "clave-segura-123",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["rol"] == "capturista"
        assert respuesta.json()["empresa_codigo"] == codigo_empresa
    finally:
        _borrar_usuario(sesion, "capturista-registrado@pgac.com")
        _borrar_usuario(sesion, email_admin)


def test_admin_autenticado_crea_usuario_en_su_empresa(cliente_autenticado, sesion) -> None:
    try:
        respuesta = cliente_autenticado.post(
            "/api/v1/auth/registro",
            json={
                "email": "revisor@pgac.com",
                "nombre_completo": "Revisor Designado",
                "rol": "revisor",
                "password": "clave-segura-123",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["rol"] == "revisor"
        assert respuesta.json()["empresa_codigo"].startswith("PGAC-")
    finally:
        _borrar_usuario(sesion, "revisor@pgac.com")


def test_registro_no_acepta_token_revocado_para_asignar_empresa(
    cliente_anonimo, sesion
) -> None:
    email_admin = "admin-token-revocado@pgac.com"
    admin = _crear_usuario(sesion, email_admin, "Administrador")
    admin.codigo_empresa = "PGAC-EMPRESA-TOKEN-REVOCADO"
    sesion.commit()
    try:
        login = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email_admin, "password": "secreto-1"},
        )
        token_anterior = login.json()["access_token"]
        admin.token_version += 1
        sesion.commit()

        respuesta = cliente_anonimo.post(
            "/api/v1/auth/registro",
            json={
                "email": "capturista-token-revocado@pgac.com",
                "nombre_completo": "Capturista",
                "rol": "capturista",
                "password": "clave-segura-123",
            },
            headers={"Authorization": f"Bearer {token_anterior}"},
        )

        assert respuesta.status_code == 422
        assert (
            sesion.query(Usuario)
            .filter(Usuario.email == "capturista-token-revocado@pgac.com")
            .first()
            is None
        )
    finally:
        _borrar_usuario(sesion, "capturista-token-revocado@pgac.com")
        _borrar_usuario(sesion, email_admin)


def test_admin_no_puede_crear_otro_administrador(cliente_autenticado, sesion) -> None:
    try:
        respuesta = cliente_autenticado.post(
            "/api/v1/auth/registro",
            json={
                "email": "admin-empresa@pgac.com",
                "nombre_completo": "Administrador de Empresa",
                "rol": "Administrador",
                "password": "clave-segura-123",
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
                "password": "clave-segura-123",
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
            "password": "clave-segura-123",
        },
    )
    assert respuesta.status_code == 422


def test_registro_rechaza_password_corta(cliente_anonimo) -> None:
    respuesta = cliente_anonimo.post(
        "/api/v1/auth/registro",
        json={
            "email": "password-corta@pgac.com",
            "nombre_completo": "Usuario de Prueba",
            "rol": "capturista",
            "password": "corta123",
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


def test_hash_password_no_trunca_entradas_mayores_a_72_bytes() -> None:
    password = "a" * 73
    password_hash = security.hash_password(password)

    assert security.verify_password(password, password_hash)
    assert not security.verify_password(password[:72], password_hash)


def test_login_actualiza_hash_bcrypt_legacy(cliente_anonimo, sesion) -> None:
    email = "bcrypt-legacy@pgac.com"
    password = "clave-segura-123"
    usuario = _crear_usuario(sesion, email, "capturista", password)
    usuario.password_hash = CryptContext(schemes=["bcrypt"]).hash(password)
    sesion.commit()

    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

        assert respuesta.status_code == 200
        sesion.refresh(usuario)
        assert security.pwd_context.identify(usuario.password_hash) == "bcrypt_sha256"
    finally:
        _borrar_usuario(sesion, email)


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
        sesion.refresh(usuario)
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


def test_reset_password_exitoso_se_registra_en_bitacora(cliente_anonimo, sesion) -> None:
    email = "reset-auditado@pgac.com"
    usuario = _crear_usuario(sesion, email, "capturista")
    token = crear_token_reinicio_password(usuario, sesion)
    try:
        respuesta = cliente_anonimo.post(
            "/api/v1/auth/reset-password/confirm",
            json={"token": token, "nuevo_password": "clave-nueva-9"},
        )
        assert respuesta.status_code == 200, respuesta.text

        evento = (
            sesion.query(BitacoraCambios)
            .filter(
                BitacoraCambios.usuario_id == usuario.id,
                BitacoraCambios.accion == "cambiar_password",
            )
            .order_by(BitacoraCambios.id.desc())
            .first()
        )
        assert evento is not None
        assert evento.datos_despues["password_actualizada"] is True
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
        evento = (
            sesion.query(BitacoraCambios)
            .filter(
                BitacoraCambios.usuario_id == usuario.id,
                BitacoraCambios.accion == "actualizar",
                BitacoraCambios.entidad == "usuarios",
            )
            .order_by(BitacoraCambios.id.desc())
            .first()
        )
        assert evento is not None
        assert evento.datos_despues["password_actualizada"] is True
    finally:
        _borrar_usuario(sesion, email)


def test_eliminar_usuario_conserva_bitacora_y_es_visible_globalmente(
    cliente_anonimo, sesion
) -> None:
    email_super = "super-elimina@pgac.com"
    email_eliminar = "usuario-eliminar@pgac.com"
    super_usuario = _crear_usuario(sesion, email_super, "SuperAdministrador")
    usuario = _crear_usuario(sesion, email_eliminar, "capturista")
    usuario_id = usuario.id
    usuario.empresa_codigo = "PGAC-EMPRESA-AUDITORIA"
    sesion.add(
        BitacoraCambios(
            usuario_id=usuario.id,
            empresa_codigo=usuario.empresa_codigo,
            accion="crear",
            entidad="actas",
            entidad_id=123,
            datos_despues={"folio": "PGAC-123"},
        )
    )
    sesion.commit()
    sesion.refresh(usuario)
    evento_anterior = (
        sesion.query(BitacoraCambios)
        .filter(BitacoraCambios.usuario_id == usuario.id)
        .first()
    )
    evento_anterior_id = evento_anterior.id

    try:
        inicio = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email_super, "password": "secreto-1"},
        )
        cabeceras = {"Authorization": f"Bearer {inicio.json()['access_token']}"}
        respuesta = cliente_anonimo.delete(
            f"/api/v1/auth/users/{usuario_id}", headers=cabeceras
        )
        assert respuesta.status_code == 200, respuesta.text

        sesion.expire_all()
        evento_anterior = sesion.get(BitacoraCambios, evento_anterior_id)
        assert evento_anterior is not None
        assert evento_anterior.usuario_id is None

        eventos_visibles = cliente_anonimo.get(
            "/api/v1/bitacora?limite=500", headers=cabeceras
        )
        assert eventos_visibles.status_code == 200, eventos_visibles.text
        eventos = eventos_visibles.json()
        assert any(evento["id"] == evento_anterior_id for evento in eventos)
        assert any(
            evento["accion"] == "eliminar"
            and evento["entidad"] == "usuarios"
            and evento["entidad_id"] == usuario_id
            for evento in eventos
        )
    finally:
        sesion.query(BitacoraCambios).filter(
            BitacoraCambios.id == evento_anterior_id
        ).delete(synchronize_session=False)
        sesion.query(BitacoraCambios).filter(
            BitacoraCambios.entidad == "usuarios",
            BitacoraCambios.entidad_id == usuario_id,
        ).delete(synchronize_session=False)
        sesion.query(BitacoraCambios).filter(
            BitacoraCambios.usuario_id == super_usuario.id
        ).delete(synchronize_session=False)
        sesion.commit()
        _borrar_usuario(sesion, email_eliminar)
        _borrar_usuario(sesion, email_super)


def test_bitacora_cursor_devuelve_eventos_anteriores(cliente_anonimo, sesion) -> None:
    email = "super-cursor@pgac.com"
    super_usuario = _crear_usuario(sesion, email, "SuperAdministrador")
    eventos = [
        BitacoraCambios(
            usuario_id=super_usuario.id,
            accion="validar",
            entidad="actas",
            entidad_id=identificador,
            datos_despues={"folio": f"PGAC-CURSOR-{identificador}"},
        )
        for identificador in (1, 2, 3)
    ]
    sesion.add_all(eventos)
    sesion.commit()
    ids_eventos = [evento.id for evento in eventos]

    try:
        inicio = cliente_anonimo.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "secreto-1"},
        )
        cabeceras = {"Authorization": f"Bearer {inicio.json()['access_token']}"}
        recientes = cliente_anonimo.get(
            "/api/v1/bitacora?accion=validar&limite=2", headers=cabeceras
        )
        assert recientes.status_code == 200, recientes.text
        ids_recientes = [evento["id"] for evento in recientes.json()]
        assert ids_recientes == sorted(ids_eventos, reverse=True)[0:2]

        anteriores = cliente_anonimo.get(
            f"/api/v1/bitacora?accion=validar&limite=2&cursor_id={ids_recientes[-1]}",
            headers=cabeceras,
        )
        assert anteriores.status_code == 200, anteriores.text
        assert anteriores.json()[0]["id"] == ids_eventos[0]
    finally:
        sesion.query(BitacoraCambios).filter(
            BitacoraCambios.usuario_id == super_usuario.id
        ).delete(synchronize_session=False)
        sesion.commit()
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
