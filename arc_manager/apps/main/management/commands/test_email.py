from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Prueba la configuración de AWS SES'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email de destino para la prueba',
            required=True
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write("🔍 Verificando configuración de AWS SES...")
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        
        if settings.DEBUG:
            self.stdout.write(
                self.style.WARNING("⚠️  Ejecutándose en modo DEBUG - emails irán a consola")
            )
            self.stdout.write("Para probar en producción, configura DEBUG=False")
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
                    self.stdout.write(f"✅ {var}: {masked_value}")
                else:
                    self.stdout.write(f"✅ {var}: {value}")
        
        if missing_vars:
            self.stdout.write(
                self.style.ERROR(f"❌ Variables faltantes: {', '.join(missing_vars)}")
            )
            self.stdout.write("Configura estas variables en Railway antes de continuar")
            return
        
        # Configuración de email
        self.stdout.write(f"\n📧 Configuración de email:")
        self.stdout.write(f"   Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"   Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"   TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"   From: {settings.DEFAULT_FROM_EMAIL}")
        
        try:
            self.stdout.write(f"\n🚀 Enviando email de prueba a {test_email}...")
            
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
            
            self.stdout.write(
                self.style.SUCCESS("✅ ¡Email enviado exitosamente!")
            )
            self.stdout.write(f"📬 Revisa tu bandeja de entrada en {test_email}")
            self.stdout.write("💡 Si no lo ves, revisa la carpeta de spam")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error al enviar email: {str(e)}")
            )
            self.stdout.write("\n🔧 Posibles soluciones:")
            self.stdout.write("1. Verifica que el email de remitente esté verificado en AWS SES")
            self.stdout.write("2. Confirma que las credenciales SMTP sean correctas")
            self.stdout.write("3. Asegúrate de que la región de AWS SES sea correcta")
            self.stdout.write("4. Verifica que no estés en modo sandbox de AWS SES")