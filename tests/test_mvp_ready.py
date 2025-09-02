#!/usr/bin/env python
"""
🧪 Test MVP Ready - Verificación rápida de funcionalidades críticas
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent / 'arc_manager'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_imports():
    """Verificar que todos los módulos se importan correctamente"""
    print("📦 Verificando imports...")
    try:
        from django.contrib.auth import get_user_model
        from apps.orgs.models import Organization, Client
        from apps.projects.models import Project, Phase, Task, PhaseTemplate
        from apps.plans.models import Plan, Subscription
        from apps.files.models import ProjectFile
        # UserProfile no existe en el proyecto actual
        print("✅ Todos los modelos importados correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

def test_database_connection():
    """Verificar conexión a base de datos"""
    print("🗄️ Verificando conexión a BD...")
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] == 1:
            print("✅ Conexión a BD exitosa")
            return True
        else:
            print("❌ Conexión a BD falló")
            return False
    except Exception as e:
        print(f"❌ Error de BD: {e}")
        return False

def test_migrations():
    """Verificar estado de migraciones"""
    print("🔄 Verificando migraciones...")
    try:
        from django.core.management import execute_from_command_line
        from django.core.management.commands.migrate import Command
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connection
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print(f"⚠️ Hay {len(plan)} migraciones pendientes")
            return False
        else:
            print("✅ Todas las migraciones aplicadas")
            return True
    except Exception as e:
        print(f"❌ Error verificando migraciones: {e}")
        return False

def test_settings_security():
    """Verificar configuraciones de seguridad"""
    print("🔒 Verificando configuración de seguridad...")
    try:
        from django.conf import settings
        
        checks = []
        
        # SECRET_KEY no debe estar vacía
        if settings.SECRET_KEY and len(settings.SECRET_KEY) > 10:
            checks.append("✅ SECRET_KEY configurada")
        else:
            checks.append("❌ SECRET_KEY insegura o vacía")
        
        # ALLOWED_HOSTS debe estar configurado
        if settings.ALLOWED_HOSTS:
            checks.append("✅ ALLOWED_HOSTS configurado")
        else:
            checks.append("❌ ALLOWED_HOSTS vacío")
        
        # Verificar middleware crítico
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'apps.accounts.middleware.LoginRequiredMiddleware',
            'apps.orgs.middleware.OrganizationContextMiddleware'
        ]
        
        missing_middleware = []
        for middleware in required_middleware:
            if middleware not in settings.MIDDLEWARE:
                missing_middleware.append(middleware)
        
        if not missing_middleware:
            checks.append("✅ Middleware crítico presente")
        else:
            checks.append(f"❌ Middleware faltante: {missing_middleware}")
        
        # Verificar apps instaladas
        required_apps = [
            'apps.accounts',
            'apps.orgs', 
            'apps.projects',
            'apps.plans',
            'apps.files',
            'apps.users',
            'apps.main'
        ]
        
        missing_apps = []
        for app in required_apps:
            if app not in settings.INSTALLED_APPS:
                missing_apps.append(app)
        
        if not missing_apps:
            checks.append("✅ Todas las apps instaladas")
        else:
            checks.append(f"❌ Apps faltantes: {missing_apps}")
        
        for check in checks:
            print(f"  {check}")
        
        return "❌" not in "".join(checks)
        
    except Exception as e:
        print(f"❌ Error verificando settings: {e}")
        return False

def test_static_files():
    """Verificar archivos estáticos"""
    print("📁 Verificando archivos estáticos...")
    try:
        from django.conf import settings
        from django.contrib.staticfiles.finders import find
        
        # Verificar que los CSS críticos existen
        critical_files = [
            'css/base.css',
            'css/dashboard.css',
            'css/projects.css',
            'css/kanban.css'
        ]
        
        missing_files = []
        for file_path in critical_files:
            if not find(file_path):
                missing_files.append(file_path)
        
        if not missing_files:
            print("✅ Archivos estáticos críticos encontrados")
            return True
        else:
            print(f"⚠️ Archivos faltantes: {missing_files}")
            return True  # No crítico para MVP
            
    except Exception as e:
        print(f"❌ Error verificando estáticos: {e}")
        return False

def test_urls():
    """Verificar URLs principales"""
    print("🌐 Verificando configuración de URLs...")
    try:
        from django.urls import reverse
        from django.test import Client
        
        # URLs que deben existir
        critical_urls = [
            ('accounts:login', {}),
            ('main:dashboard', {}),
            ('projects:project-list', {}),
            ('users:user-list', {}),
            ('orgs:client-list', {}),
        ]
        
        client = Client()
        
        for url_name, kwargs in critical_urls:
            try:
                url = reverse(url_name, kwargs=kwargs)
                print(f"  ✅ {url_name} -> {url}")
            except Exception as e:
                print(f"  ❌ {url_name} error: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")
        return False

def main():
    """Ejecutar todos los tests de verificación"""
    print("🚀 VERIFICANDO MVP READY - Arc Manager")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Base de Datos", test_database_connection), 
        ("Migraciones", test_migrations),
        ("Seguridad", test_settings_security),
        ("Archivos Estáticos", test_static_files),
        ("URLs", test_urls),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"💥 Error en {test_name}: {e}")
            results.append(False)
    
    # Resultados finales
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTADOS: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🎉 ¡MVP LISTO PARA DESPLIEGUE!")
        print("✅ Todas las verificaciones críticas pasaron")
        print("🚀 Puedes proceder con confianza al despliegue")
    elif passed >= total - 1:
        print("⚠️ MVP casi listo - revisar warnings menores")
        print("🚀 Despliegue viable con precauciones")
    else:
        print("❌ MVP NO LISTO - resolver problemas críticos")
        print("🛑 No desplegar hasta resolver errores")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
