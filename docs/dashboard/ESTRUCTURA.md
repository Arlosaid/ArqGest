# 🏗️ Estructura del Dashboard

## 📁 Archivos Principales

```
arc_manager/
├── templates/dashboard.html          # Template principal (v32)
├── static/css/dashboard.css          # Estilos (v32)
├── static/js/dashboard.js            # JavaScript (v14)
└── apps/main/views.py                # Lógica backend
```

## 🎨 Componentes del Template

### **1. Header (Banner Azul)**
```html
<header class="dashboard-header-premium">
    <div class="welcome-section">
        <div class="welcome-content">
            <div class="time-greeting">¡Bienvenido de vuelta!</div>
            <h1 class="user-name">{{ greeting_name }}</h1>
            <p class="welcome-subtitle">...</p>
        </div>
        <div class="header-stats">
            <!-- 3 tarjetas de estadísticas -->
        </div>
    </div>
</header>
```

### **2. Grid Principal**
```html
<div class="dashboard-main-grid">
    <!-- Columna izquierda: Proyectos -->
    <section class="projects-section-compact">
        <div class="section-header-mini">...</div>
        <div class="projects-grid-mini">
            <!-- 6 proyectos -->
        </div>
    </section>
    
    <!-- Columna derecha: Sidebar -->
    <div class="dashboard-side-grid">
        <!-- Tareas pendientes -->
        <section class="summary-section-mini">...</section>
        <!-- Documentos recientes -->
        <section class="summary-section-mini">...</section>
    </div>
</div>
```

## 🎯 Jerarquía de Componentes

```
dashboard-premium
├── dashboard-header-premium
│   ├── welcome-content
│   └── header-stats
└── dashboard-main-grid
    ├── projects-section-compact
    │   ├── section-header-mini
    │   └── projects-grid-mini
    └── dashboard-side-grid
        ├── summary-section-mini (tareas)
        └── summary-section-mini (documentos)
```

## 🎨 Sistema de Diseño

### **Variables CSS**
```css
.dashboard-premium {
    --primary: #3b82f6;           /* Azul principal */
    --primary-dark: #2563eb;      /* Azul oscuro */
    --accent: #14b8a6;            /* Teal */
    --success: #10b981;           /* Verde */
    --warning: #f59e0b;           /* Amarillo */
    --error: #ef4444;             /* Rojo */
    --text: #0f172a;              /* Texto principal */
    --surface: #ffffff;           /* Superficie */
    --radius: 0.75rem;            /* Border radius */
    --shadow: 0 4px 6px -1px...;  /* Sombra */
}
```

### **Layout Grid**
```css
.dashboard-main-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;  /* Proyectos + Sidebar */
    gap: 1.5rem;
}

.projects-grid-mini {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
}
```

## 📱 Responsive Design

### **Breakpoints**
```css
/* Desktop */
@media (min-width: 1201px) {
    .dashboard-main-grid {
        grid-template-columns: 2fr 1fr;
    }
}

/* Tablet */
@media (max-width: 1200px) {
    .dashboard-main-grid {
        grid-template-columns: 1fr;
    }
}

/* Mobile */
@media (max-width: 768px) {
    .welcome-section {
        flex-direction: column;
    }
}
```

## 🔄 Flujo de Datos

### **Backend → Template**
```python
# views.py
context = {
    'greeting_name': current_user.first_name,
    'my_tasks': my_tasks,           # 3 tareas
    'active_projects': active_projects,  # 6 proyectos
    'total_clients': total_clients,
    'recent_files': recent_files,   # Documentos
}
```

### **Template → Frontend**
```html
{% for project in active_projects %}
<div class="project-card-mini">
    <!-- Renderizar datos del proyecto -->
</div>
{% endfor %}
```

## 🎯 Componentes Reutilizables

### **Cards**
- `.project-card-mini` - Tarjetas de proyectos
- `.empty-state-card` - Estados vacíos

### **Botones**
- `.btn-add-project` - Botón primario
- `.btn-mini-secondary` - Botón secundario
- `.btn-project-primary` - Botón de proyecto

### **Indicadores**
- `.priority-dot` - Indicadores de prioridad
- `.project-status-mini` - Estados de proyecto
- `.progress-bar-mini` - Barras de progreso

### **Iconos de Documentos**
- `.doc-icon-mini.pdf` - PDF
- `.doc-icon-mini.dwg` - DWG
- `.doc-icon-mini.excel` - Excel
- `.doc-icon-mini.word` - Word
- `.doc-icon-mini.image` - Imágenes
- `.doc-icon-mini.other` - Otros

## 🔧 Optimizaciones

### **CSS**
- Variables CSS para consistencia
- Flexbox para layouts complejos
- Grid para layouts principales
- Transiciones suaves

### **JavaScript**
- Clases ES6
- Event listeners optimizados
- Animaciones CSS-driven

### **Backend**
- Consultas con `select_related`
- Prefetch de datos relacionados
- Límites en consultas (3 tareas, 6 proyectos)

---

*Estructura simplificada para referencia rápida*
