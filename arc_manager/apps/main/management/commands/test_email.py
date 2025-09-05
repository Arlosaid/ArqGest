from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Prueba la configuración de correos electrónicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='Dirección de correo de destino para la prueba',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔧 Probando configuración de correos...")
        
        # Mostrar configuración actual
        self.show_email_config()
        
        # Probar envío si se proporciona destinatario
        if options['to']:
            self.test_send_email(options['to'])
        else:
            self.stdout.write(
                self.style.WARNING("💡 Usa --to email@ejemplo.com para probar el envío")
            )

    def show_email_config(self):
        """Mostrar la configuración actual de correo"""
        self.stdout.write("\n📧 Configuración de correo:")
        
        backend = getattr(settings, 'EMAIL_BACKEND', 'No configurado')
        self.stdout.write(f"   Backend: {backend}")
        
        if 'smtp' in backend.lower():
            self.stdout.write("   Tipo: SMTP")
            self.stdout.write(f"   Host: {os.environ.get('EMAIL_HOST', 'No configurado')}")
            self.stdout.write(f"   Puerto: {os.environ.get('EMAIL_PORT', 'No configurado')}")
            self.stdout.write(f"   TLS: {os.environ.get('EMAIL_USE_TLS', 'No configurado')}")
            self.stdout.write(f"   Usuario: {os.environ.get('EMAIL_HOST_USER', 'No configurado')}")
            password_set = "✅ Configurado" if os.environ.get('EMAIL_HOST_PASSWORD') else "❌ No configurado"
            self.stdout.write(f"   Password: {password_set}")
        elif 'ses' in backend.lower():
            self.stdout.write("   Tipo: AWS SES")
            self.stdout.write(f"   Región: {os.environ.get('AWS_SES_REGION', 'No configurado')}")
            aws_key_set = "✅ Configurado" if os.environ.get('AWS_ACCESS_KEY_ID') else "❌ No configurado"
            self.stdout.write(f"   AWS Key: {aws_key_set}")
        elif 'console' in backend.lower():
            self.stdout.write("   Tipo: Console (desarrollo)")
        else:
            self.stdout.write(f"   Tipo: {backend}")
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')
        self.stdout.write(f"   From Email: {from_email}")

    def test_send_email(self, to_email):
        """Probar envío de correo"""
        self.stdout.write(f"\n📤 Enviando correo de prueba a {to_email}...")
        
        try:
            send_mail(
                subject='✅ Prueba de correo - ARC Manager',
                message='Este es un correo de prueba desde ARC Manager.\n\n'
                       'Si recibes este mensaje, la configuración de correos está funcionando correctamente.\n\n'
                       '¡Saludos!\nEquipo ARC Manager',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS("✅ Correo enviado exitosamente!")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error al enviar correo: {str(e)}")
            )
            
            # Sugerencias de solución
            self.stdout.write("\n💡 Posibles soluciones:")
            self.stdout.write("   1. Verifica las credenciales SMTP")
            self.stdout.write("   2. Confirma que EMAIL_HOST_USER y EMAIL_HOST_PASSWORD estén configurados")
            self.stdout.write("   3. Revisa que el host SMTP sea correcto")
            self.stdout.write("   4. Verifica la configuración de TLS/SSL")
