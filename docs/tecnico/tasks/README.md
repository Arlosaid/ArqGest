# Módulo de Tareas (Tasks) – ArcManager

## Propósito

Centralizar la gestión de tareas de los proyectos con un tablero Kanban como vista principal: crear, editar, mover, cambiar estado y eliminar tareas de forma visual y simple.

## Componentes principales

- Kanban por estado (`TODO`, `IN_PROGRESS`, `PAUSED`, `DONE`).
- Contadores y estadísticas del proyecto en tiempo real.
- Modales para creación y edición de tareas.
- Filtros por fase y utilidades de navegación.

## Flujo de usuario

1. Dashboard → Proyecto → pestaña Kanban.
2. Gestionar tareas visualmente (drag & drop, modales).
3. Ver progreso y estadísticas sin recargar la página.

## Arquitectura (alto nivel)

- Modelos: `Project`, `Phase`, `Task` en `arc_manager/apps/projects/models.py`.
- Vistas/Controladores en `arc_manager/apps/projects/views.py`:
  - `project_kanban`, `project_statistics`.
  - `task_create`, `task_edit`, `task_delete`.
  - `update_task_status`, `move_task`.
  - `TaskListView`, `MyTaskListView`.
- URLs en `arc_manager/apps/projects/urls.py`.
- Plantillas en `arc_manager/apps/projects/templates/projects/`:
  - `kanban_board.html`, `partials/task_edit_modal.html`, `task_detail_modal.html`.
- Frontend: `arc_manager/static/js/kanban.js` y estilos en `arc_manager/static/css/kanban.css` y `arc_manager/static/css/tasks.css` (si aplica).

## Archivos clave

- Backend
  - `arc_manager/apps/projects/models.py`
  - `arc_manager/apps/projects/views.py`
  - `arc_manager/apps/projects/urls.py`
- Frontend
  - `arc_manager/static/js/kanban.js`
  - `arc_manager/apps/projects/templates/projects/kanban_board.html`
  - `arc_manager/apps/projects/templates/projects/partials/task_edit_modal.html`
  - `arc_manager/apps/projects/templates/projects/task_detail_modal.html`

## Documentación relacionada

- `./IMPLEMENTACION_TECNICA.md`
- `./API_ENDPOINTS.md`
- `./FLUJO_OPTIMIZADO.md`
- `../projects/IMPLEMENTACION_TECNICA.md` (contexto del módulo de proyectos)


