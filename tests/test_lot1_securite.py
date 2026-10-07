import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.academique.departement.dep_admin.forms import EtudiantDepConfirmImportForm
from tests.factories import (
    AffectationPosteFactory,
    AnneeUniversitaireFactory,
    ClasseFactory,
    DepartementFactory,
    EnsDepFactory,
    EnseignantFactory,
    EtudiantFactory,
    NivSpeDepSGFactory,
    PosteFactory,
    PostePermissionFactory,
    UserFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestLot1Securite:
    """Tests de sécurité pour le Lot 1."""

    def test_a02_idor_reset_password_blocked_for_other_department_user(self, client):
        """A02: Un chef de département ne peut pas réinitialiser le mot de passe d'un utilisateur d'un autre département."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep_a = DepartementFactory(code="DEP_A")
        dep_b = DepartementFactory(code="DEP_B")

        chef = UserFactory(username="chef_a")
        poste_chef = PosteFactory(code="chef_dep")
        AffectationPosteFactory(user=chef, poste=poste_chef, departement=dep_a, annee_univ=annee)
        PostePermissionFactory(poste=poste_chef, user_change=True, user_view=True)

        # Utilisateur cible appartenant à dep_b
        user_b = UserFactory(username="etud_b")
        user_b.set_password("OldPassword123!")
        user_b.save()
        sg_b = NivSpeDepSGFactory(
            niv_spe_dep__departement=dep_b,
            niv_spe_dep__specialite__departement=dep_b,
        )
        EtudiantFactory(user=user_b, niv_spe_dep_sg=sg_b)

        client.force_login(chef)
        session = client.session
        session["selected_departement_id"] = dep_a.id
        session.save()

        # Tentative de réinitialisation via l'URL admin dep
        url = f"/departement/admin/authentification/customuser/{user_b.id}/reset-password/"
        client.post(url, follow=True)

        user_b.refresh_from_db()
        assert user_b.check_password("OldPassword123!"), "Le mot de passe de l'utilisateur d'un autre département a été modifié !"

    def test_a03_reset_password_requires_post(self, client):
        """A03: reset_password_view ne doit pas modifier le mot de passe sur un simple GET."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep = DepartementFactory()
        chef = UserFactory(username="chef_dep")
        poste_chef = PosteFactory(code="chef_dep")
        AffectationPosteFactory(user=chef, poste=poste_chef, departement=dep, annee_univ=annee)
        PostePermissionFactory(poste=poste_chef, user_change=True, user_view=True)

        etud_user = UserFactory(username="etud_dep", first_name="Ali", last_name="Ben")
        etud_user.set_password("SecretInitialPass123!")
        etud_user.save()
        sg = NivSpeDepSGFactory(
            niv_spe_dep__departement=dep,
            niv_spe_dep__specialite__departement=dep,
        )
        EtudiantFactory(user=etud_user, niv_spe_dep_sg=sg)

        client.force_login(chef)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        url = f"/departement/admin/authentification/customuser/{etud_user.id}/reset-password/"
        client.get(url)

        etud_user.refresh_from_db()
        assert etud_user.check_password("SecretInitialPass123!"), "Le mot de passe ne doit PAS être modifié sur un GET !"

    def test_a20_set_password_validates_password_strength(self, client):
        """A20: set_password_view doit rejeter les mots de passe trop faibles via validate_password."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep = DepartementFactory()
        chef = UserFactory(username="chef_dep")
        poste_chef = PosteFactory(code="chef_dep")
        AffectationPosteFactory(user=chef, poste=poste_chef, departement=dep, annee_univ=annee)
        PostePermissionFactory(poste=poste_chef, user_change=True, user_view=True)

        etud_user = UserFactory(username="etud_user")
        etud_user.set_password("OldStrongPassword123!")
        etud_user.save()
        sg = NivSpeDepSGFactory(
            niv_spe_dep__departement=dep,
            niv_spe_dep__specialite__departement=dep,
        )
        EtudiantFactory(user=etud_user, niv_spe_dep_sg=sg)

        client.force_login(chef)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        url = f"/departement/admin/authentification/customuser/{etud_user.id}/set-password/"
        # Tentative avec un mot de passe trivial de 4 caractères
        client.post(url, {"new_password": "1234", "confirm_password": "1234"}, follow=True)

        etud_user.refresh_from_db()
        assert etud_user.check_password("OldStrongPassword123!"), "Le mot de passe faible ne doit pas être accepté !"

    def test_a21_logout_view_rejects_or_confirms_on_get(self, client):
        """A21: logout_view ne doit pas déconnecter sur un simple GET."""
        user = UserFactory()
        client.force_login(user)

        client.get(reverse("auth:logout"))
        # Sur un GET, l'utilisateur doit toujours être authentifié (page de confirmation)
        assert "_auth_user_id" in client.session, "Un simple GET ne doit pas déconnecter l'utilisateur !"

        # Sur un POST, l'utilisateur est déconnecté
        client.post(reverse("auth:logout"))
        assert "_auth_user_id" not in client.session, "Le POST doit déconnecter l'utilisateur."

    def test_a06_etudiant_views_restricted_by_role_and_department(self, client):
        """A06: list_Etud et detail_Etud sont restreints aux permissions et au département."""
        dep_a = DepartementFactory()
        dep_b = DepartementFactory()

        sg_a = NivSpeDepSGFactory(niv_spe_dep__departement=dep_a, niv_spe_dep__specialite__departement=dep_a)
        sg_b = NivSpeDepSGFactory(niv_spe_dep__departement=dep_b, niv_spe_dep__specialite__departement=dep_b)

        etud_a = EtudiantFactory(niv_spe_dep_sg=sg_a)
        etud_b = EtudiantFactory(niv_spe_dep_sg=sg_b)

        # Un étudiant connecté tente d'accéder à la liste globale
        client.force_login(etud_a.user)
        resp_list = client.get(reverse("etudiant:list_Etud"))
        assert resp_list.status_code == 403, "Un simple étudiant ne doit pas accéder à list_Etud"

        # L'étudiant peut voir sa propre fiche
        resp_own = client.get(reverse("etudiant:detail_Etud", args=[etud_a.id]))
        assert resp_own.status_code == 200

        # Mais il ne peut pas voir la fiche d'un autre étudiant
        resp_other = client.get(reverse("etudiant:detail_Etud", args=[etud_b.id]))
        assert resp_other.status_code == 403, "Un étudiant ne doit pas voir la fiche d'un autre étudiant"

    def test_a07_sous_groupes_restricted_to_teacher_class(self, client):
        """A07: Un enseignant ne peut pas gérer les sous-groupes d'une classe d'un autre enseignant."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep = DepartementFactory()

        ens_1 = EnseignantFactory()
        ens_2 = EnseignantFactory()
        EnsDepFactory(enseignant=ens_1, departement=dep, annee_univ=annee)
        ens_dep_2 = EnsDepFactory(enseignant=ens_2, departement=dep, annee_univ=annee)

        sg = NivSpeDepSGFactory(niv_spe_dep__departement=dep, niv_spe_dep__specialite__departement=dep)
        classe_ens2 = ClasseFactory(enseignant=ens_dep_2, niv_spe_dep_sg=sg)

        # ens_1 tente d'accéder à la classe de ens_2
        client.force_login(ens_1.user)
        url = reverse("ense:page_nombre_sous_groupes", kwargs={"dep_id": dep.id, "classe_id": classe_ens2.id})
        resp = client.get(url)
        assert resp.status_code == 404, "Un enseignant ne doit pas pouvoir accéder à la classe d'un autre enseignant"

    def test_a08_etudiant_dep_confirm_import_form_scoped_to_department(self):
        """A08: EtudiantDepConfirmImportForm doit restreindre les groupes au département."""
        dep_a = DepartementFactory()
        dep_b = DepartementFactory()

        sg_b = NivSpeDepSGFactory(niv_spe_dep__departement=dep_b, niv_spe_dep__specialite__departement=dep_b)

        form = EtudiantDepConfirmImportForm(departement_id=dep_a.id, data={"niv_spe_dep_sg": sg_b.id})
        assert not form.is_valid(), "Le formulaire ne doit pas valider un groupe d'un autre département !"

    def test_a05_set_password_renders_safely_without_xss(self, client):
        """A05: Le template de set_password échappe les données utilisateur contre les failles XSS."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep = DepartementFactory()
        chef = UserFactory(username="chef_dep_xss")
        poste_chef = PosteFactory(code="chef_dep_xss")
        AffectationPosteFactory(user=chef, poste=poste_chef, departement=dep, annee_univ=annee)
        PostePermissionFactory(poste=poste_chef, user_change=True, user_view=True)

        xss_payload = "<script>alert('xss')</script>"
        etud_user = UserFactory(username="xss_user", first_name=xss_payload, last_name="Nom")
        sg = NivSpeDepSGFactory(
            niv_spe_dep__departement=dep,
            niv_spe_dep__specialite__departement=dep,
        )
        EtudiantFactory(user=etud_user, niv_spe_dep_sg=sg)

        client.force_login(chef)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        url = f"/departement/admin/authentification/customuser/{etud_user.id}/set-password/"
        response = client.get(url)
        assert response.status_code == 200
        # Vérifie que le script n'est pas inséré de manière brute
        content = response.content.decode("utf-8")
        assert "<script>alert('xss')</script>" not in content
        assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in content or "&lt;script&gt;" in content

    def test_a06_enseignant_views_restricted_by_role_and_department(self, client):
        """A06: list_Ens et detail_Ens sont restreints aux permissions et au département."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep_a = DepartementFactory()
        dep_b = DepartementFactory()

        ens_a = EnseignantFactory()
        ens_b = EnseignantFactory()
        EnsDepFactory(enseignant=ens_a, departement=dep_a, annee_univ=annee)
        EnsDepFactory(enseignant=ens_b, departement=dep_b, annee_univ=annee)

        # Un enseignant standard sans droit enseignant_view ne peut pas voir list_Ens
        client.force_login(ens_a.user)
        resp_list = client.get(reverse("ense:list_Ens"))
        assert resp_list.status_code == 403, "Un simple enseignant ne doit pas accéder à list_Ens"

        # L'enseignant peut voir sa propre fiche
        resp_own = client.get(reverse("ense:detail_Ens", args=[ens_a.id]))
        assert resp_own.status_code == 200

        # Mais ne peut pas voir la fiche d'un enseignant d'un autre département
        resp_other = client.get(reverse("ense:detail_Ens", args=[ens_b.id]))
        assert resp_other.status_code == 403

    def test_a07_liste_sous_groupes_direct_restricted_to_teacher(self, client):
        """A07: liste_sous_groupes et affecter_direct_sous_groupes vérifient que l'enseignant enseigne le groupe."""
        annee = AnneeUniversitaireFactory(est_courante=True)
        dep = DepartementFactory()

        ens_1 = EnseignantFactory()
        ens_2 = EnseignantFactory()
        EnsDepFactory(enseignant=ens_1, departement=dep, annee_univ=annee)
        ens_dep_2 = EnsDepFactory(enseignant=ens_2, departement=dep, annee_univ=annee)

        sg = NivSpeDepSGFactory(niv_spe_dep__departement=dep, niv_spe_dep__specialite__departement=dep)
        ClasseFactory(enseignant=ens_dep_2, niv_spe_dep_sg=sg)

        # ens_1 tente d'accéder aux sous-groupes d'un groupe qu'il n'enseigne pas
        client.force_login(ens_1.user)
        url = reverse("ense:liste_sous_groupes", kwargs={"dep_id": dep.id, "niv_spe_dep_sg_id": sg.id})
        resp = client.get(url)
        assert resp.status_code == 404
