# Sistema de Logging - Documentación Completa

## 📋 Índice
1. [Configuración Global del Sistema de Logging](#configuración-global)
2. [Módulo de Login - Implementación Actual](#módulo-de-login)
3. [Niveles de Log y Cuándo Usarlos](#niveles-de-log)
4. [Módulos Prioritarios para Implementar Logging](#módulos-prioritarios)
5. [Estándares y Mejores Prácticas](#estándares-y-mejores-prácticas)
6. [Ejemplos de Implementación por Módulo](#ejemplos-de-implementación)

---

## 🔧 Configuración Global

### Ubicación: `arc_manager/core/settings.py`

### Niveles de Log Configurados:
- **DEBUG**: Solo en desarrollo (`DEBUG=True`)
- **INFO**: Operaciones normales importantes (login, logout, creación de recursos)
- **WARNING**: Eventos de seguridad, intentos fallidos, accesos no autorizados
- **ERROR**: Errores de sistema, excepciones capturadas
- **CRITICAL**: Fallos críticos del sistema

### Handlers:
```python
LOGGING = {
    'handlers': {
        'console_dev': {
            'level': 'INFO',
            'filters': ['require_debug_true', 'ignore_static_files'],
            'formatter': 'simple'
        },
        'console_prod': {
            'level': 'INFO',
            'filters': ['require_debug_false', 'ignore_static_files'],
            'formatter': 'json'  # Estructurado para CloudWatch/Sentry
        },
        'stderr': {
            'level': 'ERROR',
            'formatter': 'verbose'
        }
    }
}
```

### Filtros Aplicados Globalmente:
1. **IgnoreStaticFilesFilter**: Elimina logs de `/static/`, `/media/`, favicon, etc.
2. **SensitiveDataFilter**: Filtra passwords, tokens CSRF, API keys (NO filtra emails)
3. **RequestIdFilter**: Agrega `request_id` para correlación de logs
4. **CompactExceptionFilter**: Reduce stack traces en producción

---

## 🔐 Módulo de Login - Implementación Actual

### Ubicación: `arc_manager/apps/accounts/`

### Archivos Involucrados:
- `views.py`: CustomLoginView, CustomLogoutView, SecurePasswordResetView, ForcePasswordChangeView
- `forms.py`: CustomAuthenticationForm, ForcePasswordChangeForm
- `middleware.py`: LoginRequiredMiddleware, PasswordChangeRequiredMiddleware, SuperuserRestrictMiddleware

### Logger Configurado:
```python
logger = logging.getLogger('apps.accounts')
```

---

## 📊 Logs Implementados en el Módulo de Login

### 1. LOGIN EXITOSO (Usuario Normal)
**Nivel:** `INFO`  
**Ubicación:** `views.py` - `CustomLoginView.form_valid()`  
**Cuándo:** Después de autenticación exitosa de usuario regular

```python
logger.info(
    f"LOGIN EXITOSO | Email: {user_info['email']} | ID: {user_info['id']} | "
    f"Rol: {user_info['role']} | Org: {user_info['organization']} | "
    f"IP: {client_ip} | Sesión: {session_duration}"
)
```

**Ejemplo de salida:**
```
INFO | LOGIN EXITOSO | Email: juan@empresa.com | ID: 123 | Rol: user | Org: Empresa ABC | IP: 192.168.1.100 | Sesión: 7 días
```

**Información capturada:**
- ✅ Email del usuario
- ✅ ID de usuario (para correlación en BD)
- ✅ Rol (user, org_admin, superuser)
- ✅ Organización
- ✅ IP del cliente
- ✅ Duración de sesión configurada

---

### 2. SUPERUSER LOGIN
**Nivel:** `WARNING` (evento de seguridad crítico)  
**Ubicación:** `views.py` - `CustomLoginView.form_valid()`  
**Cuándo:** Login de superusuario (acceso total al sistema)

```python
logger.warning(
    f"SUPERUSER LOGIN | Email: {user.email} | IP: {client_ip} | "
    f"Sesión: {session_duration}"
)
```

**Ejemplo:**
```
WARNING | SUPERUSER LOGIN | Email: admin@sistema.com | IP: 10.0.0.1 | Sesión: 30 días
```

**Por qué WARNING:** 
- Acceso con privilegios máximos
- Debe monitorearse para detectar accesos no autorizados
- Alertas en Sentry/CloudWatch

---

### 3. ORG_ADMIN LOGIN
**Nivel:** `WARNING` (evento de seguridad)  
**Ubicación:** `views.py` - `CustomLoginView.form_valid()`  
**Cuándo:** Login de administrador de organización

```python
logger.warning(
    f"ORG_ADMIN LOGIN | Email: {user.email} | "
    f"Org: {user_info['organization']} | IP: {client_ip}"
)
```

**Ejemplo:**
```
WARNING | ORG_ADMIN LOGIN | Email: admin@empresa.com | Org: Empresa ABC | IP: 192.168.1.50
```

---

### 4. LOGIN FALLIDO
**Nivel:** `WARNING` (seguridad)  
**Ubicación:** `views.py` - `CustomLoginView.form_invalid()`  
**Cuándo:** Credenciales incorrectas o usuario no existe

```python
logger.warning(
    f"LOGIN FALLIDO | Motivo: {error_detail} | "
    f"Email: {username} | IP: {client_ip}"
)
```

**Motivos posibles:**
- `Email vacío`
- `Email NO existe`
- `Cuenta INACTIVA`
- `Contraseña INCORRECTA`

**Ejemplos:**
```
WARNING | LOGIN FALLIDO | Motivo: Contraseña INCORRECTA | Email: juan@empresa.com | IP: 192.168.1.100
WARNING | LOGIN FALLIDO | Motivo: Email NO existe | Email: noexiste@test.com | IP: 203.0.113.45
WARNING | LOGIN FALLIDO | Motivo: Cuenta INACTIVA | Email: suspendido@empresa.com | IP: 192.168.1.75
```

**Utilidad:**
- ✅ Detectar ataques de fuerza bruta
- ✅ Identificar intentos de acceso no autorizado
- ✅ Analizar IPs sospechosas
- ✅ Auditoría de seguridad

---

### 5. LOGIN BLOQUEADO - CUENTA INACTIVA
**Nivel:** `WARNING`  
**Ubicación:** `forms.py` - `CustomAuthenticationForm.clean()`  
**Cuándo:** Usuario desactivado intenta hacer login

```python
logger.warning(
    f"LOGIN BLOQUEADO - CUENTA INACTIVA | Email: {username}"
)
```

**Ejemplo:**
```
WARNING | LOGIN BLOQUEADO - CUENTA INACTIVA | Email: empleado.inactivo@empresa.com
```

---

### 6. PASSWORD CHANGE REQUIRED
**Nivel:** `INFO`  
**Ubicación:** `views.py` - `CustomLoginView.form_valid()`  
**Cuándo:** Usuario necesita cambiar contraseña (primer login, reset por admin)

```python
logger.info(
    f"PASSWORD CHANGE REQUIRED | Email: {user.email} | IP: {client_ip}"
)
```

---

### 7. LOGOUT
**Nivel:** `INFO`  
**Ubicación:** `views.py` - `CustomLogoutView.logout_user()`  
**Cuándo:** Usuario cierra sesión

```python
logger.info(
    f"LOGOUT | Email: {email} | ID: {user_id} | IP: {client_ip}"
)
```

**Ejemplo:**
```
INFO | LOGOUT | Email: juan@empresa.com | ID: 123 | IP: 192.168.1.100
```

---

### 8. PASSWORD RESET
**Nivel:** `INFO` / `WARNING`  
**Ubicación:** `views.py` - `SecurePasswordResetView.form_valid()`

**Password reset exitoso:**
```python
logger.info(f"PASSWORD RESET | Email: {email} | IP: {client_ip}")
```

**Email no registrado:**
```python
logger.warning(
    f"PASSWORD RESET | Email NO registrado: {email} | IP: {client_ip}"
)
```

**Solicitud duplicada bloqueada (rate limiting):**
```python
logger.warning(
    f"PASSWORD RESET BLOQUEADO | Email: {email} | IP: {client_ip} | "
    f"Razón: Solicitud reciente"
)
```

---

### 9. PASSWORD CHANGE EXITOSO
**Nivel:** `INFO`  
**Ubicación:** `views.py` - `ForcePasswordChangeView.post()`

```python
logger.info(
    f"PASSWORD CHANGE EXITOSO | Email: {user.email} | IP: {client_ip}"
)
```

---

### 10. PASSWORD CHANGE FALLIDO
**Nivel:** `WARNING`  
**Ubicación:** `views.py` - `ForcePasswordChangeView.post()`

```python
logger.warning(
    f"PASSWORD CHANGE FALLIDO | Email: {request.user.email} | "
    f"Errores: {form.errors.as_text()}"
)
```

---

### 11. ERRORES DE SISTEMA
**Nivel:** `ERROR`  
**Ubicación:** Múltiples `try/except` blocks

```python
logger.error(f"ERROR verificando login | Email: {username} | Error: {str(e)}")
logger.error(f"ERROR PASSWORD CHANGE | Email: {user.email} | Error: {str(e)}")
```

---

## 🎯 Niveles de Log - Guía de Uso

| Nivel | Cuándo Usar | Ejemplos |
|-------|-------------|----------|
| **DEBUG** | Solo desarrollo, debugging detallado | Validación de formularios, valores de variables |
| **INFO** | Operaciones normales importantes | Login exitoso, creación de recursos, logout |
| **WARNING** | Eventos de seguridad, intentos fallidos | Login fallido, acceso no autorizado, rate limiting |
| **ERROR** | Errores de sistema, excepciones | Query fallida, servicio no disponible, validación crítica |
| **CRITICAL** | Fallos catastróficos | BD caída, servicio crítico offline |

---

## 🚀 Módulos Prioritarios para Implementar Logging

### **ALTA PRIORIDAD** (Implementar inmediatamente)

#### 1. **Módulo de Archivos** (`apps/files/`)
**Por qué:** Manejo de datos sensibles, uploads, storage, permisos

**Logs críticos a implementar:**
- ✅ Upload de archivo (quién, cuándo, tamaño, tipo)
- ✅ Descarga de archivo (quién accedió, cuándo)
- ✅ Eliminación de archivo (quién borró, archivo eliminado)
- ✅ Cambio de permisos (quién modificó, qué cambió)
- ✅ Archivos rechazados (tamaño excedido, tipo no permitido)
- ✅ Errores de storage (R2, local filesystem)
- ✅ Acceso denegado a archivo

**Logger:**
```python
logger = logging.getLogger('apps.files')
```

---

#### 2. **Módulo de Proyectos** (`apps/projects/`)
**Por qué:** Core business logic, múltiples usuarios, permisos

**Logs críticos:**
- ✅ Creación de proyecto (quién, nombre, organización)
- ✅ Modificación de proyecto (qué cambió, quién)
- ✅ Eliminación de proyecto (quién eliminó, proyecto ID)
- ✅ Cambio de estado de proyecto (de estado X a estado Y)
- ✅ Asignación de usuarios a proyecto
- ✅ Acceso denegado a proyecto

**Logger:**
```python
logger = logging.getLogger('apps.projects')
```

---

#### 3. **Módulo de Organizaciones** (`apps/orgs/`)
**Por qué:** Multitenancy, facturación, límites de plan

**Logs críticos:**
- ✅ Creación de organización
- ✅ Cambio de plan/suscripción (plan anterior → nuevo)
- ✅ Límites excedidos (usuarios, proyectos, storage)
- ✅ Invitación de usuarios (quién invitó a quién)
- ✅ Eliminación de usuario de organización
- ✅ Cambio de roles (user → admin, etc.)

**Logger:**
```python
logger = logging.getLogger('apps.orgs')
```

---

#### 4. **Módulo de Planes** (`apps/plans/`)
**Por qué:** Facturación, límites, monetización

**Logs críticos:**
- ✅ Cambio de plan (downgrade/upgrade)
- ✅ Límite alcanzado (usuarios, proyectos, storage)
- ✅ Validación de plan fallida
- ✅ Suscripción expirada
- ✅ Intento de uso de feature no disponible en plan

**Logger:**
```python
logger = logging.getLogger('apps.plans')
```

---

### **MEDIA PRIORIDAD** (Implementar después)

#### 5. **Módulo de Usuarios** (`apps/users/`)
**Por qué:** Gestión de usuarios, permisos, perfiles

**Logs críticos:**
- ✅ Creación de usuario
- ✅ Modificación de perfil
- ✅ Desactivación/activación de cuenta
- ✅ Cambio de email
- ✅ Cambio de rol

---

#### 6. **Core - Middleware** (`core/middleware/`)
**Por qué:** Errores globales, rate limiting, security

**Logs críticos:**
- ✅ Rate limiting activado
- ✅ Errores 500 (ya implementado en error handlers)
- ✅ Accesos bloqueados por seguridad

---

### **BAJA PRIORIDAD** (Opcional)

#### 7. **Módulo Main** (`apps/main/`)
**Por qué:** Dashboard, navegación general

**Logs opcionales:**
- Acceso a dashboard (si es necesario para analytics)
- Uso de features específicos

---

## 📐 Estándares y Mejores Prácticas

### 1. **Formato Consistente**
Todos los logs deben seguir este formato:

```python
logger.{level}(
    f"EVENTO | Campo1: {valor1} | Campo2: {valor2} | Campo3: {valor3}"
)
```

**Ejemplo:**
```python
logger.info(
    f"ARCHIVO SUBIDO | Nombre: {filename} | Tamaño: {file_size}MB | "
    f"Usuario: {user.email} | Proyecto: {project.name} | IP: {client_ip}"
)
```

---

### 2. **Información Esencial por Log**

**SIEMPRE incluir:**
- ✅ Quién (email, user ID)
- ✅ Qué (acción realizada)
- ✅ Cuándo (timestamp automático del logger)
- ✅ Dónde (IP, recurso afectado)

**Opcional según contexto:**
- Organización
- Proyecto
- Archivo
- Motivo del error

---

### 3. **NO Incluir en Logs**

❌ Contraseñas  
❌ Tokens CSRF  
❌ API keys  
❌ Tokens de sesión  
❌ Información de tarjetas de crédito  

**Nota:** Los emails SÍ se incluyen (necesarios para trazabilidad interna)

---

### 4. **Niveles por Tipo de Evento**

| Tipo de Evento | Nivel |
|----------------|-------|
| Creación exitosa de recurso | INFO |
| Modificación exitosa | INFO |
| Eliminación exitosa | WARNING |
| Acceso denegado | WARNING |
| Intento fallido (permisos, validación) | WARNING |
| Error de sistema/BD | ERROR |
| Servicio externo caído | ERROR |
| Superuser/admin action | WARNING |

---

### 5. **Evitar SPAM de Logs**

**NO loguear:**
- ❌ En middlewares que se ejecutan en cada request
- ❌ En loops (loguear resumen al final)
- ❌ Operaciones GET simples (solo POST/PUT/DELETE)
- ❌ Accesos a archivos estáticos

**SÍ loguear:**
- ✅ Operaciones de escritura (CREATE, UPDATE, DELETE)
- ✅ Cambios de estado importantes
- ✅ Eventos de seguridad
- ✅ Errores y excepciones

---

### 6. **Performance**

**Buenas prácticas:**
- Usar f-strings en lugar de concatenación
- No hacer queries adicionales solo para logging
- Usar información ya disponible en el contexto
- Limitar longitud de strings (user-agent a 100 chars, etc.)

**Ejemplo optimizado:**
```python
# ✅ BIEN - Usa datos ya cargados
logger.info(f"PROYECTO CREADO | Nombre: {project.name} | Usuario: {request.user.email}")

# ❌ MAL - Query adicional solo para log
user = User.objects.get(pk=user_id)
logger.info(f"PROYECTO CREADO | Usuario: {user.email}")
```

---

## 💡 Ejemplos de Implementación por Módulo

### Ejemplo 1: Módulo de Archivos

```python
# apps/files/views.py
import logging
from django.utils import timezone

logger = logging.getLogger('apps.files')

class FileUploadView(View):
    def post(self, request):
        try:
            file = request.FILES['file']
            project = Project.objects.get(pk=request.POST['project_id'])
            
            # Validación de tamaño
            if file.size > settings.MAX_FILE_SIZE:
                logger.warning(
                    f"ARCHIVO RECHAZADO | Motivo: Tamaño excedido | "
                    f"Archivo: {file.name} | Tamaño: {file.size / 1024 / 1024:.2f}MB | "
                    f"Usuario: {request.user.email} | Proyecto: {project.name}"
                )
                return JsonResponse({'error': 'Archivo muy grande'}, status=400)
            
            # Upload exitoso
            uploaded_file = FileModel.objects.create(
                file=file,
                project=project,
                uploaded_by=request.user
            )
            
            logger.info(
                f"ARCHIVO SUBIDO | Nombre: {file.name} | "
                f"Tamaño: {file.size / 1024 / 1024:.2f}MB | "
                f"Usuario: {request.user.email} | Proyecto: {project.name} | "
                f"ID: {uploaded_file.pk}"
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            logger.error(
                f"ERROR UPLOAD | Archivo: {file.name if 'file' in locals() else 'N/A'} | "
                f"Usuario: {request.user.email} | Error: {str(e)}"
            )
            return JsonResponse({'error': 'Error interno'}, status=500)


class FileDeleteView(View):
    def post(self, request, file_id):
        try:
            file = FileModel.objects.get(pk=file_id)
            
            # Verificar permisos
            if not file.can_delete(request.user):
                logger.warning(
                    f"ELIMINACIÓN ARCHIVO DENEGADA | Archivo: {file.name} | "
                    f"Usuario: {request.user.email} | Motivo: Sin permisos"
                )
                return JsonResponse({'error': 'Sin permisos'}, status=403)
            
            # Guardar info antes de eliminar
            filename = file.name
            project_name = file.project.name
            
            file.delete()
            
            logger.warning(
                f"ARCHIVO ELIMINADO | Nombre: {filename} | "
                f"Proyecto: {project_name} | Usuario: {request.user.email}"
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            logger.error(
                f"ERROR ELIMINACIÓN ARCHIVO | ID: {file_id} | "
                f"Usuario: {request.user.email} | Error: {str(e)}"
            )
            return JsonResponse({'error': 'Error'}, status=500)
```

---

### Ejemplo 2: Módulo de Proyectos

```python
# apps/projects/views.py
import logging

logger = logging.getLogger('apps.projects')

class ProjectCreateView(View):
    def post(self, request):
        form = ProjectForm(request.POST)
        
        if form.is_valid():
            project = form.save(commit=False)
            project.organization = request.user.organization
            project.created_by = request.user
            project.save()
            
            logger.info(
                f"PROYECTO CREADO | Nombre: {project.name} | "
                f"Org: {project.organization.name} | "
                f"Usuario: {request.user.email} | ID: {project.pk}"
            )
            
            return redirect('project_detail', pk=project.pk)
        else:
            logger.warning(
                f"CREACIÓN PROYECTO FALLIDA | "
                f"Usuario: {request.user.email} | "
                f"Errores: {form.errors.as_text()}"
            )
            return render(request, 'project_form.html', {'form': form})


class ProjectDeleteView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        # Verificar permisos
        if not project.can_delete(request.user):
            logger.warning(
                f"ELIMINACIÓN PROYECTO DENEGADA | Proyecto: {project.name} | "
                f"Usuario: {request.user.email} | Motivo: Sin permisos"
            )
            return HttpResponseForbidden()
        
        project_name = project.name
        org_name = project.organization.name
        
        project.delete()
        
        logger.warning(
            f"PROYECTO ELIMINADO | Nombre: {project_name} | "
            f"Org: {org_name} | Usuario: {request.user.email}"
        )
        
        return redirect('projects_list')
```

---

### Ejemplo 3: Módulo de Organizaciones

```python
# apps/orgs/views.py
import logging

logger = logging.getLogger('apps.orgs')

class ChangePlanView(View):
    def post(self, request):
        org = request.user.organization
        new_plan = Plan.objects.get(pk=request.POST['plan_id'])
        old_plan = org.plan
        
        # Validar downgrade
        if new_plan.tier < old_plan.tier:
            if org.users.count() > new_plan.max_users:
                logger.warning(
                    f"CAMBIO DE PLAN BLOQUEADO | Org: {org.name} | "
                    f"Plan actual: {old_plan.name} | Plan deseado: {new_plan.name} | "
                    f"Motivo: Usuarios exceden límite ({org.users.count()} > {new_plan.max_users})"
                )
                messages.error(request, 'Tienes demasiados usuarios para este plan')
                return redirect('billing')
        
        org.plan = new_plan
        org.save()
        
        logger.warning(
            f"CAMBIO DE PLAN | Org: {org.name} | "
            f"Plan anterior: {old_plan.name} | Plan nuevo: {new_plan.name} | "
            f"Usuario: {request.user.email}"
        )
        
        return redirect('billing')


class InviteUserView(View):
    def post(self, request):
        email = request.POST['email']
        org = request.user.organization
        
        # Verificar límite
        if org.users.count() >= org.plan.max_users:
            logger.warning(
                f"INVITACIÓN BLOQUEADA | Org: {org.name} | "
                f"Email invitado: {email} | "
                f"Motivo: Límite de usuarios alcanzado ({org.users.count()}/{org.plan.max_users})"
            )
            messages.error(request, 'Has alcanzado el límite de usuarios de tu plan')
            return redirect('team')
        
        # Crear invitación
        invitation = Invitation.objects.create(
            organization=org,
            email=email,
            invited_by=request.user
        )
        
        logger.info(
            f"USUARIO INVITADO | Org: {org.name} | "
            f"Email: {email} | Invitado por: {request.user.email}"
        )
        
        # Enviar email...
        
        return redirect('team')
```

---

## 🔍 Monitoreo y Análisis

### Queries Útiles en Sentry/CloudWatch

**Detectar ataques de fuerza bruta:**
```
level:WARNING message:"LOGIN FALLIDO" 
| stats count by email, ip 
| where count > 5
```

**Monitorear accesos de superuser:**
```
level:WARNING message:"SUPERUSER LOGIN"
| stats count by email
```

**Archivos rechazados por tamaño:**
```
level:WARNING message:"ARCHIVO RECHAZADO" motivo:"Tamaño excedido"
| stats sum(size) by user
```

**Cambios de plan:**
```
level:WARNING message:"CAMBIO DE PLAN"
| stats count by plan_anterior, plan_nuevo
```

---

## ✅ Checklist de Implementación por Módulo

Para cada módulo nuevo:

- [ ] Crear logger: `logger = logging.getLogger('apps.{module_name}')`
- [ ] Identificar operaciones críticas (CREATE, UPDATE, DELETE)
- [ ] Implementar logs en form_valid/form_invalid
- [ ] Logs de seguridad (acceso denegado, permisos)
- [ ] Logs de errores (try/except con contexto)
- [ ] Validar que no genere spam (evitar loops, middlewares)
- [ ] Testing: Verificar que logs se generen correctamente
- [ ] Documentar en este archivo qué se loguea

---

## 🎓 Conclusión

El sistema de logging está diseñado para:
1. **Seguridad**: Detectar accesos no autorizados, ataques
2. **Auditoría**: Compliance (GDPR, SOC2, ISO 27001)
3. **Debugging**: Identificar errores rápidamente
4. **Analytics**: Entender uso de la plataforma
5. **Performance**: Sin impacto significativo en rendimiento

**Regla de oro:** Si una operación modifica datos o es sensible para seguridad, debe loguearse.
