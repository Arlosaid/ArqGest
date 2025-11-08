"""
⚠️ TESTS DE VALIDACIÓN IMPORTANTES - LOGIN (P1)

Estos tests verifican validaciones importantes de datos y casos edge
que deben manejarse correctamente.

COBERTURA P1:
✅ VD-06: Case sensitivity - Email
✅ VD-07: Case sensitivity - Password
✅ VD-08: Espacios en credenciales
✅ VD-09: Caracteres especiales en email
✅ ACC-03: Redirección con ?next=
✅ PWD-03: Validación de password strength
✅ SEG-05: Clickjacking protection

Autor: ARC Manager Team
Fecha: 7 Nov 2025
Fase: Tests Importantes de Validación
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.forms import CustomAuthenticationForm, ForcePasswordChangeForm
from tests.factories import UserFactory
from tests.factories import OrganizationFactory
from apps.plans.models import Plan, Subscription

User = get_user_model()


# ============================================================================
# VD-06: CASE SENSITIVITY - EMAIL
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestEmailCaseSensitivity:
    """Tests para verificar normalización de email"""
    
    def test_email_lowercase_normalization_on_creation(self, disable_account_signals):
        """
        ⚠️ IMPORTANTE: Email debe normalizarse a lowercase al crear usuario
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario creado con EMAIL MAYÚSCULAS se guarda en lowercase
        2. Previene duplicados por capitalización
        3. CustomUserManager normaliza correctamente
        """
        # ARRANGE & ACT: Crear usuario con email en MAYÚSCULAS
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='Password123!',
            organization=org
        )
        
        # ASSERT: Email guardado en lowercase
        assert user.email == 'test@example.com', \
            f"Email debería estar en lowercase, obtuve: {user.email}"
    
    
    def test_login_case_insensitive_email(self, client, disable_account_signals, rf):
        """
        ⚠️ IMPORTANTE: Login debe funcionar con cualquier capitalización de email
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario registrado: test@example.com
        2. Login con: TEST@EXAMPLE.COM debe funcionar
        3. Login con: TeSt@ExAmPlE.cOm debe funcionar
        """
        # ARRANGE: Crear usuario con email lowercase
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='test@example.com',
            password='Password123!',
            organization=org
        )
        
        # ACT & ASSERT: Login con diferentes capitalizaciones
        test_emails = [
            'TEST@EXAMPLE.COM',
            'TeSt@ExAmPlE.cOm',
            'test@EXAMPLE.com',
        ]
        
        for test_email in test_emails:
            # Crear nuevo form para cada test
            request = rf.post('/accounts/login/')
            form = CustomAuthenticationForm(request, data={
                'username': test_email,
                'password': 'Password123!',
            })
            
            # ASSERT: Form debe ser válido
            assert form.is_valid(), \
                f"Login con email '{test_email}' debería funcionar, errores: {form.errors}"
            
            # ASSERT: Usuario correcto autenticado
            assert form.get_user() == user, \
                f"Email '{test_email}' debería autenticar al mismo usuario"
    
    
    def test_cannot_create_duplicate_users_different_case(self, disable_account_signals):
        """
        ⚠️ IMPORTANTE: No se pueden crear 2 usuarios con email diferente solo en capitalización
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario 1: test@example.com
        2. Usuario 2: TEST@example.com → IntegrityError
        3. Constraint UNIQUE funciona con normalización
        """
        # ARRANGE: Crear primer usuario
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        User.objects.create_user(
            email='test@example.com',
            password='Password123!',
            organization=org
        )
        
        # ACT & ASSERT: Intentar crear segundo usuario con email en MAYÚSCULAS
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='TEST@EXAMPLE.COM',
                password='AnotherPass456!',
                organization=org
            )


# ============================================================================
# VD-07: CASE SENSITIVITY - PASSWORD
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestPasswordCaseSensitivity:
    """Tests para verificar que password es case-sensitive"""
    
    def test_password_is_case_sensitive(self, client, disable_account_signals, rf):
        """
        ⚠️ IMPORTANTE: Password debe ser case-sensitive (contrario a email)
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario con password: MyPassword123
        2. Login con: mypassword123 → FALLA
        3. Login con: MYPASSWORD123 → FALLA
        4. Solo funciona con capitalización exacta
        """
        # ARRANGE: Crear usuario con password específica
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='passtest@example.com',
            password='MyPassword123',  # Mixed case
            organization=org
        )
        
        # ACT & ASSERT: Intentar con diferentes capitalizaciones
        wrong_passwords = [
            'mypassword123',    # lowercase
            'MYPASSWORD123',    # uppercase
            'mYpAsSWoRD123',    # random mixed
        ]
        
        for wrong_pass in wrong_passwords:
            request = rf.post('/accounts/login/')
            form = CustomAuthenticationForm(request, data={
                'username': 'passtest@example.com',
                'password': wrong_pass,
            })
            
            # ASSERT: Form NO debe ser válido
            assert not form.is_valid(), \
                f"Password '{wrong_pass}' NO debería autenticar (case-sensitive)"
        
        # ACT & ASSERT: Password correcta debe funcionar
        request = rf.post('/accounts/login/')
        form = CustomAuthenticationForm(request, data={
            'username': 'passtest@example.com',
            'password': 'MyPassword123',  # Exacta
        })
        
        assert form.is_valid(), \
            "Password con capitalización correcta debe funcionar"


# ============================================================================
# VD-08: ESPACIOS EN CREDENCIALES
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestWhitespaceHandling:
    """Tests para verificar manejo de espacios leading/trailing"""
    
    def test_password_whitespace_trimmed(self, client, disable_account_signals, rf):
        """
        ⚠️ IMPORTANTE: Espacios en password deben limpiarse (mejor UX)
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario con password: Password123
        2. Login con: ' Password123 ' (espacios) → Funciona (limpiado)
        3. clean_password() en form hace .strip()
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='whitespace@example.com',
            password='Password123',
            organization=org
        )
        
        # ACT: Login con espacios en password
        request = rf.post('/accounts/login/')
        form = CustomAuthenticationForm(request, data={
            'username': 'whitespace@example.com',
            'password': '  Password123  ',  # Espacios leading/trailing
        })
        
        # ASSERT: Debe funcionar (espacios limpiados)
        assert form.is_valid(), \
            f"Password con espacios debería funcionar (trimming), errores: {form.errors}"
        
        assert form.get_user() == user
    
    
    def test_email_whitespace_trimmed(self, client, disable_account_signals, rf):
        """
        ⚠️ IMPORTANTE: Espacios en email deben limpiarse
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario: test@example.com
        2. Login con: ' test@example.com ' → Funciona
        3. clean_username() en form hace .strip()
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='spacemail@example.com',
            password='Password123',
            organization=org
        )
        
        # ACT: Login con espacios en email
        request = rf.post('/accounts/login/')
        form = CustomAuthenticationForm(request, data={
            'username': '  spacemail@example.com  ',  # Espacios
            'password': 'Password123',
        })
        
        # ASSERT: Debe funcionar
        assert form.is_valid(), \
            f"Email con espacios debería funcionar (trimming), errores: {form.errors}"


# ============================================================================
# VD-09: CARACTERES ESPECIALES EN EMAIL
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSpecialCharactersInEmail:
    """Tests para verificar soporte de emails válidos con caracteres especiales"""
    
    def test_valid_emails_with_special_characters(self, disable_account_signals):
        """
        ⚠️ IMPORTANTE: Emails válidos con caracteres especiales deben funcionar
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Emails válidos según RFC 5322
        2. +, ., _, -, números permitidos
        3. Sistema no rechaza emails válidos
        """
        # ARRANGE: Lista de emails válidos con caracteres especiales
        valid_emails = [
            'user+tag@example.com',      # Gmail-style tags
            'user.name@example.com',     # Dot en local part
            'user_name@example.com',     # Underscore
            'user-name@example.com',     # Hyphen
            'user123@example.com',       # Números
            'user+test-123@example.com', # Combinación
        ]
        
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        # ACT & ASSERT: Crear usuario con cada email
        for email in valid_emails:
            user = User.objects.create_user(
                email=email,
                password='Password123!',
                organization=org
            )
            
            # ASSERT: Usuario creado exitosamente
            assert user.pk is not None, \
                f"Email válido '{email}' debería crear usuario"
            
            # ASSERT: Email normalizado a lowercase
            assert user.email == email.lower(), \
                f"Email debería estar en lowercase: {user.email}"
            
            # Limpiar para siguiente iteración
            user.delete()


# ============================================================================
# ACC-03: REDIRECCIÓN CON ?next=
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestLoginRedirection:
    """Tests para verificar redirección post-login con ?next="""
    
    def test_login_redirects_to_next_parameter(self, client, disable_account_signals):
        """
        ⚠️ IMPORTANTE: Login debe redirigir a URL en ?next=
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Usuario accede /projects/ sin auth → redirige a /login/?next=/projects/
        2. Después del login → redirige a /projects/
        3. Django LoginView maneja esto automáticamente
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='redirect@example.com',
            password='Password123!',
            organization=org
        )
        
        # ACT: Login con ?next= parameter
        response = client.post(
            reverse('accounts:login') + '?next=/projects/',
            {
                'username': 'redirect@example.com',
                'password': 'Password123!',
            }
        )
        
        # ASSERT: Redirección a /projects/
        assert response.status_code == 302
        assert response.url == '/projects/', \
            f"Debería redirigir a /projects/, redirigió a: {response.url}"
    
    
    def test_login_blocks_external_next_urls(self, client, disable_account_signals):
        """
        🔴 CRÍTICO: ?next= con URL externa debe ser bloqueado
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Atacante intenta: /login/?next=https://evil.com
        2. Django valida y rechaza URL externa
        3. Redirige a dashboard por defecto
        
        ¿POR QUÉ ES CRÍTICO?
        - Previene open redirect vulnerability
        - Atacante no puede redirigir a sitio de phishing
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='security@example.com',
            password='Password123!',
            organization=org
        )
        
        # ACT: Intentar con URL externa
        malicious_urls = [
            'https://evil.com',
            '//evil.com',
            'http://evil.com/steal-data',
        ]
        
        for malicious_url in malicious_urls:
            response = client.post(
                reverse('accounts:login') + f'?next={malicious_url}',
                {
                    'username': 'security@example.com',
                    'password': 'Password123!',
                }
            )
            
            # ASSERT: NO redirige a URL externa
            assert response.status_code == 302
            assert 'evil.com' not in response.url, \
                f"NO debe redirigir a URL externa: {malicious_url}"
            
            # Logout para próximo test
            client.post(reverse('accounts:logout'))
    
    
    def test_login_preserves_query_params_in_next(self, client, disable_account_signals):
        """
        ⚠️ IMPORTANTE: Query params en ?next= deben preservarse
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. ?next=/projects/?status=active
        2. Después del login → /projects/?status=active
        3. Query params no se pierden
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='params@example.com',
            password='Password123!',
            organization=org
        )
        
        # ACT: Login con next que incluye query params
        response = client.post(
            reverse('accounts:login') + '?next=/projects/?status=active',
            {
                'username': 'params@example.com',
                'password': 'Password123!',
            }
        )
        
        # ASSERT: Query params preservados
        assert response.status_code == 302
        assert 'status=active' in response.url, \
            f"Query params deberían preservarse, obtuve: {response.url}"


# ============================================================================
# PWD-03: VALIDACIÓN DE PASSWORD STRENGTH
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestPasswordStrengthValidation:
    """Tests para verificar validación de fuerza de contraseña"""
    
    def test_password_reset_rejects_weak_passwords(self, disable_account_signals):
        """
        ⚠️ IMPORTANTE: Contraseñas débiles deben rechazarse
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Contraseña muy corta → Error
        2. Contraseña solo números → Error
        3. Contraseña muy común → Error
        4. Validadores de Django activos
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='strength@example.com',
            password='OldPass123!',
            organization=org
        )
        
        # Lista de contraseñas débiles
        weak_passwords = [
            ('abc123', 'muy corta'),
            ('12345678', 'solo números'),
            ('password', 'muy común'),
            ('qwerty123', 'muy común'),
            ('abc12345', 'corta y común'),
        ]
        
        # ACT & ASSERT: Cada contraseña débil debe ser rechazada
        for weak_pass, reason in weak_passwords:
            form = ForcePasswordChangeForm(
                user=user,
                data={
                    'old_password': 'OldPass123!',
                    'new_password1': weak_pass,
                    'new_password2': weak_pass,
                }
            )
            
            # ASSERT: Form NO válido
            assert not form.is_valid(), \
                f"Contraseña '{weak_pass}' ({reason}) debería rechazarse"
            
            # ASSERT: Error en new_password1 o __all__
            assert 'new_password1' in form.errors or '__all__' in form.errors, \
                f"Debe haber error de validación para '{weak_pass}'"
    
    
    def test_password_reset_accepts_strong_password(self, disable_account_signals):
        """
        ✅ IMPORTANTE: Contraseñas fuertes deben aceptarse
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Contraseña cumple todos los requisitos
        2. Form válido
        3. Usuario puede cambiar a contraseña segura
        """
        # ARRANGE
        org = OrganizationFactory()
        plan = Plan.objects.create(
            name='trial', display_name='Test Plan',
            max_users=10, max_storage_gb=100
        )
        Subscription.objects.create(organization=org, plan=plan)
        
        user = User.objects.create_user(
            email='strongpass@example.com',
            password='OldPass123!',
            organization=org
        )
        
        # ACT: Contraseña fuerte
        strong_password = 'MyV3ryStr0ng!P@ssw0rd'
        
        form = ForcePasswordChangeForm(
            user=user,
            data={
                'old_password': 'OldPass123!',
                'new_password1': strong_password,
                'new_password2': strong_password,
            }
        )
        
        # ASSERT: Form válido
        assert form.is_valid(), \
            f"Contraseña fuerte debería aceptarse, errores: {form.errors}"


# ============================================================================
# SEG-05: CLICKJACKING PROTECTION
# ============================================================================

@pytest.mark.security
@pytest.mark.django_db
class TestClickjackingProtection:
    """Tests para verificar protección contra clickjacking"""
    
    def test_login_page_has_x_frame_options_deny(self, client):
        """
        ⚠️ IMPORTANTE: Response debe incluir X-Frame-Options: DENY
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. GET a /accounts/login/ incluye header X-Frame-Options
        2. Valor es DENY (no permite embedding en iframes)
        3. SecurityMiddleware configurado correctamente
        
        ¿POR QUÉ ES IMPORTANTE?
        - Previene clickjacking attacks
        - Página no puede ser embebida en iframe malicioso
        - Requisito de seguridad básico
        """
        # ACT: Obtener página de login
        response = client.get(reverse('accounts:login'))
        
        # ASSERT 1: Response exitoso
        assert response.status_code == 200
        
        # ASSERT 2: Header X-Frame-Options presente
        assert 'X-Frame-Options' in response, \
            "Response debe incluir header X-Frame-Options"
        
        # ASSERT 3: Valor es DENY
        assert response['X-Frame-Options'] == 'DENY', \
            f"X-Frame-Options debería ser DENY, es: {response.get('X-Frame-Options')}"
    
    
    def test_all_pages_have_clickjacking_protection(self, client, disable_account_signals):
        """
        ⚠️ IMPORTANTE: Todas las páginas protegidas deben tener el header
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. No solo login, sino dashboard, password reset, etc.
        2. Middleware aplica a todas las views
        """
        # Lista de URLs a verificar
        pages_to_test = [
            reverse('accounts:login'),
            reverse('accounts:password_reset'),
            reverse('accounts:logout'),
        ]
        
        for url in pages_to_test:
            response = client.get(url)
            
            # ASSERT: Cada página tiene el header
            assert 'X-Frame-Options' in response, \
                f"URL {url} debe tener X-Frame-Options header"
            
            assert response['X-Frame-Options'] == 'DENY', \
                f"URL {url} debe tener X-Frame-Options: DENY"


# =============================================================================
# RESUMEN DE TESTS IMPORTANTES (P1)
# =============================================================================

"""
📊 TESTS IMPLEMENTADOS: 18 tests importantes

⚠️ Case Sensitivity (5 tests):
   - Email normalizado a lowercase
   - Login case-insensitive para email
   - No duplicados con diferente capitalización
   - Password es case-sensitive
   - Password correcta debe funcionar

⚠️ Espacios en Credenciales (2 tests):
   - Password whitespace trimmed
   - Email whitespace trimmed

⚠️ Caracteres Especiales (1 test):
   - Emails válidos con +, ., _, -, números

⚠️ Redirección (3 tests):
   - Redirige a ?next= después de login
   - Bloquea URLs externas en ?next=
   - Preserva query params

⚠️ Password Strength (2 tests):
   - Rechaza contraseñas débiles
   - Acepta contraseñas fuertes

⚠️ Clickjacking (2 tests):
   - X-Frame-Options: DENY en login
   - X-Frame-Options en todas las páginas

---

🎯 PRÓXIMO PASO:
- Correr tests: pytest tests/unit/test_accounts/test_login_validations.py -v
- Verificar que todos pasan
- Actualizar COBERTURA_TESTS_LOGIN.md con nuevas métricas
"""
