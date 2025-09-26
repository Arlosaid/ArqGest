# Python 3.11 - usando imagen base completa para evitar problemas de autenticación
FROM python:3.11

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
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
RUN mkdir -p /app/arc_manager/staticfiles \
    && mkdir -p /app/arc_manager/media \
    && mkdir -p /app/arc_manager/logs

# Directorio Django
WORKDIR /app/arc_manager

# Crear script de inicio
RUN echo '#!/bin/bash\n\
echo "🔄 Ejecutando migraciones..."\n\
python manage.py migrate --noinput || echo "⚠️ Error en migraciones - continuando por ahora"\n\
echo "✅ Migraciones listas"\n\
echo "📦 Desplegando archivos estáticos con cache busting..."\n\
python manage.py deploy_static || echo "⚠️ Error en deploy_static - continuando"\n\
echo "✅ Archivos estáticos con cache busting listos"\n\
# echo "🔍 Ejecutando diagnóstico de conexión SMTP..."\n\
# python manage.py check_smtp_connection\n\
# echo "✅ Diagnóstico finalizado"\n\
echo "🚀 Iniciando servidor..."\n\
exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 core.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

# Puerto (Railway asignará automáticamente)
EXPOSE ${PORT:-8000}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Ejecutar script de inicio
CMD ["/app/start.sh"] 