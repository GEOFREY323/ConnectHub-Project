from django.apps import AppConfig


class SocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social'
    
    def ready(self):
        # Import signal handlers to ensure they are registered
        import social.signals
