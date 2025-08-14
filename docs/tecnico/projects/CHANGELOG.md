# 📝 Changelog - Módulo de Proyectos

Formato basado en Keep a Changelog. Versionado semántico.

---

## [10.0.0] - 2024-12-13

### ✨ Agregado
- Tablero Kanban con drag & drop y actualización silenciosa vía JSON
- Endpoint `/projects/<id>/statistics/` para métricas en tiempo real
- Modal de edición de tarea con respuesta JSON para htmx
- Selector de Kanban por proyecto (`/projects/kanban-selector/`)
- Centro de tareas en `project_detail` con próximas, vencidas y recientes

### 🔄 Cambiado
- Queries optimizadas con `select_related/prefetch_related` en vistas clave
- Validaciones de organización en creación/movimiento/edición/eliminación de tareas

### 🐛 Corregido
- Asignación de usuarios ahora verifica pertenencia a la organización
- Manejo robusto de `due_date` inválidas en creación/edición de tareas

### 📚 Documentación
- Documentación técnica exhaustiva en `docs/tecnico/projects`
- Endpoints y ejemplos actualizados

---

## [9.0.0] - 2024-11-10

### 🎉 MVP Proyectos
- CRUD de proyectos
- Fases y tareas básicas
- Lista de tareas y mis tareas

---

## 🔮 Roadmap

### v10.5.0
- Filtros avanzados en Kanban (por asignado, prioridad, vencimiento)
- Acciones masivas en lista de tareas

### v11.0.0
- API REST para tareas y proyectos (DRF)
- Webhooks para eventos de tareas
- Métricas por usuario/equipo

Última actualización: Diciembre 2024
