"""
Configuración de Playwright para tests E2E

Este archivo contiene:
- Configuración del navegador
- Fixtures de usuarios para E2E
- Helpers de autenticación
- Hook para capturar screenshots en fallos
- Generadores de archivos de prueba
- Fixtures de datos complejos
"""
import pytest
import os
import tempfile
import io
from pathlib import Path

# Configurar SQLite ANTES de importar Django
os.environ['DATABASE_URL'] = 'sqlite:///test_e2e_db.sqlite3'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['DEBUG'] = 'True'
os.environ['TESTING'] = 'True'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

from playwright.sync_api import Page, Browser, BrowserContext
from django.contrib.auth import get_user_model
from django.test import override_settings

# PIL es opcional - algunos fixtures lo necesitan
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

User = get_user_model()


# ============================================================================
# CONFIGURACIÓN DEL NAVEGADOR
# ============================================================================

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configuración del contexto del navegador"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "es-MX",
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configuración para lanzar el navegador en pantalla completa"""
    return {
        **browser_type_launch_args,
        "args": ["--start-maximized"],
    }


# ============================================================================
# FIXTURES DE USUARIOS PARA E2E
# ============================================================================

@pytest.fixture
def e2e_user(db, django_db_blocker):
    """
    Usuario para tests E2E con password conocido.
    Crea una organización con plan activo y un usuario admin de esa org.
    """
    with django_db_blocker.unblock():
        from tests.factories.orgs.org_factories import OrganizationFactory
        from tests.factories.plans.plan_factories import SubscriptionFactory, BasicPlanFactory
        
        # Crear organización
        org = OrganizationFactory(name='E2E Test Organization')
        
        # Crear plan con suficientes usuarios
        plan = BasicPlanFactory(max_users=10, max_storage_gb=100)
        
        # Crear suscripción activa
        SubscriptionFactory(organization=org, plan=plan, subscription_status='basic_active')
        
        # Ahora crear el usuario
        user = User.objects.create_user(
            username='e2e_user',
            email='e2e@test.com',
            password='TestPass123!',
            first_name='E2E',
            last_name='Tester',
            organization=org,
            is_org_admin=True
        )
        return user


@pytest.fixture
def e2e_admin(db, django_db_blocker):
    """Superusuario para tests E2E del admin de Django"""
    with django_db_blocker.unblock():
        admin = User.objects.create_superuser(
            username='e2e_admin',
            email='admin@test.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='E2E'
        )
        return admin


@pytest.fixture
def e2e_client(db, e2e_user, django_db_blocker):
    """Cliente asociado a la organización del usuario E2E"""
    with django_db_blocker.unblock():
        from tests.factories.orgs.org_factories import ClientFactory
        
        return ClientFactory(
            organization=e2e_user.organization,
            name='Cliente E2E Test'
        )


# ============================================================================
# HELPERS DE AUTENTICACIÓN
# ============================================================================

@pytest.fixture
def logged_in_page(page: Page, live_server, e2e_user):
    """
    Página ya autenticada con un usuario.
    Usa este fixture cuando necesites un usuario ya logueado.
    """
    page.goto(f"{live_server.url}/accounts/login/")
    
    # Esperar a que cargue el formulario
    page.wait_for_selector('input[name="username"], input[name="login"]', timeout=5000)
    
    # Intentar con diferentes nombres de campo (Django puede variar)
    username_field = page.locator('input[name="username"], input[name="login"]').first
    password_field = page.locator('input[name="password"]').first
    
    username_field.fill('e2e@test.com')
    password_field.fill('TestPass123!')
    
    # Buscar botón de submit
    submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
    submit_btn.click()
    
    # Esperar redirección (no estar en login)
    page.wait_for_timeout(2000)
    
    return page


@pytest.fixture
def admin_page(page: Page, live_server, e2e_admin):
    """Página autenticada como superadmin en Django Admin"""
    page.goto(f"{live_server.url}/admin/login/")
    
    page.fill('input[name="username"]', 'admin@test.com')
    page.fill('input[name="password"]', 'AdminPass123!')
    page.click('input[type="submit"]')
    
    # Esperar a estar en admin
    page.wait_for_url(f"{live_server.url}/admin/**", timeout=5000)
    
    return page


# ============================================================================
# SCREENSHOT EN FALLOS (DEBUGGING)
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Captura screenshot automáticamente cuando un test E2E falla.
    Los screenshots se guardan en tests/e2e/screenshots/
    """
    outcome = yield
    report = outcome.get_result()
    
    # Solo capturar en fallos durante la ejecución del test
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
            screenshot_path = os.path.join(screenshot_dir, f"{item.name}.png")
            
            try:
                os.makedirs(screenshot_dir, exist_ok=True)
                page.screenshot(path=screenshot_path)
                print(f"\n[Screenshot] Guardado: {screenshot_path}")
            except Exception as e:
                print(f"\n[Warning] No se pudo guardar screenshot: {e}")


# ============================================================================
# HELPERS ÚTILES
# ============================================================================

@pytest.fixture
def wait_for_page_load(page: Page):
    """Helper para esperar que la página cargue completamente"""
    def _wait():
        page.wait_for_load_state("networkidle")
    return _wait


# ============================================================================
# FIXTURES DE ARCHIVOS PARA E2E
# ============================================================================

@pytest.fixture
def temp_pdf_file():
    """
    Crea un archivo PDF válido temporal para tests de upload.
    Retorna la ruta al archivo.
    """
    # PDF mínimo válido
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        f.write(pdf_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_image_file():
    """
    Crea una imagen JPG válida temporal para tests de upload.
    Retorna la ruta al archivo.
    """
    if HAS_PIL:
        # Crear imagen simple con PIL
        img = Image.new('RGB', (100, 100), color='red')
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            temp_path = f.name
        
        img.save(temp_path, 'JPEG')
    else:
        # Fallback: minimal JPEG bytes
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5,
            0xDB, 0x20, 0xA8, 0xBA, 0xAC, 0xEA, 0xFF, 0xD9
        ])
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            f.write(jpeg_bytes)
            temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_png_file():
    """Crea una imagen PNG válida temporal"""
    if HAS_PIL:
        img = Image.new('RGBA', (200, 200), color=(0, 128, 255, 255))
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            temp_path = f.name
        
        img.save(temp_path, 'PNG')
    else:
        # Minimal PNG (1x1 blue pixel)
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x80, 0xFF,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xA3, 0xE5, 0xEB,
            0x7A, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(png_bytes)
            temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_txt_file():
    """Crea un archivo TXT válido temporal"""
    content = b"Este es un archivo de texto de prueba para E2E tests.\n" * 10
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_malicious_file():
    """
    Crea un archivo con extensión peligrosa para tests de seguridad.
    El sistema debería rechazar este archivo.
    """
    content = b"MZ\x90\x00fake executable content"
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.exe', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_large_file():
    """
    Crea un archivo de ~5MB para tests de archivos grandes.
    Marcado como slow porque puede tardar en crear/subir.
    """
    # 5MB de contenido
    content = b"0" * (5 * 1024 * 1024)
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================================================
# FIXTURES DE DATOS COMPLEJOS PARA E2E
# ============================================================================

@pytest.fixture
def e2e_project_with_phases(db, e2e_user, e2e_client, django_db_blocker):
    """
    Proyecto completo con fases para tests E2E.
    Incluye: proyecto, cliente, 3 fases, y algunas tareas.
    """
    with django_db_blocker.unblock():
        from tests.factories.projects.project_factories import (
            ProjectFactory, PhaseFactory, TaskFactory
        )
        from decimal import Decimal
        
        project = ProjectFactory(
            organization=e2e_user.organization,
            owner=e2e_user,
            client=e2e_client,
            name='Proyecto E2E Completo',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        
        # Crear fases
        phase_design = PhaseFactory(
            project=project,
            name='Diseño',
            order=1,
            status='pending'
        )
        phase_development = PhaseFactory(
            project=project,
            name='Desarrollo',
            order=2,
            status='pending'
        )
        phase_delivery = PhaseFactory(
            project=project,
            name='Entrega',
            order=3,
            status='pending'
        )
        
        # Crear algunas tareas
        TaskFactory(
            phase=phase_design,
            title='Diseñar planos arquitectónicos',
            assigned_to=e2e_user,
            status='todo'
        )
        TaskFactory(
            phase=phase_design,
            title='Revisar especificaciones',
            assigned_to=e2e_user,
            status='todo'
        )
        TaskFactory(
            phase=phase_development,
            title='Coordinar con contratistas',
            assigned_to=e2e_user,
            status='todo'
        )
        
        return {
            'project': project,
            'phases': {
                'design': phase_design,
                'development': phase_development,
                'delivery': phase_delivery
            }
        }


@pytest.fixture
def e2e_second_user(db, e2e_user, django_db_blocker):
    """
    Segundo usuario en la misma organización que e2e_user.
    Útil para tests de asignación y colaboración.
    """
    with django_db_blocker.unblock():
        user = User.objects.create_user(
            username='e2e_user2',
            email='e2e2@test.com',
            password='TestPass123!',
            first_name='Second',
            last_name='User',
            organization=e2e_user.organization,
            is_org_admin=False
        )
        return user


@pytest.fixture
def e2e_other_org_user(db, django_db_blocker):
    """
    Usuario de una organización DIFERENTE.
    Útil para tests de aislamiento entre organizaciones.
    """
    with django_db_blocker.unblock():
        from tests.factories.orgs.org_factories import OrganizationFactory
        from tests.factories.plans.plan_factories import SubscriptionFactory, BasicPlanFactory
        
        # Crear otra organización
        other_org = OrganizationFactory(name='Other Organization E2E')
        
        # Plan y suscripción para la otra org
        plan = BasicPlanFactory(max_users=5, max_storage_gb=50)
        SubscriptionFactory(organization=other_org, plan=plan, subscription_status='basic_active')
        
        user = User.objects.create_user(
            username='other_org_user',
            email='other@test.com',
            password='TestPass123!',
            first_name='Other',
            last_name='OrgUser',
            organization=other_org,
            is_org_admin=True
        )
        return user


@pytest.fixture
def logged_in_other_org_page(page: Page, live_server, e2e_other_org_user):
    """
    Página autenticada con usuario de OTRA organización.
    Para tests de aislamiento/seguridad.
    """
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector('input[name="username"], input[name="login"]', timeout=5000)
    
    username_field = page.locator('input[name="username"], input[name="login"]').first
    password_field = page.locator('input[name="password"]').first
    
    username_field.fill('other@test.com')
    password_field.fill('TestPass123!')
    
    submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
    submit_btn.click()
    
    page.wait_for_timeout(2000)
    
    return page


# ============================================================================
# HELPERS ADICIONALES
# ============================================================================

@pytest.fixture
def upload_file_helper(page: Page):
    """
    Helper para subir archivos en tests E2E.
    Maneja la interacción con el input file y la espera.
    """
    def _upload(file_path: str, input_selector: str = 'input[type="file"]', timeout: int = 10000):
        # Esperar a que el input esté disponible
        page.wait_for_selector(input_selector, timeout=timeout)
        
        # Subir archivo
        file_input = page.locator(input_selector).first
        file_input.set_input_files(file_path)
        
        # Esperar procesamiento
        page.wait_for_timeout(1000)
        
        return True
    
    return _upload


@pytest.fixture
def wait_for_toast(page: Page):
    """
    Helper para esperar y verificar mensajes toast/notificaciones.
    """
    def _wait(expected_text: str = None, timeout: int = 5000):
        # Selectores comunes para toasts/alertas
        toast_selectors = [
            '.toast',
            '.alert',
            '.notification',
            '[role="alert"]',
            '.message',
            '.django-messages li',
            '.messages li'
        ]
        
        selector = ', '.join(toast_selectors)
        
        try:
            page.wait_for_selector(selector, timeout=timeout)
            
            if expected_text:
                toast = page.locator(selector).first
                return expected_text.lower() in toast.inner_text().lower()
            return True
        except Exception:
            return False
    
    return _wait


@pytest.fixture
def navigate_to_project_phase(logged_in_page: Page, live_server):
    """
    Helper para navegar a una fase específica de un proyecto.
    """
    def _navigate(project_id: int, phase_id: int = None):
        page = logged_in_page
        
        # Ir al proyecto
        page.goto(f"{live_server.url}/projects/{project_id}/")
        page.wait_for_load_state("networkidle")
        
        if phase_id:
            # Buscar y hacer click en la fase
            phase_link = page.locator(f'[data-phase-id="{phase_id}"], a[href*="phase/{phase_id}"]')
            if phase_link.count() > 0:
                phase_link.first.click()
                page.wait_for_timeout(500)
        
        return page
    
    return _navigate


@pytest.fixture
def assert_no_console_errors(page: Page):
    """
    Helper para verificar que no hay errores en la consola del navegador.
    Útil para detectar errores JavaScript.
    """
    errors = []
    
    def handle_console(msg):
        if msg.type == 'error':
            errors.append(msg.text)
    
    page.on('console', handle_console)
    
    def _check():
        return errors
    
    return _check
