"""
Configuración de fixtures para tests de Files

Incluye configuración especial para testing de storage
que funciona tanto en local como en R2.
"""
import pytest
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models.signals import pre_save


@pytest.fixture(autouse=True)
def disable_account_signals():
    """
    Deshabilitar signals de accounts que validan límites de usuarios
    para evitar que interfieran con los tests.
    
    Este fixture se aplica automáticamente a todos los tests del módulo files.
    """
    from apps.accounts import signals as account_signals
    from apps.accounts.models import User
    
    # Desconectar el signal que valida límites de organización
    pre_save.disconnect(
        account_signals.validate_organization_limits,
        sender=User
    )
    
    yield
    
    # Reconectar después del test
    pre_save.connect(
        account_signals.validate_organization_limits,
        sender=User
    )


@pytest.fixture(scope='function')
def disable_file_signals(db):
    """
    Deshabilita las signals de archivos durante los tests
    para evitar procesamiento asíncrono.
    """
    from django.db.models import signals
    from apps.files.models import ProjectFile
    from apps.files import storage_signals
    
    # Guardar handlers originales
    original_handlers = {}
    
    # Deshabilitar signals
    for signal_type in [signals.pre_save, signals.post_save, signals.post_delete]:
        handlers = signal_type.receivers[:]
        original_handlers[signal_type] = handlers
        signal_type.receivers = []
    
    yield
    
    # Restaurar signals
    for signal_type, handlers in original_handlers.items():
        signal_type.receivers = handlers


@pytest.fixture(scope='function')
def use_local_storage(settings):
    """
    Fuerza el uso de FileSystemStorage para tests
    independientemente de la configuración.
    
    Esto asegura que los tests sean rápidos y no dependan de R2.
    """
    original_backend = settings.STORAGES['default']['BACKEND']
    settings.STORAGES['default']['BACKEND'] = 'django.core.files.storage.FileSystemStorage'
    
    yield
    
    settings.STORAGES['default']['BACKEND'] = original_backend


@pytest.fixture(scope='function')
def mock_r2_storage(settings, mocker):
    """
    Mock del storage de R2 para tests de integración.
    
    Simula las operaciones de R2 sin conectarse realmente.
    """
    # Mock del cliente S3/R2
    mock_client = mocker.Mock()
    mock_client.put_object.return_value = {'ETag': 'fake-etag'}
    mock_client.delete_object.return_value = {}
    mock_client.head_object.return_value = {'ContentLength': 1024}
    
    mocker.patch('boto3.client', return_value=mock_client)
    
    return mock_client


@pytest.fixture
def sample_pdf_content():
    """Contenido de muestra para un archivo PDF"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"


@pytest.fixture
def sample_image_content():
    """Contenido de muestra para una imagen JPEG"""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


@pytest.fixture
def sample_malicious_content():
    """Contenido de muestra para archivo malicioso (para tests de seguridad)"""
    return b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Directorio temporal para uploads durante tests"""
    upload_dir = tmp_path / "test_uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture
def cleanup_test_files():
    """
    Limpia archivos de test después de cada prueba.
    
    Útil para evitar acumulación de archivos en tests.
    """
    created_files = []
    
    def track_file(file_obj):
        created_files.append(file_obj)
        return file_obj
    
    yield track_file
    
    # Cleanup
    for file_obj in created_files:
        try:
            if file_obj.file:
                file_obj.file.delete(save=False)
            file_obj.delete()
        except Exception:
            pass


@pytest.fixture
def allowed_extensions(settings):
    """Lista de extensiones permitidas desde settings"""
    return [
        'PDF', 'JPG', 'JPEG', 'PNG', 'GIF',
        'DWG', 'DXF', 'RVT', 'SKP', '3DS', 'MAX',
        'ZIP', 'RAR', '7Z',
        'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX',
        'TXT', 'MD'
    ]


@pytest.fixture
def dangerous_extensions():
    """Lista de extensiones peligrosas que deben ser bloqueadas"""
    return [
        'EXE', 'BAT', 'CMD', 'COM', 'PIF', 'SCR',
        'SH', 'BASH', 'ZSH',
        'PS1', 'VBS', 'VBE', 'JS', 'JSE',
        'APP', 'DMG', 'PKG',
        'DEB', 'RPM',
        'MSI', 'MSP',
        'JAR', 'CLASS',
        'PY', 'PYC', 'PYO',
        'RB', 'PL', 'PHP'
    ]

