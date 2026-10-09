"""Administration du doyen / faculté : site dédié et enregistrement des modèles."""

from apps.academique.affectation.models import (
    Abs_Etu_Seance,
    Amphi_Dep,
    Classe,
    Ens_Dep,
    EtudiantSousGroupe,
    Gestion_Etu_Classe,
    Laboratoire_Dep,
    Salle_Dep,
    Seance,
    SousGroupe,
)
from apps.academique.departement.models import Departement, Matiere, NivSpeDep, NivSpeDep_SG, Specialite
from apps.academique.enseignant.models import Enseignant
from apps.academique.etudiant.models import Etudiant
from apps.academique.faculte.models import Faculte, Filiere
from apps.academique.universite.models import Domaine, Universite
from apps.noyau.authentification.models import CustomUser
from apps.noyau.commun.models import (
    AffectationPoste,
    Amphi,
    AnneeUniversitaire,
    Cycle,
    Diplome,
    Grade,
    Groupe,
    Identification,
    Laboratoire,
    Niveau,
    Parcours,
    Pays,
    Poste,
    Reforme,
    Salle,
    Section,
    Semestre,
    Session,
    Unite,
    Wilaya,
)

from .admins import (
    AbsEtuSeanceFacAdmin,
    AffectationPosteFacAdmin,
    AmphiDepFacAdmin,
    AmphiReadOnlyAdmin,
    AnneeUniversitaireReadOnlyAdmin,
    ClasseFacAdmin,
    CycleReadOnlyAdmin,
    DepartementFacAdmin,
    DiplomeReadOnlyAdmin,
    DomaineReadOnlyAdmin,
    EnsDepFacAdmin,
    EnseignantFacAdmin,
    EtudiantFacAdmin,
    EtudiantSousGroupeFacAdmin,
    FaculteAdminForFac,
    FiliereFacAdmin,
    GestionEtuClasseFacAdmin,
    GradeReadOnlyAdmin,
    GroupeReadOnlyAdmin,
    IdentificationReadOnlyAdmin,
    LaboratoireDepFacAdmin,
    LaboratoireReadOnlyAdmin,
    MatiereFacAdmin,
    NiveauReadOnlyAdmin,
    NivSpeDepFacAdmin,
    NivSpeDepSGFacAdmin,
    ParcoursReadOnlyAdmin,
    PaysReadOnlyAdmin,
    PosteReadOnlyAdmin,
    ReformeReadOnlyAdmin,
    SalleDepFacAdmin,
    SalleReadOnlyAdmin,
    SeanceFacAdmin,
    SectionReadOnlyAdmin,
    SemestreReadOnlyAdmin,
    SessionReadOnlyAdmin,
    SousGroupeFacAdmin,
    SpecialiteFacAdmin,
    UniteReadOnlyAdmin,
    UniversiteReadOnlyAdmin,
    UserFacAdmin,
    WilayaReadOnlyAdmin,
)
from .site import fac_admin_site

# ══════════════════════════════════════════════════════════════
# ENREGISTREMENT DES MODÈLES DANS L'ADMIN FACULTÉ
# ══════════════════════════════════════════════════════════════

# 1. Fiche Faculté & Départements
fac_admin_site.register(Faculte, FaculteAdminForFac)
fac_admin_site.register(Departement, DepartementFacAdmin)

# 2. Utilisateurs, Enseignants et Étudiants
fac_admin_site.register(Enseignant, EnseignantFacAdmin)
fac_admin_site.register(Etudiant, EtudiantFacAdmin)
fac_admin_site.register(Ens_Dep, EnsDepFacAdmin)
fac_admin_site.register(CustomUser, UserFacAdmin)

# 3. Structure Académique
fac_admin_site.register(Specialite, SpecialiteFacAdmin)
fac_admin_site.register(Matiere, MatiereFacAdmin)
fac_admin_site.register(Filiere, FiliereFacAdmin)
fac_admin_site.register(NivSpeDep, NivSpeDepFacAdmin)
fac_admin_site.register(NivSpeDep_SG, NivSpeDepSGFacAdmin)

# 4. Infrastructures affectées
fac_admin_site.register(Amphi_Dep, AmphiDepFacAdmin)
fac_admin_site.register(Salle_Dep, SalleDepFacAdmin)
fac_admin_site.register(Laboratoire_Dep, LaboratoireDepAdmin) if False else fac_admin_site.register(Laboratoire_Dep, LaboratoireDepFacAdmin)

# 5. Enseignement & Suivi
fac_admin_site.register(Classe, ClasseFacAdmin)
fac_admin_site.register(Seance, SeanceFacAdmin)
fac_admin_site.register(SousGroupe, SousGroupeFacAdmin)
fac_admin_site.register(Gestion_Etu_Classe, GestionEtuClasseFacAdmin)
fac_admin_site.register(Abs_Etu_Seance, AbsEtuSeanceFacAdmin)
fac_admin_site.register(EtudiantSousGroupe, EtudiantSousGroupeFacAdmin)

# 6. Postes et Affectations
fac_admin_site.register(AffectationPoste, AffectationPosteFacAdmin)

# 7. Tables de référence en lecture seule
fac_admin_site.register(Universite, UniversiteReadOnlyAdmin)
fac_admin_site.register(Domaine, DomaineReadOnlyAdmin)
fac_admin_site.register(Cycle, CycleReadOnlyAdmin)
fac_admin_site.register(Niveau, NiveauReadOnlyAdmin)
fac_admin_site.register(Grade, GradeReadOnlyAdmin)
fac_admin_site.register(Diplome, DiplomeReadOnlyAdmin)
fac_admin_site.register(Semestre, SemestreReadOnlyAdmin)
fac_admin_site.register(Session, SessionReadOnlyAdmin)
fac_admin_site.register(Reforme, ReformeReadOnlyAdmin)
fac_admin_site.register(Parcours, ParcoursReadOnlyAdmin)
fac_admin_site.register(Unite, UniteReadOnlyAdmin)
fac_admin_site.register(Groupe, GroupeReadOnlyAdmin)
fac_admin_site.register(Section, SectionReadOnlyAdmin)
fac_admin_site.register(Identification, IdentificationReadOnlyAdmin)
fac_admin_site.register(Poste, PosteReadOnlyAdmin)
fac_admin_site.register(AnneeUniversitaire, AnneeUniversitaireReadOnlyAdmin)
fac_admin_site.register(Wilaya, WilayaReadOnlyAdmin)
fac_admin_site.register(Pays, PaysReadOnlyAdmin)
fac_admin_site.register(Amphi, AmphiReadOnlyAdmin)
fac_admin_site.register(Salle, SalleReadOnlyAdmin)
fac_admin_site.register(Laboratoire, LaboratoireReadOnlyAdmin)

__all__ = ["fac_admin_site"]
