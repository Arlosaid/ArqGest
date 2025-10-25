"""
Ejemplos de migración de logging antiguo a logging estructurado.
Úsalos como referencia para actualizar otros archivos.
"""

# ============================================================================
# EJEMPLO 1: Errores Simples
# ============================================================================

# ❌ ANTES
import logging
logger = logging.getLogger(__name__)

try:
    # ... código ...
    pass
except Exception as e:
    logger.error(f"Error al procesar archivo {filename}: {str(e)}")


# ✅ AHORA
from core.structured_logging import log_error

try:
    # ... código ...
    pass
except Exception as e:
    log_error(
        event="file_processing_failed",
        error_code="FILE001",
        error_message=str(e),
        filename=filename,
        file_size=size if 'size' in locals() else None
    )


# ============================================================================
# EJEMPLO 2: Warnings
# ============================================================================

# ❌ ANTES
logger.warning(f"Suscripción {subscription.id} expira en {days} días")


# ✅ AHORA
from core.structured_logging import log_warning

log_warning(
    event="subscription_near_expiry",
    message="Suscripción próxima a expirar",
    subscription_id=subscription.id,
    days_remaining=days,
    organization_id=subscription.organization_id
)


# ============================================================================
# EJEMPLO 3: Info Logs (Solo en DEBUG o eventos importantes)
# ============================================================================

# ❌ ANTES (logueaba TODO)
logger.info(f"Usuario {user.email} guardado exitosamente")
logger.info(f"Proyecto {project.name} actualizado")
logger.info(f"Archivo {file.name} subido")


# ✅ AHORA (solo eventos de negocio importantes)
from core.structured_logging import log_business_event
from django.conf import settings

# Solo loguear creación de usuarios en producción (auditoría)
if not settings.DEBUG:
    log_business_event(
        event="user_created",
        action="created",
        entity_type="user",
        entity_id=user.id,
        outcome="success"
    )

# Para operaciones rutinarias, NO loguear en producción
# Solo en desarrollo si es necesario para debugging


# ============================================================================
# EJEMPLO 4: Eventos de Negocio Críticos
# ============================================================================

# ❌ ANTES
logger.info(f"Organización {org.name} creada por usuario {user.email}")
logger.info(f"Plan actualizado de {old_plan} a {new_plan}")
logger.info(f"Pago recibido: ${amount} MXN")


# ✅ AHORA
from core.structured_logging import log_business_event

# Creación de organización (siempre loguear - auditoría)
log_business_event(
    event="organization_created",
    action="created",
    entity_type="organization",
    entity_id=org.id,
    organization_name=org.name,  # Se anonimizará si contiene email
    created_by_user_id=user.id,
    outcome="success"
)

# Cambio de plan (siempre loguear - auditoría financiera)
log_business_event(
    event="subscription_plan_changed",
    action="updated",
    entity_type="subscription",
    entity_id=subscription.id,
    old_plan=old_plan.name,
    new_plan=new_plan.name,
    organization_id=org.id,
    outcome="success"
)

# Pago recibido (siempre loguear - auditoría financiera)
log_business_event(
    event="payment_received",
    action="created",
    entity_type="payment",
    entity_id=payment.id,
    amount=float(amount),
    currency="MXN",
    organization_id=org.id,
    subscription_id=subscription.id,
    outcome="success"
)


# ============================================================================
# EJEMPLO 5: Operaciones Lentas / Performance
# ============================================================================

# ❌ ANTES
import time
start = time.time()
# ... operación costosa ...
duration = time.time() - start
if duration > 2:
    logger.warning(f"Operación lenta: {operation_name} tomó {duration:.2f}s")


# ✅ AHORA
import time
from core.structured_logging import log_slow_operation

start = time.perf_counter()
# ... operación costosa ...
duration_ms = (time.perf_counter() - start) * 1000

# Se loguea automáticamente solo si supera threshold
log_slow_operation(
    operation="file_upload_to_r2",
    duration_ms=duration_ms,
    threshold_ms=2000,  # 2 segundos
    file_size_mb=file_size / (1024**2),
    file_type=file_type
)


# ============================================================================
# EJEMPLO 6: Eventos de Seguridad
# ============================================================================

# ❌ ANTES
logger.warning(f"Intento de login fallido para {username} desde {ip}")
logger.error(f"Acceso denegado: usuario {user.id} intentó acceder a org {org.id}")


# ✅ AHORA
from core.structured_logging import log_security_event

# Login fallido
log_security_event(
    event="failed_login_attempt",
    severity="medium",
    ip_address=request.META.get('REMOTE_ADDR'),  # Se anonimizará automáticamente
    username=username,  # NO uses email aquí
    attempts_count=failed_attempts
)

# Violación de permisos
log_security_event(
    event="permission_violation",
    severity="high",
    user_id=user.id,
    attempted_resource_type="organization",
    attempted_resource_id=org.id,
    ip_address=request.META.get('REMOTE_ADDR')
)


# ============================================================================
# EJEMPLO 7: Logging en Models.py
# ============================================================================

# ❌ ANTES
class MyModel(models.Model):
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        try:
            super().save(*args, **kwargs)
            
            if is_new:
                logger.info(f"Nuevo {self.__class__.__name__} creado: {self.name}")
            else:
                logger.info(f"{self.__class__.__name__} actualizado: {self.name}")
                
        except Exception as e:
            logger.error(f"Error al guardar {self.__class__.__name__}: {str(e)}")
            raise


# ✅ AHORA
from core.structured_logging import log_business_event, log_error
from django.conf import settings

class MyModel(models.Model):
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        try:
            super().save(*args, **kwargs)
            
            # Solo loguear en producción para auditoría (no en cada guardado en dev)
            if not settings.DEBUG:
                if is_new:
                    log_business_event(
                        event=f"{self.__class__.__name__.lower()}_created",
                        action="created",
                        entity_type=self.__class__.__name__.lower(),
                        entity_id=self.pk,
                        outcome="success"
                    )
                # Para updates, solo loguear cambios críticos (no cada update)
                
        except Exception as e:
            log_error(
                event=f"{self.__class__.__name__.lower()}_save_failed",
                error_code=f"{self.__class__.__name__.upper()}001",
                error_message=str(e),
                entity_id=self.pk if self.pk else None
            )
            raise


# ============================================================================
# EJEMPLO 8: Logging en Views
# ============================================================================

# ❌ ANTES
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def my_view(request):
    try:
        # ... código ...
        logger.info(f"Vista procesada exitosamente para user {request.user.email}")
        return render(request, 'template.html')
    except Exception as e:
        logger.error(f"Error en vista: {str(e)}")
        raise


# ✅ AHORA
from django.shortcuts import render
from core.structured_logging import log_error

def my_view(request):
    try:
        # ... código ...
        # NO loguear vistas exitosas (ruido innecesario)
        return render(request, 'template.html')
    except Exception as e:
        # Solo loguear errores
        log_error(
            event="view_processing_failed",
            error_code="VIEW001",
            error_message=str(e),
            view_name=my_view.__name__,
            user_id=request.user.id if request.user.is_authenticated else None
        )
        raise


# ============================================================================
# EJEMPLO 9: Logging Condicional (Solo en DEBUG)
# ============================================================================

# ❌ ANTES
logger.debug(f"Processing item {item.id}")
logger.debug(f"Step 1: validating...")
logger.debug(f"Step 2: saving...")


# ✅ AHORA
from django.conf import settings
from core.structured_logging import log_info

# Solo loguear pasos intermedios en desarrollo
if settings.DEBUG:
    log_info(
        event="processing_step",
        step="validation",
        item_id=item.id
    )


# ============================================================================
# EJEMPLO 10: Logging de Cambios con Comparación
# ============================================================================

# ❌ ANTES
class User(models.Model):
    def save(self, *args, **kwargs):
        if self.pk:
            old_user = User.objects.get(pk=self.pk)
            if old_user.email != self.email:
                logger.info(f"Email changed from {old_user.email} to {self.email}")
            if old_user.is_active != self.is_active:
                status = 'activated' if self.is_active else 'deactivated'
                logger.info(f"User {self.email} {status}")
        
        super().save(*args, **kwargs)


# ✅ AHORA
from core.structured_logging import log_business_event
from django.conf import settings

class User(models.Model):
    def save(self, *args, **kwargs):
        critical_changes = []
        
        if self.pk:
            old_user = User.objects.get(pk=self.pk)
            
            # Solo capturar cambios críticos
            if old_user.is_active != self.is_active:
                critical_changes.append(('status', 'activated' if self.is_active else 'deactivated'))
            
            if old_user.email != self.email:
                critical_changes.append(('email', 'changed'))
        
        super().save(*args, **kwargs)
        
        # Solo loguear si hay cambios críticos y estamos en producción
        if critical_changes and not settings.DEBUG:
            log_business_event(
                event="user_critical_change",
                action="updated",
                entity_type="user",
                entity_id=self.pk,
                changes=str(critical_changes),
                outcome="success"
            )


# ============================================================================
# REGLAS DE ORO PARA MIGRACIÓN
# ============================================================================

"""
1. ❌ NO loguear:
   - Requests a archivos estáticos
   - Operaciones exitosas rutinarias
   - Cada paso de un proceso (solo inicio/fin/errores)
   - Datos sensibles sin anonimizar

2. ✅ SÍ loguear:
   - Errores con código único
   - Eventos de negocio importantes (auditoría)
   - Violaciones de seguridad
   - Operaciones lentas (>2s)

3. 🎯 Usar el nivel correcto:
   - ERROR: Excepciones, fallos
   - WARNING: Operaciones sospechosas, límites cercanos
   - INFO: Solo eventos de negocio en producción
   - DEBUG: Solo en desarrollo

4. 📊 Siempre incluir contexto:
   - error_code único
   - entity_id relevante
   - organization_id cuando aplique
   - user_id cuando aplique

5. 🔐 Privacidad:
   - Los emails se anonimizan automáticamente
   - Las IPs se anonimizan automáticamente
   - Passwords/tokens se filtran automáticamente
   - NO necesitas hacer nada especial
"""
