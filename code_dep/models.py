from django.db import models
from django.forms import ValidationError
from apps.noyau.commun.models import BaseModel, Reforme, Identification, Parcours, Section, Groupe, Niveau, Unite, Semestre
from apps.academique.faculte.models import Faculte
from apps.academique.enseignant.models import Enseignant



# Create your models here.
# ----------------------------------------------------------------------------------------
class Departement(BaseModel):
    chef_departement = models.ForeignKey(
        Enseignant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='chef_departement',
        verbose_name="Chef de Département"
    )
    chef_dep_adj_p = models.ForeignKey(
        Enseignant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='chef_dep_adj_p',
        verbose_name="Chef Dep. Adjoint Pédagogique"
    )
    chef_dep_adj_pg = models.ForeignKey(
        Enseignant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='chef_dep_adj_pg',
        verbose_name="Chef Dep. Adjoint Post-Graduation"
    )

    nom_ar = models.CharField(max_length=200, verbose_name="القسم", null=True)
    nom_fr = models.CharField(max_length=200, verbose_name="Département", null=True, blank=True)
    code = models.CharField(max_length=10, verbose_name="الكود", null=True, blank=True)
    sigle = models.CharField(max_length=200, verbose_name="Sigle", null=True, blank=True)
    logo = models.ImageField(upload_to='departement_logos/', null=True, blank=True, verbose_name="Logo")
    faculte = models.ForeignKey(Faculte, on_delete=models.PROTECT, verbose_name="الكلية", null=True, related_name='departements_faculte')
    telmobile = models.CharField(max_length=50, verbose_name="المحمول 1", null=True, blank=True)
    telfix1 = models.CharField(max_length=50, verbose_name="الهاتف 1", null=True, blank=True)
    telfix2 = models.CharField(max_length=50, verbose_name="الهاتف 2", null=True, blank=True)
    tel3chiffre = models.CharField(max_length=50, verbose_name="Tel 3 Chiffre", null=True, blank=True)
    fax = models.CharField(max_length=50, verbose_name="الفاكس", null=True, blank=True)
    email = models.CharField(max_length=100, verbose_name="الإيميل", null=True, blank=True)
    siteweb = models.CharField(max_length=100, verbose_name="الموقع", null=True, blank=True)
    linkedIn = models.CharField(max_length=100, verbose_name="LinkedIn", null=True, blank=True)
    facebook = models.CharField(max_length=100, verbose_name="Facebook", null=True, blank=True)
    x_twitter = models.CharField(max_length=100, verbose_name="X (Twitter)", null=True, blank=True)
    tiktok = models.CharField(max_length=100, verbose_name="TikTok", null=True, blank=True)
    telegram = models.CharField(max_length=100, verbose_name="Telegram", null=True, blank=True)
    creationALLseances = models.BooleanField(verbose_name="إنشاء جميع الدروس", default=False)
    
    def clean(self):
        # Validation pour le chef_departement
        if self.chef_departement and self.chef_departement.user.poste_principal and self.chef_departement.user.poste_principal.code != 'chef_departement':
            raise ValidationError("Le chef de département doit avoir le poste 'Chef de Département'.")
        # Validation pour le chef_dep_adj_p pédagogique
        if self.chef_dep_adj_p and self.chef_dep_adj_p.user.poste_principal and self.chef_dep_adj_p.user.poste_principal.code != 'chef_dep_adj_p':
            raise ValidationError("Le chef de département adj pédagogique doit avoir le poste 'Chef Dep. Adjoint Pédagogique'.")
        # Validation pour le vice-doyen post-graduation
        if self.chef_dep_adj_pg and self.chef_dep_adj_pg.user.poste_principal and self.chef_dep_adj_pg.user.poste_principal.code != 'chef_dep_adj_pg':
            raise ValidationError("Le chef de département adj post-graduation doit avoir le poste 'Chef Dep. Adjoint Post-Graduation'.")

    class Meta:
        verbose_name_plural = "Départements"
    
    def __str__(self):
        # Retourne nom_ar s'il existe, sinon nom_fr, sinon une chaîne par défaut
        return self.nom_ar or self.nom_fr or f"Département {self.code or 'sans nom'}"
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Appelle clean() pour les validations
        super().save(*args, **kwargs)
    


# ----------------------------------------------------------------------------------------
class Specialite(BaseModel):
    nom_ar = models.CharField(max_length=200, verbose_name="التخصص", null=True, blank=True)
    nom_fr = models.CharField(max_length=200, verbose_name="Specialite", null=True, blank=True)
    code = models.CharField(max_length=10, verbose_name="الكود", null=True, blank=True)
    departement = models.ForeignKey(Departement, on_delete=models.PROTECT, verbose_name="القسم", null=True, blank=True, related_name='Specialites_departement')
    reforme = models.ForeignKey(Reforme, on_delete=models.PROTECT, verbose_name="الإصلاح", null=True, blank=True, related_name='Specialites_reforme')
    identification = models.ForeignKey(Identification, on_delete=models.PROTECT, verbose_name="التعريف", null=True, blank=True, related_name='Specialites_identification')
    parcours = models.ForeignKey(Parcours, on_delete=models.PROTECT, verbose_name="المسار", null=True, blank=True, related_name='Specialites_parcours')
   
    class Meta:
        verbose_name_plural = "Spécialités"
    
    def __str__(self):
        # Retourne nom_ar s'il existe, sinon nom_fr, sinon une chaîne par défaut
        return f"{self.departement}/{self.reforme} : {self.nom_ar}" or \
            f"{self.departement}/{self.reforme} : {self.nom_fr}" or \
            f"Spécialité {self.code or 'sans nom'}"


    


#--------------------------------------------------------------------------------------------------------
class NivSpeDep(models.Model):
    niveau = models.ForeignKey(Niveau, on_delete=models.PROTECT, verbose_name="المستوى")
    specialite = models.ForeignKey(Specialite, on_delete=models.PROTECT, verbose_name="التخصص")
    departement = models.ForeignKey(Departement, on_delete=models.PROTECT, verbose_name="القسم")
    nbr_matieres_s1 = models.IntegerField(verbose_name="عدد المواد السداسي 1", default=0)
    nbr_matieres_s2 = models.IntegerField(verbose_name="عدد المواد السداسي 2", default=0)
    nbr_etudiants = models.IntegerField(verbose_name="عدد الطلبة", default=0)

    class Meta:
        verbose_name = "Niv-Spe-Dep"
        verbose_name_plural = "Niv-Spe-Dep"
        unique_together = ('niveau', 'specialite', 'departement')  # Assure une combinaison unique

    def __str__(self):
        return f"{self.niveau} - {self.specialite}"
    


#--------------------------------------------------------------------------------------------------------
# from django.db import models
# from django.core.exceptions import ValidationError

class NivSpeDep_SG(models.Model):
    Affectblock = [
        ('par_section', 'بالقطاع'),
        ('par_groupe', 'بالفوج'),
        ('tous_etudiants', 'جميع الطلبة'),
    ]
    niv_spe_dep = models.ForeignKey(NivSpeDep, on_delete=models.PROTECT, verbose_name="Niveau, Spécialité, Département", related_name='NivSpeDep_SGsss_NivSpeDep')
    section = models.ForeignKey(Section, on_delete=models.PROTECT, verbose_name="القطاع", null=True, blank=True)
    groupe = models.ForeignKey(Groupe, on_delete=models.PROTECT, verbose_name="الفوج", null=True, blank=True)
    nbr_etudiants_SG = models.IntegerField(verbose_name="عدد الطلبة", default=0)
    type_affectation = models.CharField(max_length=20, choices=Affectblock, default='par_groupe', verbose_name="نوع التوزيع")

    class Meta:
        verbose_name = "Niv-Spe-Dep-SG"
        verbose_name_plural = "Niv-Spe-Dep-SG"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.type_affectation == 'par_section' and not self.section:
            raise ValidationError("Une affectation 'Par Section' nécessite une section.")
        if self.type_affectation == 'par_groupe' and not self.groupe:
            raise ValidationError("Une affectation 'Par Groupe' nécessite un groupe.")
        if self.type_affectation == 'tous_etudiants' and (self.section or self.groupe):
            raise ValidationError("Une affectation 'Tous les Étudiants' ne permet ni section ni groupe.")
        if self.section and not self.groupe and self.type_affectation != 'par_section':
            raise ValidationError("Une section sans groupe nécessite un type 'Par Section'.")
        if self.groupe and self.type_affectation not in ['par_groupe', 'par_section']:
            raise ValidationError("Un groupe nécessite un type 'Par Groupe' ou 'Par Section'.")

    def __str__(self):
        base_str = f"{self.niv_spe_dep}"
        
        if self.type_affectation == 'par_section' and self.section:
            return f"{base_str} - {self.section}"
        elif self.type_affectation == 'par_groupe' and self.groupe:
            return f"{base_str} - {self.groupe}"
        elif self.type_affectation == 'tous_etudiants':
            return f"{base_str} - Tous les Étudiants"
        return base_str
        



# ----------------------------------------------------------------------------------------   
class Matiere(models.Model):
    nom_ar = models.CharField(max_length=100, verbose_name="المادة", blank=True, null=True)
    nom_fr = models.CharField(max_length=100, verbose_name="Matière", blank=True, null=True) # Optionnel si nom_ar est rempli
    code = models.CharField(max_length=20, verbose_name="Code", blank=True, null=True)
    coeff = models.FloatField(verbose_name="المعامل", default=1.0)
    credit = models.IntegerField(verbose_name="Crédit", default=0)
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT, verbose_name="الوحدة", blank=True, null=True)
    niv_spe_dep = models.ForeignKey(NivSpeDep, on_delete=models.PROTECT, verbose_name="المستوى")
    semestre = models.ForeignKey(Semestre, on_delete=models.PROTECT, verbose_name="السداسي")

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        unique_together = ('code', 'niv_spe_dep')  # Évite les doublons pour un même niveau/spécialité/département

    def __str__(self):
        return f"{self.nom_fr} - {self.niv_spe_dep}"

    def clean(self):
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError("Au moins un nom (arabe ou français) doit être fourni.")
        