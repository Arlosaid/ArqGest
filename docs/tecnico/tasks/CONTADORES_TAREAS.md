# Sistema de Contadores de Tareas

## Descripción General

El módulo de tareas implementa un sistema inteligente de contadores que muestra estadísticas en tiempo real tanto para el total de tareas como para el desglose por estado.

## Estructura de Contadores

### 1. Contadores del Header
Los contadores se muestran en el header de la página y incluyen:

```html
<div class="tasks-stats">
    <div class="task-stat">
        <span class="task-stat-number">{{ total_tasks|default:"0" }}</span>
        <span class="task-stat-label">{% trans "Total" %}</span>
    </div>
    <div class="task-stat">
        <span class="task-stat-number">{{ tasks_todo|default:"0" }}</span>
        <span class="task-stat-label">{% trans "Pendientes" %}</span>
    </div>
    <div class="task-stat">
        <span class="task-stat-number">{{ tasks_in_progress|default:"0" }}</span>
        <span class="task-stat-label">{% trans "En Progreso" %}</span>
    </div>
    <div class="task-stat">
        <span class="task-stat-number">{{ tasks_done|default:"0" }}</span>
        <span class="task-stat-label">{% trans "Completadas" %}</span>
    </div>
</div>
```

### 2. Estados de Tareas Soportados
- **TODO**: Tareas pendientes
- **IN_PROGRESS**: Tareas en progreso
- **PAUSED**: Tareas pausadas
- **DONE**: Tareas completadas

## Funcionamiento del Sistema

### Sin Filtros Activos
Cuando no hay filtros aplicados, los contadores muestran:
- **Total**: Número total de tareas en la lista
- **Pendientes**: Tareas con estado `TODO`
- **En Progreso**: Tareas con estado `IN_PROGRESS`
- **Completadas**: Tareas con estado `DONE`

### Con Filtros Activos
Cuando se aplican filtros (estado, prioridad, búsqueda), los contadores se actualizan para mostrar:
- **Total**: Número de tareas visibles después del filtrado
- **Pendientes**: Tareas visibles con estado `TODO`
- **En Progreso**: Tareas visibles con estado `IN_PROGRESS`
- **Completadas**: Tareas visibles con estado `DONE`

## Indicadores Visuales

### 1. Filtros Activos
- **Borde izquierdo azul** en la sección de filtros
- **Cambio de fondo** sutil para indicar estado activo

### 2. Estadísticas Filtradas
- **Etiqueta "📊 Filtrado"** en la esquina superior derecha de las estadísticas
- **Contador de resultados** que muestra "Filtrado: X de Y tareas"

## Funciones JavaScript Clave

### `updateHeaderStats(totalTasks)`
Actualiza todos los contadores con estadísticas completas:
```javascript
updateHeaderStats(totalTasks) {
    // Contar tareas por estado
    const taskItems = document.querySelectorAll('.task-item');
    let todoCount = 0, inProgressCount = 0, doneCount = 0, pausedCount = 0;
    
    // Contar por estado...
    
    // Actualizar contadores
    stats[0].textContent = totalTasks;      // Total
    stats[1].textContent = todoCount;       // Pendientes
    stats[2].textContent = inProgressCount; // En Progreso
    stats[3].textContent = doneCount;       // Completadas
}
```

### `updateFilteredStats(visibleCount)`
Actualiza contadores cuando hay filtros activos:
```javascript
updateFilteredStats(visibleCount) {
    // Contar solo tareas visibles por estado
    const visibleTaskItems = Array.from(document.querySelectorAll('.task-item'))
        .filter(item => item.style.display !== 'none');
    
    // Contar y actualizar contadores...
}
```

### `updateTaskCounters(visibleCount, hiddenCount)`
Función principal que decide qué estadísticas mostrar:
```javascript
updateTaskCounters(visibleCount, hiddenCount) {
    if (!this.hasActiveFilters()) {
        // Sin filtros: estadísticas completas
        this.updateHeaderStats(totalTasks);
    } else {
        // Con filtros: estadísticas filtradas
        this.updateFilteredStats(visibleCount);
    }
}
```

## Flujo de Actualización

1. **Inicialización**: Al cargar la página, se muestran estadísticas completas
2. **Aplicación de Filtros**: Los contadores se actualizan para mostrar solo tareas visibles
3. **Limpieza de Filtros**: Los contadores vuelven a mostrar estadísticas completas
4. **Actualización en Tiempo Real**: Los contadores se actualizan automáticamente con cada cambio

## Responsive Design

Los contadores se adaptan a diferentes tamaños de pantalla:
- **Desktop**: Contadores en fila horizontal
- **Tablet**: Contadores en fila con wrap
- **Mobile**: Contadores apilados verticalmente

## Personalización

### Variables CSS
```css
:root {
    --task-primary: #3b82f6;
    --task-primary-light: #dbeafe;
    --task-primary-dark: #2563eb;
    --task-radius-sm: 0.5rem;
    --task-transition: all 0.2s ease;
}
```

### Clases CSS
- `.task-stat`: Contenedor de cada estadística
- `.task-stat-number`: Número de la estadística
- `.task-stat-label`: Etiqueta descriptiva
- `.has-filtered-stats`: Indicador de estadísticas filtradas

## Troubleshooting

### Problema: Contadores no se actualizan
**Solución**: Verificar que los elementos tengan los IDs correctos:
- `statusFilter`
- `priorityFilter`
- `taskSearch`
- `tasksList`

### Problema: Estadísticas por estado incorrectas
**Solución**: Verificar que las tareas tengan el atributo `data-status` correcto:
```html
<li class="task-item" data-status="{{ task.status }}">
```

### Problema: Contador de filtros no aparece
**Solución**: Verificar que exista el elemento `.filters-row` en el DOM

## Próximas Mejoras

1. **Persistencia de Filtros**: Guardar estado de filtros en localStorage
2. **Exportación de Estadísticas**: Permitir descargar reportes
3. **Gráficos Visuales**: Agregar gráficos de barras o donas
4. **Filtros Avanzados**: Filtros por fecha, asignado, etc.
5. **Actualización en Tiempo Real**: WebSockets para actualizaciones automáticas
