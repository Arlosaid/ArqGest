"""
Factory para crear organizaciones de prueba
"""
import factory
from factory.django import DjangoModelFactory
from apps.orgs.models import Organization, Client
from decimal import Decimal


class OrganizationFactory(DjangoModelFactory):
    """Factory para crear organizaciones de prueba"""
    
    class Meta:
        model = Organization
        django_get_or_create = ('name',)
    
    # Datos básicos
    name = factory.Sequence(lambda n: f'Organization {n}')
    description = factory.Faker('text', max_nb_chars=200)
    
    # Estados
    is_active = True
    is_founder_member = False
    extra_storage_gb = 0
    founder_discount_percentage = Decimal('0.00')


class InactiveOrganizationFactory(OrganizationFactory):
    """Factory para organizaciones inactivas"""
    is_active = False


class FounderOrganizationFactory(OrganizationFactory):
    """Factory para organizaciones con membresía fundadora"""
    is_founder_member = True
    founder_discount_percentage = Decimal('33.44')
    founder_joined_date = factory.Faker('date_time_this_year')


class OrganizationWithExtraStorageFactory(OrganizationFactory):
    """Factory para organizaciones con almacenamiento extra"""
    extra_storage_gb = 100  # 100 GB extra


class ClientFactory(DjangoModelFactory):
    """Factory para crear clientes de prueba"""
    
    class Meta:
        model = Client
    
    # Relación con organización
    organization = factory.SubFactory(OrganizationFactory)
    
    # Datos básicos
    name = factory.Sequence(lambda n: f'Client {n}')
    email = factory.Faker('email')
    phone_number = factory.Faker('phone_number')
    address = factory.Faker('address')
    
    # Estados
    is_active = True


class InactiveClientFactory(ClientFactory):
    """Factory para clientes inactivos"""
    is_active = False
