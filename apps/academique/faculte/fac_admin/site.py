"""Site d'administration réservé au doyen / équipe de direction de la faculté."""

from functools import update_wrapper

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.shortcuts import redirect

from apps.noyau.commun.models import AffectationPoste, AnneeUniversitaire, PostePermission

from .mixins import FaculteFilterMixin


class FacAdminSite(AdminSite):
    """
    Site d'administration personnalisé pour la faculté (Doyen & Vice-Doyens).
    Accès limité aux utilisateurs ayant les droits de direction au niveau faculté ou superutilisateurs.
    """

    site_header = "إدارة الكلية / Administration Faculté"
    site_title = "لوحة إدارة الكلية"
    index_title = "إدارة الكلية والأقسام والأساتذة والطلبة"
    login_template = None

    def has_permission(self, request):
        """
        Vérifie si l'utilisateur a accès à l'administration de la faculté.
        """
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user = request.user
        faculte_id = request.session.get("selected_faculte_id")

        # Vérifier si l'utilisateur occupe un poste de direction de la faculté
        annee = AnneeUniversitaire.get_courante()
        postes_doyen = ["doyen", "vice_doyen_p", "vice_doyen_pg"]

        affectations = AffectationPoste.objects.filter(
            user=user,
            est_actif=True,
            poste__code__in=postes_doyen,
        )
        if faculte_id:
            affectations = affectations.filter(faculte_id=faculte_id)
        if annee:
            affectations = affectations.filter(annee_univ=annee)

        if affectations.exists():
            aff = affectations.first()
            request.session["current_role_code"] = aff.poste.code
            request.session["current_affectation_id"] = aff.id
            if aff.faculte_id:
                request.session["selected_faculte_id"] = aff.faculte_id
            return True

        # Vérification via PostePermission
        perms = PostePermission.get_permissions(request)
        if any(perms.get(k, False) for k in perms.keys() if k.endswith("_view")):
            return True

        return False

    def get_app_list(self, request, app_label=None):
        """
        Corrige les URLs pour utiliser /faculte/admin/ au lieu de /admin/
        """
        app_list = super().get_app_list(request, app_label)

        for app in app_list:
            for model in app.get("models", []):
                if "admin_url" in model and model["admin_url"]:
                    if model["admin_url"].startswith("/admin/"):
                        model["admin_url"] = model["admin_url"].replace("/admin/", "/faculte/admin/", 1)
                if "add_url" in model and model["add_url"]:
                    if model["add_url"].startswith("/admin/"):
                        model["add_url"] = model["add_url"].replace("/admin/", "/faculte/admin/", 1)

        return app_list

    def each_context(self, request):
        """Ajoute le contexte personnalisé pour les templates admin."""
        context = super().each_context(request)
        context["site_url"] = "/faculte/admin/"
        context["admin_url_prefix"] = "/faculte/admin/"
        context["faculte"] = getattr(request, "faculte", None)
        return context

    def admin_view(self, view, cacheable=False):
        """Injecte request.faculte et request.annee_courante dans chaque vue admin."""

        def with_faculte(request, *args, **kwargs):
            request.faculte = FaculteFilterMixin().get_faculte(request)
            request.annee_courante = AnneeUniversitaire.get_courante()
            return view(request, *args, **kwargs)

        return super().admin_view(update_wrapper(with_faculte, view), cacheable)

    def login(self, request, extra_context=None):
        """Redirige vers l'accueil ou login principal si non connecté."""
        if request.user.is_authenticated:
            if self.has_permission(request):
                return redirect("/faculte/admin/")
            else:
                messages.error(request, "ليس لديك صلاحية الدخول إلى إدارة الكلية.")
                return redirect("facu:dashboard_Fac")
        return redirect("auth:login")


# Instance de l'admin faculté
fac_admin_site = FacAdminSite(name="fac_admin")
