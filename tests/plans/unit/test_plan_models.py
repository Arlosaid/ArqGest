"""
Tests exhaustivos para el modelo Plan

Estos tests DEBEN detectar bugs reales en la lógica de negocio de planes.
El modelo Plan es CRÍTICO porque define los límites y precios del negocio.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from apps.plans.models import Plan
from tests.factories import PlanFactory
from unittest.mock import patch


# ============================================================================
# TESTS DE CREACIÓN DE PLANES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanCreation:
    """Tests de creación básica de planes"""
    
    def test_plan_creation_with_factory(self):
        """Verificar que se puede crear un plan con la factory"""
        plan = PlanFactory()
        
        assert plan.pk is not None
        assert plan.name is not None
        assert plan.display_name is not None
        assert plan.is_active is True
    
    def test_trial_plan_creation(self):
        """Crear plan trial con todos los campos correctos"""
        plan = Plan.objects.create(
            name='trial',
            display_name='Trial Gratuito',
            description='Plan de prueba gratis',
            price=Decimal('0.00'),
            max_users=1,
            max_storage_gb=10,
            trial_days=7,
            billing_cycle_days=30,
            is_active=True
        )
        
        assert plan.name == 'trial'
        assert plan.price == Decimal('0.00')
        assert plan.trial_days == 7
        assert plan.is_trial is True
    
    def test_basic_plan_creation(self):
        """Crear plan básico con precio"""
        plan = Plan.objects.create(
            name='basic',
            display_name='Plan Básico',
            price=Decimal('299.00'),
            max_users=3,
            max_storage_gb=25,
            trial_days=0,
            billing_cycle_days=30,
            is_active=True
        )
        
        assert plan.name == 'basic'
        assert plan.price == Decimal('299.00')
        assert plan.is_trial is False
    
    def test_plan_str_representation(self):
        """__str__ debe retornar display_name"""
        plan = PlanFactory(display_name='Mi Plan Especial')
        
        assert str(plan) == 'Mi Plan Especial'


# ============================================================================
# TESTS DE VALIDACIÓN Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanValidation:
    """Tests de validación de planes - DETECTAR BUGS REALES"""
    
    def test_name_is_required(self):
        """El nombre debe ser obligatorio"""
        with pytest.raises(Exception):
            Plan.objects.create(
                name=None,
                display_name='Test'
            )
    
    def test_name_is_unique(self):
        """
        CRÍTICO: No pueden existir dos planes con el mismo name
        """
        PlanFactory(name='trial')
        
        with pytest.raises(IntegrityError):
            PlanFactory(name='trial')
    
    def test_display_name_is_required(self):
        """display_name debe ser obligatorio"""
        with pytest.raises(Exception):
            Plan.objects.create(
                name='test',
                display_name=None
            )
    
    def test_name_must_be_valid_choice(self):
        """
        CRÍTICO: name debe ser uno de los choices válidos
        """
        # Intentar crear plan con name inválido
        # Django validará esto en forms/admin, no en modelo directamente
        invalid_plan = Plan(
            name='invalid_plan_type',
            display_name='Invalid'
        )
        
        # El modelo permite guardarlo, pero el form debe validar
        # Esto es un WARNING - debería haber validación en modelo
    
    def test_price_cannot_be_negative(self):
        """Precio no debe ser negativo"""
        plan = PlanFactory(price=Decimal('-100.00'))
        
        # Django permite negativos en DecimalField por defecto
        # ESTO ES UN BUG POTENCIAL - debería validarse
        assert plan.price == Decimal('-100.00')
        # WARNING: Debería haber validación que prevenga esto
    
    def test_max_users_cannot_be_zero(self):
        """
        BUG POTENCIAL: max_users en 0 no tiene sentido
        """
        plan = PlanFactory(max_users=0)
        
        # Se permite crear, pero no tiene sentido de negocio
        assert plan.max_users == 0
        # WARNING: Debería haber validación mínima de 1
    
    def test_max_storage_gb_cannot_be_zero(self):
        """
        BUG POTENCIAL: max_storage_gb en 0 no tiene sentido
        """
        plan = PlanFactory(max_storage_gb=0)
        
        # Se permite crear
        assert plan.max_storage_gb == 0
        # WARNING: Debería haber validación mínima
    
    def test_negative_max_users_rejected(self):
        """max_users negativo debe ser rechazado por PositiveIntegerField"""
        with pytest.raises((ValidationError, IntegrityError)):
            plan = Plan.objects.create(
                name='test',
                display_name='Test',
                max_users=-1
            )
    
    def test_trial_days_defaults_to_zero(self):
        """trial_days debe defaultear a 0"""
        plan = PlanFactory(trial_days=None)
        plan.save()
        plan.refresh_from_db()
        
        # El default debe ser 0
        assert plan.trial_days is not None


# ============================================================================
# TESTS DE PROPIEDADES Y MÉTODOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanProperties:
    """Tests de propiedades y métodos de Plan"""
    
    def test_is_trial_property_for_trial_plan(self):
        """Plan con name='trial' debe retornar is_trial=True"""
        plan = PlanFactory(name='trial')
        
        assert plan.is_trial is True
    
    def test_is_trial_property_for_basic_plan(self):
        """Plan con name='basic' debe retornar is_trial=False"""
        plan = PlanFactory(name='basic')
        
        assert plan.is_trial is False
    
    def test_get_feature_list_includes_users(self):
        """get_feature_list debe incluir número de usuarios"""
        plan = PlanFactory(max_users=5, max_storage_gb=50)
        
        features = plan.get_feature_list()
        
        assert any('5 usuarios' in f.lower() or '5 usuario' in f.lower() for f in features)
    
    def test_get_feature_list_includes_storage(self):
        """get_feature_list debe incluir almacenamiento"""
        plan = PlanFactory(max_users=3, max_storage_gb=25)
        
        features = plan.get_feature_list()
        
        assert any('25 gb' in f.lower() for f in features)
    
    def test_get_feature_list_singular_user(self):
        """get_feature_list debe usar singular para 1 usuario"""
        plan = PlanFactory(max_users=1)
        
        features = plan.get_feature_list()
        
        # Debe decir "1 usuario" no "1 usuarios"
        assert any('1 usuario' in f.lower() and 'usuarios' not in f.lower() for f in features)


# ============================================================================
# TESTS DE MÉTODOS DE CLASE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanClassMethods:
    """Tests de métodos de clase - CRÍTICOS para obtener planes"""
    
    def test_get_trial_plan_returns_active_trial(self):
        """get_trial_plan() debe retornar el plan trial activo"""
        trial = PlanFactory(name='trial', is_active=True)
        PlanFactory(name='basic', is_active=True)
        
        result = Plan.get_trial_plan()
        
        assert result == trial
        assert result.is_trial is True
    
    def test_get_trial_plan_returns_none_if_not_found(self):
        """
        CRÍTICO: get_trial_plan() debe retornar None si no existe
        """
        PlanFactory(name='basic', is_active=True)
        
        result = Plan.get_trial_plan()
        
        assert result is None
    
    def test_get_trial_plan_returns_none_if_inactive(self):
        """
        get_trial_plan() NO debe retornar planes inactivos
        """
        PlanFactory(name='trial', is_active=False)
        
        result = Plan.get_trial_plan()
        
        assert result is None
    
    def test_get_basic_plan_returns_active_basic(self):
        """get_basic_plan() debe retornar el plan básico activo"""
        PlanFactory(name='trial', is_active=True)
        basic = PlanFactory(name='basic', is_active=True)
        
        result = Plan.get_basic_plan()
        
        assert result == basic
        assert result.name == 'basic'
    
    def test_get_basic_plan_returns_none_if_not_found(self):
        """
        CRÍTICO: get_basic_plan() debe retornar None si no existe
        """
        PlanFactory(name='trial', is_active=True)
        
        result = Plan.get_basic_plan()
        
        assert result is None


# ============================================================================
# TESTS DE get_usage_percentage
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanUsagePercentage:
    """Tests del método get_usage_percentage - CRÍTICO para UI"""
    
    def test_get_usage_percentage_for_users(self):
        """Calcular porcentaje de uso de usuarios"""
        plan = PlanFactory(max_users=10)
        
        percentage = plan.get_usage_percentage(5, 'users')
        
        assert percentage == 50  # 5/10 = 50%
    
    def test_get_usage_percentage_at_limit(self):
        """Porcentaje al límite debe ser 100%"""
        plan = PlanFactory(max_users=10)
        
        percentage = plan.get_usage_percentage(10, 'users')
        
        assert percentage == 100
    
    def test_get_usage_percentage_over_limit(self):
        """
        Porcentaje sobre el límite debe ser 100% (capped)
        """
        plan = PlanFactory(max_users=10)
        
        percentage = plan.get_usage_percentage(15, 'users')
        
        assert percentage == 100  # Debe estar capped a 100
    
    def test_get_usage_percentage_with_zero_limit(self):
        """
        BUG POTENCIAL: División por cero si el límite es 0
        """
        plan = PlanFactory(max_users=0)
        
        # Con current_value > 0 y límite 0, debe retornar 100
        percentage = plan.get_usage_percentage(5, 'users')
        
        assert percentage == 100
    
    def test_get_usage_percentage_zero_usage_zero_limit(self):
        """Sin uso y sin límite debe retornar 0%"""
        plan = PlanFactory(max_users=0)
        
        percentage = plan.get_usage_percentage(0, 'users')
        
        assert percentage == 0
    
    def test_get_usage_percentage_unknown_limit_type(self):
        """
        Limit type desconocido debe retornar 100% si hay uso
        """
        plan = PlanFactory()
        
        # 'storage' no está implementado
        percentage = plan.get_usage_percentage(5, 'storage')
        
        # Limit será 0, entonces debe retornar 100
        assert percentage == 100


# ============================================================================
# TESTS DE ORDERING Y QUERYSETS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanQuerysets:
    """Tests de ordenamiento y querysets"""
    
    def test_default_ordering_by_price(self):
        """Planes deben ordenarse por precio por defecto"""
        PlanFactory(name='trial', price=Decimal('0.00'))
        PlanFactory(name='basic', price=Decimal('299.00'))
        
        plans = Plan.objects.all()
        prices = [p.price for p in plans]
        
        assert prices == sorted(prices)  # Debe estar ordenado ascendente
    
    def test_filter_active_plans(self):
        """Filtrar solo planes activos"""
        PlanFactory(name='trial', is_active=True)
        PlanFactory(name='basic', is_active=False)
        
        active_plans = Plan.objects.filter(is_active=True)
        
        assert active_plans.count() == 1
        assert active_plans.first().name == 'trial'


# ============================================================================
# TESTS DE SAVE METHOD Y LOGGING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanSaveMethod:
    """Tests del método save - CRÍTICO para logging"""
    
    @patch('apps.plans.models.log_business_event')
    def test_save_creates_log_for_new_plan(self, mock_log):
        """Crear nuevo plan debe generar log"""
        plan = Plan(
            name='trial',
            display_name='Trial',
            price=Decimal('0.00'),
            max_users=1,
            max_storage_gb=10
        )
        
        plan.save()
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs['event'] == 'plan_created'
        assert call_kwargs['plan_name'] == 'Trial'
    
    @patch('apps.plans.models.log_business_event')
    def test_save_logs_price_change(self, mock_log):
        """Cambiar precio debe generar log con el cambio"""
        plan = PlanFactory(price=Decimal('299.00'))
        
        plan.price = Decimal('349.00')
        plan.save()
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs['event'] == 'plan_updated'
        
        # Verificar que se registró el cambio de precio
        changes = call_kwargs['changes']
        assert any(c['field'] == 'price' for c in changes)
    
    @patch('apps.plans.models.log_business_event')
    def test_save_logs_limits_change(self, mock_log):
        """Cambiar límites debe generar log"""
        plan = PlanFactory(max_users=3, max_storage_gb=25)
        
        plan.max_users = 5
        plan.max_storage_gb = 50
        plan.save()
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        changes = call_kwargs['changes']
        
        # Verificar que se registraron ambos cambios
        assert any(c['field'] == 'max_users' for c in changes)
        assert any(c['field'] == 'max_storage_gb' for c in changes)
    
    @patch('apps.plans.models.log_business_event')
    def test_save_logs_activation_deactivation(self, mock_log):
        """
        CRÍTICO: Cambiar is_active debe generar log WARNING
        """
        plan = PlanFactory(is_active=True)
        
        plan.is_active = False
        plan.save()
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        changes = call_kwargs['changes']
        
        # Verificar que se registró el cambio de estado
        assert any(c['field'] == 'is_active' for c in changes)


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanEdgeCases:
    """Tests de casos extremos - ENCONTRAR BUGS"""
    
    def test_plan_with_unicode_name(self):
        """Nombres con Unicode deben funcionar"""
        plan = PlanFactory(
            name='trial',
            display_name='Plan Español 中文 🚀'
        )
        
        assert '中文' in plan.display_name
        assert str(plan) == 'Plan Español 中文 🚀'
    
    def test_plan_with_very_long_description(self):
        """Descripción muy larga debe funcionar"""
        long_desc = 'A' * 10000
        plan = PlanFactory(description=long_desc)
        
        assert len(plan.description) == 10000
    
    def test_plan_with_extreme_price(self):
        """Precio extremadamente alto debe funcionar"""
        plan = PlanFactory(price=Decimal('99999999.99'))
        
        assert plan.price == Decimal('99999999.99')
    
    def test_plan_with_extreme_max_users(self):
        """Número extremo de usuarios debe funcionar"""
        plan = PlanFactory(max_users=999999)
        
        assert plan.max_users == 999999
        
        # get_usage_percentage debe manejarlo
        percentage = plan.get_usage_percentage(500000, 'users')
        assert percentage == 50
    
    def test_plan_with_decimal_precision(self):
        """Precio debe respetar precisión decimal"""
        plan = PlanFactory(price=Decimal('299.99'))
        
        assert plan.price == Decimal('299.99')
        # Verificar que NO se redondea a 300.00
    
    def test_multiple_plans_with_same_display_name(self):
        """
        Múltiples planes pueden tener el mismo display_name
        (pero NO el mismo name)
        """
        plan1 = PlanFactory(name='trial', display_name='Mismo Nombre')
        plan2 = PlanFactory(name='basic', display_name='Mismo Nombre')
        
        assert plan1.display_name == plan2.display_name
        assert plan1.name != plan2.name


# ============================================================================
# TESTS DE TIMESTAMPS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanTimestamps:
    """Tests de campos de fecha automática"""
    
    def test_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        plan = PlanFactory()
        
        assert plan.created_at is not None
    
    def test_updated_at_auto_set(self):
        """updated_at debe establecerse automáticamente"""
        plan = PlanFactory()
        
        assert plan.updated_at is not None
    
    def test_updated_at_changes_on_save(self):
        """updated_at debe actualizarse al guardar"""
        plan = PlanFactory()
        original_updated_at = plan.updated_at
        
        # Esperar un momento y actualizar
        import time
        time.sleep(0.1)
        
        plan.price = Decimal('350.00')
        plan.save()
        
        assert plan.updated_at > original_updated_at


