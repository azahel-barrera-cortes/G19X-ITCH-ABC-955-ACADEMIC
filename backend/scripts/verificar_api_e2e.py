"""Verificación end-to-end del backend sobre HTTP real (uvicorn).

Levanta el servidor en un hilo, ejecuta el flujo completo de la API con un
cliente HTTP verdadero (no TestClient) y lo apaga al terminar.

Uso (desde la carpeta ``backend``)::

    .venv\\Scripts\\python.exe scripts\\verificar_api_e2e.py
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import httpx  # noqa: E402
import uvicorn  # noqa: E402

from app.main import app  # noqa: E402

PUERTO = 8123
BASE = f"http://127.0.0.1:{PUERTO}"

DATOS_ACTA = {
    "sociedad": "Verificadora E2E, S.A. de C.V.",
    "rfc_sociedad": "VER260101AAA",
    "tipo_asamblea": "extraordinaria",
    "titulo": "Aumento de capital social",
    "fecha": "2026-05-10",
    "hora": "09:30:00",
    "lugar": "Av. Insurgentes Sur 1602, Ciudad de México",
    "convocatoria_fecha": "2026-04-24",
    "convocatoria_medio": "Publicación en el sistema electrónico de la Secretaría de Economía",
    "convocatoria_quien": "Consejo de Administración",
    "capital_social": 200000.0,
    "acciones_totales": 200000.0,
    "capital_presente": 160000.0,
    "presidente": "Laura Beatriz Solís Márquez",
    "secretario": "Ricardo Núñez Padilla",
    "asistentes": [
        {
            "nombre": "Laura Beatriz Solís Márquez",
            "caracter": "presidente",
            "acciones": 100000,
            "es_presidente": True,
        },
        {
            "nombre": "Ricardo Núñez Padilla",
            "caracter": "secretario",
            "acciones": 60000,
            "es_secretario": True,
        },
    ],
    "orden_del_dia": [
        {
            "numero": 1,
            "titulo": "Aumento de capital social",
            "descripcion": "Suscripción de nuevas acciones y reforma estatutaria.",
            "requiere_votacion": True,
        }
    ],
    "acuerdos": [
        {
            "numero": 1,
            "titulo": "Aumento de capital social",
            "resumen": (
                "Aumentar el capital social en $80,000.00 mediante la emisión de 80,000 acciones "
                "ordinarias con respeto al derecho de preferencia."
            ),
            "votacion": {
                "tipo_mayoria": "mayoria_calificada",
                "acciones_a_favor": 160000,
                "porcentaje_requerido": 75,
                "aprobado": True,
            },
        }
    ],
    "observaciones": "Se anexa el proyecto de reforma estatutaria.",
    "guardar": True,
    "generar_clausulas": True,
    "incluir_validacion": True,
}


def _esperar_servidor(cliente: httpx.Client, intentos: int = 60) -> bool:
    """Espera a que el servidor responda ``/health`` con 200."""
    for _ in range(intentos):
        try:
            if cliente.get(f"{BASE}/health").status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    return False


def main() -> None:
    """Ejecuta el flujo completo de la API sobre HTTP y reporta los resultados."""
    servidor = uvicorn.Server(
        uvicorn.Config(app=app, host="127.0.0.1", port=PUERTO, log_level="warning")
    )
    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()

    with httpx.Client(timeout=90) as cliente:
        if not _esperar_servidor(cliente):
            raise SystemExit("El servidor no respondió en el tiempo esperado.")
        print(f"uvicorn activo en {BASE}")

        estado = cliente.get(f"{BASE}/api/v1/sistema/estado").json()
        print(f"GET   /sistema/estado       -> BD={estado['base_de_datos']} IA={estado['proveedor_ia']}")

        catalogos = cliente.get(f"{BASE}/api/v1/actas/catalogos").json()
        print(
            "GET   /actas/catalogos      -> "
            f"{len(catalogos['tipos_asamblea'])} tipos de asamblea, "
            f"{len(catalogos['tipos_mayoria'])} mayorías"
        )

        redaccion = cliente.post(f"{BASE}/api/v1/actas/redactar", json=DATOS_ACTA)
        redaccion.raise_for_status()
        borrador = redaccion.json()
        print(
            f"POST  /actas/redactar       -> folio={borrador['folio']} "
            f"puntaje={borrador['validacion']['puntaje']} cláusulas={len(borrador['clausulas'])}"
        )

        pdf = cliente.post(f"{BASE}/api/v1/actas/generar-pdf", json=DATOS_ACTA)
        pdf.raise_for_status()
        destino = RAIZ / "ejemplos" / "acta_e2e.pdf"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(pdf.content)
        print(
            f"POST  /actas/generar-pdf    -> {len(pdf.content):,} bytes | "
            f"folio={pdf.headers.get('x-acta-folio')} | páginas={pdf.headers.get('x-acta-paginas')} | "
            f"guardada={pdf.headers.get('x-acta-guardada')}"
        )
        print(f"      PDF escrito en {destino}")

        listado = cliente.get(f"{BASE}/api/v1/actas").json()
        print(f"GET   /actas                -> {len(listado)} registro(s)")
        acta_id = listado[0]["id"]

        detalle = cliente.get(f"{BASE}/api/v1/actas/{acta_id}").json()
        print(f"GET   /actas/{acta_id}           -> folio={detalle['folio']} estatus={detalle['estatus']}")

        pdf_guardado = cliente.get(f"{BASE}/api/v1/actas/{acta_id}/pdf")
        pdf_guardado.raise_for_status()
        print(
            f"GET   /actas/{acta_id}/pdf       -> {len(pdf_guardado.content):,} bytes | "
            f"versión={pdf_guardado.headers.get('x-acta-version')}"
        )

        validacion = cliente.post(f"{BASE}/api/v1/actas/{acta_id}/validar").json()
        print(f"POST  /actas/{acta_id}/validar   -> puntaje={validacion['puntaje']}")

        estatus = cliente.patch(
            f"{BASE}/api/v1/actas/{acta_id}/estatus", params={"estatus": "aprobada"}
        )
        print(f"PATCH /actas/{acta_id}/estatus   -> {estatus.json()['estatus']}")

        borrado = cliente.delete(f"{BASE}/api/v1/actas/{acta_id}").json()
        print(f"DEL   /actas/{acta_id}           -> {borrado['mensaje']}")

        faltante = cliente.get(f"{BASE}/api/v1/actas/{acta_id}")
        print(f"GET   /actas/{acta_id} (borrada) -> HTTP {faltante.status_code}")

    servidor.should_exit = True
    hilo.join(timeout=10)
    print("Servidor detenido: verificación end-to-end completada.")


if __name__ == "__main__":
    main()

