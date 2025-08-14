# API y Endpoints – Módulo de Tareas

Documenta los endpoints actuales usados por el Kanban y la gestión de tareas. Requiere usuario autenticado y pertenencia a la organización del proyecto.

## Kanban y métricas

- `GET /projects/<pk>/tasks/`
  - Vista: `projects:project-kanban`
  - Renderiza tablero Kanban del proyecto.
- `GET /projects/<pk>/statistics/`
  - Vista: `projects:project-statistics`
  - Respuesta: `{ success, total_tasks, completed_tasks, in_progress_tasks, paused_tasks }`

## Tareas – CRUD y acciones

- `POST /projects/<project_pk>/tasks/create/`
  - Crea tarea en el proyecto. Requiere `title`; `phase` opcional (usa primera o crea Backlog).
  - Respuesta: HTML (redirect) o JSON `{ success, task_id }` si `Accept: application/json`.
- `GET /projects/tasks/<pk>/edit/`
  - Devuelve HTML del modal de edición.
- `POST /projects/tasks/<pk>/edit/`
  - Actualiza campos básicos; valida `assigned_to` por organización; puede mover de fase.
  - Respuesta: redirect o JSON mínimo si `HX-Request`.
- `POST /projects/tasks/<pk>/delete/`
  - Elimina la tarea. Respuesta JSON `{ success: true }`.
- `POST /projects/tasks/<task_pk>/update_status/`
  - Cambia el estado. Cuerpo: `{ status }` (JSON o form). Respuesta JSON `{ success }`.
- `POST /projects/tasks/<task_pk>/move/`
  - Mueve a otra fase. Cuerpo: `{ phase_id }`. Respuesta JSON `{ success }`.

## Listados

- `GET /projects/tasks/` → Listado global (`TaskListView`)
- `GET /projects/my-tasks/` → Mis tareas (`MyTaskListView`)

## Errores comunes

- `400 invalid_assignee` en creación/edición si el usuario asignado no pertenece a la organización.
- `404` cuando el recurso no pertenece a la organización del usuario autenticado.

## Autenticación y CSRF

- Requiere sesión autenticada.
- En POST desde JS, incluir cabecera `X-CSRFToken`.
