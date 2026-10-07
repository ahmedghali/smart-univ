from django.apps import AppConfig


class AffectationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.academique.affectation"

    def ready(self):
        import apps.academique.affectation.signals  # noqa
