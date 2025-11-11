# ETAPA 1: Build
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r requirements.txt

# ETAPA 2: Runtime
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    DOCKER_CONTAINER=true \
    PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /root/.local /root/.local

WORKDIR /app

COPY requirements.txt .
COPY . .

RUN mkdir -p \
    /app/arc_manager/staticfiles \
    /app/arc_manager/media \
    /app/arc_manager/logs \
    /app/temp_uploads && \
    chmod -R 755 /app

WORKDIR /app/arc_manager

# Script de inicio optimizado
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== ArqGest Startup ==="\n\
echo "Port: ${PORT:-8000}"\n\
\n\
# Esperar DB (máximo 1 minuto)\n\
echo "Waiting for database..."\n\
attempt=0\n\
while [ $attempt -lt 30 ]; do\n\
  if python manage.py check --database default >/dev/null 2>&1; then\n\
    echo "✓ Database ready"\n\
    break\n\
  fi\n\
  attempt=$((attempt + 1))\n\
  if [ $attempt -eq 30 ]; then\n\
    echo "✗ Database not available after 60s"\n\
    exit 1\n\
  fi\n\
  sleep 2\n\
done\n\
\n\
# Migraciones (falla si hay error)\n\
echo "Running migrations..."\n\
if ! python manage.py migrate --noinput; then\n\
  echo "✗ Migrations failed"\n\
  exit 1\n\
fi\n\
echo "✓ Migrations completed"\n\
\n\
# Estáticos (no crítico)\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput >/dev/null 2>&1 || echo "⚠ Static collection skipped"\n\
\n\
# Iniciar Gunicorn\n\
echo "✓ Starting Gunicorn..."\n\
exec gunicorn --bind 0.0.0.0:${PORT:-8000} \\\n\
    --workers ${GUNICORN_WORKERS:-2} \\\n\
    --threads 2 \\\n\
    --worker-class gthread \\\n\
    --timeout 120 \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    --log-level info \\\n\
    core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

EXPOSE ${PORT:-8000}

# Health check para Docker
# start-period: tiempo de gracia para startup inicial (3 minutos)
# interval: frecuencia de checks después del start-period
# timeout: tiempo máximo para que responda el check
# retries: intentos fallidos antes de marcar como unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ready/ || exit 1

CMD ["/app/start.sh"]