# ⚡ Quick Reference - Estilos ArqGest

Guía rápida de copiar y pegar para homologar vistas.

---

## 🎯 Template Base Completo

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
    
    <!-- HEADER -->
    <div class="header-section">
        <div class="header-content">
            <div class="header-title">
                <div class="header-icon">
                    <i class="fas fa-ICON"></i>
                </div>
                <div>
                    <h1>TÍTULO</h1>
                    <div class="text-muted">Descripción</div>
                </div>
            </div>
            <div class="d-flex gap-2">
                <a href="#" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Crear
                </a>
            </div>
        </div>
    </div>

    <!-- CONTENIDO AQUÍ -->
    
</div>
{% endblock %}
```

---

## 📦 Info Card - Copy/Paste

### Azul (General)
```html
<div class="col-md-6">
    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0; transition: all 0.3s;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-building" style="color: #3b82f6; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">ETIQUETA</div>
                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">Valor</div>
            </div>
        </div>
    </div>
</div>
```

### Verde (Estado/Completado)
```html
<div class="col-md-6">
    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0; transition: all 0.3s;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-check-circle" style="color: #10b981; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">ESTADO</div>
                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">Activo</div>
            </div>
        </div>
    </div>
</div>
```

### Amarillo (Fecha)
```html
<div class="col-md-6">
    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0; transition: all 0.3s;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-calendar-alt" style="color: #f59e0b; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">FECHA</div>
                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">01/01/2025</div>
            </div>
        </div>
    </div>
</div>
```

### Verde Oscuro (Dinero)
```html
<div class="col-md-6">
    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0; transition: all 0.3s;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-sack-dollar" style="color: #059669; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">PRESUPUESTO</div>
                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">$50,000</div>
            </div>
        </div>
    </div>
</div>
```

### Púrpura (Descripción)
```html
<div class="col-12">
    <div class="info-card p-3 rounded" style="background: white; border: 1px solid #e2e8f0;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <i class="fas fa-align-left" style="color: #8b5cf6; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">DESCRIPCIÓN</div>
                <div class="text-secondary" style="color: #475569; font-size: 0.95rem; line-height: 1.6;">Texto largo...</div>
            </div>
        </div>
    </div>
</div>
```

---

## 📊 Stats - Copy/Paste

```html
<div class="stats-compact">
    <div class="stat-item stat-total">
        <div class="stat-number">0</div>
        <div class="stat-label">Total</div>
    </div>
    <div class="stat-item stat-todo">
        <div class="stat-number">0</div>
        <div class="stat-label">Pendientes</div>
    </div>
    <div class="stat-item stat-progress">
        <div class="stat-number">0</div>
        <div class="stat-label">En Curso</div>
    </div>
    <div class="stat-item stat-done">
        <div class="stat-number">0</div>
        <div class="stat-label">Completadas</div>
    </div>
</div>
```

---

## 🔍 Búsqueda - Copy/Paste

```html
<div class="search-and-filters">
    <div class="search-section">
        <div class="search-box-enhanced">
            <i class="fas fa-search"></i>
            <input type="text" 
                   id="searchInput" 
                   placeholder="Buscar..." 
                   class="search-input-enhanced">
            <button type="button" class="search-clear" id="clearSearch" style="display: none;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
    
    <div class="filters-section">
        <div class="filter-pills">
            <div class="filter-pill">
                <select id="filterSelect" class="filter-select-modern">
                    <option value="">Todos</option>
                    <option value="1">Opción 1</option>
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
</div>
```

---

## 📋 Tabla - Copy/Paste

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
                {% for item in items %}
                <tr>
                    <td>{{ item.campo1 }}</td>
                    <td>{{ item.campo2 }}</td>
                    <td>
                        <button class="btn btn-sm btn-primary">Ver</button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
```

---

## 🔘 Botones - Copy/Paste

### Primario
```html
<a href="#" class="btn btn-primary">
    <i class="fas fa-plus"></i> Crear
</a>
```

### Secundario
```html
<a href="#" class="btn btn-secondary">
    <i class="fas fa-cog"></i> Configurar
</a>
```

### Acciones en Cards
```html
<div class="task-simple-actions">
    <button type="button" class="btn-action btn-view">
        <i class="fas fa-eye"></i>
        <span>Ver</span>
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

## 📈 Barra de Progreso - Copy/Paste

```html
<div class="mb-4 p-3 rounded" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-left: 4px solid #3b82f6;">
    <div class="d-flex justify-content-between align-items-center mb-2">
        <span class="text-muted" style="font-size: 0.875rem; font-weight: 600;">
            Progreso general
        </span>
        <span class="badge bg-primary" style="font-size: 0.9rem; padding: 0.35rem 0.75rem;">
            {{ porcentaje }}%
        </span>
    </div>
    <div class="progress" style="height: 12px; border-radius: 8px; background-color: #e2e8f0;">
        <div class="progress-bar" role="progressbar" 
             style="width: {{ porcentaje }}%; background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); border-radius: 8px;" 
             aria-valuenow="{{ porcentaje }}" 
             aria-valuemin="0" 
             aria-valuemax="100">
        </div>
    </div>
</div>
```

---

## 🎴 Card Simple - Copy/Paste

```html
<div class="card mt-3 border-0 shadow-sm">
    <div class="card-body p-4">
        <h3 class="mb-4" style="font-weight: 700; font-size: 1.25rem; color: #1e293b;">
            <i class="fas fa-info-circle text-primary me-2"></i>
            Título de la Sección
        </h3>
        
        <!-- Contenido aquí -->
        
    </div>
</div>
```

---

## 🎨 Paleta de Colores

### Iconos y Gradientes

```css
/* Azul - General */
background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
color: #3b82f6;

/* Verde - Éxito/Activo */
background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
color: #10b981;

/* Amarillo - Advertencia/Fecha */
background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
color: #f59e0b;

/* Verde Oscuro - Dinero */
background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
color: #059669;

/* Púrpura - Descripción */
background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
color: #8b5cf6;
```

---

## 📐 Espaciado

### Gaps
```html
gap-2  = 0.5rem (8px)
gap-3  = 1rem (16px)
gap-4  = 1.5rem (24px)
```

### Padding
```html
p-2  = 0.5rem (8px)
p-3  = 1rem (16px)
p-4  = 1.5rem (24px)
```

### Margin
```html
mb-2  = 0.5rem (8px)
mb-3  = 1rem (16px)
mb-4  = 1.5rem (24px)
```

### Grid Gaps
```html
<div class="row g-2">  <!-- 0.5rem -->
<div class="row g-3">  <!-- 1rem -->
<div class="row g-4">  <!-- 1.5rem -->
```

---

## 🔤 Tipografía

### Títulos
```html
h1: 1.75rem (28px) - peso 700
h2: 1.5rem (24px) - peso 700
h3: 1.25rem (20px) - peso 700
```

### Tamaños de Texto
```css
Muy pequeño: 0.75rem (12px)
Pequeño: 0.875rem (14px)
Normal: 1rem (16px)
Grande: 1.125rem (18px)
```

---

## 📱 Grid Columns

### Layouts Comunes

```html
<!-- 2 columnas en desktop -->
<div class="row g-4">
    <div class="col-md-6">...</div>
    <div class="col-md-6">...</div>
</div>

<!-- 3 columnas en desktop -->
<div class="row g-4">
    <div class="col-md-4">...</div>
    <div class="col-md-4">...</div>
    <div class="col-md-4">...</div>
</div>

<!-- Ancho completo -->
<div class="row g-4">
    <div class="col-12">...</div>
</div>

<!-- Sidebar + Contenido -->
<div class="row g-4">
    <div class="col-md-8">...</div>
    <div class="col-md-4">...</div>
</div>
```

---

## ⚡ Iconos Comunes

```
Cliente:        fa-building
Usuario:        fa-user-tie
Estado:         fa-check-circle
Fecha:          fa-calendar-alt
Dinero:         fa-sack-dollar
Descripción:    fa-align-left
Proyecto:       fa-project-diagram
Tarea:          fa-tasks
Archivo:        fa-file-alt
Configuración:  fa-cog
Editar:         fa-edit
Eliminar:       fa-trash
Ver:            fa-eye
Buscar:         fa-search
Filtrar:        fa-filter
Limpiar:        fa-eraser
Agregar:        fa-plus
```

---

## 🎯 Orden de Componentes (Recomendado)

```
1. Header Section (con título e icono)
2. Stats Compactas (opcional)
3. Búsqueda y Filtros (opcional)
4. Card de Información Principal
   - Info Cards (grid)
   - Barra de Progreso (si aplica)
5. Tabla o Lista de Elementos
6. Paginación (si aplica)
```

---

## ✅ Checklist Rápida

- [ ] Header con gradiente azul y icono
- [ ] Info cards con iconos de colores
- [ ] Etiquetas en MAYÚSCULAS pequeñas
- [ ] Valores destacados 1rem
- [ ] Gaps consistentes (g-4)
- [ ] Padding p-3 en cards
- [ ] Bordes #e2e8f0
- [ ] Botones con gradientes
- [ ] Iconos Font Awesome
- [ ] Responsive col-md-*

---

**Versión**: 1.0  
**Fecha**: Noviembre 26, 2025
