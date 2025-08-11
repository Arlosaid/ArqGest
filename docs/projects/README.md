# 📋 Módulo de Proyectos - ArcManager

## 🎯 Descripción General

El módulo de proyectos es el núcleo central de ArcManager, permitiendo la gestión completa de proyectos de construcción y arquitectura. Este módulo ha sido completamente rediseñado con una interfaz ultra compacta y profesional que optimiza la experiencia del usuario para arquitectos.

## 🚀 Características Principales

### **Gestión de Proyectos**
- ✅ Creación y edición de proyectos
- ✅ Vista de lista con filtro ultra compacto
- ✅ Vista detallada de proyectos (v2.5 - Refactorizada)
- ✅ Sistema de estados y progreso
- ✅ Gestión de clientes asociados

### **Interfaz Ultra Compacta**
- ✅ Filtro minimalista (solo búsqueda por nombre)
- ✅ Tarjetas con información estructurada
- ✅ Botones de acción con colores específicos
- ✅ Diseño responsive optimizado
- ✅ Búsqueda en tiempo real
- ✅ Vista de detalle unificada con pestañas (sin sidebar)

### **Funcionalidades Avanzadas**
- ✅ Búsqueda instantánea por nombre de proyecto
- ✅ Información estructurada en grid 2x2
- ✅ Progreso visual con barras Bootstrap
- ✅ Metadatos contextuales
- ✅ Acciones rápidas con colores distintivos
- ✅ Navegación por pestañas: Detalles, Fases, Tareas, Archivos

## 🎨 Diseño y UX

### **Principios de Diseño**
- **Minimalismo**: Interfaz ultra compacta sin elementos innecesarios
- **Funcionalidad**: Enfoque en la usabilidad para arquitectos
- **Consistencia**: Patrones de diseño uniformes
- **Responsividad**: Funciona perfectamente en todos los dispositivos
- **Performance**: Carga rápida y búsqueda instantánea

### **Paleta de Colores**
```css
--primary: #3b82f6;        /* Azul principal */
--primary-dark: #2563eb;   /* Azul oscuro */
--success: #27ae60;        /* Verde */
--warning: #f39c12;        /* Amarillo */
--error: #e74c3c;          /* Rojo */
--text: #2c3e50;           /* Texto principal */
--surface: #ffffff;        /* Superficie */
```

### **Colores de Botones de Acción**
- **Ver (Verde)**: `#dcfce7` fondo, `#166534` texto
- **Editar (Azul)**: `#dbeafe` fondo, `#1e40af` texto  
- **Eliminar (Rojo)**: `#fee2e2` fondo, `#991b1b` texto

### **Componentes Clave**
- **Filtro Ultra Compacto**: Solo campo de búsqueda, sin botones extra
- **Tarjetas Estructuradas**: Información organizada en grid 2x2
- **Botones de Acción**: Colores específicos para cada acción
- **Indicadores de Estado**: Estados visuales claros
- **Barras de Progreso**: Progreso visual del proyecto
- **Vista de Detalle Unificada**: Layout estándar con sidebar y navegación mejorada

## 🎯 Refactorización de Vista de Detalle (v2.5)

### **Cambios Implementados**

#### **Estructura Unificada**
- **Tabs principales**: `Detalles`, `Fases`, `Tareas`, `Archivos`
- **Sin sidebar**: se eliminó la columna derecha para maximizar el lienzo de trabajo
- **Header consistente**: Usa `header-section` global (sin breadcrumbs)

#### **Mejoras de UX**
- **Navegación clara**: pestañas visibles y accesibles
- **Progreso simplificado**: barra Bootstrap nativa
- **Información organizada**: grid responsivo para datos clave
- **Acciones claras**: botones con jerarquía visual estándar

#### **Consistencia Visual**
- **Colores unificados**: Variables CSS globales (`--arc-color-primary`)
- **Espaciado estándar**: Implementa espaciados de `base.css`
- **Tipografía coherente**: Clases Bootstrap estándar

#### **Responsive Design**
- **Mobile-first**: Se adapta perfectamente a móviles
- **Sidebar colapsable**: En pantallas pequeñas
- **Tabs accesibles**: Funcionan en todos los dispositivos

### **Componentes Utilizados**
- `header-section` - Encabezado estándar
- `nav nav-tabs` - Sistema de pestañas Bootstrap
- `tab-content` - Contenedor de contenido por pestaña
- `progress` - Barra de progreso Bootstrap

---

## 🗂️ Pestaña “Archivos” (para Arquitectos)

### Diseño
- **Agrupado por Fase**: acordeón por cada fase del proyecto.
- **Subida por Fase**: formulario simple por fase (múltiples archivos) usando la ruta `files:upload_file`.
- **Dos vistas**: conmutador Tabla/Galería por fase.
  - Tabla: ícono por tipo (Imagen, PDF, DWG/DXF, Word, Excel, Genérico) y metadatos (subido por, fecha, tamaño).
  - Galería: tarjetas con miniatura cuando es imagen, ícono grande para el resto.
- **Sin previsualización**: enfoque ligero y rápido.

### Backend
- `ProjectDetailView` hace `prefetch_related('tasks__assigned_to', 'files', 'files__uploaded_by')` para rendimiento.
- Modelo `ProjectFile` expone:
  - `filename`: nombre sin ruta
  - `extension`: extensión en mayúsculas (ej. PDF, DWG)

### Endpoints relevantes
- Subir: `files:upload_file` → `projects/<project_id>/phases/<phase_id>/files/upload/` (POST multipart)
- Borrar: `files:delete_file` → `files/<file_id>/delete/` (POST)

### Plantillas
- `projects/partials/_files_tab.html` contiene el acordeón, formulario y el conmutador Tabla/Galería.

---

## 🧭 Comportamiento de pestañas (v2.5)

- Siempre hay una única pestaña visible. El JS normaliza el DOM para evitar panes superpuestos.
- Pestaña por defecto: **Detalles**.
- Puedes abrir una pestaña específica con `?tab=<details|phases|tasks|files>` o `#<details|phases|tasks|files>`.
  - Ejemplo: `.../projects/42/?tab=files`.
- Archivo clave: `templates/projects/project_detail.html` y `static/js/projects.js` (v1.2).

## 🗃️ Acordeón de Archivos (v2.5)

- Ninguna sección se abre por defecto; todas las fases inician colapsadas.
- Se usa Bootstrap Accordion. Estructura base en `projects/partials/_files_tab.html`.
- Clases de estilo relevantes (definidas en `static/css/projects.css` v1.5):
  - `.file-phase-item` (contenedor)
  - `.accordion-button.file-phase-header` (cabecera con chevron animado)
  - `.bg-primary-soft` (badge de conteo)
  - `.file-list-table.modern-table` (tabla moderna)

### Personalización rápida

Para ajustar apariencia:

```css
/* Cambiar color del chevron activo */
.accordion-button.file-phase-header:not(.collapsed)::after { color: #3b82f6; }

/* Fondo del encabezado */
.accordion-button.file-phase-header { background: linear-gradient(180deg, #fff, #f8fbff); }
```

## 🔢 Versionado de assets

- `projects.css` → v1.5
- `projects.js` → v1.2
- El template `project_detail.html` incluye query `?v=` para bust de caché.

---

## 📱 Responsive Design

### **Breakpoints**
- **Desktop**: > 1200px - Layout completo con grid de 3+ columnas
- **Tablet**: 768px - 1200px - Grid de 2 columnas
- **Mobile**: < 768px - Grid de 1 columna, filtro adaptado

### **Adaptaciones**
- Filtro ultra compacto que se adapta al ancho disponible
- Tarjetas que mantienen proporciones en móvil
- Botones de acción que se reorganizan en pantallas pequeñas
- Información estructurada que se apila verticalmente

## 🔧 Arquitectura Técnica

### **Frontend**
- **CSS**: Variables CSS para consistencia total
- **JavaScript**: Clases ES6 con búsqueda optimizada
- **HTML**: Estructura semántica y accesible
- **Templates**: Sistema de herencia de Django

### **Backend**
- **Views**: Lógica de negocio optimizada
- **Models**: Estructura de datos eficiente
- **URLs**: Rutas RESTful
- **Forms**: Validación robusta

## 📊 Métricas de Performance

### **Tiempo de Carga**
- **CSS**: < 50ms (ultra optimizado)
- **JavaScript**: < 30ms (búsqueda instantánea)
- **Renderizado**: < 150ms
- **Interactividad**: < 50ms

### **Optimizaciones**
- CSS crítico optimizado
- JavaScript con debounce inteligente
- Búsqueda en tiempo real
- Cache efectivo

## 🎯 Flujos de Usuario

### **Buscar Proyecto**
1. Usuario escribe en el campo de búsqueda
2. Búsqueda instantánea (≤2 caracteres) o con debounce (200ms)
3. Resultados filtrados en tiempo real
4. Contador automático de resultados
5. Limpieza manual del campo

### **Ver Proyecto**
1. Usuario hace clic en botón verde "Ver"
2. Se abre vista detallada
3. Información completa del proyecto
4. Acciones disponibles
5. Navegación contextual

### **Editar Proyecto**
1. Usuario hace clic en botón azul "Editar"
2. Formulario pre-poblado
3. Validación en tiempo real
4. Guardado con confirmación
5. Actualización de vista

### **Eliminar Proyecto**
1. Usuario hace clic en botón rojo "Eliminar"
2. Confirmación de eliminación
3. Proceso de eliminación
4. Actualización de lista
5. Feedback visual

## 🔄 Integración con Otros Módulos

### **Clientes**
- Asociación de proyectos con clientes
- Información de cliente en grid estructurado
- Navegación entre módulos

### **Tareas**
- Enlace a tareas del proyecto
- Progreso basado en tareas
- Gestión de fases

### **Archivos**
- Documentos asociados al proyecto
- Vista de archivos recientes
- Gestión de documentos

## 🚀 Roadmap

### **Versión 2.5**
- [ ] Drag & drop para reordenar proyectos
- [ ] Vista de calendario integrada
- [ ] Exportación de proyectos
- [ ] Notificaciones en tiempo real

### **Versión 2.6**
- [ ] Dashboard de proyectos avanzado
- [ ] Reportes con gráficos
- [ ] Integración con calendario externo
- [ ] Plantillas de proyecto personalizables

### **Versión 2.7**
- [ ] Colaboración en tiempo real
- [ ] Comentarios en proyectos
- [ ] Historial de cambios detallado
- [ ] Backup automático con versionado

## 📚 Documentación Relacionada

- [Estructura del Módulo](./ESTRUCTURA.md)
- [Guía de Desarrollo](./DESARROLLO.md)
- [API Reference](./API.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

## 🎯 Características Destacadas

### **Filtro Ultra Compacto**
- ✅ **Solo búsqueda por nombre**: Sin filtros complejos
- ✅ **Búsqueda instantánea**: Para términos cortos
- ✅ **Debounce inteligente**: 200ms para términos largos
- ✅ **Contador automático**: Solo cuando hay filtros activos
- ✅ **Sin botón de limpiar**: Limpieza manual

### **Tarjetas Estructuradas**
- ✅ **Grid 2x2**: Cliente, Fase, Fechas organizadas
- ✅ **Información precisa**: Sin repetición de datos
- ✅ **Progreso visual**: Barra de progreso clara
- ✅ **Metadatos**: Fechas de creación y actualización
- ✅ **Acciones claras**: Botones con colores específicos

### **Botones de Acción**
- ✅ **Verde para Ver**: `#dcfce7` / `#166534`
- ✅ **Azul para Editar**: `#dbeafe` / `#1e40af`
- ✅ **Rojo para Eliminar**: `#fee2e2` / `#991b1b`
- ✅ **Hover effects**: Transiciones suaves
- ✅ **Responsive**: Se adaptan a móviles

---

*Módulo de proyectos ultra compacto y profesional para ArcManager - Optimizado para arquitectos*

## 🧱 Kanban – Ajustes UI recientes (v2.5.x)

### Cambios de UX

- Tarjeta simplificada:
  - Fondo único blanco (sin gradientes ni header de tarjeta).
  - Muestra Título, Asignado a y etiqueta de Fase.
  - Se ocultó el estado dentro de la tarjeta para evitar redundancia (el estado ya está representado por la columna).
  - Archivos: `templates/projects/kanban_board.html` y `static/css/kanban.css`.

- Contador por columna con pluralización:
  - Muestra “1 tarea” o “N tareas”.
  - Se actualiza en vivo con drag & drop, creación, edición y eliminación.
  - Función: `updateColumnCounters()` en `static/js/kanban.js`.

- Placeholder de columna (casco):
  - Desaparece automáticamente cuando hay al menos una tarjeta.
  - Vuelve a mostrarse cuando queda vacía la columna.
  - Función: `syncEmptyStates()` en `static/js/kanban.js`.

### Flujo de edición/creación/eliminación (modal)

- Editar tarea (HTMX):
  - El modal envía POST a `tasks/<id>/edit/`.
  - Si es HTMX, el servidor retorna JSON `{ success, task: { id, title, assigned_to_name, phase_name } }`.
  - El cliente cierra el modal y actualiza la tarjeta sin recargar (título, asignado, fase).
  - Archivos: `views.py (task_edit)`, `templates/projects/partials/task_edit_modal.html`.

- Crear tarea (modal):
  - Añadido campo “Asignado a” con usuarios de la organización.
  - Respuesta JSON cuando el `Accept` incluye `application/json`.
  - Archivo: `views.py (task_create)` y `kanban_board.html` (form).

- Eliminar tarea (desde modal):
  - Botón “Eliminar” en el modal de edición.
  - Endpoint: `POST /projects/tasks/<id>/delete/` → JSON `{ success: true }`.
  - El cliente remueve la tarjeta del DOM, re-calcula contador y placeholder.
  - Archivos: `views.py (task_delete)`, `urls.py`, `kanban.js (handleDeleteTask)`.

### Drag & drop

- Cambiar estado (agrupado por estado): `updateTaskStatus(evt)`.
- Mover de columna (cuando agrupe por fase): `updateTaskPhase(evt)`.
- Ambos flujos actualizan estadísticas, contador y placeholder en vivo.

### Archivos y ubicaciones clave

- Plantilla: `apps/projects/templates/projects/kanban_board.html`.
- JS: `arc_manager/static/js/kanban.js` (clase `KanbanManager`).
- CSS: `arc_manager/static/css/kanban.css`.
- Vistas: `apps/projects/views.py` (`project_kanban`, `task_create`, `task_edit`, `task_delete`, `update_task_status`, `move_task`).
- Rutas: `apps/projects/urls.py`.
