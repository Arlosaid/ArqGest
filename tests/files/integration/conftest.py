"""
Configuración específica para tests de integración de files.
"""
import pytest
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore


@pytest.fixture(scope='function', autouse=True)
def disable_integration_test_middlewares(settings):
    """
    Deshabilita middlewares problemáticos para tests de integración.
    
    Esta fixture se aplica automáticamente a todos los tests de integración
    en este módulo usando autouse=True.
    """
    # Forzar TESTING = True para que los middlewares se bypaseen
    settings.TESTING = True
    
    yield
    
    # Restaurar valor original
    settings.TESTING = False


def setup_request_with_messages(request):
    """
    Helper para configurar un request de RequestFactory con soporte para messages.
    
    Usage:
        factory = RequestFactory()
        request = factory.post(...)
        request.user = user
        setup_request_with_messages(request)
    """
    # Agregar session
    request.session = SessionStore()
    # Agregar messages
    request._messages = FallbackStorage(request)
    return request

