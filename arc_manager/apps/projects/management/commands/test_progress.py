"""
Comando para probar y verificar el cálculo de progreso de proyectos.
"""
from django.core.management.base import BaseCommand
from apps.projects.models import Project, Phase, Task
from apps.orgs.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Prueba y verifica el cálculo de progreso de proyectos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Crear datos de prueba si no existen',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== VERIFICACIÓN DE PROGRESO DE PROYECTOS ===\n")
        
        # Verificar proyectos existentes
        projects = Project.objects.all()
        self.stdout.write(f"Total de proyectos: {projects.count()}")
        
        if projects.count() == 0:
            if options['create_test_data']:
                self.create_test_data()
                projects = Project.objects.all()
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No hay proyectos. Usa --create-test-data para crear datos de prueba."
                    )
                )
                return
        
        # Analizar cada proyecto
        for project in projects[:3]:  # Solo los primeros 3
            self.stdout.write(f"\n--- PROYECTO: {project.name} (ID: {project.id}) ---")
            
            # Verificar fases
            phases = project.phases.all()
            self.stdout.write(f"Fases: {phases.count()}")
            
            # Verificar tareas
            all_tasks = Task.objects.filter(phase__project=project)
            total_tasks = all_tasks.count()
            
            self.stdout.write(f"Total tareas: {total_tasks}")
            
            if total_tasks > 0:
                # Contar tareas por estado
                todo_tasks = all_tasks.filter(status='TODO').count()
                in_progress_tasks = all_tasks.filter(status='IN_PROGRESS').count()
                paused_tasks = all_tasks.filter(status='PAUSED').count()
                done_tasks = all_tasks.filter(status='DONE').count()
                
                self.stdout.write(f"  - TODO: {todo_tasks}")
                self.stdout.write(f"  - IN_PROGRESS: {in_progress_tasks}")
                self.stdout.write(f"  - PAUSED: {paused_tasks}")
                self.stdout.write(f"  - DONE: {done_tasks}")
                
                # Calcular progreso
                progress = project.progress_percentage
                self.stdout.write(f"Progreso calculado: {progress}%")
                
                if done_tasks == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            "⚠️  No hay tareas completadas (DONE). El progreso será 0%."
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  Este proyecto no tiene tareas.")
                )
        
        self.stdout.write(f"\n=== RESUMEN ===")
        self.stdout.write(
            "Para ver progreso, necesitas tener tareas con estado 'DONE' en tus proyectos."
        )

    def create_test_data(self):
        """Crear datos de prueba básicos."""
        self.stdout.write("Creando datos de prueba...")
        
        # Obtener o crear organización
        org = Organization.objects.first()
        if not org:
            org = Organization.objects.create(name="Organización de Prueba")
        
        # Obtener o crear usuario
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                email="test@example.com",
                password="test123",
                organization=org
            )
        
        # Crear proyecto de prueba
        project = Project.objects.create(
            name="Proyecto de Prueba - Progreso",
            organization=org,
            owner=user,
            status='ACTIVE'
        )
        
        # Crear fase
        phase = Phase.objects.create(
            project=project,
            name="Fase de Prueba",
            order=1,
            status='IN_PROGRESS'
        )
        
        # Crear tareas con diferentes estados
        Task.objects.create(
            phase=phase,
            title="Tarea Completada 1",
            status='DONE',
            assigned_to=user
        )
        Task.objects.create(
            phase=phase,
            title="Tarea Completada 2",
            status='DONE',
            assigned_to=user
        )
        Task.objects.create(
            phase=phase,
            title="Tarea en Progreso 1",
            status='IN_PROGRESS',
            assigned_to=user
        )
        Task.objects.create(
            phase=phase,
            title="Tarea Pendiente 1",
            status='TODO',
            assigned_to=user
        )
        Task.objects.create(
            phase=phase,
            title="Tarea Pendiente 2",
            status='TODO',
            assigned_to=user
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Datos de prueba creados: {project.name} con 5 tareas (2 completadas = 40% progreso)"
            )
        )
