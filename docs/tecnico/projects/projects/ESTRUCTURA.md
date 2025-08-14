# 🏗️ Estructura del Módulo de Proyectos

## 📁 Archivos Principales

```
arc_manager/
├── apps/projects/
│   ├── templates/projects/
│   │   ├── project_list.html          # Lista principal (v2.4)
│   │   ├── project_detail.html        # Detalle de proyecto (v2.5 - Refactorizado)
│   │   ├── project_form.html          # Formulario de proyecto
│   │   ├── kanban_board.html          # Tablero Kanban
│   │   ├── task_list.html             # Lista de tareas
│   │   ├── my_tasks.html              # Mis tareas
│   │   ├── phase_detail.html          # Detalle de fase
│   │   ├── phasetemplate_list.html    # Lista de plantillas
│   │   ├── phasetemplate_detail.html  # Detalle de plantilla
│   │   ├── phasetemplate_form.html    # Formulario de plantilla
│   │   ├── project_confirm_delete.html # Confirmación de eliminación
│   │   ├── phasetemplate_confirm_delete.html
│   │   ├── defaultphase_confirm_delete.html
│   │   └── defaultphase_form.html
│   ├── views.py                       # Lógica backend
│   ├── models.py                      # Modelos de datos
│   └── urls.py                        # Rutas
├── static/css/projects.css            # Estilos (v2.4)
└── static/js/projects.js              # JavaScript (v1.2)
```

## 🎨 Componentes del Template Principal

### **1. Header Section (Estándar)**
```html
<div class="header-section">
    <div class="header-content">
        <div class="header-title">
            <div class="header-icon">
                <i class="fas fa-project-diagram"></i>
            </div>
            <h1>{% trans "Mis Proyectos" %}</h1>
        </div>
        <a href="{% url 'projects:project-create' %}" class="btn-primary-prominent">
            <i class="fas fa-plus"></i> {% trans "Crear Nuevo Proyecto" %}
        </a>
    </div>
</div>
```

### **2. Vista de Detalle de Proyecto (v2.5 - Refactorizada)**
```html
<div class="page-container">
    <!-- Header consistente con la app -->
    <div class="header-section">
        <div class="header-content">
            <div class="header-title">
                <div class="header-icon">
                    <i class="fas fa-folder-open"></i>
                </div>
                <div>
                    <h1>{{ project.name }}</h1>
                    <div class="text-muted">{{ project.client.name|default:"Sin cliente asignado" }}</div>
                </div>
            </div>
            <div class="d-flex gap-2">
                <a href="{% url 'projects:project-update' project.pk %}" class="btn btn-secondary">
                    <i class="fas fa-edit"></i> {% trans "Editar" %}
                </a>
                <a href="{% url 'projects:project-kanban' project.pk %}" class="btn btn-primary">
                    <i class="fas fa-columns"></i> {% trans "Kanban" %}
                </a>
            </div>
        </div>
        <!-- Breadcrumbs -->
        <nav aria-label="breadcrumb" class="mt-3">
            <ol class="breadcrumb mb-0">
                <li class="breadcrumb-item"><a href="{% url 'projects:project-list' %}">{% trans "Proyectos" %}</a></li>
                <li class="breadcrumb-item active" aria-current="page">{{ project.name }}</li>
            </ol>
        </nav>
    </div>

    <!-- Layout con Tabs (sin sidebar) -->
    <div class="left-content">
        <ul class="nav nav-tabs" id="projectTab" role="tablist">
            <li class="nav-item"><button class="nav-link active" data-bs-target="#details" data-bs-toggle="tab">Detalles</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-target="#phases" data-bs-toggle="tab">Fases</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-target="#tasks" data-bs-toggle="tab">Tareas</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-target="#files" data-bs-toggle="tab">Archivos</button></li>
        </ul>
        <div class="tab-content" id="projectTabContent">
            <!-- Contenido por pestaña -->
        </div>
    </div>
</div>
```

#### **Características de la Vista Refactorizada:**
- ✅ **Header unificado**: Usa `header-section` con icono, título y acciones
- ✅ **Tabs principales**: `Detalles`, `Fases`, `Tareas`, `Archivos`
- ✅ **Sin sidebar**: foco total en el contenido funcional
- ✅ **Progreso Bootstrap**: componente nativo
- ✅ **Responsive**: se adapta a todos los dispositivos

### **3. Filtro Ultra Compacto**
```html
<div class="projects-filters-modern">
    <div class="filters-header-modern">
        <h3 class="filters-title-modern">{% trans "Filtros" %}</h3>
        <span class="search-results-counter" style="display: none;"></span>
    </div>
    <form class="filters-form-modern">
        <div class="search-box-modern">
            <input type="text" class="search-input-modern" placeholder="{% trans 'Buscar proyectos por nombre...' %}" name="search">
        </div>
    </form>
</div>
```

### **4. Grid de Proyectos Profesional**
```html
<div class="projects-grid-modern">
    {% for project in projects %}
    <div class="project-card-modern" data-project-date="{{ project.created_at|date:'Y-m-d' }}">
        <div class="project-card-header-modern">
            <div class="project-card-badge">
                <span class="project-status-modern {{ project.get_phase_display|lower }}">
                    {{ project.get_phase_display }}
                </span>
            </div>
            <div class="project-card-menu">
                <button class="btn-card-menu" data-project-id="{{ project.pk }}">
                    <i class="fas fa-ellipsis-v"></i>
                </button>
            </div>
        </div>
        
        <div class="project-card-body-modern">
            <h3 class="project-card-title-modern">{{ project.name }}</h3>
            
            <!-- Información estructurada del proyecto -->
            <div class="project-card-info-modern">
                <div class="info-item-modern">
                    <span class="info-label-modern">{% trans "Cliente" %}</span>
                    <span class="info-value-modern">{{ project.client.name|default:"No asignado" }}</span>
                </div>
                <div class="info-item-modern">
                    <span class="info-label-modern">{% trans "Fase" %}</span>
                    <span class="info-value-modern">{{ project.get_phase_display }}</span>
                </div>
                <div class="info-item-modern">
                    <span class="info-label-modern">{% trans "Fecha Inicio" %}</span>
                    <span class="info-value-modern">{{ project.created_at|date:"d/m/Y" }}</span>
                </div>
                <div class="info-item-modern">
                    <span class="info-label-modern">{% trans "Última Actualización" %}</span>
                    <span class="info-value-modern">{{ project.updated_at|date:"d/m/Y" }}</span>
                </div>
            </div>
            
            <div class="project-card-progress-modern">
                <div class="progress-header-modern">
                    <span class="progress-label">{% trans "Progreso General" %}</span>
                    <span class="progress-value">{{ project.progress|default:"0" }}%</span>
                </div>
                <div class="progress-bar-modern">
                    <div class="progress-fill-modern" style="width: {{ project.progress|default:'0' }}%"></div>
                </div>
            </div>
            
            <div class="project-card-meta-modern">
                <div class="meta-item-modern">
                    <i class="fas fa-calendar-alt"></i>
                    <span>{{ project.created_at|date:"d/m/Y" }}</span>
                </div>
                <div class="meta-item-modern">
                    <i class="fas fa-clock"></i>
                    <span>{{ project.updated_at|timesince }}</span>
                </div>
            </div>
        </div>
        
        <div class="project-card-footer-modern">
            <div class="project-actions-modern">
                <a href="{% url 'projects:project-detail' project.pk %}" class="btn-action-modern btn-view-modern">
                    <i class="fas fa-eye"></i> {% trans "Ver" %}
                </a>
                <a href="{% url 'projects:project-update' project.pk %}" class="btn-action-modern btn-edit-modern">
                    <i class="fas fa-edit"></i> {% trans "Editar" %}
                </a>
                {% if user.is_org_admin %}
                <a href="{% url 'projects:project-delete' project.pk %}" class="btn-action-modern btn-delete-modern">
                    <i class="fas fa-trash"></i> {% trans "Eliminar" %}
                </a>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

## 🎯 Jerarquía de Componentes

```
projects-module
├── header-section (estándar)
├── projects-filters-modern (ultra compacto)
│   ├── filters-header-modern
│   └── filters-form-modern
└── projects-grid-modern
    └── project-card-modern
        ├── project-card-header-modern
        ├── project-card-body-modern
        └── project-card-footer-modern

kanban-board
├── kanban-board (contenedor)
└── kanban-column (x4: TODO, IN_PROGRESS, PAUSED, DONE)
    ├── kanban-column-header
    │   ├── column-title (título estado)
    │   └── task-count (contador por columna)
    └── kanban-column-body
        ├── kanban-card (tarjeta de tarea)
        └── empty-column (estado vacío con icono de casco)
```

## 🎨 Sistema de Diseño Profesional

### **Variables CSS Profesionales**
```css
.projects-module {
    --primary: #3b82f6;           /* Azul principal */
    --primary-dark: #2563eb;      /* Azul oscuro */
    --primary-light: #dbeafe;     /* Azul claro */
    --accent: #3498db;            /* Azul acento */
    --success: #27ae60;           /* Verde */
    --warning: #f39c12;           /* Amarillo */
    --error: #e74c3c;             /* Rojo */
    --text: #2c3e50;              /* Texto principal */
    --text-secondary: #7f8c8d;    /* Texto secundario */
    --surface: #ffffff;           /* Superficie */
    --surface-secondary: #f8f9fa; /* Superficie secundaria */
    --border: #ecf0f1;           /* Borde */
    --radius: 0.5rem;            /* Border radius */
    --shadow: 0 2px 4px rgba(0, 0, 0, 0.08);  /* Sombra sutil */
    --shadow-hover: 0 4px 8px rgba(0, 0, 0, 0.12); /* Sombra hover */
    --transition: all 0.2s ease; /* Transición suave */
}
```

### **Layout Grid Profesional**
```css
.projects-grid-modern {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

@media (max-width: 768px) {
    .projects-grid-modern {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
}
```

## 🎯 Vista de Detalle de Proyecto - Refactorización v2.5

### **Cambios Principales Implementados**

#### **1. Estructura Unificada**
- **Antes**: Layout custom con clases específicas de proyectos
- **Ahora**: Usa componentes globales de `base.css`
  - `header-section` para el encabezado
  - `main-content-grid` para el layout principal
  - `info-card-sidebar` para la barra lateral

#### **2. Header Mejorado**
```html
<!-- Header consistente con la app -->
<div class="header-section">
    <div class="header-content">
        <div class="header-title">
            <div class="header-icon">
                <i class="fas fa-folder-open"></i>
            </div>
            <div>
                <h1>{{ project.name }}</h1>
                <div class="text-muted">{{ project.client.name|default:"Sin cliente asignado" }}</div>
            </div>
        </div>
        <div class="d-flex gap-2">
            <a href="{% url 'projects:project-update' project.pk %}" class="btn btn-secondary">
                <i class="fas fa-edit"></i> {% trans "Editar" %}
            </a>
            <a href="{% url 'projects:project-kanban' project.pk %}" class="btn btn-primary">
                <i class="fas fa-columns"></i> {% trans "Kanban" %}
            </a>
        </div>
    </div>
    <!-- Breadcrumbs para navegación -->
    <nav aria-label="breadcrumb" class="mt-3">
        <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item"><a href="{% url 'projects:project-list' %}">{% trans "Proyectos" %}</a></li>
            <li class="breadcrumb-item active" aria-current="page">{{ project.name }}</li>
        </ol>
    </nav>
</div>
```

#### **3. Layout con Sidebar Estándar**
```html
<div class="main-content-grid">
    <div class="left-content">
        <!-- Tabs y contenido principal -->
        <ul class="nav nav-tabs" id="projectTab" role="tablist">
            <!-- Tabs: Detalles, Fases, Tareas, Archivos -->
        </ul>
        <div class="tab-content" id="projectTabContent">
            <!-- Contenido de cada tab -->
        </div>
    </div>
    
    <div class="right-sidebar">
        <!-- Estadísticas -->
        <div class="info-card-sidebar">
            <div class="info-header-sidebar">
                <i class="fas fa-chart-bar"></i>
                <h4>{% trans "Estadísticas" %}</h4>
            </div>
            <div class="info-content-sidebar">
                <div class="stats-grid-mini">
                    <!-- Tarjetas de estadísticas -->
                </div>
            </div>
        </div>
        
        <!-- Equipo y Actividad -->
        <!-- Más info-card-sidebar... -->
    </div>
</div>
```

#### **4. Progreso Simplificado**
```html
<!-- Antes: Barra de progreso custom -->
<div class="project-progress mb-4">
    <div class="progress-bar-container">
        <div class="progress-bar" data-progress="{{ project.progress|default:'0' }}" style="width: {{ project.progress|default:'0' }}%"></div>
    </div>
</div>

<!-- Ahora: Progreso Bootstrap estándar -->
<div class="mb-3 d-flex justify-content-between align-items-center">
    <span class="text-secondary">{% trans "Progreso general del proyecto" %}</span>
    <span class="fw-semibold">{{ project.progress|default:"0" }}%</span>
</div>
<div class="progress" style="height:8px;">
    <div class="progress-bar bg-primary" role="progressbar" style="width: {{ project.progress|default:'0' }}%" aria-valuenow="{{ project.progress|default:'0' }}" aria-valuemin="0" aria-valuemax="100"></div>
</div>
```

#### **5. Información Estructurada**
```html
<div class="row g-3 mt-3">
    <div class="col-sm-6">
        <div class="text-muted small">{% trans "Cliente" %}</div>
        <div class="fw-semibold">{{ project.client.name|default:"No asignado" }}</div>
    </div>
    <div class="col-sm-6">
        <div class="text-muted small">{% trans "Propietario" %}</div>
        <div class="fw-semibold">{{ project.owner.get_full_name|default:"No asignado" }}</div>
    </div>
    <!-- Más campos... -->
</div>
```

### **Beneficios de la Refactorización**

#### **Consistencia Visual**
- ✅ **Colores unificados**: Usa variables CSS globales (`--arc-color-primary`, etc.)
- ✅ **Espaciado estándar**: Implementa espaciados de `base.css`
- ✅ **Tipografía coherente**: Usa clases Bootstrap estándar

#### **Mantenibilidad**
- ✅ **Componentes reutilizables**: Sidebar y header globales
- ✅ **Menos CSS custom**: Reduce dependencias específicas
- ✅ **Estructura clara**: Layout semántico y accesible

#### **Experiencia de Usuario**
- ✅ **Navegación mejorada**: Breadcrumbs para orientación
- ✅ **Acciones claras**: Botones con jerarquía visual
- ✅ **Información organizada**: Grid responsivo para datos

#### **Responsive Design**
- ✅ **Mobile-first**: Se adapta perfectamente a móviles
- ✅ **Sidebar colapsable**: En pantallas pequeñas
- ✅ **Tabs accesibles**: Funcionan en todos los dispositivos

### **Componentes Utilizados**

#### **Globales (base.css)**
- `header-section` - Encabezado estándar
- `main-content-grid` - Layout principal con sidebar
- `info-card-sidebar` - Tarjetas de información
- `stats-grid-mini` - Estadísticas compactas
- `user-info` - Información de usuario

#### **Bootstrap**
- `nav nav-tabs` - Sistema de pestañas
- `progress` - Barra de progreso
- `breadcrumb` - Navegación de migas
- `btn btn-primary/secondary` - Botones estándar

---

## 📱 Responsive Design

### **Breakpoints**
```css
/* Desktop */
@media (min-width: 1201px) {
    .projects-grid-modern {
        grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    }
}

/* Tablet */
@media (max-width: 1200px) {
    .projects-grid-modern {
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    }
}

/* Mobile */
@media (max-width: 768px) {
    .project-card-modern {
        margin: 0 0.5rem;
    }
    
    .project-actions-modern {
        justify-content: center;
        flex-wrap: wrap;
    }
}
```

## 🔄 Flujo de Datos

### **Backend → Template**
```python
# views.py
context = {
    'projects': projects,           # Lista de proyectos
    'total_projects': total_projects,
    'active_projects': active_projects,
    'completed_projects': completed_projects,
}
```

### **Template → Frontend**
```html
{% for project in projects %}
<div class="project-card-modern" data-project-id="{{ project.pk }}">
    <!-- Renderizar datos del proyecto -->
</div>
{% endfor %}
```

## 🎯 Componentes Reutilizables

### **Cards Profesionales**
- `.project-card-modern` - Tarjetas de proyectos con diseño sobrio
- `.empty-projects-modern` - Estados vacíos profesionales

### **Botones Profesionales**
- `.btn-primary-prominent` - Botón primario elegante
- `.btn-action-modern` - Botones de acción con colores específicos
- `.btn-card-menu` - Botón de menú contextual

### **Indicadores Profesionales**
- `.project-status-modern` - Estados de proyecto con badges
- `.progress-bar-modern` - Barras de progreso simples
- `.meta-item-modern` - Elementos de metadatos

### **Filtros Ultra Compactos**
- `.search-input-modern` - Campo de búsqueda minimalista
- `.search-results-counter` - Contador de resultados

## 🔧 Optimizaciones

### **CSS**
- Variables CSS para consistencia
- Flexbox y Grid para layouts
- Transiciones suaves
- Sombras sutiles

### **JavaScript**
- Clases ES6
- Event listeners optimizados
- Búsqueda en tiempo real
- Debounce inteligente

### **Backend**
- Consultas optimizadas
- Paginación
- Filtros eficientes

## 🎨 Colores de Botones de Acción

### **Botón Ver (Verde)**
```css
.btn-view-modern {
    background: #dcfce7;
    color: #166534;
    border-color: #bbf7d0;
}
```

### **Botón Editar (Azul)**
```css
.btn-edit-modern {
    background: #dbeafe;
    color: #1e40af;
    border-color: #bfdbfe;
}
```

### **Botón Eliminar (Rojo)**
```css
.btn-delete-modern {
    background: #fee2e2;
    color: #991b1b;
    border-color: #fecaca;
}
```

## 📊 Características del Filtro

### **Diseño Ultra Compacto**
- ✅ **Padding mínimo**: 0.75rem (desktop), 0.5rem (móvil)
- ✅ **Ancho limitado**: Campo de búsqueda máximo 300px
- ✅ **Sin botón extra**: Solo campo de búsqueda
- ✅ **Búsqueda en vivo**: Funciona mientras escribes

### **Funcionalidad Inteligente**
- ✅ **Búsqueda inmediata**: Para términos de 2 caracteres o menos
- ✅ **Debounce optimizado**: 200ms para términos más largos
- ✅ **Contador automático**: Solo se muestra cuando hay filtros activos
- ✅ **Responsive**: Se adapta perfectamente a móviles

---

*Estructura profesional para el módulo de proyectos - Diseño sobrio y funcional para arquitectos*
