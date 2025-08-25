from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.subscriptions'
    verbose_name = 'Subscriptions'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import apps.subscriptions.signals
        except ImportError:
            pass
