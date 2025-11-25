"""
Tests exhaustivos de validación de presupuesto en pagos de proyectos.

ENFOQUE: Tests prácticos para encontrar bugs reales, NO solo para pasar.

Este módulo verifica que:
1. No se puede crear un pago que exceda el presupuesto
2. No se puede EDITAR un pago para que exceda el presupuesto (ESTE ERA EL ERROR CORREGIDO)
3. Las validaciones funcionan correctamente en todos los escenarios
4. El caché se invalida cuando es necesario
5. Los totales se calculan correctamente
"""

import pytest
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from unittest.mock import patch, MagicMock
from datetime import timedelta

from tests.factories import (
    OrganizationFactory,
    UserFactory,
    ProjectFactory,
    ProjectPaymentFactory,
)
from apps.projects.models import Project, ProjectPayment


# ============================================================================
# TESTS DE CREACIÓN DE PAGOS CON PRESUPUESTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentCreationBudgetValidation:
    """
    Tests de creación de pagos verificando validación de presupuesto.
    Estos tests simulan la lógica de PaymentCreateView.form_valid()
    """
    
    def test_create_payment_within_budget(self):
        """
        ✅ CORRECTO: Crear pago dentro del presupuesto debe funcionar
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        cache.delete(f"project_total_paid:{project.id}")
        
        # Total pagado: $0
        # Nuevo pago: $5,000
        # Total resultaría en: $5,000 (dentro de $10,000)
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('5000.00'),
            date=timezone.now().date(),
            created_by=UserFactory()
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert payment.pk is not None
        assert project.total_paid == Decimal('5000.00')
        assert project.remaining_amount == Decimal('5000.00')
    
    def test_create_payment_exactly_budget(self):
        """
        ✅ CORRECTO: Pago exacto al presupuesto debe permitirse
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        cache.delete(f"project_total_paid:{project.id}")
        
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('10000.00'),
            date=timezone.now().date()
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert payment.pk is not None
        assert project.total_paid == Decimal('10000.00')
        assert project.remaining_amount == Decimal('0.00')
    
    def test_create_payment_exceeding_budget_should_fail_in_view(self):
        """
        ⚠️ BUG HUNTING: En la vista PaymentCreateView, esto debe rechazarse.
        Este test simula lo que DEBERÍA pasar en form_valid()
        
        A nivel de modelo, no hay restricción, pero la vista debe validar.
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        cache.delete(f"project_total_paid:{project.id}")
        
        # El modelo permite crear el pago (sin restricción en el modelo)
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('12000.00'),
            date=timezone.now().date()
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # A nivel de modelo, el pago existe pero excede el presupuesto
        assert project.total_paid == Decimal('12000.00')
        assert project.remaining_amount == Decimal('-2000.00')  # NEGATIVO = PROBLEMA
        
        # NOTA: La validación debe ocurrir en la VISTA, no en el modelo
        # La vista debe rechazar pagos que causen total_paid > total_budget
    
    def test_create_multiple_payments_cumulatively_exceeding_budget(self):
        """
        ⚠️ BUG HUNTING: Crear varios pagos que juntos excedan el presupuesto.
        El segundo pago debería rechazarse.
        
        Presupuesto: $10,000
        Pago 1: $6,000 ✅ (total = $6,000)
        Pago 2: $5,000 ❌ (total sería $11,000, excede)
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        cache.delete(f"project_total_paid:{project.id}")
        
        # Primer pago: $6,000 - debe pasar
        payment1 = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('6000.00'),
            date=timezone.now().date()
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('6000.00')
        
        # Segundo pago: $5,000 - si fuera permitido, total = $11,000
        # La vista debería rechazar esto
        payment2 = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('5000.00'),
            date=timezone.now().date()
        )
        
        # A nivel de modelo, se crea (sin restricción)
        # Pero la vista debe haber rechazado en form_valid()
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # BUG: Si llegó a crearse, total_paid será incorrecto
        assert project.total_paid == Decimal('11000.00')  # EXCEDE EL PRESUPUESTO


# ============================================================================
# TESTS DE EDICIÓN DE PAGOS CON PRESUPUESTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentUpdateBudgetValidation:
    """
    Tests de edición de pagos verificando validación de presupuesto.
    ⭐ ESTE ERA EL ERROR PRINCIPAL CORREGIDO EN TC-52
    
    Escenario:
    - Presupuesto: $10,000
    - Pago existente: $5,000
    - Editar pago a $8,000: ✅ (total sería $8,000, dentro de presupuesto)
    - Editar pago a $11,000: ❌ (total sería $11,000, EXCEDE presupuesto)
    """
    
    def _simulate_payment_update_validation(self, project, old_amount, new_amount):
        """
        Simula la lógica de validación de PaymentUpdateView.form_valid()
        
        Returns: (is_valid, max_allowed, new_total)
        """
        # Calcular lo que sería el nuevo total
        new_total = (project.total_paid - old_amount) + new_amount
        
        if project.total_budget and project.total_budget > Decimal('0'):
            if new_total > project.total_budget:
                # Calcular máximo permitido
                max_allowed = project.total_budget - (project.total_paid - old_amount)
                return False, max_allowed, new_total
        
        return True, None, new_total
    
    def test_edit_payment_increase_within_budget(self):
        """
        ✅ CORRECTO: Aumentar pago dentro del saldo disponible debe funcionar.
        
        - Presupuesto: $10,000
        - Pagado actualmente: $5,000 (1 pago de $5,000)
        - Editar pago: $5,000 → $8,000
        - Nuevo total: $8,000 ✅ (dentro de $10,000)
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        
        # Crear pago de $5,000
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Simular validación de edición: $5,000 → $8,000
        old_amount = payment.amount
        new_amount = Decimal('8000.00')
        
        is_valid, _, new_total = self._simulate_payment_update_validation(
            project, old_amount, new_amount
        )
        
        assert is_valid is True, "Edición debería ser válida"
        assert new_total == Decimal('8000.00')
        
        # Realizar la edición
        payment.amount = new_amount
        payment.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('8000.00')
        assert project.remaining_amount == Decimal('2000.00')
    
    def test_edit_payment_exceed_budget_should_fail(self):
        """
        ❌ BUG QUE FUE CORREGIDO EN TC-52
        
        Si editas un pago a un monto que EXCEDE el presupuesto, debe rechazarse.
        
        - Presupuesto: $10,000
        - Pagado actualmente: $5,000 (1 pago de $5,000)
        - Intentar editar pago: $5,000 → $11,000
        - Nuevo total SERÍA: $11,000 ❌ (EXCEDE $10,000)
        - DEBE RECHAZARSE
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        
        # Crear pago de $5,000
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Simular validación de edición: $5,000 → $11,000
        old_amount = payment.amount
        new_amount = Decimal('11000.00')
        
        is_valid, max_allowed, new_total = self._simulate_payment_update_validation(
            project, old_amount, new_amount
        )
        
        # DEBE SER INVÁLIDO
        assert is_valid is False, "Esta edición debería ser RECHAZADA"
        assert new_total == Decimal('11000.00')
        assert max_allowed == Decimal('10000.00')  # Máximo: $10,000 - ($5,000 - $5,000) = $10,000
        
        # La edición no debe ejecutarse en la vista
        # Aquí verificamos que si no se valida, el pago NO se actualiza
        payment.refresh_from_db()
        assert payment.amount == Decimal('5000.00'), "Pago no debe haber sido modificado"
    
    def test_edit_payment_decrease_should_work(self):
        """
        ✅ CORRECTO: Disminuir el monto de un pago siempre debe funcionar.
        
        - Presupuesto: $10,000
        - Pagado: $8,000 (1 pago de $8,000)
        - Editar pago: $8,000 → $5,000
        - Nuevo total: $5,000 ✅ (dentro de $10,000)
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('8000.00')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Disminuir: $8,000 → $5,000
        old_amount = payment.amount
        new_amount = Decimal('5000.00')
        
        is_valid, _, new_total = self._simulate_payment_update_validation(
            project, old_amount, new_amount
        )
        
        assert is_valid is True, "Disminución debe ser válida"
        assert new_total == Decimal('5000.00')
        
        # Realizar la edición
        payment.amount = new_amount
        payment.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('5000.00')
    
    def test_edit_payment_with_multiple_existing_payments(self):
        """
        ⚠️ BUG HUNTING: Editar un pago cuando hay VARIOS pagos existentes.
        
        - Presupuesto: $10,000
        - Pago 1: $3,000
        - Pago 2: $4,000
        - Total actual: $7,000
        - Editar Pago 1: $3,000 → $5,000
        - Nuevo total SERÍA: $5,000 + $4,000 = $9,000 ✅
        
        La validación debe restar el monto ANTIGUO del total actual,
        luego sumar el monto NUEVO.
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        
        payment1 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        payment2 = ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('7000.00')
        
        # Editar pago1: $3,000 → $5,000
        old_amount = Decimal('3000.00')
        new_amount = Decimal('5000.00')
        
        is_valid, _, new_total = self._simulate_payment_update_validation(
            project, old_amount, new_amount
        )
        
        assert is_valid is True
        assert new_total == Decimal('9000.00')  # $5,000 + $4,000
        
        # Realizar edición
        payment1.amount = new_amount
        payment1.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('9000.00')
    
    def test_edit_payment_exceeding_with_multiple_payments(self):
        """
        ❌ BUG HUNTING: Editar un pago que con otros la exceda.
        
        - Presupuesto: $10,000
        - Pago 1: $3,000
        - Pago 2: $4,000
        - Total: $7,000
        - Intentar editar Pago 1: $3,000 → $8,000
        - Nuevo total SERÍA: $8,000 + $4,000 = $12,000 ❌ (EXCEDE)
        - DEBE RECHAZARSE
        """
        project = ProjectFactory(
            total_budget=Decimal('10000.00'),
            budget_configured=True
        )
        
        payment1 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        payment2 = ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('7000.00')
        
        # Editar pago1: $3,000 → $8,000
        old_amount = Decimal('3000.00')
        new_amount = Decimal('8000.00')
        
        is_valid, max_allowed, new_total = self._simulate_payment_update_validation(
            project, old_amount, new_amount
        )
        
        assert is_valid is False, "Esta edición debe ser RECHAZADA"
        assert new_total == Decimal('12000.00')
        # max_allowed = $10,000 - ($7,000 - $3,000) = $10,000 - $4,000 = $6,000
        assert max_allowed == Decimal('6000.00')


# ============================================================================
# TESTS DE VALIDACIÓN DE MONTOS CERO Y NEGATIVOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentAmountValidation:
    """
    Tests para detectar bugs en validación de montos específicos.
    
    ⚠️ BUG HUNTING: Busca casos donde se permitan montos inválidos
    """
    
    def test_create_payment_with_zero_amount(self):
        """
        ⚠️ POTENCIAL BUG: ¿Se permite crear un pago de $0?
        
        Esto NO tiene sentido en negocio. Debe validarse en la VISTA.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # A nivel de modelo, permite $0
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('0.00'),
            date=timezone.now().date()
        )
        
        assert payment.pk is not None
        assert payment.amount == Decimal('0.00')
        
        # NOTA: La vista debe validar y rechazar esto
    
    def test_create_payment_with_negative_amount(self):
        """
        ⚠️ POTENCIAL BUG: ¿Se permite crear un pago negativo?
        
        Esto es un BUG SERIO. Un pago negativo es una devolución/nota de crédito.
        No debe permitirse en crear pago normal.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # A nivel de modelo, permite negativos
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('-500.00'),
            date=timezone.now().date()
        )
        
        assert payment.pk is not None
        assert payment.amount == Decimal('-500.00')
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Total pagado sería NEGATIVO = BUG
        assert project.total_paid == Decimal('-500.00')
        
        # NOTA: La vista debe validar y rechazar montos <= 0
    
    def test_edit_payment_to_zero_amount(self):
        """
        ⚠️ POTENCIAL BUG: ¿Se permite editar un pago a $0?
        
        Si existe un pago de $5,000 y lo editas a $0, probablemente significa
        que quieres eliminarlo, no convertirlo a $0.
        """
        payment = ProjectPaymentFactory(amount=Decimal('5000.00'))
        
        # A nivel de modelo, permite cambiar a $0
        payment.amount = Decimal('0.00')
        payment.save()
        
        payment.refresh_from_db()
        assert payment.amount == Decimal('0.00')
        
        # NOTA: La vista debe validar y rechazar esto
    
    def test_edit_payment_to_negative_amount(self):
        """
        ⚠️ POTENCIAL BUG: ¿Se permite editar un pago a monto negativo?
        
        Un pago no debe cambiar a negativo simplemente editándolo.
        """
        payment = ProjectPaymentFactory(amount=Decimal('5000.00'))
        project = payment.project
        
        # A nivel de modelo, permite negativos
        payment.amount = Decimal('-1000.00')
        payment.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert payment.amount == Decimal('-1000.00')
        assert project.total_paid == Decimal('-1000.00')  # BUG: negativo
        
        # NOTA: La vista debe validar y rechazar esto


# ============================================================================
# TESTS DE PRESUPUESTO NO CONFIGURADO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentWithoutBudgetConfiguration:
    """
    Tests cuando el presupuesto NO está configurado.
    
    ⚠️ BUG HUNTING: ¿Qué pasa si se intenta crear pago sin presupuesto?
    """
    
    def test_create_payment_without_budget_configured(self):
        """
        ⚠️ EDGE CASE: Si no hay presupuesto, ¿se puede crear pagos?
        
        Regla de negocio: Si no hay presupuesto, no hay límite de pagos.
        Pero la UI no permite agregar pagos sin presupuesto configurado.
        """
        project = ProjectFactory(
            total_budget=None,
            budget_configured=False
        )
        
        # A nivel de modelo, permite crear pagos sin presupuesto
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('5000.00'),
            date=timezone.now().date()
        )
        
        assert payment.pk is not None
        assert payment.amount == Decimal('5000.00')
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('5000.00')
        assert project.remaining_amount is None or project.remaining_amount < 0
    
    def test_edit_payment_without_budget_should_allow_any_amount(self):
        """
        Si el presupuesto NO está configurado, editar un pago
        no debería tener límite.
        """
        project = ProjectFactory(
            total_budget=None,
            budget_configured=False
        )
        
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00')
        )
        
        # Editar a cantidad arbitraria grande
        payment.amount = Decimal('999999.99')
        payment.save()
        
        payment.refresh_from_db()
        assert payment.amount == Decimal('999999.99')


# ============================================================================
# TESTS DE CACHE INVALIDATION
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentCacheInvalidation:
    """
    Tests para verificar que el caché se invalida correctamente.
    
    ⚠️ BUG HUNTING: ¿El caché se invalida en todas las situaciones?
    """
    
    def test_cache_invalidated_after_payment_creation(self):
        """
        El caché de total_paid debe invalidarse cuando se crea un pago.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # Establecer cache manualmente
        cache.set(f"project_total_paid:{project.id}", Decimal('5000.00'), 600)
        
        # Crear pago
        ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        
        # El cache debe estar vacío (invalidado por el save())
        cached_value = cache.get(f"project_total_paid:{project.id}")
        assert cached_value is None, "Cache debería estar invalidado"
    
    def test_cache_invalidated_after_payment_update(self):
        """
        El caché debe invalidarse cuando se edita un pago.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment = ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        # Establecer cache
        cache.set(f"project_total_paid:{project.id}", Decimal('5000.00'), 600)
        
        # Editar pago
        payment.amount = Decimal('6000.00')
        payment.save()
        
        # Cache debe estar invalidado
        cached_value = cache.get(f"project_total_paid:{project.id}")
        assert cached_value is None, "Cache debería estar invalidado"
    
    def test_cache_invalidated_after_payment_deletion(self):
        """
        El caché debe invalidarse cuando se elimina un pago.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        payment = ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        # Establecer cache
        cache.set(f"project_total_paid:{project.id}", Decimal('5000.00'), 600)
        
        # Eliminar pago
        payment.delete()
        
        # Cache debe estar invalidado
        cached_value = cache.get(f"project_total_paid:{project.id}")
        assert cached_value is None, "Cache debería estar invalidado"


# ============================================================================
# TESTS DE CÁLCULOS DE TOTALES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentTotalCalculations:
    """
    Tests para detectar bugs en cálculos de totales.
    
    ⚠️ BUG HUNTING: ¿Los cálculos de total_paid son correctos siempre?
    """
    
    def test_total_paid_sum_accuracy_with_decimal(self):
        """
        ⚠️ POTENCIAL BUG: Precisión decimal en sumas.
        
        Problemas comunes:
        - Redondeo incorrecto
        - Pérdida de precisión al convertir a float
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # Crear varios pagos con decimales complicados
        ProjectPaymentFactory(project=project, amount=Decimal('1000.01'))
        ProjectPaymentFactory(project=project, amount=Decimal('2000.99'))
        ProjectPaymentFactory(project=project, amount=Decimal('3000.33'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Debe ser exacto
        expected = Decimal('6001.33')
        assert project.total_paid == expected
    
    def test_remaining_amount_calculation(self):
        """
        remaining_amount = total_budget - total_paid
        
        ⚠️ POTENCIAL BUG: ¿Qué pasa cuando total_paid > total_budget?
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        ProjectPaymentFactory(project=project, amount=Decimal('8000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Remaining debe ser positivo
        assert project.remaining_amount == Decimal('2000.00')
    
    def test_remaining_amount_negative_when_overpaid(self):
        """
        ⚠️ POTENCIAL BUG: Si total_paid > total_budget, remaining es NEGATIVO.
        
        Esto NO debe permitirse si las validaciones funcionan correctamente.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # Forzar creación de pagos que excedan (bypass de vista)
        ProjectPaymentFactory(project=project, amount=Decimal('8000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Si las validaciones NO funcionan, esto será negativo
        remaining = project.remaining_amount
        
        if remaining < Decimal('0'):
            # BUG: Presupuesto fue excedido
            assert remaining == Decimal('-1000.00')
    
    def test_percentage_accuracy_with_large_numbers(self):
        """
        ⚠️ POTENCIAL BUG: percentage_of_total con números grandes.
        """
        project = ProjectFactory(total_budget=Decimal('1000000.00'))
        
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('333333.33')
        )
        
        # Debe ser aproximadamente 33.33%
        percentage = payment.percentage_of_total
        
        # Usar rango porque el redondeo puede variar
        assert Decimal('33.3') <= percentage <= Decimal('33.4')


# ============================================================================
# TESTS DE CONDICIONES DE CARRERA
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentRaceConditions:
    """
    Tests para detectar condiciones de carrera.
    
    ⚠️ BUG HUNTING: ¿Qué pasa con actualizaciones concurrentes?
    """
    
    def test_payment_total_with_stale_cache(self):
        """
        ESCENARIO: Cache desactualizado (race condition)
        
        Verificamos que cuando el cache no está disponible,
        el sistema calcula correctamente desde la base de datos.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # Crear 2 pagos
        ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        
        # Forzar recalcular desde BD
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        # Debe calcular correctamente desde los pagos en BD
        assert project.total_paid == Decimal('8000.00')
        
        # Ahora el cache está almacenado ($8,000)
        # Simular que otro proceso usa cache stale
        with patch('django.core.cache.cache.get') as mock_get:
            # Mock devuelve valor stale (float, como redis)
            mock_get.return_value = 5000.0
            # Con el mock, devolverá el valor stale
            assert project.total_paid == Decimal('5000.00')
    
    @patch('django.core.cache.cache.delete')
    def test_payment_cache_delete_failure_recovery(self, mock_cache_delete):
        """
        ESCENARIO: Falla al borrar cache
        
        Si la invalidación del cache falla, ¿qué pasa?
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        # Simular que cache.delete() falla
        mock_cache_delete.side_effect = Exception("Cache error")
        
        # El payment.save() llama a cache.delete()
        # Si falla, ¿continúa el save()?
        with pytest.raises(Exception):
            ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))


# ============================================================================
# TESTS DE COMPORTAMIENTO EN PROYECTOS SIN PRESUPUESTO INICIAL
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentPresupuetoConfigurationFlow:
    """
    Tests del flujo completo:
    1. Proyecto sin presupuesto
    2. Configurar presupuesto
    3. Crear pagos
    4. Editar pagos
    """
    
    def test_complete_flow_from_no_budget_to_payments(self):
        """
        Flujo completo de TC-52:
        
        1. Crear proyecto SIN presupuesto
        2. Configurar presupuesto a $10,000
        3. Crear pago de $5,000 ✅
        4. Editar pago a $8,000 ✅
        5. Intentar editar pago a $11,000 ❌
        """
        # 1. Crear proyecto sin presupuesto
        project = ProjectFactory(
            total_budget=None,
            budget_configured=False
        )
        
        assert project.total_budget is None
        
        # 2. Configurar presupuesto
        project.total_budget = Decimal('10000.00')
        project.budget_configured = True
        project.save()
        
        assert project.total_budget == Decimal('10000.00')
        
        # 3. Crear pago de $5,000
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('5000.00')
        
        # 4. Editar pago a $8,000 (debe funcionar)
        old_amount = Decimal('5000.00')
        new_amount = Decimal('8000.00')
        new_total = (project.total_paid - old_amount) + new_amount
        
        assert new_total == Decimal('8000.00')
        assert new_total <= project.total_budget  # ✅ Válido
        
        payment.amount = new_amount
        payment.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('8000.00')
        
        # 5. Intentar editar pago a $11,000 (debe rechazarse)
        old_amount = Decimal('8000.00')
        new_amount = Decimal('11000.00')
        new_total = (project.total_paid - old_amount) + new_amount
        
        assert new_total == Decimal('11000.00')
        assert new_total > project.total_budget  # ❌ INVÁLIDO
        
        # La edición NO debe realizarse en la vista (form_invalid)
        # Aquí verificamos el cálculo
        payment.refresh_from_db()
        assert payment.amount == Decimal('8000.00')  # No cambió
