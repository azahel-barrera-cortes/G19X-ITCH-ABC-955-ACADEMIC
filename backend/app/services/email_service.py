"""Envío de correos de recuperación mediante SMTP configurable."""

from __future__ import annotations

from email.message import EmailMessage
from email.utils import formataddr
import smtplib
import ssl

from app.core.config import settings


class CorreoNoConfiguradoError(RuntimeError):
    """Se intenta enviar un correo sin una configuración SMTP válida."""


class ErrorEnvioCorreo(RuntimeError):
    """El servidor SMTP rechazó o no pudo entregar el correo."""


def correo_configurado() -> bool:
    """Indica si se puede enviar correo con la configuración actual."""
    return settings.correo_recuperacion_configurado


def enviar_correo_recuperacion(destinatario: str, token: str) -> None:
    """Envía un token temporal sin incluirlo en respuestas de la API."""
    if not correo_configurado():
        raise CorreoNoConfiguradoError(
            "Configura SMTP_HOST y EMAIL_FROM_ADDRESS para habilitar la recuperación."
        )

    mensaje = EmailMessage()
    mensaje["Subject"] = "Recuperación de contraseña de PGAC"
    mensaje["From"] = formataddr((settings.email_from_name, settings.email_from_address))
    mensaje["To"] = destinatario
    mensaje.set_content(
        "Se solicitó restablecer la contraseña de tu cuenta de PGAC.\n\n"
        f"Tu token de recuperación es:\n{token}\n\n"
        "Ingresa este token en la pantalla de recuperación dentro de los próximos "
        "60 minutos. Si no solicitaste este cambio, ignora este correo."
    )

    try:
        if settings.smtp_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
                context=ssl.create_default_context(),
            ) as servidor:
                _autenticar_y_enviar(servidor, mensaje)
        else:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as servidor:
                if settings.smtp_starttls:
                    servidor.ehlo()
                    servidor.starttls(context=ssl.create_default_context())
                    servidor.ehlo()
                _autenticar_y_enviar(servidor, mensaje)
    except (OSError, smtplib.SMTPException) as error:
        raise ErrorEnvioCorreo("No se pudo entregar el correo de recuperación.") from error


def _autenticar_y_enviar(servidor: smtplib.SMTP, mensaje: EmailMessage) -> None:
    if settings.smtp_username:
        servidor.login(settings.smtp_username, settings.smtp_password)
    servidor.send_message(mensaje)
