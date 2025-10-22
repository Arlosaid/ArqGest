"""
Configuración optimizada de Gunicorn para Railway
"""
import os
import logging
import sys

# Configuración básica
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get('WEB_CONCURRENCY', '2'))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging optimizado
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Formato de access log optimizado para Railway
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de logging estructurado
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if os.environ.get('RAILWAY_ENVIRONMENT') else 'simple',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Configuración de preload
preload_app = True

# Configuración de seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configuración de memoria
worker_tmp_dir = '/dev/shm' if os.path.exists('/dev/shm') else None

# Configuración de Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # En Railway, usar configuración optimizada
    workers = min(workers, 4)  # Máximo 4 workers en Railway
    timeout = 60  # Timeout más largo para Railway
    keepalive = 5
