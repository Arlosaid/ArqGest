"""
Comando para verificar la configuración de email sin enviar nada
Uso: python manage.py check_email_config
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.email_utils import validate_resend_config
import os


class Command(BaseCommand):
    help = 'Verifica la configuración de emails (Resend)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('VERIFICACION DE CONFIGURACION DE EMAILS'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        # Variables de entorno
        self.stdout.write('\n1. Variables de entorno:')
        self._check_env_var('RESEND_API_KEY', obscure=True)
        self._check_env_var('DEFAULT_FROM_EMAIL')
        self._check_env_var('SUPPORT_EMAIL')
        self._check_env_var('ADMIN_EMAIL')
        self._check_env_var('SITE_URL')
        self._check_env_var('SITE_DOMAIN')
        
        # Validar configuración de Resend
        self.stdout.write('\n2. Validacion de Resend:')
        is_valid, message = validate_resend_config()
        
        if is_valid:
            self.stdout.write(self.style.SUCCESS(f'   OK: {message}'))
        else:
            self.stdout.write(self.style.ERROR(f'   ERROR: {message}'))
        
        # Settings de Django
        self.stdout.write('\n3. Configuracion de Django:')
        self._check_setting('EMAIL_BACKEND')
        self._check_setting('DEFAULT_FROM_EMAIL')
        self._check_setting('DEBUG')
        
        # Resumen
        self.stdout.write('\n' + '=' * 70)
        if is_valid:
            self.stdout.write(self.style.SUCCESS('CONFIGURACION CORRECTA'))
            self.stdout.write('\nPuedes probar el envio con:')
            self.stdout.write(self.style.WARNING('  python manage.py test_email tu@email.com'))
        else:
            self.stdout.write(self.style.ERROR('HAY ERRORES EN LA CONFIGURACION'))
            self.stdout.write('\nRevisa la guia: CONFIGURACION_EMAILS_RESEND.md')
        self.stdout.write('=' * 70 + '\n')
    
    def _check_env_var(self, var_name, obscure=False):
        """Verifica si una variable de entorno existe"""
        value = os.environ.get(var_name)
        
        if value:
            if obscure and len(value) > 10:
                display_value = f"{value[:10]}...{value[-4:]}"
            else:
                display_value = value
            
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ {var_name}:') + f' {display_value}'
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'   ✗ {var_name}: NO CONFIGURADA')
            )
    
    def _check_setting(self, setting_name):
        """Verifica un setting de Django"""
        try:
            value = getattr(settings, setting_name)
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ {setting_name}:') + f' {value}'
            )
        except AttributeError:
            self.stdout.write(
                self.style.ERROR(f'   ✗ {setting_name}: NO CONFIGURADO')
            )

