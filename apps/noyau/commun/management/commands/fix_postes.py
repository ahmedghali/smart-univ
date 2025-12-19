# apps/noyau/commun/management/commands/fix_postes.py

from django.core.management.base import BaseCommand
from apps.noyau.commun.models import Poste
from apps.noyau.authentification.models import CustomUser


class Command(BaseCommand):
    help = 'Corrige les postes ENS et ETU en les remplacant par enseignant et etudiant'

    def handle(self, *args, **kwargs):
        self.stdout.write("=" * 50)
        self.stdout.write("  Correction des postes")
        self.stdout.write("=" * 50 + "\n")

        # Recuperer les postes corrects
        try:
            poste_enseignant = Poste.objects.get(code='enseignant')
            self.stdout.write(self.style.SUCCESS("[OK] Poste 'enseignant' trouve"))
        except Poste.DoesNotExist:
            self.stdout.write(self.style.ERROR("[ERREUR] Poste 'enseignant' introuvable!"))
            return

        try:
            poste_etudiant = Poste.objects.get(code='etudiant')
            self.stdout.write(self.style.SUCCESS("[OK] Poste 'etudiant' trouve"))
        except Poste.DoesNotExist:
            self.stdout.write(self.style.ERROR("[ERREUR] Poste 'etudiant' introuvable!"))
            return

        self.stdout.write("")

        # Traiter les postes 'ENS'
        try:
            poste_ens = Poste.objects.get(code='ENS')
            self.stdout.write("-> Poste 'ENS' trouve")

            # Reaffecter tous les utilisateurs avec poste_principal='ENS' vers 'enseignant'
            users_principal = CustomUser.objects.filter(poste_principal=poste_ens)
            count_principal = users_principal.count()
            users_principal.update(poste_principal=poste_enseignant)
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count_principal} utilisateurs reaffectes (poste principal)"))

            # Reaffecter tous les utilisateurs avec 'ENS' dans postes_secondaires vers 'enseignant'
            users_secondaires = CustomUser.objects.filter(postes_secondaires=poste_ens)
            count_secondaires = users_secondaires.count()
            for user in users_secondaires:
                user.postes_secondaires.remove(poste_ens)
                user.postes_secondaires.add(poste_enseignant)
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count_secondaires} utilisateurs reaffectes (postes secondaires)"))

            # Supprimer le poste 'ENS'
            poste_ens.delete()
            self.stdout.write(self.style.SUCCESS("  [OK] Poste 'ENS' supprime"))

        except Poste.DoesNotExist:
            self.stdout.write(self.style.WARNING("  [INFO] Poste 'ENS' introuvable (deja supprime?)"))

        self.stdout.write("")

        # Traiter les postes 'ETU'
        try:
            poste_etu = Poste.objects.get(code='ETU')
            self.stdout.write("-> Poste 'ETU' trouve")

            # Reaffecter tous les utilisateurs avec poste_principal='ETU' vers 'etudiant'
            users_principal = CustomUser.objects.filter(poste_principal=poste_etu)
            count_principal = users_principal.count()
            users_principal.update(poste_principal=poste_etudiant)
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count_principal} utilisateurs reaffectes (poste principal)"))

            # Reaffecter tous les utilisateurs avec 'ETU' dans postes_secondaires vers 'etudiant'
            users_secondaires = CustomUser.objects.filter(postes_secondaires=poste_etu)
            count_secondaires = users_secondaires.count()
            for user in users_secondaires:
                user.postes_secondaires.remove(poste_etu)
                user.postes_secondaires.add(poste_etudiant)
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count_secondaires} utilisateurs reaffectes (postes secondaires)"))

            # Supprimer le poste 'ETU'
            poste_etu.delete()
            self.stdout.write(self.style.SUCCESS("  [OK] Poste 'ETU' supprime"))

        except Poste.DoesNotExist:
            self.stdout.write(self.style.WARNING("  [INFO] Poste 'ETU' introuvable (deja supprime?)"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("  Termine!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
