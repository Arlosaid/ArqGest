"""
Tests exhaustivos para el modelo Task

Estos tests DEBEN detectar bugs reales en la lógica de tareas.
El modelo Task es CRÍTICO porque maneja asignaciones, estados, prioridades
y fechas límite - es fundamental para la gestión de proyectos.
"""
import pytest
from datetime import timedelta, date
from django.utils import timezone
from django.db import IntegrityError
from django.core.cache import cache
from unittest.mock import patch, Mock
from tests.factories import (
    OrganizationFactory,
    UserFactory,
    ProjectFactory,
    PhaseFactory,
    TaskFactory,
    TodoTaskFactory,
    InProgressTaskFactory,
    DoneTaskFactory,
    PausedTaskFactory,
    HighPriorityTaskFactory,
)
from apps.projects.models import Task


# ============================================================================
# TESTS DE CREACIÓN DE TAREAS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskCreation:
    """Tests de creación básica de tareas"""
    
    def test_task_creation_with_factory(self):
        """Verificar que se puede crear una tarea con la factory"""
        task = TaskFactory()
        
        assert task.pk is not None
        assert task.phase is not None
        assert task.title is not None
        assert task.status == Task.Status.TODO
        assert task.priority == Task.Priority.MEDIUM
    
    def test_task_creation_with_valid_data(self):
        """Crear tarea con datos válidos completos"""
        phase = PhaseFactory()
        user = UserFactory()
        
        task = Task.objects.create(
            phase=phase,
            assigned_to=user,
            title='Revisar planos estructurales',
            description='Verificar dimensiones y refuerzos',
            status=Task.Status.TODO,
            priority=Task.Priority.HIGH,
            due_date=(timezone.now() + timedelta(days=7)).date()
        )
        
        assert task.pk is not None
        assert task.phase == phase
        assert task.assigned_to == user
        assert task.title == 'Revisar planos estructurales'
        assert task.description == 'Verificar dimensiones y refuerzos'
        assert task.status == Task.Status.TODO
        assert task.priority == Task.Priority.HIGH
    
    def test_task_creation_without_assignment(self):
        """
        EDGE CASE: Tarea sin usuario asignado
        """
        phase = PhaseFactory()
        
        task = Task.objects.create(
            phase=phase,
            title='Tarea sin asignar',
            assigned_to=None
        )
        
        assert task.pk is not None
        assert task.assigned_to is None
    
    def test_task_creation_without_due_date(self):
        """
        EDGE CASE: Tarea sin fecha de vencimiento
        """
        phase = PhaseFactory()
        
        task = Task.objects.create(
            phase=phase,
            title='Tarea sin fecha',
            due_date=None
        )
        
        assert task.pk is not None
        assert task.due_date is None
    
    def test_task_str_representation(self):
        """__str__ debe retornar el título de la tarea"""
        task = TaskFactory(title='Mi Tarea Test')
        
        assert str(task) == 'Mi Tarea Test'
    
    def test_task_creation_with_unicode_title(self):
        """
        EDGE CASE: Título con caracteres especiales y unicode
        """
        phase = PhaseFactory()
        
        task = Task.objects.create(
            phase=phase,
            title='Tarea Diseño Müller & Associés 日本'
        )
        
        assert task.pk is not None
        assert task.title == 'Tarea Diseño Müller & Associés 日本'
    
    def test_task_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        task = TaskFactory()
        
        assert task.created_at is not None
        assert (timezone.now() - task.created_at).seconds < 5


# ============================================================================
# TESTS DE RELACIONES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskRelationships:
    """Tests de relaciones con otros modelos"""
    
    def test_task_phase_relationship(self):
        """Tarea debe estar relacionada con una fase"""
        phase = PhaseFactory()
        task = TaskFactory(phase=phase)
        
        assert task.phase == phase
        assert task in phase.tasks.all()
    
    def test_task_assigned_to_relationship(self):
        """Tarea puede estar asignada a un usuario"""
        user = UserFactory(email='user@test.com')
        task = TaskFactory(assigned_to=user)
        
        assert task.assigned_to == user
        assert task in user.assigned_tasks.all()
    
    def test_task_cascade_on_phase_delete(self):
        """
        CRITICAL: Tarea debe eliminarse al eliminar la fase
        (CASCADE delete)
        """
        phase = PhaseFactory()
        task = TaskFactory(phase=phase)
        task_id = task.id
        
        phase.delete()
        
        with pytest.raises(Task.DoesNotExist):
            Task.objects.get(id=task_id)
    
    def test_task_set_null_on_user_delete(self):
        """
        Tarea debe mantener assigned_to=None al eliminar usuario
        (SET_NULL behavior)
        """
        user = UserFactory()
        task = TaskFactory(assigned_to=user)
        
        user.delete()
        
        task.refresh_from_db()
        assert task.assigned_to is None


# ============================================================================
# TESTS DE ESTADOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskStatus:
    """Tests de estados de la tarea"""
    
    def test_task_default_status_is_todo(self):
        """Estado por defecto debe ser TODO"""
        task = TaskFactory()
        
        assert task.status == Task.Status.TODO
    
    def test_task_can_be_todo(self):
        """Tarea puede estar TODO"""
        task = TodoTaskFactory()
        
        assert task.status == Task.Status.TODO
    
    def test_task_can_be_in_progress(self):
        """Tarea puede estar IN_PROGRESS"""
        task = InProgressTaskFactory()
        
        assert task.status == Task.Status.IN_PROGRESS
    
    def test_task_can_be_done(self):
        """Tarea puede estar DONE"""
        task = DoneTaskFactory()
        
        assert task.status == Task.Status.DONE
    
    def test_task_can_be_paused(self):
        """Tarea puede estar PAUSED"""
        task = PausedTaskFactory()
        
        assert task.status == Task.Status.PAUSED
    
    def test_task_status_transition_todo_to_in_progress(self):
        """Transición de estado: TODO -> IN_PROGRESS"""
        task = TodoTaskFactory()
        
        task.status = Task.Status.IN_PROGRESS
        task.save()
        
        task.refresh_from_db()
        assert task.status == Task.Status.IN_PROGRESS
    
    def test_task_status_transition_in_progress_to_done(self):
        """Transición de estado: IN_PROGRESS -> DONE"""
        task = InProgressTaskFactory()
        
        task.status = Task.Status.DONE
        task.save()
        
        task.refresh_from_db()
        assert task.status == Task.Status.DONE
    
    def test_task_status_choices_validation(self):
        """Solo deben permitirse estados válidos"""
        valid_statuses = [
            Task.Status.TODO,
            Task.Status.IN_PROGRESS,
            Task.Status.PAUSED,
            Task.Status.DONE
        ]
        
        for status in valid_statuses:
            task = TaskFactory(status=status)
            assert task.status == status


# ============================================================================
# TESTS DE PRIORIDADES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskPriority:
    """Tests de prioridades de la tarea"""
    
    def test_task_default_priority_is_medium(self):
        """Prioridad por defecto debe ser MEDIUM"""
        task = TaskFactory()
        
        assert task.priority == Task.Priority.MEDIUM
    
    def test_task_can_be_low_priority(self):
        """Tarea puede tener prioridad BAJA"""
        task = TaskFactory(priority=Task.Priority.LOW)
        
        assert task.priority == Task.Priority.LOW
    
    def test_task_can_be_medium_priority(self):
        """Tarea puede tener prioridad MEDIA"""
        task = TaskFactory(priority=Task.Priority.MEDIUM)
        
        assert task.priority == Task.Priority.MEDIUM
    
    def test_task_can_be_high_priority(self):
        """Tarea puede tener prioridad ALTA"""
        task = HighPriorityTaskFactory()
        
        assert task.priority == Task.Priority.HIGH
    
    def test_task_priority_choices_validation(self):
        """Solo deben permitirse prioridades válidas"""
        valid_priorities = [
            Task.Priority.LOW,
            Task.Priority.MEDIUM,
            Task.Priority.HIGH
        ]
        
        for priority in valid_priorities:
            task = TaskFactory(priority=priority)
            assert task.priority == priority


# ============================================================================
# TESTS DE SAVE METHOD Y LOGGING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskSaveMethod:
    """Tests del método save y logging"""
    
    def test_task_save_stores_original_values(self):
        """__init__ debe guardar valores originales"""
        user = UserFactory()
        task = TodoTaskFactory(assigned_to=user)
        
        assert hasattr(task, '_original_status')
        assert hasattr(task, '_original_assigned_to')
        assert task._original_status == Task.Status.TODO
        assert task._original_assigned_to == user.id
    
    @patch('core.structured_logging.log_info')
    def test_task_save_logs_status_change(self, mock_log_info):
        """
        save() debe loguear cambios de estado
        """
        task = TodoTaskFactory()
        
        # Cambiar estado
        task.status = Task.Status.DONE
        task.save()
        
        # Verificar que se llamó al logging
        mock_log_info.assert_called_once()
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'TASK_CHANGED'
        assert 'changes' in call_kwargs
    
    @patch('core.structured_logging.log_info')
    def test_task_save_logs_assignment_change(self, mock_log_info):
        """
        save() debe loguear cambios de asignación
        """
        user1 = UserFactory()
        user2 = UserFactory()
        task = TaskFactory(assigned_to=user1)
        mock_log_info.reset_mock()
        
        # Cambiar asignación
        task.assigned_to = user2
        task.save()
        
        # Verificar que se llamó al logging
        mock_log_info.assert_called_once()
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'TASK_CHANGED'
    
    @patch('apps.projects.models.invalidate_project_progress_cache')
    def test_task_save_invalidates_cache_on_status_change(self, mock_invalidate):
        """
        save() debe invalidar caché al cambiar status
        """
        task = TodoTaskFactory()
        
        # Cambiar estado
        task.status = Task.Status.DONE
        task.save()
        
        # Verificar que se invalidó el cache
        mock_invalidate.assert_called_once()
    
    @patch('apps.projects.models.invalidate_project_progress_cache')
    def test_task_save_invalidates_cache_on_creation(self, mock_invalidate):
        """
        save() debe invalidar caché al crear tarea nueva
        """
        phase = PhaseFactory()
        
        task = Task(
            phase=phase,
            title='New task'
        )
        task.save()
        
        # Verificar que se invalidó el cache
        mock_invalidate.assert_called_once()


# ============================================================================
# TESTS DE DELETE METHOD
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskDeleteMethod:
    """Tests del método delete"""
    
    @patch('apps.projects.models.invalidate_project_progress_cache')
    def test_task_delete_invalidates_cache(self, mock_invalidate):
        """
        delete() debe invalidar caché de progreso del proyecto
        """
        task = TaskFactory()
        task_id = task.id
        
        task.delete()
        
        # Verificar que se invalidó el cache
        mock_invalidate.assert_called_once()


# ============================================================================
# TESTS DE is_due_soon PROPERTY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskIsDueSoonProperty:
    """Tests de la propiedad is_due_soon"""
    
    def test_is_due_soon_with_no_due_date(self):
        """
        EDGE CASE: is_due_soon sin fecha = False
        """
        task = TaskFactory(due_date=None)
        
        assert task.is_due_soon is False
    
    def test_is_due_soon_with_date_today(self):
        """Tarea que vence hoy = True"""
        task = TaskFactory(due_date=date.today())
        
        assert task.is_due_soon is True
    
    def test_is_due_soon_with_date_tomorrow(self):
        """Tarea que vence mañana = True"""
        task = TaskFactory(due_date=date.today() + timedelta(days=1))
        
        assert task.is_due_soon is True
    
    def test_is_due_soon_with_date_in_3_days(self):
        """Tarea que vence en 3 días = True"""
        task = TaskFactory(due_date=date.today() + timedelta(days=3))
        
        assert task.is_due_soon is True
    
    def test_is_due_soon_with_date_in_4_days(self):
        """Tarea que vence en 4 días = False"""
        task = TaskFactory(due_date=date.today() + timedelta(days=4))
        
        assert task.is_due_soon is False
    
    def test_is_due_soon_with_past_date(self):
        """
        EDGE CASE: Tarea vencida (fecha pasada) = False
        (solo vence 'soon', no vencida)
        """
        task = TaskFactory(due_date=date.today() - timedelta(days=1))
        
        # La propiedad revisa si vence en los próximos 3 días
        # Fecha pasada NO cumple esta condición
        assert task.is_due_soon is False


# ============================================================================
# TESTS DE ORDENAMIENTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskOrdering:
    """Tests de ordenamiento de tareas"""
    
    def test_tasks_ordered_by_due_date_and_priority(self):
        """Tareas deben ordenarse por due_date y priority"""
        phase = PhaseFactory()
        
        future_date = (timezone.now() + timedelta(days=10)).date()
        near_date = (timezone.now() + timedelta(days=2)).date()
        
        task3 = TaskFactory(phase=phase, due_date=future_date, priority=Task.Priority.HIGH)
        task1 = TaskFactory(phase=phase, due_date=near_date, priority=Task.Priority.HIGH)
        task2 = TaskFactory(phase=phase, due_date=near_date, priority=Task.Priority.MEDIUM)
        
        tasks = Task.objects.filter(phase=phase)
        
        # Ordenar por due_date primero, luego por priority
        assert tasks[0] == task1  # near_date, HIGH
        assert tasks[1] == task2  # near_date, MEDIUM
        assert tasks[2] == task3  # future_date, HIGH


# ============================================================================
# TESTS DE VALIDACIONES Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskValidations:
    """Tests de validaciones y constraints"""
    
    def test_task_requires_phase(self):
        """
        CRITICAL: Tarea debe requerir fase
        """
        with pytest.raises(IntegrityError):
            Task.objects.create(
                phase=None,
                title='Task without phase'
            )
    
    def test_task_requires_title(self):
        """
        CRITICAL: Tarea debe requerir título
        """
        phase = PhaseFactory()
        
        with pytest.raises(IntegrityError):
            Task.objects.create(
                phase=phase,
                title=None
            )
    
    def test_task_title_max_length(self):
        """Título no debe exceder 120 caracteres"""
        phase = PhaseFactory()
        
        # 121 caracteres
        long_title = 'A' * 121
        
        with pytest.raises(Exception):  # ValidationError o DataError
            Task.objects.create(
                phase=phase,
                title=long_title
            )


# ============================================================================
# TESTS DE EDGE CASES Y BUG HUNTING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskEdgeCases:
    """Tests de casos extremos y potenciales bugs"""
    
    def test_task_with_very_long_description(self):
        """
        EDGE CASE: Descripción muy larga (TextField sin límite)
        """
        phase = PhaseFactory()
        
        # 10,000 caracteres
        long_description = 'A' * 10000
        
        task = Task.objects.create(
            phase=phase,
            title='Task with long description',
            description=long_description
        )
        
        assert task.pk is not None
        assert len(task.description) == 10000
    
    def test_task_reassignment(self):
        """Reasignar tarea de un usuario a otro"""
        user1 = UserFactory()
        user2 = UserFactory()
        task = TaskFactory(assigned_to=user1)
        
        task.assigned_to = user2
        task.save()
        
        task.refresh_from_db()
        assert task.assigned_to == user2
    
    def test_task_unassignment(self):
        """Desasignar tarea (assigned_to = None)"""
        user = UserFactory()
        task = TaskFactory(assigned_to=user)
        
        task.assigned_to = None
        task.save()
        
        task.refresh_from_db()
        assert task.assigned_to is None
    
    def test_task_status_cycle(self):
        """Ciclo completo de estados de tarea"""
        task = TodoTaskFactory()
        
        # TODO -> IN_PROGRESS
        task.status = Task.Status.IN_PROGRESS
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.IN_PROGRESS
        
        # IN_PROGRESS -> PAUSED
        task.status = Task.Status.PAUSED
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.PAUSED
        
        # PAUSED -> IN_PROGRESS
        task.status = Task.Status.IN_PROGRESS
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.IN_PROGRESS
        
        # IN_PROGRESS -> DONE
        task.status = Task.Status.DONE
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.DONE
    
    def test_task_with_past_due_date(self):
        """
        EDGE CASE: Tarea con fecha de vencimiento en el pasado
        """
        phase = PhaseFactory()
        past_date = (timezone.now() - timedelta(days=10)).date()
        
        task = Task.objects.create(
            phase=phase,
            title='Overdue task',
            due_date=past_date
        )
        
        assert task.pk is not None
        assert task.due_date < date.today()
    
    def test_multiple_tasks_same_title_same_phase(self):
        """
        Múltiples tareas pueden tener el mismo título en la misma fase
        """
        phase = PhaseFactory()
        
        task1 = Task.objects.create(
            phase=phase,
            title='Revisar planos'
        )
        task2 = Task.objects.create(
            phase=phase,
            title='Revisar planos'
        )
        
        assert task1.title == task2.title
        assert task1.pk != task2.pk


# ============================================================================
# TESTS DE INDEXES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskIndexes:
    """Tests de que los índices están configurados correctamente"""
    
    def test_task_has_phase_status_due_date_index(self):
        """Verificar que existe índice task_phase_status_idx"""
        indexes = [index.name for index in Task._meta.indexes]
        assert 'task_phase_status_idx' in indexes
    
    def test_task_has_assigned_status_due_date_index(self):
        """Verificar que existe índice task_assigned_status_idx"""
        indexes = [index.name for index in Task._meta.indexes]
        assert 'task_assigned_status_idx' in indexes
    
    def test_task_has_progress_index(self):
        """Verificar que existe índice task_progress_idx"""
        indexes = [index.name for index in Task._meta.indexes]
        assert 'task_progress_idx' in indexes
    
    def test_task_has_due_status_index(self):
        """Verificar que existe índice task_due_status_idx"""
        indexes = [index.name for index in Task._meta.indexes]
        assert 'task_due_status_idx' in indexes
    
    def test_task_status_field_has_db_index(self):
        """Verificar que status tiene db_index=True"""
        status_field = Task._meta.get_field('status')
        assert status_field.db_index is True
    
    def test_task_priority_field_has_db_index(self):
        """Verificar que priority tiene db_index=True"""
        priority_field = Task._meta.get_field('priority')
        assert priority_field.db_index is True
    
    def test_task_due_date_field_has_db_index(self):
        """Verificar que due_date tiene db_index=True"""
        due_date_field = Task._meta.get_field('due_date')
        assert due_date_field.db_index is True


# ============================================================================
# TESTS DE META OPTIONS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskMetaOptions:
    """Tests de opciones Meta del modelo"""
    
    def test_task_verbose_name(self):
        """Verificar verbose_name configurado"""
        assert Task._meta.verbose_name == 'Tarea'
    
    def test_task_verbose_name_plural(self):
        """Verificar verbose_name_plural configurado"""
        assert Task._meta.verbose_name_plural == 'Tareas'
    
    def test_task_ordering(self):
        """Verificar ordenamiento por defecto"""
        assert Task._meta.ordering == ['due_date', 'priority']


# ============================================================================
# TESTS DE INTEGRACIÓN CON CACHE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskCacheInvalidation:
    """Tests de invalidación de caché"""
    
    @patch('apps.projects.models.invalidate_user_accessible_projects_cache')
    def test_task_assignment_invalidates_user_cache(self, mock_invalidate):
        """
        Cambio de asignación debe invalidar cache del usuario
        """
        user1 = UserFactory()
        user2 = UserFactory()
        task = TaskFactory(assigned_to=user1)
        
        # Cambiar asignación
        task.assigned_to = user2
        task.save()
        
        # Debe invalidar cache de ambos usuarios
        assert mock_invalidate.call_count == 2

