"""Configuración compartida de las pruebas.

Antes de importar la aplicación se fijan variables de entorno para que las
pruebas sean deterministas y aisladas:

* base de datos SQLite en un directorio temporal (no toca datos reales),
* ``AI_PROVIDER=plantillas`` para forzar la ruta sin servicios externos.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, List

# ---------------------------------------------------------------------------
# Entorno de pruebas (debe fijarse ANTES de importar `app`)
# ---------------------------------------------------------------------------
DIRECTORIO_TEMPORAL = Path(tempfile.mkdtemp(prefix="pluriactas-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(DIRECTORIO_TEMPORAL / 'pruebas.db').as_posix()}"
os.environ["AI_PROVIDER"] = "plantillas"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["SQL_ECHO"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.models.acta import Acta  # noqa: E402


@pytest.fixture(scope="session")
def cliente() -> Iterator[TestClient]:
    """Cliente HTTP con el ciclo de vida completo de la aplicación."""
    from app.main import app

    with TestClient(app) as cliente_pruebas:
        yield cliente_pruebas


@pytest.fixture(autouse=True)
def _base_de_datos_limpia() -> Iterator[None]:
    """Deja la tabla de actas vacía antes de cada prueba (aislamiento total)."""
    from app.db.init_db import init_db
    from app.db.session import SessionLocal
    from app.models.acta import Acta, ActaVersion

    init_db()
    base = SessionLocal()
    try:
        # El borrado masivo no dispara la cascada ORM, así que se limpian ambas
        # tablas en orden (primero las versiones hijas, luego las actas).
        base.execute(delete(ActaVersion))
        base.execute(delete(Acta))
        base.commit()
    finally:
        base.close()
    yield


@pytest.fixture()
def sesion() -> Iterator[Any]:
    """Sesión de base de datos para consultas directas en las pruebas."""
    from app.db.session import SessionLocal

    base = SessionLocal()
    try:
        yield base
    finally:
        base.close()


@pytest.fixture()
def payload_acta() -> Dict[str, Any]:
    """Formulario completo de un acta de asamblea extraordinaria con aumento de capital."""
    return {
        "sociedad": "Comercializadora del Norte, S.A. de C.V.",
        "rfc_sociedad": "CDN950101ABC",
        "tipo_asamblea": "extraordinaria",
        "titulo": "Aumento de capital y reforma estatutaria",
        "fecha": "2026-03-15",
        "hora": "10:30:00",
        "lugar": "Av. Paseo de la Reforma 1234, Ciudad de México",
        "convocatoria_fecha": "2026-02-25",
        "convocatoria_medio": "Publicación en el sistema electrónico de la Secretaría de Economía",
        "convocatoria_quien": "Consejo de Administración",
        "capital_social": 100000.0,
        "acciones_totales": 100000.0,
        "capital_presente": 80000.0,
        "presidente": "Ana María Ruiz Salazar",
        "secretario": "Carlos Peña Domínguez",
        "asistentes": [
            {
                "nombre": "Ana María Ruiz Salazar",
                "caracter": "presidente",
                "cargo": "Presidenta del Consejo de Administración",
                "acciones": 50000,
                "es_presidente": True,
            },
            {
                "nombre": "Carlos Peña Domínguez",
                "caracter": "secretario",
                "cargo": "Secretario del Consejo de Administración",
                "acciones": 20000,
                "es_secretario": True,
            },
            {
                "nombre": "Luis Alberto Gómez Terán",
                "caracter": "escrutador",
                "acciones": 10000,
                "es_escrutador": True,
            },
        ],
        "orden_del_dia": [
            {
                "numero": 1,
                "titulo": "Aumento de capital social",
                "descripcion": "Suscripción de nuevas acciones y reforma de la cláusula de capital.",
                "requiere_votacion": True,
            },
            {
                "numero": 2,
                "titulo": "Reforma de estatutos sociales",
                "descripcion": "Adecuación de la cláusula quinta de los estatutos sociales.",
                "requiere_votacion": True,
            },
        ],
        "acuerdos": [
            {
                "numero": 1,
                "titulo": "Aumento de capital social",
                "resumen": (
                    "Aumentar el capital social en $500,000.00 mediante la emisión de "
                    "50,000 acciones ordinarias, nominativas y sin expresión de valor nominal."
                ),
                "votacion": {
                    "tipo_mayoria": "unanimidad",
                    "acciones_a_favor": 80000,
                    "aprobado": True,
                },
            },
            {
                "numero": 2,
                "titulo": "Reforma de estatutos sociales",
                "resumen": "Reformar la cláusula quinta relativa al capital social y a las acciones.",
                "votacion": {
                    "tipo_mayoria": "mayoria_calificada",
                    "acciones_a_favor": 80000,
                    "porcentaje_requerido": 75.0,
                    "aprobado": True,
                },
            },
        ],
        "observaciones": "Se anexa el proyecto de reforma estatutaria firmado por la mesa directiva.",
        "guardar": True,
    }


@pytest.fixture()
def payload_quorum_insuficiente(payload_acta: Dict[str, Any]) -> Dict[str, Any]:
    """Variante con quórum por debajo del mínimo legal (25%)."""
    datos = dict(payload_acta)
    datos["capital_presente"] = 25000.0
    datos["asistentes"] = [
        {
            "nombre": "Ana María Ruiz Salazar",
            "caracter": "propietario",
            "acciones": 15000,
            "es_presidente": True,
        },
        {"nombre": "Carlos Peña Domínguez", "caracter": "propietario", "acciones": 10000},
    ]
    datos["convocatoria_fecha"] = None
    datos["convocatoria_medio"] = None
    datos["convocatoria_quien"] = None
    return datos
