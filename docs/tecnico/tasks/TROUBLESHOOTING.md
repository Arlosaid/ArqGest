# Troubleshooting — Módulo de Tareas

## Problemas comunes y soluciones

- No se actualiza el estado al arrastrar en Kanban
  - Verifica el token CSRF en el DOM y cabecera `X-CSRFToken` en `static/js/kanban.js`.
  - Revisa que el endpoint `/projects/tasks/<id>/update_status/` responda `{ success: true }`.

- Error "invalid_assignee" al crear/editar
  - El usuario asignado no pertenece a la organización del proyecto. Selecciona un miembro válido.

- Modal de edición no carga
  - Comprueba la ruta `GET /projects/tasks/<id>/edit/` y la inclusión del HTML en `#taskModalContent`.

- Contadores no cambian tras mover tarjeta
  - Asegúrate de usar `updateTaskStatusSilently` que llama a `moveCardVisually` y `updateStatisticsSilently`.

- No aparecen tareas en Kanban
  - Verifica filtro de fase (`phase_id`) en la URL y que existan tareas con `phase__project=<proyecto>`.

## Diagnóstico rápido

1. Abre DevTools → Network y filtra por `/projects/tasks/`.
2. Verifica códigos 200/204 en `update_status` y `move`.
3. Revisa consola por errores JS.
4. Valida permisos de organización en el backend (`views.update_task_status`).

## Recursos

- `docs/tecnico/tasks/API_ENDPOINTS.md`
- `arc_manager/static/js/kanban.js`
- `arc_manager/apps/projects/views.py`
