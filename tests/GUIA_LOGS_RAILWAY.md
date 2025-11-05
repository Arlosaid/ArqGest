# 📊 GUÍA DE LOGS EN RAILWAY - TRAZABILIDAD COMPLETA
## ARC Manager - Qué esperar en railway logs

**Fecha:** 4 de Noviembre 2025  
**Objetivo:** Documentar TODOS los logs que se generan por módulo para monitoreo y debugging en Railway

---

## 🎯 CÓMO VER LOGS EN RAILWAY

```bash
# Ver logs en tiempo real (recomendado para monitoreo)
railway logs --tail 100 --follow

# Ver últimos 50 logs
railway logs --tail 50

# Filtrar por nivel
railway logs | grep "INFO"
railway logs | grep "WARNING"
railway logs | grep "ERROR"

# Filtrar por evento específico
railway logs | grep "LOGIN"
railway logs | grep "user_created"
railway logs | grep "PASSWORD"

# Buscar logs de un usuario específico
railway logs | grep "usuario@test.com"
```

---

## 📋 FORMATO DE LOGS

### **Estructura Estándar**

Todos los logs siguen este formato:

```
[NIVEL] | [EVENTO] | [DETALLES] | [CONTEXTO]
```

**Ejemplo:**
```
INFO | LOGIN EXITOSO | Email: user@test.com | ID: 123 | Rol: Usuario | Org: Test Org | IP: 203.0.113.45 | Sesión: 7 días
```

---

## 🔐 MÓDULO 1: ACCOUNTS (Login/Logout/Password)

### **📍 Archivo:** `apps/accounts/views.py`

---

#### **1.1 Login Exitoso - Usuario Regular**

**Cuándo:** Usuario se loguea correctamente (no superuser, no org_admin)

**Log:**
```
INFO | LOGIN EXITOSO | Email: usuario@test.com | ID: 123 | Rol: Usuario | Org: Mi Organización | IP: 203.0.113.45 | Sesión: 7 días
```

**Cuándo aparece:**
- ✅ Credenciales correctas
- ✅ Usuario activo
- ✅ NO es superuser
- ✅ NO es org_admin
- ✅ NO requiere cambio de contraseña

**Contexto incluido:**
- Email del usuario
- ID en base de datos
- Rol (Usuario / Admin Org)
- Nombre de organización
- IP de origen
- Duración de sesión (7 días o 30 días si marcó "remember me")

---

#### **1.2 Login Exitoso - Con Remember Me**

**Cuándo:** Usuario marca checkbox "Recordarme"

**Log:**
```
INFO | LOGIN EXITOSO | Email: usuario@test.com | ID: 123 | Rol: Usuario | Org: Mi Organización | IP: 203.0.113.45 | Sesión: 30 días
```

**Diferencia:** Sesión dice `30 días` en lugar de `7 días`

---

#### **1.3 Login Exitoso - Superuser (CRÍTICO)**

**Cuándo:** Superuser se loguea

**Log 1 (WARNING - Crítico):**
```
WARNING | SUPERUSER LOGIN | Email: admin@arcmanager.com | IP: 203.0.113.45 | Sesión: 7 días
```

**Por qué WARNING:**
- ⚠️ Login de superuser es evento de seguridad crítico
- ⚠️ Debe monitorearse para detectar accesos no autorizados
- ⚠️ Nivel WARNING permite configurar alertas

**Redirección:** `/admin/` (Django Admin)

---

#### **1.4 Login Exitoso - Org Admin (Seguridad)**

**Cuándo:** Admin de organización se loguea

**Log 1 (INFO - Login normal):**
```
INFO | LOGIN EXITOSO | Email: admin@empresa.com | ID: 45 | Rol: Administrador | Org: Empresa XYZ | IP: 203.0.113.45 | Sesión: 7 días
```

**Log 2 (WARNING - Seguridad):**
```
WARNING | ORG_ADMIN LOGIN | Email: admin@empresa.com | Org: Empresa XYZ | IP: 203.0.113.45
```

**Por qué doble log:**
- INFO → Auditoría normal
- WARNING → Seguridad (admins tienen permisos elevados)

---

#### **1.5 Login - Requiere Cambio de Contraseña**

**Cuándo:** Usuario con `password_change_required=True` se loguea

**Log:**
```
INFO | PASSWORD CHANGE REQUIRED | Email: temporal@test.com | IP: 203.0.113.45
```

**Resultado:**
- Login exitoso
- Redirección a `/accounts/force-password-change/`
- Usuario no puede acceder a otras páginas

---

#### **1.6 Login Fallido - Contraseña Incorrecta**

**Cuándo:** Contraseña incorrecta pero email existe

**Log:**
```
WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: usuario@test.com | IP: 203.0.113.45
```

**Contexto:**
- Motivo específico en log (backend)
- Mensaje genérico al usuario (frontend): "Credenciales incorrectas"

---

#### **1.7 Login Fallido - Email No Existe**

**Cuándo:** Email no está registrado

**Log:**
```
WARNING | LOGIN FALLIDO | Motivo: Email NO existe | Email: noexiste@test.com | IP: 203.0.113.45
```

**Seguridad:**
- ✅ Log muestra motivo real (backend)
- ✅ Usuario ve mensaje genérico (frontend): "Credenciales incorrectas"
- ✅ No se revela que el email no existe (previene user enumeration)

---

#### **1.8 Login Fallido - Cuenta Inactiva**

**Cuándo:** Usuario existe pero `is_active=False`

**Log 1 (WARNING - En form):**
```
WARNING | LOGIN BLOQUEADO - CUENTA INACTIVA | Email: inactivo@test.com
```

**Log 2 (WARNING - En view):**
```
WARNING | LOGIN FALLIDO | Motivo: Cuenta INACTIVA | Email: inactivo@test.com | IP: 203.0.113.45
```

**Mensaje al usuario:** "Tu cuenta está inactiva. Contacta con el administrador..."

---

#### **1.9 Logout Exitoso**

**Cuándo:** Usuario hace logout

**Log:**
```
INFO | LOGOUT EXITOSO | Email: usuario@test.com | Duración sesión: 45 minutos
```

**Contexto:**
- Email del usuario
- Duración real de la sesión (calculada)

---

#### **1.10 Password Change Exitoso**

**Cuándo:** Usuario cambia contraseña correctamente

**Log:**
```
INFO | PASSWORD CHANGED | Email: usuario@test.com | password_change_required: False
```

**Contexto:**
- Flag `password_change_required` se pone en False
- Usuario puede acceder normalmente después

---

#### **1.11 Password Change - Contraseña Actual Incorrecta**

**Cuándo:** Usuario ingresa mal su contraseña actual

**Log:**
```
WARNING | Contraseña actual incorrecta para usuario: usuario@test.com
```

**Mensaje al usuario:** "La contraseña actual no es correcta"

---

#### **1.12 Password Change - Validación Fallida**

**Cuándo:** Nueva contraseña no cumple requisitos

**Ejemplos:**

**Contraseña muy corta:**
```
WARNING | Nueva contraseña muy corta para usuario@test.com: 5 caracteres
```

**Contraseña solo números:**
```
WARNING | Nueva contraseña completamente numérica para usuario@test.com
```

---

#### **1.13 Password Reset Solicitado**

**Cuándo:** Usuario solicita recuperación de contraseña

**Log (si email existe y usuario activo):**
```
INFO | Password reset solicitado para: usuario@test.com
```

**Log (si email no existe):**
```
INFO | Password reset solicitado para email no existente: noexiste@test.com
```

**Seguridad:**
- ✅ Ambos casos muestran mismo mensaje al usuario
- ✅ Log distingue el caso real (backend)

---

#### **1.14 Password Reset - Usuario Inactivo**

**Cuándo:** Solicitar reset para usuario inactivo

**Log:**
```
WARNING | Password reset solicitado para usuario INACTIVO: inactivo@test.com
```

**Resultado:**
- ✅ NO se envía email
- ✅ Usuario ve mensaje genérico (no revela que está inactivo)

---

#### **1.15 Password Reset - Rate Limiting**

**Cuándo:** Usuario solicita múltiples resets en < 15 minutos

**Log:**
```
WARNING | Password reset rate limit alcanzado para: usuario@test.com
```

**Mensaje al usuario:** "Ya solicitaste un reset recientemente. Espera 15 minutos."

---

## 👤 MÓDULO 2: USERS (Gestión de Usuarios)

### **📍 Archivo:** `apps/users/views.py`

---

#### **2.1 Usuario Creado Exitosamente**

**Cuándo:** Org admin crea nuevo usuario

**Log (Business Event):**
```
INFO | user_created | action: created | entity_type: user | entity_id: 123 | user_email: nuevo@test.com | organization_id: 5
```

**Contexto:**
- Email del nuevo usuario
- ID asignado
- Organización
- Usuario que lo creó (implícito en request)

---

#### **2.2 Usuario Creado - Email Enviado**

**Cuándo:** Email de credenciales enviado exitosamente

**Log:**
```
INFO | Email de credenciales enviado a: nuevo@test.com
```

**Si falla el envío:**
```
WARNING | Error enviando email a usuario creado: nuevo@test.com
```

---

#### **2.3 Usuario Creado - Error de Validación**

**Cuándo:** ValidationError durante creación

**Log:**
```
ERROR | user_create_validation_error | [USR???] | Los usuarios activos deben tener org | target_email: nuevo@test.com
```

**Mensaje al usuario:** Específico del campo (ej: "Email ya registrado")

---

#### **2.4 Usuario Creado - Email Duplicado**

**Cuándo:** IntegrityError por email duplicado

**Log:**
```
ERROR | user_create_failed | [USR001] | Email duplicado | target_email: existente@test.com
```

**Mensaje al usuario:** "Este correo ya está registrado"

---

#### **2.5 Usuario Creado - Error Inesperado**

**Cuándo:** Exception no controlada

**Log:**
```
ERROR | user_create_failed | [USR005] | [Detalle del error] | target_email: nuevo@test.com | exception_type: DatabaseError
```

**Mensaje al usuario:** "Error inesperado. Contacta soporte."

---

#### **2.6 Usuario Actualizado**

**Cuándo:** Org admin edita usuario

**Log (si hay cambios críticos):**
```
INFO | user_updated | action: updated | entity_type: user | entity_id: 123 | user_email: usuario@test.com | changes: [('status_change', 'deactivated')]
```

**Cambios críticos que se loguean:**
- Cambio de `is_active` (activado/desactivado)
- Cambio de `is_org_admin` (promovido/degradado)
- Cambio de organización

---

#### **2.7 Usuario Eliminado**

**Cuándo:** Org admin elimina usuario

**Log:**
```
INFO | Usuario eliminado: usuario@test.com | por: admin@empresa.com
```

**Si hay error:**
```
ERROR | Error al eliminar usuario: usuario@test.com | Error: [detalle]
```

---

## 🏢 MÓDULO 3: ORGANIZATIONS (Organizaciones)

### **📍 Archivo:** `apps/orgs/models.py`

---

#### **3.1 Organización Creada**

**Cuándo:** Se crea nueva organización

**Log:**
```
INFO | organization_created | action: created | entity_type: organization | entity_id: 10 | name: Nueva Empresa | slug: nueva-empresa
```

---

#### **3.2 Organización Actualizada**

**Cuándo:** Se modifica organización

**Log (solo cambios importantes):**
```
INFO | organization_updated | action: updated | entity_id: 10 | changes: [('extra_storage_gb', '0 -> 50')]
```

---

#### **3.3 Límite de Usuarios Alcanzado**

**Cuándo:** Intentar crear usuario superando límite del plan

**Log:**
```
WARNING | La organización Mi Empresa ha alcanzado su límite de usuarios (10/10)
```

**Mensaje al usuario:** "La organización ha alcanzado su límite de usuarios"

---

## 💾 MÓDULO 4: MODELS - USER

### **📍 Archivo:** `apps/accounts/models.py`

---

#### **4.1 Usuario Guardado - Nuevo (Desarrollo)**

**Cuándo:** Nuevo usuario creado (solo en DEBUG=True)

**Log:**
```
INFO | user_saved | action: created | entity_type: user | entity_id: 123 | user_email: nuevo@test.com | is_superuser: False | is_org_admin: False | organization_id: 5
```

**Nota:** Solo en desarrollo para evitar spam en producción

---

#### **4.2 Usuario Guardado - Actualizado (Producción)**

**Cuándo:** Usuario existente modificado CON cambios críticos

**Log:**
```
INFO | user_updated | action: updated | entity_type: user | entity_id: 123 | user_email: usuario@test.com | changes: [('status_change', 'deactivated')]
```

**Cambios que generan log:**
- Cambio de estado (activo/inactivo)
- Cambio de rol (promovido a admin / degradado)
- Cambio de organización

---

#### **4.3 Usuario Save Fallido**

**Cuándo:** Exception durante `user.save()`

**Log:**
```
ERROR | user_save_failed | [USR005] | [Detalle del error] | user_email: usuario@test.com | user_id: 123
```

**Nota:** El error se re-lanza para que sea capturado por quien llamó (view/admin)

---

#### **4.4 Superuser Creado (CRÍTICO)**

**Cuándo:** Se crea nuevo superusuario

**Log:**
```
WARNING | SUPERUSUARIO CREADO - admin@arcmanager.com | user_id: 1 | user_email: admin@arcmanager.com
```

**Nivel:** WARNING para seguridad (puede configurarse alerta)

---

#### **4.5 Superuser - Cambio de Permisos (CRÍTICO)**

**Cuándo:** Usuario promovido/degradado a/de superuser

**Log:**
```
WARNING | CAMBIO CRÍTICO: Usuario usuario@test.com - promovido a superusuario | user_id: 45 | old_is_superuser: False | new_is_superuser: True
```

**Log (degradado):**
```
WARNING | CAMBIO CRÍTICO: Usuario admin@test.com - removido como superusuario | user_id: 1 | old_is_superuser: True | new_is_superuser: False
```

---

## 🔒 MÓDULO 5: SIGNALS - VALIDACIONES

### **📍 Archivo:** `apps/accounts/signals.py`

---

#### **5.1 Signal - ValidationError (Usuario sin Org)**

**Cuándo:** Intentar guardar usuario activo sin organización

**Log (indirecto - desde model save):**
```
ERROR | user_save_failed | [USR005] | Los usuarios activos deben tener una organización asignada | user_email: usuario@test.com
```

**Nota:** El signal lanza `ValidationError`, el model lo captura y loggea

---

#### **5.2 Signal - Límite de Organización**

**Cuándo:** Crear usuario excediendo límite

**Log (indirecto):**
```
ERROR | user_save_failed | [USR005] | La organización Mi Empresa ha alcanzado su límite de usuarios | user_email: nuevo@test.com
```

---

#### **5.3 Signal - Superuser Creado (Post-Save)**

**Cuándo:** Nuevo superuser guardado

**Log:**
```
WARNING | superuser_created | SUPERUSUARIO CREADO - admin@arcmanager.com | user_id: 1 | user_email: admin@arcmanager.com
```

---

## 🌐 MÓDULO 6: MIDDLEWARE

### **📍 Archivo:** `core/logging_middleware.py`

---

#### **6.1 Request HTTP - Exitoso**

**Cuándo:** Request completado sin errores

**Log:**
```
INFO | GET /dashboard/ | Status: 200 | Usuario: usuario@test.com | IP: 203.0.113.45 | Tiempo: 0.15s
```

**Contexto:**
- Método HTTP (GET, POST, etc.)
- URL path
- Status code
- Email del usuario (si está autenticado)
- IP de origen
- Tiempo de respuesta

---

#### **6.2 Request HTTP - Error 400 (Bad Request)**

**Cuándo:** Request malformado

**Log:**
```
WARNING | POST /api/users/ | Status: 400 | Usuario: admin@empresa.com | IP: 203.0.113.45 | Error: Validación fallida
```

---

#### **6.3 Request HTTP - Error 403 (Forbidden)**

**Cuándo:** Usuario sin permisos

**Log:**
```
WARNING | GET /admin/users/ | Status: 403 | Usuario: usuario@test.com | IP: 203.0.113.45 | Error: Acceso denegado
```

---

#### **6.4 Request HTTP - Error 404 (Not Found)**

**Cuándo:** URL no existe

**Log:**
```
INFO | GET /ruta-inexistente/ | Status: 404 | Usuario: usuario@test.com | IP: 203.0.113.45
```

**Nota:** 404 es INFO, no WARNING (es común en navegación)

---

#### **6.5 Request HTTP - Error 500 (Internal Server Error)**

**Cuándo:** Exception no controlada

**Log:**
```
ERROR | POST /users/create/ | Status: 500 | Usuario: admin@empresa.com | IP: 203.0.113.45 | Error: DatabaseError | Traceback: [...]
```

**Contexto completo:**
- Request completo (método, path, params)
- Usuario que generó error
- IP
- Tipo de excepción
- **Traceback completo** (para debugging)

---

## 📧 MÓDULO 7: EMAIL

### **📍 Archivos:** `apps/users/utils.py`, `core/email_utils.py`

---

#### **7.1 Email Enviado - Credenciales Nuevas**

**Cuándo:** Email de bienvenida con credenciales

**Log:**
```
INFO | Email de credenciales enviado a: nuevo@test.com
```

---

#### **7.2 Email Enviado - Password Reset**

**Cuándo:** Email de recuperación de contraseña

**Log:**
```
INFO | Password reset email enviado a: usuario@test.com
```

---

#### **7.3 Email Fallido**

**Cuándo:** Error al enviar email

**Log:**
```
ERROR | Error enviando email a: usuario@test.com | Error: SMTP connection timeout
```

---

## 🚨 MÓDULO 8: ERROR HANDLERS

### **📍 Archivo:** `core/error_handlers.py`

---

#### **8.1 Error 400 - Bad Request**

**Cuándo:** Request malformado capturado por handler

**Log (desde middleware):**
```
WARNING | GET /api/endpoint/ | Status: 400 | Usuario: usuario@test.com | IP: 203.0.113.45
```

**Usuario ve:** Mensaje amigable + redirección

---

#### **8.2 Error 403 - Forbidden**

**Cuándo:** Acceso denegado capturado por handler

**Log (desde middleware):**
```
WARNING | GET /admin/secreto/ | Status: 403 | Usuario: usuario@test.com | IP: 203.0.113.45
```

---

#### **8.3 Error 404 - Not Found**

**Cuándo:** Página no encontrada

**Log (desde middleware):**
```
INFO | GET /pagina-inexistente/ | Status: 404 | Usuario: usuario@test.com | IP: 203.0.113.45
```

**Usuario ve:** Template 404 personalizado

---

#### **8.4 Error 500 - Internal Server Error**

**Cuándo:** Exception no controlada

**Log (desde middleware):**
```
ERROR | POST /operacion/ | Status: 500 | Usuario: admin@empresa.com | IP: 203.0.113.45 | Error: DatabaseError | Traceback: [traceback completo]
```

**Usuario ve:** Mensaje genérico "Algo salió mal..." + redirección

---

## 📊 TABLA RESUMEN POR NIVEL

### **INFO - Operaciones Normales**

| Evento | Cuándo Aparece | Ejemplo |
|--------|----------------|---------|
| Login exitoso | Usuario se loguea correctamente | `LOGIN EXITOSO \| Email: user@test.com` |
| Logout | Usuario cierra sesión | `LOGOUT EXITOSO \| Email: user@test.com` |
| Usuario creado | Nuevo usuario en sistema | `user_created \| user_email: nuevo@test.com` |
| Password changed | Contraseña cambiada | `PASSWORD CHANGED \| Email: user@test.com` |
| Request exitoso | HTTP 200 | `GET /dashboard/ \| Status: 200` |
| Email enviado | Email enviado correctamente | `Email enviado a: user@test.com` |

---

### **WARNING - Eventos de Seguridad / Alertas**

| Evento | Cuándo Aparece | Ejemplo |
|--------|----------------|---------|
| Login fallido | Credenciales incorrectas | `LOGIN FALLIDO \| Motivo: Contraseña INCORRECTA` |
| Cuenta inactiva | Login bloqueado | `LOGIN BLOQUEADO - CUENTA INACTIVA` |
| Superuser login | Login de superusuario | `SUPERUSER LOGIN \| Email: admin@test.com` |
| Org admin login | Login de admin org | `ORG_ADMIN LOGIN \| Email: admin@empresa.com` |
| Rate limiting | Múltiples intentos | `Password reset rate limit alcanzado` |
| Superuser creado | Nuevo superuser | `SUPERUSUARIO CREADO - admin@test.com` |
| Error 403 | Acceso denegado | `GET /admin/ \| Status: 403` |
| Error 400 | Request malformado | `POST /api/ \| Status: 400` |

---

### **ERROR - Fallos del Sistema**

| Evento | Cuándo Aparece | Ejemplo |
|--------|----------------|---------|
| User save failed | Error guardando usuario | `user_save_failed \| [USR005] \| [detalle]` |
| User create failed | Error creando usuario | `user_create_failed \| Email duplicado` |
| Error 500 | Exception no controlada | `POST /op/ \| Status: 500 \| DatabaseError` |
| Email failed | Email no enviado | `Error enviando email a: user@test.com` |

---

## 🔍 MONITOREO EN RAILWAY

### **Comandos Útiles**

```bash
# Monitorear logins en tiempo real
railway logs --follow | grep "LOGIN"

# Ver todos los errores
railway logs --tail 100 | grep "ERROR"

# Ver eventos de seguridad
railway logs --tail 100 | grep "WARNING"

# Buscar actividad de un usuario específico
railway logs --tail 200 | grep "usuario@test.com"

# Ver creación de usuarios
railway logs --follow | grep "user_created"

# Ver cambios de contraseña
railway logs --follow | grep "PASSWORD"
```

---

### **Alertas Recomendadas**

Configurar alertas para estos eventos:

1. **Múltiples login fallidos** (mismo IP o mismo email)
   ```
   railway logs | grep "LOGIN FALLIDO" | grep "203.0.113.45"
   ```

2. **Login de superuser** (debe ser raro)
   ```
   railway logs | grep "SUPERUSER LOGIN"
   ```

3. **Errores 500** (problemas del sistema)
   ```
   railway logs | grep "Status: 500"
   ```

4. **Creación de superusers** (muy crítico)
   ```
   railway logs | grep "SUPERUSUARIO CREADO"
   ```

---

## 📋 CHECKLIST DE LOGS SALUDABLES

### **Lo que DEBE aparecer normalmente:**
- ✅ `LOGIN EXITOSO` (usuarios activos)
- ✅ `LOGOUT EXITOSO` (sesiones cerradas)
- ✅ `GET /dashboard/ | Status: 200` (navegación normal)
- ✅ `user_created` (nuevos usuarios)
- ✅ `Email enviado` (comunicaciones)

### **Lo que es NORMAL pero debe monitorearse:**
- ⚠️ `LOGIN FALLIDO` (ocasional por error de tecleo)
- ⚠️ `Status: 404` (usuarios probando URLs)
- ⚠️ `Password reset solicitado` (usuarios olvidando contraseñas)

### **Lo que es CRÍTICO y debe investigarse:**
- 🚨 `Status: 500` (errores del sistema)
- 🚨 Múltiples `LOGIN FALLIDO` del mismo IP (ataque)
- 🚨 `SUPERUSUARIO CREADO` (verificar autorización)
- 🚨 `user_save_failed` recurrente (problema en código)

---

## 🎯 EJEMPLO DE SESIÓN COMPLETA EN LOGS

### **Escenario: Usuario normal hace login, navega y logout**

```
2025-11-04T10:30:15Z | INFO | LOGIN EXITOSO | Email: usuario@test.com | ID: 123 | Rol: Usuario | Org: Mi Empresa | IP: 203.0.113.45 | Sesión: 7 días

2025-11-04T10:30:16Z | INFO | GET /dashboard/ | Status: 200 | Usuario: usuario@test.com | IP: 203.0.113.45 | Tiempo: 0.12s

2025-11-04T10:31:02Z | INFO | GET /projects/ | Status: 200 | Usuario: usuario@test.com | IP: 203.0.113.45 | Tiempo: 0.25s

2025-11-04T10:35:00Z | INFO | LOGOUT EXITOSO | Email: usuario@test.com | Duración sesión: 4 minutos
```

---

### **Escenario: Admin crea nuevo usuario**

```
2025-11-04T11:00:00Z | INFO | POST /users/create/ | Status: 200 | Usuario: admin@empresa.com | IP: 203.0.113.45 | Tiempo: 0.45s

2025-11-04T11:00:00Z | INFO | user_created | action: created | entity_type: user | entity_id: 124 | user_email: nuevo@empresa.com | organization_id: 5

2025-11-04T11:00:01Z | INFO | Email de credenciales enviado a: nuevo@empresa.com
```

---

### **Escenario: Login fallido múltiple (posible ataque)**

```
2025-11-04T14:20:10Z | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100

2025-11-04T14:20:15Z | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100

2025-11-04T14:20:20Z | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100

2025-11-04T14:20:25Z | WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: victima@test.com | IP: 192.0.2.100
```

**🚨 ALERTA:** Mismo IP, mismo email, 4 intentos en 15 segundos → Posible ataque de fuerza bruta

---

### **Escenario: Error 500 (problema del sistema)**

```
2025-11-04T15:45:30Z | ERROR | POST /projects/create/ | Status: 500 | Usuario: usuario@test.com | IP: 203.0.113.45 | Error: OperationalError | Traceback: 
  File "/app/apps/projects/views.py", line 123, in create_project
    project.save()
  File "/app/apps/projects/models.py", line 89, in save
    super().save(*args, **kwargs)
  django.db.utils.OperationalError: database is locked
```

**🚨 ACCIÓN:** Investigar problema de base de datos

---

## 📚 CONCLUSIÓN

**Esta guía cubre TODOS los logs que verás en Railway.** 

Usa esta tabla para:
- ✅ Monitorear salud del sistema
- ✅ Detectar problemas de seguridad
- ✅ Debugging de errores
- ✅ Auditoría de acciones de usuarios
- ✅ Compliance y trazabilidad

---

**Última actualización:** 4 de Noviembre 2025  
**Autor:** ARC Manager Team  
**Estado:** Documentación completa de logs
