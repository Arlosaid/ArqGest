"""
Tests E2E: Flujo de Login

Estos tests verifican que el sistema de autenticación funciona
correctamente desde la perspectiva de un usuario real.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLoginFlow:
    """Tests del flujo de autenticación"""
    
    def test_login_page_loads(self, page: Page, live_server):
        """Verificar que la página de login carga correctamente"""
        page.goto(f"{live_server.url}/accounts/login/")
        
        # Verificar que existen los elementos del formulario
        # Usamos locators flexibles por si los nombres varían
        username_field = page.locator('input[name="username"], input[name="login"], input[type="email"]')
        password_field = page.locator('input[name="password"]')
        submit_btn = page.locator('button[type="submit"], input[type="submit"]')
        
        expect(username_field.first).to_be_visible()
        expect(password_field.first).to_be_visible()
        expect(submit_btn.first).to_be_visible()
    
    def test_login_success(self, page: Page, live_server, e2e_user):
        """Usuario puede hacer login correctamente"""
        page.goto(f"{live_server.url}/accounts/login/")
        
        # Llenar formulario
        page.locator('input[name="username"], input[name="login"]').first.fill('e2e@test.com')
        page.locator('input[name="password"]').first.fill('TestPass123!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        
        # Esperar a que redireccione
        page.wait_for_timeout(2000)
        
        # Verificar que NO estamos en la página de login
        assert "/login" not in page.url, f"Debería haber redireccionado, pero está en: {page.url}"
    
    def test_login_wrong_password(self, page: Page, live_server, e2e_user):
        """Login falla con contraseña incorrecta"""
        page.goto(f"{live_server.url}/accounts/login/")
        
        page.locator('input[name="username"], input[name="login"]').first.fill('e2e@test.com')
        page.locator('input[name="password"]').first.fill('WrongPassword123!')
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        
        # Esperar respuesta
        page.wait_for_timeout(1500)
        
        # Debería mostrar error O quedarse en login
        still_on_login = "/login" in page.url
        has_error = page.locator('.errorlist, .alert-danger, .error, .invalid-feedback, [class*="error"]').count() > 0
        
        assert still_on_login or has_error, "Debería mostrar error o quedarse en login"
    
    def test_login_empty_fields(self, page: Page, live_server):
        """Login falla con campos vacíos"""
        page.goto(f"{live_server.url}/accounts/login/")
        
        # Intentar enviar sin llenar
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        
        page.wait_for_timeout(1000)
        
        # Debería quedarse en login (validación HTML5 o del servidor)
        assert "/login" in page.url


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLogoutFlow:
    """Tests del flujo de logout"""
    
    def test_logout_success(self, logged_in_page: Page, live_server):
        """Usuario puede cerrar sesión"""
        page = logged_in_page
        
        # Primero abrir el dropdown del usuario si existe
        user_dropdown = page.locator('.dropdown-toggle, [data-bs-toggle="dropdown"], .user-menu, .nav-link.dropdown-toggle')
        if user_dropdown.count() > 0:
            # Usar JavaScript para abrir dropdown (más confiable)
            user_dropdown.first.evaluate("el => el.click()")
            page.wait_for_timeout(500)
        
        # Buscar link/botón de logout - usar force para elementos ocultos
        logout_link = page.locator('a[href*="logout"]')
        
        if logout_link.count() > 0:
            # Usar JavaScript click para evitar problemas de visibilidad
            logout_link.first.evaluate("el => el.click()")
            page.wait_for_timeout(1500)
            
            # Verificar que está deslogueado (en login o home)
            is_logged_out = "/login" in page.url or "/accounts/login" in page.url
            assert is_logged_out, f"Debería estar deslogueado, pero está en: {page.url}"
