# 📊 REFERENCIA RÁPIDA: LOGS POR CÓDIGO DE ERROR
## ARC Manager - Railway Logs

**Fecha:** 4 de Noviembre 2025

---

## 🎯 BÚSQUEDA RÁPIDA DE LOGS

### **Por Evento**

```bash
# LOGINS
railway logs | grep "LOGIN EXITOSO"        # Logins correctos
railway logs | grep "LOGIN FALLIDO"        # Logins fallidos
railway logs | grep "SUPERUSER LOGIN"      # Logins de superuser (crítico)
railway logs | grep "ORG_ADMIN LOGIN"      # Logins de admins

# USUARIOS
railway logs | grep "user_created"         # Nuevos usuarios
railway logs | grep "user_updated"         # Usuarios modificados
railway logs | grep "user_save_failed"     # Errores guardando usuarios

# CONTRASEÑAS
railway logs | grep "PASSWORD CHANGED"     # Cambios de contraseña
railway logs | grep "PASSWORD CHANGE REQUIRED"  # Requiere cambio
railway logs | grep "Password reset"       # Recuperación contraseña

# ERRORES
railway logs | grep "ERROR"                # Todos los errores
railway logs | grep "Status: 500"          # Errores internos
railway logs | grep "WARNING"              # Alertas de seguridad

# EMAILS
railway logs | grep "Email enviado"        # Emails exitosos
railway logs | grep "Error enviando email" # Emails fallidos
```

---

## 📋 CÓDIGOS DE ERROR Y SUS LOGS

### **USER ERROR CODES (USR001-USR999)**

| Código | Evento | Log Esperado | Nivel |
|--------|--------|--------------|-------|
| `USR001` | Email duplicado al crear | `user_create_failed \| [USR001] \| Email duplicado \| target_email: ...` | ERROR |
| `USR002` | Superuser sin is_staff | `superuser_creation_failed \| [USR002] \| is_staff debe ser True` | ERROR |
| `USR003` | Superuser sin is_superuser | `superuser_creation_failed \| [USR003] \| is_superuser debe ser True` | ERROR |
| `USR004` | Error creando superuser | `superuser_creation_failed \| [USR004] \| [detalle]` | ERROR |
| `USR005` | Error guardando usuario | `user_save_failed \| [USR005] \| [detalle] \| user_email: ...` | ERROR |

---

### **AUTH ERROR CODES (A001-A999)**

| Código | Evento | Log Esperado | Nivel |
|--------|--------|--------------|-------|
| `A201` | Credenciales inválidas | `LOGIN FALLIDO \| Motivo: Contraseña INCORRECTA \| Email: ...` | WARNING |
| `A202` | Cuenta bloqueada | `LOGIN FALLIDO \| Motivo: Cuenta bloqueada \| Email: ...` | WARNING |
| `A203` | Cuenta inactiva | `LOGIN BLOQUEADO - CUENTA INACTIVA \| Email: ...` | WARNING |

---

### **EMAIL ERROR CODES (E001-E999)**

| Código | Evento | Log Esperado | Nivel |
|--------|--------|--------------|-------|
| `E001` | Email enviado correctamente | `Email enviado a: usuario@test.com` | INFO |
| `E002` | Email fallido | `Error enviando email a: ... \| Error: [detalle]` | ERROR |

---

## 🔍 LOGS POR MÓDULO Y OPERACIÓN

### **ACCOUNTS (Login/Logout/Password)**

| Operación | Log de Éxito | Log de Error |
|-----------|-------------|--------------|
| **Login normal** | `INFO \| LOGIN EXITOSO \| Email: user@test.com \| ID: 123` | `WARNING \| LOGIN FALLIDO \| Motivo: Contraseña INCORRECTA` |
| **Login superuser** | `WARNING \| SUPERUSER LOGIN \| Email: admin@test.com` | `WARNING \| LOGIN FALLIDO \| Motivo: Email NO existe` |
| **Login org_admin** | `INFO \| LOGIN EXITOSO ...`<br>`WARNING \| ORG_ADMIN LOGIN ...` | — |
| **Logout** | `INFO \| LOGOUT EXITOSO \| Email: user@test.com` | — |
| **Password change** | `INFO \| PASSWORD CHANGED \| Email: user@test.com` | `WARNING \| Contraseña actual incorrecta para ...` |
| **Password reset** | `INFO \| Password reset solicitado para: user@test.com` | `WARNING \| Password reset rate limit alcanzado` |

---

### **USERS (Gestión)**

| Operación | Log de Éxito | Log de Error |
|-----------|-------------|--------------|
| **Crear usuario** | `INFO \| user_created \| entity_id: 123 \| user_email: nuevo@test.com` | `ERROR \| user_create_failed \| [USR001] \| Email duplicado` |
| **Actualizar usuario** | `INFO \| user_updated \| changes: [('status_change', 'activated')]` | `ERROR \| user_save_failed \| [USR005] \| [detalle]` |
| **Eliminar usuario** | `INFO \| Usuario eliminado: user@test.com` | `ERROR \| Error al eliminar usuario \| [detalle]` |

---

### **ORGANIZATIONS**

| Operación | Log de Éxito | Log de Error |
|-----------|-------------|--------------|
| **Crear org** | `INFO \| organization_created \| entity_id: 10 \| name: Nueva Empresa` | `ERROR \| organization_create_failed \| [detalle]` |
| **Actualizar org** | `INFO \| organization_updated \| changes: [('extra_storage_gb', '0 -> 50')]` | — |
| **Límite usuarios** | — | `WARNING \| La organización ... ha alcanzado su límite de usuarios` |

---

### **MODELS - USER SAVE**

| Operación | Log de Éxito | Log de Error |
|-----------|-------------|--------------|
| **Nuevo usuario (dev)** | `INFO \| user_saved \| action: created \| entity_id: 123` | — |
| **Usuario actualizado** | `INFO \| user_updated \| changes: [...]` (solo si hay cambios críticos) | `ERROR \| user_save_failed \| [USR005] \| [detalle]` |
| **Superuser creado** | `WARNING \| SUPERUSUARIO CREADO - admin@test.com` | — |
| **Cambio rol superuser** | `WARNING \| CAMBIO CRÍTICO: Usuario ... - promovido a superusuario` | — |

---

### **SIGNALS - VALIDACIONES**

| Validación | Log (Indirecto desde save) |
|------------|---------------------------|
| **Usuario sin org** | `ERROR \| user_save_failed \| [USR005] \| Los usuarios activos deben tener org` |
| **Límite usuarios** | `ERROR \| user_save_failed \| [USR005] \| La organización ... ha alcanzado límite` |
| **Admin sin org** | `ERROR \| user_save_failed \| [USR005] \| Admins deben tener organización` |

---

### **MIDDLEWARE**

| Tipo Request | Log |
|-------------|-----|
| **200 OK** | `INFO \| GET /dashboard/ \| Status: 200 \| Usuario: user@test.com \| Tiempo: 0.15s` |
| **400 Bad Request** | `WARNING \| POST /api/ \| Status: 400 \| Error: Validación fallida` |
| **403 Forbidden** | `WARNING \| GET /admin/ \| Status: 403 \| Error: Acceso denegado` |
| **404 Not Found** | `INFO \| GET /inexistente/ \| Status: 404` |
| **500 Error** | `ERROR \| POST /op/ \| Status: 500 \| Error: DatabaseError \| Traceback: [...]` |

---

### **EMAIL**

| Operación | Log de Éxito | Log de Error |
|-----------|-------------|--------------|
| **Credenciales nuevas** | `INFO \| Email de credenciales enviado a: nuevo@test.com` | `WARNING \| Error enviando email a usuario creado` |
| **Password reset** | `INFO \| Password reset email enviado a: user@test.com` | `ERROR \| Error enviando email a: ... \| Error: SMTP timeout` |

---

## 🎨 PATRONES DE LOGS POR NIVEL

### **INFO - Operaciones Normales ✅**

```
LOGIN EXITOSO | Email: user@test.com | ID: 123 | Rol: Usuario | Org: Mi Empresa
LOGOUT EXITOSO | Email: user@test.com | Duración sesión: 45 minutos
user_created | action: created | entity_id: 123 | user_email: nuevo@test.com
user_updated | action: updated | entity_id: 123 | changes: [...]
PASSWORD CHANGED | Email: user@test.com | password_change_required: False
GET /dashboard/ | Status: 200 | Usuario: user@test.com | Tiempo: 0.15s
Email enviado a: user@test.com
organization_created | entity_id: 10 | name: Nueva Empresa
```

---

### **WARNING - Alertas de Seguridad / Problemas ⚠️**

```
LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: user@test.com | IP: 203.0.113.45
LOGIN FALLIDO | Motivo: Email NO existe | Email: noexiste@test.com | IP: 203.0.113.45
LOGIN BLOQUEADO - CUENTA INACTIVA | Email: inactivo@test.com
SUPERUSER LOGIN | Email: admin@test.com | IP: 203.0.113.45 | Sesión: 7 días
ORG_ADMIN LOGIN | Email: admin@empresa.com | Org: Mi Empresa | IP: 203.0.113.45
Password reset rate limit alcanzado para: user@test.com
Password reset solicitado para usuario INACTIVO: inactivo@test.com
SUPERUSUARIO CREADO - admin@test.com | user_id: 1
CAMBIO CRÍTICO: Usuario user@test.com - promovido a superusuario
La organización Mi Empresa ha alcanzado su límite de usuarios (10/10)
POST /api/ | Status: 400 | Error: Validación fallida
GET /admin/ | Status: 403 | Error: Acceso denegado
Contraseña actual incorrecta para usuario: user@test.com
Nueva contraseña muy corta para user@test.com: 5 caracteres
Error enviando email a usuario creado: nuevo@test.com
```

---

### **ERROR - Fallos del Sistema 🚨**

```
user_save_failed | [USR005] | Los usuarios activos deben tener org | user_email: user@test.com
user_create_failed | [USR001] | Email duplicado | target_email: existente@test.com
user_create_failed | [USR005] | DatabaseError | target_email: nuevo@test.com
superuser_creation_failed | [USR002] | is_staff debe ser True | user_email: admin@test.com
POST /projects/create/ | Status: 500 | Error: DatabaseError | Traceback: [completo]
Error enviando email a: user@test.com | Error: SMTP connection timeout
organization_create_failed | [O004] | [detalle del error]
```

---

## 🔥 LOGS CRÍTICOS - ALERTA INMEDIATA

### **Eventos que requieren revisión urgente**

1. **Login de superuser** (debe ser raro)
   ```
   WARNING | SUPERUSER LOGIN | Email: admin@test.com
   ```

2. **Múltiples login fallidos mismo IP** (posible ataque)
   ```
   WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: user@test.com | IP: 192.0.2.100
   WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: user@test.com | IP: 192.0.2.100
   WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: user@test.com | IP: 192.0.2.100
   ```

3. **Creación de superuser** (muy crítico)
   ```
   WARNING | SUPERUSUARIO CREADO - admin@test.com
   ```

4. **Errores 500 recurrentes** (problema del sistema)
   ```
   ERROR | POST /api/ | Status: 500 | Error: DatabaseError
   ```

5. **Usuario promovido a superuser** (cambio de permisos crítico)
   ```
   WARNING | CAMBIO CRÍTICO: Usuario user@test.com - promovido a superusuario
   ```

---

## 📊 EJEMPLOS DE SESIONES COMPLETAS

### **Sesión Normal - Todo OK ✅**

```
10:30:15 | INFO | LOGIN EXITOSO | Email: user@test.com | ID: 123
10:30:16 | INFO | GET /dashboard/ | Status: 200 | Usuario: user@test.com
10:31:02 | INFO | GET /projects/ | Status: 200 | Usuario: user@test.com
10:35:00 | INFO | LOGOUT EXITOSO | Email: user@test.com
```

---

### **Admin Creando Usuario - Todo OK ✅**

```
11:00:00 | INFO | POST /users/create/ | Status: 200 | Usuario: admin@empresa.com
11:00:00 | INFO | user_created | entity_id: 124 | user_email: nuevo@empresa.com
11:00:01 | INFO | Email de credenciales enviado a: nuevo@empresa.com
```

---

### **Login Fallido Múltiple - ALERTA 🚨**

```
14:20:10 | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100
14:20:15 | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100
14:20:20 | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100
14:20:25 | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100
```
**🚨 Mismo IP + mismo email + 4 intentos en 15s = Posible ataque**

---

### **Error 500 - Problema del Sistema 🚨**

```
15:45:30 | ERROR | POST /projects/create/ | Status: 500 | Usuario: user@test.com | IP: 203.0.113.45 | Error: OperationalError | Traceback:
  File "/app/apps/projects/views.py", line 123, in create_project
    project.save()
  File "/app/apps/projects/models.py", line 89, in save
    super().save(*args, **kwargs)
  django.db.utils.OperationalError: database is locked
```
**🚨 Investigar problema de base de datos**

---

## 🎯 DASHBOARD DE MONITOREO SUGERIDO

### **Métricas Clave a Monitorear**

1. **Logins exitosos/fallidos por hora**
   ```bash
   railway logs --tail 1000 | grep "LOGIN" | wc -l
   ```

2. **Errores 500 por hora**
   ```bash
   railway logs --tail 1000 | grep "Status: 500" | wc -l
   ```

3. **Logins de superuser (debe ser muy bajo)**
   ```bash
   railway logs --tail 1000 | grep "SUPERUSER LOGIN" | wc -l
   ```

4. **Usuarios creados por hora**
   ```bash
   railway logs --tail 1000 | grep "user_created" | wc -l
   ```

5. **Emails fallidos**
   ```bash
   railway logs --tail 1000 | grep "Error enviando email" | wc -l
   ```

---

## 📚 REFERENCIAS

- Códigos de error: `/arc_manager/core/error_codes.py`
- Logging estructurado: `/arc_manager/core/structured_logging.py`
- Middleware de logging: `/arc_manager/core/logging_middleware.py`
- Guía completa de logs: `/tests/GUIA_LOGS_RAILWAY.md`

---

**Última actualización:** 4 de Noviembre 2025  
**Tipo:** Referencia rápida para búsqueda de logs
