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
    # Logging middlewares - DEBEN ir antes del ErrorHandlingMiddleware
    'core.logging_middleware.Enhanced500LoggingMiddleware',
    'core.logging_middleware.DatabaseErrorLoggingMiddleware',
    'core.logging_middleware.PerformanceLoggingMiddleware',
    'apps.accounts.middleware.ErrorHandlingMiddleware',
    'core.mixins.PerformanceMiddleware',
]

# Insertar Debug Toolbar Middleware si DEBUG está activado
if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
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
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Mantener compatibilidad con versiones anteriores
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración adicional de WhiteNoise optimizada
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# Configuración robusta para evitar errores de manifest en producción
WHITENOISE_MANIFEST_STRICT = False  # No fallar si falta algún archivo del manifest
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

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
        
        # Para CSS y JS - FORZAR NO CACHE para actualizaciones inmediatas
        if path.endswith(('.css', '.js')):
            headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            headers['Pragma'] = 'no-cache'
            headers['Expires'] = '0'
            headers['ETag'] = f'W/"{hash(url + str(__import__("time").time()))}"'  # ETag único
        
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

# Tamaño máximo total de la petición HTTP (650MB para múltiples archivos)
# Permite múltiples archivos hasta el límite total
DATA_UPLOAD_MAX_NUMBER_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_NUMBER_SIZE', '681574400'))  # 650MB en bytes

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
    
    # Logging optimizado para Railway (reducir overhead)
    if 'LOGGING' in locals():
        # Reducir nivel de logs en producción para mejorar performance
        LOGGING['handlers']['production']['level'] = 'INFO'
        LOGGING['loggers']['django.db.backends']['level'] = 'WARNING'
        
        # Agregar handler específico para Railway
        LOGGING['handlers']['railway'] = {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'production',
        }
    
    # Configuración de sesiones optimizada para Railway
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    SESSION_CACHE_ALIAS = 'default'
    SESSION_COOKIE_AGE = 86400  # 24 horas
    
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
    
    # Configuración específica para Cloudflare R2
    AWS_S3_CUSTOM_DOMAIN = None  # Usar dominio directo de R2
    AWS_S3_FILE_OVERWRITE = False  # No sobrescribir archivos con mismo nombre
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # Cache por 1 día
    }
    
    print(f"🌍 Usando almacenamiento Cloudflare R2: {AWS_S3_ENDPOINT_URL}")
else:
    print("💾 Usando almacenamiento local: FileSystemStorage")

# Configuración de sesiones (usando Redis)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_SAVE_EVERY_REQUEST = False  # Mejora de rendimiento

# Configuración de la cookie de sesión
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_AGE = 1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False

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
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true', 'ignore_timezone_warnings', 'ignore_payment_warnings', 'clean_request_logs', 'filter_sensitive_data'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_prod': {
            'level': 'INFO',
            'filters': ['require_debug_false', 'ignore_timezone_warnings', 'ignore_payment_warnings', 'clean_request_logs', 'filter_sensitive_data'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/errors.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/security.log'),
            'maxBytes': 1024 * 1024 * 2,
            'backupCount': 3,
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
            'handlers': ['console', 'console_prod', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'console_prod', 'error_file', 'debug_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.plans': {
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.accounts': {
            'handlers': ['console', 'console_prod', 'security_file', 'debug_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'console_prod', 'error_file', 'debug_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.error_handler': {
            'handlers': ['console', 'console_prod', 'error_file', 'debug_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console_prod', 'error_file'],
        'level': 'WARNING',
    },
}

# Configuración del sitio
SITE_NAME = os.environ.get('SITE_NAME', 'ARC Manager')
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'localhost:8000')


if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = 'localhost'
    DEFAULT_FROM_EMAIL = 'ARC MANAGER <noreply@archmanager.local>'
else:
    # ========================================
    # 🚀 CONFIGURACIÓN RESEND (REEMPLAZA AWS SES)
    # ========================================
    
    # Verificar si tenemos API key de Resend
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    
    if RESEND_API_KEY:
        # 📧 Railway bloquea SMTP, usamos API de Resend
        # Mantenemos el backend console para compatibilidad con Django
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        
        # 📮 Email de remitente - debe estar verificado en Resend
        DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'adroal08@gmail.com')
        SERVER_EMAIL = DEFAULT_FROM_EMAIL
        
        print("📧 Email configurado (temporalmente deshabilitado)")
    
    if not RESEND_API_KEY:
        # 🔄 Fallback a AWS SES (si no hay Resend configurado)
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        
        EMAIL_HOST = os.environ.get('AWS_SES_HOST', 'email-smtp.us-west-1.amazonaws.com')
        EMAIL_PORT = int(os.environ.get('AWS_SES_PORT', '587'))
        EMAIL_USE_TLS = True
        EMAIL_USE_SSL = False
        
        EMAIL_HOST_USER = os.environ.get('AWS_SES_USER')
        EMAIL_HOST_PASSWORD = os.environ.get('AWS_SES_PASS')
        
        DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tudominio.com')
        SERVER_EMAIL = DEFAULT_FROM_EMAIL
        
        # Timeouts cortos para Railway
        EMAIL_TIMEOUT = 10
        EMAIL_CONNECTION_TIMEOUT = 8
        EMAIL_READ_TIMEOUT = 8
        
        print("📧 AWS SES configurado (fallback)")


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
    
    print("🚀 Configuración de producción activada")

else:
    print("🏠 Ejecutándose en ambiente local")

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
