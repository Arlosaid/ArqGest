# apps/plans/models.py
from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
import logging

class Plan(models.Model):
    """
    Modelo simplificado para definir los planes de la aplicación para el MVP.
    """
    PLAN_TYPES = [
        ('trial', 'Prueba Gratuita'),
        ('basic', 'Plan Básico'),
    ]
    
    # Información básica
    name = models.CharField("Nombre del plan", max_length=50, choices=PLAN_TYPES, unique=True)
    display_name = models.CharField("Nombre para mostrar", max_length=100)
    description = models.TextField("Descripción", blank=True)
    
    # Configuración de precios
    price = models.DecimalField("Precio", max_digits=10, decimal_places=2, default=0)
    
    # Límites del plan para el MVP
    max_users = models.PositiveIntegerField("Máximo de usuarios", default=1)
    max_storage_gb = models.PositiveIntegerField("Límite de almacenamiento (GB)", default=10, help_text="Límite de almacenamiento en gigabytes")
    
    # Características adicionales
    trial_days = models.PositiveIntegerField("Días de prueba", default=0, help_text="Para planes 'trial', establece la duración de la prueba.")
    billing_cycle_days = models.PositiveIntegerField("Días del ciclo de facturación", default=30, help_text="Duración estándar del ciclo de pago en días.")
    grace_period_days = models.PositiveIntegerField("Días de gracia", default=0, help_text="Días de gracia después de la expiración antes de restringir el acceso.")
    
    # Estado y configuración
    is_active = models.BooleanField("Activo", default=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    
    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ['price']
    
    def __str__(self):
        return self.display_name
    
    def save(self, *args, **kwargs):
        """Override de save para logging estructurado"""
        from core.structured_logging import log_business_event
        import logging
        logger = logging.getLogger(__name__)
        
        is_new = self.pk is None
        changed_fields = []
        
        # Rastrear cambios críticos si es actualización
        if self.pk:
            try:
                old_instance = Plan.objects.get(pk=self.pk)
                
                if old_instance.price != self.price:
                    changed_fields.append({
                        'field': 'price',
                        'field_label': 'Precio',
                        'old': str(old_instance.price),
                        'new': str(self.price)
                    })
                
                if old_instance.max_users != self.max_users:
                    changed_fields.append({
                        'field': 'max_users',
                        'field_label': 'Máximo de usuarios',
                        'old': old_instance.max_users,
                        'new': self.max_users
                    })
                
                if old_instance.max_storage_gb != self.max_storage_gb:
                    changed_fields.append({
                        'field': 'max_storage_gb',
                        'field_label': 'Almacenamiento máximo',
                        'old': old_instance.max_storage_gb,
                        'new': self.max_storage_gb
                    })
                
                if old_instance.is_active != self.is_active:
                    changed_fields.append({
                        'field': 'is_active',
                        'field_label': 'Estado activo',
                        'old': old_instance.is_active,
                        'new': self.is_active
                    })
                
                if old_instance.trial_days != self.trial_days:
                    changed_fields.append({
                        'field': 'trial_days',
                        'field_label': 'Días de prueba',
                        'old': old_instance.trial_days,
                        'new': self.trial_days
                    })
                
            except Plan.DoesNotExist:
                pass
        
        # Guardar
        super().save(*args, **kwargs)
        
        # Invalidar caches si cambiaron límites críticos
        if not is_new and changed_fields:
            storage_changed = any(c['field'] == 'max_storage_gb' for c in changed_fields)
            users_changed = any(c['field'] == 'max_users' for c in changed_fields)
            
            if storage_changed or users_changed:
                # Invalidar caches de todas las organizaciones afectadas
                # Usamos iterator() para evitar cargar todos los objetos en memoria si son muchos
                for sub in self.subscription_set.select_related('organization').iterator():
                    if storage_changed:
                        sub.organization.invalidate_storage_cache()
                    if users_changed:
                        sub.organization.invalidate_user_cache()

        # Logging de negocio
        if is_new:
            log_business_event(
                event='plan_created',
                action='created',
                entity_type='plan',
                entity_id=self.id,
                outcome='success',
                logger_name='apps.plans',
                plan_name=self.display_name,
                plan_type=self.name,
                price=str(self.price),
                max_users=self.max_users,
                max_storage_gb=self.max_storage_gb,
                trial_days=self.trial_days,
                is_active=self.is_active
            )
        elif changed_fields:
            log_business_event(
                event='plan_updated',
                action='updated',
                entity_type='plan',
                entity_id=self.id,
                outcome='success',
                logger_name='apps.plans',
                plan_name=self.display_name,
                plan_type=self.name,
                changes=changed_fields
            )
    
    def get_feature_list(self):
        """Retorna las características del plan como una lista simple."""
        features = [f"Hasta {self.max_users} usuario{'s' if self.max_users != 1 else ''}"]
        if self.max_storage_gb:
            features.append(f"{self.max_storage_gb} GB de almacenamiento")
        return features

    @property
    def is_trial(self):
        return self.name == 'trial'

    # Métodos de clase para obtener planes comunes
    @classmethod
    def get_trial_plan(cls):
        try:
            return cls.objects.get(name='trial', is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_basic_plan(cls):
        try:
            return cls.objects.get(name='basic', is_active=True)
        except cls.DoesNotExist:
            return None

    def get_usage_percentage(self, current_value, limit_type):
        """Calcula el porcentaje de uso para un límite específico de forma simple."""
        limit = 0
        if limit_type == 'users':
            limit = self.max_users
        
        if not limit or limit == 0:
            return 100 if current_value > 0 else 0
        
        percentage = (current_value / limit) * 100
        return min(100, round(percentage))


class Subscription(models.Model):
    """
    Modelo simplificado para gestionar las suscripciones de las organizaciones.
    """
    SUBSCRIPTION_STATUS_CHOICES = [
        ('trial_active', 'Trial Activo'),
        ('trial_expired', 'Trial Expirado'),
        ('basic_active', 'Plan Básico Activo'),
        ('basic_grace', 'Plan Básico en Gracia'),
        ('basic_expired', 'Plan Básico Expirado'),
    ]
    
    organization = models.OneToOneField('orgs.Organization', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, verbose_name="Plan Actual")
    
    start_date = models.DateTimeField("Fecha de inicio", default=timezone.now)
    end_date = models.DateTimeField("Fecha de vencimiento", null=True, blank=True, db_index=True)
    grace_end_date = models.DateTimeField("Fin del período de gracia", null=True, blank=True)
    
    subscription_status = models.CharField("Estado de Suscripción", max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='trial_active', db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} - {self.plan.display_name}"

    def save(self, *args, **kwargs):
        from core.structured_logging import log_business_event
        from django.core.cache import cache
        import logging
        logger = logging.getLogger(__name__)
        
        is_new = not self.pk
        changed_fields = []
        plan_changed = False
        
        # Rastrear cambios si es actualización
        if self.pk:
            try:
                old_instance = Subscription.objects.get(pk=self.pk)
                
                if old_instance.plan_id != self.plan_id:
                    plan_changed = True
                    changed_fields.append({
                        'field': 'plan',
                        'field_label': 'Plan',
                        'old': old_instance.plan.display_name,
                        'new': self.plan.display_name
                    })
                
                if old_instance.subscription_status != self.subscription_status:
                    changed_fields.append({
                        'field': 'subscription_status',
                        'field_label': 'Estado de suscripción',
                        'old': old_instance.subscription_status,
                        'new': self.subscription_status
                    })
                
                if old_instance.end_date != self.end_date:
                    changed_fields.append({
                        'field': 'end_date',
                        'field_label': 'Fecha de vencimiento',
                        'old': str(old_instance.end_date),
                        'new': str(self.end_date)
                    })
                
            except Subscription.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Invalidar caches si cambió el plan o es nueva suscripción
        # Esto asegura que el dashboard muestre los límites correctos inmediatamente
        if is_new or plan_changed:
            self.organization.invalidate_storage_cache()
            # También invalidar cache de suscripción y dashboard
            cache_keys = [
                f"org_subscription:{self.organization.id}",
                f"dashboard_stats:{self.organization.id}"
            ]
            cache.delete_many(cache_keys)
        
        if is_new:
            self.setup_initial_subscription(self.plan)
            self.save(update_fields=['start_date', 'end_date', 'subscription_status'])
            
            log_business_event(
                event='subscription_created',
                action='created',
                entity_type='subscription',
                entity_id=self.id,
                outcome='success',
                logger_name='apps.plans',
                organization_id=self.organization.id,
                organization_name=self.organization.name,
                plan_name=self.plan.display_name,
                plan_type=self.plan.name,
                start_date=str(self.start_date),
                end_date=str(self.end_date),
                status=self.subscription_status
            )
        elif changed_fields:
            log_business_event(
                event='subscription_updated',
                action='updated',
                entity_type='subscription',
                entity_id=self.id,
                outcome='success',
                logger_name='apps.plans',
                organization_id=self.organization.id,
                organization_name=self.organization.name,
                plan_name=self.plan.display_name,
                changes=changed_fields
            )

    def setup_initial_subscription(self, plan):
        """Configura las fechas y el estado inicial de la suscripción."""
        now = timezone.now()
        self.start_date = now
        days = plan.trial_days if plan.is_trial else plan.billing_cycle_days
        self.end_date = now + timedelta(days=days)
        self.subscription_status = f'{plan.name}_active'

    def calculate_current_status(self):
        """
        Calcula el estado de la suscripción basado en las fechas, sin modificar el estado.
        
        IMPORTANTE: Compara solo fechas (sin hora) para que la suscripción
        sea válida todo el día de expiración hasta las 23:59:59.
        Ejemplo: Si end_date es 5 dic 15:00, la suscripción es válida
        todo el 5 dic, sin importar la hora actual.
        """
        today = timezone.now().date()
        plan_prefix = self.plan.name
        
        # Comparar solo fechas: la suscripción es válida todo el día de end_date
        if self.end_date:
            end_date = self.end_date.date() if hasattr(self.end_date, 'date') else self.end_date
            if today <= end_date:
                return f'{plan_prefix}_active'
        
        # Sin período de gracia: si pasó el día de vencimiento, expira
        return f'{plan_prefix}_expired'

    def update_status(self):
        """Actualiza el estado si ha cambiado. Usado en vistas y cron jobs."""
        new_status = self.calculate_current_status()
        if new_status != self.subscription_status:
            self.subscription_status = new_status
            
            # Sin período de gracia: limpiar grace_end_date
            if self.grace_end_date:
                self.grace_end_date = None

            self.save(update_fields=['subscription_status', 'grace_end_date', 'updated_at'])
            return True
        return False

    @property
    def is_active(self):
        return self.subscription_status.endswith('_active')

    @property
    def is_in_grace_period(self):
        return self.subscription_status.endswith('_grace')
    
    @property
    def is_expired(self):
        return self.subscription_status.endswith('_expired')

    @property
    def days_remaining(self):
        """
        Calcula los días restantes comparando solo fechas (sin horas).
        Así el día de hoy siempre cuenta como día completo.
        Ejemplo: Si hoy es 3 dic y end_date es 2 ene → 30 días
        """
        today = timezone.now().date()

        if self.is_active and self.end_date:
            end_date = self.end_date.date() if hasattr(self.end_date, 'date') else self.end_date
            remaining_days = (end_date - today).days
        elif self.is_in_grace_period and self.grace_end_date:
            grace_date = self.grace_end_date.date() if hasattr(self.grace_end_date, 'date') else self.grace_end_date
            remaining_days = (grace_date - today).days
        else:
            return 0

        return max(0, remaining_days)

    def process_payment(self, amount, processed_by):
        """Procesa un pago, extiende la suscripción y crea un registro de pago."""
        from core.structured_logging import log_business_event
        import logging
        logger = logging.getLogger(__name__)
        
        now = timezone.now()
        old_end_date = self.end_date
        
        # Extender desde la fecha de vencimiento si aún no ha pasado, o desde hoy si ya expiró.
        base_date = max(now, self.end_date or now)
        self.end_date = base_date + timedelta(days=self.plan.billing_cycle_days)
        
        self.subscription_status = f'{self.plan.name}_active'
        self.grace_end_date = None # Reiniciar el periodo de gracia
        
        # Asegurar que las fechas sean timezone-aware antes de crear el Payment
        safe_old_end_date = timezone.make_aware(old_end_date) if old_end_date and old_end_date.tzinfo is None else old_end_date
        safe_new_end_date = timezone.make_aware(self.end_date) if self.end_date and self.end_date.tzinfo is None else self.end_date
        
        payment = Payment.objects.create(
            subscription=self,
            amount=amount,
            payment_method='manual',
            payment_type='subscription',
            status='completed',
            processed_by=processed_by,
            description=f'Pago procesado para extender el plan {self.plan.display_name}',
            days_added=self.plan.billing_cycle_days,
            old_end_date=safe_old_end_date,
            new_end_date=safe_new_end_date
        )
        self.save()
        
        log_business_event(
            event='subscription_payment_processed',
            action='payment_received',
            entity_type='subscription',
            entity_id=self.id,
            outcome='success',
            logger_name='apps.plans',
            payment_id=payment.id,
            organization_id=self.organization.id,
            organization_name=self.organization.name,
            amount=str(amount),
            days_added=self.plan.billing_cycle_days,
            old_end_date=str(old_end_date),
            new_end_date=str(self.end_date),
            processed_by=processed_by
        )
        
        return {'success': True, 'payment_id': payment.id}

    def extend_subscription(self, days, processed_by, reason=""):
        """
        Extiende la suscripción por un número determinado de días.
        """
        from core.structured_logging import log_business_event
        import logging
        logger = logging.getLogger(__name__)
        
        now = timezone.now()
        old_end_date = self.end_date

        # Extender desde la fecha de vencimiento si aún no ha pasado, o desde hoy si ya expiró.
        base_date = max(now, self.end_date or now)
        self.end_date = base_date + timedelta(days=days)

        self.subscription_status = f'{self.plan.name}_active'
        self.grace_end_date = None  # Reiniciar el período de gracia

        description = f'Extensión de {days} días para el plan {self.plan.display_name}.'
        if reason:
            description += f' Razón: {reason}'

        # Asegurar que las fechas sean timezone-aware antes de crear el Payment
        safe_old_end_date = timezone.make_aware(old_end_date) if old_end_date and old_end_date.tzinfo is None else old_end_date
        safe_new_end_date = timezone.make_aware(self.end_date) if self.end_date and self.end_date.tzinfo is None else self.end_date
        
        payment = Payment.objects.create(
            subscription=self,
            amount=0,  # No hay un pago monetario directo para esta acción
            payment_method='manual',
            payment_type='extension',  # Nuevo tipo de pago para distinguir extensiones
            status='completed',
            processed_by=processed_by,
            description=description,
            days_added=days,
            old_end_date=safe_old_end_date,
            new_end_date=safe_new_end_date
        )
        self.save()
        
        log_business_event(
            event='subscription_extended',
            action='extended',
            entity_type='subscription',
            entity_id=self.id,
            outcome='success',
            logger_name='apps.plans',
            payment_id=payment.id,
            organization_id=self.organization.id,
            organization_name=self.organization.name,
            days_added=days,
            old_end_date=str(old_end_date),
            new_end_date=str(self.end_date),
            reason=reason or 'N/A',
            processed_by=processed_by
        )
        
        return {'success': True, 'payment_id': payment.id}

    def switch_plan(self, new_plan, processed_by):
        """Cambia el plan de la suscripción, reinicia las fechas y crea un registro."""
        from core.structured_logging import log_business_event
        import logging
        logger = logging.getLogger(__name__)
        
        now = timezone.now()
        old_plan_name = self.plan.display_name
        old_plan_type = self.plan.name
        
        self.plan = new_plan
        self.start_date = now
        self.end_date = now + timedelta(days=new_plan.billing_cycle_days)
        self.subscription_status = f'{new_plan.name}_active'
        self.grace_end_date = None

        payment = Payment.objects.create(
            subscription=self,
            amount=new_plan.price,
            payment_method='upgrade',
            payment_type='upgrade',
            status='completed',
            processed_by=processed_by,
            description=f'Upgrade de plan: {old_plan_name} -> {new_plan.display_name}',
            days_added=new_plan.billing_cycle_days
        )
        self.save()
        
        log_business_event(
            event='subscription_plan_changed',
            action='plan_switched',
            entity_type='subscription',
            entity_id=self.id,
            outcome='success',
            logger_name='apps.plans',
            payment_id=payment.id,
            organization_id=self.organization.id,
            organization_name=self.organization.name,
            old_plan=old_plan_name,
            old_plan_type=old_plan_type,
            new_plan=new_plan.display_name,
            new_plan_type=new_plan.name,
            amount=str(new_plan.price),
            days_added=new_plan.billing_cycle_days,
            processed_by=processed_by
        )
        
        return {'success': True, 'payment_id': payment.id}

    def get_payment_history(self, limit=10):
        return self.payments.filter(status='completed').order_by('-created_at')[:limit]


class Payment(models.Model):
    """Modelo para registrar todos los pagos y transacciones, simplificado para MVP."""
    PAYMENT_STATUS = [('completed', 'Completado')]
    PAYMENT_METHODS = [('manual', 'Pago Manual'), ('upgrade', 'Upgrade')]
    PAYMENT_TYPES = [
        ('subscription', 'Suscripción'),
        ('upgrade', 'Upgrade'),
        ('trial_to_paid', 'Activación Trial'),
        ('extension', 'Extensión Manual')
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField("Monto", max_digits=10, decimal_places=2)
    payment_method = models.CharField("Método de Pago", max_length=20, choices=PAYMENT_METHODS, default='manual')
    payment_type = models.CharField("Tipo de Pago", max_length=20, choices=PAYMENT_TYPES, default='subscription')
    status = models.CharField("Estado", max_length=20, choices=PAYMENT_STATUS, default='completed')
    processed_by = models.CharField("Procesado por", max_length=100, blank=True, null=True)
    description = models.TextField("Descripción", blank=True)
    days_added = models.PositiveIntegerField("Días agregados", default=0)
    
    old_end_date = models.DateTimeField("Fecha anterior de vencimiento", null=True, blank=True)
    new_end_date = models.DateTimeField("Nueva fecha de vencimiento", null=True, blank=True)
    
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-created_at']

    def __str__(self):
        return f"Pago #{self.pk} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        """Override de save para logging estructurado"""
        from core.structured_logging import log_business_event
        import logging
        logger = logging.getLogger(__name__)
        
        is_new = self.pk is None
        
        # Guardar
        super().save(*args, **kwargs)
        
        # Logging solo para nuevos pagos (los updates son raros en Payment)
        if is_new:
            log_business_event(
                event='payment_recorded',
                action='created',
                entity_type='payment',
                entity_id=self.id,
                outcome='success',
                logger_name='apps.plans',
                subscription_id=self.subscription.id,
                organization_id=self.subscription.organization.id,
                organization_name=self.subscription.organization.name,
                amount=str(self.amount),
                payment_method=self.payment_method,
                payment_type=self.payment_type,
                days_added=self.days_added,
                processed_by=self.processed_by or 'N/A',
                description=self.description[:100] if self.description else 'N/A'
            )


class RenewalRequest(models.Model):
    """Gestiona las solicitudes de los usuarios para renovar su suscripción actual."""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]
    
    organization = models.ForeignKey('orgs.Organization', on_delete=models.CASCADE, related_name='renewal_requests')
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='renewal_requests')
    
    renewal_amount = models.DecimalField("Monto de renovación", max_digits=10, decimal_places=2)
    renewal_days = models.PositiveIntegerField("Días de renovación")
    reason = models.TextField("Motivo de renovación", blank=True, help_text="Motivo opcional para la renovación")
    
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    approved_by = models.CharField("Aprobado por", max_length=100, blank=True)
    processed_at = models.DateTimeField("Fecha de procesamiento", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitud de Renovación"
        verbose_name_plural = "Solicitudes de Renovación"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name}: Renovación de {self.subscription.plan.display_name}"

    def approve(self, approved_by_user):
        """Aprueba la solicitud, registra el pago y extiende exactamente renewal_days."""
        from django.db import transaction
        
        logger = logging.getLogger(__name__)
        
        if self.status != 'pending':
            return {'success': False, 'error': 'La solicitud no está pendiente.'}

        try:
            with transaction.atomic():
                self.status = 'approved'
                self.approved_by = f"{approved_by_user.email} (ID: {approved_by_user.pk})"
                self.processed_at = timezone.now()
                self.save(update_fields=['status', 'approved_by', 'processed_at', 'updated_at'])

                # Extender exactamente renewal_days y crear el Payment correspondiente
                subscription = self.subscription
                now = timezone.now()
                old_end_date = subscription.end_date
                base_date = max(now, subscription.end_date or now)
                subscription.end_date = base_date + timedelta(days=self.renewal_days)
                subscription.subscription_status = f'{subscription.plan.name}_active'
                subscription.grace_end_date = None

                # Asegurar timezone-aware en Payment
                safe_old_end_date = timezone.make_aware(old_end_date) if old_end_date and old_end_date.tzinfo is None else old_end_date
                safe_new_end_date = timezone.make_aware(subscription.end_date) if subscription.end_date and subscription.end_date.tzinfo is None else subscription.end_date

                payment = Payment.objects.create(
                    subscription=subscription,
                    amount=self.renewal_amount,
                    payment_method='manual',
                    payment_type='subscription',
                    status='completed',
                    processed_by=self.approved_by,
                    description=f'Renovación aprobada por {self.renewal_days} días',
                    days_added=self.renewal_days,
                    old_end_date=safe_old_end_date,
                    new_end_date=safe_new_end_date
                )

                subscription.save(update_fields=['end_date', 'subscription_status', 'grace_end_date', 'updated_at'])

                logger.info(
                    f"Renovación aprobada para {self.organization.name}. "
                    f"Plan {subscription.plan.display_name} extendido por {self.renewal_days} días."
                )
                return {'success': True, 'payment_id': payment.id}

        except Exception as e:
            logger.error(f"Error al aprobar la solicitud de renovación {self.id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Error interno: {str(e)}'}

    def reject(self, rejected_by_user, reason: str | None = None):
        """Rechaza la solicitud y registra el usuario que la procesó."""
        logger = logging.getLogger(__name__)
        if self.status != 'pending':
            return {'success': False, 'error': 'La solicitud no está pendiente.'}
        try:
            self.status = 'rejected'
            # Reutilizamos el campo approved_by para almacenar el usuario que procesó
            self.approved_by = f"{rejected_by_user.email} (ID: {rejected_by_user.pk})"
            self.processed_at = timezone.now()
            if reason:
                self.reason = f"Rechazado: {reason}"
            self.save(update_fields=['status', 'approved_by', 'processed_at', 'reason', 'updated_at'])
            logger.info(f"Solicitud de renovación {self.id} rechazada por {self.approved_by}.")
            return {'success': True}
        except Exception as e:
            logger.error(f"Error al rechazar la solicitud de renovación {self.id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Error interno: {str(e)}'}


class UpgradeRequest(models.Model):
    """Gestiona las solicitudes de los usuarios para cambiar a un plan superior."""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]
    
    organization = models.ForeignKey('orgs.Organization', on_delete=models.CASCADE, related_name='upgrade_requests')
    current_plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='+')
    requested_plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='+')
    
    amount = models.DecimalField("Monto del upgrade", max_digits=10, decimal_places=2)
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    approved_by = models.CharField("Aprobado por", max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitud de Upgrade"
        verbose_name_plural = "Solicitudes de Upgrade"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name}: {self.current_plan.display_name} -> {self.requested_plan.display_name}"

    def approve(self, approved_by_user):
        """Aprueba la solicitud, actualiza el estado y ejecuta el cambio de plan en la suscripción."""
        from django.db import transaction
        
        logger = logging.getLogger(__name__)
        
        if self.status != 'pending':
            return {'success': False, 'error': 'La solicitud no está pendiente.'}

        try:
            with transaction.atomic():
                self.status = 'approved'
                self.approved_by = f"{approved_by_user.email} (ID: {approved_by_user.pk})"
                self.save()
                
                # Asegurar que la organización tenga suscripción antes de cambiar el plan
                try:
                    subscription = self.organization.subscription
                except Subscription.DoesNotExist:
                    # Crear una suscripción trial (o la primera activa) como base
                    fallback_plan = Plan.get_trial_plan() or Plan.get_basic_plan() or Plan.objects.filter(is_active=True).order_by('price').first()
                    if not fallback_plan:
                        raise Exception('No hay planes activos disponibles para inicializar la suscripción.')
                    subscription = Subscription.objects.create(
                        organization=self.organization,
                        plan=fallback_plan
                    )
                result = subscription.switch_plan(
                    new_plan=self.requested_plan,
                    processed_by=self.approved_by
                )
                
                if result['success']:
                    logger.info(f"Upgrade a {self.requested_plan.display_name} completado para {self.organization.name}.")
                    return {'success': True}
                else:
                    # Si switch_plan falla, la transacción se revierte, así que no es necesario
                    # revertir manualmente el estado de la solicitud.
                    raise Exception("Fallo al cambiar el plan en la suscripción.")

        except Exception as e:
            logger.error(f"Error al aprobar la solicitud de upgrade {self.id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Error interno: {str(e)}'}        

    def reject(self, rejected_by_user, reason: str | None = None):
        """Rechaza la solicitud y registra el usuario que la procesó."""
        logger = logging.getLogger(__name__)
        if self.status != 'pending':
            return {'success': False, 'error': 'La solicitud no está pendiente.'}
        try:
            self.status = 'rejected'
            # Reutilizamos el campo approved_by para almacenar el usuario que procesó
            self.approved_by = f"{rejected_by_user.email} (ID: {rejected_by_user.pk})"
            self.save(update_fields=['status', 'approved_by', 'updated_at'])
            logger.info(f"Solicitud de upgrade {self.id} rechazada por {self.approved_by}.")
            return {'success': True}
        except Exception as e:
            logger.error(f"Error al rechazar la solicitud de upgrade {self.id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Error interno: {str(e)}'}
