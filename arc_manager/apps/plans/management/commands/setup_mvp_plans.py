from django.core.management.base import BaseCommand
from django.db import transaction
from apps.plans.models import Plan
import json

class Command(BaseCommand):
    help = 'Configura los planes básicos para el MVP simplificado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir planes existentes',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        plans_config = [
            {
                'name': 'trial',
                'display_name': 'Prueba Gratuita',
                'description': 'Período de prueba para evaluar el sistema.',
                'price': 0.00,
                'max_users': 5,
                'max_storage_gb': 10,
                'trial_days': 30,
                'grace_period_days': 5,
                'is_active': True,
            },
            {
                'name': 'basic',
                'display_name': 'Plan Básico',
                'description': 'Plan básico para equipos.',
                'price': 299.00,
                'max_users': 10,
                'max_storage_gb': 100,
                'trial_days': 0,
                'grace_period_days': 5,
                'is_active': True,
            }
        ]

        self.stdout.write("🚀 Configurando planes para MVP (versión simplificada)...")
        
        with transaction.atomic():
            created_count = 0
            updated_count = 0
            
            for plan_data in plans_config:
                plan_name = plan_data['name']
                
                try:
                    plan, created = Plan.objects.get_or_create(
                        name=plan_name,
                        defaults=plan_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Creado: {plan.display_name}")
                        )
                    elif force:
                        for key, value in plan_data.items():
                            setattr(plan, key, value)
                        plan.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f"🔄 Actualizado: {plan.display_name}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Ya existe: {plan.display_name} (usa --force para actualizar)")
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error creando {plan_name}: {str(e)}")
                    )

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN DE CONFIGURACIÓN"))
        self.stdout.write("="*50)
        
        if created_count > 0:
            self.stdout.write(f"✅ Planes creados: {created_count}")
        if updated_count > 0:
            self.stdout.write(f"🔄 Planes actualizados: {updated_count}")
            
        active_plans = Plan.objects.filter(is_active=True).order_by('price')
        self.stdout.write(f"\n📋 Planes activos ({active_plans.count()}):")
        
        for plan in active_plans:
            price_display = f"${plan.price:,.0f} MXN" if plan.price > 0 else "Gratis"
            self.stdout.write(f"  • {plan.display_name} - {price_display}")
            self.stdout.write(f"    👥 {plan.max_users} usuarios | ⏳ {plan.trial_days} días de prueba")

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📝 PRÓXIMOS PASOS"))
        self.stdout.write("="*50)
        self.stdout.write("1. Crea organizaciones y usuarios desde el admin de Django.")
        self.stdout.write("2. Verifica que los límites de usuarios se apliquen correctamente.")
        self.stdout.write(f"\n🎉 ¡Configuración de planes simplificada completada!") 