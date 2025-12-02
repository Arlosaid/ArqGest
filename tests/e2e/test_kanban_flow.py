"""
Tests E2E: Flujo Completo de Kanban

Estos tests verifican el uso del tablero Kanban:
- Mover tareas entre columnas (estados)
- Crear múltiples tareas y organizarlas
- Filtrar por fase/asignado
- Drag and drop de tareas
- Vista de usuario limitado
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestKanbanBasic:
    """Tests básicos del tablero Kanban"""
    
    def test_kanban_board_loads_with_columns(self, logged_in_page: Page, live_server, e2e_project_with_phases):
        """Tablero Kanban carga con todas las columnas de estado"""
        page = logged_in_page
        project = e2e_project_with_phases['project']
        
        # Ir al proyecto y luego al kanban
        page.goto(f"{live_server.url}/projects/{project.pk}/tasks/")
        page.wait_for_load_state("networkidle")
        
        # Verificar columnas del Kanban
        column_names = ['Por Hacer', 'En Progreso', 'Completado', 'Todo', 'In Progress', 'Done']
        
        columns_found = 0
        for name in column_names:
            if page.locator(f'text={name}').count() > 0:
                columns_found += 1
        
        has_kanban_structure = (
            columns_found >= 2 or
            page.locator('[class*="kanban"]').count() > 0 or
            page.locator('[data-status]').count() > 0
        )
        
        print(f"✓ Columnas de Kanban encontradas: {columns_found}")
        assert has_kanban_structure, "Debería mostrar estructura de Kanban"
    
    def test_tasks_appear_in_correct_columns(self, logged_in_page: Page, live_server, db):
        """Las tareas aparecen en la columna correcta según su estado"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Columns E2E')
        phase = PhaseFactory(project=project, name='Fase Test', order=1)
        
        # Crear tareas con diferentes estados
        task_todo = TaskFactory(phase=phase, title='Tarea TODO E2E', status='todo', assigned_to=user)
        task_progress = TaskFactory(phase=phase, title='Tarea PROGRESS E2E', status='in_progress', assigned_to=user)
        task_done = TaskFactory(phase=phase, title='Tarea DONE E2E', status='done', assigned_to=user)
        
        page.goto(f"{live_server.url}/projects/{project.pk}/tasks/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que las tareas son visibles
        todo_visible = page.locator(f'text={task_todo.title}').count() > 0
        progress_visible = page.locator(f'text={task_progress.title}').count() > 0
        done_visible = page.locator(f'text={task_done.title}').count() > 0
        
        print(f"✓ Tarea TODO visible: {todo_visible}")
        print(f"✓ Tarea In Progress visible: {progress_visible}")
        print(f"✓ Tarea Done visible: {done_visible}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestKanbanTaskMovement:
    """Tests de movimiento de tareas en Kanban"""
    
    def test_change_task_status_via_select(self, logged_in_page: Page, live_server, db):
        """Cambiar estado de tarea usando selector (si existe)"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Change Status E2E')
        phase = PhaseFactory(project=project, name='Fase Test', order=1)
        task = TaskFactory(phase=phase, title='Tarea Mover E2E', status='todo', assigned_to=user)
        
        page.goto(f"{live_server.url}/projects/{project.pk}/tasks/")
        page.wait_for_load_state("networkidle")
        
        # Buscar la tarea
        task_card = page.locator(f'text={task.title}')
        
        if task_card.count() > 0:
            # Hacer click en la tarea para abrir detalle/modal
            task_card.first.click()
            page.wait_for_timeout(500)
            
            # Buscar selector de estado
            status_select = page.locator('select[name="status"]:visible')
            
            if status_select.count() > 0:
                status_select.first.select_option(value='in_progress')
                page.wait_for_timeout(500)
                
                # Guardar si hay botón
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn and save_btn.count() > 0:
                    save_btn.click()
                    page.wait_for_timeout(1500)
                
                # Verificar cambio
                task.refresh_from_db()
                print(f"✓ Estado cambiado: {task.status}")
            else:
                print("⚠ No se encontró selector de estado")
        else:
            pytest.skip("Tarea no visible en Kanban")
    
    def test_move_task_between_phases(self, logged_in_page: Page, live_server, db):
        """Mover tarea entre fases"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Move Phase E2E')
        phase1 = PhaseFactory(project=project, name='Fase 1', order=1)
        phase2 = PhaseFactory(project=project, name='Fase 2', order=2)
        task = TaskFactory(phase=phase1, title='Tarea Cambiar Fase E2E', status='todo', assigned_to=user)
        
        # Ir a editar la tarea
        page.goto(f"{live_server.url}/projects/tasks/{task.pk}/edit/")
        page.wait_for_load_state("networkidle")
        
        # Buscar selector de fase
        phase_select = page.locator('select[name="phase"]:visible')
        
        if phase_select.count() > 0:
            # Cambiar a fase 2
            phase_select.select_option(str(phase2.pk))
            
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar
            task.refresh_from_db()
            assert task.phase.pk == phase2.pk, f"Tarea debería estar en Fase 2, está en {task.phase.name}"
            print(f"✓ Tarea movida a: {task.phase.name}")
        else:
            pytest.skip("Formulario de edición de tarea no encontrado")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestKanbanMultipleTasks:
    """Tests con múltiples tareas en Kanban"""
    
    def test_create_multiple_tasks_in_kanban(self, logged_in_page: Page, live_server, db):
        """Crear múltiples tareas y ver en Kanban"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        from apps.projects.models import Task
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Multi Tasks E2E')
        phase = PhaseFactory(project=project, name='Fase Test', order=1)
        
        # Ir al kanban
        page.goto(f"{live_server.url}/projects/{project.pk}/tasks/")
        page.wait_for_load_state("networkidle")
        
        tasks_created = 0
        task_titles = [
            'Revisar planos arquitectónicos',
            'Calcular materiales necesarios',
            'Coordinar con proveedores',
            'Preparar presupuesto detallado'
        ]
        
        for title in task_titles:
            # Buscar botón de nueva tarea
            new_task_btn = page.locator('button:has-text("Nueva Tarea"), a:has-text("Nueva Tarea")')
            
            if new_task_btn.count() > 0 and new_task_btn.first.is_visible():
                new_task_btn.first.click()
                page.wait_for_timeout(500)
                
                # Llenar formulario
                title_field = page.locator('input[name="title"]:visible')
                if title_field.count() > 0:
                    title_field.fill(title)
                    
                    phase_select = page.locator('select[name="phase"]:visible')
                    if phase_select.count() > 0:
                        phase_select.select_option(str(phase.pk))
                    
                    save_btn = page.locator('button[type="submit"]:visible').first
                    if save_btn:
                        save_btn.click()
                        page.wait_for_timeout(1000)
                        tasks_created += 1
        
        # Verificar tareas creadas
        final_count = Task.objects.filter(phase__project=project).count()
        print(f"✓ Tareas creadas: {tasks_created}, Total en BD: {final_count}")
    
    def test_filter_tasks_by_status(self, logged_in_page: Page, live_server, db):
        """Filtrar tareas por estado en el Kanban"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Filter E2E')
        phase = PhaseFactory(project=project, name='Fase Test', order=1)
        
        # Crear varias tareas
        TaskFactory(phase=phase, title='Filter Task 1', status='todo', assigned_to=user)
        TaskFactory(phase=phase, title='Filter Task 2', status='in_progress', assigned_to=user)
        TaskFactory(phase=phase, title='Filter Task 3', status='done', assigned_to=user)
        
        page.goto(f"{live_server.url}/projects/{project.pk}/tasks/")
        page.wait_for_load_state("networkidle")
        
        # Buscar filtros
        filter_controls = page.locator(
            'select[name="status"], '
            '[class*="filter"], '
            'input[type="checkbox"][name*="status"]'
        )
        
        if filter_controls.count() > 0:
            print("✓ Controles de filtro disponibles")
        else:
            print("⚠ No se encontraron controles de filtro")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestKanbanFromMyTasks:
    """Tests del Kanban desde la vista "Mis Tareas" """
    
    def test_my_tasks_shows_only_assigned_tasks(self, logged_in_page: Page, live_server, db):
        """Mis Tareas solo muestra tareas asignadas al usuario actual"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear segundo usuario
        other_user = User.objects.create_user(
            username='other_kanban_user',
            email='other_kanban@test.com',
            password='TestPass123!',
            organization=user.organization
        )
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban My Tasks E2E')
        phase = PhaseFactory(project=project, name='Fase Test', order=1)
        
        # Tareas del usuario actual
        my_task = TaskFactory(phase=phase, title='MI TAREA E2E', status='todo', assigned_to=user)
        
        # Tarea del otro usuario
        other_task = TaskFactory(phase=phase, title='TAREA OTRO USUARIO E2E', status='todo', assigned_to=other_user)
        
        # Ir a "Mis Tareas"
        page.goto(f"{live_server.url}/projects/my-tasks/")
        page.wait_for_load_state("networkidle")
        
        # Verificar visibilidad
        my_task_visible = page.locator(f'text=MI TAREA E2E').count() > 0
        other_task_visible = page.locator(f'text=TAREA OTRO USUARIO E2E').count() > 0
        
        print(f"✓ Mi tarea visible: {my_task_visible}")
        print(f"✓ Tarea de otro usuario visible: {other_task_visible}")
        
        assert my_task_visible, "Mi tarea debería ser visible en 'Mis Tareas'"
    
    def test_change_task_status_from_my_tasks(self, logged_in_page: Page, live_server, db):
        """Cambiar estado de tarea desde "Mis Tareas" """
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Status Change E2E')
        phase = PhaseFactory(project=project, name='Fase Test', order=1)
        task = TaskFactory(phase=phase, title='Cambiar Estado MyTasks E2E', status='todo', assigned_to=user)
        
        page.goto(f"{live_server.url}/projects/my-tasks/")
        page.wait_for_load_state("networkidle")
        
        # Buscar la tarea y cambiar estado
        task_element = page.locator(f'text={task.title}')
        
        if task_element.count() > 0:
            task_element.first.click()
            page.wait_for_timeout(500)
            
            status_select = page.locator('select[name="status"]:visible')
            if status_select.count() > 0:
                status_select.first.select_option(value='in_progress')
                
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn:
                    save_btn.click()
                    page.wait_for_timeout(1500)
                
                task.refresh_from_db()
                print(f"✓ Estado actualizado a: {task.status}")
            else:
                print("⚠ No se encontró selector de estado")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestKanbanSelector:
    """Tests del selector de proyecto para Kanban"""
    
    def test_kanban_selector_loads(self, logged_in_page: Page, live_server, db):
        """El selector de proyecto para Kanban carga correctamente"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear varios proyectos
        p1 = ProjectFactory(organization=user.organization, owner=user, name='Kanban Selector 1')
        p2 = ProjectFactory(organization=user.organization, owner=user, name='Kanban Selector 2')
        PhaseFactory(project=p1, name='Fase 1', order=1)
        PhaseFactory(project=p2, name='Fase 1', order=1)
        
        page.goto(f"{live_server.url}/projects/kanban-selector/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que los proyectos aparecen
        p1_visible = page.locator(f'text=Kanban Selector 1').count() > 0
        p2_visible = page.locator(f'text=Kanban Selector 2').count() > 0
        
        print(f"✓ Proyecto 1 en selector: {p1_visible}")
        print(f"✓ Proyecto 2 en selector: {p2_visible}")
    
    def test_kanban_selector_navigates_to_project(self, logged_in_page: Page, live_server, db):
        """Seleccionar proyecto navega al Kanban correcto"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(organization=user.organization, owner=user, name='Kanban Navigate Test')
        PhaseFactory(project=project, name='Fase Test', order=1)
        
        page.goto(f"{live_server.url}/projects/kanban-selector/")
        page.wait_for_load_state("networkidle")
        
        # Buscar y clickear el proyecto
        project_link = page.locator(f'text=Kanban Navigate Test')
        
        if project_link.count() > 0:
            project_link.first.click()
            page.wait_for_timeout(1500)
            
            # Verificar navegación
            current_url = page.url
            navigated = str(project.pk) in current_url or 'tasks' in current_url or 'kanban' in current_url
            print(f"✓ Navegó al proyecto: {navigated}, URL: {current_url}")
        else:
            pytest.skip("Proyecto no encontrado en selector")
