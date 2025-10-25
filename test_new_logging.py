"""
Script de verificación para el nuevo sistema de logging.
Ejecutar con: python test_new_logging.py
"""
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'arc_manager'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.setdefault('DEBUG', 'True')

import django
django.setup()

from core.structured_logging import (
    log_error,
    log_warning,
    log_info,
    log_business_event,
    log_slow_operation,
    log_security_event
)

def test_logging():
    """Probar el sistema de logging estructurado"""
    
    print("=" * 60)
    print("VERIFICACIÓN DEL SISTEMA DE LOGGING ESTRUCTURADO")
    print("=" * 60)
    print()
    
    # Test 1: Log de error
    print("✓ Test 1: Log de error con código")
    log_error(
        event="test_error",
        error_code="TEST001",
        error_message="Este es un error de prueba",
        test_field="valor de prueba"
    )
    print("  → Debería aparecer arriba con formato estructurado")
    print()
    
    # Test 2: Log de warning
    print("✓ Test 2: Log de warning")
    log_warning(
        event="test_warning",
        message="Este es un warning de prueba",
        severity="medium"
    )
    print("  → Debería aparecer arriba con formato estructurado")
    print()
    
    # Test 3: Log de info
    print("✓ Test 3: Log de info")
    log_info(
        event="test_info",
        message="Este es un log informativo de prueba"
    )
    print("  → Debería aparecer arriba con formato estructurado")
    print()
    
    # Test 4: Evento de negocio
    print("✓ Test 4: Evento de negocio")
    log_business_event(
        event="test_entity_created",
        action="created",
        entity_type="test_entity",
        entity_id=999,
        outcome="success",
        additional_info="Creado exitosamente"
    )
    print("  → Debería aparecer arriba con formato estructurado")
    print()
    
    # Test 5: Operación lenta
    print("✓ Test 5: Operación lenta (solo si >2000ms)")
    log_slow_operation(
        operation="test_operation",
        duration_ms=3500,  # Mayor que el threshold
        threshold_ms=2000,
        test_metric=123
    )
    print("  → Debería aparecer arriba porque 3500ms > 2000ms")
    print()
    
    # Test 6: Operación rápida (no debe loguearse)
    print("✓ Test 6: Operación rápida (NO debería loguearse)")
    log_slow_operation(
        operation="fast_operation",
        duration_ms=1500,  # Menor que el threshold
        threshold_ms=2000
    )
    print("  → NO debería aparecer nada arriba (demasiado rápida)")
    print()
    
    # Test 7: Evento de seguridad
    print("✓ Test 7: Evento de seguridad")
    log_security_event(
        event="test_security_event",
        severity="high",
        ip_address="192.168.1.100",
        username="test_user"
    )
    print("  → Debería aparecer arriba con severidad 'high'")
    print()
    
    # Test 8: Verificar anonimización de email
    print("✓ Test 8: Verificar anonimización de email")
    from core.logging_filters import SensitiveDataFilter
    
    test_message = "Error al guardar usuario test@example.com con IP 192.168.1.100"
    
    # Simular filtro
    import logging
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg=test_message,
        args=(),
        exc_info=None
    )
    
    filter_instance = SensitiveDataFilter()
    filter_instance.filter(record)
    
    print(f"  Original: {test_message}")
    print(f"  Filtrado: {record.msg}")
    print("  → Email e IP deberían estar anonimizados")
    print()
    
    print("=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("Notas:")
    print("- En DEBUG=True: logs en formato texto simple")
    print("- En DEBUG=False: logs en formato JSON")
    print("- Archivos estáticos (/static/, /media/) NO se loguean")
    print("- Datos sensibles se anonimizan automáticamente")
    print()

if __name__ == "__main__":
    test_logging()
