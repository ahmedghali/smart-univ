from unittest.mock import MagicMock, patch

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from apps.academique.affectation.models import Classe, Seance
from apps.academique.departement.dep_admin.admins import DepartementReadOnlyAdmin
from apps.academique.departement.dep_admin.mixins import (
    PermissionCheckMixinNoImport,
    _admin_request_var,
)
from apps.academique.departement.models import Departement, NivSpeDep, NivSpeDep_SG
from apps.academique.enseignant.views.consultation import list_NivSpeDep_Ens
from apps.academique.enseignant.views.emploi_temps import timeTable_Ens
from apps.noyau.commun.middleware import ObjectDoesNotExistMiddleware
from tests.factories import (
    ClasseFactory,
    DepartementFactory,
    EnsDepFactory,
    EnseignantFactory,
    EtudiantFactory,
    NivSpeDepFactory,
    NivSpeDepSGFactory,
    SemestreFactory,
    UserFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestLot4PerfFiabilite:
    """Tests pour le Lot 4 (A14, A15, A16, A17, A27, A29)."""

    # ══════════════════════════════════════════════════════════
    # A14 : Aucun save() dans la vue GET emploi du temps
    # ══════════════════════════════════════════════════════════

    def test_a14_no_save_on_get_timeTable_Ens(self, rf):
        """A14: La vue GET timeTable_Ens ne persiste pas l'objet Classe en base."""
        dep = DepartementFactory()
        ens = EnseignantFactory()
        ens_dep = EnsDepFactory(enseignant=ens, departement=dep)
        semestre = SemestreFactory(numero=1, code="S1")

        classe = ClasseFactory(
            enseignant=ens_dep,
            semestre=semestre,
            seance_created=True,
        )
        Seance.objects.create(
            classe=classe,
            date="2025-01-01",
            fait=True,
        )

        request = rf.get(f"/enseignant/timetable/{dep.id}/")
        request.user = ens.user
        request.session = {}

        with patch.object(Classe, "save", autospec=True) as mock_save:
            timeTable_Ens(request, dep_id=dep.id, enseignant=ens, departement=dep)
            assert mock_save.call_count == 0, "Classe.save() ne doit pas être appelé dans une requête GET !"

    # ══════════════════════════════════════════════════════════
    # A15 : Aucun save() en boucle dans list_NivSpeDep_Ens
    # ══════════════════════════════════════════════════════════

    def test_a15_no_loop_save_in_list_nivspedep(self, rf):
        """A15: list_NivSpeDep_Ens ne sauvegarde pas les objets en base à chaque affichage GET."""
        dep = DepartementFactory()
        ens = EnseignantFactory()
        EnsDepFactory(enseignant=ens, departement=dep)
        niv = NivSpeDepFactory(departement=dep)
        NivSpeDepSGFactory(niv_spe_dep=niv)

        request = rf.get(f"/enseignant/departement/{dep.id}/niveaux-specialites/")
        request.user = ens.user
        request.session = {}

        with patch.object(NivSpeDep, "save", autospec=True) as mock_save_niv:
            with patch.object(NivSpeDep_SG, "save", autospec=True) as mock_save_sg:
                list_NivSpeDep_Ens(request, dep_id=dep.id, enseignant=ens, departement=dep)
                assert mock_save_niv.call_count == 0, "NivSpeDep.save() ne doit pas être appelé en boucle dans un GET !"
                assert mock_save_sg.call_count == 0, "NivSpeDep_SG.save() ne doit pas être appelé en boucle dans un GET !"

    # ══════════════════════════════════════════════════════════
    # A16 : Transaction atomique sur la génération des absences
    # ══════════════════════════════════════════════════════════

    def test_a16_seances_uses_atomic_transaction(self):
        """A16: Le module seances importe et utilise transaction.atomic dans update_seance."""
        import inspect

        from apps.academique.enseignant.views import seances

        source = inspect.getsource(seances.update_seance)
        assert "transaction.atomic" in source, "update_seance doit utiliser with transaction.atomic():"

    # ══════════════════════════════════════════════════════════
    # A17 : Pas de stockage de requête sur l'instance ModelAdmin
    # ══════════════════════════════════════════════════════════

    def test_a17_no_self_current_request_mutation_on_admin(self, rf):
        """A17: ModelAdmin n'écrit pas _current_request sur l'instance partagée (utilise contextvars)."""
        request = rf.get("/admin/")
        request.resolver_match = MagicMock()
        request.resolver_match.namespace = "dep_admin"

        request.user = UserFactory(is_superuser=True)

        class DummyModelAdmin(PermissionCheckMixinNoImport, admin.ModelAdmin):
            pass

        admin_instance = DummyModelAdmin(Departement, MagicMock())
        admin_instance.admin_site = MagicMock()
        admin_instance.admin_site.name = "dep_admin"

        with patch.object(admin.ModelAdmin, "changelist_view", return_value=MagicMock()):
            admin_instance.changelist_view(request)
            assert not hasattr(admin_instance, "_current_request"), "L'instance ModelAdmin ne doit plus porter _current_request !"
            assert _admin_request_var.get() == request

            # Vérifier aussi DepartementReadOnlyAdmin
            dep_admin = DepartementReadOnlyAdmin(Departement, MagicMock())
            dep_admin.changelist_view(request)
            assert not hasattr(dep_admin, "_current_request"), "DepartementReadOnlyAdmin ne doit plus porter _current_request !"

    # ══════════════════════════════════════════════════════════
    # A27 : Pagination des listes de departement/views.py
    # ══════════════════════════════════════════════════════════

    def test_a27_pagination_list_etudiants(self, client):
        """A27: list_etudiants pagine les résultats (25 par page)."""
        dep = DepartementFactory()
        niv = NivSpeDepFactory(departement=dep)
        sg = NivSpeDepSGFactory(niv_spe_dep=niv)
        EtudiantFactory.create_batch(30, niv_spe_dep_sg=sg)

        user = UserFactory(is_superuser=True)
        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        response = client.get("/departement/etudiants/?page=1")
        assert response.status_code == 200
        assert "etudiants" in response.context
        assert len(response.context["etudiants"]) == 25

        response2 = client.get("/departement/etudiants/?page=2")
        assert response2.status_code == 200
        assert len(response2.context["etudiants"]) == 5

    # ══════════════════════════════════════════════════════════
    # A29 : ObjectDoesNotExistMiddleware ciblé sur les profils
    # ══════════════════════════════════════════════════════════

    def test_a29_middleware_converts_missing_profile_to_404(self, rf):
        """A29: RelatedObjectDoesNotExist sur profil manquant renvoie 404."""
        middleware = ObjectDoesNotExistMiddleware(lambda req: None)
        user = UserFactory()
        request = rf.get("/departement/1/")
        request.user = user

        # Déclenche RelatedObjectDoesNotExist sur enseignant_profile
        try:
            _ = user.enseignant_profile
        except ObjectDoesNotExist as exc:
            res = middleware.process_exception(request, exc)
            assert res is not None
            assert res.status_code == 404

        # Déclenche RelatedObjectDoesNotExist sur etudiant_profile
        try:
            _ = user.etudiant_profile
        except ObjectDoesNotExist as exc:
            res = middleware.process_exception(request, exc)
            assert res is not None
            assert res.status_code == 404

    def test_a29_middleware_propagates_other_does_not_exist(self, rf):
        """A29: Les autres DoesNotExist (ex: Departement.DoesNotExist) retournent None pour erreur 500."""
        middleware = ObjectDoesNotExistMiddleware(lambda req: None)
        request = rf.get("/departement/999/")
        request.user = UserFactory()

        try:
            Departement.objects.get(id=999999)
        except Departement.DoesNotExist as exc:
            res = middleware.process_exception(request, exc)
            assert res is None, "Les erreurs DoesNotExist ordinaires doivent remonter normalement (500) !"
