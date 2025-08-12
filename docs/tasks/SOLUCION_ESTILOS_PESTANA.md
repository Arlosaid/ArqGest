# Solución: Estilos de la Pestaña de Tareas en el Hub de Proyectos

## Problema Identificado

El usuario reportó que "en el hub de proyectos no se ve el estilo de la pestaña de tareas". Después de investigar, se identificó que:

1. **Faltaba la carga de estilos**: El archivo `project_detail.html` no estaba cargando `tasks.css`
2. **Faltaba la carga de JavaScript**: No se estaba cargando `tasks.js` 
3. **IDs incorrectos**: Los filtros en `_tasks_tab.html` tenían IDs diferentes a los que esperaba el `TaskManager`
4. **Falta de inicialización**: El `TaskManager` no se inicializaba cuando se activaba la pestaña de tareas

## Solución Implementada

### 1. Carga de Estilos y JavaScript

**Archivo**: `arc_manager/apps/projects/templates/projects/project_detail.html`

```html
{% block extra_css %}
<link href="{% static 'css/projects.css' %}?v=1.5" rel="stylesheet">
<link href="{% static 'css/tasks.css' %}?v=1.0" rel="stylesheet">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/projects.js' %}?v=1.2"></script>
<script src="{% static 'js/tasks.js' %}?v=1.0"></script>
<script>
// ... resto del código
</script>
{% endblock %}
```

### 2. Corrección de IDs en Filtros

**Archivo**: `arc_manager/apps/projects/templates/projects/partials/_tasks_tab.html`

**Cambios realizados**:
- `id="projectStatusFilter"` → `id="statusFilter"`
- `id="projectPriorityFilter"` → `id="priorityFilter"`  
- `id="projectTaskSearch"` → `id="searchInput"`

**Código corregido**:
```html
<select class="filter-select" id="statusFilter">
    <option value="">{% trans "Todos" %}</option>
    <option value="TODO">{% trans "Pendiente" %}</option>
    <option value="IN_PROGRESS">{% trans "En Progreso" %}</option>
    <option value="PAUSED">{% trans "Pausada" %}</option>
    <option value="DONE">{% trans "Completada" %}</option>
</select>

<select class="filter-select" id="priorityFilter">
    <option value="">{% trans "Todas" %}</option>
    <option value="LOW">{% trans "Baja" %}</option>
    <option value="MEDIUM">{% trans "Media" %}</option>
    <option value="HIGH">{% trans "Alta" %}</option>
</select>

<input type="text" class="search-input" id="searchInput" placeholder="{% trans 'Buscar tareas del proyecto...' %}">
```

### 3. Inicialización del TaskManager

**Inicialización al cargar la página**:
```javascript
// Inicializar TaskManager si la pestaña inicial es tasks
if (initial === 'tasks') {
  setTimeout(() => {
    if (typeof TaskManager !== 'undefined') {
      new TaskManager();
    }
  }, 100);
}
```

**Inicialización al cambiar de pestaña**:
```javascript
// Evento de Bootstrap (si está disponible)
tabContainer.addEventListener('shown.bs.tab', (e) => {
  const id = e.target?.getAttribute('data-bs-target')?.replace('#','');
  if (id) showTabById(id);
  
  // Inicializar TaskManager cuando se active la pestaña de tareas
  if (id === 'tasks') {
    // Pequeño delay para asegurar que el DOM esté listo
    setTimeout(() => {
      if (typeof TaskManager !== 'undefined') {
        new TaskManager();
      }
    }, 100);
  }
});
```

**Inicialización en el partial**:
```javascript
// Inicializar TaskManager para la pestaña de tareas del proyecto
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('tasks').classList.contains('active') || 
        document.getElementById('tasks').classList.contains('show')) {
        new TaskManager();
    }
});
```

## Archivos Modificados

1. **`arc_manager/apps/projects/templates/projects/project_detail.html`**
   - Agregada carga de `tasks.css` y `tasks.js`
   - Mejorada inicialización del `TaskManager`

2. **`arc_manager/apps/projects/templates/projects/partials/_tasks_tab.html`**
   - Corregidos IDs de filtros para coincidir con `TaskManager`
   - Agregada inicialización del `TaskManager`

## Resultado Esperado

Después de estos cambios, la pestaña de tareas en el hub de proyectos debería:

- ✅ Mostrar todos los estilos definidos en `tasks.css`
- ✅ Tener funcionalidad completa de filtros y búsqueda
- ✅ Mostrar contadores de tareas por estado correctamente
- ✅ Funcionar con el sistema de filtros y estadísticas
- ✅ Mantener consistencia visual con el resto del módulo de tareas

## Verificación

Para verificar que la solución funciona:

1. Navegar al hub de proyectos
2. Hacer clic en la pestaña "Tareas"
3. Verificar que se muestren los estilos correctos
4. Probar los filtros de estado y prioridad
5. Verificar que los contadores se actualicen correctamente
6. Probar la funcionalidad de búsqueda

## Notas Técnicas

- Se usa un delay de 100ms para asegurar que el DOM esté completamente cargado
- Se verifica que `TaskManager` esté definido antes de inicializarlo
- Se mantiene la compatibilidad con el sistema de pestañas existente
- Los estilos se cargan con versionado para evitar problemas de caché
