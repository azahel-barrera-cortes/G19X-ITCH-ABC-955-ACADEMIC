"""Verifica que la aplicación FastAPI se construye y enumera sus rutas.

Uso (desde la carpeta ``backend``)::

    .venv\\Scripts\\python.exe scripts\\verificar_rutas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.main import app  # noqa: E402


def main() -> None:
    """Imprime las rutas publicadas por la API y el proveedor de IA activo."""
    esquema = app.openapi()
    rutas = esquema["paths"]

    print(f"Aplicación   : {app.title} v{app.version}")
    print(f"Rutas (openapi): {len(rutas)}")
    for ruta in sorted(rutas):
        metodos = ",".join(sorted(metodo.upper() for metodo in rutas[ruta]))
        print(f"  {metodos:<18} {ruta}")

    from app.core.config import settings

    print(f"Proveedor IA : {settings.proveedor_ia_configurado}")
    print(f"Base de datos: {settings.database_url}")


if __name__ == "__main__":
    main()
