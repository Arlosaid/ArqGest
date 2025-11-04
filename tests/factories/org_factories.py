"""
Factory para crear organizaciones de prueba
"""
import factory
from factory.django import DjangoModelFactory
from apps.orgs.models import Organization


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
    founder_discount_percentage = 0
