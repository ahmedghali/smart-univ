import contextvars

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.academique.departement.models import Departement
from apps.noyau.commun.models import AffectationPoste, AnneeUniversitaire, PostePermission

# Variable de contexte thread-safe pour stocker la requête courante (A17)
_admin_request_var = contextvars.ContextVar("admin_request_var", default=None)

# ══════════════════════════════════════════════════════════════


class DepartementFilterMixin:
    """Mixin pour filtrer les données par département de l'utilisateur."""

    def get_departement(self, request):
        """
        Récupère le département de l'utilisateur.
        Priorité: session > AffectationPoste
        """
        departement_id = request.session.get("selected_departement_id")
        if departement_id:
            try:
                return Departement.objects.get(id=departement_id)
            except Departement.DoesNotExist:
                pass

        # Fallback: utiliser AffectationPoste
        user = request.user
        if user.is_authenticated:
            departements = AffectationPoste.get_departements_user(user)
            if departements.exists():
                dep = departements.first()
                # Stocker en session pour les prochaines requêtes
                request.session["selected_departement_id"] = dep.id
                return dep

        return None

    def get_departements_user(self, request):
        """Récupère TOUS les départements où l'utilisateur a un poste."""
        user = request.user
        if user.is_authenticated:
            return AffectationPoste.get_departements_user(user)
        return Departement.objects.none()

    def get_annee_courante(self):
        """Récupère l'année universitaire courante."""
        return AnneeUniversitaire.get_courante()


# ══════════════════════════════════════════════════════════════
# MIXIN VÉRIFICATION DES PERMISSIONS
# ══════════════════════════════════════════════════════════════

# Mapping des modèles vers leurs clés de permission
MODEL_PERMISSION_MAP = {
    # Affectations
    "Ens_Dep": "ens_dep",
    "Amphi_Dep": "amphi_dep",
    "Salle_Dep": "salle_dep",
    "Laboratoire_Dep": "labo_dep",
    "Classe": "classe",
    "Seance": "seance",
    "SousGroupe": "sous_groupe",
    "EtudiantSousGroupe": "etu_sous_groupe",
    "Gestion_Etu_Classe": "gestion_etu",
    "Abs_Etu_Seance": "abs_etu",
    # Département
    "Departement": "departement",
    "Specialite": "specialite",
    "NivSpeDep": "niv_spe_dep",
    "NivSpeDep_SG": "niv_spe_dep_sg",
    "Matiere": "matiere",
    # Enseignant/Etudiant
    "Enseignant": "enseignant",
    "Etudiant": "etudiant",
    # Faculté/Université
    "Faculte": "faculte",
    "Filiere": "filiere",
    "Universite": "universite",
    "Domaine": "domaine",
    # Authentification
    "CustomUser": "user",
    # Données communes
    "Poste": "poste",
    "AffectationPoste": "affectation_poste",
    "AnneeUniversitaire": "annee_univ",
    "Cycle": "cycle",
    "Niveau": "niveau",
    "Grade": "grade",
    "Diplome": "diplome",
    "Semestre": "semestre",
    "Session": "session",
    "Reforme": "reforme",
    "Parcours": "parcours",
    "Unite": "unite",
    "Groupe": "groupe",
    "Section": "section",
    "Identification": "identification",
    "Wilaya": "wilaya",
    "Pays": "pays",
    "Amphi": "amphi",
    "Salle": "salle",
    "Laboratoire": "laboratoire",
}


class PermissionCheckMixinNoImport:
    """
    Vérifie les droits PostePermission (voir / ajouter / modifier / supprimer) du poste actif.
    Doit être placé AVANT admin.ModelAdmin dans l'héritage.
    """

    def get_permission_key(self):
        """Clé de permission du modèle (ex. "enseignant", "ens_dep")."""
        model_name = self.model.__name__
        return MODEL_PERMISSION_MAP.get(model_name, model_name.lower())

    def _get_perms(self, request):
        return PostePermission.get_permissions(request)

    def _has(self, request, action):
        return self._get_perms(request).get(f"{self.get_permission_key()}_{action}", False)

    def has_module_permission(self, request):
        return self._has(request, "view")

    def has_view_permission(self, request, obj=None):
        return self._has(request, "view")

    def has_add_permission(self, request, *args, **kwargs):
        return self._has(request, "add")

    def has_change_permission(self, request, obj=None):
        return self._has(request, "change")

    def has_delete_permission(self, request, obj=None):
        return self._has(request, "delete")

    def changelist_view(self, request, extra_context=None):
        # Mémorise la requête dans un contextvar thread-safe (A17)
        _admin_request_var.set(request)
        return super().changelist_view(request, extra_context)

    @admin.display(description="الإجراءات / Actions")
    def action_buttons(self, obj):
        """Boutons modifier / supprimer (supprimer seulement si le poste en a le droit)."""
        request = _admin_request_var.get()
        match = getattr(request, "resolver_match", None)
        namespace = match.namespace if match and match.namespace else self.admin_site.name
        info = (namespace, obj._meta.app_label, obj._meta.model_name)
        style = "color: white; padding: 3px 6px; text-decoration: none; border-radius: 3px; font-size: 11px;"
        html = format_html(
            '<a href="{}" title="تعديل / Modifier" style="background-color: #417690; {}">✏️</a>',
            reverse("{}:{}_{}_change".format(*info), args=[obj.pk]),
            style,
        )
        if request is not None and self.has_delete_permission(request, obj):
            html += format_html(
                ' <a href="{}" title="حذف / Supprimer" style="background-color: #8b0000; {}">🗑️</a>',
                reverse("{}:{}_{}_delete".format(*info), args=[obj.pk]),
                style,
            )
        return html


class PermissionCheckMixin(PermissionCheckMixinNoImport):
    """Comme PermissionCheckMixinNoImport, plus les droits d'import (= ajout) et d'export (= lecture)."""

    def has_import_permission(self, request):
        return self._has(request, "add")

    def has_export_permission(self, request):
        return self._has(request, "view")


class ReadOnlyAdminMixin(PermissionCheckMixinNoImport):
    """Modèles de référence : mêmes contrôles de droits, sans import/export."""
