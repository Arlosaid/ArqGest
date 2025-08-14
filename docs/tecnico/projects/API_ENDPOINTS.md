# 🌐 API y Endpoints - Módulo de Proyectos

## 📋 Tabla de Contenidos

1. URLs y Routing
2. Endpoints HTML (vistas)
3. Endpoints JSON (acciones Kanban/Tareas)
4. Parámetros y formatos
5. Autenticación y permisos
6. Códigos de error y respuestas comunes

---

## 🛣️ URLs y Routing

```python
# apps/projects/urls.py (extracto)
urlpatterns = [
    path('', ProjectListView.as_view(), name='project-list'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),

    # Kanban y estadísticas
    path('<int:pk>/tasks/', project_kanban, name='project-kanban'),
    path('<int:pk>/kanban/', project_kanban, name='project-kanban-alt'),
    path('<int:pk>/statistics/', project_statistics, name='project-statistics'),

    # Tareas
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('my-tasks/', MyTaskListView.as_view(), name='my-task-list'),
    path('tasks/<int:pk>/', task_detail, name='task-detail'),
    path('tasks/<int:pk>/edit/', task_edit, name='task-edit'),
    path('tasks/<int:pk>/delete/', task_delete, name='task-delete'),
    path('tasks/<int:task_pk>/update_status/', update_task_status, name='update-task-status'),
    path('tasks/<int:task_pk>/move/', move_task, name='task-move'),

    # Fases
    path('<int:project_pk>/phases/<int:pk>/', PhaseDetailView.as_view(), name='phase-detail'),
    path('<int:project_pk>/phases/create/', phase_create, name='phase-create'),

    # Crear tarea desde proyecto
    path('<int:project_pk>/tasks/create/', task_create, name='task-create'),

    # Plantillas de fases
    path('templates/', PhaseTemplateListView.as_view(), name='phasetemplate-list'),
    path('templates/new/', PhaseTemplateCreateView.as_view(), name='phasetemplate-create'),
    path('templates/<int:pk>/', PhaseTemplateDetailView.as_view(), name='phasetemplate-detail'),
    path('templates/<int:pk>/edit/', PhaseTemplateUpdateView.as_view(), name='phasetemplate-update'),
    path('templates/<int:pk>/delete/', PhaseTemplateDeleteView.as_view(), name='phasetemplate-delete'),
    path('kanban-selector/', ProjectKanbanSelectorView.as_view(), name='kanban-selector'),
]
```

---

## 🎯 Endpoints HTML (vistas)

- GET `/projects/` → Lista de proyectos por organización
- GET `/projects/new/` → Formulario de creación (elige plantilla o manual)
- GET `/projects/<id>/` → Detalle del proyecto (fases, archivos, centro de tareas)
- GET `/projects/<id>/tasks/` → Tablero Kanban del proyecto
- GET `/projects/tasks/` → Lista de tareas de la organización
- GET `/projects/my-tasks/` → Mis tareas asignadas
- GET `/projects/tasks/<id>/` → Detalle modal de tarea
- GET `/projects/tasks/<id>/edit/` → Modal de edición de tarea

---

## 🧩 Endpoints JSON (acciones)

### Actualizar estado de tarea

- POST `/projects/tasks/<task_id>/update_status/`
- Content-Type: `application/json` o `application/x-www-form-urlencoded`
- Body JSON: `{ "status": "TODO|IN_PROGRESS|PAUSED|DONE" }`
- Respuesta OK: `{ "success": true }`

### Mover tarea a otra fase

- POST `/projects/tasks/<task_id>/move/`
- Body JSON: `{ "phase_id": <int> }`
- Respuesta OK: `{ "success": true }`

### Crear tarea (desde Kanban)

- POST `/projects/<project_id>/tasks/create/`
- FormData: `title`, `description?`, `phase?`, `assigned_to?`, `priority?`, `due_date?`
- Respuesta JSON si `Accept: application/json`: `{ "success": true, "task_id": <int> }` o redirect HTML

### Eliminar tarea

- POST `/projects/tasks/<task_id>/delete/`
- Respuesta OK: `{ "success": true }`

### Estadísticas del proyecto

- GET `/projects/<project_id>/statistics/`
- Respuesta: `{ success, total_tasks, completed_tasks, in_progress_tasks, paused_tasks }`

---

## 📦 Parámetros y formatos

- Estados de `Task.status`: `TODO`, `IN_PROGRESS`, `PAUSED`, `DONE`
- Prioridades de `Task.priority`: `LOW`, `MEDIUM`, `HIGH`
- Fechas `YYYY-MM-DD`; entrada inválida se ignora en creación/edición
- CSRF requerido para POST; JS usa token desde input `csrfmiddlewaretoken`

---

## 🔐 Autenticación y permisos

- Todas las rutas requieren login
- Filtro por `organization` en consultas y access control
- Asignación de usuarios validada: deben pertenecer a la organización y ser activos (no superuser)

---

## ❌ Códigos de error comunes

- 302 Redirect a login si no autenticado
- 400 JSON: `{ success: false, error: '...' }` en validaciones fallidas
- 404 si proyecto/fase/tarea no pertenece a la organización

---

Última actualización: Diciembre 2024

