# Python 3.11 - usando imagen base completa para evitar problemas de autenticación
FROM python:3.11

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    DOCKER_CONTAINER=true

# Instalar dependencias del sistema
# OPTIMIZACIÓN: Incluir libmagic para validación MIME type
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo el código, no solo la carpeta arc_manager
COPY . .

# Crear directorios
# OPTIMIZACIÓN: Incluir directorio para uploads temporales grandes
# Nota: logs/ solo para desarrollo local, en Docker los logs van a STDOUT/STDERR
RUN mkdir -p /app/arc_manager/staticfiles \
    && mkdir -p /app/arc_manager/media \
    && mkdir -p /app/arc_manager/logs \
    && mkdir -p /app/temp_uploads \
    && chmod 777 /app/temp_uploads

# Directorio Django
WORKDIR /app/arc_manager

# Crear script de inicio con reintentos
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Waiting for database..."\n\
for i in {1..30}; do\n\
  if python manage.py migrate --check > /dev/null 2>&1; then\n\
    echo "Database is ready"\n\
    break\n\
  fi\n\
  echo "Database not ready, waiting... ($i/30)"\n\
  sleep 2\n\
done\n\
\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
\n\
echo "Starting server..."\n\
exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 1800 --worker-class sync --max-requests 1000 --max-requests-jitter 50 core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

# Puerto (Railway asignará automáticamente)
EXPOSE ${PORT:-8000}

# Health check
HEALTHCHECK --interval=600s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Ejecutar script de inicio
CMD ["/app/start.sh"] 