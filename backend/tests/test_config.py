import pytest
from pydantic import ValidationError

from app.core.config import Settings, CLAVE_DE_EJEMPLO, PASSWORD_ADMIN_EJEMPLO


def test_secret_key_vacia_lanza_error():
    with pytest.raises(ValidationError):
        Settings(secret_key="", _env_file=None)


def test_correo_superadmin_predeterminado(monkeypatch):
    monkeypatch.delenv("SEED_ADMIN_EMAIL", raising=False)
    assert Settings(_env_file=None).seed_admin_email == "super@admin.com"


def test_secret_key_ejemplo_en_produccion_lanza_error():
    with pytest.raises(ValidationError):
        Settings(
            secret_key=CLAVE_DE_EJEMPLO,
            seed_admin_password="una-clave-admin-segura-123",
            environment="production",
            _env_file=None,
        )


def test_secret_key_corta_en_produccion_lanza_error():
    with pytest.raises(ValidationError):
        Settings(
            secret_key="clave-corta",
            seed_admin_password="una-clave-admin-segura-123",
            environment="production",
            _env_file=None,
        )


def test_password_admin_predeterminada_en_produccion_lanza_error():
    with pytest.raises(ValidationError):
        Settings(
            secret_key="clave-jwt-segura-de-al-menos-32-caracteres",
            seed_admin_password=PASSWORD_ADMIN_EJEMPLO,
            environment="production",
            _env_file=None,
        )