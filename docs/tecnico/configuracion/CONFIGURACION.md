# ⚙️ Configuración — Django Settings y Entorno

Guía completa para configurar ArcManager en local (Docker), staging y producción (AWS). Incluye variables de entorno, servicios (DB/Redis), seguridad, email, sesiones, logging y despliegue.

---

## 1) Variables de Entorno (.env)

```
# App
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Base de datos (si usas docker-compose)
POSTGRES_DB=arc_manager_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_PORT=5432
WEB_PORT=8000

# Conexión DB para Django
DATABASE_URL=postgresql://postgres:postgres123@db:5432/arc_manager_dev

# Redis (opcional pero recomendado)
REDIS_URL=redis://redis:6379/0
REDIS_PORT=6379

# Email (Amazon SES en producción)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SES_REGION=us-east-1
AWS_SES_CONFIGURATION_SET=
DEFAULT_FROM_EMAIL=noreply@tudominio.com

# Flags de entorno
PRODUCTION=
AWS_EXECUTION_ENV=
```

Consejos:
- Mantén `SECRET_KEY` fuera del repositorio.
- Usa `DATABASE_URL` como fuente única de verdad para la base de datos.

---

## 2) Aplicaciones Instaladas (INSTALLED_APPS)
- Django core: admin, auth, sessions, staticfiles, humanize.
- Terceros: `debug_toolbar` (solo DEBUG), `axes`, `crispy_forms`, `crispy_bootstrap5`, `import_export`.
- Locales: `core`, `apps.accounts`, `apps.main`, `apps.orgs`, `apps.users`, `apps.plans`, `apps.projects`, `apps.files`.

---

## 3) Middleware (orden recomendado)
1. `django.middleware.security.SecurityMiddleware`
2. `whitenoise.middleware.WhiteNoiseMiddleware`
3. `django.contrib.sessions.middleware.SessionMiddleware`
4. `django.middleware.common.CommonMiddleware`
5. `django.middleware.csrf.CsrfViewMiddleware`
6. `django.contrib.auth.middleware.AuthenticationMiddleware`
7. `django.contrib.messages.middleware.MessageMiddleware`
8. `django.middleware.clickjacking.XFrameOptionsMiddleware`
9. `axes.middleware.AxesMiddleware`
10. `apps.accounts.middleware.LoginRequiredMiddleware`
11. `apps.accounts.middleware.SuperuserRestrictMiddleware`
12. `apps.orgs.middleware.OrganizationContextMiddleware`
13. `apps.accounts.middleware.ErrorHandlingMiddleware`

Nota: `debug_toolbar.middleware.DebugToolbarMiddleware` se inserta primero solo si `DEBUG=True`.

---

## 4) Bases de Datos, Caché y Sesiones
- Base de datos via `dj_database_url.parse(DATABASE_URL)` (SQLite por defecto en local sin Docker).
- Caché Redis (`REDIS_URL`), con alias `default` y `sessions`.
- Sesiones en cache: `SESSION_ENGINE='django.contrib.sessions.backends.cache'` y `SESSION_CACHE_ALIAS='sessions'`.

Recomendaciones:
- En producción, usa Redis gestionado (ElastiCache) y habilita `SESSION_COOKIE_SECURE=True`.

---

## 5) Archivos Estáticos y Medios
- `STATIC_URL=/static/`, `STATIC_ROOT=staticfiles`, `STATICFILES_DIRS=['static']`.
- WhiteNoise para servir estáticos en contenedores: `CompressedManifestStaticFilesStorage`.
- Medios en `MEDIA_ROOT=media`, `MEDIA_URL=/media/`.

---

## 6) Seguridad
- `DEBUG=False` en producción.
- `ALLOWED_HOSTS` configurado apropiadamente.
- En AWS: `SECURE_SSL_REDIRECT=True`, `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')`, cookies seguras.
- `django-axes` para limitar intentos de login.

---

## 7) Email
- Local: `EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'`.
- Producción: `django_ses.SESBackend` con credenciales y región.
- `DEFAULT_FROM_EMAIL` configurable por entorno.

---

## 8) Logging
- Formateadores `verbose` y `simple`.
- Handlers: consola (dev/prod), archivos rotativos `logs/debug.log`, `logs/errors.log`, `logs/security.log`.
- En AWS se agrega handler a CloudWatch (StreamHandler).
- Logger raíz con nivel WARNING y `django.request` con email a admins en errores.

---

## 9) Docker (Desarrollo)
Comandos básicos:
```
docker-compose up -d --build
docker-compose logs -f web | cat
docker-compose exec web python manage.py migrate | cat
docker-compose exec web python manage.py createsuperuser --noinput | cat
```

Credenciales y puertos:
- App en `http://localhost:${WEB_PORT:-8000}`
- Postgres en `localhost:${POSTGRES_PORT:-5432}`
- Redis en `localhost:${REDIS_PORT:-6379}`

---

## 10) Despliegue (Producción / AWS Beanstalk)
- Variables de entorno en la plataforma (SECRET_KEY, DATABASE_URL, AWS_SES, REDIS_ENDPOINT, DEFAULT_FROM_EMAIL, etc.).
- Seguridad activada por `AWS_EXECUTION_ENV` (SSL redirect, cookies seguras, logging a CloudWatch).
- Redis gestionado (si existe `REDIS_ENDPOINT`, se reconfigura `CACHES`).
- Healthcheck en `/health/` definido en settings.

Checklist rápido:
- DEBUG desactivado, SECRET_KEY seguro, ALLOWED_HOSTS.
- Base de datos gestionada y accesible (RDS o similar).
- Email SES validado y `DEFAULT_FROM_EMAIL` configurado.
- Archivos estáticos colectados si usas un servidor WSGI (o WhiteNoise).

---

## 11) Comandos de gestión útiles
```
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 12) Problemas comunes
- Bucle de login: revisa `LOGIN_EXEMPT_URLS` y orden de middleware.
- Correo de reset no llega: verifica backend de email y credenciales; en local va a la consola.
- Redis inaccesible: ajusta `REDIS_URL` o `REDIS_ENDPOINT` y verifica firewall.

