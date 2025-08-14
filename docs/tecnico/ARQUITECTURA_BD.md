# 🗄️ Arquitectura de Base de Datos — ArcManager

Este documento describe las tablas principales, relaciones y decisiones de modelado. Incluye un diagrama ER (Mermaid) y artefactos para visualizar en herramientas externas (DBML y PlantUML).

## Diagrama ER (Mermaid)

```mermaid
erDiagram
  Organization ||--o{ User : has
  Organization ||--o{ Client : has
  Organization ||--o{ Project : has
  Organization ||--|| Subscription : has
  Subscription }o--|| Plan : uses
  Subscription ||--o{ Payment : records
  Organization ||--o{ PhaseTemplate : has

  Project ||--o{ Phase : has
  Phase ||--o{ Task : has
  Phase ||--o{ ProjectFile : has
  User ||--o{ Project : owns
  User ||--o{ Task : assigned_to
  Client ||--o{ Project : requested_by

  Organization {
    int id PK
    string name
    text description
    bool is_active
    datetime created_at
    datetime updated_at
  }

  User {
    int id PK
    string email UK
    string username
    string first_name
    string last_name
    bool is_org_admin
    int organization_id FK
  }

  Client {
    int id PK
    int organization_id FK
    string name
    string email
    string phone_number
    text address
    bool is_active
    datetime created_at
    datetime updated_at
  }

  Plan {
    int id PK
    string name
    string display_name
    text description
    decimal price
    int max_users
    int trial_days
    int billing_cycle_days
    int grace_period_days
    bool is_active
    datetime created_at
    datetime updated_at
  }

  Subscription {
    int id PK
    int organization_id FK
    int plan_id FK
    datetime start_date
    datetime end_date
    datetime grace_end_date
    string subscription_status
    datetime created_at
    datetime updated_at
  }

  Payment {
    int id PK
    int subscription_id FK
    decimal amount
    string payment_method
    string payment_type
    string status
    string processed_by
    text description
    int days_added
    datetime old_end_date
    datetime new_end_date
    datetime created_at
  }

  UpgradeRequest {
    int id PK
    int organization_id FK
    int current_plan_id FK
    int requested_plan_id FK
    decimal amount
    string status
    string approved_by
    datetime created_at
    datetime updated_at
  }

  Project {
    int id PK
    int organization_id FK
    int owner_id FK
    int client_id FK
    string name
    string status
    date start_date
    date end_date
    datetime created_at
  }

  PhaseTemplate {
    int id PK
    int organization_id FK
    string name
    text description
    json phases
  }

  Phase {
    int id PK
    int project_id FK
    string name
    string status
    int order
    date start_date
    date end_date
    text notes
    datetime created_at
  }

  Task {
    int id PK
    int phase_id FK
    int assigned_to_id FK
    string title
    text description
    string status
    string priority
    date due_date
    datetime created_at
  }

  ProjectFile {
    int id PK
    int phase_id FK
    string file
    int uploaded_by_id FK
    datetime uploaded_at
  }
```

## Explicación del modelo
- Multiorganización: `Organization` es el núcleo. Todas las entidades de negocio (`User`, `Client`, `Project`, `PhaseTemplate`, `Subscription`) referencian a la organización.
- Suscripciones: `Subscription` es 1:1 con `Organization` y referencia `Plan`. `Payment` guarda transacciones ligadas a la suscripción.
- Proyectos: `Project` pertenece a `Organization`, puede tener `owner` (usuario) y `client` opcional. Un proyecto tiene múltiples `Phase`, y cada `Phase` contiene `Task` y `ProjectFile`.
- Tareas: `Task` puede asignarse a un `User` (nullable) y está indexada por `status`, `priority`, `due_date`.
- Archivos: `ProjectFile` pertenece a `Phase` y guarda metadatos de subida.

Cardinalidades destacadas
- Organization→Subscription: 1:1 (única suscripción activa por organización).
- Organization→Project/Client/User/PhaseTemplate: 1:N.
- Project→Phase: 1:N; Phase→Task/ProjectFile: 1:N.
- Subscription→Payment: 1:N.

Políticas de borrado (resumen)
- `CASCADE`: `Project`→`Phase`→`Task/ProjectFile`, `Organization`→`Project/Client/PhaseTemplate/Subscription`.
- `SET_NULL`: `Project.owner`, `Task.assigned_to`, `Project.client`.
- `PROTECT`: `Subscription.plan`, `UpgradeRequest.(current_plan, requested_plan)`.

Índices y unicidad
- `User.email` único.
- `Client (organization, name)` único.
- `Project.status`, `Phase.status`, `Task.status/priority/due_date` indexados.
- `Subscription (subscription_status, end_date)` indexados.

## Visualización en programas externos

- Archivo DBML: `docs/tecnico/er/arcmanager.dbml`
  - Úsalo en `dbdiagram.io` (importar DBML) o en `https://dbdiagram.io` → Import → DBML.
  - También compatible con herramientas como `dbdocs`/`dbml-render`.

- Archivo PlantUML: `docs/tecnico/er/arcmanager.puml`
  - Visualízalo con el plugin de PlantUML (VSCode/IntelliJ) o con el jar de PlantUML.

Pasos rápidos
1) dbdiagram.io → Import → `arcmanager.dbml` → Render automático.
2) PlantUML: abre `arcmanager.puml` en un editor con soporte PlantUML y renderiza.

## Notas de implementación
- Nombres de tablas en inglés para consistencia.
- Revisa `settings.py` para `MEDIA_*` y `STATIC_*` en serving de archivos.
- Para producción, considerar S3 para `ProjectFile` y políticas de retención.
