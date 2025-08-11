# Proyectos - Guía interna (v2.5)

## Vista Detalle con Pestañas

- Pestañas: `Detalles`, `Fases`, `Tareas`, `Archivos`.
- Por defecto se activa `Detalles`. Si ninguna queda activa, el JS fuerza `Detalles`.
- Forzar pestaña vía URL: `?tab=details|phases|tasks|files` o `#details|phases|tasks|files`.
- Archivos clave:
  - `templates/projects/project_detail.html`
  - `static/js/projects.js` (normaliza pestañas, v1.2)
  - `static/css/projects.css` (estilos, v1.5)

## Acordeón de Archivos

- Renderiza todas las fases colapsadas (ninguna abierta por defecto).
- Estilos mejorados:
  - Cabecera `.accordion-button.file-phase-header` con chevron animado.
  - Badge redondo `.bg-primary-soft` para conteo.
  - Tabla `.file-list-table.modern-table` con separadores y hover.

## Convenciones de Estilo

- Evitar reescribir reglas globales; usar las clases proveídas en `projects.css`.
- Si se agregan columnas a la tabla de archivos, mantener anchos porcentuales y alineación de metadatos.

## Notas de Caché

- El template incluye `?v=` para bust de caché. Actualizar el número al cambiar CSS/JS.


