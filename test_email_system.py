#!/usr/bin/env python
"""
🧪 Script de testing para el sistema de emails optimizado
Ejecutar desde el directorio raíz del proyecto
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'arc_manager'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.utils import (
    test_email_configuration,
    send_user_credentials_email,
    send_welcome_email
)

def test_email_system():
    """
    🧪 Test completo del sistema de emails
    """
    print("🚀 Iniciando test del sistema de emails optimizado...")
    print("=" * 60)
    
    # Test 1: Configuración
    print("\n📋 Test 1: Verificando configuración...")
    config_ok = test_email_configuration()
    
    if not config_ok:
        print("❌ La configuración tiene problemas. Revisa los logs.")
        return False
    
    print("✅ Configuración correcta")
    
    # Test 2: Email de credenciales (simulado)
    print("\n📧 Test 2: Probando envío de credenciales...")
    test_email = input("Ingresa tu email para testing: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Email inválido")
        return False
    
    print(f"📤 Enviando credenciales de prueba a {test_email}...")
    success = send_user_credentials_email(
        user_email=test_email,
        password="TestPassword123!",
        username="UsuarioPrueba"
    )
    
    if success:
        print("✅ Email de credenciales programado correctamente")
        print("📡 Revisa tu bandeja de entrada en unos segundos")
    else:
        print("❌ Error programando email de credenciales")
        return False
    
    # Test 3: Email de bienvenida (opcional)
    test_welcome = input("\n¿Probar también email de bienvenida? (y/n): ").strip().lower()
    
    if test_welcome == 'y':
        print(f"🎉 Enviando bienvenida a {test_email}...")
        success_welcome = send_welcome_email(test_email, "UsuarioPrueba")
        
        if success_welcome:
            print("✅ Email de bienvenida programado correctamente")
        else:
            print("❌ Error programando email de bienvenida")
    
    print("\n" + "=" * 60)
    print("🎯 Test completado!")
    print("📊 Revisa los logs del servidor para detalles")
    print("📧 Los emails se envían en segundo plano (threading)")
    print("⏱️ Deberían llegar en 2-10 segundos")
    
    return True

if __name__ == "__main__":
    try:
        test_email_system()
    except KeyboardInterrupt:
        print("\n❌ Test interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
