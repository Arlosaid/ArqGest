from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.http import JsonResponse
from apps.plans.views import SubscriptionInfoAPIView
from apps.main.admin import financial_dashboard_view
from .test_views import test_resend_api

def root_redirect(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    return redirect('main:dashboard')

def health_check(request):
    """Endpoint optimizado para health check (Railway, monitoring services, etc.)"""
    try:
        # Verificar conexión a la base de datos
        from django.db import connection
        connection.ensure_connection()
        
        # Verificar que Django está funcionando
        from django.conf import settings
        
        return JsonResponse({
            'status': 'healthy',
            'service': 'arc-manager',
            'database': 'connected',
            'django': 'ready',
            'version': '1.0.0'
        })
    except Exception as e:
        # Si hay error, devolver 503 (Service Unavailable)
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'arc-manager',
            'error': str(e)[:100]
        }, status=503)

urlpatterns = [
    path('admin/financial-dashboard/', financial_dashboard_view, name='admin_financial_dashboard'),
    path('admin/test-resend/', test_resend_api, name='test_resend_api'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('main/', include('apps.main.urls')),
    path('organizations/', include('apps.orgs.urls')),
    path('users/', include('apps.users.urls')),
    path('plans/', include('apps.plans.urls')),
    path('projects/', include('apps.projects.urls')),
    path('', include('apps.files.urls')),
    path('api/subscription-info/', SubscriptionInfoAPIView.as_view(), name='subscription_info_api'),
    path('health/', health_check, name='health_check'),
    path('', root_redirect),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
    ] + urlpatterns
    
    # Rutas de test para errores (solo en desarrollo)
    from .test_views import test_400, test_403, test_404, test_500
    urlpatterns += [
        path('test-400/', test_400, name='test_400'),
        path('test-403/', test_403, name='test_403'),
        path('test-404/', test_404, name='test_404'),
        path('test-500/', test_500, name='test_500'),
    ]

# Custom error handlers for production
# Estos handlers aseguran que se muestren nuestras páginas de error personalizadas
handler400 = 'core.error_handlers.custom_400_view'
handler403 = 'core.error_handlers.custom_403_view'
handler404 = 'core.error_handlers.custom_404_view'
handler500 = 'core.error_handlers.custom_500_view'
