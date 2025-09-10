#!/usr/bin/env python
"""
Script para probar el sistema de logging estructurado.
Ejecutar con: python manage.py shell < test_logging.py
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import logging
from core.error_codes import (
    log_operation, 
    log_performance_warning,
    log_security_event,
    TaskErrorCodes, 
    ProjectErrorCodes, 
    UserErrorCodes,
    FileErrorCodes,
    AuthErrorCodes,
    OrgErrorCodes,
    PlanErrorCodes,
    SystemErrorCodes,
    get_error_category
)

# Configurar logger
logger = logging.getLogger('test_logging')

def test_logging_system():
    """Prueba el sistema completo de logging estructurado."""
    
    print("🧪 TESTING STRUCTURED LOGGING SYSTEM")
    print("="*60)
    
    # 1. Test logging básico
    print("\n1. Testing basic operation logging...")
    log_operation(
        'TEST_BASIC_OPERATION',
        'test@example.com',
        logger,
        level='INFO',
        test_param='test_value',
        numeric_param=123
    )
    
    # 2. Test logging con código de error
    print("\n2. Testing error code logging...")
    log_operation(
        'TEST_ERROR_OPERATION',
        'test@example.com',
        logger,
        level='ERROR',
        error_code=TaskErrorCodes.TASK_CREATE_MISSING_TITLE,
        task_id=999,
        reason='Missing title in form'
    )
    
    # 3. Test diferentes tipos de errores
    print("\n3. Testing different error types...")
    
    # Task errors - nuevos códigos
    log_operation(
        'TASK_OPERATION_ERROR',
        'user@example.com',
        logger,
        level='WARNING',
        error_code=TaskErrorCodes.TASK_UPDATE_STATUS_TRANSITION_INVALID,
        task_id=123,
        current_status='IN_PROGRESS',
        attempted_status='COMPLETED',
        reason='Missing required fields'
    )
    
    # Project errors - códigos expandidos
    log_operation(
        'PROJECT_PHASE_ERROR',
        'admin@example.com',
        logger,
        level='ERROR',
        error_code=ProjectErrorCodes.PHASE_CREATE_DUPLICATE_NAME,
        project_id=456,
        phase_name='Development',
        org_id=1
    )
    
    # User errors - nuevos códigos
    log_operation(
        'USER_AUTH_ERROR',
        'user@example.com',
        logger,
        level='WARNING',
        error_code=UserErrorCodes.USER_LOGIN_TOO_MANY_ATTEMPTS,
        ip_address='192.168.1.100',
        attempts_count=6
    )
    
    # File errors - códigos expandidos
    log_operation(
        'FILE_PROCESSING_ERROR',
        'user@example.com',
        logger,
        level='ERROR',
        error_code=FileErrorCodes.FILE_PROCESSING_CONVERSION_ERROR,
        filename='document.docx',
        target_format='pdf',
        file_size_mb=25
    )
    
    # Organization errors - nuevos
    log_operation(
        'ORG_MEMBER_ERROR',
        'admin@example.com',
        logger,
        level='WARNING',
        error_code=OrgErrorCodes.ORG_MEMBER_ADD_PLAN_LIMIT,
        org_id=1,
        current_members=10,
        plan_limit=10,
        attempted_email='new_user@example.com'
    )
    
    # Plan errors - nuevos
    log_operation(
        'PLAN_BILLING_ERROR',
        'billing@example.com',
        logger,
        level='ERROR',
        error_code=PlanErrorCodes.PLAN_BILLING_PAYMENT_FAILED,
        org_id=1,
        amount=99.99,
        currency='USD',
        payment_method='card_****1234'
    )
    
    # Auth errors - nuevos
    log_operation(
        'AUTH_2FA_ERROR',
        'user@example.com',
        logger,
        level='WARNING',
        error_code=AuthErrorCodes.AUTH_2FA_INVALID_CODE,
        ip_address='192.168.1.100',
        device='iPhone 13',
        attempts_remaining=2
    )
    
    # System errors - expandidos
    log_operation(
        'SYSTEM_SECURITY_ERROR',
        'system',
        logger,
        level='ERROR',
        error_code=SystemErrorCodes.SYSTEM_SECURITY_BRUTE_FORCE_ATTACK,
        ip_address='1.2.3.4',
        failed_attempts=50,
        time_window='5 minutes'
    )
    
    # 4. Test performance logging
    print("\n4. Testing performance logging...")
    from core.error_codes import log_performance_warning
    
    log_performance_warning(
        'SLOW_QUERY_TEST',
        'user@example.com',
        logger,
        duration_ms=3500,
        threshold_ms=2000,
        query_type='SELECT',
        table='tasks',
        record_count=1500
    )
    
    # 5. Test security logging
    print("\n5. Testing security logging...")
    from core.error_codes import log_security_event
    
    log_security_event(
        'SUSPICIOUS_LOGIN_ATTEMPT',
        'anonymous',
        logger,
        ip_address='192.168.1.100',
        user_agent='Suspicious Bot',
        failed_attempts=5
    )
    
    print("\n✅ All logging tests completed!")
    print("Check the logs in arc_manager/logs/ to see the structured output.")
    print("\n📊 Expected log patterns:")
    print("- INFO logs: OP [OPERATION_NAME] User: email ...")
    print("- ERROR logs: OP [OPERATION_NAME] User: email ... ERROR_CODE: T001")
    print("- Performance: OP [OPERATION_NAME_SLOW] User: email ... ERROR_CODE: PERF_SLOW_QUERY")
    print("- Security: OP [SECURITY_EVENT] User: email ...")


def test_error_code_mapping():
    """Prueba el mapeo de códigos de error."""
    print("\n🗺️  TESTING ERROR CODE MAPPING")
    print("="*40)
    
    # Test códigos de todas las categorías
    test_codes = [
        # Tasks
        TaskErrorCodes.TASK_CREATE_MISSING_TITLE,
        TaskErrorCodes.TASK_BULK_UPDATE_PARTIAL_FAILURE,
        TaskErrorCodes.TASK_TIME_LOG_INVALID_DURATION,
        
        # Projects  
        ProjectErrorCodes.PROJECT_CREATE_NAME_DUPLICATE,
        ProjectErrorCodes.PHASE_CREATE_DUPLICATE_NAME,
        ProjectErrorCodes.PROJECT_TEAM_ADD_MEMBER_ERROR,
        
        # Users
        UserErrorCodes.USER_CREATE_EMAIL_DUPLICATE,
        UserErrorCodes.USER_PASSWORD_CHANGE_WEAK_PASSWORD,
        UserErrorCodes.USER_ROLE_UPDATE_PERMISSION_DENIED,
        
        # Organizations
        OrgErrorCodes.ORG_CREATE_NAME_DUPLICATE,
        OrgErrorCodes.ORG_MEMBER_ADD_PLAN_LIMIT,
        OrgErrorCodes.ORG_CONFIG_DOMAIN_VERIFICATION_FAILED,
        
        # Files
        FileErrorCodes.FILE_UPLOAD_TOO_LARGE,
        FileErrorCodes.FILE_PROCESSING_CONVERSION_ERROR,
        FileErrorCodes.FILE_SYNC_CONFLICT,
        
        # Authentication
        AuthErrorCodes.AUTH_LOGIN_INVALID_CREDENTIALS,
        AuthErrorCodes.AUTH_2FA_INVALID_CODE,
        AuthErrorCodes.AUTH_OAUTH_PROVIDER_ERROR,
        
        # Plans
        PlanErrorCodes.PLAN_UPGRADE_PAYMENT_ERROR,
        PlanErrorCodes.PLAN_BILLING_PAYMENT_FAILED,
        PlanErrorCodes.PLAN_LIMIT_PROJECTS_EXCEEDED,
        
        # System
        SystemErrorCodes.SYSTEM_DB_CONNECTION_ERROR,
        SystemErrorCodes.SYSTEM_SECURITY_BRUTE_FORCE_ATTACK,
        SystemErrorCodes.SYSTEM_INFRA_DISK_SPACE_LOW,
    ]
    
    for code in test_codes:
        category = get_error_category(code)
        print(f"Code: {code:>6} -> Category: {category}")
    
    # Test estadísticas
    total_codes = len([getattr(cls, attr) for cls in [
        TaskErrorCodes, ProjectErrorCodes, UserErrorCodes, OrgErrorCodes,
        FileErrorCodes, AuthErrorCodes, PlanErrorCodes, SystemErrorCodes
    ] for attr in dir(cls) if not attr.startswith('_') and isinstance(getattr(cls, attr), str)])
    
    print(f"\n📊 Total códigos de error definidos: {total_codes}")
    
    # Contar por categoría
    from collections import Counter
    categories = [get_error_category(getattr(cls, attr)) for cls in [
        TaskErrorCodes, ProjectErrorCodes, UserErrorCodes, OrgErrorCodes,
        FileErrorCodes, AuthErrorCodes, PlanErrorCodes, SystemErrorCodes
    ] for attr in dir(cls) if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]
    
    category_counts = Counter(categories)
    print("\n📊 Códigos por categoría:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} códigos")


def simulate_500_error():
    """Simula un error 500 para probar el middleware."""
    print("\n💥 SIMULATING 500 ERROR")
    print("="*30)
    print("This will generate a test exception to verify middleware logging...")
    
    try:
        # Simular diferentes tipos de errores
        raise ValueError("This is a test exception to verify 500 error logging")
    except Exception as e:
        log_operation(
            'SIMULATED_500_ERROR',
            'test@example.com',
            logger,
            level='ERROR',
            error_code=SystemErrorCodes.SYSTEM_MIDDLEWARE_UNEXPECTED_ERROR,
            exception_type=type(e).__name__,
            exception_message=str(e),
            test_context='middleware_testing'
        )
        print(f"✅ Simulated error logged: {type(e).__name__}: {str(e)}")


if __name__ == '__main__':
    test_logging_system()
    test_error_code_mapping()
    simulate_500_error()
    
    print(f"\n🎯 LOGGING SYSTEM READY!")
    print(f"Next steps:")
    print(f"1. Check logs in: arc_manager/logs/errors.log")
    print(f"2. Test a real 500 error by accessing: /projects/tasks/40/edit/")
    print(f"3. Monitor logs with: tail -f arc_manager/logs/errors.log | grep ERROR_CODE")
    print(f"4. In production (Railway), these logs will be visible in the dashboard")
