# Implementación Técnica – Módulo de Tareas

Este documento explica la arquitectura y los flujos internos del módulo de tareas (Tasks) y su tablero Kanban.

## Modelos clave

Ubicación: `arc_manager/apps/projects/models.py`

- `Task`: `phase`, `assigned_to`, `title`, `description`, `status` (`TODO | IN_PROGRESS | PAUSED | DONE`), `priority` (`LOW | MEDIUM | HIGH`), `due_date`, `created_at`.
- `Phase` y `Project`: estructura para agrupar y filtrar tareas por proyecto y fase.

## Vistas y URLs

Ubicación: `arc_manager/apps/projects/views.py` y `arc_manager/apps/projects/urls.py`

- Kanban y métricas
  - `GET /projects/<pk>/tasks/` → `project_kanban` (vista principal)
  - `GET /projects/<pk>/kanban/` → alias
  - `GET /projects/<pk>/statistics/` → `project_statistics` (JSON)
- Tareas (CRUD mínimo y acciones)
  - `POST /projects/<project_pk>/tasks/create/` → `task_create`
  - `GET|POST /projects/tasks/<pk>/edit/` → `task_edit` (GET = modal, POST = guarda; HTMX/JSON)
  - `POST /projects/tasks/<pk>/delete/` → `task_delete` (JSON)
  - `POST /projects/tasks/<task_pk>/update_status/` → `update_task_status` (JSON)
  - `POST /projects/tasks/<task_pk>/move/` → `move_task` (JSON)
- Listados
  - `GET /projects/tasks/` → `TaskListView`
  - `GET /projects/my-tasks/` → `MyTaskListView`

Seguridad: todas las vistas validan organización; POST con CSRF (el frontend envía `X-CSRFToken`).

## Plantillas y JavaScript

- Plantillas: `arc_manager/apps/projects/templates/projects/`
  - `kanban_board.html` (tablero y métricas)
  - `partials/task_edit_modal.html` (edición)
  - `task_detail_modal.html` (detalle)
- JavaScript: `arc_manager/static/js/kanban.js`
  - Drag & drop y actualización silenciosa de estado
  - Estadísticas en tiempo real desde `/projects/<id>/statistics/`
  - Modales de creación/edición y notificaciones

## Flujos clave

- Cambio de estado (drag & drop): POST a `/projects/tasks/{id}/update_status/`; si éxito, mover tarjeta en el DOM y actualizar contadores/estadísticas.
- Creación: POST a `/projects/<project_pk>/tasks/create/`; fallback de fase a la primera del proyecto o crea Backlog; valida `assigned_to` por organización.
- Edición: GET devuelve HTML del modal; POST actualiza campos; si `HX-Request` devuelve JSON mínimo para refrescar tarjeta.

## Rendimiento

- `prefetch_related('tasks__assigned_to')` en Kanban; `select_related` en listados.
- Cálculo inicial de métricas del proyecto para contadores.

## Extensiones previstas

- Filtros avanzados (prioridad/fechas), subtareas y dependencias, websockets para tiempo real.
