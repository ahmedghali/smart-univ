from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

from apps.academique.affectation.models import Classe, Gestion_Etu_Classe
from apps.academique.affectation.services import recalculer_statistiques_ens_dep
from apps.academique.departement.dep_admin.resources import EtudiantResource
from apps.academique.departement.views import StatsCalculator
from apps.noyau.commun.models import AnneeUniversitaire
from tests.factories import (
    AnneeUniversitaireFactory,
    ClasseFactory,
    DepartementFactory,
    EnsDepFactory,
    EtudiantFactory,
    GestionEtuClasseFactory,
    NivSpeDepFactory,
    NivSpeDepSGFactory,
    SemestreFactory,
)


@pytest.mark.django_db
class TestLot3CalculsEtMetier:
    """Tests pour le Lot 3 (A10, A09, A11, A23, A24)."""

    # ══════════════════════════════════════════════════════════
    # A10 : Calculs notes et présences
    # ══════════════════════════════════════════════════════════

    def test_a10_note_presence_zero_seances_reste_cinq(self):
        """A10: Quand 0 séance n'a été effectuée, la note de présence ne doit pas tomber à 0 (5/5 de départ)."""
        gestion = GestionEtuClasseFactory(
            nbr_absence=0,
            nbr_absence_justifiee=0,
        )
        gestion.calculate_note_presence()
        gestion.calculate_note_finale()
        gestion.save()

        assert gestion.note_presence == Decimal("5.00")
        assert gestion.note_finale == Decimal("5.00")

    def test_a10_note_presence_absences_justifiees_vs_non_justifiees(self):
        """A10: Formule 5 - absences non justifiées. Les absences justifiées ne pénalisent pas l'étudiant."""
        gestion = GestionEtuClasseFactory(
            nbr_absence=3,
            nbr_absence_justifiee=2,  # 1 seule absence non justifiée
        )
        gestion.calculate_note_presence()
        gestion.calculate_note_finale()
        gestion.save()

        # 5 - 1 = 4.00
        assert gestion.note_presence == Decimal("4.00")
        assert gestion.note_finale == Decimal("4.00")

    def test_a10_note_presence_minimum_zero(self):
        """A10: Au-delà de 5 absences non justifiées, la note de présence est plafonnée à 0."""
        gestion = GestionEtuClasseFactory(
            nbr_absence=7,
            nbr_absence_justifiee=0,
        )
        gestion.calculate_note_presence()
        gestion.calculate_note_finale()
        gestion.save()

        assert gestion.note_presence == Decimal("0.00")

    def test_a10_note_finale_plafond_vingt(self):
        """A10: La note finale est bornée à 20 même si les composantes dépassent."""
        gestion = GestionEtuClasseFactory(
            nbr_absence=0,
            nbr_absence_justifiee=0,
            note_participe_HW=Decimal("5.00"),
            note_controle_1=Decimal("10.00"),
            note_controle_2=Decimal("10.00"),
        )
        # Total composantes = 5 + 5 + 10 + 10 = 30
        gestion.calculate_note_presence()
        gestion.calculate_note_finale()
        gestion.save()

        assert gestion.note_finale == Decimal("20.00")

    def test_a10_update_all_presence_notes_recalcule_note_finale(self):
        """A10: update_all_presence_notes_for_classe recalcule note_presence ET note_finale."""
        classe = ClasseFactory()
        gestion = GestionEtuClasseFactory(
            classe=classe,
            nbr_absence=2,
            nbr_absence_justifiee=0,
            note_participe_HW=Decimal("3.00"),
            note_controle_1=Decimal("4.00"),
            note_controle_2=Decimal("5.00"),
            validee_par_enseignant=False,
        )
        Gestion_Etu_Classe.update_all_presence_notes_for_classe(classe)
        gestion.refresh_from_db()

        # note_presence = 5 - 2 = 3.00
        # note_finale = 3.00 (presence) + 3.00 (participe) + 4.00 (ctrl1) + 5.00 (ctrl2) = 15.00
        assert gestion.note_presence == Decimal("3.00")
        assert gestion.note_finale == Decimal("15.00")

    # ══════════════════════════════════════════════════════════
    # A09 : Compteurs Ens_Dep et signaux
    # ══════════════════════════════════════════════════════════

    def test_a09_recalculer_statistiques_ens_dep(self):
        """A09: Recalcul des compteurs Ens_Dep à partir d'une classe de 1h30 de cours dans le département."""
        dep = DepartementFactory()
        ens_dep = EnsDepFactory(departement=dep)
        s1 = SemestreFactory(numero=1, code="S1")

        niv_spe_dep = NivSpeDepFactory(departement=dep)
        sg = NivSpeDepSGFactory(niv_spe_dep=niv_spe_dep)

        classe = ClasseFactory(
            enseignant=ens_dep,
            semestre=s1,
            niv_spe_dep_sg=sg,
            type=Classe.Typeblock.COURS,
            temps=Classe.Timeblock.CLASSE01,  # "08:00-09:30" => 1.5h
            jour=Classe.Dayblock.SUNDAY,
        )

        recalculer_statistiques_ens_dep(ens_dep)
        ens_dep.refresh_from_db()

        assert ens_dep.nbrClas_Cours_in_Dep_S1 == 1
        assert ens_dep.nbrClas_in_Dep_S1 == 1
        assert ens_dep.volHor_in_Dep_S1 == Decimal("1.50")
        assert ens_dep.nbrJour_in_Dep_S1 == 1

        # Test suppression via signal post_delete
        classe.delete()
        ens_dep.refresh_from_db()

        assert ens_dep.nbrClas_Cours_in_Dep_S1 == 0
        assert ens_dep.nbrClas_in_Dep_S1 == 0
        assert ens_dep.volHor_in_Dep_S1 == Decimal("0.00")

    def test_a09_management_command_recalculer_compteurs(self):
        """A09: Commande manage.py recalculer_compteurs s'exécute sans erreur."""
        dep = DepartementFactory()
        EnsDepFactory(departement=dep)
        call_command("recalculer_compteurs")

    # ══════════════════════════════════════════════════════════
    # A11 : Import Excel EtudiantResource
    # ══════════════════════════════════════════════════════════

    def test_a11_import_rejette_ligne_sans_matricule(self):
        """A11: Une ligne sans matricule lève une ValidationError lisible au lieu de générer un matricule aléatoire."""
        resource = EtudiantResource()
        row = {"matricule": "", "nom_fr": "Dupont", "prenom_fr": "Jean"}

        with pytest.raises(ValidationError) as exc_info:
            resource.before_import_row(row, row_number=4)

        assert "matricule est obligatoire" in str(exc_info.value).lower()

    def test_a11_import_num_ins_vide_devient_none(self):
        """A11: Un num_ins vide reste None sans générer de faux identifiant TMP."""
        resource = EtudiantResource()
        row = {"matricule": "ETU2025001", "num_ins": "", "nom_fr": "Dupont"}

        resource.before_import_row(row, row_number=1)

        assert row["matricule"] == "ETU2025001"
        assert row["num_ins"] is None

    # ══════════════════════════════════════════════════════════
    # A23 : Décompte d'étudiants par département
    # ══════════════════════════════════════════════════════════

    def test_a23_total_students_filtre_par_departement(self):
        """A23: Le tableau de bord départemental ne compte que les étudiants de son département."""
        dep1 = DepartementFactory()
        dep2 = DepartementFactory()

        niv1 = NivSpeDepFactory(departement=dep1)
        sg1 = NivSpeDepSGFactory(niv_spe_dep=niv1)

        niv2 = NivSpeDepFactory(departement=dep2)
        sg2 = NivSpeDepSGFactory(niv_spe_dep=niv2)

        # 2 étudiants dans Dep1, 3 étudiants dans Dep2
        EtudiantFactory.create_batch(2, niv_spe_dep_sg=sg1)
        EtudiantFactory.create_batch(3, niv_spe_dep_sg=sg2)

        annee = AnneeUniversitaireFactory()
        calculator = StatsCalculator(departement=dep1, annee_univ=annee)
        calculator.get_teacher_stats = MagicMock(return_value={
            "vacataire_teachers": 0,
            "associe_teachers": 0,
            "doctorant_teachers": 0,
            "permanent_vacataire_teachers": 0,
        })

        stats = calculator.get_all_stats()
        assert stats["total_students"] == 2

    # ══════════════════════════════════════════════════════════
    # A24 : Unicité de l'année courante
    # ══════════════════════════════════════════════════════════

    def test_a24_annee_universitaire_save_desactive_anciennes_courantes(self):
        """A24: Définir est_courante=True désactive automatiquement les autres années courantes."""
        annee1 = AnneeUniversitaireFactory(est_courante=True)
        assert annee1.est_courante is True

        annee2 = AnneeUniversitaireFactory(est_courante=True)
        annee1.refresh_from_db()

        assert annee2.est_courante is True
        assert annee1.est_courante is False
        assert AnneeUniversitaire.get_courante() == annee2
