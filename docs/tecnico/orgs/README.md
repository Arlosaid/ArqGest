## 🏢 Módulo Orgs — Descripción General

El módulo Orgs gestiona organizaciones y sus clientes. Provee vistas CRUD de `Client`, vistas de detalle de `Organization`, middleware de contexto organizacional y comandos de utilidad para mantenimiento, creación de demo data y diagnóstico multitenant.

---

## 📁 Estructura de Archivos

```
arc_manager/apps/orgs/
├── admin.py                      # Admin de Organization y Client con import/export
├── apps.py                       # AppConfig ('apps.orgs')
├── cache_utils.py                # Helpers de caché por organización y permisos
├── decorators.py                 # Decoradores: require_org_admin, check_user_limit, etc.
├── forms.py                      # ClientForm, OrganizationForm (crea Subscription al guardar)
├── management/commands/
│   ├── clean_tenant_data.py     # Limpieza y saneamiento multitenant
│   ├── create_organization.py   # Crear Organization
│   ├── create_user.py           # Crear usuario asignado a Organization
│   ├── list_orgs.py             # Listar organizaciones y usuarios
│   └── setup_demo_data.py       # Crear datos de ejemplo
├── middleware.py                 # OrganizationContextMiddleware
├── mixins.py                     # OrganizationAdminMixin, ClientOwnerMixin
├── models.py                     # Organization, Client
├── templates/orgs/              # Templates de clientes y organización
├── urls.py                       # Rutas /organizations/
└── views.py                      # Vistas CRUD y de organización
```

---

## 🔗 Relación con otros módulos

- `apps.accounts`: `User.organization` y `is_org_admin` controlan acceso; constraints validan pertenencia.
- `apps.plans`: `Organization.subscription` (OneToOne) y `Plan` determinan límites (`max_users`), estados y redirecciones.
- `apps.projects`: vistas de clientes muestran proyectos asociados (`client.projects`).

---

## 🧭 Flujos principales

- Gestión de clientes:
  - Lista, creación, edición, eliminación restringidos a la `organization` del usuario.
  - `ClientOwnerMixin` impide acceso entre organizaciones.

- Panel de organización:
  - `my_organization` muestra usuarios, admins, y porcentaje de uso vs `get_max_users()`.

- Contexto global:
  - `OrganizationContextMiddleware` inyecta `request.organization` y `request.subscription` para vistas.

---

## ⚙️ Requisitos y dependencias

- `INSTALLED_APPS` incluye `apps.orgs` y `apps.plans` (para suscripciones iniciales desde `OrganizationForm`).
- Middlewares globales de acceso y contexto (ver `core/settings.py`).
- Redis configurado para caché y sesiones (aprovechado en `cache_utils.py`).

- Ejecución de comandos (Docker):
  - `docker compose exec web python manage.py create_organization "Acme" --description "Demo"`
  - `docker compose exec web python manage.py create_user john@acme.demo --org-id 1 --admin --password demo123`
  - `docker compose exec web python manage.py setup_demo_data --orgs 2 --users-per-org 3`
  - `docker compose exec web python manage.py list_orgs --detailed`
  - `docker compose exec web python manage.py clean_tenant_data --all --yes`

---

Arc Manager · Módulo Orgs


