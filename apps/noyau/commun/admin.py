# apps/noyau/commun/admin.py

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import (
    Poste, Wilaya, Pays, AnneeUniversitaire,
    Amphi, Salle, Laboratoire,
    Semestre, Grade, Diplome, Cycle, Niveau, Parcours, Unite,
    Groupe, Section, Session, Reforme, Identification
)


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class PosteResource(resources.ModelResource):
    class Meta:
        model = Poste
        fields = ('id', 'code', 'nom_ar', 'nom_fr', 'nom_ar_mini', 'nom_fr_mini', 'niveau', 'type')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr', 'nom_ar_mini', 'nom_fr_mini', 'niveau', 'type')


class WilayaResource(resources.ModelResource):
    class Meta:
        model = Wilaya
        fields = ('id', 'code', 'codePostal', 'nom_ar', 'nom_fr', 'pays')
        export_order = ('id', 'code', 'codePostal', 'nom_ar', 'nom_fr', 'pays')


class PaysResource(resources.ModelResource):
    class Meta:
        model = Pays
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class AnneeUniversitaireResource(resources.ModelResource):
    class Meta:
        model = AnneeUniversitaire
        fields = ('id', 'nom', 'date_debut', 'date_fin', 'est_courante')
        export_order = ('id', 'nom', 'date_debut', 'date_fin', 'est_courante')


class AmphiResource(resources.ModelResource):
    class Meta:
        model = Amphi
        fields = ('id', 'numero', 'nom_ar', 'nom_fr', 'capacite')
        export_order = ('id', 'numero', 'nom_ar', 'nom_fr', 'capacite')


class SalleResource(resources.ModelResource):
    class Meta:
        model = Salle
        fields = ('id', 'numero', 'nom_ar', 'nom_fr', 'capacite')
        export_order = ('id', 'numero', 'nom_ar', 'nom_fr', 'capacite')


class LaboratoireResource(resources.ModelResource):
    class Meta:
        model = Laboratoire
        fields = ('id', 'numero', 'nom_ar', 'nom_fr', 'type', 'capacite')
        export_order = ('id', 'numero', 'nom_ar', 'nom_fr', 'type', 'capacite')


class SemestreResource(resources.ModelResource):
    class Meta:
        model = Semestre
        fields = ('id', 'numero', 'code', 'nom_ar', 'nom_fr', 'date_debut', 'date_fin')
        export_order = ('id', 'numero', 'code', 'nom_ar', 'nom_fr', 'date_debut', 'date_fin')


class GradeResource(resources.ModelResource):
    class Meta:
        model = Grade
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class DiplomeResource(resources.ModelResource):
    class Meta:
        model = Diplome
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class CycleResource(resources.ModelResource):
    class Meta:
        model = Cycle
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class NiveauResource(resources.ModelResource):
    class Meta:
        model = Niveau
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class ParcoursResource(resources.ModelResource):
    class Meta:
        model = Parcours
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class UniteResource(resources.ModelResource):
    class Meta:
        model = Unite
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class GroupeResource(resources.ModelResource):
    class Meta:
        model = Groupe
        fields = ('id', 'numero', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'numero', 'code', 'nom_ar', 'nom_fr')


class SectionResource(resources.ModelResource):
    class Meta:
        model = Section
        fields = ('id', 'numero', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'numero', 'code', 'nom_ar', 'nom_fr')


class SessionResource(resources.ModelResource):
    class Meta:
        model = Session
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


class ReformeResource(resources.ModelResource):
    class Meta:
        model = Reforme
        fields = ('id', 'code', 'nom_ar', 'nom_fr', 'cycle')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr', 'cycle')


class IdentificationResource(resources.ModelResource):
    class Meta:
        model = Identification
        fields = ('id', 'code', 'nom_ar', 'nom_fr')
        export_order = ('id', 'code', 'nom_ar', 'nom_fr')


# ══════════════════════════════════════════════════════════════
# ADMINISTRATION
# ══════════════════════════════════════════════════════════════


@admin.register(Poste)
class PosteAdmin(ImportExportModelAdmin):
    """
    Administration pour le modèle Poste avec support Import/Export.
    """
    resource_class = PosteResource

    # Champs affichés dans la liste
    list_display = [
        'code',
        'get_nom_bilingue',
        'type',
        'niveau',
        'est_actif',
        'created_at'
    ]

    # Filtres
    list_filter = [
        'type',
        'niveau',
        'est_actif',
        'created_at'
    ]

    # Recherche
    search_fields = [
        'code',
        'nom_ar',
        'nom_fr',
        'nom_ar_mini',
        'nom_fr_mini'
    ]

    # Ordre
    ordering = ['-niveau', 'nom_ar']

    # Champs éditables dans la liste
    list_editable = ['est_actif']

    # Organisation des champs
    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('code', 'type', 'niveau', 'est_actif')
        }),
        ('الأسماء / Libellés', {
            'fields': (
                ('nom_ar', 'nom_fr'),
                ('nom_ar_mini', 'nom_fr_mini')
            )
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Champs en lecture seule
    readonly_fields = ['created_at', 'updated_at']

    def get_nom_bilingue(self, obj):
        """Affiche le nom en arabe et français."""
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'المنصب / Poste'

    # Nombre d'éléments par page
    list_per_page = 25


@admin.register(Wilaya)
class WilayaAdmin(ImportExportModelAdmin):
    """
    Administration pour le modèle Wilaya avec support Import/Export.
    """
    resource_class = WilayaResource

    list_display = ['code', 'codePostal', 'get_nom_bilingue', 'pays', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'codePostal', 'nom_ar', 'nom_fr', 'pays__nom_ar', 'pays__nom_fr']
    ordering = ['code']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('code', 'codePostal', 'pays')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_nom_bilingue(self, obj):
        """Affiche le nom en arabe et français."""
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الولاية / Wilaya'

    list_per_page = 58  # 58 wilayas algériennes


# ══════════════════════════════════════════════════════════════
# ADMINISTRATION DES NOUVEAUX MODÈLES
# ══════════════════════════════════════════════════════════════

@admin.register(Pays)
class PaysAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Pays avec support Import/Export."""
    resource_class = PaysResource
    list_display = ['code', 'get_nom_bilingue', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'nom_ar', 'nom_fr']
    ordering = ['nom_ar']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('code',)
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'البلد / Pays'


@admin.register(AnneeUniversitaire)
class AnneeUniversitaireAdmin(ImportExportModelAdmin):
    """Administration pour le modèle AnneeUniversitaire avec support Import/Export."""
    resource_class = AnneeUniversitaireResource
    list_display = ['nom', 'date_debut', 'date_fin', 'est_courante', 'created_at']
    list_filter = ['est_courante', 'date_debut']
    search_fields = ['nom']
    ordering = ['-date_debut']
    list_editable = ['est_courante']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('المعلومات الأساسية / Informations de base', {
            'fields': ('nom', 'date_debut', 'date_fin', 'est_courante')
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Si est_courante=True, désactive les autres années courantes."""
        if obj.est_courante:
            AnneeUniversitaire.objects.filter(est_courante=True).update(est_courante=False)
        super().save_model(request, obj, form, change)


@admin.register(Amphi)
class AmphiAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Amphi avec support Import/Export."""
    resource_class = AmphiResource
    list_display = ['numero', 'get_nom_bilingue', 'capacite', 'created_at']
    list_filter = ['created_at']
    search_fields = ['numero', 'nom_ar', 'nom_fr']
    ordering = ['numero']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('numero', 'capacite')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}" if obj.nom_ar or obj.nom_fr else '-'
    get_nom_bilingue.short_description = 'المدرج / Amphithéâtre'


@admin.register(Salle)
class SalleAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Salle avec support Import/Export."""
    resource_class = SalleResource
    list_display = ['numero', 'get_nom_bilingue', 'capacite', 'created_at']
    list_filter = ['created_at']
    search_fields = ['numero', 'nom_ar', 'nom_fr']
    ordering = ['numero']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('numero', 'capacite')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}" if obj.nom_ar or obj.nom_fr else '-'
    get_nom_bilingue.short_description = 'القاعة / Salle'


@admin.register(Laboratoire)
class LaboratoireAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Laboratoire avec support Import/Export."""
    resource_class = LaboratoireResource
    list_display = ['numero', 'get_nom_bilingue', 'type', 'capacite', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['numero', 'nom_ar', 'nom_fr']
    ordering = ['numero']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('numero', 'type', 'capacite')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}" if obj.nom_ar or obj.nom_fr else '-'
    get_nom_bilingue.short_description = 'المخبر / Laboratoire'


# Administration pour les modèles d'organisation pédagogique avec une classe de base
class BaseOrganisationAdmin(ImportExportModelAdmin):
    """Classe de base pour l'administration des modèles d'organisation avec support Import/Export."""
    list_display = ['code', 'get_nom_bilingue', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'nom_ar', 'nom_fr']
    ordering = ['code']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('code',)
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الاسم / Nom'


@admin.register(Semestre)
class SemestreAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Semestre."""
    resource_class = SemestreResource
    list_display = ['numero', 'code', 'get_nom_bilingue', 'date_debut', 'date_fin', 'created_at']
    ordering = ['numero']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('numero', 'code')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('التواريخ / Dates', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'السداسي / Semestre'


@admin.register(Grade)
class GradeAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Grade."""
    resource_class = GradeResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الرتبة / Grade'


@admin.register(Diplome)
class DiplomeAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Diplome."""
    resource_class = DiplomeResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الشهادة / Diplôme'


@admin.register(Cycle)
class CycleAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Cycle."""
    resource_class = CycleResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الطور / Cycle'


@admin.register(Niveau)
class NiveauAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Niveau."""
    resource_class = NiveauResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'المستوى / Niveau'


@admin.register(Parcours)
class ParcoursAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Parcours."""
    resource_class = ParcoursResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'المسار / Parcours'


@admin.register(Unite)
class UniteAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Unite."""
    resource_class = UniteResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الوحدة / Unité'


@admin.register(Session)
class SessionAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Session."""
    resource_class = SessionResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الدورة / Session'


@admin.register(Identification)
class IdentificationAdmin(BaseOrganisationAdmin):
    """Administration pour le modèle Identification."""
    resource_class = IdentificationResource

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'نوع الوثيقة / Type d\'identification'


@admin.register(Groupe)
class GroupeAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Groupe avec support Import/Export."""
    resource_class = GroupeResource
    list_display = ['numero', 'code', 'get_nom_bilingue', 'created_at']
    list_filter = ['created_at']
    search_fields = ['numero', 'code', 'nom_ar', 'nom_fr']
    ordering = ['numero']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('numero', 'code')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}" if obj.nom_ar or obj.nom_fr else f"Groupe {obj.numero}"
    get_nom_bilingue.short_description = 'الفوج / Groupe'


@admin.register(Section)
class SectionAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Section avec support Import/Export."""
    resource_class = SectionResource
    list_display = ['numero', 'code', 'get_nom_bilingue', 'created_at']
    list_filter = ['created_at']
    search_fields = ['numero', 'code', 'nom_ar', 'nom_fr']
    ordering = ['numero']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('numero', 'code')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}" if obj.nom_ar or obj.nom_fr else f"Section {obj.numero}"
    get_nom_bilingue.short_description = 'القسم / Section'


@admin.register(Reforme)
class ReformeAdmin(ImportExportModelAdmin):
    """Administration pour le modèle Reforme avec support Import/Export."""
    resource_class = ReformeResource
    list_display = ['code', 'get_nom_bilingue', 'cycle', 'created_at']
    list_filter = ['cycle', 'created_at']
    search_fields = ['code', 'nom_ar', 'nom_fr']
    ordering = ['code']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('التعريف / Identification', {
            'fields': ('code', 'cycle')
        }),
        ('الأسماء / Libellés', {
            'fields': (('nom_ar', 'nom_fr'),)
        }),
        ('ملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_nom_bilingue(self, obj):
        return f"{obj.nom_ar} / {obj.nom_fr}"
    get_nom_bilingue.short_description = 'الإصلاح / Réforme'
