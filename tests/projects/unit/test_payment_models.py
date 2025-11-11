"""
Tests exhaustivos para el modelo ProjectPayment

Estos tests DEBEN detectar bugs reales en la lógica de pagos de proyectos.
El modelo ProjectPayment es CRÍTICO porque maneja finanzas - es fundamental
para el seguimiento de pagos y presupuestos.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import IntegrityError
from django.core.cache import cache
from unittest.mock import patch, Mock
from tests.factories import (
    OrganizationFactory,
    UserFactory,
    ProjectFactory,
    ProjectPaymentFactory,
)
from apps.projects.models import ProjectPayment


# ============================================================================
# TESTS DE CREACIÓN DE PAGOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentCreation:
    """Tests de creación básica de pagos"""
    
    def test_payment_creation_with_factory(self):
        """Verificar que se puede crear un pago con la factory"""
        payment = ProjectPaymentFactory()
        
        assert payment.pk is not None
        assert payment.project is not None
        assert payment.amount is not None
        assert payment.date is not None
    
    def test_payment_creation_with_valid_data(self):
        """Crear pago con datos válidos completos"""
        project = ProjectFactory()
        user = UserFactory()
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('5000.00'),
            date=timezone.now().date(),
            description='Primer pago del proyecto',
            created_by=user
        )
        
        assert payment.pk is not None
        assert payment.project == project
        assert payment.amount == Decimal('5000.00')
        assert payment.date == timezone.now().date()
        assert payment.description == 'Primer pago del proyecto'
        assert payment.created_by == user
    
    def test_payment_creation_without_optional_fields(self):
        """
        EDGE CASE: Pago sin campos opcionales
        """
        project = ProjectFactory()
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date(),
            description='',
            receipt_file=None,
            receipt=None,
            created_by=None
        )
        
        assert payment.pk is not None
        assert payment.description == ''
        assert not payment.receipt_file  # FieldFile evalúa a False cuando está vacío
        assert payment.receipt is None
        assert payment.created_by is None
    
    def test_payment_str_representation(self):
        """__str__ debe retornar proyecto, monto y fecha"""
        project = ProjectFactory(name='Mi Proyecto')
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('2500.00'),
            date=timezone.now().date()
        )
        
        expected_str = f"Mi Proyecto - $2500.00 ({timezone.now().date()})"
        assert str(payment) == expected_str
    
    def test_payment_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        payment = ProjectPaymentFactory()
        
        assert payment.created_at is not None
        assert (timezone.now() - payment.created_at).seconds < 5
    
    def test_payment_updated_at_auto_set(self):
        """updated_at debe actualizarse automáticamente"""
        payment = ProjectPaymentFactory()
        
        assert payment.updated_at is not None
        assert (timezone.now() - payment.updated_at).seconds < 5


# ============================================================================
# TESTS DE RELACIONES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentRelationships:
    """Tests de relaciones con otros modelos"""
    
    def test_payment_project_relationship(self):
        """Pago debe estar relacionado con un proyecto"""
        project = ProjectFactory(name='Test Project')
        payment = ProjectPaymentFactory(project=project)
        
        assert payment.project == project
        assert payment in project.payments.all()
    
    def test_payment_created_by_relationship(self):
        """Pago puede estar relacionado con usuario que lo creó"""
        user = UserFactory(email='creator@test.com')
        payment = ProjectPaymentFactory(created_by=user)
        
        assert payment.created_by == user
        assert payment in user.created_payments.all()
    
    def test_payment_cascade_on_project_delete(self):
        """
        CRITICAL: Pago debe eliminarse al eliminar el proyecto
        (CASCADE delete)
        """
        project = ProjectFactory()
        payment = ProjectPaymentFactory(project=project)
        payment_id = payment.id
        
        project.delete()
        
        with pytest.raises(ProjectPayment.DoesNotExist):
            ProjectPayment.objects.get(id=payment_id)
    
    def test_payment_set_null_on_user_delete(self):
        """
        Pago debe mantener created_by=None al eliminar usuario
        (SET_NULL behavior)
        """
        user = UserFactory()
        payment = ProjectPaymentFactory(created_by=user)
        
        user.delete()
        
        payment.refresh_from_db()
        assert payment.created_by is None


# ============================================================================
# TESTS DE CAMPOS FINANCIEROS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentFinancialFields:
    """Tests de campos financieros del pago"""
    
    def test_payment_amount_decimal_precision(self):
        """
        Monto debe mantener precisión decimal (2 decimales)
        """
        payment = ProjectPaymentFactory(amount=Decimal('12345.67'))
        payment.refresh_from_db()
        
        assert payment.amount == Decimal('12345.67')
    
    def test_payment_amount_large_value(self):
        """
        EDGE CASE: Monto con valor grande (12 dígitos)
        """
        payment = ProjectPaymentFactory(amount=Decimal('9999999999.99'))
        payment.refresh_from_db()
        
        assert payment.amount == Decimal('9999999999.99')
    
    def test_payment_amount_small_value(self):
        """
        EDGE CASE: Monto con valor pequeño
        """
        payment = ProjectPaymentFactory(amount=Decimal('0.01'))
        payment.refresh_from_db()
        
        assert payment.amount == Decimal('0.01')
    
    def test_payment_amount_zero_value(self):
        """
        EDGE CASE: Monto con valor cero
        WARNING: Debería validarse que el monto sea positivo
        """
        project = ProjectFactory()
        
        # NOTA: Actualmente permite monto cero
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('0.00'),
            date=timezone.now().date()
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert payment.amount == Decimal('0.00')
        # TODO: Considerar agregar validación para montos positivos
    
    def test_payment_amount_negative_value(self):
        """
        EDGE CASE: Monto negativo
        WARNING: Debería validarse que el monto sea positivo
        """
        project = ProjectFactory()
        
        # NOTA: Actualmente permite monto negativo
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('-1000.00'),
            date=timezone.now().date()
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert payment.amount == Decimal('-1000.00')
        # TODO: Considerar agregar validación para montos positivos


# ============================================================================
# TESTS DE percentage_of_total PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentPercentageOfTotalProperty:
    """Tests de la propiedad percentage_of_total"""
    
    def test_percentage_of_total_with_budget(self):
        """Calcular porcentaje del total con presupuesto"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('2500.00')
        )
        
        # 2500 / 10000 = 25%
        assert payment.percentage_of_total == 25.0
    
    def test_percentage_of_total_without_budget(self):
        """
        EDGE CASE: Porcentaje sin presupuesto = 0
        """
        project = ProjectFactory(total_budget=None, budget_configured=False)
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('2500.00')
        )
        
        assert payment.percentage_of_total == 0
    
    def test_percentage_of_total_with_zero_budget(self):
        """
        EDGE CASE: División por cero - presupuesto = 0
        """
        project = ProjectFactory(total_budget=Decimal('0.00'))
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('1000.00')
        )
        
        # Debe manejar división por cero
        assert payment.percentage_of_total == 0
    
    def test_percentage_of_total_precision(self):
        """
        Porcentaje debe tener precisión de 1 decimal
        """
        project = ProjectFactory(total_budget=Decimal('7.00'))
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('3.00')
        )
        
        # 3/7 = 42.857... debe redondearse a 42.9
        # percentage_of_total retorna Decimal, no float
        assert payment.percentage_of_total == Decimal('42.9')
    
    def test_percentage_of_total_full_payment(self):
        """Porcentaje con pago completo = 100%"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('10000.00')
        )
        
        assert payment.percentage_of_total == 100.0
    
    def test_percentage_of_total_overpayment(self):
        """
        EDGE CASE: Porcentaje con sobrepago > 100%
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('15000.00')
        )
        
        # 15000 / 10000 = 150%
        assert payment.percentage_of_total == 150.0


# ============================================================================
# TESTS DE SAVE METHOD Y LOGGING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentSaveMethod:
    """Tests del método save y logging"""
    
    @patch('apps.projects.models.logger')
    def test_payment_save_logs_creation(self, mock_logger):
        """
        save() debe loguear creación de pago
        """
        project = ProjectFactory()
        
        payment = ProjectPayment(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date()
        )
        payment.save()
        
        # Verificar que se llamó al logging
        assert mock_logger.info.call_count >= 1
    
    def test_payment_save_invalidates_cache(self):
        """
        save() debe invalidar caché financiero del proyecto
        """
        project = ProjectFactory()
        
        # Establecer cache
        cache.set(f"project_total_paid:{project.id}", 5000.00, 600)
        
        # Crear pago
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date()
        )
        
        # Verificar que el cache fue invalidado
        cached_value = cache.get(f"project_total_paid:{project.id}")
        assert cached_value is None


# ============================================================================
# TESTS DE DELETE METHOD
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentDeleteMethod:
    """Tests del método delete"""
    
    @patch('apps.projects.models.logger')
    def test_payment_delete_logs_deletion(self, mock_logger):
        """
        delete() debe loguear eliminación de pago
        """
        payment = ProjectPaymentFactory()
        
        payment.delete()
        
        # Verificar que se llamó al logging
        assert mock_logger.info.call_count >= 1
    
    def test_payment_delete_invalidates_cache(self):
        """
        delete() debe invalidar caché financiero del proyecto
        """
        project = ProjectFactory()
        payment = ProjectPaymentFactory(project=project)
        
        # Establecer cache
        cache.set(f"project_total_paid:{project.id}", 5000.00, 600)
        
        # Eliminar pago
        payment.delete()
        
        # Verificar que el cache fue invalidado
        cached_value = cache.get(f"project_total_paid:{project.id}")
        assert cached_value is None


# ============================================================================
# TESTS DE ORDENAMIENTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentOrdering:
    """Tests de ordenamiento de pagos"""
    
    def test_payments_ordered_by_date_desc(self):
        """Pagos deben ordenarse por fecha descendente"""
        project = ProjectFactory()
        
        old_payment = ProjectPaymentFactory(
            project=project,
            date=(timezone.now() - timedelta(days=10)).date()
        )
        recent_payment = ProjectPaymentFactory(
            project=project,
            date=timezone.now().date()
        )
        
        payments = ProjectPayment.objects.filter(project=project)
        
        # Orden descendente por fecha
        assert payments[0] == recent_payment
        assert payments[1] == old_payment
    
    def test_payments_ordered_by_created_at_if_same_date(self):
        """Si tienen misma fecha, ordenar por created_at descendente"""
        project = ProjectFactory()
        same_date = timezone.now().date()
        
        old_payment = ProjectPaymentFactory(
            project=project,
            date=same_date
        )
        # Esperar un momento
        import time
        time.sleep(0.01)
        recent_payment = ProjectPaymentFactory(
            project=project,
            date=same_date
        )
        
        payments = ProjectPayment.objects.filter(
            project=project,
            date=same_date
        )
        
        # Orden por created_at (el más reciente primero)
        assert payments[0] == recent_payment
        assert payments[1] == old_payment


# ============================================================================
# TESTS DE VALIDACIONES Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentValidations:
    """Tests de validaciones y constraints"""
    
    def test_payment_requires_project(self):
        """
        CRITICAL: Pago debe requerir proyecto
        """
        with pytest.raises((IntegrityError, Exception)):  # Puede lanzar diferentes excepciones
            payment = ProjectPayment.objects.create(
                project=None,
                amount=Decimal('1000.00'),
                date=timezone.now().date()
            )
            payment.save()
    
    def test_payment_requires_amount(self):
        """
        CRITICAL: Pago debe requerir monto
        """
        project = ProjectFactory()
        
        with pytest.raises(IntegrityError):
            ProjectPayment.objects.create(
                project=project,
                amount=None,
                date=timezone.now().date()
            )
    
    def test_payment_requires_date(self):
        """
        CRITICAL: Pago debe requerir fecha
        """
        project = ProjectFactory()
        
        with pytest.raises(IntegrityError):
            ProjectPayment.objects.create(
                project=project,
                amount=Decimal('1000.00'),
                date=None
            )


# ============================================================================
# TESTS DE EDGE CASES Y BUG HUNTING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentEdgeCases:
    """Tests de casos extremos y potenciales bugs"""
    
    def test_payment_with_unicode_description(self):
        """
        EDGE CASE: Descripción con caracteres especiales y unicode
        """
        project = ProjectFactory()
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date(),
            description='Pago Müller & Associés 日本 50%'
        )
        
        assert payment.pk is not None
        assert payment.description == 'Pago Müller & Associés 日本 50%'
    
    def test_payment_with_very_long_description(self):
        """
        EDGE CASE: Descripción muy larga (TextField sin límite)
        """
        project = ProjectFactory()
        
        # 10,000 caracteres
        long_description = 'A' * 10000
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date(),
            description=long_description
        )
        
        assert payment.pk is not None
        assert len(payment.description) == 10000
    
    def test_payment_with_future_date(self):
        """
        EDGE CASE: Pago con fecha futura
        WARNING: Debería validarse que la fecha no sea futura
        """
        project = ProjectFactory()
        future_date = (timezone.now() + timedelta(days=30)).date()
        
        # NOTA: Actualmente permite fecha futura
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=future_date
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert payment.date > timezone.now().date()
        # TODO: Considerar agregar validación para fechas no futuras
    
    def test_payment_with_very_old_date(self):
        """
        EDGE CASE: Pago con fecha muy antigua
        """
        project = ProjectFactory()
        old_date = (timezone.now() - timedelta(days=365*10)).date()
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=old_date
        )
        
        assert payment.pk is not None
        assert payment.date == old_date
    
    def test_multiple_payments_same_project_same_amount(self):
        """
        Múltiples pagos pueden tener el mismo monto en el mismo proyecto
        """
        project = ProjectFactory()
        
        payment1 = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date()
        )
        payment2 = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date()
        )
        
        assert payment1.amount == payment2.amount
        assert payment1.pk != payment2.pk
    
    def test_payment_modification_after_creation(self):
        """Pago puede modificarse después de creación"""
        payment = ProjectPaymentFactory(
            amount=Decimal('1000.00'),
            description='Pago inicial'
        )
        
        # Modificar
        payment.amount = Decimal('1500.00')
        payment.description = 'Pago modificado'
        payment.save()
        
        payment.refresh_from_db()
        assert payment.amount == Decimal('1500.00')
        assert payment.description == 'Pago modificado'
        assert payment.updated_at > payment.created_at


# ============================================================================
# TESTS DE INDEXES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentIndexes:
    """Tests de que los índices están configurados correctamente"""
    
    def test_payment_has_project_date_index(self):
        """Verificar que existe índice payment_project_date_idx"""
        indexes = [index.name for index in ProjectPayment._meta.indexes]
        assert 'payment_project_date_idx' in indexes
    
    def test_payment_has_created_index(self):
        """Verificar que existe índice payment_created_idx"""
        indexes = [index.name for index in ProjectPayment._meta.indexes]
        assert 'payment_created_idx' in indexes
    
    def test_payment_has_project_amount_index(self):
        """Verificar que existe índice payment_project_amount_idx"""
        indexes = [index.name for index in ProjectPayment._meta.indexes]
        assert 'payment_project_amount_idx' in indexes


# ============================================================================
# TESTS DE META OPTIONS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentMetaOptions:
    """Tests de opciones Meta del modelo"""
    
    def test_payment_verbose_name(self):
        """Verificar verbose_name configurado"""
        assert ProjectPayment._meta.verbose_name == 'Pago de Proyecto'
    
    def test_payment_verbose_name_plural(self):
        """Verificar verbose_name_plural configurado"""
        assert ProjectPayment._meta.verbose_name_plural == 'Pagos de Proyecto'
    
    def test_payment_ordering(self):
        """Verificar ordenamiento por defecto"""
        assert ProjectPayment._meta.ordering == ['-date', '-created_at']


# ============================================================================
# TESTS DE INTEGRACIÓN FINANCIERA
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentFinancialIntegration:
    """Tests de integración con cálculos financieros del proyecto"""
    
    def test_payment_affects_project_total_paid(self):
        """Crear pago debe afectar total_paid del proyecto"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        # Inicialmente 0
        assert project.total_paid == Decimal('0.00')
        
        # Crear pago
        ProjectPaymentFactory(project=project, amount=Decimal('2500.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        # Debe actualizarse
        project.refresh_from_db()
        assert project.total_paid == Decimal('2500.00')
    
    def test_multiple_payments_accumulate(self):
        """Múltiples pagos deben acumularse correctamente"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('1500.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Total debe ser la suma
        assert project.total_paid == Decimal('4500.00')
    
    def test_payment_deletion_affects_project_total(self):
        """Eliminar pago debe afectar total_paid del proyecto"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment1 = ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        payment2 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        assert project.total_paid == Decimal('5000.00')
        
        # Eliminar un pago
        payment1.delete()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Total debe actualizarse
        assert project.total_paid == Decimal('3000.00')

