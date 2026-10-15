"""Pruebas del generador de PDF (ReportLab) y del contrato de datos."""

from __future__ import annotations

import re
from io import BytesIO
from typing import Any, Dict

import pytest
from pypdf import PdfReader

from app.schemas.acta import ActaGenerarPdfRequest
from app.services import acta_service
from app.services.pdf_generator import build_acta_pdf, nombre_archivo_acta


def _texto_del_pdf(pdf: bytes) -> str:
    """Extrae el texto de todas las páginas para poder hacer aserciones."""
    lector = PdfReader(BytesIO(pdf))
    return "\n".join(pagina.extract_text() or "" for pagina in lector.pages)


def _documento_desde_servicio(payload_acta: Dict[str, Any]) -> Dict[str, Any]:
    """Integra redacción + composición + contrato de documento real."""
    desde = {clave: valor for clave, valor in payload_acta.items() if clave != "guardar"}
    peticion = ActaGenerarPdfRequest(**desde)
    borrador = acta_service.redactar(peticion)
    return acta_service.construir_documento(
        peticion,
        folio="PGAC-2026-0001",
        acuerdos=borrador["acuerdos"],
        clausulas=borrador["clausulas"],
        validacion=borrador["validacion"],
        meta={"version": 1, "estatus": "borrador", "proveedor_ia": "plantillas"},
    )


def test_pdf_integral_del_acta(payload_acta: Dict[str, Any]) -> None:
    """El documento generado por el servicio debe ser un PDF legal completo."""
    documento = _documento_desde_servicio(payload_acta)
    pdf = build_acta_pdf(documento)

    assert pdf.startswith(b"%PDF")
    assert b"%%EOF" in pdf

    texto = _texto_del_pdf(pdf)
    assert "ACTA DE ASAMBLEA GENERAL EXTRAORDINARIA" in texto
    assert "Comercializadora del Norte" in texto
    assert "Ana María Ruiz Salazar" in texto
    assert "Carlos Peña Domínguez" in texto
    assert "ACUERDO 1" in texto
    assert "Ley General de Sociedades Mercantiles" in texto
    assert "FIRMAS" in texto
    assert re.search(r"P\S*gina\s+1\s+de\s+\d+", texto), "Falta la numeración de páginas"


def test_omite_hoja_de_firmas_cuando_no_se_solicita(payload_acta: Dict[str, Any]) -> None:
    documento = _documento_desde_servicio(payload_acta)
    documento["opciones"]["incluir_hoja_firmas"] = False
    pdf = build_acta_pdf(documento)

    assert pdf.startswith(b"%PDF")
    assert "VII. FIRMAS" not in _texto_del_pdf(pdf)


def test_incluye_anexo_de_validacion(payload_acta: Dict[str, Any]) -> None:
    documento = _documento_desde_servicio(payload_acta)
    documento["opciones"]["incluir_anexo_validacion"] = True
    pdf = build_acta_pdf(documento)
    texto = _texto_del_pdf(pdf)

    assert "ANEXO" in texto
    assert "VALIDACIÓN DE CONSISTENCIA" in texto


def test_build_acta_pdf_rechaza_valores_no_diccionario() -> None:
    with pytest.raises(TypeError):
        build_acta_pdf("no soy un diccionario")  # type: ignore[arg-type]


def test_nombre_de_archivo_sin_acentos_ni_espacios() -> None:
    nombre = nombre_archivo_acta(
        "PGAC-2026-0001", "Comercializadora del Norte, S.A. de C.V.", "2026-03-15"
    )
    assert nombre.startswith("PGAC-2026-0001_")
    assert nombre.endswith(".pdf")
    assert " " not in nombre and "," not in nombre
