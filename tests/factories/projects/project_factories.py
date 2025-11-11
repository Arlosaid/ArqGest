"""
Factories para modelos de Projects
"""
import factory
from factory.django import DjangoModelFactory
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from apps.projects.models import (
    Project,
    Phase,
    Task,
    ProjectPayment,
    PhaseTemplate
)


class ProjectFactory(DjangoModelFactory):
    """Factory para crear proyectos de prueba"""
    
    class Meta:
        model = Project
    
    # Relaciones
    organization = factory.SubFactory('tests.factories.orgs.org_factories.OrganizationFactory')
    owner = factory.SubFactory('tests.factories.accounts.account_factories.UserFactory')
    client = factory.SubFactory('tests.factories.orgs.org_factories.ClientFactory')
    
    # Datos básicos
    name = factory.Sequence(lambda n: f'Project {n}')
    status = Project.Status.ACTIVE
    
    # Fechas
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=90)).date())
    
    # Campos financieros
    total_budget = Decimal('10000.00')
    budget_configured = True


class ActiveProjectFactory(ProjectFactory):
    """Factory para proyectos activos"""
    status = Project.Status.ACTIVE


class ArchivedProjectFactory(ProjectFactory):
    """Factory para proyectos archivados"""
    status = Project.Status.ARCHIVED


class CompletedProjectFactory(ProjectFactory):
    """Factory para proyectos completados"""
    status = Project.Status.COMPLETED
    end_date = factory.LazyFunction(lambda: timezone.now().date())


class PhaseFactory(DjangoModelFactory):
    """Factory para crear fases de prueba"""
    
    class Meta:
        model = Phase
    
    # Relaciones
    project = factory.SubFactory(ProjectFactory)
    
    # Datos básicos
    name = factory.Sequence(lambda n: f'Phase {n}')
    status = Phase.Status.PENDING
    order = factory.Sequence(lambda n: n + 1)
    notes = factory.Faker('text', max_nb_chars=200)
    
    # Fechas
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=30)).date())


class PendingPhaseFactory(PhaseFactory):
    """Factory para fases pendientes"""
    status = Phase.Status.PENDING


class InProgressPhaseFactory(PhaseFactory):
    """Factory para fases en progreso"""
    status = Phase.Status.IN_PROGRESS


class CompletedPhaseFactory(PhaseFactory):
    """Factory para fases completadas"""
    status = Phase.Status.COMPLETED
    end_date = factory.LazyFunction(lambda: timezone.now().date())


class TaskFactory(DjangoModelFactory):
    """Factory para crear tareas de prueba"""
    
    class Meta:
        model = Task
    
    # Relaciones
    phase = factory.SubFactory(PhaseFactory)
    assigned_to = factory.SubFactory('tests.factories.accounts.account_factories.UserFactory')
    
    # Datos básicos
    title = factory.Sequence(lambda n: f'Task {n}')
    description = factory.Faker('text', max_nb_chars=300)
    status = Task.Status.TODO
    priority = Task.Priority.MEDIUM
    
    # Fechas
    due_date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=7)).date())


class TodoTaskFactory(TaskFactory):
    """Factory para tareas por hacer"""
    status = Task.Status.TODO


class InProgressTaskFactory(TaskFactory):
    """Factory para tareas en progreso"""
    status = Task.Status.IN_PROGRESS


class DoneTaskFactory(TaskFactory):
    """Factory para tareas completadas"""
    status = Task.Status.DONE


class PausedTaskFactory(TaskFactory):
    """Factory para tareas pausadas"""
    status = Task.Status.PAUSED


class HighPriorityTaskFactory(TaskFactory):
    """Factory para tareas de alta prioridad"""
    priority = Task.Priority.HIGH


class ProjectPaymentFactory(DjangoModelFactory):
    """Factory para crear pagos de proyectos"""
    
    class Meta:
        model = ProjectPayment
    
    # Relaciones
    project = factory.SubFactory(ProjectFactory)
    created_by = factory.SubFactory('tests.factories.accounts.account_factories.UserFactory')
    
    # Datos básicos
    amount = Decimal('1000.00')
    date = factory.LazyFunction(lambda: timezone.now().date())
    description = factory.Faker('text', max_nb_chars=200)
    
    # Archivos
    receipt_file = None
    receipt = None


class PhaseTemplateFactory(DjangoModelFactory):
    """Factory para plantillas de fases"""
    
    class Meta:
        model = PhaseTemplate
    
    # Relaciones
    organization = factory.SubFactory('tests.factories.orgs.org_factories.OrganizationFactory')
    
    # Datos básicos
    name = factory.Sequence(lambda n: f'Phase Template {n}')
    description = factory.Faker('text', max_nb_chars=200)
    phases = factory.LazyFunction(lambda: [
        {'name': 'Diseño Preliminar', 'order': 1},
        {'name': 'Diseño Detallado', 'order': 2},
        {'name': 'Construcción', 'order': 3},
    ])

