"""
Comando para probar la configuración de email y diagnosticar problemas.
"""
import logging
import time
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.users.utils import send_new_user_email, generate_random_password

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prueba la configuración de email y diagnostica problemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email de destino para la prueba (opcional, usa el primer admin si no se especifica)'
        )
        parser.add_argument(
            '--test-credentials',
            action='store_true',
            help='Prueba específicamente el envío de credenciales'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada de configuración'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando diagnóstico de email...'))
        
        # 1. Verificar configuración
        self.check_email_configuration(verbose=options.get('verbose', False))
        
        # 2. Determinar email de destino
        test_email = self.get_test_email(options.get('email'))
        if not test_email:
            return
            
        # 3. Prueba básica de email
        self.test_basic_email(test_email)
        
        # 4. Prueba de credenciales si se solicita
        if options.get('test_credentials'):
            self.test_credentials_email(test_email)
            
        self.stdout.write(self.style.SUCCESS('✅ Diagnóstico completado'))

    def check_email_configuration(self, verbose=False):
        """Verificar la configuración de email"""
        self.stdout.write(self.style.WARNING('📧 Verificando configuración de email...'))
        
        # Configuraciones críticas
        configs = {
            'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'No configurado'),
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'No configurado'),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'No configurado'),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'No configurado'),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'No configurado'),
            'EMAIL_HOST_PASSWORD': '***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'No configurado',
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado'),
        }
        
        # Mostrar configuraciones
        for key, value in configs.items():
            if value == 'No configurado':
                self.stdout.write(f"❌ {key}: {value}")
            else:
                self.stdout.write(f"✅ {key}: {value}")
        
        if verbose:
            # Información adicional
            self.stdout.write(f"\n🔍 Información adicional:")
            self.stdout.write(f"DEBUG: {getattr(settings, 'DEBUG', 'No configurado')}")
            self.stdout.write(f"SITE_NAME: {getattr(settings, 'SITE_NAME', 'No configurado')}")
            self.stdout.write(f"SITE_URL: {getattr(settings, 'SITE_URL', 'No configurado')}")

    def get_test_email(self, provided_email):
        """Obtener email para pruebas"""
        if provided_email:
            self.stdout.write(f"📧 Usando email proporcionado: {provided_email}")
            return provided_email
        
        # Buscar primer superuser
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user and admin_user.email:
                self.stdout.write(f"📧 Usando email del primer admin: {admin_user.email}")
                return admin_user.email
            else:
                self.stdout.write(self.style.ERROR('❌ No se encontró un admin con email. Proporciona --email'))
                return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error buscando admin: {str(e)}'))
            return None

    def test_basic_email(self, test_email):
        """Prueba básica de envío de email"""
        self.stdout.write(self.style.WARNING('📨 Probando envío básico de email...'))
        
        try:
            start_time = time.time()
            
            # Crear conexión con timeout
            connection = get_connection()
            if hasattr(connection, 'timeout'):
                connection.timeout = 30
            
            subject = '🧪 Prueba de Email - ARC Manager'
            message = f'''
            ¡Hola!
            
            Este es un email de prueba del sistema ARC Manager.
            
            Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}
            
            Si recibes este email, la configuración está funcionando correctamente.
            
            Saludos,
            El equipo de ARC Manager
            '''
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
            
            self.stdout.write(f"📤 Enviando desde: {from_email}")
            self.stdout.write(f"📥 Enviando hacia: {test_email}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[test_email],
                connection=connection,
                fail_silently=False
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.stdout.write(self.style.SUCCESS(f'✅ Email básico enviado exitosamente en {duration:.2f} segundos'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error enviando email básico: {str(e)}'))
            self.stdout.write(self.style.ERROR(f'❌ Tipo de error: {type(e).__name__}'))
            
            # Información adicional para debugging
            import traceback
            self.stdout.write(self.style.ERROR(f'❌ Traceback: {traceback.format_exc()}'))

    def test_credentials_email(self, test_email):
        """Prueba específica del envío de credenciales"""
        self.stdout.write(self.style.WARNING('🔑 Probando envío de credenciales...'))
        
        try:
            # Crear usuario temporal para la prueba
            test_user = User(
                email=test_email,
                first_name='Usuario',
                last_name='Prueba',
                username=f'test_{int(time.time())}'
            )
            # No guardar en BD, solo usar para la prueba
            
            test_password = generate_random_password()
            
            self.stdout.write(f"👤 Usuario de prueba: {test_user.email}")
            self.stdout.write(f"🔒 Contraseña generada: {test_password}")
            
            # Usar la función real de envío de credenciales
            result = send_new_user_email(test_user, test_password)
            
            if result:
                self.stdout.write(self.style.SUCCESS('✅ Email de credenciales enviado exitosamente'))
            else:
                self.stdout.write(self.style.ERROR('❌ Error enviando email de credenciales'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en prueba de credenciales: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(f'❌ Traceback: {traceback.format_exc()}'))