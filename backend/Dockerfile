# ===========================================================================
#  PGAC - Dockerfile del Backend (FastAPI)
#
#  Construcción:
#    docker build -t pgac-backend -f backend/Dockerfile .
#
#  Ejecución:
#    docker run -p 8000:8000 --env-file backend/.env pgac-backend
# ===========================================================================
FROM python:3.11-slim

WORKDIR /app

# Variables de entorno de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema (necesarias para psycopg y reportlab)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY backend/requirements.txt ./requirements.txt
COPY backend/requirements-postgres.txt ./requirements-postgres.txt
RUN pip install --no-cache-dir -r requirements.txt -r requirements-postgres.txt

# Copiar código de la aplicación
COPY backend/app ./app
COPY backend/.env ./.env
COPY backend/pytest.ini ./pytest.ini

# Puerto expuesto
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]