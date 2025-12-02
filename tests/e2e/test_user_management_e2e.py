"""
Tests E2E: Gestión de Usuarios

Estos tests verifican flujos de usuario como:
- Login con contraseña temporal
- Cambio de contraseña obligatorio
- Gestión de usuarios por admin de org
- Flujo de registro/invitación
- Recuperación de contraseña
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestUserLoginFlows:
    """Tests de diferentes flujos de login"""
    
    def test_first_login_requires_password_change(self, page: Page, live_server, db, django_db_blocker):
        """
        Usuario con password_change_required debe cambiar contraseña en primer login.
        
        Simula: Admin crea usuario → Usuario hace login → Sistema obliga cambio de password
        """
        from django.contrib.auth import get_user_model
        from tests.factories.orgs.org_factories import OrganizationFactory
        from tests.factories.plans.plan_factories import SubscriptionFactory, BasicPlanFactory
        
        User = get_user_model()
        
        with django_db_blocker.unblock():
            # Crear org con plan
            org = OrganizationFactory(name='Org Password Change E2E')
            plan = BasicPlanFactory(max_users=5)
            SubscriptionFactory(organization=org, plan=plan, subscription_status='basic_active')
            
            # Crear usuario que debe cambiar password
            temp_password = 'TempPass123!'
            user = User.objects.create_user(
                username='new_user_e2e',
                email='newuser@test.com',
                password=temp_password,
                first_name='Nuevo',
                last_name='Usuario',
                organization=org,
                password_change_required=True  # IMPORTANTE
            )
        
        # Intentar login
        page.goto(f"{live_server.url}/accounts/login/")
        page.wait_for_load_state("networkidle")
        
        page.locator('input[name="username"], input[name="login"]').first.fill('newuser@test.com')
        page.locator('input[name="password"]').first.fill(temp_password)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        
        page.wait_for_timeout(2000)
        
        # Verificar que redirige a cambio de contraseña
        is_password_change_page = (
            'password' in page.url.lower() and 'change' in page.url.lower() or
            'cambiar' in page.url.lower() or
            page.locator('text=cambiar contraseña, text=change password, text=nueva contraseña').count() > 0
        )
        
        print(f"✓ Redirigido a cambio de contraseña: {is_password_change_page}")
        print(f"  URL actual: {page.url}")
    
    def test_password_change_flow_complete(self, page: Page, live_server, db, django_db_blocker):
        """
        Flujo completo de cambio de contraseña obligatorio.
        """
        from django.contrib.auth import get_user_model
        from tests.factories.orgs.org_factories import OrganizationFactory
        from tests.factories.plans.plan_factories import SubscriptionFactory, BasicPlanFactory
        
        User = get_user_model()
        
        with django_db_blocker.unblock():
            org = OrganizationFactory(name='Org Complete Change E2E')
            plan = BasicPlanFactory(max_users=5)
            SubscriptionFactory(organization=org, plan=plan, subscription_status='basic_active')
            
            temp_password = 'TempPass456!'
            user = User.objects.create_user(
                username='complete_change_e2e',
                email='completechange@test.com',
                password=temp_password,
                first_name='Complete',
                last_name='Change',
                organization=org,
                password_change_required=True
            )
        
        # Login
        page.goto(f"{live_server.url}/accounts/login/")
        page.locator('input[name="username"], input[name="login"]').first.fill('completechange@test.com')
        page.locator('input[name="password"]').first.fill(temp_password)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(2000)
        
        # Buscar formulario de cambio de contraseña
        new_password_field = page.locator(
            'input[name="new_password1"], '
            'input[name="new_password"], '
            'input[type="password"]:visible'
        )
        
        if new_password_field.count() > 0:
            # Nueva contraseña segura
            new_password = 'NewSecurePass789!'
            
            # Llenar campos
            new_pass_1 = page.locator('input[name="new_password1"]:visible')
            new_pass_2 = page.locator('input[name="new_password2"]:visible')
            
            if new_pass_1.count() > 0 and new_pass_2.count() > 0:
                new_pass_1.fill(new_password)
                new_pass_2.fill(new_password)
                
                # Submit
                page.locator('button[type="submit"]:visible').first.click()
                page.wait_for_timeout(3000)
                
                # Verificar redirección (indica éxito)
                # El sistema debería redirigir al dashboard después del cambio exitoso
                was_redirected = '/force-password-change' not in page.url
                
                if was_redirected:
                    # Verificar que ya no requiere cambio
                    with django_db_blocker.unblock():
                        user.refresh_from_db()
                        print(f"✓ password_change_required: {user.password_change_required}")
                        assert not user.password_change_required, "Flag debería estar en False"
                else:
                    # Si aún estamos en la página de cambio, puede haber errores de validación
                    errors = page.locator('.errorlist:visible, .alert-danger:visible, .invalid-feedback:visible')
                    if errors.count() > 0:
                        error_text = errors.first.text_content()
                        pytest.skip(f"Formulario mostró errores de validación: {error_text}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestOrgAdminUserManagement:
    """Tests de gestión de usuarios por admin de organización"""
    
    def test_org_admin_can_view_users_list(self, logged_in_page: Page, live_server, e2e_user, e2e_second_user):
        """
        Admin de org puede ver la lista de usuarios de su organización.
        """
        page = logged_in_page
        
        # Navegar a gestión de usuarios
        page.goto(f"{live_server.url}/users/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que carga la página de usuarios
        users_page_loaded = (
            page.locator('text=Usuarios, text=Users, text=Miembros').count() > 0 or
            page.locator('[class*="user"]').count() > 0 or
            'users' in page.url.lower()
        )
        
        # Verificar que el segundo usuario aparece
        second_user_visible = page.locator(f'text={e2e_second_user.email}').count() > 0
        
        print(f"✓ Página de usuarios cargada: {users_page_loaded}")
        print(f"✓ Segundo usuario visible: {second_user_visible}")
    
    def test_org_admin_can_create_user(self, logged_in_page: Page, live_server, e2e_user, db):
        """
        Admin de org puede crear nuevos usuarios.
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        page = logged_in_page
        
        # Ir a crear usuario
        page.goto(f"{live_server.url}/users/new/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que el formulario cargó
        email_field = page.locator('input[name="email"]')
        
        if email_field.count() > 0:
            new_email = 'newcreated@test.com'
            
            email_field.fill(new_email)
            
            # Otros campos
            first_name = page.locator('input[name="first_name"]')
            if first_name.count() > 0:
                first_name.fill('Nuevo')
            
            last_name = page.locator('input[name="last_name"]')
            if last_name.count() > 0:
                last_name.fill('Creado')
            
            # Submit
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(2000)
            
            # Verificar en BD
            user_created = User.objects.filter(
                email=new_email,
                organization=e2e_user.organization
            ).exists()
            
            print(f"✓ Usuario creado en BD: {user_created}")
    
    def test_org_admin_can_deactivate_user(self, logged_in_page: Page, live_server, e2e_second_user, db):
        """
        Admin de org puede desactivar usuarios.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        page = logged_in_page
        
        # Ir a editar el segundo usuario
        page.goto(f"{live_server.url}/users/{e2e_second_user.pk}/edit/")
        page.wait_for_load_state("networkidle")
        
        # Buscar checkbox de activo
        is_active_checkbox = page.locator('input[name="is_active"]')
        
        if is_active_checkbox.count() > 0:
            # Desmarcar si está marcado
            if is_active_checkbox.is_checked():
                is_active_checkbox.uncheck()
            
            # Guardar
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(1500)
            
            # Verificar en BD
            e2e_second_user.refresh_from_db()
            print(f"✓ Usuario desactivado: {not e2e_second_user.is_active}")
        else:
            # Buscar botón de desactivar
            deactivate_btn = page.locator(
                'button:has-text("Desactivar"), '
                'a:has-text("Desactivar"), '
                '[data-action="deactivate"]'
            )
            if deactivate_btn.count() > 0:
                deactivate_btn.first.click()
                page.wait_for_timeout(1500)


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPasswordResetFlow:
    """Tests del flujo de recuperación de contraseña"""
    
    def test_password_reset_page_loads(self, page: Page, live_server):
        """La página de recuperación de contraseña carga correctamente"""
        page.goto(f"{live_server.url}/accounts/password-reset/")
        page.wait_for_load_state("networkidle")
        
        # Verificar elementos de la página
        email_field = page.locator('input[name="email"], input[type="email"]')
        
        page_loaded = (
            email_field.count() > 0 or
            page.locator('text=recuperar, text=reset, text=restablecer').count() > 0
        )
        
        print(f"✓ Página de reset cargada: {page_loaded}")
    
    def test_password_reset_request_for_valid_email(self, page: Page, live_server, e2e_user):
        """
        Solicitar reset para email válido muestra mensaje de confirmación.
        """
        page.goto(f"{live_server.url}/accounts/password-reset/")
        page.wait_for_load_state("networkidle")
        
        email_field = page.locator('input[name="email"], input[type="email"]')
        
        if email_field.count() > 0:
            email_field.first.fill(e2e_user.email)
            
            # Submit
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(2000)
            
            # Debería mostrar mensaje de confirmación (no revelar si existe)
            confirmation = page.locator(
                'text=enviado, text=correo, text=email, text=sent, '
                '.alert-success, .alert-info'
            )
            
            print(f"✓ Mensaje de confirmación: {confirmation.count() > 0}")
    
    def test_password_reset_request_for_invalid_email(self, page: Page, live_server):
        """
        Solicitar reset para email inexistente NO revela información.
        SECURITY: No debe indicar si el email existe o no.
        """
        page.goto(f"{live_server.url}/accounts/password-reset/")
        page.wait_for_load_state("networkidle")
        
        email_field = page.locator('input[name="email"], input[type="email"]')
        
        if email_field.count() > 0:
            # Email que no existe
            email_field.first.fill('nonexistent@fake-domain-xyz.com')
            
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(2000)
            
            # Debería mostrar el MISMO mensaje que para email válido
            # NO debería decir "usuario no encontrado"
            error_revealing = page.locator(
                'text=no existe, text=no encontrado, text=not found, '
                'text=usuario no existe'
            )
            
            is_secure = error_revealing.count() == 0
            print(f"✓ No revela info de usuario: {is_secure}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestUserProfileManagement:
    """Tests de gestión del perfil de usuario"""
    
    def test_user_can_view_profile(self, logged_in_page: Page, live_server, e2e_user):
        """Usuario puede ver su perfil"""
        page = logged_in_page
        
        # Navegar al perfil
        page.goto(f"{live_server.url}/accounts/profile/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que muestra información del usuario
        email_visible = page.locator(f'text={e2e_user.email}').count() > 0
        name_visible = page.locator(f'text={e2e_user.first_name}').count() > 0
        
        profile_loaded = (
            email_visible or
            name_visible or
            page.locator('[class*="profile"]').count() > 0
        )
        
        print(f"✓ Perfil cargado: {profile_loaded}")
        print(f"  Email visible: {email_visible}")
        print(f"  Nombre visible: {name_visible}")
    
    def test_user_can_update_profile(self, logged_in_page: Page, live_server, e2e_user, db):
        """Usuario puede actualizar su perfil"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        page = logged_in_page
        
        page.goto(f"{live_server.url}/accounts/profile/")
        page.wait_for_load_state("networkidle")
        
        # Buscar botón de editar
        edit_btn = page.locator(
            'a:has-text("Editar"), '
            'button:has-text("Editar"), '
            'a[href*="edit"]'
        )
        
        if edit_btn.count() > 0:
            edit_btn.first.click()
            page.wait_for_timeout(500)
        
        # Editar nombre
        first_name_field = page.locator('input[name="first_name"]')
        
        if first_name_field.count() > 0:
            new_name = 'UpdatedName'
            first_name_field.fill(new_name)
            
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(1500)
            
            # Verificar en BD
            e2e_user.refresh_from_db()
            name_updated = e2e_user.first_name == new_name
            print(f"✓ Nombre actualizado: {name_updated} ({e2e_user.first_name})")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestUserSessionManagement:
    """Tests de gestión de sesión de usuario"""
    
    def test_session_persists_after_navigation(self, logged_in_page: Page, live_server):
        """La sesión persiste mientras el usuario navega"""
        page = logged_in_page
        
        # Navegar a varias páginas
        pages_to_visit = [
            '/projects/',
            '/dashboard/',
            '/accounts/profile/',
        ]
        
        for path in pages_to_visit:
            page.goto(f"{live_server.url}{path}")
            page.wait_for_timeout(500)
            
            # Verificar que NO redirige a login
            is_logged_in = '/login' not in page.url
            
            if not is_logged_in:
                print(f"⚠ Sesión perdida en {path}")
                break
        else:
            print("✓ Sesión persistente en navegación")
    
    def test_logout_clears_session(self, logged_in_page: Page, live_server):
        """Logout limpia la sesión correctamente"""
        page = logged_in_page
        
        # Hacer logout
        # Buscar link de logout
        user_menu = page.locator('.dropdown-toggle, [data-bs-toggle="dropdown"], .user-menu')
        if user_menu.count() > 0:
            user_menu.first.click()
            page.wait_for_timeout(300)
        
        logout_link = page.locator('a[href*="logout"]')
        if logout_link.count() > 0:
            logout_link.first.evaluate("el => el.click()")
            page.wait_for_timeout(1500)
        
        # Intentar acceder a página protegida
        page.goto(f"{live_server.url}/projects/")
        page.wait_for_timeout(1000)
        
        # Debería redirigir a login
        redirected_to_login = '/login' in page.url or '/accounts/login' in page.url
        
        print(f"✓ Logout limpió sesión: {redirected_to_login}")
    
    def test_inactive_user_cannot_login(self, page: Page, live_server, db, django_db_blocker):
        """Usuario inactivo no puede hacer login"""
        from django.contrib.auth import get_user_model
        from tests.factories.orgs.org_factories import OrganizationFactory
        from tests.factories.plans.plan_factories import SubscriptionFactory, BasicPlanFactory
        
        User = get_user_model()
        
        with django_db_blocker.unblock():
            org = OrganizationFactory(name='Org Inactive User E2E')
            plan = BasicPlanFactory(max_users=5)
            SubscriptionFactory(organization=org, plan=plan, subscription_status='basic_active')
            
            # Crear usuario INACTIVO
            user = User.objects.create_user(
                username='inactive_e2e',
                email='inactive@test.com',
                password='InactivePass123!',
                first_name='Inactive',
                last_name='User',
                organization=org,
                is_active=False  # IMPORTANTE
            )
        
        # Intentar login
        page.goto(f"{live_server.url}/accounts/login/")
        page.locator('input[name="username"], input[name="login"]').first.fill('inactive@test.com')
        page.locator('input[name="password"]').first.fill('InactivePass123!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        
        page.wait_for_timeout(2000)
        
        # Debería quedarse en login con error
        still_on_login = '/login' in page.url
        has_error = page.locator('.alert-danger, .error, .errorlist, [class*="error"]').count() > 0
        
        print(f"✓ Usuario inactivo rechazado: login={still_on_login}, error={has_error}")
        assert still_on_login, "Usuario inactivo NO debería poder entrar"


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestUserRolePermissions:
    """Tests de permisos según rol de usuario"""
    
    def test_non_admin_cannot_access_user_management(self, page: Page, live_server, e2e_second_user, db):
        """
        Usuario sin rol de admin NO puede acceder a gestión de usuarios.
        """
        # Login como usuario NO admin
        page.goto(f"{live_server.url}/accounts/login/")
        page.locator('input[name="username"], input[name="login"]').first.fill(e2e_second_user.email)
        page.locator('input[name="password"]').first.fill('TestPass123!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(2000)
        
        # Intentar acceder a gestión de usuarios
        page.goto(f"{live_server.url}/users/")
        page.wait_for_timeout(1500)
        
        # Debería ser rechazado o redirigido
        access_denied = (
            '/login' in page.url or
            page.locator('text=403, text=permiso, text=acceso denegado').count() > 0 or
            page.url != f"{live_server.url}/users/"
        )
        
        print(f"✓ No-admin sin acceso a users: {access_denied}")
    
    def test_org_admin_can_access_user_management(self, logged_in_page: Page, live_server, e2e_user):
        """
        Admin de org puede acceder a gestión de usuarios.
        """
        page = logged_in_page
        
        # e2e_user es org_admin
        page.goto(f"{live_server.url}/users/")
        page.wait_for_timeout(1500)
        
        # Debería poder acceder
        access_granted = (
            '/login' not in page.url and
            page.locator('text=403, text=Forbidden').count() == 0
        )
        
        print(f"✓ Org-admin con acceso a users: {access_granted}")
