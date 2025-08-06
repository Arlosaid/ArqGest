from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.db.models import Q, F, Count
from apps.orgs.models import Organization
from apps.accounts.models import User
import re


class Command(BaseCommand):
    help = 'Limpiar datos inconsistentes del sistema multitenant'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar cambios',
        )
        parser.add_argument(
            '--fix-usernames',
            action='store_true',
            help='Corregir usernames problemáticos',
        )
        parser.add_argument(
            '--create-subscriptions',
            action='store_true',
            help='Crear suscripciones trial para organizaciones sin suscripción',
        )
        parser.add_argument(
            '--deactivate-orphaned',
            action='store_true',
            help='Desactivar usuarios sin organización',
        )
        parser.add_argument(
            '--remove-admin-flags',
            action='store_true',
            help='Remover flags de admin de usuarios sin organización',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip interactive confirmation when not in dry-run mode.',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Ejecutar todas las limpiezas',
        )
    
    def handle(self, *args, **options):
        is_dry_run = options['dry_run']
        skip_confirmation = options['yes']
        
        if is_dry_run:
            self.stdout.write(self.style.WARNING('🧪 MODO DRY RUN - No se realizarán cambios\n'))
        else:
            self.stdout.write(self.style.HTTP_INFO('🔧 Iniciando limpieza de datos...\n'))
            if not skip_confirmation:
                self.stdout.write(self.style.WARNING("This command will modify the database."))
                confirm = input("Are you sure you want to continue? Type 'yes' to confirm: ")
                if confirm != 'yes':
                    self.stdout.write(self.style.ERROR('Cleanup cancelled.'))
                    return

        
        changes_made = 0
        
        # Determinar qué limpiezas ejecutar
        fix_usernames = options['fix_usernames'] or options['all']
        create_subscriptions = options['create_subscriptions'] or options['all']
        deactivate_orphaned = options['deactivate_orphaned'] or options['all']
        remove_admin_flags = options['remove_admin_flags'] or options['all']
        
        if not any([fix_usernames, create_subscriptions, deactivate_orphaned, remove_admin_flags]):
            self.stdout.write(
                self.style.ERROR('❌ Debes especificar al menos una opción de limpieza o usar --all')
            )
            return
        
        # 1. Corregir usernames problemáticos
        if fix_usernames:
            changes_made += self.fix_usernames(is_dry_run)
        
        # 2. Crear suscripciones trial
        if create_subscriptions:
            changes_made += self.create_default_subscriptions(is_dry_run)
        
        # 3. Desactivar usuarios sin organización
        if deactivate_orphaned:
            changes_made += self.deactivate_orphaned_users(is_dry_run)
        
        # 4. Remover flags de admin de usuarios sin organización
        if remove_admin_flags:
            changes_made += self.remove_orphaned_admin_flags(is_dry_run)
        
        # Resumen final
        if is_dry_run:
            self.stdout.write(f'\n🧪 DRY RUN COMPLETADO: Se realizarían {changes_made} cambios')
        else:
            self.stdout.write(f'\n✅ LIMPIEZA COMPLETADA: Se realizaron {changes_made} cambios')
    
    def fix_usernames(self, is_dry_run):
        """Corregir usernames problemáticos"""
        self.stdout.write(self.style.HTTP_INFO('🏷️  Corrigiendo usernames problemáticos...'))
        
        changes = 0
        
        # 1. Usuarios con username igual al email
        users_username_email = User.objects.filter(username=F('email')).exclude(username__isnull=True)
        
        if users_username_email.exists():
            self.stdout.write(f'   Encontrados {users_username_email.count()} usuarios con username = email')
            
            for user in users_username_email:
                new_username = self.generate_username_from_name(user)
                self.stdout.write(f'   - {user.email}: {user.username} → {new_username}')
                
                if not is_dry_run:
                    user.username = new_username
                    user.save()
                
                changes += 1
        
        # 2. Usuarios sin username
        users_no_username = User.objects.filter(Q(username__isnull=True) | Q(username=''))
        
        if users_no_username.exists():
            self.stdout.write(f'   Encontrados {users_no_username.count()} usuarios sin username')
            
            for user in users_no_username:
                new_username = self.generate_username_from_name(user)
                self.stdout.write(f'   - {user.email}: (vacío) → {new_username}')
                
                if not is_dry_run:
                    user.username = new_username
                    user.save()
                
                changes += 1
        
        # 3. Usuarios con usernames duplicados
        duplicate_usernames = User.objects.values('username').annotate(
            count=Count('username')
        ).filter(count__gt=1, username__isnull=False).exclude(username='')
        
        if duplicate_usernames.exists():
            self.stdout.write(f'   Encontrados {duplicate_usernames.count()} usernames duplicados')
            
            for dup in duplicate_usernames:
                username = dup['username']
                users_with_username = User.objects.filter(username=username).order_by('id')
                
                # Mantener el primer usuario, renombrar el resto
                for i, user in enumerate(users_with_username[1:], 1):
                    new_username = f"{username}{i}"
                    
                    # Asegurar que el nuevo username sea único
                    counter = 1
                    while User.objects.filter(username=new_username).exists():
                        new_username = f"{username}{i}_{counter}"
                        counter += 1
                    
                    self.stdout.write(f'   - {user.email}: {username} → {new_username}')
                    
                    if not is_dry_run:
                        user.username = new_username
                        user.save()
                    
                    changes += 1
        
        if changes == 0:
            self.stdout.write(self.style.SUCCESS('   ✅ No se encontraron usernames problemáticos'))
        
        return changes
    
    def create_default_subscriptions(self, is_dry_run):
        """Crear suscripciones trial para organizaciones sin suscripción"""
        self.stdout.write(self.style.HTTP_INFO('📋 Creando suscripciones trial...'))
        
        orgs_no_sub = Organization.objects.filter(subscription__isnull=True)
        changes = 0
        
        if orgs_no_sub.exists():
            self.stdout.write(f'   Encontradas {orgs_no_sub.count()} organizaciones sin suscripción')
            
            for org in orgs_no_sub:
                self.stdout.write(f'   - Creando suscripción trial para: {org.name}')
                
                if not is_dry_run:
                    subscription = org._create_default_subscription()
                    if subscription:
                        changes += 1
                        self.stdout.write(f'     ✅ Suscripción creada: {subscription.plan.display_name}')
                    else:
                        self.stdout.write(f'     ❌ Error: No se pudo crear suscripción trial')
                else:
                    changes += 1
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Todas las organizaciones tienen suscripción'))
        
        return changes
    
    def deactivate_orphaned_users(self, is_dry_run):
        """Desactivar usuarios activos sin organización"""
        self.stdout.write(self.style.HTTP_INFO('👥 Desactivando usuarios sin organización...'))
        
        orphaned_users = User.objects.filter(
            organization__isnull=True,
            is_active=True,
            is_superuser=False
        )
        changes = 0
        
        if orphaned_users.exists():
            self.stdout.write(f'   Encontrados {orphaned_users.count()} usuarios activos sin organización')
            
            for user in orphaned_users:
                self.stdout.write(f'   - Desactivando: {user.email}')
                
                if not is_dry_run:
                    user.is_active = False
                    user.save()
                
                changes += 1
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No hay usuarios activos sin organización'))
        
        return changes
    
    def remove_orphaned_admin_flags(self, is_dry_run):
        """Remover flags de admin de usuarios sin organización"""
        self.stdout.write(self.style.HTTP_INFO('👑 Removiendo flags de admin huérfanos...'))
        
        orphaned_admins = User.objects.filter(
            is_org_admin=True,
            organization__isnull=True,
            is_superuser=False
        )
        changes = 0
        
        if orphaned_admins.exists():
            self.stdout.write(f'   Encontrados {orphaned_admins.count()} admins sin organización')
            
            for admin in orphaned_admins:
                self.stdout.write(f'   - Removiendo flag de admin: {admin.email}')
                
                if not is_dry_run:
                    admin.is_org_admin = False
                    admin.save()
                
                changes += 1
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No hay flags de admin huérfanos'))
        
        return changes
    
    def generate_username_from_name(self, user):
        """Generar username único basado en nombre y apellido"""
        first_name = user.first_name.lower() if user.first_name else ''
        last_name = user.last_name.lower() if user.last_name else ''
        
        # Limpiar caracteres especiales
        first_name = re.sub(r'[^a-z]', '', first_name)
        last_name = re.sub(r'[^a-z]', '', last_name)
        
        if first_name and last_name:
            base_username = f"{first_name}.{last_name}"
        elif first_name:
            base_username = first_name
        elif last_name:
            base_username = last_name
        else:
            # Fallback al email
            email_part = user.email.split('@')[0] if user.email else 'user'
            base_username = re.sub(r'[^a-z0-9]', '', email_part.lower())
        
        # Buscar username único
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exclude(pk=user.pk).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username 