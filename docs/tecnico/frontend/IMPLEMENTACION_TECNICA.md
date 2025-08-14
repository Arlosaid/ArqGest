# 🎨 Implementación Técnica — Frontend de ArcManager

## 📋 Objetivo

Documentar de forma exhaustiva cómo está diseñado y configurado el frontend de ArcManager: herencia de plantillas, includes compartidos, arquitectura de CSS/JS, librerías externas, configuración de archivos estáticos, patrones de bloques, utilidades y mejores prácticas. Basado en el análisis vigente y verificado contra el código actual.

---

## 🏗️ Arquitectura de Plantillas (Django Templates)

### Estructura y herencia

Plantilla base global y herencia modular por vistas:

```
templates/
├── base.html                  # Plantilla base global
├── includes/
│   ├── navbar.html           # Navbar global
│   └── sidebar.html          # Sidebar global
├── auth/
│   ├── base_auth.html        # Base específica para auth
│   └── login.html            # Ejemplo de auth heredando base_auth.html
├── plans/ ...                # Módulo planes
├── projects/ ...             # Módulo proyectos (lista, detalle, kanban, tareas, plantillas)
└── users/, orgs/, files/ ... # Otros módulos
```

Bloques estándar expuestos por `base.html`:
- `block title` — título del documento
- `block extra_css` — CSS específico por página
- `block content` — contenido principal
- `block extra_js` — JS específico por página

### base.html (puntos clave)

- Meta tags: `charset`, `viewport`
- CDNs: Bootstrap 5.3.2 (CSS/JS), Font Awesome 6.4.0, jQuery 3.7.1
- CSS base con cache-busting: `base.css?v=1.4`, `navbar.css?v=1.4`, `sidebar.css?v=1.4`
- Includes: `includes/sidebar.html` y `includes/navbar.html`
- Sistema de mensajes Django mapeado a alerts Bootstrap
- HTMX cargado y CSRF configurado globalmente (evento `htmx:configRequest`)
- JS global: `base.js`, `navbar.js`, `sidebar.js`
- Modal global reutilizable `#appModal` + helper `window.openAppModal(url, title)`

### Includes compartidos

Navbar (`includes/navbar.html`):
- Menú de usuario minimalista (iniciales, nombre, rol)
- Dropdown con Perfil y Cerrar sesión

Sidebar (`includes/sidebar.html`):
- Navegación principal: Dashboard, Kanban Selector, Proyectos, Mis Tareas
- Sección Administración (solo `is_org_admin`): Usuarios, Clientes, Plantillas de Fases, Organización
- Estado activo condicionado por `request.resolver_match`
- Toggle para móvil + overlay

### Patrones de bloques en vistas

- Siempre extender `base.html` (o `base_auth.html` para auth)
- Cargar CSS/JS del módulo en `extra_css`/`extra_js`
- Usar contenedor estándar `page-container` definido en `base.css`

Ejemplo mínimo:

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Título | ArcManager{% endblock %}

{% block extra_css %}
<link href="{% static 'css/feature.css' %}?v=1.0" rel="stylesheet">
{% endblock %}

{% block content %}
<div class="page-container">Contenido</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/feature.js' %}?v=1.0"></script>
{% endblock %}
```

---

## 🧩 Arquitectura CSS (Design System y módulos)

### Archivos principales

- `static/css/base.css` — Variables CSS, layout, utilidades, tipografía, componentes base y contenedores estándar (p. ej., `.page-container`, `.main-content-grid`, `.header-section`)
- `static/css/navbar.css` — Estilos del navbar global
- `static/css/sidebar.css` — Estilos del sidebar global

Módulos específicos (ejemplos):
- `static/css/projects.css`, `static/css/kanban.css`, `static/css/tasks.css`, `static/css/plans.css`, etc.

### Design tokens (variables CSS)

Paleta y layout (definidas en `:root`):
- Colores: `--arc-color-primary`, `--arc-color-success`, `--arc-color-warning`, `--arc-color-danger`, etc.
- Fondo/texto: `--arc-bg-*`, `--arc-text-*`
- Layout: `--arc-layout-sidebar-width`, `--arc-layout-navbar-height`
- Sombra/borde: `--arc-shadow-*`, `--arc-border-color`, `--arc-border-radius`
- Espaciado/animación: `--arc-spacing-*`, `--arc-transition`

### Responsive design

- Breakpoints utilizados: 1400, 1200, 1024, 768, 480 px
- Mobile-first con Flexbox y CSS Grid
- Tablas y tarjetas adaptativas; sidebar colapsable

### Utilidades y componentes

- Utilidades de espaciado, display, alineación
- Componentes comunes: cards, tablas modernas, badges de estado, formularios, botones prominentes

### Cache-busting

- Versión en query string para forzar recarga tras despliegues: `?v=1.4` en CSS críticos

---

## ⚙️ Arquitectura JavaScript (modular)

Archivos principales:
- `static/js/base.js` — Clase `BaseAnimation`, inicialización de tooltips/popovers Bootstrap, utilidades de animación
- `static/js/navbar.js`, `static/js/sidebar.js` — Interacciones del layout

Módulos por feature:
- `static/js/projects.js` — Lógica de vistas de proyectos
- `static/js/kanban.js` — Tablero Kanban: drag & drop, actualización silenciosa de estado, estadísticas en vivo, modales, notificaciones
- `static/js/tasks.js` — Gestión de tareas (si aplica)

Librerías externas:
- Bootstrap (bundle con Popper), jQuery (compatibilidad), HTMX (interacciones parciales)

Patrones:
- Clases ES6, listeners delegados, mínima lógica inline en templates, uso de `data-*`
- CSRF añadido automáticamente a HTMX; para fetch se obtiene de `input[name=csrfmiddlewaretoken]`

---

## 🔒 Seguridad y permisos (capa UI)

- Vistas renderizadas solo si el usuario está autenticado (middleware)
- Elementos de navegación condicionados por rol (`is_org_admin`)
- Validaciones en acciones Ajax (asignaciones y scoping por organización se validan en backend)

---

## 🗂️ Archivos estáticos: configuración y despliegue

### Django settings

```
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

Implicaciones:
- Desarrollo: archivos en `arc_manager/static/` (dentro del paquete del proyecto)
- Producción: `collectstatic` recopila en `staticfiles/` y WhiteNoise sirve con hashing y compresión

### Estructura estándar (evitar duplicados)

Regla: un solo directorio `static` bajo `arc_manager/static/` con subcarpetas `css/`, `js/`, `images/`.

### Docker/Deploy

- Volumen persistente para `staticfiles/` y `media/`
- Ejecutar: `python manage.py collectstatic --noinput` en build/deploy
- Cache-busting controlado por ManifestStorage + query string opcional en templates

---

## 📦 Librerías externas y orden de carga

Orden recomendado en `base.html`:
1) CSS: Bootstrap, Font Awesome, CSS base y específicos por página
2) JS: jQuery (si se usa), Bootstrap bundle, HTMX, `base.js`, `navbar.js`, `sidebar.js`, luego `extra_js`

Notas:
- HTMX: configurar CSRF global con `htmx:configRequest`
- Modales Bootstrap inicializados desde `base.html` y helpers globales (`openAppModal`)

---

## 📊 Módulos notables

### Kanban (static/js/kanban.js)

- Drag & drop por columnas (`.kanban-column-body`) con `data-status-code`
- POST JSON a `/projects/tasks/<id>/update_status/` con CSRF
- Actualización visual silenciosa + recálculo de contadores + refresco de estadísticas vía `/projects/<id>/statistics/`
- Creación de tareas con `FormData` y soporte JSON/redirect
- Edición/Detalle en modal; fallback a navegación si no hay modal global

### Mensajes y modal global

- Mensajes Django → Alerts Bootstrap; limpieza de duplicados por script simple
- Modal `#appModal` reutilizable para cargar contenido remoto (HTMX o fetch)

---

## 🧪 Testing UI/Frontend (sugerido)

- Render de plantillas con bloques y assets correctos
- Navegación condicional de sidebar/navbar por rol
- Kanban: DnD actualiza estado y métricas; manejo de errores JSON
- Modales: carga remota, edición/guardado y cierre
- Responsive: layouts clave en breakpoints definidos

---

## 🚀 Performance y Accesibilidad

- Minificar/combinar en producción (WhiteNoise ya comprime; considerar pipeline adicional si crece)
- Lazy loading de imágenes y contenidos secundarios
- Reducir trabajo en scroll/drag; debouncing donde aplique
- ARIA y foco en modales; contraste de colores; navegación por teclado

---

## 🛠️ Troubleshooting (resumen práctico)

Síntomas de CSS/JS no cargando:
- Verificar estructura de `static/` única, `STATICFILES_DIRS`, `collectstatic`, rutas en templates
- Revisar DevTools → Network (404, 500), Cache (Ctrl+F5), errores JS en consola
- En Docker: reiniciar contenedores y re-ejecutar `collectstatic`

Problemas HTMX/CSRF:
- Confirmar cookie `csrftoken` presente y listener `htmx:configRequest` activo
- Para fetch, usar el token desde `input[name=csrfmiddlewaretoken]`

---

## 📑 Convenciones y buenas prácticas

- Siempre usar `extra_css`/`extra_js` en plantillas que lo requieran
- Evitar estilos/scripts inline; preferir archivos estáticos versionados
- Reutilizar componentes y utilidades de `base.css`
- Mantener nombres consistentes por módulo: `projects.css`, `projects.js`, etc.

---

## 🔮 Roadmap Frontend

- CSS/JS específicos pendientes: `kanban.css`, `tasks.css` (si aún no están completos)
- Code splitting por página, carga diferida de JS no crítico
- Modo oscuro con variables CSS, preferencia de sistema
- Tests de accesibilidad y performance automatizados

---

Última actualización: Diciembre 2024

