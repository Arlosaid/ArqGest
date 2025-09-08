"""
Vistas de test para administradores
"""
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
import resend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@staff_member_required
@require_http_methods(["GET"])
def test_resend_api(request):
    """
    Vista para probar Resend API desde el admin
    Acceso: /admin/test-resend/
    """
    try:
        # Obtener API key
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'RESEND_API_KEY no configurado',
                'details': 'Configura RESEND_API_KEY en Railway'
            })
        
        # Configurar Resend
        resend.api_key = api_key
        
        # Datos del test
        email_data = {
            "from": getattr(settings, 'DEFAULT_FROM_EMAIL', 'onboarding@resend.dev'),
            "to": ["adroal08@gmail.com"],
            "subject": "Test Admin - ARC Manager",
            "html": "<p>✅ <strong>Test desde admin exitoso</strong>!</p><p>Resend API funciona correctamente.</p>"
        }
        
        # Enviar email
        response = resend.Emails.send(email_data)
        
        if response:
            return JsonResponse({
                'success': True,
                'message': 'Email enviado exitosamente',
                'response': str(response),
                'email_data': email_data
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Resend retornó None',
                'details': 'Posible problema con API key o límites',
                'email_data': email_data
            })
            
    except Exception as e:
        logger.error(f"Error en test de Resend: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'type': str(type(e)),
            'details': 'Ver logs para más información'
        })