## 📋 Módulo Accounts — Descripción General

### Objetivo
Proveer autenticación por email, gestión del usuario personalizado (`AUTH_USER_MODEL = 'accounts.User'`), flujos de login/logout, recuperación de contraseña con rate-limit y políticas de acceso vía middleware.

---

## 📁 Estructura de Archivos

```
arc_manager/apps/accounts/
├── admin.py                  # Admin con import/export y acciones masivas
├── apps.py                   # Registro de señales en ready()
├── forms.py                  # Form de login con mensajes en español
├── middleware.py             # LoginRequired, SuperuserRestrict, ErrorHandling
├── migrations/               # Migraciones del modelo User
├── models.py                 # Custom User basado en AbstractUser
├── signals.py                # Validaciones y logging
├── urls.py                   # Rutas de login/logout/password reset
└── views.py                  # Vistas personalizadas de auth
```

---

## 🗃️ Modelo de Datos

- `User(AbstractUser)`
  - `email` único como credencial principal (`USERNAME_FIELD='email'`).
  - `username` autogenerado y no editable (compatibilidad interna).
  - `first_name` y `last_name` obligatorios.
  - `organization` (FK opcional) y `is_org_admin` para permisos por organización.
  - Restricción: usuarios activos deben tener `organization` salvo superusers.

---

## 🔐 Middleware y Seguridad

- Acceso protegido por `LoginRequiredMiddleware` con `LOGIN_EXEMPT_URLS` configurables.
- Superusuarios redirigidos al panel `/admin/` por `SuperuserRestrictMiddleware`.
- Reset de contraseña con limitación por email durante 15 min (cache Redis recomendado).

---

## 🎮 Vistas Principales

- `CustomLoginView` → login por email y limpieza de flags de sesión.
- `CustomLogoutView` → limpia mensajes/sesión y registra auditoría.
- `SecurePasswordResetView` → rate-limit + flujo estándar de Django.

---

## 🧭 Casos de Uso

- Autenticación por email con redirección condicional para superusuarios.
- Equipos por organización con admins (`is_org_admin`) que gestionan miembros desde otros módulos.
- Soporte/QA validan problemas comunes: bucles de redirect, límites de reset, mensajes localizados.

---

## 🧩 Integraciones Relacionadas

- `apps.orgs` para `organization` y límites por plan (validado en señales).
- `apps.plans` para restricciones de uso mostradas en UI (mensajes de sesión limpiados en login/logout).

---

## 🛠️ Configuración Clave

- `AUTH_USER_MODEL = 'accounts.User'`
- `LOGIN_URL = '/accounts/login/'`
- `LOGIN_EXEMPT_URLS` en `settings.py` para rutas públicas.
- Cache por Redis para rate-limit de reset.

---

Arc Manager · Módulo Accounts · Última actualización: 2025-08-13


