"""Catálogos de dominio expuestos a la API y utilizados por el frontend.

Centralizan las etiquetas legibles (español) y las referencias normativas de cada
tipo de asamblea y de mayoría, evitando duplicar textos entre backend y frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.models.enums import CaracterAsistente, EstatusActa, TipoAsamblea, TipoMayoria

# ---------------------------------------------------------------------------
# Tipos de asamblea: valor técnico -> etiqueta, descripción y fundamento
# ---------------------------------------------------------------------------
TIPOS_ASAMBLEA: List[Dict[str, Any]] = [
    {
        "valor": TipoAsamblea.CONSTITUTIVA.value,
        "etiqueta": "Asamblea Constitutiva",
        "descripcion": "Aprobación de la escritura social, suscripción del capital y estatutos iniciales.",
        "articulos": ["Art. 5º LGSM", "Art. 6º LGSM"],
    },
    {
        "valor": TipoAsamblea.ORDINARIA.value,
        "etiqueta": "Asamblea General Ordinaria",
        "descripcion": "Nombramientos, informes, estados financieros y asuntos que no requieren reforma estatutaria.",
        "articulos": ["Art. 178 LGSM", "Art. 181 LGSM", "Art. 189 LGSM"],
    },
    {
        "valor": TipoAsamblea.EXTRAORDINARIA.value,
        "etiqueta": "Asamblea General Extraordinaria",
        "descripcion": "Modificación del contrato social, aumento o reducción de capital, fusión, disolución y demás supuestos del artículo 182.",
        "articulos": ["Art. 182 LGSM", "Art. 190 LGSM"],
    },
    {
        "valor": TipoAsamblea.MIXTA.value,
        "etiqueta": "Asamblea General Mixta",
        "descripcion": "Celebración conjunta de asuntos ordinarios y extraordinarios en la misma sesión.",
        "articulos": ["Art. 178 LGSM", "Art. 182 LGSM"],
    },
    {
        "valor": TipoAsamblea.AUMENTO_CAPITAL.value,
        "etiqueta": "Aumento de Capital Social",
        "descripcion": "Suscripción de nuevas acciones, capitalización de pasivos o primas de acciones.",
        "articulos": ["Art. 182 LGSM", "Art. 189 LGSM", "Art. 190 LGSM", "Art. 209 LGSM"],
    },
    {
        "valor": TipoAsamblea.REDUCCION_CAPITAL.value,
        "etiqueta": "Reducción de Capital Social",
        "descripcion": "Reembolso de aportaciones o amortización de acciones con las consecuencias del artículo 135.",
        "articulos": ["Art. 134 LGSM", "Art. 135 LGSM", "Art. 182 LGSM"],
    },
    {
        "valor": TipoAsamblea.FUSION.value,
        "etiqueta": "Fusión",
        "descripcion": "Incorporación o integración de sociedades conforme a las bases aprobadas por las asambleas.",
        "articulos": ["Art. 222 LGSM", "Art. 223 LGSM", "Art. 224 LGSM"],
    },
    {
        "valor": TipoAsamblea.ESCISION.value,
        "etiqueta": "Escisión",
        "descripcion": "División del patrimonio social en dos o más sociedades.",
        "articulos": ["Art. 228 bis LGSM"],
    },
    {
        "valor": TipoAsamblea.DISOLUCION_LIQUIDACION.value,
        "etiqueta": "Disolución y Liquidación",
        "descripcion": "Acuerdos de disolución anticipada y nombramiento de liquidadores.",
        "articulos": ["Art. 229 LGSM", "Art. 230 LGSM", "Art. 249 LGSM"],
    },
    {
        "valor": TipoAsamblea.SESION_CONSEJO.value,
        "etiqueta": "Sesión del Consejo de Administración",
        "descripcion": "Actas de consejo (no de asamblea de accionistas) con base en los estatutos sociales.",
        "articulos": ["Estatutos sociales", "Art. 158 LGSM"],
    },
]

# ---------------------------------------------------------------------------
# Tipos de mayoría
# ---------------------------------------------------------------------------
TIPOS_MAYORIA: List[Dict[str, Any]] = [
    {
        "valor": TipoMayoria.UNANIMIDAD.value,
        "etiqueta": "Unanimidad",
        "descripcion": "Voto favorable de la totalidad del capital representado en la asamblea.",
        "porcentaje_requerido": 100.0,
    },
    {
        "valor": TipoMayoria.MAYORIA_CALIFICADA.value,
        "etiqueta": "Mayoría calificada (75%)",
        "descripcion": "Tres cuartas partes del capital representado, según lo previsto por los estatutos sociales.",
        "porcentaje_requerido": 75.0,
    },
    {
        "valor": TipoMayoria.MAYORIA_ESPECIAL.value,
        "etiqueta": "Mayoría especial (dos terceras partes)",
        "descripcion": "Dos terceras partes del capital representado, cuando los estatutos lo exijan.",
        "porcentaje_requerido": 66.67,
    },
    {
        "valor": TipoMayoria.MAYORIA_SIMPLE.value,
        "etiqueta": "Mayoría simple (50% + 1)",
        "descripcion": "Más de la mitad de las acciones representadas con derecho a voto.",
        "porcentaje_requerido": 50.0,
    },
    {
        "valor": TipoMayoria.SIN_VOTACION.value,
        "etiqueta": "Sin votación (informativo)",
        "descripcion": "Asunto que solo se hace constar en el acta y no se somete a votación.",
        "porcentaje_requerido": None,
    },
]

# ---------------------------------------------------------------------------
# Carácter de cada asistente
# ---------------------------------------------------------------------------
CARACTERES_ASISTENTE: List[Dict[str, Any]] = [
    {"valor": CaracterAsistente.PRESIDENTE.value, "etiqueta": "Presidente de la asamblea"},
    {"valor": CaracterAsistente.SECRETARIO.value, "etiqueta": "Secretario de la asamblea"},
    {"valor": CaracterAsistente.ESCRUTADOR.value, "etiqueta": "Escrutador"},
    {"valor": CaracterAsistente.PROPIETARIO.value, "etiqueta": "Accionista propietario"},
    {"valor": CaracterAsistente.SUPLENTE.value, "etiqueta": "Accionista suplente (ad hoc)"},
    {"valor": CaracterAsistente.REPRESENTANTE.value, "etiqueta": "Representante con carta poder"},
    {"valor": CaracterAsistente.COMISARIO.value, "etiqueta": "Comisario"},
    {"valor": CaracterAsistente.INVITADO.value, "etiqueta": "Invitado (sin voz ni voto)"},
]

# ---------------------------------------------------------------------------
# Estatus del ciclo de vida del acta
# ---------------------------------------------------------------------------
ESTATUS_ACTA: List[Dict[str, Any]] = [
    {"valor": EstatusActa.BORRADOR.value, "etiqueta": "Borrador"},
    {"valor": EstatusActa.EN_REVISION.value, "etiqueta": "En revisión"},
    {"valor": EstatusActa.APROBADA.value, "etiqueta": "Aprobada"},
    {"valor": EstatusActa.FIRMADA.value, "etiqueta": "Firmada"},
    {"valor": EstatusActa.ARCHIVADA.value, "etiqueta": "Archivada (protocolizada)"},
]

_ETIQUETAS_TIPO_ASAMBLEA: Dict[str, str] = {item["valor"]: item["etiqueta"] for item in TIPOS_ASAMBLEA}
_ETIQUETAS_MAYORIA: Dict[str, str] = {item["valor"]: item["etiqueta"] for item in TIPOS_MAYORIA}
_PORCENTAJE_MAYORIA: Dict[str, float] = {
    item["valor"]: item["porcentaje_requerido"]
    for item in TIPOS_MAYORIA
    if item.get("porcentaje_requerido") is not None
}


def _clave(valor: Any) -> str:
    """Clave de catálogo: admite el valor literal o el miembro de un enum."""
    return str(getattr(valor, "value", valor))


def etiqueta_tipo_asamblea(valor: str) -> str:
    """Etiqueta legible de un tipo de asamblea (tolerante a valores desconocidos)."""
    clave = _clave(valor)
    return _ETIQUETAS_TIPO_ASAMBLEA.get(clave, clave.replace("_", " ").capitalize())


def etiqueta_mayoria(valor: str) -> str:
    """Etiqueta legible de un tipo de mayoría."""
    clave = _clave(valor)
    return _ETIQUETAS_MAYORIA.get(clave, clave.replace("_", " ").capitalize())


def porcentaje_requerido_mayoria(valor: str) -> float | None:
    """Porcentaje de capital exigido por el tipo de mayoría (``None`` si no aplica)."""
    return _PORCENTAJE_MAYORIA.get(_clave(valor))


def articulos_tipo_asamblea(valor: str) -> List[str]:
    """Artículos de referencia del tipo de asamblea (lista vacía si es desconocido)."""
    clave = _clave(valor)
    for item in TIPOS_ASAMBLEA:
        if item["valor"] == clave:
            return list(item.get("articulos") or [])
    return []



def catalogos() -> Dict[str, Any]:
    """Catálogos completos con los que se pueblan los formularios del frontend."""
    return {
        "tipos_asamblea": TIPOS_ASAMBLEA,
        "tipos_mayoria": TIPOS_MAYORIA,
        "caracteres_asistente": CARACTERES_ASISTENTE,
        "estatus_acta": ESTATUS_ACTA,
    }


# ---------------------------------------------------------------------------
# Artículo de la LGSM que rige el quórum de instalación según el tipo de asamblea
# ---------------------------------------------------------------------------
ARTICULO_QUORUM: Dict[str, str] = {
    TipoAsamblea.CONSTITUTIVA.value: "5º",
    TipoAsamblea.ORDINARIA.value: "189",
    TipoAsamblea.MIXTA.value: "189 y 190",
    TipoAsamblea.SESION_CONSEJO.value: "158 y los estatutos sociales",
}


def articulo_quorum(tipo_asamblea: str) -> str:
    """Artículo aplicable al quórum de instalación (por defecto el 190: extraordinarias)."""
    return ARTICULO_QUORUM.get(_clave(tipo_asamblea), "190")



