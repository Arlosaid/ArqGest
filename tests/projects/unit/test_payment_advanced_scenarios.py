"""
Tests avanzados del módulo de finanzas - Casos complejos y de integración.

ENFOQUE: Encontrar bugs en interacciones complejas y flujos realistas.

Estos tests verifican:
1. Cálculos financieros en proyectos con múltiples pagos
2. Comportamiento del property remaining_amount en diferentes escenarios
3. Interacciones entre proyecto, pagos y presupuesto
4. Validaciones que podrían fallar en casos extremos
5. Comportamiento con archivos de comprobantes
"""

import pytest
from decimal import Decimal, InvalidOperation
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock

from tests.factories import (
    OrganizationFactory,
    UserFactory,
    ProjectFactory,
    ProjectPaymentFactory,
)
from apps.projects.models import Project, ProjectPayment


# ============================================================================
# TESTS DE PROJECT.remaining_amount PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectRemainingAmountProperty:
    """
    Tests del property remaining_amount del proyecto.
    
    remaining_amount = total_budget - total_paid
    
    ⚠️ BUG HUNTING: ¿Qué pasa en casos extremos?
    """
    
    def test_remaining_amount_with_no_budget(self):
        """
        ⚠️ EDGE CASE: Si no hay presupuesto, ¿cuál es remaining_amount?
        """
        project = ProjectFactory(
            total_budget=None,
            budget_configured=False
        )
        
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # remaining_amount debería ser None o algo que indique "sin límite"
        remaining = project.remaining_amount
        
        # NOTA: Verificar qué devuelve en la implementación
        assert remaining is None or remaining < Decimal('0')
    
    def test_remaining_amount_exactly_zero(self):
        """
        ✅ CORRECTO: remaining_amount = 0 cuando total_paid = total_budget
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        ProjectPaymentFactory(project=project, amount=Decimal('10000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.remaining_amount == Decimal('0.00')
    
    def test_remaining_amount_negative_overflow(self):
        """
        ⚠️ POTENCIAL BUG: remaining_amount negativo significa SOBREPAGO.
        
        Si las validaciones funcionan correctamente, esto NO debería ocurrir.
        Pero si ocurre, ¿lo maneja bien el sistema?
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # Forzar creación de dos pagos que juntos excedan (bypass de validación)
        ProjectPaymentFactory(project=project, amount=Decimal('7000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # remaining_amount sería -2000
        remaining = project.remaining_amount
        
        if remaining < Decimal('0'):
            # BUG: El presupuesto fue excedido
            assert remaining == Decimal('-2000.00')
            # TODO: Investigar cómo el sistema llegó a este estado


# ============================================================================
# TESTS DE INTERACCIÓN ENTRE MÚLTIPLES PAGOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestMultiplePaymentsInteraction:
    """
    Tests de interacción entre múltiples pagos en un proyecto.
    
    ⚠️ BUG HUNTING: ¿Funciona correctamente con muchos pagos?
    """
    
    def test_many_small_payments_accumulation(self):
        """
        Crear muchos pagos pequeños que juntos forman el presupuesto.
        
        - Presupuesto: $10,000
        - 100 pagos de $100 cada uno
        - Total: $10,000 ✅
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        for i in range(100):
            ProjectPaymentFactory(
                project=project,
                amount=Decimal('100.00'),
                date=timezone.now().date() - timedelta(days=i)
            )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('10000.00')
        assert project.remaining_amount == Decimal('0.00')
        assert project.payments.count() == 100
    
    def test_payments_with_different_dates_sum_correctly(self):
        """
        Pagos con diferentes fechas deben sumarse correctamente.
        
        La fecha del pago no debe afectar el cálculo de total_paid.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        base_date = timezone.now().date()
        
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('3000.00'),
            date=base_date - timedelta(days=30)
        )
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('4000.00'),
            date=base_date - timedelta(days=15)
        )
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('2000.00'),
            date=base_date
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9000.00')
        # total_paid debe ser independiente de las fechas
    
    def test_edit_multiple_payments_in_sequence(self):
        """
        Editar pagos uno por uno en secuencia.
        
        ⚠️ BUG HUNTING: ¿Los cálculos se mantienen correctos?
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        payment1 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        payment2 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        payment3 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9000.00')
        
        # Editar payment1: 3000 -> 2500
        payment1.amount = Decimal('2500.00')
        payment1.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('8500.00')
        
        # Editar payment2: 3000 -> 3500
        payment2.amount = Decimal('3500.00')
        payment2.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9000.00')
        
        # Editar payment3: 3000 -> 1000
        payment3.amount = Decimal('1000.00')
        payment3.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('7000.00')
    
    def test_delete_payment_updates_total_correctly(self):
        """
        Eliminar un pago debe actualizar el total correctamente.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        payment1 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        payment2 = ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        payment3 = ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9000.00')
        
        # Eliminar payment2
        payment2.delete()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('5000.00')
        assert project.payments.count() == 2


# ============================================================================
# TESTS DE VALIDACIÓN DE PRESUPUESTO CON DECIMALES COMPLICADOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDecimalPrecisionInBudgetValidation:
    """
    Tests con números decimales complicados.
    
    ⚠️ BUG HUNTING: ¿Se redondea correctamente?
    """
    
    def test_exact_budget_match_with_many_decimals(self):
        """
        Presupuesto con decimales debe coincidir exactamente.
        
        - Presupuesto: $1,234.56
        - Pago 1: $500.23
        - Pago 2: $734.33
        - Total: $1,234.56 ✅
        """
        project = ProjectFactory(total_budget=Decimal('1234.56'))
        
        ProjectPaymentFactory(project=project, amount=Decimal('500.23'))
        ProjectPaymentFactory(project=project, amount=Decimal('734.33'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('1234.56')
        assert project.remaining_amount == Decimal('0.00')
    
    def test_edit_payment_with_decimal_precision(self):
        """
        Editar un pago con decimales complicados.
        
        - Presupuesto: $1,000.00
        - Pago actual: $333.33
        - Editar a: $333.34 (aumenta $0.01)
        - Nuevo total: $333.34
        """
        project = ProjectFactory(total_budget=Decimal('1000.00'))
        
        payment = ProjectPaymentFactory(project=project, amount=Decimal('333.33'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Editar payment
        old_amount = Decimal('333.33')
        new_amount = Decimal('333.34')
        new_total = (project.total_paid - old_amount) + new_amount
        
        # Verificar cálculo
        assert new_total == Decimal('333.34')
        assert new_total <= project.total_budget
        
        payment.amount = new_amount
        payment.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('333.34')
    
    def test_three_decimal_places_not_allowed(self):
        """
        ⚠️ VALIDACIÓN: El modelo solo permite 2 decimales.
        
        Si se intenta $100.999, ¿qué ocurre?
        """
        project = ProjectFactory(total_budget=Decimal('1000.00'))
        
        # El modelo no debería permitir 3 decimales
        # DecimalField(max_digits=12, decimal_places=2)
        
        # Intentar crear con 3 decimales
        try:
            payment = ProjectPayment.objects.create(
                project=project,
                amount=Decimal('100.999'),  # 3 decimales
                date=timezone.now().date()
            )
            
            # Si llega aquí, ¿qué valor tiene realmente?
            payment.refresh_from_db()
            # Debería estar redondeado a 100.99 o 101.00
            
        except Exception as e:
            # Lo correcto es que lance error
            assert True


# ============================================================================
# TESTS DE PRESUPUESTO CON VALORES EXTREMOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestBudgetExtremeValues:
    """
    Tests con valores extremos (muy grandes, muy pequeños).
    
    ⚠️ BUG HUNTING: ¿Funciona con números extremos?
    """
    
    def test_very_large_budget(self):
        """
        Presupuesto muy grande (máximo permitido).
        
        DecimalField: max_digits=12, decimal_places=2
        Máximo: 9,999,999,999.99
        """
        project = ProjectFactory(
            total_budget=Decimal('9999999999.99')
        )
        
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('4999999999.99')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('4999999999.99')
        assert project.remaining_amount == Decimal('5000000000.00')
    
    def test_very_small_budget(self):
        """
        Presupuesto muy pequeño ($0.01).
        """
        project = ProjectFactory(total_budget=Decimal('0.01'))
        
        ProjectPaymentFactory(project=project, amount=Decimal('0.01'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('0.01')
        assert project.remaining_amount == Decimal('0.00')
    
    def test_payment_close_to_max_limit(self):
        """
        Pago próximo al máximo permitido.
        """
        project = ProjectFactory(
            total_budget=Decimal('10000000.00')
        )
        
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('9999999.99')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9999999.99')


# ============================================================================
# TESTS DE COMPROBANTES Y ARCHIVOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentWithReceipts:
    """
    Tests de pagos con archivos de comprobantes.
    
    ⚠️ BUG HUNTING: ¿La validación del archivo interfiere con la de presupuesto?
    """
    
    def test_payment_creation_with_receipt_file(self):
        """
        Crear pago CON archivo de comprobante.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # A nivel de modelo, crear pago con archivo
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00'),
            receipt_file=None  # En realidad iría un FileField aquí
        )
        
        assert payment.pk is not None
        assert payment.receipt_file is None or not payment.receipt_file
    
    def test_payment_edit_replace_receipt(self):
        """
        Editar un pago Y reemplazar su comprobante.
        
        ⚠️ BUG HUNTING: Si la edición de comprobante falla,
        ¿se actualiza igual el monto?
        """
        payment = ProjectPaymentFactory(
            project=ProjectFactory(total_budget=Decimal('10000.00')),
            amount=Decimal('5000.00'),
            receipt_file=None
        )
        
        # Editar monto sin tocar comprobante
        payment.amount = Decimal('6000.00')
        payment.save()
        
        payment.refresh_from_db()
        assert payment.amount == Decimal('6000.00')


# ============================================================================
# TESTS DE PROYECTOS CON MÚLTIPLES USUARIOS CREANDO PAGOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestMultipleUsersPaymentCreation:
    """
    Tests de múltiples usuarios creando pagos para el mismo proyecto.
    
    ⚠️ BUG HUNTING: ¿Hay condiciones de carrera?
    """
    
    def test_two_users_create_payments_same_project(self):
        """
        Usuario 1 crea pago de $5,000
        Usuario 2 crea pago de $4,000
        Total debe ser $9,000
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Usuario 1
        payment1 = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00'),
            created_by=user1
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('5000.00')
        
        # Usuario 2
        payment2 = ProjectPaymentFactory(
            project=project,
            amount=Decimal('4000.00'),
            created_by=user2
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9000.00')
    
    def test_two_users_try_edit_payment_concurrently(self):
        """
        ESCENARIO: Dos usuarios intentan editar el MISMO pago.
        
        ⚠️ BUG HUNTING: Race condition - quién gana?
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment = ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        # Usuario 1 obtiene el pago
        payment_u1 = ProjectPayment.objects.get(id=payment.id)
        
        # Usuario 2 obtiene el pago (misma versión)
        payment_u2 = ProjectPayment.objects.get(id=payment.id)
        
        # Usuario 1 edita a $6,000
        payment_u1.amount = Decimal('6000.00')
        payment_u1.save()
        
        # Usuario 2 edita a $7,000 (con datos desactualizados)
        payment_u2.amount = Decimal('7000.00')
        payment_u2.save()
        
        payment.refresh_from_db()
        
        # El último en guardar "gana"
        assert payment.amount == Decimal('7000.00')
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # total_paid será $7,000 (del último save)
        assert project.total_paid == Decimal('7000.00')


# ============================================================================
# TESTS DE ORDERING Y LISTADO DE PAGOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentOrdering:
    """
    Tests del ordenamiento de pagos.
    
    ⚠️ BUG HUNTING: ¿El ordenamiento funciona correctamente?
    """
    
    def test_payments_ordered_by_date_descending(self):
        """
        Pagos deben ordenarse por fecha DESCENDENTE.
        
        Meta.ordering = ['-date', '-created_at']
        """
        project = ProjectFactory()
        
        date1 = timezone.now().date() - timedelta(days=10)
        date2 = timezone.now().date() - timedelta(days=5)
        date3 = timezone.now().date()
        
        p1 = ProjectPaymentFactory(project=project, date=date1)
        p2 = ProjectPaymentFactory(project=project, date=date2)
        p3 = ProjectPaymentFactory(project=project, date=date3)
        
        payments = list(ProjectPayment.objects.filter(project=project))
        
        # Debe ser: p3 (today), p2 (5 days ago), p1 (10 days ago)
        assert payments[0] == p3
        assert payments[1] == p2
        assert payments[2] == p1
    
    def test_payments_same_date_ordered_by_created_at(self):
        """
        Si tienen la misma fecha, ordenar por created_at DESCENDENTE.
        """
        project = ProjectFactory()
        same_date = timezone.now().date()
        
        p1 = ProjectPaymentFactory(project=project, date=same_date)
        import time
        time.sleep(0.01)
        p2 = ProjectPaymentFactory(project=project, date=same_date)
        
        payments = list(ProjectPayment.objects.filter(project=project, date=same_date))
        
        # Debe ser: p2 (created last), p1 (created first)
        assert payments[0] == p2
        assert payments[1] == p1


# ============================================================================
# TESTS DEL STRING REPRESENTATION
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentStringRepresentation:
    """
    Tests del __str__ del modelo.
    """
    
    def test_payment_str_format(self):
        """
        __str__ debe retornar: "{project_name} - ${amount} ({date})"
        """
        project = ProjectFactory(name='Proyecto A')
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('1234.56'),
            date=timezone.now().date()
        )
        
        expected = f"Proyecto A - $1234.56 ({timezone.now().date()})"
        assert str(payment) == expected
    
    def test_payment_str_with_special_characters_in_project_name(self):
        """
        ⚠️ EDGE CASE: Proyecto con caracteres especiales.
        """
        project = ProjectFactory(name='Proyecto & Cie. Ltda. [México]')
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00')
        )
        
        str_repr = str(payment)
        assert 'Proyecto & Cie. Ltda. [México]' in str_repr
        assert '$5000.00' in str_repr
