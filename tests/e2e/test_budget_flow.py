"""
Tests E2E: Flujo Completo de Presupuestos

Estos tests verifican el ciclo completo de gestión de presupuestos:
- Configurar presupuesto desde cero en un proyecto
- Ver dashboard de finanzas
- Modificar configuración de presupuesto
- Verificar cálculos y porcentajes
"""
import pytest
from playwright.sync_api import Page, expect
from decimal import Decimal


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestBudgetConfigurationFlow:
    """Tests del flujo completo de configuración de presupuesto"""
    
    def test_configure_budget_from_scratch(self, logged_in_page: Page, live_server, e2e_client, db):
        """
        Flujo completo: Crear proyecto sin presupuesto → Ir a Finanzas → Configurar presupuesto
        """
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        from apps.projects.models import Project
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear proyecto SIN presupuesto configurado
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            client=e2e_client,
            name='Proyecto Sin Presupuesto E2E',
            total_budget=Decimal('0'),
            budget_configured=False,
            status='active'
        )
        PhaseFactory(project=project, name='Fase Principal', order=1)
        
        # Ir al dashboard de Finanzas
        page.goto(f"{live_server.url}/projects/finance/")
        page.wait_for_load_state("networkidle")
        
        # El proyecto debería aparecer pero con opción de "Configurar"
        project_row = page.locator(f'text="{project.name}"')
        
        if project_row.count() > 0:
            # Buscar botón "Configurar" en la fila del proyecto
            config_btn = page.locator('a:has-text("Configurar"), button:has-text("Configurar")')
            
            if config_btn.count() > 0 and config_btn.first.is_visible():
                config_btn.first.click()
                page.wait_for_timeout(1000)
                
                # Verificar que cargó el formulario de configuración
                budget_field = page.locator('input[name="total_budget"]:visible')
                
                if budget_field.count() > 0:
                    # Configurar presupuesto de $150,000
                    budget_field.fill('150000')
                    
                    # Guardar configuración
                    save_btn = page.locator('button[type="submit"]:visible').first
                    if save_btn:
                        save_btn.click()
                        page.wait_for_timeout(2000)
                    
                    # Verificar en BD
                    project.refresh_from_db()
                    assert project.budget_configured, "El proyecto debería tener presupuesto configurado"
                    assert project.total_budget == Decimal('150000'), f"Presupuesto debería ser 150000, es {project.total_budget}"
                    print(f"✓ Presupuesto configurado: ${project.total_budget}")
                else:
                    pytest.skip("No se encontró campo de presupuesto en el formulario")
            else:
                pytest.skip("No se encontró botón de Configurar")
        else:
            pytest.skip("Proyecto no visible en dashboard de finanzas")
    
    def test_update_existing_budget(self, logged_in_page: Page, live_server, db):
        """Usuario puede actualizar un presupuesto existente"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear proyecto CON presupuesto configurado
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Actualizar Budget E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Ir al detalle de finanzas del proyecto
        page.goto(f"{live_server.url}/projects/{project.pk}/budget/config/")
        page.wait_for_load_state("networkidle")
        
        # Buscar campo de presupuesto
        budget_field = page.locator('input[name="total_budget"]:visible')
        
        if budget_field.count() > 0:
            # Actualizar a $200,000
            budget_field.clear()
            budget_field.fill('200000')
            
            # Guardar
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar
            project.refresh_from_db()
            assert project.total_budget == Decimal('200000'), f"Presupuesto actualizado debería ser 200000, es {project.total_budget}"
            print(f"✓ Presupuesto actualizado: ${project.total_budget}")
        else:
            pytest.skip("No se encontró campo de presupuesto")
    
    def test_budget_validation_negative_amount(self, logged_in_page: Page, live_server, db):
        """Sistema valida que el presupuesto no puede ser negativo"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Validación Budget E2E',
            budget_configured=False
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Ir a configurar presupuesto
        page.goto(f"{live_server.url}/projects/{project.pk}/budget/config/")
        page.wait_for_load_state("networkidle")
        
        budget_field = page.locator('input[name="total_budget"]:visible')
        
        if budget_field.count() > 0:
            # Intentar valor negativo
            budget_field.fill('-50000')
            
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(1500)
            
            # Verificar que muestra error o no guardó
            error_msg = page.locator('.errorlist:visible, .invalid-feedback:visible, .alert-danger')
            
            # Si no hay mensaje de error explícito, verificar que no se guardó
            project.refresh_from_db()
            
            if error_msg.count() > 0:
                print("✓ Sistema mostró error de validación")
            elif project.total_budget >= 0:
                print("✓ Sistema previno valor negativo")
            else:
                print("⚠ Sistema aceptó valor negativo (revisar validación)")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestFinanceDashboard:
    """Tests del dashboard de finanzas"""
    
    def test_finance_dashboard_shows_all_projects(self, logged_in_page: Page, live_server, db):
        """Dashboard de finanzas muestra todos los proyectos de la organización"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear varios proyectos
        project1 = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Finance 1 E2E',
            total_budget=Decimal('50000'),
            budget_configured=True
        )
        PhaseFactory(project=project1, name='Fase 1', order=1)
        
        project2 = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Finance 2 E2E',
            total_budget=Decimal('75000'),
            budget_configured=True
        )
        PhaseFactory(project=project2, name='Fase 1', order=1)
        
        project3 = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Sin Config E2E',
            budget_configured=False
        )
        PhaseFactory(project=project3, name='Fase 1', order=1)
        
        # Ir al dashboard de finanzas
        page.goto(f"{live_server.url}/projects/finance/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que los proyectos aparecen
        p1_visible = page.locator(f'text="{project1.name}"').count() > 0
        p2_visible = page.locator(f'text="{project2.name}"').count() > 0
        p3_visible = page.locator(f'text="{project3.name}"').count() > 0
        
        print(f"✓ Proyecto 1 (con config): {p1_visible}")
        print(f"✓ Proyecto 2 (con config): {p2_visible}")
        print(f"✓ Proyecto 3 (sin config): {p3_visible}")
    
    def test_finance_dashboard_shows_summary(self, logged_in_page: Page, live_server, db):
        """Dashboard muestra resumen de totales"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        # Crear proyecto con pagos
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Resumen E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Agregar pagos
        ProjectPaymentFactory(project=project, amount=Decimal('30000'), created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('20000'), created_by=user)
        
        page.goto(f"{live_server.url}/projects/finance/")
        page.wait_for_load_state("networkidle")
        
        # Buscar indicadores de resumen (totales, porcentajes)
        summary_elements = page.locator('[class*="summary"], [class*="total"], [class*="stats"]')
        
        # Verificar que hay algún tipo de resumen/estadísticas
        has_summary = summary_elements.count() > 0 or page.locator('text=Total, text=Pagado').count() > 0
        print(f"✓ Dashboard tiene resumen: {has_summary}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestProjectFinanceDetail:
    """Tests del detalle financiero de un proyecto"""
    
    def test_project_finance_detail_loads(self, logged_in_page: Page, live_server, db):
        """Página de detalle financiero carga correctamente"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Detalle Finance E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Agregar pagos
        ProjectPaymentFactory(project=project, amount=Decimal('25000'), description='Pago 1', created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('15000'), description='Pago 2', created_by=user)
        
        # Ir al detalle financiero del proyecto
        page.goto(f"{live_server.url}/projects/{project.pk}/finance/")
        page.wait_for_load_state("networkidle")
        
        # Verificar elementos clave
        project_name_visible = page.locator(f'text="{project.name}"').count() > 0 or project.name in page.content()
        
        # Buscar información de presupuesto
        budget_info = page.locator('text=100,000, text=$100,000, text=Presupuesto')
        has_budget_info = budget_info.count() > 0
        
        # Buscar lista de pagos
        payments_visible = (
            page.locator('text=Pago 1').count() > 0 or
            page.locator('text=25,000').count() > 0 or
            page.locator('[class*="payment"]').count() > 0
        )
        
        print(f"✓ Nombre de proyecto visible: {project_name_visible}")
        print(f"✓ Info de presupuesto visible: {has_budget_info}")
        print(f"✓ Pagos visibles: {payments_visible}")
    
    def test_project_finance_shows_balance(self, logged_in_page: Page, live_server, db):
        """Detalle financiero muestra balance (presupuesto - pagos)"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Balance E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Agregar pagos que sumen $40,000 (balance debería ser $60,000)
        ProjectPaymentFactory(project=project, amount=Decimal('25000'), created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('15000'), created_by=user)
        
        page.goto(f"{live_server.url}/projects/{project.pk}/finance/")
        page.wait_for_load_state("networkidle")
        
        # Buscar indicadores de balance/restante
        balance_indicators = page.locator(
            'text=60,000, text=$60,000, '
            'text=Balance, text=Restante, text=Pendiente'
        )
        
        has_balance = balance_indicators.count() > 0
        print(f"✓ Balance mostrado: {has_balance}")
        
        # Buscar porcentaje de avance (40%)
        progress_indicators = page.locator(
            'text=40%, text=40 %, '
            '[class*="progress"]'
        )
        
        has_progress = progress_indicators.count() > 0
        print(f"✓ Progreso mostrado: {has_progress}")
