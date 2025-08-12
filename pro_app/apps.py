from django.apps import AppConfig

class ProAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pro_app'
    def ready(self):
        import pro_app.signals  # Import the signals to connect them