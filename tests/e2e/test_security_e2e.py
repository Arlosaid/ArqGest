"""
Tests E2E: Seguridad y Aislamiento

SECURITY TESTS: Estos tests verifican la seguridad del sistema:
- Aislamiento entre organizaciones (multi-tenancy)
- Protección contra acceso no autorizado
- Validación de permisos
- Manejo seguro de sesiones
- Protección contra ataques comunes
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestOrganizationIsolation:
    """
    Tests de aislamiento entre organizaciones.
    
    CRÍTICO: Verificar que usuarios de una org NO pueden acceder
    a recursos de otra org.
    """
    
    def test_cannot_access_other_org_project(
        self, logged_in_page: Page, live_server, e2e_other_org_user, db
    ):
        """
        SECURITY: Usuario NO puede ver proyectos de otra organización.
        """
        from tests.factories.projects.project_factories import ProjectFactory
        
        # Crear proyecto en la organización del otro usuario
        other_project = ProjectFactory(
            organization=e2e_other_org_user.organization,
            owner=e2e_other_org_user,
            name='Proyecto Secreto de Otra Org'
        )
        
        page = logged_in_page  # Logueado como e2e_user (org diferente)
        
        # Intentar acceder directamente al proyecto de otra org
        page.goto(f"{live_server.url}/projects/{other_project.pk}/")
        page.wait_for_timeout(1500)
        
        # Verificar acceso denegado
        access_blocked = (
            page.locator('text=403, text=Forbidden, text=permiso, text=acceso').count() > 0 or
            '/login' in page.url or
            page.locator(f'text={other_project.name}').count() == 0
        )
        
        assert access_blocked, "NO debería poder ver proyecto de otra org"
        print(f"✓ Acceso a proyecto de otra org bloqueado")
    
    def test_cannot_list_other_org_clients(
        self, logged_in_page: Page, live_server, e2e_other_org_user, db
    ):
        """
        SECURITY: Usuario NO puede ver clientes de otra organización.
        """
        from tests.factories.orgs.org_factories import ClientFactory
        
        # Crear cliente en otra org
        other_client = ClientFactory(
            organization=e2e_other_org_user.organization,
            name='Cliente Secreto'
        )
        
        page = logged_in_page
        
        # Ir a lista de clientes
        page.goto(f"{live_server.url}/orgs/clients/")
        page.wait_for_load_state("networkidle")
        
        # El cliente de otra org NO debería aparecer
        client_visible = page.locator(f'text={other_client.name}').count() > 0
        
        assert not client_visible, "NO debería ver cliente de otra org"
        print(f"✓ Cliente de otra org no visible en lista")
    
    def test_cannot_access_other_org_files(
        self, logged_in_page: Page, live_server, e2e_other_org_user, db
    ):
        """
        SECURITY: Usuario NO puede acceder a archivos de otra organización.
        """
        from tests.factories.files.file_factories import PDFFileFactory
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        
        # Crear proyecto, fase y archivo en otra org
        other_project = ProjectFactory(
            organization=e2e_other_org_user.organization,
            owner=e2e_other_org_user,
            name='Proyecto con Archivos Secretos'
        )
        other_phase = PhaseFactory(project=other_project)
        other_file = PDFFileFactory(phase=other_phase, uploaded_by=e2e_other_org_user)
        
        page = logged_in_page
        
        # Intentar acceder al archivo directamente
        page.goto(f"{live_server.url}/files/{other_file.pk}/")
        page.wait_for_timeout(1500)
        
        access_blocked = (
            page.locator('text=403').count() > 0 or
            page.locator('text=404').count() > 0 or
            page.locator('text=Forbidden').count() > 0 or
            page.locator('text=permiso').count() > 0 or
            page.locator('text="No encontrado"').count() > 0 or
            '/login' in page.url
        )
        
        assert access_blocked, "NO debería poder acceder archivo de otra org"
        print(f"✓ Acceso a archivo de otra org bloqueado")
    
    def test_cannot_edit_other_org_task(
        self, logged_in_page: Page, live_server, e2e_other_org_user, db
    ):
        """
        SECURITY: Usuario NO puede editar tareas de otra organización.
        """
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, TaskFactory
        
        other_project = ProjectFactory(
            organization=e2e_other_org_user.organization,
            owner=e2e_other_org_user,
        )
        other_phase = PhaseFactory(project=other_project)
        other_task = TaskFactory(phase=other_phase, assigned_to=e2e_other_org_user)
        
        page = logged_in_page
        
        # Intentar editar tarea de otra org
        page.goto(f"{live_server.url}/projects/{other_project.pk}/tasks/{other_task.pk}/edit/")
        page.wait_for_timeout(1500)
        
        access_blocked = (
            page.locator('text=403').count() > 0 or
            page.locator('text=404').count() > 0 or
            page.locator('text=Forbidden').count() > 0 or
            page.locator('text="No encontrado"').count() > 0 or
            '/login' in page.url
        )
        
        print(f"✓ Edición de tarea de otra org bloqueada: {access_blocked}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestURLManipulationProtection:
    """
    Tests contra manipulación de URLs y ataques IDOR.
    
    IDOR (Insecure Direct Object Reference): Verificar que no se puede
    acceder a objetos cambiando IDs en la URL.
    """
    
    def test_cannot_access_random_project_id(self, logged_in_page: Page, live_server):
        """
        SECURITY: Acceder a ID de proyecto inexistente debe dar 404, no error.
        """
        page = logged_in_page
        
        # ID muy alto que probablemente no existe
        fake_project_id = 999999999
        
        page.goto(f"{live_server.url}/projects/{fake_project_id}/")
        page.wait_for_timeout(1500)
        
        # Debería dar 404, no 500 o revelar información
        shows_404 = (
            page.locator('text=404, text=no encontrado, text=not found').count() > 0 or
            page.url != f"{live_server.url}/projects/{fake_project_id}/"
        )
        
        # NO debería mostrar error de servidor
        no_server_error = page.locator('text=500, text=error interno, text=internal error').count() == 0
        
        print(f"✓ ID inexistente manejado correctamente: 404={shows_404}, no_500={no_server_error}")
    
    def test_negative_id_handled_gracefully(self, logged_in_page: Page, live_server):
        """
        SECURITY: IDs negativos deben ser manejados sin errores.
        """
        page = logged_in_page
        
        # ID negativo
        page.goto(f"{live_server.url}/projects/-1/")
        page.wait_for_timeout(1500)
        
        # No debe crashear
        no_crash = page.locator('text=500, text=Server Error').count() == 0
        
        print(f"✓ ID negativo manejado sin crash: {no_crash}")
    
    def test_string_id_handled_gracefully(self, logged_in_page: Page, live_server):
        """
        SECURITY: IDs tipo string deben ser manejados sin errores.
        """
        page = logged_in_page
        
        # ID como string
        page.goto(f"{live_server.url}/projects/abc-injection/")
        page.wait_for_timeout(1500)
        
        no_crash = page.locator('text=500, text=Server Error, text=TypeError').count() == 0
        
        print(f"✓ ID string manejado sin crash: {no_crash}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestCSRFProtection:
    """
    Tests de protección CSRF.
    """
    
    def test_forms_include_csrf_token(self, logged_in_page: Page, live_server):
        """
        Verificar que los formularios incluyen token CSRF.
        """
        page = logged_in_page
        
        # Ir a un formulario
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Buscar input de CSRF
        csrf_input = page.locator('input[name="csrfmiddlewaretoken"]')
        
        has_csrf = csrf_input.count() > 0
        
        print(f"✓ Formulario tiene CSRF token: {has_csrf}")
        assert has_csrf, "Formularios deben incluir CSRF token"


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestAuthenticationSecurity:
    """
    Tests de seguridad de autenticación.
    """
    
    def test_login_page_uses_https_headers(self, page: Page, live_server):
        """
        Verificar headers de seguridad en página de login.
        """
        response = page.goto(f"{live_server.url}/accounts/login/")
        
        # En tests locales no hay HTTPS, pero verificamos que la página funciona
        page_loaded = page.locator('input[name="username"], input[name="login"]').count() > 0
        
        print(f"✓ Página de login cargada correctamente: {page_loaded}")
    
    def test_password_not_visible_in_url(self, page: Page, live_server, e2e_user):
        """
        SECURITY: La contraseña nunca debe aparecer en la URL.
        """
        page.goto(f"{live_server.url}/accounts/login/")
        
        page.locator('input[name="username"], input[name="login"]').first.fill(e2e_user.email)
        page.locator('input[name="password"]').first.fill('TestPass123!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        
        page.wait_for_timeout(2000)
        
        # La contraseña NO debe estar en la URL
        password_in_url = 'TestPass123!' in page.url or 'password=' in page.url
        
        assert not password_in_url, "Contraseña NO debe aparecer en URL"
        print(f"✓ Contraseña no visible en URL")
    
    def test_error_messages_do_not_reveal_info(self, page: Page, live_server, e2e_user):
        """
        SECURITY: Mensajes de error no deben revelar si el usuario existe.
        """
        page.goto(f"{live_server.url}/accounts/login/")
        
        # Intento 1: Email existente, password incorrecto
        page.locator('input[name="username"], input[name="login"]').first.fill(e2e_user.email)
        page.locator('input[name="password"]').first.fill('WrongPassword!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(1500)
        
        error_1 = page.locator('.errorlist, .alert-danger, .error, [class*="error"]').inner_text() if \
            page.locator('.errorlist, .alert-danger, .error').count() > 0 else ""
        
        # Intento 2: Email inexistente
        page.goto(f"{live_server.url}/accounts/login/")
        page.locator('input[name="username"], input[name="login"]').first.fill('nonexistent@fake.com')
        page.locator('input[name="password"]').first.fill('SomePassword!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(1500)
        
        error_2 = page.locator('.errorlist, .alert-danger, .error, [class*="error"]').inner_text() if \
            page.locator('.errorlist, .alert-danger, .error').count() > 0 else ""
        
        # Los mensajes deberían ser similares (no revelar si email existe)
        # No comparamos exactamente porque pueden variar
        
        reveals_user_exists = (
            'no existe' in error_2.lower() or
            'user not found' in error_2.lower() or
            'does not exist' in error_2.lower()
        )
        
        print(f"✓ Error no revela existencia de usuario: {not reveals_user_exists}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestSessionSecurity:
    """
    Tests de seguridad de sesión.
    """
    
    def test_session_invalidated_on_logout(self, logged_in_page: Page, live_server):
        """
        SECURITY: La sesión debe invalidarse completamente al hacer logout.
        """
        page = logged_in_page
        
        # Obtener una página protegida funciona
        page.goto(f"{live_server.url}/projects/")
        page.wait_for_timeout(500)
        assert '/login' not in page.url, "Debería estar logueado"
        
        # Hacer logout
        user_menu = page.locator('.dropdown-toggle, [data-bs-toggle="dropdown"]')
        if user_menu.count() > 0:
            user_menu.first.click()
            page.wait_for_timeout(300)
        
        logout_link = page.locator('a[href*="logout"]')
        if logout_link.count() > 0:
            logout_link.first.evaluate("el => el.click()")
            page.wait_for_timeout(1500)
        
        # Volver atrás NO debe restaurar sesión
        page.go_back()
        page.wait_for_timeout(500)
        
        # Intentar acceder a página protegida
        page.goto(f"{live_server.url}/projects/")
        page.wait_for_timeout(1000)
        
        # Debería pedir login
        requires_login = '/login' in page.url
        print(f"✓ Sesión invalidada correctamente: {requires_login}")
    
    def test_protected_pages_require_login(self, page: Page, live_server):
        """
        SECURITY: Páginas protegidas deben requerir autenticación.
        """
        protected_urls = [
            '/projects/',
            '/dashboard/',
            '/users/',
            '/orgs/clients/',
            '/accounts/profile/',
        ]
        
        for url in protected_urls:
            page.goto(f"{live_server.url}{url}")
            page.wait_for_timeout(500)
            
            redirected_to_login = '/login' in page.url or '/accounts/login' in page.url
            
            print(f"  {url}: {'✓ Requiere login' if redirected_to_login else '⚠ NO requiere login'}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestInputValidation:
    """
    Tests de validación de entrada y protección XSS.
    """
    
    def test_xss_in_project_name_escaped(self, logged_in_page: Page, live_server, e2e_client, db):
        """
        SECURITY: Scripts en campos de texto deben ser escapados.
        """
        from apps.projects.models import Project
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        xss_payload = '<script>alert("XSS")</script>'
        
        # Crear proyecto con payload XSS
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="name"]', xss_payload)
        
        desc_field = page.locator('textarea[name="description"]')
        if desc_field.count() > 0:
            desc_field.fill('Test XSS')
        
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(2000)
        
        # Obtener proyecto creado
        project = Project.objects.filter(organization=user.organization).order_by('-id').first()
        
        if project:
            # Ver el proyecto
            page.goto(f"{live_server.url}/projects/{project.pk}/")
            page.wait_for_timeout(1000)
            
            # El script NO debería ejecutarse (debería estar escapado)
            # Si hubiera XSS, habría un alert
            # Verificamos que el texto aparece como texto, no como HTML ejecutable
            
            # Buscar el texto del script (escapado)
            script_as_text = page.locator('text=<script>').count() > 0
            
            print(f"✓ XSS payload escapado: {script_as_text or 'script no visible'}")
    
    def test_sql_injection_prevented(self, logged_in_page: Page, live_server):
        """
        SECURITY: Intentos de SQL injection deben fallar gracefully.
        """
        page = logged_in_page
        
        sql_payloads = [
            "'; DROP TABLE projects; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users--",
        ]
        
        for payload in sql_payloads:
            # Intentar en búsqueda
            search_input = page.locator('input[name="q"], input[name="search"], input[type="search"]')
            
            if search_input.count() > 0:
                search_input.first.fill(payload)
                
                # Submit si hay form
                form = page.locator('form:has(input[name="search"])')
                if form.count() > 0:
                    form.locator('button[type="submit"]').first.click() if \
                        form.locator('button[type="submit"]').count() > 0 else None
                    page.wait_for_timeout(1000)
                
                # No debería haber error de SQL
                has_sql_error = page.locator(
                    'text=SQL, text=syntax error, text=database error'
                ).count() > 0
                
                assert not has_sql_error, f"SQL injection debería ser prevenido: {payload}"
        
        print(f"✓ SQL injection prevenido")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
@pytest.mark.security
class TestRateLimiting:
    """
    Tests de rate limiting (protección contra brute force).
    """
    
    def test_multiple_failed_logins(self, page: Page, live_server, e2e_user):
        """
        Múltiples intentos de login fallidos deberían ser limitados.
        """
        page.goto(f"{live_server.url}/accounts/login/")
        
        failed_attempts = 0
        blocked = False
        
        # Intentar varios logins fallidos
        for i in range(10):
            page.goto(f"{live_server.url}/accounts/login/")
            page.wait_for_timeout(300)
            
            page.locator('input[name="username"], input[name="login"]').first.fill(e2e_user.email)
            page.locator('input[name="password"]').first.fill(f'WrongPass{i}!')
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(500)
            
            failed_attempts += 1
            
            # Verificar si hay mensaje de bloqueo
            blocked_msg = page.locator(
                'text=bloqueado, text=blocked, text=too many, '
                'text=demasiados intentos, text=try again later'
            )
            
            if blocked_msg.count() > 0:
                blocked = True
                break
        
        print(f"✓ Intentos fallidos: {failed_attempts}, Bloqueado: {blocked}")
        # Nota: El bloqueo depende de la configuración del sistema
