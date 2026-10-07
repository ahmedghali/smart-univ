"""Tests pour la Phase 2 bis - Groupe 3 : R4.

Correction de l'erreur 500 sur /departement/api/dashboard-stats/ :
- Sérialisation correcte de annee_courante en str
- Log de l'exception dans get_department_stats
"""

import logging
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.academique.departement.views import get_default_stats, get_department_stats
from tests.factories import (
    AffectationPosteFactory,
    AnneeUniversitaireFactory,
    DepartementFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestR4DashboardStatsApi:
    """R4: Vérification que l'API /departement/api/dashboard-stats/ sérialise l'année sans erreur 500."""

    def test_r4_dashboard_stats_api_success(self, client):
        """L'API /departement/api/dashboard-stats/ renvoie un JSON valide (statut 200) avec annee_courante en chaîne."""
        dep = DepartementFactory()
        annee = AnneeUniversitaireFactory(est_courante=True)
        user = UserFactory()
        AffectationPosteFactory(user=user, departement=dep, annee_univ=annee, est_actif=True)

        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        url = reverse("depa:dashboard_stats_api")
        resp = client.get(url)

        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

        data = resp.json()
        assert "annee_courante" in data
        assert isinstance(data["annee_courante"], str)
        assert data["annee_courante"] == str(annee)
        assert "total_teachers" in data
        assert "total_students" in data
        assert "total_classes" in data

    def test_r4_get_department_stats_logs_exception_on_failure(self, caplog):
        """get_department_stats logue l'exception rencontrée au lieu de la masquer silencieusement."""
        dep = DepartementFactory()
        annee = AnneeUniversitaireFactory(est_courante=True)

        with (
            caplog.at_level(logging.ERROR),
            patch(
                "apps.academique.departement.views.StatsCalculator.get_all_stats",
                side_effect=RuntimeError("Calculateur en panne"),
            ),
        ):
            stats = get_department_stats(dep, annee)

        assert stats == get_default_stats()
        assert any(
            "Erreur lors du calcul des statistiques du département" in record.message for record in caplog.records
        )
