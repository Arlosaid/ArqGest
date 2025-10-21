# 📧 Sistema de Logging de Emails - ArqGest

Documentación del sistema de logging estructurado con trazabilidad completa para el módulo de emails.

---

## 📊 **Códigos de Error (E001-E999)**

Todos los eventos de email se registran con códigos estructurados siguiendo las buenas prácticas de la aplicación.

### **Envío de Emails (E001-E099)**

| Código | Nombre | Descripción | Nivel |
|--------|--------|-------------|-------|
| `E001` | `EMAIL_SEND_SUCCESS` | Email enviado exitosamente | INFO |
| `E002` | `EMAIL_SEND_FAILED` | Error al enviar email | ERROR |
| `E003` | `EMAIL_SEND_INVALID_RECIPIENT` | Destinatario inválido | WARNING |
| `E004` | `EMAIL_SEND_INVALID_SENDER` | Remitente inválido | ERROR |
| `E005` | `EMAIL_SEND_MISSING_SUBJECT` | Falta asunto del email | ERROR |
| `E006` | `EMAIL_SEND_MISSING_CONTENT` | Falta contenido del email | ERROR |
| `E007` | `EMAIL_SEND_API_ERROR` | Error en API de Resend | ERROR |
| `E008` | `EMAIL_SEND_RATE_LIMIT` | Límite de tasa excedido | WARNING |
| `E009` | `EMAIL_SEND_QUOTA_EXCEEDED` | Cuota diaria excedida | ERROR |
| `E015` | `EMAIL_SEND_SPAM_REJECTED` | Email rechazado como spam | WARNING |

### **Configuración (E101-E199)**

| Código | Nombre | Descripción | Nivel |
|--------|--------|-------------|-------|
| `E101` | `EMAIL_CONFIG_API_KEY_MISSING` | API Key no configurada | ERROR |
| `E102` | `EMAIL_CONFIG_API_KEY_INVALID` | API Key inválida | ERROR |
| `E103` | `EMAIL_CONFIG_DOMAIN_NOT_VERIFIED` | Dominio no verificado | ERROR |
| `E104` | `EMAIL_CONFIG_BACKEND_ERROR` | Error en backend de email | ERROR |
| `E107` | `EMAIL_CONFIG_CONNECTION_ERROR` | Error de conexión con Resend | ERROR |

### **Notificaciones (E301-E399)**

| Código | Nombre | Descripción | Nivel |
|--------|--------|-------------|-------|
| `E301` | `EMAIL_NOTIFICATION_PASSWORD_RESET` | Email de recuperación de contraseña | INFO |
| `E302` | `EMAIL_NOTIFICATION_CREDENTIALS_SENT` | Credenciales enviadas a usuario | INFO |
| `E303` | `EMAIL_NOTIFICATION_WELCOME` | Email de bienvenida | INFO |
| `E304` | `EMAIL_NOTIFICATION_SUBSCRIPTION_REMINDER` | Recordatorio de suscripción | INFO |
| `E305` | `EMAIL_NOTIFICATION_SUBSCRIPTION_EXPIRED` | Notificación de expiración | WARNING |

---

## 📝 **Formato de Logs**

### **Estructura del Log**

Todos los logs siguen el formato estructurado de la aplicación usando `log_operation()`:

```python
OP [OPERATION] User: user@email.com sender: from@email.com subject: Asunto... email_id: abc123 ERROR_CODE: E001
```

### **Ejemplo de Log Exitoso**

```
OP [EMAIL_SEND_START] User: alonso.delacruzhdez@gmail.com sender: ArqGest <noreply@arqgest.com> subject: Restablece tu contraseña de ArqGest recipients_count: 1 has_html: True has_attachments: 0
OP [EMAIL_SEND_SUCCESS] User: alonso.delacruzhdez@gmail.com email_id: 01jb7k8m9n0p1q2r3s4t5u6v sender: ArqGest <noreply@arqgest.com> subject: Restablece tu contraseña de ArqGest provider: Resend recipients_count: 1 ERROR_CODE: E001
```

### **Ejemplo de Log con Error**

```
OP [EMAIL_SEND_ERROR] User: test@example.com sender: ArqGest <noreply@arqgest.com> subject: Test Email error_type: ResendError error_message: Invalid API key format provider: Resend fail_silently: False ERROR_CODE: E102
```

---

## 🔍 **Trazabilidad Completa**

Cada envío de email registra:

### **Inicio del Envío (`EMAIL_SEND_START`)**
- ✅ Usuario destinatario
- ✅ Email remitente
- ✅ Asunto (primeros 50 caracteres)
- ✅ Número de destinatarios
- ✅ Tipo de contenido (HTML/texto)
- ✅ Número de adjuntos
- ✅ Timestamp automático

### **Envío Exitoso (`EMAIL_SEND_SUCCESS`)**
- ✅ Código de operación: `E001`
- ✅ ID del email en Resend
- ✅ Proveedor (Resend)
- ✅ Todos los datos del inicio

### **Envío Fallido (`EMAIL_SEND_ERROR`)**
- ✅ Código de error específico (`E002`, `E007`, `E008`, etc.)
- ✅ Tipo de excepción
- ✅ Mensaje de error (primeros 200 caracteres)
- ✅ Contexto completo del envío

---

## 🛠️ **Uso en Código**

### **Backend de Django (Automático)**

El backend de Resend registra automáticamente todos los emails enviados mediante Django:

```python
from django.core.mail import send_mail

# Esto ya registra logs automáticamente
send_mail(
    'Asunto',
    'Mensaje',
    'from@arqgest.com',
    ['to@example.com'],
)
```

**Logs generados:**
```
OP [EMAIL_SEND_START] User: to@example.com ...
OP [EMAIL_SEND_SUCCESS] User: to@example.com email_id: xyz123 ERROR_CODE: E001
```

### **API Directa de Resend**

```python
from core.email_utils import send_resend_email

result = send_resend_email(
    to_email='usuario@example.com',
    subject='Bienvenido a ArqGest',
    html_content='<h1>Bienvenido</h1>',
    text_content='Bienvenido'
)
```

**Logs generados:**
```
OP [EMAIL_SEND_START] User: usuario@example.com sender: ArqGest <noreply@arqgest.com> subject: Bienvenido a ArqGest has_html: True has_text: True provider: Resend
OP [EMAIL_SEND_SUCCESS] User: usuario@example.com email_id: abc123 ERROR_CODE: E001 ...
```

---

## 📈 **Monitoreo y Análisis**

### **Buscar Emails Enviados**

```bash
# En Railway
railway logs | grep "EMAIL_SEND_SUCCESS"

# Filtrar por usuario específico
railway logs | grep "alonso.delacruzhdez@gmail.com"

# Ver solo errores
railway logs | grep "EMAIL_SEND_ERROR"
```

### **Estadísticas de Envío**

```bash
# Contar emails exitosos
railway logs | grep "ERROR_CODE: E001" | wc -l

# Ver emails con rate limit
railway logs | grep "ERROR_CODE: E008"

# Ver problemas de configuración
railway logs | grep "ERROR_CODE: E101\|E102\|E103"
```

### **Análisis de Errores por Tipo**

```bash
# Errores de API
railway logs | grep "ERROR_CODE: E007"

# Quota excedida
railway logs | grep "ERROR_CODE: E009"

# API Key inválida
railway logs | grep "ERROR_CODE: E102"
```

---

## 🔐 **Seguridad y Privacidad**

### **Datos que NO se registran:**

- ❌ Contenido completo del email
- ❌ API Key completa (solo primeros 10 caracteres)
- ❌ Contraseñas o datos sensibles
- ❌ Información personal identificable en exceso

### **Datos que SÍ se registran:**

- ✅ Email destinatario
- ✅ Asunto (primeros 50 caracteres)
- ✅ Tipo de email (HTML/texto)
- ✅ ID de Resend para trazabilidad
- ✅ Códigos de error
- ✅ Timestamps

---

## 🎯 **Mejores Prácticas**

### **1. Siempre usar el backend de Django**

```python
# ✅ Recomendado - Logging automático
from django.core.mail import send_mail
send_mail(...)

# ⚠️ Solo si necesitas control directo
from core.email_utils import send_resend_email
send_resend_email(...)
```

### **2. Monitorear códigos de error específicos**

```python
# Configurar alertas para códigos críticos:
# - E009: Quota excedida
# - E102: API Key inválida
# - E103: Dominio no verificado
```

### **3. Revisar logs diariamente**

```bash
# Script diario para revisar salud de emails
railway logs --tail 1000 | grep "EMAIL_" | grep "ERROR"
```

### **4. Mantener trazabilidad**

```python
# Cada email tiene un ID único de Resend
# Usa ese ID para rastrear entregas en:
# https://resend.com/emails
```

---

## 📊 **Dashboard de Monitoreo**

### **KPIs Importantes**

1. **Tasa de éxito**: `E001` vs total de envíos
2. **Rate limiting**: Frecuencia de `E008`
3. **Errores de configuración**: `E101`, `E102`, `E103`
4. **Errores de API**: `E007`
5. **Quota**: Monitor de `E009`

### **Alertas Recomendadas**

| Error | Alerta | Acción |
|-------|--------|---------|
| `E009` | Inmediata | Upgrade plan de Resend |
| `E102` | Inmediata | Verificar API Key |
| `E103` | Alta | Verificar DNS/dominio |
| `E008` | Media | Revisar volumen de envíos |
| `E007` | Media | Verificar status de Resend |

---

## 🚀 **Integración con Monitoring**

### **Formato para Exportación**

Los logs están diseñados para integrarse fácilmente con:

- **Sentry**: Errores automáticos (`ERROR` level)
- **DataDog**: Métricas y trazas
- **CloudWatch**: Logs estructurados
- **Grafana**: Dashboards visuales

### **Ejemplo de Query**

```python
from core.error_codes import get_error_codes_by_category

# Obtener todos los códigos de email
email_codes = get_error_codes_by_category('EMAIL')
# ['E001', 'E002', 'E003', ...]
```

---

## ✅ **Verificación del Sistema**

```bash
# 1. Verificar configuración
railway run python manage.py check_email_config

# 2. Probar envío
railway run python manage.py test_email tu@email.com

# 3. Ver logs en tiempo real
railway logs --tail
```

---

## 📚 **Referencias**

- **Códigos de Error**: `arc_manager/core/error_codes.py`
- **Backend Resend**: `arc_manager/core/backends/resend_backend.py`
- **Utilidades**: `arc_manager/core/email_utils.py`
- **Logging System**: `arc_manager/core/error_codes.py` → `log_operation()`

---

**Última actualización**: Octubre 2025  
**Versión**: 1.0.0  
**Autor**: Sistema ArqGest

