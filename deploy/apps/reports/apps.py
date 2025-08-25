from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'
    verbose_name = 'User Reports'
    
    def ready(self):
        # Import signals when the app is ready
        try:
            import apps.reports.signals
        except ImportError:
            pass