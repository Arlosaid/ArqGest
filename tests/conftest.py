"""
Configuración global de pytest y fixtures compartidas
Este archivo se carga automáticamente por pytest
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from faker import Faker

fake = Faker()
User = get_user_model()


# ============================================================================
# FIXTURES DE CLIENTE Y AUTENTICACIÓN
# ============================================================================

@pytest.fixture
def api_client():
    """Cliente de Django para hacer requests"""
    return Client()


@pytest.fixture
def authenticated_client(db, user):
    """Cliente autenticado con un usuario básico"""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(db, superuser):
    """Cliente autenticado con un superusuario"""
    client = Client()
    client.force_login(superuser)
    return client


# ============================================================================
# FIXTURES DE USUARIOS
# ============================================================================

@pytest.fixture
def user(db):
    """Usuario básico para tests"""
    return User.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password='testpass123',
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )


@pytest.fixture
def superuser(db):
    """Superusuario para tests de admin"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def user_password():
    """Password conocido para tests de autenticación"""
    return 'testpass123'


@pytest.fixture
def user_with_known_password(db, user_password):
    """Usuario con password conocido para tests de login"""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password=user_password
    )


# ============================================================================
# FIXTURES DE ARCHIVOS
# ============================================================================

@pytest.fixture
def sample_image():
    """Imagen JPG de prueba"""
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=b'\xFF\xD8\xFF\xE0\x00\x10JFIF',  # JPG header
        content_type='image/jpeg'
    )


@pytest.fixture
def sample_png():
    """Imagen PNG de prueba"""
    return SimpleUploadedFile(
        name='test_image.png',
        content=b'\x89PNG\r\n\x1a\n',  # PNG header
        content_type='image/png'
    )


@pytest.fixture
def sample_pdf():
    """PDF de prueba"""
    return SimpleUploadedFile(
        name='test_document.pdf',
        content=b'%PDF-1.4',
        content_type='application/pdf'
    )


@pytest.fixture
def sample_text_file():
    """Archivo de texto de prueba"""
    return SimpleUploadedFile(
        name='test_document.txt',
        content=b'This is a test document.',
        content_type='text/plain'
    )


@pytest.fixture
def malicious_file():
    """Archivo potencialmente malicioso de prueba (ejecutable)"""
    return SimpleUploadedFile(
        name='malware.exe',
        content=b'MZ\x90\x00',  # DOS executable header
        content_type='application/x-msdownload'
    )


@pytest.fixture
def oversized_file():
    """Archivo que excede el límite de tamaño"""
    # 11MB (asumiendo límite de 10MB)
    large_content = b'0' * (11 * 1024 * 1024)
    return SimpleUploadedFile(
        name='large_file.bin',
        content=large_content,
        content_type='application/octet-stream'
    )


# ============================================================================
# FIXTURES DE CONFIGURACIÓN Y MOCKING
# ============================================================================

@pytest.fixture
def disable_account_signals():
    """Deshabilitar signals de validación de accounts para tests"""
    from django.db.models import signals
    from apps.accounts import signals as account_signals
    from apps.accounts.models import User
    
    # Desconectar signals de validación
    signals.pre_save.disconnect(account_signals.validate_user_organization, sender=User)
    signals.pre_save.disconnect(account_signals.validate_organization_limits, sender=User)
    signals.pre_save.disconnect(account_signals.ensure_names_present, sender=User)
    signals.pre_save.disconnect(account_signals.validate_admin_without_org, sender=User)
    
    yield
    
    # Reconectar signals
    signals.pre_save.connect(account_signals.validate_user_organization, sender=User)
    signals.pre_save.connect(account_signals.validate_organization_limits, sender=User)
    signals.pre_save.connect(account_signals.ensure_names_present, sender=User)
    signals.pre_save.connect(account_signals.validate_admin_without_org, sender=User)


@pytest.fixture
def disable_subscription_middleware(settings):
    """
    Deshabilitar middleware de subscription para tests unitarios
    
    Los tests unitarios de views NO deberían depender de reglas de negocio
    de subscriptions. Esta fixture permite testear la lógica de las views
    sin interferencia de middlewares.
    """
    # Guardar middlewares originales
    original_middleware = settings.MIDDLEWARE.copy()
    
    # Remover middlewares de subscription y organización
    middlewares_to_remove = [
        'apps.plans.middleware.SubscriptionAccessMiddleware',
        'apps.plans.middleware.SubscriptionInfoMiddleware',
        'apps.orgs.middleware.OrganizationContextMiddleware',
    ]
    
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE 
        if m not in middlewares_to_remove
    ]
    
    yield
    
    # Restaurar middlewares originales
    settings.MIDDLEWARE = original_middleware


@pytest.fixture
def mock_r2_storage(mocker):
    """Mock del storage de Cloudflare R2"""
    mock_storage = mocker.Mock()
    mock_storage.save.return_value = 'test-file-key-12345.jpg'
    mock_storage.url.return_value = 'https://r2.example.com/test-file-key-12345.jpg'
    mock_storage.delete.return_value = True
    mock_storage.exists.return_value = True
    mock_storage.size.return_value = 1024
    return mock_storage


@pytest.fixture
def mock_email_backend(mocker, settings):
    """Mock del backend de email para evitar envíos reales"""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mock_send = mocker.patch('django.core.mail.send_mail')
    return mock_send


@pytest.fixture(autouse=True)
def reset_cache(settings):
    """Limpiar cache antes de cada test (autouse=True lo ejecuta siempre)"""
    from django.core.cache import cache
    try:
        cache.clear()
    except Exception:
        pass  # Si el cache no está disponible o no soporta clear, continuar
    yield
    try:
        cache.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Usar directorio temporal para MEDIA_ROOT en tests"""
    settings.MEDIA_ROOT = tmpdir.strpath


# ============================================================================
# FIXTURES DE DATOS DE PRUEBA
# ============================================================================

@pytest.fixture
def sample_transaction_data():
    """Datos de ejemplo para crear una transacción"""
    return {
        'description': 'Test transaction',
        'amount': 100.50,
        'transaction_type': 'income',
        'date': '2025-11-04'
    }


@pytest.fixture
def sample_project_data():
    """Datos de ejemplo para crear un proyecto"""
    return {
        'name': 'Test Project',
        'description': 'A test project for unit testing',
        'budget': 10000.00,
        'start_date': '2025-11-01',
        'end_date': '2025-12-31'
    }


# ============================================================================
# UTILIDADES Y HELPERS
# ============================================================================

@pytest.fixture
def assert_redirects_to_login():
    """Helper para verificar redirección a login"""
    def _assert(response):
        assert response.status_code == 302
        assert '/login' in response.url or '/accounts/login' in response.url
    return _assert


@pytest.fixture
def create_multiple_users(db):
    """Helper para crear múltiples usuarios de prueba"""
    def _create(count=5):
        users = []
        for i in range(count):
            user = User.objects.create_user(
                username=f'user{i}_{fake.user_name()}',
                email=fake.email(),
                password='testpass123'
            )
            users.append(user)
        return users
    return _create


# ============================================================================
# CONFIGURACIÓN DE MARKERS
# ============================================================================

def pytest_configure(config):
    """Registrar markers personalizados"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests"
    )
    config.addinivalue_line(
        "markers", "wip: marks tests as work in progress"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security-related"
    )
