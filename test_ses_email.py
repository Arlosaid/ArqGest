#!/usr/bin/env python
"""
Script para probar la configuración de AWS SES
Ejecutar con: python test_ses_email.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arc_manager.core.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_ses_configuration():
    """Prueba la configuración de AWS SES"""
    
    print("🔍 Verificando configuración de AWS SES...")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    if settings.DEBUG:
        print("⚠️  Ejecutándose en modo DEBUG - emails irán a consola")
        print("Para probar en producción, configura DEBUG=False")
        return
    
    # Verificar variables de entorno
    required_vars = ['AWS_SES_USER', 'AWS_SES_PASS', 'AWS_SES_HOST', 'DEFAULT_FROM_EMAIL']
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mostrar solo los primeros y últimos caracteres por seguridad
            if 'PASS' in var or 'USER' in var:
                masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ Variables faltantes: {', '.join(missing_vars)}")
        print("Configura estas variables en Railway antes de continuar")
        return
    
    # Configuración de email
    print(f"\n📧 Configuración de email:")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   TLS: {settings.EMAIL_USE_TLS}")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    
    # Solicitar email de prueba
    test_email = input("\n📨 Ingresa tu email para recibir la prueba (o presiona Enter para cancelar): ").strip()
    
    if not test_email:
        print("❌ Prueba cancelada")
        return
    
    try:
        print(f"\n🚀 Enviando email de prueba a {test_email}...")
        
        send_mail(
            subject='Prueba de AWS SES - ArcManager',
            message='''
¡Hola!

Este es un email de prueba para verificar que la configuración de AWS SES está funcionando correctamente.

Si recibes este email, significa que:
✅ AWS SES está configurado correctamente
✅ Las credenciales son válidas
✅ El email de remitente está verificado
✅ La aplicación puede enviar emails

¡Excelente trabajo!

---
ArcManager - Sistema de Gestión de Proyectos
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        print("✅ ¡Email enviado exitosamente!")
        print(f"📬 Revisa tu bandeja de entrada en {test_email}")
        print("💡 Si no lo ves, revisa la carpeta de spam")
        
    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verifica que el email de remitente esté verificado en AWS SES")
        print("2. Confirma que las credenciales SMTP sean correctas")
        print("3. Asegúrate de que la región de AWS SES sea correcta")
        print("4. Verifica que no estés en modo sandbox de AWS SES")

if __name__ == '__main__':
    test_ses_configuration()
