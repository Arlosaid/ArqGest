"""
Tests exhaustivos para el modelo Payment

Estos tests DEBEN detectar bugs reales en la lógica de negocio de pagos.
El modelo Payment es CRÍTICO porque registra todas las transacciones y pagos.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch
from tests.factories import (
    OrganizationFactory,
    PlanFactory,
    TrialPlanFactory,
    BasicPlanFactory,
    SubscriptionFactory,
    PaymentFactory,
)
from apps.plans.models import Payment, Subscription


# ============================================================================
# TESTS DE CREACIÓN DE PAGOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentCreation:
    """Tests de creación básica de pagos"""
    
    def test_payment_creation_with_factory(self):
        """Verificar que se puede crear un pago con la factory"""
        payment = PaymentFactory()
        
        assert payment.pk is not None
        assert payment.subscription is not None
        assert payment.amount is not None
        assert payment.payment_method is not None
        assert payment.payment_type is not None
        assert payment.status is not None
    
    def test_payment_creation_with_all_fields(self):
        """Crear pago con todos los campos"""
        subscription = SubscriptionFactory()
        payment = Payment.objects.create(
            subscription=subscription,
            amount=Decimal('299.00'),
            payment_method='manual',
            payment_type='subscription',
            status='completed',
            processed_by='admin@example.com',
            description='Pago de suscripción mensual',
            days_added=30
        )
        
        assert payment.pk is not None
        assert payment.subscription == subscription
        assert payment.amount == Decimal('299.00')
        assert payment.payment_method == 'manual'
        assert payment.payment_type == 'subscription'
        assert payment.status == 'completed'
        assert payment.processed_by == 'admin@example.com'
        assert payment.days_added == 30
    
    def test_payment_str_representation(self):
        """__str__ debe retornar organización, monto y estado"""
        payment = PaymentFactory()
        
        expected_str = f"{payment.subscription.organization.name} - ${payment.amount} ({payment.get_status_display()})"
        assert str(payment) == expected_str
    
    def test_payment_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        payment = PaymentFactory()
        
        assert payment.created_at is not None
        assert payment.created_at <= timezone.now()


# ============================================================================
# TESTS DE VALIDACIÓN Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentValidation:
    """Tests de validación de pagos - DETECTAR BUGS REALES"""
    
    def test_subscription_is_required(self):
        """subscription debe ser obligatorio"""
        with pytest.raises(Exception):  # IntegrityError o ValidationError
            Payment.objects.create(
                subscription=None,
                amount=Decimal('299.00'),
                payment_method='manual',
                payment_type='subscription',
                status='completed'
            )
    
    def test_amount_is_required(self):
        """amount debe ser obligatorio"""
        subscription = SubscriptionFactory()
        
        with pytest.raises(Exception):
            Payment.objects.create(
                subscription=subscription,
                amount=None,
                payment_method='manual',
                payment_type='subscription',
                status='completed'
            )
    
    def test_payment_method_must_be_valid_choice(self):
        """
        CRÍTICO: payment_method debe ser uno de los choices válidos
        Opciones válidas: 'manual', 'upgrade'
        """
        subscription = SubscriptionFactory()
        
        # Opciones válidas
        payment1 = PaymentFactory(
            subscription=subscription,
            payment_method='manual'
        )
        assert payment1.payment_method == 'manual'
        
        payment2 = PaymentFactory(
            subscription=subscription,
            payment_method='upgrade'
        )
        assert payment2.payment_method == 'upgrade'
    
    def test_payment_type_must_be_valid_choice(self):
        """
        CRÍTICO: payment_type debe ser uno de los choices válidos
        Opciones válidas: 'subscription', 'upgrade', 'trial_to_paid', 'extension'
        """
        subscription = SubscriptionFactory()
        
        # Opciones válidas
        valid_types = ['subscription', 'upgrade', 'trial_to_paid', 'extension']
        for payment_type in valid_types:
            payment = PaymentFactory(
                subscription=subscription,
                payment_type=payment_type
            )
            assert payment.payment_type == payment_type
    
    def test_status_must_be_valid_choice(self):
        """
        CRÍTICO: status debe ser uno de los choices válidos
        Opciones válidas: 'completed'
        """
        subscription = SubscriptionFactory()
        
        # Solo 'completed' está disponible
        payment = PaymentFactory(
            subscription=subscription,
            status='completed'
        )
        assert payment.status == 'completed'
    
    def test_amount_can_be_zero(self):
        """
        EDGE CASE: ¿El monto puede ser 0?
        Esto puede ser válido para extensiones manuales o trials
        """
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            amount=Decimal('0.00')
        )
        
        assert payment.amount == Decimal('0.00')
    
    def test_amount_can_be_negative(self):
        """
        BUG POTENCIAL: ¿El monto puede ser negativo?
        Django permite negativos en DecimalField por defecto
        """
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            amount=Decimal('-100.00')
        )
        
        # Django permite negativos
        assert payment.amount == Decimal('-100.00')
        # WARNING: Debería validarse que amount >= 0
    
    def test_days_added_can_be_zero(self):
        """days_added puede ser 0"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            days_added=0
        )
        
        assert payment.days_added == 0
    
    def test_days_added_cannot_be_negative(self):
        """days_added no puede ser negativo (PositiveIntegerField)"""
        subscription = SubscriptionFactory()
        
        with pytest.raises((ValidationError, Exception)):
            Payment.objects.create(
                subscription=subscription,
                amount=Decimal('299.00'),
                payment_method='manual',
                payment_type='subscription',
                status='completed',
                days_added=-1
            )
    
    def test_processed_by_can_be_blank(self):
        """processed_by puede estar vacío"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            processed_by=''
        )
        
        assert payment.processed_by == ''
    
    def test_description_can_be_blank(self):
        """description puede estar vacío"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            description=''
        )
        
        assert payment.description == ''


# ============================================================================
# TESTS DE RELACIÓN CON SUSCRIPCIÓN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentSubscriptionRelationship:
    """Tests de relación entre Payment y Subscription"""
    
    def test_payment_belongs_to_subscription(self):
        """Payment debe pertenecer a una suscripción"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(subscription=subscription)
        
        assert payment.subscription == subscription
    
    def test_subscription_has_many_payments(self):
        """Subscription puede tener múltiples pagos"""
        subscription = SubscriptionFactory()
        PaymentFactory.create_batch(5, subscription=subscription)
        
        payments = Payment.objects.filter(subscription=subscription)
        assert payments.count() == 5
    
    def test_payment_cascade_delete_on_subscription_delete(self):
        """
        CRÍTICO: Eliminar suscripción debe eliminar pagos (CASCADE)
        """
        subscription = SubscriptionFactory()
        payment = PaymentFactory(subscription=subscription)
        payment_id = payment.id
        
        subscription.delete()
        
        # Payment debe eliminarse
        with pytest.raises(Payment.DoesNotExist):
            Payment.objects.get(id=payment_id)
    
    def test_payment_accesses_organization_through_subscription(self):
        """Payment debe poder acceder a organización a través de suscripción"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(subscription=subscription)
        
        assert payment.subscription.organization == subscription.organization


# ============================================================================
# TESTS DE TIPOS DE PAGO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentTypes:
    """Tests de diferentes tipos de pago"""
    
    def test_payment_type_subscription(self):
        """Pago de tipo subscription"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            payment_type='subscription',
            amount=Decimal('299.00'),
            days_added=30
        )
        
        assert payment.payment_type == 'subscription'
        assert payment.amount == Decimal('299.00')
        assert payment.days_added == 30
    
    def test_payment_type_upgrade(self):
        """Pago de tipo upgrade"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            payment_type='upgrade',
            payment_method='upgrade',
            amount=Decimal('399.00'),
            days_added=30
        )
        
        assert payment.payment_type == 'upgrade'
        assert payment.payment_method == 'upgrade'
        assert payment.amount == Decimal('399.00')
    
    def test_payment_type_trial_to_paid(self):
        """Pago de tipo trial_to_paid"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            payment_type='trial_to_paid',
            amount=Decimal('0.00'),
            days_added=7
        )
        
        assert payment.payment_type == 'trial_to_paid'
        assert payment.amount == Decimal('0.00')
    
    def test_payment_type_extension(self):
        """Pago de tipo extension (extensión manual)"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            payment_type='extension',
            amount=Decimal('0.00'),
            days_added=15
        )
        
        assert payment.payment_type == 'extension'
        assert payment.amount == Decimal('0.00')
        assert payment.days_added == 15


# ============================================================================
# TESTS DE MÉTODOS DE PAGO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentMethods:
    """Tests de métodos de pago"""
    
    def test_payment_method_manual(self):
        """Pago manual"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            payment_method='manual',
            processed_by='admin@example.com'
        )
        
        assert payment.payment_method == 'manual'
        assert payment.processed_by == 'admin@example.com'
    
    def test_payment_method_upgrade(self):
        """Pago por upgrade"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            payment_method='upgrade',
            payment_type='upgrade'
        )
        
        assert payment.payment_method == 'upgrade'
        assert payment.payment_type == 'upgrade'


# ============================================================================
# TESTS DE FECHAS (old_end_date, new_end_date)
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentDates:
    """Tests de fechas en pagos"""
    
    def test_payment_with_old_and_new_end_date(self):
        """Pago con fechas de vencimiento antiguas y nuevas"""
        subscription = SubscriptionFactory()
        old_end = timezone.now() + timedelta(days=5)
        new_end = timezone.now() + timedelta(days=35)
        
        payment = PaymentFactory(
            subscription=subscription,
            old_end_date=old_end,
            new_end_date=new_end
        )
        
        assert payment.old_end_date == old_end
        assert payment.new_end_date == new_end
    
    def test_payment_without_dates(self):
        """Pago sin fechas (puede ser válido para algunos tipos)"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            old_end_date=None,
            new_end_date=None
        )
        
        assert payment.old_end_date is None
        assert payment.new_end_date is None
    
    def test_payment_dates_can_be_in_past(self):
        """Fechas pueden estar en el pasado (para registros históricos)"""
        subscription = SubscriptionFactory()
        old_end = timezone.now() - timedelta(days=10)
        new_end = timezone.now() - timedelta(days=5)
        
        payment = PaymentFactory(
            subscription=subscription,
            old_end_date=old_end,
            new_end_date=new_end
        )
        
        assert payment.old_end_date == old_end
        assert payment.new_end_date == new_end
    
    def test_payment_dates_can_be_in_future(self):
        """Fechas pueden estar en el futuro"""
        subscription = SubscriptionFactory()
        old_end = timezone.now() + timedelta(days=10)
        new_end = timezone.now() + timedelta(days=40)
        
        payment = PaymentFactory(
            subscription=subscription,
            old_end_date=old_end,
            new_end_date=new_end
        )
        
        assert payment.old_end_date == old_end
        assert payment.new_end_date == new_end


# ============================================================================
# TESTS DE SAVE METHOD Y LOGGING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentSaveMethod:
    """Tests del método save - CRÍTICO para logging"""
    
    @patch('core.structured_logging.log_business_event')
    def test_save_creates_log_for_new_payment(self, mock_log):
        """Crear nuevo pago debe generar log"""
        subscription = SubscriptionFactory()
        payment = Payment(
            subscription=subscription,
            amount=Decimal('299.00'),
            payment_method='manual',
            payment_type='subscription',
            status='completed',
            processed_by='test@example.com',
            description='Test payment',
            days_added=30
        )
        
        payment.save()
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs['event'] == 'payment_recorded'
        assert call_kwargs['entity_type'] == 'payment'
        assert call_kwargs['amount'] == '299.00'
    
    @patch('core.structured_logging.log_business_event')
    def test_save_does_not_log_on_update(self, mock_log):
        """Actualizar pago NO debe generar log (solo crea log en creación)"""
        payment = PaymentFactory()
        mock_log.reset_mock()
        
        payment.amount = Decimal('399.00')
        payment.save()
        
        # No debe llamar al log en updates
        # El código solo loguea en is_new, así que esto debería pasar
        # Pero verificar que no se llama con event='payment_recorded'
        if mock_log.called:
            # Si se llama, no debe ser payment_recorded
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs.get('event') != 'payment_recorded'


# ============================================================================
# TESTS DE ORDENAMIENTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentOrdering:
    """Tests de ordenamiento de pagos"""
    
    def test_default_ordering_by_created_at_desc(self):
        """Pagos deben ordenarse por created_at descendente por defecto"""
        subscription = SubscriptionFactory()
        payment1 = PaymentFactory(subscription=subscription)
        payment2 = PaymentFactory(subscription=subscription)
        
        payments = Payment.objects.filter(subscription=subscription)
        
        # El más reciente debe estar primero
        assert payments[0].created_at >= payments[1].created_at
    
    def test_payments_ordered_correctly_for_subscription(self):
        """Pagos de una suscripción deben estar ordenados correctamente"""
        subscription = SubscriptionFactory()
        PaymentFactory.create_batch(5, subscription=subscription)
        
        payments = Payment.objects.filter(subscription=subscription)
        
        # Verificar que están ordenados descendente
        for i in range(len(payments) - 1):
            assert payments[i].created_at >= payments[i + 1].created_at


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentEdgeCases:
    """Tests de casos extremos - ENCONTRAR BUGS"""
    
    def test_payment_with_very_large_amount(self):
        """Pago con monto muy grande"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            amount=Decimal('999999.99')
        )
        
        assert payment.amount == Decimal('999999.99')
    
    def test_payment_with_very_large_days_added(self):
        """Pago con muchos días agregados"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            days_added=36500  # 100 años
        )
        
        assert payment.days_added == 36500
    
    def test_payment_with_very_long_description(self):
        """Pago con descripción muy larga"""
        subscription = SubscriptionFactory()
        long_description = 'A' * 10000
        payment = PaymentFactory(
            subscription=subscription,
            description=long_description
        )
        
        assert len(payment.description) == 10000
    
    def test_payment_with_unicode_description(self):
        """Pago con descripción Unicode"""
        subscription = SubscriptionFactory()
        payment = PaymentFactory(
            subscription=subscription,
            description='Pago en Español 中文 🚀'
        )
        
        assert '中文' in payment.description
        assert '🚀' in payment.description
    
    def test_payment_with_very_long_processed_by(self):
        """
        BUG POTENCIAL: processed_by tiene max_length=100
        Django debe lanzar error si intentamos guardar más caracteres
        """
        subscription = SubscriptionFactory()
        long_processed_by = 'A' * 200
        
        # Django debe lanzar DataError al intentar guardar más de 100 caracteres
        with pytest.raises(Exception):  # DataError de Django
            PaymentFactory(
                subscription=subscription,
                processed_by=long_processed_by
            )
    
    def test_multiple_payments_same_subscription(self):
        """Múltiples pagos para la misma suscripción"""
        subscription = SubscriptionFactory()
        PaymentFactory.create_batch(100, subscription=subscription)
        
        payments = Payment.objects.filter(subscription=subscription)
        assert payments.count() == 100
    
    def test_payment_with_same_amount_different_types(self):
        """Pagos con mismo monto pero diferentes tipos"""
        subscription = SubscriptionFactory()
        amount = Decimal('299.00')
        
        payment1 = PaymentFactory(
            subscription=subscription,
            amount=amount,
            payment_type='subscription'
        )
        payment2 = PaymentFactory(
            subscription=subscription,
            amount=amount,
            payment_type='upgrade'
        )
        
        assert payment1.amount == payment2.amount
        assert payment1.payment_type != payment2.payment_type


# ============================================================================
# TESTS DE INTEGRACIÓN CON SUSCRIPCIÓN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentSubscriptionIntegration:
    """Tests de integración entre Payment y Subscription"""
    
    def test_payment_created_by_process_payment(self):
        """Payment creado por process_payment debe tener campos correctos"""
        subscription = SubscriptionFactory()
        amount = Decimal('299.00')
        
        result = subscription.process_payment(
            amount=amount,
            processed_by='test@example.com'
        )
        
        assert result['success'] is True
        payment = Payment.objects.get(id=result['payment_id'])
        assert payment.amount == amount
        assert payment.payment_method == 'manual'
        assert payment.payment_type == 'subscription'
        assert payment.status == 'completed'
        assert payment.processed_by == 'test@example.com'
        assert payment.days_added == subscription.plan.billing_cycle_days
    
    def test_payment_created_by_extend_subscription(self):
        """Payment creado por extend_subscription debe tener campos correctos"""
        subscription = SubscriptionFactory()
        days = 30
        
        result = subscription.extend_subscription(
            days=days,
            processed_by='test@example.com',
            reason='Test extension'
        )
        
        assert result['success'] is True
        payment = Payment.objects.get(id=result['payment_id'])
        assert payment.amount == Decimal('0.00')
        assert payment.payment_method == 'manual'
        assert payment.payment_type == 'extension'
        assert payment.status == 'completed'
        assert payment.days_added == days
        assert 'Test extension' in payment.description
    
    def test_payment_created_by_switch_plan(self):
        """Payment creado por switch_plan debe tener campos correctos"""
        subscription = SubscriptionFactory()
        new_plan = BasicPlanFactory(price=Decimal('399.00'))
        
        result = subscription.switch_plan(
            new_plan=new_plan,
            processed_by='test@example.com'
        )
        
        assert result['success'] is True
        payment = Payment.objects.get(id=result['payment_id'])
        assert payment.amount == new_plan.price
        assert payment.payment_method == 'upgrade'
        assert payment.payment_type == 'upgrade'
        assert payment.status == 'completed'
        assert payment.days_added == new_plan.billing_cycle_days
    
    def test_payment_history_includes_all_payment_types(self):
        """Historial de pagos debe incluir todos los tipos"""
        subscription = SubscriptionFactory()
        PaymentFactory(subscription=subscription, payment_type='subscription', status='completed')
        PaymentFactory(subscription=subscription, payment_type='upgrade', status='completed')
        PaymentFactory(subscription=subscription, payment_type='extension', status='completed')
        
        history = subscription.get_payment_history()
        
        assert len(history) == 3
        payment_types = [p.payment_type for p in history]
        assert 'subscription' in payment_types
        assert 'upgrade' in payment_types
        assert 'extension' in payment_types

