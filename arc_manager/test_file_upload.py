#!/usr/bin/env python
"""
Script para probar la funcionalidad de subida de archivos directamente
"""
import os
import django
import tempfile
from io import BytesIO

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.projects.models import Project, Phase
from django.core.files.uploadedfile import SimpleUploadedFile

def test_file_upload():
    print("🔍 Iniciando prueba de subida de archivos...")
    
    # Obtener usuario y proyecto
    User = get_user_model()
    try:
        # Usar el usuario administrador de organización correcto
        user = User.objects.get(email='alonso.delacruzhdez@gmail.com')
        project = Project.objects.get(id=35)
        phase = project.phases.first()
        
        print(f"✅ Usuario: {user.email}")
        print(f"✅ Proyecto: {project.name} (ID: {project.id})")
        print(f"✅ Fase: {phase.name} (ID: {phase.id})")
        
        # Crear cliente de prueba con HOST correcto
        client = Client()
        client.force_login(user)
        
        # Crear archivo de prueba DOCX (similar al que causó el error)
        # Simulamos el contenido de un DOCX básico
        test_content = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00b\xe9\xd6f\xf6\x00\x00\x00'\x01\x00\x00\x13\x00\x08\x02[Content_Types].xml \xa2\x04\x02(\xa0\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        test_file = SimpleUploadedFile(
            "delaCruz_Alonso_R1_U1.docx",
            test_content * 850,  # Hacerlo similar al tamaño original (24733 bytes)
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # URL de subida
        upload_url = f"/projects/{project.id}/phases/{phase.id}/files/upload/"
        print(f"🔗 URL de subida: {upload_url}")
        
        # Realizar solicitud POST
        response = client.post(
            upload_url,
            {'files': test_file},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET=f'#files-container-{phase.id}',
            HTTP_HOST='localhost:8000'
        )
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Subida exitosa!")
            # Verificar que se creó el archivo
            updated_phase = Phase.objects.get(id=phase.id)
            files_count = updated_phase.files.count()
            print(f"📁 Archivos en la fase después de subida: {files_count}")
            
            if files_count > 0:
                latest_file = updated_phase.files.latest('uploaded_at')
                print(f"📄 Último archivo subido: {latest_file.original_filename}")
                return True
        else:
            print(f"❌ Error en la subida: {response.status_code}")
            print(f"📄 Contenido de respuesta: {response.content.decode()[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_file_upload()
    if success:
        print("\n🎉 La funcionalidad de subida de archivos funciona correctamente!")
    else:
        print("\n❌ La funcionalidad de subida de archivos tiene problemas.")
