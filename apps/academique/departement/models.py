# apps/academique/departement/models.py

from django.db import models
from django.core.exceptions import ValidationError
from apps.noyau.commun.models import (
    BaseModel, Reforme, Identification, Parcours,
    Section, Groupe, Niveau, Unite, Semestre
)
from apps.academique.faculte.models import Faculte
from apps.academique.enseignant.models import Enseignant


class Departement(BaseModel):
    """
    Modèle représentant un département universitaire.
    Un département appartient à une faculté et regroupe plusieurs spécialités.
    """

    # ══════════════════════════════════════════════════════════════
    # INFORMATIONS DE BASE
    # ══════════════════════════════════════════════════════════════

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="الرمز / Code",
        help_text="Ex: INFO, MATH"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="القسم / Département",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Département",
        blank=True,
        default=""
    )
    sigle = models.CharField(
        max_length=50,
        verbose_name="الاختصار / Sigle",
        blank=True,
        default="",
        help_text="Ex: INFO, MATH"
    )
    logo = models.ImageField(
        upload_to='departements/logos/%Y/',
        null=True,
        blank=True,
        verbose_name="الشعار / Logo"
    )
    faculte = models.ForeignKey(
        Faculte,
        on_delete=models.PROTECT,
        verbose_name="الكلية / Faculté",
        related_name='departements'
    )

    # ══════════════════════════════════════════════════════════════
    # RESPONSABLES
    # ══════════════════════════════════════════════════════════════

    chef_departement = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departement_as_chef',
        verbose_name="رئيس القسم / Chef de Département"
    )
    chef_dep_adj_p = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departement_as_chef_adj_p',
        verbose_name="نائب رئيس القسم للبيداغوجيا / Chef Dep. Adjoint Pédagogique"
    )
    chef_dep_adj_pg = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departement_as_chef_adj_pg',
        verbose_name="نائب رئيس القسم للدراسات العليا / Chef Dep. Adjoint Post-Graduation"
    )

    # ══════════════════════════════════════════════════════════════
    # COORDONNÉES
    # ══════════════════════════════════════════════════════════════

    telmobile = models.CharField(
        max_length=20,
        verbose_name="المحمول / Mobile",
        blank=True,
        default=""
    )
    telfix1 = models.CharField(
        max_length=20,
        verbose_name="الهاتف 1 / Tél 1",
        blank=True,
        default=""
    )
    telfix2 = models.CharField(
        max_length=20,
        verbose_name="الهاتف 2 / Tél 2",
        blank=True,
        default=""
    )
    tel3chiffre = models.CharField(
        max_length=10,
        verbose_name="رقم داخلي / Tél 3 chiffres",
        blank=True,
        default="",
        help_text="Numéro interne à 3 chiffres"
    )
    fax = models.CharField(
        max_length=20,
        verbose_name="الفاكس / Fax",
        blank=True,
        default=""
    )
    email = models.EmailField(
        max_length=100,
        verbose_name="الإيميل / Email",
        blank=True,
        default=""
    )
    siteweb = models.URLField(
        max_length=200,
        verbose_name="الموقع / Site Web",
        blank=True,
        default=""
    )

    # ══════════════════════════════════════════════════════════════
    # RÉSEAUX SOCIAUX
    # ══════════════════════════════════════════════════════════════

    facebook = models.URLField(
        max_length=200,
        verbose_name="Facebook",
        blank=True,
        default=""
    )
    x_twitter = models.URLField(
        max_length=200,
        verbose_name="X (Twitter)",
        blank=True,
        default=""
    )
    linkedIn = models.URLField(
        max_length=200,
        verbose_name="LinkedIn",
        blank=True,
        default=""
    )
    tiktok = models.URLField(
        max_length=200,
        verbose_name="TikTok",
        blank=True,
        default=""
    )
    telegram = models.URLField(
        max_length=200,
        verbose_name="Telegram",
        blank=True,
        default=""
    )

    # ══════════════════════════════════════════════════════════════
    # PARAMÈTRES
    # ══════════════════════════════════════════════════════════════

    creationALLseances = models.BooleanField(
        verbose_name="إنشاء جميع الدروس / Création auto des séances",
        default=False,
        help_text="Créer automatiquement toutes les séances"
    )

    class Meta:
        verbose_name = "قسم / Département"
        verbose_name_plural = "أقسام / Départements"
        ordering = ['faculte', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['faculte', 'code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Validation des responsables."""
        # Validation pour le chef_departement
        if self.chef_departement and hasattr(self.chef_departement, 'user') and self.chef_departement.user.poste_principal:
            if self.chef_departement.user.poste_principal.code != 'chef_departement':
                raise ValidationError({
                    'chef_departement': "رئيس القسم يجب أن يكون له منصب 'رئيس القسم' / Le chef de département doit avoir le poste 'Chef de Département'."
                })

        # Validation pour le chef_dep_adj_p
        if self.chef_dep_adj_p and hasattr(self.chef_dep_adj_p, 'user') and self.chef_dep_adj_p.user.poste_principal:
            if self.chef_dep_adj_p.user.poste_principal.code != 'chef_dep_adj_p':
                raise ValidationError({
                    'chef_dep_adj_p': "نائب رئيس القسم للبيداغوجيا يجب أن يكون له المنصب المناسب / Le chef adj. pédagogique doit avoir le poste approprié."
                })

        # Validation pour le chef_dep_adj_pg
        if self.chef_dep_adj_pg and hasattr(self.chef_dep_adj_pg, 'user') and self.chef_dep_adj_pg.user.poste_principal:
            if self.chef_dep_adj_pg.user.poste_principal.code != 'chef_dep_adj_pg':
                raise ValidationError({
                    'chef_dep_adj_pg': "نائب رئيس القسم للدراسات العليا يجب أن يكون له المنصب المناسب / Le chef adj. PG doit avoir le poste approprié."
                })

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class Specialite(BaseModel):
    """
    Modèle représentant une spécialité d'études.
    Une spécialité appartient à un département et suit une réforme/identification/parcours.
    """

    code = models.CharField(
        max_length=20,
        verbose_name="الرمز / Code",
        help_text="Ex: INFO-L, MATH-M"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="التخصص / Spécialité",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Spécialité",
        blank=True,
        default=""
    )
    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        verbose_name="القسم / Département",
        related_name='specialites'
    )
    reforme = models.ForeignKey(
        Reforme,
        on_delete=models.PROTECT,
        verbose_name="الإصلاح / Réforme",
        null=True,
        blank=True,
        related_name='specialites'
    )
    identification = models.ForeignKey(
        Identification,
        on_delete=models.PROTECT,
        verbose_name="التعريف / Identification",
        null=True,
        blank=True,
        related_name='specialites'
    )
    parcours = models.ForeignKey(
        Parcours,
        on_delete=models.PROTECT,
        verbose_name="المسار / Parcours",
        null=True,
        blank=True,
        related_name='specialites'
    )

    class Meta:
        verbose_name = "تخصص / Spécialité"
        verbose_name_plural = "تخصصات / Spécialités"
        ordering = ['departement', 'code']
        unique_together = ['code', 'departement', 'reforme']
        indexes = [
            models.Index(fields=['departement', 'code']),
            models.Index(fields=['departement', 'reforme']),
        ]

    def __str__(self):
        if self.departement and self.reforme:
            nom = self.nom_ar or self.nom_fr or self.code
            return f"{self.departement}/{self.reforme} : {nom}"
        return self.nom_ar or self.nom_fr or f"Spécialité {self.code}"

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class NivSpeDep(models.Model):
    """
    Modèle représentant la relation Niveau-Spécialité-Département.
    Définit le nombre de matières et d'étudiants pour chaque niveau d'une spécialité.
    """

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.PROTECT,
        verbose_name="المستوى / Niveau"
    )
    specialite = models.ForeignKey(
        Specialite,
        on_delete=models.PROTECT,
        verbose_name="التخصص / Spécialité"
    )
    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        verbose_name="القسم / Département"
    )
    nbr_matieres_s1 = models.IntegerField(
        verbose_name="عدد المواد السداسي 1 / Nb matières S1",
        default=0
    )
    nbr_matieres_s2 = models.IntegerField(
        verbose_name="عدد المواد السداسي 2 / Nb matières S2",
        default=0
    )
    nbr_etudiants = models.IntegerField(
        verbose_name="عدد الطلبة / Nombre d'étudiants",
        default=0
    )

    class Meta:
        verbose_name = "Niveau-Spécialité-Département"
        verbose_name_plural = "Niveaux-Spécialités-Départements"
        unique_together = ('niveau', 'specialite', 'departement')
        indexes = [
            models.Index(fields=['departement', 'specialite', 'niveau']),
        ]

    def __str__(self):
        return f"{self.niveau} - {self.specialite}"


class NivSpeDep_SG(models.Model):
    """
    Modèle représentant la relation Niveau-Spécialité-Département avec Section/Groupe.
    Gère l'affectation des étudiants par section, groupe ou tous les étudiants.
    """

    TYPE_AFFECTATION_CHOICES = [
        ('par_section', 'بالقطاع / Par Section'),
        ('par_groupe', 'بالفوج / Par Groupe'),
        ('tous_etudiants', 'جميع الطلبة / Tous les Étudiants'),
    ]

    niv_spe_dep = models.ForeignKey(
        NivSpeDep,
        on_delete=models.PROTECT,
        verbose_name="المستوى-التخصص-القسم / Niveau-Spécialité-Département",
        related_name='sections_groupes'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        verbose_name="القطاع / Section",
        null=True,
        blank=True
    )
    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.PROTECT,
        verbose_name="الفوج / Groupe",
        null=True,
        blank=True
    )
    nbr_etudiants_SG = models.IntegerField(
        verbose_name="عدد الطلبة / Nombre d'étudiants",
        default=0
    )
    type_affectation = models.CharField(
        max_length=20,
        choices=TYPE_AFFECTATION_CHOICES,
        default='par_groupe',
        verbose_name="نوع التوزيع / Type d'affectation"
    )

    class Meta:
        verbose_name = "Niv-Spe-Dep avec Section/Groupe"
        verbose_name_plural = "Niv-Spe-Dep avec Sections/Groupes"

    def clean(self):
        """Validation des affectations."""
        if self.type_affectation == 'par_section' and not self.section:
            raise ValidationError({
                'section': "Une affectation 'Par Section' nécessite une section."
            })
        if self.type_affectation == 'par_groupe' and not self.groupe:
            raise ValidationError({
                'groupe': "Une affectation 'Par Groupe' nécessite un groupe."
            })
        if self.type_affectation == 'tous_etudiants' and (self.section or self.groupe):
            raise ValidationError(
                "Une affectation 'Tous les Étudiants' ne permet ni section ni groupe."
            )
        if self.section and not self.groupe and self.type_affectation != 'par_section':
            raise ValidationError({
                'type_affectation': "Une section sans groupe nécessite un type 'Par Section'."
            })
        if self.groupe and self.type_affectation not in ['par_groupe', 'par_section']:
            raise ValidationError({
                'type_affectation': "Un groupe nécessite un type 'Par Groupe' ou 'Par Section'."
            })

    def __str__(self):
        base_str = f"{self.niv_spe_dep}"

        if self.type_affectation == 'par_section' and self.section:
            return f"{base_str} - {self.section}"
        elif self.type_affectation == 'par_groupe' and self.groupe:
            return f"{base_str} - {self.groupe}"
        elif self.type_affectation == 'tous_etudiants':
            return f"{base_str} - Tous les Étudiants"
        return base_str


class Matiere(models.Model):
    """
    Modèle représentant une matière/module d'enseignement.
    Une matière appartient à un niveau-spécialité-département et à un semestre.
    """

    code = models.CharField(
        max_length=20,
        verbose_name="الرمز / Code",
        blank=True,
        default=""
    )
    nom_ar = models.CharField(
        max_length=100,
        verbose_name="المادة / Matière",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=100,
        verbose_name="Matière",
        blank=True,
        default=""
    )
    coeff = models.FloatField(
        verbose_name="المعامل / Coefficient",
        default=1.0
    )
    credit = models.IntegerField(
        verbose_name="الرصيد / Crédit",
        default=0
    )
    unite = models.ForeignKey(
        Unite,
        on_delete=models.PROTECT,
        verbose_name="الوحدة / Unité",
        null=True,
        blank=True
    )
    niv_spe_dep = models.ForeignKey(
        NivSpeDep,
        on_delete=models.PROTECT,
        verbose_name="المستوى / Niveau",
        related_name='matieres'
    )
    semestre = models.ForeignKey(
        Semestre,
        on_delete=models.PROTECT,
        verbose_name="السداسي / Semestre"
    )

    class Meta:
        verbose_name = "مادة / Matière"
        verbose_name_plural = "مواد / Matières"
        ordering = ['niv_spe_dep', 'semestre', 'code']
        unique_together = ('code', 'niv_spe_dep')
        indexes = [
            models.Index(fields=['niv_spe_dep', 'semestre']),
        ]

    def __str__(self):
        nom = self.nom_fr or self.nom_ar or self.code
        return f"{nom} - {self.niv_spe_dep}"

    def clean(self):
        """Validation des champs."""
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError(
                "Au moins un nom (arabe ou français) doit être fourni."
            )

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code
