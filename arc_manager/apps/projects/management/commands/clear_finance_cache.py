"""
Comando de gestión para limpiar caché financiero.
Útil para mantenimiento y debugging.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.projects.finance_cache import invalidate_finance_cache, safe_delete_pattern
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Limpia el caché financiero de Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization-id',
            type=int,
            help='ID de la organización específica (opcional)',
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='ID del proyecto específico (opcional)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpiar todo el caché financiero',
        )

    def handle(self, *args, **options):
        organization_id = options.get('organization_id')
        project_id = options.get('project_id')
        clear_all = options.get('all', False)

        if clear_all:
            # Limpiar todo el caché financiero
            patterns_to_clear = [
                'org_finance_stats:*',
                'project_finance_stats:*',
                'project_total_paid:*',
                'projects_finance_list:*',
                'payment_aggregates:*',
            ]
            
            for pattern in patterns_to_clear:
                if safe_delete_pattern(pattern):
                    self.stdout.write(
                        self.style.SUCCESS(f'Cleared cache pattern: {pattern}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Could not clear pattern (backend may not support it): {pattern}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS('All finance cache cleared successfully')
            )
        
        elif organization_id or project_id:
            # Limpiar caché específico
            invalidate_finance_cache(
                organization_id=organization_id,
                project_id=project_id
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Finance cache cleared for org_id={organization_id}, project_id={project_id}'
                )
            )
        
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify --organization-id, --project-id, or --all'
                )
            )
