# apps/academique/etudiant/admin.py

from django.contrib import admin
from django.contrib import messages
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Etudiant
from .utils import create_user_for_etudiant


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class EtudiantResource(resources.ModelResource):
    """Resource pour l'import/export Excel des étudiants."""

    class Meta:
        model = Etudiant
        fields = (
            'id', 'user', 'civilite', 'nom_ar', 'prenom_ar', 'nom_fr', 'prenom_fr',
            'date_nais', 'sexe', 'sit_fam',
            'matricule', 'num_ins', 'bac_annee', 'niv_spe_dep_sg', 'delegue',
            'tel_mobile1', 'tel_mobile2', 'tel_fix', 'fax',
            'email_perso', 'email_prof', 'adresse', 'wilaya',
            'inscrit_progres', 'inscrit_moodle', 'inscrit_sndl', 'est_inscrit',
            'google_scholar', 'researchgate', 'orcid_id',
            'linkedin', 'facebook', 'x_twitter', 'tiktok', 'telegram',
            'en_vac_aca', 'en_maladie', 'est_actif',
            'created_at', 'updated_at'
        )
        export_order = fields


# ══════════════════════════════════════════════════════════════
# ADMIN ETUDIANT
# ══════════════════════════════════════════════════════════════

@admin.register(Etudiant)
class EtudiantAdmin(ImportExportModelAdmin):
    """Administration des étudiants avec import/export Excel."""

    resource_class = EtudiantResource

    list_display = (
        'matricule',
        'num_ins',
        'get_nom_display',
        'get_niveau_display',
        'delegue',
        'est_actif',
        'get_status_display',
        'get_user_creation_button',
    )

    list_filter = (
        'est_actif',
        'delegue',
        'sexe',
        'sit_fam',
        'niv_spe_dep_sg__niv_spe_dep__niveau',
        'niv_spe_dep_sg__niv_spe_dep__specialite',
        'niv_spe_dep_sg__niv_spe_dep__departement',
        'wilaya',
        'en_vac_aca',
        'en_maladie',
        'inscrit_progres',
        'inscrit_moodle',
        'inscrit_sndl',
        'est_inscrit',
        'created_at',
        'updated_at'
    )

    search_fields = (
        'matricule',
        'num_ins',
        'nom_ar',
        'nom_fr',
        'prenom_ar',
        'prenom_fr',
        'email_prof',
        'email_perso',
        'tel_mobile1',
        'tel_mobile2',
        'user__username',
        'user__email'
    )

    readonly_fields = (
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('المستخدم / Utilisateur', {
            'fields': ('user',),
            'description': 'Compte utilisateur lié à cet étudiant'
        }),
        ('معلومات شخصية / Informations personnelles', {
            'fields': (
                'civilite',
                ('nom_ar', 'prenom_ar'),
                ('nom_fr', 'prenom_fr'),
                'date_nais',
                'sexe',
                'sit_fam'
            )
        }),
        ('معلومات أكاديمية / Informations académiques', {
            'fields': (
                'matricule',
                'num_ins',
                'bac_annee',
                'niv_spe_dep_sg',
                'delegue'
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                ('tel_mobile1', 'tel_mobile2'),
                'tel_fix',
                'fax',
                'email_prof',
                'email_perso',
                'adresse',
                'wilaya'
            )
        }),
        ('المنصات الأكاديمية / Plateformes académiques', {
            'fields': (
                'inscrit_progres',
                'inscrit_moodle',
                'inscrit_sndl',
                'est_inscrit'
            )
        }),
        ('الشبكات الاجتماعية والأكاديمية / Réseaux sociaux et académiques', {
            'fields': (
                'google_scholar',
                'researchgate',
                'orcid_id',
                'linkedin',
                'facebook',
                'x_twitter',
                'tiktok',
                'telegram'
            ),
            'classes': ('collapse',)
        }),
        ('الحالة / Statut', {
            'fields': (
                'est_actif',
                'en_vac_aca',
                'en_maladie'
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

    def get_niveau_display(self, obj):
        """Affichage du niveau-spécialité-département-SG."""
        return obj.get_niveau_info()
    get_niveau_display.short_description = "المستوى / Niveau"

    def get_status_display(self, obj):
        """Affichage du statut."""
        statuses = []
        if obj.en_vac_aca:
            statuses.append("عطلة أكاديمية")
        if obj.en_maladie:
            statuses.append("عطلة مرضية")
        if obj.delegue:
            statuses.append("مندوب")
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
            url = reverse('admin:etudiant_create_user', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Créer utilisateur</a>',
                url
            )
    get_user_creation_button.short_description = "Utilisateur"
    get_user_creation_button.allow_tags = True

    def save_model(self, request, obj, form, change):
        """
        Override save_model pour créer automatiquement un utilisateur
        lors de l'ajout d'un étudiant.
        """
        # Sauvegarder l'étudiant d'abord
        super().save_model(request, obj, form, change)

        # Si c'est une création (pas une modification) ou si pas d'utilisateur
        if not change or not obj.user:
            user = create_user_for_etudiant(obj)
            if user:
                self.message_user(
                    request,
                    f"Utilisateur créé automatiquement - Login: {user.username}",
                    messages.SUCCESS
                )

    def after_import_row(self, row, row_result, **kwargs):
        """
        Override after_import_row pour créer automatiquement un utilisateur
        lors de l'import Excel.
        """
        super().after_import_row(row, row_result, **kwargs)

        # Récupérer l'étudiant qui vient d'être importé
        if row_result.object_id:
            try:
                etudiant = Etudiant.objects.get(pk=row_result.object_id)
                if not etudiant.user:
                    create_user_for_etudiant(etudiant)
            except Etudiant.DoesNotExist:
                pass

    def get_urls(self):
        """Ajoute une URL personnalisée pour créer un utilisateur."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:etudiant_id>/create-user/',
                self.admin_site.admin_view(self.create_user_view),
                name='etudiant_create_user',
            ),
        ]
        return custom_urls + urls

    def create_user_view(self, request, etudiant_id):
        """Vue pour créer un utilisateur pour un étudiant."""
        from django.shortcuts import redirect
        from django.contrib import messages as django_messages

        try:
            etudiant = Etudiant.objects.get(pk=etudiant_id)

            if etudiant.user:
                django_messages.warning(request, "Cet étudiant a déjà un utilisateur.")
            else:
                user = create_user_for_etudiant(etudiant)
                if user:
                    django_messages.success(
                        request,
                        f"Utilisateur créé avec succès - Login: {user.username}, Mot de passe: (voir utils.py)"
                    )
                else:
                    django_messages.error(request, "Erreur lors de la création de l'utilisateur.")

        except Etudiant.DoesNotExist:
            django_messages.error(request, "Étudiant introuvable.")

        return redirect('admin:etudiant_etudiant_changelist')
