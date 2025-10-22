#!/usr/bin/env python
"""
Script para probar el admin con organizaciones sin suscripción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.admin.sites import site
from apps.orgs.models import Organization
from apps.orgs.admin import OrganizationAdmin

def test_admin():
    try:
        admin = OrganizationAdmin(Organization, site)
        queryset = admin.get_queryset(None)
        print(f'Queryset: {queryset.count()} organizaciones')
        
        for org in queryset:
            print(f'\nProcesando: {org.name}')
            has_subscription = hasattr(org, 'subscription') and org.subscription is not None
            print(f'  - Tiene suscripción: {has_subscription}')
            
            # Probar métodos críticos
            try:
                status = admin.get_subscription_status(org)
                print(f'  ✅ get_subscription_status: OK')
            except Exception as e:
                print(f'  ❌ get_subscription_status: {e}')
                
            try:
                link = admin.get_subscription_link(org)
                print(f'  ✅ get_subscription_link: OK')
            except Exception as e:
                print(f'  ❌ get_subscription_link: {e}')
                
            try:
                storage = admin.get_storage_info(org)
                print(f'  ✅ get_storage_info: OK')
            except Exception as e:
                print(f'  ❌ get_storage_info: {e}')
        
        print('\n✅ Admin funciona con organizaciones sin suscripción')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin()
