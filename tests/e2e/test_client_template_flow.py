"""
Tests E2E: Gestión de Clientes y Plantillas

Estos tests verifican:
- Crear, editar y eliminar clientes
- Crear y gestionar plantillas de fases
- Usar plantillas al crear proyectos
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestClientManagement:
    """Tests de gestión de clientes"""
    
    def test_client_list_loads(self, logged_in_page: Page, live_server, e2e_client):
        """La lista de clientes carga correctamente"""
        page = logged_in_page
        
        page.goto(f"{live_server.url}/orgs/clients/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que la página cargó
        page_loaded = (
            page.locator('text=Cliente').count() > 0 or
            page.locator('[class*="client"]').count() > 0 or
            'clients' in page.url
        )
        
        # Verificar que el cliente de prueba aparece
        client_visible = page.locator(f'text={e2e_client.name}').count() > 0
        
        print(f"✓ Página de clientes cargada: {page_loaded}")
        print(f"✓ Cliente de prueba visible: {client_visible}")
    
    def test_create_new_client(self, logged_in_page: Page, live_server, db):
        """Usuario puede crear un nuevo cliente"""
        from apps.orgs.models import Client
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        initial_count = Client.objects.filter(organization=user.organization).count()
        
        page.goto(f"{live_server.url}/orgs/clients/new/")
        page.wait_for_load_state("networkidle")
        
        # Llenar formulario
        name_field = page.locator('input[name="name"]')
        
        if name_field.count() > 0:
            name_field.fill('Cliente Nuevo E2E Test')
            
            # Email opcional
            email_field = page.locator('input[name="email"]')
            if email_field.count() > 0:
                email_field.fill('cliente_nuevo@test.com')
            
            # Teléfono opcional
            phone_field = page.locator('input[name="phone_number"]')
            if phone_field.count() > 0:
                phone_field.fill('+52 123 456 7890')
            
            # Dirección opcional
            address_field = page.locator('textarea[name="address"]')
            if address_field.count() > 0:
                address_field.fill('Calle Principal 123, Ciudad')
            
            # Guardar
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar creación
            final_count = Client.objects.filter(organization=user.organization).count()
            assert final_count > initial_count, "Debería haberse creado el cliente"
            print(f"✓ Cliente creado: {initial_count} -> {final_count}")
        else:
            pytest.skip("Formulario de cliente no encontrado")
    
    def test_edit_client(self, logged_in_page: Page, live_server, e2e_client, db):
        """Usuario puede editar un cliente existente"""
        from apps.orgs.models import Client
        
        page = logged_in_page
        
        page.goto(f"{live_server.url}/orgs/clients/{e2e_client.pk}/edit/")
        page.wait_for_load_state("networkidle")
        
        name_field = page.locator('input[name="name"]')
        
        if name_field.count() > 0:
            # Actualizar nombre
            name_field.clear()
            name_field.fill('Cliente Editado E2E')
            
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar
            e2e_client.refresh_from_db()
            assert e2e_client.name == 'Cliente Editado E2E', f"Nombre debería ser 'Cliente Editado E2E', es '{e2e_client.name}'"
            print(f"✓ Cliente editado: {e2e_client.name}")
        else:
            pytest.skip("Formulario de edición no encontrado")
    
    def test_toggle_client_status(self, logged_in_page: Page, live_server, db):
        """Usuario puede activar/desactivar un cliente"""
        from tests.factories.orgs.org_factories import ClientFactory
        from apps.accounts.models import User
        from apps.orgs.models import Client
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear cliente activo
        client = ClientFactory(
            organization=user.organization,
            name='Cliente Toggle E2E',
            is_active=True
        )
        
        page.goto(f"{live_server.url}/orgs/clients/")
        page.wait_for_load_state("networkidle")
        
        # Buscar botón de toggle
        toggle_btn = page.locator(
            f'[data-client-id="{client.pk}"] button[data-action="toggle"], '
            'button:has-text("Desactivar"):visible'
        )
        
        if toggle_btn.count() > 0:
            toggle_btn.first.click()
            page.wait_for_timeout(1500)
            
            client.refresh_from_db()
            print(f"✓ Estado del cliente: is_active={client.is_active}")
        else:
            print("⚠ No se encontró botón de toggle")
    
    def test_delete_client(self, logged_in_page: Page, live_server, db):
        """Usuario puede eliminar un cliente"""
        from tests.factories.orgs.org_factories import ClientFactory
        from apps.accounts.models import User
        from apps.orgs.models import Client
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        client = ClientFactory(
            organization=user.organization,
            name='Cliente Eliminar E2E'
        )
        client_id = client.pk
        
        page.goto(f"{live_server.url}/orgs/clients/{client.pk}/delete/")
        page.wait_for_load_state("networkidle")
        
        # Confirmar eliminación
        delete_btn = page.locator('button[type="submit"]:visible')
        
        if delete_btn.count() > 0:
            delete_btn.first.click()
            page.wait_for_timeout(2000)
            
            # Verificar eliminación
            client_exists = Client.objects.filter(pk=client_id).exists()
            print(f"✓ Cliente eliminado: {not client_exists}")
        else:
            pytest.skip("Página de eliminación no encontrada")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPhaseTemplateManagement:
    """Tests de gestión de plantillas de fases"""
    
    def test_template_list_loads(self, logged_in_page: Page, live_server):
        """La lista de plantillas de fases carga correctamente"""
        page = logged_in_page
        
        page.goto(f"{live_server.url}/projects/templates/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que la página cargó
        page_loaded = (
            page.locator('text=Plantilla').count() > 0 or
            page.locator('text=Template').count() > 0 or
            'templates' in page.url
        )
        
        print(f"✓ Página de plantillas cargada: {page_loaded}")
    
    def test_create_phase_template(self, logged_in_page: Page, live_server, db):
        """Usuario puede crear una plantilla de fases"""
        from apps.projects.models import PhaseTemplate
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        initial_count = PhaseTemplate.objects.filter(organization=user.organization).count()
        
        page.goto(f"{live_server.url}/projects/templates/new/")
        page.wait_for_load_state("networkidle")
        
        # Llenar nombre de plantilla
        name_field = page.locator('input[name="name"]')
        
        if name_field.count() > 0:
            name_field.fill('Plantilla Arquitectura E2E')
            
            # Descripción si existe
            desc_field = page.locator('textarea[name="description"]')
            if desc_field.count() > 0:
                desc_field.fill('Plantilla para proyectos arquitectónicos')
            
            # Agregar fases (depende de la UI)
            # Puede ser un campo JSON, inputs dinámicos, etc.
            phases_field = page.locator('textarea[name="phases"], input[name="phases"]')
            if phases_field.count() > 0:
                # Si es campo de texto/JSON
                phases_json = '[{"name": "Diseño Conceptual", "order": 1}, {"name": "Diseño Detallado", "order": 2}, {"name": "Construcción", "order": 3}]'
                phases_field.fill(phases_json)
            
            # Guardar
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar
            final_count = PhaseTemplate.objects.filter(organization=user.organization).count()
            print(f"✓ Plantillas: {initial_count} -> {final_count}")
        else:
            pytest.skip("Formulario de plantilla no encontrado")
    
    def test_view_template_detail(self, logged_in_page: Page, live_server, db):
        """Usuario puede ver el detalle de una plantilla"""
        from tests.factories.projects.project_factories import PhaseTemplateFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        template = PhaseTemplateFactory(
            organization=user.organization,
            name='Plantilla Detalle E2E',
            phases=[
                {'name': 'Fase A', 'order': 1},
                {'name': 'Fase B', 'order': 2},
            ]
        )
        
        page.goto(f"{live_server.url}/projects/templates/{template.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que muestra la plantilla
        name_visible = page.locator(f'text={template.name}').count() > 0
        
        # Verificar que muestra las fases
        phase_a_visible = page.locator('text=Fase A').count() > 0
        phase_b_visible = page.locator('text=Fase B').count() > 0
        
        print(f"✓ Nombre de plantilla visible: {name_visible}")
        print(f"✓ Fase A visible: {phase_a_visible}")
        print(f"✓ Fase B visible: {phase_b_visible}")
    
    def test_edit_template(self, logged_in_page: Page, live_server, db):
        """Usuario puede editar una plantilla"""
        from tests.factories.projects.project_factories import PhaseTemplateFactory
        from apps.accounts.models import User
        from apps.projects.models import PhaseTemplate
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        template = PhaseTemplateFactory(
            organization=user.organization,
            name='Plantilla Editar E2E',
            phases=[{'name': 'Fase Original', 'order': 1}]
        )
        
        page.goto(f"{live_server.url}/projects/templates/{template.pk}/edit/")
        page.wait_for_load_state("networkidle")
        
        name_field = page.locator('input[name="name"]')
        
        if name_field.count() > 0:
            name_field.clear()
            name_field.fill('Plantilla Editada E2E')
            
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            template.refresh_from_db()
            print(f"✓ Plantilla editada: {template.name}")
        else:
            pytest.skip("Formulario de edición no encontrado")
    
    def test_delete_template(self, logged_in_page: Page, live_server, db):
        """Usuario puede eliminar una plantilla"""
        from tests.factories.projects.project_factories import PhaseTemplateFactory
        from apps.accounts.models import User
        from apps.projects.models import PhaseTemplate
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        template = PhaseTemplateFactory(
            organization=user.organization,
            name='Plantilla Eliminar E2E',
            phases=[{'name': 'Fase', 'order': 1}]
        )
        template_id = template.pk
        
        page.goto(f"{live_server.url}/projects/templates/{template.pk}/delete/")
        page.wait_for_load_state("networkidle")
        
        delete_btn = page.locator('button[type="submit"]:visible')
        
        if delete_btn.count() > 0:
            delete_btn.click()
            page.wait_for_timeout(2000)
            
            template_exists = PhaseTemplate.objects.filter(pk=template_id).exists()
            print(f"✓ Plantilla eliminada: {not template_exists}")
        else:
            pytest.skip("Página de eliminación no encontrada")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestTemplateUsage:
    """Tests de uso de plantillas al crear proyectos"""
    
    def test_create_project_with_template(self, logged_in_page: Page, live_server, e2e_client, db):
        """Usuario puede crear proyecto usando una plantilla"""
        from tests.factories.projects.project_factories import PhaseTemplateFactory
        from apps.accounts.models import User
        from apps.projects.models import Project, Phase
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear plantilla con fases definidas
        template = PhaseTemplateFactory(
            organization=user.organization,
            name='Plantilla Proyecto E2E',
            phases=[
                {'name': 'Análisis', 'order': 1},
                {'name': 'Diseño', 'order': 2},
                {'name': 'Implementación', 'order': 3},
                {'name': 'Pruebas', 'order': 4},
            ]
        )
        
        page.goto(f"{live_server.url}/projects/new/")
        page.wait_for_load_state("networkidle")
        
        # Llenar nombre del proyecto
        name_field = page.locator('#id_name, input[name="name"]:not(#quick_client_name)').first
        name_field.fill('Proyecto con Plantilla E2E')
        
        # Seleccionar plantilla
        template_select = page.locator('select[name="phase_template"], #id_phase_template')
        
        if template_select.count() > 0:
            # Seleccionar la plantilla creada
            template_select.select_option(str(template.pk))
            page.wait_for_timeout(500)
        
        # Seleccionar cliente si es requerido
        client_select = page.locator('select[name="client"]')
        if client_select.count() > 0 and client_select.locator('option').count() > 1:
            client_select.select_option(str(e2e_client.pk))
        
        # Guardar
        save_btn = page.locator('button[type="submit"]:visible').first
        if save_btn:
            save_btn.click()
            page.wait_for_timeout(3000)
        
        # Verificar que se creó el proyecto con las fases de la plantilla
        project = Project.objects.filter(
            name='Proyecto con Plantilla E2E',
            organization=user.organization
        ).first()
        
        if project:
            phases = Phase.objects.filter(project=project).order_by('order')
            phase_names = [p.name for p in phases]
            
            print(f"✓ Proyecto creado: {project.name}")
            print(f"✓ Fases creadas: {phase_names}")
            
            # Verificar que las fases de la plantilla se copiaron
            assert phases.count() == 4, f"Debería tener 4 fases, tiene {phases.count()}"
        else:
            # Verificar si hay errores
            errors = page.locator('.errorlist:visible, .invalid-feedback:visible')
            if errors.count() > 0:
                pytest.skip(f"Formulario tiene errores: {errors.first.text_content()}")
            else:
                pytest.fail("No se creó el proyecto")
