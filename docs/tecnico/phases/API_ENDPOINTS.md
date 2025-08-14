# API y Endpoints – Módulo de Fases

Requiere autenticación; acceso restringido por `organization`.

## Fases

- `GET /projects/<project_pk>/phases/<pk>/`
  - Vista: `projects:phase-detail`
  - Renderiza detalle de fase (archivos, notas).
- `POST /projects/<project_pk>/phases/create/`
  - Vista: `projects:phase-create`
  - Crea una fase rápida para el proyecto actual. Campos: `name`, `notes` (opcional), `order` (opcional).
  - Respuesta: redirect con mensajes flash.

## Plantillas de Fase

- `GET /projects/templates/` → `projects:phasetemplate-list`
- `GET|POST /projects/templates/new/` → `projects:phasetemplate-create`
- `GET /projects/templates/<pk>/` → `projects:phasetemplate-detail`
- `GET|POST /projects/templates/<pk>/edit/` → `projects:phasetemplate-update`
- `GET|POST /projects/templates/<pk>/delete/` → `projects:phasetemplate-delete`

## Notas

- `ProjectForm` expone `phase_creation_method` y `phase_template` para la creación inicial de fases.
- El servicio `create_phases_for_project` expande plantillas (`phases` JSON) al crear proyectos.
