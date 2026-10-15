"""Verificación E2E de la INTELIGENCIA ARTIFICIAL con un LLM simulado.

Levanta un servidor falso con la misma API de OpenAI que consume
``ProveedorOpenAICompatible`` y comprueba el flujo completo contra el backend real
de GICORP / PluriActas:

1. ``GET  /sistema/estado``        -> reconoce el proveedor configurable.
2. ``POST /actas/redactar``        -> las cláusulas provienen del LLM.
3. ``POST /actas/redactar-stream`` -> transmite el texto en vivo por SSE.
4. Auditoría de fidelidad          -> avisa si el modelo inventa cifras.

No requiere credenciales ni conexión a Internet: el LLM es local y falso.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx

# El LLM falso debe fijarse ANTES de importar la app (Settings se cachea).
os.environ["AI_PROVIDER"] = "openai_compatible"
os.environ["AI_BASE_URL"] = "http://127.0.0.1:8199/v1"
os.environ["AI_MODEL"] = "modelo-simulado"
os.environ["AI_MAX_REINTENTOS"] = "2"
os.environ.setdefault("DATABASE_URL", "sqlite:///./verificacion_ia.db")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PUERTO_LLM = 8199
PUERTO_API = 8131
BASE_API = f"http://127.0.0.1:{PUERTO_API}/api/v1"

# Texto con una cifra INVENTADA (987654.00 no viene de los datos) para comprobar
# que la auditoría de fidelidad la detecta.
CLAUSULA_INVENTADA = (
    "PRIMERO.- Los socios acuerdan aumentar el capital social en $987,654.00 pesos "
    "mediante la emision de acciones, de conformidad con el articulo 182 de la Ley "
    "General de Sociedades Mercantiles."
)


class LlmFalso(BaseHTTPRequestHandler):
    """Implementa la API de chat completions que espera el proveedor del backend."""

    peticiones = 0

    def log_message(self, *args: object) -> None:  # silencia el log estándar
        return

    def do_POST(self) -> None:  # noqa: N802 (nombre impuesto por BaseHTTPRequestHandler)
        LlmFalso.peticiones += 1
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = json.loads(self.rfile.read(longitud) or b"{}")
        en_streaming = bool(cuerpo.get("stream"))
        contenido = json.dumps(cuerpo, ensure_ascii=False).lower()

        if "hallazgos" in contenido:
            texto = json.dumps(
                {
                    "puntaje": 96,
                    "consistencia": "El acta es consistente segun la revision del modelo simulado.",
                    "hallazgos": [],
                    "recomendaciones": ["Verificar los datos contra el libro de registro."],
                },
                ensure_ascii=False,
            )
        else:
            texto = json.dumps(
                {
                    "titulo": "Aumento de capital social",
                    "materia": "aumento_capital",
                    "clausula_legal": CLAUSULA_INVENTADA,
                    "fundamento_legal": "Articulo 182 de la LGSM",
                },
                ensure_ascii=False,
            )

        if not en_streaming:
            respuesta = {
                "choices": [{"message": {"role": "assistant", "content": texto}}],
                "usage": {"prompt_tokens": 120, "completion_tokens": 80},
            }
            datos = json.dumps(respuesta, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)
            return

        # --- Streaming SSE ---
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        palabras = texto.split(" ")
        for i, palabra in enumerate(palabras):
            trozo = palabra if i == len(palabras) - 1 else palabra + " "
            evento = {"choices": [{"delta": {"content": trozo}}]}
            self.wfile.write(f"data: {json.dumps(evento)}\n\n".encode("utf-8"))
            self.wfile.flush()
            time.sleep(0.01)
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def arrancar_llm() -> HTTPServer:
    servidor = HTTPServer(("127.0.0.1", PUERTO_LLM), LlmFalso)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor
def cargar_payload() -> dict:
    """Reutiliza el payload de ``tests/conftest.py`` para no duplicar el acta de ejemplo."""
    ruta = Path(__file__).resolve().parents[1] / "tests" / "conftest.py"
    contenido = ruta.read_text(encoding="utf-8")
    inicio = contenido.index('"sociedad":')
    fin = contenido.index('"observaciones"', inicio)
    fragmento = contenido[inicio:fin].rstrip().rstrip(",")
    datos = eval("{" + fragmento + "}")  # noqa: S307 - fixture local y controlada
    datos["guardar"] = False
    return datos


def main() -> int:
    import uvicorn

    servidor_llm = arrancar_llm()
    print(f"LLM simulado escuchando en http://127.0.0.1:{PUERTO_LLM}/v1")

    from app.main import app

    configuracion = uvicorn.Config(app, host="127.0.0.1", port=PUERTO_API, log_level="warning")
    servidor_api = uvicorn.Server(configuracion)
    threading.Thread(target=servidor_api.run, daemon=True).start()

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

    # 1) Estado del sistema ---------------------------------------------------
    print("1) GET /sistema/estado")
    estado = cliente.get(f"{BASE_API}/sistema/estado").json()
    print(
        f"   proveedor={estado['proveedor_ia']} modelo={estado.get('modelo_ia')} "
        f"ia_habilitada={estado['ia_habilitada']} streaming={estado.get('streaming_habilitado')}"
    )
    verificar(estado["proveedor_ia"] == "openai_compatible", "Se detecta el proveedor compatible")
    verificar(estado["ia_habilitada"] is True, "La IA queda habilitada")
    verificar(estado.get("modelo_ia") == "modelo-simulado", "El modelo activo es el configurado")
    verificar(len(estado.get("proveedores") or []) == 4, "Se listan los 4 proveedores posibles")

    # 2) Redacción completa ---------------------------------------------------
    print("\n2) POST /actas/redactar")
    payload = cargar_payload()
    cuerpo = cliente.post(f"{BASE_API}/actas/redactar", json=payload)
    verificar(cuerpo.status_code == 200, f"HTTP 200 (recibido {cuerpo.status_code})")
    datos = cuerpo.json()

    acuerdos = datos.get("acuerdos", [])
    verificar(bool(acuerdos), "El borrador incluye acuerdos")
    if acuerdos:
        con_ia = [a for a in acuerdos if a.get("generado_por_ia")]
        verificar(
            len(con_ia) == len(acuerdos),
            f"Todos los acuerdos provienen del LLM ({len(con_ia)}/{len(acuerdos)})",
        )
        verificar(
            "987,654.00" in (acuerdos[0].get("clausula_legal") or ""),
            "La clausula generada por el LLM llega intacta al acta",
        )
        verificar(
            "182" in (acuerdos[0].get("fundamento_legal") or ""),
            "Se conservo el fundamento legal propuesto por el modelo",
        )

    validacion = datos.get("validacion") or {}
    verificar(validacion.get("generado_por_ia") is True, "La validacion fue enriquecida por el LLM")
    if validacion.get("puntaje") is not None:
        print(f"   puntaje={validacion['puntaje']}")

    advertencias = " | ".join(datos.get("advertencias") or [])
    print(f"   advertencias={advertencias[:160]}")
    verificar(
        "no aparecen en los datos" in advertencias,
        "La auditoria de fidelidad detecta la cifra inventada por el modelo",
    )

    # 3) Streaming SSE --------------------------------------------------------
    print("\n3) POST /actas/redactar-stream (SSE)")
    eventos: list[str] = []
    acumulado = ""
    with cliente.stream("POST", f"{BASE_API}/actas/redactar-stream", json=payload) as flujo:
        verificar(
            flujo.headers.get("content-type", "").startswith("text/event-stream"),
            "La respuesta es text/event-stream",
        )
        evento_actual = None
        for linea in flujo.iter_lines():
            if linea.startswith("event:"):
                evento_actual = linea.split("event:", 1)[1].strip()
            elif linea.startswith("data:"):
                try:
                    datos_evento = json.loads(linea.split("data:", 1)[1].strip())
                except json.JSONDecodeError:
                    continue
                eventos.append(evento_actual)
                if evento_actual == "fragmento":
                    acumulado += datos_evento.get("texto", "")
                elif evento_actual == "inicio":
                    print(
                        f"   proveedor={datos_evento.get('proveedor')} "
                        f"acuerdo={datos_evento.get('acuerdo')}"
                    )

    verificar("inicio" in eventos, "Se emite el evento 'inicio'")
    verificar(
        eventos.count("fragmento") > 5,
        f"Llegan varios fragmentos en vivo ({eventos.count('fragmento')})",
    )
    verificar("fin" in eventos, "Se emite el evento 'fin'")
    verificar(len(acumulado) > 80, f"El texto llega completo ({len(acumulado)} caracteres)")
    print(f"   inicio del texto: {acumulado[:90]}...")

    cliente.close()
    servidor_llm.shutdown()

    print(f"\nLlamadas reales al LLM simulado: {LlmFalso.peticiones}")
    print("=" * 70)
    if fallos:
        print(f"RESULTADO: {len(fallos)} verificacion(es) fallida(s):")
        for fallo in fallos:
            print(f"  - {fallo}")
        return 1
    print("RESULTADO: todas las verificaciones de la IA pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())