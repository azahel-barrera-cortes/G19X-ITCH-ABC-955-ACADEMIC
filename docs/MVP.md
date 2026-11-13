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
| Modelos | `Acta` con ID, tipo de asamblea, fecha, sociedad, asistentes, orden del día, acuerdos, estatus, versión y `empresa_codigo` (indexado); `Usuario` (email, nombre, rol, password_hash, activo, `codigo_empresa`, `empresa_codigo`, hash de `reset_token`, vencimiento y `token_version`) y `BitacoraCambios` (usuario_id, accion, entidad, `empresa_codigo`, datos_antes/despues, ip_origen, user_agent) |
| Catálogos jurídicos | 26 tipos de acta y 13 tipos societarios, con requisitos específicos por materia y fundamentos normativos |
| Plantillas legales parametrizadas | `PlantillaLegal` + `ParametroPlantilla` con validación de parámetros requeridos, valores por defecto, `obtener_parametros_plantilla()`, `parametros_requeridos_por_materia()` y `DatosPlantillaIncompletosError` |
| IA + degradación | `ai_service.py` con integración a Azure OpenAI / Gemini / OpenAI-compatible (Ollama, Groq, DeepSeek, LM Studio, vLLM); si falla, degrada a plantillas deterministas |
| ReportLab | `build_acta_pdf(data) -> bytes` con encabezados, márgenes, firmas, numeración de páginas |
| Orquestación | `acta_service.py`: folios, CRUD de actas, composición de cláusulas |
| Administración | `administracion.py`: resumen del repositorio, clasificación por vigencia, historial de versiones con restauración, gestión de caducidad y endpoint `PATCH /actas/{acta_id}/empresa` para reasignar actas en cuarentena (SuperAdministrador) |
| Aislamiento por tenant | `tenant_access.py`: `AlcanceEmpresa`, `alcance_empresa()`, `filtrar_por_empresa()` y `obtener_acta_autorizada()` para filtrado fail-closed por `empresa_codigo` en todos los endpoints de actas, administración, notaría y expediente |
| Asistente IA | `asistente.py`: chat conversacional para creación guiada, validación, consulta de estatus y versiones (`/api/v1/asistente/chat`, `/api/v1/asistente/ayuda`) |
| Auth y RBAC | `auth_service.py`, `security.py`, `deps.py`: semilla inicial de SuperAdministrador vía `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD`, registro público vinculado a empresa para capturista/revisor/abogado responsable, JWT HS256, perfil, recuperación de contraseña, `requiere_rol` y dependencias por rol; generación y persistencia de `codigo_empresa` para cada `Administrador`, administración de usuarios reservada al `SuperAdministrador` y bloqueo de cuentas inactivas |
| Bitácora | `BitacoraCambios` + `GET /api/v1/bitacora` (revisor+): quién modificó qué, cuándo, con antes/después |
| Expediente | `GET /api/v1/expediente/{id}/zip`: PDF + `metadatos.json` (capturista+) |
| Notaría | `GET /api/v1/notaria/actas*` (revisor+): metadatos para integración notarial |
| Endpoints | `GET /health`, catálogos, `redactar`, `redactar-stream`, `generar-pdf`, CRUD de actas, `estatus`, `pdf`, `validar`, `bitacora`, `expediente/zip`, `notaria/actas*`, `administracion/*`, `asistente/chat*`, `auth/*`; el PDF devuelve encabezados de trazabilidad `X-Acta-Folio`, `X-Acta-Id`, `X-Acta-Version`, `X-Acta-Paginas`, `X-Acta-Guardada`, `X-IA-Proveedor`, `X-IA-Advertencias`, `X-Validacion-Puntaje` |
| Variables de entorno | `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `AI_PROVIDER`, `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`, `AZURE_OPENAI_*`, `GEMINI_API_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `SMTP_SSL`, `SMTP_TIMEOUT_SECONDS`, `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`, `MARGEN_CM`, `PIE_CONFIDENCIALIDAD`, `CORS_ORIGINS`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `SEED_ADMIN_NOMBRE` |

### Frontend (React 18 + Vite + Tailwind)
| Componente | Qué incluye |
|------------|-------------|
| Interfaz de acceso (separada) | `Acceso.jsx`: `Login`, `Registro` y `RecuperarPassword` con marca institucional — **sin barra lateral ni funciones de actas**. El registro vincula la cuenta a una empresa mediante código; tras el acceso se abre `Perfil` o el panel global del SuperAdministrador. |
| Perfil y permisos por rol | `Perfil.jsx`: muestra nombre, correo y rol; permite cambiar contraseña, presenta el código empresarial al `Administrador`, limita la edición del nombre al `SuperAdministrador` y muestra la información de empresa en modo lectura para capturista, revisor y abogado responsable. |
| Wizard de 4 pasos | 1. Datos generales → 2. Asistentes y quórum → 3. Orden del día y acuerdos → 4. Revisión y PDF |
| Generación | Botón «Generar borrador con IA» y «Descargar PDF final» |
| Biblioteca de actas | Listar actas con filtros, descarga de PDF, edición, cambio de estatus, revalidación y eliminación (revisor+ para listar/delete) |
| Administración de actas | Resumen del repositorio, clasificación por vigencia, historial de versiones con restauración, gestión de caducidad (revisor+ consulta; capturista+ mutaciones) |
| Asistente IA | Chat conversacional para creación guiada de actas, validación, consulta de estatus y descarga de PDF (usuario autenticado) |
| Autenticación | Login, registro, perfil, cambio y recuperación de contraseña por SMTP, control de cuentas inactivas y administración global de usuarios. La recuperación es igual para todos los roles, incluidos SuperAdministrador; token hash de un solo uso, expiración de 60 minutos, respuestas que no enumeran cuentas y revocación de sesiones previas |
| Administración global | `UsuariosSuperAdmin.jsx`, `VitacoraSuperAdmin.jsx` y `UsuarioInactivo.jsx`: gestión de usuarios, bitácora para SuperAdministrador y pantalla de bloqueo para cuentas inactivas |
| Catálogos | Tipos de asamblea, mayorías, caracteres de asistente, estatus |
| Navegación y administración | Menú filtrado por rol, rutas con hash persistidas, panel de generación con plantillas frecuentes, panel de Administrador (perfil, empresa, usuarios y seguridad) y panel global del SuperAdministrador (usuarios, bitácora, estadísticas, seguridad y guía) |

### Pruebas
- Suite de pruebas automatizadas, con desglose por archivo:
  - `test_administracion.py`: 11
  - `test_ai_service.py`: 23
  - `test_api_actas.py`: 9
  - `test_asistente.py`: 6
  - `test_auth.py`: 11
  - `test_flujo_creacion.py`: 3
  - `test_pdf_generator.py`: 5
  - `test_plantillas_legales.py`: 17
- `test_tenant_isolation.py`: 3
  - Total histórico documentado: 88
- Build del frontend exitoso (Vite)

---

## 3. Qué NO entra en el MVP (posterior)

| Área | Qué queda fuera | Motivo |
|------|----------------|--------|
| **Autenticación y roles** | ✅ Entregado (JWT + RBAC + interfaz de acceso separada + perfil por rol + SuperAdministrador inicial por variables de entorno) | Requisito RF-11 de la versión entregada |
| **Firma electrónica** | Firma electrónica avanzada, hash + sellado de tiempo | Requiere infraestructura adicional y validez legal específica |
| **Aislamiento multiempresa completo** | Separación estricta de datos por sociedad/cliente | ✅ Entregado en esta versión: `empresa_codigo` en modelos, filtrado fail-closed en endpoints y `tenant_access.py`. El `SuperAdministrador` puede reasignar actas en cuarentena mediante `PATCH /administracion/actas/{acta_id}/empresa`. |
| **Migraciones Alembic** | AUTO_CREATE_TABLES=false + migraciones gestionadas | El MVP crea tablas automáticamente en SQLite |
| **Plantillas Word/PDF adjuntas** | Poderes, convocatorias, balances como anexos | Solo se genera el acta base |
| **Rate limiting** | Límites de intentos para login y recuperación | Requiere definir almacenamiento compartido y política por cuenta/IP |

---

## 4. Criterios de aceptación del MVP

- [ ] Se instala y arranca la aplicación: backend con PostgreSQL o SQLite, frontend en Vite.
- [ ] El SuperAdministrador inicial accede por login con las credenciales de `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD`; **sin sesión iniciada solo se muestra la interfaz de acceso**: ninguna sección del sistema de actas visible.
- [ ] La recuperación envía por SMTP un token de un solo uso y vigencia de 60 minutos; no revela si la cuenta existe y, al cambiar la contraseña, invalida sesiones previas. Esto aplica también al SuperAdministrador.
- [ ] Tras un acceso correcto se abre **Mi perfil** para usuarios operativos con las funciones permitidas por el rol: capturista (generar actas, asistente y empresa en modo lectura), revisor+ (biblioteca, administración, bitácora y API notarial), abogado responsable+ (estatus y validación) y Administrador (gestión de información de empresa). El SuperAdministrador entra directamente al panel global de superadministración del sistema.
- [ ] El acta se valida en consistencia (quórum, mayorías, fundamentos legales)
- [ ] Las actas se pueden listar, editar, cambiar de estatus y eliminar
- [ ] Se puede consultar el resumen del repositorio, la vigencia de actas, el historial de versiones y la caducidad (administración)
- [ ] El asistente IA guía la creación de actas mediante conversación
- [ ] La información de la empresa/sociedad se captura y se usa automáticamente al generar actas
- [ ] La suite de backend pasa; el frontend builda sin errores.
- [ ] Build del frontend exitoso

---

## 5. Limitaciones conocidas del MVP

- ✅ Autenticación y roles (JWT + RBAC + interfaz de acceso separada + perfil
  por rol), registro vinculado por código empresarial, navegación filtrada,
  paneles de administración, cuentas inactivas y bitácora de cambios:
  **entregados en esta versión**.
- SQLite por defecto: apto para desarrollo y demostración; para producción se
  recomienda PostgreSQL con migraciones (Alembic).
- El número de acciones e importes se almacenan como `float`; para precisión
  monetaria estricta migrar a `Numeric`/`Decimal`.
- El envío de recuperación requiere configurar SMTP y el remitente en
  `backend/.env`; sin esos valores la API responde `503`. La configuración de
  producción debe usar STARTTLS o SSL. Sigue pendiente implementar rate limiting.
- El asistente conversacional exige rol `abogado_responsable` (o superior)
   para cambiar el estatus de un acta y restaurar versiones anteriores.
- El front-end guarda la sesión (JWT + usuario) en `localStorage`: si se
  evalúa un entorno multi-usuario, migrar a cookies `HttpOnly` + `Secure`.

---

> Generado con asistencia de IA (declarado en el README del proyecto).