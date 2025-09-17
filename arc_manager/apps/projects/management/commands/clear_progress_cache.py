"""
Comando para limpiar el cache de progreso de proyectos.
Útil para mantenimiento o cuando se detecten inconsistencias.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.orgs.models import Organization


class Command(BaseCommand):
    help = 'Limpia el cache de progreso de proyectos para todas las organizaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=int,
            help='ID de la organización específica (opcional)',
        )

    def handle(self, *args, **options):
        if options['org_id']:
            # Limpiar cache de una organización específica
            org_id = options['org_id']
            cache_keys = [
                f"dashboard_projects_progress:{org_id}",
                f"dashboard_stats:{org_id}",
                f"project_list_stats:{org_id}",
            ]
            
            # También limpiar cache específico de cada proyecto de la organización
            from apps.projects.models import Project
            project_ids = Project.objects.filter(
                organization_id=org_id
            ).values_list('id', flat=True)
            
            for project_id in project_ids:
                cache_keys.append(f"project_progress:{project_id}")
            
            cache.delete_many(cache_keys)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cache de progreso limpiado para organización {org_id} '
                    f'({len(project_ids)} proyectos)'
                )
            )
        else:
            # Limpiar cache de todas las organizaciones
            organizations = Organization.objects.all()
            total_cleaned = 0
            
            for org in organizations:
                cache_keys = [
                    f"dashboard_projects_progress:{org.id}",
                    f"dashboard_stats:{org.id}",
                    f"project_list_stats:{org.id}",
                ]
                
                # También limpiar cache específico de cada proyecto
                from apps.projects.models import Project
                project_ids = Project.objects.filter(
                    organization=org
                ).values_list('id', flat=True)
                
                for project_id in project_ids:
                    cache_keys.append(f"project_progress:{project_id}")
                
                cache.delete_many(cache_keys)
                total_cleaned += len(cache_keys)
                
                self.stdout.write(
                    f'Org {org.id}: {len(project_ids)} proyectos limpiados'
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cache de progreso limpiado para {organizations.count()} organizaciones '
                    f'({total_cleaned} entradas totales)'
                )
            )
