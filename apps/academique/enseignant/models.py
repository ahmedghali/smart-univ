# apps/academique/enseignant/models.py

from django.db import models
from django.core.exceptions import ValidationError
from apps.noyau.commun.models import BaseModel, Wilaya, Diplome, Grade
from apps.noyau.authentification.models import CustomUser


# ══════════════════════════════════════════════════════════════
# MODÈLE ENSEIGNANT
# ══════════════════════════════════════════════════════════════

class Enseignant(BaseModel):
    """
    Modèle représentant un enseignant de l'université.
    Contient toutes les informations personnelles, professionnelles et académiques.
    """

    # ══════════════════════════════════════════════════════════
    # CHOIX / CHOICES
    # ══════════════════════════════════════════════════════════

    class SitFam(models.TextChoices):
        """Situation Familiale / الحالة العائلية"""
        CELIBATAIRE = 'أعزب', 'أعزب'
        MARIE = 'متزوج', 'متزوج'
        DIVORCE = 'مطلق', 'مطلق'
        VEUF = 'أرمل', 'أرمل'

    class Civilite(models.TextChoices):
        """Civilité / حضرة"""
        MR = 'Mr', 'السيد'
        MME = 'Mme', 'السيدة'
        MLLE = 'Mlle', 'الآنسة'

    class Sexe(models.TextChoices):
        """Sexe / الجنس"""
        M = "ذكر", "ذكر"
        F = "أنثى", "أنثى"

    # ══════════════════════════════════════════════════════════
    # RELATION AVEC UTILISATEUR
    # ══════════════════════════════════════════════════════════

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'poste_principal__type': 'enseignant'},
        verbose_name="المستخدم / Utilisateur",
        related_name='enseignant_profile',
        help_text="Compte utilisateur lié à cet enseignant",
        null=True,
        blank=True
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS PERSONNELLES / PERSONAL INFORMATION
    # ══════════════════════════════════════════════════════════

    civilite = models.CharField(
        max_length=50,
        verbose_name="حضرة / Civilité",
        choices=Civilite.choices,
        blank=True,
        default=""
    )

    nom_ar = models.CharField(
        max_length=100,
        verbose_name="اللقب / Nom",
        blank=True,
        default=""
    )

    prenom_ar = models.CharField(
        max_length=100,
        verbose_name="الإسم / Prénom",
        blank=True,
        default=""
    )

    nom_fr = models.CharField(
        max_length=100,
        verbose_name="Nom",
        blank=True,
        default=""
    )

    prenom_fr = models.CharField(
        max_length=100,
        verbose_name="Prénom",
        blank=True,
        default=""
    )

    date_nais = models.DateField(
        verbose_name="تاريخ الميلاد / Date de naissance",
        null=True,
        blank=True
    )

    sex = models.CharField(
        max_length=50,
        verbose_name="الجنس / Sexe",
        choices=Sexe.choices,
        blank=True,
        default=Sexe.M
    )

    sitfam = models.CharField(
        max_length=50,
        verbose_name="الحالة العائلية / Situation familiale",
        choices=SitFam.choices,
        blank=True,
        default=SitFam.CELIBATAIRE
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS ADMINISTRATIVES / ADMINISTRATIVE INFO
    # ══════════════════════════════════════════════════════════

    matricule = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="رقم التسجيل / Matricule",
        help_text="Ex: ENS2024001"
    )

    codeIns = models.CharField(
        max_length=20,
        verbose_name="كود التسجيل / Code d'inscription",
        blank=True,
        default=""
    )

    bac_annee = models.CharField(
        max_length=4,
        verbose_name="سنة البكالوريا / Année du bac",
        blank=True,
        default="",
        help_text="Ex: 2010"
    )

    date_Recrut = models.DateField(
        verbose_name="تاريخ الإلتحاق بالجامعة / Date de recrutement",
        null=True,
        blank=True
    )

    # ══════════════════════════════════════════════════════════
    # COORDONNÉES / CONTACT INFORMATION
    # ══════════════════════════════════════════════════════════

    telmobile1 = models.CharField(
        max_length=50,
        verbose_name="الهاتف المحمول 1 / Tel mobile 1",
        blank=True,
        default=""
    )

    telmobile2 = models.CharField(
        max_length=50,
        verbose_name="الهاتف المحمول 2 / Tel mobile 2",
        blank=True,
        default=""
    )

    telfix = models.CharField(
        max_length=50,
        verbose_name="الهاتف الثابت / Tel fixe",
        blank=True,
        default=""
    )

    fax = models.CharField(
        max_length=50,
        verbose_name="الفاكس / Fax",
        blank=True,
        default=""
    )

    email_perso = models.EmailField(
        max_length=100,
        verbose_name="البريد الإلكتروني الشخصي / E-mail personnel",
        blank=True,
        default=""
    )

    email_prof = models.EmailField(
        max_length=100,
        verbose_name="البريد الإلكتروني المهني / E-mail professionnel",
        blank=True,
        default=""
    )

    adresse = models.CharField(
        max_length=200,
        verbose_name="العنوان / Adresse",
        blank=True,
        default=""
    )

    wilaya = models.ForeignKey(
        Wilaya,
        on_delete=models.PROTECT,
        verbose_name="الولاية / Wilaya",
        null=True,
        blank=True,
        related_name='enseignants_wilaya'
    )

    # ══════════════════════════════════════════════════════════
    # QUALIFICATIONS ACADÉMIQUES / ACADEMIC QUALIFICATIONS
    # ══════════════════════════════════════════════════════════

    diplome = models.ForeignKey(
        Diplome,
        on_delete=models.PROTECT,
        verbose_name="الدبلوم / Diplôme",
        null=True,
        blank=True,
        related_name='enseignants_diplome'
    )

    specialite_ar = models.CharField(
        max_length=100,
        verbose_name="التخصص / Spécialité",
        blank=True,
        default=""
    )

    specialite_fr = models.CharField(
        max_length=100,
        verbose_name="Spécialité",
        blank=True,
        default=""
    )

    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        verbose_name="الرتبة / Grade",
        null=True,
        blank=True,
        related_name='enseignants_grade',
        help_text="Ex: Professeur, MCA, MCB, MAA, MAB"
    )

    # ══════════════════════════════════════════════════════════
    # PLATEFORMES ACADÉMIQUES / ACADEMIC PLATFORMS
    # ══════════════════════════════════════════════════════════

    inscritProgres = models.BooleanField(
        verbose_name="مسجل بمنصة PROGRES / Inscrit PROGRES",
        default=False
    )

    inscritMoodle = models.BooleanField(
        verbose_name="مسجل بمنصة MOODLE / Inscrit MOODLE",
        default=False
    )

    inscritSNDL = models.BooleanField(
        verbose_name="مسجل بمنصة SNDL / Inscrit SNDL",
        default=False
    )

    # ══════════════════════════════════════════════════════════
    # RÉSEAUX SOCIAUX ET ACADÉMIQUES / SOCIAL & ACADEMIC NETWORKS
    # ══════════════════════════════════════════════════════════

    googlescholar = models.URLField(
        max_length=200,
        verbose_name="Google Scholar",
        blank=True,
        default="",
        help_text="URL du profil Google Scholar"
    )

    researchgate = models.URLField(
        max_length=200,
        verbose_name="Research Gate",
        blank=True,
        default="",
        help_text="URL du profil ResearchGate"
    )

    orcid_id = models.CharField(
        max_length=100,
        verbose_name="ORCID iD",
        blank=True,
        default="",
        help_text="Ex: 0000-0002-1234-5678"
    )

    linkedIn = models.URLField(
        max_length=200,
        verbose_name="LinkedIn",
        blank=True,
        default=""
    )

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

    # ══════════════════════════════════════════════════════════
    # STATUT / STATUS
    # ══════════════════════════════════════════════════════════

    vacAcademique = models.BooleanField(
        verbose_name="عطلة أكاديمية / Vacances académiques",
        default=False
    )

    maladie = models.BooleanField(
        verbose_name="عطلة مرضية / Congé maladie",
        default=False
    )

    est_inscrit = models.BooleanField(
        default=True,
        verbose_name="مسجل بمنصة Inscrit sur UNIV"
    )

    # ══════════════════════════════════════════════════════════
    # MÉTRIQUES GOOGLE SCHOLAR / GOOGLE SCHOLAR METRICS
    # ══════════════════════════════════════════════════════════

    scholar_publications_count = models.IntegerField(
        default=0,
        verbose_name="عدد المنشورات / Nombre de publications"
    )

    scholar_citations_count = models.IntegerField(
        default=0,
        verbose_name="عدد الاستشهادات / Nombre de citations"
    )

    scholar_h_index = models.IntegerField(
        default=0,
        verbose_name="H-index"
    )

    scholar_i10_index = models.IntegerField(
        default=0,
        verbose_name="i10-index"
    )

    scholar_last_update = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخر تحديث / Dernière mise à jour"
    )

    # ══════════════════════════════════════════════════════════
    # META
    # ══════════════════════════════════════════════════════════

    class Meta:
        verbose_name = "أستاذ / Enseignant"
        verbose_name_plural = "الأساتذة / Enseignants"
        ordering = ['nom_ar', 'prenom_ar']
        indexes = [
            models.Index(fields=['matricule']),
            models.Index(fields=['user']),
            models.Index(fields=['grade']),
            models.Index(fields=['wilaya']),
        ]

    # ══════════════════════════════════════════════════════════
    # MÉTHODES / METHODS
    # ══════════════════════════════════════════════════════════

    def __str__(self):
        """Représentation string de l'enseignant."""
        nom = self.nom_ar or self.nom_fr or "Sans nom"
        prenom = self.prenom_ar or self.prenom_fr or ""
        return f"{nom} {prenom}".strip() or self.matricule

    def get_nom_complet(self, langue='ar'):
        """Retourne le nom complet selon la langue."""
        if langue == 'ar':
            nom = self.nom_ar or self.nom_fr or ""
            prenom = self.prenom_ar or self.prenom_fr or ""
            return f"{nom} {prenom}".strip() or self.matricule
        else:
            nom = self.nom_fr or self.nom_ar or ""
            prenom = self.prenom_fr or self.prenom_ar or ""
            return f"{prenom} {nom}".strip() or self.matricule

    def get_specialite(self, langue='ar'):
        """Retourne la spécialité selon la langue."""
        if langue == 'ar':
            return self.specialite_ar or self.specialite_fr or "-"
        return self.specialite_fr or self.specialite_ar or "-"

    @property
    def scholar_user_id(self):
        """Extrait l'ID utilisateur depuis l'URL Google Scholar."""
        if not self.googlescholar:
            return None
        import re
        match = re.search(r'user=([^&]+)', self.googlescholar)
        return match.group(1) if match else None

    def clean(self):
        """Validation des données."""
        super().clean()

        # Validation du matricule
        if not self.matricule:
            raise ValidationError({
                'matricule': "Le matricule est obligatoire."
            })

        # Au moins un nom doit être renseigné
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError({
                'nom_ar': "Au moins un nom (arabe ou français) doit être renseigné.",
                'nom_fr': "Au moins un nom (arabe ou français) doit être renseigné."
            })

        # Validation de l'ORCID iD format
        if self.orcid_id:
            import re
            pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$'
            if not re.match(pattern, self.orcid_id):
                raise ValidationError({
                    'orcid_id': "Format ORCID iD invalide. Format attendu: 0000-0002-1234-5678"
                })
