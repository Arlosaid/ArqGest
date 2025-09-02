from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.cache import cache
from .forms import CustomAuthenticationForm, ForcePasswordChangeForm
import logging

logger = logging.getLogger('app')

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    authentication_form = CustomAuthenticationForm
    
    def form_valid(self, form):
        user = form.get_user()
        
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
            
            # NO agregar mensaje aquí - se mostrará en el admin
            logger.info(f"Superuser {user.email} intentó acceder a la app - redirigido a admin")
            
            # Redirigir directamente al admin sin mensaje
            # El mensaje se mostrará en el admin mediante el middleware
            return redirect('/admin/')
        
        # Para usuarios normales y org_admin, verificar si necesita cambio de contraseña
        if getattr(user, 'password_change_required', False):
            # Hacer login primero
            login(self.request, user)
            # Redirigir al cambio forzado de contraseña
            return redirect('/accounts/force-password-change/')
        
        user_info = {
            'username': user.username or user.email,
            'role': user.role_display(),
            'organization': user.get_organization_name()
        }
        
        # Proceder con el login normal
        response = super().form_valid(form)
        
        # Registrar login exitoso
        logger.info(f"Login exitoso - Usuario: {user_info['username']}, Rol: {user_info['role']}, Organización: {user_info['organization']}")
        return response
    
    def form_invalid(self, form):
        # Registrar intento de login fallido
        username = form.cleaned_data.get('username', 'No especificado')
        logger.warning(f"Intento de login fallido para: {username}")
        return super().form_invalid(form)

class CustomLogoutView(View):
    """Vista personalizada para logout con logging"""
    
    def get(self, request, *args, **kwargs):
        return self.logout_user(request)
    
    def post(self, request, *args, **kwargs):
        return self.logout_user(request)
    
    def logout_user(self, request):
        # Capturar el nombre de usuario ANTES de hacer logout
        if request.user.is_authenticated:
            username = request.user.username or request.user.email
            role = request.user.role_display()
            organization = request.user.get_organization_name()
            
            logger.info(f"Logout - Usuario: {username}, Rol: {role}, Organización: {organization}")
        
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
        return redirect('accounts:login')

class SecurePasswordResetView(PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        cache_key = f"password_reset_{email}"
        
        # Verificar si ya hay una solicitud reciente
        if cache.get(cache_key):
            messages.info(self.request, "Ya enviamos instrucciones. Revisa tu correo o espera 15 minutos para solicitar otro.", extra_tags='password_reset')
            return self.form_invalid(form)
        
        # Guardar en cache por 15 minutos
        cache.set(cache_key, True, timeout=900)
        
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ForcePasswordChangeView(View):
    """Vista para forzar cambio de contraseña en el primer login"""
    template_name = 'auth/force_password_change.html'
    
    def get(self, request):
        # Si el usuario no necesita cambiar contraseña, redirigir al dashboard
        if not getattr(request.user, 'password_change_required', False):
            return redirect('/')
        
        form = ForcePasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        # Si el usuario no necesita cambiar contraseña, redirigir al dashboard
        if not getattr(request.user, 'password_change_required', False):
            return redirect('/')
        
        form = ForcePasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            # Cambiar la contraseña
            user = request.user
            user.set_password(form.cleaned_data['new_password1'])
            user.password_change_required = False  # Ya no necesita cambiar contraseña
            user.save()
            
            # Mantener la sesión activa después del cambio de contraseña
            update_session_auth_hash(request, user)
            
            messages.success(request, '¡Contraseña cambiada exitosamente! Ahora puedes acceder a todas las funciones del sistema.')
            
            # Redirigir al dashboard principal
            return redirect('/')
        
        return render(request, self.template_name, {'form': form})