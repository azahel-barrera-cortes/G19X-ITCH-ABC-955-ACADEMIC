"""Extrae el texto del PDF de ejemplo para comprobar su contenido.

Uso (desde la carpeta ``backend``)::

    .venv\\Scripts\\python.exe scripts\\verificar_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

from pypdf import PdfReader  # noqa: E402


def main() -> None:
    """Comprueba las secciones clave del PDF generado por el script de ejemplo."""
    ruta = RAIZ / "ejemplos" / "acta_ejemplo.pdf"
    if not ruta.exists():
        raise SystemExit("Primero ejecuta scripts/generar_acta_ejemplo.py")

    lector = PdfReader(str(ruta))
    texto = "\n".join(pagina.extract_text() or "" for pagina in lector.pages)

    print(f"Archivo : {ruta}")
    print(f"Páginas : {len(lector.pages)}")
    print(f"Caracteres extraídos: {len(texto)}")

    secciones = [
        "ACTA DE ASAMBLEA GENERAL ORDINARIA",
        "I. DATOS GENERALES",
        "II. ASISTENCIA Y QUÓRUM",
        "III. ORDEN DEL DÍA",
        "IV. DESARROLLO DE LA ASAMBLEA",
        "V. ACUERDOS Y RESOLUCIONES",
        "VI. DECLARACIÓN DE CIERRE",
        "VII. FIRMAS",
        "ANEXO. VALIDACIÓN DE CONSISTENCIA",
    ]
    for seccion in secciones:
        encontrada = seccion.split(".")[0] in texto or seccion in texto
        print(f"  [{'OK ' if encontrada else 'FALTA'}] {seccion}")

    for dato in ("Grupo Industrial PluriActas", "María Fernanda Ortega Lima", "Página 1 de"):
        print(f"  [{'OK ' if dato in texto else 'FALTA'}] {dato}")


if __name__ == "__main__":
    main()
