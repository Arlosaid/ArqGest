# 🛠️ Troubleshooting - Módulo de Proyectos (Kanban)

## Contador de tareas muestra una “pelota” blanca
- **Síntoma**: El badge del contador en el encabezado de cada columna muestra una esfera/blanco decorativo.
- **Causa**: Pseudo-elemento `::before` en `.task-count` definido en `static/css/kanban.css`.
- **Solución**: Se eliminó el pseudo-elemento y se ajustó el padding del badge.
  - Archivo: `arc_manager/static/css/kanban.css`
  - Regla:
    ```css
    .task-count { padding: 0.35rem 0.6rem; }
    .task-count::before { display: none; }
    ```

## Estado “Sin tareas” con icono genérico
- **Síntoma**: En columnas vacías, el icono no es representativo del dominio.
- **Cambio aplicado**: Se reemplazó por `fa-helmet-safety` (casco de obra), más alineado con arquitectura.
  - Archivo: `arc_manager/apps/projects/templates/projects/kanban_board.html`
  - Bloque: `.empty-column > .empty-icon`

## ¿No ves los cambios?
- Asegúrate de que el bust de caché de assets corresponda.
- Forzar recarga dura del navegador (Ctrl+F5) o limpiar caché.

---

# 🪟 Modal queda bloqueado con pantalla negra (no permite escribir)

- **Síntoma**
  - Al abrir un modal (por ejemplo, "Nueva Tarea"), se ve el overlay oscuro pero no puedes interactuar: parece que el modal está "detrás" del contenido.

- **Causa**
  - La capa principal del layout (`.content-area`) tenía `z-index: 1`, creando un stacking context por encima del modal y su backdrop de Bootstrap.

- **Solución**
  - Eliminar el `z-index` de `.content-area` para que los modales queden por encima, como espera Bootstrap 5.3.
  - Archivo: `arc_manager/static/css/base.css`
  - Cambio:
    ```css
    .content-area {
        /* ... */
        position: relative;
        /* z-index: 1;  ← quitado */
        /* ... */
    }
    ```

- **Notas**
  - Evitar `z-index` en contenedores globales salvo necesidad.
  - Revisar que no existan overrides para `.modal` o `.modal-backdrop` en CSS propios.
  - Opcional: usar `modal-dialog-centered` para centrar verticalmente.

# 🚧 Incidencia: Crear Tarea se “bloquea” (sin request en Network)

- **Síntoma observado**
  - Al abrir el modal “Nueva Tarea” (Kanban o Detalle del Proyecto) y pulsar “Crear Tarea”, no aparece ningún request en la pestaña Network. El modal permanece abierto.

- **Contexto**
  - Kanban: `templates/projects/kanban_board.html` → `#addTaskModal`.
  - Detalle: `templates/projects/partials/_tasks_tab.html` → `#createTaskModal`.
  - Backend: `views.task_create` (`/projects/<project_pk>/tasks/create/`) devuelve JSON si `Accept: application/json` o redirige en HTML.

- **Hipótesis consideradas**
  1) Rutas incongruentes en JS (singular vs plural) → 404 silencioso.
  2) Falta de cookies/CSRF en `fetch` → 403 y fallo silencioso.
  3) Listener global intercepta `submit` y lo cancela sin continuar.
  4) `relatedTarget` nulo al abrir el modal → `TypeError` y el listener deja de ejecutarse.

- **Cambios realizados (no resolvieron el síntoma en el entorno del usuario)**
  - En `static/js/kanban.js`:
    - Rutas corregidas a plural: `tasks/${id}/move/`, `tasks/${id}/edit/`.
    - `credentials: 'same-origin'` añadido a los `fetch` para asegurar envío de cookies/CSRF.
    - Guard ante `relatedTarget` nulo; preselección de fase por defecto si está vacío.
  - Unificación del submit en `static/js/tasks.js` (nuevo):
    - Captura el `submit` de `#addTaskModal` y `#createTaskModal` y hace `fetch` con CSRF, soporte JSON/HTML y recarga ligera.
    - Incluido en `kanban_board.html` y `project_detail.html`.
  - Limpieza: `kanban.js` deja de manejar el submit para evitar duplicidad.

- **Resultado**
  - Sigue sin aparecer el POST en Network, lo que sugiere bloqueo del `submit` por algún listener externo en esa instancia.

- **Verificaciones recomendadas**
  1) Forzar envío manual para aislar la UI:
     - Kanban: `document.querySelector('#addTaskModal form')?.submit()`
     - Detalle: `document.querySelector('#createTaskModal form')?.submit()`
  2) Confirmar carga de `tasks.js?v=1.0` en Network y ausencia de errores en Consola.
  3) Verificar que el `<select name="phase">` tenga opciones válidas (el proyecto debe tener fases); si no, la vista valida y no crea tarea.

- **Siguiente plan**
  - Instrumentar logs en navegador para detectar quién hace `preventDefault()` en `submit`.
  - Como mitigación, cambiar el botón “Crear Tarea” a `type="button"` y enganchar un `click` que lance `fetch` directamente (bypass del submit nativo) en ambos modales.
  - Alternativa: endpoint específico JSON-only para creación con payload mínimo y handler por `click`.

### Archivos tocados
- `arc_manager/static/js/kanban.js`
- `arc_manager/static/js/tasks.js` (nuevo)
- `arc_manager/apps/projects/templates/projects/kanban_board.html`
- `arc_manager/apps/projects/templates/projects/project_detail.html`
- `arc_manager/apps/projects/templates/projects/partials/_tasks_tab.html`
# 🛠️ Troubleshooting - Módulo de Proyectos

## Errores de Template

### TemplateSyntaxError: Invalid filter 'endswith'
- Causa: uso de filtro inexistente en Django templates.
- Solución: usar propiedades del modelo (`ProjectFile.extension`) para comparar tipos.
- Archivo: `projects/partials/_files_tab.html` (corrigido).

## Archivos que no aparecen en la pestaña
- Verifica que `ProjectDetailView` tenga `prefetch_related('files', 'files__uploaded_by')`.
- Asegúrate de que existan fases para el proyecto; los archivos se agrupan por fase.

## El acordeón aparece abierto por defecto
- Desde v2.5, todos los ítems se renderizan colapsados (sin `show`). Si ves uno abierto, limpia caché o revisa que `_files_tab.html` no agregue `show` condicionalmente.

## No se puede subir archivo
- Confirmar que se envía `multipart/form-data` y el campo `files` permite múltiples.
- Ruta correcta: `files:upload_file` → `/projects/<project_id>/phases/<phase_id>/files/upload/`.
- Usuario debe pertenecer a la organización del proyecto.

## Iconos incorrectos
- La lógica depende de `ProjectFile.extension` (mayúsculas). Si se agregan tipos nuevos, extender condiciones en `_files_tab.html`.

## Limpieza de caché del navegador
- Tras cambios de CSS/JS, recargar con hard refresh (Ctrl+F5). El template usa query `?v=` para bust de caché (`projects.css v1.5`, `projects.js v1.2`).


