import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-insecure-key'
    else:
        raise RuntimeError('SECRET_KEY must be set via environment when DEBUG=False')

# Configuración mejorada de ALLOWED_HOSTS
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

TESTING = bool(os.environ.get('TESTING')) or ('test' in sys.argv)

# En desarrollo o testing se permite configuración laxa
if DEBUG or TESTING:
    if '*' in ALLOWED_HOSTS:
        ALLOWED_HOSTS = ['*']
else:
    # En producción, prohibir comodín
    if '*' in ALLOWED_HOSTS:
        raise RuntimeError('ALLOWED_HOSTS cannot contain "*" when DEBUG=False')

# En producción, asegurar que DEBUG esté en False si variable de entorno lo indica
if os.environ.get('AWS_EXECUTION_ENV') or os.environ.get('PRODUCTION'):
    DEBUG = False


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
    'apps.accounts.middleware.SuperuserRestrictMiddleware',
    'apps.orgs.middleware.OrganizationContextMiddleware',
    'apps.accounts.middleware.ErrorHandlingMiddleware',
    'core.mixins.PerformanceMiddleware',
]

# Insertar Debug Toolbar Middleware si DEBUG está activado
if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')


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


# Configuración de Redis para cache
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {},
        'KEY_PREFIX': 'arc_manager',
        'TIMEOUT': 300,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {},
        'KEY_PREFIX': 'arc_sessions',
        'TIMEOUT': 86400,
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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

# Configuración de sesiones con Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
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
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_prod': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
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
            'propagate': True,
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
            'propagate': True,
        },
        'apps.plans': {
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console_prod', 'error_file'],
        'level': 'WARNING',
    },
}

# Configuración del sitio
SITE_NAME = 'ARC Manager'
SITE_DOMAIN = 'localhost:8000'


if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = 'localhost'
    DEFAULT_FROM_EMAIL = 'ARC MANAGER <noreply@archmanager.local>'
else:
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION', 'us-east-1')
    AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
    AWS_SES_AUTO_THROTTLE = 0.5
    AWS_SES_CONFIGURATION_SET = os.environ.get('AWS_SES_CONFIGURATION_SET')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tudominio.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configuración para el sistema de pagos
PAYMENT_BANK_INFO = {
    'bank_name': 'Banco BBVA',
    'account_holder': 'TU EMPRESA SA DE CV',
    'account_number': '0123456789',
    'clabe': '012345678901234567',
    'concept_prefix': 'Upgrade-Plan'
}

ADMIN_EMAIL = 'admin@tudominio.com'
SITE_URL = 'http://localhost:8000' if DEBUG else 'https://tudominio.com'

# Información de contacto de soporte
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '55 1234 5678')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'soporte@tuempresa.com')

# ========================================
# CONFIGURACIONES ESPECÍFICAS PARA AWS BEANSTALK
# ========================================

IS_AWS_ENVIRONMENT = os.environ.get('AWS_EXECUTION_ENV') is not None

if IS_AWS_ENVIRONMENT:
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
    
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION', 'us-east-1')
    AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
    AWS_SES_AUTO_THROTTLE = 0.5
    
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tudominio.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    
    if os.environ.get('REDIS_ENDPOINT'):
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"redis://{os.environ.get('REDIS_ENDPOINT')}:6379/1",
                'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
            }
        }
    
    HEALTH_CHECK_URL = '/health/'
    
    print("🚀 Configuración AWS Beanstalk activada")

else:
    print("🏠 Ejecutándose en ambiente local")

# Health check endpoint para AWS Beanstalk
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
