## 📚 Documentación del Módulo Files - Arc Manager

### 🎯 Bienvenido

Esta es la documentación completa del módulo **Files**. Gestiona la subida, listado, descarga y eliminación de archivos asociados a las fases de un proyecto, con aislamiento por organización y soporte para HTMX.

---

## 📖 Documentos Disponibles

- 🏠 [README.md](README.md) — Descripción general y arquitectura
- 🔧 [IMPLEMENTACION_TECNICA.md](IMPLEMENTACION_TECNICA.md) — Detalle técnico profundo
- 🌐 [API_ENDPOINTS.md](API_ENDPOINTS.md) — URLs, permisos y ejemplos
- 📝 [CHANGELOG.md](CHANGELOG.md) — Historial de cambios

---

## 🚀 Inicio Rápido por Rol

### Para Desarrolladores
- Revisa `apps/files/models.py` para entender `ProjectFile` y `upload_to`.
- Revisa `apps/files/views.py` para el flujo de subida/eliminación y manejo de HTMX.
- Verifica `MEDIA_ROOT`/`MEDIA_URL` en `core/settings.py`.
- Plantillas: `projects/partials/_files_tab.html` y `projects/partials/file_list.html`.

### Para Administradores
- La gestión de archivos se realiza desde el detalle del proyecto, pestaña “Archivos”. No hay admin Django personalizado para `ProjectFile`.
- Validar que los usuarios actúen dentro de su organización.

### Para Soporte/QA
- Si los archivos no cargan/descargan: comprobar `MEDIA_ROOT`, permisos de filesystem y rutas públicas a `/media/`.
- Verificar que el usuario pertenece a la misma organización del proyecto/fase.
- Revisar mensajes de la UI tras subir/eliminar.

---

## 🏗️ Visión General (Flujo)

```mermaid
flowchart TD
  A[UI: _files_tab.html] -->|POST multipart files[]| B[View: upload_file]
  B -->|Crea ProjectFile| C[Model: ProjectFile]
  C --> D[Storage: default MEDIA_ROOT]
  B -->|HX-Request| E[Render file_list.html]
  A -->|click Eliminar (HTMX)| F[View: delete_file]
  F -->|delete()| C
  F -->|HTMX 200 vacío| A
  A -->|Descargar| G[Link directo file.url]
```

---

Arc Manager · Módulo Files · Última actualización: 2025-08-13


