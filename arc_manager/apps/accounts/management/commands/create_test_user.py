"""
Management command para crear usuario de prueba
"""
from django.core.management.base import BaseCommand
from apps.orgs.models import Organization
from apps.accounts.models import User
from apps.plans.models import Plan, Subscription
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Crear usuario de prueba para testing'

    def handle(self, *args, **options):
        # 1. Obtener plan básico
        try:
            plan = Plan.objects.get(name='basic')
        except Plan.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Plan "basic" no encontrado')
            )
            return
        
        # 2. Crear organización
        org, org_created = Organization.objects.get_or_create(
            name='Test Organization',
            defaults={
                'description': 'Organización para pruebas de logging',
                'is_active': True,
            }
        )
        
        if org_created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Organización creada: {org.name} (ID: {org.id})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✅ Organización ya existe: {org.name} (ID: {org.id})')
            )
        
        # 3. Crear suscripción para la organización
        subscription, sub_created = Subscription.objects.get_or_create(
            organization=org,
            defaults={
                'plan': plan,
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),  # 30 días
                'subscription_status': 'basic_active',
            }
        )
        
        if sub_created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Suscripción creada: {plan.display_name} (max_users: {plan.max_users})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✅ Suscripción ya existe: {subscription.plan.display_name}')
            )
        
        # 2. Crear usuario
        user, user_created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'organization': org,
            }
        )
        
        if user_created:
            user.set_password('test123')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario creado: {user.email} (ID: {user.id})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✅ Usuario ya existe: {user.email} (ID: {user.id})')
            )
        
        self.stdout.write('\n🎯 Credenciales para probar logging:')
        self.stdout.write(f'   Email: test@example.com')
        self.stdout.write(f'   Password: test123')
        self.stdout.write(f'   User ID: {user.id}')
        self.stdout.write(f'   Organización: {org.name}')
        self.stdout.write('\n📋 Para probar:')
        self.stdout.write('   1. Login en http://localhost:8000/accounts/login/')
        self.stdout.write('   2. Probar URLs que generen 404:')
        self.stdout.write('      - http://localhost:8000/projects/999999/')
        self.stdout.write('      - http://localhost:8000/nonexistent-page/')
        self.stdout.write('   3. Ver logs: docker-compose logs web --tail=20')
