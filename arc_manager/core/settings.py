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


# Configuración de cache (usando base de datos)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
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

# Configuración mejorada de WhiteNoise para archivos estáticos
if DEBUG:
    # En desarrollo, usar el backend estándar
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # En producción, usar WhiteNoise más estable
    # CompressedManifestStaticFilesStorage puede fallar si hay archivos faltantes
    # Usar CompressedStaticFilesStorage que es más robusto
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración adicional de WhiteNoise
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# Configuración de cache para archivos estáticos en producción
if not DEBUG:
    # Cache estático por 1 año para archivos con hash
    WHITENOISE_MAX_AGE = 31536000
    # Configurar headers de cache específicos
    WHITENOISE_STATIC_PREFIX = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Storage backend opcional para R2/S3 (activado por variables de entorno)
if os.environ.get('DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = os.environ['DEFAULT_FILE_STORAGE']
    AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('R2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or os.environ.get('R2_SECRET_ACCESS_KEY')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'auto')
    AWS_S3_ADDRESSING_STYLE = os.environ.get('AWS_S3_ADDRESSING_STYLE', 'virtual')
    AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION', 's3v4')
    AWS_DEFAULT_ACL = None

# Configuración de sesiones (usando base de datos)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SAVE_EVERY_REQUEST = False

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
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true', 'ignore_timezone_warnings', 'ignore_payment_warnings'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_prod': {
            'level': 'INFO',
            'filters': ['require_debug_false', 'ignore_timezone_warnings', 'ignore_payment_warnings'],
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
            'level': 'ERROR',
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
        'core': {
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
        
        print("📧 Configuración Resend API activada (Railway bloquea SMTP):")
        print(f"   🚀 API KEY configurada")
        print(f"   📮 FROM: {DEFAULT_FROM_EMAIL}")
    
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
        
        print("📧 Configuración AWS SES (fallback):")
        print(f"   🌎 HOST: {EMAIL_HOST}")
        print(f"   📮 FROM: {DEFAULT_FROM_EMAIL}")


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
