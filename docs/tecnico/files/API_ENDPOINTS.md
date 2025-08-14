# 🌐 API y Endpoints — Módulo Files

## 🛣️ URLs y Routing

```python
# apps/files/urls.py
urlpatterns = [
    path('projects/<int:project_id>/phases/<int:phase_id>/files/upload/', views.upload_file, name='upload_file'),
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
]
```

---

## Endpoints

- POST `/projects/<project_id>/phases/<phase_id>/files/upload/` (name: `files:upload_file`)
  - Requiere login.
  - Requiere que `request.user.organization == phase.project.organization`.
  - Request: `multipart/form-data`, campo `files` (multiple).
  - Respuesta:
    - Si `HX-Request: true`: HTML parcial de `projects/partials/file_list.html` con los archivos actualizados de la fase.
    - Si no es HTMX: redirección a `projects:project-detail?tab=files#files`.
  - Errores:
    - 400 cuando no se envían archivos.
    - 403 cuando la organización no coincide.

- POST `/files/<file_id>/delete/` (name: `files:delete_file`)
  - Requiere login.
  - Requiere que `request.user.organization == file.phase.project.organization`.
  - Request: sin cuerpo específico; recomendado `HX-Request: true` para UI dinámica.
  - Respuesta:
    - Si `HX-Request: true`: 200 con cuerpo vacío. La fila se elimina del DOM (`hx-swap="outerHTML"`).
    - Si no es HTMX: JSON `{ "success": true, "id": <file_id> }`.
  - Errores:
    - 403 cuando la organización no coincide.

---

## Ejemplos de Requests/Responses

### Subida (HTMX)

Request headers: `HX-Request: true`

Body: `multipart/form-data`

Campos: `files=<file1>, files=<file2>, ...`

Response: HTML parcial (tabla con filas `<tr id="file-{{ file.id }}">...`)

### Eliminación (HTMX)

Request: `POST /files/123/delete/` con `HX-Request: true`

Response: 200 OK, cuerpo vacío

### Eliminación (fetch normal)

Response JSON:

```json
{ "success": true, "id": 123 }
```

---

## Permisos y Seguridad

- Autenticación obligatoria (`@login_required`).
- Validación de organización en cada operación (verifica acceso a la misma organización del proyecto/fase).
- CSRF habilitado en formularios HTML (token presente en `_files_tab.html`).

---

## Estados de UI más comunes

- Subida exitosa: se muestra mensaje `File(s) uploaded successfully.` y se refresca la lista (HTMX).
- Sin archivos seleccionados: mensaje de error `No files were selected.`.
- Error de permisos: `You do not have permission to access this resource.`.
- Eliminación exitosa: la fila desaparece (HTMX) o JSON success.

---

Arc Manager · Files · Última actualización: 2025-08-13


