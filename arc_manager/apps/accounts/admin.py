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
    send_new_user_email, 
    generate_random_password
)
from django.core.mail import send_mail
from django.template.loader import render_to_string
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
        initial="Se generará automáticamente y se enviará por email",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        required=False,
        help_text="La contraseña se generará automáticamente y se enviará al usuario por email al crear la cuenta."
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
            # Enviar credenciales automáticamente con la función simple
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]
                username = user.username or user.first_name or user.email.split('@')[0]
                
                login_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/accounts/login/"
                site_name = getattr(settings, 'SITE_NAME', 'ARC Manager')
                
                message = f"""
🎉 ¡Bienvenido a {site_name}!

Hola {full_name},

Se ha creado tu cuenta. Aquí tienes tus credenciales de acceso:

📧 Email: {user.email}
👤 Usuario: {username}
🔒 Contraseña: {password}

🚀 Acceder: {login_url}

💡 Por seguridad, cambia esta contraseña después de tu primer acceso.

---
{site_name} - Sistema de Gestión
Este mensaje fue generado automáticamente.
                """
                
                send_mail(
                    subject=f'Bienvenido a {site_name} - Tus credenciales',
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True  # No fallar la creación si hay error de email
                )
                
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
        'send_credentials_simple'
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

    def send_credentials_simple(self, request, queryset):
        """
        📧 Envío simple y directo de credenciales sin threads
        Optimizado para Railway con timeouts cortos
        """
        import logging
        from django.conf import settings
        
        logger = logging.getLogger(__name__)
        
        # Límite de seguridad
        users_count = queryset.count()
        if users_count > 5:
            self.message_user(
                request,
                f"⚠️ Por seguridad, máximo 5 usuarios por vez. Seleccionaste {users_count}.",
                level=messages.WARNING
            )
            return
        
        # Verificar configuración básica
        if not all([
            getattr(settings, 'EMAIL_HOST', None),
            getattr(settings, 'EMAIL_HOST_USER', None),
            getattr(settings, 'EMAIL_HOST_PASSWORD', None),
            getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        ]):
            self.message_user(
                request,
                "❌ Configuración de email incompleta. Revisa las variables de entorno.",
                level=messages.ERROR
            )
            return
        
        logger.info(f"📧 [ADMIN_SIMPLE] Iniciando envío a {users_count} usuarios")
        
        success_count = 0
        error_count = 0
        processed_emails = []
        error_details = []
        
        for user in queryset:
            try:
                # Validar email
                if not user.email or '@' not in user.email:
                    error_count += 1
                    error_details.append(f"{user.first_name or 'Usuario'} - sin email válido")
                    continue
                
                # Generar nueva contraseña
                new_password = generate_random_password()
                user.set_password(new_password)
                user.password_change_required = True
                user.save(update_fields=['password', 'password_change_required'])
                
                # Preparar contenido del email
                full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]
                username = user.username or user.first_name or user.email.split('@')[0]
                
                login_url = f"{getattr(settings, 'SITE_URL', request.build_absolute_uri('/'))}/accounts/login/"
                site_name = getattr(settings, 'SITE_NAME', 'ARC Manager')
                
                # Email en texto plano simple
                message = f"""
🎉 ¡Bienvenido a {site_name}!

Hola {full_name},

Se han actualizado tus credenciales de acceso:

📧 Email: {user.email}
👤 Usuario: {username}
🔒 Nueva contraseña: {new_password}

🚀 Acceder: {login_url}

💡 Por seguridad, cambia esta contraseña después de tu primer acceso.

---
{site_name} - Sistema de Gestión
Este mensaje fue generado automáticamente.
                """
                
                # Enviar email simple y directo
                logger.info(f"📤 [ADMIN_SIMPLE] Enviando a {user.email}...")
                
                result = send_mail(
                    subject=f'Credenciales actualizadas - {site_name}',
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                
                if result:
                    success_count += 1
                    processed_emails.append(user.email)
                    logger.info(f"✅ [ADMIN_SIMPLE] Enviado a {user.email}")
                else:
                    error_count += 1
                    error_details.append(f"{user.email} - send_mail retornó 0")
                    logger.error(f"❌ [ADMIN_SIMPLE] Falló envío a {user.email}")
                    
            except Exception as e:
                error_count += 1
                error_details.append(f"{user.email} - {str(e)[:50]}...")
                logger.error(f"❌ [ADMIN_SIMPLE] Error con {user.email}: {str(e)}")
        
        # Mostrar resultados
        if success_count > 0:
            email_list = ', '.join(processed_emails)
            self.message_user(
                request,
                f"✅ Credenciales enviadas exitosamente a {success_count} usuarios: {email_list}",
                level=messages.SUCCESS
            )
        
        if error_count > 0:
            error_summary = '; '.join(error_details[:3])
            if len(error_details) > 3:
                error_summary += f"... (+{len(error_details)-3} más)"
            
            self.message_user(
                request,
                f"❌ {error_count} errores: {error_summary}",
                level=messages.ERROR
            )
        
        logger.info(f"📊 [ADMIN_SIMPLE] Resumen: {success_count} éxitos, {error_count} errores")
        
    send_credentials_simple.short_description = "📧 Enviar credenciales (Simple)"

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
