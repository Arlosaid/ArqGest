"""
Tests unitarios para el modelo User
"""
import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from tests.factories.account_factories import (
    UserFactory, 
    SuperUserFactory, 
    OrgAdminFactory,
    InactiveUserFactory
)

User = get_user_model()


# ============================================================================
# TESTS DE CREACIÓN DE USUARIOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUserCreation:
    """Tests de creación básica de usuarios"""
    
    def test_user_creation_with_factory(self, disable_account_signals):
        """Verificar que se puede crear un usuario con la factory"""
        user = UserFactory()
        
        assert user.pk is not None
        assert user.email is not None
        assert user.first_name is not None
        assert user.last_name is not None
        assert user.is_active is True
    
    def test_user_creation_with_manager(self, disable_account_signals):
        """Verificar creación de usuario usando el manager"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.pk is not None
        assert user.email == 'test@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
    
    def test_superuser_creation(self, disable_account_signals):
        """Verificar creación de superusuario"""
        superuser = SuperUserFactory()
        
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.is_active is True
    
    def test_org_admin_creation(self, disable_account_signals):
        """Verificar creación de admin de organización"""
        admin = OrgAdminFactory()
        
        assert admin.is_org_admin is True
        assert admin.is_superuser is False
    
    def test_inactive_user_creation(self):
        """Verificar creación de usuario inactivo"""
        user = InactiveUserFactory()
        
        assert user.is_active is False


# ============================================================================
# TESTS DE VALIDACIÓN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUserValidation:
    """Tests de validación de usuarios"""
    
    def test_email_is_required(self, disable_account_signals):
        """El email debe ser obligatorio"""
        with pytest.raises(ValueError, match='El correo electrónico es obligatorio'):
            User.objects.create_user(
                email='',
                password='testpass123',
                first_name='John',
                last_name='Doe'
            )
    
    def test_email_must_be_unique(self, disable_account_signals):
        """No se pueden crear dos usuarios con el mismo email"""
        # Crear primer usuario
        User.objects.create_user(
            email='duplicate@example.com',
            password='testpass123',
            first_name='First',
            last_name='User'
        )
        
        # Intentar crear segundo usuario con el mismo email
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='duplicate@example.com',
                password='testpass123',
                first_name='Second',
                last_name='User'
            )
    
    def test_username_auto_generation(self, disable_account_signals):
        """El username se debe generar automáticamente"""
        user = UserFactory(email='johndoe@example.com')
        
        assert user.username is not None
        assert len(user.username) > 0
        assert 'johndoe' in user.username
    
    def test_username_uniqueness(self, disable_account_signals):
        """Los usernames generados deben ser únicos"""
        user1 = UserFactory(email='same@example.com')
        # Forzar la creación de otro usuario con email diferente
        user2 = UserFactory(email='different@example.com')
        
        assert user1.username != user2.username


# ============================================================================
# TESTS DE CONTRASEÑAS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUserPassword:
    """Tests relacionados con contraseñas"""
    
    def test_password_is_hashed(self, disable_account_signals):
        """Las contraseñas deben estar hasheadas"""
        user = UserFactory()
        
        # La contraseña hasheada no debe ser igual al texto plano
        assert user.password != 'testpass123'
        # Debe empezar con el algoritmo de hash
        assert user.password.startswith('pbkdf2_sha256')
    
    def test_password_check_works(self, disable_account_signals):
        """check_password debe funcionar correctamente"""
        user = UserFactory()
        
        assert user.check_password('testpass123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_superuser_has_staff_and_superuser_flags(self, disable_account_signals):
        """Superusuario debe tener flags correctos"""
        superuser = User.objects.create_superuser(
            email='super@example.com',
            password='superpass123',
            first_name='Super',
            last_name='User'
        )
        
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
    
    def test_superuser_requires_is_staff_true(self, disable_account_signals):
        """create_superuser debe validar is_staff=True"""
        with pytest.raises(ValueError, match='is_staff=True'):
            User.objects.create_superuser(
                email='test@example.com',
                password='pass',
                first_name='Test',
                last_name='User',
                is_staff=False
            )
    
    def test_superuser_requires_is_superuser_true(self, disable_account_signals):
        """create_superuser debe validar is_superuser=True"""
        with pytest.raises(ValueError, match='is_superuser=True'):
            User.objects.create_superuser(
                email='test@example.com',
                password='pass',
                first_name='Test',
                last_name='User',
                is_superuser=False
            )


# ============================================================================
# TESTS DE PROPIEDADES Y MÉTODOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUserMethods:
    """Tests de métodos y propiedades del usuario"""
    
    def test_full_name_property(self, disable_account_signals):
        """La propiedad full_name debe retornar nombre completo"""
        user = UserFactory(first_name='John', last_name='Doe')
        
        assert user.full_name == 'John Doe'
    
    def test_full_name_with_empty_names(self, disable_account_signals):
        """full_name debe retornar email si no hay nombre"""
        # Crear usuario con el manager para controlar los campos exactamente
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='',
            last_name=''
        )
        
        assert user.full_name == 'test@example.com'
    
    def test_get_full_name_method(self, disable_account_signals):
        """get_full_name debe retornar el nombre completo"""
        user = UserFactory(first_name='Jane', last_name='Smith')
        
        assert user.get_full_name() == 'Jane Smith'
    
    def test_str_representation(self, disable_account_signals):
        """__str__ debe retornar el nombre completo"""
        user = UserFactory(first_name='Bob', last_name='Johnson')
        
        assert str(user) == 'Bob Johnson'
    
    def test_username_display(self, disable_account_signals):
        """username_display debe retornar el nombre completo"""
        user = UserFactory(first_name='Alice', last_name='Williams')
        
        assert user.username_display == 'Alice Williams'
    
    def test_role_display_admin(self, disable_account_signals):
        """role_display debe retornar 'Administrador' para org_admin"""
        admin = OrgAdminFactory()
        
        assert admin.role_display() == 'Administrador'
    
    def test_role_display_regular_user(self, disable_account_signals):
        """role_display debe retornar 'Usuario' para usuarios regulares"""
        user = UserFactory()
        
        assert user.role_display() == 'Usuario'
    
    def test_can_manage_users_as_admin(self, disable_account_signals):
        """Administrador de org debe poder gestionar usuarios"""
        admin = OrgAdminFactory()
        
        assert admin.can_manage_users() is True
    
    def test_can_manage_users_as_regular_user(self, disable_account_signals):
        """Usuario regular no debe poder gestionar usuarios"""
        user = UserFactory()
        
        assert user.can_manage_users() is False
    
    def test_get_organization_name_without_org(self, disable_account_signals):
        """get_organization_name debe retornar mensaje si no hay org"""
        user = UserFactory(organization=None)
        
        assert user.get_organization_name() == 'Sin organización'
    
    def test_is_in_organization_without_org(self, disable_account_signals):
        """is_in_organization debe retornar False si no hay org"""
        user = UserFactory()
        
        assert user.is_in_organization(1) is False
    
    def test_can_manage_organization_without_org(self, disable_account_signals):
        """can_manage_organization debe retornar falsy value sin org"""
        admin = OrgAdminFactory(organization=None)
        
        # El método retorna None o False cuando no puede gestionar
        assert not admin.can_manage_organization()


# ============================================================================
# TESTS DE CAMPOS ESPECIALES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUserSpecialFields:
    """Tests de campos especiales del modelo"""
    
    def test_password_change_required_default(self, disable_account_signals):
        """password_change_required debe ser False por defecto"""
        user = UserFactory()
        
        assert user.password_change_required is False
    
    def test_password_change_required_can_be_set(self, disable_account_signals):
        """password_change_required puede ser establecido"""
        user = UserFactory(password_change_required=True)
        
        assert user.password_change_required is True
    
    def test_organization_can_be_null(self, disable_account_signals):
        """El campo organization puede ser nulo"""
        user = UserFactory(organization=None)
        
        assert user.organization is None
        assert user.organization_id is None


# ============================================================================
# TESTS DE INTEGRACIÓN CON BASE DE DATOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUserDatabase:
    """Tests de interacciones con la base de datos"""
    
    def test_user_count_increments(self, disable_account_signals):
        """El contador de usuarios debe incrementar al crear"""
        initial_count = User.objects.count()
        
        UserFactory()
        
        assert User.objects.count() == initial_count + 1
    
    def test_user_can_be_retrieved_by_email(self, disable_account_signals):
        """Usuario debe poder recuperarse por email"""
        user = UserFactory(email='findme@example.com')
        
        found_user = User.objects.get(email='findme@example.com')
        
        assert found_user.pk == user.pk
    
    def test_user_can_be_deleted(self, disable_account_signals):
        """Usuario debe poder eliminarse"""
        user = UserFactory()
        user_id = user.pk
        
        user.delete()
        
        with pytest.raises(User.DoesNotExist):
            User.objects.get(pk=user_id)
    
    def test_user_can_be_updated(self, disable_account_signals):
        """Usuario debe poder actualizarse"""
        user = UserFactory(first_name='Original')
        
        user.first_name = 'Updated'
        user.save()
        
        user.refresh_from_db()
        assert user.first_name == 'Updated'
