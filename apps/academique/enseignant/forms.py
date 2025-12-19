# apps/academique/enseignant/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Enseignant


class UserUpdateForm(forms.ModelForm):
    """Formulaire pour mettre à jour les informations de l'utilisateur."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
        labels = {
            'first_name': 'الاسم الأول / Prénom',
            'last_name': 'اللقب / Nom',
            'email': 'البريد الإلكتروني / Email',
        }


class EnseignantForm(forms.ModelForm):
    """Formulaire complet pour créer/modifier un enseignant."""

    class Meta:
        model = Enseignant
        fields = [
            'user',
            'civilite',
            'nom_ar',
            'prenom_ar',
            'nom_fr',
            'prenom_fr',
            'date_nais',
            'sex',
            'sitfam',
            'matricule',
            'codeIns',
            'bac_annee',
            'date_Recrut',
            'telmobile1',
            'telmobile2',
            'telfix',
            'fax',
            'email_perso',
            'email_prof',
            'adresse',
            'wilaya',
            'diplome',
            'specialite_ar',
            'specialite_fr',
            'grade',
            'inscritProgres',
            'inscritMoodle',
            'inscritSNDL',
            'googlescholar',
            'researchgate',
            'orcid_id',
            'linkedIn',
            'facebook',
            'x_twitter',
            'tiktok',
            'telegram',
            'vacAcademique',
            'maladie',
        ]
        widgets = {
            'date_nais': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_Recrut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-select'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'sitfam': forms.Select(attrs={'class': 'form-select'}),
            'nom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اللقب'}),
            'prenom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الإسم'}),
            'nom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ENS2024001'}),
            'codeIns': forms.TextInput(attrs={'class': 'form-control'}),
            'bac_annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2010'}),
            'telmobile1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'telmobile2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'telfix': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email_perso': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@email.com'}),
            'email_prof': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'prenom.nom@univ.dz'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'wilaya': forms.Select(attrs={'class': 'form-select'}),
            'diplome': forms.Select(attrs={'class': 'form-select'}),
            'specialite_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'التخصص'}),
            'specialite_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Spécialité'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'googlescholar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://scholar.google.com/...'}),
            'researchgate': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.researchgate.net/...'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0002-1234-5678'}),
            'linkedIn': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/...'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'x_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/...'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
            'inscritProgres': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscritMoodle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscritSNDL': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vacAcademique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maladie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProfileUpdateEnsForm(forms.ModelForm):
    """Formulaire pour mettre à jour le profil d'un enseignant (informations modifiables)."""

    class Meta:
        model = Enseignant
        fields = [
            # Informations personnelles
            'civilite',
            'nom_ar',
            'prenom_ar',
            'nom_fr',
            'prenom_fr',
            'date_nais',
            'sex',
            'sitfam',
            'matricule',
            'codeIns',
            # Informations professionnelles
            'grade',
            'diplome',
            'specialite_ar',
            'specialite_fr',
            'bac_annee',
            'date_Recrut',
            'vacAcademique',
            'maladie',
            # Coordonnées
            'telmobile1',
            'telmobile2',
            'telfix',
            'fax',
            'email_perso',
            'email_prof',
            'adresse',
            'wilaya',
            # Plateformes académiques
            'inscritProgres',
            'inscritMoodle',
            'inscritSNDL',
            # Réseaux sociaux et académiques
            'googlescholar',
            'researchgate',
            'orcid_id',
            'linkedIn',
            'facebook',
            'x_twitter',
            'tiktok',
            'telegram',
            # Statistiques Google Scholar
            'scholar_publications_count',
            'scholar_citations_count',
            'scholar_h_index',
            'scholar_i10_index',
        ]
        widgets = {
            'date_nais': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_Recrut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-select'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'sitfam': forms.Select(attrs={'class': 'form-select'}),
            'nom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اللقب'}),
            'prenom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الإسم'}),
            'nom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ENS2024001'}),
            'codeIns': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'diplome': forms.Select(attrs={'class': 'form-select'}),
            'specialite_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'التخصص'}),
            'specialite_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Spécialité'}),
            'bac_annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2010'}),
            'telmobile1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'telmobile2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'telfix': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email_perso': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@email.com'}),
            'email_prof': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'prenom.nom@univ.dz'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'wilaya': forms.Select(attrs={'class': 'form-select'}),
            'googlescholar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://scholar.google.com/...'}),
            'researchgate': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.researchgate.net/...'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0002-1234-5678'}),
            'linkedIn': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/...'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'x_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/...'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
            'inscritProgres': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscritMoodle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscritSNDL': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vacAcademique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maladie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scholar_publications_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'scholar_citations_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'scholar_h_index': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'scholar_i10_index': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class AdminEnseignantForm(forms.ModelForm):
    """Formulaire administratif pour modifier les informations sensibles d'un enseignant."""

    class Meta:
        model = Enseignant
        fields = [
            'matricule',
            'codeIns',
            'bac_annee',
            'date_Recrut',
            'grade',
            'vacAcademique',
            'maladie',
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ENS2024001'}),
            'codeIns': forms.TextInput(attrs={'class': 'form-control'}),
            'bac_annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2010'}),
            'date_Recrut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'vacAcademique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maladie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
