# PRD — PGAC (Página de Gestión de Actas Corporativas)

**Documento de Requisitos del Producto** — Plataforma LegalTech para automatizar actas corporativas conforme a la Ley General de Sociedades Mercantiles (México).

---

## 1. Visión del producto

PGAC automatiza la redacción, estructuración, validación y exportación a PDF de actas corporativas (asambleas ordinarias, extraordinarias, aumentos de capital, fusiones, disoluciones, etc.). Utiliza Inteligencia Artificial para redactar contenido legal complejo y validar consistencia, con plantillas legales deterministas parametrizadas como respaldo offline, y ReportLab para el renderizado determinista del PDF.

---

## 2. Público objetivo

- Abogados corporativos y asistentes legales que redactan actas de asamblea
- Contadores y administradores de sociedades mercantiles
- Emprendedores que constituyen sociedades y necesitan actas formales

---

## 3. Requisitos funcionales (RF)

### RF-01: Generación de actas
El usuario debe poder capturar datos generales (sociedad, fecha, hora, tipo de asamblea, lugar), asistentes con quórum, orden del día y acuerdos, y generar el acta completa.

### RF-02: Redacción asistida por IA
El sistema debe redactar las cláusulas legales de cada acuerdo usando IA (Azure OpenAI, Gemini o compatible) y devolver el texto en español jurídico formal.

### RF-03: Plantillas legales parametrizadas (respaldo offline)
Cuando no haya proveedor de IA disponible o falle, el sistema debe usar plantillas legales deterministas parametrizadas:
- Cada materia declara sus parámetros `{clave}` (requeridos u opcionales con valor por defecto)
- `redactar_con_plantilla()` valida que los requeridos estén presentes; si faltan, lanza `DatosPlantillaIncompletosError`
- `obtener_parametros_plantilla(materia)` permite al frontend saber qué campos capturar

### RF-04: Validación de consistencia
El sistema debe validar quórum, convocatoria, mayorías, orden del día y fundamentos legales, asignando un puntaje y lista de hallazgos (crítico, advertencia, informativo).

### RF-05: Exportación a PDF
El sistema debe generar un PDF formal con ReportLab: encabezados, márgenes profesionales, firmas, numeración de página y leyenda de confidencialidad.

### RF-06: Gestión de actas (CRUD)
Listar, crear, leer, actualizar, cambiar estatus y eliminar actas. Cada acta tiene folio, versión y historial.

### RF-07: Catálogos
Proveer catálogos de tipos de asamblea, tipos de mayoría, caracteres de asistente y estatus de acta para los formularios del frontend.

### RF-08: Administración de actas (versiones, vigencia y caducidad)
El sistema debe administrar el ciclo de vida documental de cada acta:
- **Resumen del repositorio:** obtener totales de actas agrupadas por estatus y clasificación de vigencia (vencida, por vencer, vigente, sin fecha).
- **Vigencia:** listar actas ordenadas por prioridad de atención, con las vencidas primero, permitiendo filtro por estado de vigencia.
- **Historial de versiones:** cada actualización de un acta genera una nueva versión. El usuario puede listar versiones, ver el contenido completo de cualquier versión y restaurar una versión anterior (emitando una versión nueva sin borrar el historial de auditoría).
- **Caducidad:** fijar, ampliar o eliminar la fecha de caducidad de un acta, registrando el cambio como nueva versión con su motivo.

### RF-09: Asistente IA conversacional
El sistema debe incluir un asistente de IA basado en chat que guíe al usuario en la creación de actas mediante lenguaje natural:
- **Creación guiada:** solicitar los datos faltantes paso a paso para generar un acta, mostrando el progreso de recopilación.
- **Catálogo de tipos de asamblea:** ofrecer tipos de acta para elegir (ordinaria, extraordinaria, aumento de capital, fusión, disolución, etc.).
- **Acciones rápidas:** validar una acta, cambiar su estatus, consultar versiones, descargar el PDF y restaurar versiones.
- **Borrador organizable:** generar un texto estructurado del acta que pueda copiarse al formulario manual.
- **Endpoint de ayuda:** devolver sugerencias de preguntas válidas y capacidades del asistente.

### RF-10: Información de la empresa o sociedad
El sistema debe permitir capturar y persistir los datos de la sociedad que comparece en las actas:
- Razón social, R.F.C., tipo de sociedad (7 opciones), logo de la empresa y firma electrónica opcional.
- Toggle «Usar esta información al generar el acta»: al activarse, la sociedad, tipo de sociedad, logo y firma se incluyen automáticamente en cada acta generada, y la IA puede incorporar estos datos al redactar cláusulas y el encabezado del PDF.
- Persistencia en localStorage del navegador (sin depender de autenticación ni backend).

---

## 4. Requisitos no funcionales (RNF)

| ID | Requisito |
|----|-----------|
| RNF-01 | Backend en Python 3.10+ con FastAPI |
| RNF-02 | Frontend en React 18 + Vite + Tailwind CSS |
| RNF-03 | PDF generado de forma determinista (sin depender del modelo IA) |
| RNF-04 | SQLite por defecto (desarrollo); PostgreSQL opcional (producción) |
| RNF-05 | Separación de responsabilidades: IA = texto legal; ReportLab = maquetado |
| RNF-06 | Código con type hints (Python) y componentes funcionales (React) |

---

## 5. Alcance del MVP vs. Post-MVP

### ✅ Entra en el MVP (ver `docs/MVP.md`)
Todo lo listado en RF-01 a RF-07, sin autenticación ni firma electrónica.

### ❌ Queda fuera del MVP (posterior)
| Área | Qué queda fuera |
|------|-----------------|
| Autenticación y roles | Login, capturista/revisor/abogado responsable, bitácora de cambios |
| Firma electrónica | Firma electrónica avanzada, hash + sellado de tiempo |
| Multiempresa | Aislamiento de datos por sociedad/cliente |
| Migraciones Alembic | `AUTO_CREATE_TABLES=false` + migraciones gestionadas |
| Plantillas Word/PDF adjuntas | Poderes, convocatorias, balances como anexos |
| Exportación ZIP | Expediente comprimido |
| API de integración para notarías | Webhooks, endpoints de terceros |

---

## 6. Seguridad y acceso (declarado en PRD)

**Advertencia:** En el MVP **no hay autenticación ni autorización**. Cualquier persona que tenga acceso a la API puede:
- Listar todas las actas (`GET /api/v1/actas`)
- Leer cualquier acta (`GET /api/v1/actas/{id}`)
- Editar cualquier acta (`PUT /api/v1/actas/{id}`)
- Eliminar cualquier acta (`DELETE /api/v1/actas/{id}`)

Como las actas son documentos societarios confidenciales, esto es un riesgo conocido del MVP. Se debe agregar en una versión posterior:
- Inicio de sesión sencillo con roles (capturista, revisor, abogado responsable)
- Control de acceso basado en roles (RBAC) sobre los endpoints de actas
- Bitácora de cambios (quién modificó qué y cuándo)

---

## 7. Métricas de éxito del MVP

- 55 pruebas de backend pasando
- Build del frontend sin errores
- PDF generado: ≥ 1 página, con encabezado, quórum y firmas
- Validación de consistencia: puntaje visible y hallazgos listados
- Tiempo de respuesta de redacción < 30 segundos (con IA) o < 2 segundos (plantillas)

---

## 8. Hoja de ruta sugerida (post-MVP)

1. Autenticación y roles + bitácora de cambios
2. Migraciones con Alembic y fusión con catálogos de sociedades
3. Firma electrónica y control de versiones firmadas
4. Plantillas en Word/PDF adjuntas y anexos
5. Exportación a expediente ZIP y API de integración para notarías

---

> Generado con asistencia de IA (declarado en el README del proyecto).