"""
Backend de email personalizado para Django que usa Resend API
Compatible con el sistema de emails de Django (send_mail, etc.)
Implementa logging estructurado con trazabilidad completa
"""
import logging
import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from core.error_codes import EmailErrorCodes
from core.structured_logging import log_error, log_info

logger = logging.getLogger('core.email')


class ResendBackend(BaseEmailBackend):
    """
    Backend de email que usa la API de Resend.
    Compatible con todas las funciones de Django: send_mail(), EmailMessage, etc.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', None)
        
        if not self.api_key:
            log_error(
                event='email_backend_init',
                error_code=EmailErrorCodes.EMAIL_CONFIG_API_KEY_MISSING,
                reason='RESEND_API_KEY no configurado en variables de entorno',
                logger_name='core.email'
            )
            raise ValueError("RESEND_API_KEY no esta configurado")
        
        # Configurar Resend con el API key
        resend.api_key = self.api_key
        
        log_info(
            event='email_backend_init',
            backend='ResendBackend',
            api_key_prefix=self.api_key[:10] if self.api_key else 'None',
            logger_name='core.email'
        )
    
    def send_messages(self, email_messages):
        """
        Envia una lista de mensajes de email.
        Este metodo es llamado por Django.
        
        Args:
            email_messages: Lista de objetos EmailMessage de Django
            
        Returns:
            int: Numero de mensajes enviados exitosamente
        """
        if not email_messages:
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            try:
                sent = self._send_message(message)
                if sent:
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error enviando email: {e}")
                if not self.fail_silently:
                    raise
        
        return sent_count
    
    def _send_message(self, message):
        """
        Envia un mensaje individual usando Resend API con logging estructurado completo
        
        Args:
            message: Objeto EmailMessage de Django
            
        Returns:
            bool: True si se envio exitosamente
        """
        # Extraer destinatarios para logging
        recipients = message.to[0] if message.to else 'unknown'
        sender = message.from_email or settings.DEFAULT_FROM_EMAIL
        
        try:
            # Preparar datos del email para Resend
            email_data = {
                "from": sender,
                "to": message.to,
                "subject": message.subject,
            }
            
            # Agregar contenido HTML si existe
            if message.content_subtype == 'html':
                email_data["html"] = message.body
            else:
                # Si es texto plano
                email_data["text"] = message.body
            
            # Si hay alternativas (texto plano + HTML)
            if hasattr(message, 'alternatives') and message.alternatives:
                for content, mimetype in message.alternatives:
                    if mimetype == 'text/html':
                        email_data["html"] = content
            
            # Agregar CC si existe
            if message.cc:
                email_data["cc"] = message.cc
            
            # Agregar BCC si existe
            if message.bcc:
                email_data["bcc"] = message.bcc
            
            # Agregar Reply-To si existe
            if message.reply_to:
                email_data["reply_to"] = message.reply_to
            
            # Log inicio de envío
            log_info(
                event='email_send_start',
                recipients=recipients,
                sender=sender,
                subject=message.subject[:50],
                recipients_count=len(message.to),
                has_html='html' in email_data,
                has_attachments=len(message.attachments) if hasattr(message, 'attachments') else 0,
                logger_name='core.email'
            )
            
            # Enviar usando Resend
            response = resend.Emails.send(email_data)
            
            # Verificar respuesta
            if response and isinstance(response, dict) and 'id' in response:
                # Log exitoso con trazabilidad completa
                log_info(
                    event='email_send_success',
                    error_code=EmailErrorCodes.EMAIL_SEND_SUCCESS,
                    email_id=response['id'],
                    recipients=recipients,
                    sender=sender,
                    subject=message.subject[:50],
                    provider='Resend',
                    recipients_count=len(message.to),
                    logger_name='core.email'
                )
                return True
            else:
                # Respuesta inesperada
                log_error(
                    event='email_send_warning',
                    error_code=EmailErrorCodes.EMAIL_SEND_API_ERROR,
                    recipients=recipients,
                    sender=sender,
                    subject=message.subject[:50],
                    response=str(response)[:100],
                    reason='Respuesta inesperada de Resend API',
                    logger_name='core.email'
                )
                return False
                
        except Exception as e:
            # Log de error con contexto completo
            error_type = type(e).__name__
            error_message = str(e)
            
            # Determinar código de error específico
            if 'rate' in error_message.lower() or 'limit' in error_message.lower():
                error_code = EmailErrorCodes.EMAIL_SEND_RATE_LIMIT
            elif 'quota' in error_message.lower():
                error_code = EmailErrorCodes.EMAIL_SEND_QUOTA_EXCEEDED
            elif 'invalid' in error_message.lower() and 'key' in error_message.lower():
                error_code = EmailErrorCodes.EMAIL_CONFIG_API_KEY_INVALID
            else:
                error_code = EmailErrorCodes.EMAIL_SEND_FAILED
            
            log_error(
                event='email_send_error',
                error_code=error_code,
                recipients=recipients,
                sender=sender,
                subject=message.subject[:50],
                error_type=error_type,
                error_message=error_message[:200],
                provider='Resend',
                fail_silently=self.fail_silently,
                logger_name='core.email'
            )
            
            if not self.fail_silently:
                raise
            return False

