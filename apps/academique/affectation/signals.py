import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.academique.affectation.models import Classe, Seance
from apps.academique.affectation.services import (
    recalculer_avancement_classe,
    recalculer_effectifs_niveau,
    recalculer_statistiques_ens_dep,
    recalculer_statistiques_nivspedep,
)
from apps.academique.departement.models import Matiere, NivSpeDep_SG
from apps.academique.etudiant.models import Etudiant

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Classe)
def on_classe_save(sender, instance, **kwargs):
    """Recalcule les compteurs Ens_Dep après création ou modification d'une classe (A09, R6)."""
    if instance.enseignant_id:
        try:
            recalculer_statistiques_ens_dep(instance.enseignant)
        except Exception:
            logger.exception("Erreur lors du recalcul des compteurs Ens_Dep: %s", instance.enseignant_id)


@receiver(post_delete, sender=Classe)
def on_classe_delete(sender, instance, **kwargs):
    """Recalcule les compteurs Ens_Dep après suppression d'une classe (A09, R6)."""
    if instance.enseignant_id:
        try:
            recalculer_statistiques_ens_dep(instance.enseignant)
        except Exception:
            logger.exception(
                "Erreur lors du recalcul des compteurs Ens_Dep après suppression: %s", instance.enseignant_id
            )


# ══════════════════════════════════════════════════════════════
# SÉANCES (R3) -> Classe.taux_avancement
# ══════════════════════════════════════════════════════════════


@receiver(post_save, sender=Seance)
def on_seance_save(sender, instance, **kwargs):
    """Recalcule le taux d'avancement de la classe après enregistrement d'une séance (R3)."""
    if instance.classe_id:
        try:
            recalculer_avancement_classe(instance.classe)
        except Exception:
            logger.exception("Erreur lors du recalcul de l'avancement de la classe: %s", instance.classe_id)


@receiver(post_delete, sender=Seance)
def on_seance_delete(sender, instance, **kwargs):
    """Recalcule le taux d'avancement de la classe après suppression d'une séance (R3)."""
    if instance.classe_id:
        try:
            recalculer_avancement_classe(instance.classe)
        except Exception:
            logger.exception(
                "Erreur lors du recalcul de l'avancement de la classe après suppression: %s", instance.classe_id
            )


# ══════════════════════════════════════════════════════════════
# MATIÈRES (R3) -> NivSpeDep.nbr_matieres_s1 / s2
# ══════════════════════════════════════════════════════════════


@receiver(post_save, sender=Matiere)
def on_matiere_save(sender, instance, **kwargs):
    """Recalcule les nombres de matières S1 et S2 du NivSpeDep (R3)."""
    if instance.niv_spe_dep_id:
        try:
            recalculer_statistiques_nivspedep(instance.niv_spe_dep)
        except Exception:
            logger.exception("Erreur lors du recalcul des matières NivSpeDep: %s", instance.niv_spe_dep_id)


@receiver(post_delete, sender=Matiere)
def on_matiere_delete(sender, instance, **kwargs):
    """Recalcule les nombres de matières S1 et S2 du NivSpeDep après suppression (R3)."""
    if instance.niv_spe_dep_id:
        try:
            recalculer_statistiques_nivspedep(instance.niv_spe_dep)
        except Exception:
            logger.exception(
                "Erreur lors du recalcul des matières NivSpeDep après suppression: %s", instance.niv_spe_dep_id
            )


# ══════════════════════════════════════════════════════════════
# ÉTUDIANTS (R3) -> NivSpeDep.nbr_etudiants & NivSpeDep_SG.nbr_etudiants_SG
# ══════════════════════════════════════════════════════════════


@receiver(pre_save, sender=Etudiant)
def on_etudiant_pre_save(sender, instance, **kwargs):
    """Mémorise l'ancien groupe en cas de réaffectation (R3)."""
    if instance.pk:
        try:
            old = Etudiant.objects.filter(pk=instance.pk).values("niv_spe_dep_sg_id").first()
            if old and old["niv_spe_dep_sg_id"] != instance.niv_spe_dep_sg_id:
                instance._old_niv_spe_dep_sg_id = old["niv_spe_dep_sg_id"]
        except Exception:
            pass


@receiver(post_save, sender=Etudiant)
def on_etudiant_save(sender, instance, **kwargs):
    """Recalcule les effectifs NivSpeDep et NivSpeDep_SG après enregistrement d'un étudiant (R3)."""
    old_sg_id = getattr(instance, "_old_niv_spe_dep_sg_id", None)
    if old_sg_id:
        try:
            old_sg = NivSpeDep_SG.objects.get(pk=old_sg_id)
            recalculer_effectifs_niveau(old_sg.niv_spe_dep)
        except Exception:
            logger.exception("Erreur lors du recalcul de l'ancien groupe étudiant: %s", old_sg_id)

    if instance.niv_spe_dep_sg_id:
        try:
            recalculer_effectifs_niveau(instance.niv_spe_dep_sg.niv_spe_dep)
        except Exception:
            logger.exception("Erreur lors du recalcul des effectifs étudiant: %s", instance.niv_spe_dep_sg_id)


@receiver(post_delete, sender=Etudiant)
def on_etudiant_delete(sender, instance, **kwargs):
    """Recalcule les effectifs NivSpeDep et NivSpeDep_SG après suppression d'un étudiant (R3)."""
    if instance.niv_spe_dep_sg_id:
        try:
            recalculer_effectifs_niveau(instance.niv_spe_dep_sg.niv_spe_dep)
        except Exception:
            logger.exception(
                "Erreur lors du recalcul des effectifs étudiant après suppression: %s", instance.niv_spe_dep_sg_id
            )
