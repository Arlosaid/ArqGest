# 📊 Análisis Comparativo: Proyectos vs Tareas

Comparación detallada de estilos entre las vistas de Proyectos y Tareas para identificar elementos a homologar.

---

## 🎯 Resumen Ejecutivo

### Estado Actual

| Vista | Header | Info Cards | Stats | Búsqueda | Tabla | Homologado |
|-------|--------|------------|-------|----------|-------|------------|
| **Proyectos (Lista)** | ✅ Completo | ❌ No usa | ✅ Stats inline | ✅ Básica | ❌ Grid cards | 🟡 Parcial |
| **Proyectos (Detalle)** | ✅ Completo | ✅ Completo | ❌ No usa | ❌ No usa | ❌ No usa | ✅ Referencia |
| **Tareas (Mi Lista)** | 🟡 Diferente | ❌ No usa | ✅ Stats compact | ✅ Avanzada | ❌ Grid cards | 🟡 Parcial |
| **Tareas (Kanban)** | ✅ Completo | ❌ No usa | ❌ No usa | ✅ Filtros | ❌ Kanban | 🟡 Específico |

---

## 📌 Componente por Componente

### 1. Header Section

#### 📘 Proyectos (Lista)
```html
<div class="header-section">
    <div class="header-content">
        <div class="header-title">
            <div class="header-icon">
                <i class="fas fa-project-diagram"></i>
            </div>
            <div>
                <h1>Mis Proyectos</h1>
                <div class="text-muted">Gestiona y organiza tus proyectos arquitectónicos</div>
            </div>
        </div>
        <div class="d-flex gap-2">
            <a href="#" class="btn btn-primary">
                <i class="fas fa-plus"></i> Crear Nuevo Proyecto
            </a>
        </div>
    </div>
</div>
```

**Características:**
- ✅ Gradiente azul claro
- ✅ Icono cuadrado con gradiente
- ✅ Título + Subtítulo
- ✅ Botón primario con gradiente

#### 📗 Tareas (Mi Lista)
```html
<div class="my-tasks-header">
    <div class="header-content">
        <h1><i class="fas fa-user-check"></i> Mis Tareas</h1>
        <p class="header-subtitle">Gestiona y revisa tus tareas asignadas</p>
    </div>

    <div class="stats-compact">
        <!-- Stats dentro del header -->
    </div>
</div>
```

**Características:**
- ❌ **Diferente**: Clase `my-tasks-header` en lugar de `header-section`
- ❌ **Diferente**: Icono inline en h1, no cuadrado separado
- ❌ **Diferente**: Stats dentro del header
- ✅ Similar: Título + Subtítulo

**🔧 Acción Requerida:**
- Cambiar `my-tasks-header` por `header-section`
- Separar el icono en su propio div `header-icon`
- Mover stats fuera del header
- Agregar botón de acción si aplica

---

### 2. Estadísticas

#### 📘 Proyectos (Lista)
```html
<div class="stats-inline">
    <div class="stat-inline-item">
        <div class="stat-icon-compact total">
            <i class="fas fa-folder"></i>
        </div>
        <div class="stat-content-compact">
            <div class="stat-number-compact">42</div>
            <div class="stat-label-compact">Total</div>
        </div>
    </div>
</div>
```

**Características:**
- Horizontal inline
- Icono + Número + Label
- Más compacta

#### 📗 Tareas (Mi Lista)
```html
<div class="stats-compact">
    <div class="stat-item stat-total">
        <div class="stat-number">25</div>
        <div class="stat-label">Total</div>
    </div>
</div>
```

**Características:**
- Centrada vertical
- Solo Número + Label
- Sin icono
- Más espaciada

**🔧 Acción Requerida:**
- Decidir un estilo único para toda la aplicación
- **Recomendación**: Usar `stats-compact` (más limpio y moderno)

---

### 3. Info Cards

#### 📘 Proyectos (Detalle)
```html
<div class="col-md-6">
    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 10px;">
                <i class="fas fa-building" style="color: #3b82f6; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                    CLIENTE
                </div>
                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">
                    Constructora ABC
                </div>
            </div>
        </div>
    </div>
</div>
```

**Características:**
- ✅ Icono cuadrado 40x40px con gradiente
- ✅ Etiqueta en mayúsculas pequeña
- ✅ Valor destacado
- ✅ Fondo blanco con borde gris claro
- ✅ **ESTE ES EL ESTÁNDAR A SEGUIR**

#### 📗 Tareas (Mi Lista)
```html
<!-- NO TIENE INFO CARDS -->
```

**🔧 Acción Requerida:**
- Si en tareas se necesita mostrar información detallada, usar el mismo patrón de proyectos

---

### 4. Búsqueda y Filtros

#### 📘 Proyectos (Lista)
```html
<!-- Búsqueda básica sin estructura avanzada -->
<input type="text" placeholder="Buscar...">
```

**Características:**
- ❌ Búsqueda simple
- ❌ Sin iconos
- ❌ Sin estructura contenedora

#### 📗 Tareas (Mi Lista)
```html
<div class="search-and-filters">
    <div class="search-section">
        <div class="search-box-enhanced">
            <i class="fas fa-search"></i>
            <input type="text" class="search-input-enhanced" placeholder="Buscar...">
            <button type="button" class="search-clear">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
    
    <div class="filters-section">
        <div class="filter-pills">
            <select class="filter-select-modern">...</select>
            <button class="clear-filters-btn">...</button>
        </div>
    </div>
</div>
```

**Características:**
- ✅ Búsqueda avanzada con iconos
- ✅ Botón de limpiar
- ✅ Filtros modernos
- ✅ Estructura contenedora
- ✅ **ESTE ES EL ESTÁNDAR A SEGUIR**

**🔧 Acción Requerida:**
- Aplicar búsqueda mejorada en proyectos

---

### 5. Visualización de Elementos

#### 📘 Proyectos (Lista)
```html
<div class="project-card">
    <div class="project-card-header">
        <div class="project-image">...</div>
    </div>
    <div class="project-card-body">
        <h3 class="project-title">...</h3>
        <div class="project-client">...</div>
    </div>
</div>
```

**Características:**
- Grid de cards
- Imagen/preview
- Título destacado
- Información adicional

#### 📗 Tareas (Mi Lista)
```html
<div class="task-card-compact">
    <div class="task-card-top">
        <div class="task-badges-compact">...</div>
    </div>
    <div class="task-card-content">
        <h4 class="task-title-compact">...</h4>
        <div class="task-meta-compact">...</div>
    </div>
    <div class="task-card-actions">...</div>
</div>
```

**Características:**
- Grid de cards compactas
- Badges de estado/prioridad
- Título compacto
- Meta información
- Botones de acción

**🔧 Acción Requerida:**
- Ambos estilos son válidos para sus contextos
- Mantener consistencia dentro de cada sección

---

## 🎨 Paleta de Colores

### Proyectos
| Elemento | Color de Fondo | Color de Icono | Uso |
|----------|----------------|----------------|-----|
| Cliente | linear-gradient(135deg, #dbeafe, #bfdbfe) | #3b82f6 | Info card |
| Estado | linear-gradient(135deg, #dcfce7, #bbf7d0) | #10b981 | Info card |
| Fecha | linear-gradient(135deg, #fef3c7, #fde68a) | #f59e0b | Info card |
| Presupuesto | linear-gradient(135deg, #d1fae5, #a7f3d0) | #059669 | Info card |
| Descripción | linear-gradient(135deg, #f3e8ff, #e9d5ff) | #8b5cf6 | Info card |

### Tareas
| Elemento | Color | Uso |
|----------|-------|-----|
| Estado: TODO | #64748b | Badge |
| Estado: IN_PROGRESS | #4285f4 | Badge |
| Estado: PAUSED | #f59e0b | Badge |
| Estado: DONE | #10b981 | Badge |
| Prioridad: HIGH | #ef4444 | Badge |
| Prioridad: MEDIUM | #f59e0b | Badge |
| Prioridad: LOW | #10b981 | Badge |

**🔧 Acción Requerida:**
- Mantener paletas separadas pero consistentes
- Usar info cards de proyectos si se necesitan en tareas

---

## 📏 Espaciado y Tamaños

### Comparación de Medidas

| Elemento | Proyectos | Tareas | Estándar |
|----------|-----------|--------|----------|
| Header padding | 2rem | 1.5rem | **2rem** |
| Info card padding | p-3 (1rem) | N/A | **p-3** |
| Grid gap | g-4 (1.5rem) | g-4 (1.5rem) | ✅ **g-4** |
| Título H1 | 1.75rem | 1.75rem | ✅ **1.75rem** |
| Subtítulo | 0.875rem | 1rem | **0.875rem** |
| Icono header | 40x40px | inline | **40x40px** |
| Icono info card | 40x40px | N/A | **40x40px** |

---

## 🔄 Plan de Homologación

### Prioridad Alta (Inmediato)

1. **Header de Tareas**
   - [ ] Cambiar de `my-tasks-header` a `header-section`
   - [ ] Separar icono en `header-icon`
   - [ ] Mover stats fuera del header
   - [ ] Aplicar gradiente azul de fondo

2. **Búsqueda en Proyectos**
   - [ ] Implementar `search-and-filters`
   - [ ] Agregar iconos de búsqueda
   - [ ] Agregar botón de limpiar
   - [ ] Implementar filtros modernos

### Prioridad Media (Siguiente Sprint)

3. **Estadísticas Unificadas**
   - [ ] Decidir entre `stats-inline` o `stats-compact`
   - [ ] Aplicar en todas las vistas
   - [ ] Documentar el estándar elegido

4. **Info Cards**
   - [ ] Verificar que todas las vistas de detalle usen el mismo patrón
   - [ ] Documentar colores por tipo de información
   - [ ] Crear componente reutilizable

### Prioridad Baja (Futuro)

5. **Responsive**
   - [ ] Verificar breakpoints en todas las vistas
   - [ ] Unificar comportamiento móvil
   - [ ] Optimizar grids para tablet

---

## ✅ Checklist de Homologación por Vista

### Para cada vista nueva o actualizada:

#### Header
- [ ] Usa `header-section` como clase principal
- [ ] Tiene gradiente azul de fondo
- [ ] Icono separado en `header-icon` 40x40px
- [ ] Título h1 de 1.75rem
- [ ] Subtítulo de 0.875rem
- [ ] Botones alineados a la derecha

#### Estadísticas
- [ ] Usa `stats-compact` o `stats-inline` (según estándar)
- [ ] Números grandes y destacados
- [ ] Etiquetas en mayúsculas pequeñas
- [ ] Colores específicos por tipo

#### Búsqueda
- [ ] Usa `search-and-filters` como contenedor
- [ ] Icono de búsqueda a la izquierda
- [ ] Input con clase `search-input-enhanced`
- [ ] Botón de limpiar a la derecha
- [ ] Filtros en `filter-pills`

#### Info Cards (si aplica)
- [ ] Usa grid `row g-4`
- [ ] Cada card con `col-md-6` o `col-md-4`
- [ ] Icono 40x40px con gradiente
- [ ] Etiqueta en mayúsculas 0.8rem
- [ ] Valor destacado 1rem
- [ ] Padding p-3

#### Botones
- [ ] Primarios con gradiente azul
- [ ] Incluyen icono + texto
- [ ] Gap de 8px entre elementos
- [ ] Sombra y hover effect

---

## 📚 Archivos de Referencia

### CSS Principal
- `base.css` - Estilos globales (HEADER ESTÁNDAR aquí)
- `project_detail.css` - Info cards estándar
- `my_tasks_page.css` - Búsqueda mejorada estándar

### Templates de Referencia
- `project_detail.html` - Info cards perfectas
- `project_list.html` - Header estándar
- `my_tasks.html` - Búsqueda y filtros estándar

---

## 🎯 Recomendaciones Finales

### Estándares Definidos

1. **Header Section**: Usar siempre `header-section` con gradiente azul y icono separado
2. **Info Cards**: Patrón de `project_detail.html` es el estándar
3. **Búsqueda**: Patrón de `my_tasks.html` es el estándar
4. **Estadísticas**: Decidir entre inline o compact (recomendado: compact)
5. **Botones**: Siempre gradientes con iconos

### Elementos a Homologar en Tareas

```diff
- <div class="my-tasks-header">
+ <div class="header-section">
      <div class="header-content">
          <div class="header-title">
+             <div class="header-icon">
-                 <h1><i class="fas fa-user-check"></i> Mis Tareas</h1>
+                 <i class="fas fa-user-check"></i>
+             </div>
+             <div>
+                 <h1>Mis Tareas</h1>
-                 <p class="header-subtitle">Gestiona y revisa...</p>
+                 <div class="text-muted">Gestiona y revisa...</div>
+             </div>
          </div>
      </div>
  </div>

- <div class="stats-compact">
-     <!-- dentro del header -->
- </div>
+ <!-- Mover stats fuera del header -->
+ <div class="stats-compact">
+     ...
+ </div>
```

---

**Documento creado**: Noviembre 26, 2025  
**Última actualización**: Noviembre 26, 2025  
**Versión**: 1.0  
**Estado**: Plan de acción definido
