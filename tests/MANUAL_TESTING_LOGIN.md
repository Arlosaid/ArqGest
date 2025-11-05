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

### HP-01: Login Exitoso - Usuario Normal

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

### HP-02: Login Exitoso - Con "Recordarme"

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

### HP-03: Login Exitoso - Superusuario

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

### HP-04: Login Exitoso - Org Admin

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

### HP-05: Logout Exitoso

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

### VD-01: Email Vacío

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

### VD-02: Contraseña Vacía

**Pasos:**
1. Ingresar email válido
2. Dejar campo contraseña **vacío**
3. Intentar hacer login

**Resultado esperado:**
- ✅ Validación HTML5: "Por favor, rellene este campo"
- ✅ No se envía el formulario

---

### VD-03: Email con Formato Inválido

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

### VD-04: Email No Registrado

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

### VD-05: Contraseña Incorrecta

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

### VD-06: Case Sensitivity - Email

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

### VD-07: Case Sensitivity - Contraseña

**Pasos:**
1. Usuario con password: `MyPassword123`
2. Intentar login con: `mypassword123`

**Resultado esperado:**
- ❌ Login fallido
- ✅ Las contraseñas **SÍ son case-sensitive**

---

### VD-08: Espacios en Credenciales

**Objetivo:** Verificar manejo de espacios leading/trailing

**Casos de prueba:**

| Email ingresado | Password ingresado | ¿Debe funcionar? |
|----------------|-------------------|------------------|
| ` test@example.com` | `Password123` | ✅ Sí (trim automático) |
| `test@example.com ` | `Password123` | ✅ Sí (trim automático) |
| `test@example.com` | ` Password123` | ❌ No (password exacto) |
| `test@example.com` | `Password123 ` | ❌ No (password exacto) |

---

### VD-09: Caracteres Especiales en Email

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

### VD-10: Inyección SQL en Campos

**Objetivo:** Verificar protección contra SQL injection

**Payloads de prueba:**
```
Email: admin'--
Email: ' OR '1'='1
Email: admin'; DROP TABLE users--
Password: ' OR '1'='1'--
```

**Resultado esperado:**
- ✅ Login fallido sin errores
- ✅ No hay ejecución SQL maliciosa
- ✅ Django ORM previene automáticamente
- ✅ Log: `LOGIN FALLIDO | Motivo: Email NO existe`

---

## 🛡️ ESCENARIOS DE SEGURIDAD

### SEG-01: Protección Contra Fuerza Bruta

**Objetivo:** Verificar bloqueo por intentos fallidos

**Configuración actual:**
- `AXES_FAILURE_LIMIT = 10` intentos
- `AXES_COOLOFF_TIME = 0.25` horas (15 minutos)

**Pasos:**
1. Ingresar email válido
2. Ingresar contraseña incorrecta
3. Repetir **10 veces**
4. Intentar el 11º login

**Resultado esperado:**
- ✅ Intento 1-10: Mensaje "credenciales inválidas"
- ✅ Intento 11+: Redirección a `/accounts/login/?locked=1`
- ✅ Mensaje: "Cuenta bloqueada: demasiados intentos"
- ✅ Log: `PASSWORD RESET BLOQUEADO` (si intentan recuperar password)
- ⏱️ **Esperar 15 minutos** → bloqueo se levanta automáticamente

**Verificación:**
- Revisar en admin Django: `/admin/axes/accessattempt/`
- Ver contador de intentos por IP y username

---

### SEG-02: Bloqueo por IP

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

### SEG-04: CSRF Protection

**Objetivo:** Verificar protección contra CSRF

**Pasos:**
1. Inspeccionar formulario de login
2. Verificar presencia de token CSRF
3. Intentar enviar POST sin token

**Verificación:**
```html
<input type="hidden" name="csrfmiddlewaretoken" value="...">
```

**Prueba de ataque:**
1. Crear HTML externo con formulario POST a `/accounts/login/`
2. Omitir token CSRF
3. Intentar enviar

**Resultado esperado:**
- ❌ Request rechazado: `403 Forbidden`
- ✅ Mensaje: "CSRF verification failed"

**Configuración:**
- `SESSION_COOKIE_SAMESITE = 'Lax'`
- `CSRF_COOKIE_SECURE = True` (en producción)

---

### SEG-05: Clickjacking Protection

**Objetivo:** Verificar headers de seguridad

**Pasos:**
1. Hacer login exitoso
2. Inspeccionar respuesta HTTP en DevTools → Network

**Resultado esperado:**
```http
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none'
```

**Prueba:**
1. Crear página con `<iframe src="https://tuapp.com/accounts/login/">`
2. Intentar cargar en navegador
3. Debe bloquearse

---

### SEG-06: Password Exposure en Logs

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

### SEG-07: Session Fixation

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

### SEG-08: Brute Force en Password Reset

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

### SEG-09: Password Reset Token Security

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

---

### SEG-10: Información en Mensajes de Error

**Objetivo:** Prevenir enumeración de usuarios

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

### ACC-01: Cuenta Inactiva

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

### ACC-02: Usuario sin Organización

**Objetivo:** Verificar comportamiento con usuarios sin org

**Pre-requisitos:**
- Usuario con `organization=NULL`

**Pasos:**
1. Hacer login
2. Verificar acceso al dashboard

**Resultado esperado:**
- ✅ Login exitoso
- ✅ Mensaje en dashboard: "No perteneces a ninguna organización"
- ✅ Funcionalidad limitada
- ✅ Log: `Org: Sin organización`

---

### ACC-03: Redirección Post-Login

**Objetivo:** Verificar parámetro `?next=`

**Pasos:**
1. Intentar acceder a URL protegida sin autenticar: `/projects/123/`
2. Sistema redirige a: `/accounts/login/?next=/projects/123/`
3. Hacer login

**Resultado esperado:**
- ✅ Después del login → redirigir a `/projects/123/` (no al dashboard)
- ✅ Si `next` no existe → redirigir a `/`

**Pruebas de seguridad:**
- `?next=https://evil.com` → debe validarse como URL interna
- `?next=//evil.com` → debe bloquearse

---

### ACC-04: Acceso a Login Estando Autenticado

**Objetivo:** Verificar comportamiento si usuario ya tiene sesión

**Pasos:**
1. Usuario ya autenticado
2. Navegar manualmente a `/accounts/login/`

**Resultado esperado:**
- ✅ Redirección automática a dashboard (`/`)
- **O** mostrar página de login con mensaje: "Ya has iniciado sesión"

---

### ACC-05: Superuser Restringido de App Normal

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

### SES-01: Duración de Sesión - Sin "Recordarme"

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

### SES-02: Duración de Sesión - Con "Recordarme"

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

### SES-03: Cerrar Navegador - Sesión Persistente

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

### SES-04: Sesión Expirada

**Objetivo:** Verificar comportamiento con sesión expirada

**Pasos simulados:**
1. Login exitoso
2. **Simular** expiración (eliminar cookie en DevTools o modificar timestamp en BD)
3. Intentar acceder a ruta protegida

**Resultado esperado:**
- ✅ Redirección a `/accounts/login/?next=/ruta-protegida/`
- ✅ No hay error 500

---

### SES-05: Múltiples Sesiones Simultáneas

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

### SES-06: Limpieza de Flags de Sesión

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

### SES-07: Session Hijacking Prevention

**Objetivo:** Verificar validación de IP/User-Agent

**Pasos:**
1. Login exitoso → anotar session ID
2. Modificar User-Agent en DevTools
3. Hacer request con misma cookie

**Resultado esperado (depende de configuración):**
- Django por defecto **NO valida** IP/UA automáticamente
- Si hay middleware custom: sesión debe invalidarse

**Recomendación de seguridad:**
- En producción, considerar agregar validación de IP cambios drásticos

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

### PWD-03: Password Reset - Rate Limiting

**Objetivo:** Prevenir spam de solicitudes

**Pasos:**
1. Solicitar reset para `test@example.com`
2. Inmediatamente solicitar de nuevo para mismo email
3. Repetir múltiples veces

**Resultado esperado:**
- ✅ 1ª solicitud: "Te enviamos instrucciones"
- ✅ 2ª+ solicitud: "Ya enviamos instrucciones. Revisa tu correo o espera 15 minutos"
- ✅ Cache: `password_reset_test@example.com` válido 15 min
- ❌ No se envían múltiples emails

---

### PWD-04: Password Reset - Token Expirado

**Pasos:**
1. Solicitar reset
2. **Esperar >1 hora** (PASSWORD_RESET_TIMEOUT = 3600)
3. Intentar usar el enlace

**Resultado esperado:**
- ❌ Mensaje: "El enlace ha expirado"
- ✅ Opción: "Solicitar nuevo enlace"

---

### PWD-05: Password Reset - Token Usado

**Pasos:**
1. Solicitar reset → recibir enlace
2. Usar enlace → cambiar contraseña exitosamente
3. **Volver a usar el mismo enlace**

**Resultado esperado:**
- ❌ Mensaje: "El enlace ya no es válido"
- ✅ Token de un solo uso

---

### PWD-06: Password Reset - Validación de Nueva Contraseña

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

### PWD-07: Password Reset - Contraseñas No Coinciden

**Pasos:**
1. Ingresar nueva contraseña: `NewPass123!`
2. Confirmar con: `NewPass456!` (diferente)
3. Submit

**Resultado esperado:**
- ❌ Error: "Las contraseñas no coinciden"
- ❌ No se guarda la contraseña

---

### PWD-08: Force Password Change - Contraseña Actual Incorrecta

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

### PWD-09: Force Password Change - Nueva = Actual

**Pasos:**
1. En force password change
2. Ingresar contraseña actual: `OldPass123`
3. Ingresar nueva contraseña: `OldPass123` (misma)
4. Submit

**Resultado esperado:**
- ❌ Error: "La nueva contraseña debe ser diferente a la actual"

---

### PWD-10: Force Password Change - Bypass Attempt

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

### UI-01: Responsive Design - Mobile

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

### UI-02: Toggle de Mostrar/Ocultar Contraseña

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

### UI-03: Accesibilidad - Navegación con Teclado

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

### UI-04: Accesibilidad - Lectores de Pantalla

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

### UI-05: Estados de Validación Visual

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

### UI-06: Mensajes de Error - Persistencia

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

### UI-07: Animaciones y Transiciones

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

### UI-08: Branding y Estética

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

### UI-09: Indicadores de Carga

**Pasos:**
1. Click en "Iniciar Sesión"
2. Observar durante procesamiento

**Resultado esperado:**
- ✅ Botón deshabilitado inmediatamente
- ✅ Texto cambia a "Iniciando sesión..." o spinner
- ✅ Cursor cambia a `wait` o `progress`
- ✅ Previene doble submit

---

### UI-10: Links y Navegación

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
