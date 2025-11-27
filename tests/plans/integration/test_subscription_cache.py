# tests/plans/integration/test_subscription_cache.py
"""
Tests de integración para verificar que el cache se invalida correctamente
cuando se crean o modifican suscripciones.
"""
import pytest
from django.core.cache import cache
from apps.orgs.models import Organization
from apps.plans.models import Plan, Subscription


@pytest.mark.django_db
class TestSubscriptionCacheInvalidation:
    """Tests para verificar invalidación de cache al modificar suscripciones"""
    
    def test_cache_invalidated_when_creating_subscription(self):
        """
        Bug Visual Fix: Cuando se crea una suscripción para una org,
        el cache de storage debe invalidarse para mostrar el límite correcto.
        """
        # 1. Crear organización SIN suscripción (usa fallback de 75 GB)
        org = Organization.objects.create(
            name="Test Org",
            extra_storage_gb=0
        )
        
        # 2. Llamar al método que cachea el storage (simula vista del dashboard)
        initial_limit = org.get_total_storage_limit_gb()
        assert initial_limit == 10  # Fallback
        
        # 3. Establecer cache manualmente (simula primera carga del dashboard)
        cache_key = f"org_storage:{org.id}"
        cache.set(cache_key, {'total_gb': 10}, timeout=300)
        
        # 4. Verificar que el cache existe
        cached_value = cache.get(cache_key)
        assert cached_value is not None
        assert cached_value['total_gb'] == 10
        
        # 5. Crear plan de 10 GB (trial)
        trial_plan = Plan.objects.create(
            name='trial',
            display_name='Trial Plan',
            max_storage_gb=10,
            max_users=1,
            trial_days=7,
            is_active=True
        )
        
        # 6. Asignar suscripción a la org (esto debe invalidar el cache)
        subscription = Subscription.objects.create(
            organization=org,
            plan=trial_plan
        )
        
        # 7. Verificar que el cache fue invalidado
        cached_value_after = cache.get(cache_key)
        assert cached_value_after is None, (
            "El cache de storage debería haberse invalidado al crear la suscripción"
        )
        
        # 8. Verificar que el nuevo límite es correcto (10 GB del plan)
        org.refresh_from_db()
        new_limit = org.get_total_storage_limit_gb()
        assert new_limit == 10, (
            f"El límite debería ser 10 GB (del plan trial), pero es {new_limit} GB"
        )
    
    def test_cache_invalidated_when_switching_plan(self):
        """
        Bug Visual Fix: Cuando se cambia el plan de una suscripción,
        el cache debe invalidarse para mostrar el nuevo límite.
        """
        # 1. Crear org con plan trial (10 GB)
        org = Organization.objects.create(
            name="Test Org Switch",
            extra_storage_gb=0
        )
        
        trial_plan = Plan.objects.create(
            name='trial',
            display_name='Trial Plan',
            max_storage_gb=10,
            max_users=1,
            trial_days=7,
            is_active=True
        )
        
        subscription = Subscription.objects.create(
            organization=org,
            plan=trial_plan
        )
        
        # 2. Cachear el límite actual (10 GB)
        cache_key = f"org_storage:{org.id}"
        cache.set(cache_key, {'total_gb': 10}, timeout=300)
        
        # 3. Verificar que el cache existe con 10 GB
        cached_value = cache.get(cache_key)
        assert cached_value is not None
        assert cached_value['total_gb'] == 10
        
        # 4. Crear plan básico (100 GB)
        basic_plan = Plan.objects.create(
            name='basic',
            display_name='Basic Plan',
            max_storage_gb=100,
            max_users=3,
            billing_cycle_days=30,
            is_active=True
        )
        
        # 5. Cambiar el plan (esto debe invalidar el cache)
        result = subscription.switch_plan(
            new_plan=basic_plan,
            processed_by="admin@test.com"
        )
        
        assert result['success'] is True
        
        # 6. Verificar que el cache fue invalidado
        cached_value_after = cache.get(cache_key)
        assert cached_value_after is None, (
            "El cache de storage debería haberse invalidado al cambiar de plan"
        )
        
        # 7. Verificar que el nuevo límite es correcto (100 GB)
        org.refresh_from_db()
        subscription.refresh_from_db()
        new_limit = org.get_total_storage_limit_gb()
        assert new_limit == 100, (
            f"El límite debería ser 100 GB (del plan basic), pero es {new_limit} GB"
        )
    
    def test_cache_invalidated_when_updating_subscription_plan_directly(self):
        """
        Bug Visual Fix: Cuando se modifica el plan directamente en el admin,
        el cache debe invalidarse.
        """
        # 1. Setup inicial con plan trial
        org = Organization.objects.create(
            name="Test Org Direct",
            extra_storage_gb=0
        )
        
        trial_plan = Plan.objects.create(
            name='trial',
            display_name='Trial Plan',
            max_storage_gb=10,
            max_users=1,
            is_active=True
        )
        
        subscription = Subscription.objects.create(
            organization=org,
            plan=trial_plan
        )
        
        # 2. Cachear límite inicial
        cache_key = f"org_storage:{org.id}"
        cache.set(cache_key, {'total_gb': 10}, timeout=300)
        
        # 3. Crear otro plan
        basic_plan = Plan.objects.create(
            name='basic',
            display_name='Basic Plan',
            max_storage_gb=100,
            max_users=3,
            is_active=True
        )
        
        # 4. Cambiar el plan directamente (como lo haría el admin)
        subscription.plan = basic_plan
        subscription.save()
        
        # 5. Verificar que el cache fue invalidado
        cached_value_after = cache.get(cache_key)
        assert cached_value_after is None, (
            "El cache de storage debería haberse invalidado al modificar el plan"
        )
        
        # 6. Verificar nuevo límite
        org.refresh_from_db()
        new_limit = org.get_total_storage_limit_gb()
        assert new_limit == 100
    
    def test_dashboard_stats_cache_also_invalidated(self):
        """
        Verificar que también se invalida el cache de dashboard_stats
        """
        org = Organization.objects.create(name="Test Org Dashboard")
        
        trial_plan = Plan.objects.create(
            name='trial',
            display_name='Trial',
            max_storage_gb=10,
            is_active=True
        )
        
        # Establecer cache de dashboard stats
        dashboard_cache_key = f"dashboard_stats:{org.id}"
        cache.set(dashboard_cache_key, {'some': 'data'}, timeout=300)
        
        # Verificar que existe
        assert cache.get(dashboard_cache_key) is not None
        
        # Crear suscripción
        Subscription.objects.create(
            organization=org,
            plan=trial_plan
        )
        
        # Verificar que se invalidó
        assert cache.get(dashboard_cache_key) is None, (
            "El cache de dashboard_stats debería haberse invalidado"
        )
    
    def test_subscription_cache_also_invalidated(self):
        """
        Verificar que también se invalida el cache de org_subscription
        """
        org = Organization.objects.create(name="Test Org Subscription")
        
        trial_plan = Plan.objects.create(
            name='trial',
            display_name='Trial',
            max_storage_gb=10,
            is_active=True
        )
        
        # Establecer cache de subscription
        sub_cache_key = f"org_subscription:{org.id}"
        cache.set(sub_cache_key, {'cached': 'subscription'}, timeout=300)
        
        # Verificar que existe
        assert cache.get(sub_cache_key) is not None
        
        # Crear suscripción
        Subscription.objects.create(
            organization=org,
            plan=trial_plan
        )
        
        # Verificar que se invalidó
        assert cache.get(sub_cache_key) is None, (
            "El cache de org_subscription debería haberse invalidado"
        )
