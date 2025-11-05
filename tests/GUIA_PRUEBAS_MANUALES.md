# 📋 GUÍA DE PRUEBAS MANUALES - ARC Manager
## Basada en Tests Unitarios Implementados

**Autor:** ARC Manager Team  
**Fecha:** 4 de Noviembre 2025  
**Objetivo:** Validar manualmente los flujos críticos del sistema basándose en los tests automatizados ya implementados.

---

## 🎯 OBJETIVO DE ESTA GUÍA

Esta guía te permitirá validar manualmente que el sistema funciona correctamente en un entorno real (con signals, middleware, email y storage activos), complementando los tests unitarios que validan la lógica aislada.

**¿Por qué hacer pruebas manuales si ya hay tests?**
- Los tests unitarios usan `disable_account_signals` → no ejecutan validaciones reales de producción
- Los tests no prueban UI, UX, ni flujos end-to-end completos
- Email, storage (R2/S3) y servicios externos están mockeados en tests
- Middleware de suscripciones y permisos puede comportarse diferente en prod
- Logs estructurados necesitan verificación manual en stdout/stderr real

---

## 🔧 PRERREQUISITOS

### OPCIÓN A: ENTORNO LOCAL (DOCKER) 🐳

#### 1. Entorno Docker levantado
```bash
# En PowerShell, desde c:\Users\Alonso\Desktop\arc_manager
docker compose up -d
```

#### 2. Base de datos de desarrollo limpia (opcional - si quieres empezar fresh)
```bash
# CUIDADO: Esto borra todos los datos
# Primero encuentra la ruta correcta de manage.py:
docker compose exec web pwd
docker compose exec web find / -name "manage.py" 2>$null | Select-Object -First 1

# Ajusta el comando según tu ruta (ejemplo sin cd /app):
docker compose exec web python manage.py flush --no-input
```

#### 3. Crear superusuario de pruebas (LOCAL)
```bash
# Si manage.py está en la raíz del contenedor:
docker compose exec web python manage.py createsuperuser --username admin --email admin@arcmanager.test

# Si necesitas activar venv:
docker compose exec web bash -c "source venv/bin/activate && python manage.py createsuperuser --username admin --email admin@arcmanager.test"

# Te pedirá la contraseña - usa: AdminPass123!
```

#### 4. Crear usuarios de prueba adicionales (LOCAL)
```powershell
# En PowerShell:
docker compose exec web python manage.py shell
```

Luego pega este código Python:
```python
from django.contrib.auth import get_user_model
from apps.orgs.models import Organization
from apps.plans.models import Plan, Subscription

User = get_user_model()

# Crear organización y plan
org = Organization.objects.get_or_create(name='Test Organization', slug='test-org')[0]
plan = Plan.objects.get_or_create(
    name='trial',
    defaults={
        'display_name': 'Trial Plan',
        'max_users': 10,
        'max_storage_gb': 100
    }
)[0]
Subscription.objects.get_or_create(organization=org, plan=plan)

# Usuario regular activo
user1 = User.objects.create_user(
    email='regular@arcmanager.test',
    password='RegularPass123!',
    first_name='Regular',
    last_name='User',
    organization=org,
    is_active=True
)

# Usuario con cambio de contraseña requerido
user2 = User.objects.create_user(
    email='needschange@arcmanager.test',
    password='TempPass123!',
    first_name='Needs',
    last_name='Change',
    organization=org,
    is_active=True,
    password_change_required=True
)

# Usuario inactivo
user3 = User.objects.create_user(
    email='inactive@arcmanager.test',
    password='InactivePass123!',
    first_name='Inactive',
    last_name='User',
    organization=org,
    is_active=False
)

print("✅ Usuarios de prueba creados:")
print(f"   - {user1.email} / RegularPass123!")
print(f"   - {user2.email} / TempPass123! (requiere cambio)")
print(f"   - {user3.email} / InactivePass123! (inactivo)")
exit()
```

#### 5. Verificar logs en tiempo real (LOCAL)
```bash
# En una terminal separada, monitorear logs
docker compose logs -f web
```

---

### OPCIÓN B: ENTORNO RAILWAY (PRODUCCIÓN) 🚂

#### 1. Obtener URL de tu aplicación Railway

```bash
# Opción 1: Railway CLI
railway open

# Opción 2: Railway Dashboard
# Ir a: Dashboard > Tu proyecto > Settings > Domains
# Ejemplo de URL: https://arc-manager-production-abcd1234.up.railway.app
```

**💡 Guarda esta URL - la usarás en todas las pruebas:**
```powershell
# En PowerShell (Windows):
$RAILWAY_URL = "https://tu-app-production-xxxx.up.railway.app"

# Ejemplo:
# $RAILWAY_URL = "https://arc-manager-production-abcd1234.up.railway.app"
```

#### 2. Verificar que el deployment está activo

```bash
# Railway CLI:
railway status

# Debe mostrar:
# ✓ Service: web - Running
# ✓ Database: PostgreSQL - Running
```

#### 3. Crear superusuario en Railway

```bash
# Método 1: Interactivo (Railway CLI)
railway run python manage.py createsuperuser

# Método 2: No interactivo (recomendado para scripts)
railway run python manage.py shell << 'PYTHON'
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@railway.test').exists():
    User.objects.create_superuser(
        email='admin@railway.test',
        username='admin',
        password='RailwayAdmin123!',
        first_name='Admin',
        last_name='Railway'
    )
    print('✅ Superuser creado: admin@railway.test / RailwayAdmin123!')
else:
    print('⚠️  Superuser ya existe')
PYTHON
```

#### 4. Crear usuarios de prueba en Railway

```bash
railway run python manage.py shell << 'PYTHON'
from django.contrib.auth import get_user_model
from apps.orgs.models import Organization
from apps.plans.models import Plan, Subscription

User = get_user_model()

# Crear organización y plan
org, created = Organization.objects.get_or_create(
    name='Railway Test Org',
    defaults={'slug': 'railway-test-org'}
)

plan, created = Plan.objects.get_or_create(
    name='trial',
    defaults={
        'display_name': 'Trial Plan',
        'max_users': 10,
        'max_storage_gb': 100
    }
)

Subscription.objects.get_or_create(organization=org, plan=plan)

# Usuario regular activo
user1, created = User.objects.get_or_create(
    email='regular@railway.test',
    defaults={
        'first_name': 'Regular',
        'last_name': 'Railway',
        'organization': org,
        'is_active': True
    }
)
if created:
    user1.set_password('RailwayPass123!')
    user1.save()
    print(f'✅ Usuario creado: {user1.email}')

# Usuario con password change required
user2, created = User.objects.get_or_create(
    email='needschange@railway.test',
    defaults={
        'first_name': 'Needs',
        'last_name': 'Change',
        'organization': org,
        'is_active': True,
        'password_change_required': True
    }
)
if created:
    user2.set_password('TempRailway123!')
    user2.save()
    print(f'✅ Usuario creado: {user2.email} (requiere cambio)')

# Usuario inactivo
user3, created = User.objects.get_or_create(
    email='inactive@railway.test',
    defaults={
        'first_name': 'Inactive',
        'last_name': 'User',
        'organization': org,
        'is_active': False
    }
)
if created:
    user3.set_password('InactiveRailway123!')
    user3.save()
    print(f'✅ Usuario inactivo creado: {user3.email}')

print('\n📋 RESUMEN - Usuarios Railway:')
print('1. admin@railway.test / RailwayAdmin123! (superuser)')
print('2. regular@railway.test / RailwayPass123!')
print('3. needschange@railway.test / TempRailway123! (requiere cambio)')
print('4. inactive@railway.test / InactiveRailway123! (inactivo)')
PYTHON
```

#### 5. Verificar logs en tiempo real (RAILWAY)

```bash
# Railway CLI (recomendado):
railway logs --tail 100 --follow

# O desde Dashboard:
# Railway > Tu proyecto > Deployments > [última deployment] > View Logs
```

---

## 🌍 ENTORNOS DE PRUEBA

Esta guía cubre pruebas en **DOS entornos**:
1. **� Local (Docker)** - Desarrollo con datos de prueba
2. **🚂 Railway (Producción)** - Entorno real con HTTPS, email SMTP real y storage

### Tabla comparativa de entornos

| Aspecto | Local (Docker) | Railway (Producción) |
|---------|----------------|----------------------|
| **Base URL** | `http://localhost:8000` | `https://tu-app.railway.app` |
| **Base de datos** | PostgreSQL/SQLite local | PostgreSQL gestionado |
| **HTTPS** | No (HTTP simple) | Sí (certificado automático) |
| **Email** | Console/Mock backend | SMTP real (Gmail, SendGrid) |
| **Storage** | Filesystem local | R2/S3 real |
| **Logs** | `docker compose logs` | `railway logs` |
| **Crear usuarios** | `docker compose exec web ...` | `railway run ...` |
| **Signals** | Activos | Activos |
| **Middleware** | Todos activos | Todos activos |

---

## �📝 GRUPOS DE PRUEBAS MANUALES

**💡 NOTA:** Cada prueba incluye instrucciones para ambos entornos (Local y Railway).

---

## 🔐 GRUPO 1: LOGIN Y AUTENTICACIÓN

### Basado en: `tests/unit/test_accounts/test_login_views.py`

#### ✅ PRUEBA 1.1: Login exitoso - Usuario regular

**Objetivo:** Validar que un usuario regular puede loguearse y accede al dashboard.

**Test relacionado:** `test_login_successful_regular_user`

**🐳 LOCAL - Pasos:**
1. Abre tu navegador en `http://localhost:8000/accounts/login/`
2. Ingresa credenciales:
   - Email: `regular@arcmanager.test`
   - Password: `RegularPass123!`
   - ☐ Remember me (sin marcar)
3. Click en "Iniciar sesión"

**🚂 RAILWAY - Pasos:**
1. Abre tu navegador en `https://tu-app-production-xxxx.up.railway.app/accounts/login/`
2. Ingresa credenciales:
   - Email: `regular@railway.test`
   - Password: `RailwayPass123!`
   - ☐ Remember me (sin marcar)
3. Click en "Iniciar sesión"

**Resultado esperado (ambos entornos):**
- ✅ Redirección a dashboard (`/`)
- ✅ Usuario aparece logueado (nombre en navbar)
- ✅ No aparecen mensajes de error
- ✅ Sesión expira en 7 días (verificar en logs o sesión)

**Verificar en logs:**
```bash
# LOCAL:
docker compose logs -f web | grep "Usuario autenticado"

# RAILWAY:
railway logs --tail 50 | grep "Usuario autenticado"
```

**Verificar en navegador (DevTools > Application > Cookies):**
- Cookie `sessionid` presente
- Expira en ~7 días desde ahora
- **RAILWAY:** Cookie tiene flag `Secure: true` (HTTPS)

---

#### ✅ PRUEBA 1.2: Login con "Remember Me"

**Objetivo:** Validar que marcar "Remember me" extiende la sesión a 30 días.

**Test relacionado:** `test_login_with_remember_me`

**🐳 LOCAL - Credenciales:**
- Email: `regular@arcmanager.test`
- Password: `RegularPass123!`
- ☑ Remember me (marcar)

**🚂 RAILWAY - Credenciales:**
- Email: `regular@railway.test`
- Password: `RailwayPass123!`
- ☑ Remember me (marcar)

**Resultado esperado:**
- ✅ Login exitoso
- ✅ Cookie de sesión expira en ~30 días

**Verificar en navegador (DevTools > Cookies):**
- Cookie `sessionid` expira en ~30 días

---

#### ✅ PRUEBA 1.3: Login como superusuario → Redirige a /admin/

**Objetivo:** Validar que superusers son redirigidos automáticamente al admin.

**Test relacionado:** `test_login_superuser_redirects_to_admin`

**🐳 LOCAL - Credenciales:**
- Email: `admin@arcmanager.test`
- Password: `AdminPass123!`

**🚂 RAILWAY - Credenciales:**
- Email: `admin@railway.test`
- Password: `RailwayAdmin123!`

**Resultado esperado:**
- ✅ Redirección a `/admin/` (Django admin)
- ✅ Log WARNING generado (login de superuser es crítico)

**Verificar en logs:**
```bash
# LOCAL:
docker compose logs | grep "SUPERUSER login"

# RAILWAY:
railway logs | grep "SUPERUSER login"
```

---

#### ✅ PRUEBA 1.4: Usuario con cambio de contraseña requerido

**Objetivo:** Validar que usuarios con `password_change_required=True` son redirigidos al cambio forzado.

**Test relacionado:** `test_login_user_with_password_change_required`

**🐳 LOCAL - Credenciales:**
- Email: `needschange@arcmanager.test`
- Password: `TempPass123!`

**🚂 RAILWAY - Credenciales:**
- Email: `needschange@railway.test`
- Password: `TempRailway123!`

**Resultado esperado:**
- ✅ Login exitoso pero redirección a `/accounts/force-password-change/`
- ✅ Mensaje indicando que debe cambiar contraseña
- ✅ No puede acceder a otras páginas hasta cambiar contraseña

---

#### ❌ PRUEBA 1.5: Login fallido - Contraseña incorrecta

**Objetivo:** Validar rechazo de contraseña incorrecta.

**Test relacionado:** `test_login_with_wrong_password`

**🐳 LOCAL - Credenciales:**
- Email: `regular@arcmanager.test`
- Password: `PasswordIncorrecta!`

**🚂 RAILWAY - Credenciales:**
- Email: `regular@railway.test`
- Password: `PasswordIncorrecta!`

**Resultado esperado:**
- ❌ NO redirige (vuelve a mostrar form)
- ❌ Mensaje de error: "Credenciales incorrectas" o similar
- ❌ Usuario NO queda logueado
- ✅ Log WARNING generado con motivo "Contraseña incorrecta"

**Verificar en logs:**
```bash
# LOCAL:
docker compose logs | grep "Login fallido"

# RAILWAY:
railway logs | grep "Login fallido"
```

---

#### ❌ PRUEBA 1.6: Login fallido - Usuario inactivo

**Objetivo:** Validar que usuarios inactivos no pueden loguearse.

**Test relacionado:** `test_login_with_inactive_user`

**🐳 LOCAL - Credenciales:**
- Email: `inactive@arcmanager.test`
- Password: `InactivePass123!`

**🚂 RAILWAY - Credenciales:**
- Email: `inactive@railway.test`
- Password: `InactiveRailway123!`

**Resultado esperado:**
- ❌ NO redirige
- ❌ Mensaje de error: "Esta cuenta está inactiva"
- ❌ Usuario NO queda logueado

---

#### ❌ PRUEBA 1.7: Login fallido - Email no existe

**Objetivo:** Validar que emails inexistentes NO revelan información (seguridad).

**Test relacionado:** `test_login_with_nonexistent_email`

**Credenciales (ambos entornos):**
- Email: `noexiste@test.com`
- Password: `AnyPassword123!`

**Resultado esperado:**
- ❌ Mensaje genérico de error (NO revelar si email existe)
- ❌ Usuario NO queda logueado

**SEGURIDAD:** El mensaje debe ser igual al de contraseña incorrecta (prevenir user enumeration).

---

#### ❌ PRUEBA 1.8: Login con campos vacíos

**Objetivo:** Validar validación de campos requeridos.

**Test relacionado:** `test_login_with_empty_credentials`

**Pasos (ambos entornos):**
1. Ir a `/accounts/login/`
2. Dejar email y password vacíos
3. Click en "Iniciar sesión"

**Resultado esperado:**
- ❌ Errores de validación: "Este campo es requerido"
- ❌ NO se genera log (no es intento legítimo)

---

## 🚪 GRUPO 2: LOGOUT

### Basado en: `tests/unit/test_accounts/test_logout_views.py`

#### ✅ PRUEBA 2.1: Logout exitoso

**Objetivo:** Validar que logout limpia la sesión y redirige a login.

**Test relacionado:** `test_logout_via_get_successful`

**Pasos (ambos entornos):**
1. Login como usuario regular
2. Verificar que estás logueado (nombre en navbar)
3. Click en "Logout" o ir a `/accounts/logout/`

**Resultado esperado:**
- ✅ Redirección a `/accounts/login/`
- ✅ Usuario completamente deslogueado
- ✅ Cookie de sesión eliminada o invalidada
- ✅ Log INFO generado

**Verificar en logs:**
```bash
# LOCAL:
docker compose logs | grep "Usuario deslogueado"

# RAILWAY:
railway logs | grep "Usuario deslogueado"
```

---

#### ✅ PRUEBA 2.2: Logout sin estar autenticado

**Objetivo:** Validar que logout sin sesión NO crashea.

**Test relacionado:** `test_logout_without_authentication`

**Pasos:**
1. Asegúrate de estar completamente deslogueado
2. Ir manualmente a `/accounts/logout/`

**Resultado esperado:**
- ✅ Redirección a `/accounts/login/` sin errores
- ✅ NO genera log (no había usuario logueado)

---

## 🔑 GRUPO 3: PASSWORD RESET

### Basado en: `tests/unit/test_accounts/test_password_reset_views.py`

#### ✅ PRUEBA 3.1: Password reset exitoso

**Objetivo:** Validar flujo completo de recuperación de contraseña.

**Test relacionado:** `test_password_reset_successful`

**Pasos (ambos entornos):**
1. Logout completamente
2. Ir a `/accounts/login/`
3. Click en "¿Olvidaste tu contraseña?"
4. Ingresar email:
   - 🐳 **LOCAL:** `regular@arcmanager.test`
   - 🚂 **RAILWAY:** `regular@railway.test`
5. Click en "Enviar"

**Resultado esperado:**
- ✅ Redirección a página de confirmación: `/accounts/password_reset/done/`
- ✅ Mensaje: "Revisa tu correo electrónico"
- ✅ Email enviado
  - 🐳 **LOCAL:** Verificar en logs (console backend)
  - 🚂 **RAILWAY:** Verificar inbox real (Gmail, SendGrid, etc.)
- ✅ Log INFO generado

**Verificar en logs:**
```bash
# LOCAL:
docker compose logs | grep "Password reset solicitado"

# RAILWAY:
railway logs | grep "Password reset solicitado"
```

**Verificar email (RAILWAY):**
- Asunto: "Recuperación de contraseña"
- Link de reset válido y funcional
- De: Tu servicio SMTP configurado

---

#### ✅ PRUEBA 3.2: Password reset - Email no existe

**Objetivo:** Validar que emails inexistentes NO revelan información.

**Test relacionado:** `test_password_reset_with_nonexistent_email`

**Pasos:**
1. Solicitar reset para: `noexiste@test.com`

**Resultado esperado:**
- ✅ Mismo mensaje genérico: "Revisa tu correo"
- ✅ Misma redirección
- ✅ NO se envía email (verificar logs)

**SEGURIDAD:** No debe revelar que el email no existe.

---

#### 🚫 PRUEBA 3.3: Rate limiting - 15 minutos

**Objetivo:** Validar que no se pueden solicitar múltiples resets seguidos.

**Test relacionado:** `test_password_reset_rate_limiting`

**Pasos (ambos entornos):**
1. Solicitar reset para usuario regular
2. Esperar mensaje de confirmación
3. **INMEDIATAMENTE** volver atrás y solicitar reset nuevamente

**Resultado esperado:**
- ❌ Mensaje de error: "Ya solicitaste un reset recientemente. Espera 15 minutos."
- ❌ NO se envía segundo email
- ✅ Log WARNING generado

**Para continuar testing (limpiar cache):**
```bash
# LOCAL:
docker compose exec web python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# RAILWAY:
railway run python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

---

#### ❌ PRUEBA 3.4: Password reset - Usuario inactivo

**Objetivo:** Validar que usuarios inactivos NO reciben email.

**Test relacionado:** `test_password_reset_inactive_user_logs_warning`

**Pasos:**
1. Solicitar reset para:
   - 🐳 **LOCAL:** `inactive@arcmanager.test`
   - 🚂 **RAILWAY:** `inactive@railway.test`

**Resultado esperado:**
- ✅ Mismo mensaje genérico (no revelar que está inactivo)
- ❌ NO se envía email
- ✅ Log WARNING generado

---

## 📝 GRUPO 4: FORMS Y VALIDACIONES

### Basado en: `tests/unit/test_accounts/test_forms.py`

#### ✅ PRUEBA 4.1: Validación de campos vacíos en login

**Test relacionado:** `test_form_with_empty_email`, `test_form_with_empty_password`

**Pasos:**
1. Ir a `/accounts/login/`
2. Dejar email vacío, password con valor
3. Submit → Ver error en email
4. Llenar email, vaciar password
5. Submit → Ver error en password

**Resultado esperado:**
- ❌ Error: "Este campo es requerido" para cada caso

---

#### ✅ PRUEBA 4.2: Force password change - Contraseña actual incorrecta

**Test relacionado:** `test_form_rejects_wrong_old_password`

**Pasos:**
1. Login como `needschange@arcmanager.test` / `TempPass123!`
2. Serás redirigido a `/accounts/force-password-change/`
3. Llenar:
   - Contraseña actual: `PasswordIncorrecta!`
   - Nueva contraseña: `NewSecure123!`
   - Confirmar nueva: `NewSecure123!`
4. Submit

**Resultado esperado:**
- ❌ Error: "La contraseña actual es incorrecta"

---

#### ✅ PRUEBA 4.3: Force password change - Contraseñas no coinciden

**Test relacionado:** `test_form_rejects_non_matching_passwords`

**Pasos:**
1. Mismo setup anterior
2. Llenar:
   - Contraseña actual: `TempPass123!`
   - Nueva contraseña: `NewPass123!`
   - Confirmar nueva: `DifferentPass456!` ❌ Diferente
3. Submit

**Resultado esperado:**
- ❌ Error: "Las contraseñas no coinciden"

---

#### ✅ PRUEBA 4.4: Force password change - Contraseña muy corta

**Test relacionado:** `test_form_rejects_short_password`

**Pasos:**
1. Nueva contraseña: `Short1!` (solo 7 caracteres)
2. Submit

**Resultado esperado:**
- ❌ Error: "La contraseña debe tener al menos 8 caracteres"

---

#### ✅ PRUEBA 4.5: Force password change - Solo números

**Test relacionado:** `test_form_rejects_numeric_only_password`

**Pasos:**
1. Nueva contraseña: `12345678`
2. Submit

**Resultado esperado:**
- ❌ Error: "La contraseña no puede ser completamente numérica"

---

#### ✅ PRUEBA 4.6: Force password change - Exitoso

**Test relacionado:** `test_form_valid_with_correct_data`

**Pasos:**
1. Llenar correctamente:
   - Contraseña actual: `TempPass123!`
   - Nueva contraseña: `NewSecurePass456!`
   - Confirmar nueva: `NewSecurePass456!`
2. Submit

**Resultado esperado:**
- ✅ Contraseña cambiada exitosamente
- ✅ Redirección a dashboard
- ✅ Flag `password_change_required` se pone en False
- ✅ Log INFO generado

**Verificar:** Logout e intenta login con nueva contraseña.

---

## 👤 GRUPO 5: MODELO USER Y VALIDACIONES

### Basado en: `tests/unit/test_accounts/test_models.py` y `test_user_validation.py`

#### ✅ PRUEBA 5.1: Normalización de email a lowercase

**Test relacionado:** `test_email_normalization`

**Pasos:**
1. Ir a Django Admin (`/admin/`)
2. Login como `admin@arcmanager.test`
3. Crear nuevo usuario con:
   - Email: `TEST.USER@EXAMPLE.COM` (uppercase)
   - First name: `Test`
   - Last name: `User`
   - Password: `TestPass123!`
4. Guardar

**Resultado esperado:**
- ✅ Email se guarda como `test.user@example.com` (lowercase)

**Verificar en DB:**
```bash
docker compose exec web bash -lc "cd /app && python manage.py shell -c \"from django.contrib.auth import get_user_model; u=get_user_model().objects.get(email='test.user@example.com'); print(f'Email: {u.email}')\""
```

**Salida esperada:**
```
Email: test.user@example.com
```

---

#### ✅ PRUEBA 5.2: Email es único (no duplicados)

**Test relacionado:** `test_email_must_be_unique`

**Pasos:**
1. En Django Admin, crear usuario con email: `unique@arcmanager.test`
2. Guardar
3. Intentar crear OTRO usuario con mismo email

**Resultado esperado:**
- ❌ Error de integridad: "Ya existe un usuario con este email"

---

#### ✅ PRUEBA 5.3: Username se genera automáticamente

**Test relacionado:** `test_username_auto_generation`

**Pasos:**
1. Crear usuario con email `johndoe@example.com`
2. NO llenar campo username (si es visible)

**Resultado esperado:**
- ✅ Username se genera automáticamente basado en email
- ✅ Formato aproximado: `johndoe_<random>` o similar

---

#### ✅ PRUEBA 5.4: Contraseñas están hasheadas

**Test relacionado:** `test_password_is_hashed`

**Pasos:**
1. Crear usuario con password: `MyPlainPassword123!`
2. Guardar
3. Ver en Django Admin el campo password

**Resultado esperado:**
- ✅ Password NO se muestra en texto plano
- ✅ Formato hash: `pbkdf2_sha256$...`

**Verificar en DB:**
```bash
docker compose exec web bash -lc "cd /app && python manage.py shell -c \"from django.contrib.auth import get_user_model; u=get_user_model().objects.first(); print(f'Password hash starts with: {u.password[:20]}')\""
```

**Salida esperada:**
```
Password hash starts with: pbkdf2_sha256$600000$
```

---

## 📊 GRUPO 6: LOGGING Y MONITOREO

### Basado en: `test_login_views.py` (logging tests)

#### ✅ PRUEBA 6.1: Login exitoso genera log INFO estructurado

**Test relacionado:** `test_successful_login_logs_info`

**Pasos:**
1. En terminal separada: `docker compose logs -f web`
2. Hacer login como `regular@arcmanager.test`

**Verificar en logs:**
```json
{
  "level": "INFO",
  "event": "user_login_success",
  "email": "regular@arcmanager.test",
  "user_id": 123,
  "ip": "172.18.0.1",
  "session_duration": "7_days",
  "timestamp": "2025-11-04T..."
}
```

**Validar que contiene:**
- ✅ Email del usuario
- ✅ IP de origen
- ✅ Duración de sesión
- ✅ Timestamp

---

#### ✅ PRUEBA 6.2: Login fallido genera log WARNING

**Test relacionado:** `test_failed_login_logs_warning`

**Pasos:**
1. Monitorear logs
2. Intentar login con credenciales incorrectas

**Verificar en logs:**
```json
{
  "level": "WARNING",
  "event": "user_login_failed",
  "email": "regular@arcmanager.test",
  "reason": "invalid_password",
  "ip": "172.18.0.1",
  "timestamp": "2025-11-04T..."
}
```

**Validar:**
- ✅ Motivo del fallo (invalid_password / user_not_found / inactive)
- ✅ Email que intentó acceder
- ✅ IP

---

#### ✅ PRUEBA 6.3: Superuser login genera WARNING crítico

**Test relacionado:** `test_superuser_login_logs_warning`

**Pasos:**
1. Monitorear logs
2. Login como `admin@arcmanager.test`

**Verificar en logs:**
```json
{
  "level": "WARNING",
  "event": "superuser_login",
  "email": "admin@arcmanager.test",
  "ip": "...",
  "critical": true
}
```

**Validar:**
- ✅ Log de nivel WARNING (no INFO)
- ✅ Indica que es login de superuser

---

#### ✅ PRUEBA 6.4: Logs NO contienen contraseñas

**Test relacionado:** Implícito en todos los logging tests

**Pasos:**
1. Monitorear logs durante login
2. Buscar en logs la palabra "password" o valores de contraseñas

**Resultado esperado:**
- ✅ NINGÚN log contiene contraseñas en texto plano
- ✅ Solo se loguean hashes (si acaso)

**SEGURIDAD CRÍTICA:** Si encuentras contraseñas en logs, es un bug de seguridad.

---

## 🎨 GRUPO 7: UX Y MENSAJES

#### ✅ PRUEBA 7.1: Mensajes flash de confirmación

**Pasos:**
1. Hacer login exitoso
2. Verificar mensaje verde: "Bienvenido, {nombre}"
3. Cambiar contraseña exitosamente
4. Verificar mensaje: "Contraseña cambiada exitosamente"
5. Logout
6. Verificar mensaje: "Sesión cerrada correctamente"

---

#### ✅ PRUEBA 7.2: Mensajes de error claros y apropiados

**Objetivo:** Validar que los mensajes de error son apropiados según el contexto.

**Pasos:**

1. **Frontend - Login con contraseña incorrecta:**
   - Intentar login con contraseña incorrecta
   - ✅ Mensaje genérico: "Credenciales incorrectas" (no revela si email existe)
   - ❌ NO debe decir: "La contraseña es incorrecta" (revelaría que email existe)

2. **Frontend - Login con usuario inactivo:**
   - Intentar login con usuario inactivo
   - ✅ Mensaje específico: "Tu cuenta está inactiva"
   - ✅ Sugiere contactar administrador

3. **Frontend - Error 500 (inesperado):**
   - Forzar error interno (ej: modificar código temporalmente)
   - ✅ Mensaje genérico: "Algo salió mal de nuestro lado..."
   - ❌ NO debe mostrar traceback o detalles técnicos
   - ✅ Backend loggea error completo con traceback

4. **Django Admin - ValidationError:**
   - Ir a `/admin/` y login como superuser
   - Crear usuario activo SIN organización
   - ✅ Mensaje específico: "Los usuarios activos deben tener una organización asignada"
   - ✅ Mensaje aparece en el campo correcto (organization)
   - ❌ NO debe mostrar mensaje genérico

5. **Django Admin - IntegrityError:**
   - Crear usuario con email existente
   - ✅ Mensaje específico: "Este correo electrónico ya está registrado"
   - ✅ Mensaje aparece en el campo email

**Resultado esperado:**
- ❌ NO mensajes técnicos en frontend: "IntegrityError", "ValidationError", "Exception"
- ✅ Mensajes amigables en frontend: "Credenciales incorrectas", "Tu cuenta está inactiva"
- ✅ Mensajes específicos en Django Admin (para staff)
- ✅ Logs completos en backend para debugging

**Verificar en logs (errores inesperados):**
```bash
# LOCAL:
docker compose logs | grep ERROR

# RAILWAY:
railway logs | grep ERROR

# Debe contener:
# - Traceback completo
# - Tipo de excepción
# - Contexto (user_email, IP, etc.)
```

---

#### ✅ PRUEBA 7.3: Validaciones de formularios con mensajes específicos

**Pasos:**

1. **Password Change - Contraseña muy corta:**
   - Nueva contraseña: `Short1!` (7 caracteres)
   - ✅ Error específico: "La contraseña debe tener al menos 8 caracteres"

2. **Password Change - Contraseña solo números:**
   - Nueva contraseña: `12345678`
   - ✅ Error específico: "La contraseña no puede ser completamente numérica"

3. **Password Change - Contraseñas no coinciden:**
   - Nueva: `Pass123!`, Confirmar: `Different456!`
   - ✅ Error específico: "Las nuevas contraseñas no coinciden"

4. **Login - Email vacío:**
   - Dejar email vacío
   - ✅ Error específico: "Este campo es requerido"

**Resultado esperado:**
- ✅ Cada validación tiene mensaje claro y específico
- ✅ Errores aparecen en el campo correspondiente
- ✅ Mensajes en español
- ✅ Sin tecnicismos innecesarios

---

#### ✅ PRUEBA 7.4: Seguridad - User Enumeration

**Objetivo:** Verificar que el sistema NO revela si un email existe.

**Pasos:**

1. **Login - Email que NO existe:**
   - Email: `noexiste@test.com`, Password: `AnyPass123!`
   - ✅ Mensaje: "Credenciales incorrectas" (genérico)
   
2. **Login - Email que SÍ existe pero password incorrecta:**
   - Email: `regular@arcmanager.test`, Password: `WrongPass123!`
   - ✅ Mensaje: "Credenciales incorrectas" (igual que anterior)

3. **Password Reset - Email que NO existe:**
   - Email: `noexiste@test.com`
   - ✅ Mensaje: "Revisa tu correo electrónico" (genérico)
   - ✅ NO se envía email (verificar logs)

4. **Password Reset - Email que SÍ existe:**
   - Email: `regular@arcmanager.test`
   - ✅ Mensaje: "Revisa tu correo electrónico" (igual que anterior)
   - ✅ SÍ se envía email (verificar logs o inbox)

**Resultado esperado:**
- ✅ Mensajes idénticos para emails existentes y no existentes
- ✅ Atacante NO puede determinar si un email está registrado
- ✅ Backend loggea el detalle real (email existe / no existe)

**CRÍTICO:** Si los mensajes son diferentes, es una vulnerabilidad de seguridad.

---

## 📈 RESUMEN DE COBERTURA DE PRUEBAS MANUALES

### Tests implementados vs Pruebas manuales

| Grupo | Tests Automatizados | Pruebas Manuales | Cobertura |
|-------|---------------------|------------------|-----------|
| Login | 15 tests | 8 pruebas | 100% |
| Logout | 5 tests | 2 pruebas | 100% |
| Password Reset | 7 tests | 4 pruebas | 100% |
| Forms | 13 tests | 6 pruebas | 100% |
| Modelo User | 25+ tests | 4 pruebas | 80% |
| Logging | 4 tests | 4 pruebas | 100% |
| **TOTAL** | **69+ tests** | **28 pruebas** | **~95%** |

---

## 🚀 COMANDOS ÚTILES PARA TESTING

### Comandos por entorno

#### 🐳 LOCAL (Docker)

```bash
# Limpiar cache
docker compose exec web python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Ver logs en tiempo real
docker compose logs -f web

# Ejecutar todos los tests automatizados
docker compose exec web python -m pytest tests/unit/test_accounts/ -v

# Ejecutar un test específico
docker compose exec web python -m pytest tests/unit/test_accounts/test_login_views.py::TestLoginViewHappyPath::test_login_successful_regular_user -v -s

# Ver cobertura de tests
docker compose exec web python -m pytest tests/unit/test_accounts/ --cov=apps.accounts --cov-report=html --cov-report=term-missing

# Resetear DB de desarrollo
docker compose exec web python manage.py flush --no-input
docker compose exec web python manage.py migrate
```

#### 🚂 RAILWAY (Producción)

```bash
# Ver status del proyecto
railway status

# Limpiar cache
railway run python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Ver logs en tiempo real
railway logs --tail 100 --follow

# Ver logs recientes
railway logs --tail 50

# Filtrar logs por nivel
railway logs | grep ERROR
railway logs | grep WARNING
railway logs | grep INFO

# Ejecutar comando en Railway
railway run python manage.py <comando>

# Shell interactivo
railway shell

# Abrir app en navegador
railway open

# Ver variables de entorno
railway variables

# Setear variable
railway variables set KEY="value"

# Ejecutar migraciones
railway run python manage.py migrate

# Collectstatic
railway run python manage.py collectstatic --noinput
```

---

## 🔒 VERIFICACIONES ADICIONALES PARA RAILWAY

### Checklist de seguridad en producción

#### 1. HTTPS habilitado
```
✅ URL empieza con https://
✅ Candado verde en navegador
✅ Certificado válido (click en candado)
```

#### 2. Headers de seguridad
```bash
# Abrir DevTools > Network > Seleccionar cualquier request
# Verificar Response Headers:

✅ Strict-Transport-Security: max-age=31536000
✅ X-Content-Type-Options: nosniff
✅ X-Frame-Options: DENY
✅ Referrer-Policy: same-origin
```

#### 3. Cookies seguras
```bash
# DevTools > Application > Cookies
# Verificar cookie sessionid:

✅ Secure: true
✅ HttpOnly: true
✅ SameSite: Lax o Strict
```

#### 4. Debug deshabilitado
```bash
# Ir a URL inexistente en Railway:
# https://tu-app.railway.app/ruta-que-no-existe

❌ NO debe mostrar traceback de Django
✅ Debe mostrar página 404 genérica o personalizada
```

#### 5. Logs estructurados
```bash
# Railway logs debe mostrar JSON o formato estructurado:
railway logs --tail 10

# Ejemplo esperado:
{
  "timestamp": "2025-11-04T12:34:56Z",
  "level": "INFO",
  "event": "user_login_success",
  "email": "user@test.com",
  "user_id": 123,
  "ip": "203.0.113.45"
}
```

#### 6. Email real funciona
```bash
# Solicitar password reset en Railway
# Verificar que llega email real a inbox
✅ Email recibido
✅ Link de reset funcional
✅ Remitente correcto
```

---

## 🔍 CHECKLIST FINAL - Antes de pasar a producción

### Funcionalidad
- [ ] Login con usuario regular funciona
- [ ] Login con superuser redirige a /admin/
- [ ] Remember me extiende sesión a 30 días
- [ ] Logout limpia sesión completamente
- [ ] Password reset envía email correctamente
- [ ] Rate limiting bloquea múltiples intentos
- [ ] Force password change funciona
- [ ] Validaciones de form muestran errores claros

### Seguridad
- [ ] Contraseñas están hasheadas (pbkdf2_sha256)
- [ ] Emails inexistentes NO revelan información
- [ ] Usuarios inactivos NO pueden loguearse
- [ ] Rate limiting previene spam
- [ ] Logs NO contienen contraseñas en texto plano
- [ ] IP tracking funciona correctamente

### Logging y Monitoreo
- [ ] Login exitoso loggea INFO con contexto completo
- [ ] Login fallido loggea WARNING con motivo
- [ ] Superuser login genera WARNING crítico
- [ ] Logs contienen: email, IP, timestamp, contexto
- [ ] Formato de logs es estructurado (JSON o key=value)

### UX
- [ ] Mensajes de error son claros y no técnicos
- [ ] Mensajes de confirmación se muestran correctamente
- [ ] Redirecciones funcionan (login → dashboard, superuser → admin)
- [ ] Forms muestran errores en campos específicos

### Performance
- [ ] Login responde en < 2 segundos
- [ ] Cache funciona correctamente (rate limiting)
- [ ] DB no tiene queries N+1 (verificar con Django Debug Toolbar)

---

## 📞 SOPORTE Y DUDAS

Si encuentras algún comportamiento inesperado durante las pruebas manuales:

1. Verificar logs: `docker compose logs -f web`
2. Ejecutar test automatizado equivalente
3. Verificar estado de DB: Django Admin
4. Limpiar cache y volver a probar
5. Documentar bug en detalle (steps to reproduce)

---

## 📚 REFERENCIAS

- Tests automatizados: `tests/unit/test_accounts/`
- Configuración pytest: `pytest.ini`
- Fixtures de tests: `tests/conftest.py`
- Plan completo de testing: `tests/PLAN_TESTING_COMPLETO.md`
- Análisis crítico: `tests/ANALISIS_CRITICO_Y_PLAN_ACCION.md`

---

**Última actualización:** 4 de Noviembre 2025  
**Autor:** ARC Manager Team  
**Versión:** 1.0
