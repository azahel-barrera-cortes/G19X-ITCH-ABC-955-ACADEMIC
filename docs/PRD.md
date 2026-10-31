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
El sistema debe redactar las cláusulas legales de cada acuerdo usando IA (Azure OpenAI, Gemini o compatible con OpenAI, incluyendo Ollama local, Groq, DeepSeek, LM Studio, vLLM) y devolver el texto en español jurídico formal. El maquetado del PDF nunca lo hace el modelo: ReportLab es determinista y aislado de la IA.

### RF-03: Plantillas legales parametrizadas (respaldo offline)
Cuando no haya proveedor de IA disponible o falle, el sistema debe usar plantillas legales deterministas parametrizadas:
- Cada materia declara sus parámetros `{clave}` (requeridos u opcionales con valor por defecto)
- `redactar_con_plantilla()` valida que los requeridos estén presentes; si faltan, lanza `DatosPlantillaIncompletosError`
- `obtener_parametros_plantilla(materia)` permite al frontend saber qué campos capturar

### RF-04: Validación de consistencia
El sistema debe validar quórum, convocatoria, mayorías, orden del día y fundamentos legales, asignando un puntaje y lista de hallazgos (crítico, advertencia, informativo).

### RF-05: Exportación a PDF
El sistema debe generar un PDF formal con ReportLab: encabezados, márgenes profesionales, firmas, numeración de página y leyenda de confidencialidad. El PDF debe devolver encabezados de trazabilidad (`X-Acta-Folio`, `X-Acta-Id`, `X-Acta-Version`, `X-Acta-Paginas`, `X-Acta-Guardada`, `X-IA-Proveedor`, `X-IA-Advertencias`, `X-Validacion-Puntaje`) y nombrarse `PGAC-AAAA-NNNN_Razón_Social_AAAA-MM-DD.pdf` respetando acentos y espacios en `Content-Disposition`.

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
- Persistencia en el backend: los datos de la sociedad se guardan con cada acta (campos `tipo_sociedad` y `logo_empresa` del modelo `Acta`) y están disponibles para el usuario autenticado; el frontend también conserva una copia en `localStorage` para uso inmediato.

### RF-11: Autenticación y control de acceso por roles (RBAC)
El sistema debe exigir autenticación para toda operación del dominio:
- El primer usuario registrado se crea como `Administrador`; los registros
  públicos posteriores se asignan forzosamente como `capturista` (cualquier
  usuario autenticado puede elevar su propio rol desde `PUT /api/v1/auth/me`;
  solo un Administrador puede elevar el rol de otros usuarios desde
  `PUT /api/v1/auth/users/{id}`).
- Inicio de sesión con email y contraseña (bcrypt); devolución de un JWT
  firmado (HS256) con expiración configurada.
- Roles con privilegios crecientes: `capturista` (1) < `revisor` (2) <
  `abogado_responsable` (3) < `Administrador` (4). Cada operación declara el
  rol mínimo requerido y el backend responde 401 si no hay token y 403 si el
  rol es insuficiente.
- Perfil del usuario autenticado: consulta y actualización de nombre y
  contraseña; gestión de usuarios (listar, cambiar rol, activar/desactivar)
  reservada al Administrador.
- Recuperación de contraseña mediante token temporal de un solo uso (1 hora).

### RF-12: Interfaz de acceso separada y perfil por rol
- Sin sesión iniciada, la aplicación muestra únicamente la interfaz de acceso
  (inicio de sesión, creación de cuenta, recuperación de contraseña): ninguna
  sección del sistema de actas es visible ni accesible.
- Tras un acceso correcto se abre el perfil del usuario, que enumera las
  funciones permitidas por su rol; la navegación (barra lateral y móvil) solo
  presenta esas secciones.
- El frontend adjunta el JWT en cada llamada a la API (interceptor axios y
  cabecera en el flujo SSE de redacción en vivo).
- La separación por rol también protege los datos: un capturista no puede
  listar ni eliminar actas, ni ver la bitácora ni la administración, incluso
  si intenta llamar directamente a los endpoints.

### RF-13: Bitácora de cambios (auditoría)
El sistema debe registrar automáticamente quién realizó cada acción sensible
(crear, actualizar, eliminar, cambiar estatus, validar, restaurar versión,
fijar caducidad, exportar ZIP y consultas de integración) con: usuario,
rol, IP, user-agent y retrato `datos_antes` / `datos_después`. La bitácora se
puede listar y consultar con filtros `accion` y `entidad`, mediante
`GET /api/v1/bitacora` y `GET /api/v1/bitacora/{id}` (revisor+).

### RF-14: Exportación a expediente ZIP
Generar `GET /api/v1/expediente/{acta_id}/zip` con el PDF del acta y un
`metadatos.json` (folio, sociedad, estatus, quién exportó y cuándo), y
registrar la operación en la bitácora. Disponible para capturista+.

### RF-15: API de integración para notarías
Endpoints de solo lectura y metadatos (`/api/v1/notaria/actas` y
`/api/v1/notaria/actas/{id}`) que exponen resúmenes y datos públicos del
 Acta para validación notarial (sin cláusulas completas), requieren rol
 revisor+ y dejan constancia en la bitácora.

### RF-16: Redacción en vivo por streaming (SSE)
El sistema debe ofrecer un endpoint `POST /api/v1/actas/redactar-stream` que transmita la cláusula del primer acuerdo fragmento a fragmento (`inicio` → `fragmento`… → `fin`) mediante `text/event-stream`, permitiendo al frontend mostrar la redacción mientras se genera. Requiere autenticación y rol capturista+.

---

## Modelo de datos

El backend persiste la información en tres tablas principales (portables entre SQLite y PostgreSQL):

### `actas`
| Grupo | Columnas |
|-------|----------|
| Identificación | `id`, `folio` (único), `version` |
| Generales | `sociedad`, `rfc_sociedad`, `tipo_asamblea`, `titulo`, `fecha`, `hora`, `lugar` |
| Convocatoria | `convocatoria_fecha`, `convocatoria_medio`, `convocatoria_quien` |
| Capital | `capital_social`, `acciones_totales`, `capital_presente`, `quorum_porcentaje` |
| Mesa directiva | `presidente`, `secretario` |
| Cuerpo (JSON) | `asistentes`, `orden_del_dia`, `acuerdos`, `clausulas`, `validacion_ia` |
| Documento | `texto_legal`, `observaciones` |
| Trazabilidad | `proveedor_ia`, `estatus`, `created_at`, `updated_at` |

### `usuarios`
| Campo | Descripción |
|-------|-------------|
| `id` (PK) | Autoincremental |
| `email` (único) | Credencial de login |
| `nombre_completo` | Nombre visible |
| `rol` | `capturista`, `revisor`, `abogado_responsable`, `Administrador` |
| `password_hash` | bcrypt, nunca expuesto por la API |
| `activo` | Habilita/deshabilita la cuenta |
| `reset_token`, `reset_token_expires` | Token de recuperación (1 hora) |
| `created_at`, `updated_at` | Auditoría |

### `bitacora_cambios`
| Campo | Descripción |
|-------|-------------|
| `id` (PK) | Autoincremental |
| `usuario_id` (FK) | Quién realizó la acción |
| `accion` | `crear`, `actualizar`, `eliminar`, `cambiar_estatus`, `validar`, `restaurar_version`, `fijar_caducidad`, `exportar_zip`, etc. |
| `entidad`, `entidad_id` | Recurso afectado (p. ej. `actas`, `42`) |
| `datos_antes`, `datos_despues` | Retrato JSON del cambio |
| `ip_origen`, `user_agent` | Contexto de la petición |
| `created_at` | Marca de tiempo |

Los catálogos (`tipo_asamblea`, `estatus`) se almacenan como `VARCHAR + CHECK` para portabilidad.

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

### ✅ Entra en el MVP (ver `docs/MVP.md`) y en la versión entregada
RF-01 a RF-10 (MVP original) más RF-11 a RF-16 de esta versión:
autenticación con roles (JWT + RBAC), interfaz de acceso separada y perfil por
rol, bitácora de cambios, expediente ZIP, API para notarías y redacción en vivo por streaming (SSE).

### ❌ Queda fuera (post-escimiento actual)
| Área | Qué queda fuera |
|------|-----------------|
| Firma electrónica | Firma electrónica avanzada, hash + sellado de tiempo |
| Multiempresa | Aislamiento de datos por sociedad/cliente |
| Migraciones Alembic | `AUTO_CREATE_TABLES=false` + migraciones gestionadas |
| Plantillas Word/PDF adjuntas | Poderes, convocatorias, balances como anexos |
| Servicio de correo | Envío del token de recuperación por email (hoy solo en `DEBUG`) |
| Panel de gestión de usuarios en UI | El alta/cambio de roles se hace por API; el frontend no incluye un panel de usuarios |

---

## 6. Seguridad y acceso

La plataforma implementa autenticación JWT con control de acceso por roles
(RBAC) y bitácora de cambios:

- Todas las operaciones sensibles (actas, administración, asistente, bitácora,
  expediente, notaría) requieren `Authorization: Bearer <JWT>`; sin token
  responden 401 y con rol insuficiente 403.
- El registro es público pero el servidor fuerza el rol `capturista`; el
  primer usuario del sistema arranca como `Administrador`.
- Las contraseñas se guardan con bcrypt y la recuperación se hace con un
  token temporal de un solo uso de 1 hora (en `DEBUG` el token viaja en la
  respuesta para poder probar el flujo de extremo a extremo).
- Las acciones sensibles quedan registradas en la bitácora de cambios
  (usuario, rol, IP, antes/después).

Riesgos conocidos (aceptados hasta la versión post-actual):
- El JWT se almacena en `localStorage` del navegador (exposición ante XSS);
  recomiéndase HTTPS y, a futuro, cookies `HttpOnly`.
- No hay aislamiento multiempresa: un revisor+ puede consultar todas las
  actas del repositorio.
- El asistente conversacional opera con el usuario autenticado, pero no
  restringe intenciones por rol (un usuario autenticado puede pedir por chat
  cambios de estatus que, en el flujo guiado, requieren un rol superior).

---

## 7. Métricas de éxito del MVP

- 85 pruebas de backend pasando
- Build del frontend sin errores
- PDF generado: ≥ 1 página, con encabezado, quórum y firmas
- Validación de consistencia: puntaje visible y hallazgos listados
- Tiempo de respuesta de redacción < 30 segundos (con IA) o < 2 segundos (plantillas)

---

## 8. Hoja de ruta sugerida (post-MVP)

1. Servicio de correo para la recuperación de contraseña
2. Migraciones con Alembic y fusión de la tabla `actas` con catálogos de sociedades
3. Plantillas en Word/PDF adjuntas y anexos (poderes, convocatorias, balances)
4. Firma electrónica y control de versiones firmadas (hash + sellado de tiempo)
5. Multiusuario/logotipos por sociedad y gestión de usuarios en el frontend

---

> Generado con asistencia de IA (declarado en el README del proyecto).