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
from apps.users.utils import send_welcome_reminder_email, send_new_user_email, generate_random_password
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

    list_display = ('email', 'full_name', 'get_organization_link', 'get_role_display', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_org_admin', 'organization__name', 'date_joined')
    readonly_fields = ('date_joined', 'last_login')
    
    actions = ['activate_users', 'deactivate_users', 'make_org_admin', 'remove_org_admin', 'force_password_reset', 'resend_welcome_email']
    
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
        import time
        import logging
        from apps.users.tasks import send_user_credentials_email
        
        logger = logging.getLogger(__name__)
        
        success_count = 0
        error_count = 0
        
        total_users = queryset.count()
        logger.info(f"🚀 Iniciando envío ASÍNCRONO de credenciales a {total_users} usuarios")
        
        # Preparar datos de la request para la tarea asíncrona
        request_data = {
            'HTTP_HOST': request.get_host(),
            'is_secure': request.is_secure(),
        }
        
        for i, user in enumerate(queryset, 1):
            try:
                logger.info(f"📧 Procesando usuario {i}/{total_users}: {user.email}")

                # Generar nueva contraseña temporal
                new_password = generate_random_password()
                user.set_password(new_password)
                # Forzar cambio de contraseña en próximo login
                user.password_change_required = True
                user.save()
                
                # Enviar credenciales de forma ASÍNCRONA
                start_time = time.time()
                task = send_user_credentials_email.delay(user.id, new_password, request_data)
                elapsed_time = time.time() - start_time
                
                success_count += 1
                logger.info(f"✅ Email programado para {user.email} en {elapsed_time:.3f}s (Task ID: {task.id})")
                        
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Excepción programando email para {user.email}: {str(e)}")
        
        # Mostrar resumen detallado
        logger.info(f"📊 Resumen: {success_count} programados, {error_count} fallidos")

        
        # Mensajes de resultado
        if success_count > 0:
            self.message_user(request, f"✅ Se programaron {success_count} correos para envío asíncrono.", messages.SUCCESS)

        if error_count > 0:
            self.message_user(request, f"❌ {error_count} correos fallaron al programarse. Revisa los logs.", messages.ERROR)
            
    resend_welcome_email.short_description = "📧 Reenviar credenciales de acceso"
