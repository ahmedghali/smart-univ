"""Resources pour import/export Excel des données au niveau de la faculté."""

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from apps.academique.affectation.models import Ens_Dep
from apps.academique.departement.models import Departement, Matiere, NivSpeDep_SG, Specialite
from apps.academique.departement.dep_admin.resources import (
    EnseignantResource as DepEnseignantResource,
    EtudiantResource as DepEtudiantResource,
    MatiereResource as DepMatiereResource,
    SpecialiteResource as DepSpecialiteResource,
    EnsDepResource as DepEnsDepResource,
)
from apps.academique.faculte.models import Faculte, Filiere


class EnseignantFacResource(DepEnseignantResource):
    """Import/export des enseignants au niveau faculté."""
    pass


class EtudiantFacResource(DepEtudiantResource):
    """Import/export des étudiants au niveau faculté."""
    pass


class MatiereFacResource(DepMatiereResource):
    """Import/export des matières au niveau faculté."""
    pass


class SpecialiteFacResource(DepSpecialiteResource):
    """Import/export des spécialités au niveau faculté."""
    pass


class EnsDepFacResource(DepEnsDepResource):
    """Import/export des affectations enseignants au niveau faculté."""
    pass


class DepartementFacResource(resources.ModelResource):
    """Export/Import des départements de la faculté."""

    class Meta:
        model = Departement
        fields = ("id", "code", "nom_ar", "nom_fr", "faculte__nom_ar", "created_at", "updated_at")
        export_order = ("id", "code", "nom_ar", "nom_fr", "faculte__nom_ar", "created_at", "updated_at")


class FiliereFacResource(resources.ModelResource):
    """Export/Import des filières de la faculté."""

    class Meta:
        model = Filiere
        fields = ("id", "code", "nom_ar", "nom_fr", "domaine__nom_ar", "created_at", "updated_at")
        export_order = ("id", "code", "nom_ar", "nom_fr", "domaine__nom_ar", "created_at", "updated_at")
