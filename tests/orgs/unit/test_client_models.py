"""
Tests unitarios para el modelo Client

Tests robustos que deben detectar fallos reales en el modelo Client.
"""
import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from tests.factories import (
    OrganizationFactory,
    ClientFactory,
    InactiveClientFactory
)
from apps.orgs.models import Client


# ============================================================================
# TESTS DE CREACIÓN DE CLIENTES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientCreation:
    """Tests de creación básica de clientes"""
    
    def test_client_creation_with_factory(self):
        """Verificar que se puede crear un cliente con la factory"""
        client = ClientFactory()
        
        assert client.pk is not None
        assert client.name is not None
        assert client.organization is not None
        assert client.is_active is True
    
    def test_client_creation_with_all_fields(self):
        """Verificar creación con todos los campos"""
        org = OrganizationFactory()
        client = Client.objects.create(
            organization=org,
            name='Test Client',
            email='client@example.com',
            phone_number='+1234567890',
            address='123 Test St',
            is_active=True
        )
        
        assert client.pk is not None
        assert client.name == 'Test Client'
        assert client.email == 'client@example.com'
        assert client.organization == org
    
    def test_inactive_client_creation(self):
        """Verificar creación de cliente inactivo"""
        client = InactiveClientFactory()
        
        assert client.is_active is False
    
    def test_client_str_representation(self):
        """Verificar representación string del cliente"""
        client = ClientFactory(name='My Client')
        
        assert str(client) == 'My Client'


# ============================================================================
# TESTS DE VALIDACIÓN Y CONSTRAINTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientValidation:
    """Tests de validación de clientes - DETECTAR BUGS REALES"""
    
    def test_name_is_required(self):
        """El nombre debe ser obligatorio - BUG POTENCIAL"""
        org = OrganizationFactory()
        
        with pytest.raises(Exception):
            Client.objects.create(
                organization=org,
                name=None
            )
    
    def test_organization_is_required(self):
        """La organización debe ser obligatoria - BUG POTENCIAL"""
        with pytest.raises((IntegrityError, ValueError)):
            Client.objects.create(
                organization=None,
                name='Test Client'
            )
    
    def test_name_max_length_validation(self):
        """El nombre no debe exceder 100 caracteres - BUG POTENCIAL"""
        org = OrganizationFactory()
        long_name = 'A' * 101
        
        with pytest.raises(Exception):
            Client.objects.create(
                organization=org,
                name=long_name
            )
    
    def test_email_max_length_validation(self):
        """El email no debe exceder 254 caracteres"""
        org = OrganizationFactory()
        long_email = 'a' * 250 + '@test.com'  # > 254 chars
        
        with pytest.raises(Exception):
            Client.objects.create(
                organization=org,
                name='Test',
                email=long_email
            )
    
    def test_email_can_be_blank(self):
        """El email puede estar vacío"""
        org = OrganizationFactory()
        client = Client.objects.create(
            organization=org,
            name='Test Client',
            email=''
        )
        
        assert client.email == ''
    
    def test_phone_can_be_blank(self):
        """El teléfono puede estar vacío"""
        org = OrganizationFactory()
        client = Client.objects.create(
            organization=org,
            name='Test Client',
            phone_number=''
        )
        
        assert client.phone_number == ''
    
    def test_address_can_be_blank(self):
        """La dirección puede estar vacía"""
        org = OrganizationFactory()
        client = Client.objects.create(
            organization=org,
            name='Test Client',
            address=''
        )
        
        assert client.address == ''


# ============================================================================
# TESTS DE UNIQUE TOGETHER
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientUniqueConstraints:
    """
    Tests de constraint unique_together (organization, name)
    CRÍTICO: Debe prevenir duplicados dentro de la misma org
    """
    
    def test_duplicate_name_same_organization_fails(self):
        """
        BUG POTENCIAL: No se pueden crear dos clientes con el mismo nombre
        en la MISMA organización.
        """
        org = OrganizationFactory()
        ClientFactory(organization=org, name='Duplicate Client')
        
        # Intentar crear otro cliente con el mismo nombre en la MISMA org
        with pytest.raises(IntegrityError):
            ClientFactory(organization=org, name='Duplicate Client')
    
    def test_same_name_different_organizations_allowed(self):
        """
        Clientes con el MISMO nombre pueden existir en DIFERENTES organizaciones
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        client1 = ClientFactory(organization=org1, name='Same Name')
        client2 = ClientFactory(organization=org2, name='Same Name')
        
        assert client1.name == client2.name
        assert client1.organization != client2.organization
        assert client1.pk != client2.pk
    
    def test_case_sensitive_name_uniqueness(self):
        """
        PREGUNTA: ¿Los nombres son case-sensitive?
        Este test detecta el comportamiento actual.
        """
        org = OrganizationFactory()
        ClientFactory(organization=org, name='Test Client')
        
        # ¿Se permite 'test client' (minúsculas)?
        try:
            client2 = ClientFactory(organization=org, name='test client')
            # Si llegamos aquí, es case-sensitive (permite minúsculas)
            assert client2.name == 'test client'
        except IntegrityError:
            # Si falla, es case-insensitive
            pytest.skip("Los nombres son case-insensitive en la BD")


# ============================================================================
# TESTS DE RELACIÓN CON ORGANIZATION
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientOrganizationRelationship:
    """Tests de la relación con Organization"""
    
    def test_client_belongs_to_organization(self):
        """Cliente debe pertenecer a una organización"""
        org = OrganizationFactory()
        client = ClientFactory(organization=org)
        
        assert client.organization == org
    
    def test_organization_can_have_multiple_clients(self):
        """Una organización puede tener múltiples clientes"""
        org = OrganizationFactory()
        clients = ClientFactory.create_batch(5, organization=org)
        
        assert org.clients.count() == 5
        for client in clients:
            assert client in org.clients.all()
    
    def test_deleting_organization_deletes_clients(self):
        """
        CRÍTICO: Al eliminar una organización, sus clientes se eliminan (CASCADE)
        Si este test falla, hay un BUG de integridad referencial.
        """
        org = OrganizationFactory()
        client_ids = [ClientFactory(organization=org).id for _ in range(3)]
        
        # Eliminar la organización
        org.delete()
        
        # Los clientes deben haberse eliminado (CASCADE)
        for client_id in client_ids:
            assert not Client.objects.filter(id=client_id).exists(), \
                f"BUG: Cliente {client_id} no se eliminó con la organización"
    
    def test_client_access_to_organization_fields(self):
        """Cliente puede acceder a campos de su organización"""
        org = OrganizationFactory(name='Parent Org')
        client = ClientFactory(organization=org)
        
        assert client.organization.name == 'Parent Org'
        assert client.organization.is_active is True


# ============================================================================
# TESTS DE TIMESTAMPS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientTimestamps:
    """Tests de campos de fecha automática"""
    
    def test_created_at_auto_set(self):
        """created_at debe establecerse automáticamente"""
        client = ClientFactory()
        
        assert client.created_at is not None
    
    def test_updated_at_auto_set(self):
        """updated_at debe establecerse automáticamente"""
        client = ClientFactory()
        
        assert client.updated_at is not None
    
    def test_updated_at_changes_on_save(self):
        """updated_at debe actualizarse al guardar"""
        client = ClientFactory()
        original_updated_at = client.updated_at
        
        # Esperar un momento y actualizar
        import time
        time.sleep(0.1)
        
        client.name = 'Updated Name'
        client.save()
        
        assert client.updated_at > original_updated_at


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientEdgeCases:
    """Tests de casos extremos - ENCONTRAR BUGS"""
    
    def test_client_with_unicode_name(self):
        """Nombres con caracteres Unicode deben funcionar"""
        org = OrganizationFactory()
        client = ClientFactory(
            organization=org,
            name='Cliente Español 中文 🚀'
        )
        
        assert client.name == 'Cliente Español 中文 🚀'
        assert str(client) == 'Cliente Español 中文 🚀'
    
    def test_client_with_special_characters_in_email(self):
        """Email con caracteres especiales válidos"""
        org = OrganizationFactory()
        client = ClientFactory(
            organization=org,
            email='test+tag@example.co.uk'
        )
        
        assert client.email == 'test+tag@example.co.uk'
    
    def test_client_with_very_long_address(self):
        """Dirección muy larga debe funcionar (TextField)"""
        org = OrganizationFactory()
        long_address = 'A' * 1000
        client = ClientFactory(
            organization=org,
            address=long_address
        )
        
        assert len(client.address) == 1000
    
    def test_client_with_international_phone(self):
        """Teléfono internacional debe funcionar"""
        org = OrganizationFactory()
        client = ClientFactory(
            organization=org,
            phone_number='+52 123 456 7890'
        )
        
        assert client.phone_number == '+52 123 456 7890'
    
    def test_multiple_clients_same_email_different_orgs(self):
        """
        ¿Se permite el mismo email en clientes de diferentes organizaciones?
        Este test detecta el comportamiento actual.
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        email = 'same@example.com'
        client1 = ClientFactory(organization=org1, email=email)
        client2 = ClientFactory(organization=org2, email=email)
        
        # Debe permitirse (no hay constraint unique en email)
        assert client1.email == client2.email
        assert client1.organization != client2.organization


# ============================================================================
# TESTS DE QUERYSETS Y ORDENAMIENTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientQuerysets:
    """Tests de queryset y ordenamiento por defecto"""
    
    def test_default_ordering_by_name(self):
        """Clientes deben ordenarse por nombre por defecto"""
        org = OrganizationFactory()
        ClientFactory(organization=org, name='Zebra Client')
        ClientFactory(organization=org, name='Alpha Client')
        ClientFactory(organization=org, name='Beta Client')
        
        clients = Client.objects.filter(organization=org)
        names = [c.name for c in clients]
        
        assert names == ['Alpha Client', 'Beta Client', 'Zebra Client']
    
    def test_filter_by_organization(self):
        """Filtrar clientes por organización"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        ClientFactory.create_batch(3, organization=org1)
        ClientFactory.create_batch(2, organization=org2)
        
        org1_clients = Client.objects.filter(organization=org1)
        org2_clients = Client.objects.filter(organization=org2)
        
        assert org1_clients.count() == 3
        assert org2_clients.count() == 2
    
    def test_filter_by_active_status(self):
        """Filtrar clientes por estado activo"""
        org = OrganizationFactory()
        
        ClientFactory.create_batch(3, organization=org, is_active=True)
        ClientFactory.create_batch(2, organization=org, is_active=False)
        
        active_clients = Client.objects.filter(organization=org, is_active=True)
        inactive_clients = Client.objects.filter(organization=org, is_active=False)
        
        assert active_clients.count() == 3
        assert inactive_clients.count() == 2
