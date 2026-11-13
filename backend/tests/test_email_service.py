"""Pruebas del adaptador SMTP sin conexiones externas."""

from __future__ import annotations

from email.message import EmailMessage

from app.core.config import settings
from app.services import email_service


def test_correo_recuperacion_usa_smtp_con_starttls_y_autenticacion(monkeypatch) -> None:
    llamadas = {}

    class SMTPFalso:
        def __init__(self, host, port, timeout):
            llamadas["conexion"] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def ehlo(self):
            llamadas["ehlo"] = True

        def starttls(self, context):
            llamadas["starttls"] = context

        def login(self, usuario, password):
            llamadas["credenciales"] = (usuario, password)

        def send_message(self, mensaje: EmailMessage):
            llamadas["mensaje"] = mensaje

    monkeypatch.setattr(settings, "smtp_host", "smtp.example.test")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "pgac-user")
    monkeypatch.setattr(settings, "smtp_password", "smtp-secret")
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_ssl", False)
    monkeypatch.setattr(settings, "smtp_timeout_seconds", 10.0)
    monkeypatch.setattr(settings, "email_from_address", "no-reply@example.test")
    monkeypatch.setattr(settings, "email_from_name", "PGAC")
    monkeypatch.setattr(email_service.smtplib, "SMTP", SMTPFalso)

    email_service.enviar_correo_recuperacion("persona@example.test", "token-secreto")

    mensaje = llamadas["mensaje"]
    assert llamadas["conexion"] == ("smtp.example.test", 587, 10.0)
    assert llamadas["credenciales"] == ("pgac-user", "smtp-secret")
    assert mensaje["To"] == "persona@example.test"
    assert mensaje["From"] == "PGAC <no-reply@example.test>"
    assert "token-secreto" in mensaje.get_content()
    assert llamadas["starttls"] is not None
