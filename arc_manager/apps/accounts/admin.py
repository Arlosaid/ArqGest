from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import User
from apps.users.utils import (
    send_welcome_reminder_email, 
    send_new_user_email, 
    generate_random_password,
    send_user_credentials_email,
    send_welcome_email,
    test_email_configuration
)
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# --- Recurso para Import/Export ---

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organization__name', 'is_active', 'is_staff', 'is_org_admin', 'date_joined')
        export_order = fields

# --- Formularios ---

class UserCreationForm(forms.ModelForm):
    """Formulario para crear nuevos usuarios con contraseña automática."""
    email = forms.EmailField(required=True, label="Correo electrónico")
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellido")
    
    # Campo informativo para mostrar que se generará automáticamente
    password_info = forms.CharField(
        label="Contraseña",
        initial="Se generará automáticamente y se enviará por correo",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        required=False,
        help_text="La contraseña se generará automáticamente y se enviará al usuario por correo electrónico."
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'organization')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Generar contraseña automáticamente
        password = generate_random_password()
        user.set_password(password)
        # Forzar cambio de contraseña en primer login
        user.password_change_required = True
        if commit:
            user.save()
            # Enviar credenciales por email automáticamente
            try:
                send_new_user_email(user, password)
            except Exception as e:
                # Log el error pero no fallar la creación del usuario
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error enviando credenciales a {user.email}: {str(e)}")
        return user


class UserChangeForm(forms.ModelForm):
    """Formulario para actualizar usuarios."""
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'is_active', 'is_staff', 
                   'is_org_admin', 'password_change_required', 'organization')

    def clean_password(self):
        return self.initial["password"]

# --- ModelAdmin ---

@admin.register(User)
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_class = UserResource
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'email_status_display', 'full_name', 'get_organization_link', 'get_role_display', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_org_admin', 'organization__name', 'date_joined')
    readonly_fields = ('date_joined', 'last_login')
    
    actions = [
        'activate_users', 
        'deactivate_users', 
        'make_org_admin', 
        'remove_org_admin', 
        'force_password_reset', 
        'send_credentials_production_ready',
        'send_welcome_emails_production_ready',
        'test_email_config_action',
        'resend_welcome_email'  # Mantener la acción original como fallback
    ]
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name')}),
        ('Organización', {'fields': ('organization',)}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_org_admin', 'password_change_required'),
            'description': 'is_org_admin: Administrador de su organización | is_staff: Acceso al admin | is_superuser: Admin total'
        }),
        ('Información del sistema', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password_info'),
        }),
        ('Organización', {
            'fields': ('organization',),
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_org_admin'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'organization__name')
    ordering = ('-date_joined',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('organization')
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    full_name.short_description = 'Nombre completo'
    
    def get_organization_link(self, obj):
        if obj.organization:
            org_url = reverse('admin:orgs_organization_change', args=[obj.organization.pk])
            return format_html('<a href="{}">{}</a>', org_url, obj.organization.name)
        return 'Sin organización'
    get_organization_link.short_description = 'Organización'
    
    def get_role_display(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color: red; font-weight: bold;">🔑 Superusuario</span>')
        elif obj.is_staff:
            return format_html('<span style="color: blue; font-weight: bold;">👔 Staff</span>')
        elif obj.is_org_admin:
            return format_html('<span style="color: green; font-weight: bold;">👨‍💼 Admin Org</span>')
        else:
            return format_html('<span style="color: gray;">👤 Usuario</span>')
    get_role_display.short_description = 'Rol'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✅ Se activaron {updated} usuarios correctamente.", messages.SUCCESS)
    activate_users.short_description = "✅ Activar usuarios"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"❌ Se desactivaron {updated} usuarios correctamente.", messages.SUCCESS)
    deactivate_users.short_description = "❌ Desactivar usuarios"
    
    def make_org_admin(self, request, queryset):
        updated = queryset.update(is_org_admin=True)
        self.message_user(request, f"👨‍💼 Se convirtieron {updated} usuarios en administradores de organización.", messages.SUCCESS)
    make_org_admin.short_description = "👨‍💼 Hacer admin de org"
    
    def remove_org_admin(self, request, queryset):
        updated = queryset.update(is_org_admin=False)
        self.message_user(request, f"👤 Se removieron permisos de admin de org a {updated} usuarios.", messages.SUCCESS)
    remove_org_admin.short_description = "👤 Quitar admin de org"
    
    def force_password_reset(self, request, queryset):
        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain

        for user in queryset:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_path = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            reset_url = f"{request.scheme}://{domain}{reset_path}"
            
            message = format_html(
                "Enlace de reseteo para <b>{}</b>: <a href='{}' target='_blank'>{}</a>",
                user.full_name,
                reset_url,
                reset_url
            )
            messages.add_message(request, messages.INFO, message)
            
    force_password_reset.short_description = "🔑 Forzar cambio de contraseña"

    def resend_welcome_email(self, request, queryset):
        import logging
        
        logger = logging.getLogger(__name__)
        
        success_count = 0
        error_count = 0
        
        total_users = queryset.count()
        logger.info(f"🚀 Iniciando envío directo de credenciales a {total_users} usuarios")
        
        for i, user in enumerate(queryset, 1):
            try:
                logger.info(f"📧 Procesando usuario {i}/{total_users}: {user.email}")

                # Generar nueva contraseña temporal
                new_password = generate_random_password()
                user.set_password(new_password)
                # Forzar cambio de contraseña en próximo login
                user.password_change_required = True
                user.save()
                
                # Enviar credenciales usando la función directa de utils
                if send_new_user_email(user, new_password, request):
                    success_count += 1
                    logger.info(f"✅ Email enviado exitosamente para {user.email}")
                else:
                    error_count += 1
                    logger.error(f"❌ Error enviando email para {user.email}")
                        
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error procesando usuario {user.email}: {str(e)}")
        
        # Mostrar resumen detallado
        logger.info(f"📊 Resumen: {success_count} exitosos, {error_count} fallidos")

        
        # Mensajes de resultado
        if success_count > 0:
            self.message_user(request, f"✅ Se enviaron {success_count} correos exitosamente.", messages.SUCCESS)

        if error_count > 0:
            self.message_user(request, f"❌ {error_count} correos fallaron al enviarse. Revisa los logs.", messages.ERROR)
            
    resend_welcome_email.short_description = "📧 Reenviar credenciales de acceso"

    # ========================================
    # 🚀 NUEVAS ACCIONES PRODUCTION-READY
    # ========================================

    def send_credentials_production_ready(self, request, queryset):
        """
        🚀 Versión final de envío de credenciales con todas las optimizaciones
        """
        from django.db import transaction
        
        # Verificar configuración antes de empezar
        if not test_email_configuration():
            self.message_user(
                request,
                "❌ Error de configuración de email. Revisa las variables de entorno AWS SES.",
                level=messages.ERROR
            )
            return
        
        users_count = queryset.count()
        
        # Límite de seguridad
        if users_count > 20:
            self.message_user(
                request,
                f"⚠️ Límite de seguridad: máximo 20 usuarios por lote. Seleccionaste {users_count}.",
                level=messages.WARNING
            )
            return
        
        logger.info(f"🚀 [ADMIN] Iniciando envío de credenciales a {users_count} usuarios")
        
        processed_users = []
        skipped_users = []
        error_users = []
        
        # Procesar usuarios con transacción
        with transaction.atomic():
            for user in queryset:
                try:
                    # Validar email
                    if not user.email or '@' not in user.email:
                        skipped_users.append(f"{user.username or user.first_name or 'Usuario'} (sin email válido)")
                        logger.warning(f"⚠️ [ADMIN] Usuario {user.username} sin email válido")
                        continue
                    
                    # Generar contraseña segura
                    temp_password = generate_random_password(length=12)
                    
                    # Actualizar contraseña
                    user.set_password(temp_password)
                    user.password_change_required = True  # Forzar cambio
                    user.save(update_fields=['password', 'password_change_required'])
                    
                    # Enviar email (asíncrono) - pasando el objeto user completo
                    username = user.username or user.first_name or user.email.split('@')[0]
                    success = send_user_credentials_email(
                        user_email=user.email,
                        password=temp_password,
                        username=username,
                        user_obj=user  # Pasar el objeto user completo para usar tus templates
                    )
                    
                    if success:
                        processed_users.append({
                            'username': username,
                            'email': user.email
                        })
                        logger.info(f"✅ [ADMIN] Usuario {username} procesado - Email programado")
                    else:
                        error_users.append(f"{username} (error de envío)")
                        logger.error(f"❌ [ADMIN] Error programando email para {username}")
                        
                except Exception as e:
                    username = user.username or user.first_name or user.email
                    error_users.append(f"{username} (excepción: {str(e)})")
                    logger.error(f"❌ [ADMIN] Excepción procesando {username}: {e}")
        
        # Mostrar resultados
        success_count = len(processed_users)
        skip_count = len(skipped_users)
        error_count = len(error_users)
        
        if success_count > 0:
            success_emails = [u['email'] for u in processed_users]
            if success_count <= 3:
                email_list = ', '.join(success_emails)
            else:
                email_list = f"{', '.join(success_emails[:3])}... (+{success_count-3} más)"
                
            self.message_user(
                request,
                f"✅ Credenciales actualizadas y emails programados para {success_count} usuarios: {email_list}",
                level=messages.SUCCESS
            )
        
        if skip_count > 0:
            self.message_user(
                request,
                f"⚠️ {skip_count} usuarios omitidos: {', '.join(skipped_users[:3])}{'...' if skip_count > 3 else ''}",
                level=messages.WARNING
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"❌ {error_count} errores: {', '.join(error_users[:3])}{'...' if error_count > 3 else ''}",
                level=messages.ERROR
            )
        
        # Mensaje informativo
        if success_count > 0:
            self.message_user(
                request,
                f"📡 Los {success_count} emails se están enviando en segundo plano. "
                f"Revisa los logs del servidor para seguimiento detallado.",
                level=messages.INFO
            )

    send_credentials_production_ready.short_description = "📧 Enviar credenciales (Production Ready)"

    def send_welcome_emails_production_ready(self, request, queryset):
        """
        🎉 Versión optimizada de emails de bienvenida
        """
        # Filtrar usuarios con email válido
        users_with_email = []
        for user in queryset:
            if user.email and '@' in user.email:
                users_with_email.append(user)
        
        users_count = len(users_with_email)
        
        if users_count == 0:
            self.message_user(
                request,
                "⚠️ Ningún usuario seleccionado tiene email válido configurado",
                level=messages.WARNING
            )
            return
        
        if users_count > 15:
            self.message_user(
                request,
                f"⚠️ Límite para emails de bienvenida: máximo 15 usuarios. Seleccionaste {users_count}.",
                level=messages.WARNING
            )
            return
        
        logger.info(f"🎉 [ADMIN] Iniciando envío de bienvenida a {users_count} usuarios")
        
        processed_emails = []
        error_emails = []
        
        for user in users_with_email:
            try:
                username = user.username or user.first_name or user.email.split('@')[0]
                success = send_welcome_email(user.email, username)
                
                if success:
                    processed_emails.append(user.email)
                    logger.info(f"🎉 [ADMIN] Bienvenida programada para {username}")
                else:
                    error_emails.append(user.email)
                    logger.error(f"❌ [ADMIN] Error programando bienvenida para {username}")
                    
            except Exception as e:
                error_emails.append(user.email)
                logger.error(f"❌ [ADMIN] Excepción en bienvenida para {user.username}: {e}")
        
        # Mostrar resultados
        success_count = len(processed_emails)
        error_count = len(error_emails)
        
        if success_count > 0:
            self.message_user(
                request,
                f"🎉 Emails de bienvenida programados para {success_count} usuarios. "
                f"Se enviarán en segundo plano.",
                level=messages.SUCCESS
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"❌ {error_count} errores en el envío de bienvenida",
                level=messages.ERROR
            )

    send_welcome_emails_production_ready.short_description = "🎉 Enviar emails de bienvenida"

    def test_email_config_action(self, request, queryset):
        """
        🧪 Acción para testing de configuración de email
        """
        logger.info("🧪 [ADMIN] Test de configuración solicitado")
        
        # Test de configuración
        config_ok = test_email_configuration()
        
        if config_ok:
            self.message_user(
                request,
                "✅ Configuración de email correcta. Revisa logs para detalles.",
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "❌ Problemas en configuración de email. Revisa logs para detalles.",
                level=messages.ERROR
            )

    test_email_config_action.short_description = "🧪 Test configuración de email"

    def email_status_display(self, obj):
        """
        📧 Muestra el estado del email en el listado del admin
        """
        if not obj.email:
            return format_html('<span style="color: #dc3545;">❌ Sin email</span>')
        
        # Validación básica
        if '@' not in obj.email or '.' not in obj.email.split('@')[-1]:
            return format_html('<span style="color: #fd7e14;">⚠️ Email inválido</span>')
        
        # Email válido
        return format_html('<span style="color: #198754;">✅ {}</span>', obj.email)

    email_status_display.short_description = 'Estado Email'
