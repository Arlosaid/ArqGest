from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.conf import settings
from .forms import CustomAuthenticationForm, ForcePasswordChangeForm
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger('apps.accounts')
User = get_user_model()

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    authentication_form = CustomAuthenticationForm
    
    def dispatch(self, request, *args, **kwargs):
        """Process login request"""
        # Log eliminado - se registra en form_valid/form_invalid para evitar duplicación
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.get_user()
        client_ip = self.get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:200]  # Limitar longitud
        
        # Configurar duración de sesión según checkbox "Recordarme"
        remember_me = form.cleaned_data.get('remember_me', False)
        if remember_me:
            # Extender sesión a 30 días (2592000 segundos)
            self.request.session.set_expiry(2592000)
            session_duration = "30 días"
        else:
            # Usar duración predeterminada de 7 días
            self.request.session.set_expiry(604800)
            session_duration = "7 días"
        
        # Limpiar cualquier flag de sesión anterior (para evitar mensajes cruzados)
        session_keys_to_clear = [
            'admin_welcome_shown',
            # Limpiar flags de warnings de suscripción
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
            # Hacer login primero
            login(self.request, user)
            
            # Log de seguridad CRÍTICO para superusuarios
            logger.warning(f"SUPERUSER LOGIN - Usuario: {user.email}, IP: {client_ip}, User-Agent: {user_agent[:50]}, Sesión: {session_duration}")
            
            # Redirigir directamente al admin sin mensaje
            # El mensaje se mostrará en el admin mediante el middleware
            return redirect('/admin/')
        
        # Para usuarios normales y org_admin, verificar si necesita cambio de contraseña
        if getattr(user, 'password_change_required', False):
            # Hacer login primero
            login(self.request, user)
            logger.info(f"Usuario requiere cambio de contraseña - {user.email}, IP: {client_ip}")
            # Redirigir al cambio forzado de contraseña
            return redirect('/accounts/force-password-change/')
        
        user_info = {
            'email': user.email,
            'id': user.pk,
            'role': user.role_display(),
            'organization': user.get_organization_name()
        }
        
        # Proceder con el login normal
        response = super().form_valid(form)
        
        # Registrar login exitoso con información completa para SEGURIDAD
        logger.info(
            f"LOGIN EXITOSO - Usuario: {user_info['email']} (ID: {user_info['id']}), "
            f"Rol: {user_info['role']}, Org: {user_info['organization']}, "
            f"IP: {client_ip}, Sesión: {session_duration}"
        )
        
        # Log de seguridad adicional para admins (solo org_admin, superuser ya logueó arriba)
        if user.is_org_admin and not user.is_superuser:
            logger.warning(
                "admin_login",
                extra={
                    "event": "admin_login",
                    "user": user.email,
                    "user_id": user.pk,
                    "role": "org_admin",
                    "ip": client_ip,
                    "session_duration": session_duration
                }
            )
        
        return response
    
    def form_invalid(self, form):
        # Registrar intento de login fallido con formato estructurado
        username = form.cleaned_data.get('username', 'No especificado')
        client_ip = self.get_client_ip()
        
        # Verificar si el usuario existe para determinar el motivo del fallo
        try:
            user_exists = User.objects.filter(email=username).exists()
            reason = "invalid_password" if user_exists else "user_not_found"
            
            # Un solo log estructurado con toda la información necesaria
            logger.warning(
                "login_failed",
                extra={
                    "event": "login_failed",
                    "reason": reason,
                    "user": username if not user_exists else f"hash_{username[:8]}",
                    "ip": client_ip,
                    "user_agent": self.request.META.get('HTTP_USER_AGENT', '')[:100]
                }
            )
        except Exception as e:
            logger.error(f"Error al verificar existencia de usuario {username}: {str(e)}")
        
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
            role = request.user.role_display()
            organization = request.user.get_organization_name()
            client_ip = self.get_client_ip(request)
            session_key = request.session.session_key
            
            logger.info(
                f"LOGOUT - Usuario: {email} (ID: {user_id}), Rol: {role}, "
                f"Org: {organization}, IP: {client_ip}"
            )
        
        # Limpiar flags de sesión específicos antes del logout
        session_keys_to_clear = [
            'admin_welcome_shown',
            # Limpiar flags de warnings de suscripción
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
            pass  # Esto consume/limpia los mensajes
        
        # Forzar guardar la sesión limpia antes del logout
        request.session.save()
        
        logout(request)
        logger.info(f"Logout completado exitosamente - IP: {client_ip}")
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
        
        logger.info(f"Solicitud de reset de contraseña - Email: {email}, IP: {client_ip}")
        
        # Verificar si ya hay una solicitud reciente
        if cache.get(cache_key):
            logger.warning(f"Reset de contraseña duplicado bloqueado - Email: {email}, IP: {client_ip}")
            messages.info(self.request, "Ya enviamos instrucciones. Revisa tu correo o espera 15 minutos para solicitar otro.", extra_tags='password_reset')
            return self.form_invalid(form)
        
        # Verificar si el usuario existe
        try:
            user_exists = User.objects.filter(email=email, is_active=True).exists()
            if user_exists:
                logger.info(f"Reset de contraseña procesado para usuario existente: {email}")
            else:
                logger.warning(f"Reset de contraseña solicitado para email no registrado: {email} (IP: {client_ip})")
        except Exception as e:
            logger.error(f"Error al verificar usuario para reset: {email} - {str(e)}")
        
        # Guardar en cache por 15 minutos
        cache.set(cache_key, True, timeout=900)
        
        # Usar el método estándar de Django
        return super().form_valid(form)
    
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
            logger.warning(f"User {request.user.email} accessed force-password-change without requirement")
            return redirect('/')
        
        form = ForcePasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        client_ip = self.get_client_ip()
        
        # Si el usuario no necesita cambiar contraseña, redirigir al dashboard
        if not getattr(request.user, 'password_change_required', False):
            logger.warning(f"Usuario {request.user.email} intentó cambio de contraseña sin requerimiento (IP: {client_ip})")
            return redirect('/')
        
        form = ForcePasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                # Cambiar la contraseña
                user = request.user
                user.set_password(form.cleaned_data['new_password1'])
                user.password_change_required = False  # Ya no necesita cambiar contraseña
                user.save()
                
                # Mantener la sesión activa después del cambio de contraseña
                update_session_auth_hash(request, user)
                
                logger.info(f"Cambio forzado de contraseña exitoso - Usuario: {user.email}, IP: {client_ip}")
                messages.success(request, '¡Contraseña cambiada exitosamente! Ahora puedes acceder a todas las funciones del sistema.')
                
                # Redirigir al dashboard principal
                return redirect('/')
            except Exception as e:
                logger.error(f"Error en cambio forzado de contraseña para {request.user.email}: {str(e)}")
                messages.error(request, 'Ocurrió un error al cambiar la contraseña. Por favor inténtalo de nuevo.')
        else:
            logger.warning(f"Formulario inválido en cambio forzado de contraseña - Usuario: {request.user.email}, Errores: {form.errors.as_text()}")
        
        return render(request, self.template_name, {'form': form})
    
    def get_client_ip(self):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip