from django import forms
from django.contrib.auth.models import User
from .models import *
from apps.academique.affectation.models import *


class profileUpdate_Dep_Form(forms.ModelForm):
    class Meta:
        model = Departement
        # fields = '__all__'
        exclude = ('observation', 'chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg', 'faculte', 'creationALLseances', 'logo', 'code')
        # exclude = ('dep_fk_user','dep_fk_fac','dep_fk_ens')




#-------------------------------------------------------
class Ens_Vac_Form(forms.Form):
    class Meta:
        model = Ens_Dep
        fields = [
            'matricule',
            'codeIns',
            'BAC_annee',
            'nom_ar',
            'prenom_ar',
            'nom_fr',
            'prenom_fr',
            'date_nais',
            ]
        


from django.contrib import admin
from .models import NivSpeDep_SG

class NivSpeDepSGForm(forms.ModelForm):
    class Meta:
        model = NivSpeDep_SG
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        # Validation personnalisée (déjà dans le modèle, mais peut être redéfinie ici si besoin)
        return cleaned_data

# @admin.register(NivSpeDep_SG)
class NivSpeDepSGAdmin(admin.ModelAdmin):
    form = NivSpeDepSGForm
    # Autres configurations...





class profileUpdate_Etu_Form(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = '__all__'
        # exclude = ('ens_categorie','ens_inscrit','ens_fk_user','ens_codeIns')
        exclude = ('user',)







from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import Matiere, NivSpeDep_SG
from apps.noyau.commun.models import Semestre 
from apps.academique.affectation.models import Amphi_Dep, Salle_Dep, Laboratoire_Dep, Classe, Ens_Dep

class ClasseEditForm(forms.ModelForm):
    # Champs pour le lieu générique
    lieu_type = forms.ChoiceField(
        label="نوع المكان",
        choices=[
            ('', '--- اختر نوع المكان ---'),
            ('amphi', 'مدرج'),
            ('salle', 'قاعة'),
            ('labo', 'مخبر')
        ],
        required=False
    )
    lieu_id = forms.IntegerField(
        label="المكان",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Classe
        fields = [
            'semestre', 'matiere', 'enseignant', 'niv_spe_dep_sg',
            'jour', 'temps', 'type', 'observation'
        ]
        widgets = {
            'semestre': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
            'niv_spe_dep_sg': forms.Select(attrs={'class': 'form-control'}),
            'jour': forms.Select(attrs={'class': 'form-control'}),
            'temps': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si on édite une classe existante, pré-remplir le lieu
        if self.instance and self.instance.pk and self.instance.lieu:
            content_type = self.instance.content_type
            
            if content_type.model == 'amphi_dep':
                self.fields['lieu_type'].initial = 'amphi'
                self.fields['lieu_id'].initial = self.instance.object_id
                
                # Charger les amphithéâtres
                amphitheatres = Amphi_Dep.objects.filter(
                    departement=self.instance.enseignant.departement
                )
                self.fields['lieu_id'].widget = forms.Select(
                    choices=[('', '--- اختر المدرج ---')] + 
                    [(a.id, str(a)) for a in amphitheatres],
                    attrs={'class': 'form-control'}
                )
                
            elif content_type.model == 'salle_dep':
                self.fields['lieu_type'].initial = 'salle'
                self.fields['lieu_id'].initial = self.instance.object_id
                
                # Charger les salles
                salles = Salle_Dep.objects.filter(
                    departement=self.instance.enseignant.departement
                )
                self.fields['lieu_id'].widget = forms.Select(
                    choices=[('', '--- اختر القاعة ---')] + 
                    [(s.id, str(s)) for s in salles],
                    attrs={'class': 'form-control'}
                )
                
            elif content_type.model == 'Laboratoire_Dep':
                self.fields['lieu_type'].initial = 'labo'
                self.fields['lieu_id'].initial = self.instance.object_id
                
                # Charger les laboratoires
                labos = Laboratoire_Dep.objects.filter(
                    departement=self.instance.enseignant.departement
                )
                self.fields['lieu_id'].widget = forms.Select(
                    choices=[('', '--- اختر المخبر ---')] + 
                    [(l.id, str(l)) for l in labos],
                    attrs={'class': 'form-control'}
                )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Gérer le lieu générique
        lieu_type = self.cleaned_data.get('lieu_type')
        lieu_id = self.cleaned_data.get('lieu_id')
        
        if lieu_type and lieu_id:
            if lieu_type == 'amphi':
                content_type = ContentType.objects.get_for_model(Amphi_Dep)
            elif lieu_type == 'salle':
                content_type = ContentType.objects.get_for_model(Salle_Dep)
            elif lieu_type == 'labo':
                content_type = ContentType.objects.get_for_model(Laboratoire_Dep)
            else:
                content_type = None
            
            if content_type:
                instance.content_type = content_type
                instance.object_id = lieu_id
        
        if commit:
            instance.save()
        
        return instance