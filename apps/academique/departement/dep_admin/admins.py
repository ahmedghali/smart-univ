# apps/academique/departement/dep_admin/admins.py
"""
Classes d'administration pour le département.
"""

from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.db.models import Case, IntegerField, OuterRef, Subquery, Value, When
from django.shortcuts import redirect, render
from django.utils.html import format_html
from import_export.admin import ImportExportMixin

from apps.academique.affectation.models import (
    Classe,
    Ens_Dep,
    SousGroupe,
)
from apps.academique.departement.models import Departement, Matiere, NivSpeDep, NivSpeDep_SG, Specialite
from apps.academique.enseignant.models import Enseignant
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.models import CustomUser
from apps.noyau.commun.models import (
    AffectationPoste,
    AnneeUniversitaire,
    Poste,
    PostePermission,
)

from .forms import EtudiantDepConfirmImportForm, EtudiantDepImportForm
from .mixins import (
    DepartementFilterMixin,
    PermissionCheckMixin,
    PermissionCheckMixinNoImport,
    ReadOnlyAdminMixin,
    _admin_request_var,
)
from .resources import EnsDepResource, EnseignantResource, EtudiantResource, MatiereResource, SpecialiteResource


class EnseignantDepAdmin(PermissionCheckMixin, DepartementFilterMixin, ImportExportMixin, admin.ModelAdmin):
    """
    Administration des enseignants pour le chef de département.
    Permissions contrôlées par PostePermission.
    Import/Export Excel activé.
    Interface identique à l'admin principal.
    """

    # Resource pour import/export
    resource_class = EnseignantResource
    import_template_name = "admin/dep_admin/import.html"

    # Template personnalisé pour la liste avec statistiques
    change_list_template = "admin/enseignant/enseignant/change_list.html"

    list_display = (
        "nom_fr",
        "prenom_fr",
        "nom_ar",
        "prenom_ar",
        "get_grade_code",
        "get_poste",
        "get_statut_ens_dep",
        "get_last_login",
        "get_user_creation_button",
        "action_buttons",
    )

    list_filter = (
        ("created_at", admin.DateFieldListFilter),
        ("updated_at", admin.DateFieldListFilter),
        "grade",
        "diplome",
        "sex",
        "sitfam",
        "wilaya",
        "vacAcademique",
        "maladie",
        "inscritProgres",
        "inscritMoodle",
        "inscritSNDL",
        "est_inscrit",
    )

    search_fields = (
        "matricule",
        "codeIns",
        "nom_ar",
        "prenom_ar",
        "nom_fr",
        "prenom_fr",
        "email_prof",
        "email_perso",
        "telmobile1",
        "telmobile2",
        "user__username",
        "user__email",
    )

    ordering = ("nom_fr", "prenom_fr", "nom_ar", "prenom_ar")

    readonly_fields = (
        "created_at",
        "updated_at",
        "get_user_link",
    )

    fieldsets = (
        (
            "المستخدم / Utilisateur",
            {"fields": ("get_user_link",), "description": "Compte utilisateur lié à cet enseignant"},
        ),
        (
            "معلومات شخصية / Informations personnelles",
            {"fields": ("civilite", ("nom_ar", "prenom_ar"), ("nom_fr", "prenom_fr"), "date_nais", "sex", "sitfam")},
        ),
        (
            "معلومات إدارية / Informations administratives",
            {"fields": ("matricule", "codeIns", "bac_annee", "date_Recrut")},
        ),
        (
            "مؤهلات أكاديمية / Qualifications académiques",
            {"fields": ("diplome", ("specialite_ar", "specialite_fr"), "grade")},
        ),
        (
            "معلومات الاتصال / Coordonnées",
            {
                "fields": (
                    ("telmobile1", "telmobile2"),
                    "telfix",
                    "fax",
                    "email_prof",
                    "email_perso",
                    "adresse",
                    "wilaya",
                )
            },
        ),
        (
            "المنصات الأكاديمية / Plateformes académiques",
            {"fields": ("inscritProgres", "inscritMoodle", "inscritSNDL", "est_inscrit")},
        ),
        (
            "الشبكات الاجتماعية والأكاديمية / Réseaux sociaux et académiques",
            {
                "fields": (
                    "googlescholar",
                    "researchgate",
                    "orcid_id",
                    "linkedIn",
                    "facebook",
                    "x_twitter",
                    "tiktok",
                    "telegram",
                ),
                "classes": ("collapse",),
            },
        ),
        ("الحالة / Statut", {"fields": ("vacAcademique", "maladie")}),
        ("الملاحظات / Observations", {"fields": ("observation",), "classes": ("collapse",)}),
        ("معلومات النظام / Informations système", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_last_login(self, obj):
        """Affiche la date de dernière connexion de l'utilisateur."""
        if obj.user and obj.user.last_login:
            return obj.user.last_login.strftime("%Y-%m-%d %H:%M")
        elif obj.user:
            return format_html('<span style="color: #9ca3af;">لم يسجل بعد</span>')
        return format_html('<span style="color: #ef4444;">-</span>')

    get_last_login.short_description = "آخر دخول / Dernier login"
    get_last_login.admin_order_field = "user__last_login"

    def get_user_link(self, obj):
        """Affiche les informations de l'utilisateur avec un style carte professionnelle dark."""
        if obj.user:
            user = obj.user
            status_color = "#4ade80" if user.is_active else "#f87171"
            status_bg = "rgba(74, 222, 128, 0.15)" if user.is_active else "rgba(248, 113, 113, 0.15)"
            status_text = "نشط / Actif" if user.is_active else "غير نشط / Inactif"
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "لم يسجل الدخول بعد"
            user_edit_url = f"/departement/admin/authentification/customuser/{user.pk}/change/"

            return format_html(
                '<div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); '
                "padding: 20px; border-radius: 12px; color: #e2e8f0; "
                'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); border: 1px solid #475569; max-width: 450px;">'
                '<div style="display: flex; align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #475569;">'
                '<div style="width: 50px; height: 50px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); '
                'border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-left: 15px;">👤</div>'
                '<div style="flex-grow: 1;">'
                '<div style="font-size: 16px; font-weight: 600; color: #f1f5f9;">{}</div>'
                '<div style="font-size: 12px; color: #94a3b8; margin-bottom: 6px;">@{}</div>'
                '<div style="background: {}; color: {}; padding: 3px 10px; border-radius: 20px; font-size: 11px; display: inline-block;">{}</div>'
                "</div></div>"
                '<div style="display: grid; gap: 10px; margin-bottom: 16px;">'
                '<div style="display: flex; align-items: center;"><span style="color: #64748b; font-size: 12px; width: 100px;">📧 البريد:</span>'
                '<span style="color: #e2e8f0; font-size: 13px;">{}</span></div>'
                '<div style="display: flex; align-items: center;"><span style="color: #64748b; font-size: 12px; width: 100px;">🕐 آخر دخول:</span>'
                '<span style="color: #e2e8f0; font-size: 13px;">{}</span></div></div>'
                '<a href="{}" style="display: block; text-align: center; background: linear-gradient(135deg, #3b82f6, #2563eb); '
                'color: white; padding: 10px 16px; text-decoration: none; border-radius: 8px; font-size: 13px;">⚙️ إدارة الحساب</a></div>',
                user.nom_complet,
                user.username,
                status_bg,
                status_color,
                status_text,
                user.email or "-",
                last_login,
                user_edit_url,
            )
        return format_html(
            '<div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 20px; '
            'border-radius: 12px; color: #94a3b8; text-align: center; border: 1px solid #475569; max-width: 450px;">'
            '<div style="font-size: 40px; margin-bottom: 10px;">⚠️</div>'
            '<div style="font-size: 14px;">لا يوجد حساب مرتبط</div>'
            '<div style="font-size: 12px; color: #64748b;">Aucun compte utilisateur lié</div></div>'
        )

    get_user_link.short_description = "المستخدم / Utilisateur"

    def get_user_creation_button(self, obj):
        """Affiche le nom d'utilisateur ou un bouton pour créer un utilisateur."""
        if obj.user:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ {}</span>', obj.user.username)
        else:
            url = f"/departement/admin/enseignant/enseignant/{obj.pk}/create-user/"
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; '
                'padding: 5px 10px; text-decoration: none; border-radius: 3px;">Créer utilisateur</a>',
                url,
            )

    get_user_creation_button.short_description = "Utilisateur"

    def get_grade_code(self, obj):
        """Affiche le code du grade."""
        if obj.grade:
            return obj.grade.code
        return "-"

    get_grade_code.short_description = "الرتبة / Grade"
    get_grade_code.admin_order_field = "grade__code"

    def get_poste(self, obj):
        """Affiche le poste de l'enseignant."""
        if obj.user:
            # Chercher l'affectation poste active
            from apps.noyau.commun.models import AffectationPoste

            affectation = AffectationPoste.objects.filter(user=obj.user, est_actif=True).select_related("poste").first()
            if affectation and affectation.poste:
                return affectation.poste.nom_ar or affectation.poste.nom_fr or affectation.poste.code
        return "-"

    get_poste.short_description = "المنصب / Poste"

    def get_statut_ens_dep(self, obj):
        """Affiche le statut de l'enseignant depuis Ens_Dep."""
        departement = getattr(self, "_current_departement", None)
        annee = getattr(self, "_current_annee", None)

        if departement and annee:
            ens_dep = Ens_Dep.objects.filter(enseignant=obj, departement=departement, annee_univ=annee).first()
            if ens_dep:
                # Couleurs selon le statut (utiliser les valeurs de l'enum)
                statut_colors = {
                    Ens_Dep.StatutEnseignant.PERMANENT: "#28a745",  # vert - مرسم
                    Ens_Dep.StatutEnseignant.PERMANENT_VACATAIRE: "#17a2b8",  # bleu
                    Ens_Dep.StatutEnseignant.VACATAIRE: "#ffc107",  # jaune
                    Ens_Dep.StatutEnseignant.ASSOCIE: "#fd7e14",  # orange
                    Ens_Dep.StatutEnseignant.DOCTORANT: "#6f42c1",  # violet
                }
                color = statut_colors.get(ens_dep.statut, "#6c757d")
                return format_html(
                    '<span style="color: {}; font-weight: bold;">{}</span>', color, ens_dep.get_statut_display()
                )
        return "-"

    get_statut_ens_dep.short_description = "الحالة / Statut"

    def action_buttons(self, obj):
        """Affiche les boutons d'action pour chaque enseignant."""
        edit_url = f"/departement/admin/enseignant/enseignant/{obj.pk}/change/"

        # Vérifier le statut pour afficher le bouton de suppression
        departement = getattr(self, "_current_departement", None)
        annee = getattr(self, "_current_annee", None)

        buttons = format_html(
            '<a href="{}" title="تعديل / Modifier" style="background-color: #417690; color: white; '
            'padding: 5px 8px; text-decoration: none; border-radius: 3px; font-size: 14px; margin-left: 3px;">'
            "✏️</a>",
            edit_url,
        )

        # Ajouter le bouton supprimer UNIQUEMENT si NON-PERMANENT (مرسم)
        if departement and annee:
            ens_dep = Ens_Dep.objects.filter(enseignant=obj, departement=departement, annee_univ=annee).first()
            # Comparer avec la valeur de l'enum, pas le label
            if ens_dep and ens_dep.statut != Ens_Dep.StatutEnseignant.PERMANENT:
                delete_url = f"/departement/admin/enseignant/enseignant/{obj.pk}/delete/"
                buttons = format_html(
                    '{}<a href="{}" title="حذف / Supprimer" style="background-color: #8b0000; color: white; '
                    'padding: 5px 8px; text-decoration: none; border-radius: 3px; font-size: 14px; margin-right: 3px;">'
                    "🗑️</a>",
                    buttons,
                    delete_url,
                )

        return buttons

    action_buttons.short_description = "الإجراءات"
    action_buttons.allow_tags = True

    def get_queryset(self, request):
        """Filtre les enseignants par département - uniquement les permanents."""
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        annee = self.get_annee_courante()

        # Stocker pour les autres méthodes
        self._current_departement = departement
        self._current_annee = annee

        if departement and annee:
            # Filtrer uniquement les enseignants PERMANENT
            ens_ids = Ens_Dep.objects.filter(
                departement=departement, annee_univ=annee, statut=Ens_Dep.StatutEnseignant.PERMANENT
            ).values_list("enseignant_id", flat=True)
            return qs.filter(id__in=ens_ids)
        return qs.none()

    def save_model(self, request, obj, form, change):
        """Après la sauvegarde, créer automatiquement l'affectation Ens_Dep et l'utilisateur."""
        super().save_model(request, obj, form, change)

        if not change:
            departement = self.get_departement(request)
            annee = self.get_annee_courante()

            if departement and annee:
                Ens_Dep.objects.get_or_create(
                    enseignant=obj,
                    departement=departement,
                    annee_univ=annee,
                    defaults={
                        "statut": Ens_Dep.StatutEnseignant.PERMANENT,  # مرسم
                        "est_actif": True,
                        "semestre_1": True,
                        "semestre_2": True,
                    },
                )

        # Créer l'utilisateur si pas encore créé
        if not obj.user:
            from apps.academique.enseignant.utils import create_user_for_enseignant

            user, _ = create_user_for_enseignant(obj)
            if user:
                pwd_info = f" - Mot de passe temporaire : {user._generated_password}" if getattr(user, "_generated_password", None) else ""
                messages.success(request, f"Utilisateur créé - Login: {user.username}{pwd_info}")

    def get_urls(self):
        """Ajoute une URL personnalisée pour créer un utilisateur."""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:enseignant_id>/create-user/",
                self.admin_site.admin_view(self.create_user_view),
                name="enseignant_enseignant_create_user",
            ),
        ]
        return custom_urls + urls

    def create_user_view(self, request, enseignant_id):
        """Vue pour créer un utilisateur pour un enseignant."""
        from apps.academique.enseignant.utils import create_user_for_enseignant

        try:
            enseignant = Enseignant.objects.get(pk=enseignant_id)
            if enseignant.user:
                messages.warning(request, "Cet enseignant a déjà un utilisateur.")
            else:
                user, error = create_user_for_enseignant(enseignant)
                if user:
                    pwd_info = f" - Mot de passe temporaire : {user._generated_password}" if getattr(user, "_generated_password", None) else ""
                    messages.success(request, f"Utilisateur créé - Login: {user.username}{pwd_info}")
                else:
                    messages.error(request, error or "Erreur lors de la création de l'utilisateur.")
        except Enseignant.DoesNotExist:
            messages.error(request, "Enseignant introuvable.")
        return redirect("/departement/admin/enseignant/enseignant/")

    def get_import_resource_kwargs(self, request, **kwargs):
        """Passe le département_id à la Resource pour créer les relations Ens_Dep."""
        kw = (
            super().get_import_resource_kwargs(request, **kwargs)
            if hasattr(super(), "get_import_resource_kwargs")
            else {}
        )
        departement_id = request.session.get("selected_departement_id")
        kw["departement_id"] = departement_id
        return kw

    def changelist_view(self, request, extra_context=None):
        """Ajoute les statistiques au contexte de la liste."""
        from django.db.models import Count

        extra_context = extra_context or {}

        qs = self.get_queryset(request)

        # Statistiques générales
        total = qs.count()
        inscrits = qs.filter(est_inscrit=True).count()

        # Statistiques par sexe
        stats_sexe = qs.values("sex").annotate(count=Count("id"))
        hommes = next((s["count"] for s in stats_sexe if s["sex"] == "ذكر"), 0)
        femmes = next((s["count"] for s in stats_sexe if s["sex"] == "أنثى"), 0)

        # Statistiques par statut
        en_vacances = qs.filter(vacAcademique=True).count()
        en_maladie = qs.filter(maladie=True).count()

        # Statistiques utilisateurs
        avec_compte = qs.filter(user__isnull=False).count()
        sans_compte = total - avec_compte

        # Pourcentages
        pct_hommes = round((hommes / total * 100), 1) if total > 0 else 0
        pct_femmes = round((femmes / total * 100), 1) if total > 0 else 0
        pct_inscrits = round((inscrits / total * 100), 1) if total > 0 else 0
        pct_avec_compte = round((avec_compte / total * 100), 1) if total > 0 else 0

        extra_context["enseignant_stats"] = {
            "total": total,
            "hommes": hommes,
            "femmes": femmes,
            "pct_hommes": pct_hommes,
            "pct_femmes": pct_femmes,
            "inscrits": inscrits,
            "pct_inscrits": pct_inscrits,
            "en_vacances": en_vacances,
            "en_maladie": en_maladie,
            "avec_compte": avec_compte,
            "sans_compte": sans_compte,
            "pct_avec_compte": pct_avec_compte,
        }

        return super().changelist_view(request, extra_context=extra_context)


# ══════════════════════════════════════════════════════════════
# ADMIN ETUDIANT POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════


class EtudiantDepAdmin(PermissionCheckMixin, DepartementFilterMixin, ImportExportMixin, admin.ModelAdmin):
    """
    Administration des étudiants pour le chef de département.
    Import/Export Excel activé avec sélection du groupe obligatoire.
    Interface identique à l'admin principal.
    """

    # Resource et formulaires pour import/export
    resource_class = EtudiantResource
    import_form_class = EtudiantDepImportForm
    confirm_form_class = EtudiantDepConfirmImportForm
    import_template_name = "admin/dep_admin/import.html"

    # Template personnalisé pour la liste avec statistiques
    change_list_template = "admin/etudiant/etudiant/change_list.html"

    @admin.display(description="الرقم التسلسلي / Matricule", ordering="matricule")
    def get_matricule(self, obj):
        return obj.matricule

    def get_import_form_kwargs(self, request, *args, **kwargs):
        """Passe le département au formulaire d'import."""
        kw = (
            super().get_import_form_kwargs(request, *args, **kwargs)
            if hasattr(super(), "get_import_form_kwargs")
            else {}
        )
        dep = self.get_departement(request)
        kw["departement_id"] = dep.id if dep else None
        return kw

    def get_confirm_form_kwargs(self, request, *args, **kwargs):
        """Passe le département au formulaire de confirmation (A08)."""
        kw = (
            super().get_confirm_form_kwargs(request, *args, **kwargs)
            if hasattr(super(), "get_confirm_form_kwargs")
            else {}
        )
        dep = self.get_departement(request)
        kw["departement_id"] = dep.id if dep else None
        return kw

    def get_confirm_form_initial(self, request, import_form):
        """Passe le groupe sélectionné au formulaire de confirmation."""
        initial = (
            super().get_confirm_form_initial(request, import_form)
            if hasattr(super(), "get_confirm_form_initial")
            else {}
        )
        if import_form and hasattr(import_form, "cleaned_data"):
            niv_spe_dep_sg = import_form.cleaned_data.get("niv_spe_dep_sg")
            if niv_spe_dep_sg:
                initial["niv_spe_dep_sg"] = niv_spe_dep_sg.id
        return initial

    def get_import_resource_kwargs(self, request, **kwargs):
        """Passe le groupe à la resource avec vérification de département (A08)."""
        kw = (
            super().get_import_resource_kwargs(request, **kwargs)
            if hasattr(super(), "get_import_resource_kwargs")
            else {}
        )
        niv_spe_dep_sg_id = request.POST.get("niv_spe_dep_sg")
        if niv_spe_dep_sg_id:
            dep = self.get_departement(request)
            sg = NivSpeDep_SG.objects.filter(
                id=niv_spe_dep_sg_id,
                niv_spe_dep__departement=dep,
            ).first()
            if sg:
                kw["niv_spe_dep_sg_id"] = sg.id
        return kw

    list_display = (
        "get_matricule",
        "nom_fr",
        "prenom_fr",
        "nom_ar",
        "prenom_ar",
        "get_last_login",
        "get_user_creation_button",
        "action_buttons",
    )

    list_filter = (
        ("created_at", admin.DateFieldListFilter),
        ("updated_at", admin.DateFieldListFilter),
        "est_actif",
        "delegue",
        "sexe",
        "sit_fam",
        "niv_spe_dep_sg__niv_spe_dep__niveau",
        "niv_spe_dep_sg__niv_spe_dep__specialite",
        "wilaya",
        "en_vac_aca",
        "en_maladie",
        "inscrit_progres",
        "inscrit_moodle",
        "inscrit_sndl",
        "est_inscrit",
    )

    search_fields = (
        "matricule",
        "num_ins",
        "nom_ar",
        "nom_fr",
        "prenom_ar",
        "prenom_fr",
        "email_prof",
        "email_perso",
        "tel_mobile1",
        "tel_mobile2",
        "user__username",
        "user__email",
    )

    ordering = ("nom_fr", "prenom_fr", "nom_ar", "prenom_ar")

    readonly_fields = (
        "created_at",
        "updated_at",
        "get_user_link",
    )

    fieldsets = (
        (
            "المستخدم / Utilisateur",
            {"fields": ("get_user_link",), "description": "Compte utilisateur lié à cet étudiant"},
        ),
        (
            "معلومات شخصية / Informations personnelles",
            {"fields": ("civilite", ("nom_ar", "prenom_ar"), ("nom_fr", "prenom_fr"), "date_nais", "sexe", "sit_fam")},
        ),
        (
            "معلومات أكاديمية / Informations académiques",
            {"fields": ("matricule", "num_ins", "bac_annee", "niv_spe_dep_sg", "delegue")},
        ),
        (
            "معلومات الاتصال / Coordonnées",
            {
                "fields": (
                    ("tel_mobile1", "tel_mobile2"),
                    "tel_fix",
                    "fax",
                    "email_prof",
                    "email_perso",
                    "adresse",
                    "wilaya",
                )
            },
        ),
        (
            "المنصات الأكاديمية / Plateformes académiques",
            {"fields": ("inscrit_progres", "inscrit_moodle", "inscrit_sndl", "est_inscrit")},
        ),
        (
            "الشبكات الاجتماعية والأكاديمية / Réseaux sociaux et académiques",
            {
                "fields": (
                    "google_scholar",
                    "researchgate",
                    "orcid_id",
                    "linkedin",
                    "facebook",
                    "x_twitter",
                    "tiktok",
                    "telegram",
                ),
                "classes": ("collapse",),
            },
        ),
        ("الحالة / Statut", {"fields": ("est_actif", "en_vac_aca", "en_maladie")}),
        ("الملاحظات / Observations", {"fields": ("observation",), "classes": ("collapse",)}),
        ("معلومات النظام / Informations système", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_last_login(self, obj):
        """Affiche la date de dernière connexion de l'utilisateur."""
        if obj.user and obj.user.last_login:
            return obj.user.last_login.strftime("%Y-%m-%d %H:%M")
        elif obj.user:
            return format_html('<span style="color: #9ca3af;">لم يسجل بعد</span>')
        return format_html('<span style="color: #ef4444;">-</span>')

    get_last_login.short_description = "آخر دخول / Dernier login"
    get_last_login.admin_order_field = "user__last_login"

    def get_user_link(self, obj):
        """Affiche les informations de l'utilisateur avec un style carte professionnelle dark."""
        if obj.user:
            user = obj.user
            status_color = "#4ade80" if user.is_active else "#f87171"
            status_bg = "rgba(74, 222, 128, 0.15)" if user.is_active else "rgba(248, 113, 113, 0.15)"
            status_text = "نشط / Actif" if user.is_active else "غير نشط / Inactif"
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "لم يسجل الدخول بعد"
            user_edit_url = f"/departement/admin/authentification/customuser/{user.pk}/change/"

            return format_html(
                '<div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); '
                "padding: 20px; border-radius: 12px; color: #e2e8f0; "
                'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); border: 1px solid #475569; max-width: 450px;">'
                '<div style="display: flex; align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #475569;">'
                '<div style="width: 50px; height: 50px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); '
                'border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-left: 15px;">👤</div>'
                '<div style="flex-grow: 1;">'
                '<div style="font-size: 16px; font-weight: 600; color: #f1f5f9;">{}</div>'
                '<div style="font-size: 12px; color: #94a3b8; margin-bottom: 6px;">@{}</div>'
                '<div style="background: {}; color: {}; padding: 3px 10px; border-radius: 20px; font-size: 11px; display: inline-block;">{}</div>'
                "</div></div>"
                '<div style="display: grid; gap: 10px; margin-bottom: 16px;">'
                '<div style="display: flex; align-items: center;"><span style="color: #64748b; font-size: 12px; width: 100px;">📧 البريد:</span>'
                '<span style="color: #e2e8f0; font-size: 13px;">{}</span></div>'
                '<div style="display: flex; align-items: center;"><span style="color: #64748b; font-size: 12px; width: 100px;">🕐 آخر دخول:</span>'
                '<span style="color: #e2e8f0; font-size: 13px;">{}</span></div></div>'
                '<a href="{}" style="display: block; text-align: center; background: linear-gradient(135deg, #3b82f6, #2563eb); '
                'color: white; padding: 10px 16px; text-decoration: none; border-radius: 8px; font-size: 13px;">⚙️ إدارة الحساب</a></div>',
                user.nom_complet,
                user.username,
                status_bg,
                status_color,
                status_text,
                user.email or "-",
                last_login,
                user_edit_url,
            )
        return format_html(
            '<div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 20px; '
            'border-radius: 12px; color: #94a3b8; text-align: center; border: 1px solid #475569; max-width: 450px;">'
            '<div style="font-size: 40px; margin-bottom: 10px;">⚠️</div>'
            '<div style="font-size: 14px;">لا يوجد حساب مرتبط</div>'
            '<div style="font-size: 12px; color: #64748b;">Aucun compte utilisateur lié</div></div>'
        )

    get_user_link.short_description = "المستخدم / Utilisateur"

    def get_user_creation_button(self, obj):
        """Affiche le nom d'utilisateur ou un bouton pour créer un utilisateur."""
        if obj.user:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ {}</span>', obj.user.username)
        else:
            url = f"/departement/admin/etudiant/etudiant/{obj.pk}/create-user/"
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; '
                'padding: 5px 10px; text-decoration: none; border-radius: 3px;">Créer utilisateur</a>',
                url,
            )

    get_user_creation_button.short_description = "Utilisateur"

    def get_queryset(self, request):
        """Filtre les étudiants par département."""
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(niv_spe_dep_sg__niv_spe_dep__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtre les choix de NivSpeDep_SG selon le département."""
        if db_field.name == "niv_spe_dep_sg":
            departement = self.get_departement(request)
            if departement:
                kwargs["queryset"] = NivSpeDep_SG.objects.filter(niv_spe_dep__departement=departement)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Crée automatiquement un utilisateur lors de l'ajout."""
        super().save_model(request, obj, form, change)
        if not change or not obj.user:
            from apps.academique.etudiant.utils import create_user_for_etudiant

            user = create_user_for_etudiant(obj)
            if user:
                pwd_info = f" - Mot de passe temporaire : {user._generated_password}" if getattr(user, "_generated_password", None) else ""
                messages.success(request, f"Utilisateur créé - Login: {user.username}{pwd_info}")

    def get_urls(self):
        """Ajoute une URL personnalisée pour créer un utilisateur."""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:etudiant_id>/create-user/",
                self.admin_site.admin_view(self.create_user_view),
                name="etudiant_etudiant_create_user",
            ),
        ]
        return custom_urls + urls

    def create_user_view(self, request, etudiant_id):
        """Vue pour créer un utilisateur pour un étudiant."""
        from apps.academique.etudiant.utils import create_user_for_etudiant

        try:
            etudiant = Etudiant.objects.get(pk=etudiant_id)
            if etudiant.user:
                messages.warning(request, "Cet étudiant a déjà un utilisateur.")
            else:
                user = create_user_for_etudiant(etudiant)
                if user:
                    pwd_info = f" - Mot de passe temporaire : {user._generated_password}" if getattr(user, "_generated_password", None) else ""
                    messages.success(request, f"Utilisateur créé - Login: {user.username}{pwd_info}")
                else:
                    messages.error(request, "Erreur lors de la création de l'utilisateur.")
        except Etudiant.DoesNotExist:
            messages.error(request, "Étudiant introuvable.")
        return redirect("/departement/admin/etudiant/etudiant/")

    def action_buttons(self, obj):
        """Affiche les boutons d'action pour chaque étudiant."""
        edit_url = f"/departement/admin/etudiant/etudiant/{obj.pk}/change/"
        return format_html(
            '<a class="button" href="{}" style="background-color: #417690; color: white; '
            'padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
            "✏️</a>",
            edit_url,
        )

    action_buttons.short_description = "الإجراءات"
    action_buttons.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        """Ajoute les statistiques au contexte de la liste."""
        from django.db.models import Count

        extra_context = extra_context or {}

        # Récupérer le queryset filtré
        qs = self.get_queryset(request)

        # Statistiques générales
        total = qs.count()
        total_actifs = qs.filter(est_actif=True).count()
        total_inactifs = total - total_actifs

        # Statistiques par sexe
        stats_sexe = qs.values("sexe").annotate(count=Count("id"))
        hommes = next((s["count"] for s in stats_sexe if s["sexe"] == "ذكر"), 0)
        femmes = next((s["count"] for s in stats_sexe if s["sexe"] == "أنثى"), 0)

        # Statistiques par statut
        delegues = qs.filter(delegue=True).count()
        en_vacances = qs.filter(en_vac_aca=True).count()
        en_maladie = qs.filter(en_maladie=True).count()
        inscrits = qs.filter(est_inscrit=True).count()

        # Statistiques utilisateurs
        avec_compte = qs.filter(user__isnull=False).count()
        sans_compte = total - avec_compte

        # Pourcentages
        pct_hommes = round((hommes / total * 100), 1) if total > 0 else 0
        pct_femmes = round((femmes / total * 100), 1) if total > 0 else 0
        pct_actifs = round((total_actifs / total * 100), 1) if total > 0 else 0
        pct_avec_compte = round((avec_compte / total * 100), 1) if total > 0 else 0

        extra_context["etudiant_stats"] = {
            "total": total,
            "total_actifs": total_actifs,
            "total_inactifs": total_inactifs,
            "hommes": hommes,
            "femmes": femmes,
            "pct_hommes": pct_hommes,
            "pct_femmes": pct_femmes,
            "pct_actifs": pct_actifs,
            "delegues": delegues,
            "en_vacances": en_vacances,
            "en_maladie": en_maladie,
            "inscrits": inscrits,
            "avec_compte": avec_compte,
            "sans_compte": sans_compte,
            "pct_avec_compte": pct_avec_compte,
        }

        return super().changelist_view(request, extra_context=extra_context)


# ══════════════════════════════════════════════════════════════
# ADMIN AFFECTATION (ENS_DEP) POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════


class EnsDep_DepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """
    Administration des affectations enseignant-département.
    Permet au chef de département de gérer les affectations.
    Style identique à EnseignantDepAdmin.
    """

    resource_class = EnsDepResource

    list_display = (
        "get_nom_fr",
        "get_prenom_fr",
        "get_nom_ar",
        "get_prenom_ar",
        "get_statut_display",
        "get_grade_code",
        "get_poste",
        "get_semestres",
        "get_date_affectation",
        "get_last_login",
        "get_user_display",
        "get_est_actif",
        "action_buttons",
    )

    list_filter = (
        "statut",
        "semestre_1",
        "semestre_2",
        "est_actif",
        "enseignant__grade",
    )

    search_fields = (
        "enseignant__nom_ar",
        "enseignant__prenom_ar",
        "enseignant__nom_fr",
        "enseignant__prenom_fr",
        "enseignant__matricule",
        "enseignant__user__username",
    )

    readonly_fields = (
        "departement",
        "annee_univ",
    )

    fieldsets = (
        (
            "معلومات الانتماء / Informations d'affectation",
            {
                "fields": (
                    "enseignant",
                    "departement",
                    "annee_univ",
                    "date_affectation",
                    "statut",
                )
            },
        ),
        ("السداسيات / Semestres", {"fields": (("semestre_1", "semestre_2"),)}),
        ("الحالة / Statut", {"fields": ("est_actif",)}),
    )

    # ══════════════════════════════════════════════════════════
    # COLONNES PERSONNALISÉES
    # ══════════════════════════════════════════════════════════

    def get_nom_fr(self, obj):
        return obj.enseignant.nom_fr or "-"

    get_nom_fr.short_description = "Nom"
    get_nom_fr.admin_order_field = "enseignant__nom_fr"

    def get_prenom_fr(self, obj):
        return obj.enseignant.prenom_fr or "-"

    get_prenom_fr.short_description = "Prénom"
    get_prenom_fr.admin_order_field = "enseignant__prenom_fr"

    def get_nom_ar(self, obj):
        return obj.enseignant.nom_ar or "-"

    get_nom_ar.short_description = "اللقب"
    get_nom_ar.admin_order_field = "enseignant__nom_ar"

    def get_prenom_ar(self, obj):
        return obj.enseignant.prenom_ar or "-"

    get_prenom_ar.short_description = "الاسم"
    get_prenom_ar.admin_order_field = "enseignant__prenom_ar"

    def get_grade_code(self, obj):
        """Affiche le code du grade."""
        if obj.enseignant.grade:
            return obj.enseignant.grade.code
        return "-"

    get_grade_code.short_description = "الرتبة"
    get_grade_code.admin_order_field = "enseignant__grade__code"

    def get_semestres(self, obj):
        """Affiche les semestres actifs avec style."""
        semestres = []
        if obj.semestre_1:
            semestres.append(
                '<span style="background:#28a745;color:white;padding:2px 6px;border-radius:3px;font-size:11px;">S1</span>'
            )
        if obj.semestre_2:
            semestres.append(
                '<span style="background:#17a2b8;color:white;padding:2px 6px;border-radius:3px;font-size:11px;">S2</span>'
            )
        return format_html(" ".join(semestres)) if semestres else "-"

    get_semestres.short_description = "السداسيات"

    def get_poste(self, obj):
        """Affiche le poste de l'enseignant."""
        # Utilise l'annotation poste_nom si disponible
        if hasattr(obj, "poste_nom") and obj.poste_nom:
            return obj.poste_nom
        if obj.enseignant.user:
            affectation = (
                AffectationPoste.objects.filter(user=obj.enseignant.user, est_actif=True)
                .select_related("poste")
                .first()
            )
            if affectation and affectation.poste:
                return affectation.poste.nom_ar or affectation.poste.nom_fr or affectation.poste.code
        return "-"

    get_poste.short_description = "المنصب"
    get_poste.admin_order_field = "poste_nom"

    def get_statut_display(self, obj):
        """Affiche le statut avec couleur."""
        statut_colors = {
            Ens_Dep.StatutEnseignant.PERMANENT: "#28a745",  # vert
            Ens_Dep.StatutEnseignant.PERMANENT_VACATAIRE: "#17a2b8",  # bleu
            Ens_Dep.StatutEnseignant.VACATAIRE: "#ffc107",  # jaune
            Ens_Dep.StatutEnseignant.ASSOCIE: "#fd7e14",  # orange
            Ens_Dep.StatutEnseignant.DOCTORANT: "#6f42c1",  # violet
        }
        color = statut_colors.get(obj.statut, "#6c757d")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_statut_display())

    get_statut_display.short_description = "الحالة"
    get_statut_display.admin_order_field = "statut"

    def get_date_affectation(self, obj):
        """Affiche la date d'affectation."""
        if obj.date_affectation:
            return obj.date_affectation.strftime("%Y-%m-%d")
        return "-"

    get_date_affectation.short_description = "تاريخ الإنتساب"
    get_date_affectation.admin_order_field = "date_affectation"

    def get_last_login(self, obj):
        """Affiche la date de dernière connexion."""
        if obj.enseignant.user and obj.enseignant.user.last_login:
            return obj.enseignant.user.last_login.strftime("%Y-%m-%d %H:%M")
        elif obj.enseignant.user:
            return format_html('<span style="color: #9ca3af;">لم يسجل بعد</span>')
        return format_html('<span style="color: #ef4444;">-</span>')

    get_last_login.short_description = "آخر دخول"

    def get_user_display(self, obj):
        """Affiche le nom d'utilisateur."""
        if obj.enseignant.user:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ {}</span>', obj.enseignant.user.username
            )
        return format_html('<span style="color: #dc3545;">✗ لا يوجد</span>')

    get_user_display.short_description = "Utilisateur"

    def get_est_actif(self, obj):
        """Affiche le statut actif."""
        if obj.est_actif:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')

    get_est_actif.short_description = "Actif"
    get_est_actif.admin_order_field = "est_actif"

    def action_buttons(self, obj):
        """Affiche les boutons d'action."""
        edit_url = f"/departement/admin/affectation/ens_dep/{obj.pk}/change/"

        # Ajouter le bouton supprimer UNIQUEMENT si NON-PERMANENT
        if obj.statut != Ens_Dep.StatutEnseignant.PERMANENT:
            delete_url = f"/departement/admin/affectation/ens_dep/{obj.pk}/delete/"
            return format_html(
                '<div style="display: flex; gap: 3px; white-space: nowrap;">'
                '<a href="{}" title="تعديل / Modifier" style="background-color: #417690; color: white; '
                'padding: 3px 5px; text-decoration: none; border-radius: 3px; font-size: 11px;">✏️</a>'
                '<a href="{}" title="حذف / Supprimer" style="background-color: #8b0000; color: white; '
                'padding: 3px 5px; text-decoration: none; border-radius: 3px; font-size: 11px;">🗑️</a>'
                "</div>",
                edit_url,
                delete_url,
            )
        else:
            return format_html(
                '<a href="{}" title="تعديل / Modifier" style="background-color: #417690; color: white; '
                'padding: 3px 5px; text-decoration: none; border-radius: 3px; font-size: 11px;">✏️</a>',
                edit_url,
            )

    action_buttons.short_description = "الإجراءات"

    def has_delete_permission(self, request, obj=None):
        """
        Permet la suppression UNIQUEMENT pour les enseignants non-permanents.
        Le chef de département peut supprimer les affectations des vacataires, etc.
        """
        # Vérifier d'abord si l'utilisateur a accès à ce module
        perm_key = self.get_permission_key()
        perms = PostePermission.get_permissions(request)
        has_view = perms.get(f"{perm_key}_view", False)

        if not has_view:
            return False

        # Si un objet spécifique est passé, vérifier son statut
        if obj is not None:
            # Autoriser la suppression UNIQUEMENT si NON-PERMANENT
            return obj.statut != Ens_Dep.StatutEnseignant.PERMANENT

        # Pour la liste (pas d'objet spécifique), autoriser l'accès à la vue de suppression
        # La vérification du statut se fait au niveau de l'objet individuel
        return True

    # ══════════════════════════════════════════════════════════
    # MÉTHODES STANDARD
    # ══════════════════════════════════════════════════════════

    ordering = ("enseignant__nom_fr", "enseignant__prenom_fr")  # Tri par défaut: Nom puis Prénom

    # Colonnes triables: الحالة, Nom, Prénom, اللقب, الاسم, الرتبة, المنصب
    sortable_by = (
        "get_statut_display",
        "get_nom_fr",
        "get_prenom_fr",
        "get_nom_ar",
        "get_prenom_ar",
        "get_grade_code",
        "get_poste",
    )

    def get_queryset(self, request):
        """Filtre les affectations par département avec tri personnalisé."""
        # Effacer d'abord le tri par défaut du modèle avec order_by()
        qs = (
            super()
            .get_queryset(request)
            .order_by()
            .select_related("enseignant", "enseignant__user", "enseignant__grade", "departement", "annee_univ")
        )
        departement = self.get_departement(request)
        annee = self.get_annee_courante()

        if departement and annee:
            # Tri personnalisé: PERMANENT, PERMANENT_VACATAIRE, ASSOCIE, VACATAIRE, DOCTORANT
            statut_order = Case(
                When(statut="Permanent", then=Value(1)),
                When(statut="Permanent & Vacataire", then=Value(2)),
                When(statut="Associe", then=Value(3)),
                When(statut="Vacataire", then=Value(4)),
                When(statut="Doctorant", then=Value(5)),
                default=Value(6),
                output_field=IntegerField(),
            )

            # Subquery pour obtenir le nom du poste
            poste_subquery = AffectationPoste.objects.filter(user=OuterRef("enseignant__user"), est_actif=True).values(
                "poste__nom_ar"
            )[:1]

            return (
                qs.filter(departement=departement, annee_univ=annee)
                .annotate(statut_order=statut_order, poste_nom=Subquery(poste_subquery))
                .order_by("enseignant__nom_fr", "enseignant__prenom_fr")
            )
        return qs.none()

    def get_ordering(self, request):
        """Tri par défaut: Nom puis Prénom."""
        return ("enseignant__nom_fr", "enseignant__prenom_fr")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Pré-remplit le département et l'année."""
        if db_field.name == "departement":
            departement = self.get_departement(request)
            if departement:
                kwargs["queryset"] = Departement.objects.filter(id=departement.id)
                kwargs["initial"] = departement

        if db_field.name == "annee_univ":
            annee = self.get_annee_courante()
            if annee:
                kwargs["queryset"] = AnneeUniversitaire.objects.filter(id=annee.id)
                kwargs["initial"] = annee

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Force le département et l'année lors de la sauvegarde."""
        if not change:
            departement = self.get_departement(request)
            annee = self.get_annee_courante()
            if departement:
                obj.departement = departement
            if annee:
                obj.annee_univ = annee

        super().save_model(request, obj, form, change)

        if not change:
            messages.success(request, f'تم ربط الأستاذ "{obj.enseignant}" بالقسم بنجاح.')


# ══════════════════════════════════════════════════════════════
# ADMIN UTILISATEURS POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════


class UserDepAdmin(PermissionCheckMixinNoImport, DepartementFilterMixin, admin.ModelAdmin):
    """
    Administration des utilisateurs pour le chef de département.
    Permet de gérer les comptes des enseignants et étudiants du département.
    Utilise PermissionCheckMixinNoImport car pas besoin d'import/export pour les utilisateurs.
    """

    list_display = (
        "username",
        "get_nom_complet",
        "get_type_utilisateur",
        "is_active",
        "last_login",
        "get_reset_password_button",
        "action_buttons",
    )

    list_filter = (
        "is_active",
        "groups",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "get_password_change_link",
    )

    # Actions personnalisées
    actions = [
        "reset_password_action",
        "activate_users",
        "deactivate_users",
    ]

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
                "description": "Cliquez sur le bouton pour réinitialiser le mot de passe",
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

    filter_horizontal = ["groups"]

    def get_nom_complet(self, obj):
        """Affiche le nom complet."""
        return obj.nom_complet

    get_nom_complet.short_description = "الاسم الكامل / Nom"

    def get_type_utilisateur(self, obj):
        """Affiche le type d'utilisateur (Enseignant ou Étudiant)."""
        if hasattr(obj, "enseignant_profile") and obj.enseignant_profile:
            return format_html('<span style="color: #2196F3;">أستاذ</span>')
        elif hasattr(obj, "etudiant_profile") and obj.etudiant_profile:
            return format_html('<span style="color: #4CAF50;">طالب</span>')
        return format_html('<span style="color: #9E9E9E;">-</span>')

    get_type_utilisateur.short_description = "النوع / Type"

    def get_reset_password_button(self, obj):
        """Affiche un bouton pour réinitialiser le mot de passe."""
        url = f"/departement/admin/authentification/customuser/{obj.pk}/reset-password/"
        return format_html(
            '<a class="button" href="{}" style="background: #417690; color: white; '
            'padding: 3px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;">'
            "إعادة تعيين</a>",
            url,
        )

    get_reset_password_button.short_description = "كلمة المرور"
    get_reset_password_button.allow_tags = True

    def get_password_change_link(self, obj):
        """Affiche les options de gestion du mot de passe dans le formulaire."""
        if obj and obj.pk:
            # Utiliser des URLs directes au lieu de reverse
            reset_url = f"/departement/admin/authentification/customuser/{obj.pk}/reset-password/"
            set_password_url = f"/departement/admin/authentification/customuser/{obj.pk}/set-password/"
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
                "• إعادة تعيين تلقائي: كلمة المرور = أول حرفين من الاسم + أول حرفين من اللقب + 123<br>"
                "• Réinitialiser auto: Mot de passe = 2 premières lettres nom + prénom + 123"
                "</div>",
                reset_url,
                set_password_url,
            )
        return format_html('<span style="color: #9ca3af;">احفظ المستخدم أولاً / Enregistrez d\'abord</span>')

    get_password_change_link.short_description = "إدارة كلمة المرور / Gestion du mot de passe"
    get_password_change_link.allow_tags = True

    def get_urls(self):
        """Ajoute des URLs personnalisées."""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/reset-password/",
                self.admin_site.admin_view(self.reset_password_view),
                name="user_reset_password",
            ),
            path(
                "<int:user_id>/set-password/",
                self.admin_site.admin_view(self.set_password_view),
                name="user_set_password",
            ),
        ]
        return custom_urls + urls

    def reset_password_view(self, request, user_id):
        """Vue pour réinitialiser le mot de passe d'un utilisateur (automatique)."""
        from apps.academique.etudiant.utils import generate_password

        try:
            user = CustomUser.objects.get(pk=user_id)

            # Vérifier que l'utilisateur appartient au département (A02)
            departement = self.get_departement(request)
            if not departement:
                messages.error(request, "لا يوجد قسم محدد.")
                return redirect("/departement/admin/authentification/customuser/")

            annee = self.get_annee_courante()
            allowed_ids = self.get_user_ids_for_department(departement, annee)
            if user.pk not in allowed_ids:
                messages.error(
                    request,
                    "المستخدم لا ينتمي إلى هذا القسم. / L'utilisateur n'appartient pas à ce département.",
                )
                return redirect("/departement/admin/authentification/customuser/")

            # A03: Confirmation requise, modification uniquement via POST
            if request.method != "POST":
                context = {
                    "title": f"تأكيد إعادة تعيين كلمة المرور لـ {user.username}",
                    "user_obj": user,
                    "opts": self.model._meta,
                }
                return render(request, "admin/dep_admin/reset_password_confirm.html", context)

            # Générer le nouveau mot de passe
            new_password = generate_password(user.last_name, user.last_name, user.first_name, user.first_name)
            user.set_password(new_password)
            user.save(update_fields=["password"])

            messages.success(
                request,
                format_html(
                    "تم إعادة تعيين كلمة المرور للمستخدم <strong>{}</strong><br>"
                    '<span style="font-size: 14px; background: #1e293b; color: #fbbf24; padding: 8px 12px; '
                    'border-radius: 4px; font-family: monospace; display: inline-block; margin-top: 5px;">'
                    'كلمة المرور الجديدة: <strong style="color: #4ade80;">{}</strong></span>',
                    user.username,
                    new_password,
                ),
            )

        except CustomUser.DoesNotExist:
            messages.error(request, "المستخدم غير موجود.")

        return redirect("/departement/admin/authentification/customuser/")

    def set_password_view(self, request, user_id):
        """Vue pour définir un mot de passe personnalisé (A02, A05, A20)."""
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        try:
            user = CustomUser.objects.get(pk=user_id)

            # Vérifier que l'utilisateur appartient au département (A02)
            departement = self.get_departement(request)
            if not departement:
                messages.error(request, "لا يوجد قسم محدد.")
                return redirect("/departement/admin/authentification/customuser/")

            annee = self.get_annee_courante()
            allowed_ids = self.get_user_ids_for_department(departement, annee)
            if user.pk not in allowed_ids:
                messages.error(
                    request,
                    "المستخدم لا ينتمي إلى هذا القسم. / L'utilisateur n'appartient pas à ce département.",
                )
                return redirect("/departement/admin/authentification/customuser/")

            if request.method == "POST":
                new_password = request.POST.get("new_password", "").strip()
                confirm_password = request.POST.get("confirm_password", "").strip()

                if not new_password:
                    messages.error(request, "كلمة المرور مطلوبة / Le mot de passe est requis")
                elif new_password != confirm_password:
                    messages.error(request, "كلمتا المرور غير متطابقتين / Les mots de passe ne correspondent pas")
                else:
                    try:
                        # Validation selon les validateurs Django (A20)
                        validate_password(new_password, user)
                        user.set_password(new_password)
                        user.save(update_fields=["password"])
                        messages.success(
                            request,
                            format_html(
                                "تم تعيين كلمة المرور الجديدة للمستخدم <strong>{}</strong> بنجاح",
                                user.username,
                            ),
                        )
                        return redirect("/departement/admin/authentification/customuser/")
                    except ValidationError as e:
                        for err in e.messages:
                            messages.error(request, err)

            context = {
                "title": f"تعيين كلمة مرور جديدة لـ {user.username}",
                "user_obj": user,
                "opts": self.model._meta,
                "has_view_permission": True,
            }
            # Rendu via template Django sécurisé (A05)
            return render(request, "admin/dep_admin/set_password.html", context)

        except CustomUser.DoesNotExist:
            messages.error(request, "المستخدم غير موجود.")
            return redirect("/departement/admin/authentification/customuser/")

    def changelist_view(self, request, extra_context=None):
        """Ajoute un message si aucun département n'est sélectionné."""
        departement = self.get_departement(request)
        if not departement:
            messages.warning(
                request,
                "لم يتم تحديد قسم. يرجى تحديد قسمك من لوحة التحكم. / "
                "Aucun département sélectionné. Veuillez sélectionner votre département.",
            )
        return super().changelist_view(request, extra_context=extra_context)

    def get_user_ids_for_department(self, departement, annee=None):
        """Récupère les IDs des utilisateurs du département."""
        ens_ids = []
        if annee:
            ens_ids = list(
                Ens_Dep.objects.filter(
                    departement=departement, annee_univ=annee, enseignant__user__isnull=False
                ).values_list("enseignant__user_id", flat=True)
            )

        etu_ids = list(
            Etudiant.objects.filter(
                niv_spe_dep_sg__niv_spe_dep__departement=departement, user__isnull=False
            ).values_list("user_id", flat=True)
        )

        return list(set(ens_ids + etu_ids))

    def get_queryset(self, request):
        """
        Filtre les utilisateurs par département.
        Affiche uniquement les utilisateurs liés aux enseignants ou étudiants du département.
        """
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        annee = self.get_annee_courante()

        if not departement:
            return qs.none()

        all_user_ids = self.get_user_ids_for_department(departement, annee)

        if all_user_ids:
            return qs.filter(id__in=all_user_ids)
        return qs.none()

    def get_object(self, request, object_id, from_field=None):
        """
        Permet d'accéder aux détails d'un utilisateur du département.
        Vérifie que l'utilisateur appartient bien au département.
        """
        obj = super().get_object(request, object_id, from_field)
        if obj is None:
            return None

        # Vérifier que l'utilisateur appartient au département
        departement = self.get_departement(request)
        if departement:
            annee = self.get_annee_courante()
            allowed_ids = self.get_user_ids_for_department(departement, annee)
            if obj.pk in allowed_ids:
                return obj

        return None

    # ══════════════════════════════════════════════════════════
    # ACTIONS PERSONNALISÉES
    # ══════════════════════════════════════════════════════════

    @admin.action(description="إعادة تعيين كلمة المرور / Réinitialiser le mot de passe")
    def reset_password_action(self, request, queryset):
        """Réinitialise le mot de passe des utilisateurs sélectionnés."""
        from apps.academique.etudiant.utils import generate_password

        reset_count = 0
        for user in queryset:
            # Générer un nouveau mot de passe basé sur le nom
            new_password = generate_password(
                user.last_name,
                user.last_name,  # Fallback arabe
                user.first_name,
                user.first_name,  # Fallback arabe
            )
            user.set_password(new_password)
            user.save(update_fields=["password"])
            reset_count += 1

        messages.success(
            request,
            f"تم إعادة تعيين كلمة المرور لـ {reset_count} مستخدم(ين). "
            f"كلمة المرور الجديدة: ...XX123 (XX = أول حرفين من الاسم واللقب)",
        )

    reset_password_action.short_description = "إعادة تعيين كلمة المرور / Réinitialiser le mot de passe"

    @admin.action(description="تفعيل الحسابات / Activer les comptes")
    def activate_users(self, request, queryset):
        """Active les comptes sélectionnés."""
        updated = queryset.update(is_active=True)
        messages.success(request, f"تم تفعيل {updated} حساب(ات).")

    activate_users.short_description = "تفعيل الحسابات / Activer les comptes"

    @admin.action(description="تعطيل الحسابات / Désactiver les comptes")
    def deactivate_users(self, request, queryset):
        """Désactive les comptes sélectionnés."""
        # Ne pas désactiver son propre compte
        queryset = queryset.exclude(id=request.user.id)
        updated = queryset.update(is_active=False)
        messages.success(request, f"تم تعطيل {updated} حساب(ات).")

    deactivate_users.short_description = "تعطيل الحسابات / Désactiver les comptes"

    # Permissions gérées par PermissionCheckMixin

    def get_readonly_fields(self, request, obj=None):
        """
        Rend certains champs en lecture seule selon le contexte.
        """
        readonly = list(self.readonly_fields)
        if obj:
            # Ne peut pas changer le nom d'utilisateur ni les permissions superuser
            readonly.extend(["is_superuser", "is_staff", "user_permissions"])
        return readonly

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Filtre les groupes disponibles pour le chef de département."""
        if db_field.name == "groups":
            # Exclure les groupes admin/superuser
            kwargs["queryset"] = Group.objects.exclude(name__in=["Administrateurs", "Admin", "Superusers"])
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def action_buttons(self, obj):
        """Affiche les boutons d'action pour chaque utilisateur."""
        edit_url = f"/departement/admin/authentification/customuser/{obj.pk}/change/"
        return format_html(
            '<a class="button" href="{}" style="background-color: #417690; color: white; '
            'padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
            "✏️ تعديل / Modifier</a>",
            edit_url,
        )

    action_buttons.short_description = "الإجراءات / Actions"
    action_buttons.allow_tags = True


# ══════════════════════════════════════════════════════════════
# ADMIN CRUD - INFRASTRUCTURE (Amphi_Dep, Salle_Dep, Laboratoire_Dep)
# ══════════════════════════════════════════════════════════════


class AmphiDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des affectations amphithéâtres-département."""

    list_display = ("get_amphi_nom", "get_departement_nom", "semestre_1", "semestre_2", "est_actif", "action_buttons")
    list_filter = ("semestre_1", "semestre_2", "est_actif")
    search_fields = ("amphi__nom_ar", "amphi__nom_fr", "amphi__numero")

    fieldsets = (("المدرج / Amphithéâtre", {"fields": ("amphi", "semestre_1", "semestre_2", "est_actif")}),)

    def get_amphi_nom(self, obj):
        return f"{obj.amphi.numero} - {obj.amphi.nom_ar or obj.amphi.nom_fr or ''}"

    get_amphi_nom.short_description = "المدرج / Amphi"

    def get_departement_nom(self, obj):
        return obj.departement.nom_ar if obj.departement else "-"

    get_departement_nom.short_description = "القسم / Département"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "departement":
            departement = self.get_departement(request)
            if departement:
                kwargs["queryset"] = Departement.objects.filter(id=departement.id)
                kwargs["initial"] = departement
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.departement_id:
            obj.departement = self.get_departement(request)
        super().save_model(request, obj, form, change)

    # Permissions gérées par PermissionCheckMixin


class SalleDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des affectations salles-département."""

    list_display = ("get_salle_nom", "get_departement_nom", "semestre_1", "semestre_2", "est_actif", "action_buttons")
    list_filter = ("semestre_1", "semestre_2", "est_actif")
    search_fields = ("salle__nom_ar", "salle__nom_fr", "salle__numero")

    fieldsets = (("القاعة / Salle", {"fields": ("salle", "semestre_1", "semestre_2", "est_actif")}),)

    def get_salle_nom(self, obj):
        return f"{obj.salle.numero} - {obj.salle.nom_ar or obj.salle.nom_fr or ''}"

    get_salle_nom.short_description = "القاعة / Salle"

    def get_departement_nom(self, obj):
        return obj.departement.nom_ar if obj.departement else "-"

    get_departement_nom.short_description = "القسم / Département"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "departement":
            departement = self.get_departement(request)
            if departement:
                kwargs["queryset"] = Departement.objects.filter(id=departement.id)
                kwargs["initial"] = departement
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.departement_id:
            obj.departement = self.get_departement(request)
        super().save_model(request, obj, form, change)

    # Permissions gérées par PermissionCheckMixin


class LaboratoireDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des affectations laboratoires-département."""

    list_display = (
        "get_labo_nom",
        "get_labo_type",
        "get_departement_nom",
        "semestre_1",
        "semestre_2",
        "est_actif",
        "action_buttons",
    )
    list_filter = ("laboratoire__type", "semestre_1", "semestre_2", "est_actif")
    search_fields = ("laboratoire__nom_ar", "laboratoire__nom_fr", "laboratoire__numero")

    fieldsets = (("المخبر / Laboratoire", {"fields": ("laboratoire", "semestre_1", "semestre_2", "est_actif")}),)

    def get_labo_nom(self, obj):
        return f"{obj.laboratoire.numero} - {obj.laboratoire.nom_ar or obj.laboratoire.nom_fr or ''}"

    get_labo_nom.short_description = "المخبر / Labo"

    def get_labo_type(self, obj):
        return obj.laboratoire.get_type_display() if obj.laboratoire else "-"

    get_labo_type.short_description = "النوع / Type"

    def get_departement_nom(self, obj):
        return obj.departement.nom_ar if obj.departement else "-"

    get_departement_nom.short_description = "القسم / Département"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "departement":
            departement = self.get_departement(request)
            if departement:
                kwargs["queryset"] = Departement.objects.filter(id=departement.id)
                kwargs["initial"] = departement
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.departement_id:
            obj.departement = self.get_departement(request)
        super().save_model(request, obj, form, change)

    # Permissions gérées par PermissionCheckMixin


# ══════════════════════════════════════════════════════════════
# ADMIN CRUD - ENSEIGNEMENT (Classe, Seance, SousGroupe)
# ══════════════════════════════════════════════════════════════


class ClasseDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des classes/séances d'enseignement."""

    list_display = (
        "get_matiere",
        "get_enseignant",
        "get_groupe",
        "jour",
        "temps",
        "type",
        "get_taux_avancement",
        "action_buttons",
    )
    list_filter = ("semestre", "type", "jour")
    search_fields = (
        "matiere__nom_ar",
        "matiere__nom_fr",
        "enseignant__enseignant__nom_ar",
        "enseignant__enseignant__nom_fr",
    )

    fieldsets = (
        (
            "المعلومات الأساسية / Informations de base",
            {"fields": ("semestre", "matiere", "enseignant", "niv_spe_dep_sg")},
        ),
        ("التوقيت / Horaire", {"fields": ("jour", "temps", "type")}),
        ("المكان / Lieu", {"fields": ("content_type", "object_id"), "classes": ("collapse",)}),
        ("التقدم / Progression", {"fields": ("taux_avancement", "lien_moodle"), "classes": ("collapse",)}),
    )

    def get_matiere(self, obj):
        return obj.matiere.nom_ar if obj.matiere else "-"

    get_matiere.short_description = "المادة / Matière"

    def get_enseignant(self, obj):
        if obj.enseignant and obj.enseignant.enseignant:
            return obj.enseignant.enseignant.get_nom_complet("ar")
        return "-"

    get_enseignant.short_description = "الأستاذ / Enseignant"

    def get_groupe(self, obj):
        if obj.niv_spe_dep_sg:
            return str(obj.niv_spe_dep_sg)
        return "-"

    get_groupe.short_description = "الفوج / Groupe"

    def get_taux_avancement(self, obj):
        return f"{obj.taux_avancement}%"

    get_taux_avancement.short_description = "التقدم / Avancement"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(enseignant__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)
        annee = self.get_annee_courante()

        if db_field.name == "enseignant" and departement:
            qs = Ens_Dep.objects.filter(departement=departement, est_actif=True)
            if annee:
                qs = qs.filter(annee_univ=annee)
            kwargs["queryset"] = qs.select_related("enseignant")

        if db_field.name == "matiere" and departement:
            kwargs["queryset"] = Matiere.objects.filter(niv_spe_dep__departement=departement).select_related(
                "niv_spe_dep", "semestre"
            )

        if db_field.name == "niv_spe_dep_sg" and departement:
            kwargs["queryset"] = NivSpeDep_SG.objects.filter(niv_spe_dep__departement=departement).select_related(
                "niv_spe_dep", "section", "groupe"
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Permissions gérées par PermissionCheckMixin


class SeanceDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des séances."""

    list_display = ("get_classe", "intitule", "date", "temps", "fait", "get_audience", "action_buttons")
    list_filter = ("fait", "annuler", "remplacer", "type_audience")
    search_fields = ("intitule", "classe__matiere__nom_ar", "classe__matiere__nom_fr")
    date_hierarchy = "date"

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("classe", "intitule", "date", "temps")}),
        ("الحالة / État", {"fields": ("fait", "remplacer", "annuler")}),
        (
            "الجمهور / Audience",
            {"fields": ("type_audience", "sous_groupe_unique", "nb_etudiants_concernes"), "classes": ("collapse",)},
        ),
        ("ملاحظات / Observations", {"fields": ("obs",), "classes": ("collapse",)}),
    )

    def get_classe(self, obj):
        if obj.classe:
            return f"{obj.classe.matiere.nom_ar if obj.classe.matiere else ''} - {obj.classe.get_type_display()}"
        return "-"

    get_classe.short_description = "الحصة / Classe"

    def get_audience(self, obj):
        return obj.get_type_audience_display()

    get_audience.short_description = "الجمهور / Audience"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(classe__enseignant__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "classe" and departement:
            kwargs["queryset"] = Classe.objects.filter(enseignant__departement=departement).select_related(
                "matiere", "enseignant"
            )

        if db_field.name == "sous_groupe_unique" and departement:
            kwargs["queryset"] = SousGroupe.objects.filter(groupe_principal__niv_spe_dep__departement=departement)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Permissions gérées par PermissionCheckMixin


class SousGroupeDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des sous-groupes."""

    list_display = ("nom", "nom_complet", "get_groupe_principal", "effectif", "actif", "action_buttons")
    list_filter = ("actif",)
    search_fields = ("nom", "nom_complet", "description")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("groupe_principal", "nom", "nom_complet")}),
        ("التفاصيل / Détails", {"fields": ("description", "effectif", "ordre_affichage", "actif")}),
    )

    def get_groupe_principal(self, obj):
        return str(obj.groupe_principal) if obj.groupe_principal else "-"

    get_groupe_principal.short_description = "الفوج الرئيسي / Groupe principal"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(groupe_principal__niv_spe_dep__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "groupe_principal" and departement:
            kwargs["queryset"] = NivSpeDep_SG.objects.filter(niv_spe_dep__departement=departement).select_related(
                "niv_spe_dep", "section", "groupe"
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Permissions gérées par PermissionCheckMixin


# ══════════════════════════════════════════════════════════════
# ADMIN CRUD - SUIVI (Gestion_Etu_Classe, Abs_Etu_Seance, EtudiantSousGroupe)
# ══════════════════════════════════════════════════════════════


class GestionEtuClasseDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration de la gestion étudiants-classes."""

    list_display = (
        "get_etudiant",
        "get_classe",
        "nbr_absence",
        "note_finale",
        "validee_par_enseignant",
        "action_buttons",
    )
    list_filter = ("validee_par_enseignant", "classe__matiere")
    search_fields = ("etudiant__nom_ar", "etudiant__nom_fr", "etudiant__matricule", "classe__matiere__nom_ar")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("classe", "etudiant")}),
        ("الغيابات / Absences", {"fields": ("nbr_absence", "nbr_absence_justifiee", "nbr_seances_totales")}),
        (
            "النقاط / Notes",
            {"fields": ("note_presence", "note_participe_HW", "note_controle_1", "note_controle_2", "note_finale")},
        ),
        ("التحقق / Validation", {"fields": ("validee_par_enseignant", "date_validation"), "classes": ("collapse",)}),
    )

    readonly_fields = ("date_derniere_maj",)

    def get_etudiant(self, obj):
        if obj.etudiant:
            return f"{obj.etudiant.matricule} - {obj.etudiant.nom_ar or obj.etudiant.nom_fr}"
        return "-"

    get_etudiant.short_description = "الطالب / Étudiant"

    def get_classe(self, obj):
        if obj.classe and obj.classe.matiere:
            return obj.classe.matiere.nom_ar
        return "-"

    get_classe.short_description = "الحصة / Classe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(classe__enseignant__departement=departement)
        return qs.none()

    # Permissions gérées par PermissionCheckMixin


class AbsEtuSeanceDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des absences étudiants par séance."""

    list_display = ("get_etudiant", "get_seance", "present", "justifiee", "participation", "action_buttons")
    list_filter = ("present", "justifiee", "participation")
    search_fields = ("etudiant__nom_ar", "etudiant__nom_fr", "etudiant__matricule")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("seance", "etudiant")}),
        ("الحضور / Présence", {"fields": ("present", "justifiee", "participation", "points_sup_seance")}),
        ("ملاحظات / Observations", {"fields": ("obs",), "classes": ("collapse",)}),
    )

    def get_etudiant(self, obj):
        if obj.etudiant:
            return f"{obj.etudiant.matricule} - {obj.etudiant.nom_ar or obj.etudiant.nom_fr}"
        return "-"

    get_etudiant.short_description = "الطالب / Étudiant"

    def get_seance(self, obj):
        if obj.seance:
            return f"{obj.seance.date} - {obj.seance.intitule or ''}"
        return "-"

    get_seance.short_description = "الحصة / Séance"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(seance__classe__enseignant__departement=departement)
        return qs.none()

    # Permissions gérées par PermissionCheckMixin


class EtudiantSousGroupeDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des affectations étudiants-sous-groupes."""

    list_display = ("get_etudiant", "get_sous_groupe", "date_affectation", "actif", "action_buttons")
    list_filter = ("actif", "sous_groupe")
    search_fields = ("etudiant__nom_ar", "etudiant__nom_fr", "etudiant__matricule", "sous_groupe__nom")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("etudiant", "sous_groupe")}),
        ("التفاصيل / Détails", {"fields": ("ordre_dans_groupe", "actif")}),
    )

    def get_etudiant(self, obj):
        if obj.etudiant:
            return f"{obj.etudiant.matricule} - {obj.etudiant.nom_ar or obj.etudiant.nom_fr}"
        return "-"

    get_etudiant.short_description = "الطالب / Étudiant"

    def get_sous_groupe(self, obj):
        return obj.sous_groupe.nom if obj.sous_groupe else "-"

    get_sous_groupe.short_description = "الفوج الفرعي / Sous-groupe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(sous_groupe__groupe_principal__niv_spe_dep__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "sous_groupe" and departement:
            kwargs["queryset"] = SousGroupe.objects.filter(groupe_principal__niv_spe_dep__departement=departement)

        if db_field.name == "etudiant" and departement:
            kwargs["queryset"] = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep__departement=departement)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Permissions gérées par PermissionCheckMixin


# ══════════════════════════════════════════════════════════════
# ADMIN CRUD - STRUCTURE (NivSpeDep, NivSpeDep_SG, Specialite)
# ══════════════════════════════════════════════════════════════


class NivSpeDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des niveaux-spécialités par département."""

    list_display = (
        "get_niveau",
        "get_specialite",
        "nbr_matieres_s1",
        "nbr_matieres_s2",
        "nbr_etudiants",
        "action_buttons",
    )
    list_filter = ("niveau", "specialite")
    search_fields = ("niveau__nom_ar", "niveau__nom_fr", "specialite__nom_ar", "specialite__nom_fr")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("niveau", "specialite")}),
        (
            "الإحصائيات / Statistiques",
            {"fields": ("nbr_matieres_s1", "nbr_matieres_s2", "nbr_etudiants"), "classes": ("collapse",)},
        ),
    )

    def get_niveau(self, obj):
        return obj.niveau.nom_ar if obj.niveau else "-"

    get_niveau.short_description = "المستوى / Niveau"

    def get_specialite(self, obj):
        return obj.specialite.nom_ar if obj.specialite else "-"

    get_specialite.short_description = "التخصص / Spécialité"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "departement" and departement:
            kwargs["queryset"] = Departement.objects.filter(id=departement.id)
            kwargs["initial"] = departement

        if db_field.name == "specialite" and departement:
            kwargs["queryset"] = Specialite.objects.filter(departement=departement)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.departement_id:
            obj.departement = self.get_departement(request)
        super().save_model(request, obj, form, change)

    # Permissions gérées par PermissionCheckMixin


class NivSpeDepSGAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des groupes par niveau-spécialité."""

    list_display = (
        "get_niv_spe",
        "get_section",
        "get_groupe",
        "type_affectation",
        "nbr_etudiants_SG",
        "action_buttons",
    )
    list_filter = ("type_affectation", "niv_spe_dep__niveau", "section", "groupe")
    search_fields = ("niv_spe_dep__niveau__nom_ar", "niv_spe_dep__specialite__nom_ar")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("niv_spe_dep", "type_affectation")}),
        ("القسم والفوج / Section et Groupe", {"fields": ("section", "groupe", "nbr_etudiants_SG")}),
    )

    def get_niv_spe(self, obj):
        if obj.niv_spe_dep:
            return f"{obj.niv_spe_dep.niveau.nom_ar if obj.niv_spe_dep.niveau else ''} - {obj.niv_spe_dep.specialite.nom_ar if obj.niv_spe_dep.specialite else ''}"
        return "-"

    get_niv_spe.short_description = "المستوى-التخصص / Niv-Spé"

    def get_section(self, obj):
        return obj.section.nom_ar if obj.section else "-"

    get_section.short_description = "القسم / Section"

    def get_groupe(self, obj):
        return obj.groupe.nom_ar if obj.groupe else "-"

    get_groupe.short_description = "الفوج / Groupe"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(niv_spe_dep__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "niv_spe_dep" and departement:
            kwargs["queryset"] = NivSpeDep.objects.filter(departement=departement).select_related(
                "niveau", "specialite"
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Permissions gérées par PermissionCheckMixin


class SpecialiteDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des spécialités du département."""

    resource_class = SpecialiteResource

    list_display = ("code", "nom_ar", "nom_fr", "get_reforme", "get_parcours", "action_buttons")
    list_filter = ("reforme", "parcours")
    search_fields = ("code", "nom_ar", "nom_fr")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("code", ("nom_ar", "nom_fr"))}),
        ("التصنيف / Classification", {"fields": ("reforme", "identification", "parcours")}),
    )

    def get_reforme(self, obj):
        return obj.reforme.nom_ar if obj.reforme else "-"

    get_reforme.short_description = "الإصلاح / Réforme"

    def get_parcours(self, obj):
        return obj.parcours.nom_ar if obj.parcours else "-"

    get_parcours.short_description = "المسار / Parcours"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "departement" and departement:
            kwargs["queryset"] = Departement.objects.filter(id=departement.id)
            kwargs["initial"] = departement

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.departement_id:
            obj.departement = self.get_departement(request)
        super().save_model(request, obj, form, change)

    # Permissions gérées par PermissionCheckMixin


class MatiereAdminForDep(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des matières dans l'admin département."""

    resource_class = MatiereResource

    list_display = ("code", "nom_ar", "nom_fr", "get_niveau_spe", "semestre", "coeff", "credit", "action_buttons")
    list_filter = ("semestre", "niv_spe_dep__niveau", "unite")
    search_fields = ("code", "nom_ar", "nom_fr")

    fieldsets = (
        ("المعلومات الأساسية / Informations de base", {"fields": ("code", ("nom_ar", "nom_fr"))}),
        ("الانتماء / Rattachement", {"fields": ("niv_spe_dep", "semestre", "unite")}),
        ("المعاملات / Coefficients", {"fields": (("coeff", "credit"),)}),
    )

    def get_niveau_spe(self, obj):
        if obj.niv_spe_dep:
            return f"{obj.niv_spe_dep.niveau.nom_ar if obj.niv_spe_dep.niveau else ''} - {obj.niv_spe_dep.specialite.nom_ar if obj.niv_spe_dep.specialite else ''}"
        return "-"

    get_niveau_spe.short_description = "المستوى-التخصص / Niv-Spé"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(niv_spe_dep__departement=departement)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "niv_spe_dep" and departement:
            kwargs["queryset"] = NivSpeDep.objects.filter(departement=departement).select_related(
                "niveau", "specialite"
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Permissions gérées par PermissionCheckMixin


# ══════════════════════════════════════════════════════════════
# ADMIN CRUD - AFFECTATION POSTE
# ══════════════════════════════════════════════════════════════


class AffectationPosteDepAdmin(PermissionCheckMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Administration des affectations de postes pour le département."""

    list_display = ("get_user", "get_poste", "get_annee", "date_debut", "date_fin", "est_actif", "action_buttons")
    list_filter = ("est_actif", "poste", "annee_univ")
    search_fields = ("user__username", "user__first_name", "user__last_name", "poste__nom_ar", "poste__nom_fr")

    fieldsets = (
        ("المستخدم والمنصب / Utilisateur et Poste", {"fields": ("user", "poste")}),
        ("الفترة / Période", {"fields": ("annee_univ", ("date_debut", "date_fin"), "est_actif")}),
        ("ملاحظات / Observations", {"fields": ("observation",), "classes": ("collapse",)}),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Retourne un formulaire qui pré-remplit le département."""
        form = super().get_form(request, obj, **kwargs)
        departement = self.get_departement(request)

        class AffectationPosteDepForm(form):
            def __init__(self, *args, **inner_kwargs):
                super().__init__(*args, **inner_kwargs)
                # Pour les nouveaux objets, pré-remplir le département
                if not self.instance.pk and departement:
                    self.instance.departement = departement
                    self.instance.niveau_contexte = "departement"

        return AffectationPosteDepForm

    def get_user(self, obj):
        if obj.user:
            return f"{obj.user.last_name} {obj.user.first_name}"
        return "-"

    get_user.short_description = "المستخدم / Utilisateur"

    def get_poste(self, obj):
        return obj.poste.nom_ar if obj.poste else "-"

    get_poste.short_description = "المنصب / Poste"

    def get_annee(self, obj):
        return obj.annee_univ.nom if obj.annee_univ else "-"

    get_annee.short_description = "السنة / Année"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(departement=departement, niveau_contexte="departement")
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        departement = self.get_departement(request)

        if db_field.name == "departement" and departement:
            kwargs["queryset"] = Departement.objects.filter(id=departement.id)
            kwargs["initial"] = departement

        if db_field.name == "poste":
            kwargs["queryset"] = Poste.objects.filter(type__in=["enseignant", "admin"]).order_by("niveau", "nom_ar")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.niveau_contexte = "departement"
            if not obj.departement_id:
                obj.departement = self.get_departement(request)
        super().save_model(request, obj, form, change)

    # Permissions gérées par PermissionCheckMixin


# ══════════════════════════════════════════════════════════════
# ADMIN LECTURE SEULE - DONNÉES DE RÉFÉRENCE
# ══════════════════════════════════════════════════════════════


class DepartementReadOnlyAdmin(ReadOnlyAdminMixin, DepartementFilterMixin, admin.ModelAdmin):
    """Vue lecture seule du département actuel."""

    list_display = ("code", "nom_ar", "nom_fr", "sigle", "get_faculte", "action_buttons")
    list_display_links = None  # Désactiver les liens par défaut
    search_fields = ("code", "nom_ar", "nom_fr", "sigle")
    exclude = ("creationALLseances",)  # Cacher ce champ

    def get_faculte(self, obj):
        return obj.faculte.nom_ar if obj.faculte else "-"

    get_faculte.short_description = "الكلية / Faculté"

    def changelist_view(self, request, extra_context=None):
        """Mémorise la requête dans un contextvar pour l'utiliser dans action_buttons (A17)."""
        _admin_request_var.set(request)
        return super().changelist_view(request, extra_context)

    def action_buttons(self, obj):
        """Génère les liens d'action selon les permissions."""
        req = _admin_request_var.get()
        if req:
            perms = PostePermission.get_permissions(req)
            has_change = perms.get("departement_change", False)
        else:
            has_change = False

        if has_change:
            return format_html(
                '<a href="/departement/admin/departement/departement/{}/change/" '
                'class="button" style="padding: 4px 8px; background: #417690; color: white; '
                'text-decoration: none; border-radius: 4px;">تعديل / Modifier</a>',
                obj.pk,
            )
        else:
            return format_html('<span style="color: #6c757d; font-size: 12px;">عرض فقط / Lecture seule</span>')

    action_buttons.short_description = "الإجراءات / Actions"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        if departement:
            return qs.filter(id=departement.id)
        return qs.none()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Surcharge pour s'assurer que le formulaire poste vers la bonne URL."""
        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = True
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        """Redirige vers la bonne URL après enregistrement."""
        from django.http import HttpResponseRedirect

        if "_continue" in request.POST:
            return HttpResponseRedirect(f"/departement/admin/departement/departement/{obj.pk}/change/")
        return HttpResponseRedirect("/departement/admin/departement/departement/")


class FaculteReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Vue lecture seule des facultés."""

    list_display = ("code", "nom_ar", "nom_fr", "sigle", "get_universite")
    search_fields = ("code", "nom_ar", "nom_fr", "sigle")

    def get_universite(self, obj):
        return obj.universite.nom_ar if obj.universite else "-"

    get_universite.short_description = "الجامعة / Université"


class UniversiteReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Vue lecture seule des universités."""

    list_display = ("code", "nom_ar", "nom_fr", "sigle", "get_wilaya")
    search_fields = ("code", "nom_ar", "nom_fr", "sigle")

    def get_wilaya(self, obj):
        return obj.wilaya.nom_ar if obj.wilaya else "-"

    get_wilaya.short_description = "الولاية / Wilaya"


class DomaineReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Vue lecture seule des domaines."""

    list_display = ("code", "nom_ar", "nom_fr", "get_universite")
    search_fields = ("code", "nom_ar", "nom_fr")

    def get_universite(self, obj):
        return obj.universite.nom_ar if obj.universite else "-"

    get_universite.short_description = "الجامعة / Université"


class FiliereReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Vue lecture seule des filières."""

    list_display = ("code", "nom_ar", "nom_fr", "get_domaine")
    search_fields = ("code", "nom_ar", "nom_fr")

    def get_domaine(self, obj):
        return obj.domaine.nom_ar if obj.domaine else "-"

    get_domaine.short_description = "الميدان / Domaine"


# Données de référence communes
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
    list_display = ("numero", "code", "nom_ar", "nom_fr", "date_debut", "date_fin")
    search_fields = ("code", "nom_ar", "nom_fr")


class SessionReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr")
    search_fields = ("code", "nom_ar", "nom_fr")


class ReformeReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "nom_ar", "nom_fr", "get_cycle")
    search_fields = ("code", "nom_ar", "nom_fr")

    def get_cycle(self, obj):
        return obj.cycle.nom_ar if obj.cycle else "-"

    get_cycle.short_description = "الطور / Cycle"


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
    list_display = ("code", "codePostal", "nom_ar", "nom_fr", "get_pays")
    search_fields = ("code", "nom_ar", "nom_fr")

    def get_pays(self, obj):
        return obj.pays.nom_ar if obj.pays else "-"

    get_pays.short_description = "البلد / Pays"


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
