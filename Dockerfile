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

# Crear script de inicio optimizado para Railway
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Starting ArqGest application..."\n\
echo "Environment: $RAILWAY_ENVIRONMENT"\n\
\n\
# Función optimizada para verificar DB (máximo 10 intentos = 20 segundos)\n\
check_db_connection() {\n\
  python -c "\n\
import os, sys, django\n\
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"core.settings\")\n\
try:\n\
    django.setup()\n\
    from django.db import connection\n\
    connection.ensure_connection()\n\
    print(\"✅ Database ready\")\n\
    sys.exit(0)\n\
except Exception as e:\n\
    print(f\"❌ DB error: {str(e)[:100]}\")\n\
    sys.exit(1)\n\
"\n\
}\n\
\n\
# Espera inteligente: máximo 20 segundos\n\
echo "⏳ Checking database connection..."\n\
for i in {1..10}; do\n\
  if check_db_connection 2>/dev/null; then\n\
    echo "✅ Database connected successfully!"\n\
    break\n\
  fi\n\
  echo "⏳ Database not ready, waiting... ($i/10)"\n\
  sleep 2\n\
done\n\
\n\
# Si falla después de 10 intentos, continuar de todas formas\n\
# Railway manejará el error si la DB realmente no está disponible\n\
if ! check_db_connection 2>/dev/null; then\n\
  echo "⚠️  Database connection failed, but continuing startup..."\n\
  echo "   Railway will handle database availability"\n\
fi\n\
\n\
echo "📦 Running migrations..."\n\
python manage.py migrate --noinput || echo "⚠️  Migration failed, continuing..."\n\
\n\
echo "📁 Collecting static files..."\n\
python manage.py collectstatic --noinput || echo "⚠️  Static collection failed, continuing..."\n\
\n\
echo "🌐 Starting Gunicorn server..."\n\
exec gunicorn --bind 0.0.0.0:${PORT:-8000} \\\n\
    --workers 2 \\\n\
    --timeout 300 \\\n\
    --worker-class sync \\\n\
    --max-requests 1000 \\\n\
    --max-requests-jitter 50 \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

# Puerto (Railway asignará automáticamente)
EXPOSE ${PORT:-8000}

# Health check optimizado para Railway
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Ejecutar script de inicio
CMD ["/app/start.sh"] 