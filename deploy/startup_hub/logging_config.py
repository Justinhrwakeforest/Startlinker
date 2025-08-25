# Advanced logging configuration for production

import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

def setup_logging():
    """Configure logging for production environment"""
    
    # Create log directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Configure specific loggers
    configure_django_logging(log_dir)
    configure_celery_logging(log_dir)
    configure_security_logging(log_dir)
    
    return logging.getLogger(__name__)

def configure_django_logging(log_dir):
    """Configure Django-specific logging"""
    django_logger = logging.getLogger('django')
    
    # Handler for Django requests
    request_handler = RotatingFileHandler(
        os.path.join(log_dir, 'django_requests.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    request_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    django_logger.addHandler(request_handler)

def configure_celery_logging(log_dir):
    """Configure Celery-specific logging"""
    celery_logger = logging.getLogger('celery')
    
    # Handler for Celery tasks
    celery_handler = RotatingFileHandler(
        os.path.join(log_dir, 'celery.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    celery_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    celery_logger.addHandler(celery_handler)

def configure_security_logging(log_dir):
    """Configure security-specific logging"""
    security_logger = logging.getLogger('security')
    
    # Handler for security events
    security_handler = RotatingFileHandler(
        os.path.join(log_dir, 'security.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    security_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    security_logger.addHandler(security_handler)

def configure_email_logging():
    """Configure email notifications for critical errors"""
    if os.environ.get('EMAIL_HOST') and os.environ.get('ADMIN_EMAIL'):
        mail_handler = SMTPHandler(
            mailhost=(os.environ.get('EMAIL_HOST'), int(os.environ.get('EMAIL_PORT', 587))),
            fromaddr=os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@startuphub.com'),
            toaddrs=[os.environ.get('ADMIN_EMAIL')],
            subject='StartupHub Critical Error',
            credentials=(os.environ.get('EMAIL_USER'), os.environ.get('EMAIL_PASSWORD')),
            secure=()
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Add to root logger
        logging.getLogger().addHandler(mail_handler)