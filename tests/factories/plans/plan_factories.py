"""
Factories para modelos de Plans usando factory_boy
"""
import factory
from decimal import Decimal
from django.utils import timezone
from apps.plans.models import Plan, Subscription, Payment


class PlanFactory(factory.django.DjangoModelFactory):
    """Factory para crear planes de prueba"""
    
    class Meta:
        model = Plan
    
    name = factory.Sequence(lambda n: f'plan_{n}')
    display_name = factory.Sequence(lambda n: f'Plan {n}')
    description = factory.Faker('text', max_nb_chars=200)
    price = Decimal('299.00')
    max_users = 3
    max_storage_gb = 25
    trial_days = 0
    billing_cycle_days = 30
    grace_period_days = 0
    is_active = True


class TrialPlanFactory(PlanFactory):
    """Factory para crear planes trial"""
    
    name = factory.Sequence(lambda n: f'trial_{n}')
    display_name = 'Plan de Prueba'
    price = Decimal('0.00')
    max_users = 1
    max_storage_gb = 10
    trial_days = 7
    billing_cycle_days = 30


class BasicPlanFactory(PlanFactory):
    """Factory para crear planes básicos"""
    
    name = factory.Sequence(lambda n: f'basic_{n}')
    display_name = 'Plan Básico'
    price = Decimal('299.00')
    max_users = 3
    max_storage_gb = 25
    trial_days = 0
    billing_cycle_days = 30


class SubscriptionFactory(factory.django.DjangoModelFactory):
    """Factory para crear suscripciones"""
    
    class Meta:
        model = Subscription
    
    organization = factory.SubFactory('tests.factories.orgs.org_factories.OrganizationFactory')
    plan = factory.SubFactory(BasicPlanFactory)
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timezone.timedelta(days=obj.plan.billing_cycle_days)
    )
    subscription_status = 'basic_active'


class TrialSubscriptionFactory(SubscriptionFactory):
    """Factory para crear suscripciones trial"""
    
    plan = factory.SubFactory(TrialPlanFactory, name='trial')
    subscription_status = 'trial_active'


class PaymentFactory(factory.django.DjangoModelFactory):
    """Factory para crear pagos"""
    
    class Meta:
        model = Payment
    
    subscription = factory.SubFactory(SubscriptionFactory)
    amount = Decimal('299.00')
    payment_method = 'manual'
    payment_type = 'subscription'
    status = 'completed'
    processed_by = 'system'
    description = factory.Faker('sentence')
    days_added = 30

