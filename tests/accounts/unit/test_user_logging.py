"""
🔴 TESTS DE LOGGING - MODELO USER (ALTA PRIORIDAD)

Estos tests verifican que los eventos críticos de negocio se loggean correctamente
para auditoría, debugging y compliance (GDPR, regulaciones financieras, etc.)

IMPORTANCIA:
- Auditoría legal: Probar quién hizo qué y cuándo
- Debugging producción: Identificar problemas sin acceso directo
- Compliance: GDPR, SOX, HIPAA requieren logs de cambios
- Análisis de negocio: KPIs, métricas de uso
- Seguridad: Detectar actividad sospechosa

FUNCIONALIDADES PROBADAS:
1. user_created - Business event de creación exitosa
2. user_creation_failed - Error logging con código USR001
3. superuser_created - Business event de superuser

COBERTURA: 3/7 tests de logging (42%)
- ✅ user_created
- ✅ user_creation_failed  
- ✅ superuser_created
- ⏳ user_creation_started (DEBUG only)
- ⏳ superuser_creation_failed (is_staff)
- ⏳ superuser_creation_failed (is_superuser)
- ⏳ user_updated (cambios críticos)

Autor: ARC Manager Team
Fecha: 4 Nov 2025
Fase: 2 - Alta Prioridad
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import transaction
import logging
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.mark.unit
class TestUserCreationLogging:
    """
    Tests para verificar que la creación de usuarios genera logs apropiados
    para auditoría y debugging.
    """
    
    @patch('apps.accounts.models.log_business_event')
    def test_user_creation_logs_business_event(self, mock_log_business, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que creación exitosa loggea business event
        
        ¿POR QUÉ ES IMPORTANTE?
        - Auditoría legal: Necesitamos saber cuándo se creó cada usuario
        - Compliance GDPR: Registro de cuando se agregaron datos personales
        - Analytics: Medir crecimiento de usuarios
        - Debugging: Trazabilidad de usuarios en producción
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Se llama a log_business_event con los parámetros correctos
        2. El evento se llama "user_created"
        3. Los campos obligatorios están presentes:
           - event: "user_created"
           - action: "created"
           - entity_type: "user"
           - entity_id: ID del usuario
           - user_email: Email del usuario
           - organization_id: ID de org o None
        
        ¿QUÉ PASARÍA SI FALLA?
        - No podríamos auditar creaciones de usuarios
        - Violación de compliance en industrias reguladas
        - Imposible rastrear origen de usuarios spam
        - Analytics de crecimiento inexacto
        
        FORMATO ESPERADO DE LA LLAMADA:
        log_business_event(
            event="user_created",
            action="created",
            entity_type="user",
            entity_id=123,
            user_email="test@example.com",
            organization_id=None,
            logger_name='apps.accounts'
        )
        """
        # ARRANGE & ACT: Crear usuario usando el manager
        user = User.objects.create_user(
            email='test@example.com',
            password='SecurePass123!',
            first_name='Test',
            last_name='User'
        )
        
        # ASSERT: Verificar que se llamó a log_business_event
        assert mock_log_business.called, \
            "No se llamó a log_business_event durante la creación del usuario"
        
        # Verificar que se llamó al menos una vez con event="user_created"
        user_created_calls = [
            call for call in mock_log_business.call_args_list
            if call[1].get('event') == 'user_created'  # call[1] son los kwargs
        ]
        assert len(user_created_calls) >= 1, \
            "No se encontró ninguna llamada con event='user_created'"
        
        # Obtener la última llamada de user_created
        last_call = user_created_calls[-1]
        kwargs = last_call[1]  # Los argumentos nombrados
        
        # Verificar campos obligatorios
        assert kwargs['event'] == 'user_created', \
            f"Evento esperado 'user_created', obtuve '{kwargs.get('event')}'"
        
        assert kwargs['action'] == 'created', \
            f"Action esperado 'created', obtuve '{kwargs.get('action')}'"
        
        assert kwargs['entity_type'] == 'user', \
            f"Entity_type esperado 'user', obtuve '{kwargs.get('entity_type')}'"
        
        assert kwargs['entity_id'] == user.pk, \
            f"Entity_id esperado {user.pk}, obtuve '{kwargs.get('entity_id')}'"
        
        assert kwargs['user_email'] == 'test@example.com', \
            f"User_email esperado 'test@example.com', obtuve '{kwargs.get('user_email')}'"
        
        assert 'organization_id' in kwargs, \
            "El log debe incluir 'organization_id'"
        assert kwargs['organization_id'] is None, \
            f"Organization_id esperado None, obtuve '{kwargs.get('organization_id')}'"
        
        assert kwargs['logger_name'] == 'apps.accounts', \
            f"Logger_name esperado 'apps.accounts', obtuve '{kwargs.get('logger_name')}'"
    
    
    @patch('apps.accounts.models.log_error')
    def test_user_creation_failure_logs_error(self, mock_log_error, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que fallos en creación loggean errores con código
        
        ¿POR QUÉ ES IMPORTANTE?
        - Debugging: Identificar por qué fallan las creaciones
        - Alertas: Monitorear tasas de error en registros
        - Soporte: Ayudar a usuarios bloqueados
        - Seguridad: Detectar ataques de registro masivo
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Se llama a log_error cuando falla la creación
        2. El evento se llama "user_creation_failed"
        3. El log contiene:
           - event: "user_creation_failed"
           - error_code: "USR001"
           - error_message: Descripción del error
           - user_email: Email que intentó registrarse
        
        ¿QUÉ PASARÍA SI FALLA?
        - Errores silenciosos en producción
        - No podríamos identificar problemas sistémicos
        - Usuarios frustrados sin soporte
        - Imposible detectar ataques automatizados
        
        FORMATO ESPERADO DE LA LLAMADA:
        log_error(
            event="user_creation_failed",
            error_code="USR001",
            error_message="...",
            user_email="duplicate@example.com",
            logger_name='apps.accounts'
        )
        """
        # ARRANGE: Crear un usuario primero
        User.objects.create_user(
            email='duplicate@example.com',
            password='FirstPassword123!'
        )
        
        # ACT: Intentar crear usuario con email duplicado
        # Esto debería lanzar IntegrityError y loggearse
        with pytest.raises(Exception):  # IntegrityError o ValidationError
            User.objects.create_user(
                email='duplicate@example.com',
                password='SecondPassword123!'
            )
        
        # ASSERT: Verificar que se llamó a log_error
        assert mock_log_error.called, \
            "No se llamó a log_error durante el fallo de creación"
        
        # Buscar la llamada con event="user_creation_failed"
        creation_failed_calls = [
            call for call in mock_log_error.call_args_list
            if call[1].get('event') == 'user_creation_failed'
        ]
        assert len(creation_failed_calls) >= 1, \
            "No se encontró ninguna llamada con event='user_creation_failed'"
        
        # Obtener la última llamada
        last_call = creation_failed_calls[-1]
        kwargs = last_call[1]
        
        # Verificar campos obligatorios
        assert kwargs['event'] == 'user_creation_failed', \
            f"Evento esperado 'user_creation_failed', obtuve '{kwargs.get('event')}'"
        
        assert kwargs['error_code'] == 'USR001', \
            f"Error_code esperado 'USR001', obtuve '{kwargs.get('error_code')}'"
        
        assert 'error_message' in kwargs, \
            "El log debe tener el campo 'error_message'"
        assert len(kwargs['error_message']) > 0, \
            "El error_message no debe estar vacío"
        
        assert kwargs['user_email'] == 'duplicate@example.com', \
            f"User_email esperado 'duplicate@example.com', obtuve '{kwargs.get('user_email')}'"
        
        assert kwargs['logger_name'] == 'apps.accounts', \
            f"Logger_name esperado 'apps.accounts', obtuve '{kwargs.get('logger_name')}'"
    
    
    @patch('apps.accounts.models.log_business_event')
    def test_superuser_creation_logs_business_event(self, mock_log_business, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que creación de superuser loggea evento especial
        
        ¿POR QUÉ ES IMPORTANTE?
        - Seguridad: Creación de superusers es evento crítico
        - Auditoría: Requisito legal en muchas industrias
        - Compliance: SOX, HIPAA requieren logs de privilegios
        - Forense: Investigar brechas de seguridad
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Se generan DOS logs de business event:
           a) user_created (del método create_user)
           b) superuser_created (adicional para auditoría)
        2. El log de superuser_created contiene:
           - event: "superuser_created"
           - action: "created"
           - entity_type: "superuser" (no "user")
           - entity_id: ID del usuario
           - user_email: Email del superuser
        
        ¿QUÉ PASARÍA SI FALLA?
        - No podríamos auditar creación de cuentas privilegiadas
        - Violación de compliance en sectores regulados
        - Imposible rastrear creación de superusers maliciosos
        - Falta de trazabilidad en auditorías de seguridad
        
        FORMATO ESPERADO DE LA LLAMADA:
        log_business_event(
            event="superuser_created",
            action="created",
            entity_type="superuser",
            entity_id=123,
            user_email="admin@example.com",
            logger_name='apps.accounts'
        )
        """
        # ARRANGE & ACT: Crear superuser usando el manager
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='SuperSecurePass123!',
            first_name='Admin',
            last_name='User'
        )
        
        # ASSERT: Verificar que se llamó a log_business_event
        assert mock_log_business.called, \
            "No se llamó a log_business_event durante la creación del superuser"
        
        # Buscar llamadas con event="superuser_created"
        superuser_created_calls = [
            call for call in mock_log_business.call_args_list
            if call[1].get('event') == 'superuser_created'
        ]
        assert len(superuser_created_calls) >= 1, \
            "No se encontró ninguna llamada con event='superuser_created'"
        
        # Obtener la última llamada
        last_call = superuser_created_calls[-1]
        kwargs = last_call[1]
        
        # Verificar campos obligatorios
        assert kwargs['event'] == 'superuser_created', \
            f"Evento esperado 'superuser_created', obtuve '{kwargs.get('event')}'"
        
        assert kwargs['action'] == 'created', \
            f"Action esperado 'created', obtuve '{kwargs.get('action')}'"
        
        assert kwargs['entity_type'] == 'superuser', \
            f"Entity_type esperado 'superuser', obtuve '{kwargs.get('entity_type')}'"
        
        assert kwargs['entity_id'] == superuser.pk, \
            f"Entity_id esperado {superuser.pk}, obtuve '{kwargs.get('entity_id')}'"
        
        assert kwargs['user_email'] == 'admin@example.com', \
            f"User_email esperado 'admin@example.com', obtuve '{kwargs.get('user_email')}'"
        
        assert kwargs['logger_name'] == 'apps.accounts', \
            f"Logger_name esperado 'apps.accounts', obtuve '{kwargs.get('logger_name')}'"
        
        # BONUS: Verificar que TAMBIÉN se loggeó user_created
        user_created_calls = [
            call for call in mock_log_business.call_args_list
            if call[1].get('event') == 'user_created'
        ]
        assert len(user_created_calls) >= 1, \
            "También debería loggearse 'user_created' al crear superuser"
