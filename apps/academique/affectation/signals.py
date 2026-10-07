from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.academique.affectation.models import Classe
from apps.academique.affectation.services import recalculer_statistiques_ens_dep


@receiver(post_save, sender=Classe)
def on_classe_save(sender, instance, **kwargs):
    """Recalcule les compteurs Ens_Dep après création ou modification d'une classe (A09)."""
    if instance.enseignant_id:
        try:
            recalculer_statistiques_ens_dep(instance.enseignant)
        except Exception:
            pass


@receiver(post_delete, sender=Classe)
def on_classe_delete(sender, instance, **kwargs):
    """Recalcule les compteurs Ens_Dep après suppression d'une classe (A09)."""
    if instance.enseignant_id:
        try:
            recalculer_statistiques_ens_dep(instance.enseignant)
        except Exception:
            pass
