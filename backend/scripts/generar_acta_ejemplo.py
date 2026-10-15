"""Script de ejemplo: redacta y genera un acta de demostración en PDF.

Uso (desde la carpeta ``backend``)::

    .venv\\Scripts\\python.exe scripts\\generar_acta_ejemplo.py

El PDF resultante se guarda en ``backend/ejemplos/acta_ejemplo.pdf`` y en consola
se imprime el resultado de la validación de consistencia.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar el script directamente (`python scripts/...`).
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.schemas.acta import ActaGenerarPdfRequest  # noqa: E402
from app.services import acta_service  # noqa: E402
from app.services.pdf_generator import build_acta_pdf  # noqa: E402

DATOS_ACTA = {
    "sociedad": "Grupo Industrial PluriActas, S.A. de C.V.",
    "rfc_sociedad": "GIP160101XYZ",
    "tipo_asamblea": "ordinaria",
    "titulo": "Aprobación de estados financieros y decreto de dividendos",
    "fecha": "2026-04-20",
    "hora": "11:00:00",
    "lugar": "Blvd. Manuel Ávila Camacho 40, Naucalpan de Juárez, Estado de México",
    "convocatoria_fecha": "2026-04-05",
    "convocatoria_medio": "Publicación en el sistema electrónico de la Secretaría de Economía",
    "convocatoria_quien": "Consejo de Administración",
    "capital_social": 500000.0,
    "acciones_totales": 500000.0,
    "capital_presente": 425000.0,
    "presidente": "María Fernanda Ortega Lima",
    "secretario": "Jorge Alberto Medina Cruz",
    "asistentes": [
        {
            "nombre": "María Fernanda Ortega Lima",
            "caracter": "presidente",
            "cargo": "Presidenta del Consejo de Administración",
            "acciones": 250000,
            "es_presidente": True,
        },
        {
            "nombre": "Jorge Alberto Medina Cruz",
            "caracter": "secretario",
            "cargo": "Secretario del Consejo de Administración",
            "acciones": 100000,
            "es_secretario": True,
        },
        {
            "nombre": "Rosa Elena Bustamante Ibarra",
            "caracter": "escrutador",
            "acciones": 75000,
            "es_escrutador": True,
        },
    ],
    "orden_del_dia": [
        {
            "numero": 1,
            "titulo": "Aprobación de estados financieros y resultado del ejercicio",
            "descripcion": "Presentación del informe del comisario y del dictamen de los estados financieros.",
            "requiere_votacion": True,
        },
        {
            "numero": 2,
            "titulo": "Decreto y pago de dividendos",
            "descripcion": "Aplicación del resultado del ejercicio y decreto de dividendos a los accionistas.",
            "requiere_votacion": True,
        },
    ],
    "acuerdos": [
        {
            "numero": 1,
            "titulo": "Aprobación de estados financieros y resultado del ejercicio",
            "resumen": (
                "Aprobar los estados financieros dictaminados al 31 de diciembre de 2025 y el informe "
                "del comisario, así como la aplicación del resultado del ejercicio con integración "
                "previa de la reserva legal."
            ),
            "votacion": {
                "tipo_mayoria": "mayoria_simple",
                "acciones_a_favor": 425000,
                "acciones_en_contra": 0,
                "abstenciones": 0,
                "aprobado": True,
            },
        },
        {
            "numero": 2,
            "titulo": "Decreto y pago de dividendos",
            "resumen": (
                "Decretar el pago de dividendos por $2,500,000.00 a cargo de las utilidades acumuladas, "
                "pagaderos a los accionistas con derecho en proporción a su tenencia accionaria."
            ),
            "votacion": {
                "tipo_mayoria": "mayoria_simple",
                "acciones_a_favor": 425000,
                "aprobado": True,
            },
        },
    ],
    "observaciones": "Se anexa el dictamen del auditor externo y el informe del comisario.",
    "guardar": False,
    "generar_clausulas": True,
    "incluir_validacion": True,
    "incluir_anexo_validacion": True,
}


def valor_de(valor: object) -> str:
    """Valor literal de un enum del backend (o el propio valor si ya es texto)."""
    return str(getattr(valor, "value", valor))


def main() -> None:
    """Redacta el acta, la valida y escribe el PDF de demostración."""
    peticion = ActaGenerarPdfRequest(**DATOS_ACTA)
    borrador = acta_service.redactar(peticion)

    documento = acta_service.construir_documento(
        peticion,
        folio="PGAC-DEMO-0001",
        acuerdos=borrador["acuerdos"],
        clausulas=borrador["clausulas"],
        validacion=borrador["validacion"],
        meta={"version": 1, "estatus": "borrador", "proveedor_ia": valor_de(borrador["proveedor"])},
    )
    pdf = build_acta_pdf(documento)

    destino = RAIZ / "ejemplos" / "acta_ejemplo.pdf"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(pdf)

    validacion = borrador["validacion"]
    print(f"PDF generado : {destino}")
    print(f"Tamaño       : {len(pdf):,} bytes | páginas: {acta_service.contar_paginas(pdf)}")
    print(f"Proveedor IA : {valor_de(borrador['proveedor'])} (habilitada: {borrador['ia_habilitada']})")
    if validacion:
        print(f"Validación   : {validacion.puntaje:.2f}/100 - {validacion.consistencia}")
        for hallazgo in validacion.hallazgos:
            print(f"  · [{hallazgo.severidad}] {hallazgo.campo}: {hallazgo.mensaje}")
    for acuerdo in borrador["acuerdos"]:
        print(f"Acuerdo {acuerdo.numero}: {acuerdo.titulo} | materia={acuerdo.materia}")


if __name__ == "__main__":
    main()
