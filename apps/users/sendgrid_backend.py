"""
Custom SendGrid email backend for Django
Compatible with Python 3.11+ and modern Django versions
"""

import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from django.conf import settings
import sendgrid
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from python_http_client import exceptions

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """
    SendGrid email backend for Django
    """
    
    def __init__(self, api_key=None, sandbox_mode=None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or getattr(settings, 'SENDGRID_API_KEY', None)
        self.sandbox_mode = sandbox_mode or getattr(settings, 'SENDGRID_SANDBOX_MODE_IN_DEBUG', False)
        
        if not self.api_key:
            logger.error("SendGrid API key is not configured")
            
        self.client = sendgrid.SendGridAPIClient(api_key=self.api_key) if self.api_key else None
    
    def send_messages(self, email_messages):
        """
        Send multiple email messages
        """
        if not self.client:
            logger.error("SendGrid client not initialized - missing API key")
            return 0
            
        sent_count = 0
        for message in email_messages:
            if self._send_message(message):
                sent_count += 1
        
        return sent_count
    
    def _send_message(self, message):
        """
        Send a single email message
        """
        try:
            # Create SendGrid mail object
            mail = Mail()
            
            # Set from email
            from_email = message.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            mail.from_email = From(from_email)
            
            # Set subject
            mail.subject = Subject(message.subject)
            
            # Add recipients
            to_list = []
            for recipient in message.recipients():
                to_list.append(To(recipient))
            mail.to = to_list
            
            # Set content
            if hasattr(message, 'body') and message.body:
                mail.plain_text_content = PlainTextContent(message.body)
            
            # Set HTML content if available
            html_content = None
            for content, mimetype in getattr(message, 'alternatives', []):
                if mimetype == 'text/html':
                    html_content = content
                    break
            
            if html_content:
                mail.html_content = HtmlContent(html_content)
            elif hasattr(message, 'body') and message.body:
                # If no HTML content but has body, use body as plain text
                mail.plain_text_content = PlainTextContent(message.body)
            
            # Enable sandbox mode if in debug
            if self.sandbox_mode and getattr(settings, 'DEBUG', False):
                mail.mail_settings = {
                    "sandbox_mode": {
                        "enable": True
                    }
                }
            
            # Send the email
            response = self.client.send(mail)
            
            # Check response
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {message.recipients()}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return False
                
        except exceptions.BadRequestsError as e:
            logger.error(f"SendGrid BadRequest error: {e}")
            return False
        except Exception as e:
            logger.error(f"SendGrid sending error: {e}")
            return False


# Alias for compatibility
SendgridBackend = SendGridBackend