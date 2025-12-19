# apps/academique/faculte/forms.py

from django import forms
from .models import Faculte, Filiere


class profileUpdate_Fac_Form(forms.ModelForm):
    """
    Formulaire pour la mise à jour du profil de la faculté.
    Permet au doyen de modifier les informations de contact et autres détails.
    """

    class Meta:
        model = Faculte
        fields = [
            'nom_ar',
            'nom_fr',
            'sigle',
            'logo',
            'adresse',
            'telmobile',
            'telfix1',
            'telfix2',
            'tel3chiffre',
            'fax',
            'email',
            'siteweb',
            'facebook',
            'x_twitter',
            'linkedIn',
            'tikTok',
            'telegram',
        ]

        widgets = {
            'nom_ar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الكلية بالعربية'
            }),
            'nom_fr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la faculté en français'
            }),
            'sigle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: FSI, FSNV'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'العنوان / Adresse'
            }),
            'telmobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0555123456'
            }),
            'telfix1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023123456'
            }),
            'telfix2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023123457'
            }),
            'tel3chiffre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023123458'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@faculte.dz'
            }),
            'siteweb': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://faculte.univ.dz'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/...'
            }),
            'x_twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://x.com/...'
            }),
            'linkedIn': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/...'
            }),
            'tikTok': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tiktok.com/@...'
            }),
            'telegram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://t.me/...'
            }),
        }


class FaculteForm(forms.ModelForm):
    """
    Formulaire complet pour la création/modification d'une faculté.
    À utiliser dans l'interface admin ou pour les superutilisateurs.
    """

    class Meta:
        model = Faculte
        fields = '__all__'

        widgets = {
            'nom_ar': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_fr': forms.TextInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'universite': forms.Select(attrs={'class': 'form-control'}),
            'doyen': forms.Select(attrs={'class': 'form-control'}),
            'vice_doyen_p': forms.Select(attrs={'class': 'form-control'}),
            'vice_doyen_pg': forms.Select(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'telmobile': forms.TextInput(attrs={'class': 'form-control'}),
            'telfix1': forms.TextInput(attrs={'class': 'form-control'}),
            'telfix2': forms.TextInput(attrs={'class': 'form-control'}),
            'tel3chiffre': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'siteweb': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'x_twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedIn': forms.URLInput(attrs={'class': 'form-control'}),
            'tikTok': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control'}),
        }


class FiliereForm(forms.ModelForm):
    """
    Formulaire pour la création/modification d'une filière.
    """

    class Meta:
        model = Filiere
        fields = '__all__'

        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: MI, INFO'
            }),
            'nom_ar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الشعبة بالعربية'
            }),
            'nom_fr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la filière en français'
            }),
            'domaine': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
