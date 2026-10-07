from django.core.management.base import BaseCommand

from apps.academique.affectation.services import recalculer_tous_les_compteurs


class Command(BaseCommand):
    help = "Recalcule l'ensemble des compteurs et statistiques (Ens_Dep, Classe, NivSpeDep, NivSpeDep_SG) (A09, R3)."

    def handle(self, *args, **options):
        self.stdout.write("Recalcul de l'ensemble des compteurs en cours...")
        counts = recalculer_tous_les_compteurs()
        if isinstance(counts, dict):
            msg = (
                f"Recalcul terminé avec succès : "
                f"{counts.get('ens_dep', 0)} Ens_Dep, "
                f"{counts.get('classes', 0)} classes, "
                f"{counts.get('niv_spe_dep', 0)} NivSpeDep, "
                f"{counts.get('niv_spe_dep_sg', 0)} NivSpeDep_SG."
            )
        else:
            msg = f"Recalcul terminé avec succès pour {counts} enregistrement(s)."
        self.stdout.write(self.style.SUCCESS(msg))
