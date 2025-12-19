from django import forms
from .models import Departement


class DepartementForm(forms.ModelForm):
    """Formulaire pour modifier les informations d'un département."""

    class Meta:
        model = Departement
        fields = [
            # Informations de base
            'code', 'nom_ar', 'nom_fr', 'sigle', 'logo',
            # Coordonnées
            'telmobile', 'telfix1', 'telfix2', 'tel3chiffre', 'fax', 'email', 'siteweb',
            # Réseaux sociaux
            'facebook', 'x_twitter', 'linkedIn', 'tiktok', 'telegram',
            # Paramètres
            'creationALLseances',
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: INFO'}),
            'nom_ar': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'nom_fr': forms.TextInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: INFO'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'telmobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0xxx xx xx xx'}),
            'telfix1': forms.TextInput(attrs={'class': 'form-control'}),
            'telfix2': forms.TextInput(attrs={'class': 'form-control'}),
            'tel3chiffre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'xxx'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@univ.dz'}),
            'siteweb': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'x_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'linkedIn': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/...'}),
            'tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/...'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
            'creationALLseances': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }