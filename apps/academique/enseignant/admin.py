# apps/academique/enseignant/admin.py

from django.contrib import admin
from django.contrib import messages
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Enseignant
from .utils import create_user_for_enseignant
from apps.academique.affectation.models import Ens_Dep


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class EnseignantResource(resources.ModelResource):
    """Resource pour l'import/export Excel des enseignants."""

    class Meta:
        model = Enseignant
        fields = (
            'id', 'user', 'civilite', 'nom_ar', 'prenom_ar', 'nom_fr', 'prenom_fr',
            'date_nais', 'sex', 'sitfam',
            'matricule', 'codeIns', 'bac_annee', 'date_Recrut',
            'telmobile1', 'telmobile2', 'telfix', 'fax',
            'email_perso', 'email_prof', 'adresse', 'wilaya',
            'diplome', 'specialite_ar', 'specialite_fr', 'grade',
            'inscritProgres', 'inscritMoodle', 'inscritSNDL',
            'googlescholar', 'researchgate', 'orcid_id',
            'linkedIn', 'facebook', 'x_twitter', 'tiktok', 'telegram',
            'vacAcademique', 'maladie',
            'scholar_publications_count', 'scholar_citations_count',
            'scholar_h_index', 'scholar_i10_index', 'scholar_last_update',
            'created_at', 'updated_at'
        )
        export_order = fields


# ══════════════════════════════════════════════════════════════
# ADMIN ENSEIGNANT
# ══════════════════════════════════════════════════════════════

@admin.register(Enseignant)
class EnseignantAdmin(ImportExportModelAdmin):
    """Administration des enseignants avec import/export Excel."""

    resource_class = EnseignantResource

    list_display = (
        # 'matricule',
        'get_nom_display',
        'get_grade_display',
        'email_prof',
        'get_diplome_display',
        'get_status_display',
        'est_inscrit',
        'get_user_creation_button',
    )

    list_filter = (
        'grade',
        'diplome',
        'wilaya',
        'sex',
        'sitfam',
        'vacAcademique',
        'maladie',
        'inscritProgres',
        'inscritMoodle',
        'inscritSNDL',
        'created_at',
        'updated_at'
    )

    search_fields = (
        'matricule',
        'codeIns',
        'nom_ar',
        'nom_fr',
        'prenom_ar',
        'prenom_fr',
        'email_prof',
        'email_perso',
        'telmobile1',
        'telmobile2',
        'user__username',
        'user__email',
        'specialite_ar',
        'specialite_fr'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'scholar_last_update'
    )

    fieldsets = (
        ('المستخدم / Utilisateur', {
            'fields': ('user',),
            'description': 'Compte utilisateur lié à cet enseignant'
        }),
        ('معلومات شخصية / Informations personnelles', {
            'fields': (
                'civilite',
                ('nom_ar', 'prenom_ar'),
                ('nom_fr', 'prenom_fr'),
                'date_nais',
                'sex',
                'sitfam'
            )
        }),
        ('معلومات إدارية / Informations administratives', {
            'fields': (
                'matricule',
                'codeIns',
                'bac_annee',
                'date_Recrut'
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                ('telmobile1', 'telmobile2'),
                'telfix',
                'fax',
                'email_prof',
                'email_perso',
                'adresse',
                'wilaya'
            )
        }),
        ('مؤهلات أكاديمية / Qualifications académiques', {
            'fields': (
                'diplome',
                ('specialite_ar', 'specialite_fr'),
                'grade'
            )
        }),
        ('المنصات الأكاديمية / Plateformes académiques', {
            'fields': (
                'inscritProgres',
                'inscritMoodle',
                'inscritSNDL'
            )
        }),
        ('الشبكات الاجتماعية والأكاديمية / Réseaux sociaux et académiques', {
            'fields': (
                'googlescholar',
                'researchgate',
                'orcid_id',
                'linkedIn',
                'facebook',
                'x_twitter',
                'tiktok',
                'telegram'
            ),
            'classes': ('collapse',)
        }),
        ('مؤشرات Google Scholar / Métriques Google Scholar', {
            'fields': (
                'scholar_publications_count',
                'scholar_citations_count',
                ('scholar_h_index', 'scholar_i10_index'),
                'scholar_last_update'
            ),
            'classes': ('collapse',)
        }),
        ('الحالة / Statut', {
            'fields': (
                'vacAcademique',
                'maladie'
            )
        }),
        ('الملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def get_nom_display(self, obj):
        """Affichage bilingue du nom complet."""
        nom_ar = f"{obj.nom_ar} {obj.prenom_ar}".strip() if obj.nom_ar and obj.prenom_ar else ""
        nom_fr = f"{obj.nom_fr} {obj.prenom_fr}".strip() if obj.nom_fr and obj.prenom_fr else ""

        if nom_ar and nom_fr:
            return f"{nom_ar} / {nom_fr}"
        return nom_ar or nom_fr or obj.matricule
    get_nom_display.short_description = "الاسم / Nom"

    def get_grade_display(self, obj):
        """Affichage du grade."""
        if obj.grade:
            return obj.grade.get_nom() if hasattr(obj.grade, 'get_nom') else str(obj.grade)
        return "-"
    get_grade_display.short_description = "الرتبة / Grade"

    def get_diplome_display(self, obj):
        """Affichage du diplôme."""
        if obj.diplome:
            return obj.diplome.get_nom() if hasattr(obj.diplome, 'get_nom') else str(obj.diplome)
        return "-"
    get_diplome_display.short_description = "الدبلوم / Diplôme"

    def get_status_display(self, obj):
        """Affichage du statut."""
        statuses = []
        if obj.vacAcademique:
            statuses.append("عطلة أكاديمية")
        if obj.maladie:
            statuses.append("عطلة مرضية")
        return " / ".join(statuses) if statuses else "نشط"
    get_status_display.short_description = "الحالة / Statut"

    def get_user_creation_button(self, obj):
        """Affiche le nom d'utilisateur ou un bouton pour créer un utilisateur."""
        if obj.user:
            from django.utils.html import format_html
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ {}</span>',
                obj.user.username
            )
        else:
            from django.utils.html import format_html
            from django.urls import reverse
            url = reverse('admin:enseignant_create_user', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Créer utilisateur</a>',
                url
            )
    get_user_creation_button.short_description = "Utilisateur"
    get_user_creation_button.allow_tags = True

    def save_model(self, request, obj, form, change):
        """
        Override save_model pour créer automatiquement un utilisateur
        lors de l'ajout d'un enseignant.
        """
        # Sauvegarder l'enseignant d'abord
        super().save_model(request, obj, form, change)

        # Si c'est une création (pas une modification) ou si pas d'utilisateur
        if not change or not obj.user:
            user, error = create_user_for_enseignant(obj)
            if user:
                self.message_user(
                    request,
                    f"Utilisateur créé automatiquement - Login: {user.username}",
                    messages.SUCCESS
                )
            elif error and "déjà un utilisateur" not in error:
                self.message_user(request, error, messages.ERROR)

    def after_import_row(self, row, row_result, **kwargs):
        """
        Override after_import_row pour créer automatiquement un utilisateur
        lors de l'import Excel.
        """
        super().after_import_row(row, row_result, **kwargs)

        # Récupérer l'enseignant qui vient d'être importé
        if row_result.object_id:
            try:
                enseignant = Enseignant.objects.get(pk=row_result.object_id)
                if not enseignant.user:
                    user, error = create_user_for_enseignant(enseignant)
                    # Les erreurs sont loguées dans la console
            except Enseignant.DoesNotExist:
                pass

    def get_urls(self):
        """Ajoute une URL personnalisée pour créer un utilisateur."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:enseignant_id>/create-user/',
                self.admin_site.admin_view(self.create_user_view),
                name='enseignant_create_user',
            ),
        ]
        return custom_urls + urls

    def create_user_view(self, request, enseignant_id):
        """Vue pour créer un utilisateur pour un enseignant."""
        from django.shortcuts import redirect
        from django.contrib import messages as django_messages

        try:
            enseignant = Enseignant.objects.get(pk=enseignant_id)

            if enseignant.user:
                django_messages.warning(request, "Cet enseignant a déjà un utilisateur.")
            else:
                user, error = create_user_for_enseignant(enseignant)
                if user:
                    django_messages.success(
                        request,
                        f"Utilisateur créé avec succès - Login: {user.username}, Mot de passe: (voir utils.py)"
                    )
                else:
                    django_messages.error(request, error or "Erreur inconnue lors de la création de l'utilisateur.")

        except Enseignant.DoesNotExist:
            django_messages.error(request, "Enseignant introuvable.")

        return redirect('admin:enseignant_enseignant_changelist')

    def get_queryset(self, request):
        """
        Filtre les enseignants par département pour les non-superusers.
        Les chefs de département ne voient que les enseignants de leur département.
        """
        qs = super().get_queryset(request)

        # Les superusers voient tout
        if request.user.is_superuser:
            return qs

        # Pour les autres, filtrer par département
        departement_id = request.session.get('selected_departement_id')
        if departement_id:
            # Récupérer les IDs des enseignants affectés à ce département
            ens_ids = Ens_Dep.objects.filter(
                departement_id=departement_id
            ).values_list('enseignant_id', flat=True)
            return qs.filter(id__in=ens_ids)

        return qs.none()
