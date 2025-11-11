# apps/orgs/models.py - Versión simplificada
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.core.cache import cache

class Organization(models.Model):
    """Modelo simplificado de organización"""
    
    name = models.CharField(
        "Nombre de la organización", 
        max_length=100, 
        db_index=True,
        help_text="Máximo 100 caracteres"
    )
    description = models.TextField("Descripción", blank=True, null=True)
    is_active = models.BooleanField("Activa", default=True, db_index=True)
    
    # Almacenamiento extra más allá del límite del plan
    extra_storage_gb = models.IntegerField(
        "Almacenamiento extra (GB)", 
        default=0, 
        help_text="GB adicionales. Puede ser positivo (más almacenamiento) o negativo (reducir del plan base)."
    )
    
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    
    # Campos para gestión de miembros fundadores
    is_founder_member = models.BooleanField(
        "Miembro fundador", 
        default=False,
        help_text="Indica si la organización tiene membresía fundadora"
    )
    founder_joined_date = models.DateTimeField(
        "Fecha de ingreso como fundador", 
        blank=True, 
        null=True,
        help_text="Fecha en la que se unió como miembro fundador"
    )
    founder_discount_percentage = models.DecimalField(
        "Descuento fundador (%)",
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de descuento en renovaciones para miembros fundadores (ej: 20.00 para 20%)"
    )
    
    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_founder_price(self, original_price=None):
        """
        Retorna el precio para miembros fundadores.
        Miembros fundadores pagan $199/mes en lugar de $299/mes (plan básico).
        """
        if self.is_founder_member:
            return 199  # Precio fijo para fundadores
        return original_price if original_price is not None else 299
    
    @cached_property
    def subscription_cached(self):
        """Retorna la suscripción actual de la organización, cacheada por instancia."""
        try:
            # La relación OneToOne desde Subscription nos da acceso a 'subscription'
            return self.subscription
        except self.subscription.RelatedObjectDoesNotExist:
            # Si no existe, creamos una de prueba.
            return self._create_default_subscription()

    def get_subscription(self):
        """Método de conveniencia para acceder a la propiedad cacheada."""
        return self.subscription_cached
    
    def get_total_storage_limit_gb(self):
        """
        Retorna el límite total de almacenamiento (plan + extras).
        Garantiza que el valor nunca sea negativo.
        """
        plan_limit = 0
        if hasattr(self, 'subscription') and self.subscription:
            plan_limit = self.subscription.plan.max_storage_gb
        else:
            # Fallback para organizaciones sin suscripción
            plan_limit = 10
        
        total = plan_limit + self.extra_storage_gb
        # BUG FIX: Prevenir almacenamiento total negativo
        return max(0, total)
    
    def _create_default_subscription(self):
        """Crea suscripción trial por defecto para nuevas organizaciones"""
        from apps.plans.models import Plan, Subscription
        
        try:
            trial_plan = Plan.objects.get(name='trial', is_active=True)
            subscription = Subscription.objects.create(
                organization=self,
                plan=trial_plan
            )
            return subscription
        except Plan.DoesNotExist:
            return None
    
    def get_max_users(self):
        """Retorna el límite de usuarios basado en el plan"""
        subscription = self.get_subscription()
        return subscription.plan.max_users if subscription else 1
    
    def get_user_count(self):
        """Retorna el total de usuarios (con cache)"""
        cache_key = f"org_user_count:{self.id}"
        count = cache.get(cache_key)
        if count is None:
            count = self.users.count()
            cache.set(cache_key, count, 300)  # 5 minutos
        return count
    
    def get_active_user_count(self):
        """Retorna solo usuarios activos (con cache)"""
        cache_key = f"org_active_users:{self.id}"
        count = cache.get(cache_key)
        if count is None:
            count = self.users.filter(is_active=True).count()
            cache.set(cache_key, count, 300)  # 5 minutos
        return count
    
    def get_inactive_user_count(self):
        """Retorna usuarios inactivos (con cache)"""
        cache_key = f"org_inactive_users:{self.id}"
        count = cache.get(cache_key)
        if count is None:
            count = self.users.filter(is_active=False).count()
            cache.set(cache_key, count, 300)  # 5 minutos
        return count
    
    def can_add_user(self):
        """Verifica si se puede agregar un usuario"""
        return self.get_user_count() < self.get_max_users()
    
    def can_add_user_detailed(self):
        """Información detallada sobre capacidad de usuarios"""
        active_count = self.get_active_user_count()
        inactive_count = self.get_inactive_user_count()
        total_count = self.get_user_count()
        max_users = self.get_max_users()
        
        return {
            'can_add': total_count < max_users,
            'active_users': active_count,
            'inactive_users': inactive_count,
            'total_users': total_count,
            'max_users': max_users,
            'available_slots': max(0, max_users - total_count),
            'is_at_limit': total_count >= max_users,
            'has_inactive_users': inactive_count > 0
        }
    
    @property
    def is_trial(self):
        """Verifica si está en período de trial"""
        try:
            subscription = self.subscription
            return subscription and subscription.plan.is_trial and subscription.is_active
        except:
            return False
    
    def trial_days_remaining(self):
        """Días restantes de trial"""
        try:
            subscription = self.subscription
            if subscription and subscription.plan.is_trial and subscription.is_active:
                return subscription.trial_days_remaining
            return 0
        except:
            return 0
    
    def invalidate_user_cache(self):
        """Invalida el cache de contadores de usuarios cuando se agregan/quitan usuarios"""
        cache_keys = [
            f"org_user_count:{self.id}",
            f"org_active_users:{self.id}",
            f"org_inactive_users:{self.id}",
            f"org_subscription:{self.id}",
            f"dashboard_stats:{self.id}"
        ]
        cache.delete_many(cache_keys)
    
    def invalidate_storage_cache(self):
        """Invalida el cache de almacenamiento cuando se modifica el límite"""
        from apps.orgs.storage_service import StorageService
        StorageService.invalidate_cache(self.id)
    
    def save(self, *args, **kwargs):
        """Override del save para invalidar cache"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Rastrear si cambió extra_storage_gb para invalidar cache
        should_invalidate_storage = False
        if self.pk:
            try:
                old_instance = Organization.objects.get(pk=self.pk)
                if old_instance.extra_storage_gb != self.extra_storage_gb:
                    should_invalidate_storage = True
            except Organization.DoesNotExist:
                pass
        
        # Guardar
        super().save(*args, **kwargs)
        
        # Invalidar cache si cambió extra_storage_gb
        if should_invalidate_storage:
            self.invalidate_storage_cache()
    
    def delete(self, *args, **kwargs):
        """
        Override del delete para limpiar archivos de R2/S3 antes de eliminar la organización.
        El logging se maneja en el admin para tener contexto del usuario.
        """
        # 1. Limpiar archivos de R2/S3 (silenciosamente)
        self._cleanup_r2_files()
        
        # 2. Invalidar todos los caches relacionados
        self.invalidate_user_cache()
        self.invalidate_storage_cache()
        
        # 3. Eliminar la organización (cascada eliminará proyectos, fases, archivos DB, etc.)
        super().delete(*args, **kwargs)
    
    def _cleanup_r2_files(self):
        """
        Elimina todos los archivos de R2/S3 de esta organización.
        Retorna el número de archivos eliminados.
        Solo loggea errores críticos, no eventos de éxito (para evitar ruido).
        """
        import logging
        import os
        from django.conf import settings
        
        logger = logging.getLogger(__name__)
        
        # Verificar si R2/S3 está habilitado
        if os.environ.get('ENABLE_STORAGES', 'false').lower() != 'true':
            logger.debug(f"R2/S3 no habilitado para org {self.id}")
            return 0
        
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            logger.warning("boto3 no disponible, no se pueden limpiar archivos de R2")
            return 0
        
        try:
            # Obtener cliente S3/R2
            from core.r2_config import get_optimized_r2_client
            s3_client = get_optimized_r2_client()
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            
            # Prefijo de la organización en R2
            org_prefix = f'organizations/{self.id}/'
            
            logger.debug(f"Limpiando archivos de R2 para org {self.id} (prefix: {org_prefix})")
            
            files_deleted = 0
            files_to_delete = []
            
            # Listar todos los objetos con el prefijo de esta organización
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=org_prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                # Recolectar archivos para eliminación en lote
                for obj in page['Contents']:
                    files_to_delete.append({'Key': obj['Key']})
                    
                    # Eliminar en lotes de 1000 (límite de S3 delete_objects)
                    if len(files_to_delete) >= 1000:
                        response = s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': files_to_delete}
                        )
                        files_deleted += len(response.get('Deleted', []))
                        
                        # Log de errores si los hay
                        if 'Errors' in response:
                            for error in response['Errors']:
                                logger.error(f"Error eliminando {error['Key']}: {error['Message']}")
                        
                        files_to_delete = []
            
            # Eliminar archivos restantes
            if files_to_delete:
                response = s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': files_to_delete}
                )
                files_deleted += len(response.get('Deleted', []))
                
                if 'Errors' in response:
                    for error in response['Errors']:
                        logger.error(f"Error eliminando {error['Key']}: {error['Message']}")
            
            # Solo log DEBUG para éxito (no INFO para evitar ruido)
            if files_deleted > 0:
                logger.debug(f"Eliminados {files_deleted} archivos de R2 para org {self.id}")
            
            return files_deleted
            
        except Exception as e:
            # Log de error crítico
            from core.structured_logging import log_error
            log_error(
                event='ORGANIZATION_R2_CLEANUP_ERROR',
                error_code='ORG_R2_001',
                error_message=str(e),
                logger_name='apps.orgs',
                organization_id=self.id,
                organization_name=self.name
            )
            logger.error(f"Error limpiando archivos de R2 para org {self.id}: {e}")
            return 0
    
    def get_admins(self):
        """Retorna usuarios administradores"""
        return self.users.filter(is_org_admin=True)
    
    @property
    def plan(self):
        """Retorna el plan actual de la organización"""
        subscription = self.get_subscription()
        return subscription.plan if subscription else None
    
    def get_subscription_status(self):
        """Retorna el estado de la suscripción"""
        if hasattr(self, 'subscription'):
            return self.subscription.status
        return 'no_subscription'
    
    def is_subscription_active(self):
        """Verifica si la suscripción está activa"""
        if hasattr(self, 'subscription'):
            return self.subscription.is_active
        return False
    
    def get_current_plan(self):
        """Retorna el plan actual de la organización"""
        if hasattr(self, 'subscription'):
            return self.subscription.plan
        return None
    
    def can_create_user_with_subscription(self):
        """Verifica si puede crear usuarios considerando la suscripción"""
        if not self.is_subscription_active():
            return {
                'can_create': False,
                'reason': 'Suscripción inactiva o expirada',
                'subscription_required': True
            }
        
        current_plan = self.get_current_plan()
        if not current_plan:
            return {
                'can_create': False,
                'reason': 'No hay plan asignado',
                'subscription_required': True
            }
        
        current_count = self.get_user_count()
        can_create = current_count < current_plan.max_users
        
        return {
            'can_create': can_create,
            'reason': 'Límite de usuarios alcanzado' if not can_create else 'OK',
            'current_count': current_count,
            'limit': current_plan.max_users,
            'subscription_required': False
        }
    
    def get_subscription_limits(self):
        """Retorna todos los límites de la suscripción actual"""
        if not hasattr(self, 'subscription') or not self.subscription.is_active:
            return {
                'users': {'current': 0, 'limit': 0, 'available': 0},
                'projects': {'current': 0, 'limit': 0, 'available': 0},
                'storage_gb': {'current': 0, 'limit': 0, 'available': 0},
                'subscription_active': False
            }
        
        plan = self.subscription.plan
        user_count = self.get_user_count()
        
        # TODO: Implementar cuando tengas los módulos de proyectos y almacenamiento
        project_count = 0  # self.projects.count() when implemented
        storage_used = 0   # self.get_storage_usage() when implemented
        
        return {
            'users': {
                'current': user_count,
                'limit': plan.max_users,
                'available': max(0, plan.max_users - user_count),
                'usage_percentage': plan.get_usage_percentage(user_count, 'users')
            },
            'projects': {
                'current': 0,
                'limit': 0,
                'available': 0,
                'usage_percentage': 0
            },
            'storage_gb': {
                'current': 0,
                'limit': 0,
                'available': 0,
                'usage_percentage': 0
            },
            'subscription_active': True
        }
    
    def get_subscription_warning_level(self):
        """Retorna el nivel de advertencia de la suscripción"""
        if not hasattr(self, 'subscription'):
            return 'error'  # No subscription
        
        subscription = self.subscription
        
        if not subscription.is_active:
            return 'error'  # Inactive subscription
        
        days_remaining = subscription.days_remaining
        
        if days_remaining <= 3:
            return 'critical'  # Critical - expires in 3 days or less
        elif days_remaining <= 7:
            return 'warning'   # Warning - expires in 7 days or less
        elif days_remaining <= 14:
            return 'info'      # Info - expires in 14 days or less
        else:
            return 'success'   # All good
    
    def get_next_billing_info(self):
        """Retorna información de la próxima facturación"""
        if not hasattr(self, 'subscription'):
            return None
        
        subscription = self.subscription
        plan = subscription.plan
        
        return {
            'next_billing_date': subscription.next_billing_date,
            'amount': plan.price,
            'currency': plan.currency,
            'billing_cycle': plan.get_billing_cycle_display(),
            'days_until_billing': subscription.days_remaining,
            'auto_renew': subscription.auto_renew
        }
    
    def calculate_upgrade_cost(self, new_plan):
        """Calcula el costo de upgrade a un nuevo plan (para implementación futura)"""
        if not hasattr(self, 'subscription'):
            return None
        
        current_plan = self.subscription.plan
        
        if new_plan.price <= current_plan.price:
            return {
                'is_upgrade': False,
                'cost': 0,
                'reason': 'El nuevo plan no es superior al actual'
            }
        
        # Cálculo básico para MVP (sin prorrateo)
        cost_difference = new_plan.price - current_plan.price
        
        return {
            'is_upgrade': True,
            'cost': cost_difference,
            'currency': new_plan.currency,
            'billing_cycle': new_plan.billing_cycle,
            'effective_date': 'immediate',  # Para MVP
            'proration': 0  # No implementado en MVP
        }
    
    # Método actualizado para compatibilidad con el sistema anterior
    def can_add_user(self):
        """Método de compatibilidad que considera suscripciones"""
        # Primero verificar límites de suscripción
        subscription_check = self.can_create_user_with_subscription()
        if subscription_check['subscription_required']:
            return False
        
        if not subscription_check['can_create']:
            return False
        
        # Si la suscripción permite, verificar límites legacy
        return super().can_add_user() if hasattr(super(), 'can_add_user') else True
    
    def can_add_user_detailed(self):
        """
        Método detallado que considera suscripciones.
        IMPORTANTE: Siempre retorna la misma estructura de dict para evitar KeyError en el frontend.
        """
        # Obtener contadores de usuarios (siempre necesarios)
        current_users = self.get_user_count()
        active_users = self.get_active_user_count()
        inactive_users = self.get_inactive_user_count()
        
        # Verificar suscripción
        subscription_check = self.can_create_user_with_subscription()
        
        # Obtener límites del plan
        plan = self.get_current_plan()
        max_users = plan.max_users if plan else 0
        available_slots = max(0, max_users - current_users)
        
        # Determinar si puede agregar usuarios
        can_add = subscription_check['can_create'] if not subscription_check.get('subscription_required') else False
        
        # BUG FIX: Estructura SIEMPRE consistente, independientemente del estado de subscription
        return {
            'can_add': can_add,
            'reason': subscription_check['reason'],
            'subscription_issue': subscription_check.get('subscription_required', False),
            'current_users': current_users,
            'max_users': max_users,
            'available_slots': available_slots,
            # Claves que faltaban cuando no había subscription:
            'active_users': active_users,
            'inactive_users': inactive_users,
            'total_users': current_users,
            'has_inactive_users': inactive_users > 0,
            'is_at_limit': current_users >= max_users if max_users > 0 else True
        }

class Client(models.Model):
    """Modelo para gestionar clientes dentro de una organización."""
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name="Organización"
    )
    name = models.CharField(
        "Nombre del cliente", 
        max_length=100,
        help_text="Máximo 100 caracteres"
    )
    email = models.EmailField(
        "Correo electrónico", 
        max_length=254, 
        blank=True, 
        null=True,
        help_text="Email de contacto del cliente"
    )
    phone_number = models.CharField(
        "Teléfono", 
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Formato: +52 123 456 7890 o 1234567890"
    )
    address = models.TextField("Dirección", blank=True, null=True)
    
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['name']
        unique_together = ('organization', 'name')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override de save - el logging se maneja en el admin"""
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override de delete - el logging se maneja en el admin"""
        super().delete(*args, **kwargs)
