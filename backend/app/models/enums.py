"""Enumeraciones del dominio corporativo.

Se definen como ``str, Enum`` para que Pydantic, SQLAlchemy y JSON compartan los
mismos valores literales (por ejemplo ``"ordinaria"``) y no los nombres internos
del enum. ``enum_column`` genera columnas portables entre PostgreSQL y SQLite.
"""

from __future__ import annotations

import enum
from typing import List, Type

from sqlalchemy import Enum as SAEnum

__all__ = [
    "TipoAsamblea",
    "EstatusActa",
    "CaracterAsistente",
    "TipoMayoria",
    "MateriaAcuerdo",
    "SeveridadHallazgo",
    "ProveedorIA",
    "enum_column",
]


class TipoAsamblea(str, enum.Enum):
    """Clase de asamblea/consejo que se documenta en el acta."""

    CONSTITUTIVA = "constitutiva"
    ORDINARIA = "ordinaria"
    EXTRAORDINARIA = "extraordinaria"
    MIXTA = "mixta"
    AUMENTO_CAPITAL = "aumento_capital"
    REDUCCION_CAPITAL = "reduccion_capital"
    FUSION = "fusion"
    ESCISION = "escision"
    DISOLUCION_LIQUIDACION = "disolucion_liquidacion"
    SESION_CONSEJO = "sesion_consejo"


class EstatusActa(str, enum.Enum):
    """Ciclo de vida del acta dentro de la plataforma."""

    BORRADOR = "borrador"
    EN_REVISION = "en_revision"
    APROBADA = "aprobada"
    FIRMADA = "firmada"
    ARCHIVADA = "archivada"


class CaracterAsistente(str, enum.Enum):
    """Carácter con el que comparece cada asistente a la asamblea."""

    PRESIDENTE = "presidente"
    SECRETARIO = "secretario"
    ESCRUTADOR = "escrutador"
    PROPIETARIO = "propietario"
    SUPLENTE = "suplente"
    REPRESENTANTE = "representante"
    COMISARIO = "comisario"
    INVITADO = "invitado"


class TipoMayoria(str, enum.Enum):
    """Mayoría exigida para tener por aprobado un acuerdo."""

    UNANIMIDAD = "unanimidad"
    MAYORIA_CALIFICADA = "mayoria_calificada"
    MAYORIA_ESPECIAL = "mayoria_especial"
    MAYORIA_SIMPLE = "mayoria_simple"
    SIN_VOTACION = "sin_votacion"


class MateriaAcuerdo(str, enum.Enum):
    """Materia detectada del acuerdo; determina la cláusula legal a redactar."""

    CONSTITUCION = "constitucion"
    AUMENTO_CAPITAL = "aumento_capital"
    REDUCCION_CAPITAL = "reduccion_capital"
    NOMBRAMIENTO_ADMINISTRADORES = "nombramiento_administradores"
    REMOCION_ADMINISTRADORES = "remocion_administradores"
    APROBACION_ESTADOS_FINANCIEROS = "aprobacion_estados_financieros"
    DISTRIBUCION_DIVIDENDOS = "distribucion_dividendos"
    REFORMA_ESTATUTOS = "reforma_estatutos"
    CAMBIO_DOMICILIO = "cambio_domicilio"
    FUSION = "fusion"
    ESCISION = "escision"
    DISOLUCION_LIQUIDACION = "disolucion_liquidacion"
    EMISION_TITULOS = "emision_titulos"
    DESIGNACION_DELEGADOS = "designacion_delegados"
    INFORME_CONSEJO = "informe_consejo"
    GENERICA = "generica"


class SeveridadHallazgo(str, enum.Enum):
    """Severidad de un hallazgo de la validación de IA."""

    CRITICO = "critico"
    ADVERTENCIA = "advertencia"
    INFORMATIVO = "informativo"


class ProveedorIA(str, enum.Enum):
    """Origen del texto legal: servicio externo o plantillas deterministas."""

    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai_compatible"
    PLANTILLAS = "plantillas"


def _valores(enum_cls: Type[enum.Enum]) -> List[str]:
    """Valores literales del enum (SQLAlchemy persiste estos, no los nombres)."""
    return [miembro.value for miembro in enum_cls]


def enum_column(enum_cls: Type[enum.Enum], nombre: str, longitud: int = 48) -> SAEnum:
    """Columna ``Enum`` portable entre PostgreSQL y SQLite.

    ``native_enum=False`` almacena VARCHAR + restricción CHECK, lo que evita tener
    que crear tipos ENUM nativos (necesarios en PostgreSQL, inexistentes en SQLite).
    """
    return SAEnum(
        enum_cls,
        name=nombre,
        native_enum=False,
        length=longitud,
        validate_strings=True,
        values_callable=_valores,
    )
