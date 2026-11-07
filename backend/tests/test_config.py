import pytest
from pydantic import ValidationError

from app.core.config import Settings, CLAVE_DE_EJEMPLO


def test_secret_key_vacia_lanza_error():
    with pytest.raises(ValidationError):
        Settings(secret_key="", _env_file=None)


def test_secret_key_ejemplo_en_produccion_lanza_error():
    with pytest.raises(ValidationError):
        Settings(secret_key=CLAVE_DE_EJEMPLO, environment="production", _env_file=None)