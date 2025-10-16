"""
Management command para analizar el rendimiento de queries
Uso: python manage.py analyze_performance
"""
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.conf import settings
from django.test.utils import override_settings
from apps.projects.models import Project, Task, Phase
from apps.orgs.models import Organization
import time


class Command(BaseCommand):
    help = 'Analiza el rendimiento de las queries más comunes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostrar queries SQL detalladas',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        # Activar DEBUG temporalmente para poder capturar queries
        original_debug = settings.DEBUG
        settings.DEBUG = True
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('ANÁLISIS DE RENDIMIENTO - ARC MANAGER'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Obtener una organización de prueba
        try:
            org = Organization.objects.first()
            if not org:
                self.stdout.write(self.style.ERROR('No hay organizaciones en la base de datos'))
                return
            
            self.stdout.write(f'Organización de prueba: {org.name} (ID: {org.id})\n')
            
            # Test 1: Listado de proyectos
            self._test_project_list(org, detailed)
            
            # Test 2: Listado con datos financieros
            self._test_project_list_with_payments(org, detailed)
            
            # Test 3: Cálculo de progreso
            self._test_progress_calculation(org, detailed)
            
            # Test 4: Listado de tareas
            self._test_task_list(org, detailed)
            
            # Test 5: Dashboard stats
            self._test_dashboard_stats(org, detailed)
            
            # Resumen final
            self._print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en análisis: {str(e)}'))
        finally:
            # Restaurar DEBUG original
            settings.DEBUG = original_debug
    
    def _test_project_list(self, org, detailed):
        """Test: Listado básico de proyectos"""
        self.stdout.write(self.style.WARNING('\n📊 TEST 1: Listado básico de proyectos'))
        self.stdout.write('-' * 80)
        
        reset_queries()
        start_time = time.time()
        
        # Query SIN optimización
        projects = list(Project.objects.filter(organization=org)[:10])
        
        elapsed = (time.time() - start_time) * 1000
        num_queries = len(connection.queries)
        
        self.stdout.write(f'Proyectos obtenidos: {len(projects)}')
        self.stdout.write(f'Queries ejecutadas: {num_queries}')
        self.stdout.write(f'Tiempo: {elapsed:.2f}ms')
        
        if num_queries > 15:
            self.stdout.write(self.style.ERROR('⚠️  PROBLEMA: Demasiadas queries (> 15)'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ OK: Número de queries aceptable'))
        
        if detailed:
            self._print_queries()
        
        # Query CON optimización
        self.stdout.write('\n  → Con optimización (select_related):')
        reset_queries()
        start_time = time.time()
        
        projects_opt = list(
            Project.objects.filter(organization=org)
            .select_related('client', 'owner')[:10]
        )
        
        elapsed_opt = (time.time() - start_time) * 1000
        num_queries_opt = len(connection.queries)
        
        self.stdout.write(f'  Queries: {num_queries_opt} (antes: {num_queries})')
        self.stdout.write(f'  Tiempo: {elapsed_opt:.2f}ms (antes: {elapsed:.2f}ms)')
        
        improvement = ((num_queries - num_queries_opt) / num_queries * 100) if num_queries > 0 else 0
        self.stdout.write(self.style.SUCCESS(f'  Mejora: {improvement:.1f}% menos queries'))
    
    def _test_project_list_with_payments(self, org, detailed):
        """Test: Listado de proyectos con total_paid"""
        self.stdout.write(self.style.WARNING('\n💰 TEST 2: Listado con datos financieros (total_paid)'))
        self.stdout.write('-' * 80)
        
        reset_queries()
        start_time = time.time()
        
        # Query SIN optimización (accediendo a total_paid)
        projects = Project.objects.filter(organization=org)[:10]
        totals = [p.total_paid for p in projects]
        
        elapsed = (time.time() - start_time) * 1000
        num_queries = len(connection.queries)
        
        self.stdout.write(f'Proyectos procesados: {len(totals)}')
        self.stdout.write(f'Queries ejecutadas: {num_queries}')
        self.stdout.write(f'Tiempo: {elapsed:.2f}ms')
        
        if num_queries > 20:
            self.stdout.write(self.style.ERROR('⚠️  PROBLEMA: N+1 queries detectado'))
        
        # Query CON optimización
        self.stdout.write('\n  → Con optimización (prefetch_related):')
        reset_queries()
        start_time = time.time()
        
        projects_opt = Project.objects.filter(organization=org).prefetch_related('payments')[:10]
        totals_opt = [p.total_paid for p in projects_opt]
        
        elapsed_opt = (time.time() - start_time) * 1000
        num_queries_opt = len(connection.queries)
        
        self.stdout.write(f'  Queries: {num_queries_opt} (antes: {num_queries})')
        self.stdout.write(f'  Tiempo: {elapsed_opt:.2f}ms (antes: {elapsed:.2f}ms)')
        
        if num_queries_opt < num_queries:
            improvement = ((num_queries - num_queries_opt) / num_queries * 100)
            self.stdout.write(self.style.SUCCESS(f'  Mejora: {improvement:.1f}% menos queries'))
    
    def _test_progress_calculation(self, org, detailed):
        """Test: Cálculo de progreso de proyectos"""
        self.stdout.write(self.style.WARNING('\n📈 TEST 3: Cálculo de progreso (progress_percentage)'))
        self.stdout.write('-' * 80)
        
        reset_queries()
        start_time = time.time()
        
        # Obtener progreso de todos los proyectos
        projects = Project.objects.filter(organization=org)[:10]
        progress_values = [p.progress_percentage for p in projects]
        
        elapsed = (time.time() - start_time) * 1000
        num_queries = len(connection.queries)
        
        self.stdout.write(f'Proyectos analizados: {len(progress_values)}')
        self.stdout.write(f'Queries ejecutadas: {num_queries}')
        self.stdout.write(f'Tiempo: {elapsed:.2f}ms')
        
        # El progreso debería usar caché en la segunda llamada
        self.stdout.write('\n  → Segunda llamada (debe usar caché):')
        reset_queries()
        start_time = time.time()
        
        progress_values_2 = [p.progress_percentage for p in projects]
        
        elapsed_2 = (time.time() - start_time) * 1000
        num_queries_2 = len(connection.queries)
        
        self.stdout.write(f'  Queries: {num_queries_2} (debería ser 0 si caché funciona)')
        self.stdout.write(f'  Tiempo: {elapsed_2:.2f}ms')
        
        if num_queries_2 == 0:
            self.stdout.write(self.style.SUCCESS('  ✅ Caché funcionando correctamente'))
        else:
            self.stdout.write(self.style.ERROR('  ⚠️  Caché NO está funcionando'))
    
    def _test_task_list(self, org, detailed):
        """Test: Listado de tareas"""
        self.stdout.write(self.style.WARNING('\n✅ TEST 4: Listado de tareas'))
        self.stdout.write('-' * 80)
        
        reset_queries()
        start_time = time.time()
        
        # Query SIN optimización
        tasks = list(Task.objects.filter(phase__project__organization=org)[:20])
        
        elapsed = (time.time() - start_time) * 1000
        num_queries = len(connection.queries)
        
        self.stdout.write(f'Tareas obtenidas: {len(tasks)}')
        self.stdout.write(f'Queries ejecutadas: {num_queries}')
        self.stdout.write(f'Tiempo: {elapsed:.2f}ms')
        
        # Query CON optimización
        self.stdout.write('\n  → Con optimización (select_related):')
        reset_queries()
        start_time = time.time()
        
        tasks_opt = list(
            Task.objects.filter(phase__project__organization=org)
            .select_related('phase__project', 'assigned_to')[:20]
        )
        
        elapsed_opt = (time.time() - start_time) * 1000
        num_queries_opt = len(connection.queries)
        
        self.stdout.write(f'  Queries: {num_queries_opt} (antes: {num_queries})')
        self.stdout.write(f'  Tiempo: {elapsed_opt:.2f}ms (antes: {elapsed:.2f}ms)')
        
        if num_queries_opt < num_queries:
            improvement = ((num_queries - num_queries_opt) / num_queries * 100)
            self.stdout.write(self.style.SUCCESS(f'  Mejora: {improvement:.1f}% menos queries'))
    
    def _test_dashboard_stats(self, org, detailed):
        """Test: Estadísticas del dashboard"""
        self.stdout.write(self.style.WARNING('\n📊 TEST 5: Dashboard stats'))
        self.stdout.write('-' * 80)
        
        from django.db.models import Count, Q
        
        reset_queries()
        start_time = time.time()
        
        # Simular carga del dashboard
        total_projects = Project.objects.filter(organization=org).count()
        active_projects = Project.objects.filter(organization=org, status='ACTIVE')[:6]
        total_tasks = Task.objects.filter(phase__project__organization=org).count()
        
        elapsed = (time.time() - start_time) * 1000
        num_queries = len(connection.queries)
        
        self.stdout.write(f'Estadísticas calculadas:')
        self.stdout.write(f'  - Total proyectos: {total_projects}')
        self.stdout.write(f'  - Proyectos activos: {len(list(active_projects))}')
        self.stdout.write(f'  - Total tareas: {total_tasks}')
        self.stdout.write(f'Queries ejecutadas: {num_queries}')
        self.stdout.write(f'Tiempo: {elapsed:.2f}ms')
        
        if num_queries > 15:
            self.stdout.write(self.style.WARNING('⚠️  Considera usar caché para stats'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Número de queries aceptable'))
    
    def _print_queries(self):
        """Imprime las queries SQL ejecutadas"""
        self.stdout.write('\n  Queries SQL ejecutadas:')
        for i, query in enumerate(connection.queries, 1):
            sql = query['sql']
            time_ms = float(query['time']) * 1000
            self.stdout.write(f'  {i}. [{time_ms:.2f}ms] {sql[:100]}...')
    
    def _print_summary(self):
        """Imprime un resumen de recomendaciones"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RESUMEN Y RECOMENDACIONES'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write('✅ OPTIMIZACIONES RECOMENDADAS:')
        self.stdout.write('  1. Usar .select_related() para ForeignKey (client, owner)')
        self.stdout.write('  2. Usar .prefetch_related() para ManyToMany y reverse FK (payments, tasks)')
        self.stdout.write('  3. Implementar caché Redis para cálculos pesados (progress, totals)')
        self.stdout.write('  4. Usar managers personalizados (ProjectManager.with_payments())')
        self.stdout.write('  5. Agregar índices compuestos en modelos (ver OPTIMIZACIONES_RENDIMIENTO.md)')
        
        self.stdout.write('\n📚 DOCUMENTACIÓN:')
        self.stdout.write('  - Ver archivo OPTIMIZACIONES_RENDIMIENTO.md para más detalles')
        self.stdout.write('  - Ejecutar migraciones para crear índices: python manage.py migrate')
        
        self.stdout.write('\n' + '='*80 + '\n')

