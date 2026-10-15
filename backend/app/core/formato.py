"""Utilidades de formato (fechas, horas, importes y porcentajes) en español.

Se emplean tanto en la composición del texto legal como en la maquetación del PDF,
para que el documento generado sea homogéneo.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

DIAS = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)


def fecha_larga(valor: Optional[date | datetime]) -> str:
    """``01 de octubre de 2026``."""
    if valor is None:
        return "la fecha señalada"
    return f"{valor.day:02d} de {MESES[valor.month - 1]} de {valor.year}"


def fecha_con_dia(valor: Optional[date | datetime]) -> str:
    """``jueves 01 de octubre de 2026``."""
    if valor is None:
        return "la fecha señalada"
    return f"{DIAS[valor.weekday()]} {fecha_larga(valor)}"


def fecha_corta(valor: Optional[date | datetime]) -> str:
    """``01/10/2026`` (formato ISO invertido para tablas y nombres de archivo)."""
    if valor is None:
        return ""
    return f"{valor.day:02d}/{valor.month:02d}/{valor.year}"


def fecha_iso(valor: Optional[date | datetime]) -> str:
    """``2026-10-01`` (también usado en el nombre del archivo PDF)."""
    if valor is None:
        return datetime.now().strftime("%Y-%m-%d")
    return valor.strftime("%Y-%m-%d")


def hora_larga(valor: Optional[time]) -> str:
    """``10:30 horas`` (o ``la hora señalada`` si no se capturó)."""
    if valor is None:
        return "la hora señalada"
    return f"{valor.hour:02d}:{valor.minute:02d} horas"


def marca_tiempo(valor: Optional[datetime] = None) -> str:
    """``01/10/2026 10:30`` para pies de página y metadatos."""
    valor = valor or datetime.now()
    return valor.strftime("%d/%m/%Y %H:%M")


def moneda(valor: Optional[float], moneda_simbolo: str = "$") -> str:
    """``$1,250,000.00`` (o ``importe no determinado``)."""
    if valor is None:
        return "importe no determinado"
    return f"{moneda_simbolo}{valor:,.2f}"


def acciones(valor: Optional[float]) -> str:
    """Cantidad de acciones con separador de miles y sin decimales innecesarios."""
    if valor is None:
        return "las acciones representadas"
    if float(valor).is_integer():
        return f"{valor:,.0f}"
    return f"{valor:,.2f}"


def porcentaje(valor: Optional[float], decimales: int = 2) -> str:
    """``75.00%``."""
    if valor is None:
        return "porcentaje no determinado"
    return f"{valor:.{decimales}f}%"


def texto_opcional(valor: Optional[str], predeterminado: str = "No especificado") -> str:
    """Texto de respaldo cuando el dato no fue capturado."""
    limpio = (valor or "").strip()
    return limpio or predeterminado
