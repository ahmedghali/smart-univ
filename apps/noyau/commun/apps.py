from django.apps import AppConfig


class CommunConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.noyau.commun"

    def ready(self):
        from .tri import installer

        installer()
