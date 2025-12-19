# apps/noyau/commun/models.py

from django.db import models
from django.core.exceptions import ValidationError


class BaseModel(models.Model):
    """
    Modèle abstrait avec champs d'audit.
    Utilisé comme base pour tous les modèles de l'application.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء / Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التعديل / Date de modification"
    )
    observation = models.TextField(
        verbose_name="الملاحظة / Observation",
        blank=True,
        default=""
    )

    class Meta:
        abstract = True


class Poste(BaseModel):
    """
    Représente un rôle/poste dans le système universitaire.
    Supporte le bilinguisme Arabe/Français.
    """
    
    TYPE_CHOICES = [
        ('enseignant', 'أستاذ'),
        ('etudiant', 'طالب'),
        ('admin', 'إداري'),
        ('personnel', 'موظف'),
        ('invite', 'ضيف'),
    ]
    
    # ══════════════════════════════════════════════════════════════
    # IDENTIFICATION
    # ══════════════════════════════════════════════════════════════
    
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="الرمز",
        help_text="مثال: ENS, ETU, CHF_DEP..."
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='personnel',
        verbose_name="النوع"
    )
    
    # ══════════════════════════════════════════════════════════════
    # LIBELLÉS BILINGUES
    # ══════════════════════════════════════════════════════════════
    
    nom_ar = models.CharField(
        max_length=100, 
        verbose_name="المنصب",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=100, 
        verbose_name="Poste (FR)",
        blank=True,
        default=""
    )
    nom_ar_mini = models.CharField(
        max_length=20, 
        verbose_name="الإختصار",
        blank=True,
        default=""
    )
    nom_fr_mini = models.CharField(
        max_length=20, 
        verbose_name="Abréviation (FR)",
        blank=True,
        default=""
    )
    
    # ══════════════════════════════════════════════════════════════
    # HIÉRARCHIE & STATUT
    # ══════════════════════════════════════════════════════════════
    
    niveau = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="المستوى الهرمي",
        help_text="0=قاعدة، 10=إدارة عليا"
    )
    est_actif = models.BooleanField(
        default=True, 
        verbose_name="نشط"
    )

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type', 'niveau']),
        ]
        verbose_name = "منصب"
        verbose_name_plural = "المناصب"
        ordering = ['-niveau', 'nom_ar']
    
    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code
    
    def clean(self):
        """Valide qu'au moins un nom est renseigné."""
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError("يجب إدخال اسم واحد على الأقل (عربي أو فرنسي)")
    
    # ══════════════════════════════════════════════════════════════
    # MÉTHODES UTILES
    # ══════════════════════════════════════════════════════════════
    
    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code
    
    def get_nom_mini(self, langue='ar'):
        """Retourne l'abréviation selon la langue."""
        if langue == 'ar':
            return self.nom_ar_mini or self.nom_fr_mini or self.code[:3]
        return self.nom_fr_mini or self.nom_ar_mini or self.code[:3]
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ══════════════════════════════════════════════════════════════
# ANNÉE UNIVERSITAIRE
# ══════════════════════════════════════════════════════════════

class AnneeUniversitaire(BaseModel):
    """
    Représente une année universitaire (ex: 2024-2025).
    Une seule année peut être marquée comme courante.
    """
    nom = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="السنة الجامعية / Année universitaire",
        help_text="مثال: 2024-2025 / Exemple: 2024-2025"
    )
    date_debut = models.DateField(
        verbose_name="تاريخ البداية / Date de début"
    )
    date_fin = models.DateField(
        verbose_name="تاريخ النهاية / Date de fin"
    )
    est_courante = models.BooleanField(
        default=False,
        verbose_name="السنة الحالية / Année courante"
    )

    class Meta:
        verbose_name = "سنة جامعية / Année universitaire"
        verbose_name_plural = "سنوات جامعية / Années universitaires"
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['est_courante']),
            models.Index(fields=['date_debut', 'date_fin']),
        ]

    def __str__(self):
        return self.nom

    def clean(self):
        """Validation de la cohérence des dates."""
        if self.date_debut and self.date_fin:
            if self.date_debut >= self.date_fin:
                raise ValidationError(
                    "تاريخ البداية يجب أن يكون قبل تاريخ النهاية / "
                    "La date de début doit être antérieure à la date de fin."
                )

    @classmethod
    def get_courante(cls):
        """Retourne l'année universitaire courante."""
        try:
            return cls.objects.get(est_courante=True)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            return cls.objects.filter(est_courante=True).order_by('-date_debut').first()


# ══════════════════════════════════════════════════════════════
# GÉOGRAPHIE
# ══════════════════════════════════════════════════════════════

class Pays(BaseModel):
    """Représente un pays."""
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="الرمز / Code",
        help_text="Code ISO 3 lettres"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="البلد",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Pays",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "بلد / Pays"
        verbose_name_plural = "بلدان / Pays"
        ordering = ['nom_ar', 'nom_fr']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Validation: au moins un nom doit être renseigné."""
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError(
                "يجب إدخال اسم واحد على الأقل / Au moins un nom doit être renseigné"
            )

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class Wilaya(BaseModel):
    """
    Représente une wilaya (province) algérienne.
    Support bilingue arabe/français.
    """

    code = models.CharField(
        max_length=2,
        unique=True,
        verbose_name="الرمز",
        help_text="01-58"
    )
    codePostal = models.CharField(
        max_length=5,
        verbose_name="الرمز البريدي / Code postal",
        blank=True,
        default=""
    )
    
    nom_ar = models.CharField(
        max_length=100,
        verbose_name="الولاية",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=100,
        verbose_name="Wilaya (FR)",
        blank=True,
        default=""
    )

    pays = models.ForeignKey(
        Pays,
        on_delete=models.PROTECT,
        verbose_name="البلد / Pays",
        related_name='wilayas',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "ولاية"
        verbose_name_plural = "الولايات"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom_ar or self.nom_fr}"

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr
        return self.nom_fr or self.nom_ar
    

# ══════════════════════════════════════════════════════════════
# INFRASTRUCTURE
# ══════════════════════════════════════════════════════════════

class Amphi(BaseModel):
    """Représente un amphithéâtre."""
    numero = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرقم / Numéro"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="المدرج",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Amphithéâtre",
        blank=True,
        default=""
    )
    capacite = models.PositiveIntegerField(
        verbose_name="السعة / Capacité",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "مدرج / Amphithéâtre"
        verbose_name_plural = "مدرجات / Amphithéâtres"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['numero']),
        ]

    def __str__(self):
        return f"Amphi {self.numero}"


class Salle(BaseModel):
    """Représente une salle de cours."""
    numero = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرقم / Numéro"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="القاعة",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Salle",
        blank=True,
        default=""
    )
    capacite = models.PositiveIntegerField(
        verbose_name="السعة / Capacité",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "قاعة / Salle"
        verbose_name_plural = "قاعات / Salles"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['numero']),
        ]

    def __str__(self):
        return f"Salle {self.numero}"


class Laboratoire(BaseModel):
    """Représente un laboratoire."""

    TYPE_CHOICES = [
        ('informatique', 'إعلام آلي / Informatique'),
        ('physique', 'فيزياء / Physique'),
        ('chimie', 'كيمياء / Chimie'),
        ('biologie', 'بيولوجيا / Biologie'),
        ('geologie', 'جيولوجيا / Géologie'),
        ('autres', 'أخرى / Autres'),
    ]

    numero = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرقم / Numéro"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="المخبر",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Laboratoire",
        blank=True,
        default=""
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='autres',
        verbose_name="نوع المخبر / Type"
    )
    capacite = models.PositiveIntegerField(
        verbose_name="السعة / Capacité",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "مخبر / Laboratoire"
        verbose_name_plural = "مخابر / Laboratoires"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"Lab {self.numero} ({self.get_type_display()})"


# ══════════════════════════════════════════════════════════════
# ORGANISATION PÉDAGOGIQUE
# ══════════════════════════════════════════════════════════════

class Semestre(BaseModel):
    """Représente un semestre dans l'année universitaire."""
    numero = models.PositiveSmallIntegerField(
        verbose_name="الرقم / Numéro",
        help_text="1, 2, 3, etc."
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code",
        help_text="S1, S2, etc."
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="السداسي",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Semestre",
        blank=True,
        default=""
    )
    date_debut = models.DateField(
        verbose_name="تاريخ البداية / Date de début",
        blank=True,
        null=True
    )
    date_fin = models.DateField(
        verbose_name="تاريخ النهاية / Date de fin",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "سداسي / Semestre"
        verbose_name_plural = "سداسيات / Semestres"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['numero']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Grade(BaseModel):
    """Représente un grade académique (Professeur, MCA, MCB, etc.)."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الرتبة",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Grade",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "رتبة / Grade"
        verbose_name_plural = "رتب / Grades"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Diplome(BaseModel):
    """Représente un diplôme (Licence, Master, Doctorat, etc.)."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الشهادة",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Diplôme",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "شهادة / Diplôme"
        verbose_name_plural = "شهادات / Diplômes"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Cycle(BaseModel):
    """Représente un cycle d'études (Licence, Master, Doctorat)."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الطور",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Cycle",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "طور / Cycle"
        verbose_name_plural = "أطوار / Cycles"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Niveau(BaseModel):
    """Représente un niveau d'études (L1, L2, L3, M1, M2, etc.)."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="المستوى",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Niveau",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "مستوى / Niveau"
        verbose_name_plural = "مستويات / Niveaux"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Parcours(BaseModel):
    """Représente un parcours d'études."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="المسار",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Parcours",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "مسار / Parcours"
        verbose_name_plural = "مسارات / Parcours"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Unite(BaseModel):
    """Représente une unité d'enseignement (UE)."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الوحدة",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Unité",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "وحدة / Unité"
        verbose_name_plural = "وحدات / Unités"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Groupe(BaseModel):
    """Représente un groupe d'étudiants."""
    numero = models.CharField(
        max_length=5,
        verbose_name="الرقم / Numéro"
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الفوج",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Groupe",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "فوج / Groupe"
        verbose_name_plural = "أفواج / Groupes"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['numero']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Groupe {self.numero}"


class Section(BaseModel):
    """Représente une section d'étudiants."""
    numero = models.CharField(
        max_length=5,
        verbose_name="الرقم / Numéro"
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="القطاع",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Section",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "قطاع / Section"
        verbose_name_plural = "قطاعات / Sections"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['numero']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Section {self.numero}"


class Session(BaseModel):
    """Représente une session d'examens (Normale, Rattrapage)."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الدورة",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Session",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "دورة / Session"
        verbose_name_plural = "دورات / Sessions"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Reforme(BaseModel):
    """Représente une réforme pédagogique."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الإصلاح",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Réforme",
        blank=True,
        default=""
    )
    cycle = models.ForeignKey(
        Cycle,
        on_delete=models.PROTECT,
        verbose_name="الطور / Cycle",
        related_name='reformes',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "إصلاح / Réforme"
        verbose_name_plural = "إصلاحات / Réformes"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Identification(BaseModel):
    """Représente un type d'identification."""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="الرمز / Code"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="التعريف / Identification",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Type d'identification",
        blank=True,
        default=""
    )

    class Meta:
        verbose_name = "التعريف / Identification"
        verbose_name_plural = "التعاريف / Identifications"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code