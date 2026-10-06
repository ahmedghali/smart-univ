# apps/academique/affectation/models.py

from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.noyau.commun.models import BaseModel, AnneeUniversitaire, Amphi, Salle, Laboratoire, Semestre
from apps.academique.enseignant.models import Enseignant
from apps.academique.departement.models import Departement, Matiere, NivSpeDep_SG
from apps.academique.etudiant.models import Etudiant


# ══════════════════════════════════════════════════════════════
# MODÈLE AFFECTATION ENSEIGNANT-DEPARTEMENT
# ══════════════════════════════════════════════════════════════

class Ens_Dep(BaseModel):
    """
    Modèle représentant l'affectation d'un enseignant à un département
    pour une année universitaire donnée.
    Contient les informations sur les séances, volumes horaires et statistiques.
    """

    # ══════════════════════════════════════════════════════════
    # CHOIX / CHOICES
    # ══════════════════════════════════════════════════════════

    class StatutEnseignant(models.TextChoices):
        """Statut de l'enseignant / حالة الأستاذ"""
        PERMANENT = 'Permanent', 'مرسّم'
        PERMANENT_VACATAIRE = 'Permanent & Vacataire', 'مرسّم و مؤقت'
        VACATAIRE = 'Vacataire', 'مؤقت'
        ASSOCIE = 'Associe', 'مشارك'
        DOCTORANT = 'Doctorant', 'طالب دكتوراه'

    # ══════════════════════════════════════════════════════════
    # RELATIONS
    # ══════════════════════════════════════════════════════════

    enseignant = models.ForeignKey(
        Enseignant,
        on_delete=models.PROTECT,
        verbose_name="الأستاذ / Enseignant",
        related_name='affectations_departement',
        db_index=True
    )

    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        verbose_name="القسم / Département",
        related_name='affectations_enseignant',
        db_index=True
    )

    annee_univ = models.ForeignKey(
        AnneeUniversitaire,
        on_delete=models.PROTECT,
        verbose_name="السنة الجامعية / Année universitaire",
        related_name='affectations_ens_dep',
        db_index=True
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS GÉNÉRALES
    # ══════════════════════════════════════════════════════════

    date_affectation = models.DateField(
        default=timezone.now,
        verbose_name="تاريخ الإنتساب / Date d'affectation"
    )

    statut = models.CharField(
        max_length=50,
        choices=StatutEnseignant.choices,
        default=StatutEnseignant.PERMANENT,
        verbose_name="حالة الأستاذ / Statut de l'enseignant"
    )

    est_actif = models.BooleanField(
        default=True,
        verbose_name="نشط / Actif"
    )

    # ══════════════════════════════════════════════════════════
    # SEMESTRES
    # ══════════════════════════════════════════════════════════

    semestre_1 = models.BooleanField(
        default=True,
        verbose_name="السداسي الأول / Semestre 1"
    )

    semestre_2 = models.BooleanField(
        default=True,
        verbose_name="السداسي الثاني / Semestre 2"
    )

    # ══════════════════════════════════════════════════════════
    # STATISTIQUES SEMESTRE 1
    # ══════════════════════════════════════════════════════════

    # Nombre total de séances
    nbrClas_ALL_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الحصص الكلي - س1 / Nb total séances S1"
    )

    # Séances dans le département
    nbrClas_in_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الحصص داخل القسم - س1 / Nb séances dans dép. S1"
    )

    nbrClas_Cours_in_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص المحاضرات داخل القسم - س1 / Nb cours dans dép. S1"
    )

    nbrClas_TD_in_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الموجهة داخل القسم - س1 / Nb TD dans dép. S1"
    )

    nbrClas_TP_in_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال التطبيقية داخل القسم - س1 / Nb TP dans dép. S1"
    )

    nbrClas_SS_in_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الشخصية داخل القسم - س1 / Nb travail personnel dans dép. S1"
    )

    # Séances hors département
    nbrClas_out_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الحصص خارج القسم - س1 / Nb séances hors dép. S1"
    )

    nbrClas_Cours_out_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص المحاضرات خارج القسم - س1 / Nb cours hors dép. S1"
    )

    nbrClas_TD_out_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الموجهة خارج القسم - س1 / Nb TD hors dép. S1"
    )

    nbrClas_TP_out_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال التطبيقية خارج القسم - س1 / Nb TP hors dép. S1"
    )

    nbrClas_SS_out_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الشخصية خارج القسم - س1 / Nb travail personnel hors dép. S1"
    )

    # Jours et volumes horaires
    nbrJour_in_Dep_S1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الأيام داخل القسم - س1 / Nb jours dans dép. S1"
    )

    volHor_in_Dep_S1 = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="الحجم الساعي داخل القسم - س1 / Vol. horaire dans dép. S1"
    )

    volHor_out_Dep_S1 = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="الحجم الساعي خارج القسم - س1 / Vol. horaire hors dép. S1"
    )

    # Taux de progression
    taux_min_S1 = models.IntegerField(
        default=0,
        verbose_name="أقل نسبة تقدم - س1 / Taux min progression S1"
    )

    taux_moyen_S1 = models.FloatField(
        default=0.0,
        verbose_name="متوسط نسبة التقدم - س1 / Taux moyen progression S1"
    )

    # Pourcentage Moodle
    moodle_percentage_S1 = models.FloatField(
        default=0.0,
        verbose_name="نسبة النشر على Moodle - س1 / Pourcentage Moodle S1"
    )

    # ══════════════════════════════════════════════════════════
    # STATISTIQUES SEMESTRE 2
    # ══════════════════════════════════════════════════════════

    # Nombre total de séances
    nbrClas_ALL_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الحصص الكلي - س2 / Nb total séances S2"
    )

    # Séances dans le département
    nbrClas_in_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الحصص داخل القسم - س2 / Nb séances dans dép. S2"
    )

    nbrClas_Cours_in_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص المحاضرات داخل القسم - س2 / Nb cours dans dép. S2"
    )

    nbrClas_TD_in_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الموجهة داخل القسم - س2 / Nb TD dans dép. S2"
    )

    nbrClas_TP_in_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال التطبيقية داخل القسم - س2 / Nb TP dans dép. S2"
    )

    nbrClas_SS_in_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الشخصية داخل القسم - س2 / Nb travail personnel dans dép. S2"
    )

    # Séances hors département
    nbrClas_out_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الحصص خارج القسم - س2 / Nb séances hors dép. S2"
    )

    nbrClas_Cours_out_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص المحاضرات خارج القسم - س2 / Nb cours hors dép. S2"
    )

    nbrClas_TD_out_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الموجهة خارج القسم - س2 / Nb TD hors dép. S2"
    )

    nbrClas_TP_out_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال التطبيقية خارج القسم - س2 / Nb TP hors dép. S2"
    )

    nbrClas_SS_out_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد حصص الأعمال الشخصية خارج القسم - س2 / Nb travail personnel hors dép. S2"
    )

    # Jours et volumes horaires
    nbrJour_in_Dep_S2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الأيام داخل القسم - س2 / Nb jours dans dép. S2"
    )

    volHor_in_Dep_S2 = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="الحجم الساعي داخل القسم - س2 / Vol. horaire dans dép. S2"
    )

    volHor_out_Dep_S2 = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="الحجم الساعي خارج القسم - س2 / Vol. horaire hors dép. S2"
    )

    # Taux de progression
    taux_min_S2 = models.IntegerField(
        default=0,
        verbose_name="أقل نسبة تقدم - س2 / Taux min progression S2"
    )

    taux_moyen_S2 = models.FloatField(
        default=0.0,
        verbose_name="متوسط نسبة التقدم - س2 / Taux moyen progression S2"
    )

    # Pourcentage Moodle
    moodle_percentage_S2 = models.FloatField(
        default=0.0,
        verbose_name="نسبة النشر على Moodle - س2 / Pourcentage Moodle S2"
    )

    # ══════════════════════════════════════════════════════════
    # META ET MÉTHODES
    # ══════════════════════════════════════════════════════════

    class Meta:
        verbose_name = "إنتساب أستاذ-قسم / Affectation Enseignant-Département"
        verbose_name_plural = "إنتسابات أستاذ-قسم / Affectations Enseignant-Département"
        unique_together = ['enseignant', 'departement', 'annee_univ']
        ordering = ['-annee_univ__date_debut', 'departement__code', 'enseignant__nom_ar']
        indexes = [
            models.Index(fields=['enseignant', 'annee_univ']),
            models.Index(fields=['departement', 'annee_univ']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        """Représentation textuelle de l'affectation."""
        semestres_info = []
        if self.semestre_1:
            semestres_info.append("S1")
        if self.semestre_2:
            semestres_info.append("S2")

        semestres_str = " + ".join(semestres_info) if semestres_info else "غير مسجل"

        # Nom de l'enseignant
        if self.enseignant.nom_ar and self.enseignant.prenom_ar:
            ens_nom = f"{self.enseignant.nom_ar} {self.enseignant.prenom_ar}"
        elif self.enseignant.nom_fr and self.enseignant.prenom_fr:
            ens_nom = f"{self.enseignant.nom_fr} {self.enseignant.prenom_fr}"
        else:
            ens_nom = self.enseignant.matricule

        # Nom du département
        dep_nom = self.departement.nom_ar if self.departement.nom_ar else self.departement.code

        return f"{ens_nom} - {dep_nom} ({self.get_statut_display()}) - {semestres_str}"

    def clean(self):
        """Validation du modèle."""
        super().clean()

        # Vérifier qu'au moins un semestre est sélectionné
        if not self.semestre_1 and not self.semestre_2:
            raise ValidationError(
                "يجب اختيار سداسي واحد على الأقل / Au moins un semestre doit être sélectionné"
            )

    def get_volume_horaire_total_S1(self):
        """Calcule le volume horaire total pour le semestre 1."""
        return float(self.volHor_in_Dep_S1) + float(self.volHor_out_Dep_S1)

    def get_volume_horaire_total_S2(self):
        """Calcule le volume horaire total pour le semestre 2."""
        return float(self.volHor_in_Dep_S2) + float(self.volHor_out_Dep_S2)

    def get_volume_horaire_total_annee(self):
        """Calcule le volume horaire total pour l'année."""
        return self.get_volume_horaire_total_S1() + self.get_volume_horaire_total_S2()


# ══════════════════════════════════════════════════════════════
# MODÈLE AFFECTATION AMPHITHÉÂTRE-DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class Amphi_Dep(BaseModel):
    """
    Modèle représentant l'affectation d'un amphithéâtre à un département.
    Permet de gérer la disponibilité par semestre.
    """

    amphi = models.ForeignKey(
        Amphi,
        on_delete=models.CASCADE,
        verbose_name="المدرج / Amphithéâtre",
        related_name='affectations_departement',
        db_index=True
    )

    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        verbose_name="القسم / Département",
        related_name='affectations_amphi',
        db_index=True
    )

    semestre_1 = models.BooleanField(
        default=True,
        verbose_name="السداسي الأول / Semestre 1"
    )

    semestre_2 = models.BooleanField(
        default=True,
        verbose_name="السداسي الثاني / Semestre 2"
    )

    est_actif = models.BooleanField(
        default=True,
        verbose_name="نشط / Actif"
    )

    class Meta:
        verbose_name = "تخصيص مدرج-قسم / Affectation Amphi-Département"
        verbose_name_plural = "تخصيصات مدرج-قسم / Affectations Amphi-Département"
        unique_together = ['amphi', 'departement']
        ordering = ['departement__code', 'amphi__numero']
        indexes = [
            models.Index(fields=['amphi', 'departement']),
            models.Index(fields=['est_actif']),
        ]

    def __str__(self):
        dep_nom = self.departement.nom_ar or self.departement.code
        return f"{self.amphi} - {dep_nom}"

    def clean(self):
        """Validation du modèle."""
        super().clean()
        if not self.semestre_1 and not self.semestre_2:
            raise ValidationError(
                "يجب اختيار سداسي واحد على الأقل / Au moins un semestre doit être sélectionné"
            )

    def get_semestres_display(self):
        """Retourne les semestres sous forme de texte."""
        semestres = []
        if self.semestre_1:
            semestres.append("S1")
        if self.semestre_2:
            semestres.append("S2")
        return " + ".join(semestres) if semestres else "-"


# ══════════════════════════════════════════════════════════════
# MODÈLE AFFECTATION SALLE-DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class Salle_Dep(BaseModel):
    """
    Modèle représentant l'affectation d'une salle à un département.
    Permet de gérer la disponibilité par semestre.
    """

    salle = models.ForeignKey(
        Salle,
        on_delete=models.CASCADE,
        verbose_name="القاعة / Salle",
        related_name='affectations_departement',
        db_index=True
    )

    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        verbose_name="القسم / Département",
        related_name='affectations_salle',
        db_index=True
    )

    semestre_1 = models.BooleanField(
        default=True,
        verbose_name="السداسي الأول / Semestre 1"
    )

    semestre_2 = models.BooleanField(
        default=True,
        verbose_name="السداسي الثاني / Semestre 2"
    )

    est_actif = models.BooleanField(
        default=True,
        verbose_name="نشط / Actif"
    )

    class Meta:
        verbose_name = "تخصيص قاعة-قسم / Affectation Salle-Département"
        verbose_name_plural = "تخصيصات قاعة-قسم / Affectations Salle-Département"
        unique_together = ['salle', 'departement']
        ordering = ['departement__code', 'salle__numero']
        indexes = [
            models.Index(fields=['salle', 'departement']),
            models.Index(fields=['est_actif']),
        ]

    def __str__(self):
        dep_nom = self.departement.nom_ar or self.departement.code
        return f"{self.salle} - {dep_nom}"

    def clean(self):
        """Validation du modèle."""
        super().clean()
        if not self.semestre_1 and not self.semestre_2:
            raise ValidationError(
                "يجب اختيار سداسي واحد على الأقل / Au moins un semestre doit être sélectionné"
            )

    def get_semestres_display(self):
        """Retourne les semestres sous forme de texte."""
        semestres = []
        if self.semestre_1:
            semestres.append("S1")
        if self.semestre_2:
            semestres.append("S2")
        return " + ".join(semestres) if semestres else "-"


# ══════════════════════════════════════════════════════════════
# MODÈLE AFFECTATION LABORATOIRE-DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

class Laboratoire_Dep(BaseModel):
    """
    Modèle représentant l'affectation d'un laboratoire à un département.
    Permet de gérer la disponibilité par semestre.
    """

    laboratoire = models.ForeignKey(
        Laboratoire,
        on_delete=models.CASCADE,
        verbose_name="المخبر / Laboratoire",
        related_name='affectations_departement',
        db_index=True
    )

    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        verbose_name="القسم / Département",
        related_name='affectations_laboratoire',
        db_index=True
    )

    semestre_1 = models.BooleanField(
        default=True,
        verbose_name="السداسي الأول / Semestre 1"
    )

    semestre_2 = models.BooleanField(
        default=True,
        verbose_name="السداسي الثاني / Semestre 2"
    )

    est_actif = models.BooleanField(
        default=True,
        verbose_name="نشط / Actif"
    )

    class Meta:
        verbose_name = "تخصيص مخبر-قسم / Affectation Labo-Département"
        verbose_name_plural = "تخصيصات مخبر-قسم / Affectations Labo-Département"
        unique_together = ['laboratoire', 'departement']
        ordering = ['departement__code', 'laboratoire__numero']
        indexes = [
            models.Index(fields=['laboratoire', 'departement']),
            models.Index(fields=['est_actif']),
        ]

    def __str__(self):
        dep_nom = self.departement.nom_ar or self.departement.code
        return f"{self.laboratoire} - {dep_nom}"

    def clean(self):
        """Validation du modèle."""
        super().clean()
        if not self.semestre_1 and not self.semestre_2:
            raise ValidationError(
                "يجب اختيار سداسي واحد على الأقل / Au moins un semestre doit être sélectionné"
            )

    def get_semestres_display(self):
        """Retourne les semestres sous forme de texte."""
        semestres = []
        if self.semestre_1:
            semestres.append("S1")
        if self.semestre_2:
            semestres.append("S2")
        return " + ".join(semestres) if semestres else "-"


# ══════════════════════════════════════════════════════════════
# MODÈLE CLASSE (SÉANCE D'ENSEIGNEMENT)
# ══════════════════════════════════════════════════════════════

class Classe(BaseModel):
    """
    Modèle représentant une séance d'enseignement (classe).
    Relie un enseignant, une matière, des étudiants et un lieu
    pour un créneau horaire donné.
    """

    # ══════════════════════════════════════════════════════════
    # CHOIX / CHOICES
    # ══════════════════════════════════════════════════════════

    class Timeblock(models.TextChoices):
        """Créneaux horaires disponibles / الحصص المتاحة"""
        CLASSE01 = '08:00-09:30', 'الحصة الأولى 08:00-09:30'
        CLASSE02 = '09:40-11:10', 'الحصة الثانية 09:40-11:10'
        CLASSE03 = '11:20-12:50', 'الحصة الثالثة 11:20-12:50'
        CLASSE04 = '13:10-14:40', 'الحصة الرابعة 13:10-14:40'
        CLASSE05 = '14:50-16:20', 'الحصة الخامسة 14:50-16:20'
        CLASSE06 = '16:30-18:00', 'الحصة السادسة 16:30-18:00'

    class Dayblock(models.TextChoices):
        """Jours de la semaine / أيام الأسبوع"""
        SATURDAY = 'Samedi', 'السبت'
        SUNDAY = 'Dimanche', 'الأحد'
        MONDAY = 'Lundi', 'الإثنين'
        TUESDAY = 'Mardi', 'الثلاثاء'
        WEDNESDAY = 'Mercredi', 'الأربعاء'
        THURSDAY = 'Jeudi', 'الخميس'

    class Typeblock(models.TextChoices):
        """Types de séances / أنواع الحصص"""
        COURS = 'Cours', 'محاضرة / Cours'
        TD = 'TD', 'أعمال موجهة / TD'
        TP = 'TP', 'أعمال تطبيقية / TP'
        SS = 'Sortie', 'خرجة علمية / Sortie Scientifique'

    # ══════════════════════════════════════════════════════════
    # RELATIONS PRINCIPALES
    # ══════════════════════════════════════════════════════════

    semestre = models.ForeignKey(
        Semestre,
        on_delete=models.PROTECT,
        verbose_name="السداسي / Semestre",
        related_name='classes',
        db_index=True
    )

    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.PROTECT,
        verbose_name="المادة / Matière",
        related_name='classes',
        db_index=True
    )

    enseignant = models.ForeignKey(
        'Ens_Dep',
        on_delete=models.PROTECT,
        verbose_name="الأستاذ / Enseignant",
        related_name='classes',
        db_index=True
    )

    niv_spe_dep_sg = models.ForeignKey(
        NivSpeDep_SG,
        on_delete=models.PROTECT,
        verbose_name="الطلبة / Étudiants (Niveau-Spécialité-Section/Groupe)",
        related_name='classes',
        db_index=True
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS HORAIRES
    # ══════════════════════════════════════════════════════════

    jour = models.CharField(
        max_length=20,
        choices=Dayblock.choices,
        verbose_name="يوم الحصة / Jour"
    )

    temps = models.CharField(
        max_length=20,
        choices=Timeblock.choices,
        verbose_name="وقت الحصة / Créneau horaire"
    )

    type = models.CharField(
        max_length=20,
        choices=Typeblock.choices,
        verbose_name="نوع الحصة / Type de séance"
    )

    # ══════════════════════════════════════════════════════════
    # LIEU (POLYMORPHIQUE)
    # ══════════════════════════════════════════════════════════

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="نوع المكان / Type de lieu",
        null=True,
        blank=True,
        limit_choices_to={
            'model__in': ['amphi_dep', 'salle_dep', 'laboratoire_dep']
        }
    )

    object_id = models.PositiveIntegerField(
        verbose_name="معرف المكان / ID du lieu",
        null=True,
        blank=True
    )

    lieu = GenericForeignKey('content_type', 'object_id')

    # ══════════════════════════════════════════════════════════
    # SUIVI PÉDAGOGIQUE
    # ══════════════════════════════════════════════════════════

    taux_avancement = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="نسبة التقدم / Taux d'avancement (%)",
        help_text="Pourcentage de progression (0-100)"
    )

    seance_created = models.BooleanField(
        default=False,
        verbose_name="تم إنشاء الدروس / Séances créées"
    )

    abs_liste_Etu = models.BooleanField(
        default=False,
        verbose_name="تم إنشاء قائمة الغيابات / Liste absences créée"
    )

    notes_liste_Etu = models.BooleanField(
        default=False,
        verbose_name="تم إنشاء قائمة النقاط / Liste notes créée"
    )

    lien_moodle = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="رابط Moodle / Lien Moodle"
    )

    # ══════════════════════════════════════════════════════════
    # META ET MÉTHODES
    # ══════════════════════════════════════════════════════════

    class Meta:
        verbose_name = "حصة / Classe"
        verbose_name_plural = "حصص / Classes"
        unique_together = ('semestre', 'matiere', 'enseignant', 'niv_spe_dep_sg', 'jour', 'temps')
        ordering = ['semestre', 'jour', 'temps', 'type']
        indexes = [
            models.Index(fields=['semestre', 'jour', 'temps']),
            models.Index(fields=['enseignant', 'semestre']),
            models.Index(fields=['matiere', 'semestre']),
            models.Index(fields=['niv_spe_dep_sg', 'semestre']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        """Représentation textuelle de la classe."""
        return f"{self.matiere} - {self.enseignant} - {self.get_jour_display()} {self.temps} ({self.get_type_display()})"

    def clean(self):
        """Validation du modèle."""
        super().clean()

        # Vérifier que tous les champs obligatoires sont remplis
        if not all([self.semestre, self.matiere, self.enseignant, self.niv_spe_dep_sg, self.jour, self.temps, self.type]):
            raise ValidationError(
                "يجب ملء جميع الحقول الرئيسية / Tous les champs principaux doivent être remplis"
            )

        # Vérifier que le lieu est spécifié
        if not self.content_type or not self.object_id:
            raise ValidationError(
                "يجب تحديد مكان الحصة / Un lieu doit être spécifié"
            )

        # Vérifier le taux d'avancement
        if self.taux_avancement < 0 or self.taux_avancement > 100:
            raise ValidationError(
                "نسبة التقدم يجب أن تكون بين 0 و 100 / Le taux d'avancement doit être entre 0 et 100"
            )

    def save(self, *args, **kwargs):
        """Sauvegarde avec validation optionnelle."""
        # Ne pas appeler full_clean() ici car le formulaire admin valide déjà
        # Si vous voulez valider lors de la création programmatique, utilisez:
        # instance.full_clean() avant instance.save()
        super().save(*args, **kwargs)

    def get_lieu_display(self):
        """Retourne une représentation du lieu."""
        if self.lieu:
            return str(self.lieu)
        return "-"

    @property
    def lieu_nom(self):
        """Retourne uniquement le nom du lieu (sans le département)."""
        if not self.lieu:
            return None
        # Check which type of lieu it is and return just the place name
        if hasattr(self.lieu, 'salle'):
            return str(self.lieu.salle)
        elif hasattr(self.lieu, 'amphi'):
            return str(self.lieu.amphi)
        elif hasattr(self.lieu, 'laboratoire'):
            return str(self.lieu.laboratoire)
        return str(self.lieu)

    def get_duree_heures(self):
        """Retourne la durée en heures (1.5h par défaut)."""
        return 1.5

    @property
    def est_cours(self):
        """Vérifie si c'est un cours magistral."""
        return self.type == self.Typeblock.COURS

    @property
    def est_td(self):
        """Vérifie si c'est un TD."""
        return self.type == self.Typeblock.TD

    @property
    def est_tp(self):
        """Vérifie si c'est un TP."""
        return self.type == self.Typeblock.TP

    @classmethod
    def get_classes_by_enseignant(cls, ens_dep, semestre=None):
        """Retourne les classes d'un enseignant."""
        qs = cls.objects.filter(enseignant=ens_dep)
        if semestre:
            qs = qs.filter(semestre=semestre)
        return qs.select_related('matiere', 'semestre', 'niv_spe_dep_sg')

    @classmethod
    def get_classes_by_jour(cls, jour, semestre=None):
        """Retourne les classes d'un jour donné."""
        qs = cls.objects.filter(jour=jour)
        if semestre:
            qs = qs.filter(semestre=semestre)
        return qs.select_related('matiere', 'enseignant', 'semestre')


# ══════════════════════════════════════════════════════════════
# MODÈLE SOUS-GROUPE
# ══════════════════════════════════════════════════════════════

class SousGroupe(BaseModel):
    """
    Modèle pour gérer les sous-groupes d'un groupe principal.
    Permet de diviser un groupe (NivSpeDep_SG) en sous-groupes pour les TP/TD.
    """

    groupe_principal = models.ForeignKey(
        NivSpeDep_SG,
        on_delete=models.CASCADE,
        verbose_name="المجموعة الأصلية / Groupe principal",
        related_name='sous_groupes',
        db_index=True
    )

    nom = models.CharField(
        max_length=50,
        verbose_name="اسم المجموعة الفرعية / Nom du sous-groupe",
        help_text="مثال: A, B, 1, 2 / Ex: A, B, 1, 2"
    )

    nom_complet = models.CharField(
        max_length=100,
        verbose_name="الاسم الكامل / Nom complet",
        blank=True,
        help_text="سيتم إنشاؤه تلقائياً / Généré automatiquement"
    )

    description = models.TextField(
        verbose_name="الوصف / Description",
        blank=True
    )

    effectif = models.PositiveIntegerField(
        verbose_name="عدد الطلاب / Effectif",
        default=0
    )

    actif = models.BooleanField(
        verbose_name="نشط / Actif",
        default=True
    )

    ordre_affichage = models.PositiveIntegerField(
        verbose_name="ترتيب العرض / Ordre d'affichage",
        default=1,
        help_text="ترتيب عرض المجموعة الفرعية / Ordre d'affichage du sous-groupe"
    )

    # Métadonnées
    created_by = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="أنشأ بواسطة / Créé par",
        related_name='sous_groupes_crees'
    )

    class Meta:
        verbose_name = "مجموعة فرعية / Sous-groupe"
        verbose_name_plural = "مجموعات فرعية / Sous-groupes"
        unique_together = ['groupe_principal', 'nom']
        ordering = ['groupe_principal', 'ordre_affichage', 'nom']
        indexes = [
            models.Index(fields=['groupe_principal', 'actif']),
            models.Index(fields=['actif', 'ordre_affichage']),
        ]

    def save(self, *args, **kwargs):
        """Génère le nom complet automatiquement."""
        if not self.nom_complet and self.groupe_principal:
            self.nom_complet = f"{self.groupe_principal} - {self.nom}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_complet or f"{self.groupe_principal} - {self.nom}"

    def get_etudiants(self):
        """Retourne les étudiants affectés à ce sous-groupe."""
        return self.etudiants_affectes.filter(actif=True).select_related('etudiant')

    def update_effectif(self):
        """Met à jour l'effectif du sous-groupe."""
        self.effectif = self.get_etudiants().count()
        self.save(update_fields=['effectif'])


# ══════════════════════════════════════════════════════════════
# MODÈLE ASSOCIATION ÉTUDIANT-SOUS-GROUPE
# ══════════════════════════════════════════════════════════════

class EtudiantSousGroupe(BaseModel):
    """
    Association entre un étudiant et un sous-groupe.
    Permet de définir à quel sous-groupe appartient chaque étudiant.
    """

    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        verbose_name="الطالب / Étudiant",
        related_name='affectations_sous_groupes',
        db_index=True
    )

    sous_groupe = models.ForeignKey(
        SousGroupe,
        on_delete=models.CASCADE,
        verbose_name="المجموعة الفرعية / Sous-groupe",
        related_name='etudiants_affectes',
        db_index=True
    )

    date_affectation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ التعيين / Date d'affectation"
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="نشط / Actif"
    )

    ordre_dans_groupe = models.PositiveIntegerField(
        verbose_name="الترتيب في المجموعة / Ordre dans le groupe",
        default=1,
        help_text="ترتيب الطالب داخل المجموعة الفرعية / Ordre de l'étudiant dans le sous-groupe"
    )

    affecte_par = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="أُسند بواسطة / Affecté par",
        related_name='affectations_etudiants_sg'
    )

    class Meta:
        verbose_name = "طالب - مجموعة فرعية / Étudiant-Sous-groupe"
        verbose_name_plural = "طلاب - مجموعات فرعية / Étudiants-Sous-groupes"
        unique_together = ['etudiant', 'sous_groupe']
        ordering = ['sous_groupe', 'ordre_dans_groupe', 'etudiant__nom_ar']
        indexes = [
            models.Index(fields=['sous_groupe', 'actif']),
            models.Index(fields=['etudiant', 'actif']),
        ]

    def save(self, *args, **kwargs):
        """Sauvegarde et met à jour l'effectif du sous-groupe."""
        super().save(*args, **kwargs)
        self.sous_groupe.update_effectif()

    def delete(self, *args, **kwargs):
        """Supprime et met à jour l'effectif du sous-groupe."""
        sous_groupe = self.sous_groupe
        super().delete(*args, **kwargs)
        sous_groupe.update_effectif()

    def __str__(self):
        return f"{self.etudiant} → {self.sous_groupe}"


# ══════════════════════════════════════════════════════════════
# MODÈLE SÉANCE
# ══════════════════════════════════════════════════════════════

class Seance(BaseModel):
    """
    Modèle représentant une séance d'enseignement.
    Une séance est une occurrence d'une classe à une date et heure précises.
    """

    # ══════════════════════════════════════════════════════════
    # CHOIX / CHOICES
    # ══════════════════════════════════════════════════════════

    class Timeblock(models.TextChoices):
        """Créneaux horaires disponibles / الحصص المتاحة"""
        SEANCE01 = '08:00-09:30', 'الحصة الأولى 08:00-09:30'
        SEANCE02 = '09:40-11:10', 'الحصة الثانية 09:40-11:10'
        SEANCE03 = '11:20-12:50', 'الحصة الثالثة 11:20-12:50'
        SEANCE04 = '13:10-14:40', 'الحصة الرابعة 13:10-14:40'
        SEANCE05 = '14:50-16:20', 'الحصة الخامسة 14:50-16:20'
        SEANCE06 = '16:30-18:00', 'الحصة السادسة 16:30-18:00'

    class TypeAudience(models.TextChoices):
        """Types d'audience pour la séance / أنواع الجمهور"""
        GROUPE_COMPLET = 'groupe_complet', 'المجموعة كاملة / Groupe complet'
        SOUS_GROUPE = 'sous_groupe', 'مجموعة فرعية / Sous-groupe'
        MULTI_SOUS_GROUPES = 'multi_sous_groupes', 'عدة مجموعات فرعية / Multi sous-groupes'

    # ══════════════════════════════════════════════════════════
    # RELATIONS
    # ══════════════════════════════════════════════════════════

    classe = models.ForeignKey(
        Classe,
        on_delete=models.PROTECT,
        verbose_name="الفصل / Classe",
        related_name='seances_classe',
        db_index=True
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS DE LA SÉANCE
    # ══════════════════════════════════════════════════════════

    intitule = models.CharField(
        max_length=200,
        verbose_name="عنوان الحصة / Intitulé",
        null=True,
        blank=True,
        default="لم أقم بالتدريس"
    )

    date = models.DateField(
        verbose_name="تاريخ الحصة / Date",
        default=timezone.now
    )

    temps = models.CharField(
        max_length=20,
        verbose_name="وقت الحصة / Créneau horaire",
        default=Timeblock.SEANCE01,
        choices=Timeblock.choices
    )

    # ══════════════════════════════════════════════════════════
    # STATUT DE LA SÉANCE
    # ══════════════════════════════════════════════════════════

    fait = models.BooleanField(
        verbose_name="تمت الحصة / Séance effectuée",
        default=False
    )

    remplacer = models.BooleanField(
        verbose_name="حصة تعويضية / Séance de remplacement",
        default=False
    )

    annuler = models.BooleanField(
        verbose_name="الحصة ملغاة / Séance annulée",
        default=False
    )

    list_abs_etudiant_generee = models.BooleanField(
        verbose_name="تم إنشاء قائمة الغيابات / Liste absences générée",
        default=False
    )

    obs = models.TextField(
        verbose_name="الملاحظة / Observation",
        blank=True
    )

    # ══════════════════════════════════════════════════════════
    # GESTION DES SOUS-GROUPES
    # ══════════════════════════════════════════════════════════

    type_audience = models.CharField(
        max_length=20,
        choices=TypeAudience.choices,
        default=TypeAudience.GROUPE_COMPLET,
        verbose_name="نوع الجمهور / Type d'audience",
        help_text="تحديد من سيحضر هذه الحصة / Définir qui assiste à cette séance"
    )

    sous_groupe_unique = models.ForeignKey(
        SousGroupe,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="المجموعة الفرعية / Sous-groupe",
        help_text="يُستخدم عند اختيار 'مجموعة فرعية' / Utilisé pour un seul sous-groupe",
        related_name='seances_sous_groupe_unique'
    )

    sous_groupes_multiples = models.ManyToManyField(
        SousGroupe,
        blank=True,
        verbose_name="المجموعات الفرعية المتعددة / Sous-groupes multiples",
        help_text="يُستخدم عند اختيار 'عدة مجموعات فرعية' / Utilisé pour plusieurs sous-groupes",
        related_name='seances_sous_groupes_multiples'
    )

    nb_etudiants_concernes = models.PositiveIntegerField(
        verbose_name="عدد الطلاب المعنيين / Nb étudiants concernés",
        default=0,
        help_text="يتم حسابه تلقائياً / Calculé automatiquement"
    )

    class Meta:
        verbose_name = "حصة / Séance"
        verbose_name_plural = "حصص / Séances"
        constraints = [
            models.UniqueConstraint(
                fields=['classe', 'date', 'temps'],
                name='unique_seance_par_classe_date_temps'
            )
        ]
        indexes = [
            models.Index(fields=['classe', 'date']),
            models.Index(fields=['type_audience']),
            models.Index(fields=['fait', 'annuler']),
        ]
        ordering = ['-date', 'temps']

    def clean(self):
        """Validation du modèle."""
        super().clean()

        # Une séance annulée ne peut pas être faite ou remplacée
        if self.annuler and (self.fait or self.remplacer):
            raise ValidationError(
                "حصة ملغاة لا يمكن أن تكون تمت أو تعويضية / "
                "Une séance annulée ne peut pas être marquée comme faite ou remplacée."
            )

        # Validation pour sous-groupe unique
        if self.type_audience == self.TypeAudience.SOUS_GROUPE:
            if not self.sous_groupe_unique:
                raise ValidationError(
                    "يجب تحديد المجموعة الفرعية عند اختيار 'مجموعة فرعية' / "
                    "Un sous-groupe doit être sélectionné."
                )
            # Vérifier que le sous-groupe appartient au groupe de la classe
            if self.classe and self.sous_groupe_unique.groupe_principal != self.classe.niv_spe_dep_sg:
                raise ValidationError(
                    "المجموعة الفرعية يجب أن تنتمي لمجموعة الفصل / "
                    "Le sous-groupe doit appartenir au groupe de la classe."
                )

        # Pour groupe complet, vider le sous-groupe unique
        elif self.type_audience == self.TypeAudience.GROUPE_COMPLET:
            self.sous_groupe_unique = None

    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul du nombre d'étudiants."""
        # Calculer le nombre d'étudiants si l'objet existe déjà
        if self.pk:
            self.nb_etudiants_concernes = len(self.get_etudiants_concernes())
        super().save(*args, **kwargs)

    def __str__(self):
        if not self.classe:
            return f"Séance sans classe - {self.date}"

        audience_info = ""
        if self.type_audience == self.TypeAudience.SOUS_GROUPE and self.sous_groupe_unique:
            audience_info = f" - {self.sous_groupe_unique.nom}"
        elif self.type_audience == self.TypeAudience.MULTI_SOUS_GROUPES:
            count = self.sous_groupes_multiples.count()
            audience_info = f" - {count} مجموعات فرعية"

        return f"{self.classe.matiere.nom_fr} - {self.date} ({self.get_temps_display()}){audience_info}"

    # ══════════════════════════════════════════════════════════
    # MÉTHODES POUR LES ÉTUDIANTS CONCERNÉS
    # ══════════════════════════════════════════════════════════

    def get_etudiants_concernes(self):
        """Retourne la liste des étudiants concernés par cette séance."""
        if self.type_audience == self.TypeAudience.SOUS_GROUPE and self.sous_groupe_unique:
            # Pour un sous-groupe spécifique
            affectations = EtudiantSousGroupe.objects.filter(
                sous_groupe=self.sous_groupe_unique,
                actif=True
            )
            return [aff.etudiant for aff in affectations]

        elif self.type_audience == self.TypeAudience.MULTI_SOUS_GROUPES:
            # Pour plusieurs sous-groupes
            etudiants = []
            for sous_groupe in self.sous_groupes_multiples.filter(actif=True):
                affectations = EtudiantSousGroupe.objects.filter(
                    sous_groupe=sous_groupe,
                    actif=True
                )
                etudiants.extend([aff.etudiant for aff in affectations])
            return list(set(etudiants))  # Éviter les doublons

        else:  # GROUPE_COMPLET
            # Tous les étudiants du groupe principal
            if self.classe and self.classe.niv_spe_dep_sg:
                return list(self.classe.niv_spe_dep_sg.etudiants.filter(est_actif=True))
            return []

    def get_audience_display(self):
        """Retourne l'affichage formaté de l'audience."""
        if self.type_audience == self.TypeAudience.SOUS_GROUPE and self.sous_groupe_unique:
            return f"مجموعة فرعية: {self.sous_groupe_unique.nom_complet}"
        elif self.type_audience == self.TypeAudience.MULTI_SOUS_GROUPES:
            sous_groupes = self.sous_groupes_multiples.filter(actif=True)
            if sous_groupes.exists():
                noms = [sg.nom for sg in sous_groupes]
                return f"مجموعات فرعية: {', '.join(noms)}"
            return "مجموعات فرعية: غير محدد"
        return "المجموعة كاملة / Groupe complet"

    def peut_avoir_sous_groupes(self):
        """Vérifie si cette séance peut utiliser des sous-groupes."""
        if not self.classe or not self.classe.niv_spe_dep_sg:
            return False
        return SousGroupe.objects.filter(
            groupe_principal=self.classe.niv_spe_dep_sg,
            actif=True
        ).exists()

    @property
    def nbr_absence(self):
        """Retourne le nombre d'absences non justifiées."""
        return self.absences_etudiants_seance.filter(present=False, justifiee=False).count()

    @property
    def nbr_absence_justifiee(self):
        """Retourne le nombre d'absences justifiées."""
        return self.absences_etudiants_seance.filter(present=False, justifiee=True).count()


# ══════════════════════════════════════════════════════════════
# MODÈLE GESTION ÉTUDIANT-CLASSE (Absences et Notes)
# ══════════════════════════════════════════════════════════════

class Gestion_Etu_Classe(BaseModel):
    """
    Modèle pour gérer les absences et les notes d'un étudiant dans une classe.
    Centralise toutes les informations de suivi d'un étudiant pour une matière.
    """

    # ══════════════════════════════════════════════════════════
    # RELATIONS
    # ══════════════════════════════════════════════════════════

    classe = models.ForeignKey(
        Classe,
        on_delete=models.PROTECT,
        verbose_name="الحصة / Classe",
        related_name='gestion_etudiants',
        null=True,
        db_index=True
    )

    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.PROTECT,
        verbose_name="الطالب / Étudiant",
        related_name='gestion_classes',
        null=True,
        db_index=True
    )

    # ══════════════════════════════════════════════════════════
    # GESTION DES ABSENCES
    # ══════════════════════════════════════════════════════════

    nbr_absence = models.PositiveIntegerField(
        verbose_name="عدد الغيابات / Nb absences",
        default=0,
        help_text="العدد الإجمالي للغيابات / Nombre total d'absences"
    )

    nbr_absence_justifiee = models.PositiveIntegerField(
        verbose_name="عدد الغيابات المبررة / Nb absences justifiées",
        default=0,
        help_text="الغيابات المبررة بوثائق رسمية / Absences justifiées par documents"
    )

    nbr_seances_totales = models.PositiveIntegerField(
        verbose_name="العدد الإجمالي للحصص / Nb total séances",
        default=0,
        help_text="يتم حسابه تلقائياً / Calculé automatiquement"
    )

    # ══════════════════════════════════════════════════════════
    # POINTS SUPPLÉMENTAIRES
    # ══════════════════════════════════════════════════════════

    total_sup_seance = models.DecimalField(
        verbose_name="نقاط إضافية للمشاركة / Points bonus participation",
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('3.00'))
        ],
        help_text="نقاط إضافية للمشاركة المتميزة (حد أقصى 3 نقاط) / Max 3 points"
    )

    # ══════════════════════════════════════════════════════════
    # BARÈME DE NOTATION
    # ══════════════════════════════════════════════════════════

    note_presence = models.DecimalField(
        verbose_name="نقطة الحضور / Note présence",
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ],
        help_text="محسوبة تلقائياً حسب نسبة الحضور / Calculée auto selon présence"
    )

    note_participe_HW = models.DecimalField(
        verbose_name="نقطة المشاركة والأعمال المنزلية / Note participation/devoirs",
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ],
        help_text="تقييم المشاركة والواجبات المنزلية / Évaluation participation et devoirs"
    )

    note_controle_1 = models.DecimalField(
        verbose_name="نقطة الإمتحان 1 / Note contrôle 1",
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ],
        help_text="نقطة الامتحان 1 / Note du contrôle 1"
    )

    note_controle_2 = models.DecimalField(
        verbose_name="نقطة الإمتحان 2 / Note contrôle 2",
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ],
        help_text="نقطة الامتحان 2 / Note du contrôle 2"
    )

    # ══════════════════════════════════════════════════════════
    # NOTE FINALE
    # ══════════════════════════════════════════════════════════

    note_finale = models.DecimalField(
        verbose_name="النقطة النهائية / Note finale",
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('20.00'))
        ],
        help_text="النقطة النهائية محسوبة تلقائياً / Note finale calculée auto"
    )

    # ══════════════════════════════════════════════════════════
    # MÉTADONNÉES DE VALIDATION
    # ══════════════════════════════════════════════════════════

    date_derniere_maj = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ آخر تحديث / Dernière mise à jour"
    )

    validee_par_enseignant = models.BooleanField(
        default=False,
        verbose_name="تم التصديق من طرف الأستاذ / Validé par enseignant",
        help_text="هل تم تأكيد النقاط من طرف الأستاذ؟ / Notes confirmées par l'enseignant?"
    )

    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ التصديق / Date validation"
    )

    obs = models.TextField(
        verbose_name="الملاحظة / Observation",
        null=True,
        blank=True,
        default="",
        help_text="ملاحظات الأستاذ حول أداء الطالب / Observations de l'enseignant"
    )

    class Meta:
        verbose_name = "إدارة طالب-حصة / Gestion Étudiant-Classe"
        verbose_name_plural = "إدارة طلاب-حصص / Gestions Étudiants-Classes"
        unique_together = ['classe', 'etudiant']
        indexes = [
            models.Index(fields=['classe', 'validee_par_enseignant']),
            models.Index(fields=['etudiant', 'note_finale']),
            models.Index(fields=['classe', 'note_finale']),
        ]
        ordering = ['classe', 'etudiant__nom_ar', 'etudiant__prenom_ar']

    def __str__(self):
        if self.etudiant and self.classe:
            return f"{self.etudiant.nom_ar} {self.etudiant.prenom_ar} - {self.classe} - {self.note_finale}/20"
        return f"Gestion #{self.pk}"

    def clean(self):
        """Validation des données."""
        super().clean()

        # Vérifier que les absences justifiées <= total absences
        if self.nbr_absence_justifiee > self.nbr_absence:
            raise ValidationError({
                'nbr_absence_justifiee': 'عدد الغيابات المبررة لا يمكن أن يكون أكبر من العدد الإجمالي للغيابات / '
                                         'Les absences justifiées ne peuvent pas dépasser le total des absences.'
            })

    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul automatique des notes."""
        self.calculate_note_presence()
        self.calculate_note_finale()

        if self.validee_par_enseignant and not self.date_validation:
            self.date_validation = timezone.now()
        elif not self.validee_par_enseignant:
            self.date_validation = None

        super().save(*args, **kwargs)

    # ══════════════════════════════════════════════════════════
    # MÉTHODES DE CALCUL
    # ══════════════════════════════════════════════════════════

    def calculate_note_presence(self):
        """Calcule automatiquement la note de présence."""
        # Calculer nbr_seances_totales dynamiquement
        if self.classe:
            nbr_seances_reelles = self.classe.seances_classe.filter(
                annuler=False,
                fait=True
            ).count()
            self.nbr_seances_totales = nbr_seances_reelles
        else:
            self.nbr_seances_totales = 0

        # Si aucune séance n'a eu lieu, note = 0
        if self.nbr_seances_totales == 0:
            self.note_presence = Decimal('0.00')
            return

        # Système: Départ à 5 points, -1 par absence non justifiée
        absences_non_justifiees = self.nbr_absence - self.nbr_absence_justifiee
        self.note_presence = max(Decimal('0.00'), Decimal('5.00') - Decimal(str(absences_non_justifiees)))

    def calculate_note_finale(self):
        """Calcule la note finale en additionnant toutes les composantes."""
        note_presence = self.note_presence or Decimal('0.00')
        note_participe = self.note_participe_HW or Decimal('0.00')
        note_controle_1 = self.note_controle_1 or Decimal('0.00')
        note_controle_2 = self.note_controle_2 or Decimal('0.00')
        total_sup_seance = self.total_sup_seance or Decimal('0.00')

        base_total = note_presence + note_participe + note_controle_1 + note_controle_2
        bonus_total = total_sup_seance

        # Limiter à 20 points maximum
        self.note_finale = min(Decimal('20.00'), base_total + bonus_total)

    def update_nbr_seances_totales(self):
        """Met à jour le nombre total de séances pour cette classe."""
        if self.classe:
            total_seances = self.classe.seances_classe.filter(annuler=False).count()
            self.nbr_seances_totales = total_seances
            self.save(update_fields=['nbr_seances_totales'])

    # ══════════════════════════════════════════════════════════
    # PROPRIÉTÉS UTILES
    # ══════════════════════════════════════════════════════════

    @property
    def taux_presence_pourcentage(self):
        """Retourne le taux de présence en pourcentage."""
        if self.nbr_seances_totales == 0:
            return 0
        absences_non_justifiees = self.nbr_absence - self.nbr_absence_justifiee
        presence = max(0, self.nbr_seances_totales - absences_non_justifiees)
        return round((presence / self.nbr_seances_totales) * 100, 1)

    @property
    def nombre_participations(self):
        """Retourne le nombre total de participations de l'étudiant."""
        if not self.classe or not self.etudiant:
            return 0
        return Abs_Etu_Seance.objects.filter(
            seance__classe=self.classe,
            etudiant=self.etudiant,
            participation=True
        ).count()

    @property
    def mention(self):
        """Retourne la mention selon la note finale."""
        if self.note_finale >= 16:
            return "ممتاز"
        elif self.note_finale >= 14:
            return "جيد جداً"
        elif self.note_finale >= 12:
            return "جيد"
        elif self.note_finale >= 10:
            return "مقبول"
        else:
            return "لا شيء"

    @property
    def est_admis(self):
        """Vérifie si l'étudiant est admis (note >= 10)."""
        return self.note_finale >= 10

    @property
    def points_bonus_total(self):
        """Retourne le total des points bonus."""
        return self.total_sup_seance

    # ══════════════════════════════════════════════════════════
    # MÉTHODES UTILITAIRES
    # ══════════════════════════════════════════════════════════

    def valider_notes(self, enseignant=None):
        """Valide les notes (appelée par l'enseignant)."""
        self.validee_par_enseignant = True
        self.date_validation = timezone.now()
        self.save(update_fields=['validee_par_enseignant', 'date_validation'])

    def invalider_notes(self):
        """Invalide les notes (pour permettre modification)."""
        self.validee_par_enseignant = False
        self.date_validation = None
        self.save(update_fields=['validee_par_enseignant', 'date_validation'])

    @classmethod
    def get_statistiques_classe(cls, classe):
        """Retourne les statistiques pour une classe donnée."""
        notes = cls.objects.filter(classe=classe)

        if not notes.exists():
            return {
                'nombre_etudiants': 0,
                'moyenne_classe': 0,
                'note_max': 0,
                'note_min': 0,
                'nombre_admis': 0,
                'taux_reussite': 0
            }

        notes_finales = [float(note.note_finale or 0) for note in notes]

        return {
            'nombre_etudiants': notes.count(),
            'moyenne_classe': round(sum(notes_finales) / len(notes_finales), 2) if notes_finales else 0,
            'note_max': max(notes_finales) if notes_finales else 0,
            'note_min': min(notes_finales) if notes_finales else 0,
            'nombre_admis': notes.filter(note_finale__gte=10).count(),
            'taux_reussite': round((notes.filter(note_finale__gte=10).count() / notes.count()) * 100, 1) if notes.count() > 0 else 0
        }

    @staticmethod
    def update_all_presence_notes_for_classe(classe):
        """Met à jour les notes de présence pour tous les étudiants d'une classe."""
        notes_classe = Gestion_Etu_Classe.objects.filter(classe=classe)

        for note in notes_classe:
            note.calculate_note_presence()
            note.save(update_fields=['note_presence', 'nbr_seances_totales', 'note_finale'])


# ══════════════════════════════════════════════════════════════
# MODÈLE ABSENCE ÉTUDIANT PAR SÉANCE
# ══════════════════════════════════════════════════════════════

class Abs_Etu_Seance(BaseModel):
    """
    Modèle pour suivre la présence/absence d'un étudiant à une séance spécifique.
    Permet également de noter la participation et les points supplémentaires.
    """

    # ══════════════════════════════════════════════════════════
    # RELATIONS
    # ══════════════════════════════════════════════════════════

    seance = models.ForeignKey(
        Seance,
        on_delete=models.CASCADE,
        verbose_name="الحصة / Séance",
        related_name='absences_etudiants_seance',
        db_index=True
    )

    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.PROTECT,
        verbose_name="الطالب / Étudiant",
        related_name='absences_etudiant',
        db_index=True
    )

    # ══════════════════════════════════════════════════════════
    # PRÉSENCE ET PARTICIPATION
    # ══════════════════════════════════════════════════════════

    present = models.BooleanField(
        verbose_name="حضور الطالب / Présent",
        default=False
    )

    justifiee = models.BooleanField(
        verbose_name="غياب مبرر / Absence justifiée",
        default=False
    )

    participation = models.BooleanField(
        verbose_name="مشاركة في الحصة / Participation",
        default=False
    )

    points_sup_seance = models.DecimalField(
        verbose_name="نقطة + / Points bonus",
        max_digits=3,
        decimal_places=1,
        default=Decimal('0.0')
    )

    obs = models.TextField(
        verbose_name="ملاحظة / Observation",
        blank=True
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS SUR LES SOUS-GROUPES
    # ══════════════════════════════════════════════════════════

    sous_groupe_concerne = models.ForeignKey(
        SousGroupe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المجموعة الفرعية المعنية / Sous-groupe concerné",
        help_text="المجموعة الفرعية التي ينتمي إليها الطالب في هذه الحصة / Sous-groupe de l'étudiant pour cette séance",
        related_name='absences_sous_groupe'
    )

    type_audience_lors_creation = models.CharField(
        max_length=20,
        verbose_name="نوع الجمهور عند الإنشاء / Type audience à la création",
        help_text="لحفظ نوع الجمهور عند إنشاء الغياب / Pour historique",
        blank=True
    )

    class Meta:
        verbose_name = "حضور/غياب طالب-حصة / Présence Étudiant-Séance"
        verbose_name_plural = "حضور/غياب طلاب-حصص / Présences Étudiants-Séances"
        constraints = [
            models.UniqueConstraint(
                fields=['seance', 'etudiant'],
                name='unique_absence_par_seance_etudiant'
            )
        ]
        indexes = [
            models.Index(fields=['seance', 'present']),
            models.Index(fields=['etudiant', 'present']),
            models.Index(fields=['sous_groupe_concerne']),
        ]
        ordering = ['seance', 'etudiant__nom_ar']

    def save(self, *args, **kwargs):
        """Sauvegarde avec auto-remplissage des champs sous-groupes."""
        # Auto-remplir le type d'audience
        if not self.type_audience_lors_creation and self.seance:
            self.type_audience_lors_creation = self.seance.type_audience

        # Auto-remplir le sous-groupe si applicable
        if not self.sous_groupe_concerne and self.seance:
            if self.seance.type_audience == Seance.TypeAudience.SOUS_GROUPE:
                self.sous_groupe_concerne = self.seance.sous_groupe_unique

        super().save(*args, **kwargs)

    def __str__(self):
        sous_groupe_info = ""
        if self.sous_groupe_concerne:
            sous_groupe_info = f" ({self.sous_groupe_concerne.nom})"

        status = "حاضر" if self.present else ("مبرر" if self.justifiee else "غائب")
        return f"{self.etudiant.nom_ar} {self.etudiant.prenom_ar} - {self.seance} - {status}{sous_groupe_info}"


# ══════════════════════════════════════════════════════════════
# CLASSE UTILITAIRE POUR LA GESTION DES SOUS-GROUPES
# ══════════════════════════════════════════════════════════════

class SousGroupeManager:
    """
    Classe utilitaire pour gérer les opérations sur les sous-groupes.
    Fournit des méthodes statiques pour la création et la répartition automatiques.
    """

    @staticmethod
    def creer_sous_groupes_automatiques(groupe_principal, nombre_sous_groupes, prefixe="", enseignant=None):
        """
        Créer automatiquement des sous-groupes pour un groupe.

        Args:
            groupe_principal: Instance de NivSpeDep_SG
            nombre_sous_groupes: Nombre de sous-groupes à créer
            prefixe: Préfixe pour les noms (ex: "SG", "Groupe")
            enseignant: Enseignant créateur (optionnel)

        Returns:
            Liste des sous-groupes créés
        """
        sous_groupes = []

        for i in range(1, nombre_sous_groupes + 1):
            nom = f"{prefixe}{i}" if prefixe else str(i)

            sous_groupe, created = SousGroupe.objects.get_or_create(
                groupe_principal=groupe_principal,
                nom=nom,
                defaults={
                    'nom_complet': f"{groupe_principal} - {nom}",
                    'actif': True,
                    'ordre_affichage': i,
                    'created_by': enseignant
                }
            )
            sous_groupes.append(sous_groupe)

        return sous_groupes

    @staticmethod
    def repartir_etudiants_automatiquement(groupe_principal, enseignant=None):
        """
        Répartir automatiquement les étudiants dans les sous-groupes.

        Args:
            groupe_principal: Instance de NivSpeDep_SG
            enseignant: Enseignant effectuant la répartition (optionnel)

        Returns:
            True si la répartition a réussi, False sinon
        """
        # Récupérer tous les étudiants du groupe principal
        etudiants = groupe_principal.etudiants.filter(est_actif=True)

        # Récupérer tous les sous-groupes actifs
        sous_groupes = SousGroupe.objects.filter(
            groupe_principal=groupe_principal,
            actif=True
        ).order_by('ordre_affichage')

        if not sous_groupes.exists():
            return False

        # Effacer les anciennes affectations
        EtudiantSousGroupe.objects.filter(sous_groupe__in=sous_groupes).delete()

        # Répartir équitablement
        affectations = []
        sous_groupes_list = list(sous_groupes)
        nb_sg = len(sous_groupes_list)

        for index, etudiant in enumerate(etudiants):
            sous_groupe = sous_groupes_list[index % nb_sg]

            affectation = EtudiantSousGroupe(
                etudiant=etudiant,
                sous_groupe=sous_groupe,
                ordre_dans_groupe=index // nb_sg + 1,
                affecte_par=enseignant
            )
            affectations.append(affectation)

        # Créer toutes les affectations en une fois
        EtudiantSousGroupe.objects.bulk_create(affectations)

        # Mettre à jour les effectifs
        for sous_groupe in sous_groupes:
            sous_groupe.update_effectif()

        return True

    @staticmethod
    def generer_liste_absences_pour_seance(seance):
        """
        Génère automatiquement la liste des absences pour une séance.

        Args:
            seance: Instance de Seance

        Returns:
            Nombre d'absences créées
        """
        etudiants_concernes = seance.get_etudiants_concernes()

        # Supprimer les anciennes absences si elles existent
        Abs_Etu_Seance.objects.filter(seance=seance).delete()

        # Créer les nouvelles absences
        absences = []
        for etudiant in etudiants_concernes:
            # Déterminer le sous-groupe concerné
            sous_groupe_concerne = None
            if seance.type_audience == Seance.TypeAudience.SOUS_GROUPE:
                sous_groupe_concerne = seance.sous_groupe_unique
            elif seance.type_audience == Seance.TypeAudience.MULTI_SOUS_GROUPES:
                # Trouver le sous-groupe de cet étudiant parmi ceux sélectionnés
                for sg in seance.sous_groupes_multiples.all():
                    if EtudiantSousGroupe.objects.filter(
                        etudiant=etudiant,
                        sous_groupe=sg,
                        actif=True
                    ).exists():
                        sous_groupe_concerne = sg
                        break

            absence = Abs_Etu_Seance(
                seance=seance,
                etudiant=etudiant,
                present=True,  # Par défaut présent
                sous_groupe_concerne=sous_groupe_concerne,
                type_audience_lors_creation=seance.type_audience
            )
            absences.append(absence)

        # Créer toutes les absences en une fois
        Abs_Etu_Seance.objects.bulk_create(absences)

        # Marquer la liste comme générée
        seance.list_abs_etudiant_generee = True
        seance.nb_etudiants_concernes = len(etudiants_concernes)
        seance.save(update_fields=['list_abs_etudiant_generee', 'nb_etudiants_concernes'])

        return len(absences)
