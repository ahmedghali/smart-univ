# apps/academique/universite/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Universite, Domaine


class UniversiteForm(forms.ModelForm):
    """
    Formulaire complet pour la création et modification d'une université.
    Utilisé par les administrateurs système.
    """

    class Meta:
        model = Universite
        fields = [
            'code', 'nom_ar', 'nom_fr', 'sigle', 'logo',
            'recteur', 'vice_rect_p', 'vice_rect_pg',
            'wilaya', 'adresse',
            'telmobile', 'telfix1', 'telfix2', 'fax', 'email', 'siteweb',
            'facebook', 'x_twitter', 'linkedIn', 'tiktok', 'telegram'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: USTHB',
                'dir': 'ltr'
            }),
            'nom_ar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الجامعة بالعربية',
                'dir': 'rtl'
            }),
            'nom_fr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'université en français',
                'dir': 'ltr'
            }),
            'sigle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: USTHB',
                'dir': 'ltr'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'recteur': forms.Select(attrs={
                'class': 'form-select',
            }),
            'vice_rect_p': forms.Select(attrs={
                'class': 'form-select',
            }),
            'vice_rect_pg': forms.Select(attrs={
                'class': 'form-select',
            }),
            'wilaya': forms.Select(attrs={
                'class': 'form-select',
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'العنوان / Adresse'
            }),
            'telmobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0555123456',
                'dir': 'ltr'
            }),
            'telfix1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023123456',
                'dir': 'ltr'
            }),
            'telfix2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023654321',
                'dir': 'ltr'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023789456',
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@universite.dz',
                'dir': 'ltr'
            }),
            'siteweb': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.universite.dz',
                'dir': 'ltr'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/...',
                'dir': 'ltr'
            }),
            'x_twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://x.com/...',
                'dir': 'ltr'
            }),
            'linkedIn': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/...',
                'dir': 'ltr'
            }),
            'tiktok': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tiktok.com/@...',
                'dir': 'ltr'
            }),
            'telegram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://t.me/...',
                'dir': 'ltr'
            }),
        }

    def clean(self):
        """Validation supplémentaire."""
        cleaned_data = super().clean()
        nom_ar = cleaned_data.get('nom_ar')
        nom_fr = cleaned_data.get('nom_fr')

        # Au moins un nom doit être renseigné
        if not nom_ar and not nom_fr:
            raise ValidationError(
                "يجب إدخال اسم واحد على الأقل (عربي أو فرنسي) / Au moins un nom doit être renseigné."
            )

        return cleaned_data


class UniversiteProfileUpdateForm(forms.ModelForm):
    """
    Formulaire de mise à jour du profil de l'université.
    Utilisé par le recteur pour mettre à jour les informations de son université.
    Exclut les champs sensibles comme le code et les responsables.
    """

    class Meta:
        model = Universite
        fields = [
            'nom_ar', 'nom_fr', 'sigle', 'logo',
            'adresse',
            'telmobile', 'telfix1', 'telfix2', 'fax', 'email', 'siteweb',
            'facebook', 'x_twitter', 'linkedIn', 'tiktok', 'telegram'
        ]
        widgets = {
            'nom_ar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الجامعة بالعربية',
                'dir': 'rtl'
            }),
            'nom_fr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'université en français',
                'dir': 'ltr'
            }),
            'sigle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: USTHB',
                'dir': 'ltr'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'العنوان الكامل / Adresse complète',
                'rows': 2
            }),
            'telmobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0555123456',
                'dir': 'ltr'
            }),
            'telfix1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023123456',
                'dir': 'ltr'
            }),
            'telfix2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023654321',
                'dir': 'ltr'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '023789456',
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@universite.dz',
                'dir': 'ltr'
            }),
            'siteweb': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.universite.dz',
                'dir': 'ltr'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/...',
                'dir': 'ltr'
            }),
            'x_twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://x.com/...',
                'dir': 'ltr'
            }),
            'linkedIn': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/...',
                'dir': 'ltr'
            }),
            'tiktok': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tiktok.com/@...',
                'dir': 'ltr'
            }),
            'telegram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://t.me/...',
                'dir': 'ltr'
            }),
        }

    def clean(self):
        """Validation supplémentaire."""
        cleaned_data = super().clean()
        nom_ar = cleaned_data.get('nom_ar')
        nom_fr = cleaned_data.get('nom_fr')

        if not nom_ar and not nom_fr:
            raise ValidationError(
                "يجب إدخال اسم واحد على الأقل (عربي أو فرنسي) / Au moins un nom doit être renseigné."
            )

        return cleaned_data


class DomaineForm(forms.ModelForm):
    """
    Formulaire pour la création et modification d'un domaine d'études.
    """

    class Meta:
        model = Domaine
        fields = ['code', 'nom_ar', 'nom_fr', 'universite']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: ST, SNV',
                'dir': 'ltr'
            }),
            'nom_ar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الميدان بالعربية',
                'dir': 'rtl'
            }),
            'nom_fr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du domaine en français',
                'dir': 'ltr'
            }),
            'universite': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def clean(self):
        """Validation supplémentaire."""
        cleaned_data = super().clean()
        nom_ar = cleaned_data.get('nom_ar')
        nom_fr = cleaned_data.get('nom_fr')

        if not nom_ar and not nom_fr:
            raise ValidationError(
                "يجب إدخال اسم واحد على الأقل (عربي أو فرنسي) / Au moins un nom doit être renseigné."
            )

        return cleaned_data
