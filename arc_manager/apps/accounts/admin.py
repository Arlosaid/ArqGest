from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.core.cache import cache
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
from core.structured_logging import log_error, log_info

# Configurar logger
logger = logging.getLogger('apps.accounts')

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
        
        # Almacenar la contraseña para que save_model pueda accederla
        self._generated_password = password
        
        if commit:
            user.save()
            # NOTA: El envío de email ahora se maneja en save_model() del admin
            # para garantizar que se ejecute siempre desde el admin
            logger.info(f"[ADMIN] Usuario guardado por formulario: {user.email}")
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
        'send_password_reset_email', 
        'send_credentials_simple',
        'generate_and_show_passwords',
        'clear_password_reset_throttle'
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
    
    def save_model(self, request, obj, form, change):
        """
        Método que se ejecuta cuando se guarda un usuario desde el admin.
        Si es un nuevo usuario, automáticamente envía las credenciales por email.
        Implementa logging estructurado.
        """
        is_new_user = not change  # change=False significa que es un nuevo usuario
        
        try:
            if is_new_user and isinstance(form, UserCreationForm):
                # Para nuevo usuario creado con UserCreationForm
                # El formulario ya se encargó de generar y hashear la contraseña
                password = getattr(form, '_generated_password', None)
                
                if not password:
                    # Fallback: esto no debería pasar si el formulario funcionó correctamente
                    password = generate_random_password()
                    obj.set_password(password)
                    obj.password_change_required = True
                    
                    log_error(
                        event='USER_PASSWORD_GENERATION_FALLBACK',
                        error_code='USR002',
                        error_message='No se encontró contraseña generada en formulario, usando fallback',
                        logger_name='apps.accounts',
                        user_email=obj.email
                    )
                
                # Guardar el usuario primero
                super().save_model(request, obj, form, change)
                
                # Log de creación
                log_info(
                    event='USER_CREATED',
                    message=f"Nuevo usuario creado: {obj.email}",
                    logger_name='apps.accounts',
                    user_id=obj.id,
                    user_email=obj.email,
                    organization_id=obj.organization.id if obj.organization else None,
                    organization_name=obj.organization.name if obj.organization else None,
                    is_org_admin=obj.is_org_admin,
                    created_by=request.user.email if request.user else 'Sistema'
                )
                
                # Enviar credenciales automáticamente
                try:
                    result = send_new_user_email(obj, password)
                    
                    if result:
                        messages.success(
                            request, 
                            f"Usuario creado exitosamente. Las credenciales fueron enviadas automáticamente a {obj.email}"
                        )
                    else:
                        log_error(
                            event='USER_EMAIL_SEND_FAILED',
                            error_code='USR003',
                            error_message='Falló el envío de credenciales',
                            logger_name='apps.accounts',
                            user_email=obj.email
                        )
                        
                        messages.warning(
                            request, 
                            f"Usuario creado pero falló el envío de credenciales a {obj.email}. "
                            f"Usa la acción 'Enviar credenciales' desde la lista de usuarios."
                        )
                except Exception as e:
                    log_error(
                        event='USER_EMAIL_SEND_ERROR',
                        error_code='USR004',
                        error_message=str(e),
                        logger_name='apps.accounts',
                        user_email=obj.email
                    )
                    
                    messages.error(
                        request, 
                        f"Usuario creado pero error al enviar credenciales a {obj.email}: {str(e)[:100]}... "
                        f"Usa la acción 'Enviar credenciales' desde la lista de usuarios."
                    )
            else:
                # Para usuarios existentes - capturar cambios
                if change:
                    changes = []
                    tracked_fields = {
                        'is_active': 'Estado activo',
                        'is_org_admin': 'Admin de organización',
                        'is_staff': 'Staff',
                        'organization': 'Organización'
                    }
                    
                    try:
                        original = User.objects.get(pk=obj.pk)
                        for field_name, field_label in tracked_fields.items():
                            old_value = getattr(original, field_name)
                            new_value = getattr(obj, field_name)
                            
                            if old_value != new_value:
                                # Formatear valores para logging
                                if field_name == 'organization':
                                    old_val = old_value.name if old_value else 'Sin organización'
                                    new_val = new_value.name if new_value else 'Sin organización'
                                else:
                                    old_val = str(old_value)
                                    new_val = str(new_value)
                                
                                changes.append({
                                    'field': field_name,
                                    'field_label': field_label,
                                    'old': old_val,
                                    'new': new_val
                                })
                    except User.DoesNotExist:
                        pass
                    
                    # Guardar el usuario
                    super().save_model(request, obj, form, change)
                    
                    # Log de actualización
                    if changes:
                        log_info(
                            event='USER_UPDATED',
                            message=f"Usuario {obj.email} actualizado con {len(changes)} cambio(s)",
                            logger_name='apps.accounts',
                            user_id=obj.id,
                            user_email=obj.email,
                            changes=changes,
                            updated_by=request.user.email if request.user else 'Sistema'
                        )
                else:
                    # Guardar sin cambios específicos
                    super().save_model(request, obj, form, change)
                    
        except Exception as e:
            log_error(
                event='USER_SAVE_FAILED',
                error_code='USR001',
                error_message=str(e),
                logger_name='apps.accounts',
                user_email=getattr(obj, 'email', 'Desconocido'),
                action='create' if is_new_user else 'update',
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al {'crear' if is_new_user else 'actualizar'} el usuario: {str(e)}"
            )
            
            raise
    
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
            return format_html('<span style="color: green; font-weight: bold;">Admin Org</span>')
        else:
            return format_html('<span style="color: gray;">Usuario</span>')
    get_role_display.short_description = 'Rol'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Se activaron {updated} usuarios correctamente.", messages.SUCCESS)
    activate_users.short_description = "Activar usuarios"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Se desactivaron {updated} usuarios correctamente.", messages.SUCCESS)
    deactivate_users.short_description = "Desactivar usuarios"
    
    def make_org_admin(self, request, queryset):
        updated = queryset.update(is_org_admin=True)
        self.message_user(request, f"Se convirtieron {updated} usuarios en administradores de organización.", messages.SUCCESS)
    make_org_admin.short_description = "Hacer admin de org"
    
    def remove_org_admin(self, request, queryset):
        updated = queryset.update(is_org_admin=False)
        self.message_user(request, f"Se removieron permisos de admin de org a {updated} usuarios.", messages.SUCCESS)
    remove_org_admin.short_description = "Quitar admin de org"
    
    def send_password_reset_email(self, request, queryset):
        """
        Envía email de reset de contraseña a usuarios seleccionados
        """
        from django.contrib.auth.forms import PasswordResetForm
        from core.email_utils import get_site_protocol_and_domain
        
        # Límite de seguridad
        users_count = queryset.count()
        if users_count > 10:
            self.message_user(
                request,
                f"Por seguridad, máximo 10 usuarios por vez. Seleccionaste {users_count}.",
                level=messages.WARNING
            )
            return
        
        success_count = 0
        error_count = 0
        processed_emails = []
        
        protocol, domain = get_site_protocol_and_domain()
        
        for user in queryset:
            try:
                # Validar email
                if not user.email or '@' not in user.email:
                    error_count += 1
                    continue
                
                # Limpiar throttle para este usuario si existe
                cache_key = f"password_reset_{user.email}"
                cache.delete(cache_key)
                
                # Usar el formulario de Django para enviar el reset
                form = PasswordResetForm({'email': user.email})
                if form.is_valid():
                    form.save(
                        request=request,
                        use_https=protocol == 'https',
                        domain_override=domain,
                        email_template_name='auth/password_reset_email.html',
                        subject_template_name='auth/password_reset_subject.txt',
                        html_email_template_name='auth/password_reset_email.html',
                        extra_email_context={
                            'protocol': protocol,
                            'domain': domain,
                            'site_name': 'ArqGest'
                        }
                    )
                    success_count += 1
                    processed_emails.append(user.email)
                    logger.info(f"[ADMIN] Reset email enviado a {user.email}")
                else:
                    error_count += 1
                    logger.error(f"[ADMIN] Error en formulario para {user.email}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"[ADMIN] Error enviando reset a {user.email}: {str(e)}")
        
        # Mostrar resultados
        if success_count > 0:
            email_list = ', '.join(processed_emails)
            self.message_user(
                request,
                f"Emails de reset enviados a {success_count} usuarios: {email_list}",
                level=messages.SUCCESS
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"{error_count} errores al enviar emails de reset",
                level=messages.ERROR
            )
    
    send_password_reset_email.short_description = "Enviar email de reset de contraseña"

    def send_credentials_simple(self, request, queryset):
        """
        Envío simple y directo de credenciales usando funciones existentes
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Límite de seguridad
        users_count = queryset.count()
        if users_count > 5:
            self.message_user(
                request,
                f"Por seguridad, máximo 5 usuarios por vez. Seleccionaste {users_count}.",
                level=messages.WARNING
            )
            return
        
        logger.info(f"[ADMIN] Sending credentials to {users_count} users")
        
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
                
                # Usar la función existente que ya maneja Resend
                try:
                    send_new_user_email(user, new_password)
                    success_count += 1
                    processed_emails.append(user.email)
                    # Solo logear errores, no éxitos
                except Exception as e:
                    error_count += 1
                    error_details.append(f"{user.email} - {str(e)[:50]}...")
                    logger.error(f"[ADMIN] Error sending to {user.email}: {str(e)}")
                    
            except Exception as e:
                error_count += 1
                error_details.append(f"{user.email} - {str(e)[:50]}...")
                logger.error(f"[ADMIN] Error processing {user.email}: {str(e)}")
        
        # Mostrar resultados
        if success_count > 0:
            email_list = ', '.join(processed_emails)
            self.message_user(
                request,
                f"Credenciales enviadas a {success_count} usuarios: {email_list}",
                level=messages.SUCCESS
            )
        
        if error_count > 0:
            error_summary = '; '.join(error_details[:3])
            if len(error_details) > 3:
                error_summary += f"... (+{len(error_details)-3} más)"
            
            self.message_user(
                request,
                f"{error_count} errores: {error_summary}",
                level=messages.ERROR
            )
        
        logger.info(f"[ADMIN] Summary: {success_count} success, {error_count} errors")
    
    send_credentials_simple.short_description = "Enviar credenciales por email"

    def generate_and_show_passwords(self, request, queryset):
        """
        Generar nuevas contraseñas y mostrarlas en pantalla (respaldo cuando falla email)
        """
        logger.info(f"[ADMIN] Generating passwords for {queryset.count()} users")
        
        if queryset.count() > 10:
            self.message_user(
                request,
                "Por seguridad, máximo 10 usuarios a la vez para mostrar contraseñas",
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
                
                logger.info(f"[ADMIN] Password generated for {user.email}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"[ADMIN] Error with {user.email}: {str(e)}")
        
        # Mostrar contraseñas en pantalla
        if passwords_generated:
            # Crear mensaje HTML con las contraseñas
            password_list = []
            for item in passwords_generated:
                password_list.append(
                    f"<strong>{item['name']}</strong> ({item['email']})<br>"
                    f"Email: {item['email']}<br>"
                    f"Contraseña: <code style='background:#f0f0f0;padding:2px 4px;'>{item['password']}</code><br><br>"
                )
            
            password_html = "".join(password_list)
            
            from django.utils.safestring import mark_safe
            self.message_user(
                request,
                mark_safe(
                    f"<strong>CONTRASEÑAS GENERADAS</strong> (cópialas ahora, no se mostrarán de nuevo):<br><br>"
                    f"{password_html}"
                    f"<strong>Importante:</strong> Los usuarios deberán cambiar estas contraseñas en su primer login."
                ),
                level=messages.SUCCESS
            )
            
            logger.info(f"[ADMIN] {len(passwords_generated)} passwords shown, {error_count} errors")
        else:
            self.message_user(
                request,
                "No se pudieron generar contraseñas para ningún usuario",
                level=messages.ERROR
            )
    
    generate_and_show_passwords.short_description = "Generar y mostrar contraseñas (Respaldo)"

    def clear_password_reset_throttle(self, request, queryset):
        """
        Limpia el throttle de password reset para usuarios seleccionados
        Útil cuando un email no llegó y el usuario necesita solicitar otro inmediatamente
        """
        users_count = queryset.count()
        cleared_count = 0
        
        for user in queryset:
            if user.email:
                cache_key = f"password_reset_{user.email}"
                # Verificar si existe el throttle
                if cache.get(cache_key):
                    cache.delete(cache_key)
                    cleared_count += 1
                    logger.info(f"[ADMIN] Throttle de reset limpiado para {user.email}")
        
        if cleared_count > 0:
            self.message_user(
                request,
                f"Throttle de password reset limpiado para {cleared_count} usuarios. "
                f"Ahora pueden solicitar un nuevo reset inmediatamente.",
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                f"Ninguno de los {users_count} usuarios seleccionados tenía throttle activo.",
                level=messages.INFO
            )
    
    clear_password_reset_throttle.short_description = "Limpiar bloqueo de reset de contraseña (15 min)"

    def email_status_display(self, obj):
        """
        Muestra el estado del email en el listado del admin
        """
        if not obj.email:
            return format_html('<span style="color: #dc3545;">Sin email</span>')
        
        # Validación básica
        if '@' not in obj.email or '.' not in obj.email.split('@')[-1]:
            return format_html('<span style="color: #fd7e14;">Email inválido</span>')
        
        # Email válido
        return format_html('<span style="color: #198754;">{}</span>', obj.email)

    email_status_display.short_description = 'Estado Email'
