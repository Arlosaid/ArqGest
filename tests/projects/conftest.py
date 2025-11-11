"""
Configuración de fixtures para tests de Projects
"""
import pytest
from django.db.models.signals import pre_save, post_save, post_delete


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

