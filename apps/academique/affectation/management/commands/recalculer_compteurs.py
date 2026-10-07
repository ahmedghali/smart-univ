from django.core.management.base import BaseCommand

from apps.academique.affectation.services import recalculer_tous_les_compteurs


class Command(BaseCommand):
    help = "Recalcule l'ensemble des compteurs de séances et de volumes horaires pour tous les Ens_Dep (A09)."

    def handle(self, *args, **options):
        self.stdout.write("Recalcul des compteurs Ens_Dep en cours...")
        total = recalculer_tous_les_compteurs()
        self.stdout.write(self.style.SUCCESS(f"Recalcul terminé avec succès pour {total} enregistrement(s) Ens_Dep."))
