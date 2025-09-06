#!/usr/bin/env python3
"""
Script para testear que las páginas de error personalizadas funcionen correctamente.
Ejecutar desde el directorio raíz del proyecto.
"""
import os
import sys
import requests
import json
from urllib.parse import urljoin

def test_error_pages(base_url):
    """
    Testea las páginas de error del sitio.
    """
    print(f"🧪 Testeando páginas de error en: {base_url}")
    print("-" * 50)
    
    # Test endpoints que deberían devolver páginas de error personalizadas
    test_cases = [
        {
            'url': urljoin(base_url, 'pagina-que-no-existe'),
            'expected_status': 404,
            'expected_content': 'Página no encontrada',
            'description': 'Test 404 - Página no encontrada'
        },
        {
            'url': urljoin(base_url, 'admin/secret-page/'),
            'expected_status': 403,
            'expected_content': 'Acceso denegado',
            'description': 'Test 403 - Acceso denegado (puede variar)'
        }
    ]
    
    # Si es desarrollo local, agregar rutas de test
    if 'localhost' in base_url or '127.0.0.1' in base_url:
        test_cases.extend([
            {
                'url': urljoin(base_url, 'test-400/'),
                'expected_status': 400,
                'expected_content': 'Solicitud incorrecta',
                'description': 'Test 400 - Solicitud incorrecta'
            },
            {
                'url': urljoin(base_url, 'test-403/'),
                'expected_status': 403,
                'expected_content': 'Acceso denegado',
                'description': 'Test 403 - Acceso denegado'
            },
            {
                'url': urljoin(base_url, 'test-404/'),
                'expected_status': 404,
                'expected_content': 'Página no encontrada',
                'description': 'Test 404 - Página no encontrada'
            },
            {
                'url': urljoin(base_url, 'test-500/'),
                'expected_status': 500,
                'expected_content': 'Error del servidor',
                'description': 'Test 500 - Error del servidor'
            }
        ])
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"⏳ {test_case['description']}...")
            
            response = requests.get(test_case['url'], timeout=10, allow_redirects=False)
            
            # Verificar status code
            status_ok = response.status_code == test_case['expected_status']
            
            # Verificar contenido (debe contener nuestro texto personalizado)
            content_ok = test_case['expected_content'].lower() in response.text.lower()
            
            # Verificar que NO contenga textos de Railway
            railway_error = any(phrase in response.text.lower() for phrase in [
                'application failed to respond',
                'railway',
                'request id:',
                'if this is your project',
                'help station'
            ])
            
            # Verificar que contenga "ARC Manager"
            has_branding = 'arc manager' in response.text.lower()
            
            success = status_ok and content_ok and not railway_error and has_branding
            
            result = {
                'test': test_case['description'],
                'url': test_case['url'],
                'success': success,
                'status_code': response.status_code,
                'expected_status': test_case['expected_status'],
                'has_custom_content': content_ok,
                'has_railway_error': railway_error,
                'has_branding': has_branding
            }
            
            results.append(result)
            
            if success:
                print(f"✅ {test_case['description']} - OK")
            else:
                print(f"❌ {test_case['description']} - FALLO")
                if not status_ok:
                    print(f"   Status: {response.status_code} (esperado: {test_case['expected_status']})")
                if not content_ok:
                    print(f"   Contenido personalizado no encontrado")
                if railway_error:
                    print(f"   ⚠️  Contiene errores de Railway")
                if not has_branding:
                    print(f"   Sin branding de ARC Manager")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_case['description']} - ERROR DE CONEXIÓN: {e}")
            results.append({
                'test': test_case['description'],
                'url': test_case['url'],
                'success': False,
                'error': str(e)
            })
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*50)
    
    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print(f"✅ Exitosos: {successful}/{total}")
    print(f"❌ Fallidos: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 ¡Todas las páginas de error están funcionando correctamente!")
        print("   Las páginas de error personalizadas se muestran en lugar de los errores de Railway.")
    else:
        print("\n⚠️  Algunas páginas de error necesitan atención.")
        print("   Revisa la configuración de handlers de error en core/urls.py")
    
    return results


if __name__ == '__main__':
    # Detectar URL base
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        # Intentar detectar automáticamente
        if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
            base_url = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}"
        elif os.environ.get('SITE_URL'):
            base_url = os.environ.get('SITE_URL')
        else:
            base_url = 'http://localhost:8000'
    
    # Asegurar que termine con /
    if not base_url.endswith('/'):
        base_url += '/'
    
    print(f"🚀 Testeando páginas de error en: {base_url}")
    print("   Uso: python test_error_pages.py [URL_BASE]")
    print()
    
    results = test_error_pages(base_url)
    
    # Salir con código de error si hay fallos
    if not all(r.get('success', False) for r in results):
        sys.exit(1)
