# apps/academique/affectation/forms.py

from django import forms
from .models import Ens_Dep


class Ens_DepForm(forms.ModelForm):
    """Formulaire pour l'ajout et modification d'affectation enseignant-département."""

    class Meta:
        model = Ens_Dep
        fields = [
            'enseignant', 'departement', 'annee_univ',
            'date_affectation', 'statut', 'est_actif',
            'semestre_1', 'semestre_2'
        ]
        widgets = {
            'date_affectation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
            'departement': forms.Select(attrs={'class': 'form-control'}),
            'annee_univ': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'est_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'semestre_1': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'semestre_2': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class Ens_DepStatistiquesS1Form(forms.ModelForm):
    """Formulaire pour les statistiques du semestre 1."""

    class Meta:
        model = Ens_Dep
        fields = [
            'nbrClas_ALL_Dep_S1',
            'nbrClas_in_Dep_S1', 'nbrClas_Cours_in_Dep_S1', 'nbrClas_TD_in_Dep_S1',
            'nbrClas_TP_in_Dep_S1', 'nbrClas_SS_in_Dep_S1',
            'nbrClas_out_Dep_S1', 'nbrClas_Cours_out_Dep_S1', 'nbrClas_TD_out_Dep_S1',
            'nbrClas_TP_out_Dep_S1', 'nbrClas_SS_out_Dep_S1',
            'nbrJour_in_Dep_S1', 'volHor_in_Dep_S1', 'volHor_out_Dep_S1',
            'taux_min_S1', 'taux_moyen_S1', 'moodle_percentage_S1'
        ]
        widgets = {
            field: forms.NumberInput(attrs={'class': 'form-control'})
            for field in fields
        }


class Ens_DepStatistiquesS2Form(forms.ModelForm):
    """Formulaire pour les statistiques du semestre 2."""

    class Meta:
        model = Ens_Dep
        fields = [
            'nbrClas_ALL_Dep_S2',
            'nbrClas_in_Dep_S2', 'nbrClas_Cours_in_Dep_S2', 'nbrClas_TD_in_Dep_S2',
            'nbrClas_TP_in_Dep_S2', 'nbrClas_SS_in_Dep_S2',
            'nbrClas_out_Dep_S2', 'nbrClas_Cours_out_Dep_S2', 'nbrClas_TD_out_Dep_S2',
            'nbrClas_TP_out_Dep_S2', 'nbrClas_SS_out_Dep_S2',
            'nbrJour_in_Dep_S2', 'volHor_in_Dep_S2', 'volHor_out_Dep_S2',
            'taux_min_S2', 'taux_moyen_S2', 'moodle_percentage_S2'
        ]
        widgets = {
            field: forms.NumberInput(attrs={'class': 'form-control'})
            for field in fields
        }
