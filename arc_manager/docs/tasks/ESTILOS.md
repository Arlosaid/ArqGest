# 🎨 Guía de Estilos CSS - Módulo de Tareas

## 📋 Visión General

Esta guía documenta el sistema de diseño CSS del módulo de tareas de ArcManager, proporcionando una referencia completa para desarrolladores y diseñadores.

## 🎯 Sistema de Variables CSS

### **Colores Principales**
```css
:root {
    /* Azules */
    --task-primary: #3b82f6;           /* Azul principal */
    --task-primary-dark: #2563eb;      /* Azul oscuro para hover */
    --task-primary-light: #dbeafe;     /* Azul claro para fondos */
    
    /* Estados */
    --task-success: #10b981;           /* Verde para completado */
    --task-success-light: #d1fae5;     /* Verde claro para badges */
    --task-warning: #f59e0b;           /* Amarillo para pausado */
    --task-warning-light: #fef3c7;     /* Amarillo claro para badges */
    --task-error: #ef4444;             /* Rojo para prioridad alta */
    --task-error-light: #fee2e2;       /* Rojo claro para badges */
    --task-info: #06b6d4;              /* Azul info para fases */
    --task-info-light: #cffafe;        /* Azul info claro */
}
```

### **Colores de Texto**
```css
:root {
    --task-text: #1e293b;              /* Texto principal */
    --task-text-secondary: #64748b;    /* Texto secundario */
    --task-text-muted: #94a3b8;        /* Texto atenuado */
}
```

### **Superficies y Fondos**
```css
:root {
    --task-surface: #ffffff;           /* Superficie principal */
    --task-surface-secondary: #f8fafc; /* Superficie secundaria */
    --task-surface-tertiary: #f1f5f9;  /* Superficie terciaria */
}
```

### **Bordes y Sombras**
```css
:root {
    --task-border: #e2e8f0;           /* Borde principal */
    --task-border-light: #f1f5f9;     /* Borde sutil */
    --task-radius: 0.75rem;           /* Radio de borde principal */
    --task-radius-sm: 0.5rem;         /* Radio de borde pequeño */
    
    /* Sombras */
    --task-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --task-shadow-hover: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --task-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
```

### **Transiciones y Animaciones**
```css
:root {
    --task-transition: all 0.2s ease;      /* Transición estándar */
    --task-transition-slow: all 0.3s ease; /* Transición lenta */
}
```

## 🏗️ Layout y Estructura

### **Container Principal**
```css
.tasks-container {
    background: var(--task-surface);
    border-radius: var(--task-radius);
    box-shadow: var(--task-shadow);
    overflow: hidden;
}
```

**Características:**
- Fondo blanco con sombra sutil
- Bordes redondeados consistentes
- Overflow hidden para elementos internos

### **Header de Tareas**
```css
.tasks-header {
    background: linear-gradient(135deg, var(--task-primary) 0%, var(--task-primary-dark) 100%);
    color: white;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
}

.tasks-header::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 200px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    transform: translate(50%, -50%);
}
```

**Elementos Decorativos:**
- Gradiente azul profesional
- Círculo decorativo con transparencia
- Posicionamiento relativo para elementos internos

### **Estadísticas**
```css
.tasks-stats {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.task-stat {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.5rem 1rem;
    border-radius: var(--task-radius-sm);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
}
```

**Características:**
- Flexbox para distribución horizontal
- Fondo semi-transparente con blur
- Bordes sutiles con transparencia
- Wrap automático en pantallas pequeñas

## 🔍 Filtros y Búsqueda

### **Contenedor de Filtros**
```css
.tasks-filters {
    background: var(--task-surface-secondary);
    border-bottom: 1px solid var(--task-border);
    padding: 1rem 1.5rem;
}

.filters-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}
```

### **Grupos de Filtros**
```css
.filter-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.filter-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--task-text-secondary);
    white-space: nowrap;
}

.filter-select {
    background: var(--task-surface);
    border: 1px solid var(--task-border);
    border-radius: var(--task-radius-sm);
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    color: var(--task-text);
    transition: var(--task-transition);
    min-width: 120px;
}
```

### **Campo de Búsqueda**
```css
.search-box {
    flex: 1;
    max-width: 300px;
    position: relative;
}

.search-input {
    width: 100%;
    background: var(--task-surface);
    border: 1px solid var(--task-border);
    border-radius: var(--task-radius-sm);
    padding: 0.5rem 0.75rem 0.5rem 2.5rem;
    font-size: 0.875rem;
    color: var(--task-text);
    transition: var(--task-transition);
}

.search-icon {
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--task-text-muted);
    font-size: 0.875rem;
}
```

## 📋 Lista de Tareas

### **Contenedor de Lista**
```css
.tasks-list {
    padding: 0;
    margin: 0;
    list-style: none;
}

.task-item {
    background: var(--task-surface);
    border-bottom: 1px solid var(--task-border-light);
    transition: var(--task-transition);
    position: relative;
}

.task-item:hover {
    background: var(--task-surface-secondary);
    transform: translateX(4px);
}
```

### **Layout de Contenido**
```css
.task-content {
    padding: 1.25rem 1.5rem;
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 1rem;
    align-items: center;
}

.task-main {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
```

**Grid Layout:**
- **1fr**: Contenido principal (título, descripción, metadatos)
- **auto**: Sección de estado y prioridad
- **auto**: Botones de acción

### **Título y Descripción**
```css
.task-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--task-text);
    margin: 0;
    line-height: 1.4;
}

.task-description {
    color: var(--task-text-secondary);
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
```

**Características:**
- Título con peso semibold
- Descripción truncada a 2 líneas
- Colores diferenciados para jerarquía

### **Metadatos de Tarea**
```css
.task-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.task-project,
.task-phase,
.task-due-date {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--task-text-secondary);
    font-size: 0.875rem;
}

.task-project i {
    color: var(--task-primary);
    font-size: 0.75rem;
}

.task-phase i {
    color: var(--task-info);
    font-size: 0.75rem;
}
```

## 🏷️ Badges y Estados

### **Badges de Estado**
```css
.task-status-badge {
    padding: 0.375rem 0.75rem;
    border-radius: var(--task-radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    min-width: 80px;
    text-align: center;
}

/* Estados específicos */
.task-status-badge.todo {
    background: var(--task-surface-secondary);
    color: var(--task-text-secondary);
    border: 1px solid var(--task-border);
}

.task-status-badge.in-progress {
    background: var(--task-primary-light);
    color: var(--task-primary-dark);
    border: 1px solid var(--task-primary);
}

.task-status-badge.paused {
    background: var(--task-warning-light);
    color: var(--task-warning);
    border: 1px solid var(--task-warning);
}

.task-status-badge.done {
    background: var(--task-success-light);
    color: var(--task-success);
    border: 1px solid var(--task-success);
}
```

### **Badges de Prioridad**
```css
.task-priority-badge {
    padding: 0.25rem 0.5rem;
    border-radius: var(--task-radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.task-priority-badge.low {
    background: var(--task-surface-secondary);
    color: var(--task-text-secondary);
    border: 1px solid var(--task-border);
}

.task-priority-badge.medium {
    background: var(--task-warning-light);
    color: var(--task-warning);
    border: 1px solid var(--task-warning);
}

.task-priority-badge.high {
    background: var(--task-error-light);
    color: var(--task-error);
    border: 1px solid var(--task-error);
}
```

## 🔘 Botones de Acción

### **Botón Base**
```css
.task-action-btn {
    background: transparent;
    border: 1px solid var(--task-border);
    border-radius: var(--task-radius-sm);
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    color: var(--task-text-secondary);
    cursor: pointer;
    transition: var(--task-transition);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 80px;
    justify-content: center;
}

.task-action-btn:hover {
    background: var(--task-surface-secondary);
    border-color: var(--task-primary);
    color: var(--task-primary);
    text-decoration: none;
}
```

### **Variantes de Botones**
```css
.task-action-btn.primary {
    background: var(--task-primary);
    color: white;
    border-color: var(--task-primary);
}

.task-action-btn.primary:hover {
    background: var(--task-primary-dark);
    border-color: var(--task-primary-dark);
    color: white;
}

.task-action-btn.success {
    background: var(--task-success);
    color: white;
    border-color: var(--task-success);
}

.task-action-btn.warning {
    background: var(--task-warning);
    color: white;
    border-color: var(--task-warning);
}
```

## 📱 Responsive Design

### **Breakpoints Principales**
```css
/* Desktop */
@media (min-width: 1201px) {
    .tasks-grid {
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    }
}

/* Tablet */
@media (max-width: 1200px) {
    .tasks-grid {
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    }
}

/* Mobile */
@media (max-width: 768px) {
    .tasks-header {
        padding: 1rem;
    }
    
    .tasks-title {
        font-size: 1.5rem;
    }
    
    .tasks-stats {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .task-content {
        grid-template-columns: 1fr;
        gap: 0.75rem;
        padding: 1rem;
    }
    
    .task-status-section {
        flex-direction: row;
        justify-content: space-between;
        width: 100%;
    }
    
    .task-actions {
        flex-direction: row;
        justify-content: center;
        width: 100%;
    }
}
```

### **Adaptaciones Móviles Específicas**
```css
@media (max-width: 480px) {
    .page-container {
        padding: 1rem;
    }
    
    .tasks-header {
        padding: 0.75rem;
    }
    
    .tasks-title {
        font-size: 1.25rem;
    }
    
    .task-content {
        padding: 0.75rem;
    }
    
    .task-actions {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .task-action-btn {
        width: 100%;
        justify-content: center;
    }
}
```

## 🎭 Animaciones y Transiciones

### **Entrada de Tareas**
```css
@keyframes taskSlideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.task-item {
    animation: taskSlideIn 0.3s ease-out;
}

/* Entrada escalonada */
.task-item:nth-child(1) { animation-delay: 0.1s; }
.task-item:nth-child(2) { animation-delay: 0.2s; }
.task-item:nth-child(3) { animation-delay: 0.3s; }
.task-item:nth-child(4) { animation-delay: 0.4s; }
.task-item:nth-child(5) { animation-delay: 0.5s; }
```

### **Hover Effects**
```css
@keyframes taskCardFloat {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-4px);
    }
}

.task-card:hover {
    animation: taskCardFloat 0.6s ease-in-out;
}
```

### **Transiciones de Botones**
```css
.task-action-btn {
    transition: var(--task-transition);
}

.task-action-btn:hover {
    transform: translateY(-1px);
    box-shadow: var(--task-shadow-hover);
}

.task-action-btn:active {
    transform: translateY(0);
    box-shadow: var(--task-shadow);
}
```

## 🎨 Estados Especiales

### **Estado Vacío**
```css
.tasks-empty {
    text-align: center;
    padding: 3rem 1.5rem;
    color: var(--task-text-muted);
}

.tasks-empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.tasks-empty-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--task-text-secondary);
}

.tasks-empty-text {
    font-size: 1rem;
    margin-bottom: 1.5rem;
    line-height: 1.6;
}
```

### **Estados de Carga y Error**
```css
.tasks-loading {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 3rem;
    color: var(--task-text-muted);
}

.tasks-loading i {
    font-size: 2rem;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.tasks-error {
    text-align: center;
    padding: 3rem 1.5rem;
    color: var(--task-error);
}
```

## 🔧 Utilidades CSS

### **Espaciado**
```css
.mb-0 { margin-bottom: 0; }
.mb-1 { margin-bottom: var(--arc-spacing-xs); }
.mb-2 { margin-bottom: var(--arc-spacing-sm); }
.mb-3 { margin-bottom: var(--arc-spacing-md); }
.mb-4 { margin-bottom: var(--arc-spacing-lg); }

.mt-0 { margin-top: 0; }
.mt-1 { margin-top: var(--arc-spacing-xs); }
.mt-2 { margin-top: var(--arc-spacing-sm); }
.mt-3 { margin-top: var(--arc-spacing-md); }
.mt-4 { margin-top: var(--arc-spacing-lg); }
```

### **Display y Flexbox**
```css
.d-flex { display: flex; }
.d-grid { display: grid; }
.d-none { display: none; }

.align-items-center { align-items: center; }
.justify-content-center { justify-content: center; }
.justify-content-between { justify-content: space-between; }
```

### **Texto**
```css
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.text-muted { color: var(--task-text-muted); }
.text-danger { color: var(--task-error); }
.text-primary { color: var(--task-primary); }
```

## 📚 Mejores Prácticas

### **1. Uso de Variables CSS**
- ✅ Siempre usar variables CSS para colores y espaciados
- ✅ Mantener consistencia en nombres de variables
- ✅ Agrupar variables relacionadas

### **2. Responsive Design**
- ✅ Mobile-first approach
- ✅ Breakpoints consistentes
- ✅ Flexbox y Grid para layouts complejos

### **3. Performance**
- ✅ Transiciones CSS en lugar de JavaScript
- ✅ Animaciones optimizadas con transform
- ✅ Lazy loading de estilos no críticos

### **4. Accesibilidad**
- ✅ Contraste de colores adecuado
- ✅ Estados de focus visibles
- ✅ Textos descriptivos para screen readers

### **5. Mantenibilidad**
- ✅ Clases semánticas y descriptivas
- ✅ Comentarios para secciones complejas
- ✅ Estructura modular y reutilizable

---

*Guía de estilos CSS del módulo de tareas - Sistema de diseño profesional para arquitectos*
