"""
Tests exhaustivos para el modelo Phase

Estos tests DEBEN detectar bugs reales en la lógica de fases del proyecto.
El modelo Phase es importante porque organiza las tareas y determina el flujo
de trabajo del proyecto.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.db import IntegrityError
from unittest.mock import patch, Mock
from tests.factories import (
    OrganizationFactory,
    UserFactory,
    ProjectFactory,
    PhaseFactory,
    PendingPhaseFactory,
    InProgressPhaseFactory,
    CompletedPhaseFactory,
    TaskFactory,
    TodoTaskFactory,
    InProgressTaskFactory,
    DoneTaskFactory,
)
from apps.projects.models import Phase, Task


# ============================================================================
# TESTS DE CREACIÓN DE FASES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseCreation:
    """Tests de creación básica de fases"""
    
    def test_phase_creation_with_factory(self):
        """Verificar que se puede crear una fase con la factory"""
        phase = PhaseFactory()
        
        assert phase.pk is not None
        assert phase.project is not None
        assert phase.name is not None
        assert phase.status == Phase.Status.PENDING
        assert phase.order is not None
    
    def test_phase_creation_with_valid_data(self):
        """Crear fase con datos válidos completos"""
        project = ProjectFactory()
        
        phase = Phase.objects.create(
            project=project,
            name='Diseño Preliminar',
            status=Phase.Status.PENDING,
            order=1,
            notes='Fase de diseño inicial'
        )
        
        assert phase.pk is not None
        assert phase.project == project
        assert phase.name == 'Diseño Preliminar'
        assert phase.status == Phase.Status.PENDING
        assert phase.order == 1
        assert phase.notes == 'Fase de diseño inicial'
    
    def test_phase_creation_without_optional_fields(self):
        """
        EDGE CASE: Fase sin campos opcionales
        """
        project = ProjectFactory()
        
        phase = Phase.objects.create(
            project=project,
            name='Fase Simple',
            order=1,
            start_date=None,
            end_date=None,
            notes=''
        )
        
        assert phase.pk is not None
        assert phase.start_date is None
        assert phase.end_date is None
        assert phase.notes == ''
    
    def test_phase_str_representation(self):
        """__str__ debe retornar proyecto y nombre de fase"""
        project = ProjectFactory(name='Mi Proyecto')
        phase = PhaseFactory(project=project, name='Mi Fase')
        
        expected_str = 'Mi Proyecto - Mi Fase'
        assert str(phase) == expected_str
    
    def test_phase_creation_with_unicode_name(self):
        """
        EDGE CASE: Nombre con caracteres especiales y unicode
        """
        project = ProjectFactory()
        
        phase = Phase.objects.create(
            project=project,
            name='Diseño Técnico Müller & Associés 日本',
            order=1
        )
        
        assert phase.pk is not None
        assert phase.name == 'Diseño Técnico Müller & Associés 日本'
    
    def test_phase_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        phase = PhaseFactory()
        
        assert phase.created_at is not None
        assert (timezone.now() - phase.created_at).seconds < 5


# ============================================================================
# TESTS DE RELACIONES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseRelationships:
    """Tests de relaciones con otros modelos"""
    
    def test_phase_project_relationship(self):
        """Fase debe estar relacionada con un proyecto"""
        project = ProjectFactory(name='Test Project')
        phase = PhaseFactory(project=project)
        
        assert phase.project == project
        assert phase in project.phases.all()
    
    def test_phase_cascade_on_project_delete(self):
        """
        CRITICAL: Fase debe eliminarse al eliminar el proyecto
        (CASCADE delete)
        """
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        phase_id = phase.id
        
        project.delete()
        
        with pytest.raises(Phase.DoesNotExist):
            Phase.objects.get(id=phase_id)
    
    def test_phase_tasks_relationship(self):
        """Fase debe acceder a sus tareas"""
        phase = PhaseFactory()
        task1 = TaskFactory(phase=phase, title='Task 1')
        task2 = TaskFactory(phase=phase, title='Task 2')
        
        tasks = phase.tasks.all()
        assert task1 in tasks
        assert task2 in tasks
        assert tasks.count() == 2
    
    def test_phase_tasks_cascade_on_delete(self):
        """
        CRITICAL: Tareas deben eliminarse al eliminar la fase
        """
        phase = PhaseFactory()
        task1 = TaskFactory(phase=phase)
        task2 = TaskFactory(phase=phase)
        task1_id = task1.id
        task2_id = task2.id
        
        phase.delete()
        
        with pytest.raises(Task.DoesNotExist):
            Task.objects.get(id=task1_id)
        with pytest.raises(Task.DoesNotExist):
            Task.objects.get(id=task2_id)


# ============================================================================
# TESTS DE ESTADOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseStatus:
    """Tests de estados de la fase"""
    
    def test_phase_default_status_is_pending(self):
        """Estado por defecto debe ser PENDING"""
        phase = PhaseFactory()
        
        assert phase.status == Phase.Status.PENDING
    
    def test_phase_can_be_pending(self):
        """Fase puede estar pendiente"""
        phase = PendingPhaseFactory()
        
        assert phase.status == Phase.Status.PENDING
    
    def test_phase_can_be_in_progress(self):
        """Fase puede estar en progreso"""
        phase = InProgressPhaseFactory()
        
        assert phase.status == Phase.Status.IN_PROGRESS
    
    def test_phase_can_be_completed(self):
        """Fase puede estar completada"""
        phase = CompletedPhaseFactory()
        
        assert phase.status == Phase.Status.COMPLETED
    
    def test_phase_status_transition_pending_to_in_progress(self):
        """Transición de estado: PENDING -> IN_PROGRESS"""
        phase = PendingPhaseFactory()
        
        phase.status = Phase.Status.IN_PROGRESS
        phase.save()
        
        phase.refresh_from_db()
        assert phase.status == Phase.Status.IN_PROGRESS
    
    def test_phase_status_transition_in_progress_to_completed(self):
        """Transición de estado: IN_PROGRESS -> COMPLETED"""
        phase = InProgressPhaseFactory()
        
        phase.status = Phase.Status.COMPLETED
        phase.save()
        
        phase.refresh_from_db()
        assert phase.status == Phase.Status.COMPLETED
    
    def test_phase_status_choices_validation(self):
        """Solo deben permitirse estados válidos"""
        valid_statuses = [
            Phase.Status.PENDING,
            Phase.Status.IN_PROGRESS,
            Phase.Status.COMPLETED
        ]
        
        for status in valid_statuses:
            phase = PhaseFactory(status=status)
            assert phase.status == status


# ============================================================================
# TESTS DE SAVE METHOD Y LOGGING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseSaveMethod:
    """Tests del método save y logging"""
    
    def test_phase_save_stores_original_status(self):
        """__init__ debe guardar el status original"""
        phase = PendingPhaseFactory()
        
        assert hasattr(phase, '_original_status')
        assert phase._original_status == Phase.Status.PENDING
    
    @patch('core.structured_logging.log_info')
    def test_phase_save_logs_status_change(self, mock_log_info):
        """
        save() debe loguear cambios de estado
        """
        phase = PendingPhaseFactory()
        
        # Cambiar estado
        phase.status = Phase.Status.IN_PROGRESS
        phase.save()
        
        # Verificar que se llamó al logging
        mock_log_info.assert_called_once()
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'PHASE_STATUS_CHANGED'
        assert 'changes' in call_kwargs
    
    @patch('core.structured_logging.log_info')
    def test_phase_save_no_log_on_creation(self, mock_log_info):
        """
        save() NO debe loguear en creación (solo cambios)
        """
        phase = PhaseFactory()
        
        # No debe llamar al logging en creación
        mock_log_info.assert_not_called()
    
    @patch('core.structured_logging.log_info')
    def test_phase_save_no_log_if_status_unchanged(self, mock_log_info):
        """
        save() NO debe loguear si el status no cambió
        """
        phase = PendingPhaseFactory()
        mock_log_info.reset_mock()
        
        # Guardar sin cambiar status
        phase.notes = 'Nuevas notas'
        phase.save()
        
        # No debe llamar al logging
        mock_log_info.assert_not_called()


# ============================================================================
# TESTS DE ORDENAMIENTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseOrdering:
    """Tests de ordenamiento de fases"""
    
    def test_phases_ordered_by_project_and_order(self):
        """Fases deben ordenarse por proyecto y orden"""
        project = ProjectFactory()
        phase3 = PhaseFactory(project=project, order=3)
        phase1 = PhaseFactory(project=project, order=1)
        phase2 = PhaseFactory(project=project, order=2)
        
        phases = Phase.objects.filter(project=project)
        
        assert list(phases) == [phase1, phase2, phase3]
    
    def test_phases_order_across_different_projects(self):
        """Fases de diferentes proyectos se ordenan por proyecto primero"""
        project_a = ProjectFactory(name='A Project')
        project_b = ProjectFactory(name='B Project')
        
        phase_b = PhaseFactory(project=project_b, order=1)
        phase_a = PhaseFactory(project=project_a, order=1)
        
        phases = Phase.objects.filter(project__in=[project_a, project_b])
        
        # Orden por proyecto primero, luego por order
        assert phases[0].project == project_a
        assert phases[1].project == project_b


# ============================================================================
# TESTS DE VALIDACIONES Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseValidations:
    """Tests de validaciones y constraints"""
    
    def test_phase_requires_project(self):
        """
        CRITICAL: Fase debe requerir proyecto
        """
        with pytest.raises(IntegrityError):
            Phase.objects.create(
                project=None,
                name='Phase without project',
                order=1
            )
    
    def test_phase_requires_name(self):
        """
        CRITICAL: Fase debe requerir nombre
        """
        project = ProjectFactory()
        
        with pytest.raises(IntegrityError):
            Phase.objects.create(
                project=project,
                name=None,
                order=1
            )
    
    def test_phase_requires_order(self):
        """
        CRITICAL: Fase debe requerir orden
        """
        project = ProjectFactory()
        
        with pytest.raises(IntegrityError):
            Phase.objects.create(
                project=project,
                name='Test Phase',
                order=None
            )
    
    def test_phase_name_max_length(self):
        """Nombre no debe exceder 100 caracteres"""
        project = ProjectFactory()
        
        # 101 caracteres
        long_name = 'A' * 101
        
        with pytest.raises(Exception):  # ValidationError o DataError
            Phase.objects.create(
                project=project,
                name=long_name,
                order=1
            )
    
    def test_phase_order_must_be_positive(self):
        """Order debe ser un entero positivo"""
        project = ProjectFactory()
        
        # Orden 0 o negativo no debe permitirse (PositiveIntegerField)
        with pytest.raises(Exception):
            Phase.objects.create(
                project=project,
                name='Invalid Phase',
                order=-1
            )


# ============================================================================
# TESTS DE CONTADORES Y PROGRESO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseTaskCounters:
    """Tests de contadores de tareas en la fase"""
    
    def test_phase_tasks_count(self):
        """Contar tareas de una fase"""
        phase = PhaseFactory()
        TaskFactory(phase=phase)
        TaskFactory(phase=phase)
        TaskFactory(phase=phase)
        
        assert phase.tasks.count() == 3
    
    def test_phase_completed_tasks_count(self):
        """Contar tareas completadas de una fase"""
        phase = PhaseFactory()
        DoneTaskFactory(phase=phase)
        DoneTaskFactory(phase=phase)
        TodoTaskFactory(phase=phase)
        InProgressTaskFactory(phase=phase)
        
        completed = phase.tasks.filter(status='DONE').count()
        assert completed == 2
    
    def test_phase_task_progress_percentage(self):
        """Calcular porcentaje de progreso de tareas"""
        phase = PhaseFactory()
        DoneTaskFactory(phase=phase)
        DoneTaskFactory(phase=phase)
        TodoTaskFactory(phase=phase)
        TodoTaskFactory(phase=phase)
        
        total = phase.tasks.count()
        completed = phase.tasks.filter(status='DONE').count()
        progress = int((completed / total) * 100) if total > 0 else 0
        
        assert progress == 50


# ============================================================================
# TESTS DE EDGE CASES Y BUG HUNTING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseEdgeCases:
    """Tests de casos extremos y potenciales bugs"""
    
    def test_phase_with_many_tasks(self):
        """
        EDGE CASE: Fase con muchas tareas (100)
        """
        phase = PhaseFactory()
        
        for i in range(100):
            TaskFactory(phase=phase)
        
        assert phase.tasks.count() == 100
    
    def test_phase_dates_validation_start_after_end(self):
        """
        WARNING: No hay validación de que start_date < end_date
        Este test documenta el comportamiento actual.
        """
        project = ProjectFactory()
        
        # NOTA: Actualmente el modelo NO valida esto
        phase = Phase.objects.create(
            project=project,
            name='Phase with invalid dates',
            order=1,
            start_date=(timezone.now() + timedelta(days=30)).date(),
            end_date=timezone.now().date()  # End antes de start
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert phase.pk is not None
        # TODO: Considerar agregar validación clean() en el modelo
    
    def test_phase_duplicate_order_in_same_project(self):
        """
        WARNING: No hay constraint de unicidad en (project, order)
        Este test documenta el comportamiento actual.
        """
        project = ProjectFactory()
        
        # NOTA: Actualmente permite órdenes duplicados
        phase1 = Phase.objects.create(
            project=project,
            name='Phase 1',
            order=1
        )
        phase2 = Phase.objects.create(
            project=project,
            name='Phase 2',
            order=1  # Mismo orden que phase1
        )
        
        # WARNING: Esto NO lanza error actualmente
        assert phase1.pk is not None
        assert phase2.pk is not None
        # TODO: Considerar agregar constraint de unicidad
    
    def test_phase_with_very_long_notes(self):
        """
        EDGE CASE: Notas muy largas (TextField sin límite)
        """
        project = ProjectFactory()
        
        # 10,000 caracteres
        long_notes = 'A' * 10000
        
        phase = Phase.objects.create(
            project=project,
            name='Phase with long notes',
            order=1,
            notes=long_notes
        )
        
        assert phase.pk is not None
        assert len(phase.notes) == 10000
    
    def test_phase_order_zero(self):
        """
        EDGE CASE: Order con valor 0 (PositiveIntegerField)
        """
        project = ProjectFactory()
        
        # PositiveIntegerField permite 0 en Django
        phase = Phase.objects.create(
            project=project,
            name='Phase with order 0',
            order=0
        )
        
        # Esto es permitido en Django (0 es válido para PositiveIntegerField)
        assert phase.order == 0
    
    def test_multiple_phases_same_name_different_projects(self):
        """
        Múltiples fases pueden tener el mismo nombre en diferentes proyectos
        """
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        
        phase1 = Phase.objects.create(
            project=project1,
            name='Diseño',
            order=1
        )
        phase2 = Phase.objects.create(
            project=project2,
            name='Diseño',
            order=1
        )
        
        assert phase1.name == phase2.name
        assert phase1.pk != phase2.pk


# ============================================================================
# TESTS DE INDEXES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseIndexes:
    """Tests de que los índices están configurados correctamente"""
    
    def test_phase_has_project_order_index(self):
        """Verificar que existe índice phase_project_order_idx"""
        indexes = [index.name for index in Phase._meta.indexes]
        assert 'phase_project_order_idx' in indexes
    
    def test_phase_has_project_status_index(self):
        """Verificar que existe índice phase_project_status_idx"""
        indexes = [index.name for index in Phase._meta.indexes]
        assert 'phase_project_status_idx' in indexes
    
    def test_phase_status_field_has_db_index(self):
        """Verificar que status tiene db_index=True"""
        status_field = Phase._meta.get_field('status')
        assert status_field.db_index is True


# ============================================================================
# TESTS DE META OPTIONS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPhaseMetaOptions:
    """Tests de opciones Meta del modelo"""
    
    def test_phase_verbose_name(self):
        """Verificar verbose_name configurado"""
        assert Phase._meta.verbose_name == 'Fase'
    
    def test_phase_verbose_name_plural(self):
        """Verificar verbose_name_plural configurado"""
        assert Phase._meta.verbose_name_plural == 'Fases'
    
    def test_phase_ordering(self):
        """Verificar ordenamiento por defecto"""
        assert Phase._meta.ordering == ['project', 'order']

