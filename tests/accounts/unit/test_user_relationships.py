"""
🔴 TESTS DE RELACIONES - MODELO USER (ALTA PRIORIDAD)

Estos tests verifican que las relaciones ForeignKey funcionan correctamente,
especialmente el comportamiento CASCADE que es crítico para integridad de datos.

IMPORTANCIA:
- Integridad referencial: Evitar registros huérfanos
- Seguridad: No dejar datos sensibles de usuarios eliminados
- Compliance GDPR: Right to be forgotten (borrado completo)
- Performance: Evitar búsquedas lentas de datos huérfanos
- Auditoría: Saber exactamente qué se elimina

RELACIÓN PROBADA:
- User.organization → Organization (CASCADE delete)

COMPORTAMIENTO CASCADE:
Cuando se elimina una Organization, TODOS sus usuarios se eliminan automáticamente.
Esto es intencional para:
1. Compliance GDPR: Al eliminar compañía, eliminar todos sus datos
2. Evitar usuarios huérfanos sin organization
3. Mantener integridad referencial

COBERTURA: 1/2 tests de relationships (50%)
- ✅ organization_cascade_delete
- ⏳ organization_foreignkey_basic

Autor: ARC Manager Team
Fecha: 4 Nov 2025
Fase: 2 - Alta Prioridad
"""

import pytest
from django.contrib.auth import get_user_model
from apps.orgs.models import Organization
from tests.factories import OrganizationFactory

User = get_user_model()


@pytest.mark.unit
class TestUserOrganizationRelationship:
    """
    Tests para verificar que la relación User -> Organization funciona correctamente,
    especialmente el comportamiento CASCADE en deletes.
    """
    
    def test_organization_cascade_delete(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que eliminar Organization elimina sus Users
        
        ¿POR QUÉ ES IMPORTANTE?
        - GDPR Compliance: Right to be forgotten aplica a organizaciones
        - Integridad: Evitar usuarios huérfanos sin organization
        - Seguridad: No dejar datos sensibles de empresa eliminada
        - Legal: Al cerrar cuenta, borrar TODOS los datos
        - Performance: Evitar queries lentos filtrando usuarios activos
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Crear organization con múltiples usuarios
        2. Eliminar la organization
        3. Verificar que TODOS los usuarios se eliminaron
        4. Verificar que usuarios de OTRAS organizations no se afectaron
        
        ¿QUÉ PASARÍA SI FALLA?
        - Usuarios huérfanos en DB sin organization
        - Violación GDPR: datos no eliminados completamente
        - Brecha de seguridad: acceso a datos de org eliminada
        - Problemas de integridad referencial
        - Queries lentos filtrando organization=None
        
        CASO DE USO REAL:
        - Cliente cancela suscripción → Eliminar organization
        - TODOS los empleados deben ser eliminados también
        - Usuarios de otras orgs NO deben afectarse
        
        MODELO ACTUAL:
        ```python
        organization = models.ForeignKey(
            'orgs.Organization', 
            on_delete=models.CASCADE,  # ← ESTO ES LO QUE PROBAMOS
            related_name='users',
            null=True, 
            blank=True
        )
        ```
        """
        # ARRANGE: Crear 2 organizaciones
        org_to_delete = OrganizationFactory(name="Org To Delete")
        org_to_keep = OrganizationFactory(name="Org To Keep")
        
        # Crear 3 usuarios en la org que vamos a eliminar
        users_to_delete = []
        for i in range(3):
            user = User.objects.create_user(
                email=f'delete{i}@example.com',
                password='SecurePass123!',
                first_name=f'DeleteUser{i}',
                last_name='Test',
                organization=org_to_delete
            )
            users_to_delete.append(user)
        
        # Crear 2 usuarios en la org que vamos a mantener
        users_to_keep = []
        for i in range(2):
            user = User.objects.create_user(
                email=f'keep{i}@example.com',
                password='SecurePass123!',
                first_name=f'KeepUser{i}',
                last_name='Test',
                organization=org_to_keep
            )
            users_to_keep.append(user)
        
        # Crear 1 usuario SIN organization
        user_without_org = User.objects.create_user(
            email='no_org@example.com',
            password='SecurePass123!',
            first_name='NoOrg',
            last_name='User',
            organization=None
        )
        
        # Verificar setup inicial
        assert User.objects.filter(organization=org_to_delete).count() == 3, \
            "Deberían haber 3 usuarios en org_to_delete"
        assert User.objects.filter(organization=org_to_keep).count() == 2, \
            "Deberían haber 2 usuarios en org_to_keep"
        assert User.objects.filter(organization=None).count() == 1, \
            "Debería haber 1 usuario sin organization"
        
        # Guardar IDs para verificar después
        delete_user_ids = [u.id for u in users_to_delete]
        keep_user_ids = [u.id for u in users_to_keep]
        org_to_delete_id = org_to_delete.id  # Guardar ID antes de eliminar
        
        # ACT: Eliminar la organization
        org_to_delete.delete()
        
        # ASSERT 1: Los usuarios de org_to_delete fueron eliminados
        for user_id in delete_user_ids:
            assert not User.objects.filter(id=user_id).exists(), \
                f"Usuario ID {user_id} debería haber sido eliminado con la organization"
        
        # ASSERT 2: Confirmar que NO hay usuarios de org eliminada
        assert User.objects.filter(organization_id=org_to_delete_id).count() == 0, \
            "No debería haber usuarios con organization_id de org eliminada"
        
        # ASSERT 3: Los usuarios de org_to_keep NO fueron afectados
        for user_id in keep_user_ids:
            assert User.objects.filter(id=user_id).exists(), \
                f"Usuario ID {user_id} de org_to_keep NO debería haber sido eliminado"
        
        assert User.objects.filter(organization=org_to_keep).count() == 2, \
            "org_to_keep debería seguir teniendo 2 usuarios"
        
        # ASSERT 4: El usuario sin organization NO fue afectado
        assert User.objects.filter(id=user_without_org.id).exists(), \
            "Usuario sin organization NO debería haber sido eliminado"
        
        assert User.objects.filter(organization=None).count() == 1, \
            "Debería seguir habiendo 1 usuario sin organization"
        
        # ASSERT 5: Count total de usuarios
        # Inicial: 3 (delete) + 2 (keep) + 1 (no_org) = 6
        # Después: 2 (keep) + 1 (no_org) = 3
        total_users = User.objects.count()
        assert total_users == 3, \
            f"Deberían quedar 3 usuarios (2 de org_to_keep + 1 sin org), hay {total_users}"
        
        # Limpiar
        org_to_keep.delete()
        user_without_org.delete()
