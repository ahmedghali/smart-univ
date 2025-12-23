# apps/academique/departement/dep_admin.py

"""
Interface d'administration personnalisée pour le Chef de Département.
Permet uniquement l'ajout d'enseignants et d'étudiants dans son propre département.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import Group
from django.db.models import Q

from apps.academique.enseignant.models import Enseignant
from apps.academique.etudiant.models import Etudiant
from apps.academique.affectation.models import Ens_Dep
from apps.academique.departement.models import Departement, NivSpeDep_SG
from apps.noyau.commun.models import AnneeUniversitaire
from apps.noyau.authentification.models import CustomUser


# ══════════════════════════════════════════════════════════════
# SITE D'ADMINISTRATION PERSONNALISÉ POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class DepAdminSite(AdminSite):
    """
    Site d'administration personnalisé pour le chef de département.
    Accès limité à l'ajout d'enseignants et d'étudiants.
    """
    site_header = "إدارة القسم"
    site_title = "لوحة تحكم رئيس القسم"
    index_title = "إدارة الأساتذة والطلبة"
    login_template = None  # Utilise le template par défaut

    def has_permission(self, request):
        """
        Vérifie si l'utilisateur a accès à cette interface admin.
        Ne nécessite PAS is_staff - accessible aux chefs de département.
        """
        if not request.user.is_authenticated:
            return False

        # Vérifier si l'utilisateur a un département sélectionné en session
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            return False

        # Vérifier si l'utilisateur est enseignant
        if not hasattr(request.user, 'enseignant_profile') or not request.user.enseignant_profile:
            return False

        # DEBUG: Temporairement autoriser tous les enseignants avec un département
        # TODO: Remettre la vérification chef_departement après les tests
        return True

        # Vérifier si l'utilisateur est chef de département ou a le droit
        # Option 1: Vérifier via le poste
        user = request.user
        is_chef_dep = False

        # Vérifier poste_principal
        if hasattr(user, 'poste_principal') and user.poste_principal:
            if user.poste_principal.code in ['chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg']:
                is_chef_dep = True

        # Vérifier postes_secondaires
        if not is_chef_dep and hasattr(user, 'postes_secondaires'):
            if user.postes_secondaires.filter(
                code__in=['chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg']
            ).exists():
                is_chef_dep = True

        # Option 2: Vérifier via le département (si l'enseignant est chef de ce département)
        if not is_chef_dep:
            try:
                dep = Departement.objects.get(id=departement_id)
                enseignant = user.enseignant_profile
                if dep.chef_departement == enseignant or \
                   dep.chef_dep_adj_p == enseignant or \
                   dep.chef_dep_adj_pg == enseignant:
                    is_chef_dep = True
            except Departement.DoesNotExist:
                pass

        return is_chef_dep

    def get_app_list(self, request, app_label=None):
        """Personnalise la liste des applications affichées."""
        app_list = super().get_app_list(request, app_label)
        return app_list

    def login(self, request, extra_context=None):
        """Redirige vers la page de login principale si non connecté."""
        if request.user.is_authenticated:
            if self.has_permission(request):
                return redirect('dep_admin:index')
            else:
                # L'utilisateur est connecté mais n'a pas les permissions
                messages.error(request, 'ليس لديك صلاحية الدخول إلى هذه الصفحة.')
                return redirect('depa:dashboard_Dep')
        # Rediriger vers la page de login principale
        return redirect('auth:login')


# Créer l'instance du site admin personnalisé
dep_admin_site = DepAdminSite(name='dep_admin')


# ══════════════════════════════════════════════════════════════
# MIXIN POUR FILTRER PAR DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class DepartementFilterMixin:
    """Mixin pour filtrer les données par département de l'utilisateur."""

    def get_departement(self, request):
        """Récupère le département de l'utilisateur depuis la session."""
        departement_id = request.session.get('selected_departement_id')
        if departement_id:
            try:
                return Departement.objects.get(id=departement_id)
            except Departement.DoesNotExist:
                return None
        return None

    def get_annee_courante(self):
        """Récupère l'année universitaire courante."""
        try:
            return AnneeUniversitaire.objects.get(est_courante=True)
        except AnneeUniversitaire.DoesNotExist:
            return None


# ══════════════════════════════════════════════════════════════
# ADMIN ENSEIGNANT POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class EnseignantDepAdmin(DepartementFilterMixin, admin.ModelAdmin):
    """
    Administration des enseignants pour le chef de département.
    Permet uniquement l'ajout de nouveaux enseignants.
    """

    list_display = (
        'matricule',
        'get_nom_complet',
        'grade',
        'email_prof',
        'get_statut_inscription',
    )

    list_filter = (
        'grade',
        'sex',
        'est_inscrit',
    )

    search_fields = (
        'matricule',
        'nom_ar',
        'prenom_ar',
        'nom_fr',
        'prenom_fr',
        'email_prof',
    )

    readonly_fields = (
        'matricule',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('المعلومات الشخصية / Informations personnelles', {
            'fields': (
                'civilite',
                ('nom_ar', 'prenom_ar'),
                ('nom_fr', 'prenom_fr'),
                ('sex', 'sitfam'),
                'date_nais',
            )
        }),
        ('المعلومات المهنية / Informations professionnelles', {
            'fields': (
                'matricule',
                'grade',
                ('specialite_ar', 'specialite_fr'),
                'diplome',
                'date_Recrut',
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                ('email_prof', 'email_perso'),
                ('telmobile1', 'telmobile2'),
                ('telfix', 'fax'),
                'adresse',
                'wilaya',
            )
        }),
        ('المنصات الأكاديمية / Plateformes académiques', {
            'fields': (
                ('inscritProgres', 'inscritMoodle', 'inscritSNDL'),
            ),
            'classes': ('collapse',),
        }),
        ('الشبكات الأكاديمية / Réseaux académiques', {
            'fields': (
                'googlescholar',
                'researchgate',
                'orcid_id',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_nom_complet(self, obj):
        """Affiche le nom complet de l'enseignant."""
        return f"{obj.nom_ar or obj.nom_fr} {obj.prenom_ar or obj.prenom_fr}"
    get_nom_complet.short_description = "الاسم الكامل"

    def get_statut_inscription(self, obj):
        """Affiche le statut d'inscription."""
        if obj.est_inscrit:
            return format_html('<span style="color: green;">✓ مسجل</span>')
        return format_html('<span style="color: red;">✗ غير مسجل</span>')
    get_statut_inscription.short_description = "حالة التسجيل"

    def get_queryset(self, request):
        """Filtre les enseignants par département."""
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        annee = self.get_annee_courante()

        if departement and annee:
            # Récupérer les IDs des enseignants affectés à ce département
            ens_ids = Ens_Dep.objects.filter(
                departement=departement,
                annee_univ=annee
            ).values_list('enseignant_id', flat=True)
            return qs.filter(id__in=ens_ids)
        return qs.none()

    def has_module_permission(self, request):
        """Permet d'afficher le module dans l'admin."""
        return True

    def has_add_permission(self, request):
        """Le chef de département peut ajouter des enseignants."""
        return True

    def has_change_permission(self, request, obj=None):
        """Le chef de département ne peut pas modifier les enseignants."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Le chef de département ne peut pas supprimer les enseignants."""
        return False

    def has_view_permission(self, request, obj=None):
        """Le chef de département peut voir les enseignants de son département."""
        return True

    def save_model(self, request, obj, form, change):
        """
        Après la sauvegarde, créer automatiquement l'affectation Ens_Dep.
        """
        super().save_model(request, obj, form, change)

        if not change:  # Seulement pour les nouveaux enseignants
            departement = self.get_departement(request)
            annee = self.get_annee_courante()

            if departement and annee:
                # Créer l'affectation au département
                Ens_Dep.objects.get_or_create(
                    enseignant=obj,
                    departement=departement,
                    annee_univ=annee,
                    defaults={
                        'statut': 'Vacataire',
                        'est_actif': True,
                        'semestre_1': True,
                        'semestre_2': True,
                    }
                )
                messages.success(
                    request,
                    f'تم إضافة الأستاذ "{obj}" وربطه بالقسم بنجاح.'
                )


# ══════════════════════════════════════════════════════════════
# ADMIN ETUDIANT POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class EtudiantDepAdmin(DepartementFilterMixin, admin.ModelAdmin):
    """
    Administration des étudiants pour le chef de département.
    Permet uniquement l'ajout de nouveaux étudiants.
    """

    list_display = (
        'matricule',
        'num_ins',
        'get_nom_complet',
        'get_niveau_info',
        'get_statut_actif',
    )

    list_filter = (
        'sexe',
        'delegue',
        'est_actif',
        'niv_spe_dep_sg__niv_spe_dep__niveau',
    )

    search_fields = (
        'matricule',
        'num_ins',
        'nom_ar',
        'prenom_ar',
        'nom_fr',
        'prenom_fr',
        'email_prof',
    )

    readonly_fields = (
        'matricule',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('المعلومات الشخصية / Informations personnelles', {
            'fields': (
                'civilite',
                ('nom_ar', 'prenom_ar'),
                ('nom_fr', 'prenom_fr'),
                ('sexe', 'sit_fam'),
                'date_nais',
            )
        }),
        ('المعلومات الأكاديمية / Informations académiques', {
            'fields': (
                'matricule',
                'num_ins',
                'niv_spe_dep_sg',
                'bac_annee',
                'delegue',
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                ('email_prof', 'email_perso'),
                ('tel_mobile1', 'tel_mobile2'),
                ('tel_fix', 'fax'),
                'adresse',
                'wilaya',
            )
        }),
        ('المنصات الأكاديمية / Plateformes académiques', {
            'fields': (
                ('inscrit_progres', 'inscrit_moodle', 'inscrit_sndl'),
            ),
            'classes': ('collapse',),
        }),
        ('الحالة / Statut', {
            'fields': (
                'est_actif',
                ('en_vac_aca', 'en_maladie'),
            )
        }),
    )

    def get_nom_complet(self, obj):
        """Affiche le nom complet de l'étudiant."""
        return f"{obj.nom_ar or obj.nom_fr} {obj.prenom_ar or obj.prenom_fr}"
    get_nom_complet.short_description = "الاسم الكامل"

    def get_niveau_info(self, obj):
        """Affiche le niveau de l'étudiant."""
        if obj.niv_spe_dep_sg and obj.niv_spe_dep_sg.niv_spe_dep:
            nsd = obj.niv_spe_dep_sg.niv_spe_dep
            niveau = nsd.niveau.nom_ar if nsd.niveau else ""
            specialite = nsd.specialite.nom_ar if nsd.specialite else ""
            return f"{niveau} - {specialite}"
        return "-"
    get_niveau_info.short_description = "المستوى والتخصص"

    def get_statut_actif(self, obj):
        """Affiche le statut actif."""
        if obj.est_actif:
            return format_html('<span style="color: green;">✓ نشط</span>')
        return format_html('<span style="color: red;">✗ غير نشط</span>')
    get_statut_actif.short_description = "الحالة"

    def get_queryset(self, request):
        """Filtre les étudiants par département."""
        qs = super().get_queryset(request)
        departement = self.get_departement(request)

        if departement:
            # Filtrer les étudiants dont le NivSpeDep_SG appartient au département
            return qs.filter(
                niv_spe_dep_sg__niv_spe_dep__departement=departement
            )
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtre les choix de NivSpeDep_SG selon le département."""
        if db_field.name == "niv_spe_dep_sg":
            departement = self.get_departement(request)
            if departement:
                kwargs["queryset"] = NivSpeDep_SG.objects.filter(
                    niv_spe_dep__departement=departement
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        """Permet d'afficher le module dans l'admin."""
        return True

    def has_add_permission(self, request):
        """Le chef de département peut ajouter des étudiants."""
        return True

    def has_change_permission(self, request, obj=None):
        """Le chef de département ne peut pas modifier les étudiants."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Le chef de département ne peut pas supprimer les étudiants."""
        return False

    def has_view_permission(self, request, obj=None):
        """Le chef de département peut voir les étudiants de son département."""
        return True

    def save_model(self, request, obj, form, change):
        """Message de succès après la sauvegarde."""
        super().save_model(request, obj, form, change)

        if not change:
            messages.success(
                request,
                f'تم إضافة الطالب "{obj}" بنجاح.'
            )


# ══════════════════════════════════════════════════════════════
# ADMIN AFFECTATION (ENS_DEP) POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class EnsDep_DepAdmin(DepartementFilterMixin, admin.ModelAdmin):
    """
    Administration des affectations enseignant-département.
    Permet au chef de département de gérer les affectations.
    """

    list_display = (
        'enseignant',
        'statut',
        'get_semestres',
        'est_actif',
        'date_affectation',
    )

    list_filter = (
        'statut',
        'semestre_1',
        'semestre_2',
        'est_actif',
    )

    search_fields = (
        'enseignant__nom_ar',
        'enseignant__prenom_ar',
        'enseignant__nom_fr',
        'enseignant__prenom_fr',
        'enseignant__matricule',
    )

    readonly_fields = (
        'departement',
        'annee_univ',
    )

    fieldsets = (
        ('معلومات الانتماء / Informations d\'affectation', {
            'fields': (
                'enseignant',
                'departement',
                'annee_univ',
                'date_affectation',
                'statut',
            )
        }),
        ('السداسيات / Semestres', {
            'fields': (
                ('semestre_1', 'semestre_2'),
            )
        }),
        ('الحالة / Statut', {
            'fields': (
                'est_actif',
            )
        }),
    )

    def get_semestres(self, obj):
        """Affiche les semestres actifs."""
        semestres = []
        if obj.semestre_1:
            semestres.append("S1")
        if obj.semestre_2:
            semestres.append("S2")
        return ", ".join(semestres) if semestres else "-"
    get_semestres.short_description = "السداسيات"

    def get_queryset(self, request):
        """Filtre les affectations par département."""
        qs = super().get_queryset(request)
        departement = self.get_departement(request)
        annee = self.get_annee_courante()

        if departement and annee:
            return qs.filter(departement=departement, annee_univ=annee)
        return qs.none()

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

    def has_module_permission(self, request):
        """Permet d'afficher le module dans l'admin."""
        return True

    def has_add_permission(self, request):
        """Le chef de département peut ajouter des affectations."""
        return True

    def has_change_permission(self, request, obj=None):
        """Le chef de département peut modifier les affectations de son département."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Le chef de département ne peut pas supprimer les affectations."""
        return False

    def has_view_permission(self, request, obj=None):
        """Le chef de département peut voir les affectations de son département."""
        return True

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
            messages.success(
                request,
                f'تم ربط الأستاذ "{obj.enseignant}" بالقسم بنجاح.'
            )


# ══════════════════════════════════════════════════════════════
# ADMIN UTILISATEURS POUR LE DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class UserDepAdmin(DepartementFilterMixin, admin.ModelAdmin):
    """
    Administration des utilisateurs pour le chef de département.
    Permet de gérer les comptes des enseignants et étudiants du département.
    """

    list_display = (
        'username',
        'get_nom_complet',
        'get_type_utilisateur',
        'get_poste',
        'is_active',
        'last_login',
        'get_reset_password_button',
    )

    # Rendre le username cliquable pour accéder à la page de modification
    list_display_links = ('username',)

    list_filter = (
        'is_active',
        'poste_principal',
        'groups',
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    readonly_fields = (
        'last_login',
        'date_joined',
        'get_password_change_link',
    )

    # Actions personnalisées
    actions = [
        'reset_password_action',
        'activate_users',
        'deactivate_users',
    ]

    fieldsets = (
        ('معلومات الحساب / Informations du compte', {
            'fields': (
                'username',
                'is_active',
            )
        }),
        ('كلمة المرور / Mot de passe', {
            'fields': (
                'get_password_change_link',
            ),
            'description': 'Cliquez sur le bouton pour réinitialiser le mot de passe'
        }),
        ('المعلومات الشخصية / Informations personnelles', {
            'fields': (
                'first_name',
                'last_name',
                'email',
            )
        }),
        ('المجموعات / Groupes', {
            'fields': (
                'groups',
            )
        }),
        ('التدقيق / Audit', {
            'fields': (
                'last_login',
                'date_joined',
            ),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['groups']

    def get_nom_complet(self, obj):
        """Affiche le nom complet."""
        return obj.nom_complet
    get_nom_complet.short_description = "الاسم الكامل / Nom"

    def get_type_utilisateur(self, obj):
        """Affiche le type d'utilisateur (Enseignant ou Étudiant)."""
        if hasattr(obj, 'enseignant_profile') and obj.enseignant_profile:
            return format_html('<span style="color: #2196F3;">أستاذ</span>')
        elif hasattr(obj, 'etudiant_profile') and obj.etudiant_profile:
            return format_html('<span style="color: #4CAF50;">طالب</span>')
        return format_html('<span style="color: #9E9E9E;">-</span>')
    get_type_utilisateur.short_description = "النوع / Type"

    def get_poste(self, obj):
        """Affiche le poste principal."""
        if obj.poste_principal:
            return obj.poste_principal.nom_ar or obj.poste_principal.nom_fr
        return "-"
    get_poste.short_description = "المنصب / Poste"

    def get_reset_password_button(self, obj):
        """Affiche un bouton pour réinitialiser le mot de passe."""
        url = f'/departement/admin/authentification/customuser/{obj.pk}/reset-password/'
        return format_html(
            '<a class="button" href="{}" style="background: #417690; color: white; '
            'padding: 3px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;">'
            'إعادة تعيين</a>',
            url
        )
    get_reset_password_button.short_description = "كلمة المرور"
    get_reset_password_button.allow_tags = True

    def get_password_change_link(self, obj):
        """Affiche les options de gestion du mot de passe dans le formulaire."""
        if obj and obj.pk:
            # Utiliser des URLs directes au lieu de reverse
            reset_url = f'/departement/admin/authentification/customuser/{obj.pk}/reset-password/'
            set_password_url = f'/departement/admin/authentification/customuser/{obj.pk}/set-password/'
            return format_html(
                '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
                '<a href="{}" style="background: linear-gradient(135deg, #f59e0b, #d97706); '
                'color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; '
                'font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">'
                '🔄 إعادة تعيين تلقائي / Réinitialiser auto</a>'
                '<a href="{}" style="background: linear-gradient(135deg, #3b82f6, #2563eb); '
                'color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; '
                'font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">'
                '🔑 تعيين كلمة مرور جديدة / Définir nouveau</a>'
                '</div>'
                '<div style="margin-top: 8px; font-size: 11px; color: #6b7280;">'
                '• إعادة تعيين تلقائي: كلمة المرور = أول حرفين من الاسم + أول حرفين من اللقب + 123<br>'
                '• Réinitialiser auto: Mot de passe = 2 premières lettres nom + prénom + 123'
                '</div>',
                reset_url,
                set_password_url
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
                '<int:user_id>/reset-password/',
                self.admin_site.admin_view(self.reset_password_view),
                name='user_reset_password',
            ),
            path(
                '<int:user_id>/set-password/',
                self.admin_site.admin_view(self.set_password_view),
                name='user_set_password',
            ),
        ]
        return custom_urls + urls

    def reset_password_view(self, request, user_id):
        """Vue pour réinitialiser le mot de passe d'un utilisateur (automatique)."""
        from apps.academique.etudiant.utils import generate_password

        try:
            user = CustomUser.objects.get(pk=user_id)

            # Vérifier que l'utilisateur appartient au département
            departement = self.get_departement(request)
            if not departement:
                messages.error(request, "لا يوجد قسم محدد.")
                return redirect('/departement/admin/authentification/customuser/')

            # Générer le nouveau mot de passe
            new_password = generate_password(
                user.last_name,
                user.last_name,
                user.first_name,
                user.first_name
            )
            user.set_password(new_password)
            user.save(update_fields=['password'])

            messages.success(
                request,
                format_html(
                    'تم إعادة تعيين كلمة المرور للمستخدم <strong>{}</strong><br>'
                    '<span style="font-size: 14px; background: #1e293b; color: #fbbf24; padding: 8px 12px; '
                    'border-radius: 4px; font-family: monospace; display: inline-block; margin-top: 5px;">'
                    'كلمة المرور الجديدة: <strong style="color: #4ade80;">{}</strong></span>',
                    user.username,
                    new_password
                )
            )

        except CustomUser.DoesNotExist:
            messages.error(request, "المستخدم غير موجود.")

        return redirect('/departement/admin/authentification/customuser/')

    def set_password_view(self, request, user_id):
        """Vue pour définir un mot de passe personnalisé."""
        from django.shortcuts import render

        try:
            user = CustomUser.objects.get(pk=user_id)

            # Vérifier que l'utilisateur appartient au département
            departement = self.get_departement(request)
            if not departement:
                messages.error(request, "لا يوجد قسم محدد.")
                return redirect('/departement/admin/authentification/customuser/')

            if request.method == 'POST':
                new_password = request.POST.get('new_password', '').strip()
                confirm_password = request.POST.get('confirm_password', '').strip()

                if not new_password:
                    messages.error(request, "كلمة المرور مطلوبة / Le mot de passe est requis")
                elif len(new_password) < 4:
                    messages.error(request, "كلمة المرور قصيرة جداً (4 أحرف على الأقل) / Mot de passe trop court (min 4 caractères)")
                elif new_password != confirm_password:
                    messages.error(request, "كلمتا المرور غير متطابقتين / Les mots de passe ne correspondent pas")
                else:
                    user.set_password(new_password)
                    user.save(update_fields=['password'])
                    messages.success(
                        request,
                        format_html(
                            'تم تعيين كلمة المرور الجديدة للمستخدم <strong>{}</strong> بنجاح',
                            user.username
                        )
                    )
                    return redirect('/departement/admin/authentification/customuser/')

            # Afficher le formulaire
            context = {
                'title': f'تعيين كلمة مرور جديدة لـ {user.username}',
                'user_obj': user,
                'opts': self.model._meta,
                'has_view_permission': True,
            }

            # Rendu HTML inline simple
            html_content = f'''
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>تعيين كلمة مرور جديدة</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                    .container {{ max-width: 500px; margin: 50px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                    h1 {{ color: #1e293b; font-size: 20px; margin-bottom: 10px; }}
                    .user-info {{ background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                    .user-info strong {{ color: #3b82f6; }}
                    label {{ display: block; margin-bottom: 5px; color: #475569; font-weight: 500; }}
                    input[type="password"] {{ width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 15px; font-size: 14px; box-sizing: border-box; }}
                    input[type="password"]:focus {{ outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }}
                    .btn {{ padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }}
                    .btn-primary {{ background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }}
                    .btn-secondary {{ background: #e2e8f0; color: #475569; margin-right: 10px; text-decoration: none; display: inline-block; }}
                    .buttons {{ display: flex; gap: 10px; margin-top: 20px; }}
                    .messages {{ margin-bottom: 15px; }}
                    .error {{ background: #fef2f2; color: #dc2626; padding: 10px; border-radius: 6px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔑 تعيين كلمة مرور جديدة</h1>
                    <div class="user-info">
                        <strong>👤 {user.nom_complet}</strong><br>
                        <span style="color: #64748b;">@{user.username}</span>
                    </div>
                    <form method="post">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get('CSRF_COOKIE', '')}">
                        <label>كلمة المرور الجديدة / Nouveau mot de passe</label>
                        <input type="password" name="new_password" required autofocus>
                        <label>تأكيد كلمة المرور / Confirmer le mot de passe</label>
                        <input type="password" name="confirm_password" required>
                        <div class="buttons">
                            <button type="submit" class="btn btn-primary">✓ حفظ / Enregistrer</button>
                            <a href="/departement/admin/authentification/customuser/" class="btn btn-secondary">✕ إلغاء / Annuler</a>
                        </div>
                    </form>
                </div>
            </body>
            </html>
            '''
            from django.http import HttpResponse
            from django.middleware.csrf import get_token
            # Get CSRF token
            csrf_token = get_token(request)
            html_content = html_content.replace(
                f'value="{request.META.get("CSRF_COOKIE", "")}"',
                f'value="{csrf_token}"'
            )
            return HttpResponse(html_content)

        except CustomUser.DoesNotExist:
            messages.error(request, "المستخدم غير موجود.")
            return redirect('/departement/admin/authentification/customuser/')

    def changelist_view(self, request, extra_context=None):
        """Ajoute un message si aucun département n'est sélectionné."""
        departement = self.get_departement(request)
        if not departement:
            messages.warning(
                request,
                "لم يتم تحديد قسم. يرجى تحديد قسمك من لوحة التحكم. / "
                "Aucun département sélectionné. Veuillez sélectionner votre département."
            )
        return super().changelist_view(request, extra_context=extra_context)

    def get_user_ids_for_department(self, departement, annee=None):
        """Récupère les IDs des utilisateurs du département."""
        ens_ids = []
        if annee:
            ens_ids = list(Ens_Dep.objects.filter(
                departement=departement,
                annee_univ=annee,
                enseignant__user__isnull=False
            ).values_list('enseignant__user_id', flat=True))

        etu_ids = list(Etudiant.objects.filter(
            niv_spe_dep_sg__niv_spe_dep__departement=departement,
            user__isnull=False
        ).values_list('user_id', flat=True))

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
                user.first_name  # Fallback arabe
            )
            user.set_password(new_password)
            user.save(update_fields=['password'])
            reset_count += 1

        messages.success(
            request,
            f'تم إعادة تعيين كلمة المرور لـ {reset_count} مستخدم(ين). '
            f'كلمة المرور الجديدة: ...XX123 (XX = أول حرفين من الاسم واللقب)'
        )
    reset_password_action.short_description = "إعادة تعيين كلمة المرور / Réinitialiser le mot de passe"

    @admin.action(description="تفعيل الحسابات / Activer les comptes")
    def activate_users(self, request, queryset):
        """Active les comptes sélectionnés."""
        updated = queryset.update(is_active=True)
        messages.success(request, f'تم تفعيل {updated} حساب(ات).')
    activate_users.short_description = "تفعيل الحسابات / Activer les comptes"

    @admin.action(description="تعطيل الحسابات / Désactiver les comptes")
    def deactivate_users(self, request, queryset):
        """Désactive les comptes sélectionnés."""
        # Ne pas désactiver son propre compte
        queryset = queryset.exclude(id=request.user.id)
        updated = queryset.update(is_active=False)
        messages.success(request, f'تم تعطيل {updated} حساب(ات).')
    deactivate_users.short_description = "تعطيل الحسابات / Désactiver les comptes"

    # ══════════════════════════════════════════════════════════
    # PERMISSIONS
    # ══════════════════════════════════════════════════════════

    def has_module_permission(self, request):
        """Permet d'afficher le module dans l'admin."""
        return True

    def has_add_permission(self, request):
        """Le chef de département ne peut pas créer des utilisateurs directement."""
        return False

    def has_change_permission(self, request, obj=None):
        """Le chef de département peut modifier les utilisateurs de son département."""
        if obj is None:
            return True
        # Ne peut pas modifier les superusers
        if obj.is_superuser:
            return False
        # Ne peut pas modifier son propre compte (sauf is_active)
        return True

    def has_delete_permission(self, request, obj=None):
        """Le chef de département ne peut pas supprimer les utilisateurs."""
        return False

    def has_view_permission(self, request, obj=None):
        """Le chef de département peut voir les utilisateurs de son département."""
        return True

    def get_readonly_fields(self, request, obj=None):
        """
        Rend certains champs en lecture seule selon le contexte.
        """
        readonly = list(self.readonly_fields)
        if obj:
            # Ne peut pas changer le nom d'utilisateur ni les permissions superuser
            readonly.extend(['is_superuser', 'is_staff', 'user_permissions'])
        return readonly

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Filtre les groupes disponibles pour le chef de département."""
        if db_field.name == "groups":
            # Exclure les groupes admin/superuser
            kwargs["queryset"] = Group.objects.exclude(
                name__in=['Administrateurs', 'Admin', 'Superusers']
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# ══════════════════════════════════════════════════════════════
# ENREGISTREMENT DES MODÈLES DANS L'ADMIN PERSONNALISÉ
# ══════════════════════════════════════════════════════════════

dep_admin_site.register(Enseignant, EnseignantDepAdmin)
dep_admin_site.register(Etudiant, EtudiantDepAdmin)
dep_admin_site.register(Ens_Dep, EnsDep_DepAdmin)
dep_admin_site.register(CustomUser, UserDepAdmin)
