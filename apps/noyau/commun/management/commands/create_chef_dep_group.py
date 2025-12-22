# apps/noyau/commun/management/commands/create_chef_dep_group.py

"""
Commande de gestion pour créer le groupe "Chef de Département" avec les permissions appropriées.
Usage: python manage.py create_chef_dep_group
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Crée le groupe "Chef de Département" avec les permissions CRUD appropriées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Supprime le groupe existant avant de le recréer',
        )

    def handle(self, *args, **options):
        group_name = 'Chef de Département'

        # Supprimer le groupe existant si demandé
        if options['delete']:
            deleted, _ = Group.objects.filter(name=group_name).delete()
            if deleted:
                self.stdout.write(self.style.WARNING(f'Groupe "{group_name}" supprimé.'))

        # Créer ou récupérer le groupe
        group, created = Group.objects.get_or_create(name=group_name)

        if created:
            self.stdout.write(self.style.SUCCESS(f'Groupe "{group_name}" créé avec succès.'))
        else:
            self.stdout.write(self.style.WARNING(f'Groupe "{group_name}" existe déjà. Mise à jour des permissions...'))

        # Définir les permissions par modèle
        # Format: (app_label, model_name, [permissions])
        permissions_config = [
            # Enseignant - CRUD complet
            ('enseignant', 'enseignant', ['add', 'change', 'delete', 'view']),

            # Etudiant - CRUD complet
            ('etudiant', 'etudiant', ['add', 'change', 'delete', 'view']),

            # Affectation Ens_Dep - CRUD complet
            ('affectation', 'ens_dep', ['add', 'change', 'delete', 'view']),

            # Département - Lecture seule
            ('departement', 'departement', ['view']),

            # Spécialité - Lecture seule
            ('departement', 'specialite', ['view']),

            # NivSpeDep - Lecture seule
            ('departement', 'nivspedep', ['view']),

            # NivSpeDep_SG - Lecture seule
            ('departement', 'nivspedep_sg', ['view']),

            # Matière - Lecture seule
            ('departement', 'matiere', ['view']),

            # Niveau - Lecture seule
            ('commun', 'niveau', ['view']),

            # Grade - Lecture seule
            ('commun', 'grade', ['view']),

            # Année Universitaire - Lecture seule
            ('commun', 'anneeuniversitaire', ['view']),
        ]

        permissions_added = []
        permissions_not_found = []

        for app_label, model_name, perm_types in permissions_config:
            for perm_type in perm_types:
                codename = f'{perm_type}_{model_name}'
                try:
                    permission = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label
                    )
                    group.permissions.add(permission)
                    permissions_added.append(f'{app_label}.{codename}')
                except Permission.DoesNotExist:
                    permissions_not_found.append(f'{app_label}.{codename}')

        # Afficher le résumé
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'GROUPE: {group_name}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if permissions_added:
            self.stdout.write(self.style.SUCCESS(f'\n✓ {len(permissions_added)} permissions ajoutées:'))
            for perm in permissions_added:
                self.stdout.write(f'  - {perm}')

        if permissions_not_found:
            self.stdout.write(self.style.WARNING(f'\n⚠ {len(permissions_not_found)} permissions non trouvées:'))
            for perm in permissions_not_found:
                self.stdout.write(f'  - {perm}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('INSTRUCTIONS POUR LE SUPERADMIN:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('''
1. Accédez à l'admin Django: /admin/
2. Allez dans "Utilisateurs" > sélectionnez le chef de département
3. Dans la section "Permissions":
   - Cochez "Statut équipe" (is_staff = True)
   - Dans "Groupes", ajoutez "Chef de Département"
4. Sauvegardez

Le chef de département pourra maintenant accéder à /admin/ et gérer
les enseignants et étudiants de son département.
''')
