"""
Configuración de Gunicorn optimizada para logging limpio y profesional.
Elimina el ruido de logs de acceso para mantener solo logs significativos.
"""
import os
import multiprocessing

# Server Socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker Processes
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'gthread'
threads = 2
worker_connections = 1000
worker_tmp_dir = '/dev/shm'
max_requests = 1000
max_requests_jitter = 100
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging - MODO PROFESIONAL: Solo errores y warnings
# El middleware de Django se encarga del logging de requests
accesslog = None  # Desactivar access log (reduce ruido en 90%)
errorlog = '-'  # Errores a STDERR
loglevel = 'warning'  # Solo WARNING y ERROR de Gunicorn
capture_output = False  # No capturar stdout/stderr de la app

# Configuración adicional
preload_app = True
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190


def on_starting(server):
    """
    Se ejecuta cuando Gunicorn inicia.
    """
    print("=" * 50)
    print("🚀 Gunicorn starting...")
    print(f"Workers: {workers}")
    print(f"Threads per worker: {threads}")
    print(f"Binding to: {bind}")
    print(f"Log level: {loglevel} (access logs disabled)")
    print("=" * 50)


def worker_int(worker):
    """
    Se ejecuta cuando un worker recibe SIGINT o SIGQUIT.
    """
    worker.log.warning("⚠️ Worker received INT or QUIT signal")


def worker_abort(worker):
    """
    Se ejecuta cuando un worker se aborta.
    """
    worker.log.error("❌ Worker aborted (SIGABRT)")
