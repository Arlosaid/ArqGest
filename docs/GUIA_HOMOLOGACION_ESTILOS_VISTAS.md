# 🎨 Guía de Homologación de Estilos - ArqGest

## 📋 Tabla de Contenidos
1. [Estructura General](#estructura-general)
2. [Header Section](#header-section)
3. [Info Cards (Recuadros de Información)](#info-cards)
4. [Estadísticas y Métricas](#estadísticas-y-métricas)
5. [Búsqueda y Filtros](#búsqueda-y-filtros)
6. [Botones y Acciones](#botones-y-acciones)
7. [Tablas](#tablas)
8. [Cards de Contenido](#cards-de-contenido)
9. [Ejemplos de Implementación](#ejemplos-de-implementación)

---

## 🏗️ Estructura General

### Container Principal
```html
<div class="page-container">
    <!-- Todo el contenido de la página -->
</div>
```

**CSS de referencia**: `base.css`
- **Padding**: `var(--arc-spacing-xl)` (normalmente 2rem)
- **Background**: `var(--arc-bg-primary)` (blanco)
- **Max-width**: Responsive, se ajusta automáticamente

---

## 📌 Header Section

### Estructura Completa del Header

```html
<div class="header-section">
    <div class="header-content">
        <div class="header-title">
            <!-- Opcional: Icono de la sección -->
            <div class="header-icon">
                <i class="fas fa-user-check"></i>
            </div>
            
            <!-- Título y subtítulo -->
            <div>
                <h1>Título de la Vista</h1>
                <div class="text-muted">Descripción breve de la vista</div>
            </div>
        </div>
        
        <!-- Botones de acción principales -->
        <div class="d-flex gap-2">
            <a href="#" class="btn btn-primary">
                <i class="fas fa-plus"></i> Crear Nuevo
            </a>
        </div>
    </div>
</div>
```

### Estilos del Header

**Referencia**: `base.css` líneas 152-205

```css
.header-section {
    background: linear-gradient(135deg, #f8faff 0%, #eef5ff 100%);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    border: 1px solid #e8f2ff;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--arc-spacing-md);
}

.header-title {
    display: flex;
    align-items: center;
    gap: var(--arc-spacing-sm);
}

.header-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--arc-color-primary), var(--arc-color-primary-hover));
    border-radius: var(--arc-border-radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.25rem;
    flex-shrink: 0;
}

.header-title h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--arc-text-primary);
    margin: 0;
    line-height: 1.2;
}

.header-title .text-muted {
    font-size: 0.875rem;
    color: var(--arc-text-secondary);
    margin: 0;
    font-weight: 400;
    line-height: 1.3;
}
```

### Características Clave del Header
- ✅ Gradiente azul claro de fondo
- ✅ Bordes redondeados (16px)
- ✅ Sombra suave
- ✅ Icono cuadrado con gradiente azul
- ✅ Título grande y destacado
- ✅ Subtítulo descriptivo en gris
- ✅ Botones de acción alineados a la derecha

---

## 📦 Info Cards (Recuadros de Información)

### Estructura de Info Card

**Referencia**: `project_detail.html` líneas 133-218

```html
<div class="row g-4">
    <div class="col-md-6">
        <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0; transition: all 0.3s;">
            <div class="d-flex align-items-start gap-3">
                <!-- Icono con gradiente de color -->
                <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-building" style="color: #3b82f6; font-size: 1.1rem;"></i>
                </div>
                
                <!-- Contenido -->
                <div class="flex-grow-1">
                    <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                        ETIQUETA
                    </div>
                    <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">
                        Contenido Principal
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Paleta de Colores para Info Cards

#### 🔵 Azul (General, Cliente, Propietario)
```css
background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
color: #3b82f6;
```

#### 🟢 Verde (Estado Activo, Completado)
```css
background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
color: #10b981;
```

#### 🟡 Amarillo (Fecha, Calendario)
```css
background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
color: #f59e0b;
```

#### 💚 Verde Oscuro (Presupuesto, Dinero)
```css
background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
color: #059669;
```

#### 🟣 Púrpura (Descripción, Texto Largo)
```css
background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
color: #8b5cf6;
```

### Grid de Info Cards

```html
<div class="row g-4">
    <!-- col-md-6 para 2 columnas -->
    <!-- col-md-4 para 3 columnas -->
    <!-- col-12 para ancho completo (descripciones) -->
</div>
```

### Características de Info Cards
- ✅ Fondo blanco con borde gris claro
- ✅ Padding: `p-3` (0.75rem)
- ✅ Gap entre icono y contenido: `gap-3` (1rem)
- ✅ Icono cuadrado 40x40px con gradiente
- ✅ Etiqueta en mayúsculas, pequeña y gris
- ✅ Contenido principal oscuro y destacado
- ✅ Altura igual en la misma fila: `h-100`

---

## 📊 Estadísticas y Métricas

### Stats Compactas (Estilo Tareas)

**Referencia**: `my_tasks.html` líneas 23-46

```html
<div class="stats-compact">
    <div class="stat-item stat-total">
        <div class="stat-number">25</div>
        <div class="stat-label">Total</div>
    </div>
    <div class="stat-item stat-todo">
        <div class="stat-number">10</div>
        <div class="stat-label">Pendientes</div>
    </div>
    <div class="stat-item stat-progress">
        <div class="stat-number">8</div>
        <div class="stat-label">En Curso</div>
    </div>
    <div class="stat-item stat-done">
        <div class="stat-number">7</div>
        <div class="stat-label">Completadas</div>
    </div>
</div>
```

### CSS de Stats Compactas

**Referencia**: `my_tasks_page.css` líneas 30-68

```css
.stats-compact {
    display: flex;
    gap: var(--arc-spacing-lg);
    margin-top: var(--arc-spacing-lg);
    flex-wrap: wrap;
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: var(--arc-spacing-md);
    background: var(--arc-bg-secondary);
    border-radius: var(--arc-border-radius-sm);
    border: 1px solid var(--arc-border-color);
    min-width: 80px;
    cursor: pointer;
}

.stat-item:hover {
    background: var(--arc-bg-tertiary);
}

.stat-number {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--arc-text-primary);
    line-height: 1;
}

.stat-label {
    font-size: 0.75rem;
    color: var(--arc-text-secondary);
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-top: var(--arc-spacing-xs);
}
```

### Colores de Estados para Stats

```css
.stat-total .stat-number { color: var(--arc-text-primary); }
.stat-todo .stat-number { color: var(--arc-color-secondary); }
.stat-progress .stat-number { color: var(--arc-color-primary); }
.stat-paused .stat-number { color: var(--arc-color-warning); }
.stat-done .stat-number { color: var(--arc-color-success); }
```

### Stats Inline (Estilo Proyectos)

**Referencia**: `project_list.html` líneas 38-51

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

---

## 🔍 Búsqueda y Filtros

### Caja de Búsqueda Mejorada

**Referencia**: `my_tasks.html` líneas 49-57

```html
<div class="search-and-filters">
    <div class="search-section">
        <div class="search-box-enhanced">
            <i class="fas fa-search"></i>
            <input type="text" 
                   id="taskSearch" 
                   placeholder="Buscar tareas, proyectos o fases..." 
                   class="search-input-enhanced">
            <button type="button" class="search-clear" id="clearSearch" style="display: none;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
</div>
```

### CSS de Búsqueda

**Referencia**: `my_tasks_page.css` líneas 74-129

```css
.search-and-filters {
    background: var(--arc-bg-primary);
    padding: var(--arc-spacing-md);
    border-radius: var(--arc-border-radius);
    border: 1px solid var(--arc-border-color);
    margin-bottom: var(--arc-spacing-lg);
}

.search-box-enhanced {
    position: relative;
    max-width: 320px;
}

.search-box-enhanced i {
    position: absolute;
    left: var(--arc-spacing-sm);
    top: 50%;
    transform: translateY(-50%);
    color: var(--arc-text-muted);
    font-size: 0.875rem;
}

.search-input-enhanced {
    width: 100%;
    padding: var(--arc-spacing-sm) var(--arc-spacing-lg) var(--arc-spacing-sm) 2rem;
    border: 1px solid var(--arc-border-color);
    border-radius: var(--arc-border-radius-sm);
    font-size: 0.875rem;
    background: var(--arc-bg-primary);
    color: var(--arc-text-primary);
}

.search-input-enhanced:focus {
    outline: none;
    border-color: var(--arc-color-primary);
}
```

### Filtros Modernos

```html
<div class="filters-section">
    <div class="filter-pills">
        <div class="filter-pill">
            <select id="statusFilter" class="filter-select-modern">
                <option value="">Todos los estados</option>
                <option value="TODO">📋 Pendientes</option>
                <option value="IN_PROGRESS">⚡ En Progreso</option>
                <option value="DONE">✅ Completadas</option>
            </select>
        </div>
        
        <div class="filter-pill">
            <button type="button" id="clearFiltersBtn" class="clear-filters-btn">
                <i class="fas fa-eraser"></i>
                <span>Limpiar filtros</span>
            </button>
        </div>
    </div>
</div>
```

---

## 🔘 Botones y Acciones

### Botón Primario

```html
<a href="#" class="btn btn-primary">
    <i class="fas fa-plus"></i> Crear Nuevo
</a>
```

### CSS de Botones Primarios

**Referencia**: `base.css` líneas 209-233

```css
.btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border: none;
    border-radius: var(--arc-border-radius-sm);
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: var(--arc-transition);
    text-decoration: none;
    background: linear-gradient(135deg, var(--arc-color-primary), var(--arc-color-primary-hover));
    color: white !important;
    box-shadow: var(--arc-shadow-sm);
}

.btn-primary:hover {
    background: linear-gradient(135deg, var(--arc-color-primary-hover), #2451b8) !important;
    box-shadow: var(--arc-shadow-md);
    text-decoration: none;
    color: white !important;
    transform: translateY(-1px);
}
```

### Botón Secundario

```html
<a href="#" class="btn btn-secondary">
    <i class="fas fa-cog"></i> Configuración
</a>
```

```css
.btn-secondary {
    background: var(--arc-bg-primary);
    color: var(--arc-text-secondary);
    border: 1px solid var(--arc-border-color);
}

.btn-secondary:hover {
    background: var(--arc-bg-tertiary);
    border-color: var(--arc-text-secondary);
    text-decoration: none;
}
```

### Botones de Acción en Cards

**Referencia**: `project_detail.css` líneas 585-674

```html
<div class="task-simple-actions">
    <button type="button" class="btn-action btn-view">
        <i class="fas fa-eye"></i>
        <span>Ver detalles</span>
    </button>
    <button type="button" class="btn-action btn-edit">
        <i class="fas fa-edit"></i>
        <span>Editar</span>
    </button>
    <button type="button" class="btn-action btn-delete">
        <i class="fas fa-trash"></i>
        <span>Eliminar</span>
    </button>
</div>
```

---

## 📋 Tablas

### Estructura de Tabla Moderna

```html
<div class="table-container">
    <div class="table-header">
        <h3>Título de la Tabla</h3>
        <div class="d-flex gap-2">
            <button class="btn btn-primary">
                <i class="fas fa-plus"></i> Agregar
            </button>
        </div>
    </div>
    
    <div class="table-wrapper">
        <table class="modern-table">
            <thead>
                <tr>
                    <th>Columna 1</th>
                    <th>Columna 2</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Dato 1</td>
                    <td>Dato 2</td>
                    <td>
                        <button class="btn btn-sm btn-primary">Ver</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

### CSS de Tablas

**Referencia**: `base.css` líneas 266-321

```css
.table-container {
    background: var(--arc-bg-primary);
    border-radius: var(--arc-border-radius);
    box-shadow: var(--arc-shadow-sm);
    border: 1px solid var(--arc-border-color);
    overflow: hidden;
    margin-bottom: var(--arc-spacing-md);
    width: 100%;
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem;
    background: var(--arc-bg-tertiary);
    border-bottom: 1px solid var(--arc-border-color);
    flex-wrap: wrap;
    gap: 1rem;
}

.table-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
}

.modern-table {
    width: 100%;
    border-collapse: collapse;
}

.modern-table th {
    padding: 1rem;
    background: #f8fafc;
    border-bottom: 2px solid var(--arc-border-color);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.8rem;
    color: #374151;
    letter-spacing: 0.5px;
    text-align: left;
}

.modern-table td {
    padding: 1.25rem 1rem;
    border-bottom: 1px solid var(--arc-border-color);
    vertical-align: middle;
    color: #1e293b;
    background: #ffffff;
    font-size: 0.875rem;
}

.modern-table tbody tr:hover {
    background: rgba(66, 133, 244, 0.05);
}
```

---

## 🎴 Cards de Contenido

### Card Básica

```html
<div class="card mt-3 border-0 shadow-sm">
    <div class="card-body p-4">
        <h3 class="mb-4" style="font-weight: 700; font-size: 1.25rem; color: #1e293b;">
            <i class="fas fa-info-circle text-primary me-2"></i>
            Título de la Card
        </h3>
        
        <!-- Contenido de la card -->
        
    </div>
</div>
```

### Barra de Progreso

**Referencia**: `project_detail.html` líneas 115-127

```html
<div class="mb-4 p-3 rounded" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-left: 4px solid #3b82f6;">
    <div class="d-flex justify-content-between align-items-center mb-2">
        <span class="text-muted" style="font-size: 0.875rem; font-weight: 600;">
            Progreso general
        </span>
        <span class="badge bg-primary" style="font-size: 0.9rem; padding: 0.35rem 0.75rem;">
            75%
        </span>
    </div>
    <div class="progress" style="height: 12px; border-radius: 8px; background-color: #e2e8f0;">
        <div class="progress-bar" role="progressbar" 
             style="width: 75%; background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); border-radius: 8px;" 
             aria-valuenow="75" 
             aria-valuemin="0" 
             aria-valuemax="100">
        </div>
    </div>
</div>
```

---

## 🎯 Ejemplos de Implementación

### Ejemplo 1: Vista de Lista Simple

```html
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block title %}Mi Vista - ArqGest{% endblock %}

{% block extra_css %}
<link href="{% static 'css/mi-vista.css' %}" rel="stylesheet">
{% endblock %}

{% block content %}
<div class="page-container">
    
    <!-- Header Section -->
    <div class="header-section">
        <div class="header-content">
            <div class="header-title">
                <div class="header-icon">
                    <i class="fas fa-list"></i>
                </div>
                <div>
                    <h1>{% trans "Mi Vista" %}</h1>
                    <div class="text-muted">{% trans "Gestiona tus elementos" %}</div>
                </div>
            </div>
            <div class="d-flex gap-2">
                <a href="#" class="btn btn-primary">
                    <i class="fas fa-plus"></i> {% trans "Crear Nuevo" %}
                </a>
            </div>
        </div>
    </div>

    <!-- Tabla de Contenido -->
    <div class="table-container">
        <div class="table-header">
            <h3>{% trans "Lista de Elementos" %}</h3>
        </div>
        
        <div class="table-wrapper">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>{% trans "Nombre" %}</th>
                        <th>{% trans "Estado" %}</th>
                        <th>{% trans "Acciones" %}</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>{{ item.name }}</td>
                        <td>{{ item.get_status_display }}</td>
                        <td>
                            <button class="btn btn-sm btn-primary">
                                <i class="fas fa-eye"></i> Ver
                            </button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
</div>
{% endblock %}
```

### Ejemplo 2: Vista de Detalle

```html
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block title %}{{ item.name }} - ArqGest{% endblock %}

{% block content %}
<div class="page-container">
    
    <!-- Header Section -->
    <div class="header-section">
        <div class="header-content">
            <div class="header-title">
                <a href="{% url 'mi-lista' %}" class="btn btn-light border me-3">
                    <i class="fas fa-arrow-left"></i>
                </a>
                <div class="header-icon">
                    <i class="fas fa-file-alt"></i>
                </div>
                <div>
                    <h1>{{ item.name }}</h1>
                    <div class="text-muted">{{ item.description|truncatechars:50 }}</div>
                </div>
            </div>
            <div class="d-flex gap-2">
                <a href="{% url 'mi-editar' item.pk %}" class="btn btn-primary">
                    <i class="fas fa-edit"></i> {% trans "Editar" %}
                </a>
            </div>
        </div>
    </div>

    <!-- Card de Información -->
    <div class="card mt-3 border-0 shadow-sm">
        <div class="card-body p-4">
            <h3 class="mb-4" style="font-weight: 700; font-size: 1.25rem; color: #1e293b;">
                <i class="fas fa-info-circle text-primary me-2"></i>
                {% trans "Información del Elemento" %}
            </h3>
            
            <!-- Grid de Info Cards -->
            <div class="row g-4">
                <!-- Cliente -->
                <div class="col-md-6">
                    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0;">
                        <div class="d-flex align-items-start gap-3">
                            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-building" style="color: #3b82f6; font-size: 1.1rem;"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                                    {% trans "Cliente" %}
                                </div>
                                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">
                                    {{ item.cliente.name }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Estado -->
                <div class="col-md-6">
                    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0;">
                        <div class="d-flex align-items-start gap-3">
                            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-check-circle" style="color: #10b981; font-size: 1.1rem;"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                                    {% trans "Estado" %}
                                </div>
                                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">
                                    {{ item.get_status_display }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Descripción (ancho completo) -->
                <div class="col-12">
                    <div class="info-card p-3 rounded" style="background: white; border: 1px solid #e2e8f0;">
                        <div class="d-flex align-items-start gap-3">
                            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i class="fas fa-align-left" style="color: #8b5cf6; font-size: 1.1rem;"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                                    {% trans "Descripción" %}
                                </div>
                                <div class="text-secondary" style="color: #475569; font-size: 0.95rem; line-height: 1.6;">
                                    {{ item.description }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
</div>
{% endblock %}
```

---

## 📱 Responsive

### Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
    .header-section {
        padding: 1.5rem;
    }
    
    .header-title h1 {
        font-size: 1.5rem;
    }
    
    .stats-compact {
        gap: var(--arc-spacing-sm);
    }
    
    .stat-item {
        min-width: 70px;
    }
}

/* Tablet */
@media (max-width: 1024px) {
    .row.g-4 {
        gap: 1rem !important;
    }
}
```

---

## 🎨 Variables CSS Importantes

```css
/* Colores */
--arc-color-primary: #4285f4;
--arc-color-primary-hover: #3367d6;
--arc-color-success: #10b981;
--arc-color-warning: #f59e0b;
--arc-color-danger: #ef4444;
--arc-color-secondary: #64748b;

/* Backgrounds */
--arc-bg-primary: #ffffff;
--arc-bg-secondary: #f8fafc;
--arc-bg-tertiary: #f1f5f9;

/* Text */
--arc-text-primary: #1e293b;
--arc-text-secondary: #64748b;
--arc-text-muted: #94a3b8;

/* Borders */
--arc-border-color: #e2e8f0;
--arc-border-radius: 10px;
--arc-border-radius-sm: 8px;

/* Spacing */
--arc-spacing-xs: 0.25rem;
--arc-spacing-sm: 0.5rem;
--arc-spacing-md: 1rem;
--arc-spacing-lg: 1.5rem;
--arc-spacing-xl: 2rem;

/* Shadows */
--arc-shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.08);
--arc-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--arc-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
```

---

## ✅ Checklist de Homologación

Al homologar una vista, asegúrate de:

- [ ] Usar `<div class="page-container">` como contenedor principal
- [ ] Implementar el `header-section` con gradiente azul
- [ ] Incluir icono cuadrado con gradiente en el header
- [ ] Usar info-cards con iconos de colores apropiados
- [ ] Aplicar la paleta de colores correcta según el tipo de información
- [ ] Mantener consistencia en tamaños de fuente
- [ ] Usar las clases de Bootstrap para grids (col-md-6, col-12, etc.)
- [ ] Implementar botones con gradientes y sombras
- [ ] Asegurar que las tablas usen `modern-table`
- [ ] Verificar responsive en móvil y tablet
- [ ] Usar variables CSS en lugar de valores hardcodeados
- [ ] Mantener el espaciado consistente (g-4 para grids)

---

## 📚 Referencias de Archivos

### CSS Principal
- `arc_manager/static/css/base.css` - Estilos globales
- `arc_manager/static/css/project_detail.css` - Estilos de detalles
- `arc_manager/static/css/my_tasks_page.css` - Estilos de tareas

### Templates de Referencia
- `arc_manager/apps/projects/templates/projects/project_detail.html`
- `arc_manager/apps/projects/templates/projects/project_list.html`
- `arc_manager/apps/projects/templates/projects/my_tasks.html`

---

**Fecha de creación**: Noviembre 26, 2025  
**Última actualización**: Noviembre 26, 2025  
**Versión**: 1.0
