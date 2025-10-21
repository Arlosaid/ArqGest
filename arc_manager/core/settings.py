import os
import sys
import logging
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env
from dotenv import load_dotenv

# Cargar el archivo .env desde el directorio raíz del proyecto
load_dotenv(BASE_DIR.parent / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# En producción, asegurar que DEBUG esté en False si variable de entorno lo indica
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION'):
    DEBUG = False

# DEBUG se controla por variable de entorno
# En desarrollo local, usa DEBUG=True en tu .env

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-insecure-key'
    else:
        raise RuntimeError('SECRET_KEY must be set via environment when DEBUG=False')

# Configuración mejorada de ALLOWED_HOSTS
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# En Railway, agregar automáticamente el dominio de Railway si no está configurado
if os.environ.get('RAILWAY_ENVIRONMENT'):
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    if railway_domain and railway_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(railway_domain)
    
    # También permitir subdominios de railway.app
    railway_subdomain = f"{os.environ.get('RAILWAY_SERVICE_NAME', 'app')}.railway.app"
    if railway_subdomain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(railway_subdomain)
        ALLOWED_HOSTS.append('*.railway.app')
    
    # Agregar dominios personalizados comunes
    custom_domains = [
        'app.arqgest.com',
        'arqgest.com',
        'www.arqgest.com'
    ]
    for domain in custom_domains:
        if domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(domain)

TESTING = bool(os.environ.get('TESTING')) or ('test' in sys.argv)

# En desarrollo o testing se permite configuración laxa
if DEBUG or TESTING:
    if '*' in ALLOWED_HOSTS:
        ALLOWED_HOSTS = ['*']
else:
    # En producción, prohibir comodín
    if '*' in ALLOWED_HOSTS:
        raise RuntimeError('ALLOWED_HOSTS cannot contain "*" when DEBUG=False')


# Application definition

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party apps
    'debug_toolbar',
    'axes',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',

    # Local apps
    'core',
    'apps.accounts',
    'apps.main',
    'apps.orgs',
    'apps.users',
    'apps.plans',
    'apps.projects',
    'apps.files',
    
]

# Activar django-storages solo si está habilitado por entorno
if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
    INSTALLED_APPS.append('storages')

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Compresión de respuestas
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'apps.accounts.middleware.LoginRequiredMiddleware',
    'apps.accounts.middleware.PasswordChangeRequiredMiddleware',
    'apps.accounts.middleware.SuperuserRestrictMiddleware',
    'apps.orgs.middleware.OrganizationContextMiddleware',
    'apps.plans.middleware.SubscriptionAccessMiddleware',
    'apps.plans.middleware.SubscriptionInfoMiddleware',
    # Logging middlewares - DEBEN ir antes del ErrorHandlingMiddleware
    'core.logging_middleware.Enhanced500LoggingMiddleware',
    'core.logging_middleware.DatabaseErrorLoggingMiddleware',
    'core.logging_middleware.PerformanceLoggingMiddleware',
    'apps.accounts.middleware.ErrorHandlingMiddleware',
    'core.mixins.PerformanceMiddleware',
    
    # OPTIMIZACIÓN ULTRA: Middleware para uploads masivos
    'core.middleware.upload_optimization.UploadOptimizationMiddleware',
    'core.middleware.upload_optimization.R2ConnectionPoolMiddleware',
    'core.middleware.upload_optimization.UploadProgressMiddleware',
]

# Insertar Debug Toolbar Middleware si DEBUG está activado
# Debe ir DESPUÉS de GZipMiddleware para evitar warnings
if DEBUG:
    # Insertar después de GZipMiddleware (posición 3, después de Security, WhiteNoise y GZip)
    MIDDLEWARE.insert(3, 'debug_toolbar.middleware.DebugToolbarMiddleware')
else:
    # Remover debug_toolbar de INSTALLED_APPS en producción para evitar warnings
    if 'debug_toolbar' in INSTALLED_APPS:
        INSTALLED_APPS.remove('debug_toolbar')


ROOT_URLCONF = 'core.urls'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'axes.backends.AxesBackend',
]

# Configuración completa de Django Axes
# Configuración básica
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = 0.25
AXES_RESET_ON_SUCCESS = True

# Campos de formulario
AXES_USERNAME_FORM_FIELD = 'username'
AXES_PASSWORD_FORM_FIELD = 'password'

# Configuración de manipulación y almacenamiento
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
AXES_LOCKOUT_BY_USER_OR_IP = True

# URLs y redirecciones
AXES_LOCKOUT_URL = '/accounts/login/?locked=1'
AXES_REDIRECT_URL = '/'

# Parámetros de bloqueo
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address', 'user_agent']
AXES_LOCKOUT_TEMPLATE = None

# Configuración para excluir rutas específicas
AXES_ENABLE_ADMIN = False
#AXES_WHITELIST_CALLABLE = 'core.utils.axes_whitelist'

# Configuración de mensajes y respuestas
AXES_LOCKOUT_CALLABLE = None
AXES_VERBOSE = True


# Configuración de cache (usando Redis)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'arc_manager',
        'TIMEOUT': 300,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'arc_sessions',
        'TIMEOUT': 86400,  # 24 hours
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'db.sqlite3'))
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# Conexiones persistentes a DB
DATABASES['default']['CONN_MAX_AGE'] = int(os.environ.get('CONN_MAX_AGE', '120'))

# Configuración de timeouts para PostgreSQL (evitar connection timeout en Railway)
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'  # 30 segundos
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Mexico_City'  # Zona horaria de México (UTC-6)
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuración mejorada de WhiteNoise para archivos estáticos con Cache Busting
# Django 4.2+ usa STORAGES en lugar de STATICFILES_STORAGE

# Configuración de almacenamiento dinámico (local o R2/S3)
DEFAULT_STORAGE_BACKEND = "django.core.files.storage.FileSystemStorage"

# Si están habilitados los storages externos (R2/S3), usar esos
if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
    DEFAULT_STORAGE_BACKEND = "storages.backends.s3boto3.S3Boto3Storage"

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_STORAGE_BACKEND,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Mantener compatibilidad con versiones anteriores
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración adicional de WhiteNoise optimizada
# Para forzar cache-busting en dispositivos móviles (iPhone/Safari)
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False  # Evita errores si falta algún archivo
WHITENOISE_MAX_AGE = 31536000  # 1 año de cache para archivos con hash
WHITENOISE_AUTOREFRESH = DEBUG

# Versionado global para cache-busting en dispositivos móviles
# Cambiar esta versión en cada deploy para forzar recarga
STATIC_VERSION = '2025-01-15-v3'
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']
# Ventana de renovación anticipada (días antes de end_date)
RENEWAL_WINDOW_DAYS = int(os.environ.get('RENEWAL_WINDOW_DAYS', '2'))

# Configuración de cache optimizada para móviles (iOS y Android)
# Safari móvil y Chrome Android requieren headers específicos
if not DEBUG:
    # Cache reducido para compatibilidad móvil - MÁS CONSERVADOR
    WHITENOISE_MAX_AGE = 1800  # 30 minutos - cache más corto para móviles
    WHITENOISE_STATIC_PREFIX = '/static/'
    
    # Headers simplificados para evitar problemas
    def mobile_cache_headers(headers, path, url):
        """Headers optimizados para móviles sin romper funcionalidad"""
        # Headers básicos seguros
        headers['Vary'] = 'Accept-Encoding, User-Agent'
        
        # Para CSS y JS - cache moderado con validación
        if path.endswith(('.css', '.js')):
            headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
            headers['ETag'] = f'W/"{hash(url)}"'
        
        # Para imágenes - cache normal
        elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
            headers['Cache-Control'] = 'public, max-age=86400'
        
        # Otros archivos
        else:
            headers['Cache-Control'] = 'public, max-age=3600'
    
    WHITENOISE_ADD_HEADERS_FUNCTION = mobile_cache_headers
    WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: False  # Sin inmutabilidad
else:
    # En desarrollo, sin cache
    WHITENOISE_MAX_AGE = 0

# ===== CONFIGURACIÓN DE UPLOADS OPTIMIZADA =====
# Límites para manejar uploads grandes sin saturar memoria del servidor
# Configuración optimizada para archivos hasta 600MB

# Tamaño máximo de archivos que se cargan en memoria (25MB)
# Archivos más grandes se escriben a disco temporalmente
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', '26214400'))  # 25MB en bytes

# CRÍTICO: Tamaño máximo total de la petición HTTP actualizado para arquitectos
# Permite archivos hasta 1.2GB + overhead HTTP
DATA_UPLOAD_MAX_NUMBER_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_NUMBER_SIZE', '1342177280'))  # 1.25GB en bytes

# Directorio temporal para archivos grandes durante upload
FILE_UPLOAD_TEMP_DIR = os.environ.get('FILE_UPLOAD_TEMP_DIR', os.path.join(BASE_DIR, 'temp_uploads'))

# Crear el directorio temporal si no existe
if not os.path.exists(FILE_UPLOAD_TEMP_DIR):
    try:
        os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)
    except OSError as e:
        # Si no se puede crear, usar el directorio temporal del sistema
        import tempfile
        FILE_UPLOAD_TEMP_DIR = tempfile.gettempdir()

# Handler personalizado optimizado para archivos grandes
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',    # Archivos pequeños (<25MB) en memoria
    'core.upload_handlers.OptimizedTemporaryFileUploadHandler',   # Archivos grandes optimizados
    'core.upload_handlers.ProgressTrackingUploadHandler',         # Tracking de progreso (opcional)
]

# Permisos de archivos subidos
FILE_UPLOAD_PERMISSIONS = 0o644

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== CONFIGURACIONES ESPECÍFICAS PARA RAILWAY (PRODUCCIÓN) =====
if not DEBUG and os.environ.get('RAILWAY_ENVIRONMENT'):
    # Optimizaciones para evitar timeouts en Railway con archivos grandes
    
    # Optimización de conexiones de base de datos
    DATABASES['default']['CONN_MAX_AGE'] = 60  # Reutilizar conexiones por 60 segundos
    
    # Configuración de timeouts específica para Railway
    if 'OPTIONS' not in DATABASES['default']:
        DATABASES['default']['OPTIONS'] = {}
    
    # Para PostgreSQL, usar las opciones correctas
    if 'postgresql' in DATABASES['default']['ENGINE'] or 'psycopg' in str(DATABASES['default']):
        DATABASES['default']['OPTIONS'].update({
            'connect_timeout': 20,
            'options': '-c default_transaction_isolation=serializable'
        })
    else:
        # Para MySQL/MariaDB
        DATABASES['default']['OPTIONS'].update({
            'charset': 'utf8mb4',
            'connect_timeout': 20,
            'read_timeout': 30,
            'write_timeout': 30,
            'sql_mode': 'STRICT_TRANS_TABLES',
        })
    
    # Logging optimizado para Railway - ya configurado arriba con STDOUT/STDERR
    # No es necesario agregar handlers adicionales - Docker los maneja
    
    # Configuración de sesiones optimizada para Railway
    # Usar DB en Railway (más confiable que cache en entornos efímeros)
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    SESSION_CACHE_ALIAS = 'default'
    SESSION_COOKIE_AGE = 604800  # 7 días (consistente con config general)
    
    # Optimización de middleware para Railway
    MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]
    
    # Cache optimizado para Railway - usar Redis si está disponible
    # Redis es mucho más rápido que DB cache para grandes volúmenes
    if os.environ.get('REDIS_URL'):
        # Usar Redis en Railway para mejor rendimiento
        CACHES['default']['TIMEOUT'] = 600  # 10 minutos cache en producción
        CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS']['max_connections'] = 20  # Reducir conexiones en Railway
    else:
        # Fallback a DB cache solo si no hay Redis
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'django_cache_table',
                'TIMEOUT': 300,  # 5 minutos
                'OPTIONS': {
                    'MAX_ENTRIES': 1000,
                    'CULL_FREQUENCY': 3,
                }
            }
        }

# Configuración Cloudflare R2 Storage (solo cuando está habilitado)
if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
    # Configuración para django-storages con Cloudflare R2
    # Usar variables CLOUDFLARE_ (preferidas) con fallback a AWS_ para compatibilidad
    AWS_S3_ENDPOINT_URL = (
        os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL') or 
        os.environ.get('AWS_S3_ENDPOINT_URL')
    )
    AWS_STORAGE_BUCKET_NAME = (
        os.environ.get('CLOUDFLARE_R2_BUCKET_NAME') or 
        os.environ.get('AWS_STORAGE_BUCKET_NAME')
    )
    AWS_ACCESS_KEY_ID = (
        os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID') or 
        os.environ.get('AWS_ACCESS_KEY_ID') or 
        os.environ.get('R2_ACCESS_KEY_ID')
    )
    AWS_SECRET_ACCESS_KEY = (
        os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY') or 
        os.environ.get('AWS_SECRET_ACCESS_KEY') or 
        os.environ.get('R2_SECRET_ACCESS_KEY')
    )
    AWS_S3_REGION_NAME = os.environ.get('CLOUDFLARE_R2_REGION', 'auto')
    AWS_S3_ADDRESSING_STYLE = 'virtual'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None
    
    # Configuración específica para Cloudflare R2 optimizada para archivos grandes
    AWS_S3_CUSTOM_DOMAIN = None  # Usar dominio directo de R2
    AWS_S3_FILE_OVERWRITE = False  # No sobrescribir archivos con mismo nombre
    
    # CONFIGURACIÓN ULTRA-OPTIMIZADA para archivos grandes en R2
    AWS_S3_MAX_MEMORY_SIZE = 26214400  # 25MB - archivos más grandes usan multipart
    
    # Configuración de transferencia optimizada para arquitectos
    AWS_S3_TRANSFER_CONFIG = {
        'multipart_threshold': 26214400,  # 25MB - iniciar multipart upload
        'max_concurrency': 15,  # 15 conexiones concurrentes (aumentado)
        'multipart_chunksize': 52428800,  # 50MB por chunk (chunks más grandes = menos overhead)
        'max_bandwidth': None,  # Sin límite de ancho de banda
        'use_threads': True,  # Threading para máximo paralelismo
        'max_io_queue': 1000,  # Cola I/O grande para archivos masivos
    }
    
    # Timeouts y retries ultra-robustos
    AWS_S3_REQUEST_CONFIG = {
        'retries': {
            'max_attempts': 5,  # 5 intentos (aumentado)
            'mode': 'adaptive',  # Retry inteligente
            'total_max_attempts': 10  # Máximo absoluto
        },
        'connect_timeout': 120,  # 2 minutos para conectar (redes lentas)
        'read_timeout': 1800,    # 30 minutos para archivos masivos (2x aumentado)
        'max_pool_connections': 50,  # Pool de conexiones grande
    }
    
    # Configuración de streaming para archivos masivos
    AWS_S3_STREAM_CONFIG = {
        'enable_checksum': True,  # Verificación de integridad
        'checksum_algorithm': 'SHA256',  # Algoritmo robusto
        'enable_payload_signing': False,  # Desactivar para performance
    }
    
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # Cache por 1 día
    }
    
    logging.info(f"Storage: Cloudflare R2 - {AWS_S3_ENDPOINT_URL}")
else:
    logging.info("Storage: Local FileSystemStorage")

# ========================================
# CONFIGURACIÓN OPTIMIZADA DE SESIONES
# ========================================
# Usando Redis para sesiones (más rápido y escalable que DB)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# Rendimiento: No guardar en cada petición (solo cuando cambia)
SESSION_SAVE_EVERY_REQUEST = False

# DURACIÓN DE SESIÓN: 7 días (604800 segundos)
# Balance óptimo entre seguridad y experiencia de usuario para apps empresariales
# Los usuarios no tendrán que iniciar sesión diariamente
SESSION_COOKIE_AGE = 604800  # 7 días

# Configuración de la cookie de sesión
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_PATH = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Mantener sesión al cerrar navegador

# Seguridad de cookies
SESSION_COOKIE_HTTPONLY = True  # Protección contra XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección contra CSRF
SESSION_COOKIE_SECURE = False  # Se activa a True en producción automáticamente

# Authentication URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# URLs exentas del middleware de login_required
LOGIN_EXEMPT_URLS = [
    r'^accounts/login/?$',
    r'^accounts/logout/?$',
    r'^accounts/password_reset/?$',
    r'^accounts/password_reset/done/?$',
    r'^accounts/reset/(.+)/(.+)/?$',
    r'^accounts/reset/done/?$',
    r'^accounts/force-password-change/?$',
    r'^admin/.*$',
    r'^static/.*$',
    r'^media/.*$',
    r'^__debug__/.*$',
    r'^plans/cron/renewal-reminders/?$',  # Endpoint para cron externo
    r'^health/?$',  # Health check endpoint
]

# Django Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]


# Configuración del sistema de mensajes
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

# Tags de mensajes personalizados para Bootstrap
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ========================================
# CONFIGURACIÓN DE LOGGING OPTIMIZADA PARA DOCKER
# ========================================
# En Docker, los logs deben ir a STDOUT/STDERR para mejor rendimiento
# Docker maneja la rotación y límites automáticamente

# Determinar si estamos en un entorno containerizado
IS_DOCKER = os.environ.get('DOCKER_CONTAINER', 'false').lower() == 'true'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} [{process:d}:{thread:d}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'},
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
        'ignore_timezone_warnings': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'DateTimeField' not in record.getMessage() or 'received a naive datetime' not in record.getMessage()
        },
        'ignore_payment_warnings': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'Payment.created_at' not in record.getMessage()
        },
        'clean_request_logs': {'()': 'core.logging_filters.RequestLoggingFilter'},
        'filter_sensitive_data': {'()': 'core.logging_filters.SensitiveDataFilter'},
    },
    'handlers': {
        # Handler para desarrollo (consola simple)
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true', 'ignore_timezone_warnings', 'ignore_payment_warnings', 'clean_request_logs', 'filter_sensitive_data'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # Handler para producción/Docker (STDOUT con formato verbose)
        'console_prod': {
            'level': 'INFO',
            'filters': ['require_debug_false', 'ignore_timezone_warnings', 'ignore_payment_warnings', 'clean_request_logs', 'filter_sensitive_data'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # Handler de errores críticos a STDERR
        'stderr': {
            'level': 'ERROR',
            'filters': ['filter_sensitive_data'],
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',  # Errores van a STDERR
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'console_prod'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['stderr', 'mail_admins'],
            'level': 'WARNING',  # Solo errores importantes
            'propagate': False,
        },
        'django.security': {
            'handlers': ['stderr', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'console_prod'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.plans': {
            'handlers': ['console', 'console_prod'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
        'apps.accounts': {
            'handlers': ['console', 'console_prod', 'stderr'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'console_prod'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.error_handler': {
            'handlers': ['console', 'console_prod', 'stderr'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console_prod', 'stderr'],
        'level': 'WARNING',
    },
}

# En desarrollo local (no Docker), agregar handlers de archivo opcionales
if DEBUG and not IS_DOCKER:
    LOGGING['handlers']['debug_file'] = {
        'level': 'DEBUG',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
        'maxBytes': 1024 * 1024 * 5,  # 5MB
        'backupCount': 3,  # Reducido a 3 para ahorrar espacio
        'formatter': 'verbose',
    }
    LOGGING['handlers']['error_file'] = {
        'level': 'ERROR',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': os.path.join(BASE_DIR, 'logs/errors.log'),
        'maxBytes': 1024 * 1024 * 5,  # 5MB
        'backupCount': 3,
        'formatter': 'verbose',
    }
    # Agregar handlers de archivo a los loggers en desarrollo
    LOGGING['loggers']['django']['handlers'].append('error_file')
    LOGGING['loggers']['apps']['handlers'].append('debug_file')
    LOGGING['loggers']['core']['handlers'].append('debug_file')

# Configuración del sitio
SITE_NAME = os.environ.get('SITE_NAME', 'ArqGest')
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'localhost:8000')


if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = 'localhost'
    DEFAULT_FROM_EMAIL = 'ArqGest <noreply@arqgest.local>'
else:
    # ========================================
    # CONFIGURACIÓN RESEND PARA PRODUCCIÓN
    # ========================================
    
    # Verificar si tenemos API key de Resend
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    
    if RESEND_API_KEY:
        # Usar backend personalizado de Resend
        EMAIL_BACKEND = 'core.backends.resend_backend.ResendBackend'
        
        # Email de remitente - debe estar verificado en Resend
        DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ArqGest <noreply@arqgest.com>')
        SERVER_EMAIL = DEFAULT_FROM_EMAIL
        
        logging.info("Email: Resend backend configured")
    
    else:
        # Fallback: Si no hay Resend, usar console (no envía emails reales)
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ArqGest <noreply@arqgest.com>')
        SERVER_EMAIL = DEFAULT_FROM_EMAIL
        
        logging.warning("Email: No RESEND_API_KEY configured - using console backend (emails will only print to logs)")


# Configuración para el sistema de pagos
PAYMENT_BANK_INFO = {
    'bank_name': os.environ.get('PAYMENT_BANK_NAME', 'Banco BBVA'),
    'account_holder': os.environ.get('PAYMENT_ACCOUNT_HOLDER', 'TU EMPRESA SA DE CV'),
    'account_number': os.environ.get('PAYMENT_ACCOUNT_NUMBER', '0123456789'),
    'clabe': os.environ.get('PAYMENT_CLABE', '012345678901234567'),
    'concept_prefix': os.environ.get('PAYMENT_CONCEPT_PREFIX', 'Upgrade-Plan')
}

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@tudominio.com')
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000' if DEBUG else 'https://tudominio.com')

# Información de contacto de soporte
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '55 1234 5678')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'soporte@tuempresa.com')

# ========================================
# CONFIGURACIONES DE PLANES Y SUSCRIPCIONES
# ========================================

# Ventana de días antes del vencimiento en la que se permite renovar anticipadamente
# La nueva vigencia comienza cuando termina la actual, sin perder días pagados
RENEWAL_WINDOW_DAYS = int(os.environ.get('RENEWAL_WINDOW_DAYS', '3'))

# ========================================
# CONFIGURACIONES ESPECÍFICAS PARA PRODUCCIÓN
# ========================================

IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') is not None or not DEBUG

# Forzar el uso de nuestras páginas de error personalizadas en producción
if not DEBUG:
    # Asegurar que Django no use páginas de error por defecto
    USE_THOUSAND_SEPARATOR = True
    
    # Configuración adicional para handlers de error
    APPEND_SLASH = True
    PREPEND_WWW = False

if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    LOGGING['handlers']['cloudwatch'] = {
        'level': 'INFO',
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    }
    LOGGING['loggers']['django']['handlers'].append('cloudwatch')
    
    # Email ya configurado arriba - no duplicar configuración
    
    # Cache ya configurado arriba
    
    HEALTH_CHECK_URL = '/health/'
    
    logging.info("Environment: Production mode enabled")

else:
    logging.info("Environment: Local development mode")

# Health check endpoint para monitoreo
def health_check(request):
    from django.http import JsonResponse
    return JsonResponse({'status': 'healthy', 'service': 'arc-manager'})


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Endurecimiento general cuando no hay DEBUG
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ========================================
# CRON JOBS - SEGURIDAD
# ========================================
# Clave secreta para autenticar requests de cron externos
CRON_SECRET_KEY = os.environ.get('CRON_SECRET_KEY', '')