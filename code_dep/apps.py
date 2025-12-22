from django.apps import AppConfig


class DepartementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.academique.departement'  # ← CHEMIN COMPLET
    verbose_name = 'Departement'
