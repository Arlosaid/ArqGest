from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
import os
import socket
import time
import smtplib


class Command(BaseCommand):
    help = 'Diagnóstico completo de la configuración de email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            type=str,
            help='Email para enviar prueba (opcional)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout en segundos para las pruebas (default: 30)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🔍 DIAGNÓSTICO COMPLETO DE EMAIL'))
        self.stdout.write('=' * 60)
        
        # 1. Verificar configuración de Django
        self.check_django_config()
        
        # 2. Verificar variables de entorno
        self.check_environment_variables()
        
        # 3. Test de conectividad SMTP
        self.test_smtp_connection(options['timeout'])
        
        # 4. Test de envío si se proporciona email
        test_email = options.get('test_email')
        if test_email:
            self.test_email_sending(test_email, options['timeout'])
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Diagnóstico completado'))

    def check_django_config(self):
        self.stdout.write('\n📋 1. Verificando configuración de Django...')
        
        backend = getattr(settings, 'EMAIL_BACKEND', 'No configurado')
        self.stdout.write(f'   Backend: {backend}')
        
        if 'smtp' in backend.lower():
            self.stdout.write('   ✅ Usando backend SMTP')
            
            host = getattr(settings, 'EMAIL_HOST', 'No configurado')
            port = getattr(settings, 'EMAIL_PORT', 'No configurado')
            use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
            use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
            timeout = getattr(settings, 'EMAIL_TIMEOUT', 'No configurado')
            
            self.stdout.write(f'   Host: {host}')
            self.stdout.write(f'   Puerto: {port}')
            self.stdout.write(f'   TLS: {use_tls}')
            self.stdout.write(f'   SSL: {use_ssl}')
            self.stdout.write(f'   Timeout: {timeout}')
            
            # Validaciones
            if host == 'No configurado':
                self.stdout.write(self.style.ERROR('   ❌ EMAIL_HOST no está configurado'))
            if port == 'No configurado':
                self.stdout.write(self.style.WARNING('   ⚠️ EMAIL_PORT no está configurado'))
            if timeout == 'No configurado':
                self.stdout.write(self.style.WARNING('   ⚠️ EMAIL_TIMEOUT no está configurado'))
                
        elif 'console' in backend.lower():
            self.stdout.write('   ℹ️ Usando backend de consola (desarrollo)')
        else:
            self.stdout.write(f'   ℹ️ Usando backend: {backend}')
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')
        self.stdout.write(f'   From Email: {from_email}')

    def check_environment_variables(self):
        self.stdout.write('\n📋 2. Verificando variables de entorno...')
        
        required_vars = [
            'EMAIL_HOST',
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD',
            'DEFAULT_FROM_EMAIL'
        ]
        
        for var in required_vars:
            value = os.environ.get(var)
            if value:
                if 'PASSWORD' in var:
                    self.stdout.write(f'   ✅ {var}: *** (configurado)')
                else:
                    self.stdout.write(f'   ✅ {var}: {value}')
            else:
                self.stdout.write(f'   ❌ {var}: No configurado')

    def test_smtp_connection(self, timeout):
        self.stdout.write(f'\n🔌 3. Probando conectividad SMTP (timeout: {timeout}s)...')
        
        host = getattr(settings, 'EMAIL_HOST', None)
        port = getattr(settings, 'EMAIL_PORT', 587)
        use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        user = os.environ.get('EMAIL_HOST_USER')
        password = os.environ.get('EMAIL_HOST_PASSWORD')
        
        if not host:
            self.stdout.write(self.style.ERROR('   ❌ EMAIL_HOST no configurado'))
            return
        
        try:
            start_time = time.time()
            
            # Test de conexión básica
            self.stdout.write(f'   🔗 Conectando a {host}:{port}...')
            
            # Configurar timeout de socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)
            
            try:
                # Crear conexión SMTP
                if use_tls:
                    smtp = smtplib.SMTP(host, port, timeout=timeout)
                    smtp.starttls()
                else:
                    smtp = smtplib.SMTP(host, port, timeout=timeout)
                
                connect_time = time.time() - start_time
                self.stdout.write(f'   ✅ Conexión establecida en {connect_time:.2f}s')
                
                # Test de autenticación
                if user and password:
                    self.stdout.write('   🔐 Probando autenticación...')
                    auth_start = time.time()
                    smtp.login(user, password)
                    auth_time = time.time() - auth_start
                    self.stdout.write(f'   ✅ Autenticación exitosa en {auth_time:.2f}s')
                else:
                    self.stdout.write('   ⚠️ No hay credenciales para probar autenticación')
                
                smtp.quit()
                total_time = time.time() - start_time
                self.stdout.write(f'   ✅ Conexión SMTP OK (tiempo total: {total_time:.2f}s)')
                
            except socket.timeout:
                self.stdout.write(self.style.ERROR(f'   ❌ Timeout de conexión ({timeout}s)'))
            except smtplib.SMTPAuthenticationError:
                self.stdout.write(self.style.ERROR('   ❌ Error de autenticación'))
            except smtplib.SMTPException as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error SMTP: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error de conexión: {str(e)}'))
            finally:
                socket.setdefaulttimeout(original_timeout)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error general: {str(e)}'))

    def test_email_sending(self, test_email, timeout):
        self.stdout.write(f'\n📧 4. Enviando email de prueba a {test_email}...')
        
        try:
            # Configurar timeout
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)
            
            start_time = time.time()
            
            send_mail(
                subject='🧪 Prueba de Email - Diagnóstico ARC Manager',
                message=f'''¡Hola!

Este email fue enviado desde el comando de diagnóstico de ARC Manager.

✅ La configuración de email está funcionando correctamente.

Detalles del envío:
- Backend: {getattr(settings, 'EMAIL_BACKEND', 'No configurado')}
- Host: {getattr(settings, 'EMAIL_HOST', 'No configurado')}
- Puerto: {getattr(settings, 'EMAIL_PORT', 'No configurado')}
- TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}
- Timeout configurado: {timeout}s
- Email origen: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}

--
ARC Manager - Diagnóstico de Email''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(f'   ✅ Email enviado exitosamente en {elapsed_time:.2f}s'))
            self.stdout.write('   💡 Revisa tu bandeja de entrada (puede tardar unos minutos)')
            
        except socket.timeout:
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.ERROR(f'   ❌ Timeout enviando email ({elapsed_time:.0f}s)'))
            self.stdout.write('   💡 Sugerencias:')
            self.stdout.write('      - Aumenta EMAIL_TIMEOUT en variables de entorno')
            self.stdout.write('      - Verifica la configuración de SendGrid')
            self.stdout.write('      - Revisa la conectividad de red')
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.ERROR(f'   ❌ Error enviando email ({elapsed_time:.2f}s): {str(e)}'))
            
            # Sugerencias basadas en el error
            error_str = str(e).lower()
            self.stdout.write('   💡 Sugerencias:')
            if 'authentication' in error_str:
                self.stdout.write('      - Verifica EMAIL_HOST_USER y EMAIL_HOST_PASSWORD')
                self.stdout.write('      - Para SendGrid, usa "apikey" como usuario')
            elif 'connection' in error_str:
                self.stdout.write('      - Verifica EMAIL_HOST y EMAIL_PORT')
                self.stdout.write('      - Revisa la configuración de TLS/SSL')
            elif 'timeout' in error_str:
                self.stdout.write('      - Aumenta el timeout en variables de entorno')
            else:
                self.stdout.write(f'      - Error específico: {str(e)}')
                
        finally:
            socket.setdefaulttimeout(original_timeout)
