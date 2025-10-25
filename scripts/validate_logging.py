#!/usr/bin/env python
"""
Script para validar que no hay duplicaciones de logs en el sistema.
Busca patrones comunes de logs duplicados.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Patrones que indican posible duplicación
DUPLICATE_PATTERNS = [
    # Login patterns
    (r'logger\.\w+.*[Ii]ntento.*login', 'Múltiples logs de intento de login'),
    (r'logger\.\w+.*[Ll]ogin.*fallido', 'Múltiples logs de login fallido'),
    (r'logger\.\w+.*[Ll]ogin.*exitoso', 'Múltiples logs de login exitoso'),
    
    # Validación patterns
    (r'logger\.\w+.*validación.*formulario', 'Múltiples logs de validación de formulario'),
    (r'logger\.\w+.*Error.*validación', 'Múltiples logs de error de validación'),
    
    # Upload patterns
    (r'logger\.info.*[Uu]pload.*progress', 'Logs de progreso de upload (debería ser DEBUG)'),
    (r'logger\.info.*[Aa]rchivo.*recibido', 'Logs INFO de archivo recibido (debería eliminarse)'),
    
    # Creación patterns
    (r'logger\.info.*Creating new', 'Logs de creación (posible ruido)'),
    (r'logger\.info.*created successfully', 'Logs de creación exitosa (posible ruido)'),
]

# Patrones que DEBEN estar en formato estructurado
STRUCTURED_PATTERNS = [
    r'login_failed',
    r'login_success', 
    r'task_status_changed',
    r'phase_status_changed',
]

def find_python_files(root_dir):
    """Encuentra todos los archivos Python en el proyecto"""
    python_files = []
    exclude_dirs = {'__pycache__', '.git', 'venv', 'env', 'migrations', 'staticfiles', 'media'}
    
    for root, dirs, files in os.walk(root_dir):
        # Excluir directorios
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_file_for_duplicates(filepath):
    """Verifica un archivo en busca de logs duplicados"""
    issues = []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
        
        # Buscar patrones sospechosos
        for pattern, description in DUPLICATE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            match_lines = []
            
            for match in matches:
                # Encontrar número de línea
                line_num = content[:match.start()].count('\n') + 1
                match_lines.append((line_num, match.group()))
            
            if match_lines:
                issues.append({
                    'file': filepath,
                    'type': 'duplicate_pattern',
                    'description': description,
                    'matches': match_lines
                })
    
    return issues

def analyze_project(root_dir):
    """Analiza todo el proyecto en busca de duplicaciones"""
    print("🔍 Analizando proyecto en busca de logs duplicados...\n")
    
    python_files = find_python_files(root_dir)
    all_issues = []
    
    for filepath in python_files:
        # Solo analizar archivos en arc_manager/apps y arc_manager/core
        if 'arc_manager' in filepath and ('apps' in filepath or 'core' in filepath):
            issues = check_file_for_duplicates(filepath)
            all_issues.extend(issues)
    
    # Agrupar por tipo
    grouped = defaultdict(list)
    for issue in all_issues:
        grouped[issue['description']].append(issue)
    
    # Imprimir resultados
    print("=" * 80)
    print("📊 RESULTADOS DEL ANÁLISIS")
    print("=" * 80)
    
    if not grouped:
        print("✅ ¡Excelente! No se encontraron patrones de logs duplicados.\n")
        return True
    
    print(f"\n⚠️  Se encontraron {len(all_issues)} posibles duplicaciones:\n")
    
    for description, issues in grouped.items():
        print(f"\n❌ {description}")
        print(f"   Encontrado en {len(issues)} ubicaciones:")
        
        for issue in issues[:3]:  # Mostrar solo las primeras 3
            rel_path = issue['file'].replace(root_dir, '').lstrip(os.sep)
            print(f"   📄 {rel_path}")
            for line_num, match_text in issue['matches'][:2]:
                print(f"      Línea {line_num}: {match_text[:80]}...")
        
        if len(issues) > 3:
            print(f"   ... y {len(issues) - 3} más")
    
    print("\n" + "=" * 80)
    print("💡 RECOMENDACIÓN:")
    print("   Revisa los archivos indicados y aplica el patrón:")
    print("   1 evento = 1 log estructurado, sin duplicaciones")
    print("=" * 80)
    
    return False

def main():
    # Directorio raíz del proyecto
    root_dir = Path(__file__).parent.parent / 'arc_manager'
    
    if not root_dir.exists():
        print(f"❌ Error: No se encontró el directorio {root_dir}")
        return
    
    success = analyze_project(str(root_dir))
    
    if success:
        print("✅ Validación exitosa - Sistema de logging limpio")
        exit(0)
    else:
        print("\n⚠️  Revisa las duplicaciones encontradas")
        exit(1)

if __name__ == '__main__':
    main()
