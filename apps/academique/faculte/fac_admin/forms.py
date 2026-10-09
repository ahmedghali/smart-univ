"""Formulaires d'import pour l'admin de la faculté."""

from django import forms
from import_export.forms import ConfirmImportForm, ImportForm

from apps.academique.departement.models import Departement, NivSpeDep, NivSpeDep_SG


class EtudiantFacImportForm(ImportForm):
    """
    Import d'étudiants au niveau faculté :
    choix du département, niveau-spécialité et groupe.
    """

    departement = forms.ModelChoiceField(
        queryset=Departement.objects.none(),
        required=True,
        label="القسم / Département",
    )
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

    def __init__(self, *args, faculte_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculte_id:
            self.fields["departement"].queryset = Departement.objects.filter(faculte_id=faculte_id).order_by("nom_ar")
            self.fields["niv_spe_dep"].queryset = NivSpeDep.objects.filter(
                departement__faculte_id=faculte_id
            ).select_related("niveau", "specialite", "departement")
            self.fields["niv_spe_dep_sg"].queryset = NivSpeDep_SG.objects.filter(
                niv_spe_dep__departement__faculte_id=faculte_id
            ).select_related("niv_spe_dep__niveau", "niv_spe_dep__specialite", "niv_spe_dep__departement")


class EtudiantFacConfirmImportForm(ConfirmImportForm):
    """Confirmation de l'import : reporte le groupe choisi à l'étape précédente."""

    niv_spe_dep_sg = forms.ModelChoiceField(
        queryset=NivSpeDep_SG.objects.none(),
        widget=forms.HiddenInput(),
        required=True,
    )

    def __init__(self, *args, faculte_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculte_id:
            self.fields["niv_spe_dep_sg"].queryset = NivSpeDep_SG.objects.filter(
                niv_spe_dep__departement__faculte_id=faculte_id
            ).select_related("niv_spe_dep__niveau", "niv_spe_dep__specialite")
        else:
            self.fields["niv_spe_dep_sg"].queryset = NivSpeDep_SG.objects.none()
