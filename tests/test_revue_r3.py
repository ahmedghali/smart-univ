"""Tests pour la Phase 2 bis - Groupe 2 : R3.

Recalcul dynamique via signaux et commande recalculer_compteurs des valeurs :
- Classe.taux_avancement
- NivSpeDep.nbr_matieres_s1 / s2
- NivSpeDep.nbr_etudiants
- NivSpeDep_SG.nbr_etudiants_SG
"""

import pytest
from django.core.management import call_command

from apps.academique.affectation.models import Classe, Seance
from apps.academique.departement.models import Matiere, NivSpeDep, NivSpeDep_SG
from tests.factories import (
    ClasseFactory,
    EtudiantFactory,
    MatiereFactory,
    NivSpeDepFactory,
    NivSpeDepSGFactory,
    SemestreFactory,
)


@pytest.mark.django_db
class TestR3ValeursCalculeesSignaux:
    """R3: Maintien automatique des champs calculés via signaux post_save / post_delete."""

    def test_r3_signal_seance_updates_classe_taux_avancement(self):
        """Les ajouts, modifications et suppressions de séances recalculent Classe.taux_avancement."""
        classe = ClasseFactory()
        assert classe.taux_avancement == 0

        # Création de séances non effectuées
        s1 = Seance.objects.create(classe=classe, fait=False, temps=Seance.Timeblock.SEANCE01)
        s2 = Seance.objects.create(classe=classe, fait=False, temps=Seance.Timeblock.SEANCE02)
        classe.refresh_from_db()
        assert classe.taux_avancement == 0

        # 1 séance sur 2 effectuée -> 50%
        s1.fait = True
        s1.save()
        classe.refresh_from_db()
        assert classe.taux_avancement == 50

        # 2 séances sur 2 effectuées -> 100%
        s2.fait = True
        s2.save()
        classe.refresh_from_db()
        assert classe.taux_avancement == 100

        # Suppression d'une séance -> 1 sur 1 effectuée -> 100%
        s2.delete()
        classe.refresh_from_db()
        assert classe.taux_avancement == 100

        # Suppression de la dernière séance -> 0%
        s1.delete()
        classe.refresh_from_db()
        assert classe.taux_avancement == 0

    def test_r3_signal_matiere_updates_niv_spe_dep_nbr_matieres(self):
        """Les ajouts et suppressions de matières recalculent NivSpeDep.nbr_matieres_s1 et s2."""
        nsd = NivSpeDepFactory()
        s1 = SemestreFactory(numero=1, code="S1_TEST")
        s2 = SemestreFactory(numero=2, code="S2_TEST")

        nsd.refresh_from_db()
        assert nsd.nbr_matieres_s1 == 0
        assert nsd.nbr_matieres_s2 == 0

        # Ajout d'une matière S1
        m1 = Matiere.objects.create(niv_spe_dep=nsd, semestre=s1, nom_fr="Algèbre", code="ALG1")
        nsd.refresh_from_db()
        assert nsd.nbr_matieres_s1 == 1
        assert nsd.nbr_matieres_s2 == 0

        # Ajout d'une matière S2
        m2 = Matiere.objects.create(niv_spe_dep=nsd, semestre=s2, nom_fr="Analyse", code="ANA2")
        nsd.refresh_from_db()
        assert nsd.nbr_matieres_s1 == 1
        assert nsd.nbr_matieres_s2 == 1

        # Suppression de la matière S1
        m1.delete()
        nsd.refresh_from_db()
        assert nsd.nbr_matieres_s1 == 0
        assert nsd.nbr_matieres_s2 == 1

        # Nettoyage
        m2.delete()
        nsd.refresh_from_db()
        assert nsd.nbr_matieres_s2 == 0

    def test_r3_signal_etudiant_updates_effectifs(self):
        """Les ajouts et suppressions d'étudiants recalculent NivSpeDep.nbr_etudiants et NivSpeDep_SG.nbr_etudiants_SG."""
        nsd = NivSpeDepFactory()
        nsd_sg = NivSpeDepSGFactory(niv_spe_dep=nsd, type_affectation="par_groupe")

        nsd.refresh_from_db()
        nsd_sg.refresh_from_db()
        assert nsd.nbr_etudiants == 0
        assert nsd_sg.nbr_etudiants_SG == 0

        # Création du 1er étudiant
        e1 = EtudiantFactory(niv_spe_dep_sg=nsd_sg)
        nsd.refresh_from_db()
        nsd_sg.refresh_from_db()
        assert nsd.nbr_etudiants == 1
        assert nsd_sg.nbr_etudiants_SG == 1

        # Création du 2ème étudiant
        e2 = EtudiantFactory(niv_spe_dep_sg=nsd_sg)
        nsd.refresh_from_db()
        nsd_sg.refresh_from_db()
        assert nsd.nbr_etudiants == 2
        assert nsd_sg.nbr_etudiants_SG == 2

        # Suppression d'un étudiant
        e2.delete()
        nsd.refresh_from_db()
        nsd_sg.refresh_from_db()
        assert nsd.nbr_etudiants == 1
        assert nsd_sg.nbr_etudiants_SG == 1

        # Suppression du dernier
        e1.delete()
        nsd.refresh_from_db()
        nsd_sg.refresh_from_db()
        assert nsd.nbr_etudiants == 0
        assert nsd_sg.nbr_etudiants_SG == 0

    def test_r3_etudiant_reaffectation_updates_both_groups(self):
        """Le changement de groupe d'un étudiant met à jour les compteurs de l'ancien et du nouveau groupe."""
        nsd = NivSpeDepFactory()
        sg1 = NivSpeDepSGFactory(niv_spe_dep=nsd, type_affectation="par_groupe")
        sg2 = NivSpeDepSGFactory(niv_spe_dep=nsd, type_affectation="par_groupe")

        e = EtudiantFactory(niv_spe_dep_sg=sg1)
        sg1.refresh_from_db()
        sg2.refresh_from_db()
        assert sg1.nbr_etudiants_SG == 1
        assert sg2.nbr_etudiants_SG == 0

        # Réaffectation vers sg2
        e.niv_spe_dep_sg = sg2
        e.save()
        sg1.refresh_from_db()
        sg2.refresh_from_db()
        assert sg1.nbr_etudiants_SG == 0
        assert sg2.nbr_etudiants_SG == 1

    def test_r3_recalculer_compteurs_command_syncs_all(self):
        """La commande recalculer_compteurs synchronise toutes les valeurs calculées."""
        classe = ClasseFactory()
        Seance.objects.create(classe=classe, fait=True, temps=Seance.Timeblock.SEANCE01)
        Seance.objects.create(classe=classe, fait=False, temps=Seance.Timeblock.SEANCE02)

        nsd = NivSpeDepFactory()
        s1 = SemestreFactory(numero=1, code="S1_CMD")
        MatiereFactory(niv_spe_dep=nsd, semestre=s1)

        nsd_sg = NivSpeDepSGFactory(niv_spe_dep=nsd, type_affectation="par_groupe")
        EtudiantFactory(niv_spe_dep_sg=nsd_sg)

        # Corrompre volontairement les valeurs en base avec .update() (sans signaux)
        Classe.objects.filter(pk=classe.pk).update(taux_avancement=99)
        NivSpeDep.objects.filter(pk=nsd.pk).update(nbr_matieres_s1=99, nbr_etudiants=99)
        NivSpeDep_SG.objects.filter(pk=nsd_sg.pk).update(nbr_etudiants_SG=99)

        # Exécuter la commande
        call_command("recalculer_compteurs")

        # Vérifier que tout est restauré correctement
        classe.refresh_from_db()
        assert classe.taux_avancement == 50

        nsd.refresh_from_db()
        assert nsd.nbr_matieres_s1 == 1
        assert nsd.nbr_etudiants == 1

        nsd_sg.refresh_from_db()
        assert nsd_sg.nbr_etudiants_SG == 1


@pytest.mark.django_db
def test_r3_groupe_tous_etudiants_compte_les_etudiants_des_autres_groupes():
    """Un étudiant ajouté à un groupe du niveau est aussi compté dans le groupe « tous les étudiants »."""
    nsd = NivSpeDepFactory()
    tous = NivSpeDepSGFactory(niv_spe_dep=nsd, type_affectation="tous_etudiants")
    groupe = NivSpeDepSGFactory(niv_spe_dep=nsd, type_affectation="par_groupe")

    etudiant = EtudiantFactory(niv_spe_dep_sg=groupe)
    tous.refresh_from_db()
    assert tous.nbr_etudiants_SG == 1

    etudiant.delete()
    tous.refresh_from_db()
    assert tous.nbr_etudiants_SG == 0
