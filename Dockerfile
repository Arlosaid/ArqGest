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

# Script de inicio optimizado para Railway - logs reducidos
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Función para diagnosticar problemas de DB (solo si falla)\n\
diagnose_db() {\n\
  echo ""\n\
  echo "=== DATABASE DIAGNOSTIC ==="\n\
  echo "DATABASE_URL present: $(if [ -n "$DATABASE_URL" ]; then echo "YES"; else echo "NO"; fi)"\n\
  if [ -n "$DATABASE_URL" ]; then\n\
    echo "DATABASE_URL format: $(echo $DATABASE_URL | sed "s/:\/\/.*@/:\/\/***@/")"\n\
  fi\n\
  echo "PGHOST: ${PGHOST:-not set}"\n\
  echo "PGPORT: ${PGPORT:-not set}"\n\
  echo ""\n\
  \n\
  if [ -n "$PGHOST" ]; then\n\
    if timeout 5 bash -c "</dev/tcp/$PGHOST/${PGPORT:-5432}" 2>/dev/null; then\n\
      echo "✓ Network OK"\n\
    else\n\
      echo "✗ Network FAILED"\n\
    fi\n\
  fi\n\
  echo "========================="\n\
}\n\
\n\
# Verificación de DB silenciosa - solo muestra errores\n\
max_attempts=15\n\
attempt=0\n\
db_ready=false\n\
\n\
while [ $attempt -lt $max_attempts ]; do\n\
  attempt=$((attempt + 1))\n\
  \n\
  if python manage.py check --database default >/dev/null 2>&1; then\n\
    db_ready=true\n\
    break\n\
  else\n\
    if [ $attempt -eq 1 ]; then\n\
      echo "Waiting for database..."\n\
    fi\n\
    if [ $attempt -lt $max_attempts ]; then\n\
      sleep 4\n\
    fi\n\
  fi\n\
done\n\
\n\
# Solo mostrar diagnóstico si DB falló\n\
if [ "$db_ready" = false ]; then\n\
  echo ""\n\
  echo "⚠️  DATABASE CONNECTION FAILED"\n\
  diagnose_db\n\
  echo "Starting app anyway - healthcheck will report status"\n\
  echo ""\n\
fi\n\
\n\
# Migraciones silenciosas (skip si DB no disponible)\n\
if [ "$db_ready" = true ]; then\n\
  python manage.py migrate --noinput >/dev/null 2>&1 || echo "⚠️ Migration failed"\n\
  python manage.py collectstatic --noinput --clear >/dev/null 2>&1 || echo "⚠️ Static collection failed"\n\
fi\n\
\n\
# Iniciar Gunicorn\n\
workers=${GUNICORN_WORKERS:-2}\n\
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
    --access-logfile /dev/null \\\n\
    --error-logfile - \\\n\
    --log-level warning \\\n\
    --capture-output \\\n\
    --enable-stdio-inheritance \\\n\
    --preload \\\n\
    core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

EXPOSE ${PORT:-8000}

# Health check simplificado para Railway
# Railway usa /health/ por defecto
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

CMD ["/app/start.sh"]