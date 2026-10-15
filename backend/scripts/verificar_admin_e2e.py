"""Verificación E2E del módulo de ADMINISTRACIÓN (versiones + caducidad).

Levanta el backend real con uvicorn y comprueba el flujo completo:

1. ``GET  /administracion/resumen``  -> estadísticas del repositorio.
2. ``POST /actas``                   -> crea un acta y registra la versión 1.
3. ``PUT  /actas/{id}``              -> actualiza y emite la versión 2.
4. ``GET  /administracion/versiones/{id}`` -> historial con motivos.
5. ``POST .../versiones/{id}/1/restaurar`` -> genera la versión 3 restaurada.
6. ``PUT  /administracion/caducidad/{id}`` -> fija vigencia («por_vencer»).
7. ``GET  /administracion/vigencia?estado=por_vencer`` -> aparece en el reporte.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

os.environ.setdefault("AI_PROVIDER", "plantillas")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PUERTO_API = 8132
BASE_API = f"http://127.0.0.1:{PUERTO_API}/api/v1"


def payload_base() -> dict:
    return {
        "sociedad": "Comercializadora del Norte, S.A. de C.V.",
        "tipo_asamblea": "extraordinaria",
        "titulo": "Aumento de capital",
        "fecha": "2026-03-15",
        "hora": "10:30:00",
        "lugar": "Av. Reforma 1234, CDMX",
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
    }


def main() -> int:
    import uvicorn

    from app.main import app

    servidor = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=PUERTO_API, log_level="warning")
    )
    threading.Thread(target=servidor.run, daemon=True).start()
    for _ in range(80):
        try:
            httpx.get(f"{BASE_API}/sistema/estado", timeout=1.0)
            break
        except Exception:
            time.sleep(0.25)
    print(f"API de PluriActas en {BASE_API}\n")

    cliente = httpx.Client(timeout=90.0)
    fallos: list[str] = []

    def verificar(condicion: bool, mensaje: str) -> None:
        print(f"  {'OK   ' if condicion else 'FALLA'} | {mensaje}")
        if not condicion:
            fallos.append(mensaje)

    # 1) Estado inicial del repositorio ---------------------------------------
    print("1) GET /administracion/resumen")
    estado0 = cliente.get(f"{BASE_API}/administracion/resumen").json()
    print(f"   actas={estado0['total_actas']} versiones={estado0['total_versiones']}")
    verificar(estado0["total_actas"] >= 0, "El resumen responde con totales")
    verificar(estado0["vigencia"]["dias_aviso"] == 30, "La ventana de aviso es de 30 días")

    # 2) Crear un acta (dispara la versión 1) ---------------------------------
    print("\n2) POST /actas (crea el expediente y la versión 1)")
    cuerpo = cliente.post(f"{BASE_API}/actas", json=payload_base())
    verificar(cuerpo.status_code == 201, f"HTTP 201 (recibido {cuerpo.status_code})")
    acta = cuerpo.json()
    acta_id = acta["id"]
    verificar(acta["version"] == 1, f"El acta nace en la versión 1 (id={acta_id})")

    # 3) Actualizar el acta (emite la versión 2) -------------------------------
    print("\n3) PUT /actas/{id} (actualiza y emite la versión 2)")
    datos = {
        **payload_base(),
        "lugar": "Torre Sur, Piso 8, CDMX",
        "motivo_cambio": "Cambio de sede de celebración",
        "estatus": "borrador",
    }
    cuerpo = cliente.put(f"{BASE_API}/actas/{acta_id}", json=datos)
    verificar(cuerpo.status_code == 200, f"HTTP 200 (recibido {cuerpo.status_code})")
    verificar(cuerpo.json()["version"] == 2, "La versión sube a 2")
    verificar(cuerpo.json()["lugar"] == datos["lugar"], "El cambio se aplicó al acta")

    # 4) Historial de versiones ------------------------------------------------
    print("\n4) GET /administracion/versiones/{id}")
    historial = cliente.get(f"{BASE_API}/administracion/versiones/{acta_id}").json()
    verificar(len(historial) == 2, f"El historial tiene 2 entradas ({len(historial)})")
    verificar(historial[0]["version"] == 2, "La más reciente va primero")
    verificar("Cambio de sede" in historial[0]["motivo"], "Se conserva el motivo del cambio")

    print("   GET /administracion/versiones/{id}/1 (instantánea)")
    primera = cliente.get(f"{BASE_API}/administracion/versiones/{acta_id}/1").json()
    lugar_v1 = str(primera["contenido"].get("lugar") or "")
    verificar(lugar_v1 != datos["lugar"], f"La v1 conserva la sede original: {lugar_v1[:35]}")
    verificar(primera["vigente"] is False, "La v1 ya no es la vigente")

    # 5) Restaurar la versión 1 (emite la versión 3) ---------------------------
    print("\n5) POST .../versiones/{id}/1/restaurar")
    cuerpo = cliente.post(f"{BASE_API}/administracion/versiones/{acta_id}/1/restaurar")
    verificar(cuerpo.status_code == 200, f"HTTP 200 (recibido {cuerpo.status_code})")
    verificar(cuerpo.json()["version"] == 3, "Restaurar emite una versión nueva (v3)")
    verificar(cuerpo.json()["lugar"] != datos["lugar"], "El contenido se recuperó de la v1")
    historial = cliente.get(f"{BASE_API}/administracion/versiones/{acta_id}").json()
    verificar(len(historial) == 3, "El historial nunca retrocede: ahora hay 3 entradas")
    print("   motivos:", " | ".join(v["motivo"][:40] for v in historial))

    # 6) Fijar caducidad (emite la versión 4) ----------------------------------
    print("\n6) PUT /administracion/caducidad/{id}")
    futura = (date.today() + timedelta(days=10)).isoformat()  # dentro de la ventana
    cuerpo = cliente.put(
        f"{BASE_API}/administracion/caducidad/{acta_id}",
        json={"fecha_caducidad": futura, "motivo": "Vigencia por ejercicio anual"},
    )
    verificar(cuerpo.status_code == 200, f"HTTP 200 (recibido {cuerpo.status_code})")
    con_vigencia = cuerpo.json()
    verificar(con_vigencia["fecha_caducidad"] == futura, f"Caducidad fijada al {futura}")
    verificar(con_vigencia["estado_caducidad"] == "por_vencer", "Clasificada como «por vencer»")
    print(f"   dias_para_caducar={con_vigencia['dias_para_caducar']}")
    verificar(con_vigencia["version"] == 4, "La vigencia también queda versionada")

    # 7) Reporte de vigencia ----------------------------------------------------
    print("\n7) GET /administracion/vigencia?estado=por_vencer")
    reporte = cliente.get(
        f"{BASE_API}/administracion/vigencia", params={"estado": "por_vencer"}
    ).json()
    verificar(any(a["id"] == acta_id for a in reporte), "El acta aparece en el reporte")

    print("\n   GET /administracion/vigencia?estado=vencida (debe estar vacío)")
    vacio = cliente.get(
        f"{BASE_API}/administracion/vigencia", params={"estado": "vencida"}
    ).json()
    verificar(not any(a["id"] == acta_id for a in vacio), "El acta no está vencida")

    print("\n   GET /administracion/resumen (final)")
    estado1 = cliente.get(f"{BASE_API}/administracion/resumen").json()
    print(f"   actas={estado1['total_actas']} versiones={estado1['total_versiones']}")
    verificar(
        estado1["total_versiones"] >= estado0["total_versiones"] + 4,
        "El repositorio creció con las 4 versiones del flujo",
    )
    verificar(estado1["vigencia"]["por_vencer"] >= 1, "Hay al menos un acta por vencer")

    # 8) Limpieza: elimina el acta de prueba ------------------------------------
    print("\n8) DELETE /actas/{id} (limpieza del acta de prueba)")
    cuerpo = cliente.delete(f"{BASE_API}/actas/{acta_id}")
    verificar(cuerpo.status_code == 200, f"HTTP 200 (recibido {cuerpo.status_code})")

    cliente.close()
    print("=" * 70)
    if fallos:
        print(f"RESULTADO: {len(fallos)} verificación(es) fallida(s):")
        for fallo in fallos:
            print(f"  - {fallo}")
        return 1
    print("RESULTADO: todas las verificaciones de administración pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())