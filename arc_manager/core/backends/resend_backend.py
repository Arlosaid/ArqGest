"""
Backend de email personalizado para Django que usa Resend API
Compatible con el sistema de emails de Django (send_mail, etc.)
"""
import logging
import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendBackend(BaseEmailBackend):
    """
    Backend de email que usa la API de Resend.
    Compatible con todas las funciones de Django: send_mail(), EmailMessage, etc.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', None)
        
        if not self.api_key:
            logger.error("RESEND_API_KEY no esta configurado")
            raise ValueError("RESEND_API_KEY no esta configurado")
        
        # Configurar Resend con el API key
        resend.api_key = self.api_key
    
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
        Envia un mensaje individual usando Resend API
        
        Args:
            message: Objeto EmailMessage de Django
            
        Returns:
            bool: True si se envio exitosamente
        """
        try:
            # Preparar datos del email para Resend
            email_data = {
                "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
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
            
            # Enviar usando Resend
            response = resend.Emails.send(email_data)
            
            # Verificar respuesta
            if response and isinstance(response, dict) and 'id' in response:
                logger.info(f"Email enviado exitosamente via Resend. ID: {response['id']}")
                return True
            else:
                logger.warning(f"Respuesta inesperada de Resend: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error enviando email via Resend: {e}")
            if not self.fail_silently:
                raise
            return False

