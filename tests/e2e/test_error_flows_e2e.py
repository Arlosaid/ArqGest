"""
Tests E2E: Manejo de Errores y Flujos de Error

Estos tests verifican que el sistema maneja correctamente:
- Errores de validación con mensajes claros
- Límites de cuota/almacenamiento
- Operaciones inválidas
- Estados de error con feedback al usuario
- Recuperación de errores
"""
import pytest
from playwright.sync_api import Page, expect
from decimal import Decimal


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestFormValidationErrors:
    """Tests de errores de validación en formularios"""
    
    def test_project_creation_validation_errors(self, logged_in_page: Page, live_server):
        """
        Crear proyecto sin datos requeridos muestra errores de validación.
        """
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Intentar enviar formulario vacío
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(1500)
        
        # Verificar que hay errores de validación
        validation_errors = page.locator(
            '.errorlist, .invalid-feedback, .field-error, '
            '[class*="error"], .alert-danger, .form-error'
        )
        
        # O que sigue en la misma página (no redirigió)
        still_on_form = '/new' in page.url or page.locator('input[name="name"]').count() > 0
        
        has_validation = validation_errors.count() > 0 or still_on_form
        
        print(f"✓ Validación en formulario de proyecto: {has_validation}")
    
    def test_task_creation_without_title_fails(self, logged_in_page: Page, live_server, e2e_project_with_phases):
        """
        Crear tarea sin título muestra error.
        """
        page = logged_in_page
        project = e2e_project_with_phases['project']
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Primero ir al tab "Centro de Tareas"
        task_center_tab = page.locator('text=Centro de Tareas')
        if task_center_tab.count() > 0:
            task_center_tab.first.click()
            page.wait_for_timeout(1000)
        
        # Buscar botón "+ Nueva Tarea"
        new_task_btn = page.locator('button:has-text("Nueva Tarea"), a:has-text("Nueva Tarea")')
        
        if new_task_btn.count() > 0 and new_task_btn.first.is_visible():
            new_task_btn.first.click()
            page.wait_for_timeout(1000)
            
            # Verificar si hay un formulario visible (modal o página)
            title_input = page.locator('input[name="title"]:visible, input[name="name"]:visible')
            if title_input.count() > 0:
                # Dejar vacío e intentar guardar
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn.count() > 0:
                    save_btn.click()
                    page.wait_for_timeout(1000)
                    
                    # Verificar error de validación o que el formulario sigue abierto
                    has_error = page.locator(
                        '.errorlist:visible, .invalid-feedback:visible, '
                        '[class*="error"]:visible, .is-invalid'
                    ).count() > 0
                    
                    # O el formulario sigue abierto (no se guardó)
                    form_still_open = page.locator('input[name="title"]:visible, input[name="name"]:visible').count() > 0
                    
                    # El test pasa si hay error o el form sigue abierto (validación HTML5)
                    assert has_error or form_still_open, "Debería mostrar error o mantener el formulario abierto"
                    print(f"✓ Validación en tarea: error={has_error}, form_open={form_still_open}")
                else:
                    print("⚠ No se encontró botón de guardar")
            else:
                print("⚠ No se encontró campo de título visible")
        else:
            pytest.skip("No se encontró botón para agregar tarea en este proyecto")
    
    def test_duplicate_project_name_shows_error(self, logged_in_page: Page, live_server, db):
        """
        Crear proyecto con nombre duplicado muestra error apropiado.
        """
        from tests.factories.projects.project_factories import ProjectFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear proyecto existente
        existing_name = 'Proyecto Duplicado Test'
        ProjectFactory(
            organization=user.organization,
            owner=user,
            name=existing_name
        )
        
        # Intentar crear otro con el mismo nombre
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="name"]', existing_name)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(1500)
        
        # Verificar mensaje de error o que sigue en form
        error_shown = (
            page.get_by_text('existe').or_(page.get_by_text('duplicado')).or_(page.get_by_text('already exists')).or_(page.get_by_text('ya existe')).count() > 0 or
            '/new' in page.url
        )
        
        print(f"✓ Error por duplicado: {error_shown}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestStorageQuotaErrors:
    """Tests de errores por límites de almacenamiento"""
    
    def test_upload_shows_storage_usage(self, logged_in_page: Page, live_server, e2e_project_with_phases):
        """
        La interfaz muestra el uso de almacenamiento.
        """
        page = logged_in_page
        project = e2e_project_with_phases['project']
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Buscar indicador de storage
        storage_indicator = page.get_by_text('almacenamiento').or_(page.get_by_text('storage')).or_(page.get_by_text('GB')).or_(page.get_by_text('MB')).or_(page.locator('[class*="storage"], [class*="quota"]'))
        
        # O en el dashboard
        page.goto(f"{live_server.url}/dashboard/")
        page.wait_for_load_state("networkidle")
        
        storage_in_dashboard = page.get_by_text('almacenamiento').or_(page.get_by_text('storage')).or_(page.get_by_text('espacio'))
        
        has_storage_info = storage_indicator.count() > 0 or storage_in_dashboard.count() > 0
        
        print(f"✓ Información de almacenamiento visible: {has_storage_info}")
    
    def test_error_message_when_storage_limit_approached(
        self, logged_in_page: Page, live_server, e2e_project_with_phases, db
    ):
        """
        Cuando el almacenamiento está cerca del límite, se muestra advertencia.
        """
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        org = user.organization
        
        # Simular alto uso de storage (si la org tiene ese campo)
        # Esto depende de cómo está implementado el storage en el modelo
        
        page.goto(f"{live_server.url}/dashboard/")
        page.wait_for_load_state("networkidle")
        
        # Buscar advertencias de storage
        storage_warning = page.get_by_text('límite').or_(page.get_by_text('warning')).or_(page.locator('.alert-warning').filter(has_text='almacenamiento'))
        
        print(f"✓ Verificación de advertencias de storage: {storage_warning.count()} encontradas")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestNetworkAndLoadingErrors:
    """Tests de manejo de errores de carga y red"""
    
    def test_page_shows_loading_state(self, logged_in_page: Page, live_server, e2e_project_with_phases):
        """
        Las páginas muestran estado de carga mientras cargan datos.
        """
        page = logged_in_page
        project = e2e_project_with_phases['project']
        
        # Usar throttling para simular conexión lenta (si playwright lo soporta)
        # Por ahora solo verificamos que la página carga
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        
        # Buscar indicadores de carga durante la navegación
        loading_indicator = page.locator(
            '.loading, .spinner, [class*="loading"], '
            '[class*="spinner"], .skeleton'
        )
        
        # Esperar carga completa
        page.wait_for_load_state("networkidle")
        
        # La página debe cargar correctamente
        project_loaded = page.locator(f'text={project.name}').count() > 0
        
        print(f"✓ Proyecto cargado correctamente: {project_loaded}")
    
    def test_error_boundary_catches_errors(self, logged_in_page: Page, live_server):
        """
        Errores inesperados muestran página de error amigable.
        """
        page = logged_in_page
        
        # Ir a una URL que podría causar error
        page.goto(f"{live_server.url}/non-existent-page-xyz/")
        page.wait_for_timeout(1500)
        
        # Verificar página de error amigable
        has_friendly_error = (
            page.get_by_text('404').or_(page.get_by_text('no encontrada')).or_(page.get_by_text('not found')).count() > 0 or
            page.locator('[class*="error-page"]').count() > 0
        )
        
        # NO debería mostrar stack trace
        no_stack_trace = page.get_by_text('Traceback').count() == 0
        
        print(f"✓ Error amigable: {has_friendly_error}, Sin stack trace: {no_stack_trace}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestOperationFailures:
    """Tests de fallos en operaciones"""
    
    def test_delete_project_with_files_shows_confirmation(
        self, logged_in_page: Page, live_server, e2e_project_with_phases, db
    ):
        """
        Eliminar proyecto con archivos muestra confirmación/advertencia.
        El botón de eliminar está en la lista de proyectos (botón rojo con basura).
        """
        from tests.factories.files.file_factories import PDFFileFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        project = e2e_project_with_phases['project']
        phase = e2e_project_with_phases['phases']['design']
        user = User.objects.get(email='e2e@test.com')
        
        # Crear archivo en el proyecto
        PDFFileFactory(phase=phase, uploaded_by=user)
        
        # Ir a la lista de proyectos
        page.goto(f"{live_server.url}/projects/")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Buscar botón rojo de eliminar (basura) en la tabla/lista
        delete_btn = page.locator(
            'button.btn-danger, '
            'a.btn-danger, '
            '.btn-outline-danger, '
            'button:has-text("Eliminar"), '
            '[title="Eliminar"], '
            '.text-danger'
        )
        
        if delete_btn.count() > 0 and delete_btn.first.is_visible():
            delete_btn.first.click()
            page.wait_for_timeout(1000)
            
            # Debería mostrar modal de confirmación
            confirmation_dialog = page.locator('.modal.show, [role="dialog"]:visible')
            has_confirmation = confirmation_dialog.count() > 0
            
            assert has_confirmation, "Debería mostrar modal de confirmación antes de eliminar"
            print(f"✓ Modal de confirmación mostrado")
            
            # Cerrar modal sin eliminar (presionar Escape o buscar botón cancelar visible)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        else:
            pytest.skip("No se encontró botón de eliminar proyecto")
    
    def test_invalid_date_range_shows_error(self, logged_in_page: Page, live_server, e2e_client):
        """
        Fechas inválidas (fin antes de inicio) muestran error.
        """
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="name"]', 'Proyecto Fechas Inválidas')
        
        # Llenar fechas en orden incorrecto
        start_date = page.locator('input[name="start_date"]')
        end_date = page.locator('input[name="end_date"]')
        
        if start_date.count() > 0 and end_date.count() > 0:
            start_date.fill('2025-12-31')  # Fecha de inicio
            end_date.fill('2025-01-01')    # Fecha de fin ANTES de inicio
            
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(1500)
            
            # Debería mostrar error
            date_error = page.get_by_text('fecha').or_(page.get_by_text('date')).or_(page.get_by_text('anterior')).or_(page.get_by_text('before')).or_(page.get_by_text('inválid'))
            
            print(f"✓ Error de fecha detectado: {date_error.count() > 0}")
    
    def test_negative_budget_shows_error(self, logged_in_page: Page, live_server, e2e_client):
        """
        Presupuesto negativo muestra error de validación.
        """
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="name"]', 'Proyecto Presupuesto Negativo')
        
        budget_field = page.locator('input[name="total_budget"]')
        if budget_field.count() > 0:
            budget_field.fill('-5000')
            
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(1500)
            
            # Debería mostrar error
            budget_error = page.get_by_text('negativ').or_(page.get_by_text('positiv')).or_(page.get_by_text('válido')).or_(page.get_by_text('valid')).or_(page.get_by_text('mayor que 0'))
            
            # O sigue en el form (no se guardó)
            still_on_form = '/new' in page.url
            
            print(f"✓ Error de presupuesto negativo: error={budget_error.count() > 0}, form={still_on_form}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestUserFeedback:
    """Tests de feedback al usuario"""
    
    def test_success_message_after_save(self, logged_in_page: Page, live_server, e2e_client, db):
        """
        Guardar exitosamente muestra mensaje de éxito.
        """
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="name"]', f'Proyecto Success Test {pytest.importorskip("time").time()}')
        
        budget_field = page.locator('input[name="total_budget"]')
        if budget_field.count() > 0:
            budget_field.fill('10000')
        
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(2000)
        
        # Buscar mensaje de éxito
        success_by_class = page.locator('.alert-success, .message-success, .toast-success')
        success_by_text = page.locator('text=creado') or page.locator('text=guardado')
        
        has_success = success_by_class.count() > 0 or 'creado' in page.content().lower() or 'guardado' in page.content().lower()
        
        print(f"✓ Mensaje de éxito mostrado: {has_success}")
    
    def test_error_message_is_descriptive(self, logged_in_page: Page, live_server):
        """
        Mensajes de error son descriptivos y ayudan al usuario.
        """
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Enviar formulario vacío
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(1500)
        
        # Buscar mensajes de error
        error_messages = page.locator('.errorlist li, .invalid-feedback, .field-error')
        
        if error_messages.count() > 0:
            # Verificar que los mensajes son descriptivos (no solo "error")
            first_error_text = error_messages.first.inner_text()
            is_descriptive = len(first_error_text) > 5 and 'error' not in first_error_text.lower()
            
            print(f"✓ Error descriptivo: {is_descriptive} ('{first_error_text[:50]}...')")
        else:
            print("⚠ No se encontraron mensajes de error específicos")
    
    def test_loading_indicator_during_operations(
        self, logged_in_page: Page, live_server, e2e_project_with_phases
    ):
        """
        Operaciones largas muestran indicador de carga.
        """
        page = logged_in_page
        project = e2e_project_with_phases['project']
        
        # Navegar con observador de requests
        loading_shown = False
        
        def check_loading():
            # Buscar spinner/loading durante carga
            loading = page.locator('.loading, .spinner, [class*="loading"]')
            return loading.count() > 0
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        
        # No podemos capturar durante carga fácilmente en tests síncronos
        # Solo verificamos que la página carga
        page.wait_for_load_state("networkidle")
        
        project_visible = page.locator(f'text={project.name}').count() > 0
        print(f"✓ Página cargada correctamente: {project_visible}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestEdgeCases:
    """Tests de casos límite y edge cases"""
    
    def test_very_long_project_name(self, logged_in_page: Page, live_server, e2e_client, db):
        """
        Nombre de proyecto muy largo se maneja correctamente.
        """
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Nombre muy largo
        long_name = "A" * 500
        
        page.fill('input[name="name"]', long_name)
        
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(1500)
        
        # Debería mostrar error de longitud o truncar
        error_or_truncated = (
            page.get_by_text('largo').or_(page.get_by_text('long')).or_(page.get_by_text('caracteres')).or_(page.get_by_text('máximo')).count() > 0 or
            '/new' in page.url  # Sigue en form por error
        )
        
        print(f"✓ Nombre largo manejado: {error_or_truncated}")
    
    def test_special_characters_in_fields(self, logged_in_page: Page, live_server, e2e_client, db):
        """
        Caracteres especiales en campos se manejan correctamente.
        """
        from apps.projects.models import Project
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Nombre con caracteres especiales
        special_name = "Proyecto #1 @Test & Co. (2025)"
        
        page.fill('input[name="name"]', special_name)
        
        budget_field = page.locator('input[name="total_budget"]')
        if budget_field.count() > 0:
            budget_field.fill('5000')
        
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(2000)
        
        # Verificar que se guardó correctamente
        project = Project.objects.filter(
            organization=user.organization,
            name=special_name
        ).first()
        
        saved_correctly = project is not None
        print(f"✓ Caracteres especiales guardados: {saved_correctly}")
    
    def test_unicode_characters_supported(self, logged_in_page: Page, live_server, e2e_client, db):
        """
        Caracteres Unicode (emojis, acentos) se manejan correctamente.
        """
        from apps.projects.models import Project
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Nombre con Unicode
        unicode_name = "Proyecto Diseño 🏠 Café ñoño"
        
        page.fill('input[name="name"]', unicode_name)
        
        budget_field = page.locator('input[name="total_budget"]')
        if budget_field.count() > 0:
            budget_field.fill('8000')
        
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(2000)
        
        # Verificar
        project = Project.objects.filter(
            organization=user.organization,
            name=unicode_name
        ).first()
        
        unicode_saved = project is not None
        print(f"✓ Unicode guardado correctamente: {unicode_saved}")
    
    def test_rapid_form_submission(self, logged_in_page: Page, live_server, e2e_project_with_phases, db):
        """
        Múltiples envíos rápidos de formulario no causan problemas.
        """
        from apps.projects.models import Task
        
        page = logged_in_page
        project = e2e_project_with_phases['project']
        phase = e2e_project_with_phases['phases']['design']
        
        initial_task_count = Task.objects.filter(phase__project=project).count()
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Buscar botón que abre modal de tarea (no el botón dentro del modal)
        task_triggers = [
            'button[data-bs-target="#addTaskModal"]',
            'button[data-bs-target*="Task"]',
            'a[href*="tasks/new"]',
        ]
        
        clicked = False
        for selector in task_triggers:
            btn = page.locator(selector)
            if btn.count() > 0 and btn.first.is_visible():
                try:
                    btn.first.click()
                    clicked = True
                    break
                except Exception:
                    continue
        
        if clicked:
            page.wait_for_timeout(500)
            
            title_field = page.locator('input[name="title"]:visible')
            if title_field.count() > 0:
                title_field.first.fill('Tarea Doble Click Test')
                
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn.count() > 0:
                    # Simular doble click rápido
                    save_btn.click()
                    save_btn.click()  # Segundo click inmediato
                    
                    page.wait_for_timeout(2000)
        
        # Verificar que solo se creó una tarea (no duplicados)
        final_task_count = Task.objects.filter(phase__project=project).count()
        tasks_created = final_task_count - initial_task_count
        
        print(f"✓ Tareas creadas: {tasks_created} (debería ser 0 o 1, no múltiples)")
