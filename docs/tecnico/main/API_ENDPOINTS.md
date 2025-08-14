# 🌐 API y Endpoints — Módulo Main

## 🛣️ URLs y Routing

```python
# apps/main/urls.py
app_name = 'main'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
```

Relacionado en `core/urls.py`:

- `/` → redirect a `accounts:login` si no autenticado, o a `main:dashboard` si autenticado.
- `/health/` → health check (proyecto, fuera del módulo Main).

---

## Endpoints

- GET `/main/` (name: `main:dashboard`)
  - Autenticación: requerida.
  - Permisos: usuario con `organization` asociada. Si existe `subscription` y `is_expired`, se redirige a `plans:subscription_dashboard`.
  - Respuesta: HTML (`templates/dashboard.html`).
  - Contexto:
    - `my_tasks`: últimas 3 tareas no `DONE` asignadas al usuario.
    - `active_projects`: hasta 6 proyectos `status='ACTIVE'` de la organización.
    - `total_clients`, `recent_clients`.
    - Nota: el template contempla `recent_files`, aún no provisto por la vista.

---

## Ejemplos

Solicitud (autenticado):

```http
GET /main/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

Respuestas típicas:

- 200 OK — Render de `dashboard.html` con widgets.
- 302 Found — Redirección a `/accounts/login/` si no autenticado.
- 302 Found — Redirección a `plans:subscription_dashboard` si la suscripción está expirada.
- 200 OK — Render de `error_page.html` con mensaje si el usuario no tiene `organization` (template no incluido en el repo al momento de esta documentación).

---

## Estados de UI comunes

- Éxito: tablero con métricas y listas (tareas, proyectos, clientes).
- Sin permisos/autenticación: redirect a login.
- Suscripción expirada: redirect a panel de suscripción.
- Sin organización: vista de error amigable (depende de `error_page.html`).

---

Arc Manager · Main · Última actualización: 2025-08-13


