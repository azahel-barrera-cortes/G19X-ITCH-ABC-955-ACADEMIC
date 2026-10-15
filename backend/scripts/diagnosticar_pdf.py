"""Diagnóstico de la descarga del PDF: dónde se guarda y por qué puede no bajar.

Comprueba contra el backend real (uvicorn en un hilo):

1. Un acta válida -> ¿llega el PDF binario con ``Content-Disposition``?
2. ¿El acta queda persistida? (id + folio + versión en la base de datos)
3. Un acta INVÁLIDA -> ¿qué devuelve la API? Importa porque el frontend pide el
   PDF con ``responseType: 'blob'``: cuando el servidor responde con un error
   JSON, axios lo entrega como *Blob* y el mensaje real se pierde en el navegador.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import httpx

os.environ.setdefault("AI_PROVIDER", "plantillas")
RAIZ = Path(__file__).resolve().parents[1]
os.environ["DATABASE_URL"] = f"sqlite:///{(RAIZ / 'diagnostico_pdf.db').as_posix()}"

sys.path.insert(0, str(RAIZ))

PUERTO = 8142
BASE = f"http://127.0.0.1:{PUERTO}/api/v1"


def payload_valido() -> dict:
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
            {"nombre": "Ana María Ruiz Salazar", "caracter": "presidente",
             "acciones": 50000, "es_presidente": True},
            {"nombre": "Carlos Peña Domínguez", "caracter": "secretario",
             "acciones": 30000, "es_secretario": True},
        ],
        "orden_del_dia": [
            {"numero": 1, "titulo": "Aumento de capital social", "requiere_votacion": True}
        ],
        "acuerdos": [
            {
                "numero": 1,
                "titulo": "Aumento de capital social",
                "resumen": "Aumentar el capital social en $500,000.00 pesos.",
                "votacion": {"tipo_mayoria": "mayoria_simple", "acciones_a_favor": 80000},
            }
        ],
        "guardar": True,
    }


def main() -> int:
    import uvicorn

    from app.main import app

    servidor = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=PUERTO, log_level="warning")
    )
    threading.Thread(target=servidor.run, daemon=True).start()
    for _ in range(80):
        try:
            httpx.get(f"{BASE}/sistema/estado", timeout=1.0)
            break
        except Exception:
            time.sleep(0.25)

    cliente = httpx.Client(timeout=90.0)

    print("=" * 72)
    print("1) POST /actas/generar-pdf con un acta VÁLIDA")
    print("=" * 72)
    r = cliente.post(f"{BASE}/actas/generar-pdf", json=payload_valido())
    print(f"   HTTP {r.status_code}")
    print(f"   Content-Type        : {r.headers.get('content-type')}")
    print(f"   Content-Disposition : {r.headers.get('content-disposition')}")
    print(f"   Tamaño              : {len(r.content):,} bytes")
    print(f"   Es un PDF válido    : {r.content[:5] == b'%PDF-'}")
    print(f"   X-Acta-Folio        : {r.headers.get('x-acta-folio')}")
    print(f"   X-Acta-Id           : {r.headers.get('x-acta-id')}")
    print(f"   X-Acta-Guardada     : {r.headers.get('x-acta-guardada')}")
    print(f"   X-Acta-Paginas      : {r.headers.get('x-acta-paginas')}")

    acta_id = r.headers.get("x-acta-id")

    print("\n" + "=" * 72)
    print("2) ¿Dónde quedó guardada la información del acta?")
    print("=" * 72)
    if acta_id:
        guardada = cliente.get(f"{BASE}/actas/{acta_id}").json()
        print(f"   Base de datos       : diagnostico_pdf.db")
        print(f"   Tabla               : actas")
        print(f"   Folio               : {guardada['folio']}")
        print(f"   Version             : {guardada['version']}")
        print(f"   Cláusulas guardadas : {list((guardada.get('clausulas') or {}).keys())}")
        print(f"   Texto legal (chars) : {len(guardada.get('texto_legal') or '')}")
        print("   PDF en disco        : NO (se arma en memoria y viaja al navegador)")

    print("\n" + "=" * 72)
    print("3) POST /actas/generar-pdf con un acta INVÁLIDA (simula el bloqueo)")
    print("=" * 72)
    malo = payload_valido()
    malo["sociedad"] = "X"  # < 3 caracteres -> 422 del backend
    malo["guardar"] = False
    r2 = cliente.post(f"{BASE}/actas/generar-pdf", json=malo)
    print(f"   HTTP {r2.status_code}")
    print(f"   Content-Type: {r2.headers.get('content-type')}")
    detalle = json.loads(r2.content).get("detail", [])
    campos = [d.get("loc", ["?"])[-1] for d in detalle if isinstance(d, dict)]
    print(f"   Campos señalados    : {campos}")
    print("   -> Con responseType:'blob' el frontend recibe esto como Blob,")
    print("      no como JSON: mensajeDeError() no puede leer 'detail'.")

    cliente.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())