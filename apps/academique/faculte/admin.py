# apps/academique/faculte/admin.py

from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Faculte, Filiere
from apps.academique.enseignant.models import Enseignant


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class FaculteResource(resources.ModelResource):
    """Resource pour l'import/export Excel des facultés."""

    class Meta:
        model = Faculte
        fields = (
            'id', 'code', 'nom_ar', 'nom_fr', 'sigle', 'universite',
            'doyen', 'vice_doyen_p', 'vice_doyen_pg',
            'adresse', 'telmobile', 'telfix1', 'telfix2', 'tel3chiffre',
            'fax', 'email', 'siteweb',
            'facebook', 'x_twitter', 'linkedIn', 'tikTok', 'telegram',
            'created_at', 'updated_at'
        )
        export_order = (
            'id', 'code', 'nom_ar', 'nom_fr', 'sigle', 'universite',
            'doyen', 'vice_doyen_p', 'vice_doyen_pg',
            'adresse', 'telmobile', 'telfix1', 'telfix2', 'tel3chiffre',
            'fax', 'email', 'siteweb',
            'facebook', 'x_twitter', 'linkedIn', 'tikTok', 'telegram',
            'created_at', 'updated_at'
        )


class FiliereResource(resources.ModelResource):
    """Resource pour l'import/export Excel des filières."""

    class Meta:
        model = Filiere
        fields = (
            'id', 'code', 'nom_ar', 'nom_fr', 'domaine',
            'created_at', 'updated_at'
        )
        export_order = (
            'id', 'code', 'nom_ar', 'nom_fr', 'domaine',
            'created_at', 'updated_at'
        )


# ══════════════════════════════════════════════════════════════
# INLINE ADMIN
# ══════════════════════════════════════════════════════════════

class FiliereInline(admin.TabularInline):
    """Inline pour gérer les filières depuis l'admin faculté."""
    model = Filiere
    extra = 1
    fields = ('code', 'nom_ar', 'nom_fr', 'domaine')
    readonly_fields = ('created_at', 'updated_at')


# ══════════════════════════════════════════════════════════════
# ADMIN FACULTE
# ══════════════════════════════════════════════════════════════

@admin.register(Faculte)
class FaculteAdmin(ImportExportModelAdmin):
    """Administration des facultés avec import/export Excel."""

    resource_class = FaculteResource

    list_display = (
        'code',
        'get_nom_display',
        'sigle',
        'get_universite_display',
        'get_doyen_display',
        'display_logo',
    )

    list_filter = (
        'universite',
        'created_at',
        'updated_at'
    )

    search_fields = (
        'code',
        'nom_ar',
        'nom_fr',
        'sigle',
        'email',
        'universite__nom_ar',
        'universite__nom_fr',
        'doyen__nom_ar',
        'doyen__nom_fr'
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
                'universite',
                ('logo', 'display_logo_preview')
            )
        }),
        ('المسؤولون / Responsables', {
            'fields': (
                'doyen',
                'vice_doyen_p',
                'vice_doyen_pg'
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                'adresse',
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
                'tikTok',
                'telegram'
            ),
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

    # inlines = [FiliereInline]  # Décommentez si vous voulez gérer les filières depuis la faculté

    def get_nom_display(self, obj):
        """Affichage bilingue du nom."""
        if obj.nom_ar and obj.nom_fr:
            return f"{obj.nom_ar} / {obj.nom_fr}"
        return obj.nom_ar or obj.nom_fr or obj.code
    get_nom_display.short_description = "الاسم / Nom"

    def get_universite_display(self, obj):
        """Affichage de l'université."""
        if obj.universite:
            return obj.universite.get_nom()
        return "-"
    get_universite_display.short_description = "الجامعة / Université"

    def get_doyen_display(self, obj):
        """Affichage du doyen."""
        if obj.doyen:
            return f"{obj.doyen.nom_ar or obj.doyen.nom_fr} {obj.doyen.prenom_ar or obj.doyen.prenom_fr}"
        return "-"
    get_doyen_display.short_description = "العميد / Doyen"

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
        if db_field.name == "doyen":
            # Filtrer pour afficher uniquement les enseignants avec le poste "doyen"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='doyen') |
                Q(user__postes_secondaires__code='doyen')
            ).distinct()

        elif db_field.name == "vice_doyen_p":
            # Filtrer pour afficher uniquement les enseignants avec le poste "vice_doyen_p"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='vice_doyen_p') |
                Q(user__postes_secondaires__code='vice_doyen_p')
            ).distinct()

        elif db_field.name == "vice_doyen_pg":
            # Filtrer pour afficher uniquement les enseignants avec le poste "vice_doyen_pg"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='vice_doyen_pg') |
                Q(user__postes_secondaires__code='vice_doyen_pg')
            ).distinct()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ══════════════════════════════════════════════════════════════
# ADMIN FILIERE
# ══════════════════════════════════════════════════════════════

@admin.register(Filiere)
class FiliereAdmin(ImportExportModelAdmin):
    """Administration des filières avec import/export Excel."""

    resource_class = FiliereResource

    list_display = (
        'code',
        'get_nom_display',
        'get_domaine_display'
    )

    list_filter = (
        'domaine',
        'created_at',
        'updated_at'
    )

    search_fields = (
        'code',
        'nom_ar',
        'nom_fr',
        'domaine__nom_ar',
        'domaine__nom_fr'
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
                'domaine'
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

    def get_domaine_display(self, obj):
        """Affichage du domaine."""
        if obj.domaine:
            return obj.domaine.get_nom()
        return "-"
    get_domaine_display.short_description = "الميدان / Domaine"
