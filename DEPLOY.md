# Guía de Despliegue y Entrega — PGAC

PGAC — Página de Gestión de Actas Corporativas (LegalTech)
Versión: 0.1.0

Este documento describe los pasos para desplegar y entregar el proyecto a un
equipo de desarrollo de software.

---

## 1. Requisitos previos

| Componente | Versión mínima | Notas |
|------------|---------------|-------|
| Python | 3.10+ | Backend |
| pip | última | Gestor de paquetes Python |
| Node.js | 20+ | Frontend |
| npm | incluida con Node | Gestor de paquetes frontend |
| Docker Desktop | opcional | Para despliegue con contenedores |
| Git | 2.30+ | Control de versiones |

---

## 2. Estructura del repositorio

```
PGAC/
├── README.md                 Documentación principal del proyecto
├── PGAC.md                   Especificación de origen
├── DEPLOY.md                 Esta guía
├── CONTRIBUTING.md           Guía de contribución
├── LICENSE                   Licencia MIT
├── Makefile                  Tareas comunes de desarrollo
├── .gitignore                Archivos ignorados por Git
├── docker-compose.yml        Orquestación de servicios (PostgreSQL + Backend + Frontend)
├── .vscode/                  Configuración de Visual Studio Code
├── backend/                  API REST (FastAPI)
│   ├── .env.example          Plantilla de variables de entorno
│   ├── .env                  Variables de entorno (local, no se sube a Git)
│   ├── Dockerfile            Imagen del backend
│   ├── requirements.txt      Dependencias núcleo
│   ├── requirements-postgres.txt Driver PostgreSQL (producción)
│   ├── requirements-dev.txt  Dependencias de desarrollo y pruebas
│   ├── pytest.ini            Configuración de pytest
│   ├── app/                  Código fuente del backend
│   ├── scripts/              Scripts de diagnóstico y verificación
│   ├── tests/                Pruebas automatizadas (29 tests)
│   └── ejemplos/             PDF de muestra generados
└── frontend/                 SPA (React 18 + Vite + Tailwind)
    ├── .env.development      Variables de entorno (desarrollo)
    ├── .env.production       Variables de entorno (producción)
    ├── Dockerfile            Imagen del frontend (build + nginx)
    ├── nginx.conf            Configuración de nginx para producción
    ├── package.json          Dependencias y scripts
    ├── vite.config.js        Configuración de Vite (proxy a backend)
    ├── tailwind.config.js    Tema Tailwind CSS
    └── src/                  Código fuente del frontend
```

---

## 3. Despliegue en desarrollo (sin Docker)

### 3.1 Backend

```powershell
# 1. Entrar a la carpeta del backend
cd backend

# 2. Copiar plantilla de entorno (si no existe .env)
copy .env.example .env

# 3. Instalar dependencias
pip install -r requirements.txt -r requirements-dev.txt

# 4. Iniciar el servidor
python -m uvicorn app.main:app --reload --port 8000
```

El backend quedará disponible en `http://127.0.0.1:8000`.
Documentación interactiva: `http://127.0.0.1:8000/docs`.

### 3.2 Frontend

```powershell
# 1. Entrar a la carpeta del frontend
cd frontend

# 2. Instalar dependencias
npm ci

# 3. Iniciar servidor de desarrollo
npm run dev
```

El frontend quedará disponible en `http://localhost:5173`.
El proxy de Vite reenvía las peticiones a `/api` hacia el backend en el puerto 8000.

### 3.3 Verificación rápida

| Endpoint | URL | Descripción |
|----------|-----|-------------|
| Health | `http://127.0.0.1:8000/health` | Estado de BD y proveedor de IA |
| Catálogos | `http://127.0.0.1:8000/api/v1/actas/catalogos` | Opciones del formulario |
| Swagger | `http://127.0.0.1:8000/docs` | Documentación interactiva de la API |

---

## 4. Despliegue con Docker Compose (recomendado para entrega)

```powershell
# Desde la raíz del proyecto
docker compose up -d
```

Esto levanta tres servicios:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| PostgreSQL | 5432 | Base de datos de producción |
| Backend | 8000 | API FastAPI |
| Frontend | 80 | SPA servida por nginx |

Acceso:
- Aplicación: `http://localhost`
- API docs: `http://localhost:8000/docs`

Para detener:

```powershell
docker compose down
```

### Variables de entorno en Docker

El backend lee `backend/.env`. En `docker-compose.yml` se sobrescribe
`DATABASE_URL` para apuntar al contenedor de PostgreSQL:

```
DATABASE_URL=postgresql+psycopg://pgac:pgac@postgres:5432/pgac
```

Para usar SQLite en lugar de PostgreSQL, edita `backend/.env` y cambia
`DATABASE_URL` a `sqlite:///./pgac.db`.

---

## 5. Ejecución de pruebas

```powershell
# Desde la raíz del proyecto
make test

# O directamente con pytest
cd backend
pytest
```

Resultado esperado: 55 pruebas aprobadas.

---

## 6. Construcción para producción

### Backend (imagen Docker)

```powershell
docker build -t pgac-backend -f backend/Dockerfile .
```

### Frontend (imagen Docker con nginx)

```powershell
docker build -t pgac-frontend -f frontend/Dockerfile .
```

---

## 7. Configuración de variables de entorno sensibles

El archivo `backend/.env.example` contiene todas las variables con valores
por defecto. Para despliegue real:

1. Copia `.env.example` a `.env`:
   ```powershell
   copy backend/.env.example backend/.env
   ```
2. Edita `backend/.env` y configura:
   - `DATABASE_URL`: cadena de conexión a PostgreSQL (producción) o SQLite (desarrollo).
   - `CORS_ORIGINS`: orígenes permitidos (ajustar al dominio de producción).
   - `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`: si usas Azure OpenAI.
   - `GEMINI_API_KEY`: si usas Google Gemini.
   - `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`: si usas un endpoint compatible con OpenAI (Ollama, LM Studio, etc.).
   - `DEBUG=false` en producción.
   - `ENVIRONMENT=production` en producción.

> **Importante:** Nunca subas `.env` con credenciales reales a un repositorio público. El archivo `.env` está en `.gitignore`.

### Build estático del frontend (sin Docker)

```powershell
cd frontend
npm ci

---

## 8. Solución de problemas de conexión

### 8.1 Backend no responde

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `Connection refused` en puerto 8000 | Backend no iniciado | Ejecutar `python -m uvicorn app.main:app --reload` |
| Error de driver PostgreSQL | Falta `psycopg` | `pip install -r requirements-postgres.txt` |
| Base de datos no disponible | PostgreSQL aún arrancando | El backend reintenta automáticamente (3 intentos, 2s de espera) |
| CORS bloqueado | Origen del frontend no en `CORS_ORIGINS` | Agregar la URL del frontend a `CORS_ORIGINS` en `.env` |

### 8.2 Frontend no puede llamar al backend

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| Error de red en el navegador | Backend no disponible | Verificar que el backend esté corriendo en el puerto 8000 |
| CORS error | Configuración de CORS | Verificar `CORS_ORIGINS` en `backend/.env` |
| Proxy de Vite no funciona | `VITE_API_PROXY` mal configurado | Revisar `frontend/.env.development` y `vite.config.js` |

### 8.3 Proveedor de IA no disponible

El sistema degrada automáticamente a plantillas legales deterministas cuando
no hay credenciales de IA configuradas. Esto no es un error; el acta se genera
correctamente sin IA externa.

Para verificar el proveedor activo:

```powershell
curl http://127.0.0.1:8000/health
```

---

## 9. Entrega al equipo de desarrollo

Al entregar este proyecto a una desarrolladora de software, incluye:

1. **Código completo** (este repositorio).
2. **`README.md`** — descripción general, arquitectura, cómo correrlo.
3. **`DEPLOY.md`** — esta guía de despliegue.
4. **`CONTRIBUTING.md`** — estándares de código y proceso de contribución.
5. **`LICENSE`** — términos de uso (MIT).
6. **`Makefile`** — tareas automatizadas para facilitar el onboarding.
7. **`.vscode/`** — configuración de editor para consistencia en el equipo.
8. **`docker-compose.yml` + Dockerfiles** — despliegue contenedorizado listo para producción.
9. **`backend/.env.example`** — plantilla de variables de entorno (sin secretos).
10. **Pruebas automatizadas** (29 tests en `backend/tests/`) para validar entregas futuras.

### Contacto y soporte

Para dudas sobre la entrega, consultar la documentación en `README.md` y
`PGAC.md` (especificación de origen).
npm run build
```

El resultado se genera en `frontend/dist/` y puede servirse con cualquier
servidor web estático (nginx, Apache, IIS, Azure Static Web Apps, etc.).