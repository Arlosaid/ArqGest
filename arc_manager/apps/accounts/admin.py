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
from import_export import resources
from import_export.admin import ImportExportModelAdmin
import logging

# Configurar logger
logger = logging.getLogger(__name__)

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
            # Enviar credenciales automáticamente usando la función existente
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
        'send_credentials_simple',
        'generate_and_show_passwords'
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
        📧 Envío simple y directo de credenciales usando funciones existentes
        """
        import logging
        
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
                
                # Usar la función existente que ya maneja Resend/SES
                try:
                    send_new_user_email(user, new_password)
                    success_count += 1
                    processed_emails.append(user.email)
                    logger.info(f"✅ [ADMIN_SIMPLE] Enviado a {user.email}")
                except Exception as e:
                    error_count += 1
                    error_details.append(f"{user.email} - {str(e)[:50]}...")
                    logger.error(f"❌ [ADMIN_SIMPLE] Error con {user.email}: {str(e)}")
                    
            except Exception as e:
                error_count += 1
                error_details.append(f"{user.email} - {str(e)[:50]}...")
                logger.error(f"❌ [ADMIN_SIMPLE] Error procesando {user.email}: {str(e)}")
        
        # Mostrar resultados
        if success_count > 0:
            email_list = ', '.join(processed_emails)
            self.message_user(
                request,
                f"✅ Credenciales enviadas a {success_count} usuarios: {email_list}",
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

    def generate_and_show_passwords(self, request, queryset):
        """
        🔑 Generar nuevas contraseñas y mostrarlas en pantalla (respaldo cuando falla email)
        """
        logger.info(f"🔑 [ADMIN_BACKUP] Iniciando generación de contraseñas para {queryset.count()} usuarios")
        
        if queryset.count() > 10:
            self.message_user(
                request,
                "⚠️ Por seguridad, máximo 10 usuarios a la vez para mostrar contraseñas",
                level=messages.WARNING
            )
            return
        
        passwords_generated = []
        error_count = 0
        
        for user in queryset:
            try:
                # Validar usuario
                if not user.email or '@' not in user.email:
                    error_count += 1
                    continue
                
                # Generar nueva contraseña
                new_password = generate_random_password()
                user.set_password(new_password)
                user.password_change_required = True
                user.save(update_fields=['password', 'password_change_required'])
                
                passwords_generated.append({
                    'name': user.full_name,
                    'email': user.email,
                    'password': new_password
                })
                
                logger.info(f"🔑 [ADMIN_BACKUP] Contraseña generada para {user.email}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ [ADMIN_BACKUP] Error con {user.email}: {str(e)}")
        
        # Mostrar contraseñas en pantalla
        if passwords_generated:
            # Crear mensaje HTML con las contraseñas
            password_list = []
            for item in passwords_generated:
                password_list.append(
                    f"<strong>{item['name']}</strong> ({item['email']})<br>"
                    f"📧 Email: {item['email']}<br>"
                    f"🔑 Contraseña: <code style='background:#f0f0f0;padding:2px 4px;'>{item['password']}</code><br><br>"
                )
            
            password_html = "".join(password_list)
            
            from django.utils.safestring import mark_safe
            self.message_user(
                request,
                mark_safe(
                    f"🔑 <strong>CONTRASEÑAS GENERADAS</strong> (cópialas ahora, no se mostrarán de nuevo):<br><br>"
                    f"{password_html}"
                    f"⚠️ <strong>Importante:</strong> Los usuarios deberán cambiar estas contraseñas en su primer login."
                ),
                level=messages.SUCCESS
            )
            
            logger.info(f"📊 [ADMIN_BACKUP] {len(passwords_generated)} contraseñas mostradas, {error_count} errores")
        else:
            self.message_user(
                request,
                "❌ No se pudieron generar contraseñas para ningún usuario",
                level=messages.ERROR
            )
    
    generate_and_show_passwords.short_description = "🔑 Generar y mostrar contraseñas (Respaldo)"

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
