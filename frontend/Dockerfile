# ===========================================================================
#  PGAC - Dockerfile del Frontend (React + Vite)
#
#  Construcción:
#    docker build -t pgac-frontend -f frontend/Dockerfile .
#
#  Ejecución (servidor estático con nginx):
#    docker run -p 80:80 pgac-frontend
# ===========================================================================
# ---- Etapa de construcción -------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# ---- Etapa de runtime (servidor estático nginx) ---------------------------
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración de nginx para SPA (redirige todas las rutas a index.html)
RUN rm /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]