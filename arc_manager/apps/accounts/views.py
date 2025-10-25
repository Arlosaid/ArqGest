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
            
            # Log de seguridad CRÍTICO para superusuarios (nivel WARNING para alertas)
            logger.warning(
                f"SUPERUSER LOGIN | Email: {user.email} | IP: {client_ip} | "
                f"Sesión: {session_duration}"
            )
            
            return redirect('/admin/')
        
        # Verificar si necesita cambio de contraseña
        if getattr(user, 'password_change_required', False):
            login(self.request, user)
            logger.info(
                f"PASSWORD CHANGE REQUIRED | Email: {user.email} | IP: {client_ip}"
            )
            return redirect('/accounts/force-password-change/')
        
        user_info = {
            'email': user.email,
            'id': user.pk,
            'role': user.role_display(),
            'organization': user.get_organization_name()
        }
        
        # Proceder con el login normal
        response = super().form_valid(form)
        
        # Guardar timestamp de login en la sesión para calcular duración
        self.request.session['_auth_user_login_time'] = timezone.now().isoformat()
        
        # Log consolidado de login exitoso (UN SOLO LOG)
        logger.info(
            f"LOGIN EXITOSO | Email: {user_info['email']} | ID: {user_info['id']} | "
            f"Rol: {user_info['role']} | Org: {user_info['organization']} | "
            f"IP: {client_ip} | Sesión: {session_duration}"
        )
        
        # Log adicional SOLO para org_admin (seguridad)
        if user.is_org_admin and not user.is_superuser:
            logger.warning(
                f"ORG_ADMIN LOGIN | Email: {user.email} | "
                f"Org: {user_info['organization']} | IP: {client_ip}"
            )
        
        return response
    
    def form_invalid(self, form):
        """Manejar login fallido con mensaje ESPECÍFICO sobre qué está mal"""
        username = form.cleaned_data.get('username', 'N/A')
        client_ip = self.get_client_ip()
        
        # Determinar el motivo EXACTO del error (UN SOLO LOG)
        error_detail = "desconocido"
        try:
            if not username or username == 'N/A':
                error_detail = "Email vacío"
            else:
                user_exists = User.objects.filter(email=username).exists()
                
                if not user_exists:
                    error_detail = "Email NO existe"
                else:
                    user = User.objects.get(email=username)
                    if not user.is_active:
                        error_detail = "Cuenta INACTIVA"
                    else:
                        error_detail = "Contraseña INCORRECTA"
            
            # UN SOLO LOG WARNING - Información crítica sin ruido
            logger.warning(
                f"LOGIN FALLIDO | Motivo: {error_detail} | "
                f"Email: {username} | IP: {client_ip}"
            )
            
        except Exception as e:
            logger.error(f"ERROR verificando login | Email: {username} | Error: {str(e)}")
        
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
            
            # UN SOLO LOG - Sin calcular duración de sesión (overhead innecesario)
            logger.info(
                f"LOGOUT | Email: {email} | ID: {user_id} | IP: {client_ip}"
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
            user_exists = User.objects.filter(email=email, is_active=True).exists()
            if user_exists:
                logger.info(f"PASSWORD RESET | Email: {email} | IP: {client_ip}")
            else:
                logger.warning(
                    f"PASSWORD RESET | Email NO registrado: {email} | IP: {client_ip}"
                )
        except Exception as e:
            logger.error(f"ERROR en password reset | Email: {email} | Error: {str(e)}")
        
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
                user.save()
                
                update_session_auth_hash(request, user)
                
                logger.info(
                    f"PASSWORD CHANGE EXITOSO | Email: {user.email} | IP: {client_ip}"
                )
                messages.success(request, '¡Contraseña cambiada exitosamente! Ahora puedes acceder a todas las funciones del sistema.')
                
                return redirect('/')
            except Exception as e:
                logger.error(
                    f"ERROR PASSWORD CHANGE | Email: {request.user.email} | Error: {str(e)}"
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