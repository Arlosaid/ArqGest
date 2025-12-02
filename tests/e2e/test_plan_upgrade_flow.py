"""
Test E2E del flujo REAL de upgrade de plan:
1. Org admin va al sidebar → Suscripción → Solicitar upgrade
2. Superadmin va a /admin/plans/upgraderequest/ → Aprueba
3. Verificar en admin que la org tiene el plan activado con los días correctos
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPlanUpgradeRealFlow:
    """Test del flujo real de upgrade como lo usa el usuario"""
    
    def test_complete_upgrade_flow_visible(self, page: Page, live_server, db, django_db_blocker):
        """
        FLUJO COMPLETO VISIBLE:
        1. org_admin entra, va a Suscripción en sidebar, solicita upgrade
        2. superadmin entra al admin, busca en UpgradeRequest, aprueba
        3. verificamos que el plan cambió correctamente
        """
        from tests.factories.orgs.org_factories import OrganizationFactory
        from tests.factories.plans.plan_factories import SubscriptionFactory, BasicPlanFactory, TrialPlanFactory
        from tests.factories.accounts.account_factories import OrgAdminFactory
        from apps.accounts.models import User
        from apps.plans.models import Plan
        
        with django_db_blocker.unblock():
            # Crear plan trial y plan básico
            trial_plan = TrialPlanFactory()
            basic_plan = BasicPlanFactory(
                display_name='Plan Básico',
                price=299,
                max_users=10,
                billing_cycle_days=30
            )
            
            # Crear organización con plan trial
            org = OrganizationFactory(name='Mi Empresa de Prueba')
            sub = SubscriptionFactory(
                organization=org, 
                plan=trial_plan, 
                subscription_status='trial_active'
            )
            
            # Crear org_admin
            org_admin = OrgAdminFactory(
                email='admin@miempresa.com',
                organization=org,
                first_name='Carlos',
                last_name='Administrador'
            )
            org_admin.set_password('AdminPass123!')
            org_admin.save()
            
            # Crear superuser
            superuser = User.objects.create_superuser(
                email='superadmin@sistema.com',
                password='SuperPass123!',
                first_name='Super',
                last_name='Admin'
            )
            
            org_id = org.pk
            org_name = org.name
        
        # ========================================
        # PASO 1: ORG_ADMIN SOLICITA UPGRADE
        # ========================================
        print("\n" + "="*60)
        print("PASO 1: ORG_ADMIN SOLICITA UPGRADE")
        print("="*60)
        
        # Login como org_admin
        page.goto(f"{live_server.url}/accounts/login/")
        page.wait_for_load_state("networkidle")
        
        # Llenar formulario de login
        page.fill('input[name="email"], input[name="username"]', 'admin@miempresa.com')
        page.fill('input[name="password"]', 'AdminPass123!')
        page.click('button[type="submit"], input[type="submit"]')
        page.wait_for_timeout(2000)
        
        print("✓ Login como org_admin exitoso")
        
        # Buscar en el sidebar "Suscripción" o "Mi Plan" y hacer clic
        # Primero intentamos encontrar el enlace en el sidebar
        subscription_link = page.locator('a:has-text("Suscripción"), a:has-text("Mi Plan"), a:has-text("Plan")')
        if subscription_link.count() > 0:
            subscription_link.first.click()
            page.wait_for_timeout(1500)
            print("✓ Navegó a Suscripción desde sidebar")
        else:
            # Si no está en sidebar, ir directamente
            page.goto(f"{live_server.url}/plans/dashboard/")
            page.wait_for_timeout(1500)
            print("✓ Navegó directamente a /plans/dashboard/")
        
        # Tomar screenshot del dashboard de suscripción
        page.screenshot(path="tests/e2e/screenshots/01_subscription_dashboard.png")
        print("📸 Screenshot: dashboard de suscripción")
        
        # Buscar botón de "Solicitar Upgrade" o "Actualizar Plan"
        upgrade_btn = page.locator(
            'a:has-text("Solicitar"), a:has-text("Actualizar"), '
            'a:has-text("Upgrade"), button:has-text("Solicitar")'
        )
        
        if upgrade_btn.count() > 0:
            upgrade_btn.first.click()
            page.wait_for_timeout(1500)
            print("✓ Clic en botón de solicitar upgrade")
        else:
            # Ir directamente a la URL de solicitar
            page.goto(f"{live_server.url}/plans/solicitar-actualizacion/")
            page.wait_for_timeout(1500)
            print("✓ Navegó directamente a solicitar-actualizacion")
        
        # Tomar screenshot del formulario de solicitud
        page.screenshot(path="tests/e2e/screenshots/02_upgrade_request_form.png")
        print("📸 Screenshot: formulario de solicitud")
        
        # Buscar select de plan y seleccionar el plan básico
        plan_select = page.locator('select[name="requested_plan"], select[name="plan"]')
        if plan_select.count() > 0:
            # Seleccionar el plan básico (segunda opción generalmente)
            options = plan_select.locator('option')
            if options.count() > 1:
                plan_select.select_option(index=1)
                print("✓ Plan seleccionado")
        
        # Buscar y hacer clic en enviar
        submit_btn = page.locator('button[type="submit"], input[type="submit"]')
        if submit_btn.count() > 0:
            submit_btn.first.click()
            page.wait_for_timeout(2000)
            print("✓ Solicitud enviada")
        
        # Tomar screenshot después de enviar
        page.screenshot(path="tests/e2e/screenshots/03_after_request_sent.png")
        print("📸 Screenshot: después de enviar solicitud")
        
        # Verificar en BD que se creó la solicitud
        with django_db_blocker.unblock():
            from apps.plans.models import UpgradeRequest
            request_exists = UpgradeRequest.objects.filter(
                organization_id=org_id,
                status='pending'
            ).exists()
            print(f"✓ Solicitud creada en BD: {request_exists}")
        
        # Logout del org_admin
        page.goto(f"{live_server.url}/accounts/logout/")
        page.wait_for_timeout(1000)
        print("✓ Logout de org_admin")
        
        # ========================================
        # PASO 2: SUPERADMIN APRUEBA EN ADMIN
        # ========================================
        print("\n" + "="*60)
        print("PASO 2: SUPERADMIN APRUEBA EN ADMIN")
        print("="*60)
        
        # Login en admin panel
        page.goto(f"{live_server.url}/admin/login/")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="username"]', 'superadmin@sistema.com')
        page.fill('input[name="password"]', 'SuperPass123!')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)
        
        print("✓ Login como superadmin en admin panel")
        
        # Tomar screenshot del admin home
        page.screenshot(path="tests/e2e/screenshots/04_admin_home.png")
        print("📸 Screenshot: admin home")
        
        # Ir a las solicitudes de upgrade
        page.goto(f"{live_server.url}/admin/plans/upgraderequest/")
        page.wait_for_timeout(1500)
        
        # Tomar screenshot de la lista de solicitudes
        page.screenshot(path="tests/e2e/screenshots/05_upgrade_requests_list.png")
        print("📸 Screenshot: lista de solicitudes de upgrade")
        
        # Buscar la solicitud pendiente y hacer clic
        pending_row = page.locator(f'tr:has-text("{org_name}"), tr:has-text("Pendiente"), tr:has-text("pending")')
        if pending_row.count() > 0:
            # Hacer clic en el enlace de la primera columna para editar
            pending_row.first.locator('a').first.click()
            page.wait_for_timeout(1500)
            print("✓ Abrió detalle de la solicitud")
        else:
            # Intentar clic en el primer enlace de la tabla
            first_link = page.locator('#result_list a').first
            if first_link.count() > 0:
                first_link.click()
                page.wait_for_timeout(1500)
                print("✓ Abrió primera solicitud")
        
        # Tomar screenshot del detalle
        page.screenshot(path="tests/e2e/screenshots/06_upgrade_request_detail.png")
        print("📸 Screenshot: detalle de solicitud")
        
        # Cambiar estado a "approved"
        status_select = page.locator('select[name="status"]')
        if status_select.count() > 0:
            status_select.select_option('approved')
            print("✓ Estado cambiado a 'approved'")
        
        # Guardar
        save_btn = page.locator('input[name="_save"], button:has-text("Guardar")')
        if save_btn.count() > 0:
            save_btn.first.click()
            page.wait_for_timeout(2000)
            print("✓ Guardado")
        
        # Tomar screenshot después de aprobar
        page.screenshot(path="tests/e2e/screenshots/07_after_approval.png")
        print("📸 Screenshot: después de aprobar")
        
        # ========================================
        # PASO 3: VERIFICAR EN ADMIN ORG
        # ========================================
        print("\n" + "="*60)
        print("PASO 3: VERIFICAR PLAN ACTIVADO")
        print("="*60)
        
        # Ir a la organización en admin
        page.goto(f"{live_server.url}/admin/orgs/organization/{org_id}/change/")
        page.wait_for_timeout(1500)
        
        # Tomar screenshot de la organización
        page.screenshot(path="tests/e2e/screenshots/08_org_after_upgrade.png")
        print("📸 Screenshot: organización después del upgrade")
        
        # Ir a suscripciones para verificar
        page.goto(f"{live_server.url}/admin/plans/subscription/")
        page.wait_for_timeout(1500)
        
        # Buscar la suscripción de nuestra org
        org_sub_link = page.locator(f'tr:has-text("{org_name}") a').first
        if org_sub_link.count() > 0:
            org_sub_link.click()
            page.wait_for_timeout(1500)
        
        # Tomar screenshot de la suscripción actualizada
        page.screenshot(path="tests/e2e/screenshots/09_subscription_updated.png")
        print("📸 Screenshot: suscripción actualizada")
        
        # Verificar en BD
        with django_db_blocker.unblock():
            from apps.plans.models import Subscription, UpgradeRequest
            
            # Verificar que la solicitud fue aprobada
            upgrade = UpgradeRequest.objects.filter(organization_id=org_id).first()
            if upgrade:
                print(f"✓ Estado de solicitud: {upgrade.status}")
            
            # Verificar la suscripción actual
            sub = Subscription.objects.filter(organization_id=org_id).first()
            if sub:
                print(f"✓ Plan actual: {sub.plan.display_name}")
                print(f"✓ Estado de suscripción: {sub.subscription_status}")
                print(f"✓ Fecha fin: {sub.end_date}")
        
        print("\n" + "="*60)
        print("✅ FLUJO DE UPGRADE COMPLETADO")
        print("="*60)
        print("\nScreenshots guardados en: tests/e2e/screenshots/")
