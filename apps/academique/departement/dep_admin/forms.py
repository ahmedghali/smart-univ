"""Formulaires d'import des étudiants pour l'admin du département."""

from django import forms
from import_export.forms import ConfirmImportForm, ImportForm

from apps.academique.departement.models import NivSpeDep, NivSpeDep_SG


class EtudiantDepImportForm(ImportForm):
    """Import d'étudiants : choix du niveau-spécialité puis du groupe, limités au département courant."""

    niv_spe_dep = forms.ModelChoiceField(
        queryset=NivSpeDep.objects.none(),
        required=False,
        label="المستوى والتخصص / Niveau-Spécialité",
    )
    niv_spe_dep_sg = forms.ModelChoiceField(
        queryset=NivSpeDep_SG.objects.none(),
        required=True,
        label="الفوج / Groupe",
        help_text="سيتم تطبيق هذا الاختيار على جميع الطلبة المستوردين / Ce choix sera appliqué à tous les étudiants importés",
    )

    def __init__(self, *args, departement_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["niv_spe_dep"].queryset = NivSpeDep.objects.filter(departement_id=departement_id).select_related(
            "niveau", "specialite"
        )
        self.fields["niv_spe_dep_sg"].queryset = NivSpeDep_SG.objects.filter(
            niv_spe_dep__departement_id=departement_id
        ).select_related("niv_spe_dep__niveau", "niv_spe_dep__specialite")


class EtudiantDepConfirmImportForm(ConfirmImportForm):
    """Confirmation de l'import : reporte le groupe choisi à l'étape précédente (A08)."""

    niv_spe_dep_sg = forms.ModelChoiceField(
        queryset=NivSpeDep_SG.objects.none(),
        widget=forms.HiddenInput(),
        required=True,
    )

    def __init__(self, *args, departement_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if departement_id:
            self.fields["niv_spe_dep_sg"].queryset = NivSpeDep_SG.objects.filter(
                niv_spe_dep__departement_id=departement_id
            ).select_related("niv_spe_dep__niveau", "niv_spe_dep__specialite")
        else:
            self.fields["niv_spe_dep_sg"].queryset = NivSpeDep_SG.objects.none()
