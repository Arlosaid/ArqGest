# 📝 Changelog — Módulo Accounts

Formato basado en Keep a Changelog. Versionado Semántico.

## [1.0.0] - 2025-08-13

### ✨ Agregado
- Documentación completa (`INDEX`, `README`, `API_ENDPOINTS`, `IMPLEMENTACION_TECNICA`).
- Rate-limit en reset de contraseña (cache 15 min por email).
- Middleware `LoginRequired` con precarga de `organization`.
- Middleware `SuperuserRestrict` para dirigir superusuarios a `/admin/`.
- Señales de validación de organización y roles.
- Admin con import/export y acciones masivas.

### 🔄 Cambiado
- Mensajes de autenticación localizados en español.

### 🐛 Corregido
- Limpieza de flags de sesión en login/logout para evitar mensajes cruzados.

---

Arc Manager · Accounts


