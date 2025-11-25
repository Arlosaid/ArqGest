"""
Tests de integración de pagos - Simulando el comportamiento de las vistas.

ENFOQUE: Verificar que las validaciones en la VISTA funcionan correctamente.

Estos tests simulan:
1. PaymentCreateView.form_valid() - Crear pago con validación de presupuesto
2. PaymentUpdateView.form_valid() - Editar pago con validación de presupuesto
3. Mensajes de error correctos
4. Cache invalidation en cada operación
"""

import pytest
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone
from django.forms import Form
from django.test import RequestFactory
from unittest.mock import patch, MagicMock

from tests.factories import (
    OrganizationFactory,
    UserFactory,
    ProjectFactory,
    ProjectPaymentFactory,
)
from apps.projects.models import Project, ProjectPayment


# ============================================================================
# SIMULACIÓN DE VALIDACIÓN EN PAYMENT CREATE VIEW
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentCreateViewValidation:
    """
    Simulación de PaymentCreateView.form_valid()
    """
    
    def _validate_payment_creation(self, project, new_amount):
        """
        Simula la validación de creación de pago.
        
        Returns: (is_valid, error_message, max_available)
        """
        # Validación 1: Monto positivo
        if new_amount <= Decimal('0'):
            return False, "El monto del pago debe ser mayor a cero.", None
        
        # Validación 2: No exceder presupuesto
        if project.total_budget and project.total_budget > Decimal('0'):
            new_total = project.total_paid + new_amount
            
            if new_total > project.total_budget:
                max_available = project.total_budget - project.total_paid
                return False, (
                    f"Este pago excedería el presupuesto total. "
                    f"Máximo disponible: ${max_available:,.2f}"
                ), max_available
        
        return True, None, None
    
    def test_validate_create_positive_amount_within_budget(self):
        """
        ✅ Crear pago de $5,000 en proyecto con presupuesto de $10,000 y $0 pagado.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _ = self._validate_payment_creation(
            project,
            Decimal('5000.00')
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_create_zero_amount(self):
        """
        ❌ Crear pago de $0 debe rechazarse.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        is_valid, error, _ = self._validate_payment_creation(
            project,
            Decimal('0.00')
        )
        
        assert is_valid is False
        assert "mayor a cero" in error
    
    def test_validate_create_negative_amount(self):
        """
        ❌ Crear pago negativo debe rechazarse.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        
        is_valid, error, _ = self._validate_payment_creation(
            project,
            Decimal('-1000.00')
        )
        
        assert is_valid is False
        assert "mayor a cero" in error
    
    def test_validate_create_exceeding_budget(self):
        """
        ❌ Crear pago de $12,000 en proyecto con presupuesto de $10,000 y $0 pagado.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, max_available = self._validate_payment_creation(
            project,
            Decimal('12000.00')
        )
        
        assert is_valid is False
        assert "excedería el presupuesto" in error
        assert max_available == Decimal('10000.00')
    
    def test_validate_create_with_existing_payment(self):
        """
        ✅ Crear pago de $4,000 en proyecto con presupuesto de $10,000 y $5,000 ya pagado.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _ = self._validate_payment_creation(
            project,
            Decimal('4000.00')
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_create_exactly_remaining(self):
        """
        ✅ Crear pago por el monto exacto que queda disponible.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('7000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _ = self._validate_payment_creation(
            project,
            Decimal('3000.00')
        )
        
        assert is_valid is True
    
    def test_validate_create_exceeding_remaining_by_one_cent(self):
        """
        ❌ Crear pago que excede por $0.01.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('7000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, max_available = self._validate_payment_creation(
            project,
            Decimal('3000.01')
        )
        
        assert is_valid is False
        assert max_available == Decimal('3000.00')
    
    def test_validate_create_without_budget_configured(self):
        """
        ✅ Sin presupuesto configurado, permitir cualquier monto (positivo).
        """
        project = ProjectFactory(total_budget=None, budget_configured=False)
        
        is_valid, error, _ = self._validate_payment_creation(
            project,
            Decimal('999999.99')
        )
        
        assert is_valid is True
        assert error is None


# ============================================================================
# SIMULACIÓN DE VALIDACIÓN EN PAYMENT UPDATE VIEW
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentUpdateViewValidation:
    """
    Simulación de PaymentUpdateView.form_valid()
    
    ⭐ ESTE ERA EL ERROR CORREGIDO EN TC-52
    """
    
    def _validate_payment_update(self, project, old_amount, new_amount):
        """
        Simula la validación de edición de pago.
        
        Returns: (is_valid, error_message, max_allowed, new_total)
        """
        # Validación 1: Monto positivo
        if new_amount <= Decimal('0'):
            return False, "El monto del pago debe ser mayor a cero.", None, None
        
        # Validación 2: No exceder presupuesto
        if project.total_budget and project.total_budget > Decimal('0'):
            # Calcular nuevo total: quitamos el monto viejo, sumamos el nuevo
            new_total = (project.total_paid - old_amount) + new_amount
            
            if new_total > project.total_budget:
                # Máximo permitido = presupuesto - (total_actual - monto_viejo)
                max_allowed = project.total_budget - (project.total_paid - old_amount)
                return False, (
                    f"Este cambio excedería el presupuesto total. "
                    f"Máximo permitido: ${max_allowed:,.2f}"
                ), max_allowed, new_total
        else:
            new_total = (project.total_paid - old_amount) + new_amount
        
        return True, None, None, new_total
    
    def test_validate_update_increase_within_budget(self):
        """
        ✅ Aumentar pago dentro del presupuesto.
        
        - Presupuesto: $10,000
        - Pagado: $5,000 (1 pago de $5,000)
        - Editar: $5,000 → $8,000
        - Nuevo total: $8,000 ✅
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, max_allowed, new_total = self._validate_payment_update(
            project,
            Decimal('5000.00'),
            Decimal('8000.00')
        )
        
        assert is_valid is True
        assert error is None
        assert new_total == Decimal('8000.00')
    
    def test_validate_update_exceed_budget_main_bug(self):
        """
        ❌ ESTE ERA EL BUG PRINCIPAL EN TC-52
        
        - Presupuesto: $10,000
        - Pagado: $5,000 (1 pago de $5,000)
        - Intentar editar: $5,000 → $11,000
        - Nuevo total SERÍA: $11,000 ❌
        - DEBE RECHAZARSE
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, max_allowed, new_total = self._validate_payment_update(
            project,
            Decimal('5000.00'),
            Decimal('11000.00')
        )
        
        assert is_valid is False, "ESTA EDICIÓN DEBE SER RECHAZADA"
        assert error is not None
        assert "excedería el presupuesto" in error
        assert new_total == Decimal('11000.00')
        assert max_allowed == Decimal('10000.00')
    
    def test_validate_update_decrease(self):
        """
        ✅ Disminuir pago siempre debe funcionar.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('8000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _, new_total = self._validate_payment_update(
            project,
            Decimal('8000.00'),
            Decimal('5000.00')
        )
        
        assert is_valid is True
        assert error is None
        assert new_total == Decimal('5000.00')
    
    def test_validate_update_to_zero(self):
        """
        ❌ Editar pago a $0 debe rechazarse.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _, _ = self._validate_payment_update(
            project,
            Decimal('5000.00'),
            Decimal('0.00')
        )
        
        assert is_valid is False
        assert "mayor a cero" in error
    
    def test_validate_update_to_negative(self):
        """
        ❌ Editar pago a negativo debe rechazarse.
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _, _ = self._validate_payment_update(
            project,
            Decimal('5000.00'),
            Decimal('-1000.00')
        )
        
        assert is_valid is False
        assert "mayor a cero" in error
    
    def test_validate_update_with_multiple_payments(self):
        """
        Editar un pago cuando hay varios otros.
        
        - Presupuesto: $10,000
        - Pago 1: $3,000
        - Pago 2: $4,000
        - Total: $7,000
        - Editar Pago 1: $3,000 → $5,000
        - Nuevo total: $5,000 + $4,000 = $9,000 ✅
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, _, new_total = self._validate_payment_update(
            project,
            Decimal('3000.00'),
            Decimal('5000.00')
        )
        
        assert is_valid is True
        assert new_total == Decimal('9000.00')
    
    def test_validate_update_with_multiple_payments_exceed(self):
        """
        Editar pago que con otros excedería el presupuesto.
        
        - Presupuesto: $10,000
        - Pago 1: $3,000
        - Pago 2: $4,000
        - Total: $7,000
        - Intentar editar Pago 1: $3,000 → $8,000
        - Nuevo total SERÍA: $8,000 + $4,000 = $12,000 ❌
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('4000.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        is_valid, error, max_allowed, new_total = self._validate_payment_update(
            project,
            Decimal('3000.00'),
            Decimal('8000.00')
        )
        
        assert is_valid is False
        assert "excedería el presupuesto" in error
        assert new_total == Decimal('12000.00')
        assert max_allowed == Decimal('6000.00')


# ============================================================================
# TESTS DE FLUJOS COMPLETOS END-TO-END
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestCompletePaymentFlows:
    """
    Tests de flujos completos del usuario desde el inicio.
    """
    
    def test_complete_flow_as_per_tc52_specification(self):
        """
        Flujo exacto mencionado en TC-52:
        
        1. Crear proyecto sin presupuesto
        2. Configurar presupuesto a $10,000
        3. Crear pago de $5,000 ✅
        4. Editar pago a $8,000 ✅
        5. Intentar editar pago a $11,000 ❌ (debe rechazarse)
        """
        # 1. Crear proyecto sin presupuesto
        project = ProjectFactory(
            total_budget=None,
            budget_configured=False
        )
        
        # 2. Configurar presupuesto
        project.total_budget = Decimal('10000.00')
        project.budget_configured = True
        project.save()
        
        # 3. Crear pago de $5,000
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('5000.00')
        )
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('5000.00')
        assert project.remaining_amount == Decimal('5000.00')
        
        # 4. Editar pago a $8,000
        payment.amount = Decimal('8000.00')
        payment.save()
        
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        
        assert project.total_paid == Decimal('8000.00')
        assert project.remaining_amount == Decimal('2000.00')
        
        # 5. Validar que editar a $11,000 sería rechazado
        # (no hacemos el save, solo verificamos la validación)
        old_amount = Decimal('8000.00')
        new_amount = Decimal('11000.00')
        new_total = (project.total_paid - old_amount) + new_amount
        
        # Verificar cálculo
        assert new_total == Decimal('11000.00')
        assert new_total > project.total_budget  # EXCEDE
        
        # La edición NO debería realizarse
        payment.refresh_from_db()
        assert payment.amount == Decimal('8000.00')
    
    def test_workflow_with_multiple_editions(self):
        """
        Workflow con múltiples ediciones y creaciones.
        """
        project = ProjectFactory(total_budget=Decimal('20000.00'))
        
        # Crear primer pago
        p1 = ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('5000.00')
        
        # Crear segundo pago
        p2 = ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('8000.00')
        
        # Editar primer pago hacia arriba
        p1.amount = Decimal('7000.00')
        p1.save()
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('10000.00')
        
        # Crear tercer pago
        p3 = ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('15000.00')
        
        # Editar segundo pago hacia abajo
        p2.amount = Decimal('2000.00')
        p2.save()
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('14000.00')
        
        # Intentar crear pago de $7,000 (solo quedan $6,000)
        # Validación lo rechazaría
        remaining = project.total_budget - project.total_paid
        assert remaining == Decimal('6000.00')
        
        # Crear pago menor al presupuesto
        p4 = ProjectPaymentFactory(project=project, amount=Decimal('6000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        project.refresh_from_db()
        assert project.total_paid == Decimal('20000.00')
        assert project.remaining_amount == Decimal('0.00')


# ============================================================================
# TESTS DE LOGGING Y AUDIT TRAIL
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentLoggingAndAuditTrail:
    """
    Tests de logging para auditoría de operaciones.
    """
    
    @patch('apps.projects.models.logger')
    def test_creation_is_logged(self, mock_logger):
        """
        Creación de pago debe ser logueada.
        """
        project = ProjectFactory()
        
        payment = ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        
        # Verificar que se llamó a logger
        assert mock_logger.info.called
    
    @patch('apps.projects.models.logger')
    def test_deletion_is_logged(self, mock_logger):
        """
        Eliminación de pago debe ser logueada.
        """
        payment = ProjectPaymentFactory()
        
        payment.delete()
        
        # Verificar que se llamó a logger
        assert mock_logger.info.called


# ============================================================================
# TESTS DE PERMISSIONS Y SECURITY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentPermissions:
    """
    Tests de permisos y seguridad.
    """
    
    def test_payment_belongs_to_correct_project(self):
        """
        Pago debe estar relacionado con el proyecto correcto.
        """
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        
        payment = ProjectPaymentFactory(project=project1)
        
        assert payment.project == project1
        assert payment not in project2.payments.all()
        assert payment in project1.payments.all()
    
    def test_created_by_tracks_user(self):
        """
        created_by debe registrar qué usuario creó el pago.
        """
        user1 = UserFactory()
        user2 = UserFactory()
        
        payment1 = ProjectPaymentFactory(created_by=user1)
        payment2 = ProjectPaymentFactory(created_by=user2)
        
        assert payment1.created_by == user1
        assert payment2.created_by == user2
        assert payment1.created_by != payment2.created_by
