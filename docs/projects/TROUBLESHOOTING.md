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

# 🚧 Problema: Selector de Kanban no muestra proyectos

## Síntoma
- **URL afectada**: `http://localhost:8000/projects/kanban-selector/`
- **Comportamiento**: La página se carga pero no muestra ningún proyecto
- **Otros módulos funcionan**: En `/projects/` sí se ven correctamente los proyectos

## Causa Raíz
**Filtros de estado incorrectos en la vista `ProjectKanbanSelectorView`**

La vista estaba filtrando proyectos por estados que no coincidían con el modelo:

### ❌ Estados incorrectos (en la vista)
```python
active_projects = projects.filter(status='active')        # ❌ 'active'
completed_projects = projects.filter(status='completed')  # ❌ 'completed'  
on_hold_projects = projects.filter(status='on_hold')     # ❌ 'on_hold' (no existe)
```

### ✅ Estados correctos (en el modelo Project)
```python
class Status(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Activo')           # ✅ 'ACTIVE'
    ARCHIVED = 'ARCHIVED', _('Archivado')    # ✅ 'ARCHIVED'
    COMPLETED = 'COMPLETED', _('Completado') # ✅ 'COMPLETED'
```

## Solución Implementada

### 1. Corrección de la Vista (`views.py`)
```python
class ProjectKanbanSelectorView(LoginRequiredMixin, View):
    def get(self, request):
        # ... código existente ...
        
        # ✅ CORREGIDO: Usar estados reales del modelo
        active_projects = projects.filter(status='ACTIVE')
        completed_projects = projects.filter(status='COMPLETED')
        archived_projects = projects.filter(status='ARCHIVED')  # Cambiado de on_hold
        
        context = {
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'archived_projects': archived_projects,  # Cambiado de on_hold_projects
            'total_projects': projects.count(),
        }
        return render(request, self.template_name, context)
```

### 2. Actualización de la Plantilla (`kanban_selector.html`)
```html
<!-- ❌ ANTES -->
{% if on_hold_projects %}
    <div class="project-card-selector on-hold">

<!-- ✅ DESPUÉS -->
{% if archived_projects %}
    <div class="project-card-selector archived">
```

### 3. Actualización del CSS
```css
/* ❌ ANTES */
.project-card-selector.on-hold {
    border-top: 3px solid var(--project-warning, #f39c12);
}

/* ✅ DESPUÉS */
.project-card-selector.archived {
    border-top: 3px solid var(--project-warning, #f39c12);
}
```

## Verificación de la Solución

### Antes de la corrección:
- **Total proyectos en BD**: 2
- **Proyectos mostrados**: 0 ❌
- **Causa**: Filtros con estados inexistentes

### Después de la corrección:
- **Total proyectos en BD**: 2
- **Proyectos mostrados**: 2 ✅
- **Estados**: Ambos con `status='ACTIVE'`

## Archivos Modificados
1. **`arc_manager/apps/projects/views.py`**
   - Líneas 493-519: Corrección de filtros de estado
   
2. **`arc_manager/apps/projects/templates/projects/kanban_selector.html`**
   - Cambio de `on_hold_projects` a `archived_projects`
   - Actualización de clases CSS
   - Cambio de texto "En Pausa" a "Archivados"

## Prevención de Problemas Similares

### ✅ Buenas Prácticas
1. **Usar constantes del modelo**: Siempre referenciar `Model.Status.CHOICE` en lugar de strings hardcodeados
2. **Validar filtros**: Verificar que los valores de filtro existan en las opciones del modelo
3. **Testing**: Crear tests que verifiquen que los filtros funcionen con datos reales

### ❌ Evitar
1. **Strings hardcodeados**: No usar `'active'` cuando el modelo tiene `'ACTIVE'`
2. **Estados inexistentes**: No filtrar por estados que no están definidos en el modelo
3. **Nomenclatura inconsistente**: Mantener consistencia entre vista y modelo

## Comandos de Verificación

### Verificar proyectos y estados:
```bash
docker-compose exec web python manage.py shell -c "
from apps.projects.models import Project
projects = Project.objects.all()
print('Total proyectos:', projects.count())
[print(f'- {p.name}: {p.status}') for p in projects]
"
```

### Verificar vista del selector:
```bash
docker-compose exec web python manage.py shell -c "
from apps.projects.views import ProjectKanbanSelectorView
from django.test import RequestFactory
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='adroal08@gmail.com')
view = ProjectKanbanSelectorView()
request = RequestFactory().get('/')
request.user = user
context = view.get(request).context_data
print('Proyectos activos:', context['active_projects'].count())
print('Proyectos completados:', context['completed_projects'].count())
print('Proyectos archivados:', context['archived_projects'].count())
"
```

## Estado Actual
- ✅ **Problema resuelto**: El selector de kanban ahora muestra correctamente los proyectos
- ✅ **Filtros corregidos**: Los estados coinciden con el modelo
- ✅ **Plantilla actualizada**: Usa la nomenclatura correcta
- ✅ **CSS consistente**: Las clases coinciden con los nuevos nombres

## Próximos Pasos Recomendados
1. **Probar funcionalidad**: Verificar que se puedan seleccionar proyectos y acceder al kanban
2. **Revisar otros filtros**: Verificar que no haya filtros similares en otras vistas
3. **Implementar tests**: Crear tests automatizados para evitar regresiones
4. **Documentar estados**: Mantener documentación actualizada de los estados disponibles


