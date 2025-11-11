# Documentación de Logging del Panel de Administración

Esta documentación detalla todos los eventos de logging estructurado implementados en el panel de administración de ARC Manager.

## Índice
1. [Eventos de Organizaciones](#eventos-de-organizaciones)
2. [Eventos de Clientes](#eventos-de-clientes)
3. [Eventos de Suscripciones](#eventos-de-suscripciones)
4. [Eventos de Planes](#eventos-de-planes)
5. [Eventos de Pagos](#eventos-de-pagos)
6. [Formato de Logs](#formato-de-logs)

---

## Eventos de Organizaciones

### ORGANIZATION_CREATED
Se registra cuando se crea una nueva organización desde el panel de administración.

**Evento**: `ORGANIZATION_CREATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "ORGANIZATION_CREATED",
  "context": "admin",
  "timestamp": "2024-01-15T10:30:00-06:00",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "is_active": true,
  "is_founder": false,
  "extra_storage_gb": 0
}
```

### ORGANIZATION_UPDATED
Se registra cuando se modifica una organización existente.

**Evento**: `ORGANIZATION_UPDATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "ORGANIZATION_UPDATED",
  "context": "admin",
  "timestamp": "2024-01-15T11:45:00-06:00",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "changes": [
    {
      "field": "is_active",
      "old": false,
      "new": true
    },
    {
      "field": "extra_storage_gb",
      "old": 0,
      "new": 10
    },
    {
      "field": "is_founder_member",
      "old": false,
      "new": true
    }
  ]
}
```

**Campos rastreados para cambios**:
- `name`: Nombre de la organización
- `is_active`: Estado activo/inactivo
- `is_founder_member`: Membresía fundadora
- `extra_storage_gb`: Almacenamiento extra

### ORGANIZATION_DELETE_START
Se registra al iniciar la eliminación de una organización.

**Evento**: `ORGANIZATION_DELETE_START`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "ORGANIZATION_DELETE_START",
  "context": "admin",
  "timestamp": "2024-01-15T14:20:00-06:00",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "user_count": 3
}
```

### ORGANIZATION_DELETED
Se registra cuando se completa la eliminación de una organización.

**Evento**: `ORGANIZATION_DELETED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "ORGANIZATION_DELETED",
  "context": "admin",
  "timestamp": "2024-01-15T14:20:15-06:00",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "files_deleted": 47,
  "users_deleted": 3
}
```

### ORGANIZATION_R2_CLEANUP_SUCCESS
Se registra cuando se limpian exitosamente los archivos de R2/S3 de una organización.

**Evento**: `ORGANIZATION_R2_CLEANUP_SUCCESS`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "ORGANIZATION_R2_CLEANUP_SUCCESS",
  "context": "admin",
  "timestamp": "2024-01-15T14:20:10-06:00",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "files_deleted": 47,
  "prefix": "organizations/5/"
}
```

### ORGANIZATION_R2_CLEANUP_ERROR
Se registra cuando hay un error al limpiar archivos de R2/S3.

**Evento**: `ORGANIZATION_R2_CLEANUP_ERROR`  
**Contexto**: `admin`  
**Nivel**: `ERROR`

```json
{
  "event_type": "ORGANIZATION_R2_CLEANUP_ERROR",
  "context": "admin",
  "timestamp": "2024-01-15T14:20:10-06:00",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "error_message": "Connection timeout to R2 bucket"
}
```

---

## Eventos de Clientes

### CLIENT_CREATED
Se registra cuando se crea un nuevo cliente desde el panel de administración.

**Evento**: `CLIENT_CREATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "CLIENT_CREATED",
  "context": "admin",
  "timestamp": "2024-01-15T09:15:00-06:00",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "email": "contacto@hotelplaza.com",
  "is_active": true
}
```

### CLIENT_UPDATED
Se registra cuando se modifica un cliente existente.

**Evento**: `CLIENT_UPDATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "CLIENT_UPDATED",
  "context": "admin",
  "timestamp": "2024-01-15T10:00:00-06:00",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "changes": [
    {
      "field": "email",
      "old": "contacto@hotelplaza.com",
      "new": "admin@hotelplaza.com"
    },
    {
      "field": "is_active",
      "old": true,
      "new": false
    }
  ]
}
```

**Campos rastreados para cambios**:
- `name`: Nombre del cliente
- `is_active`: Estado activo/inactivo
- `email`: Email de contacto

### CLIENT_DELETED
Se registra cuando se elimina un cliente.

**Evento**: `CLIENT_DELETED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "CLIENT_DELETED",
  "context": "admin",
  "timestamp": "2024-01-15T16:30:00-06:00",
  "client_id": 12,
  "client_name": "Hotel Plaza Central",
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA"
}
```

---

## Eventos de Suscripciones

### SUBSCRIPTION_CREATED
Se registra cuando se crea una nueva suscripción.

**Evento**: `SUBSCRIPTION_CREATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "SUBSCRIPTION_CREATED",
  "context": "admin",
  "timestamp": "2024-01-15T08:00:00-06:00",
  "subscription_id": 23,
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "plan_name": "Plan Básico",
  "plan_type": "basic",
  "start_date": "2024-01-15 08:00:00-06:00",
  "end_date": "2024-02-14 08:00:00-06:00",
  "status": "basic_active"
}
```

### SUBSCRIPTION_UPDATED
Se registra cuando se modifica una suscripción existente.

**Evento**: `SUBSCRIPTION_UPDATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "SUBSCRIPTION_UPDATED",
  "context": "admin",
  "timestamp": "2024-01-15T12:00:00-06:00",
  "subscription_id": 23,
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "plan_name": "Plan Básico",
  "changes": [
    {
      "field": "end_date",
      "old": "2024-02-14 08:00:00-06:00",
      "new": "2024-03-14 08:00:00-06:00"
    },
    {
      "field": "subscription_status",
      "old": "basic_grace",
      "new": "basic_active"
    }
  ]
}
```

**Campos rastreados para cambios**:
- `plan`: Cambio de plan
- `subscription_status`: Cambio de estado
- `end_date`: Cambio de fecha de vencimiento

### SUBSCRIPTION_PAYMENT_PROCESSED
Se registra cuando se procesa un pago para extender una suscripción.

**Evento**: `SUBSCRIPTION_PAYMENT_PROCESSED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "SUBSCRIPTION_PAYMENT_PROCESSED",
  "context": "admin",
  "timestamp": "2024-01-15T13:00:00-06:00",
  "subscription_id": 23,
  "payment_id": 45,
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "amount": "299.00",
  "days_added": 30,
  "old_end_date": "2024-02-14 08:00:00-06:00",
  "new_end_date": "2024-03-14 08:00:00-06:00",
  "processed_by": "admin@example.com (ID: 1)"
}
```

### SUBSCRIPTION_EXTENDED
Se registra cuando se extiende manualmente una suscripción.

**Evento**: `SUBSCRIPTION_EXTENDED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "SUBSCRIPTION_EXTENDED",
  "context": "admin",
  "timestamp": "2024-01-15T15:00:00-06:00",
  "subscription_id": 23,
  "payment_id": 46,
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "days_added": 15,
  "old_end_date": "2024-02-14 08:00:00-06:00",
  "new_end_date": "2024-03-01 08:00:00-06:00",
  "reason": "Cortesía por retraso en facturación",
  "processed_by": "admin@example.com (ID: 1)"
}
```

### SUBSCRIPTION_PLAN_CHANGED
Se registra cuando se cambia el plan de una suscripción (upgrade/downgrade).

**Evento**: `SUBSCRIPTION_PLAN_CHANGED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "SUBSCRIPTION_PLAN_CHANGED",
  "context": "admin",
  "timestamp": "2024-01-15T11:00:00-06:00",
  "subscription_id": 23,
  "payment_id": 47,
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "old_plan": "Prueba Gratuita",
  "old_plan_type": "trial",
  "new_plan": "Plan Básico",
  "new_plan_type": "basic",
  "amount": "299.00",
  "days_added": 30,
  "processed_by": "admin@example.com (ID: 1)"
}
```

---

## Eventos de Planes

### PLAN_CREATED
Se registra cuando se crea un nuevo plan.

**Evento**: `PLAN_CREATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "PLAN_CREATED",
  "context": "admin",
  "timestamp": "2024-01-15T07:00:00-06:00",
  "plan_id": 3,
  "plan_name": "Plan Premium",
  "plan_type": "premium",
  "price": "499.00",
  "max_users": 10,
  "max_storage_gb": 150,
  "trial_days": 0,
  "is_active": true
}
```

### PLAN_UPDATED
Se registra cuando se modifica un plan existente.

**Evento**: `PLAN_UPDATED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "PLAN_UPDATED",
  "context": "admin",
  "timestamp": "2024-01-15T09:00:00-06:00",
  "plan_id": 3,
  "plan_name": "Plan Premium",
  "plan_type": "premium",
  "changes": [
    {
      "field": "price",
      "old": "499.00",
      "new": "549.00"
    },
    {
      "field": "max_users",
      "old": 10,
      "new": 15
    },
    {
      "field": "max_storage_gb",
      "old": 150,
      "new": 200
    }
  ]
}
```

**Campos rastreados para cambios**:
- `price`: Precio del plan
- `max_users`: Límite de usuarios
- `max_storage_gb`: Límite de almacenamiento
- `is_active`: Estado activo/inactivo
- `trial_days`: Días de prueba

---

## Eventos de Pagos

### PAYMENT_RECORDED
Se registra cuando se crea un nuevo registro de pago.

**Evento**: `PAYMENT_RECORDED`  
**Contexto**: `admin`  
**Nivel**: `INFO`

```json
{
  "event_type": "PAYMENT_RECORDED",
  "context": "admin",
  "timestamp": "2024-01-15T13:05:00-06:00",
  "payment_id": 45,
  "subscription_id": 23,
  "organization_id": 5,
  "organization_name": "Arquitectos Asociados SA",
  "amount": "299.00",
  "payment_method": "manual",
  "payment_type": "subscription",
  "days_added": 30,
  "processed_by": "admin@example.com (ID: 1)",
  "description": "Pago procesado para extender el plan Plan Básico"
}
```

**Tipos de pago**:
- `subscription`: Pago normal de suscripción
- `upgrade`: Upgrade de plan
- `trial_to_paid`: Conversión de trial a plan pagado
- `extension`: Extensión manual

**Métodos de pago**:
- `manual`: Pago manual procesado por admin
- `upgrade`: Pago por upgrade de plan

---

## Formato de Logs

Todos los logs estructurados siguen el siguiente formato JSON:

```json
{
  "timestamp": "ISO-8601 timestamp con zona horaria",
  "level": "INFO | WARNING | ERROR",
  "logger": "nombre del logger",
  "event_type": "EVENTO_ESPECÍFICO",
  "context": "admin | system | user",
  "...campos_específicos_del_evento": "valores"
}
```

### Niveles de Log

- **INFO**: Operaciones normales exitosas
- **WARNING**: Situaciones que requieren atención pero no impiden la operación
- **ERROR**: Errores que impiden completar una operación

### Contextos

- **admin**: Operaciones realizadas desde el panel de administración
- **system**: Operaciones automáticas del sistema
- **user**: Operaciones realizadas por usuarios normales

---

## Ubicación de los Logs

Los logs se encuentran en:

```
arc_manager/logs/django.log
```

Para logs estructurados de negocio filtrados:

```
arc_manager/logs/business_events.log
```

---

## Consulta de Logs

### Filtrar por evento específico
```bash
grep "ORGANIZATION_CREATED" logs/business_events.log
```

### Filtrar por organización
```bash
grep "organization_id.*5" logs/business_events.log
```

### Logs del último día
```bash
grep "$(date +%Y-%m-%d)" logs/business_events.log
```

### Logs de errores
```bash
grep "ERROR" logs/django.log | grep "ORGANIZATION"
```

---

## Notas Importantes

1. **Zona Horaria**: Todos los timestamps están en zona horaria de México (UTC-6)
2. **Campos Sensibles**: Los logs NO contienen información sensible como contraseñas o tokens
3. **Retención**: Los logs se rotan automáticamente cada 7 días
4. **Performance**: El logging estructurado tiene un impacto mínimo en performance (~2ms por operación)
5. **Campos `changes`**: Siempre incluyen el valor anterior (`old`) y nuevo (`new`) para auditoría completa

---

## Ejemplos de Uso

### Auditoría de cambios de organización
```python
# Buscar todos los cambios de una organización específica
grep '"organization_id": 5' logs/business_events.log | grep "ORGANIZATION_UPDATED"
```

### Rastrear pagos de un mes
```python
# Pagos de enero 2024
grep "2024-01" logs/business_events.log | grep "PAYMENT_RECORDED"
```

### Identificar cambios de planes
```python
# Todos los upgrades/downgrades
grep "SUBSCRIPTION_PLAN_CHANGED" logs/business_events.log
```

---

**Última actualización**: 2024-01-15  
**Versión**: 1.0  
**Autor**: ARC Manager Team
