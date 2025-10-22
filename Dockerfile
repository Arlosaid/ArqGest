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

# Script de inicio optimizado para Railway
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting ArqGest application..."\n\
echo "Environment: ${RAILWAY_ENVIRONMENT:-production}"\n\
echo "Port: ${PORT:-8000}"\n\
\n\
# Verificación simple de DB con timeout\n\
echo "Checking database connection..."\n\
max_attempts=10\n\
attempt=0\n\
db_ready=false\n\
\n\
while [ $attempt -lt $max_attempts ]; do\n\
  if python manage.py check --database default > /dev/null 2>&1; then\n\
    echo "Database ready"\n\
    db_ready=true\n\
    break\n\
  fi\n\
  attempt=$((attempt + 1))\n\
  if [ $attempt -lt $max_attempts ]; then\n\
    echo "Database not ready, waiting... ($attempt/$max_attempts)"\n\
    sleep 3\n\
  fi\n\
done\n\
\n\
if [ "$db_ready" = false ]; then\n\
  echo "WARNING: Could not connect to database after $max_attempts attempts"\n\
  echo "Continuing startup - Railway will retry"\n\
fi\n\
\n\
# Migraciones solo si DB está lista\n\
if [ "$db_ready" = true ]; then\n\
  echo "Running migrations..."\n\
  python manage.py migrate --noinput || echo "WARNING: Migration failed"\n\
  \n\
  echo "Collecting static files..."\n\
  python manage.py collectstatic --noinput --clear || echo "WARNING: Static collection failed"\n\
else\n\
  echo "Skipping migrations - database not ready"\n\
fi\n\
\n\
# Calcular workers basado en Railway\n\
workers=${GUNICORN_WORKERS:-2}\n\
\n\
echo "Starting Gunicorn server..."\n\
echo "  Workers: $workers"\n\
echo "  Port: ${PORT:-8000}"\n\
echo "  Timeout: 120s"\n\
\n\
exec gunicorn --bind 0.0.0.0:${PORT:-8000} \\\n\
    --workers $workers \\\n\
    --threads 2 \\\n\
    --worker-class gthread \\\n\
    --worker-tmp-dir /dev/shm \\\n\
    --timeout 120 \\\n\
    --graceful-timeout 30 \\\n\
    --keep-alive 5 \\\n\
    --max-requests 1000 \\\n\
    --max-requests-jitter 100 \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    --log-level info \\\n\
    --preload \\\n\
    core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

EXPOSE ${PORT:-8000}

# Health check simplificado para Railway
# Railway usa /health/ por defecto
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

CMD ["/app/start.sh"]