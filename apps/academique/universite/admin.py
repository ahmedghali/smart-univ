# apps/academique/universite/admin.py

from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Universite, Domaine
from apps.academique.enseignant.models import Enseignant


class UniversiteResource(resources.ModelResource):
    class Meta:
        model = Universite
        fields = ('id', 'code', 'nom_ar', 'nom_fr', 'sigle', 'wilaya',
                  'adresse', 'telmobile', 'telfix1', 'email', 'siteweb')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr', 'sigle', 'wilaya',
                        'adresse', 'telmobile', 'telfix1', 'email', 'siteweb')


class DomaineResource(resources.ModelResource):
    class Meta:
        model = Domaine
        fields = ('id', 'code', 'nom_ar', 'nom_fr', 'universite')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr', 'universite')


@admin.register(Universite)
class UniversiteAdmin(ImportExportModelAdmin):
    """
    Administration pour le modèle Universite avec support Import/Export.
    """
    resource_class = UniversiteResource

    # Champs affichés dans la liste
    list_display = [
        'code',
        'get_nom_display',
        'sigle',
        'wilaya',
        'get_recteur_display',
        'email',
        'siteweb',
    ]

    # Filtres dans la barre latérale
    list_filter = [
        'wilaya',
        'created_at',
    ]

    # Champs de recherche
    search_fields = [
        'code',
        'nom_ar',
        'nom_fr',
        'sigle',
        'email',
        'adresse',
    ]

    # Ordre d'affichage
    ordering = ['code']

    # Champs en lecture seule
    readonly_fields = ['created_at', 'updated_at', 'display_logo']

    # Organisation des champs dans le formulaire
    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': ('code', 'nom_ar', 'nom_fr', 'sigle', 'logo', 'display_logo')
        }),
        ('المسؤولون / Responsables', {
            'fields': ('recteur', 'vice_rect_p', 'vice_rect_pg'),
            'description': 'تعيين المسؤولين الأكاديميين للجامعة / Affectation des responsables académiques'
        }),
        ('الموقع / Localisation', {
            'fields': ('wilaya', 'adresse')
        }),
        ('الاتصالات / Contacts', {
            'fields': ('telmobile', 'telfix1', 'telfix2', 'fax', 'email', 'siteweb'),
            'classes': ('collapse',)
        }),
        ('الشبكات الاجتماعية / Réseaux sociaux', {
            'fields': ('facebook', 'x_twitter', 'linkedIn', 'tiktok', 'telegram'),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Méthodes personnalisées pour l'affichage
    def get_nom_display(self, obj):
        """Affiche le nom en arabe ou français."""
        return obj.nom_ar or obj.nom_fr or obj.code
    get_nom_display.short_description = 'الجامعة / Université'

    def get_recteur_display(self, obj):
        """Affiche le nom du recteur."""
        if obj.recteur:
            return str(obj.recteur)
        return '-'
    get_recteur_display.short_description = 'المدير / Recteur'

    def display_logo(self, obj):
        """Affiche le logo de l'université."""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.logo.url
            )
        return '-'
    display_logo.short_description = 'الشعار / Logo'

    # Configuration des actions
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        """Exporte les universités sélectionnées en CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="universites.csv"'
        response.write('\ufeff')  # BOM pour Excel UTF-8

        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Nom AR', 'Nom FR', 'Sigle', 'Wilaya',
            'Email', 'Site Web', 'Téléphone'
        ])

        for uni in queryset:
            writer.writerow([
                uni.code,
                uni.nom_ar,
                uni.nom_fr,
                uni.sigle,
                uni.wilaya.get_nom() if uni.wilaya else '',
                uni.email,
                uni.siteweb,
                uni.telmobile,
            ])

        return response
    export_as_csv.short_description = 'تصدير إلى CSV / Exporter en CSV'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtre les enseignants affichés dans les listes déroulantes selon leur poste.
        Vérifie à la fois le poste_principal ET les postes_secondaires.
        """
        if db_field.name == "recteur":
            # Filtrer pour afficher uniquement les enseignants avec le poste "recteur"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='recteur') |
                Q(user__postes_secondaires__code='recteur')
            ).distinct()

        elif db_field.name == "vice_rect_p":
            # Filtrer pour afficher uniquement les enseignants avec le poste "vice_rect_p"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='vice_rect_p') |
                Q(user__postes_secondaires__code='vice_rect_p')
            ).distinct()

        elif db_field.name == "vice_rect_pg":
            # Filtrer pour afficher uniquement les enseignants avec le poste "vice_rect_pg"
            kwargs["queryset"] = Enseignant.objects.filter(
                Q(user__poste_principal__code='vice_rect_pg') |
                Q(user__postes_secondaires__code='vice_rect_pg')
            ).distinct()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Domaine)
class DomaineAdmin(ImportExportModelAdmin):
    """
    Administration pour le modèle Domaine avec support Import/Export.
    """
    resource_class = DomaineResource

    # Champs affichés dans la liste
    list_display = [
        'code',
        'get_nom_display',
        'universite',
        'created_at',
    ]

    # Filtres dans la barre latérale
    list_filter = [
        'universite',
        'created_at',
    ]

    # Champs de recherche
    search_fields = [
        'code',
        'nom_ar',
        'nom_fr',
        'universite__nom_ar',
        'universite__nom_fr',
        'universite__code',
    ]

    # Ordre d'affichage
    ordering = ['universite', 'code']

    # Champs en lecture seule
    readonly_fields = ['created_at', 'updated_at']

    # Organisation des champs dans le formulaire
    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': ('universite', 'code', 'nom_ar', 'nom_fr')
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Méthodes personnalisées
    def get_nom_display(self, obj):
        """Affiche le nom en arabe ou français."""
        return obj.nom_ar or obj.nom_fr or obj.code
    get_nom_display.short_description = 'الميدان / Domaine'

    # Inline pour afficher les domaines dans l'admin de l'université
    class Meta:
        verbose_name = 'ميدان / Domaine'
        verbose_name_plural = 'ميادين / Domaines'


# Inline pour afficher les domaines dans l'admin de l'université
class DomaineInline(admin.TabularInline):
    """
    Affiche les domaines dans l'interface d'administration de l'université.
    """
    model = Domaine
    extra = 1
    fields = ['code', 'nom_ar', 'nom_fr']
    verbose_name = 'ميدان / Domaine'
    verbose_name_plural = 'ميادين / Domaines'


# Mise à jour de UniversiteAdmin pour inclure les domaines
# Note: Cette approche nécessite de modifier la classe après sa définition
UniversiteAdmin.inlines = [DomaineInline]
