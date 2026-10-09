# apps/academique/faculte/fac_admin/admins.py
"""
Classes d'administration pour la faculté (Doyen & Vice-Doyens).
"""

from django.contrib import admin, messages
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportMixin

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

from .forms import EtudiantFacConfirmImportForm, EtudiantFacImportForm
from .mixins import (
    FaculteFilterMixin,
    ImportCredentialsAdminMixin,
    PermissionCheckMixin,
    PermissionCheckMixinNoImport,
    ReadOnlyAdminMixin,
)
from .resources import (
    DepartementFacResource,
    EnsDepFacResource,
    EnseignantFacResource,
    EtudiantFacResource,
    FiliereFacResource,
    MatiereFacResource,
    SpecialiteFacResource,
)


# ══════════════════════════════════════════════════════════════
# 1. FACULTÉ & DÉPARTEMENTS
# ══════════════════════════════════════════════════════════════

class FaculteAdminForFac(PermissionCheckMixinNoImport, FaculteFilterMixin, admin.ModelAdmin):
    """Administration de la fiche faculté par le doyen."""

    list_display = ("code", "nom_ar", "nom_fr", "sigle", "get_doyen", "siteweb", "email")
    search_fields = ("code", "nom_ar", "nom_fr", "sigle")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(pk=fac.pk)
        return qs

    def get_doyen(self, obj):
        doyen_aff = obj.affectations_postes.filter(poste__code="doyen", est_actif=True).first()
        return doyen_aff.user.get_full_name() if doyen_aff else "-"

    get_doyen.short_description = "العميد / Doyen"


class DepartementFacAdmin(PermissionCheckMixin, FaculteFilterMixin, ImportExportMixin, admin.ModelAdmin):
    """Gestion des départements rattachés à la faculté."""

    resource_class = DepartementFacResource
    list_display = ("code", "nom_ar", "nom_fr", "get_chef", "get_nb_enseignants", "get_nb_etudiants", "get_nb_specialites")
    search_fields = ("code", "nom_ar", "nom_fr")
    ordering = ("nom_ar",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(faculte=fac)
        return qs

    def get_chef(self, obj):
        chef_aff = obj.affectations_postes.filter(poste__code="chef_departement", est_actif=True).first()
        return chef_aff.user.get_full_name() if chef_aff else "-"

    get_chef.short_description = "رئيس القسم / Chef de Département"

    def get_nb_enseignants(self, obj):
        return obj.enseignants_affectes.filter(est_actif=True).values("enseignant").distinct().count()

    get_nb_enseignants.short_description = "الأساتذة / Enseignants"

    def get_nb_etudiants(self, obj):
        return Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep__departement=obj).count()

    get_nb_etudiants.short_description = "الطلبة / Étudiants"

    def get_nb_specialites(self, obj):
        return obj.specialites.count()

    get_nb_specialites.short_description = "التخصصات / Spécialités"


# ══════════════════════════════════════════════════════════════
# 2. ENSEIGNANTS DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

class EnseignantFacAdmin(
    PermissionCheckMixin,
    FaculteFilterMixin,
    ImportCredentialsAdminMixin,
    ImportExportMixin,
    admin.ModelAdmin,
):
    """Administration des enseignants de tous les départements de la faculté."""

    resource_class = EnseignantFacResource
    import_template_name = "admin/fac_admin/import.html"
    list_display = (
        "nom_fr",
        "prenom_fr",
        "nom_ar",
        "prenom_ar",
        "get_grade_code",
        "get_departements",
        "get_statut_ens",
        "get_last_login",
    )
    list_filter = ("grade", "diplome", "sex", "est_inscrit")
    search_fields = ("matricule", "nom_ar", "prenom_ar", "nom_fr", "prenom_fr", "email_prof", "user__username")
    ordering = ("nom_fr", "prenom_fr")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(enseignant_departements__departement__faculte=fac).distinct()
        return qs

    def get_grade_code(self, obj):
        return obj.grade.code if obj.grade else "-"

    get_grade_code.short_description = "الرتبة / Grade"

    def get_departements(self, obj):
        deps = obj.enseignant_departements.filter(est_actif=True).select_related("departement")
        names = [d.departement.nom_ar for d in deps]
        return ", ".join(names) if names else "-"

    get_departements.short_description = "الأقسام / Départements"

    def get_statut_ens(self, obj):
        affectations = obj.enseignant_departements.filter(est_actif=True)
        if affectations.exists():
            aff = affectations.first()
            statut = "مرسم" if aff.statut == "permanent" else "مؤقت/مشارك"
            color = "success" if aff.statut == "permanent" else "warning"
            return format_html('<span class="badge bg-{} text-white">{}</span>', color, statut)
        return "-"

    get_statut_ens.short_description = "الصفة / Statut"

    def get_last_login(self, obj):
        if obj.user and obj.user.last_login:
            return obj.user.last_login.strftime("%Y-%m-%d %H:%M")
        return "-"

    get_last_login.short_description = "آخر دخول / Dernier accès"


class EnsDepFacAdmin(PermissionCheckMixin, FaculteFilterMixin, ImportExportMixin, admin.ModelAdmin):
    """Affectations des enseignants aux départements de la faculté."""

    resource_class = EnsDepFacResource
    list_display = ("enseignant", "departement", "annee_univ", "statut", "est_actif")
    list_filter = ("departement", "statut", "est_actif", "annee_univ")
    search_fields = ("enseignant__nom_fr", "enseignant__prenom_fr", "enseignant__nom_ar", "enseignant__prenom_ar")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(departement__faculte=fac)
        return qs


# ══════════════════════════════════════════════════════════════
# 3. ÉTUDIANTS DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

class EtudiantFacAdmin(
    PermissionCheckMixin,
    FaculteFilterMixin,
    ImportCredentialsAdminMixin,
    ImportExportMixin,
    admin.ModelAdmin,
):
    """Administration des étudiants de la faculté avec Import/Export."""

    resource_class = EtudiantFacResource
    import_template_name = "admin/fac_admin/import.html"
    import_form_class = EtudiantFacImportForm
    confirm_form_class = EtudiantFacConfirmImportForm

    list_display = (
        "matricule",
        "nom_fr",
        "prenom_fr",
        "nom_ar",
        "prenom_ar",
        "get_departement",
        "get_specialite",
        "get_groupe",
        "est_inscrit",
    )
    list_filter = ("sexe", "sit_fam", "est_inscrit", "delegue")
    search_fields = ("matricule", "nom_ar", "prenom_ar", "nom_fr", "prenom_fr", "user__username")
    ordering = ("nom_fr", "prenom_fr")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(niv_spe_dep_sg__niv_spe_dep__departement__faculte=fac).distinct()
        return qs

    def get_import_form_kwargs(self, request):
        kwargs = super().get_import_form_kwargs(request)
        fac = self.get_faculte(request)
        if fac:
            kwargs["faculte_id"] = fac.id
        return kwargs

    def get_confirm_form_kwargs(self, request):
        kwargs = super().get_confirm_form_kwargs(request)
        fac = self.get_faculte(request)
        if fac:
            kwargs["faculte_id"] = fac.id
        return kwargs

    def get_departement(self, obj):
        if obj.niv_spe_dep_sg and obj.niv_spe_dep_sg.niv_spe_dep:
            return obj.niv_spe_dep_sg.niv_spe_dep.departement.nom_ar
        return "-"

    get_departement.short_description = "القسم / Département"

    def get_specialite(self, obj):
        if obj.niv_spe_dep_sg and obj.niv_spe_dep_sg.niv_spe_dep:
            return obj.niv_spe_dep_sg.niv_spe_dep.specialite.nom_ar
        return "-"

    get_specialite.short_description = "التخصص / Spécialité"

    def get_groupe(self, obj):
        if obj.niv_spe_dep_sg:
            return str(obj.niv_spe_dep_sg)
        return "-"

    get_groupe.short_description = "الفوج / Groupe"


# ══════════════════════════════════════════════════════════════
# 4. STRUCTURE ACADÉMIQUE : SPÉCIALITÉS, MATIÈRES, FILIÈRES
# ══════════════════════════════════════════════════════════════

class SpecialiteFacAdmin(PermissionCheckMixin, FaculteFilterMixin, ImportExportMixin, admin.ModelAdmin):
    """Spécialités de la faculté."""

    resource_class = SpecialiteFacResource
    list_display = ("code", "nom_ar", "nom_fr", "departement", "reforme", "parcours")
    list_filter = ("departement", "reforme", "parcours")
    search_fields = ("code", "nom_ar", "nom_fr")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(departement__faculte=fac)
        return qs


class MatiereFacAdmin(PermissionCheckMixin, FaculteFilterMixin, ImportExportMixin, admin.ModelAdmin):
    """Matières de la faculté."""

    resource_class = MatiereFacResource
    list_display = ("code", "nom_ar", "nom_fr", "coeff", "credit", "semestre")
    list_filter = ("semestre", "unite")
    search_fields = ("code", "nom_ar", "nom_fr")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(niv_spe_dep__departement__faculte=fac).distinct()
        return qs


class FiliereFacAdmin(PermissionCheckMixin, ImportExportMixin, admin.ModelAdmin):
    """Filières."""

    resource_class = FiliereFacResource
    list_display = ("code", "nom_ar", "nom_fr", "domaine")
    list_filter = ("domaine",)
    search_fields = ("code", "nom_ar", "nom_fr")


class NivSpeDepFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    """Niveaux-Spécialités des départements de la faculté."""

    list_display = ("departement", "niveau", "specialite")
    list_filter = ("departement", "niveau")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(departement__faculte=fac)
        return qs


class NivSpeDepSGFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    """Groupes (Sections/Groupes) des départements de la faculté."""

    list_display = ("niv_spe_dep", "section", "groupe")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(niv_spe_dep__departement__faculte=fac)
        return qs


# ══════════════════════════════════════════════════════════════
# 5. INFRASTRUCTURES DANS LA FACULTÉ (AMPHIS, SALLES, LABOS)
# ══════════════════════════════════════════════════════════════

class AmphiDepFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_amphi_nom", "departement", "semestre_1", "semestre_2", "est_actif")
    list_filter = ("departement", "semestre_1", "semestre_2", "est_actif")

    def get_amphi_nom(self, obj):
        return f"{obj.amphi.numero} - {obj.amphi.nom_ar or obj.amphi.nom_fr or ''}"

    get_amphi_nom.short_description = "المدرج / Amphithéâtre"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(departement__faculte=fac)
        return qs


class SalleDepFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_salle_nom", "departement", "semestre_1", "semestre_2", "est_actif")
    list_filter = ("departement", "semestre_1", "semestre_2", "est_actif")

    def get_salle_nom(self, obj):
        return f"{obj.salle.numero} - {obj.salle.nom_ar or obj.salle.nom_fr or ''}"

    get_salle_nom.short_description = "القاعة / Salle"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(departement__faculte=fac)
        return qs


class LaboratoireDepFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_labo_nom", "departement", "semestre_1", "semestre_2", "est_actif")
    list_filter = ("departement", "semestre_1", "semestre_2", "est_actif")

    def get_labo_nom(self, obj):
        return f"{obj.laboratoire.numero} - {obj.laboratoire.nom_ar or obj.laboratoire.nom_fr or ''}"

    get_labo_nom.short_description = "المخبر / Laboratoire"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(departement__faculte=fac)
        return qs


# ══════════════════════════════════════════════════════════════
# 6. ENSEIGNEMENT & SUIVI (CLASSES, SÉANCES, SOUS-GROUPES)
# ══════════════════════════════════════════════════════════════

class ClasseFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_matiere", "get_enseignant", "get_groupe", "jour", "temps", "type", "taux_avancement")
    list_filter = ("semestre", "type", "jour")

    def get_matiere(self, obj):
        return obj.matiere.nom_ar if obj.matiere else "-"

    get_matiere.short_description = "المادة / Matière"

    def get_enseignant(self, obj):
        if obj.enseignant and obj.enseignant.enseignant:
            return obj.enseignant.enseignant.get_nom_complet("ar")
        return "-"

    get_enseignant.short_description = "الأستاذ / Enseignant"

    def get_groupe(self, obj):
        return str(obj.niv_spe_dep_sg) if obj.niv_spe_dep_sg else "-"

    get_groupe.short_description = "الفوج / Groupe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(matiere__niv_spe_dep__departement__faculte=fac)
        return qs


class SeanceFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_classe", "intitule", "date", "temps", "fait")
    list_filter = ("fait", "annuler", "remplacer")

    def get_classe(self, obj):
        return str(obj.classe) if obj.classe else "-"

    get_classe.short_description = "الحصة / Classe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(classe__matiere__niv_spe_dep__departement__faculte=fac)
        return qs


class SousGroupeFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("nom", "nom_complet", "get_groupe_principal", "effectif", "actif")
    list_filter = ("actif",)

    def get_groupe_principal(self, obj):
        return str(obj.groupe_principal) if obj.groupe_principal else "-"

    get_groupe_principal.short_description = "الفوج الرئيسي / Groupe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(groupe_principal__niv_spe_dep__departement__faculte=fac)
        return qs


class GestionEtuClasseFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_etudiant", "get_classe", "nbr_absence", "note_finale", "validee_par_enseignant")
    list_filter = ("validee_par_enseignant",)

    def get_etudiant(self, obj):
        return f"{obj.etudiant.matricule} - {obj.etudiant.nom_ar}" if obj.etudiant else "-"

    get_etudiant.short_description = "الطالب / Étudiant"

    def get_classe(self, obj):
        return str(obj.classe) if obj.classe else "-"

    get_classe.short_description = "الحصة / Classe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(classe__matiere__niv_spe_dep__departement__faculte=fac)
        return qs


class AbsEtuSeanceFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("get_etudiant", "get_seance", "present", "justifiee", "participation")
    list_filter = ("present", "justifiee", "participation")

    def get_etudiant(self, obj):
        return f"{obj.etudiant.matricule} - {obj.etudiant.nom_ar}" if obj.etudiant else "-"

    get_etudiant.short_description = "الطالب / Étudiant"

    def get_seance(self, obj):
        return f"{obj.seance.date} - {obj.seance.intitule or ''}" if obj.seance else "-"

    get_seance.short_description = "الحصة / Séance"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(seance__classe__matiere__niv_spe_dep__departement__faculte=fac)
        return qs


class EtudiantSousGroupeFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    list_display = ("etudiant", "sous_groupe")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(sous_groupe__groupe_principal__niv_spe_dep__departement__faculte=fac)
        return qs


# ══════════════════════════════════════════════════════════════
# 7. AFFECTATIONS DE POSTES & UTILISATEURS
# ══════════════════════════════════════════════════════════════

class AffectationPosteFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    """Affectations de postes de direction et encadrement dans la faculté et ses départements."""

    list_display = ("user", "poste", "niveau_contexte", "get_lieu", "annee_univ", "est_actif")
    list_filter = ("niveau_contexte", "poste", "est_actif", "annee_univ")
    search_fields = ("user__username", "user__last_name", "user__first_name", "poste__nom_ar")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(Q(faculte=fac) | Q(departement__faculte=fac))
        return qs

    def get_lieu(self, obj):
        return obj.get_contexte() or "-"

    get_lieu.short_description = "المكان / Lieu"


class UserFacAdmin(PermissionCheckMixin, FaculteFilterMixin, admin.ModelAdmin):
    """Gestion des comptes utilisateurs rattachés à la faculté avec gestion sécurisée des mots de passe."""

    list_display = (
        "username",
        "get_nom_complet",
        "get_type_utilisateur",
        "is_active",
        "last_login",
        "get_reset_password_button",
    )
    search_fields = ("username", "first_name", "last_name", "email")
    list_filter = ("is_active",)
    readonly_fields = ("last_login", "date_joined", "get_password_change_link")

    fieldsets = (
        (
            "معلومات الحساب / Informations du compte",
            {
                "fields": (
                    "username",
                    "is_active",
                )
            },
        ),
        (
            "كلمة المرور / Mot de passe",
            {
                "fields": ("get_password_change_link",),
                "description": "Cliquez sur le bouton pour réinitialiser ou définir le mot de passe",
            },
        ),
        (
            "المعلومات الشخصية / Informations personnelles",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        ("المجموعات / Groupes", {"fields": ("groups",)}),
        (
            "التدقيق / Audit",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        fac = self.get_faculte(request)
        if fac:
            return qs.filter(
                Q(enseignant_profile__enseignant_departements__departement__faculte=fac)
                | Q(etudiant_profile__niv_spe_dep_sg__niv_spe_dep__departement__faculte=fac)
                | Q(affectations_postes__faculte=fac)
                | Q(affectations_postes__departement__faculte=fac)
            ).distinct()
        return qs

    def get_nom_complet(self, obj):
        return obj.nom_complet

    get_nom_complet.short_description = "الاسم الكامل / Nom"

    def get_type_utilisateur(self, obj):
        if hasattr(obj, "enseignant_profile") and obj.enseignant_profile:
            return mark_safe('<span style="color: #2196F3;">أستاذ</span>')
        elif hasattr(obj, "etudiant_profile") and obj.etudiant_profile:
            return mark_safe('<span style="color: #4CAF50;">طالب</span>')
        return mark_safe('<span style="color: #9E9E9E;">-</span>')

    get_type_utilisateur.short_description = "النوع / Type"

    def get_reset_password_button(self, obj):
        url = f"/faculte/admin/authentification/customuser/{obj.pk}/reset-password/"
        return format_html(
            '<a class="button" href="{}" style="background: #417690; color: white; '
            'padding: 3px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;">'
            "إعادة تعيين</a>",
            url,
        )

    get_reset_password_button.short_description = "كلمة المرور"

    def get_password_change_link(self, obj):
        if obj and obj.pk:
            reset_url = f"/faculte/admin/authentification/customuser/{obj.pk}/reset-password/"
            set_password_url = f"/faculte/admin/authentification/customuser/{obj.pk}/set-password/"
            return format_html(
                '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
                '<a href="{}" style="background: linear-gradient(135deg, #f59e0b, #d97706); '
                "color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; "
                'font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">'
                "🔄 إعادة تعيين تلقائي / Réinitialiser auto</a>"
                '<a href="{}" style="background: linear-gradient(135deg, #3b82f6, #2563eb); '
                "color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; "
                'font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">'
                "🔑 تعيين كلمة مرور جديدة / Définir nouveau</a>"
                "</div>"
                '<div style="margin-top: 8px; font-size: 11px; color: #6b7280;">'
                "• كلمة المرور مشفرة بأمان بتقنية PBKDF2.<br>"
                "• استخدم الأزرار أعلاه لتعديل أو تعيين كلمة المرور بأمان."
                "</div>",
                reset_url,
                set_password_url,
            )
        return format_html('<span style="color: #9ca3af;">احفظ المستخدم أولاً / Enregistrez d\'abord</span>')

    get_password_change_link.short_description = "إدارة كلمة المرور / Gestion du mot de passe"

    def save_model(self, request, obj, form, change):
        if "password" in form.changed_data:
            pwd = form.cleaned_data.get("password")
            if pwd and not (pwd.startswith("pbkdf2_") or pwd.startswith("argon2") or pwd.startswith("bcrypt")):
                obj.set_password(pwd)
        super().save_model(request, obj, form, change)

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/reset-password/",
                self.admin_site.admin_view(self.reset_password_view),
                name="user_reset_password_fac",
            ),
            path(
                "<int:user_id>/set-password/",
                self.admin_site.admin_view(self.set_password_view),
                name="user_set_password_fac",
            ),
        ]
        return custom_urls + urls

    def reset_password_view(self, request, user_id):
        from django.shortcuts import render
        from apps.academique.etudiant.utils import generate_password

        if not self.has_change_permission(request):
            messages.error(request, "غير مصرح لك بتعديل المستخدمين.")
            return redirect("/faculte/admin/authentification/customuser/")

        try:
            user = CustomUser.objects.get(pk=user_id)

            if request.method != "POST":
                context = {
                    "title": f"تأكيد إعادة تعيين كلمة المرور لـ {user.username}",
                    "user_obj": user,
                    "opts": self.model._meta,
                }
                return render(request, "admin/fac_admin/reset_password_confirm.html", context)

            new_password = generate_password(user.last_name, user.last_name, user.first_name, user.first_name)
            user.set_password(new_password)
            user.doit_changer_mot_de_passe = True
            user.save(update_fields=["password", "doit_changer_mot_de_passe"])

            messages.success(
                request,
                format_html(
                    "تم إعادة تعيين كلمة المرور للمستخدم <strong>{}</strong> بنجاح.<br>"
                    '<span style="font-size: 14px; background: #1e293b; color: #fbbf24; padding: 8px 12px; '
                    'border-radius: 4px; font-family: monospace; display: inline-block; margin-top: 5px;">'
                    'كلمة المرور الجديدة: <strong style="color: #4ade80;">{}</strong></span>',
                    user.username,
                    new_password,
                ),
            )
        except CustomUser.DoesNotExist:
            messages.error(request, "المستخدم غير موجود.")

        return redirect("/faculte/admin/authentification/customuser/")

    def set_password_view(self, request, user_id):
        from django.shortcuts import render
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        if not self.has_change_permission(request):
            messages.error(request, "غير مصرح لك بتعديل المستخدمين.")
            return redirect("/faculte/admin/authentification/customuser/")

        try:
            user = CustomUser.objects.get(pk=user_id)

            if request.method == "POST":
                new_password = request.POST.get("new_password", "").strip()
                confirm_password = request.POST.get("confirm_password", "").strip()

                if not new_password:
                    messages.error(request, "كلمة المرور مطلوبة / Le mot de passe est requis")
                elif new_password != confirm_password:
                    messages.error(request, "كلمتا المرور غير متطابقتين / Les mots de passe ne correspondent pas")
                else:
                    try:
                        validate_password(new_password, user)
                        user.set_password(new_password)
                        user.doit_changer_mot_de_passe = False
                        user.save(update_fields=["password", "doit_changer_mot_de_passe"])
                        messages.success(
                            request,
                            format_html(
                                "تم تعيين كلمة المرور الجديدة للمستخدم <strong>{}</strong> بنجاح (مشفرة بأمان).",
                                user.username,
                            ),
                        )
                        return redirect("/faculte/admin/authentification/customuser/")
                    except ValidationError as e:
                        for err in e.messages:
                            messages.error(request, err)

            context = {
                "title": f"تعيين كلمة مرور جديدة لـ {user.username}",
                "user_obj": user,
                "opts": self.model._meta,
                "has_view_permission": True,
            }
            return render(request, "admin/fac_admin/set_password.html", context)

        except CustomUser.DoesNotExist:
            messages.error(request, "المستخدم غير موجود.")
            return redirect("/faculte/admin/authentification/customuser/")



# ══════════════════════════════════════════════════════════════
# 8. TABLES DE RÉFÉRENCE EN LECTURE SEULE
# ══════════════════════════════════════════════════════════════

class UniversiteReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr", "sigle", "siteweb")
    search_fields = ("code", "nom_ar", "nom_fr")


class DomaineReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class CycleReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class NiveauReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class GradeReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class DiplomeReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class SemestreReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class SessionReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class ReformeReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class ParcoursReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class UniteReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class GroupeReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("numero", "code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class SectionReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("numero", "code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class IdentificationReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class PosteReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr", "type", "niveau", "est_actif")
    list_filter = ("type", "niveau", "est_actif")
    search_fields = ("code", "nom_ar", "nom_fr")


class AnneeUniversitaireReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("nom", "date_debut", "date_fin", "est_courante")
    list_filter = ("est_courante",)
    search_fields = ("nom",)


class WilayaReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "codePostal", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class PaysReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class AmphiReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("numero", "nom_ar", "nom_fr", "capacite")
    search_fields = ("numero", "nom_ar", "nom_fr")


class SalleReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("numero", "nom_ar", "nom_fr", "capacite")
    search_fields = ("numero", "nom_ar", "nom_fr")


class LaboratoireReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("numero", "nom_ar", "nom_fr", "type", "capacite")
    list_filter = ("type",)
    search_fields = ("numero", "nom_ar", "nom_fr")
