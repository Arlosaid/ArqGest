#!/usr/bin/env python
"""
🧪 Smoke Tests Automatizados - Arc Manager MVP
Verifica que las funcionalidades críticas funcionen correctamente
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent / 'arc_manager'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.orgs.models import Organization, Client as OrgClient
from apps.projects.models import Project, Phase, Task
from apps.plans.models import Plan, Subscription

User = get_user_model()

def create_test_data():
    """Crear datos de prueba básicos"""
    print("📊 Creando datos de prueba...")
    
    # Crear organización
    org, created = Organization.objects.get_or_create(
        name="Estudio de Arquitectura Test",
        defaults={
            'description': 'Organización de prueba para smoke tests',
            'is_active': True
        }
    )
    
    # Crear usuario admin
    admin_user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'first_name': 'Admin',
            'last_name': 'Test',
            'organization': org,
            'role': 'ORG_ADMIN',
            'is_staff': True
        }
    )
    if created:
        admin_user.set_password('test123456')
        admin_user.save()
    
    # Crear usuario normal
    user, created = User.objects.get_or_create(
        username='user_test',
        defaults={
            'email': 'user@test.com',
            'first_name': 'Usuario',
            'last_name': 'Test',
            'organization': org,
            'role': 'COLLABORATOR'
        }
    )
    if created:
        user.set_password('test123456')
        user.save()
    
    # Crear cliente
    client, created = OrgClient.objects.get_or_create(
        name="Cliente Test S.A.",
        organization=org,
        defaults={
            'email': 'cliente@test.com',
            'phone': '55 1234 5678',
            'contact_person': 'Juan Cliente'
        }
    )
    
    # Crear plan básico
    plan, created = Plan.objects.get_or_create(
        name="Plan Básico Test",
        defaults={
            'description': 'Plan de prueba',
            'max_users': 5,
            'max_projects': 10,
            'max_storage_gb': 10,
            'price_monthly': 99.00,
            'is_active': True
        }
    )
    
    # Crear suscripción
    subscription, created = Subscription.objects.get_or_create(
        organization=org,
        defaults={
            'plan': plan,
            'status': 'ACTIVE'
        }
    )
    
    return org, admin_user, user, client, plan

def test_authentication():
    """Test 1: Login/Logout"""
    print("\n🔐 Test 1: Autenticación...")
    
    client = Client()
    
    # Test login exitoso
    response = client.post('/accounts/login/', {
        'username': 'admin_test',
        'password': 'test123456'
    })
    
    if response.status_code == 302:  # Redirección después de login
        print("✅ Login exitoso")
    else:
        print(f"❌ Login falló: {response.status_code}")
        return False
    
    # Test acceso a dashboard
    response = client.get('/main/')
    if response.status_code == 200:
        print("✅ Acceso a dashboard exitoso")
    else:
        print(f"❌ Dashboard inaccesible: {response.status_code}")
        return False
    
    # Test logout
    response = client.post('/accounts/logout/')
    if response.status_code == 302:
        print("✅ Logout exitoso")
    else:
        print(f"❌ Logout falló: {response.status_code}")
        return False
    
    return True

def test_project_management(org, admin_user, client_obj):
    """Test 2: Gestión de Proyectos"""
    print("\n📋 Test 2: Gestión de Proyectos...")
    
    client = Client()
    client.force_login(admin_user)
    
    # Crear proyecto
    project = Project.objects.create(
        name="Proyecto Test Casa Moderna",
        description="Proyecto de prueba para smoke test",
        organization=org,
        owner=admin_user,
        client=client_obj,
        status='ACTIVE'
    )
    
    # Crear fase
    phase = Phase.objects.create(
        name="Diseño Conceptual",
        project=project,
        status='IN_PROGRESS',
        order=1
    )
    
    # Crear tarea
    task = Task.objects.create(
        title="Elaborar planos preliminares",
        description="Crear los primeros bocetos del proyecto",
        phase=phase,
        assigned_to=admin_user,
        status='TODO',
        priority='HIGH'
    )
    
    # Test acceso a proyecto
    response = client.get(f'/projects/{project.id}/')
    if response.status_code == 200:
        print("✅ Detalle de proyecto accesible")
    else:
        print(f"❌ Detalle de proyecto inaccesible: {response.status_code}")
        return False
    
    # Test kanban
    response = client.get(f'/projects/{project.id}/kanban/')
    if response.status_code == 200:
        print("✅ Kanban accesible")
    else:
        print(f"❌ Kanban inaccesible: {response.status_code}")
        return False
    
    return True

def test_file_upload(org, admin_user):
    """Test 3: Subida de Archivos"""
    print("\n📁 Test 3: Subida de Archivos...")
    
    client = Client()
    client.force_login(admin_user)
    
    # Crear proyecto y fase para test
    project = Project.objects.create(
        name="Proyecto Test Archivos",
        organization=org,
        owner=admin_user,
        status='ACTIVE'
    )
    
    phase = Phase.objects.create(
        name="Fase Test",
        project=project,
        status='IN_PROGRESS',
        order=1
    )
    
    # Crear archivo de prueba
    test_file_content = b"Test file content for smoke test"
    test_file = SimpleUploadedFile(
        "plano_test.pdf",
        test_file_content,
        content_type="application/pdf"
    )
    
    # Test subida de archivo
    response = client.post('/files/upload/', {
        'file': test_file,
        'phase': phase.id,
        'description': 'Archivo de prueba para smoke test'
    })
    
    if response.status_code in [200, 201, 302]:
        print("✅ Subida de archivo exitosa")
    else:
        print(f"❌ Subida de archivo falló: {response.status_code}")
        return False
    
    return True

def test_user_management(org, admin_user):
    """Test 4: Gestión de Usuarios"""
    print("\n👥 Test 4: Gestión de Usuarios...")
    
    client = Client()
    client.force_login(admin_user)
    
    # Test listado de usuarios
    response = client.get('/users/')
    if response.status_code == 200:
        print("✅ Listado de usuarios accesible")
    else:
        print(f"❌ Listado de usuarios inaccesible: {response.status_code}")
        return False
    
    # Test creación de usuario (formulario)
    response = client.get('/users/create/')
    if response.status_code == 200:
        print("✅ Formulario de creación accesible")
    else:
        print(f"❌ Formulario de creación inaccesible: {response.status_code}")
        return False
    
    return True

def test_admin_panel():
    """Test 5: Panel de Administración"""
    print("\n⚙️ Test 5: Panel de Administración...")
    
    client = Client()
    
    # Test acceso al admin (sin login)
    response = client.get('/admin/')
    if response.status_code == 302:  # Redirección a login
        print("✅ Admin redirige a login correctamente")
    else:
        print(f"❌ Admin no redirige: {response.status_code}")
        return False
    
    return True

def cleanup_test_data():
    """Limpiar datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar organización test (cascade eliminará todo lo relacionado)
        org = Organization.objects.filter(name="Estudio de Arquitectura Test").first()
        if org:
            org.delete()
            print("✅ Datos de prueba eliminados")
    except Exception as e:
        print(f"⚠️ Error al limpiar: {e}")

def main():
    """Ejecutar todos los smoke tests"""
    print("🚀 INICIANDO SMOKE TESTS - Arc Manager MVP")
    print("=" * 50)
    
    try:
        # Crear datos de prueba
        org, admin_user, user, client_obj, plan = create_test_data()
        
        # Ejecutar tests
        tests = [
            test_authentication(),
            test_project_management(org, admin_user, client_obj),
            test_file_upload(org, admin_user),
            test_user_management(org, admin_user),
            test_admin_panel()
        ]
        
        # Resultados
        passed = sum(tests)
        total = len(tests)
        
        print(f"\n{'='*50}")
        print(f"📊 RESULTADOS: {passed}/{total} tests pasaron")
        
        if passed == total:
            print("🎉 ¡TODOS LOS SMOKE TESTS PASARON!")
            print("✅ Tu MVP está listo para despliegue")
        else:
            print("⚠️ Algunos tests fallaron")
            print("❌ Revisar errores antes del despliegue")
        
        # Limpiar datos de prueba
        cleanup_test_data()
        
        return passed == total
        
    except Exception as e:
        print(f"💥 Error crítico en smoke tests: {e}")
        cleanup_test_data()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
