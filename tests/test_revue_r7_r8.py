import warnings

import pytest
from django.core.paginator import UnorderedObjectListWarning
from django.urls import reverse

from tests.factories import DepartementFactory, SpecialiteFactory, UserFactory


@pytest.mark.django_db
class TestRevueR7R8:
    """Tests pour Groupe 5 : R7 (formatage) et R8 (pagination ordonnée)."""

    def test_r8_list_specialite_dep_ordered_by_nom_ar(self, client):
        """R8: list_Specialite_Dep retourne les spécialités triées par nom_ar."""
        user = UserFactory()
        dep = DepartementFactory()

        # Créer des spécialités avec différents nom_ar
        s3 = SpecialiteFactory(departement=dep, nom_ar="ج - إعلام آلي", code="INFO")
        s1 = SpecialiteFactory(departement=dep, nom_ar="أ - رياضيات", code="MATH")
        s2 = SpecialiteFactory(departement=dep, nom_ar="ب - فيزياء", code="PHYS")

        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        response = client.get(reverse("departement:list_Specialite_Dep"))
        assert response.status_code == 200

        specialites_page = list(response.context["specialites"])
        assert len(specialites_page) == 3
        # L'ordre doit être alphabétique sur nom_ar : s1, s2, s3
        assert [s.id for s in specialites_page] == [s1.id, s2.id, s3.id]

    def test_r8_list_specialite_dep_no_unordered_warning(self, client):
        """R8: La pagination de list_Specialite_Dep n'émet pas UnorderedObjectListWarning."""
        user = UserFactory()
        dep = DepartementFactory()
        SpecialiteFactory(departement=dep, nom_ar="تخصص 1")
        SpecialiteFactory(departement=dep, nom_ar="تخصص 2")

        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        with warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always")
            response = client.get(reverse("departement:list_Specialite_Dep"))
            assert response.status_code == 200

            unordered_warnings = [w for w in recorded_warnings if issubclass(w.category, UnorderedObjectListWarning)]
            assert len(unordered_warnings) == 0, f"UnorderedObjectListWarning détecté : {unordered_warnings}"
