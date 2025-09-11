#!/usr/bin/env python
"""
Script de prueba para validar la funcionalidad de upload de archivos.
Verifica que las validaciones frontend y backend funcionen correctamente.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.files.views import upload_file
from apps.projects.models import Project, Phase
from apps.orgs.models import Organization

User = get_user_model()

def create_test_data():
    """Crear datos de prueba"""
    print("🔧 Creando datos de prueba...")
    
    # Crear organización
    org = Organization.objects.create(
        name="Test Org"
    )
    
    # Crear usuario
    user = User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        organization=org
    )
    
    # Crear proyecto
    project = Project.objects.create(
        name="Test Project",
        description="Test project for file validation",
        organization=org
    )
    
    # Crear fase
    phase = Phase.objects.create(
        name="Test Phase",
        project=project,
        order=1
    )
    
    return user, project, phase

def test_file_validation():
    """Probar validación de archivos"""
    print("🧪 Iniciando pruebas de validación de archivos...")
    
    user, project, phase = create_test_data()
    factory = RequestFactory()
    
    # Casos de prueba
    test_cases = [
        {
            "name": "archivo_valido.pdf",
            "content": b"PDF content",
            "content_type": "application/pdf",
            "should_pass": True,
            "description": "Archivo PDF válido"
        },
        {
            "name": "archivo_invalido.exe",
            "content": b"EXE content",
            "content_type": "application/x-executable",
            "should_pass": False,
            "description": "Archivo EXE no permitido"
        },
        {
            "name": "archivo_muy_grande.pdf",
            "content": b"x" * (700 * 1024 * 1024),  # 700MB
            "content_type": "application/pdf",
            "should_pass": False,
            "description": "Archivo muy grande (700MB)"
        },
        {
            "name": "imagen_valida.jpg",
            "content": b"JPEG content",
            "content_type": "image/jpeg",
            "should_pass": True,
            "description": "Imagen JPEG válida"
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 Caso {i}: {case['description']}")
        
        # Crear archivo de prueba
        uploaded_file = SimpleUploadedFile(
            name=case["name"],
            content=case["content"],
            content_type=case["content_type"]
        )
        
        # Crear request
        request = factory.post(f'/files/upload/{project.id}/{phase.id}/', {
            'files': uploaded_file
        })
        request.user = user
        request.META['HTTP_HX_REQUEST'] = 'true'
        
        try:
            response = upload_file(request, project.id, phase.id)
            
            if case["should_pass"]:
                if response.status_code == 200:
                    print(f"  ✅ PASS: Archivo válido aceptado correctamente")
                    results.append(True)
                else:
                    print(f"  ❌ FAIL: Archivo válido fue rechazado (status: {response.status_code})")
                    results.append(False)
            else:
                if response.status_code >= 400:
                    print(f"  ✅ PASS: Archivo inválido rechazado correctamente (status: {response.status_code})")
                    results.append(True)
                else:
                    print(f"  ❌ FAIL: Archivo inválido fue aceptado (status: {response.status_code})")
                    results.append(False)
                    
        except Exception as e:
            print(f"  ⚠️  ERROR: Excepción durante la prueba: {e}")
            results.append(False)
    
    # Resultados finales
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 RESULTADOS FINALES:")
    print(f"   Casos pasados: {passed}/{total}")
    print(f"   Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron.")
        return False

def test_frontend_validation():
    """Verificar que las constantes del frontend coincidan con el backend"""
    print("\n🔍 Verificando consistencia frontend-backend...")
    
    # Leer configuración del backend
    backend_max_size = float(os.environ.get('MAX_FILE_SIZE_MB', '600'))
    backend_extensions = set(os.environ.get('ALLOWED_EXTENSIONS', 
        'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF,DOC,DOCX,XLS,XLSX,PPT,PPTX,TXT,MD').split(','))
    
    print(f"   Backend max size: {backend_max_size}MB")
    print(f"   Backend extensions: {sorted(backend_extensions)}")
    
    # Leer archivo frontend
    frontend_file = Path("/app/arc_manager/apps/projects/templates/projects/partials/_files_tab.html")
    if frontend_file.exists():
        content = frontend_file.read_text()
        
        # Buscar MAX_SIZE_MB en el contenido
        if f"MAX_SIZE_MB: {int(backend_max_size)}" in content:
            print("   ✅ Tamaño máximo sincronizado")
        else:
            print("   ⚠️  Tamaño máximo puede estar desincronizado")
        
        # Verificar algunas extensiones clave
        key_extensions = ['PDF', 'JPG', 'PNG', 'DWG']
        for ext in key_extensions:
            if f"'{ext}'" in content:
                print(f"   ✅ Extensión {ext} encontrada en frontend")
            else:
                print(f"   ⚠️  Extensión {ext} no encontrada en frontend")
    else:
        print("   ❌ No se pudo leer el archivo frontend")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando pruebas de validación de archivos")
        print("=" * 50)
        
        # Ejecutar pruebas
        backend_ok = test_file_validation()
        test_frontend_validation()
        
        print("\n" + "=" * 50)
        if backend_ok:
            print("✅ RESULTADO: Sistema de validación funcionando correctamente")
        else:
            print("❌ RESULTADO: Se encontraron problemas en la validación")
            
    except Exception as e:
        print(f"💥 Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
