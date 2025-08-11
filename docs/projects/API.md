# 📡 API - Módulo de Proyectos

## Kanban

### Actualización de estado (drag & drop)
- `POST /projects/tasks/<task_id>/update_status/`
- Body (JSON o form):
  - `status`: `TODO | IN_PROGRESS | PAUSED | DONE`
- Respuesta:
```json
{ "success": true }
```

### Crear tarea (modal)
- `POST /projects/<project_id>/tasks/create/`
- Body (form): `title`, `description?`, `phase`, `priority?`, `due_date?`, `assigned_to?`
- Respuesta (HTML o JSON según `Accept`):
```json
{ "success": true, "task_id": 123 }
```

### Estadísticas del proyecto
### Editar tarea (modal, HTMX)
- `POST /projects/tasks/<task_id>/edit/`
- Body (form): `title`, `description?`, `priority?`, `phase?`, `due_date?`, `assigned_to?`
- Respuesta (HTMX):
```json
{ "success": true, "task": { "id": 1, "title": "...", "assigned_to_name": "...", "phase_name": "..." } }
```

### Eliminar tarea
- `POST /projects/tasks/<task_id>/delete/`
- Respuesta:
```json
{ "success": true }
```
- `GET /projects/<project_id>/statistics/`
- Respuesta:
```json
{
  "total_tasks": 12,
  "completed_tasks": 4,
  "in_progress_tasks": 6,
  "paused_tasks": 2
}
```

## 🗂️ Archivos por Fase

- **Recurso**: archivos asociados a una `Phase` de un `Project`.
- **Modelo**: `apps.files.models.ProjectFile`
  - `id`: integer
  - `phase`: FK a `Phase`
  - `file`: archivo (media)
  - `uploaded_by`: usuario
  - `uploaded_at`: datetime
  - `filename` (propiedad): nombre base del archivo
  - `extension` (propiedad): extensión en mayúsculas (PDF, DWG, etc.)

### Subir archivo(s) a una fase
- **Ruta (name)**: `files:upload_file`
- **Método**: `POST` (multipart/form-data)
- **URL**: `/projects/<project_id>/phases/<phase_id>/files/upload/`
- **Auth**: requerido (el usuario debe pertenecer a la organización del proyecto)
- **Body**:
  - `files`: uno o varios archivos (`multiple`)

Ejemplo HTML simple:
```html
<form action="/projects/1/phases/2/files/upload/" method="post" enctype="multipart/form-data">
  <input type="file" name="files" multiple required>
  <button type="submit">Subir</button>
  <!-- Incluir CSRF en templates de Django -->
  {% csrf_token %}
  
</form>
```

Respuestas comunes:
- 200/302 con mensaje de éxito y recarga de lista de archivos (en templates)
- 400 si no se envían archivos
- 403 si el usuario no pertenece a la organización

### Eliminar archivo
- **Ruta (name)**: `files:delete_file`
- **Método**: `POST`
- **URL**: `/files/<file_id>/delete/`
- **Auth**: requerido

Respuestas comunes:
- 200/204 tras eliminar
- 403 si no tiene permisos
- 404 si no existe

## 🔎 Vistas relacionadas

### Detalle de Proyecto
- `apps.projects.views.ProjectDetailView`
  - Prefetch: `phases.tasks.assigned_to`, `phases.files`, `phases.files.uploaded_by`
  - Contexto: `phases`, `tasks`, `files`, `today`

### Kanban
- `apps.projects.views.project_kanban(request, pk)`

### Crear Fase
- `apps.projects.views.phase_create(request, project_pk)`

### Crear Tarea
- `apps.projects.views.task_create(request, project_pk)`

## 🧭 Plantillas clave
- `projects/project_detail.html`: tabs principales
- `projects/partials/_files_tab.html`: acordeón por fase (todas colapsadas por defecto), subida por fase y tabla moderna de archivos

## ⚠️ Notas
- No hay previsualización; se usan íconos por tipo y miniaturas solo para imágenes.
- Las rutas están incluidas en `core/urls.py` (incluye `apps.files.urls`).
- La pestaña activa puede forzarse con `?tab=` o `#hash` (details|phases|tasks|files).


