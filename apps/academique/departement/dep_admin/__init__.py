"""Administration du chef de département : site dédié et enregistrement des modèles."""

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
    AbsEtuSeanceDepAdmin,
    AffectationPosteDepAdmin,
    AmphiDepAdmin,
    AmphiReadOnlyAdmin,
    AnneeUniversitaireReadOnlyAdmin,
    ClasseDepAdmin,
    CycleReadOnlyAdmin,
    DepartementReadOnlyAdmin,
    DiplomeReadOnlyAdmin,
    DomaineReadOnlyAdmin,
    EnsDep_DepAdmin,
    EnseignantDepAdmin,
    EtudiantDepAdmin,
    EtudiantSousGroupeDepAdmin,
    FaculteReadOnlyAdmin,
    FiliereReadOnlyAdmin,
    GestionEtuClasseDepAdmin,
    GradeReadOnlyAdmin,
    GroupeReadOnlyAdmin,
    IdentificationReadOnlyAdmin,
    LaboratoireDepAdmin,
    LaboratoireReadOnlyAdmin,
    MatiereAdminForDep,
    NiveauReadOnlyAdmin,
    NivSpeDepAdmin,
    NivSpeDepSGAdmin,
    ParcoursReadOnlyAdmin,
    PaysReadOnlyAdmin,
    PosteReadOnlyAdmin,
    ReformeReadOnlyAdmin,
    SalleDepAdmin,
    SalleReadOnlyAdmin,
    SeanceDepAdmin,
    SectionReadOnlyAdmin,
    SemestreReadOnlyAdmin,
    SessionReadOnlyAdmin,
    SousGroupeDepAdmin,
    SpecialiteDepAdmin,
    UniteReadOnlyAdmin,
    UniversiteReadOnlyAdmin,
    UserDepAdmin,
    WilayaReadOnlyAdmin,
)
from .site import dep_admin_site

# ══════════════════════════════════════════════════════════════
# ENREGISTREMENT DES MODÈLES DANS L'ADMIN PERSONNALISÉ
# ══════════════════════════════════════════════════════════════

# Modèles déjà enregistrés
dep_admin_site.register(Enseignant, EnseignantDepAdmin)
dep_admin_site.register(Etudiant, EtudiantDepAdmin)
dep_admin_site.register(Ens_Dep, EnsDep_DepAdmin)
dep_admin_site.register(CustomUser, UserDepAdmin)

# Modèles CRUD - Infrastructure
dep_admin_site.register(Amphi_Dep, AmphiDepAdmin)
dep_admin_site.register(Salle_Dep, SalleDepAdmin)
dep_admin_site.register(Laboratoire_Dep, LaboratoireDepAdmin)

# Modèles CRUD - Enseignement
dep_admin_site.register(Classe, ClasseDepAdmin)
dep_admin_site.register(Seance, SeanceDepAdmin)
dep_admin_site.register(SousGroupe, SousGroupeDepAdmin)

# Modèles CRUD - Suivi
dep_admin_site.register(Gestion_Etu_Classe, GestionEtuClasseDepAdmin)
dep_admin_site.register(Abs_Etu_Seance, AbsEtuSeanceDepAdmin)
dep_admin_site.register(EtudiantSousGroupe, EtudiantSousGroupeDepAdmin)

# Modèles CRUD - Structure
dep_admin_site.register(NivSpeDep, NivSpeDepAdmin)
dep_admin_site.register(NivSpeDep_SG, NivSpeDepSGAdmin)
dep_admin_site.register(Specialite, SpecialiteDepAdmin)
dep_admin_site.register(Matiere, MatiereAdminForDep)

# Modèles CRUD - Postes
dep_admin_site.register(AffectationPoste, AffectationPosteDepAdmin)

# Modèles Lecture Seule - Hiérarchie
dep_admin_site.register(Departement, DepartementReadOnlyAdmin)
dep_admin_site.register(Faculte, FaculteReadOnlyAdmin)
dep_admin_site.register(Universite, UniversiteReadOnlyAdmin)
dep_admin_site.register(Domaine, DomaineReadOnlyAdmin)
dep_admin_site.register(Filiere, FiliereReadOnlyAdmin)

# Modèles Lecture Seule - Référence
dep_admin_site.register(Cycle, CycleReadOnlyAdmin)
dep_admin_site.register(Niveau, NiveauReadOnlyAdmin)
dep_admin_site.register(Grade, GradeReadOnlyAdmin)
dep_admin_site.register(Diplome, DiplomeReadOnlyAdmin)
dep_admin_site.register(Semestre, SemestreReadOnlyAdmin)
dep_admin_site.register(Session, SessionReadOnlyAdmin)
dep_admin_site.register(Reforme, ReformeReadOnlyAdmin)
dep_admin_site.register(Parcours, ParcoursReadOnlyAdmin)
dep_admin_site.register(Unite, UniteReadOnlyAdmin)
dep_admin_site.register(Groupe, GroupeReadOnlyAdmin)
dep_admin_site.register(Section, SectionReadOnlyAdmin)
dep_admin_site.register(Identification, IdentificationReadOnlyAdmin)
dep_admin_site.register(Poste, PosteReadOnlyAdmin)
dep_admin_site.register(AnneeUniversitaire, AnneeUniversitaireReadOnlyAdmin)
dep_admin_site.register(Wilaya, WilayaReadOnlyAdmin)
dep_admin_site.register(Pays, PaysReadOnlyAdmin)
dep_admin_site.register(Amphi, AmphiReadOnlyAdmin)
dep_admin_site.register(Salle, SalleReadOnlyAdmin)
dep_admin_site.register(Laboratoire, LaboratoireReadOnlyAdmin)

__all__ = ["dep_admin_site"]
