import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.academique.enseignant.utils import create_user_for_enseignant
from apps.academique.enseignant.utils import generate_password as generate_password_ens
from apps.academique.etudiant.utils import create_user_for_etudiant
from apps.academique.etudiant.utils import generate_password as generate_password_etu
from tests.factories import EnseignantFactory, EtudiantFactory

User = get_user_model()


@pytest.mark.django_db
class TestLot2MotsDePasse:
    """Tests pour le Lot 2 (A01, A31)."""

    def test_a31_get_profile_method_removed(self):
        """A31: La méthode get_profile() erronée et inutilisée a été supprimée de CustomUser."""
        assert not hasattr(User, "get_profile"), "CustomUser.get_profile ne doit plus exister !"

    def test_a01_password_is_random_and_secure(self):
        """A01: Les mots de passe générés sont aléatoires, sécurisés (min 12 caractères) et non prédictibles."""
        pass_etu = generate_password_etu("Benali", "بن علي", "Mohamed", "محمد")
        pass_ens = generate_password_ens("Khelifi", "خليفي", "Ahmed", "أحمد")

        assert len(pass_etu) >= 12, "Le mot de passe étudiant doit faire au moins 12 caractères"
        assert len(pass_ens) >= 12, "Le mot de passe enseignant doit faire au moins 12 caractères"

        # Vérifier qu'on n'a plus l'ancien format prévisible ...nomprenom123
        assert not pass_etu.startswith("..."), "Le mot de passe étudiant ne doit plus suivre l'ancien format prévisible"
        assert not pass_ens.startswith("..."), "Le mot de passe enseignant ne doit plus suivre l'ancien format prévisible"

        # Vérifier le caractère aléatoire
        pass_etu2 = generate_password_etu("Benali", "بن علي", "Mohamed", "محمد")
        assert pass_etu != pass_etu2, "Deux générations successives pour les mêmes noms doivent produire des mots de passe différents"

    def test_a01_created_user_has_flag_doit_changer_mot_de_passe(self):
        """A01: Les nouveaux comptes créés ont doit_changer_mot_de_passe = True."""
        etudiant = EtudiantFactory(user=None)
        user_etu = create_user_for_etudiant(etudiant)
        assert user_etu is not None
        assert getattr(user_etu, "doit_changer_mot_de_passe", None) is True

        enseignant = EnseignantFactory(user=None)
        user_ens, _ = create_user_for_enseignant(enseignant)
        assert user_ens is not None
        assert getattr(user_ens, "doit_changer_mot_de_passe", None) is True

    def test_a01_user_redirected_to_change_password_when_flag_true(self, client):
        """A01: Un utilisateur avec doit_changer_mot_de_passe=True est redirigé vers le changement de mot de passe."""
        etudiant = EtudiantFactory()
        user = etudiant.user
        user.doit_changer_mot_de_passe = True
        user.save()

        client.force_login(user)
        # Tentative d'accéder au dashboard
        resp = client.get(reverse("etudiant:dashboard_Etud"))
        assert resp.status_code == 302
        assert reverse("etudiant:changePassword_Etud") in resp.url

    def test_a01_flag_cleared_after_password_change(self, client):
        """A01: Après changement de mot de passe, doit_changer_mot_de_passe repasse à False."""
        etudiant = EtudiantFactory()
        user = etudiant.user
        user.set_password("OldTemporaryPass123!")
        user.doit_changer_mot_de_passe = True
        user.save()

        client.force_login(user)
        resp = client.post(
            reverse("etudiant:changePassword_Etud"),
            {
                "old_password": "OldTemporaryPass123!",
                "new_password": "NewStrongPassword456!",
                "confirm_password": "NewStrongPassword456!",
            },
            follow=True,
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert getattr(user, "doit_changer_mot_de_passe", None) is False
