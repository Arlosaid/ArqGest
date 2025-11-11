# Mejoras en el Sistema de Logging de Clientes

**Fecha:** 10 de noviembre de 2025  
**Responsable:** Sistema de Logging  
**Módulo:** apps.orgs (Clientes)

---

## Resumen

Se implementó un **sistema de logging completo y estructurado** para el módulo de clientes, siguiendo las mejores prácticas establecidas en el módulo de autenticación y usuarios. Ahora todos los eventos importantes de clientes quedan registrados para auditoría y debugging.

---

## Problema Identificado

El módulo de clientes NO tenía logging adecuado para:
- ❌ Creación de clientes
- ❌ Actualización de clientes
- ❌ Eliminación de clientes
- ❌ Manejo de errores estructurado

Esto dificultaba:
- Auditoría de cambios
- Debugging de problemas
- Trazabilidad de acciones de usuarios
- Cumplimiento de estándares de seguridad

---

## Solución Implementada

### 1. Importaciones Actualizadas

Se agregaron las funciones de logging estructurado:

```python
from core.structured_logging import log_error, log_info
from django.core.exceptions import PermissionDenied, ValidationError
```

Se cambió el logger genérico por uno específico del módulo:

```python
logger = logging.getLogger('apps.orgs')
```

### 2. ClientCreateView - Logging de Creación

**Eventos agregados:**

#### ✅ CLIENT_CREATED (INFO)
Registra cuando se crea exitosamente un cliente.

```json
{
  "event": "CLIENT_CREATED",
  "message": "Cliente 'Hotel Plaza Central' creado exitosamente",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "email": "contacto@hotelplaza.com",
  "is_active": true,
  "created_by": "admin@arquitectos.com"
}
```

#### ❌ CLIENT_CREATE_FAILED (ERROR)

**Error CLI001:** Error inesperado al crear cliente

```json
{
  "event": "CLIENT_CREATE_FAILED",
  "error_code": "CLI001",
  "error_message": "Database connection error",
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "created_by": "admin@arquitectos.com",
  "exception_type": "OperationalError"
}
```

**Error CLI002:** Cliente duplicado

```json
{
  "event": "CLIENT_CREATE_FAILED",
  "error_code": "CLI002",
  "error_message": "Cliente duplicado - ya existe un cliente con este nombre",
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "created_by": "admin@arquitectos.com",
  "exception_type": "IntegrityError"
}
```

---

### 3. ClientUpdateView - Logging de Actualización

**Características:**
- ✅ Tracking detallado de cambios campo por campo
- ✅ Log solo cuando hay cambios reales
- ✅ Manejo de errores robusto

#### ✅ CLIENT_UPDATED (INFO)

```json
{
  "event": "CLIENT_UPDATED",
  "message": "Cliente 'Hotel Plaza Central' actualizado con 2 cambio(s)",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "changes": [
    {
      "field": "email",
      "field_label": "Email",
      "old": "contacto@hotelplaza.com",
      "new": "admin@hotelplaza.com"
    },
    {
      "field": "is_active",
      "field_label": "Estado activo",
      "old": true,
      "new": false
    }
  ],
  "updated_by": "admin@arquitectos.com"
}
```

**Campos rastreados:**
- `name` - Nombre
- `email` - Email
- `phone_number` - Teléfono
- `is_active` - Estado activo

#### ❌ CLIENT_UPDATE_FAILED (ERROR)

**Error CLI003:** Error inesperado al actualizar

**Error CLI004:** Cliente duplicado al actualizar

---

### 4. ClientDeleteView - Logging de Eliminación

**Características:**
- ✅ Captura información ANTES de eliminar
- ✅ Log de auditoría completo
- ✅ Manejo de errores con rollback

#### ✅ CLIENT_DELETED (INFO)

```json
{
  "event": "CLIENT_DELETED",
  "message": "Cliente 'Hotel Plaza Central' eliminado exitosamente",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "deleted_by": "admin@arquitectos.com"
}
```

#### ❌ CLIENT_DELETE_FAILED (ERROR)

**Error CLI005:** Error al eliminar cliente

```json
{
  "event": "CLIENT_DELETE_FAILED",
  "error_code": "CLI005",
  "error_message": "Cannot delete client with active projects",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "deleted_by": "admin@arquitectos.com",
  "exception_type": "ProtectedError"
}
```

---

### 5. ClientToggleStatusView - Mejoras en Logging

**Antes:**
```python
logger.info(f"Cliente {action}: {client_to_toggle.name} (ID: {client_to_toggle.id})")
```

**Después:** Logging estructurado completo

#### ✅ CLIENT_STATUS_CHANGED (INFO)

```json
{
  "event": "CLIENT_STATUS_CHANGED",
  "message": "Cliente 'Hotel Plaza Central' desactivado",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "old_status": true,
  "new_status": false,
  "changed_by": "admin@arquitectos.com"
}
```

#### ❌ CLIENT_STATUS_CHANGE_FAILED (ERROR)

**Error CLI006:** Datos JSON inválidos

**Error CLI007:** Error inesperado al cambiar estado

---

## Códigos de Error Implementados

| Código | Descripción | Severidad |
|--------|-------------|-----------|
| CLI001 | Error inesperado al crear cliente | ERROR |
| CLI002 | Cliente duplicado (creación) | ERROR |
| CLI003 | Error inesperado al actualizar cliente | ERROR |
| CLI004 | Cliente duplicado (actualización) | ERROR |
| CLI005 | Error al eliminar cliente | ERROR |
| CLI006 | Datos JSON inválidos (toggle status) | ERROR |
| CLI007 | Error al cambiar estado del cliente | ERROR |

---

## Beneficios

### 1. Auditoría Completa
✅ Todos los cambios en clientes quedan registrados  
✅ Se sabe quién realizó cada acción (created_by, updated_by, deleted_by)  
✅ Se registra qué cambió exactamente (tracking de campos)

### 2. Debugging Mejorado
✅ Logs estructurados en formato JSON  
✅ Códigos de error únicos para cada tipo de problema  
✅ Stack traces completos en errores inesperados

### 3. Seguridad y Compliance
✅ Trazabilidad completa de acciones  
✅ Registro de IPs y usuarios (via middleware)  
✅ Cumplimiento de estándares de auditoría

### 4. Consistencia
✅ Misma estructura que módulo de usuarios  
✅ Misma estructura que módulo de autenticación  
✅ Fácil de mantener y extender

---

## Comparación: Antes vs Después

### Antes
```python
def form_valid(self, form):
    form.instance.organization = self.request.user.organization
    try:
        response = super().form_valid(form)
        messages.success(self.request, "Cliente creado con éxito.")
        return response
    except IntegrityError:
        form.add_error('name', 'Ya existe un cliente con este nombre.')
        return self.form_invalid(form)
```

**Problemas:**
- ❌ Sin logging de éxito
- ❌ Sin logging de error
- ❌ Sin información de auditoría
- ❌ Sin trazabilidad

### Después
```python
def form_valid(self, form):
    form.instance.organization = self.request.user.organization
    try:
        response = super().form_valid(form)
        
        # Log estructurado de creación
        log_info(
            event='CLIENT_CREATED',
            message=f"Cliente '{self.object.name}' creado exitosamente",
            logger_name='apps.orgs',
            client_id=self.object.id,
            client_name=self.object.name,
            organization_id=self.object.organization.id,
            created_by=self.request.user.email
        )
        
        messages.success(self.request, "Cliente creado con éxito.")
        return response
        
    except IntegrityError as e:
        log_error(
            event='CLIENT_CREATE_FAILED',
            error_code='CLI002',
            error_message='Cliente duplicado',
            logger_name='apps.orgs',
            client_name=form.cleaned_data.get('name'),
            created_by=self.request.user.email
        )
        form.add_error('name', 'Ya existe un cliente con este nombre.')
        return self.form_invalid(form)
```

**Ventajas:**
- ✅ Logging completo de éxito
- ✅ Logging estructurado de errores
- ✅ Códigos de error únicos
- ✅ Información de auditoría completa
- ✅ Trazabilidad del usuario

---

## Archivos Modificados

1. **arc_manager/apps/orgs/views.py**
   - Agregadas importaciones de logging estructurado
   - Actualizado logger a 'apps.orgs'
   - Implementado logging en ClientCreateView
   - Implementado logging en ClientUpdateView
   - Implementado logging en ClientDeleteView
   - Mejorado logging en ClientToggleStatusView

---

## Testing Manual Recomendado

### 1. Crear Cliente
1. Ir a /clients/create/
2. Crear cliente exitosamente
3. Verificar log: `CLIENT_CREATED` con todos los campos
4. Intentar crear cliente duplicado
5. Verificar log: `CLIENT_CREATE_FAILED` con código CLI002

### 2. Actualizar Cliente
1. Ir a /clients/<id>/edit/
2. Cambiar email y teléfono
3. Verificar log: `CLIENT_UPDATED` con lista de cambios
4. Guardar sin cambios
5. Verificar mensaje: "No se realizaron cambios" (sin log)

### 3. Eliminar Cliente
1. Ir a /clients/<id>/delete/
2. Confirmar eliminación
3. Verificar log: `CLIENT_DELETED` con info del cliente eliminado

### 4. Cambiar Estado
1. Toggle activo/inactivo desde lista
2. Verificar log: `CLIENT_STATUS_CHANGED` con old_status y new_status

---

## Próximos Pasos

### Opcional - Mejoras Futuras
- [ ] Agregar métricas de tiempo de respuesta
- [ ] Implementar alertas automáticas para errores CLI001-CLI007
- [ ] Dashboard de auditoría de clientes
- [ ] Exportar logs a sistema externo (ELK, Datadog, etc.)

---

## Conclusión

El módulo de clientes ahora tiene el **mismo nivel de calidad** en logging que los módulos de autenticación y usuarios. Todos los eventos importantes quedan registrados de forma estructurada, facilitando auditoría, debugging y cumplimiento de estándares de seguridad.

**Estado:** ✅ COMPLETADO

