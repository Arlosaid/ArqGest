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

# Script de inicio optimizado para Railway con diagnóstico detallado
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== ArqGest Startup ===" \n\
echo "Environment: ${RAILWAY_ENVIRONMENT:-production}"\n\
echo "Port: ${PORT:-8000}"\n\
echo "Time: $(date)"\n\
echo ""\n\
\n\
# Función para diagnosticar problemas de DB\n\
diagnose_db() {\n\
  echo ""\n\
  echo "=== DATABASE DIAGNOSTIC ==="\n\
  echo "DATABASE_URL present: $(if [ -n "$DATABASE_URL" ]; then echo "YES"; else echo "NO"; fi)"\n\
  if [ -n "$DATABASE_URL" ]; then\n\
    echo "DATABASE_URL format: $(echo $DATABASE_URL | sed "s/:\/\/.*@/:\/\/***@/")"\n\
  fi\n\
  echo "PGHOST: ${PGHOST:-not set}"\n\
  echo "PGPORT: ${PGPORT:-not set}"\n\
  echo "PGDATABASE: ${PGDATABASE:-not set}"\n\
  echo "PGUSER: ${PGUSER:-not set}"\n\
  echo ""\n\
  \n\
  # Test de conectividad de red\n\
  if [ -n "$PGHOST" ]; then\n\
    echo "Testing network connectivity to database host..."\n\
    if timeout 5 bash -c "</dev/tcp/$PGHOST/${PGPORT:-5432}" 2>/dev/null; then\n\
      echo "✓ Network connection to $PGHOST:${PGPORT:-5432} successful"\n\
    else\n\
      echo "✗ Cannot reach $PGHOST:${PGPORT:-5432} - network issue or DB not running"\n\
    fi\n\
  fi\n\
  \n\
  # Test con psql si está disponible\n\
  if command -v psql >/dev/null 2>&1 && [ -n "$DATABASE_URL" ]; then\n\
    echo "Testing PostgreSQL connection with psql..."\n\
    if psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then\n\
      echo "✓ psql connection successful"\n\
    else\n\
      echo "✗ psql connection failed - credentials or permissions issue"\n\
    fi\n\
  fi\n\
  echo "========================="\n\
  echo ""\n\
}\n\
\n\
# Verificación de DB con diagnóstico detallado\n\
echo "Checking database connection..."\n\
echo "Timeout: 3 minutes (45 attempts x 4 seconds)"\n\
max_attempts=45\n\
attempt=0\n\
db_ready=false\n\
\n\
while [ $attempt -lt $max_attempts ]; do\n\
  attempt=$((attempt + 1))\n\
  \n\
  if python manage.py check --database default 2>&1 | tee /tmp/db_check.log; then\n\
    echo "✓ Database ready after $attempt attempts!"\n\
    db_ready=true\n\
    break\n\
  else\n\
    echo "✗ Database check failed (attempt $attempt/$max_attempts)"\n\
    \n\
    # Diagnóstico detallado en el primer intento y cada 10 intentos\n\
    if [ $attempt -eq 1 ] || [ $((attempt % 10)) -eq 0 ]; then\n\
      diagnose_db\n\
    fi\n\
    \n\
    if [ $attempt -lt $max_attempts ]; then\n\
      sleep 4\n\
    fi\n\
  fi\n\
done\n\
\n\
# Si DB no está lista después de 3 minutos, FALLAR COMPLETAMENTE\n\
if [ "$db_ready" = false ]; then\n\
  echo ""\n\
  echo "===================================="\n\
  echo "❌ DATABASE CONNECTION FAILED"\n\
  echo "===================================="\n\
  diagnose_db\n\
  echo "CRITICAL ERROR: Database not available after 3 minutes"\n\
  echo ""\n\
  echo "POSSIBLE CAUSES:"\n\
  echo "  1. Database service not started (check Railway dashboard)"\n\
  echo "  2. DATABASE_URL incorrect or missing"\n\
  echo "  3. Network issue between services"\n\
  echo "  4. Database credentials wrong"\n\
  echo ""\n\
  echo "Container will exit now. Railway will retry."\n\
  echo "===================================="\n\
  exit 1\n\
fi\n\
\n\
# Migraciones\n\
echo "Running migrations..."\n\
if ! python manage.py migrate --noinput 2>&1; then\n\
  echo "❌ Migration failed - exiting"\n\
  exit 1\n\
fi\n\
echo "✓ Migrations completed successfully"\n\
\n\
# Collecting static files (sin --clear para ser más rápido)\n\
echo "Collecting static files..."\n\
if ! python manage.py collectstatic --noinput 2>&1; then\n\
  echo "⚠️  Static collection failed - continuing anyway"\n\
fi\n\
echo "✓ Static files collected"\n\
\n\
# Calcular workers\n\
workers=${GUNICORN_WORKERS:-2}\n\
\n\
echo ""\n\
echo "=== Starting Gunicorn ==="\n\
echo "Optimized logging: access logs disabled"\n\
echo "Time: $(date)"\n\
echo "========================"\n\
echo ""\n\
\n\
# Calcular workers\n\
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

# Health check para Docker
# start-period: tiempo de gracia para startup inicial (3 minutos)
# interval: frecuencia de checks después del start-period
# timeout: tiempo máximo para que responda el check
# retries: intentos fallidos antes de marcar como unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ready/ || exit 1

CMD ["/app/start.sh"]