# 🔧 Implementación Técnica — Módulo Orgs

## 📋 Tabla de Contenidos
1. Arquitectura
2. Modelos y Admin
3. Vistas/Controllers
4. Formularios
5. Decoradores, Mixins y Middleware
6. URLConf
7. Templates/Frontend
8. Management Commands
9. Seguridad
10. Performance
11. Logging
12. Testing sugerido
13. Troubleshooting
14. Roadmap

---

## 1) 🏗️ Arquitectura

- Módulo de gestión multiorganización: `Organization` y `Client` como entidades principales.
- Integración con `plans.Subscription` (OneToOne en `Organization`) para límites y estado.
- Acceso por organización mediante mixins y decoradores; middleware inyecta contexto.

---

## 2) 🗃️ Modelos y Admin

Archivo: `apps/orgs/models.py`

- `Organization`
  - Campos: `name`, `description`, `is_active`, `created_at`, `updated_at`.
  - Helpers: `get_max_users()`, `get_user_count()`, `get_admins()`, `get_subscription()`, `is_subscription_active()`, `can_add_user()`, `can_add_user_detailed()` y utilidades de estado/alertas de suscripción.
  - Relación con `plans.Subscription` (OneToOne inversa `organization.subscription`).

- `Client`
  - FK a `Organization`, `unique_together = ('organization', 'name')`.

Admin (`apps/orgs/admin.py`):

- `OrganizationAdmin(ImportExportModelAdmin)`
  - `list_display`: `user_count`, `get_subscription_status`, `get_subscription_link`.
  - `get_queryset()` con `prefetch_related('subscription__plan')` y anotaciones de conteo.
  - Acciones: activar/desactivar organizaciones.

- `ClientAdmin(ImportExportModelAdmin)` con `select_related('organization')`.

Snippets:

```24:33:arc_manager/apps/orgs/admin.py
@admin.register(Organization)
class OrganizationAdmin(ImportExportModelAdmin):
    list_display = ['name', 'is_active', 'user_count', 'get_subscription_status', 'get_subscription_link', 'created_at']
```

---

## 3) 🎮 Vistas/Controllers

Archivo: `apps/orgs/views.py`.

- Clientes (List/Detail/Create/Update/Delete) restringidos por `ClientOwnerMixin` y `request.user.organization`.
- Organización
  - `my_organization`: muestra usuarios, admins y métricas de capacidad.
  - `OrganizationDetailView`: asegura pertenencia; de lo contrario redirige al dashboard.

```92:106:arc_manager/apps/orgs/views.py
@login_required
def my_organization(request):
    if not request.user.organization:
        return redirect('main:dashboard')
    organization = request.user.organization
    return render(request, 'orgs/my_organization.html', {...})
```

---

## 4) 📝 Formularios

Archivo: `apps/orgs/forms.py`.

- `ClientForm` con `crispy_forms`.
- `OrganizationForm` crea `Subscription` automáticamente al guardar (campo `initial_plan` requerido al crear):

```90:107:arc_manager/apps/orgs/forms.py
def save(self, commit=True):
    instance = super().save(commit=False)
    if commit:
        instance.save()
        if not hasattr(instance, 'subscription'):
            Subscription.objects.create(organization=instance, plan=initial_plan)
    return instance
```

---

## 5) 🧱 Decoradores, Mixins y Middleware

- Decoradores (`apps/orgs/decorators.py`):
  - `check_user_limit`: bloquea creación cuando se supera `max_users` (JSON o redirect con mensaje).
  - `require_org_admin`: exige `is_org_admin`; 403 JSON o `PermissionDenied`.
  - `require_active_subscription`: redirige a `plans:subscription_dashboard` si la suscripción no está activa.
  - `require_plan_feature(feature)`: exige feature en el plan; JSON 403 o redirect con mensaje.

- Mixins (`apps/orgs/mixins.py`):
  - `OrganizationAdminMixin`: fuerza admin de org.
  - `ClientOwnerMixin`: verifica pertenencia del `Client` a la organización del usuario.

- Middleware (`apps/orgs/middleware.py`):
  - `OrganizationContextMiddleware`: agrega `request.organization` y `request.subscription` para usuarios autenticados no superuser.

---

## 6) 🌐 URLConf

```1:26:arc_manager/apps/orgs/urls.py
urlpatterns = [
  path('clients/', ...),
  path('clients/new/', ...),
  path('clients/<int:pk>/', ...),
  path('clients/<int:pk>/edit/', ...),
  path('clients/<int:pk>/delete/', ...),
  path('<int:pk>/', OrganizationDetailView.as_view(), name='organization_detail'),
  path('mi-organizacion/', my_organization, name='my_organization'),
]
```

---

## 7) 🎨 Templates/Frontend

- `orgs/client_list.html`, `client_form.html`, `client_detail.html`, `client_confirm_delete.html`.
- Vista de organización: `templates/orgs/my_organization.html` (también existe `templates/orgs/my_organization.html` a nivel proyecto).
- Estilos sugeridos: `static/css/organization_management.css`, `static/css/client_management.css`.

---

## 8) 🛠️ Management Commands

- `clean_tenant_data`:
  - Opciones: `--dry-run`, `--fix-usernames`, `--create_subscriptions`, `--deactivate_orphaned`, `--remove_admin_flags`, `--all`, `--yes`.
  - Sanea inconsistencias comunes (usernames, suscripciones por defecto, usuarios huérfanos, flags admin sin org).

- `create_organization`:
  - Argumentos: `name`, `--description`, `--max-users` (no usado en el modelo simplificado), `--inactive`.

- `create_user`:
  - Argumentos: `email`, `--name`, `--password`, `--org-slug`, `--org-id`, `--admin`, `--superuser`, `--inactive`.
  - Respeta límites de `Organization.can_add_user_detailed()` para usuarios activos no superuser.

- `list_orgs`:
  - Argumentos: `--detailed`, `--org-slug`, `--users-only`.

- `setup_demo_data`:
  - Argumentos: `--reset`, `--orgs`, `--users-per-org`.

Nota: algunos comandos aceptan `--org-slug`, pero en el modelo simplificado actual `Organization` no define el campo `slug`; usa `--org-id` para seleccionar la organización.

Ejecución recomendada (Docker):

```
docker compose exec web python manage.py clean_tenant_data --all --yes
docker compose exec web python manage.py create_organization "Acme" --description "Demo"
docker compose exec web python manage.py create_user john@acme.demo --org-id 1 --admin --password demo123
docker compose exec web python manage.py list_orgs --detailed
docker compose exec web python manage.py setup_demo_data --orgs 2 --users-per-org 3
```

---

## 9) 🔐 Seguridad

- Control de acceso por organización en todas las vistas de clientes.
- Verificación de límites de plan al crear usuarios.
- Superusuarios exentos en decoradores de plan, pero limitados a `/admin/` por middleware global.

---

## 10) ⚡ Performance

- Admin de `Organization` con `prefetch_related` y anotaciones.
- Uso de `cache_utils.py` para cachear datasets por organización y permisos.

Oportunidades:
- Cachear listados de clientes por organización si crecen.
- Invalidación selectiva usando `delete_pattern` en operaciones críticas.

---

## 11) 🧾 Logging

- Comandos reportan acciones vía `self.stdout` y estilos; el proyecto define `LOGGING` con handlers de archivo y consola.

---

## 12) 🧪 Testing sugerido

- Vistas de clientes: acceso, creación/edición/eliminación restringidos por organización.
- `ClientOwnerMixin`: acceso denegado entre organizaciones.
- `OrganizationForm`: crea `Subscription` cuando no existe.
- Decoradores: `check_user_limit` bloquea POST y retorna JSON 400 en AJAX.
- Middleware: `OrganizationContextMiddleware` setea `request.organization` y `request.subscription`.
- Comandos: caminos felices y flags de dry-run.

---

## 13) 🛠️ Troubleshooting

- Acceso denegado en clientes: validar `ClientOwnerMixin` y pertenencia de usuario.
- Límite de usuarios alcanzado: revisar `Plan.max_users` y estado de `Subscription`.
- Suscripción ausente: `OrganizationForm` la crea al guardar; `clean_tenant_data --create-subscriptions` también ayuda.

---

## 14) 🗺️ Roadmap

- Slug y dominios por organización; selector de contexto multi-org para superusuarios.
- Métricas de organización cacheadas en dashboard de Admin.
- Señales para invalidar cache de organización al crear/editar clientes o usuarios.

