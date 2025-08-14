## 🏠 Módulo Main — Descripción General

El módulo Main provee el punto de entrada autenticado de la aplicación (dashboard principal) y utilidades de mantenimiento a través de comandos de management. No define modelos propios; orquesta datos de `projects`, `orgs`, `plans` y `accounts` para mostrar un resumen operativo al usuario.

---

## 📁 Estructura de Archivos

```
arc_manager/apps/main/
├── admin.py                      # Registro en admin (vacío por ahora)
├── apps.py                       # AppConfig ('apps.main')
├── management/
│   └── commands/
│       ├── clean_data.py         # Limpieza total de datos de prueba
│       ├── diagnose_ses.py       # Diagnóstico de Amazon SES
│       └── setup_database.py     # Setup de DB: migraciones, superusuario, planes
├── models.py                     # Sin modelos en este módulo
├── urls.py                       # Ruta base del dashboard: '' → views.dashboard
└── views.py                      # Vistas: home (no enroutada), dashboard
```

UI asociada:

- Template: `templates/dashboard.html` (usa bloques `extra_css`/`extra_js`)
- JS: `static/js/dashboard.js`
- CSS: `static/css/dashboard.css`

---

## 🔗 Relación con otros módulos

- `apps.projects`: consulta `Project`, `Task` y sus relaciones para widgets de proyectos y tareas.
- `apps.orgs`: consulta `Client` y utiliza `request.user.organization` del contexto organizacional.
- `apps.plans`: valida `organization.subscription.is_expired` para redirigir a `plans:subscription_dashboard`.
- `apps.accounts`: autenticación y middlewares de acceso global.

---

## 🧭 Flujos principales

- Dashboard (`GET /main/` → `views.dashboard`):
  - Requiere usuario autenticado y con `organization`.
  - Redirige a `plans:subscription_dashboard` si la suscripción está expirada.
  - Contexto: `my_tasks` (3 pendientes asignadas), `active_projects` (6 más recientes, `status='ACTIVE'`, `select_related('client')`, `prefetch_related('phases__tasks')`), `total_clients`, `recent_clients`.
  - El template contempla `recent_files`, aún no poblado por la vista.

- Comandos de mantenimiento:
  - `setup_database`: migra, crea superusuario desde variables de entorno y ejecuta `setup_mvp_plans`.
  - `clean_data`: borra organizaciones, suscripciones, pagos, solicitudes de upgrade y usuarios no superuser.
  - `diagnose_ses`: valida variables, configuración de Django, conexión y límites de Amazon SES; puede enviar correo de prueba.

---

## ⚙️ Requisitos y dependencias

- Configuración en `core/settings.py`:
  - `INSTALLED_APPS` incluye `apps.main`.
  - Middlewares relevantes: `LoginRequiredMiddleware`, `OrganizationContextMiddleware`, `ErrorHandlingMiddleware`, `AxesMiddleware` y standard de Django.
  - Sesiones y caché por Redis configuradas; Debug Toolbar opcional en `DEBUG`.
  - Email: `django_ses.SESBackend` en producción; variables `AWS_*` y `DEFAULT_FROM_EMAIL`.

- Variables de entorno usadas por comandos:
  - `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_FIRST_NAME`, `DJANGO_SUPERUSER_LAST_NAME` (setup de superusuario).
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SES_REGION`, `DEFAULT_FROM_EMAIL` (diagnóstico SES).

- Ejecución de comandos (dentro del contenedor):
  - `docker compose exec web python manage.py setup_database`
  - `docker compose exec web python manage.py clean_data --yes`
  - `docker compose exec web python manage.py diagnose_ses --test-email you@example.com`

---

Arc Manager · Módulo Main


