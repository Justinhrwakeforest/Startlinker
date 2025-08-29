"""
Working SendGrid backend based on our successful direct test
"""

import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import sendgrid
from sendgrid.helpers.mail import Mail
from python_http_client import exceptions

logger = logging.getLogger(__name__)


class WorkingSendGridBackend(BaseEmailBackend):
    """
    SendGrid backend that works exactly like our successful direct test
    """
    
    def __init__(self, api_key=None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or getattr(settings, 'SENDGRID_API_KEY', None)
        
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
        Send a single email message using the exact approach that worked in our direct test
        """
        try:
            # Get the message content
            plain_content = ""
            html_content = ""
            
            # Get plain text content
            if hasattr(message, 'body') and message.body:
                plain_content = message.body
            
            # Get HTML content from alternatives
            for content, mimetype in getattr(message, 'alternatives', []):
                if mimetype == 'text/html':
                    html_content = content
                    break
            
            # Prepare from email
            from_email_addr = message.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@startlinker.com')
            
            # Extract just the email address if it's in "Name <email@domain.com>" format
            if '<' in from_email_addr and '>' in from_email_addr:
                # Extract email from "Name <email@domain.com>" format
                start = from_email_addr.find('<') + 1
                end = from_email_addr.find('>')
                email_only = from_email_addr[start:end].strip()
                name_part = from_email_addr[:from_email_addr.find('<')].strip()
            else:
                email_only = from_email_addr
                name_part = "StartLinker"
            
            # Get recipient
            recipients = list(message.recipients())
            if not recipients:
                logger.error("No recipients found")
                return False
            
            # Create the Mail object using the same approach as our direct test
            mail = Mail(
                from_email=(email_only, name_part),
                to_emails=recipients[0],  # SendGrid Mail constructor expects single recipient
                subject=message.subject,
                plain_text_content=plain_content if plain_content else None,
                html_content=html_content if html_content else None
            )
            
            logger.info(f"Sending email via SendGrid:")
            logger.info(f"  From: {name_part} <{email_only}>")
            logger.info(f"  To: {recipients[0]}")
            logger.info(f"  Subject: {message.subject}")
            logger.info(f"  Has Plain: {'Yes' if plain_content else 'No'}")
            logger.info(f"  Has HTML: {'Yes' if html_content else 'No'}")
            
            # Send using the same method as our direct test
            response = self.client.send(mail)
            
            # Check response
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully - Status: {response.status_code}")
                if hasattr(response, 'headers') and response.headers:
                    message_id = response.headers.get('X-Message-Id')
                    if message_id:
                        logger.info(f"Message ID: {message_id}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code}")
                if hasattr(response, 'body') and response.body:
                    logger.error(f"Response body: {response.body}")
                return False
                
        except exceptions.BadRequestsError as e:
            logger.error(f"SendGrid BadRequest error: {e}")
            if hasattr(e, 'body'):
                logger.error(f"Error body: {e.body}")
            return False
        except Exception as e:
            logger.error(f"SendGrid error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


# Alias for compatibility
WorkingSendgridBackend = WorkingSendGridBackend