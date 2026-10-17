# ===========================================================================
#  PGAC - Makefile para tareas de desarrollo y entrega
#
#  Requisitos: make (GNU Make), python 3.10+, node 20+
# ===========================================================================
.PHONY: help install install-backend install-frontend backend frontend test lint clean \
        docker-up docker-down docker-logs format

PYTHON ?= python
PIP ?= pip
NPM ?= npm

BACKEND_DIR := backend
FRONTEND_DIR := frontend

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
#  Instalación de dependencias
# ---------------------------------------------------------------------------
install: install-backend install-frontend ## Instala todas las dependencias

install-backend: ## Instala dependencias del backend (Python)
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt -r requirements-dev.txt

install-frontend: ## Instala dependencias del frontend (Node.js)
	cd $(FRONTEND_DIR) && $(NPM) ci

# ---------------------------------------------------------------------------
#  Ejecución en desarrollo
# ---------------------------------------------------------------------------
backend: ## Inicia el backend (FastAPI + uvicorn)
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

frontend: ## Inicia el frontend (Vite dev server)
	cd $(FRONTEND_DIR) && $(NPM) run dev

# ---------------------------------------------------------------------------
#  Pruebas y calidad
# ---------------------------------------------------------------------------
test: ## Ejecuta las pruebas del backend
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest

test-backend: test ## Alias para test

lint: ## Ejecuta linters (backend + frontend)
	cd $(BACKEND_DIR) && $(PYTHON) -m flake8 app/ || true
	cd $(FRONTEND_DIR) && $(NPM) run lint 2>/dev/null || true

# ---------------------------------------------------------------------------
#  Docker
# ---------------------------------------------------------------------------
docker-up: ## Levanta todos los servicios con Docker Compose
	docker compose up -d

docker-down: ## Detiene y elimina los contenedores
	docker compose down

docker-logs: ## Muestra los logs de los contenedores
	docker compose logs -f

docker-build: ## Construye las imágenes de Docker
	docker compose build

# ---------------------------------------------------------------------------
#  Utilidades
# ---------------------------------------------------------------------------
clean: ## Limpia archivos generados (__pycache__, .pytest_cache, dist, etc.)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/dist $(BACKEND_DIR)/pgac.db 2>/dev/null || true

format: ## Formatea el código (black + prettier)
	cd $(BACKEND_DIR) && $(PYTHON) -m black app/ 2>/dev/null || true
	cd $(FRONTEND_DIR) && $(NPM) run format 2>/dev/null || true