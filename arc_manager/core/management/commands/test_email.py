"""
Comando para probar el envío de emails con Resend
Uso: python manage.py test_email tu@email.com
"""
from django.core.management.base import BaseCommand
from core.email_utils import send_resend_email, validate_resend_config
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Prueba el envío de emails con Resend'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email de destino para la prueba'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('TEST DE CONFIGURACION DE EMAILS - RESEND'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        # Validar configuración
        self.stdout.write('\n1. Validando configuracion...')
        is_valid, message = validate_resend_config()
        
        if not is_valid:
            self.stdout.write(self.style.ERROR(f'   ERROR: {message}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'   OK: {message}'))
        
        # Intentar enviar email de prueba
        self.stdout.write(f'\n2. Enviando email de prueba a: {test_email}')
        
        subject = 'Test de Email - ArqGest'
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2c3e50;">Test de Email - ArqGest</h2>
            <p>Si recibes este email, la configuracion de Resend esta funcionando correctamente.</p>
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Estado:</strong> Configuracion exitosa</p>
                <p><strong>Servicio:</strong> Resend API</p>
                <p><strong>Dominio:</strong> arqgest.com</p>
            </div>
            <p style="color: #666; font-size: 12px;">
                Este es un email de prueba enviado desde Railway usando Resend.
            </p>
        </body>
        </html>
        """
        
        text_content = """
        Test de Email - ArqGest
        
        Si recibes este email, la configuracion de Resend esta funcionando correctamente.
        
        Estado: Configuracion exitosa
        Servicio: Resend API
        Dominio: arqgest.com
        
        Este es un email de prueba enviado desde Railway usando Resend.
        """
        
        result = send_resend_email(test_email, subject, html_content, text_content)
        
        if result:
            self.stdout.write(self.style.SUCCESS('\n   EMAIL ENVIADO EXITOSAMENTE'))
            if isinstance(result, dict) and 'id' in result:
                self.stdout.write(self.style.SUCCESS(f'   ID de Email: {result["id"]}'))
            self.stdout.write('\n3. Verifica tu bandeja de entrada')
            self.stdout.write('   (Revisa tambien SPAM por si acaso)\n')
        else:
            self.stdout.write(self.style.ERROR('\n   ERROR: No se pudo enviar el email'))
            self.stdout.write('   Revisa los logs para mas detalles\n')
        
        self.stdout.write(self.style.WARNING('=' * 60))

