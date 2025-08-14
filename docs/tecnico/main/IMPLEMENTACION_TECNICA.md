# 🔧 Implementación Técnica — Módulo Main

## 📋 Tabla de Contenidos
1. Arquitectura y contexto
2. Modelos y Admin
3. Vistas/Controllers
4. URLConf y Middlewares relevantes
5. Templates y JavaScript
6. Management Commands
7. Seguridad
8. Performance
9. Logging
10. Testing sugerido
11. Troubleshooting
12. Métricas y mejoras futuras

---

## 1) 🏗️ Arquitectura y contexto

- El módulo Main actúa como agregador del dashboard autenticado. No define modelos propios; consulta `apps.projects` (Project/Task), `apps.orgs` (Client, Organization en `request.user.organization`) y `apps.plans` (Subscription) para lógica de redirección.
- Registro de app: `apps.py` define `MainConfig` con `name='apps.main'` y `label='main'`.

```12:18:arc_manager/apps/main/apps.py
class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.main'
    label = 'main'
```

---

## 2) 🗃️ Modelos y Admin

- `models.py`: sin modelos definidos en Main.
- `admin.py`: sin registros actualmente.

Implicación: cualquier dato mostrado en el dashboard proviene de otros módulos.

---

## 3) 🎮 Vistas/Controllers

Archivo: `apps/main/views.py`.

- `home(request)`
  - Autenticada. Renderiza `home.html` (template no presente en el repo al momento de esta documentación).

- `dashboard(request)`
  - `@login_required`.
  - Obtiene `organization` desde `request.user.organization`. Si no existe, retorna `error_page.html` con mensaje (template no presente actualmente).
  - Si `organization.subscription.is_expired`, redirige a `plans:subscription_dashboard`.
  - Contexto principal:
    - `my_tasks`: `Task` asignadas al usuario actual, excluye `status='DONE'`, orden por `due_date`, límite 3.
    - `active_projects`: `Project` de la organización con `status='ACTIVE'`, `select_related('client')`, `prefetch_related('phases__tasks')`, orden `-created_at`, límite 6.
    - `total_clients` y `recent_clients` por organización.
    - Alias `tasks` apunta a `my_tasks` (compatibilidad con template).

```12:71:arc_manager/apps/main/views.py
@login_required
def dashboard(request):
    ...
    my_tasks = Task.objects.filter(assigned_to=current_user).exclude(status='DONE').order_by('due_date')[:3]
    active_projects = Project.objects.filter(organization=organization, status='ACTIVE').select_related('client').prefetch_related('phases__tasks').order_by('-created_at')[:6]
    total_clients = Client.objects.filter(organization=organization).count()
    recent_clients = Client.objects.filter(organization=organization).order_by('-created_at')[:5]
    return render(request, 'dashboard.html', context)
```

Notas:
- El template del dashboard espera `recent_files`, que no es incluido en el contexto actual.
- `home()` no está enroutada desde `apps/main/urls.py`.

---

## 4) 🌐 URLConf y Middlewares relevantes

URLConf de Main:

```1:8:arc_manager/apps/main/urls.py
app_name = 'main'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
```

En `core/urls.py`:
- `'/'` redirige a `accounts:login` si no autenticado; si autenticado, a `main:dashboard`.
- `/health/` define un health check a nivel de proyecto.

Middlewares en `core/settings.py` que afectan este módulo:
- `apps.accounts.middleware.LoginRequiredMiddleware` (protege rutas no exentas).
- `apps.accounts.middleware.SuperuserRestrictMiddleware` (superusers se restringen al admin; el dashboard no debería ser accedido por ellos salvo bypass).
- `apps.orgs.middleware.OrganizationContextMiddleware` (contexto organizacional).
- `axes.middleware.AxesMiddleware` (seguridad de login), standard de Django y `ErrorHandlingMiddleware`.

---

## 5) 🖼️ Templates y JavaScript

- Template principal: `templates/dashboard.html`.
  - Usa `base.html` (navbar, sidebar, mensajes, modal global reutilizable, HTMX CSRF helper).
  - Widgets: proyectos activos, tareas del usuario y (placeholder) documentos recientes.
  - Dependencias: `static/css/dashboard.css`, `static/js/dashboard.js`.

```1:12:arc_manager/templates/dashboard.html
{% block extra_css %}
<link href="{% static 'css/dashboard.css' %}?v=34" rel="stylesheet">
{% endblock %}
...
{% block extra_js %}
<script src="{% static 'js/dashboard.js' %}?v=14"></script>
{% endblock %}
```

Observaciones en UI:
- Se referencian rutas `projects:project-create`, `projects:project-list`, `projects:project-detail`, `projects:my-task-list`.
- Avatares usan `task.assigned_to.profile.avatar` si existe; en caso contrario, inicial del nombre.

---

## 6) 🛠️ Management Commands

- `setup_database`
  - Verifica conexión DB, ejecuta `migrate` (`interactive=False`), crea superusuario desde `DJANGO_SUPERUSER_*`, luego `call_command('setup_mvp_plans')`.
  - Opción: `--force` para continuar a pesar de errores en pasos intermedios.

- `clean_data`
  - `@transaction.atomic`.
  - Elimina en orden: `UpgradeRequest`, `Payment`, `Subscription`, `Organization`, y usuarios no superuser.
  - Opción: `--yes`/`--no-input` para modo no interactivo.

- `diagnose_ses`
  - Verifica variables de entorno requeridas (`AWS_*`, `DEFAULT_FROM_EMAIL`), configuración de Django (`EMAIL_BACKEND`, `DEBUG`), conexión a SES y límites/cotas.
  - Opción: `--test-email you@example.com` para enviar un correo de prueba con `send_mail`.

Ejecución recomendada dentro del contenedor:

```
docker compose exec web python manage.py setup_database
docker compose exec web python manage.py clean_data --yes
docker compose exec web python manage.py diagnose_ses --test-email you@example.com
```

---

## 7) 🔐 Seguridad

- Autenticación obligatoria (decorator y middleware global).
- Acceso por organización: consultas filtradas por `request.user.organization`.
- Suscripción: redirección a dashboard de planes si expirada.
- CSRF: `base.html` incluye helper para solicitudes HTMX.

---

## 8) ⚡ Performance

- `active_projects`: `select_related('client')` + `prefetch_related('phases__tasks')` para minimizar consultas n+1.
- Límite de colecciones en dashboard: tareas (3), proyectos (6) para render rápido.
- Uso de Redis para sesiones y caché a nivel proyecto (config en settings).

Oportunidades:
- Cargar `recent_files` con `select_related('phase__project', 'uploaded_by')` desde `apps.files.ProjectFile` para evitar consultas extra en template.

---

## 9) 🧾 Logging

- Comandos utilizan `self.stdout.write` con estilos para estados, advertencias y errores.
- El proyecto define `LOGGING` con handlers para consola/archivos y `mail_admins` en producción.

---

## 10) 🧪 Testing sugerido

- Vistas
  - Dashboard autenticado responde 200.
  - Usuario sin `organization` obtiene la vista de error esperada.
  - Organización con `subscription.is_expired=True` redirige a `plans:subscription_dashboard`.
  - Contexto contiene `my_tasks` (máx. 3), `active_projects` (máx. 6), `total_clients` y `recent_clients`.

- Comandos
  - `setup_database` ejecuta migraciones y crea superusuario con variables.
  - `clean_data --yes` elimina objetos esperados y preserva superusers.
  - `diagnose_ses` maneja errores de credenciales y muestra mensajes adecuados.

---

## 11) 🛠️ Troubleshooting

- Templates faltantes: `home.html` y `error_page.html` no están en el repo; su ausencia causará 500 si se invocan.
- `recent_files` no poblado: el template lo itera; si no está en el contexto, mostrará estado vacío.
- Bucles de redirección: revisar `LOGIN_EXEMPT_URLS` y orden de middlewares en `settings.py`.
- Problemas con SES: usar `diagnose_ses` y verificar variables/credenciales/zona/región.

---

## 12) 📈 Métricas y mejoras futuras

- Métricas: tiempo de render del dashboard, número de queries, tamaño de contexto.
- Mejoras sugeridas:
  - Añadir `recent_files` desde `apps.files` al contexto del dashboard.
  - Cards con contadores agregados de tareas por estado a nivel de organización.
  - Health checks extendidos específicos del módulo (dependencias de DB/Redis/Email).
  - Tests de integración para redirecciones de suscripción y estados de UI.

