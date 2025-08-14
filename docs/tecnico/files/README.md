# 📋 Módulo Files — Descripción General

### Objetivo
Permitir a los usuarios subir, listar, descargar y eliminar archivos asociados a las fases de los proyectos, asegurando el aislamiento por organización y una experiencia fluida mediante HTMX y enlaces directos a `file.url`.

---

## 📁 Estructura de Archivos

```
arc_manager/apps/files/
├── admin.py                  # (vacío por ahora)
├── apps.py                   # Config de la app
├── migrations/               # Migraciones de ProjectFile
├── models.py                 # Modelo ProjectFile + helpers
├── urls.py                   # Rutas de upload/delete
└── views.py                  # Vistas para subir y eliminar

Plantillas relacionadas:
arc_manager/apps/projects/templates/projects/partials/_files_tab.html
arc_manager/apps/projects/templates/projects/partials/file_list.html

JS relacionado:
arc_manager/static/js/projects.js (gestiona pestañas; no maneja subida/eliminación)
```

---

## 🔗 Relación con Projects/Fases/Tareas

- `ProjectFile` se relaciona con `projects.Phase` vía FK `phase` (`related_name='files'`).
- Los archivos se muestran agrupados por fase en la pestaña “Archivos” del detalle de proyecto.
- No hay vínculo directo a `Task` en el módulo actual.

---

## 🧭 Flujos de Usuario

- Subir: en `_files_tab.html` se envía `POST multipart` a `files:upload_file` con `files[]` (multiple). Si la cabecera `HX-Request` es `'true'`, se renderiza la lista de archivos parcial `file_list.html`.
- Listar: `_files_tab.html` recorre `phase.files.all` y muestra columnas (nombre, tipo/extensión, usuario, fecha, tamaño).
- Descargar: enlace directo `href="{{ file.file.url }}"` con `download`.
- Eliminar: botón con HTMX `hx-post` a `files:delete_file`, `hx-target` a la fila y `hx-swap="outerHTML"` para removerla tras respuesta vacía.

---

## ⚙️ Requisitos y Dependencias

- `MEDIA_URL` y `MEDIA_ROOT` definidos en `core/settings.py` (por defecto `/media/` y `BASE_DIR/media`).
- Middleware de autenticación global: login requerido. Adicionalmente, cada vista valida pertenencia de `request.user.organization` a la del proyecto.
- Permisos de filesystem de escritura en `MEDIA_ROOT` para el proceso de la app.
- Límite de tamaño/extensiones: no existe validación de tamaño/forma en el backend actual; depende del storage y del navegador/servidor.

---

## 🧱 Almacenamiento de Archivos

- `upload_to=project_file_path` genera rutas legibles por organización/proyecto/fase, por ejemplo:
  `organizations/<org_id>/projects/<project_id>/phases/<phase_id>/<filename>`
- Usa el storage por defecto de Django (filesystem en `MEDIA_ROOT`).

---

Arc Manager · Módulo Files · Última actualización: 2025-08-13


