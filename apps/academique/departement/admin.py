# apps/academique/departement/admin.py

from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Departement, Specialite, NivSpeDep, NivSpeDep_SG, Matiere
from apps.academique.enseignant.models import Enseignant


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class DepartementResource(resources.ModelResource):
    """Resource pour l'import/export Excel des départements."""

    class Meta:
        model = Departement
        fields = (
            'id', 'code', 'nom_ar', 'nom_fr', 'sigle', 'faculte',
            'chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg',
            'telmobile', 'telfix1', 'telfix2', 'tel3chiffre',
            'fax', 'email', 'siteweb',
            'facebook', 'x_twitter', 'linkedIn', 'tiktok', 'telegram',
            'creationALLseances', 'created_at', 'updated_at'
        )
        export_order = fields


class SpecialiteResource(resources.ModelResource):
    """Resource pour l'import/export Excel des spécialités."""

    class Meta:
        model = Specialite
        fields = (
            'id', 'code', 'nom_ar', 'nom_fr', 'departement',
            'reforme', 'identification', 'parcours',
            'created_at', 'updated_at'
        )
        export_order = fields


class NivSpeDepResource(resources.ModelResource):
    """Resource pour l'import/export Excel des Niv-Spe-Dep."""

    class Meta:
        model = NivSpeDep
        fields = (
            'id', 'niveau', 'specialite', 'departement',
            'nbr_matieres_s1', 'nbr_matieres_s2', 'nbr_etudiants'
        )
        export_order = fields


class NivSpeDep_SGResource(resources.ModelResource):
    """Resource pour l'import/export Excel des Niv-Spe-Dep-SG."""

    class Meta:
        model = NivSpeDep_SG
        fields = (
            'id', 'niv_spe_dep', 'section', 'groupe',
            'nbr_etudiants_SG', 'type_affectation'
        )
        export_order = fields


class MatiereResource(resources.ModelResource):
    """Resource pour l'import/export Excel des matières."""

    class Meta:
        model = Matiere
        fields = (
            'id', 'code', 'nom_ar', 'nom_fr',
            'coeff', 'credit', 'unite', 'niv_spe_dep', 'semestre'
        )
        export_order = fields


# ══════════════════════════════════════════════════════════════
# INLINE ADMINS
# ══════════════════════════════════════════════════════════════

class SpecialiteInline(admin.TabularInline):
    """Inline pour gérer les spécialités depuis l'admin département."""
    model = Specialite
    extra = 1
    fields = ('code', 'nom_ar', 'nom_fr', 'reforme', 'identification', 'parcours')
    readonly_fields = ('created_at', 'updated_at')


class NivSpeDepInline(admin.TabularInline):
    """Inline pour gérer les Niv-Spe-Dep depuis l'admin spécialité."""
    model = NivSpeDep
    extra = 1
    fields = ('niveau', 'specialite', 'departement', 'nbr_matieres_s1', 'nbr_matieres_s2', 'nbr_etudiants')


class NivSpeDep_SGInline(admin.TabularInline):
    """Inline pour gérer les Niv-Spe-Dep-SG depuis l'admin NivSpeDep."""
    model = NivSpeDep_SG
    extra = 1
    fields = ('type_affectation', 'section', 'groupe', 'nbr_etudiants_SG')


class MatiereInline(admin.TabularInline):
    """Inline pour gérer les matières depuis l'admin NivSpeDep."""
    model = Matiere
    extra = 1
    fields = ('code', 'nom_ar', 'nom_fr', 'coeff', 'credit', 'unite', 'semestre')


# ══════════════════════════════════════════════════════════════
# ADMIN DEPARTEMENT
# ══════════════════════════════════════════════════════════════

@admin.register(Departement)
class DepartementAdmin(ImportExportModelAdmin):
    """Administration des départements avec import/export Excel."""

    resource_class = DepartementResource

    list_display = (
        'code',
        'get_nom_display',
        'sigle',
        'get_faculte_display',
        'get_chef_display',
        'display_logo',
    )

    list_filter = (
        'faculte',
        'created_at',
        'updated_at'
    )

    search_fields = (
        'code',
        'nom_ar',
        'nom_fr',
        'sigle',
        'email',
        'faculte__nom_ar',
        'faculte__nom_fr',
        'chef_departement__nom_ar',
        'chef_departement__nom_fr'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'display_logo_preview'
    )

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'code',
                'nom_ar',
                'nom_fr',
                'sigle',
                'faculte',
                ('logo', 'display_logo_preview')
            )
        }),
        ('المسؤولون / Responsables', {
            'fields': (
                'chef_departement',
                'chef_dep_adj_p',
                'chef_dep_adj_pg'
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                ('telmobile', 'telfix1'),
                ('telfix2', 'tel3chiffre'),
                'fax',
                'email',
                'siteweb'
            )
        }),
        ('وسائل التواصل الاجتماعي / Réseaux sociaux', {
            'fields': (
                'facebook',
                'x_twitter',
                'linkedIn',
                'tiktok',
                'telegram'
            ),
            'classes': ('collapse',)
        }),
        ('الإعدادات / Paramètres', {
            'fields': (
                'creationALLseances',
            )
        }),
        ('معلومات النظام / Informations système', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    # inlines = [SpecialiteInline]  # Décommentez si vous voulez gérer les spécialités depuis le département

    def get_nom_display(self, obj):
        """Affichage bilingue du nom."""
        if obj.nom_ar and obj.nom_fr:
            return f"{obj.nom_ar} / {obj.nom_fr}"
        return obj.nom_ar or obj.nom_fr or obj.code
    get_nom_display.short_description = "الاسم / Nom"

    def get_faculte_display(self, obj):
        """Affichage de la faculté."""
        if obj.faculte:
            return obj.faculte.get_nom()
        return "-"
    get_faculte_display.short_description = "الكلية / Faculté"

    def get_chef_display(self, obj):
        """Affichage du chef de département."""
        if obj.chef_departement:
            return f"{obj.chef_departement.nom_ar or obj.chef_departement.nom_fr} {obj.chef_departement.prenom_ar or obj.chef_departement.prenom_fr}"
        return "-"
    get_chef_display.short_description = "رئيس القسم / Chef"

    def display_logo(self, obj):
        """Affichage du logo dans la liste."""
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: contain;" />',
                obj.logo.url
            )
        return "-"
    display_logo.short_description = "الشعار / Logo"

    def display_logo_preview(self, obj):
        """Aperçu du logo dans le formulaire."""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; object-fit: contain;" />',
                obj.logo.url
            )
        return "لا يوجد شعار / Pas de logo"
    display_logo_preview.short_description = "معاينة الشعار / Aperçu du logo"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtre les enseignants affichés dans les listes déroulantes selon leur poste.
        Vérifie à la fois le poste_principal ET les postes_secondaires.
        """
        if db_field.name == "chef_departement":
            # Filtrer pour afficher uniquement les enseignants avec le poste "chef_departement"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='chef_departement') |
                Q(user__postes_secondaires__code='chef_departement')
            ).distinct()

        elif db_field.name == "chef_dep_adj_p":
            # Filtrer pour afficher uniquement les enseignants avec le poste "chef_dep_adj_p"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='chef_dep_adj_p') |
                Q(user__postes_secondaires__code='chef_dep_adj_p')
            ).distinct()

        elif db_field.name == "chef_dep_adj_pg":
            # Filtrer pour afficher uniquement les enseignants avec le poste "chef_dep_adj_pg"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='chef_dep_adj_pg') |
                Q(user__postes_secondaires__code='chef_dep_adj_pg')
            ).distinct()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ══════════════════════════════════════════════════════════════
# ADMIN SPECIALITE
# ══════════════════════════════════════════════════════════════

@admin.register(Specialite)
class SpecialiteAdmin(ImportExportModelAdmin):
    """Administration des spécialités avec import/export Excel."""

    resource_class = SpecialiteResource

    list_display = (
        'code',
        'get_nom_display',
        'get_departement_display',
        'reforme'
    )

    list_filter = (
        'departement',
        'reforme',
        'identification',
        'parcours',
        'created_at'
    )

    search_fields = (
        'code',
        'nom_ar',
        'nom_fr',
        'departement__nom_ar',
        'departement__nom_fr'
    )

    readonly_fields = (
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'code',
                'nom_ar',
                'nom_fr',
                'departement'
            )
        }),
        ('الإصلاح والتعريف / Réforme et Identification', {
            'fields': (
                'reforme',
                'identification',
                'parcours'
            )
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
        """Affichage bilingue du nom."""
        if obj.nom_ar and obj.nom_fr:
            return f"{obj.nom_ar} / {obj.nom_fr}"
        return obj.nom_ar or obj.nom_fr or obj.code
    get_nom_display.short_description = "الاسم / Nom"

    def get_departement_display(self, obj):
        """Affichage du département."""
        if obj.departement:
            return obj.departement.get_nom()
        return "-"
    get_departement_display.short_description = "القسم / Département"


# ══════════════════════════════════════════════════════════════
# ADMIN NIVSPEDEP
# ══════════════════════════════════════════════════════════════

@admin.register(NivSpeDep)
class NivSpeDepAdmin(ImportExportModelAdmin):
    """Administration des Niveau-Spécialité-Département avec import/export Excel."""

    resource_class = NivSpeDepResource

    list_display = (
        'get_display',
        'nbr_matieres_s1',
        'nbr_matieres_s2',
        'nbr_etudiants'
    )

    list_filter = (
        'departement',
        'specialite',
        'niveau'
    )

    search_fields = (
        'specialite__nom_ar',
        'specialite__nom_fr',
        'departement__nom_ar',
        'departement__nom_fr',
        'niveau__nom_ar',
        'niveau__nom_fr'
    )

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'niveau',
                'specialite',
                'departement'
            )
        }),
        ('إحصائيات / Statistiques', {
            'fields': (
                'nbr_matieres_s1',
                'nbr_matieres_s2',
                'nbr_etudiants'
            )
        })
    )

    # inlines = [NivSpeDep_SGInline, MatiereInline]

    def get_display(self, obj):
        return str(obj)
    get_display.short_description = "Niv-Spe-Dep"


# ══════════════════════════════════════════════════════════════
# ADMIN NIVSPEDEP_SG
# ══════════════════════════════════════════════════════════════

@admin.register(NivSpeDep_SG)
class NivSpeDep_SGAdmin(ImportExportModelAdmin):
    """Administration des Niv-Spe-Dep avec Section/Groupe."""

    resource_class = NivSpeDep_SGResource

    list_display = (
        'get_display',
        'type_affectation',
        'nbr_etudiants_SG'
    )

    list_filter = (
        'type_affectation',
        'niv_spe_dep__departement',
        'niv_spe_dep__specialite'
    )

    search_fields = (
        'niv_spe_dep__specialite__nom_ar',
        'niv_spe_dep__specialite__nom_fr',
        'section__nom',
        'groupe__nom'
    )

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'niv_spe_dep',
                'type_affectation',
                'section',
                'groupe',
                'nbr_etudiants_SG'
            )
        }),
    )

    def get_display(self, obj):
        return str(obj)
    get_display.short_description = "Niv-Spe-Dep-SG"


# ══════════════════════════════════════════════════════════════
# ADMIN MATIERE
# ══════════════════════════════════════════════════════════════

@admin.register(Matiere)
class MatiereAdmin(ImportExportModelAdmin):
    """Administration des matières avec import/export Excel."""

    resource_class = MatiereResource

    list_display = (
        'code',
        'get_nom_display',
        'coeff',
        'credit',
        'semestre',
        'get_niv_spe_dep_display'
    )

    list_filter = (
        'semestre',
        'unite',
        'niv_spe_dep__niveau',
        'niv_spe_dep__specialite',
        'niv_spe_dep__departement'
    )

    search_fields = (
        'code',
        'nom_ar',
        'nom_fr',
        'niv_spe_dep__specialite__nom_ar',
        'niv_spe_dep__specialite__nom_fr'
    )

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'code',
                'nom_ar',
                'nom_fr',
                'niv_spe_dep',
                'semestre'
            )
        }),
        ('التقييم / Évaluation', {
            'fields': (
                'coeff',
                'credit',
                'unite'
            )
        })
    )

    def get_nom_display(self, obj):
        """Affichage bilingue du nom."""
        if obj.nom_ar and obj.nom_fr:
            return f"{obj.nom_ar} / {obj.nom_fr}"
        return obj.nom_ar or obj.nom_fr or obj.code
    get_nom_display.short_description = "الاسم / Nom"

    def get_niv_spe_dep_display(self, obj):
        """Affichage du niveau-spécialité-département."""
        return str(obj.niv_spe_dep)
    get_niv_spe_dep_display.short_description = "Niveau-Spécialité-Département"
