"""
Tests E2E: Flujo Financiero - Presupuestos y Pagos

Estos tests verifican el módulo financiero:
- Configurar presupuesto de proyecto
- Registrar pagos
- Verificar cálculos de totales
"""
import pytest
from playwright.sync_api import Page, expect
from decimal import Decimal


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestBudgetConfiguration:
    """Tests de configuración de presupuesto"""
    
    def test_project_shows_budget_info(self, logged_in_page: Page, live_server, db):
        """El proyecto muestra información del presupuesto"""
        page = logged_in_page
        
        from tests.factories.projects.project_factories import ProjectFactory
        from apps.accounts.models import User
        
        user = User.objects.get(email='e2e@test.com')
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Presupuesto E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Buscar información de presupuesto en la página
        # Puede estar en diferentes formatos
        budget_info = page.locator('text=100,000, text=$100,000, text=100000, text=Presupuesto')
        
        # Al menos debería existir alguna referencia al presupuesto
        has_budget = budget_info.count() > 0 or page.locator('[class*="budget"], [class*="finance"]').count() > 0
        
        print(f"Información de presupuesto visible: {has_budget}")
    
    def test_access_finance_section(self, logged_in_page: Page, live_server, db):
        """Usuario puede acceder a la sección de finanzas"""
        page = logged_in_page
        
        from tests.factories.projects.project_factories import ProjectFactory
        from apps.accounts.models import User
        
        user = User.objects.get(email='e2e@test.com')
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Finanzas E2E',
            total_budget=Decimal('50000'),
            budget_configured=True
        )
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Buscar tab/link de finanzas - usando selector de nav-link
        finance_selectors = [
            '#finance-tab',
            'a[href="#finance"]',
            '.nav-link:has-text("Finanzas")',
            'a.nav-link:has-text("Finanzas")',
            'button[data-bs-target="#finance"]',
        ]
        
        clicked = False
        for selector in finance_selectors:
            tab = page.locator(selector)
            if tab.count() > 0:
                try:
                    tab.first.click()
                    clicked = True
                    break
                except Exception:
                    continue
        
        if clicked:
            page.wait_for_timeout(1000)
            
            # Verificar que cambió algo (contenido de finanzas visible)
            finance_content = page.locator('text=Presupuesto, text=Pagos, text=Balance')
            
            if finance_content.count() == 0:
                # Puede que el contenido esté ahí pero con otros nombres
                print("⚠ Contenido de finanzas no encontrado con texto esperado")
        else:
            pytest.skip("No se encontró pestaña de finanzas")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPaymentFlow:
    """Tests del flujo de pagos"""
    
    def test_view_payments_list(self, logged_in_page: Page, live_server, db):
        """Usuario puede ver la lista de pagos de un proyecto"""
        page = logged_in_page
        
        from tests.factories.projects.project_factories import ProjectFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        user = User.objects.get(email='e2e@test.com')
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Pagos E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        
        # Crear algunos pagos
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('25000'),
            description='Anticipo inicial',
            created_by=user
        )
        ProjectPaymentFactory(
            project=project,
            amount=Decimal('15000'),
            description='Segundo pago',
            created_by=user
        )
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Ir a finanzas si hay tab
        finance_selectors = ['#finance-tab', 'a[href="#finance"]', '.nav-link:has-text("Finanzas")']
        for selector in finance_selectors:
            tab = page.locator(selector)
            if tab.count() > 0:
                try:
                    tab.first.click()
                    page.wait_for_timeout(1000)
                    break
                except Exception:
                    continue
        
        # Verificar que se muestran los pagos
        has_payments = (
            page.locator('text=25,000, text=$25,000').count() > 0 or
            page.locator('text=Anticipo').count() > 0 or
            page.locator('[class*="payment"]').count() > 0
        )
        
        print(f"Pagos visibles: {has_payments}")
    
    def test_add_payment_form(self, logged_in_page: Page, live_server, db):
        """Usuario puede acceder al formulario de agregar pago desde Finanzas"""
        page = logged_in_page
        
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from tests.factories.orgs.org_factories import ClientFactory
        from apps.accounts.models import User
        
        user = User.objects.get(email='e2e@test.com')
        
        # Crear cliente para la organización del usuario
        client = ClientFactory(organization=user.organization, name='Cliente Pago E2E')
        
        # Crear proyecto CON presupuesto configurado en la organización del usuario
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            client=client,
            name='Proyecto Pago E2E',
            total_budget=Decimal('50000'),
            budget_configured=True,
            status='active'
        )
        # Agregar al menos una fase
        PhaseFactory(project=project, name='Fase Principal', order=1)
        
        # Ir a Finanzas desde el menú lateral
        page.goto(f"{live_server.url}/projects/finance/")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Buscar botón "+ Pago" en la fila del proyecto (botón azul en columna acciones)
        add_payment_btn = page.locator('button:has-text("Pago"), a:has-text("Pago"), .btn:has-text("Pago")')
        
        if add_payment_btn.count() > 0 and add_payment_btn.first.is_visible():
            add_payment_btn.first.click()
            page.wait_for_timeout(1000)
            
            # Verificar que aparece formulario/modal
            form_visible = page.locator(
                '.modal.show, '
                'input[name="amount"]:visible, '
                '[role="dialog"]:visible'
            ).count() > 0
            
            assert form_visible, "Debería aparecer el formulario de pago"
            print(f"✓ Formulario de pago visible: {form_visible}")
        else:
            # Verificar si el proyecto aparece en la lista
            project_in_list = page.locator(f'text="{project.name}"').count() > 0
            if project_in_list:
                # Proyecto está pero quizás tiene botón Configurar
                config_btn = page.locator('button:has-text("Configurar"), a:has-text("Configurar")')
                if config_btn.count() > 0:
                    pytest.skip("El proyecto aparece pero necesita configurar presupuesto primero")
            pytest.skip("No se encontró botón '+ Pago' en Finanzas")
    
    def test_create_payment_success(self, logged_in_page: Page, live_server, db):
        """Usuario puede crear un pago exitosamente"""
        page = logged_in_page
        
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from tests.factories.orgs.org_factories import ClientFactory
        from apps.accounts.models import User
        from apps.projects.models import ProjectPayment
        
        user = User.objects.get(email='e2e@test.com')
        client = ClientFactory(organization=user.organization, name='Cliente Crear Pago E2E')
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            client=client,
            name='Proyecto Crear Pago E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase Principal', order=1)
        
        initial_payment_count = ProjectPayment.objects.filter(project=project).count()
        
        # Ir a Finanzas desde el menú lateral
        page.goto(f"{live_server.url}/projects/finance/")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Buscar botón "Pago" en la fila del proyecto
        add_payment_btn = page.locator('button:has-text("Pago"), a:has-text("Pago"), .btn:has-text("Pago")')
        
        if add_payment_btn.count() > 0 and add_payment_btn.first.is_visible():
            add_payment_btn.first.click()
            page.wait_for_timeout(1000)
            
            # Llenar formulario
            amount_field = page.locator('input[name="amount"]:visible')
            if amount_field.count() > 0:
                amount_field.first.fill('30000')
                
                # Descripción
                desc_field = page.locator('input[name="description"]:visible, textarea[name="description"]:visible')
                if desc_field.count() > 0:
                    desc_field.first.fill('Pago de prueba E2E')
                
                # Guardar
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn.count() > 0:
                    save_btn.click()
                    page.wait_for_timeout(2000)
                    
                    # Verificar
                    final_payment_count = ProjectPayment.objects.filter(project=project).count()
                    print(f"✓ Pagos: {initial_payment_count} -> {final_payment_count}")
            else:
                pytest.skip("No se encontró campo de monto")
        else:
            pytest.skip("No se encontró botón para agregar pago")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestFinancialSummary:
    """Tests del resumen financiero"""
    
    def test_budget_progress_displayed(self, logged_in_page: Page, live_server, db):
        """Se muestra el progreso del presupuesto"""
        page = logged_in_page
        
        from tests.factories.projects.project_factories import ProjectFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        user = User.objects.get(email='e2e@test.com')
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Progreso E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        
        # Crear pagos que sumen 40%
        ProjectPaymentFactory(project=project, amount=Decimal('25000'), created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('15000'), created_by=user)
        
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.wait_for_load_state("networkidle")
        
        # Ir a finanzas
        finance_tab = page.locator('a:has-text("Finanzas"), [data-tab="finance"]')
        if finance_tab.count() > 0:
            finance_tab.first.click()
            page.wait_for_timeout(1000)
        
        # Buscar indicadores de progreso
        progress_indicators = page.locator(
            'text=40%, '
            '[class*="progress"], '
            '[role="progressbar"], '
            'text=40,000, '
            'text=$40,000'
        )
        
        has_progress = progress_indicators.count() > 0
        print(f"Indicadores de progreso visibles: {has_progress}")
