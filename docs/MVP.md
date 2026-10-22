# MVP — PGAC (Página de Gestión de Actas Corporativas)

**Producto Mínimo Viable** — Versión inicial funcional para redacción y exportación de actas corporativas.

---

## 1. Objetivo del MVP

Permitir a un usuario capturar los datos de una asamblea societaria (datos generales, asistentes, orden del día y acuerdos), generar el texto legal de las cláusulas (mediante IA o plantillas deterministas parametrizadas como respaldo), validar la consistencia del acta y exportarla a PDF — todo sin necesidad de autenticación ni infraestructura externa.

---

## 2. Alcance del MVP (qué SÍ entra)

### Backend (Python + FastAPI)
| Módulo | Qué incluye |
|--------|-------------|
| Modelos | `Acta` con ID, tipo de asamblea, fecha, sociedad, asistentes, orden del día, acuerdos, estatus, versión |
| Plantillas legales parametrizadas | `PlantillaLegal` + `ParametroPlantilla` con validación de parámetros requeridos, valores por defecto, `obtener_parametros_plantilla()`, `parametros_requeridos_por_materia()`, `DatosPlantillaIncompletosError` — 15 materias cubiertas con fundamentos LGSM |
| IA + degradación | `ai_service.py` con integración a Azure OpenAI / Gemini / OpenAI-compatible; si falla, degrada automáticamente a plantillas deterministas |
| ReportLab | `build_acta_pdf(data) -> bytes` con encabezados, márgenes, firmas, numeración de páginas |
| Orquestación | `acta_service.py`: folios, CRUD de actas, composición de cláusulas |
| Administración | `administracion.py`: resumen del repositorio, clasificación por vigencia, historial de versiones con restauración, gestión de caducidad |
| Asistente IA | `asistente.py`: chat conversacional para creación guiada, validación, consulta de estatus y versiones (`/api/v1/asistente/chat`, `/api/v1/asistente/ayuda`) |
| Endpoints | `GET /health`, `GET /api/v1/sistema/estado`, `GET /api/v1/actas/catalogos`, `POST /api/v1/actas/redactar`, `POST /api/v1/actas/generar-pdf`, `GET/PUT/DELETE /api/v1/actas/{id}`, `GET /api/v1/actas`, `PATCH /api/v1/actas/{id}/estatus`, `GET /api/v1/actas/{id}/pdf`, `POST /api/v1/actas/{id}/validar`, `GET/POST /api/v1/administracion/resumen|vigencia|versiones/{id}|versiones/{id}/{n}|versiones/{id}/{n}/restaurar|caducidad/{id}`, `POST /api/v1/asistente/chat`, `GET /api/v1/asistente/ayuda` |
| Base de datos | SQLite por defecto (sin instalación adicional); PostgreSQL opcional para producción |

### Frontend (React 18 + Vite + Tailwind)
| Componente | Qué incluye |
|------------|-------------|
| Wizard de 4 pasos | 1. Datos generales → 2. Asistentes y quórum → 3. Orden del día y acuerdos → 4. Revisión y PDF |
| Generación | Botón "Generar borrador con IA" y "Descargar PDF final" |
| Biblioteca de actas | Listar actas con filtros, descarga de PDF, edición, cambio de estatus, revalidación y eliminación |
| Administración de actas | Resumen del repositorio, clasificación por vigencia, historial de versiones con restauración, gestión de caducidad |
| Asistente IA | Chat conversacional para creación guiada de actas, validación, consulta de estatus y descarga de PDF |
| Información de la empresa | Captura de razón social, R.F.C., tipo de sociedad (7 opciones), logo y firma electrónica; toggle para usar automáticamente en cada acta |
| Catálogos | Tipos de asamblea, mayorías, caracteres de asistente, estatus |

### Pruebas
- 55 pruebas automatizadas pasando (backend)
- Build del frontend exitoso (Vite)

---

## 3. Qué NO entra en el MVP (posterior)

| Área | Qué queda fuera | Motivo |
|------|----------------|--------|
| **Autenticación y roles** | Login, capturista/revisor/abogado, bitácora de cambios | Fuera de alcance del MVP; se declara en el PRD como requerimiento post-MVP |
| **Firma electrónica** | Firma electrónica avanzada, hash + sellado de tiempo | Requiere infraestructura adicional y validez legal específica |
| **Multiempresa** | Aislamiento de datos por sociedad/cliente | El MVP asume una sola instancia |
| **Migraciones Alembic** | `AUTO_CREATE_TABLES=false` + migraciones gestionadas | El MVP crea tablas automáticamente en SQLite |
| **Plantillas Word/PDF adjuntas** | Poderes, convocatorias, balances como anexos | Solo se genera el acta base |
| **Exportación ZIP** | Expediente comprimido con anexos | Solo PDF individual |
| **API de integración para notarías** | Webhooks, endpoints de terceros | Fuera de alcance inicial |

---

## 4. Criterios de aceptación del MVP

- [ ] Un usuario puede crear un acta completa desde el frontend (4 pasos del wizard)
- [ ] Las cláusulas se generan mediante IA o, sin credenciales, mediante plantillas deterministas parametrizadas
- [ ] El PDF generado contiene encabezado, quórum, orden del día, acuerdos, cierre y firmas
- [ ] El acta se valida en consistencia (quórum, mayorías, fundamentos legales)
- [ ] Las actas se pueden listar, editar, cambiar de estatus y eliminar
- [ ] Se puede consultar el resumen del repositorio, la vigencia de actas, el historial de versiones y la caducidad (administración)
- [ ] El asistente IA guía la creación de actas mediante conversación
- [ ] La información de la empresa/sociedad se captura y se usa automáticamente al generar actas
- [ ] 55 pruebas de backend pasando
- [ ] Build del frontend exitoso

---

## 5. Limitaciones conocidas del MVP

- Sin autenticación: cualquier persona con acceso a la API puede crear, editar o borrar actas (ver PRD §6)
- SQLite por defecto: apto para desarrollo y demostración; para producción se recomienda PostgreSQL con migraciones
- El número de acciones e importes se almacenan como `float`; para precisión monetaria estricta migrar a `Numeric`/`Decimal`
- No incluye revisión legal automatizada: el acta generada requiere validación de un abogado corporativo antes de protocolización

---

> Generado con asistencia de IA (declarado en el README del proyecto).