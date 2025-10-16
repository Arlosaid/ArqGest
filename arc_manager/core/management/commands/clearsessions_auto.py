"""
Comando personalizado para limpiar sesiones expiradas de la base de datos.
Debe ejecutarse periódicamente (ej: diariamente con cron o celery beat)

Uso:
    python manage.py clearsessions_auto
"""

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
import logging

logger = logging.getLogger('apps.accounts')


class Command(BaseCommand):
    help = 'Elimina sesiones expiradas de la base de datos para mantener el rendimiento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué sesiones se eliminarían sin eliminarlas realmente',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        now = timezone.now()
        
        # Obtener sesiones expiradas
        expired_sessions = Session.objects.filter(expire_date__lt=now)
        count = expired_sessions.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Se eliminarían {count} sesiones expiradas'
                )
            )
            logger.info(f"DRY RUN: {count} sesiones expiradas detectadas")
        else:
            # Eliminar sesiones expiradas
            deleted_count, _ = expired_sessions.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Limpieza completada: {deleted_count} sesiones expiradas eliminadas'
                )
            )
            logger.info(f"Sesiones limpias: {deleted_count} sesiones expiradas eliminadas")
        
        # Mostrar estadísticas de sesiones activas
        active_sessions = Session.objects.filter(expire_date__gte=now).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Sesiones activas actuales: {active_sessions}'
            )
        )

