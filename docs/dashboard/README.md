# 📊 Dashboard - ArcManager

## 🎯 Resumen

El dashboard es la página principal de ArcManager, diseñada para arquitectos. Muestra información relevante y accionable de forma limpia y eficiente.

## 🏗️ Estructura Principal

### **Banner Azul (Header)**
- Saludo personalizado con nombre del usuario
- Resumen de proyectos activos y tareas pendientes
- 3 tarjetas de estadísticas rápidas

### **Proyectos Activos (Columna Izquierda)**
- Grid de 6 proyectos más recientes
- Imágenes de alta calidad (400x200px) con 5 variantes
- Información: nombre, cliente, progreso, fecha fin, miembros
- Botón "Abrir Proyecto" siempre en posición fija

### **Sidebar (Columna Derecha)**
- **Mis Tareas Pendientes**: Solo 3 tareas más urgentes
- **Documentos Recientes**: Archivos subidos recientemente
- Sin scroll - todo visible de un vistazo

## 🎨 Características de UX

### **Optimizaciones Implementadas**
- ✅ Sin redundancia: Eliminadas tarjetas de métricas duplicadas
- ✅ Banner cerca del navbar: Espaciado optimizado
- ✅ Imágenes variadas: 5 tipos de proyectos arquitectónicos
- ✅ Botón fijo: No se mueve con nombres largos
- ✅ Sidebar sin scroll: Solo 3 tareas prioritarias
- ✅ Indicadores dinámicos: Prioridades de tareas con colores

### **Responsive Design**
- Desktop: 2 columnas (proyectos + sidebar)
- Tablet: 1 columna (stack vertical)
- Mobile: Layout optimizado para touch

## 📁 Archivos Principales

```
arc_manager/
├── templates/dashboard.html          # Template principal (v32)
├── static/css/dashboard.css          # Estilos (v32)
├── static/js/dashboard.js            # JavaScript (v14)
└── apps/main/views.py                # Lógica backend
```

## 🔧 Datos del Backend

### **Consultas Optimizadas**
```python
# Solo 3 tareas más urgentes
my_tasks = Task.objects.filter(
    assigned_to=current_user
).exclude(status='DONE').order_by('due_date')[:3]

# 6 proyectos activos más recientes
active_projects = Project.objects.filter(
    organization=organization,
    status='ACTIVE'
).select_related('client').prefetch_related('phases__tasks')[:6]
```

### **Contexto del Template**
- `greeting_name`: Nombre del usuario
- `my_tasks`: 3 tareas pendientes
- `active_projects`: 6 proyectos activos
- `total_clients`: Número total de clientes
- `recent_files`: Documentos recientes (cuando se implemente)

## 🎨 Sistema de Diseño

### **Variables CSS**
```css
--primary: #3b82f6;      /* Azul principal */
--accent: #14b8a6;       /* Teal */
--success: #10b981;      /* Verde */
--warning: #f59e0b;      /* Amarillo */
--error: #ef4444;        /* Rojo */
--text: #0f172a;         /* Texto principal */
--surface: #ffffff;      /* Superficie */
--radius: 0.75rem;       /* Border radius */
```

### **Tipografía**
- **Familia**: Inter (Google Fonts)
- **Pesos**: 400, 500, 600, 700, 800

## 📱 Breakpoints Responsive

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

## 🚀 Versión Actual

- **CSS**: v32
- **JavaScript**: v14
- **Template**: v32
- **Última actualización**: Agosto 2025

---

*Documentación simplificada para contexto en futuras conversaciones*
