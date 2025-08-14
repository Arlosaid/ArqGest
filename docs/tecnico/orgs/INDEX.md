## 📚 Documentación del Módulo Orgs

### Documentos disponibles

- README.md — Descripción general y arquitectura
- IMPLEMENTACION_TECNICA.md — Detalle técnico profundo
- API_ENDPOINTS.md — URLs y flujos con ejemplos
- CHANGELOG.md — Historial de cambios

---

### 🚀 Inicio rápido por rol

- **Desarrolladores**
  - Verifica `apps.orgs` en `INSTALLED_APPS` y rutas incluidas en `core/urls.py` (`path('organizations/', include('apps.orgs.urls'))`).
  - Crea datos de ejemplo:
    - `docker compose exec web python manage.py setup_database`
    - `docker compose exec web python manage.py setup_demo_data --orgs 2 --users-per-org 3`
  - Abre `/organizations/clients/` para CRUD de clientes y `/organizations/mi-organizacion/` para el panel de organización.

- **Administradores**
  - Administra `Organization` y `Client` en `/admin/` con import/export.
  - Revisa estado de suscripción desde el admin con enlaces a `plans.Subscription`.

- **Soporte/QA**
  - Comando de limpieza y saneamiento multitenant:
    - `docker compose exec web python manage.py clean_tenant_data --all --yes`
  - Listado y diagnóstico de organizaciones/usuarios:
    - `docker compose exec web python manage.py list_orgs --detailed`

---

### 🏗️ Diagrama (alto nivel)

```mermaid
flowchart TD
  subgraph Orgs Models
    M1[Organization]
    M2[Client]
  end

  subgraph Plans
    P1[Subscription]
    P2[Plan]
  end

  subgraph Views
    V1[ClientListView]
    V2[ClientCreate/Update/Delete]
    V3[ClientDetailView]
    V4[my_organization/OrganizationDetailView]
  end

  subgraph Access
    MW[OrganizationContextMiddleware]
    D1[require_org_admin]
    D2[check_user_limit]
  end

  MW --> V1
  MW --> V4
  V1 --> M2
  V2 --> M2
  V3 --> M2
  V4 --> M1
  M1 <---> P1
  P1 --> P2
```

---

Arc Manager · Módulo Orgs


