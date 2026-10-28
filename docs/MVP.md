# MVP — PGAC (Página de Gestión de Actas Corporativas)

**Producto Mínimo Viable** — Versión inicial funcional para redacción y exportación de actas corporativas.

---

## 1. Objetivo del MVP

Permitir a un usuario capturar los datos de una asamblea societaria (datos generales, asistentes, orden del día y acuerdos), generar el texto legal de las cláusulas (mediante IA o plantillas deterministas parametrizadas como respaldo), validar la consistencia del acta y exportarla a PDF — con autenticación y roles (JWT + RBAC) y una interfaz de acceso separada de actas.

---

## 2. Alcance del MVP (qué SÍ entra)

### Backend (Python + FastAPI)
| Módulo | Qué incluye |
|--------|-------------|
| Modelos | `Acta` con ID, tipo de asamblea, fecha, sociedad, asistentes, orden del día, acuerdos, estatus, versión |
| Plantillas legales parametrizadas | `PlantillaLegal` + `ParametroPlantilla` con validación de parámetros requeridos, valores por defecto, `obtener_parametros_plantilla()`, `parametros_requeridos_por_materia()`, `DatosPlantillaIncompletosError` — 15 materias cubiertas con fundamentos LGSM |
| IA + degradación | `ai_service.py` con integración a Azure OpenAI / Gemini / OpenAI-compatible; si falla, degrada a plantillas deterministas |
| ReportLab | `build_acta_pdf(data) -> bytes` con encabezados, márgenes, firmas, numeración de páginas |
| Orquestación | `acta_service.py`: folios, CRUD de actas, composición de cláusulas |
| Administración | `administracion.py`: resumen del repositorio, clasificación por vigencia, historial de versiones con restauración, gestión de caducidad |
| Asistente IA | `asistente.py`: chat conversacional para creación guiada, validación, consulta de estatus y versiones (`/api/v1/asistente/chat`, `/api/v1/asistente/ayuda`) |
| Auth y RBAC | `auth_service.py`, `security.py`, `deps.py`: registro (1er usuario = Administrador, el resto = capturista), JWT HS256, perfil, recuperación de contraseña, `requiere_rol` y dependencias por rol |
| Bitácora | `BitacoraCambios` + `GET /api/v1/bitacora` (revisor+): quién modificó qué, cuándo, con antes/después |
| Expediente | `GET /api/v1/expediente/{id}/zip`: PDF + `metadatos.json` (capturista+) |
| Notaría | `GET /api/v1/notaria/actas*` (revisor+): metadatos para integración notarial |
| Endpoints | `GET /health`, catálogos, `redactar`, `redactar-stream`, `generar-pdf`, CRUD de actas, `estatus`, `pdf`, `validar`, `bitacora`, `expediente/zip`, `notaria/actas*`, `administracion/*`, `asistente/chat*`, `auth/*` |

### Frontend (React 18 + Vite + Tailwind)
| Componente | Qué incluye |
|------------|-------------|
| Interfaz de acceso (separada) | `Acceso.jsx`: `Login`, `Registro` y `RecuperarPassword` con marca institucional — **sin barra lateral ni funciones de actas**. Tras un acceso correcto se abre `Perfil`. |
| Perfil con funciones por rol | `Perfil.jsx`: muestra el rol del usuario y las secciones habilitadas (`seccionesConAcceso`); se protege la navegación por rol en `App.jsx`, `BarraLateral` y `Encabezado`. |
| Wizard de 4 pasos | 1. Datos generales → 2. Asistentes y quórum → 3. Orden del día y acuerdos → 4. Revisión y PDF |
| Generación | Botón «Generar borrador con IA» y «Descargar PDF final» |
| Biblioteca de actas | Listar actas con filtros, descarga de PDF, edición, cambio de estatus, revalidación y eliminación (revisor+ para listar/delete) |
| Administración de actas | Resumen del repositorio, clasificación por vigencia, historial de versiones con restauración, gestión de caducidad (revisor+ consulta; capturista+ mutaciones) |
| Asistente IA | Chat conversacional para creación guiada de actas, validación, consulta de estatus y descarga de PDF (usuario autenticado) |
| Autenticación | Login, registro automático al crear cuenta, perfil, cambiar contraseña, recuperación (token muestra por `DEBUG`) |
| Catálogos | Tipos de asamblea, mayorías, caracteres de asistente, estatus |

### Pruebas
- 85 pruebas automatizadas pasando (55 de la versión anterior + 12 de seguridad,
  autenticación y RBAC en `tests/test_auth.py`)
- Build del frontend exitoso (Vite)

---

## 3. Qué NO entra en el MVP (posterior)

| Área | Qué queda fuera | Motivo |
|------|----------------|--------|
| **Autenticación y roles** | ✅ Entregado (JWT + RBAC + interfaz de acceso separada + perfil por rol) | Requisito RF-11 de la versión entregada |
| **Firma electrónica** | Firma electrónica avanzada, hash + sellado de tiempo | Requiere infraestructura adicional y validez legal específica |
| **Multiempresa** | Aislamiento de datos por sociedad/cliente | El MVP asume una sola instancia; el backend no expone organización/empresa al usuario |
| **Migraciones Alembic** | AUTO_CREATE_TABLES=false + migraciones gestionadas | El MVP crea tablas automáticamente en SQLite |
| **Plantillas Word/PDF adjuntas** | Poderes, convocatorias, balances como anexos | Solo se genera el acta base |
| **Servicio de correo** | Envío del token de recuperación por email | El token se muestra en la respuesta solo en modo DEBUG |
| **Multiempresa** | Aislamiento de datos por sociedad/cliente | El MVP asume una sola instancia |
| **Migraciones Alembic** | `AUTO_CREATE_TABLES=false` + migraciones gestionadas | El MVP crea tablas automáticamente en SQLite |
| **Plantillas Word/PDF adjuntas** | Poderes, convocatorias, balances como anexos | Solo se genera el acta base |
| **Exportación ZIP** | Expediente comprimido con anexos | Solo PDF individual |
| **API de integración para notarías** | Webhooks, endpoints de terceros | Fuera de alcance inicial |

---

## 4. Criterios de aceptación del MVP

- [ ] Se instala y arranca la aplicación: backend con PostgreSQL o SQLite, frontend en Vite.
- [ ] El **primer usuario** se registra (o lo crea el administrador) y accede por login; **sin sesión iniciada solo se muestra la interfaz de acceso**: ninguna sección del sistema de actas visible.
- [ ] Tras un acceso correcto se abre **Mi perfil** con las funciones permitidas por el rol: capturista (generar actas, asistente, empresa), revisor+ (biblioteca, administración, bitácora, API notarial), abogado responsable+ (estatus, validación, aprobación) y Administrador (total, gestión de usuarios).
- [ ] El acta se valida en consistencia (quórum, mayorías, fundamentos legales)
- [ ] Las actas se pueden listar, editar, cambiar de estatus y eliminar
- [ ] Se puede consultar el resumen del repositorio, la vigencia de actas, el historial de versiones y la caducidad (administración)
- [ ] El asistente IA guía la creación de actas mediante conversación
- [ ] La información de la empresa/sociedad se captura y se usa automáticamente al generar actas
- [ ] Las 55 pruebas de la versión anterior **y** las 12 pruebas de autenticación/RBAC pasan (85 en total); el frontend builda sin errores.
- [ ] Build del frontend exitoso

---

## 5. Limitaciones conocidas del MVP

- ✅ Autenticación y roles (JWT + RBAC + interfaz de acceso separada + perfil
  por rol) y bitácora de cambios: **entregados en esta versión**.
- SQLite por defecto: apto para desarrollo y demostración; para producción se
  recomienda PostgreSQL con migraciones (Alembic).
- El número de acciones e importes se almacenan como `float`; para precisión
  monetaria estricta migrar a `Numeric`/`Decimal`.
- La recuperación de contraseña no envía mail: en `DEBUG` el token viaja en la
  respuesta (se debe eliminar antes de la producción).
- El asistente conversacional opera con el usuario autenticado, pero no
  restringe intenciones por rol dentro del chat.
- El front-end guarda la sesión (JWT + usuario) en `localStorage`: si se
  evalúa un entorno multi-usuario, migrar a cookies `HttpOnly` + `Secure`.

---

> Generado con asistencia de IA (declarado en el README del proyecto).