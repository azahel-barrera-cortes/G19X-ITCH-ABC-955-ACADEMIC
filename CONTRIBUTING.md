# Contribución a PGAC

Gracias por considerar contribuir a PGAC (Página de Gestión de Actas Corporativas).
Este documento describe el proceso para colaborar en el proyecto.

## 1. Entender el proyecto

PGAC es una plataforma LegalTech que automatiza la redacción, validación y exportación
a PDF de actas corporativas conforme a la Ley General de Sociedades Mercantiles (México).

- **Backend:** Python 3.10+, FastAPI, SQLAlchemy, ReportLab, httpx.
- **Frontend:** React 18, Vite, Tailwind CSS, Axios.
- **Base de datos:** SQLite (desarrollo) / PostgreSQL 16 (producción).

## 2. Configuración del entorno de desarrollo

### Backend

```powershell
cd backend
copy .env.example .env
pip install -r requirements.txt -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

### Con Docker (todo incluido)

```powershell
docker compose up -d
```

## 3. Estructura de ramas

- `main`: rama estable, versión lista para producción.
- `feature/*`: nuevas funcionalidades.
- `fix/*`: correcciones de errores.
- `docs/*`: actualización de documentación.

## 4. Flujo de trabajo (Pull Requests)

1. Crea una rama desde `main`: `git checkout -b feature/mi-feature`
2. Realiza los cambios y commit con mensajes descriptivos.
3. Ejecuta las pruebas: `make test`
4. Abre un Pull Request hacia `main`.
5. Un revisor aprobador debe fusionar la rama.

## 5. Estándares de código

- **Python:** PEP 8, type hints, docstrings en español.
- **JavaScript/React:** Prettier, componentes funcionales con hooks.
- **Commits:** formato convencional (`feat:`, `fix:`, `docs:`, `refactor:`).

## 6. Pruebas

```powershell
# Backend
cd backend
pytest

# Frontend (si se añaden pruebas)
cd frontend
npm test
```

## 7. Reportar errores

Abre un issue describiendo:
- Pasos para reproducir el error.
- Comportamiento esperado vs. observado.
- Entorno (sistema operativo, versión de Python/Node, Docker o no).
- Capturas de pantalla si aplica.

## 8. Licencia

Este proyecto está bajo la Licencia MIT. Consulta `LICENSE` para más detalles.