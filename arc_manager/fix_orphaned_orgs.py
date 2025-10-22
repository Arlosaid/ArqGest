#!/usr/bin/env python
"""
Script para verificar y limpiar organizaciones huérfanas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.orgs.models import Organization
from apps.projects.models import Project

def fix_orphaned_orgs():
    print("=== ORGANIZACIONES HUÉRFANAS ===")
    orphaned_orgs = Organization.objects.filter(users__isnull=True)
    print(f"Organizaciones sin usuarios: {orphaned_orgs.count()}")
    
    for org in orphaned_orgs:
        project_count = Project.objects.filter(organization=org).count()
        print(f"ID: {org.id}, Nombre: {org.name}, Proyectos: {project_count}")
    
    print()
    print("=== VERIFICACIÓN DE PROYECTOS EN ORGANIZACIONES HUÉRFANAS ===")
    for org in orphaned_orgs:
        projects = Project.objects.filter(organization=org)
        if projects.exists():
            print(f"Organización {org.name} tiene {projects.count()} proyectos:")
            for project in projects:
                owner_email = project.owner.email if project.owner else "Sin propietario"
                print(f"  - {project.name} (Owner: {owner_email})")
        else:
            print(f"Organización {org.name} no tiene proyectos")
    
    print()
    print("=== DECISIÓN SOBRE ORGANIZACIONES HUÉRFANAS ===")
    for org in orphaned_orgs:
        project_count = Project.objects.filter(organization=org).count()
        if project_count == 0:
            print(f"Organización {org.name} (ID: {org.id}) no tiene usuarios ni proyectos - puede eliminarse")
        else:
            print(f"Organización {org.name} (ID: {org.id}) tiene {project_count} proyectos - NO eliminar")

if __name__ == "__main__":
    try:
        fix_orphaned_orgs()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
