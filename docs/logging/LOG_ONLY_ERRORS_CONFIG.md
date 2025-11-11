# 🔧 Configuración de LOG_ONLY_ERRORS

## ⚠️ Problema Actual

Tienes `LOG_ONLY_ERRORS=true` en `docker-compose.yml`, lo que bloquea **todos los logs INFO** (incluyendo LOGOUT).

Solo verás:
- ✅ WARNING (login superuser, desactivar organizaciones)
- ✅ ERROR (errores)
- ❌ INFO (logout, activar organizaciones) - **BLOQUEADOS**

---

## 🛠️ Solución: Cambiar a `false` para Desarrollo

### Opción 1: Editar docker-compose.yml (Recomendado para Dev)

```yaml
# docker-compose.yml
services:
  web:
    environment:
      - LOG_ONLY_ERRORS=false  # Cambiar a false
```

**Luego reiniciar:**
```bash
docker-compose restart web
```

### Opción 2: Variable de Entorno Temporal

```bash
# Windows PowerShell
$env:LOG_ONLY_ERRORS="false"
docker-compose up -d
```

---

## 📊 Comportamiento según Configuración

### `LOG_ONLY_ERRORS=false` (Recomendado para DEV)
```json
// Verás TODOS los logs
{"levelname": "WARNING", "message": "SUPERUSER LOGIN | ..."}
{"levelname": "INFO", "message": "LOGOUT | ..."}  ✅
{"levelname": "INFO", "message": "ORGANIZATIONS_ACTIVATED | ..."}  ✅
{"levelname": "WARNING", "message": "ORGANIZATIONS_DEACTIVATED | ..."}
{"levelname": "ERROR", "message": "ERROR PASSWORD CHANGE | ..."}
```

### `LOG_ONLY_ERRORS=true` (Recomendado para PROD)
```json
// Solo WARNING y ERROR
{"levelname": "WARNING", "message": "SUPERUSER LOGIN | ..."}
{"levelname": "WARNING", "message": "ORGANIZATIONS_DEACTIVATED | ..."}
{"levelname": "ERROR", "message": "ERROR PASSWORD CHANGE | ..."}
// ❌ NO verás LOGOUT ni ORGANIZATIONS_ACTIVATED
```

---

## ✅ Optimizaciones Aplicadas

### 1. **Logs únicos** (eliminé duplicados)

**ANTES:**
```json
// Log 1: START
{"message": "ORGANIZATIONS_DEACTIVATE_START | Desactivando 1 organizaciones..."}

// Log 2: Completado (DUPLICADO)
{"message": "ORGANIZATIONS_DEACTIVATED | 1 organizaciones desactivadas..."}
```

**AHORA:**
```json
// UN SOLO LOG con toda la info
{
  "levelname": "WARNING",
  "message": "ORGANIZATIONS_DEACTIVATED | 1 organizaciones desactivadas | Usuarios bloqueados: 1 | Orgs: Alonso Corp | Admin: admin@example.com",
  "user_id": 1,
  "organization_ids": [7],  // ✅ Array de IDs
  "organization_count": 1,
  "total_users_affected": 1
}
```

### 2. **organization_ids como array** (antes era organization_id: null)

**ANTES:**
```json
{
  "user_id": 1,
  "organization_id": null,  // ❌ No tiene sentido
  "organization_ids": [7]
}
```

**AHORA:**
```json
{
  "user_id": 1,  // ID del admin que ejecutó la acción
  "organization_ids": [7, 8, 9],  // ✅ IDs de las organizaciones afectadas
  "organization_count": 3
}
```

### 3. **user_id correcto en todos los logs**

Ahora el filtro **NO sobrescribe** los valores de `extra={}`:

```json
// Login de superuser
{
  "levelname": "WARNING",
  "message": "SUPERUSER LOGIN | Email: admin@example.com | ID: 1 | ...",
  "user_id": 1,  // ✅ Correcto
  "organization_id": null
}

// Logout
{
  "levelname": "INFO",
  "message": "LOGOUT | Email: user@example.com | ID: 3 | Org: Alonso Corp (ID: 7, ACTIVA)",
  "user_id": 3,  // ✅ Correcto
  "organization_id": 7  // ✅ Correcto
}
```

---

## 🧪 Cómo Probar

1. **Cambiar LOG_ONLY_ERRORS a false:**
   ```bash
   # Editar docker-compose.yml línea 203 y 258
   LOG_ONLY_ERRORS=false
   
   # Reiniciar
   docker-compose restart web
   ```

2. **Probar todas las acciones:**
   ```bash
   # Ver logs en tiempo real
   docker-compose logs -f web
   ```

3. **Hacer:**
   - Login como superuser → `WARNING`
   - Logout → `INFO` ✅ (antes no aparecía)
   - Activar organizaciones → `INFO` ✅ (1 solo log)
   - Desactivar organizaciones → `WARNING` ✅ (1 solo log)

---

## 🎯 Recomendaciones Finales

### Desarrollo (ahora):
```yaml
LOG_ONLY_ERRORS=false  # Ver todos los logs
```

### Producción (futuro):
```yaml
LOG_ONLY_ERRORS=true  # Solo WARNING y ERROR
```

### Por qué:
- **DEV:** Necesitas ver TODO para debugging
- **PROD:** Reducir ruido (los INFO son eventos normales, no críticos)

---

## 📝 Resumen de Cambios

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Logs por acción | 2 (START + END) | 1 (optimizado) |
| organization_id | `null` (confuso) | Array `organization_ids` |
| user_id en logs | `null` | Correcto |
| LOGOUT visible | ❌ (bloqueado) | ✅ (si LOG_ONLY_ERRORS=false) |
| Redundancia | Alta | Mínima |

---

**¡Cambia `LOG_ONLY_ERRORS=false` y reinicia para ver todos los logs!** 🚀
