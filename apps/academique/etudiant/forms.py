# apps/academique/etudiant/forms.py

from django import forms
from .models import Etudiant


class EtudiantForm(forms.ModelForm):
    """Formulaire complet pour créer/modifier un étudiant."""

    class Meta:
        model = Etudiant
        fields = [
            'user',
            'civilite',
            'nom_ar',
            'prenom_ar',
            'nom_fr',
            'prenom_fr',
            'date_nais',
            'sexe',
            'sit_fam',
            'matricule',
            'num_ins',
            'bac_annee',
            'niv_spe_dep_sg',
            'delegue',
            'tel_mobile1',
            'tel_mobile2',
            'tel_fix',
            'fax',
            'email_perso',
            'email_prof',
            'adresse',
            'wilaya',
            'inscrit_progres',
            'inscrit_moodle',
            'inscrit_sndl',
            'est_inscrit',
            'google_scholar',
            'researchgate',
            'orcid_id',
            'linkedin',
            'facebook',
            'x_twitter',
            'tiktok',
            'telegram',
            'en_vac_aca',
            'en_maladie',
        ]
        widgets = {
            'date_nais': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-select'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'sit_fam': forms.Select(attrs={'class': 'form-select'}),
            'nom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اللقب'}),
            'prenom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الإسم'}),
            'nom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ETU2024001'}),
            'num_ins': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro d\'inscription'}),
            'bac_annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2020'}),
            'niv_spe_dep_sg': forms.Select(attrs={'class': 'form-select'}),
            'tel_mobile1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'tel_mobile2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'tel_fix': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email_perso': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@email.com'}),
            'email_prof': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'prenom.nom@univ.dz'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'wilaya': forms.Select(attrs={'class': 'form-select'}),
            'google_scholar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://scholar.google.com/...'}),
            'researchgate': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.researchgate.net/...'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0002-1234-5678'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/...'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'x_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/...'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
            'delegue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscrit_progres': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscrit_moodle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscrit_sndl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_inscrit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'en_vac_aca': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'en_maladie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProfileUpdateEtudForm(forms.ModelForm):
    """Formulaire pour mettre à jour le profil d'un étudiant (informations modifiables)."""

    class Meta:
        model = Etudiant
        fields = [
            # Informations personnelles
            'civilite',
            'nom_ar',
            'prenom_ar',
            'nom_fr',
            'prenom_fr',
            'date_nais',
            'sexe',
            'sit_fam',
            # Coordonnées
            'tel_mobile1',
            'tel_mobile2',
            'tel_fix',
            'fax',
            'email_perso',
            'email_prof',
            'adresse',
            'wilaya',
            # Plateformes académiques
            'inscrit_progres',
            'inscrit_moodle',
            'inscrit_sndl',
            'est_inscrit',
            # Réseaux sociaux et académiques
            'google_scholar',
            'researchgate',
            'orcid_id',
            'linkedin',
            'facebook',
            'x_twitter',
            'tiktok',
            'telegram',
        ]
        widgets = {
            'date_nais': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-select'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'sit_fam': forms.Select(attrs={'class': 'form-select'}),
            'nom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اللقب'}),
            'prenom_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الإسم'}),
            'nom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom_fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'tel_mobile1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'tel_mobile2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0XXX XX XX XX'}),
            'tel_fix': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email_perso': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@email.com'}),
            'email_prof': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'prenom.nom@univ.dz'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'wilaya': forms.Select(attrs={'class': 'form-select'}),
            'google_scholar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://scholar.google.com/...'}),
            'researchgate': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.researchgate.net/...'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0002-1234-5678'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/...'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'x_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/...'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
            'inscrit_progres': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscrit_moodle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscrit_sndl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_inscrit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminEtudiantForm(forms.ModelForm):
    """Formulaire administratif pour modifier les informations sensibles d'un étudiant."""

    class Meta:
        model = Etudiant
        fields = [
            'matricule',
            'num_ins',
            'bac_annee',
            'niv_spe_dep_sg',
            'delegue',
            'en_vac_aca',
            'en_maladie',
            'est_actif',
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ETU2024001'}),
            'num_ins': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro d\'inscription'}),
            'bac_annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2020'}),
            'niv_spe_dep_sg': forms.Select(attrs={'class': 'form-select'}),
            'delegue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'en_vac_aca': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'en_maladie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
