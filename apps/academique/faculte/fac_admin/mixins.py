import contextvars

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from apps.academique.faculte.models import Faculte
from apps.noyau.commun.models import AffectationPoste, AnneeUniversitaire, PostePermission

# Variable de contexte thread-safe pour stocker la requête courante
_admin_request_var = contextvars.ContextVar("admin_request_var_fac", default=None)


class FaculteFilterMixin:
    """Mixin pour filtrer les données par faculté de l'utilisateur."""

    def get_faculte(self, request):
        """
        Récupère la faculté de l'utilisateur.
        Priorité: session > AffectationPoste > première faculté pour superuser.
        """
        faculte_id = request.session.get("selected_faculte_id")
        if faculte_id:
            try:
                return Faculte.objects.get(id=faculte_id)
            except Faculte.DoesNotExist:
                pass

        user = request.user
        if user.is_authenticated:
            # Chercher via affectation
            postes_doyen = ["doyen", "vice_doyen_p", "vice_doyen_pg"]
            aff = AffectationPoste.objects.filter(
                user=user,
                est_actif=True,
                poste__code__in=postes_doyen,
                faculte__isnull=False,
            ).first()
            if aff and aff.faculte:
                request.session["selected_faculte_id"] = aff.faculte.id
                return aff.faculte

            # Superutilisateur sans affectation directe
            if user.is_superuser:
                fac = Faculte.objects.first()
                if fac:
                    request.session["selected_faculte_id"] = fac.id
                    return fac

        return None

    def get_departements_faculte(self, request):
        """Récupère tous les départements de la faculté courante."""
        fac = self.get_faculte(request)
        if fac:
            return fac.departements.all()
        return Faculte.objects.none()

    def get_annee_courante(self):
        """Récupère l'année universitaire courante."""
        return AnneeUniversitaire.get_courante()


class PermissionCheckMixin:
    """
    Mixin de vérification des permissions pour l'administration de la faculté.
    Les superutilisateurs et le doyen ont accès complet à la gestion de la faculté.
    """

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        fac = FaculteFilterMixin().get_faculte(request)
        return fac is not None

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        fac = FaculteFilterMixin().get_faculte(request)
        return fac is not None

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        fac = FaculteFilterMixin().get_faculte(request)
        return fac is not None

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        fac = FaculteFilterMixin().get_faculte(request)
        return fac is not None

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        fac = FaculteFilterMixin().get_faculte(request)
        return fac is not None

    def has_import_permission(self, request):
        return self.has_add_permission(request)

    def has_export_permission(self, request):
        return self.has_view_permission(request)


class PermissionCheckMixinNoImport(PermissionCheckMixin):
    """Mixin pour les modèles sans permission d'import/export."""

    def has_import_permission(self, request):
        return False

    def has_export_permission(self, request):
        return False


class ReadOnlyAdminMixin:
    """Mixin pour rendre un ModelAdmin en lecture seule pour la faculté."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_import_permission(self, request):
        return False

    def has_export_permission(self, request):
        return False


class ImportCredentialsAdminMixin:
    """
    Mixin pour proposer le téléchargement des identifiants générés lors de l'import.
    """

    def changelist_view(self, request, extra_context=None):
        download_url = request.session.pop("import_credentials_download_url", None)
        if download_url:
            msg = format_html(
                "تم إنشاء حسابات للمستخدمين الجدد. "
                '<a href="{}" class="button" style="margin-right: 10px; font-weight: bold; color: #fff; background-color: #28a745; padding: 5px 10px; border-radius: 4px; text-decoration: none;">'
                '<i class="fas fa-file-excel"></i> تحميل بيانات الدخول (Excel)'
                "</a>",
                download_url,
            )
            messages.success(request, msg)
        return super().changelist_view(request, extra_context=extra_context)
