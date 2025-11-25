# Corrección de Permisos de Tareas - TC-62

## Problema Identificado
Los usuarios normales tenían acceso completo para:
- ✅ Crear tareas
- ✅ Editar tareas
- ✅ Asignar tareas a otros usuarios
- ✅ Mover tareas entre fases
- ✅ Eliminar tareas

Esto rompía completamente el control de roles. **Los usuarios normales SOLO deberían poder ver y cambiar estados de tareas.**

---

## Solución Implementada

### 1. **Crear archivo de permisos** (`arc_manager/apps/projects/permissions.py`)

Nuevos decoradores para validar permisos:

| Decorador | Permite | Restricción |
|-----------|---------|------------|
| `@task_create_permission_required` | Crear tareas | Solo **admins** |
| `@task_edit_permission_required` | Editar tareas | Solo **admins** O **asignado** |
| `@task_status_change_permission_required` | Cambiar estado | Solo **admins** O **asignado** |
| `@task_move_permission_required` | Mover entre fases | Solo **admins** |

**Funciones auxiliares:**
- `is_organization_admin(user)` - Valida si es admin (`is_org_admin=True`)
- `is_task_assignee(user, task)` - Valida si es el usuario asignado

---

### 2. **Aplicar decoradores en vistas** (`arc_manager/apps/projects/views.py`)

#### Vista `task_create` (línea ~847)
```python
@login_required
@task_create_permission_required
def task_create(request, project_pk):
```
**Cambio:** Solo admins pueden crear tareas. Usuarios normales reciben error 403.

#### Vista `task_edit` (línea ~1245)
```python
@login_required
@task_edit_permission_required
def task_edit(request, pk):
```
**Cambio:** Solo admins O el usuario asignado pueden editar. Cambio de vista GET permitida para todos.

#### Vista `update_task_status` (línea ~1141)
```python
@login_required
@require_POST
@task_status_change_permission_required
def update_task_status(request, task_pk):
```
**Cambio:** Admins O asignado pueden cambiar estado (esto ESTÁ PERMITIDO para usuarios normales).

#### Vista `move_task` (línea ~1195)
```python
@login_required
@require_POST
@task_move_permission_required
def move_task(request, task_pk):
```
**Cambio:** Solo admins pueden mover tareas entre fases.

---

### 3. **Actualizar templates** (`arc_manager/apps/projects/templates/projects/kanban_board.html`)

#### Cambio 1: Pasar `is_org_admin` al contexto
```python
context = {
    # ... otros campos ...
    'is_org_admin': is_organization_admin(request.user),
}
```

#### Cambio 2: Ocultar botón "Nueva Tarea"
- Solo admins ven el botón
- Solo admins ven el modal de crear tarea

```django
{% if is_org_admin %}
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTaskModal">
        <i class="fas fa-plus"></i> {% trans "Nueva Tarea" %}
    </button>
{% endif %}
```

#### Cambio 3: Ocultar botón "Editar" en todas las columnas
- TODO, IN_PROGRESS, PAUSED, DONE
- Solo admins O asignado ven el botón

```django
{% if is_org_admin or task.assigned_to.id == user.id %}
    <button class="btn btn-outline-primary" onclick="openTaskModal('edit', {{ task.pk }})">
        <i class="fas fa-edit"></i>
    </button>
{% endif %}
```

#### Cambio 4: Mantener botón "Eliminar" restringido
```django
{% if is_org_admin %}
    <button class="btn btn-outline-danger" data-action="delete-task" data-task-id="{{ task.pk }}">
        <i class="fas fa-trash-alt"></i>
    </button>
{% endif %}
```

---

## Matriz de Permisos Final

| Acción | Tipo Usuario | GET | POST | Notas |
|--------|-------------|-----|------|-------|
| **Ver tareas** | Normal | ✅ | N/A | Acceso total a lectura |
| **Ver detalles** | Normal | ✅ | N/A | Modal de detalles |
| **Cambiar estado** | Normal | N/A | ✅ | Solo si es asignado |
| **Crear tarea** | Normal | N/A | ❌ | Solo admin |
| **Editar tarea** | Normal | N/A | ❌ | Solo admin (GET permitido) |
| **Asignar tarea** | Normal | N/A | ❌ | Solo admin |
| **Mover tarea** | Normal | N/A | ❌ | Solo admin |
| **Eliminar tarea** | Normal | N/A | ❌ | Solo admin |
| --- | --- | --- | --- | --- |
| **Ver tareas** | Admin | ✅ | N/A | Acceso total |
| **Cambiar estado** | Admin | N/A | ✅ | Permitido siempre |
| **Crear tarea** | Admin | N/A | ✅ | ✅ Permitido |
| **Editar tarea** | Admin | N/A | ✅ | ✅ Permitido |
| **Asignar tarea** | Admin | N/A | ✅ | ✅ Permitido |
| **Mover tarea** | Admin | N/A | ✅ | ✅ Permitido |
| **Eliminar tarea** | Admin | N/A | ✅ | ✅ Permitido |

---

## Comportamiento de Errores

Cuando un usuario no autorizado intenta realizar una acción:

### Solicitud AJAX/JSON
```json
{
  "success": false,
  "error": "No tienes permisos para [acción]",
  "error_code": "[PERMISSION_DENIED]",
  "status": 403
}
```

### Solicitud Normal
- Mensaje de error en el navegador
- Redirige a la página anterior
- Log en `logger.warning()`

---

## Logging

Todos los intentos de acceso no autorizado se registran:

```
Usuario admin@example.com intentó crear tarea sin permisos
Usuario user@example.com intentó editar tarea 123 sin permisos
Usuario user@example.com intentó asignar tarea sin permisos
```

---

## Archivos Modificados

1. ✅ `arc_manager/apps/projects/permissions.py` - **NUEVO**
2. ✅ `arc_manager/apps/projects/views.py` - Decoradores aplicados
3. ✅ `arc_manager/apps/projects/templates/projects/kanban_board.html` - UI actualizada

---

## Testing Recomendado

### Con Usuario Normal:
- [ ] Intentar ver tareas ✅ (debe funcionar)
- [ ] Intentar cambiar estado ✅ (si es asignado)
- [ ] Intentar crear tarea ❌ (debe rechazar)
- [ ] Intentar editar tarea ❌ (debe rechazar)
- [ ] Intentar eliminar tarea ❌ (debe rechazar)
- [ ] Verificar botones ocultos en UI

### Con Admin:
- [ ] Todas las acciones ✅ (deben funcionar)
- [ ] Verificar botones visibles en UI

---

## Notas

- Los cambios son **retrocompatibles**
- Los permisos se validan a nivel de decorador (más seguro que solo UI)
- Las respuestas JSON incluyen códigos de error para debugging
- El logging captura todos los intentos no autorizados
