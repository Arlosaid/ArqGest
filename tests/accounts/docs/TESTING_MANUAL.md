# 🧪 Guía de Testing Manual - ARC Manager

**Última actualización**: 7 de Noviembre, 2025  
**Módulos probados manualmente**: Accounts (Login/Auth)  
**Estado**: Documentación consolidada de pruebas manuales realizadas

---

## 📋 Índice

1. [Resumen](#resumen)
2. [Módulo Accounts - Sistema de Autenticación](#módulo-accounts---sistema-de-autenticación)
3. [Cobertura de Tests Unitarios vs Manual](#cobertura-de-tests-unitarios-vs-manual)
4. [Checklist de Pruebas Realizadas](#checklist-de-pruebas-realizadas)

---

## 📊 Resumen

Este documento consolida las pruebas manuales realizadas en el módulo de Accounts (Login/Autenticación).
Para detalles exhaustivos de todos los casos de prueba, ver el archivo original `MANUAL_TESTING_LOGIN.md` (2581 líneas).

**Casos de prueba totales**: 62 casos
**Casos cubiertos por tests unitarios**: 31 (50%)
**Casos solo validables manualmente**: 31 (UI/UX y Performance)

---

## 🔐 Módulo Accounts - Sistema de Autenticación

### ✅ Happy Path (5 casos - 100% cubiertos)

| ID | Caso | Test Unitario | Manual | Estado |
|----|------|---------------|--------|--------|
| HP-01 | Login exitoso usuario normal | ✅ `test_login_successful_regular_user` | ✅ | Pasando |
| HP-02 | Login con "Recordarme" | ✅ `test_login_with_remember_me` | ✅ | Pasando |
| HP-03 | Login exitoso superusuario | ✅ `test_login_superuser_redirects_to_admin` | ✅ | Pasando |
| HP-04 | Login exitoso Org Admin | ✅ Incluido en HP-01 | ✅ | Pasando |
| HP-05 | Logout exitoso | ✅ `test_logout_via_get_successful` | ✅ | Pasando |

---

### 🔍 Validación de Datos (10 casos - 60% cubiertos)

| ID | Caso | Test Unitario | Estado |
|----|------|---------------|--------|
| VD-01 | Email vacío | ✅ `test_form_with_empty_email` | Cubierto |
| VD-02 | Contraseña vacía | ✅ `test_form_with_empty_password` | Cubierto |
| VD-03 | Email formato inválido | ✅ Validación HTML5 | N/A |
| VD-04 | Email no registrado | ✅ `test_login_with_nonexistent_email` | Cubierto |
| VD-05 | Contraseña incorrecta | ✅ `test_login_with_wrong_password` | Cubierto |
| VD-06 | Case sensitivity - Email | ❌ FALTANTE | **TODO P1** |
| VD-07 | Case sensitivity - Contraseña | ❌ FALTANTE | **TODO P1** |
| VD-08 | Espacios en credenciales | ❌ FALTANTE | **TODO P1** |
| VD-09 | Caracteres especiales | ❌ FALTANTE | **TODO P2** |
| VD-10 | SQL Injection | ⚠️ Parcial | **TODO P0** |

---

### 🛡️ Seguridad (10 casos - 50% cubiertos)

| ID | Caso | Test Unitario | Estado |
|----|------|---------------|--------|
| SEG-01 | Protección fuerza bruta | ❌ FALTANTE (Django Axes) | **TODO P0** |
| SEG-02 | Bloqueo por IP | ❌ Incluido en SEG-01 | **TODO P0** |
| SEG-03 | XSS en campos | ⚠️ Django auto-escape | **TODO P1** |
| SEG-04 | CSRF Protection | ❌ FALTANTE | **TODO P0** |
| SEG-05 | Clickjacking | ❌ FALTANTE | **TODO P1** |
| SEG-06 | Password no en logs | ✅ `test_passwords_never_in_logs` | Cubierto |
| SEG-07 | Session Fixation | ✅ Django automático | N/A |
| SEG-08 | Brute force reset | ❌ FALTANTE | **TODO P1** |
| SEG-09 | Token reset seguro | ✅ Django automático | N/A |
| SEG-10 | Info en errores | ✅ Tests login | Cubierto |

---

### 🔐 Control de Acceso (6 casos - 83% cubiertos)

| ID | Caso | Test Unitario | Estado |
|----|------|---------------|--------|
| ACC-01 | Cuenta inactiva | ✅ `test_login_with_inactive_user` | Cubierto |
| ACC-02 | Usuario sin org | ✅ Signal previene | Cubierto |
| ACC-03 | Redirección ?next= | ❌ FALTANTE | **TODO P1** |
| ACC-04 | Login estando auth | ✅ Django automático | N/A |
| ACC-05 | Superuser restringido | ✅ `test_superuser_restricted_to_admin` | Cubierto |
| ACC-06 | Cambio forzado password | ✅ `test_login_user_with_password_change_required` | Cubierto |

---

### ⏱️ Sesión (7 casos - 71% cubiertos)

| ID | Caso | Test Unitario | Estado |
|----|------|---------------|--------|
| SES-01 | Duración 7 días | ✅ `test_login_successful_regular_user` | Cubierto |
| SES-02 | Duración 30 días | ✅ `test_login_with_remember_me` | Cubierto |
| SES-03 | Persistente al cerrar | ✅ Config automática | N/A |
| SES-04 | Sesión expirada | ✅ Django automático | N/A |
| SES-05 | Múltiples sesiones | ✅ Django permite | N/A |
| SES-06 | Limpieza de flags | ✅ `test_login_clears_previous_session_flags` | Cubierto |
| SES-07 | Session Hijacking | ❌ FALTANTE | **TODO P0** |

---

### 🔄 Password Reset (7 casos - 71% cubiertos)

| ID | Caso | Test Unitario | Estado |
|----|------|---------------|--------|
| PWD-01 | Reset exitoso | ✅ `test_password_reset_successful` | Cubierto |
| PWD-02 | Email no existe | ✅ `test_password_reset_with_nonexistent_email` | Cubierto |
| PWD-03 | Validación nueva password | ❌ FALTANTE | **TODO P1** |
| PWD-04 | Passwords no coinciden | ✅ `test_form_rejects_non_matching_passwords` | Cubierto |
| PWD-05 | Password actual incorrecta | ✅ `test_form_rejects_wrong_old_password` | Cubierto |
| PWD-06 | Nueva = actual | ✅ `test_form_rejects_same_as_current` | Cubierto |
| PWD-07 | Bypass attempt | ✅ Middleware previene | Cubierto |

---

## 📊 Cobertura Global

| Categoría | Total | Cubiertos | Faltantes | % |
|-----------|-------|-----------|-----------|---|
| Happy Path | 5 | 5 | 0 | ✅ 100% |
| Validación de Datos | 10 | 6 | 4 | ⚠️ 60% |
| Seguridad | 10 | 5 | 5 | ⚠️ 50% |
| Control de Acceso | 6 | 5 | 1 | ✅ 83% |
| Sesión | 7 | 5 | 2 | ✅ 71% |
| Password Reset | 7 | 5 | 2 | ✅ 71% |
| UI/UX | 10 | 0 | 10 | ❌ 0% |
| Rendimiento | 7 | 0 | 7 | ❌ 0% |
| **TOTAL** | **62** | **31** | **31** | **50%** |

---

## 🎯 Tests Críticos Faltantes (Prioridad)

### 🔴 P0 - CRÍTICO (Implementar AHORA)

1. **SEG-01: Protección contra Fuerza Bruta**
   - Bloqueo después de 10 intentos fallidos
   - Log de seguridad crítico
   - Ver detalles en MANUAL_TESTING_LOGIN.md línea 403

2. **SEG-04: CSRF Protection Completo**
   - Token en formulario
   - Validación de token
   - Ver detalles en línea 656

3. **SES-07: Session Hijacking Prevention**
   - Validación de User-Agent
   - Invalidación de sesión sospechosa
   - Ver detalles en línea 1643

4. **VD-10: SQL Injection (mejorar)**
   - Pruebas con más payloads
   - Verificación de integridad de BD
   - Ver detalles en línea 567

---

### 🟠 P1 - ALTO (Próximo Sprint)

5. **VD-06, VD-07, VD-08**: Case sensitivity y espacios
6. **SEG-05**: Clickjacking Protection (X-Frame-Options)
7. **SEG-08**: Brute force en password reset
8. **ACC-03**: Redirección con ?next=
9. **PWD-03**: Validación de nueva contraseña

---

## ✅ Checklist de Pruebas Realizadas

### Flujos Principales
- [x] Login exitoso (usuario, admin, superuser)
- [x] Logout completo
- [x] Password reset completo
- [x] Cambio forzado de contraseña
- [x] Middleware de redirección

### Seguridad Básica
- [x] Passwords no en logs
- [x] Email case-insensitive
- [x] Cuenta inactiva bloqueada
- [x] Mensaje genérico para errores (no enumeración)

### Sesión
- [x] Duración 7 días sin "recordarme"
- [x] Duración 30 días con "recordarme"
- [x] Limpieza de flags de sesión

### Pendientes Críticos
- [ ] Django Axes (bloqueo por fuerza bruta)
- [ ] CSRF completo
- [ ] Session hijacking
- [ ] SQL injection (mejoras)
- [ ] Clickjacking

---

## 📚 Referencias

- **Documento original completo**: `MANUAL_TESTING_LOGIN.md` (2581 líneas)
- **Cobertura detallada**: `COBERTURA_TESTS_LOGIN.md`
- **Tests implementados**: `tests/accounts/unit/test_login_views.py`

---

**Nota**: Este documento es un resumen ejecutivo. Para procedimientos detallados paso a paso 
de cada prueba manual, consultar el documento original `MANUAL_TESTING_LOGIN.md`.
