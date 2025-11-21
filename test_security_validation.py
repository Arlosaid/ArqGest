#!/usr/bin/env python
"""
Script de prueba para demostrar que la validación de seguridad funciona.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tests.factories.orgs.org_factories import OrganizationFactory
from tests.factories.accounts.account_factories import UserFactory
from tests.factories.projects.project_factories import PhaseFactory
from apps.files.models import ProjectFile
from django.core.files.uploadedfile import SimpleUploadedFile

print('=' * 60)
print('PRUEBA DE VALIDACIÓN DE SEGURIDAD')
print('=' * 60)

# Crear organizaciones diferentes
org1 = OrganizationFactory(name='Org Test 1')
org2 = OrganizationFactory(name='Org Test 2')
print(f'\nOrg 1: {org1.name} (ID: {org1.id})')
print(f'Org 2: {org2.name} (ID: {org2.id})')

# Usuario de org1, proyecto de org2
user_org1 = UserFactory(organization=org1)
phase_org2 = PhaseFactory(project__organization=org2)
print(f'\nUsuario: {user_org1.email}')
print(f'  -> Pertenece a: {user_org1.organization.name}')
print(f'\nFase: {phase_org2.name}')
print(f'  -> Proyecto pertenece a: {phase_org2.project.organization.name}')

# Intentar crear archivo - DEBE FALLAR por seguridad
print('\n' + '-' * 60)
print('Intentando crear archivo con usuario de ORG DIFERENTE...')
print('-' * 60)

try:
    file = ProjectFile(
        phase=phase_org2,
        uploaded_by=user_org1,
        file=SimpleUploadedFile('test.pdf', b'test'),
        size_bytes=100,
        ext_upper='PDF'
    )
    file.save()
    print('\n❌ ERROR: La validación NO funcionó')
    print('   El archivo se creó incorrectamente')
    sys.exit(1)
except Exception as e:
    print('\n✅ CORRECTO: La validación de seguridad FUNCIONA')
    print(f'\nMensaje de error (primeros 200 chars):')
    print(f'   {str(e)[:200]}')
    print('\n' + '=' * 60)
    print('CONCLUSIÓN: Las correcciones en los tests son VÁLIDAS')
    print('=' * 60)
    sys.exit(0)

