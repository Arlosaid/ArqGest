# Implementación Técnica – Módulo de Fases

## Modelos

Ubicación: `arc_manager/apps/projects/models.py`

- `Phase`: `project`, `name`, `status (PENDING|IN_PROGRESS|COMPLETED)`, `order`, `start_date`, `end_date`, `notes`, `created_at`.
- `PhaseTemplate`: `name`, `description`, `organization`, `phases (JSON)`.

## Servicios

Ubicación: `arc_manager/apps/projects/services.py`

- `create_phases_for_project(project, creation_method, phase_template=None, phase_formset=None)`
  - `template`: itera `phase_template.phases` (lista de `{name, order}`) y crea `Phase`.
  - `manual`: usa `phase_formset` validado para construir `Phase`.
  - `fallback`: crea 5 fases por defecto (traducciones) con `order` incremental.
  - Se invoca en `ProjectCreateView.form_valid` tras guardar el `Project`.

## Formularios

Ubicación: `arc_manager/apps/projects/forms.py`

- `ProjectForm`: campo `phase_creation_method` (`template|manual`) y `phase_template` filtrado por organización.
- `PhaseFormSet` (`BasePhaseFormSet`): valida unicidad de nombres; relaja `name` si marcado `DELETE` al estar ligado; mantiene `order` vía `can_order`.
- `PhaseTemplateForm`: `name`, `description`.

## Vistas y URLs

Ubicación: `arc_manager/apps/projects/views.py` y `arc_manager/apps/projects/urls.py`

- Fase
  - `GET /projects/<project_pk>/phases/<pk>/` → `PhaseDetailView`
  - `POST /projects/<project_pk>/phases/create/` → `phase_create` (creación rápida)
- Plantillas de Fase
  - `GET /projects/templates/` → `PhaseTemplateListView`
  - `GET|POST /projects/templates/new/` → `PhaseTemplateCreateView`
  - `GET /projects/templates/<pk>/` → `PhaseTemplateDetailView`
  - `GET|POST /projects/templates/<pk>/edit/` → `PhaseTemplateUpdateView`
  - `GET|POST /projects/templates/<pk>/delete/` → `PhaseTemplateDeleteView`

Seguridad: todas las vistas restringidas por `organization` del usuario.

## Plantillas

- `projects/phase_detail.html`: detalle de fase con subida de archivos HTMX y edición de notas.
- `projects/phasetemplate_list.html`, `projects/phasetemplate_form.html`, `projects/phasetemplate_detail.html`.

## Consideraciones

- Orden de fases controlado por `order` (enteros crecientes).
- Las plantillas guardan fases como JSON y se expanden a `Phase` al crear proyectos.
- El detalle de fase ofrece gestión ligera (archivos, notas) y retorno al proyecto.
