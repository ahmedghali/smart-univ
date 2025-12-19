# apps/academique/affectation/admin.py

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import (
    Ens_Dep, Amphi_Dep, Salle_Dep, Laboratoire_Dep, Classe,
    SousGroupe, EtudiantSousGroupe, Seance, Gestion_Etu_Classe, Abs_Etu_Seance
)


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class Ens_DepResource(resources.ModelResource):
    """Resource pour l'import/export Excel des affectations enseignant-département."""

    class Meta:
        model = Ens_Dep
        fields = (
            'id', 'enseignant', 'departement', 'annee_univ',
            'date_affectation', 'statut', 'est_actif',
            'semestre_1', 'semestre_2',
            # Semestre 1
            'nbrClas_ALL_Dep_S1', 'nbrClas_in_Dep_S1', 'nbrClas_out_Dep_S1',
            'nbrClas_Cours_in_Dep_S1', 'nbrClas_TD_in_Dep_S1', 'nbrClas_TP_in_Dep_S1', 'nbrClas_SS_in_Dep_S1',
            'nbrClas_Cours_out_Dep_S1', 'nbrClas_TD_out_Dep_S1', 'nbrClas_TP_out_Dep_S1', 'nbrClas_SS_out_Dep_S1',
            'nbrJour_in_Dep_S1', 'volHor_in_Dep_S1', 'volHor_out_Dep_S1',
            'taux_min_S1', 'taux_moyen_S1', 'moodle_percentage_S1',
            # Semestre 2
            'nbrClas_ALL_Dep_S2', 'nbrClas_in_Dep_S2', 'nbrClas_out_Dep_S2',
            'nbrClas_Cours_in_Dep_S2', 'nbrClas_TD_in_Dep_S2', 'nbrClas_TP_in_Dep_S2', 'nbrClas_SS_in_Dep_S2',
            'nbrClas_Cours_out_Dep_S2', 'nbrClas_TD_out_Dep_S2', 'nbrClas_TP_out_Dep_S2', 'nbrClas_SS_out_Dep_S2',
            'nbrJour_in_Dep_S2', 'volHor_in_Dep_S2', 'volHor_out_Dep_S2',
            'taux_min_S2', 'taux_moyen_S2', 'moodle_percentage_S2',
            # BaseModel
            'created_at', 'updated_at'
        )
        export_order = fields


# ══════════════════════════════════════════════════════════════
# ADMIN AFFECTATION ENS-DEP
# ══════════════════════════════════════════════════════════════

@admin.register(Ens_Dep)
class Ens_DepAdmin(ImportExportModelAdmin):
    """Administration des affectations enseignant-département avec import/export Excel."""

    resource_class = Ens_DepResource

    list_display = (
        'get_enseignant_display',
        'get_departement_display',
        'get_annee_univ_display',
        'statut',
        'get_semestres_display',
        'get_volume_horaire_display',
        'est_actif',
    )

    list_filter = (
        'statut',
        'semestre_1',
        'semestre_2',
        'est_actif',
        'annee_univ',
        'departement',
        'enseignant__grade',
        'created_at',
        'updated_at'
    )

    search_fields = (
        'enseignant__nom_ar',
        'enseignant__nom_fr',
        'enseignant__prenom_ar',
        'enseignant__prenom_fr',
        'enseignant__matricule',
        'departement__nom_ar',
        'departement__nom_fr',
        'departement__code',
    )

    readonly_fields = (
        'created_at',
        'updated_at'
    )

    autocomplete_fields = ['enseignant', 'departement', 'annee_univ']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'enseignant',
                'departement',
                'annee_univ',
                'date_affectation',
                'statut',
                'est_actif'
            )
        }),
        ('السداسيات / Semestres', {
            'fields': (
                'semestre_1',
                'semestre_2'
            )
        }),
        ('إحصائيات السداسي الأول / Statistiques Semestre 1', {
            'fields': (
                'nbrClas_ALL_Dep_S1',
                ('nbrClas_in_Dep_S1', 'nbrClas_out_Dep_S1'),
                ('nbrClas_Cours_in_Dep_S1', 'nbrClas_Cours_out_Dep_S1'),
                ('nbrClas_TD_in_Dep_S1', 'nbrClas_TD_out_Dep_S1'),
                ('nbrClas_TP_in_Dep_S1', 'nbrClas_TP_out_Dep_S1'),
                ('nbrClas_SS_in_Dep_S1', 'nbrClas_SS_out_Dep_S1'),
                'nbrJour_in_Dep_S1',
                ('volHor_in_Dep_S1', 'volHor_out_Dep_S1'),
                ('taux_min_S1', 'taux_moyen_S1'),
                'moodle_percentage_S1'
            ),
            'classes': ('collapse',)
        }),
        ('إحصائيات السداسي الثاني / Statistiques Semestre 2', {
            'fields': (
                'nbrClas_ALL_Dep_S2',
                ('nbrClas_in_Dep_S2', 'nbrClas_out_Dep_S2'),
                ('nbrClas_Cours_in_Dep_S2', 'nbrClas_Cours_out_Dep_S2'),
                ('nbrClas_TD_in_Dep_S2', 'nbrClas_TD_out_Dep_S2'),
                ('nbrClas_TP_in_Dep_S2', 'nbrClas_TP_out_Dep_S2'),
                ('nbrClas_SS_in_Dep_S2', 'nbrClas_SS_out_Dep_S2'),
                'nbrJour_in_Dep_S2',
                ('volHor_in_Dep_S2', 'volHor_out_Dep_S2'),
                ('taux_min_S2', 'taux_moyen_S2'),
                'moodle_percentage_S2'
            ),
            'classes': ('collapse',)
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

    def get_enseignant_display(self, obj):
        """Affichage bilingue de l'enseignant."""
        if obj.enseignant.nom_ar and obj.enseignant.prenom_ar:
            nom_ar = f"{obj.enseignant.nom_ar} {obj.enseignant.prenom_ar}"
        else:
            nom_ar = ""

        if obj.enseignant.nom_fr and obj.enseignant.prenom_fr:
            nom_fr = f"{obj.enseignant.nom_fr} {obj.enseignant.prenom_fr}"
        else:
            nom_fr = ""

        if nom_ar and nom_fr:
            return f"{nom_ar} / {nom_fr}"
        return nom_ar or nom_fr or obj.enseignant.matricule
    get_enseignant_display.short_description = "الأستاذ / Enseignant"

    def get_departement_display(self, obj):
        """Affichage bilingue du département."""
        if obj.departement.nom_ar and obj.departement.nom_fr:
            return f"{obj.departement.nom_ar} / {obj.departement.nom_fr}"
        return obj.departement.nom_ar or obj.departement.nom_fr or obj.departement.code
    get_departement_display.short_description = "القسم / Département"

    def get_annee_univ_display(self, obj):
        """Affichage de l'année universitaire."""
        return str(obj.annee_univ)
    get_annee_univ_display.short_description = "السنة / Année"

    def get_semestres_display(self, obj):
        """Affichage des semestres."""
        semestres = []
        if obj.semestre_1:
            semestres.append("S1")
        if obj.semestre_2:
            semestres.append("S2")
        return " + ".join(semestres) if semestres else "-"
    get_semestres_display.short_description = "السداسيات / Semestres"

    def get_volume_horaire_display(self, obj):
        """Affichage du volume horaire total."""
        total = obj.get_volume_horaire_total_annee()
        return f"{total:.2f}h"
    get_volume_horaire_display.short_description = "الحجم الساعي / Vol. horaire"


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT - INFRASTRUCTURE
# ══════════════════════════════════════════════════════════════

class Amphi_DepResource(resources.ModelResource):
    """Resource pour l'import/export des affectations amphi-département."""

    class Meta:
        model = Amphi_Dep
        fields = ('id', 'amphi', 'departement', 'semestre_1', 'semestre_2', 'est_actif', 'observation', 'created_at', 'updated_at')
        export_order = fields


class Salle_DepResource(resources.ModelResource):
    """Resource pour l'import/export des affectations salle-département."""

    class Meta:
        model = Salle_Dep
        fields = ('id', 'salle', 'departement', 'semestre_1', 'semestre_2', 'est_actif', 'observation', 'created_at', 'updated_at')
        export_order = fields


class Laboratoire_DepResource(resources.ModelResource):
    """Resource pour l'import/export des affectations laboratoire-département."""

    class Meta:
        model = Laboratoire_Dep
        fields = ('id', 'laboratoire', 'departement', 'semestre_1', 'semestre_2', 'est_actif', 'observation', 'created_at', 'updated_at')
        export_order = fields


# ══════════════════════════════════════════════════════════════
# ADMIN AFFECTATION AMPHI-DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

@admin.register(Amphi_Dep)
class Amphi_DepAdmin(ImportExportModelAdmin):
    """Administration des affectations amphithéâtre-département."""

    resource_class = Amphi_DepResource

    list_display = (
        'amphi',
        'get_departement_display',
        'get_semestres_display',
        'est_actif',
        'created_at',
    )

    list_filter = (
        'semestre_1',
        'semestre_2',
        'est_actif',
        'departement',
        'amphi',
    )

    search_fields = (
        'amphi__numero',
        'amphi__nom_ar',
        'amphi__nom_fr',
        'departement__nom_ar',
        'departement__nom_fr',
        'departement__code',
    )

    readonly_fields = ('created_at', 'updated_at')

    autocomplete_fields = ['amphi', 'departement']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': ('amphi', 'departement', 'est_actif')
        }),
        ('السداسيات / Semestres', {
            'fields': ('semestre_1', 'semestre_2')
        }),
        ('الملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_departement_display(self, obj):
        """Affichage bilingue du département."""
        if obj.departement.nom_ar and obj.departement.nom_fr:
            return f"{obj.departement.nom_ar} / {obj.departement.nom_fr}"
        return obj.departement.nom_ar or obj.departement.nom_fr or obj.departement.code
    get_departement_display.short_description = "القسم / Département"

    def get_semestres_display(self, obj):
        """Affichage des semestres."""
        return obj.get_semestres_display()
    get_semestres_display.short_description = "السداسيات / Semestres"


# ══════════════════════════════════════════════════════════════
# ADMIN AFFECTATION SALLE-DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

@admin.register(Salle_Dep)
class Salle_DepAdmin(ImportExportModelAdmin):
    """Administration des affectations salle-département."""

    resource_class = Salle_DepResource

    list_display = (
        'salle',
        'get_departement_display',
        'get_semestres_display',
        'est_actif',
        'created_at',
    )

    list_filter = (
        'semestre_1',
        'semestre_2',
        'est_actif',
        'departement',
        'salle',
    )

    search_fields = (
        'salle__numero',
        'salle__nom_ar',
        'salle__nom_fr',
        'departement__nom_ar',
        'departement__nom_fr',
        'departement__code',
    )

    readonly_fields = ('created_at', 'updated_at')

    autocomplete_fields = ['salle', 'departement']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': ('salle', 'departement', 'est_actif')
        }),
        ('السداسيات / Semestres', {
            'fields': ('semestre_1', 'semestre_2')
        }),
        ('الملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_departement_display(self, obj):
        """Affichage bilingue du département."""
        if obj.departement.nom_ar and obj.departement.nom_fr:
            return f"{obj.departement.nom_ar} / {obj.departement.nom_fr}"
        return obj.departement.nom_ar or obj.departement.nom_fr or obj.departement.code
    get_departement_display.short_description = "القسم / Département"

    def get_semestres_display(self, obj):
        """Affichage des semestres."""
        return obj.get_semestres_display()
    get_semestres_display.short_description = "السداسيات / Semestres"


# ══════════════════════════════════════════════════════════════
# ADMIN AFFECTATION LABORATOIRE-DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

@admin.register(Laboratoire_Dep)
class Laboratoire_DepAdmin(ImportExportModelAdmin):
    """Administration des affectations laboratoire-département."""

    resource_class = Laboratoire_DepResource

    list_display = (
        'laboratoire',
        'get_departement_display',
        'get_semestres_display',
        'est_actif',
        'created_at',
    )

    list_filter = (
        'semestre_1',
        'semestre_2',
        'est_actif',
        'departement',
        'laboratoire',
        'laboratoire__type',
    )

    search_fields = (
        'laboratoire__numero',
        'laboratoire__nom_ar',
        'laboratoire__nom_fr',
        'departement__nom_ar',
        'departement__nom_fr',
        'departement__code',
    )

    readonly_fields = ('created_at', 'updated_at')

    autocomplete_fields = ['laboratoire', 'departement']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': ('laboratoire', 'departement', 'est_actif')
        }),
        ('السداسيات / Semestres', {
            'fields': ('semestre_1', 'semestre_2')
        }),
        ('الملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_departement_display(self, obj):
        """Affichage bilingue du département."""
        if obj.departement.nom_ar and obj.departement.nom_fr:
            return f"{obj.departement.nom_ar} / {obj.departement.nom_fr}"
        return obj.departement.nom_ar or obj.departement.nom_fr or obj.departement.code
    get_departement_display.short_description = "القسم / Département"

    def get_semestres_display(self, obj):
        """Affichage des semestres."""
        return obj.get_semestres_display()
    get_semestres_display.short_description = "السداسيات / Semestres"


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT - CLASSE
# ══════════════════════════════════════════════════════════════

class ClasseResource(resources.ModelResource):
    """Resource pour l'import/export des classes (séances)."""

    class Meta:
        model = Classe
        fields = (
            'id', 'semestre', 'matiere', 'enseignant', 'niv_spe_dep_sg',
            'jour', 'temps', 'type',
            'taux_avancement', 'seance_created', 'abs_liste_Etu', 'notes_liste_Etu',
            'lien_moodle', 'observation',
            'created_at', 'updated_at'
        )
        export_order = fields


# ══════════════════════════════════════════════════════════════
# FORMULAIRE PERSONNALISÉ POUR CLASSE
# ══════════════════════════════════════════════════════════════

class ClasseAdminForm(forms.ModelForm):
    """Formulaire personnalisé pour faciliter la sélection du lieu."""

    # Utiliser CharField au lieu de ChoiceField pour éviter la validation des choix
    # car les choix sont chargés dynamiquement via AJAX
    lieu_selection = forms.CharField(
        required=True,  # Obligatoire
        label="اختر المكان / Sélectionner le lieu",
        widget=forms.Select(
            choices=[('', '--- اختر الأستاذ أولاً / Choisir d\'abord l\'enseignant ---')],
            attrs={
                'class': 'form-select',
                'style': 'width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;'
            }
        ),
        error_messages={
            'required': 'يجب اختيار المكان / Vous devez sélectionner un lieu'
        }
    )

    class Meta:
        model = Classe
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pré-remplir les valeurs si on édite une instance existante
        if self.instance and self.instance.pk:
            if self.instance.content_type and self.instance.object_id:
                model_name = self.instance.content_type.model
                # Créer la valeur composée pour lieu_selection
                self.initial['lieu_selection'] = f"{model_name}_{self.instance.object_id}"

            # Charger les lieux disponibles si enseignant est défini
            if self.instance.enseignant_id:
                self._populate_lieu_choices(self.instance.enseignant_id)

        # Charger les choix si l'enseignant est fourni dans les données POST
        # Utiliser self.data après super().__init__()
        if self.data:
            enseignant_id = self.data.get('enseignant')
            if enseignant_id:
                self._populate_lieu_choices(enseignant_id)

    def _populate_lieu_choices(self, enseignant_id):
        """Remplit les choix de lieu basés sur le département de l'enseignant."""
        try:
            ens_dep = Ens_Dep.objects.select_related('departement').get(id=enseignant_id)
            departement = ens_dep.departement

            choices = [('', '--- اختر المكان / Sélectionner le lieu ---')]

            # Amphis
            amphis = Amphi_Dep.objects.filter(departement=departement, est_actif=True).select_related('amphi')
            if amphis.exists():
                choices.append(('AMPHIS', '🏛️ المدرجات / Amphithéâtres'))
                for a in amphis:
                    label = f"    {a.amphi.numero} - {a.amphi.nom_ar or a.amphi.nom_fr or ''} (السعة: {a.amphi.capacite}) [{a.get_semestres_display()}]"
                    choices.append((f"amphi_dep_{a.id}", label))

            # Salles
            salles = Salle_Dep.objects.filter(departement=departement, est_actif=True).select_related('salle')
            if salles.exists():
                choices.append(('SALLES', '🚪 القاعات / Salles'))
                for s in salles:
                    label = f"    {s.salle.numero} - {s.salle.nom_ar or s.salle.nom_fr or ''} (السعة: {s.salle.capacite}) [{s.get_semestres_display()}]"
                    choices.append((f"salle_dep_{s.id}", label))

            # Laboratoires
            labos = Laboratoire_Dep.objects.filter(departement=departement, est_actif=True).select_related('laboratoire')
            if labos.exists():
                choices.append(('LABOS', '🔬 المخابر / Laboratoires'))
                for l in labos:
                    label = f"    {l.laboratoire.numero} - {l.laboratoire.nom_ar or l.laboratoire.nom_fr or ''} (السعة: {l.laboratoire.capacite}) [{l.get_semestres_display()}]"
                    choices.append((f"laboratoire_dep_{l.id}", label))

            self.fields['lieu_selection'].widget.choices = choices

        except Ens_Dep.DoesNotExist:
            pass

    def clean(self):
        cleaned_data = super().clean()
        lieu_selection = cleaned_data.get('lieu_selection', '').strip()

        # Vérifier que lieu_selection est valide
        if not lieu_selection or lieu_selection in ['', 'AMPHIS', 'SALLES', 'LABOS']:
            self.add_error('lieu_selection', 'يجب اختيار المكان / Vous devez sélectionner un lieu valide')
            return cleaned_data

        if '_' not in lieu_selection:
            self.add_error('lieu_selection', 'Format de lieu invalide')
            return cleaned_data

        # Parser la valeur: "model_name_id" (ex: "amphi_dep_5")
        parts = lieu_selection.rsplit('_', 1)
        if len(parts) != 2:
            self.add_error('lieu_selection', 'Format de lieu invalide')
            return cleaned_data

        model_name = parts[0]  # ex: "amphi_dep"
        object_id_str = parts[1]  # ex: "5"

        try:
            content_type = ContentType.objects.get(
                app_label='affectation',
                model=model_name
            )
            object_id = int(object_id_str)

            # IMPORTANT: Définir sur l'instance pour que la validation du modèle passe
            # Django Admin appelle instance.full_clean() pendant _post_clean()
            self.instance.content_type = content_type
            self.instance.object_id = object_id

            # Aussi stocker dans cleaned_data pour save_model
            cleaned_data['content_type'] = content_type
            cleaned_data['object_id'] = object_id

        except ContentType.DoesNotExist:
            self.add_error('lieu_selection', f'نوع المكان غير صالح / Type de lieu invalide: {model_name}')
        except ValueError:
            self.add_error('lieu_selection', f'معرف المكان غير صالح / ID de lieu invalide: {object_id_str}')

        return cleaned_data


# ══════════════════════════════════════════════════════════════
# ADMIN CLASSE (SÉANCE D'ENSEIGNEMENT)
# ══════════════════════════════════════════════════════════════

@admin.register(Classe)
class ClasseAdmin(ImportExportModelAdmin):
    """Administration des classes (séances d'enseignement)."""

    form = ClasseAdminForm
    resource_class = ClasseResource

    list_display = (
        'get_matiere_display',
        'get_enseignant_display',
        'get_niv_spe_dep_sg_display',
        'jour',
        'temps',
        'type',
        'get_lieu_display',
        'taux_avancement',
        'seance_created',
    )

    list_filter = (
        'semestre',
        'jour',
        'temps',
        'type',
        'seance_created',
        'abs_liste_Etu',
        'notes_liste_Etu',
        'enseignant__departement',
        'matiere',
    )

    search_fields = (
        'matiere__nom_ar',
        'matiere__nom_fr',
        'matiere__code',
        'enseignant__enseignant__nom_ar',
        'enseignant__enseignant__nom_fr',
        'enseignant__enseignant__matricule',
        'niv_spe_dep_sg__niv_spe_dep__specialite__nom_ar',
        'niv_spe_dep_sg__niv_spe_dep__specialite__nom_fr',
    )

    readonly_fields = ('created_at', 'updated_at')

    autocomplete_fields = ['semestre', 'matiere', 'enseignant', 'niv_spe_dep_sg']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'semestre',
                'matiere',
                'enseignant',
                'niv_spe_dep_sg',
            )
        }),
        ('التوقيت / Horaire', {
            'fields': (
                ('jour', 'temps'),
                'type',
            )
        }),
        ('المكان / Lieu', {
            'fields': (
                'lieu_selection',
            ),
            'description': '⬇️ اختر الأستاذ أولاً ثم حدد المكان من القائمة / Sélectionnez d\'abord l\'enseignant puis choisissez le lieu'
        }),
        ('المتابعة البيداغوجية / Suivi pédagogique', {
            'fields': (
                'taux_avancement',
                ('seance_created', 'abs_liste_Etu', 'notes_liste_Etu'),
                'lien_moodle',
            )
        }),
        ('الملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    class Media:
        js = ('admin/js/classe_lieu_selector.js',)
        css = {
            'all': ('admin/css/classe_admin.css',)
        }

    def get_matiere_display(self, obj):
        """Affichage de la matière."""
        if obj.matiere.nom_ar and obj.matiere.nom_fr:
            return f"{obj.matiere.nom_ar} / {obj.matiere.nom_fr}"
        return obj.matiere.nom_ar or obj.matiere.nom_fr or obj.matiere.code
    get_matiere_display.short_description = "المادة / Matière"

    def get_enseignant_display(self, obj):
        """Affichage de l'enseignant."""
        ens = obj.enseignant.enseignant
        if ens.nom_ar and ens.prenom_ar:
            return f"{ens.nom_ar} {ens.prenom_ar}"
        elif ens.nom_fr and ens.prenom_fr:
            return f"{ens.nom_fr} {ens.prenom_fr}"
        return ens.matricule
    get_enseignant_display.short_description = "الأستاذ / Enseignant"

    def get_niv_spe_dep_sg_display(self, obj):
        """Affichage du niveau-spécialité-section/groupe."""
        return str(obj.niv_spe_dep_sg)
    get_niv_spe_dep_sg_display.short_description = "الطلبة / Étudiants"

    def get_lieu_display(self, obj):
        """Affichage du lieu."""
        return obj.get_lieu_display()
    get_lieu_display.short_description = "المكان / Lieu"

    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle avec les valeurs de content_type et object_id du formulaire."""
        # Récupérer les valeurs du lieu depuis le formulaire
        content_type = form.cleaned_data.get('content_type')
        object_id = form.cleaned_data.get('object_id')

        # Toujours définir ces valeurs (même si None)
        obj.content_type = content_type
        obj.object_id = object_id

        super().save_model(request, obj, form, change)


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT - NOUVEAUX MODÈLES
# ══════════════════════════════════════════════════════════════

class SousGroupeResource(resources.ModelResource):
    """Resource pour l'import/export des sous-groupes."""

    class Meta:
        model = SousGroupe
        fields = (
            'id', 'groupe_principal', 'nom', 'nom_complet', 'description',
            'effectif', 'actif', 'ordre_affichage', 'created_by',
            'observation', 'created_at', 'updated_at'
        )
        export_order = fields


class EtudiantSousGroupeResource(resources.ModelResource):
    """Resource pour l'import/export des associations étudiant-sous-groupe."""

    class Meta:
        model = EtudiantSousGroupe
        fields = (
            'id', 'etudiant', 'sous_groupe', 'date_affectation',
            'actif', 'ordre_dans_groupe', 'affecte_par',
            'observation', 'created_at', 'updated_at'
        )
        export_order = fields


class SeanceResource(resources.ModelResource):
    """Resource pour l'import/export des séances."""

    class Meta:
        model = Seance
        fields = (
            'id', 'classe', 'intitule', 'date', 'temps',
            'fait', 'remplacer', 'annuler', 'list_abs_etudiant_generee',
            'obs', 'type_audience', 'sous_groupe_unique',
            'nb_etudiants_concernes', 'observation', 'created_at', 'updated_at'
        )
        export_order = fields


class Gestion_Etu_ClasseResource(resources.ModelResource):
    """Resource pour l'import/export des gestions étudiant-classe."""

    class Meta:
        model = Gestion_Etu_Classe
        fields = (
            'id', 'classe', 'etudiant',
            'nbr_absence', 'nbr_absence_justifiee', 'nbr_seances_totales',
            'total_sup_seance', 'note_presence', 'note_participe_HW',
            'note_controle_1', 'note_controle_2', 'note_finale',
            'validee_par_enseignant', 'date_validation', 'obs',
            'observation', 'created_at', 'updated_at'
        )
        export_order = fields


class Abs_Etu_SeanceResource(resources.ModelResource):
    """Resource pour l'import/export des absences par séance."""

    class Meta:
        model = Abs_Etu_Seance
        fields = (
            'id', 'seance', 'etudiant', 'present', 'justifiee',
            'participation', 'points_sup_seance', 'obs',
            'sous_groupe_concerne', 'type_audience_lors_creation',
            'observation', 'created_at', 'updated_at'
        )
        export_order = fields


# ══════════════════════════════════════════════════════════════
# ADMIN SOUS-GROUPE
# ══════════════════════════════════════════════════════════════

class EtudiantSousGroupeInline(admin.TabularInline):
    """Inline pour afficher les étudiants d'un sous-groupe."""
    model = EtudiantSousGroupe
    extra = 0
    readonly_fields = ('date_affectation',)
    autocomplete_fields = ['etudiant', 'affecte_par']


@admin.register(SousGroupe)
class SousGroupeAdmin(ImportExportModelAdmin):
    """Administration des sous-groupes."""

    resource_class = SousGroupeResource
    inlines = [EtudiantSousGroupeInline]

    list_display = (
        'nom_complet',
        'groupe_principal',
        'effectif',
        'actif',
        'ordre_affichage',
        'created_at',
    )

    list_filter = (
        'actif',
        'groupe_principal__niv_spe_dep__departement',
        'created_by',
    )

    search_fields = (
        'nom',
        'nom_complet',
        'groupe_principal__nom',
        'groupe_principal__niv_spe_dep__specialite__nom_ar',
        'groupe_principal__niv_spe_dep__specialite__nom_fr',
    )

    readonly_fields = ('effectif', 'created_at', 'updated_at')

    autocomplete_fields = ['groupe_principal', 'created_by']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'groupe_principal',
                'nom',
                'nom_complet',
                'description',
            )
        }),
        ('الإعدادات / Paramètres', {
            'fields': (
                'actif',
                'ordre_affichage',
                'effectif',
            )
        }),
        ('معلومات الإنشاء / Informations création', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            # Essayer de trouver l'enseignant associé à l'utilisateur
            if hasattr(request.user, 'enseignant_profile'):
                obj.created_by = request.user.enseignant_profile
        super().save_model(request, obj, form, change)


# ══════════════════════════════════════════════════════════════
# ADMIN ÉTUDIANT-SOUS-GROUPE
# ══════════════════════════════════════════════════════════════

@admin.register(EtudiantSousGroupe)
class EtudiantSousGroupeAdmin(ImportExportModelAdmin):
    """Administration des associations étudiant-sous-groupe."""

    resource_class = EtudiantSousGroupeResource

    list_display = (
        'etudiant',
        'sous_groupe',
        'ordre_dans_groupe',
        'actif',
        'date_affectation',
    )

    list_filter = (
        'actif',
        'sous_groupe__groupe_principal',
        'sous_groupe',
        'date_affectation',
    )

    search_fields = (
        'etudiant__nom_ar',
        'etudiant__nom_fr',
        'etudiant__prenom_ar',
        'etudiant__prenom_fr',
        'etudiant__matricule',
        'sous_groupe__nom',
        'sous_groupe__nom_complet',
    )

    readonly_fields = ('date_affectation', 'created_at', 'updated_at')

    autocomplete_fields = ['etudiant', 'sous_groupe', 'affecte_par']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'etudiant',
                'sous_groupe',
                'ordre_dans_groupe',
                'actif',
            )
        }),
        ('معلومات التعيين / Informations affectation', {
            'fields': (
                'affecte_par',
                'date_affectation',
            ),
            'classes': ('collapse',)
        }),
    )


# ══════════════════════════════════════════════════════════════
# ADMIN SÉANCE
# ══════════════════════════════════════════════════════════════

class Abs_Etu_SeanceInline(admin.TabularInline):
    """Inline pour afficher les présences/absences d'une séance."""
    model = Abs_Etu_Seance
    extra = 0
    readonly_fields = ('type_audience_lors_creation',)
    autocomplete_fields = ['etudiant', 'sous_groupe_concerne']
    fields = ('etudiant', 'present', 'justifiee', 'participation', 'points_sup_seance', 'obs')


@admin.register(Seance)
class SeanceAdmin(ImportExportModelAdmin):
    """Administration des séances."""

    resource_class = SeanceResource
    inlines = [Abs_Etu_SeanceInline]

    list_display = (
        'get_classe_display',
        'date',
        'temps',
        'type_audience',
        'fait',
        'annuler',
        'nb_etudiants_concernes',
        'get_absences_display',
    )

    list_filter = (
        'fait',
        'annuler',
        'remplacer',
        'list_abs_etudiant_generee',
        'type_audience',
        'date',
        'temps',
        'classe__matiere',
        'classe__enseignant',
    )

    search_fields = (
        'intitule',
        'classe__matiere__nom_ar',
        'classe__matiere__nom_fr',
        'classe__enseignant__enseignant__nom_ar',
        'classe__enseignant__enseignant__nom_fr',
    )

    readonly_fields = (
        'list_abs_etudiant_generee',
        'nb_etudiants_concernes',
        'created_at',
        'updated_at'
    )

    autocomplete_fields = ['classe', 'sous_groupe_unique']

    filter_horizontal = ('sous_groupes_multiples',)

    date_hierarchy = 'date'

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'classe',
                'intitule',
                ('date', 'temps'),
            )
        }),
        ('حالة الحصة / État de la séance', {
            'fields': (
                ('fait', 'remplacer', 'annuler'),
                'list_abs_etudiant_generee',
            )
        }),
        ('نوع الجمهور / Type d\'audience', {
            'fields': (
                'type_audience',
                'sous_groupe_unique',
                'sous_groupes_multiples',
                'nb_etudiants_concernes',
            ),
            'description': 'حدد نوع الجمهور للحصة / Définissez le type d\'audience pour cette séance'
        }),
        ('الملاحظات / Observations', {
            'fields': ('obs', 'observation'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_classe_display(self, obj):
        """Affichage de la classe."""
        if obj.classe and obj.classe.matiere:
            return f"{obj.classe.matiere.nom_ar or obj.classe.matiere.nom_fr}"
        return "-"
    get_classe_display.short_description = "المادة / Matière"

    def get_absences_display(self, obj):
        """Affichage du nombre d'absences."""
        return format_html(
            '<span style="color: red;">{}</span> / <span style="color: orange;">{}</span>',
            obj.nbr_absence,
            obj.nbr_absence_justifiee
        )
    get_absences_display.short_description = "غيابات / Abs."


# ══════════════════════════════════════════════════════════════
# ADMIN GESTION ÉTUDIANT-CLASSE
# ══════════════════════════════════════════════════════════════

@admin.register(Gestion_Etu_Classe)
class Gestion_Etu_ClasseAdmin(ImportExportModelAdmin):
    """Administration des gestions étudiant-classe (absences et notes)."""

    resource_class = Gestion_Etu_ClasseResource

    list_display = (
        'etudiant',
        'classe',
        'nbr_absence',
        'nbr_absence_justifiee',
        'note_presence',
        'note_participe_HW',
        'note_controle_1',
        'note_controle_2',
        'note_finale',
        'get_mention_display',
        'validee_par_enseignant',
    )

    list_filter = (
        'validee_par_enseignant',
        'classe__matiere',
        'classe__enseignant',
        'classe__semestre',
    )

    search_fields = (
        'etudiant__nom_ar',
        'etudiant__nom_fr',
        'etudiant__prenom_ar',
        'etudiant__prenom_fr',
        'etudiant__matricule',
        'classe__matiere__nom_ar',
        'classe__matiere__nom_fr',
    )

    readonly_fields = (
        'note_presence',
        'note_finale',
        'nbr_seances_totales',
        'date_derniere_maj',
        'date_validation',
        'created_at',
        'updated_at'
    )

    autocomplete_fields = ['classe', 'etudiant']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'classe',
                'etudiant',
            )
        }),
        ('الغيابات / Absences', {
            'fields': (
                ('nbr_absence', 'nbr_absence_justifiee'),
                'nbr_seances_totales',
            )
        }),
        ('النقاط / Notes', {
            'fields': (
                'note_presence',
                'note_participe_HW',
                ('note_controle_1', 'note_controle_2'),
                'total_sup_seance',
                'note_finale',
            )
        }),
        ('التصديق / Validation', {
            'fields': (
                'validee_par_enseignant',
                'date_validation',
            )
        }),
        ('الملاحظات / Observations', {
            'fields': ('obs', 'observation'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': ('date_derniere_maj', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_mention_display(self, obj):
        """Affichage de la mention avec couleur."""
        mention = obj.mention
        color = 'green' if obj.est_admis else 'red'
        return format_html('<span style="color: {};">{}</span>', color, mention)
    get_mention_display.short_description = "التقدير / Mention"


# ══════════════════════════════════════════════════════════════
# ADMIN ABSENCE ÉTUDIANT PAR SÉANCE
# ══════════════════════════════════════════════════════════════

@admin.register(Abs_Etu_Seance)
class Abs_Etu_SeanceAdmin(ImportExportModelAdmin):
    """Administration des présences/absences par séance."""

    resource_class = Abs_Etu_SeanceResource

    list_display = (
        'etudiant',
        'seance',
        'get_presence_display',
        'justifiee',
        'participation',
        'points_sup_seance',
        'sous_groupe_concerne',
    )

    list_filter = (
        'present',
        'justifiee',
        'participation',
        'seance__date',
        'seance__classe__matiere',
        'sous_groupe_concerne',
    )

    search_fields = (
        'etudiant__nom_ar',
        'etudiant__nom_fr',
        'etudiant__prenom_ar',
        'etudiant__prenom_fr',
        'etudiant__matricule',
        'seance__classe__matiere__nom_ar',
        'seance__classe__matiere__nom_fr',
    )

    readonly_fields = ('type_audience_lors_creation', 'created_at', 'updated_at')

    autocomplete_fields = ['seance', 'etudiant', 'sous_groupe_concerne']

    fieldsets = (
        ('معلومات أساسية / Informations de base', {
            'fields': (
                'seance',
                'etudiant',
            )
        }),
        ('الحضور والمشاركة / Présence et participation', {
            'fields': (
                ('present', 'justifiee'),
                'participation',
                'points_sup_seance',
            )
        }),
        ('المجموعة الفرعية / Sous-groupe', {
            'fields': (
                'sous_groupe_concerne',
                'type_audience_lors_creation',
            ),
            'classes': ('collapse',)
        }),
        ('الملاحظات / Observations', {
            'fields': ('obs', 'observation'),
            'classes': ('collapse',)
        }),
    )

    def get_presence_display(self, obj):
        """Affichage de la présence avec couleur."""
        if obj.present:
            return format_html('<span style="color: green;">✓ حاضر</span>')
        elif obj.justifiee:
            return format_html('<span style="color: orange;">⚠ مبرر</span>')
        else:
            return format_html('<span style="color: red;">✗ غائب</span>')
    get_presence_display.short_description = "الحضور / Présence"
