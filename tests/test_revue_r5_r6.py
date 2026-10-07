"""Tests pour la Phase 2 bis - Groupe 4 : R5 et R6.

R5 : Sécurité réinitialisation de mot de passe par le chef de département :
- Exiger has_change_permission
- Refuser les cibles is_superuser, is_staff ou ayant une AffectationPoste active
- Activer doit_changer_mot_de_passe=True après réinitialisation

R6 : Log des exceptions dans les signaux A09.
"""

import logging
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from tests.factories import (
    AffectationPosteFactory,
    AnneeUniversitaireFactory,
    ClasseFactory,
    DepartementFactory,
    EnsDepFactory,
    EtudiantFactory,
    NivSpeDepSGFactory,
    PosteFactory,
    PostePermissionFactory,
    UserFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestR5ResetPasswordSecurity:
    """R5: Sécurisation de la réinitialisation de mot de passe dans le dep_admin."""

    def test_r5_user_without_change_permission_cannot_reset_password(self, client):
        """Un utilisateur qui a seulement le droit de voir (user_view=True, user_change=False)

        ne peut pas réinitialiser de mot de passe.
        """
        dep = DepartementFactory()
        annee = AnneeUniversitaireFactory(est_courante=True)

        user_viewer = UserFactory(username="viewer")
        poste = PosteFactory(code="observateur")
        AffectationPosteFactory(user=user_viewer, poste=poste, departement=dep, annee_univ=annee, est_actif=True)
        # Droits : voir uniquement, pas de modification
        PostePermissionFactory(poste=poste, user_view=True, user_change=False)

        # Cible étudiante normale du département
        target = UserFactory(username="cible_etud")
        target.set_password("TargetInitialPass123!")
        target.save()
        sg = NivSpeDepSGFactory(niv_spe_dep__departement=dep, niv_spe_dep__specialite__departement=dep)
        EtudiantFactory(user=target, niv_spe_dep_sg=sg)

        client.force_login(user_viewer)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        # Tentative de reset automatique
        url_reset = f"/departement/admin/authentification/customuser/{target.id}/reset-password/"
        resp_reset = client.post(url_reset, follow=True)
        assert resp_reset.status_code == 200
        target.refresh_from_db()
        assert target.check_password("TargetInitialPass123!"), "Le mot de passe ne doit pas changer sans user_change !"

        # Tentative de set password
        url_set = f"/departement/admin/authentification/customuser/{target.id}/set-password/"
        resp_set = client.post(
            url_set,
            {"new_password": "NewStrongPass999!", "confirm_password": "NewStrongPass999!"},
            follow=True,
        )
        assert resp_set.status_code == 200
        target.refresh_from_db()
        assert target.check_password("TargetInitialPass123!"), "Le mot de passe ne doit pas changer sans user_change !"

    def test_r5_cannot_reset_superuser_staff_or_active_poste(self, client):
        """Le chef ne peut pas réinitialiser le mot de passe d'un superuser, d'un staff ou d'un utilisateur avec poste actif."""
        dep = DepartementFactory()
        annee = AnneeUniversitaireFactory(est_courante=True)

        chef = UserFactory(username="chef_dep")
        poste_chef = PosteFactory(code="chef")
        AffectationPosteFactory(user=chef, poste=poste_chef, departement=dep, annee_univ=annee, est_actif=True)
        PostePermissionFactory(poste=poste_chef, user_view=True, user_change=True)

        client.force_login(chef)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        sg = NivSpeDepSGFactory(niv_spe_dep__departement=dep, niv_spe_dep__specialite__departement=dep)

        # Cible 1 : superuser
        target_su = UserFactory(username="admin_su", is_superuser=True)
        target_su.set_password("SecretAdminPass123!")
        target_su.save()
        EtudiantFactory(user=target_su, niv_spe_dep_sg=sg)

        # Cible 2 : staff
        target_staff = UserFactory(username="staff_member", is_staff=True)
        target_staff.set_password("SecretStaffPass123!")
        target_staff.save()
        EtudiantFactory(user=target_staff, niv_spe_dep_sg=sg)

        # Cible 3 : poste actif (responsable)
        target_resp = UserFactory(username="responsable_pedago")
        target_resp.set_password("SecretRespPass123!")
        target_resp.save()
        poste_resp = PosteFactory(code="resp_pedago")
        AffectationPosteFactory(user=target_resp, poste=poste_resp, departement=dep, annee_univ=annee, est_actif=True)
        EtudiantFactory(user=target_resp, niv_spe_dep_sg=sg)

        for target in (target_su, target_staff, target_resp):
            url = f"/departement/admin/authentification/customuser/{target.id}/reset-password/"
            client.post(url, follow=True)
            target.refresh_from_db()
            assert not getattr(target, "doit_changer_mot_de_passe", False)

        assert target_su.check_password("SecretAdminPass123!")
        assert target_staff.check_password("SecretStaffPass123!")
        assert target_resp.check_password("SecretRespPass123!")

    def test_r5_successful_reset_activates_doit_changer_mot_de_passe(self, client):
        """Une réinitialisation réussie par le chef positionne doit_changer_mot_de_passe=True."""
        dep = DepartementFactory()
        annee = AnneeUniversitaireFactory(est_courante=True)

        chef = UserFactory(username="chef_dep_r5")
        poste_chef = PosteFactory(code="chef_r5")
        AffectationPosteFactory(user=chef, poste=poste_chef, departement=dep, annee_univ=annee, est_actif=True)
        PostePermissionFactory(poste=poste_chef, user_view=True, user_change=True)

        client.force_login(chef)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        # Étudiant normal sans privilèges
        target = UserFactory(username="etud_normal", is_superuser=False, is_staff=False)
        target.set_password("OldNormalPass123!")
        target.doit_changer_mot_de_passe = False
        target.save()
        sg = NivSpeDepSGFactory(niv_spe_dep__departement=dep, niv_spe_dep__specialite__departement=dep)
        EtudiantFactory(user=target, niv_spe_dep_sg=sg)

        # 1. Reset automatique
        url_reset = f"/departement/admin/authentification/customuser/{target.id}/reset-password/"
        client.post(url_reset, follow=True)
        target.refresh_from_db()
        assert not target.check_password("OldNormalPass123!")
        assert target.doit_changer_mot_de_passe is True

        # 2. Set password personnalisé
        url_set = f"/departement/admin/authentification/customuser/{target.id}/set-password/"
        target.doit_changer_mot_de_passe = False
        target.save()

        client.post(
            url_set,
            {"new_password": "NewStrongManualPass123!", "confirm_password": "NewStrongManualPass123!"},
            follow=True,
        )
        target.refresh_from_db()
        assert target.check_password("NewStrongManualPass123!")
        assert target.doit_changer_mot_de_passe is True


@pytest.mark.django_db
class TestR6SignalsLogging:
    """R6: Les signaux A09 enregistrent les exceptions au lieu de les ignorer silencieusement."""

    def test_r6_on_classe_save_and_delete_logs_exception(self, caplog):
        """Les erreurs levées lors du recalcul dans les signaux Classe sont loguées via logger.exception."""
        classe = ClasseFactory()
        ens_dep = EnsDepFactory()
        classe.enseignant = ens_dep
        classe.save()

        with (
            caplog.at_level(logging.ERROR),
            patch(
                "apps.academique.affectation.signals.recalculer_statistiques_ens_dep",
                side_effect=RuntimeError("Erreur calcul Ens_Dep"),
            ),
        ):
            # Déclenchement de on_classe_save
            classe.save()
            assert any("Erreur lors du recalcul des compteurs Ens_Dep" in record.message for record in caplog.records)

            caplog.clear()

            # Déclenchement de on_classe_delete
            classe.delete()
            assert any(
                "Erreur lors du recalcul des compteurs Ens_Dep après suppression" in record.message
                for record in caplog.records
            )
