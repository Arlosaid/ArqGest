# 📋 Módulo de Proyectos - Arc Manager

## 📖 Descripción General

El módulo de **Proyectos** permite gestionar proyectos, fases y tareas por organización, con un tablero Kanban para el flujo operativo. Incluye vistas de lista y detalle, creación con plantillas de fases, centro de tareas y modales para ver/editar tareas.

---

## 🏗️ Arquitectura del Módulo

### 📁 Estructura de Archivos

```
arc_manager/apps/projects/
├── models.py                  # Project, Phase, Task, PhaseTemplate
├── views.py                   # Vistas de proyectos, fases, tareas, kanban
├── urls.py                    # Routing del módulo
├── forms.py                   # Formulario Project y Task; PhaseFormSet
├── services.py                # create_phases_for_project
├── templates/projects/        # HTML de listas, detalle, kanban, modales
└── templatetags/project_extras.py # Filtros utilitarios

arc_manager/static/js/kanban.js      # Lógica de drag & drop y acciones AJAX
arc_manager/static/css/{projects.css, kanban.css, tasks.css} # Estilos
```

---

## 🗃️ Modelos

- Project: `organization`, `owner`, `client`, `name`, `status{ACTIVE,ARCHIVED,COMPLETED}`, fechas
- Phase: `project`, `name`, `status{PENDING,IN_PROGRESS,COMPLETED}`, `order`
- Task: `phase`, `assigned_to`, `title`, `description`, `status{TODO,IN_PROGRESS,PAUSED,DONE}`, `priority{LOW,MEDIUM,HIGH}`, `due_date`
- PhaseTemplate: `name`, `description`, `organization`, `phases` (JSON)

---

## 🎯 Funcionalidades Clave

- Listado y detalle de proyectos por organización
- Creación con fases vía plantilla o manual (formset)
- Tablero Kanban agrupado por estado; drag & drop con actualización silenciosa
- Estadísticas de tareas en tiempo real vía endpoint JSON
- Centro de tareas: próximas, vencidas, recientes, por fase
- Tareas: crear, editar (modal/htmx), mover de fase, eliminar
- Plantillas de fases CRUD

---

## 🎨 UI/UX

- Kanban con columnas por estado de `Task`
- Modales de nueva tarea y de edición/detalle
- Filtros por fase y botón de actualización
- Contadores por columna y tarjetas con acciones rápidas

---

## 🔐 Seguridad y Permisos

- Todas las vistas requieren autenticación
- Filtro por `organization` en queries y `get_queryset`
- Validaciones al asignar usuarios: deben pertenecer a la organización y no ser superusuario

---

## 🧪 Pruebas sugeridas

- List/ListDetail restringidas por organización
- Kanban: conteos y contexto
- JSON: `update_task_status`, `move_task`, `task_delete`
- Creación de proyecto con plantilla y manual con formset

---

## ⚙️ Despliegue

- Migraciones del módulo `projects` aplicadas
- Archivos estáticos recolectados para JS/CSS

---

Última actualización: Diciembre 2024

