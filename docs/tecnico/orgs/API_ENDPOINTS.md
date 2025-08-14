# 🌐 API y Endpoints — Módulo Orgs

## 🛣️ URLs y Routing

```python
# apps/orgs/urls.py
app_name = 'orgs'
urlpatterns = [
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/new/', ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/edit/', ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('<int:pk>/', OrganizationDetailView.as_view(), name='organization_detail'),
    path('mi-organizacion/', my_organization, name='my_organization'),
]
```

Incluido en `core/urls.py` como `path('organizations/', include('apps.orgs.urls'))`.

---

## Endpoints y permisos

- GET `/organizations/clients/`
  - Autenticación requerida.
  - Lista clientes de la organización del usuario.
  - Respuesta: HTML (`orgs/client_list.html`).

- GET/POST `/organizations/clients/new/`
  - Autenticación requerida.
  - Crea `Client` asignado a `request.user.organization`.
  - Respuesta: HTML (`orgs/client_form.html`). Éxito redirige a `orgs:client_list`.

- GET `/organizations/clients/<pk>/`
  - Autenticación requerida.
  - `ClientOwnerMixin`: solo clientes de su organización.
  - Respuesta: HTML (`orgs/client_detail.html`) con `projects` relacionados.

- GET/POST `/organizations/clients/<pk>/edit/`
  - Autenticación requerida.
  - `ClientOwnerMixin` restringe acceso.
  - Respuesta: HTML (`orgs/client_form.html`).

- POST `/organizations/clients/<pk>/delete/`
  - Autenticación requerida.
  - `ClientOwnerMixin` restringe acceso.
  - Respuesta: Redirect a `orgs:client_list` con mensaje.

- GET `/organizations/<pk>/`
  - Autenticación requerida.
  - Ver detalles de una `Organization` propia; de lo contrario, redirige a `main:dashboard` con mensaje.
  - Respuesta: HTML (`orgs/my_organization.html`).

- GET `/organizations/mi-organizacion/`
  - Autenticación requerida.
  - Muestra información de la organización del usuario autenticado.
  - Respuesta: HTML (`orgs/my_organization.html`).

---

## Estados de UI y errores típicos

- 302 → Redirección a login si no autenticado.
- 403/redirect → Falta de permisos o acceso a entidad de otra organización.
- 200 → Render con mensajes de éxito/error mediante `messages`.

---

Arc Manager · Orgs · Última actualización: 2025-08-13


