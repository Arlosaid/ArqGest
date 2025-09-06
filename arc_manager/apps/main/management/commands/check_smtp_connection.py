import socket
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Checks the SMTP connection to SendGrid to diagnose network issues.'

    def handle(self, *args, **options):
        host = 'smtp.sendgrid.net'
        ports_to_check = [587, 465, 25]
        timeout_seconds = 15

        self.stdout.write(self.style.SUCCESS(f"--- Iniciando diagnóstico de conexión SMTP para {host} ---"))

        for port in ports_to_check:
            self.stdout.write(f"\nIntentando conectar al puerto {port}...")
            try:
                # Create a socket object
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Set a timeout for the connection attempt
                s.settimeout(timeout_seconds)
                # Attempt to connect
                s.connect((host, port))
                self.stdout.write(self.style.SUCCESS(f"✅ ÉXITO: La conexión al puerto {port} fue exitosa."))
                s.close()
            except socket.timeout:
                self.stderr.write(self.style.ERROR(f"❌ FALLO: Timeout después de {timeout_seconds} segundos al intentar conectar al puerto {port}."))
            except ConnectionRefusedError:
                 self.stderr.write(self.style.ERROR(f"❌ FALLO: La conexión fue rechazada en el puerto {port}."))
            except OSError as e:
                self.stderr.write(self.style.ERROR(f"❌ FALLO: Error de red inesperado en el puerto {port}: {e}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ FALLO: Ocurrió un error inesperado en el puerto {port}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n--- Diagnóstico completado ---"))
        self.stdout.write("Si todas las conexiones fallaron por timeout, es muy probable que haya un firewall en Railway bloqueando el tráfico SMTP saliente.")
        self.stdout.write("En ese caso, por favor contacta al soporte de Railway y pregunta si hay restricciones de red para los puertos 587, 465 o 25.")
