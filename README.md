<<<<<<< HEAD
# PGAC

**Página de Gestión de Actas Corporativas (LegalTech).**
Automatiza la redacción, estructuración, validación y exportación a PDF de actas
corporativas (asambleas ordinarias, extraordinarias, aumento de capital, fusión,
disolución, etc.) conforme a la Ley General de Sociedades Mercantiles (México).

- **IA para el texto legal** (Azure OpenAI / Gemini) — con plantillas legales
  deterministas como respaldo offline.
- **ReportLab para el PDF** — renderizado reproducible y ajeno al modelo.
- **Validación de consistencia** — reglas duras sobre quórum, convocatoria,
  mayorías, orden del día y fundamentos.

---

## 1. Arquitectura

```
PGAC/
├── PGAC.md                     Especificación de origen del proyecto
├── README.md                   Este documento
├── docker-compose.yml          PostgreSQL 16 (opcional, para producción)
├── .gitignore
├── backend/                    API REST (Python 3.10+ / FastAPI)
│   ├── requirements.txt            Núcleo (FastAPI, SQLAlchemy, ReportLab, httpx…)
│   ├── requirements-postgres.txt   Driver de PostgreSQL (psycopg 3)
│   ├── requirements-dev.txt        pytest + pypdf
│   ├── pytest.ini, .env.example
│   ├── scripts/                generar_acta_ejemplo.py, verificar_pdf.py, verificar_rutas.py, verificar_api_e2e.py
│   ├── ejemplos/               acta_ejemplo.pdf y acta_e2e.pdf (PDF generados de muestra)
│   ├── tests/                  29 pruebas automatizadas
│   └── app/
│       ├── main.py                 FastAPI, CORS, manejadores de errores, /health
│       ├── core/                   config, catálogos LGSM, formato, excepciones
│       ├── db/                     motor, sesiones, creación de tablas
│       ├── models/                 modelo SQLAlchemy `Acta` + enums de dominio
│       ├── schemas/acta.py         contratos Pydantic (entrada, validación, respuestas)
│       ├── services/
│       │   ├── plantillas_legales.py   15 materias con fundamentos de la LGSM
│       │   ├── ai_service.py           LLM + reglas + degradación a plantillas
│       │   ├── pdf_generator.py        build_acta_pdf(data: dict) -> bytes
│       │   └── acta_service.py         orquestación, folios, CRUD
│       └── api/v1/                 router + endpoints (actas, sistema)
└── frontend/                   React 18 + Vite + Tailwind CSS
    ├── package.json, vite.config.js, tailwind.config.js, postcss.config.js
    └── src/
        ├── App.jsx                 Navegación (Generar / Biblioteca / Guía)
        ├── api/client.js           axios: payloads JSON y PDF como Blob
        ├── constants/catalogos.js  catálogos con respaldo local
        ├── hooks/                  useActaWizard (reducer), useHistorialActas
        ├── utils/                  formato (es-MX) y descarga de archivos
        ├── components/ui/          Boton, Campo, Tarjeta, Etiqueta, Alerta, Stepper…
        ├── components/wizard/      Paso 1-4, editores de asistente y acuerdo
        ├── components/actas/       PanelValidacion, VistaPreviaActa, PanelHistorial
        └── pages/                  GenerarActa, BibliotecaActas, Ayuda
```

### Separación de responsabilidades (requisito del PGAC)

| Capa | Módulo | Responsabilidad |
|---|---|---|
| Redacción | `ai_service.py` + `plantillas_legales.py` | Convertir datos estructurados en **texto legal** |
| Composición | `acta_service.py` | Encabezado, quórum, cierre y texto consolidado |
| Maquetado | `pdf_generator.py` | **PDF formal** con ReportLab (única responsabilidad) |

Este aislamiento hace que el PDF sea determinista: el modelo nunca "dibuja" el
documento, solo redacta el cuerpo del acta.

---

## 2. Requisitos

| Componente | Versión probada |
|---|---|
| Python | 3.14.6 (compatible con 3.10+) |
| pip | 26.x |
| Node.js | v24.17.0 |
| npm | 11.13.0 |
| PostgreSQL | 16 (opcional; el desarrollo usa SQLite) |

> En Windows con la política de ejecución restringida, usa `npm.cmd` y `cmd /c`
> en lugar de `npm`/`npm.ps1`.

## 3. Puesta en marcha del backend

```powershell
cd backend

# 1) Entorno virtual e instalación de dependencias (núcleo + pruebas)
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# 2) Configuración (opcional; sin .env se usa SQLite y plantillas locales)
copy .env.example .env

# 3) Arranque en desarrollo
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- API interactiva: <http://127.0.0.1:8000/docs> · ReDoc: <http://127.0.0.1:8000/redoc>
- Estado: `GET /health` y `GET /api/v1/sistema/estado`

### Variables de entorno principales (`backend/.env`)

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./pgac.db` | Cadena SQLAlchemy. PostgreSQL: `postgresql+psycopg://usuario:clave@host:5432/pgac` |
| `AUTO_CREATE_TABLES` | `true` | Crea las tablas al arrancar (en producción usa migraciones) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Orígenes permitidos por CORS |
| `AI_PROVIDER` | `auto` | `auto` \| `azure_openai` \| `gemini` \| `plantillas` |
| `AI_ALLOW_FALLBACK` | `true` | Degrada a plantillas si el LLM falla |
| `AZURE_OPENAI_*` | vacío | Endpoint, clave, deployment y api-version |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | vacío | Credenciales de Google Gemini |
| `MARGEN_CM` | `2.5` | Márgenes del PDF |
| `PIE_CONFIDENCIALIDAD` | texto legal | Leyenda al pie de cada página |

---

## 4. Puesta en marcha del frontend

```powershell
cd frontend

npm.cmd install          # o `npm install` si tu política de ejecución lo permite
copy .env.example .env   # opcional

npm.cmd run dev          # http://localhost:5173  (proxy /api -> 127.0.0.1:8000)
npm.cmd run build        # genera dist/ para producción
npm.cmd run preview      # sirve dist/ en http://localhost:4173
```

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | Ruta base de la API consumida por axios |
| `VITE_API_PROXY` | `http://127.0.0.1:8000` | Destino del proxy de desarrollo de Vite |

> Con `VITE_API_BASE_URL=/api/v1` el navegador llama al mismo origen y Vite
> reenvía al backend, por lo que no hay problemas de CORS en desarrollo. En
> producción publica `dist/` tras un proxy que exponga `/api`.

### Flujo de uso de la interfaz

1. **Generar acta** → Paso 1 *Datos generales* → Paso 2 *Asistentes y quórum* →
   Paso 3 *Orden del día y acuerdos* → Paso 4 *Revisión y PDF*.
2. En el paso 4: **«Generar borrador con IA»** devuelve cláusulas + validación;
   **«Descargar PDF final»** compila el PDF (`Blob`) y lo descarga, mostrando
   folio, versión, páginas y proveedor de IA leídos de los encabezados `X-Acta-*`.
3. **Biblioteca de actas** → filtros por folio/sociedad, tipo y estatus;
   descarga, edición, revalidación, cambio de estatus y eliminación.

---

## 5. Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de la plataforma (BD + proveedor de IA) |
| `GET` | `/api/v1/sistema/estado` | Igual que `/health`, dentro de la API versionada |
| `GET` | `/api/v1/actas/catalogos` | Tipos de asamblea, mayorías, caracteres y estatus |
| `POST` | `/api/v1/actas/redactar` | Borrador con IA + validación (no persiste) |
| `POST` | `/api/v1/actas/generar-pdf` | **Endpoint principal**: redacta, guarda y devuelve el PDF |
| `POST` | `/api/v1/actas` | Crea y guarda el acta (sin PDF) |
| `GET` | `/api/v1/actas` | Historial con filtros (`sociedad`, `tipo_asamblea`, `estatus`, `texto`, paginación) |
| `GET` | `/api/v1/actas/{id}` | Acta completa (cláusulas y validación) |
| `PUT` | `/api/v1/actas/{id}` | Reemplaza el contenido e incrementa la versión |
| `PATCH` | `/api/v1/actas/{id}/estatus` | Cambia el estatus del expediente |
| `GET` | `/api/v1/actas/{id}/pdf` | Regenera el PDF desde la base de datos (sin IA) |
| `POST` | `/api/v1/actas/{id}/validar` | Revalida la consistencia y la guarda |
| `DELETE` | `/api/v1/actas/{id}` | Elimina el acta |
| `GET` | `/api/v1/administracion/resumen` | Totales, estatus y clasificación de vigencia |
| `GET` | `/api/v1/administracion/vigencia` | Actas por vigencia (`vencida`, `por_vencer`, `vigente`, `sin_fecha`) |
| `GET` | `/api/v1/administracion/versiones/{id}` | Historial de versiones (más reciente primero) |
| `GET` | `/api/v1/administracion/versiones/{id}/{n}` | Instantánea completa de una versión |
| `POST` | `/api/v1/administracion/versiones/{id}/{n}/restaurar` | Restaura y emite una versión nueva |
| `PUT` | `/api/v1/administracion/caducidad/{id}` | Fija, amplía o elimina la fecha de caducidad |

### Endpoint principal: `POST /api/v1/actas/generar-pdf`

Además del campo `guardar`, acepta las opciones de maquetado
`incluir_tabla_asistentes`, `incluir_hoja_firmas` e `incluir_anexo_validacion`, y
las de proceso `generar_clausulas` e `incluir_validacion`.

Devuelve el binario `application/pdf` con estos encabezados de trazabilidad
(expuestos por CORS):

| Encabezado | Contenido |
|---|---|
| `X-Acta-Folio` | Folio consecutivo (`PGAC-AAAA-0001`) |
| `X-Acta-Id` / `X-Acta-Version` | Identificador y versión del acta guardada |
| `X-Acta-Paginas` | Número de páginas del PDF |
| `X-Acta-Guardada` | `true` si quedó persistida |
| `X-IA-Proveedor` / `X-IA-Habilitada` | `azure_openai`, `gemini` o `plantillas` |
| `X-IA-Advertencias` | Avisos cuando el LLM falló y se usaron plantillas |
| `X-Validacion-Puntaje` | Puntaje de consistencia (0-100) |

Ejemplo con `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/actas/generar-pdf \
  -H "Content-Type: application/json" \
  -d @acta.json -o acta.pdf -D -
```

---

## 6. Modelo de datos

Tabla `actas` (SQLAlchemy 2.0, portable PostgreSQL/SQLite):

| Grupo | Columnas |
|---|---|
| Identificación | `id`, `folio` (único), `version` |
| Generales | `sociedad`, `rfc_sociedad`, `tipo_asamblea`, `titulo`, `fecha`, `hora`, `lugar` |
| Convocatoria | `convocatoria_fecha`, `convocatoria_medio`, `convocatoria_quien` |
| Capital | `capital_social`, `acciones_totales`, `capital_presente`, `quorum_porcentaje` |
| Mesa directiva | `presidente`, `secretario` |
| Cuerpo (JSON) | `asistentes`, `orden_del_dia`, `acuerdos`, `clausulas`, `validacion_ia` |
| Documento | `texto_legal`, `observaciones` |
| Trazabilidad | `proveedor_ia`, `estatus`, `created_at`, `updated_at` |

Los catálogos (`tipo_asamblea`, `estatus`) se almacenan como `VARCHAR + CHECK`
para ser portables entre PostgreSQL y SQLite.

---

## 7. Inteligencia Artificial: proveedores, redacción y seguridad

### 7.1 Qué hace la IA dentro del acta

La IA interviene en dos momentos, ambos sobre **datos estructurados** que captura el
usuario (nunca inventa hechos):

| Momento | Qué produce | Dónde se aplica |
|---|---|---|
| **Redacción** | `clausula_legal`, `fundamento_legal` y `materia` de cada acuerdo | Cuerpo del acta (PDF) |
| **Validación** | `puntaje`, `hallazgos` y `recomendaciones` | Anexo opcional y panel web |

El maquetado del PDF **nunca** lo hace el modelo: `pdf_generator.py` (ReportLab) es
determinista. Esto cumple la separación exigida por el proyecto y garantiza que el
documento final sea reproducible.

### 7.2 Proveedores soportados

Se eligió una **capa de transporte genérica** (`llm_providers.py`) que aísla *cómo*
se habla con el modelo de *qué* se le pide (los prompts viven en `ai_service.py`).
Añadir un proveedor nuevo no toca la lógica legal.

| `AI_PROVIDER` | Servicio | Credenciales |
|---|---|---|
| `auto` (por defecto) | Azure OpenAI → Gemini → compatible → plantillas | detecta la primera disponible |
| `azure_openai` | Azure OpenAI (chat completions) | `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` |
| `gemini` | Google Gemini (`generateContent`) | `GEMINI_API_KEY` |
| `openai_compatible` | **Cualquier API compatible con OpenAI**: OpenAI, Ollama, Groq, DeepSeek, LM Studio, vLLM | `AI_BASE_URL` + `AI_MODEL` (`AI_API_KEY` opcional) |
| `plantillas` | Redacción determinista local | ninguna |

> **Recomendación para información societaria confidencial:** `openai_compatible`
> con **Ollama en local**. El acta nunca sale de tu equipo y no hay costos:
> ```bash
> ollama pull llama3.1:8b
> ```
> ```env
> AI_PROVIDER=openai_compatible
> AI_BASE_URL=http://localhost:11434/v1
> AI_MODEL=llama3.1:8b
> AI_API_KEY=
> ```

### 7.3 Degradación controlada (el sistema nunca queda inoperante)

Cadena de intento: **proveedor principal → alterno → plantillas legales**.

* Reintentos con *backoff* exponencial y *jitter* solo en errores transitorios
  (408/409/425/429/5xx y fallos de red); **nunca** en 400/401/403, que son permanentes.
* Si el despliegue rechaza el modo JSON, se reintenta sin `response_format` y se
  extrae el JSON del texto.
* Si todo falla, el acta se genera con las plantillas y se registra en
  `advertencias` (visible en la web y en la cabecera `X-IA-Advertencias` del PDF).
* El PDF nunca se bloquea por una caída del proveedor de IA.

### 7.4 Salvaguardas para texto legal

Dos controles verificados que reducen el riesgo jurídico del uso de un LLM:

1. **Prompts cerrados.** El sistema exige JSON con forma fija y prohíbe inventar
   hechos, montos, fechas o artículos. Se conserva el resumen del usuario.
2. **Auditoría de fidelidad** (`AI_VERIFICAR_FIDELIDAD=true`). Después de redactar se
   comparan las cifras del texto contra las capturadas; las que no estén
   sustentadas se reportan como advertencia. Las referencias normativas
   («artículo 182 LGSM») se excluyen porque provienen de la ley, no del acta.

> El modelo **no sustituye la revisión de un abogado corporativo**; el sistema lo
> advierte en la interfaz, en el pie del PDF y en las recomendaciones de validación.

### 7.5 Redacción en vivo (SSE)

`POST /api/v1/actas/redactar-stream` transmite la cláusula del primer acuerdo
fragmento a fragmento (`inicio` → `fragmento`… → `fin`). En la web, el botón
**«Ver redacción en vivo»** muestra el texto mientras se genera.

### 7.6 Parámetros de ajuste

| Variable | Defecto | Para qué sirve |
|---|---|---|
| `AI_TEMPERATURE` | `0.2` | Determinismo: redacción jurídica reproducible |
| `AI_MAX_TOKENS` | `1500` | Tope por cláusula (evita desbordes y costos) |
| `AI_MAX_REINTENTOS` | `3` | Intentos por proveedor ante errores transitorios |
| `AI_TIMEOUT_SECONDS` | `45` | Tiempo máximo de espera al proveedor |
| `AI_VERIFICAR_FIDELIDAD` | `true` | Auditoría de cifras inventadas |
| `AI_STREAM` | `true` | Habilita el endpoint SSE |

### 7.7 ¿Dónde se guarda el PDF y por qué a veces no descarga?

Es la duda más común, así que conviene ser explícito. Hay **dos cosas distintas**:

| Qué | Dónde vive | Quién lo conserva |
|---|---|---|
| **El PDF** | Solo en memoria (`io.BytesIO`) y en la descarga del navegador | El usuario (carpeta `Descargas`) |
| **Los datos del acta** | Base de datos: `backend/pgac.db` (SQLite) o PostgreSQL | El servidor, de forma permanente |

Por diseño **el servidor no acumula archivos PDF en disco**: se arma, se envía y se
descarta. Así no quedan documentos societarios confidenciales huérfanos en el equipo
del servidor. El acta sí queda registrada (folio, versión, cláusulas, texto legal,
validación, estatus) y el PDF se **regenera bajo demanda** con
`GET /api/v1/actas/{id}/pdf`, idéntico byte a byte gracias al maquetado determinista.

El archivo se nombra `PGAC-AAAA-NNNN_Razón_Social_AAAA-MM-DD.pdf` y viaja en la
cabecera `Content-Disposition`, respetando acentos y espacios.

**Si el PDF no baja, revisa en este orden:**

1. **¿Faltan datos de los pasos 1-3?** El botón «Descargar PDF final» valida antes
   de llamar al backend; si algo falta, te devuelve al paso correspondiente y lo
   señala en rojo.
2. **Chrome/Edge bloquean descargas automáticas** cuando la pestaña no tiene foco.
   Revisa el icono de descarga bloqueada en la barra del navegador, o usa el botón
   **«Abrir en otra pestaña»**, que abre el PDF en una pestaña nueva.
3. **CORS o el proxy de Vite**: si el frontend corre en otro puerto, el proxy de
   `vite.config.js` debe apuntar al backend (`VITE_API_PROXY`).

> Un error de validación (422) se reportaba antes como «ocurrió un error inesperado»,
> porque la respuesta del PDF llega como `Blob` y no como JSON. Ya se desempaqueta y
> se muestran los campos exactos que corregir.

---

## 8. Pruebas y verificación

```powershell
cd backend
.venv\Scripts\python.exe -m pytest                            # 44 pruebas
.venv\Scripts\python.exe scripts\generar_acta_ejemplo.py     # PDF de demostración
.venv\Scripts\python.exe scripts\verificar_pdf.py            # inspecciona el PDF
.venv\Scripts\python.exe scripts\verificar_rutas.py          # lista las rutas OpenAPI
.venv\Scripts\python.exe scripts\verificar_api_e2e.py        # flujo HTTP real con uvicorn
.venv\Scripts\python.exe scripts\verificar_ia_e2e.py        # IA con un LLM simulado local
```

> `verificar_ia_e2e.py` levanta un **LLM falso** con la API de OpenAI y un servidor
> uvicorn real: comprueba la redacción con IA, el streaming SSE y la auditoría de
> fidelidad **sin requerir credenciales ni conexión a internet**.

Cobertura de las pruebas:

| Archivo | Qué verifica |
|---|---|
| `tests/test_plantillas_legales.py` | Todas las materias con plantilla, detección por palabras clave y tipo de asamblea, ordinales y fundamentos |
| `tests/test_ai_service.py` | Detección de proveedor (4 proveedores), redacción determinista, validación con puntaje alto y quórum crítico, extracción de JSON, **redacción vía LLM simulado**, **degradación por fallo**, **streaming**, **auditoría de fidelidad** y que la clave API nunca viaje en el cuerpo JSON |
| `tests/test_pdf_generator.py` | Integración real redacción→documento→PDF, secciones presentes, numeración de páginas, anexo de validación y nombre de archivo |
| `tests/test_api_actas.py` | `/health`, catálogos, `redactar`, `generar-pdf` (binario + guardado), CRUD completo, 404 y 422 |

Resultados obtenidos en esta máquina:

```
55 passed
PDF de ejemplo: 4 páginas, 11,940 bytes, validación 100.00/100
Frontend: vite build -> 115 módulos, dist/assets/index-*.js 279.48 kB (gzip 86.82 kB)

Verificación E2E de la IA (LLM simulado, llamadas HTTP reales):
  1) /sistema/estado        -> proveedor=openai_compatible, modelo=modelo-simulado
  2) /actas/redactar        -> 2/2 acuerdos generados por IA, validación enriquecida (96.0)
                              auditoría: "menciona cifras que no aparecen en los datos (987654.00)"
  3) /actas/redactar-stream -> text/event-stream, 43 fragmentos, texto completo (328 chars)
  Llamadas reales al LLM: 4  ->  RESULTADO: todas las verificaciones pasaron
```

---

## 9. PostgreSQL

Por defecto se usa SQLite (`backend/pgac.db`) para que el proyecto funcione
sin infraestructura. Para PostgreSQL:

```powershell
docker compose up -d                     # si tienes Docker Desktop
pip install -r requirements-postgres.txt # driver psycopg 3
# backend/.env
DATABASE_URL=postgresql+psycopg://pgac:pgac@localhost:5432/pgac
```

> En esta máquina **Docker no está instalado**, por lo que `docker-compose.yml`
> se entrega como plantilla lista para usarse; la ruta validada de extremo a
> extremo fue SQLite. El driver de PostgreSQL se mantiene en un archivo aparte
> porque las ruedas binarias dependen de la versión de Python.

En producción conviene además:
`AUTO_CREATE_TABLES=false` + migraciones (Alembic), `DEBUG=false`, `CORS_ORIGINS`
restringido y publicación de `frontend/dist` tras un proxy con HTTPS.

---

## 10. Notas legales y limitaciones

- La plataforma es una **herramienta de apoyo documental**: no sustituye la
  revisión de un abogado corporativo ni la protocolización ante fedatario público.
- Las referencias normativas corresponden a la **Ley General de Sociedades
  Mercantiles** (arts. 5º, 6º, 132, 134-135, 154-158, 166, 172-179, 181-191,
  208-228 bis, 229-249, entre otros) y a los estatutos sociales de cada sociedad.
- El número de acciones y los importes se almacenan como `float` para simplificar
  el andamiaje; si se requiere precisión monetaria estricta, migra esas columnas a
  `Numeric`/`Decimal`.
- El proyecto cubre la **estructura base** solicitada en `PGAC.md`: no incluye
  autenticación, multiempresa ni firma electrónica avanzada (fuera de alcance).
- El PDF se genera con ReportLab de forma determinista; los márgenes, la
  tipografía y el pie de página se ajustan desde `backend/.env`.

---

## 11. Siguientes pasos sugeridos

1. Autenticación y roles (capturista, revisor, abogado responsable) + bitácora de cambios.
2. Migraciones con Alembic y fusión de la tabla `actas` con catálogos de sociedades.
3. Plantillas en Word/PDF adjuntas y anexos (poderes, convocatorias, balances).
4. Firma electrónica y control de versiones firmadas (hash + sellado de tiempo).
5. Exportación a expediente ZIP y API de integración para notarías.



=======
# G19X-ITCH-ABC-955-ACADEMIC
Proyecto académico TODO Academy
>>>>>>> b202f4864c07a6e18fddf183387bb2bc7ee92533
