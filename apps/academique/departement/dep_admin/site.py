"""Site d'administration réservé au chef de département (et aux postes qui ont des droits)."""

from functools import update_wrapper

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path

from apps.academique.departement.models import NivSpeDep_SG
from apps.noyau.commun.models import AffectationPoste, AnneeUniversitaire, PostePermission

from .mixins import DepartementFilterMixin


class DepAdminSite(AdminSite):
    """
    Site d'administration personnalisé pour le département.
    Accès limité aux utilisateurs ayant la permission can_manage_users.
    """

    site_header = "إدارة القسم / Administration Département"
    site_title = "لوحة إدارة القسم"
    index_title = "إدارة الأساتذة والطلبة والمستخدمين"
    login_template = None  # Utilise le template par défaut

    def has_permission(self, request):
        """
        Vérifie si l'utilisateur a accès à cette interface admin.
        L'utilisateur doit avoir au moins une permission _view sur n'importe quel modèle.
        """
        if not request.user.is_authenticated:
            return False

        user = request.user
        departement_id = request.session.get("selected_departement_id")

        if not departement_id:
            return False

        # Vérifier via PostePermission si l'utilisateur a au moins une permission
        perms = PostePermission.get_permissions(request)

        # Vérifier si au moins une permission _view est True
        has_any_view_permission = any(perms.get(key, False) for key in perms.keys() if key.endswith("_view"))

        if has_any_view_permission:
            return True

        # Fallback: vérifier via AffectationPoste
        if user.is_authenticated:
            annee = AnneeUniversitaire.get_courante()
            affectations = AffectationPoste.objects.filter(
                user=user, niveau_contexte="departement", departement_id=departement_id, est_actif=True
            ).select_related("poste__permissions")

            if annee:
                affectations = affectations.filter(annee_univ=annee)

            for aff in affectations:
                if hasattr(aff.poste, "permissions"):
                    # Vérifier si au moins une permission _view est True
                    perm_obj = aff.poste.permissions
                    perm_dict = perm_obj.to_dict()
                    has_view = any(perm_dict.get(key, False) for key in perm_dict.keys() if key.endswith("_view"))
                    if has_view:
                        request.session["current_role_code"] = aff.poste.code
                        request.session["current_affectation_id"] = aff.id
                        return True

        return False

    def get_app_list(self, request, app_label=None):
        """
        Personnalise la liste des applications affichées.
        Corrige les URLs pour utiliser /departement/admin/ au lieu de /admin/
        """
        app_list = super().get_app_list(request, app_label)

        # Corriger les URLs pour pointer vers l'admin département
        for app in app_list:
            for model in app.get("models", []):
                # Remplacer /admin/ par /departement/admin/
                if "admin_url" in model and model["admin_url"]:
                    if model["admin_url"].startswith("/admin/"):
                        model["admin_url"] = model["admin_url"].replace("/admin/", "/departement/admin/", 1)
                if "add_url" in model and model["add_url"]:
                    if model["add_url"].startswith("/admin/"):
                        model["add_url"] = model["add_url"].replace("/admin/", "/departement/admin/", 1)

        return app_list

    def each_context(self, request):
        """
        Ajoute le contexte personnalisé pour les templates.
        Fixe le préfixe URL pour les templates admin.
        """
        context = super().each_context(request)
        context["site_url"] = "/departement/admin/"
        context["admin_url_prefix"] = "/departement/admin/"
        return context

    def admin_view(self, view, cacheable=False):
        """Toutes les vues de ce site reçoivent request.departement et request.annee_courante."""

        def with_departement(request, *args, **kwargs):
            request.departement = DepartementFilterMixin().get_departement(request)
            request.annee_courante = AnneeUniversitaire.get_courante()
            return view(request, *args, **kwargs)

        return super().admin_view(update_wrapper(with_departement, view), cacheable)

    def get_urls(self):
        urls = [
            path(
                "ajax/niv-spe-dep-sg/<int:niv_spe_dep_id>/",
                self.admin_view(self.niv_spe_dep_sg_options),
                name="ajax_niv_spe_dep_sg",
            ),
        ]
        return urls + super().get_urls()

    def niv_spe_dep_sg_options(self, request, niv_spe_dep_id):
        """Groupes (NivSpeDep_SG) d'un niveau-spécialité du département courant, pour les listes liées."""
        groupes = NivSpeDep_SG.objects.filter(
            niv_spe_dep_id=niv_spe_dep_id,
            niv_spe_dep__departement_id=request.session.get("selected_departement_id"),
        )
        return JsonResponse({"success": True, "options": [{"id": g.id, "text": str(g)} for g in groupes]})

    def login(self, request, extra_context=None):
        """Redirige vers la page de login principale si non connecté."""
        if request.user.is_authenticated:
            if self.has_permission(request):
                return redirect("/departement/admin/")
            else:
                # L'utilisateur est connecté mais n'a pas les permissions
                messages.error(request, "ليس لديك صلاحية الدخول إلى هذه الصفحة.")
                return redirect("depa:dashboard_Dep")
        # Rediriger vers la page de login principale
        return redirect("auth:login")


# Créer l'instance du site admin personnalisé
dep_admin_site = DepAdminSite(name="dep_admin")
