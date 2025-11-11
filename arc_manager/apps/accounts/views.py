from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SecureSetPasswordForm
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.conf import settings
from .forms import CustomAuthenticationForm, ForcePasswordChangeForm
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

logger = logging.getLogger('apps.accounts')
User = get_user_model()

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    authentication_form = CustomAuthenticationForm
    
    def dispatch(self, request, *args, **kwargs):
        """Process login request - Solo log en desarrollo para debugging"""
        # Log eliminado para evitar spam - el inicio de login se detecta en form_valid/form_invalid
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.get_user()
        client_ip = self.get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:200]
        
        # Configurar duración de sesión según checkbox "Recordarme"
        remember_me = form.cleaned_data.get('remember_me', False)
        if remember_me:
            self.request.session.set_expiry(2592000)  # 30 días
            session_duration = "30 días"
        else:
            self.request.session.set_expiry(604800)  # 7 días
            session_duration = "7 días"
        
        # Limpiar flags de sesión anterior
        session_keys_to_clear = [
            'admin_welcome_shown',
            'subscription_warning_expired_shown',
            'subscription_warning_expires_soon_shown', 
            'subscription_warning_user_limit_exceeded_shown',
            'subscription_warning_no_subscription_shown',
            'subscription_warning_validation_error_shown'
        ]
        for key in session_keys_to_clear:
            if key in self.request.session:
                del self.request.session[key]
        
        # Si es superuser, redirigir al admin de Django
        if user.is_superuser:
            login(self.request, user)
            
            # Obtener org_id de forma segura
            org_id = None
            org_name = "Sin organización"
            if hasattr(user, 'organization') and user.organization:
                org_id = user.organization.id
                org_name = user.organization.name
            
            # Log de seguridad CRÍTICO para superusuarios (nivel WARNING para alertas)
            logger.warning(
                f"SUPERUSER LOGIN | Email: {user.email} | ID: {user.id} | "
                f"Org: {org_name}" + (f" (ID: {org_id})" if org_id else "") + f" | "
                f"IP: {client_ip} | Sesion: {session_duration}",
                extra={
                    'user_id': user.id,
                    'organization_id': org_id
                }
            )
            
            return redirect('/admin/')
        
        # Verificar si necesita cambio de contraseña
        if getattr(user, 'password_change_required', False):
            login(self.request, user)
            logger.info(
                f"PASSWORD CHANGE REQUIRED | Email: {user.email} | IP: {client_ip}",
                extra={
                    'user_id': user.id,
                    'organization_id': user.organization_id if user.organization else None
                }
            )
            return redirect('/accounts/force-password-change/')
        
        user_info = {
            'email': user.email,
            'id': user.pk,
            'role': user.role_display(),
            'organization': user.get_organization_name(),
            'organization_id': user.organization_id if user.organization else None,
            'organization_active': user.organization.is_active if user.organization else None
        }
        
        # Proceder con el login normal
        response = super().form_valid(form)
        
        # Guardar timestamp de login en la sesión para calcular duración
        self.request.session['_auth_user_login_time'] = timezone.now().isoformat()
        
        # Log consolidado de login exitoso (UN SOLO LOG) - Incluye estado de org
        org_status = f"Org: {user_info['organization']}"
        if user_info['organization_id']:
            org_status += f" (ID: {user_info['organization_id']}, {'ACTIVA' if user_info['organization_active'] else 'INACTIVA'})"
        
        # Log según criticidad del rol
        # - WARNING para org_admin (acceso administrativo)
        # - INFO para usuarios regulares
        log_level = logger.warning if user.is_org_admin and not user.is_superuser else logger.info
        
        log_level(
            f"LOGIN EXITOSO | Email: {user_info['email']} | ID: {user_info['id']} | "
            f"Rol: {user_info['role']} | {org_status} | "
            f"IP: {client_ip} | Sesion: {session_duration}",
            extra={
                'user_id': user_info['id'],
                'organization_id': user_info['organization_id']
            }
        )
        
        return response
    
    def form_invalid(self, form):
        """Manejar login fallido con mensaje ESPECÍFICO sobre qué está mal"""
        username = form.cleaned_data.get('username', 'N/A')
        client_ip = self.get_client_ip()
        
        # Determinar el motivo EXACTO del error (UN SOLO LOG)
        error_detail = "desconocido"
        org_info = ""
        try:
            if not username or username == 'N/A':
                error_detail = "Email vacío"
            else:
                # Búsqueda case-insensitive con organización precargada
                user = User.objects.select_related('organization').filter(email__iexact=username).first()
                
                if not user:
                    error_detail = "Email NO existe"
                else:
                    # Construir información de organización
                    if user.organization:
                        org_info = f" | Org: {user.organization.name} (ID: {user.organization.id}, {'ACTIVA' if user.organization.is_active else 'INACTIVA'})"
                    else:
                        org_info = " | Org: Sin organización"
                    
                    # Determinar el motivo específico
                    if not user.is_active:
                        error_detail = "Cuenta INACTIVA"
                    elif user.organization and not user.organization.is_active and not user.is_superuser:
                        error_detail = "Organizacion INACTIVA"
                    else:
                        error_detail = "Contrasena INCORRECTA"
            
            # UN SOLO LOG WARNING - Información crítica sin ruido
            extra_context = {'user_id': None, 'organization_id': None}
            if user:
                extra_context['user_id'] = user.id
                extra_context['organization_id'] = user.organization_id if user.organization else None
            
            logger.warning(
                f"LOGIN FALLIDO | Motivo: {error_detail} | "
                f"Email: {username}{org_info} | IP: {client_ip}",
                extra=extra_context
            )
            
        except Exception as e:
            logger.error(
                f"ERROR verificando login | Email: {username} | Error: {str(e)} | IP: {client_ip}",
                extra={
                    'user_id': None,
                    'organization_id': None,
                    'error': str(e)
                },
                exc_info=True  # Incluir traceback completo
            )
        
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip

class CustomLogoutView(View):
    """Vista personalizada para logout con logging"""
    
    def get(self, request, *args, **kwargs):
        return self.logout_user(request)
    
    def post(self, request, *args, **kwargs):
        return self.logout_user(request)
    
    def logout_user(self, request):
        # Capturar información del usuario ANTES de hacer logout
        if request.user.is_authenticated:
            email = request.user.email
            user_id = request.user.pk
            client_ip = self.get_client_ip(request)
            
            # Informacion de organizacion
            org_info = ""
            org_id = None
            if hasattr(request.user, 'organization') and request.user.organization:
                org = request.user.organization
                org_id = org.id
                org_info = f" | Org: {org.name} (ID: {org.id}, {'ACTIVA' if org.is_active else 'INACTIVA'})"
            elif hasattr(request.user, 'organization'):
                org_info = " | Org: Sin organizacion"
            
            # Log de logout (nivel INFO - evento normal del sistema)
            logger.info(
                f"LOGOUT | Email: {email} | ID: {user_id}{org_info} | IP: {client_ip}",
                extra={
                    'user_id': user_id,
                    'organization_id': org_id
                }
            )
        
        # Limpiar flags de sesión específicos antes del logout
        session_keys_to_clear = [
            'admin_welcome_shown',
            'subscription_warning_expired_shown',
            'subscription_warning_expires_soon_shown', 
            'subscription_warning_user_limit_exceeded_shown',
            'subscription_warning_no_subscription_shown',
            'subscription_warning_validation_error_shown'
        ]
        for key in session_keys_to_clear:
            if key in request.session:
                del request.session[key]
        
        # Limpiar mensajes pendientes de la sesión actual
        storage = messages.get_messages(request)
        for message in storage:
            pass
        
        request.session.save()
        logout(request)
        
        return redirect('accounts:login')
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip

class SecurePasswordResetView(PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.txt'
    subject_template_name = 'auth/password_reset_subject.txt'
    html_email_template_name = 'auth/password_reset_email.html'
    success_url = '/accounts/password_reset/done/'
    
    def get_email_context_data(self, **kwargs):
        """Sobrescribir para agregar contexto personalizado"""
        context = super().get_email_context_data(**kwargs)
        from core.email_utils import get_site_protocol_and_domain
        
        protocol, domain = get_site_protocol_and_domain()
        context.update({
            'protocol': protocol,
            'domain': domain,
            'site_name': getattr(settings, 'SITE_NAME', 'ArqGest')
        })
        return context
    
    def form_valid(self, form):
        """Sobrescribir para agregar validaciones de seguridad"""
        email = form.cleaned_data['email']
        cache_key = f"password_reset_{email}"
        client_ip = self.get_client_ip()
        
        # Verificar si ya hay una solicitud reciente (rate limiting)
        if cache.get(cache_key):
            logger.warning(
                f"PASSWORD RESET BLOQUEADO | Email: {email} | IP: {client_ip} | "
                f"Razón: Solicitud reciente"
            )
            messages.info(self.request, "Ya enviamos instrucciones. Revisa tu correo o espera 15 minutos para solicitar otro.", extra_tags='password_reset')
            return self.form_invalid(form)
        
        # Verificar si el usuario existe (UN SOLO LOG)
        try:
            # Búsqueda case-insensitive
            user_exists = User.objects.filter(email__iexact=email, is_active=True).exists()
            if user_exists:
                logger.info(f"PASSWORD RESET | Email: {email} | IP: {client_ip}")
            else:
                logger.warning(
                    f"PASSWORD RESET | Email NO registrado: {email} | IP: {client_ip}"
                )
        except Exception as e:
            logger.error(
                f"ERROR en password reset | Email: {email} | Error: {str(e)} | IP: {client_ip}",
                extra={
                    'user_id': None,
                    'organization_id': None,
                    'email': email,
                    'error': str(e)
                },
                exc_info=True
            )
        
        # Guardar en cache por 15 minutos para evitar spam
        cache.set(cache_key, True, timeout=900)
        
        return super().form_valid(form)
    
    def get_client_ip(self):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip


class SecurePasswordResetConfirmView(PasswordResetConfirmView):
    """Vista personalizada para confirmar password reset con logging de seguridad"""
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = SecureSetPasswordForm
    
    def get_user(self, uidb64):
        """Obtener usuario desde uidb64 con manejo de errores"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
    
    def get(self, request, *args, **kwargs):
        """Log cuando se accede al link de reset"""
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')
        user = self.get_user(uidb64)
        client_ip = self.get_client_ip()
        
        if user:
            logger.info(
                f"PASSWORD RESET TOKEN ACCEDIDO | Email: {user.email} | "
                f"IP: {client_ip} | Token: {token[:10]}..."
            )
        else:
            logger.warning(
                f"PASSWORD RESET TOKEN INVÁLIDO | UID: {uidb64} | "
                f"IP: {client_ip} | Razón: Usuario no encontrado"
            )
        
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Log cuando se completa exitosamente el password reset"""
        user = form.user
        client_ip = self.get_client_ip()
        
        logger.info(
            f"PASSWORD RESET COMPLETADO | Email: {user.email} | "
            f"IP: {client_ip}"
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Log cuando falla el password reset"""
        uidb64 = self.kwargs.get('uidb64')
        user = self.get_user(uidb64)
        client_ip = self.get_client_ip()
        
        if user:
            # Detectar el tipo específico de error
            errors = form.errors.as_data()
            
            # Si el error es por reusar la contraseña anterior, no loguear duplicado
            if 'new_password1' in errors:
                for error in errors['new_password1']:
                    if error.code == 'password_same_as_old':
                        # Ya se logueó en SecureSetPasswordForm.clean_new_password1()
                        # No loguear duplicado
                        return super().form_invalid(form)
            
            # Para otros errores (validación, token expirado, etc.)
            error_messages = []
            for field, field_errors in errors.items():
                for error in field_errors:
                    error_messages.append(f"{field}: {error.message}")
            
            razon = " | ".join(error_messages) if error_messages else "Error de validación"
            
            logger.warning(
                f"PASSWORD RESET FALLIDO | Email: {user.email} | "
                f"IP: {client_ip} | Razón: {razon}"
            )
        
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip


@method_decorator(login_required, name='dispatch')
class ForcePasswordChangeView(View):
    """Vista para forzar cambio de contraseña en el primer login"""
    template_name = 'auth/force_password_change.html'
    
    def get(self, request):
        # Si el usuario no necesita cambiar contraseña, redirigir al dashboard
        if not getattr(request.user, 'password_change_required', False):
            logger.warning(
                f"ACCESO NO AUTORIZADO PASSWORD CHANGE | Email: {request.user.email}"
            )
            return redirect('/')
        
        form = ForcePasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        client_ip = self.get_client_ip()
        
        # Si el usuario no necesita cambiar contraseña, redirigir
        if not getattr(request.user, 'password_change_required', False):
            logger.warning(
                f"INTENTO NO AUTORIZADO PASSWORD CHANGE | Email: {request.user.email}"
            )
            return redirect('/')
        
        form = ForcePasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                user = request.user
                user.set_password(form.cleaned_data['new_password1'])
                user.password_change_required = False
                # 🐛 FIX: Explicit update_fields para asegurar persistencia del flag
                user.save(update_fields=['password', 'password_change_required'])
                
                update_session_auth_hash(request, user)
                
                logger.info(
                    f"PASSWORD CHANGE EXITOSO | Email: {user.email} | IP: {client_ip}"
                )
                messages.success(request, '¡Contraseña cambiada exitosamente! Ahora puedes acceder a todas las funciones del sistema.')
                
                return redirect('/')
            except Exception as e:
                logger.error(
                    f"ERROR PASSWORD CHANGE | Email: {request.user.email} | Error: {str(e)} | IP: {client_ip}",
                    extra={
                        'user_id': request.user.id,
                        'organization_id': request.user.organization_id if hasattr(request.user, 'organization') and request.user.organization else None,
                        'error': str(e)
                    },
                    exc_info=True
                )
                messages.error(request, 'Ocurrió un error al cambiar la contraseña. Por favor inténtalo de nuevo.')
        else:
            logger.warning(
                f"PASSWORD CHANGE FALLIDO | Email: {request.user.email} | "
                f"Errores: {form.errors.as_text()}"
            )
        
        return render(request, self.template_name, {'form': form})
    
    def get_client_ip(self):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip