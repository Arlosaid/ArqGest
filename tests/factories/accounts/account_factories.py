"""
Factory para crear usuarios de prueba
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth import get_user_model

fake = Faker()
User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory para crear usuarios de prueba"""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    # Datos básicos
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    
    # Organización - usamos LazyAttribute para crear solo si no se proporciona
    organization = factory.SubFactory('tests.factories.orgs.OrganizationFactory')
    
    # Password
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    
    # Estados
    is_active = True
    is_staff = False
    is_superuser = False
    is_org_admin = False
    password_change_required = False
    
    # El username se genera automáticamente en el modelo
    username = None


class SuperUserFactory(UserFactory):
    """Factory para crear superusuarios"""
    
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    first_name = 'Admin'
    last_name = factory.Faker('last_name')
    
    is_staff = True
    is_superuser = True
    is_active = True


class OrgAdminFactory(UserFactory):
    """Factory para crear administradores de organización"""
    
    email = factory.Sequence(lambda n: f'orgadmin{n}@example.com')
    is_org_admin = True


class InactiveUserFactory(UserFactory):
    """Factory para crear usuarios inactivos"""
    
    is_active = False
    organization = None  # Los usuarios inactivos pueden no tener org
