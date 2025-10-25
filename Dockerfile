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
max_attempts=15\n\
attempt=0\n\
db_ready=false\n\
\n\
while [ $attempt -lt $max_attempts ]; do\n\
  attempt=$((attempt + 1))\n\
  \n\
  if python manage.py check --database default 2>&1 | tee /tmp/db_check.log; then\n\
    echo "✓ Database ready!"\n\
    db_ready=true\n\
    break\n\
  else\n\
    echo "✗ Database check failed (attempt $attempt/$max_attempts)"\n\
    \n\
    # Mostrar error de Django\n\
    if [ -f /tmp/db_check.log ]; then\n\
      echo "Django error:"\n\
      cat /tmp/db_check.log | head -20\n\
    fi\n\
    \n\
    # Diagnóstico detallado en el primer intento y cada 5 intentos\n\
    if [ $attempt -eq 1 ] || [ $((attempt % 5)) -eq 0 ]; then\n\
      diagnose_db\n\
    fi\n\
    \n\
    if [ $attempt -lt $max_attempts ]; then\n\
      sleep 4\n\
    fi\n\
  fi\n\
done\n\
\n\
# Si DB no está lista, mostrar diagnóstico final y continuar (Railway healthcheck manejará el estado)\n\
if [ "$db_ready" = false ]; then\n\
  echo ""\n\
  echo "===================================="\n\
  echo "⚠️  DATABASE CONNECTION FAILED"\n\
  echo "===================================="\n\
  diagnose_db\n\
  echo "POSSIBLE CAUSES:"\n\
  echo "  1. Database service not started yet (Railway starting order)"\n\
  echo "  2. Database credentials incorrect (check Railway variables)"\n\
  echo "  3. Network issue between services"\n\
  echo "  4. Database not provisioned in Railway"\n\
  echo ""\n\
  echo "NEXT STEPS:"\n\
  echo "  1. Check Railway dashboard for database service status"\n\
  echo "  2. Verify DATABASE_URL is correctly set"\n\
  echo "  3. Check database service logs"\n\
  echo ""\n\
  echo "Starting app anyway - healthcheck will report unhealthy status"\n\
  echo "===================================="\n\
  echo ""\n\
fi\n\
\n\
# Migraciones (skip si DB no disponible)\n\
if [ "$db_ready" = true ]; then\n\
  echo "Running migrations..."\n\
  python manage.py migrate --noinput 2>&1 || {\n\
    echo "⚠️  Migration failed - check logs above"\n\
  }\n\
  \n\
  echo "Collecting static files..."\n\
  python manage.py collectstatic --noinput --clear 2>&1 || {\n\
    echo "⚠️  Static collection failed"\n\
  }\n\
else\n\
  echo "⚠️  Skipping migrations - database not available"\n\
fi\n\
\n\
# Calcular workers\n\
workers=${GUNICORN_WORKERS:-2}\n\
\n\
echo ""\n\
echo "=== Starting Gunicorn ==="\n\
echo "Using optimized logging config"\n\
echo "Time: $(date)"\n\
echo "========================"\n\
echo ""\n\
\n\
exec gunicorn --config gunicorn_config.py core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

EXPOSE ${PORT:-8000}

# Health check simplificado para Railway
# Railway usa /health/ por defecto
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

CMD ["/app/start.sh"]