"""
Configuración de fixtures para tests de Projects
"""
import pytest
from django.db.models.signals import pre_save, post_save, post_delete
from decimal import Decimal


@pytest.fixture(autouse=True)
def disable_account_signals():
    """
    Deshabilitar signals de accounts que validan límites de usuarios
    para evitar que interfieran con los tests.
    
    Este fixture se aplica automáticamente a todos los tests del módulo projects.
    """
    from apps.accounts import signals as account_signals
    from apps.accounts.models import User
    
    # Desconectar el signal que valida límites de organización
    pre_save.disconnect(
        account_signals.validate_organization_limits,
        sender=User
    )
    
    yield
    
    # Reconectar después del test
    pre_save.connect(
        account_signals.validate_organization_limits,
        sender=User
    )


@pytest.fixture
def organization(db):
    """Crear organización de prueba con suscripción."""
    from apps.orgs.models import Organization
    from apps.plans.models import Plan, Subscription
    
    org = Organization.objects.create(
        name='Test Organization',
        is_active=True
    )
    
    # Crear o obtener plan trial
    plan, _ = Plan.objects.get_or_create(
        name='trial',
        defaults={
            'display_name': 'Trial',
            'is_active': True,
            'max_users': 5,
            'max_storage_gb': 10,
            'trial_days': 14
        }
    )
    
    # Crear suscripción
    Subscription.objects.create(
        organization=org,
        plan=plan
    )
    
    return org


@pytest.fixture
def subscription(organization):
    """Retorna la suscripción de la organización de prueba."""
    return organization.subscription


@pytest.fixture
def basic_plan(db):
    """Crear plan básico de prueba."""
    from apps.plans.models import Plan
    
    plan, _ = Plan.objects.get_or_create(
        name='basic',
        defaults={
            'display_name': 'Plan Básico',
            'is_active': True,
            'price': Decimal('299.00'),
            'max_users': 10,
            'max_storage_gb': 50,
            'billing_cycle_days': 30
        }
    )
    return plan


@pytest.fixture
def user_for_project(db, organization):
    """Crear usuario para ser owner de proyectos."""
    from apps.accounts.models import User
    
    user = User.objects.create_user(
        email='testowner@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Owner',
        organization=organization,
        is_org_admin=True
    )
    return user


@pytest.fixture
def project_with_phase(organization, user_for_project):
    """Crear proyecto con una fase para tests."""
    from apps.projects.models import Project, Phase
    
    project = Project.objects.create(
        organization=organization,
        owner=user_for_project,
        name='Test Project',
        status='ACTIVE'
    )
    
    Phase.objects.create(
        project=project,
        name='Phase 1',
        order=1
    )
    
    return project


@pytest.fixture
def project_with_budget(organization, user_for_project):
    """Crear proyecto con presupuesto configurado."""
    from apps.projects.models import Project
    
    project = Project.objects.create(
        organization=organization,
        owner=user_for_project,
        name='Project with Budget',
        status='ACTIVE',
        total_budget=Decimal('10000.00'),
        budget_configured=True
    )
    
    return project

