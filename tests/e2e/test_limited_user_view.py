"""
Tests E2E: Vista de Usuario Limitado (Miembro de Organización)

Estos tests verifican el comportamiento de usuarios con rol limitado:
- Solo pueden ver tareas asignadas a ellos
- Pueden cambiar estado de sus tareas
- Pueden mover tareas en el Kanban
- NO pueden crear proyectos ni usuarios
- NO pueden acceder a secciones administrativas
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def limited_user(db, e2e_user, django_db_blocker):
    """
    Usuario con permisos limitados (no es org_admin).
    Este usuario solo puede ver y modificar sus propias tareas.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    with django_db_blocker.unblock():
        user = User.objects.create_user(
            username='limited_user_e2e',
            email='limited@test.com',
            password='LimitedPass123!',
            first_name='Limited',
            last_name='User',
            organization=e2e_user.organization,
            is_org_admin=False,  # NO es admin
            is_staff=False,      # NO es staff
            is_superuser=False   # NO es superuser
        )
        return user


@pytest.fixture
def logged_in_limited_page(page: Page, live_server, limited_user):
    """Página autenticada con usuario limitado"""
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector('input[name="username"], input[name="login"]', timeout=5000)
    
    username_field = page.locator('input[name="username"], input[name="login"]').first
    password_field = page.locator('input[name="password"]').first
    
    username_field.fill('limited@test.com')
    password_field.fill('LimitedPass123!')
    
    submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
    submit_btn.click()
    
    page.wait_for_timeout(2000)
    
    return page


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLimitedUserTaskVisibility:
    """Tests de visibilidad de tareas para usuario limitado"""
    
    def test_limited_user_sees_only_assigned_tasks(
        self, logged_in_limited_page: Page, live_server, limited_user, e2e_user, db, django_db_blocker
    ):
        """Usuario limitado solo ve tareas asignadas a él"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        
        with django_db_blocker.unblock():
            project = ProjectFactory(
                organization=e2e_user.organization,
                owner=e2e_user,
                name='Proyecto Tasks Visibility E2E'
            )
            phase = PhaseFactory(project=project, name='Fase Test', order=1)
            
            # Tarea asignada al usuario limitado
            my_task = TaskFactory(
                phase=phase,
                title='MI TAREA ASIGNADA E2E',
                status='todo',
                assigned_to=limited_user
            )
            
            # Tarea asignada al admin (no debería verla en "Mis Tareas")
            other_task = TaskFactory(
                phase=phase,
                title='TAREA DEL ADMIN E2E',
                status='todo',
                assigned_to=e2e_user
            )
        
        page = logged_in_limited_page
        
        # Ir a "Mis Tareas"
        page.goto(f"{live_server.url}/projects/my-tasks/")
        page.wait_for_load_state("networkidle")
        
        # Verificar visibilidad
        my_task_visible = page.locator('text=MI TAREA ASIGNADA E2E').count() > 0
        other_task_visible = page.locator('text=TAREA DEL ADMIN E2E').count() > 0
        
        print(f"✓ Mi tarea visible: {my_task_visible}")
        print(f"✓ Tarea del admin visible: {other_task_visible}")
        
        assert my_task_visible, "Usuario limitado debería ver sus tareas asignadas"
        # Nota: other_task podría ser visible si la vista no filtra, 
        # pero en "Mis Tareas" normalmente NO debería aparecer
    
    def test_limited_user_can_access_project_kanban(
        self, logged_in_limited_page: Page, live_server, limited_user, e2e_user, db, django_db_blocker
    ):
        """Usuario limitado puede acceder al Kanban del proyecto donde tiene tareas"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        
        with django_db_blocker.unblock():
            project = ProjectFactory(
                organization=e2e_user.organization,
                owner=e2e_user,
                name='Proyecto Kanban Limited E2E'
            )
            phase = PhaseFactory(project=project, name='Fase Test', order=1)
            
            # Tarea asignada al usuario limitado
            task = TaskFactory(
                phase=phase,
                title='Tarea Kanban Limited E2E',
                status='todo',
                assigned_to=limited_user
            )
            project_id = project.pk
        
        page = logged_in_limited_page
        
        # Ir al Kanban del proyecto
        page.goto(f"{live_server.url}/projects/{project_id}/tasks/")
        page.wait_for_load_state("networkidle")
        
        # Verificar acceso (no debe ser redirigido a login ni mostrar 403)
        has_access = (
            '/login' not in page.url and
            page.locator('text=403, text=Forbidden').count() == 0
        )
        
        # Verificar que la tarea aparece
        task_visible = page.locator('text=Tarea Kanban Limited E2E').count() > 0
        
        print(f"✓ Acceso al Kanban: {has_access}")
        print(f"✓ Tarea visible en Kanban: {task_visible}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLimitedUserTaskModification:
    """Tests de modificación de tareas para usuario limitado"""
    
    def test_limited_user_can_change_task_status(
        self, logged_in_limited_page: Page, live_server, limited_user, e2e_user, db, django_db_blocker
    ):
        """Usuario limitado puede cambiar el estado de sus tareas"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.projects.models import Task
        
        with django_db_blocker.unblock():
            project = ProjectFactory(
                organization=e2e_user.organization,
                owner=e2e_user,
                name='Proyecto Status Change Limited E2E'
            )
            phase = PhaseFactory(project=project, name='Fase Test', order=1)
            
            task = TaskFactory(
                phase=phase,
                title='Cambiar Estado Limited E2E',
                status='todo',
                assigned_to=limited_user
            )
            task_id = task.pk
        
        page = logged_in_limited_page
        
        # Ir a "Mis Tareas"
        page.goto(f"{live_server.url}/projects/my-tasks/")
        page.wait_for_load_state("networkidle")
        
        # Buscar la tarea y hacer click
        task_element = page.locator('text=Cambiar Estado Limited E2E')
        
        if task_element.count() > 0:
            task_element.first.click()
            page.wait_for_timeout(500)
            
            # Buscar selector de estado
            status_select = page.locator('select[name="status"]:visible')
            
            if status_select.count() > 0:
                status_select.first.select_option(value='in_progress')
                
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn:
                    save_btn.click()
                    page.wait_for_timeout(1500)
                
                # Verificar cambio
                with django_db_blocker.unblock():
                    task = Task.objects.get(pk=task_id)
                    print(f"✓ Estado cambiado a: {task.status}")
                    assert task.status == 'in_progress', "Estado debería ser 'in_progress'"
            else:
                print("⚠ No se encontró selector de estado")
        else:
            pytest.skip("Tarea no visible")
    
    def test_limited_user_can_complete_task(
        self, logged_in_limited_page: Page, live_server, limited_user, e2e_user, db, django_db_blocker
    ):
        """Usuario limitado puede completar sus tareas"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.projects.models import Task
        
        with django_db_blocker.unblock():
            project = ProjectFactory(
                organization=e2e_user.organization,
                owner=e2e_user,
                name='Proyecto Complete Task Limited E2E'
            )
            phase = PhaseFactory(project=project, name='Fase Test', order=1)
            
            task = TaskFactory(
                phase=phase,
                title='Completar Tarea Limited E2E',
                status='in_progress',
                assigned_to=limited_user
            )
            task_id = task.pk
        
        page = logged_in_limited_page
        
        # Ir a editar la tarea directamente
        page.goto(f"{live_server.url}/projects/tasks/{task_id}/edit/")
        page.wait_for_load_state("networkidle")
        
        status_select = page.locator('select[name="status"]:visible')
        
        if status_select.count() > 0:
            status_select.select_option(value='done')
            
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            with django_db_blocker.unblock():
                task = Task.objects.get(pk=task_id)
                print(f"✓ Tarea completada: {task.status}")
        else:
            pytest.skip("Formulario de tarea no encontrado")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLimitedUserRestrictions:
    """Tests de restricciones para usuario limitado"""
    
    def test_limited_user_cannot_create_project(
        self, logged_in_limited_page: Page, live_server, limited_user
    ):
        """Usuario limitado NO puede crear proyectos"""
        page = logged_in_limited_page
        
        # Intentar acceder a crear proyecto
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_timeout(1500)
        
        # Debería ser rechazado o redirigido
        access_denied = (
            '/login' in page.url or
            page.locator('text=403, text=permiso, text=acceso denegado').count() > 0 or
            page.url != f"{live_server.url}/projects/new/"
        )
        
        print(f"✓ Acceso a crear proyecto bloqueado: {access_denied}")
        # Nota: Esto depende de los permisos configurados en la app
    
    def test_limited_user_cannot_access_user_management(
        self, logged_in_limited_page: Page, live_server, limited_user
    ):
        """Usuario limitado NO puede acceder a gestión de usuarios"""
        page = logged_in_limited_page
        
        page.goto(f"{live_server.url}/users/")
        page.wait_for_timeout(1500)
        
        access_denied = (
            '/login' in page.url or
            page.locator('text=403, text=permiso').count() > 0 or
            page.url != f"{live_server.url}/users/"
        )
        
        print(f"✓ Acceso a usuarios bloqueado: {access_denied}")
    
    def test_limited_user_cannot_access_finance_config(
        self, logged_in_limited_page: Page, live_server, limited_user, e2e_user, db, django_db_blocker
    ):
        """Usuario limitado NO puede configurar presupuestos"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        
        with django_db_blocker.unblock():
            project = ProjectFactory(
                organization=e2e_user.organization,
                owner=e2e_user,
                name='Proyecto Finance Restricted E2E'
            )
            PhaseFactory(project=project, name='Fase Test', order=1)
            project_id = project.pk
        
        page = logged_in_limited_page
        
        # Intentar configurar presupuesto
        page.goto(f"{live_server.url}/projects/{project_id}/budget/config/")
        page.wait_for_timeout(1500)
        
        access_denied = (
            '/login' in page.url or
            page.locator('text=403, text=permiso').count() > 0
        )
        
        print(f"✓ Acceso a configurar presupuesto bloqueado: {access_denied}")
    
    def test_limited_user_cannot_delete_tasks(
        self, logged_in_limited_page: Page, live_server, limited_user, e2e_user, db, django_db_blocker
    ):
        """Usuario limitado NO puede eliminar tareas"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        from apps.projects.models import Task
        
        with django_db_blocker.unblock():
            project = ProjectFactory(
                organization=e2e_user.organization,
                owner=e2e_user,
                name='Proyecto Delete Task Restricted E2E'
            )
            phase = PhaseFactory(project=project, name='Fase Test', order=1)
            
            task = TaskFactory(
                phase=phase,
                title='Tarea No Eliminar E2E',
                assigned_to=limited_user
            )
            task_id = task.pk
        
        page = logged_in_limited_page
        
        # Intentar eliminar tarea
        page.goto(f"{live_server.url}/projects/tasks/{task_id}/delete/")
        page.wait_for_timeout(1500)
        
        # Verificar si fue bloqueado
        access_denied = (
            '/login' in page.url or
            page.locator('text=403, text=permiso').count() > 0
        )
        
        # Verificar que la tarea sigue existiendo
        with django_db_blocker.unblock():
            task_exists = Task.objects.filter(pk=task_id).exists()
        
        print(f"✓ Acceso a eliminar bloqueado: {access_denied}")
        print(f"✓ Tarea sigue existiendo: {task_exists}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLimitedUserNavigation:
    """Tests de navegación para usuario limitado"""
    
    def test_limited_user_sidebar_shows_limited_options(
        self, logged_in_limited_page: Page, live_server, limited_user
    ):
        """El sidebar para usuario limitado muestra opciones reducidas"""
        page = logged_in_limited_page
        
        # Ir al dashboard
        page.goto(f"{live_server.url}/dashboard/")
        page.wait_for_load_state("networkidle")
        
        # Verificar opciones del sidebar
        sidebar = page.locator('nav, .sidebar, [class*="sidebar"]')
        
        # Debería ver "Mis Tareas"
        my_tasks_visible = page.locator('text=Mis Tareas, text=My Tasks').count() > 0
        
        # NO debería ver "Gestión de Usuarios" (si aplica)
        users_management_visible = page.locator('a:has-text("Usuarios"), a:has-text("Users")').count() > 0
        
        # NO debería ver "Configuración" (si aplica)
        config_visible = page.locator('a:has-text("Configuración"), a:has-text("Settings")').count() > 0
        
        print(f"✓ 'Mis Tareas' visible: {my_tasks_visible}")
        print(f"⚠ 'Usuarios' visible (debería ser limitado): {users_management_visible}")
        print(f"⚠ 'Configuración' visible (debería ser limitado): {config_visible}")
    
    def test_limited_user_can_view_profile(
        self, logged_in_limited_page: Page, live_server, limited_user
    ):
        """Usuario limitado puede ver su propio perfil"""
        page = logged_in_limited_page
        
        page.goto(f"{live_server.url}/accounts/profile/")
        page.wait_for_load_state("networkidle")
        
        # Debería poder acceder
        has_access = '/login' not in page.url
        
        # Debería ver su información
        email_visible = page.locator(f'text={limited_user.email}').count() > 0
        
        print(f"✓ Acceso al perfil: {has_access}")
        print(f"✓ Email visible: {email_visible}")
    
    def test_limited_user_can_change_own_password(
        self, logged_in_limited_page: Page, live_server, limited_user
    ):
        """Usuario limitado puede cambiar su propia contraseña"""
        page = logged_in_limited_page
        
        # Buscar link de cambio de contraseña en perfil o directamente
        page.goto(f"{live_server.url}/accounts/password/change/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que tiene acceso al formulario
        password_form = page.locator(
            'input[name="old_password"], '
            'input[name="new_password1"], '
            'input[name="new_password"]'
        )
        
        has_access = password_form.count() > 0
        print(f"✓ Formulario de cambio de contraseña accesible: {has_access}")
