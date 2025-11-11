# 🔒 Sistema de Protección contra Fuerza Bruta - Django Axes

**Última actualización:** 07/11/2025  
**Responsable:** Sistema de Seguridad

---

## 📋 Resumen Ejecutivo

Este documento describe la implementación del sistema de protección contra ataques de fuerza bruta usando **Django Axes** con logging de seguridad estructurado.

---

## 🎯 Configuración Actual

### Settings Principal (`core/settings.py`)

```python
# Configuración básica
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 10                    # 10 intentos antes de bloqueo
AXES_COOLOFF_TIME = 0.25                   # 15 minutos de bloqueo
AXES_RESET_ON_SUCCESS = True               # Reset contador al login exitoso

# Handler personalizado con logging
AXES_HANDLER = 'core.axes_handler.CustomAxesHandler'

# Bloqueo por email O IP
AXES_LOCKOUT_BY_USER_OR_IP = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address', 'user_agent']

# URLs
AXES_LOCKOUT_URL = '/accounts/login/?locked=1'
```

**Justificación de valores:**
- **10 intentos**: Balance entre seguridad (frenar bots) y UX (permitir typos)
- **15 minutos**: Tiempo suficiente para frenar ataques automatizados sin inconveniente grave para usuarios reales
- **Reset on success**: Usuarios legítimos que finalmente aciertan no quedan penalizados

---

## 🔧 Componentes del Sistema

### 1. Custom Axes Handler (`core/axes_handler.py`)

```python
class CustomAxesHandler(AxesDatabaseHandler):
    """Handler que agrega logging estructurado a eventos de Axes"""
    
    def user_login_failed(self, ...):
        # Loguea cada intento fallido
        
    def user_locked_out(self, ...):
        # Loguea bloqueos con nivel WARNING
```

### 2. Signal Receivers (`core/signals.py`)

```python
from axes.signals import user_locked_out
from django.dispatch import receiver

@receiver(user_locked_out)
def log_user_lockout(sender, request, username, ip_address, **kwargs):
    """Signal disparado cuando Axes bloquea un usuario/IP"""
    # Log crítico de seguridad
```

### 3. App Configuration (`core/apps.py`)

```python
class CoreConfig(AppConfig):
    name = 'core'
    
    def ready(self):
        """
        Importa signals DESPUÉS de que Django cargue todas las apps.
        Esto previene errores de AppRegistryNotReady.
        """
        from . import signals  # noqa: F401
```

**⚠️ IMPORTANTE - Error AppRegistryNotReady:**

Si ves este error:
```
django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
```

**Causa:** Importar signals en `core/__init__.py` antes de que Django inicialice las apps.

**Solución:**
1. ❌ **NO** importar signals en `core/__init__.py`
2. ✅ **SÍ** importar signals en `CoreConfig.ready()` de `core/apps.py`
3. ✅ Registrar `core.apps.CoreConfig` en `INSTALLED_APPS` de `settings.py`

---

## 🔧 Componentes del Sistema (Detalle)

### 1. Custom Axes Handler (`core/axes_handler.py`)

```python
class CustomAxesHandler(AxesDatabaseHandler):
    """Handler que agrega logging estructurado a eventos de Axes"""
    
    def user_login_failed(self, ...):
        # Log cuando quedan 2 intentos o menos
        if attempts >= failure_limit - 2:
            logger.warning(
                f"ALERTA BLOQUEO INMINENTE | Email: {username} | "
                f"IP: {ip_address} | Intentos: {attempts}/{failure_limit}"
            )
    
    def user_locked_out(self, ...):
        # Log CRÍTICO cuando se bloquea
        logger.warning(
            f"🔒 USUARIO BLOQUEADO POR FUERZA BRUTA | Email: {username} | "
            f"IP: {ip_address} | User-Agent: {user_agent}"
        )
```

### 2. Signals de Seguridad (`core/signals.py`)

```python
@receiver(user_locked_out)
def log_user_lockout(sender, request, username, ip_address, **kwargs):
    """Signal que captura eventos de bloqueo de Axes"""
    logger.warning(
        f"🔒 BLOQUEO POR FUERZA BRUTA | "
        f"Email: {username} | "
        f"IP: {ip_address} | "
        f"User-Agent: {user_agent} | "
        f"Cooloff: 15 minutos"
    )
```

**Nota:** Los signals se registran automáticamente al importarse en `core/__init__.py`

---

## 📊 Flujo de Eventos y Logs

### Secuencia Normal de Intento Fallido

```
1. Usuario ingresa credenciales incorrectas
   └─> CustomLoginView.form_invalid()
       └─> Log: "LOGIN FALLIDO | Motivo: Contraseña INCORRECTA"
   └─> Axes registra el intento
       └─> CustomAxesHandler.user_login_failed()
       └─> Si quedan ≤2 intentos:
           └─> Log: "ALERTA BLOQUEO INMINENTE | Intentos: 8/10"

2. Después de 10 intentos fallidos:
   └─> Axes bloquea al usuario
       └─> CustomAxesHandler.user_locked_out()
           └─> Log: "🔒 USUARIO BLOQUEADO POR FUERZA BRUTA"
       └─> Signal user_locked_out
           └─> Log: "🔒 BLOQUEO POR FUERZA BRUTA | Cooloff: 15 minutos"
   └─> Redirección a /accounts/login/?locked=1
       └─> Mensaje: "Cuenta bloqueada temporalmente"

3. Usuario intenta login mientras está bloqueado:
   └─> Axes intercepta ANTES de validar credenciales
   └─> Redirección inmediata a locked URL
   └─> NO se ejecuta CustomLoginView.form_invalid()
```

---

## 📝 Ejemplos de Logs Reales

### Logs de Intentos Normales

```bash
# Intento 1-7
WARNING 2025-11-07 10:30:15 apps.accounts [63:123170228176576] LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: test@example.com | IP: 172.18.0.1

# Intento 8 (alerta)
WARNING 2025-11-07 10:30:20 apps.accounts [63:123170228176576] ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 172.18.0.1 | Intentos: 8/10

# Intento 9 (alerta)
WARNING 2025-11-07 10:30:25 apps.accounts [63:123170228176576] ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 172.18.0.1 | Intentos: 9/10

# Intento 10 (último antes de bloqueo)
WARNING 2025-11-07 10:30:30 apps.accounts [63:123170228176576] LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: test@example.com | IP: 172.18.0.1
WARNING 2025-11-07 10:30:30 apps.accounts [63:123170228176576] ALERTA BLOQUEO INMINENTE | Email: test@example.com | IP: 172.18.0.1 | Intentos: 10/10
```

### Log de Bloqueo (CRÍTICO)

```bash
# Intento 11 - BLOQUEADO
WARNING 2025-11-07 10:30:35 apps.accounts [63:123170228176576] 🔒 USUARIO BLOQUEADO POR FUERZA BRUTA | Email: test@example.com | IP: 172.18.0.1 | User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
WARNING 2025-11-07 10:30:35 apps.accounts [63:123170228176576] 🔒 BLOQUEO POR FUERZA BRUTA | Email: test@example.com | IP: 172.18.0.1 | User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 | Cooloff: 15 minutos
```

### Log de Desbloqueo Automático

```bash
# Después de 15 minutos - Login exitoso
INFO 2025-11-07 10:46:00 apps.accounts [63:123170228176576] LOGIN EXITOSO | Email: test@example.com | ID: 5 | Rol: Arquitecto | Org: Mi Empresa | IP: 172.18.0.1 | Sesión: 7 días
```

---

## 🔍 Monitoreo en Producción

### Queries Útiles para Railway/Logs

```bash
# Ver todos los bloqueos del día
grep "🔒 BLOQUEO POR FUERZA BRUTA" logs/security.log | grep "$(date +%Y-%m-%d)"

# Contar bloqueos por IP
grep "🔒 BLOQUEO" logs/security.log | grep -oP 'IP: \K[^ ]+' | sort | uniq -c | sort -rn

# Ver emails más atacados
grep "🔒 BLOQUEO" logs/security.log | grep -oP 'Email: \K[^ ]+' | sort | uniq -c | sort -rn

# Alertas en tiempo real (últimos 5 bloqueos)
tail -f logs/security.log | grep "🔒 BLOQUEO" | tail -5
```

### Alertas Recomendadas

**Alerta Crítica: Ataque en Curso**
```bash
# Si hay >5 bloqueos en 1 hora → Posible ataque coordinado
if [ $(grep "🔒 BLOQUEO" logs/security.log | grep "$(date +%Y-%m-%d\ %H)" | wc -l) -gt 5 ]; then
    echo "⚠️ ALERTA: Posible ataque de fuerza bruta en curso"
fi
```

**Alerta Alta: IP Sospechosa**
```bash
# Si una IP tiene >20 intentos fallidos → Bloquear en firewall
grep "LOGIN FALLIDO" logs/app.log | grep "IP: 192.168.1.1" | wc -l
```

---

## 🛡️ Mejores Prácticas

### ✅ Implementadas

1. **Logging Estructurado**
   - Formato consistente con emoji 🔒 para fácil búsqueda
   - Nivel WARNING para aparecer en alertas
   - Información completa: Email, IP, User-Agent

2. **Dual Tracking**
   - Por email: Protege cuentas específicas
   - Por IP: Previene enumeración de usuarios

3. **Alertas Tempranas**
   - Log cuando quedan 2 intentos
   - Permite intervención antes del bloqueo

4. **Auto-Recovery**
   - Desbloqueo automático en 15 minutos
   - No requiere intervención manual

5. **Reset Inteligente**
   - Contador se resetea en login exitoso
   - Usuario legítimo no queda penalizado

### ⚠️ Consideraciones Adicionales

**Para entornos de alta seguridad:**
```python
# Considerar valores más estrictos
AXES_FAILURE_LIMIT = 5                     # 5 intentos en lugar de 10
AXES_COOLOFF_TIME = 1                      # 1 hora en lugar de 15 min
AXES_ONLY_USER_FAILURES = True             # Solo cuenta por email (no IP)
```

**Para entornos de desarrollo:**
```python
# Desactivar temporalmente
AXES_ENABLED = False  # Solo en local, NUNCA en producción
```

---

## 🔧 Troubleshooting

### Problema: No aparece el log de bloqueo

**Posibles causas:**
1. Signals no están registrados
   ```python
   # Verificar en core/__init__.py
   from . import signals  # Debe estar presente
   ```

2. Logger no configurado
   ```python
   # Verificar en settings.py
   'apps.accounts': {
       'handlers': ['console_dev', 'file_app'],
       'level': 'INFO',
   }
   ```

3. Axes no está bloqueando
   ```bash
   # Verificar en admin
   /admin/axes/accessattempt/
   ```

### Problema: Bloqueo no se levanta después de 15 min

**Solución:**
```bash
# Limpiar manualmente bloqueos
python manage.py axes_reset  # Reset todos los bloqueos
python manage.py axes_reset_ip 192.168.1.1  # Reset IP específica
python manage.py axes_reset_username test@example.com  # Reset email específico
```

### Problema: Bloqueo afecta a usuarios legítimos

**Ajustar configuración:**
```python
AXES_FAILURE_LIMIT = 15  # Más intentos permitidos
AXES_COOLOFF_TIME = 0.17  # 10 minutos (más corto)
```

---

## 📚 Referencias

- **Django Axes Docs:** https://django-axes.readthedocs.io/
- **Logging de Seguridad:** `docs/SECURITY_LOGGING.md`
- **Testing Manual:** `tests/MANUAL_TESTING_LOGIN.md` (SEG-01)

---

**Última revisión:** 07/11/2025  
**Próxima revisión:** 07/12/2025
