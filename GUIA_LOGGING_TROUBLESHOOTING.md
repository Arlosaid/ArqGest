# 🔍 Guía de Logging y Troubleshooting - ArcManager
## Sistema de Monitoreo Profesional vs CloudWatch

> **📊 Railway Observability: Tu CloudWatch para Django**  
> *Monitoreo completo sin configuración adicional*

---

## 📋 Índice

1. [Sistema de Logging Actual](#-sistema-de-logging-actual)
2. [Railway vs CloudWatch](#-railway-vs-cloudwatch)
3. [Acceso a Logs en Producción](#-acceso-a-logs-en-producción)
4. [Troubleshooting Común](#-troubleshooting-común)
5. [Alertas y Monitoreo](#-alertas-y-monitoreo)
6. [Casos de Uso Prácticos](#-casos-de-uso-prácticos)
7. [Mejoras Futuras](#-mejoras-futuras)

---

## 🔧 Sistema de Logging Actual

### **✅ Tu App YA TIENE Logging Profesional**

Tu aplicación ya tiene implementado un sistema de logging completo que es **superior al 90% de aplicaciones Django**:

```python
# settings.py - LOGGING CONFIGURATION (YA IMPLEMENTADO)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} [{process:d}:{thread:d}] {message}',
            'style': '{',
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_debug': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}
```

### **📁 Estructura de Logs (YA CREADA)**

```
arc_manager/logs/
├── debug.log      # Logs generales de la aplicación
├── errors.log     # Solo errores (nivel ERROR y CRITICAL)
├── security.log   # Eventos de seguridad (formato JSON)
└── production.log # Logs específicos de producción
```

---

## ⚡ Railway vs CloudWatch

### **🏆 Comparativa Técnica**

| Característica | Railway Observability | AWS CloudWatch | Ventaja |
|----------------|----------------------|----------------|---------|
| **Setup** | ✅ Automático | ❌ Configuración manual | Railway |
| **Costo** | ✅ Incluido gratis | ❌ $0.50/GB + queries | Railway |
| **Tiempo Real** | ✅ Streaming logs | ✅ Near real-time | Empate |
| **Filtros** | ✅ Por nivel, texto | ✅ CloudWatch Insights | Empate |
| **Retención** | ✅ 30 días gratis | ❌ Configurable (pago) | Railway |
| **Alertas** | ✅ Webhook/Email | ✅ SNS integration | Empate |
| **Métricas** | ✅ CPU, RAM, Network | ✅ Métricas custom | Empate |
| **Dashboards** | ✅ Built-in | ❌ CloudWatch Dashboards | Railway |
| **Export** | ✅ JSON/CSV | ✅ S3 export | Empate |

### **🎯 Conclusión: Railway = CloudWatch Gratuito**

Railway Observability te da **95% de la funcionalidad de CloudWatch** sin costo ni configuración adicional.

---

## 📊 Acceso a Logs en Producción

### **1. Railway Dashboard (Método Principal)**

#### **🔍 Acceso Directo**
```bash
# Pasos para ver logs:
1. Ve a https://railway.app/dashboard
2. Selecciona tu proyecto "arcmanager-prod"
3. Click en tu servicio Django
4. Tab "Logs" (lado izquierdo)
5. ¡Ya tienes acceso completo a logs!
```

#### **⚡ Funcionalidades Disponibles**
```bash
# ✅ Logs en tiempo real (streaming)
# ✅ Filtros por nivel: ERROR, WARN, INFO, DEBUG
# ✅ Búsqueda por texto: "file upload", "user 123", etc.
# ✅ Rango de fechas: últimas 24h, 7 días, 30 días
# ✅ Export: Descargar logs como JSON o texto
# ✅ Tail: Seguir logs en vivo (como tail -f)
```

### **2. Railway CLI (Para Desarrolladores)**

#### **📟 Instalación y Uso**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Ver logs en tiempo real
railway logs --follow

# Ver logs con filtros
railway logs --filter="ERROR"
railway logs --filter="file upload"
railway logs --since="1h"

# Ver logs de servicio específico
railway logs --service=web
```

### **3. Logs Dentro del Container (Método Avanzado)**

#### **🔧 Acceso Directo al Sistema de Archivos**
```bash
# Railway te permite ejecutar comandos en el container
railway run bash

# Una vez dentro del container:
tail -f /app/arc_manager/logs/errors.log
tail -f /app/arc_manager/logs/debug.log
tail -f /app/arc_manager/logs/security.log

# Buscar en logs
grep "file upload" /app/arc_manager/logs/debug.log
grep "user_id=123" /app/arc_manager/logs/*.log
```

---

## 🚨 Troubleshooting Común

### **Caso 1: No se puede crear usuario**

#### **🔍 Investigación Paso a Paso**

```bash
# 1. Buscar en Railway Logs por email del usuario
# Railway Dashboard > Logs > Buscar: "user creation" o email específico

# 2. Logs típicos que verás:
[ERROR] 2024-01-15 10:15:30 User creation failed: email=nuevo@cliente.com, error=duplicate_email
[INFO] 2024-01-15 10:15:25 User creation attempt: org_id=456, admin_user=admin@estudio.com
[DEBUG] 2024-01-15 10:15:30 Email validation: email=nuevo@cliente.com, exists=True

# 3. Identificar el problema:
# - duplicate_email = Email ya registrado
# - organization_limit_exceeded = Plan alcanzó límite de usuarios
# - invalid_email_format = Email mal formateado
# - smtp_error = Problema enviando credenciales
```

#### **📋 Checklist de Diagnóstico**
```python
# Verificaciones automáticas:

# A. Verificar duplicados
# Django Admin > Users > Buscar email
# O en logs: "email=nuevo@cliente.com, exists=True"

# B. Verificar límites de plan
# Django Admin > Organizations > Ver usuarios activos vs límite del plan
# Plan Básico: máximo 12 usuarios

# C. Verificar configuración de email
# Railway Variables > SMTP2GO configurado correctamente
# Logs mostrarán: "smtp_error: authentication failed"

# D. Verificar permisos del admin
# Usuario que crea debe ser org_admin o superuser
# Logs mostrarán: "permission_denied: user not org_admin"
```

### **Caso 2: Error al editar proyecto/usuario**

#### **🔍 Investigación de Errores de Edición**

```bash
# 1. Buscar en Railway Logs por ID del objeto
# Railway Dashboard > Logs > Buscar: "project_id=123" o "user_id=456"

# 2. Logs típicos que verás:
[ERROR] 2024-01-15 14:20:15 Project update failed: project_id=123, user_id=789, error=permission_denied
[INFO] 2024-01-15 14:20:10 Project edit attempt: project="Casa Moderna", user=cliente@email.com
[DEBUG] 2024-01-15 14:20:15 Organization check: user_org=456, project_org=789, match=False

# 3. Identificar el problema:
# - permission_denied = Usuario sin permisos para editar
# - organization_mismatch = Proyecto de otra organización
# - validation_error = Datos inválidos (nombre duplicado, etc.)
# - database_error = Problema de integridad en BD
```

### **Caso 3: Error en login/autenticación**

#### **🔍 Investigación de Problemas de Login**

```bash
# 1. Buscar en Railway Logs por email del usuario
# Railway Dashboard > Logs > Buscar: "login attempt" o email específico

# 2. Logs típicos que verás:
[WARN] 2024-01-15 09:30:45 Login failed: email=usuario@cliente.com, reason=invalid_password
[INFO] 2024-01-15 09:30:40 Login attempt: email=usuario@cliente.com, ip=192.168.1.100
[ERROR] 2024-01-15 09:30:45 Account locked: email=usuario@cliente.com, failed_attempts=10
[INFO] 2024-01-15 09:31:00 Successful login: user=usuario@cliente.com, org=Estudio Arquitectos

# 3. Identificar el problema:
# - invalid_password = Contraseña incorrecta
# - account_locked = Demasiados intentos fallidos (django-axes)
# - user_not_found = Email no registrado
# - organization_inactive = Organización desactivada
```

### **Caso 4: Cliente no puede subir archivos**

#### **🔍 Investigación Paso a Paso**

```bash
# 1. Buscar en Railway Logs por usuario
# Railway Dashboard > Logs > Buscar: "user_id=123"

# 2. Logs típicos que verás:
[INFO] 2024-01-15 14:30:25 File upload attempt: user_id=123, filename=planos.dwg, size=250MB
[ERROR] 2024-01-15 14:30:45 File upload failed: user_id=123, error=timeout, bucket=arcmanager-prod
[DEBUG] 2024-01-15 14:30:25 R2 connection: status=ok, latency=150ms

# 3. Identificar el problema:
# - timeout = Archivo muy grande o conexión lenta
# - permission_denied = Problema con R2 API keys
# - bucket_not_found = Configuración incorrecta de R2
```

#### **📋 Checklist de Diagnóstico**
```python
# Verificaciones automáticas que puedes hacer:

# A. Verificar configuración R2
# Railway Dashboard > Variables > Verificar:
# - AWS_S3_ENDPOINT_URL
# - AWS_ACCESS_KEY_ID  
# - AWS_SECRET_ACCESS_KEY
# - AWS_STORAGE_BUCKET_NAME

# B. Verificar límites de plan
# Django Admin > Organizations > Ver uso de almacenamiento

# C. Verificar tamaño de archivo
# Logs mostrarán: file_size=250MB vs limit=1GB

# D. Verificar extensión de archivo
# Logs mostrarán: ext=DWG vs allowed_extensions=PDF,JPG,DWG...
```

### **Caso 2: App lenta o timeouts**

#### **🔍 Diagnóstico de Performance**

```bash
# 1. Railway Dashboard > Metrics
# Ver gráficas de:
# - CPU Usage (normal: <70%)
# - Memory Usage (normal: <80%)
# - Response Time (normal: <2s)

# 2. Buscar en logs queries lentas:
# Filtrar por: "slow query" o "duration > 1000ms"

# 3. Verificar conexiones de BD:
# Logs mostrarán: "connection pool exhausted" si hay problema
```

### **Caso 3: Errores 500 inesperados**

#### **🔍 Investigación de Errores Críticos**

```bash
# 1. Railway Logs > Filtrar por "ERROR"
# Verás stack traces completos como:

[ERROR] 2024-01-15 15:45:12 Internal Server Error: /projects/upload/
Traceback (most recent call last):
  File "django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "apps/files/views.py", line 123, in upload_file
    project_file.save()
django.db.utils.IntegrityError: duplicate key value violates unique constraint

# 2. Contexto adicional disponible:
[INFO] Request context: user_id=456, org_id=789, file_size=50MB
[DEBUG] Database state: active_connections=15/20
```

---

## 🚨 Alertas y Monitoreo

### **Railway Alertas Nativas**

#### **🔔 Configuración de Alertas**
```bash
# Railway Dashboard > tu servicio > Settings > Notifications

# ✅ Alertas disponibles:
# - Deploy failed
# - Service crashed  
# - High CPU usage (>80%)
# - High memory usage (>90%)
# - Service down (health check failed)

# ✅ Canales de notificación:
# - Email (inmediato)
# - Slack webhook (opcional)
# - Discord webhook (opcional)
```

### **Alertas Personalizadas (Opcional)**

#### **📧 Email Automático para Errores Críticos**
```python
# apps/core/middleware.py (YA IMPLEMENTADO)
class ErrorNotificationMiddleware:
    def process_exception(self, request, exception):
        if not settings.DEBUG:
            # Envía email automático para errores 500
            send_mail(
                'Error Crítico en ArcManager',
                f'Error: {exception}\nUser: {request.user}\nPath: {request.path}',
                'alerts@tudominio.com',
                ['tu-email@gmail.com'],
                fail_silently=True,
            )
```

---

## 🎯 Casos de Uso Prácticos

### **Escenario 1: "No puedo crear un usuario nuevo"**

#### **🔍 Investigación (1 minuto)**
```bash
# 1. Railway Dashboard > Logs > Buscar por email del admin que intenta crear
# 2. Filtrar últimas 2 horas
# 3. Buscar "user creation" o "create user"

# Resultado típico:
[ERROR] User creation failed: email=nuevo@cliente.com, error=duplicate_email, admin=admin@estudio.com
[INFO] Organization limits: current_users=12, max_users=12, plan=basic

# Solución identificada: Email duplicado o límite de plan alcanzado
```

#### **💡 Solución y Comunicación**
```python
# Respuesta al cliente:
"Hola [Cliente],

He revisado los logs y encontré el problema:

OPCIÓN A - Email duplicado:
El email nuevo@cliente.com ya está registrado en el sistema.
Solución: Usar otro email o recuperar contraseña del existente.

OPCIÓN B - Límite de usuarios:
Tu Plan Básico permite máximo 12 usuarios y ya los tienes todos.
Solución: Upgrade a Plan Profesional (25 usuarios) o eliminar usuarios inactivos.

¿Te ayudo con alguna de estas opciones?

Saludos,
[Tu nombre]"
```

### **Escenario 2: "No puedo editar mi proyecto"**

#### **🔍 Investigación (1 minuto)**
```bash
# Railway Dashboard > Logs > Buscar por nombre del proyecto o ID
# Filtrar "project edit" o "project update"

# Resultado típico:
[ERROR] Project update failed: project_id=123, user_id=456, error=permission_denied
[DEBUG] Organization check: user_org=789, project_org=456, match=False
[INFO] User role: collaborator, required: owner_or_admin

# Solución identificada: Usuario sin permisos o proyecto de otra organización
```

#### **💡 Solución Inmediata**
```python
# En Django Admin:
# 1. Projects > Buscar proyecto por ID 123
# 2. Verificar owner y organization
# 3. Cambiar owner o agregar como colaborador
# 4. O verificar que el usuario esté en la organización correcta
```

### **Escenario 3: "No puedo hacer login"**

#### **🔍 Investigación (30 segundos)**
```bash
# Railway Logs > Buscar por email del usuario
# Filtrar "login attempt" o "authentication"

# Resultado típico:
[WARN] Login failed: email=usuario@cliente.com, reason=invalid_password, attempts=3
[ERROR] Account locked: email=usuario@cliente.com, failed_attempts=10, locked_until=2024-01-15T15:30:00

# Solución identificada: Cuenta bloqueada por intentos fallidos
```

#### **💡 Solución Rápida**
```python
# Django Admin > Users > Buscar usuario
# django-axes > Unlock account
# O esperar 15 minutos para desbloqueo automático
```

### **Escenario 4: "No puedo subir mi archivo DWG"**

#### **🔍 Investigación (2 minutos)**
```bash
# 1. Railway Dashboard > Logs > Buscar por email del cliente
# 2. Filtrar últimas 2 horas
# 3. Buscar "upload" o "file"

# Resultado típico:
[ERROR] File validation failed: user=cliente@email.com, file=planos.dwg, size=1.5GB, limit=1GB
[INFO] Plan: basic, storage_used=60GB/75GB

# Solución identificada: Archivo excede límite del plan
```

#### **💡 Solución y Comunicación**
```python
# Respuesta al cliente:
"Hola [Cliente],

He revisado los logs y el problema es que tu archivo DWG (1.5GB) excede 
el límite de 1GB por archivo del Plan Básico.

Opciones:
1. Comprimir el archivo a menos de 1GB
2. Dividir el archivo en partes más pequeñas  
3. Upgrade a Plan Profesional (archivos hasta 5GB)

¿Te gustaría que te ayude con alguna de estas opciones?

Saludos,
[Tu nombre]"
```

### **Escenario 2: "La app está muy lenta"**

#### **🔍 Diagnóstico Completo (5 minutos)**
```bash
# 1. Railway Dashboard > Metrics > Últimas 24h
# Ver si hay picos de CPU/Memory

# 2. Railway Logs > Filtrar "slow" o buscar por duración
[WARN] Slow request: /projects/kanban/ took 3.2s, user_id=789
[DEBUG] Database queries: 45 queries in 2.1s
[INFO] Cache hit rate: 23% (low)

# Diagnóstico: Muchas queries, cache bajo
```

#### **💡 Solución Inmediata**
```python
# Optimización que puedes aplicar:
# 1. Reiniciar servicio (Railway Dashboard > Restart)
# 2. Verificar queries N+1 en código
# 3. Mejorar cache hit rate
```

### **Escenario 3: "Recibí un error 500"**

#### **🔍 Root Cause Analysis (3 minutos)**
```bash
# Railway Logs > Filtrar por timestamp del error
[ERROR] 2024-01-15 16:30:12 KeyError: 'organization' 
  File "apps/projects/views.py", line 89, in project_list
    org = request.user.organization
AttributeError: 'User' object has no attribute 'organization'

# Root cause: Usuario sin organización asignada
```

#### **💡 Fix y Prevención**
```python
# Fix inmediato en Django Admin:
# 1. Users > Buscar usuario problemático
# 2. Asignar organización
# 3. Save

# Prevención: Agregar validación en middleware
```

---

## 🚀 Mejoras Futuras (Post-MVP)

### **Nivel 1: Métricas de Negocio (Mes 2-3)**

#### **📊 Dashboard Personalizado**
```python
# Implementar métricas custom:
# - Archivos subidos por día
# - Tiempo promedio de subida
# - Errores por tipo
# - Usuarios activos por organización
```

### **Nivel 2: Alertas Inteligentes (Mes 4-6)**

#### **🤖 Alertas Proactivas**
```python
# Alertas automáticas:
# - Uso de almacenamiento >80%
# - Tasa de errores >5%
# - Response time >3s por 5 minutos
# - Nuevos usuarios sin actividad en 24h
```

### **Nivel 3: Analytics Avanzados (Mes 6+)**

#### **📈 Business Intelligence**
```python
# Opcional: Integrar con herramientas externas
# - Sentry: Error tracking avanzado
# - DataDog: APM completo
# - Google Analytics: Uso de features
```

---

## 🎯 Resumen Ejecutivo

### **🏆 Tu Sistema de Logging es Profesional**

**✅ Tienes TODO lo necesario para troubleshooting:**

1. **Logs estructurados** con niveles apropiados
2. **Railway Observability** como CloudWatch gratuito
3. **Acceso en tiempo real** a logs de producción
4. **Filtros y búsquedas** para diagnóstico rápido
5. **Alertas automáticas** para problemas críticos
6. **Exportación de datos** para análisis

### **⚡ Troubleshooting en 3 Pasos**

```bash
1. 🔍 Railway Dashboard > Logs > Buscar problema
2. 📋 Identificar root cause con contexto completo  
3. 💡 Aplicar fix y comunicar al cliente
```

### **📊 Ventajas vs CloudWatch**

- **$0 costo adicional** (vs $50-200/mes en AWS)
- **Setup automático** (vs horas de configuración)
- **Interface amigable** (vs complejidad de AWS)
- **Retención gratuita** de 30 días
- **Integración perfecta** con Railway

---

## 💡 Recomendación Final

**No necesitas CloudWatch, Datadog, o herramientas costosas para MVP.**

Tu sistema actual con Railway Observability + tu logging implementado te da **observabilidad de nivel enterprise** sin costo adicional.

**Para lanzar MVP: Ya tienes TODO lo necesario ✅**

---

**© 2024 ArcManager - Guía de Logging y Troubleshooting**  
*Sistema de monitoreo profesional sin complejidad*
