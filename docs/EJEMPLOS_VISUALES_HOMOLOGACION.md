# 🎨 Ejemplos Visuales de Homologación de Estilos

Este documento complementa la guía principal con ejemplos visuales comparativos.

---

## 📌 Componente: Header Section

### ✅ CORRECTO - Estilo Homologado

```html
<div class="header-section">
    <div class="header-content">
        <div class="header-title">
            <div class="header-icon">
                <i class="fas fa-user-check"></i>
            </div>
            <div>
                <h1>Mis Tareas</h1>
                <div class="text-muted">Gestiona y revisa tus tareas asignadas</div>
            </div>
        </div>
        <div class="d-flex gap-2">
            <a href="#" class="btn btn-primary">
                <i class="fas fa-plus"></i> Crear Nuevo
            </a>
        </div>
    </div>
</div>
```

**Características visuales:**
```
┌─────────────────────────────────────────────────────────┐
│  🔵  MIS TAREAS                     [+ Crear Nuevo]    │
│      Gestiona y revisa tus tareas asignadas             │
└─────────────────────────────────────────────────────────┘
```

- ✅ Fondo con gradiente azul claro (#f8faff → #eef5ff)
- ✅ Icono cuadrado 40x40px con gradiente azul
- ✅ Título grande (1.75rem) y subtítulo gris
- ✅ Bordes redondeados (16px)
- ✅ Sombra suave

### ❌ INCORRECTO - Sin Homologar

```html
<div class="page-header">
    <h2>Mis Tareas</h2>
    <button class="btn btn-success">Agregar</button>
</div>
```

**Problemas:**
- ❌ Sin fondo gradiente
- ❌ Sin icono
- ❌ Sin subtítulo descriptivo
- ❌ Botón con color diferente
- ❌ Sin estructura consistente

---

## 📦 Componente: Info Cards

### ✅ CORRECTO - Info Card con Icono y Gradiente

```html
<div class="col-md-6">
    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0; transition: all 0.3s;">
        <div class="d-flex align-items-start gap-3">
            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-building" style="color: #3b82f6; font-size: 1.1rem;"></i>
            </div>
            <div class="flex-grow-1">
                <div class="text-muted small mb-1" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                    CLIENTE
                </div>
                <div class="fw-semibold" style="color: #1e293b; font-size: 1rem;">
                    Constructora ABC S.A.
                </div>
            </div>
        </div>
    </div>
</div>
```

**Visualización:**
```
┌─────────────────────────────────────┐
│  🏢  CLIENTE                        │
│      Constructora ABC S.A.          │
└─────────────────────────────────────┘
```

- ✅ Icono con gradiente de color azul claro
- ✅ Etiqueta en mayúsculas pequeña
- ✅ Valor destacado y legible
- ✅ Padding consistente (p-3)

### ❌ INCORRECTO - Sin Estructura

```html
<div class="info-box">
    <p><strong>Cliente:</strong> Constructora ABC S.A.</p>
</div>
```

**Problemas:**
- ❌ Sin icono visual
- ❌ Sin separación clara entre etiqueta y valor
- ❌ Sin gradiente en el icono
- ❌ Estructura no estandarizada

---

## 🎨 Paleta de Colores para Info Cards

### Guía Visual de Colores

```html
<!-- 🔵 AZUL - General, Cliente, Propietario -->
<div class="info-icon-wrapper" style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);">
    <i class="fas fa-building" style="color: #3b82f6;"></i>
</div>

<!-- 🟢 VERDE - Estado Activo, Completado -->
<div class="info-icon-wrapper" style="background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);">
    <i class="fas fa-check-circle" style="color: #10b981;"></i>
</div>

<!-- 🟡 AMARILLO - Fecha, Calendario -->
<div class="info-icon-wrapper" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
    <i class="fas fa-calendar-alt" style="color: #f59e0b;"></i>
</div>

<!-- 💚 VERDE OSCURO - Presupuesto, Dinero -->
<div class="info-icon-wrapper" style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);">
    <i class="fas fa-sack-dollar" style="color: #059669;"></i>
</div>

<!-- 🟣 PÚRPURA - Descripción, Texto -->
<div class="info-icon-wrapper" style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);">
    <i class="fas fa-align-left" style="color: #8b5cf6;"></i>
</div>
```

**Matriz de Uso:**

| Tipo de Información | Color      | Icono Sugerido    | Ejemplo              |
|---------------------|------------|-------------------|----------------------|
| Cliente             | Azul       | fa-building       | Nombre de cliente    |
| Propietario         | Azul       | fa-user-tie       | Nombre de usuario    |
| Estado Activo       | Verde      | fa-check-circle   | Estado del proyecto  |
| Fecha               | Amarillo   | fa-calendar-alt   | Fecha de inicio      |
| Presupuesto         | Verde Osc. | fa-sack-dollar    | Monto en dinero      |
| Descripción         | Púrpura    | fa-align-left     | Texto descriptivo    |
| Progreso            | Azul       | fa-chart-line     | Porcentaje           |
| Ubicación           | Amarillo   | fa-map-marker-alt | Dirección            |

---

## 📊 Componente: Estadísticas

### ✅ CORRECTO - Stats Compactas

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

**Visualización:**
```
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│   25   │  │   10   │  │    8   │  │    7   │
│ Total  │  │Pend.   │  │En Curso│  │Compl.  │
└────────┘  └────────┘  └────────┘  └────────┘
```

- ✅ Números grandes y destacados
- ✅ Etiquetas en mayúsculas pequeñas
- ✅ Cada stat con su color específico
- ✅ Alineación centrada

### ❌ INCORRECTO - Sin Estructura

```html
<div class="stats">
    <span>Total: 25</span> | 
    <span>Pendientes: 10</span> | 
    <span>En Curso: 8</span>
</div>
```

**Problemas:**
- ❌ Sin separación visual clara
- ❌ Sin énfasis en los números
- ❌ Sin colores específicos
- ❌ No es scannable rápidamente

---

## 🔍 Componente: Búsqueda y Filtros

### ✅ CORRECTO - Búsqueda Mejorada

```html
<div class="search-and-filters">
    <div class="search-section">
        <div class="search-box-enhanced">
            <i class="fas fa-search"></i>
            <input type="text" 
                   id="searchInput" 
                   placeholder="Buscar proyectos, clientes..." 
                   class="search-input-enhanced">
            <button type="button" class="search-clear" style="display: none;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
    
    <div class="filters-section">
        <div class="filter-pills">
            <div class="filter-pill">
                <select class="filter-select-modern">
                    <option value="">Todos los estados</option>
                    <option value="active">Activos</option>
                    <option value="archived">Archivados</option>
                </select>
            </div>
            
            <div class="filter-pill">
                <button type="button" class="clear-filters-btn">
                    <i class="fas fa-eraser"></i>
                    <span>Limpiar filtros</span>
                </button>
            </div>
        </div>
    </div>
</div>
```

**Visualización:**
```
┌─────────────────────────────────────────────────────────┐
│  🔍 Buscar proyectos, clientes...                    ×  │
│                                                          │
│  [Todos los estados ▼]  [🧹 Limpiar filtros]           │
└─────────────────────────────────────────────────────────┘
```

- ✅ Icono de búsqueda a la izquierda
- ✅ Botón para limpiar a la derecha
- ✅ Filtros en pills separados
- ✅ Borde y padding consistentes

### ❌ INCORRECTO - Búsqueda Básica

```html
<input type="text" placeholder="Buscar...">
<select>
    <option>Filtrar</option>
</select>
```

**Problemas:**
- ❌ Sin iconos visuales
- ❌ Sin estructura contenedora
- ❌ Sin botón de limpiar
- ❌ Sin estilos mejorados

---

## 📋 Componente: Tablas

### ✅ CORRECTO - Tabla Moderna

```html
<div class="table-container">
    <div class="table-header">
        <h3>Lista de Proyectos</h3>
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
                    <th>NOMBRE</th>
                    <th>CLIENTE</th>
                    <th>ESTADO</th>
                    <th>ACCIONES</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Casa Residencial</td>
                    <td>Juan Pérez</td>
                    <td>Activo</td>
                    <td>
                        <button class="btn btn-sm btn-primary">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

**Visualización:**
```
┌─────────────────────────────────────────────────────────┐
│  Lista de Proyectos                    [+ Agregar]      │
├─────────────────────────────────────────────────────────┤
│  NOMBRE           │ CLIENTE      │ ESTADO   │ ACCIONES │
├───────────────────┼──────────────┼──────────┼──────────┤
│  Casa Residencial │ Juan Pérez   │ Activo   │   [👁]   │
└─────────────────────────────────────────────────────────┘
```

- ✅ Header con título y botón
- ✅ Thead con columnas en mayúsculas
- ✅ Padding generoso en celdas
- ✅ Hover suave en filas

### ❌ INCORRECTO - Tabla Básica

```html
<table class="table">
    <tr>
        <th>Nombre</th>
        <th>Cliente</th>
    </tr>
    <tr>
        <td>Casa Residencial</td>
        <td>Juan Pérez</td>
    </tr>
</table>
```

**Problemas:**
- ❌ Sin contenedor
- ❌ Sin header con acciones
- ❌ Thead sin estilos
- ❌ Padding insuficiente

---

## 🔘 Componente: Botones

### ✅ CORRECTO - Botón Primario

```html
<a href="#" class="btn btn-primary">
    <i class="fas fa-plus"></i> Crear Nuevo
</a>
```

**CSS aplicado:**
```css
background: linear-gradient(135deg, #4285f4, #3367d6);
color: white;
padding: 8px 16px;
border-radius: 8px;
box-shadow: 0 1px 3px rgba(0,0,0,0.08);
```

**Hover:**
```css
background: linear-gradient(135deg, #3367d6, #2451b8);
transform: translateY(-1px);
box-shadow: 0 4px 6px rgba(0,0,0,0.1);
```

### Tipos de Botones

```html
<!-- Botón Primario -->
<button class="btn btn-primary">
    <i class="fas fa-plus"></i> Primario
</button>

<!-- Botón Secundario -->
<button class="btn btn-secondary">
    <i class="fas fa-cog"></i> Secundario
</button>

<!-- Botón de Acción Ver -->
<button class="btn-action btn-view">
    <i class="fas fa-eye"></i> Ver
</button>

<!-- Botón de Acción Editar -->
<button class="btn-action btn-edit">
    <i class="fas fa-edit"></i> Editar
</button>

<!-- Botón de Acción Eliminar -->
<button class="btn-action btn-delete">
    <i class="fas fa-trash"></i> Eliminar
</button>
```

---

## 🎴 Componente: Cards de Progreso

### ✅ CORRECTO - Barra de Progreso

```html
<div class="mb-4 p-3 rounded" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-left: 4px solid #3b82f6;">
    <div class="d-flex justify-content-between align-items-center mb-2">
        <span class="text-muted" style="font-size: 0.875rem; font-weight: 600;">
            Progreso general del proyecto
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

**Visualización:**
```
┌─────────────────────────────────────────────────────────┐
│  Progreso general del proyecto                    75%   │
│  ███████████████████████████████░░░░░░░░░░░░░░░░░      │
└─────────────────────────────────────────────────────────┘
```

- ✅ Gradiente de fondo gris claro
- ✅ Borde izquierdo azul (4px)
- ✅ Badge con porcentaje
- ✅ Barra con gradiente azul
- ✅ Altura de 12px

---

## 🎯 Layout Completo - Ejemplo de Vista Homologada

```html
{% extends "base.html" %}
{% load i18n static %}

{% block title %}Mi Vista - ArqGest{% endblock %}

{% block extra_css %}
<link href="{% static 'css/mi-vista.css' %}" rel="stylesheet">
{% endblock %}

{% block content %}
<div class="page-container">
    
    <!-- 1. HEADER SECTION -->
    <div class="header-section">
        <div class="header-content">
            <div class="header-title">
                <div class="header-icon">
                    <i class="fas fa-project-diagram"></i>
                </div>
                <div>
                    <h1>Mis Proyectos</h1>
                    <div class="text-muted">Gestiona y organiza tus proyectos</div>
                </div>
            </div>
            <div class="d-flex gap-2">
                <a href="#" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Crear Nuevo
                </a>
            </div>
        </div>
    </div>

    <!-- 2. ESTADÍSTICAS -->
    <div class="stats-compact">
        <div class="stat-item stat-total">
            <div class="stat-number">42</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat-item stat-progress">
            <div class="stat-number">15</div>
            <div class="stat-label">Activos</div>
        </div>
        <div class="stat-item stat-done">
            <div class="stat-number">27</div>
            <div class="stat-label">Completados</div>
        </div>
    </div>

    <!-- 3. BÚSQUEDA Y FILTROS -->
    <div class="search-and-filters">
        <div class="search-section">
            <div class="search-box-enhanced">
                <i class="fas fa-search"></i>
                <input type="text" placeholder="Buscar..." class="search-input-enhanced">
            </div>
        </div>
        <div class="filters-section">
            <div class="filter-pills">
                <select class="filter-select-modern">
                    <option>Todos</option>
                </select>
                <button class="clear-filters-btn">
                    <i class="fas fa-eraser"></i> Limpiar
                </button>
            </div>
        </div>
    </div>

    <!-- 4. CONTENIDO PRINCIPAL -->
    <div class="card mt-3 border-0 shadow-sm">
        <div class="card-body p-4">
            <h3 class="mb-4" style="font-weight: 700; font-size: 1.25rem; color: #1e293b;">
                <i class="fas fa-info-circle text-primary me-2"></i>
                Información
            </h3>
            
            <!-- Info Cards -->
            <div class="row g-4">
                <div class="col-md-6">
                    <div class="info-card p-3 rounded h-100" style="background: white; border: 1px solid #e2e8f0;">
                        <div class="d-flex align-items-start gap-3">
                            <div class="info-icon-wrapper" style="width: 40px; height: 40px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
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
            </div>
        </div>
    </div>
    
</div>
{% endblock %}
```

---

## 📏 Espaciado Consistente

### Sistema de Gaps

```html
<!-- Gap pequeño (0.5rem / 8px) -->
<div class="d-flex gap-2">

<!-- Gap mediano (1rem / 16px) -->
<div class="d-flex gap-3">

<!-- Gap grande (1.5rem / 24px) -->
<div class="d-flex gap-4">

<!-- Grid gaps -->
<div class="row g-2">  <!-- 0.5rem -->
<div class="row g-3">  <!-- 1rem -->
<div class="row g-4">  <!-- 1.5rem -->
```

### Padding Consistente

```html
<!-- Padding pequeño -->
<div class="p-2">   <!-- 0.5rem -->

<!-- Padding mediano -->
<div class="p-3">   <!-- 1rem -->

<!-- Padding grande -->
<div class="p-4">   <!-- 1.5rem -->
```

---

## ✅ Checklist Visual Rápida

### Para cada nueva vista, verifica:

#### Header
- [ ] Fondo con gradiente azul claro
- [ ] Icono cuadrado 40x40px con gradiente
- [ ] Título h1 de 1.75rem
- [ ] Subtítulo en gris
- [ ] Botones alineados a la derecha

#### Info Cards
- [ ] Fondo blanco con borde #e2e8f0
- [ ] Icono 40x40px con gradiente de color
- [ ] Etiqueta en mayúsculas pequeña
- [ ] Valor destacado 1rem
- [ ] Padding p-3 consistente

#### Estadísticas
- [ ] Números grandes (1.5rem)
- [ ] Etiquetas pequeñas en mayúsculas
- [ ] Colores específicos por tipo
- [ ] Alineación centrada

#### Búsqueda
- [ ] Icono de lupa a la izquierda
- [ ] Input con padding adecuado
- [ ] Botón de limpiar a la derecha
- [ ] Borde y fondo consistentes

#### Botones
- [ ] Gradiente en primarios
- [ ] Icono + texto
- [ ] Sombra y hover
- [ ] Gap de 8px entre icono y texto

---

**Documento creado para**: ArqGest  
**Fecha**: Noviembre 26, 2025  
**Versión**: 1.0
