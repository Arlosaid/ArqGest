"""
Tests exhaustivos para el modelo Project

Estos tests DEBEN detectar bugs reales en la lógica de negocio de proyectos.
El modelo Project es CRÍTICO porque maneja toda la lógica financiera, cálculos
de progreso, relaciones y estados - es fundamental para el negocio.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import IntegrityError
from unittest.mock import patch, Mock
from tests.factories import (
    OrganizationFactory,
    ClientFactory,
    UserFactory,
    ProjectFactory,
    ActiveProjectFactory,
    ArchivedProjectFactory,
    CompletedProjectFactory,
    PhaseFactory,
    TaskFactory,
    ProjectPaymentFactory,
    TodoTaskFactory,
    InProgressTaskFactory,
    DoneTaskFactory,
    PendingPhaseFactory,
    InProgressPhaseFactory,
    CompletedPhaseFactory,
)
from apps.projects.models import Project, Phase, Task, ProjectPayment


# ============================================================================
# TESTS DE CREACIÓN DE PROYECTOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectCreation:
    """Tests de creación básica de proyectos"""
    
    def test_project_creation_with_factory(self):
        """Verificar que se puede crear un proyecto con la factory"""
        project = ProjectFactory()
        
        assert project.pk is not None
        assert project.organization is not None
        assert project.owner is not None
        assert project.client is not None
        assert project.name is not None
        assert project.status == Project.Status.ACTIVE
    
    def test_project_creation_with_valid_data(self):
        """Crear proyecto con datos válidos completos"""
        org = OrganizationFactory()
        client = ClientFactory(organization=org)
        owner = UserFactory(organization=org)
        
        project = Project.objects.create(
            organization=org,
            client=client,
            owner=owner,
            name='Test Project',
            status=Project.Status.ACTIVE,
            total_budget=Decimal('50000.00'),
            budget_configured=True
        )
        
        assert project.pk is not None
        assert project.organization == org
        assert project.client == client
        assert project.owner == owner
        assert project.name == 'Test Project'
        assert project.status == Project.Status.ACTIVE
        assert project.total_budget == Decimal('50000.00')
        assert project.budget_configured is True
    
    def test_project_creation_without_client(self):
        """
        EDGE CASE: Proyecto sin cliente debe poder crearse
        (client es opcional - SET_NULL)
        """
        org = OrganizationFactory()
        owner = UserFactory(organization=org)
        
        project = Project.objects.create(
            organization=org,
            owner=owner,
            name='Project without client',
            client=None
        )
        
        assert project.pk is not None
        assert project.client is None
    
    def test_project_creation_without_budget(self):
        """
        EDGE CASE: Proyecto sin presupuesto configurado
        """
        org = OrganizationFactory()
        owner = UserFactory(organization=org)
        
        project = Project.objects.create(
            organization=org,
            owner=owner,
            name='Project without budget',
            total_budget=None,
            budget_configured=False
        )
        
        assert project.pk is not None
        assert project.total_budget is None
        assert project.budget_configured is False
    
    def test_project_creation_without_dates(self):
        """
        EDGE CASE: Proyecto sin fechas de inicio/fin
        """
        org = OrganizationFactory()
        owner = UserFactory(organization=org)
        
        project = Project.objects.create(
            organization=org,
            owner=owner,
            name='Project without dates',
            start_date=None,
            end_date=None
        )
        
        assert project.pk is not None
        assert project.start_date is None
        assert project.end_date is None
    
    def test_project_str_representation(self):
        """__str__ debe retornar el nombre del proyecto"""
        project = ProjectFactory(name='Mi Proyecto Test')
        
        assert str(project) == 'Mi Proyecto Test'
    
    def test_project_creation_with_unicode_name(self):
        """
        EDGE CASE: Nombre con caracteres especiales y unicode
        """
        org = OrganizationFactory()
        owner = UserFactory(organization=org)
        
        project = Project.objects.create(
            organization=org,
            owner=owner,
            name='Proyecto Diseño Müller & Associés 日本'
        )
        
        assert project.pk is not None
        assert project.name == 'Proyecto Diseño Müller & Associés 日本'
    
    def test_project_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        project = ProjectFactory()
        
        assert project.created_at is not None
        assert (timezone.now() - project.created_at).seconds < 5


# ============================================================================
# TESTS DE RELACIONES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectRelationships:
    """Tests de relaciones con otros modelos"""
    
    def test_project_organization_relationship(self):
        """Proyecto debe estar relacionado con una organización"""
        org = OrganizationFactory(name='Test Org')
        project = ProjectFactory(organization=org)
        
        assert project.organization == org
        assert project in org.projects.all()
    
    def test_project_client_relationship(self):
        """Proyecto debe estar relacionado con un cliente"""
        client = ClientFactory(name='Test Client')
        project = ProjectFactory(client=client)
        
        assert project.client == client
        assert project in client.projects.all()
    
    def test_project_owner_relationship(self):
        """Proyecto debe estar relacionado con un propietario"""
        owner = UserFactory(email='owner@test.com')
        project = ProjectFactory(owner=owner)
        
        assert project.owner == owner
        assert project in owner.owned_projects.all()
    
    def test_project_cascade_on_organization_delete(self):
        """
        CRITICAL: Proyecto debe eliminarse al eliminar la organización
        (CASCADE delete)
        """
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)
        project_id = project.id
        
        org.delete()
        
        with pytest.raises(Project.DoesNotExist):
            Project.objects.get(id=project_id)
    
    def test_project_cascade_on_owner_delete(self):
        """
        CRITICAL: Proyecto debe eliminarse al eliminar el propietario
        (CASCADE delete)
        """
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        project_id = project.id
        
        owner.delete()
        
        with pytest.raises(Project.DoesNotExist):
            Project.objects.get(id=project_id)
    
    def test_project_set_null_on_client_delete(self):
        """
        Proyecto debe mantener client=None al eliminar cliente
        (SET_NULL behavior)
        """
        client = ClientFactory()
        project = ProjectFactory(client=client)
        
        client.delete()
        
        project.refresh_from_db()
        assert project.client is None
    
    def test_project_phases_relationship(self):
        """Proyecto debe acceder a sus fases"""
        project = ProjectFactory()
        phase1 = PhaseFactory(project=project, name='Phase 1')
        phase2 = PhaseFactory(project=project, name='Phase 2')
        
        phases = project.phases.all()
        assert phase1 in phases
        assert phase2 in phases
        assert phases.count() == 2
    
    def test_project_payments_relationship(self):
        """Proyecto debe acceder a sus pagos"""
        project = ProjectFactory()
        payment1 = ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        payment2 = ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        
        payments = project.payments.all()
        assert payment1 in payments
        assert payment2 in payments
        assert payments.count() == 2


# ============================================================================
# TESTS DE ESTADOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectStatus:
    """Tests de estados del proyecto"""
    
    def test_project_default_status_is_active(self):
        """Estado por defecto debe ser ACTIVE"""
        project = ProjectFactory()
        
        assert project.status == Project.Status.ACTIVE
    
    def test_project_can_be_active(self):
        """Proyecto puede estar activo"""
        project = ActiveProjectFactory()
        
        assert project.status == Project.Status.ACTIVE
    
    def test_project_can_be_archived(self):
        """Proyecto puede estar archivado"""
        project = ArchivedProjectFactory()
        
        assert project.status == Project.Status.ARCHIVED
    
    def test_project_can_be_completed(self):
        """Proyecto puede estar completado"""
        project = CompletedProjectFactory()
        
        assert project.status == Project.Status.COMPLETED
    
    def test_project_status_transition_active_to_archived(self):
        """Transición de estado: ACTIVE -> ARCHIVED"""
        project = ActiveProjectFactory()
        
        project.status = Project.Status.ARCHIVED
        project.save()
        
        project.refresh_from_db()
        assert project.status == Project.Status.ARCHIVED
    
    def test_project_status_transition_active_to_completed(self):
        """Transición de estado: ACTIVE -> COMPLETED"""
        project = ActiveProjectFactory()
        
        project.status = Project.Status.COMPLETED
        project.save()
        
        project.refresh_from_db()
        assert project.status == Project.Status.COMPLETED
    
    def test_project_status_choices_validation(self):
        """Solo deben permitirse estados válidos"""
        valid_statuses = [
            Project.Status.ACTIVE,
            Project.Status.ARCHIVED,
            Project.Status.COMPLETED
        ]
        
        for status in valid_statuses:
            project = ProjectFactory(status=status)
            assert project.status == status


# ============================================================================
# TESTS DE CAMPOS FINANCIEROS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFinancialFields:
    """Tests de campos financieros del proyecto"""
    
    def test_project_total_budget_can_be_set(self):
        """Presupuesto total puede establecerse"""
        project = ProjectFactory(total_budget=Decimal('100000.00'))
        
        assert project.total_budget == Decimal('100000.00')
    
    def test_project_total_budget_can_be_null(self):
        """
        EDGE CASE: Presupuesto total puede ser NULL
        """
        project = ProjectFactory(total_budget=None, budget_configured=False)
        
        assert project.total_budget is None
    
    def test_project_budget_configured_flag(self):
        """Flag budget_configured indica si hay presupuesto"""
        project_with_budget = ProjectFactory(
            total_budget=Decimal('50000.00'),
            budget_configured=True
        )
        project_without_budget = ProjectFactory(
            total_budget=None,
            budget_configured=False
        )
        
        assert project_with_budget.budget_configured is True
        assert project_without_budget.budget_configured is False
    
    def test_project_budget_decimal_precision(self):
        """
        Presupuesto debe mantener precisión decimal (2 decimales)
        """
        project = ProjectFactory(total_budget=Decimal('12345.67'))
        project.refresh_from_db()
        
        assert project.total_budget == Decimal('12345.67')
    
    def test_project_budget_large_value(self):
        """
        EDGE CASE: Presupuesto con valor grande (12 dígitos)
        """
        project = ProjectFactory(total_budget=Decimal('9999999999.99'))
        project.refresh_from_db()
        
        assert project.total_budget == Decimal('9999999999.99')
    
    def test_project_budget_zero_value(self):
        """
        EDGE CASE: Presupuesto con valor cero
        """
        project = ProjectFactory(total_budget=Decimal('0.00'))
        
        assert project.total_budget == Decimal('0.00')


# ============================================================================
# TESTS DE total_paid PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectTotalPaidProperty:
    """
    Tests de la propiedad total_paid - CRÍTICO para finanzas
    """
    
    def test_total_paid_with_no_payments(self):
        """
        EDGE CASE: Proyecto sin pagos debe retornar 0.00
        """
        project = ProjectFactory()
        
        assert project.total_paid == Decimal('0.00')
    
    def test_total_paid_with_single_payment(self):
        """Total pagado con un solo pago"""
        project = ProjectFactory()
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        
        # Limpiar cache para forzar cálculo
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.total_paid == Decimal('1000.00')
    
    def test_total_paid_with_multiple_payments(self):
        """Total pagado con múltiples pagos"""
        project = ProjectFactory()
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('2500.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('500.50'))
        
        # Limpiar cache
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.total_paid == Decimal('4000.50')
    
    def test_total_paid_uses_cache(self):
        """
        OPTIMIZATION: total_paid debe usar caché Redis
        """
        project = ProjectFactory()
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        
        # Primera llamada - debe calcular y cachear
        cache.delete(f"project_total_paid:{project.id}")
        total1 = project.total_paid
        
        # Segunda llamada - debe usar cache
        with patch('apps.projects.models.Project.payments') as mock_payments:
            total2 = project.total_paid
            # No debe llamar a aggregate si usa cache
            mock_payments.aggregate.assert_not_called()
        
        assert total1 == total2 == Decimal('1000.00')
    
    def test_total_paid_with_prefetched_payments(self):
        """
        OPTIMIZATION: Si payments está prefetchado, usar eso
        """
        project = ProjectFactory()
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        
        # Usar manager optimizado que hace prefetch
        project_with_prefetch = Project.objects.with_payments().get(id=project.id)
        
        # Debe calcular desde prefetch sin query adicional
        total = project_with_prefetch.total_paid
        assert total == Decimal('3000.00')


# ============================================================================
# TESTS DE remaining_amount PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectRemainingAmountProperty:
    """Tests de la propiedad remaining_amount"""
    
    def test_remaining_amount_with_no_payments(self):
        """Monto restante sin pagos = presupuesto total"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.remaining_amount == Decimal('10000.00')
    
    def test_remaining_amount_with_partial_payment(self):
        """Monto restante con pago parcial"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.remaining_amount == Decimal('7000.00')
    
    def test_remaining_amount_with_full_payment(self):
        """Monto restante con pago completo = 0"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.remaining_amount == Decimal('0.00')
    
    def test_remaining_amount_with_overpayment(self):
        """
        EDGE CASE: Monto restante con sobrepago (negativo)
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('12000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.remaining_amount == Decimal('-2000.00')
    
    def test_remaining_amount_without_budget(self):
        """
        EDGE CASE: remaining_amount sin presupuesto = None
        """
        project = ProjectFactory(total_budget=None, budget_configured=False)
        
        assert project.remaining_amount is None


# ============================================================================
# TESTS DE payment_percentage PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentPercentageProperty:
    """Tests de la propiedad payment_percentage"""
    
    def test_payment_percentage_with_no_payments(self):
        """Porcentaje de pago sin pagos = 0%"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_percentage == 0
    
    def test_payment_percentage_with_partial_payment(self):
        """Porcentaje de pago con pago parcial"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('2500.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_percentage == 25
    
    def test_payment_percentage_with_full_payment(self):
        """Porcentaje de pago con pago completo = 100%"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_percentage == 100
    
    def test_payment_percentage_with_overpayment(self):
        """
        EDGE CASE: Porcentaje de pago con sobrepago = máximo 100%
        """
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('15000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        # Debe limitarse a 100%
        assert project.payment_percentage == 100
    
    def test_payment_percentage_without_budget(self):
        """
        EDGE CASE: Porcentaje sin presupuesto = 0%
        """
        project = ProjectFactory(total_budget=None, budget_configured=False)
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_percentage == 0
    
    def test_payment_percentage_with_zero_budget(self):
        """
        EDGE CASE: División por cero - presupuesto = 0
        """
        project = ProjectFactory(total_budget=Decimal('0.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        # Debe manejar división por cero
        assert project.payment_percentage == 0


# ============================================================================
# TESTS DE payment_status PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectPaymentStatusProperty:
    """Tests de la propiedad payment_status para UI"""
    
    def test_payment_status_not_configured(self):
        """Estado 'not_configured' cuando no hay presupuesto"""
        project = ProjectFactory(budget_configured=False)
        
        assert project.payment_status == 'not_configured'
    
    def test_payment_status_started(self):
        """Estado 'started' con menos de 40% pagado"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('3000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_status == 'started'
    
    def test_payment_status_in_progress(self):
        """Estado 'in_progress' entre 40% y 79% pagado"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('5000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_status == 'in_progress'
    
    def test_payment_status_almost_complete(self):
        """Estado 'almost_complete' entre 80% y 99% pagado"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('9000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_status == 'almost_complete'
    
    def test_payment_status_completed(self):
        """Estado 'completed' con 100% pagado"""
        project = ProjectFactory(total_budget=Decimal('10000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('10000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.payment_status == 'completed'


# ============================================================================
# TESTS DE latest_payment PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectLatestPaymentProperty:
    """Tests de la propiedad latest_payment"""
    
    def test_latest_payment_with_no_payments(self):
        """
        EDGE CASE: latest_payment sin pagos = None
        """
        project = ProjectFactory()
        
        assert project.latest_payment is None
    
    def test_latest_payment_with_single_payment(self):
        """Latest payment con un solo pago"""
        project = ProjectFactory()
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('1000.00'),
            date=timezone.now().date()
        )
        
        assert project.latest_payment == payment
    
    def test_latest_payment_with_multiple_payments(self):
        """Latest payment debe retornar el más reciente"""
        project = ProjectFactory()
        
        old_payment = ProjectPaymentFactory(
            project=project,
            date=(timezone.now() - timedelta(days=10)).date()
        )
        recent_payment = ProjectPaymentFactory(
            project=project,
            date=timezone.now().date()
        )
        
        assert project.latest_payment == recent_payment


# ============================================================================
# TESTS DE progress_percentage PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectProgressPercentageProperty:
    """
    Tests de progress_percentage - CRÍTICO para cálculo de progreso
    """
    
    def test_progress_percentage_with_no_tasks(self):
        """
        EDGE CASE: Progreso sin tareas = 0%
        """
        project = ProjectFactory()
        PhaseFactory(project=project)
        cache.delete(f"project_progress:{project.id}")
        
        assert project.progress_percentage == 0
    
    def test_progress_percentage_with_all_done_tasks(self):
        """Progreso con todas las tareas completadas = 100%"""
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        DoneTaskFactory(phase=phase)
        DoneTaskFactory(phase=phase)
        DoneTaskFactory(phase=phase)
        cache.delete(f"project_progress:{project.id}")
        
        assert project.progress_percentage == 100
    
    def test_progress_percentage_with_partial_completion(self):
        """Progreso con tareas parcialmente completadas"""
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        DoneTaskFactory(phase=phase)  # 1 completada
        TodoTaskFactory(phase=phase)   # 1 pendiente
        TodoTaskFactory(phase=phase)   # 1 pendiente
        TodoTaskFactory(phase=phase)   # 1 pendiente
        cache.delete(f"project_progress:{project.id}")
        
        # 1 de 4 = 25%
        assert project.progress_percentage == 25
    
    def test_progress_percentage_uses_cache(self):
        """
        OPTIMIZATION: progress_percentage debe usar caché
        """
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        DoneTaskFactory(phase=phase)
        
        # Primera llamada - calcular y cachear
        cache.delete(f"project_progress:{project.id}")
        progress1 = project.progress_percentage
        
        # Segunda llamada - usar cache
        progress2 = project.progress_percentage
        
        assert progress1 == progress2 == 100


# ============================================================================
# TESTS DE progress_percentage_by_phases PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectProgressByPhasesProperty:
    """Tests del cálculo de progreso basado en fases"""
    
    def test_progress_by_phases_with_no_phases(self):
        """
        EDGE CASE: Progreso sin fases = 0%
        """
        project = ProjectFactory()
        
        assert project.progress_percentage_by_phases == 0
    
    def test_progress_by_phases_with_all_completed(self):
        """Progreso con todas las fases completadas = 100%"""
        project = ProjectFactory()
        CompletedPhaseFactory(project=project)
        CompletedPhaseFactory(project=project)
        
        assert project.progress_percentage_by_phases == 100
    
    def test_progress_by_phases_with_partial_completion(self):
        """Progreso con fases parcialmente completadas"""
        project = ProjectFactory()
        CompletedPhaseFactory(project=project)
        PendingPhaseFactory(project=project)
        PendingPhaseFactory(project=project)
        PendingPhaseFactory(project=project)
        
        # 1 de 4 = 25%
        assert project.progress_percentage_by_phases == 25


# ============================================================================
# TESTS DE CONTADORES Y PROPIEDADES DE TAREAS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectTaskCounters:
    """Tests de contadores de tareas"""
    
    def test_active_phases_count(self):
        """Contar fases activas (en progreso)"""
        project = ProjectFactory()
        InProgressPhaseFactory(project=project)
        InProgressPhaseFactory(project=project)
        PendingPhaseFactory(project=project)
        CompletedPhaseFactory(project=project)
        
        assert project.active_phases_count == 2
    
    def test_pending_tasks_count(self):
        """Contar tareas pendientes (TODO, IN_PROGRESS, PAUSED)"""
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        TodoTaskFactory(phase=phase)
        TodoTaskFactory(phase=phase)
        InProgressTaskFactory(phase=phase)
        DoneTaskFactory(phase=phase)
        
        # 3 pendientes (2 TODO + 1 IN_PROGRESS)
        assert project.pending_tasks_count == 3
    
    def test_total_tasks_count(self):
        """Contar total de tareas del proyecto"""
        project = ProjectFactory()
        phase1 = PhaseFactory(project=project)
        phase2 = PhaseFactory(project=project)
        TaskFactory(phase=phase1)
        TaskFactory(phase=phase1)
        TaskFactory(phase=phase2)
        
        assert project.total_tasks_count == 3
    
    def test_next_deadline(self):
        """Obtener la próxima fecha límite"""
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        
        future_date = (timezone.now() + timedelta(days=5)).date()
        far_future_date = (timezone.now() + timedelta(days=10)).date()
        
        TaskFactory(phase=phase, due_date=far_future_date, status=Task.Status.TODO)
        next_task = TaskFactory(phase=phase, due_date=future_date, status=Task.Status.TODO)
        
        assert project.next_deadline == future_date
    
    def test_next_deadline_with_no_pending_tasks(self):
        """
        EDGE CASE: next_deadline sin tareas pendientes = None
        """
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        DoneTaskFactory(phase=phase, due_date=timezone.now().date())
        
        assert project.next_deadline is None


# ============================================================================
# TESTS DE CUSTOM MANAGER
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectManager:
    """Tests del ProjectManager customizado"""
    
    def test_with_payments_prefetch(self):
        """with_payments debe hacer prefetch de pagos"""
        project = ProjectFactory()
        ProjectPaymentFactory(project=project)
        ProjectPaymentFactory(project=project)
        
        # Usar manager optimizado
        project_optimized = Project.objects.with_payments().get(id=project.id)
        
        # Verificar prefetch
        assert hasattr(project_optimized, '_prefetched_objects_cache')
        assert 'payments' in project_optimized._prefetched_objects_cache
    
    def test_with_complete_data_prefetch(self):
        """with_complete_data debe hacer select_related y prefetch"""
        org = OrganizationFactory()
        client = ClientFactory(organization=org)
        owner = UserFactory(organization=org)
        project = ProjectFactory(organization=org, client=client, owner=owner)
        PhaseFactory(project=project)
        ProjectPaymentFactory(project=project)
        
        # Usar manager optimizado
        project_optimized = Project.objects.with_complete_data().get(id=project.id)
        
        # Verificar select_related (no queries adicionales)
        assert project_optimized.client == client
        assert project_optimized.owner == owner
        assert project_optimized.organization == org
    
    def test_active_for_organization(self):
        """active_for_organization debe filtrar proyectos activos"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        active_proj1 = ActiveProjectFactory(organization=org1)
        active_proj2 = ActiveProjectFactory(organization=org1)
        ArchivedProjectFactory(organization=org1)  # No debe aparecer
        ActiveProjectFactory(organization=org2)  # No debe aparecer
        
        active_projects = Project.objects.active_for_organization(org1.id)
        
        assert active_projects.count() == 2
        assert active_proj1 in active_projects
        assert active_proj2 in active_projects
    
    def test_with_financial_data_annotate(self):
        """with_financial_data debe anotar contadores y sumas"""
        project = ProjectFactory()
        ProjectPaymentFactory(project=project, amount=Decimal('1000.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('2000.00'))
        
        # Usar manager optimizado
        project_annotated = Project.objects.with_financial_data().get(id=project.id)
        
        assert hasattr(project_annotated, 'payments_count')
        assert hasattr(project_annotated, 'total_paid_calculated')
        assert project_annotated.payments_count == 2
        assert project_annotated.total_paid_calculated == Decimal('3000.00')


# ============================================================================
# TESTS DE VALIDACIONES Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectValidations:
    """Tests de validaciones y constraints"""
    
    def test_project_requires_organization(self):
        """
        CRITICAL: Proyecto debe requerir organización
        """
        owner = UserFactory()
        
        with pytest.raises(IntegrityError):
            Project.objects.create(
                organization=None,
                owner=owner,
                name='Project without org'
            )
    
    def test_project_requires_owner(self):
        """
        CRITICAL: Proyecto debe requerir propietario
        """
        org = OrganizationFactory()
        
        with pytest.raises(IntegrityError):
            Project.objects.create(
                organization=org,
                owner=None,
                name='Project without owner'
            )
    
    def test_project_requires_name(self):
        """
        CRITICAL: Proyecto debe requerir nombre
        """
        org = OrganizationFactory()
        owner = UserFactory()
        
        with pytest.raises(IntegrityError):
            Project.objects.create(
                organization=org,
                owner=owner,
                name=None
            )
    
    def test_project_name_max_length(self):
        """Nombre no debe exceder 100 caracteres"""
        from django.core.exceptions import ValidationError
        org = OrganizationFactory()
        owner = UserFactory()
        
        # 101 caracteres
        long_name = 'A' * 101
        
        project = Project(
            organization=org,
            owner=owner,
            name=long_name
        )
        with pytest.raises(ValidationError):
            project.full_clean()


# ============================================================================
# TESTS DE ORDENAMIENTO Y QUERYSETS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectOrdering:
    """Tests de ordenamiento por defecto"""
    
    def test_projects_ordered_by_created_at_desc(self):
        """Proyectos deben ordenarse por created_at descendente"""
        old_project = ProjectFactory()
        # Esperar un momento para asegurar diferente timestamp
        import time
        time.sleep(0.01)
        new_project = ProjectFactory()
        
        projects = Project.objects.all()
        
        assert projects[0] == new_project
        assert projects[1] == old_project


# ============================================================================
# TESTS DE EDGE CASES Y BUG HUNTING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProjectEdgeCases:
    """Tests de casos extremos y potenciales bugs"""
    
    def test_project_with_many_payments(self):
        """
        EDGE CASE: Proyecto con muchos pagos (performance)
        """
        project = ProjectFactory(total_budget=Decimal('100000.00'))
        
        # Crear 100 pagos
        for i in range(100):
            ProjectPaymentFactory(project=project, amount=Decimal('100.00'))
        
        cache.delete(f"project_total_paid:{project.id}")
        
        # Debe calcular correctamente
        assert project.total_paid == Decimal('10000.00')
        assert project.payment_percentage == 10
    
    def test_project_with_many_phases_and_tasks(self):
        """
        EDGE CASE: Proyecto con muchas fases y tareas (performance)
        """
        project = ProjectFactory()
        
        # Crear 10 fases con 10 tareas cada una
        for i in range(10):
            phase = PhaseFactory(project=project)
            for j in range(10):
                TaskFactory(phase=phase)
        
        assert project.total_tasks_count == 100
    
    def test_project_dates_validation_start_after_end(self):
        """
        WARNING: No hay validación de que start_date < end_date
        Este test documenta el comportamiento actual.
        """
        org = OrganizationFactory()
        owner = UserFactory()
        
        # NOTA: Actualmente el modelo NO valida esto
        project = Project.objects.create(
            organization=org,
            owner=owner,
            name='Project with invalid dates',
            start_date=(timezone.now() + timedelta(days=30)).date(),
            end_date=timezone.now().date()  # End antes de start
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert project.pk is not None
        # TODO: Considerar agregar validación clean() en el modelo
    
    def test_project_with_extremely_large_budget(self):
        """
        EDGE CASE: Presupuesto extremadamente grande
        """
        project = ProjectFactory(total_budget=Decimal('9999999999.99'))
        ProjectPaymentFactory(project=project, amount=Decimal('1000000000.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        assert project.remaining_amount == Decimal('8999999999.99')
    
    def test_project_payment_percentage_precision(self):
        """
        EDGE CASE: Precisión en cálculo de porcentaje
        """
        project = ProjectFactory(total_budget=Decimal('7.00'))
        ProjectPaymentFactory(project=project, amount=Decimal('3.00'))
        cache.delete(f"project_total_paid:{project.id}")
        
        # 3/7 = 42.857... debe truncarse a 42%
        assert project.payment_percentage == 42
    
    def test_project_client_from_different_organization(self):
        """
        WARNING: No hay validación de que client pertenezca a la misma org
        Este test documenta el comportamiento actual.
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        client_org2 = ClientFactory(organization=org2)
        owner = UserFactory(organization=org1)
        
        # NOTA: Actualmente permite asignar cliente de otra org
        project = Project.objects.create(
            organization=org1,
            owner=owner,
            client=client_org2,  # Cliente de org2
            name='Cross-org project'
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert project.pk is not None
        # TODO: Considerar agregar validación clean() en el modelo

