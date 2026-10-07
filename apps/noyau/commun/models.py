# apps/noyau/commun/models.py

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Modèle abstrait avec champs d'audit.
    Utilisé comme base pour tous les modèles de l'application.
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء / Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل / Date de modification")
    observation = models.TextField(verbose_name="الملاحظة / Observation", blank=True, default="")

    class Meta:
        abstract = True


class Poste(BaseModel):
    """
    Représente un rôle/poste dans le système universitaire.
    Supporte le bilinguisme Arabe/Français.
    """

    TYPE_CHOICES = [
        ("enseignant", "أستاذ"),
        ("etudiant", "طالب"),
        ("admin", "إداري"),
        ("personnel", "موظف"),
        ("invite", "ضيف"),
    ]

    # ══════════════════════════════════════════════════════════════
    # IDENTIFICATION
    # ══════════════════════════════════════════════════════════════

    code = models.CharField(max_length=50, unique=True, verbose_name="الرمز", help_text="مثال: ENS, ETU, CHF_DEP...")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="personnel", verbose_name="النوع")

    # ══════════════════════════════════════════════════════════════
    # LIBELLÉS BILINGUES
    # ══════════════════════════════════════════════════════════════

    nom_ar = models.CharField(max_length=100, verbose_name="المنصب", blank=True, default="")
    nom_fr = models.CharField(max_length=100, verbose_name="Poste (FR)", blank=True, default="")
    nom_ar_mini = models.CharField(max_length=20, verbose_name="الإختصار", blank=True, default="")
    nom_fr_mini = models.CharField(max_length=20, verbose_name="Abréviation (FR)", blank=True, default="")

    # ══════════════════════════════════════════════════════════════
    # HIÉRARCHIE & STATUT
    # ══════════════════════════════════════════════════════════════

    niveau = models.PositiveSmallIntegerField(
        default=0, verbose_name="المستوى الهرمي", help_text="0=قاعدة، 10=إدارة عليا"
    )
    est_actif = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["type", "niveau"]),
        ]
        verbose_name = "منصب"
        verbose_name_plural = "المناصب"
        ordering = ["-niveau", "nom_ar"]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Valide qu'au moins un nom est renseigné."""
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError("يجب إدخال اسم واحد على الأقل (عربي أو فرنسي)")

    # ══════════════════════════════════════════════════════════════
    # MÉTHODES UTILES
    # ══════════════════════════════════════════════════════════════

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code

    def get_nom_mini(self, langue="ar"):
        """Retourne l'abréviation selon la langue."""
        if langue == "ar":
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
        help_text="مثال: 2024-2025 / Exemple: 2024-2025",
    )
    date_debut = models.DateField(verbose_name="تاريخ البداية / Date de début")
    date_fin = models.DateField(verbose_name="تاريخ النهاية / Date de fin")
    est_courante = models.BooleanField(default=False, verbose_name="السنة الحالية / Année courante")

    class Meta:
        verbose_name = "سنة جامعية / Année universitaire"
        verbose_name_plural = "سنوات جامعية / Années universitaires"
        ordering = ["-date_debut"]
        indexes = [
            models.Index(fields=["est_courante"]),
            models.Index(fields=["date_debut", "date_fin"]),
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

    def save(self, *args, **kwargs):
        """Désactive est_courante pour les autres années si cette année devient courante (A24)."""
        if self.est_courante:
            AnneeUniversitaire.objects.filter(est_courante=True).exclude(pk=self.pk).update(est_courante=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_courante(cls):
        """Retourne l'année universitaire courante."""
        try:
            return cls.objects.get(est_courante=True)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            return cls.objects.filter(est_courante=True).order_by("-date_debut").first()


# ══════════════════════════════════════════════════════════════
# GÉOGRAPHIE
# ══════════════════════════════════════════════════════════════


class Pays(BaseModel):
    """Représente un pays."""

    code = models.CharField(max_length=3, unique=True, verbose_name="الرمز / Code", help_text="Code ISO 3 lettres")
    nom_ar = models.CharField(max_length=200, verbose_name="البلد", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Pays", blank=True, default="")

    class Meta:
        verbose_name = "بلد / Pays"
        verbose_name_plural = "بلدان / Pays"
        ordering = ["nom_ar", "nom_fr"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Validation: au moins un nom doit être renseigné."""
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError("يجب إدخال اسم واحد على الأقل / Au moins un nom doit être renseigné")

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class Wilaya(BaseModel):
    """
    Représente une wilaya (province) algérienne.
    Support bilingue arabe/français.
    """

    code = models.CharField(max_length=2, unique=True, verbose_name="الرمز", help_text="01-58")
    codePostal = models.CharField(max_length=5, verbose_name="الرمز البريدي / Code postal", blank=True, default="")

    nom_ar = models.CharField(max_length=100, verbose_name="الولاية", blank=True, default="")
    nom_fr = models.CharField(max_length=100, verbose_name="Wilaya (FR)", blank=True, default="")

    pays = models.ForeignKey(
        Pays, on_delete=models.PROTECT, verbose_name="البلد / Pays", related_name="wilayas", blank=True, null=True
    )

    class Meta:
        verbose_name = "ولاية"
        verbose_name_plural = "الولايات"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom_ar or self.nom_fr}"

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr
        return self.nom_fr or self.nom_ar


# ══════════════════════════════════════════════════════════════
# INFRASTRUCTURE
# ══════════════════════════════════════════════════════════════


class Amphi(BaseModel):
    """Représente un amphithéâtre."""

    numero = models.CharField(max_length=10, unique=True, verbose_name="الرقم / Numéro")
    nom_ar = models.CharField(max_length=200, verbose_name="المدرج", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Amphithéâtre", blank=True, default="")
    capacite = models.PositiveIntegerField(verbose_name="السعة / Capacité", blank=True, null=True)

    class Meta:
        verbose_name = "مدرج / Amphithéâtre"
        verbose_name_plural = "مدرجات / Amphithéâtres"
        ordering = ["numero"]
        indexes = [
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return f"Amphi {self.numero}"


class Salle(BaseModel):
    """Représente une salle de cours."""

    numero = models.CharField(max_length=10, unique=True, verbose_name="الرقم / Numéro")
    nom_ar = models.CharField(max_length=200, verbose_name="القاعة", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Salle", blank=True, default="")
    capacite = models.PositiveIntegerField(verbose_name="السعة / Capacité", blank=True, null=True)

    class Meta:
        verbose_name = "قاعة / Salle"
        verbose_name_plural = "قاعات / Salles"
        ordering = ["numero"]
        indexes = [
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return f"Salle {self.numero}"


class Laboratoire(BaseModel):
    """Représente un laboratoire."""

    TYPE_CHOICES = [
        ("informatique", "إعلام آلي / Informatique"),
        ("physique", "فيزياء / Physique"),
        ("chimie", "كيمياء / Chimie"),
        ("biologie", "بيولوجيا / Biologie"),
        ("geologie", "جيولوجيا / Géologie"),
        ("autres", "أخرى / Autres"),
    ]

    numero = models.CharField(max_length=10, unique=True, verbose_name="الرقم / Numéro")
    nom_ar = models.CharField(max_length=200, verbose_name="المخبر", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Laboratoire", blank=True, default="")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="autres", verbose_name="نوع المخبر / Type")
    capacite = models.PositiveIntegerField(verbose_name="السعة / Capacité", blank=True, null=True)

    class Meta:
        verbose_name = "مخبر / Laboratoire"
        verbose_name_plural = "مخابر / Laboratoires"
        ordering = ["numero"]
        indexes = [
            models.Index(fields=["numero"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"Lab {self.numero} ({self.get_type_display()})"


# ══════════════════════════════════════════════════════════════
# ORGANISATION PÉDAGOGIQUE
# ══════════════════════════════════════════════════════════════


class Semestre(BaseModel):
    """Représente un semestre dans l'année universitaire."""

    numero = models.PositiveSmallIntegerField(verbose_name="الرقم / Numéro", help_text="1, 2, 3, etc.")
    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code", help_text="S1, S2, etc.")
    nom_ar = models.CharField(max_length=200, verbose_name="السداسي", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Semestre", blank=True, default="")
    date_debut = models.DateField(verbose_name="تاريخ البداية / Date de début", blank=True, null=True)
    date_fin = models.DateField(verbose_name="تاريخ النهاية / Date de fin", blank=True, null=True)

    class Meta:
        verbose_name = "سداسي / Semestre"
        verbose_name_plural = "سداسيات / Semestres"
        ordering = ["numero"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Grade(BaseModel):
    """Représente un grade académique (Professeur, MCA, MCB, etc.)."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الرتبة", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Grade", blank=True, default="")

    class Meta:
        verbose_name = "رتبة / Grade"
        verbose_name_plural = "رتب / Grades"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Diplome(BaseModel):
    """Représente un diplôme (Licence, Master, Doctorat, etc.)."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الشهادة", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Diplôme", blank=True, default="")

    class Meta:
        verbose_name = "شهادة / Diplôme"
        verbose_name_plural = "شهادات / Diplômes"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Cycle(BaseModel):
    """Représente un cycle d'études (Licence, Master, Doctorat)."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الطور", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Cycle", blank=True, default="")

    class Meta:
        verbose_name = "طور / Cycle"
        verbose_name_plural = "أطوار / Cycles"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Niveau(BaseModel):
    """Représente un niveau d'études (L1, L2, L3, M1, M2, etc.)."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="المستوى", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Niveau", blank=True, default="")

    class Meta:
        verbose_name = "مستوى / Niveau"
        verbose_name_plural = "مستويات / Niveaux"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Parcours(BaseModel):
    """Représente un parcours d'études."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="المسار", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Parcours", blank=True, default="")

    class Meta:
        verbose_name = "مسار / Parcours"
        verbose_name_plural = "مسارات / Parcours"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Unite(BaseModel):
    """Représente une unité d'enseignement (UE)."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الوحدة", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Unité", blank=True, default="")

    class Meta:
        verbose_name = "وحدة / Unité"
        verbose_name_plural = "وحدات / Unités"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Groupe(BaseModel):
    """Représente un groupe d'étudiants."""

    numero = models.CharField(max_length=5, verbose_name="الرقم / Numéro")
    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الفوج", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Groupe", blank=True, default="")

    class Meta:
        verbose_name = "فوج / Groupe"
        verbose_name_plural = "أفواج / Groupes"
        ordering = ["numero"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Groupe {self.numero}"


class Section(BaseModel):
    """Représente une section d'étudiants."""

    numero = models.CharField(max_length=5, verbose_name="الرقم / Numéro")
    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="القطاع", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Section", blank=True, default="")

    class Meta:
        verbose_name = "قطاع / Section"
        verbose_name_plural = "قطاعات / Sections"
        ordering = ["numero"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Section {self.numero}"


class Session(BaseModel):
    """Représente une session d'examens (Normale, Rattrapage)."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الدورة", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Session", blank=True, default="")

    class Meta:
        verbose_name = "دورة / Session"
        verbose_name_plural = "دورات / Sessions"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Reforme(BaseModel):
    """Représente une réforme pédagogique."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="الإصلاح", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Réforme", blank=True, default="")
    cycle = models.ForeignKey(
        Cycle, on_delete=models.PROTECT, verbose_name="الطور / Cycle", related_name="reformes", blank=True, null=True
    )

    class Meta:
        verbose_name = "إصلاح / Réforme"
        verbose_name_plural = "إصلاحات / Réformes"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


class Identification(BaseModel):
    """Représente un type d'identification."""

    code = models.CharField(max_length=10, unique=True, verbose_name="الرمز / Code")
    nom_ar = models.CharField(max_length=200, verbose_name="التعريف / Identification", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Type d'identification", blank=True, default="")

    class Meta:
        verbose_name = "التعريف / Identification"
        verbose_name_plural = "التعاريف / Identifications"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code


# ══════════════════════════════════════════════════════════════
# AFFECTATION D'UN POSTE À UN UTILISATEUR
# ══════════════════════════════════════════════════════════════


class AffectationPoste(BaseModel):
    """
    Attribue un poste (chef de département, doyen, recteur...) à un utilisateur,
    dans un contexte (université, faculté ou département) et pour une année universitaire.
    """

    NIVEAU_UNIVERSITE = "universite"
    NIVEAU_FACULTE = "faculte"
    NIVEAU_DEPARTEMENT = "departement"
    NIVEAU_CHOICES = [
        (NIVEAU_UNIVERSITE, "الجامعة / Université"),
        (NIVEAU_FACULTE, "الكلية / Faculté"),
        (NIVEAU_DEPARTEMENT, "القسم / Département"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="affectations_postes",
        verbose_name="المستخدم / Utilisateur",
    )
    poste = models.ForeignKey(
        Poste,
        on_delete=models.PROTECT,
        related_name="affectations",
        verbose_name="المنصب / Poste",
    )
    niveau_contexte = models.CharField(
        max_length=20,
        choices=NIVEAU_CHOICES,
        verbose_name="المستوى / Niveau",
    )
    universite = models.ForeignKey(
        "universite.Universite",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="affectations_postes",
        verbose_name="الجامعة / Université",
    )
    faculte = models.ForeignKey(
        "faculte.Faculte",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="affectations_postes",
        verbose_name="الكلية / Faculté",
    )
    departement = models.ForeignKey(
        "departement.Departement",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="affectations_postes",
        verbose_name="القسم / Département",
    )
    annee_univ = models.ForeignKey(
        AnneeUniversitaire,
        on_delete=models.PROTECT,
        related_name="affectations_postes",
        verbose_name="السنة الجامعية / Année universitaire",
    )
    date_debut = models.DateField(default=timezone.localdate, verbose_name="تاريخ البداية / Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="تاريخ النهاية / Date de fin")
    est_actif = models.BooleanField(default=True, verbose_name="نشط / Actif")

    class Meta:
        verbose_name = "تعيين منصب"
        verbose_name_plural = "تعيينات المناصب"
        ordering = ["-poste__niveau", "user__last_name"]
        indexes = [
            models.Index(fields=["user", "est_actif"]),
            models.Index(fields=["poste", "est_actif"]),
            models.Index(fields=["departement", "est_actif"]),
            models.Index(fields=["faculte", "est_actif"]),
            models.Index(fields=["universite", "est_actif"]),
            models.Index(fields=["annee_univ", "est_actif"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.poste} ({self.get_contexte() or self.get_niveau_contexte_display()})"

    def get_contexte(self):
        """Établissement concerné par l'affectation, selon le niveau."""
        return {
            self.NIVEAU_UNIVERSITE: self.universite,
            self.NIVEAU_FACULTE: self.faculte,
            self.NIVEAU_DEPARTEMENT: self.departement,
        }.get(self.niveau_contexte)

    def clean(self):
        if not self.get_contexte():
            raise ValidationError(
                {self.niveau_contexte or "niveau_contexte": "يجب تحديد المؤسسة الموافقة للمستوى / Établissement requis"}
            )
        if self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError({"date_fin": "تاريخ النهاية قبل تاريخ البداية / Date de fin antérieure au début"})

    @classmethod
    def actives(cls, user):
        """Affectations actives d'un utilisateur."""
        return cls.objects.filter(user=user, est_actif=True).select_related(
            "poste", "universite", "faculte", "departement", "annee_univ"
        )

    @classmethod
    def get_departements_user(cls, user):
        """Départements dans lesquels l'utilisateur occupe un poste actif."""
        from apps.academique.departement.models import Departement

        return Departement.objects.filter(
            affectations_postes__user=user,
            affectations_postes__est_actif=True,
            affectations_postes__niveau_contexte=cls.NIVEAU_DEPARTEMENT,
        ).distinct()

    @classmethod
    def user_has_poste(cls, user, poste_code, **contexte):
        """Vrai si l'utilisateur occupe ce poste (éventuellement dans un établissement donné)."""
        return cls.objects.filter(user=user, est_actif=True, poste__code=poste_code, **contexte).exists()


# ══════════════════════════════════════════════════════════════
# PERMISSIONS PAR POSTE
# ══════════════════════════════════════════════════════════════


class PostePermission(BaseModel):
    """
    Droits d'un poste sur chaque module : voir, ajouter, modifier, supprimer.
    Un champ booléen par couple (module, action), par exemple `enseignant_change`.
    """

    MODULES = [
        ("ens_dep", "أساتذة-قسم / Ens-Dép"),
        ("amphi_dep", "مدرجات-قسم / Amphi-Dép"),
        ("salle_dep", "قاعات-قسم / Salle-Dép"),
        ("labo_dep", "مخابر-قسم / Labo-Dép"),
        ("classe", "حصص / Classes"),
        ("seance", "حصص دراسية / Séances"),
        ("sous_groupe", "مجموعات فرعية / Sous-groupes"),
        ("etu_sous_groupe", "طلاب-مجموعات / Étu-SG"),
        ("gestion_etu", "إدارة طلاب / Gestion étudiants"),
        ("abs_etu", "حضور/غياب / Présences"),
        ("departement", "قسم / Département"),
        ("specialite", "تخصص / Spécialité"),
        ("niv_spe_dep", "مستوى-تخصص / Niv-Spé"),
        ("niv_spe_dep_sg", "أقسام وأفواج / Sections-Groupes"),
        ("matiere", "مادة / Matière"),
        ("enseignant", "أستاذ / Enseignant"),
        ("etudiant", "طالب / Étudiant"),
        ("faculte", "كلية / Faculté"),
        ("filiere", "شعبة / Filière"),
        ("universite", "جامعة / Université"),
        ("domaine", "ميدان / Domaine"),
        ("user", "مستخدم / Utilisateur"),
        ("poste", "منصب / Poste"),
        ("affectation_poste", "تعيين منصب / Affectation poste"),
        ("annee_univ", "سنة جامعية / Année universitaire"),
        ("cycle", "طور / Cycle"),
        ("niveau", "مستوى / Niveau"),
        ("grade", "رتبة / Grade"),
        ("diplome", "شهادة / Diplôme"),
        ("semestre", "سداسي / Semestre"),
        ("session", "دورة / Session"),
        ("reforme", "إصلاح / Réforme"),
        ("parcours", "مسار / Parcours"),
        ("unite", "وحدة / Unité"),
        ("groupe", "فوج / Groupe"),
        ("section", "قسم / Section"),
        ("identification", "تعريف / Identification"),
        ("wilaya", "ولاية / Wilaya"),
        ("pays", "بلد / Pays"),
        ("amphi", "مدرج / Amphi"),
        ("salle", "قاعة / Salle"),
        ("laboratoire", "مخبر / Laboratoire"),
    ]
    ACTIONS = [
        ("view", "عرض / Voir"),
        ("add", "إضافة / Ajouter"),
        ("change", "تعديل / Modifier"),
        ("delete", "حذف / Supprimer"),
    ]

    poste = models.OneToOneField(
        Poste,
        on_delete=models.CASCADE,
        related_name="permissions",
        verbose_name="المنصب / Poste",
    )

    class Meta:
        verbose_name = "صلاحيات منصب"
        verbose_name_plural = "صلاحيات المناصب"

    def __str__(self):
        return f"صلاحيات {self.poste}"

    @classmethod
    def field_names(cls):
        return [f"{module}_{action}" for module, _ in cls.MODULES for action, _ in cls.ACTIONS]

    def to_dict(self):
        return {name: getattr(self, name) for name in self.field_names()}

    @classmethod
    def get_permissions(cls, request):
        """
        Permissions de l'utilisateur sous forme de dict {"enseignant_view": True, ...}.

        Poste pris en compte, dans l'ordre :
        1. l'affectation active mémorisée en session (`current_affectation_id`) ;
        2. le poste choisi à la connexion (`current_role_code` ou `current_role`) ;
        3. sinon, l'union des droits de toutes ses affectations actives.
        Le superutilisateur a tous les droits.
        """
        names = cls.field_names()
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return dict.fromkeys(names, False)
        if user.is_superuser:
            return dict.fromkeys(names, True)

        affectations = AffectationPoste.actives(user)
        session = request.session
        if session.get("current_affectation_id"):
            affectations = affectations.filter(id=session["current_affectation_id"])
        else:
            role = session.get("current_role_code") or session.get("current_role")
            if role and affectations.filter(poste__code=role).exists():
                affectations = affectations.filter(poste__code=role)

        result = dict.fromkeys(names, False)
        for perm in cls.objects.filter(poste__affectations__in=affectations).distinct():
            for name, value in perm.to_dict().items():
                result[name] = result[name] or value
        return result

    @classmethod
    def add_to_context(cls, request, context):
        """Ajoute `permissions` et `is_admin_poste` (poste administratif actif) au contexte d'un template."""
        permissions = cls.get_permissions(request)
        context["permissions"] = permissions
        context["is_admin_poste"] = request.user.is_superuser or any(permissions.values())
        return context


for _module, _module_label in PostePermission.MODULES:
    for _action, _action_label in PostePermission.ACTIONS:
        PostePermission.add_to_class(
            f"{_module}_{_action}",
            models.BooleanField(default=False, verbose_name=f"{_module_label} — {_action_label}"),
        )
