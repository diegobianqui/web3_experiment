from django.apps import AppConfig

class Authweb3Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authweb3'

    def ready(self):
        import authweb3.signals  # noqa
