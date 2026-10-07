import factory
from django.contrib.auth import get_user_model

from apps.academique.affectation.models import Classe, Ens_Dep, SousGroupe
from apps.academique.departement.models import Departement, Matiere, NivSpeDep, NivSpeDep_SG, Specialite
from apps.academique.enseignant.models import Enseignant
from apps.academique.etudiant.models import Etudiant
from apps.academique.faculte.models import Faculte
from apps.academique.universite.models import Universite
from apps.noyau.commun.models import (
    AffectationPoste,
    AnneeUniversitaire,
    Niveau,
    Poste,
    PostePermission,
    Semestre,
    Wilaya,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = "Prénom"
    last_name = "Nom"
    is_active = True


class WilayaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wilaya

    code = factory.Sequence(lambda n: f"W{n:02d}")
    nom_ar = "الجزائر"
    nom_fr = "Alger"


class UniversiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Universite

    code = factory.Sequence(lambda n: f"UNIV_{n}")
    nom_ar = "جامعة"
    nom_fr = "Université"


class FaculteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Faculte

    code = factory.Sequence(lambda n: f"FAC_{n}")
    nom_ar = "كلية"
    nom_fr = "Faculté"
    universite = factory.SubFactory(UniversiteFactory)


class DepartementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Departement

    code = factory.Sequence(lambda n: f"DEP_{n}")
    nom_ar = "قسم"
    nom_fr = "Département"
    faculte = factory.SubFactory(FaculteFactory)


class AnneeUniversitaireFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnneeUniversitaire

    nom = factory.Sequence(lambda n: f"{2020 + n}-{2021 + n}")
    date_debut = "2024-09-01"
    date_fin = "2025-06-30"
    est_courante = True


class PosteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Poste

    code = factory.Sequence(lambda n: f"POSTE_{n}")
    type = "admin"
    nom_ar = "منصب"
    nom_fr = "Poste"


class AffectationPosteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AffectationPoste

    user = factory.SubFactory(UserFactory)
    poste = factory.SubFactory(PosteFactory)
    niveau_contexte = AffectationPoste.NIVEAU_DEPARTEMENT
    departement = factory.SubFactory(DepartementFactory)
    annee_univ = factory.SubFactory(AnneeUniversitaireFactory)
    date_debut = "2024-09-01"
    est_actif = True


class PostePermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PostePermission

    poste = factory.SubFactory(PosteFactory)


class NiveauFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Niveau

    code = factory.Sequence(lambda n: f"L{n}")
    nom_ar = "مستوى"
    nom_fr = "Niveau"


class SpecialiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Specialite

    code = factory.Sequence(lambda n: f"SPEC_{n}")
    nom_ar = "تخصص"
    nom_fr = "Spécialité"
    departement = factory.SubFactory(DepartementFactory)


class NivSpeDepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NivSpeDep

    niveau = factory.SubFactory(NiveauFactory)
    specialite = factory.SubFactory(SpecialiteFactory)
    departement = factory.LazyAttribute(lambda o: o.specialite.departement)


class NivSpeDepSGFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NivSpeDep_SG

    niv_spe_dep = factory.SubFactory(NivSpeDepFactory)
    type_affectation = "tous_etudiants"


class SemestreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Semestre

    numero = factory.Sequence(lambda n: n + 1)
    code = factory.Sequence(lambda n: f"S{n + 1}")
    nom_ar = "سداسي"
    nom_fr = "Semestre"


class MatiereFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Matiere

    code = factory.Sequence(lambda n: f"MAT_{n}")
    nom_ar = "مادة"
    nom_fr = "Matière"
    niv_spe_dep = factory.SubFactory(NivSpeDepFactory)
    semestre = factory.SubFactory(SemestreFactory)


class EnseignantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enseignant

    user = factory.SubFactory(UserFactory)
    matricule = factory.Sequence(lambda n: f"ENS{n:05d}")
    nom_fr = "Nom"
    prenom_fr = "Prenom"
    nom_ar = "لقب"
    prenom_ar = "اسم"


class EnsDepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ens_Dep

    enseignant = factory.SubFactory(EnseignantFactory)
    departement = factory.SubFactory(DepartementFactory)
    annee_univ = factory.SubFactory(AnneeUniversitaireFactory)
    est_actif = True


class EtudiantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Etudiant

    user = factory.SubFactory(UserFactory)
    matricule = factory.Sequence(lambda n: f"ETU{n:05d}")
    nom_fr = "NomEtu"
    prenom_fr = "PrenomEtu"
    nom_ar = "لقب_طالب"
    prenom_ar = "اسم_طالب"
    niv_spe_dep_sg = factory.SubFactory(NivSpeDepSGFactory)


class ClasseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Classe

    semestre = factory.SubFactory(SemestreFactory)
    matiere = factory.SubFactory(MatiereFactory)
    enseignant = factory.SubFactory(EnsDepFactory)
    niv_spe_dep_sg = factory.SubFactory(NivSpeDepSGFactory)
    jour = Classe.Dayblock.SUNDAY
    temps = Classe.Timeblock.CLASSE01
    type = Classe.Typeblock.COURS


class SousGroupeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SousGroupe

    groupe_principal = factory.SubFactory(NivSpeDepSGFactory)
    nom = factory.Sequence(lambda n: f"G{n}")
    actif = True
