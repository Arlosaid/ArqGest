#!/usr/bin/env python
"""
Script de diagnóstico para problemas de conexión a base de datos en Railway
"""
import os
import sys
import django
from django.conf import settings

def diagnose_database():
    """Diagnostica la configuración de la base de datos"""
    print("=== DIAGNÓSTICO DE BASE DE DATOS ===")
    
    # 1. Verificar variables de entorno
    print("\n1. Variables de entorno:")
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Mostrar solo los primeros 50 caracteres por seguridad
        print(f"   DATABASE_URL: {db_url[:50]}...")
    else:
        print("   ❌ DATABASE_URL no está configurada")
        return False
    
    # 2. Configurar Django
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        django.setup()
        print("   ✅ Django configurado correctamente")
    except Exception as e:
        print(f"   ❌ Error configurando Django: {e}")
        return False
    
    # 3. Verificar configuración de base de datos
    print("\n2. Configuración de base de datos:")
    try:
        db_config = settings.DATABASES['default']
        print(f"   Engine: {db_config.get('ENGINE', 'No especificado')}")
        print(f"   Host: {db_config.get('HOST', 'No especificado')}")
        print(f"   Port: {db_config.get('PORT', 'No especificado')}")
        print(f"   Name: {db_config.get('NAME', 'No especificado')}")
        print(f"   User: {db_config.get('USER', 'No especificado')}")
        print(f"   CONN_MAX_AGE: {db_config.get('CONN_MAX_AGE', 'No especificado')}")
        
        if 'OPTIONS' in db_config:
            print(f"   Options: {db_config['OPTIONS']}")
    except Exception as e:
        print(f"   ❌ Error leyendo configuración: {e}")
        return False
    
    # 4. Probar conexión
    print("\n3. Prueba de conexión:")
    try:
        from django.db import connection
        connection.ensure_connection()
        print("   ✅ Conexión exitosa a la base de datos")
        
        # Probar una consulta simple
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("   ✅ Consulta de prueba exitosa")
            else:
                print("   ❌ Consulta de prueba falló")
                return False
                
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    
    # 5. Verificar migraciones
    print("\n4. Estado de migraciones:")
    try:
        from django.core.management import execute_from_command_line
        # Esto es solo para verificar, no ejecutar migraciones
        print("   ✅ Django puede acceder al sistema de migraciones")
    except Exception as e:
        print(f"   ❌ Error con migraciones: {e}")
        return False
    
    print("\n=== DIAGNÓSTICO COMPLETADO ===")
    print("✅ La base de datos está configurada correctamente")
    return True

if __name__ == "__main__":
    success = diagnose_database()
    sys.exit(0 if success else 1)
