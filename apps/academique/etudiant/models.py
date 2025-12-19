# apps/academique/etudiant/models.py

from django.db import models
from django.core.exceptions import ValidationError
from apps.noyau.commun.models import BaseModel, Wilaya
from apps.noyau.authentification.models import CustomUser
from apps.academique.departement.models import NivSpeDep_SG


# ══════════════════════════════════════════════════════════════
# MODÈLE ETUDIANT
# ══════════════════════════════════════════════════════════════

class Etudiant(BaseModel):
    """
    Modèle représentant un étudiant de l'université.
    Contient toutes les informations personnelles, académiques et de contact.
    """

    # ══════════════════════════════════════════════════════════
    # CHOIX / CHOICES
    # ══════════════════════════════════════════════════════════

    class SituationFamiliale(models.TextChoices):
        """Situation Familiale / الحالة العائلية"""
        CELIBATAIRE = 'C', 'أعزب'
        MARIE = 'M', 'متزوج'
        DIVORCE = 'D', 'مطلق'
        VEUF = 'V', 'أرمل'

    class Civilite(models.TextChoices):
        """Civilité / حضرة"""
        MR = 'Mr', 'السيد'
        MME = 'Mme', 'السيدة'
        MLLE = 'Mlle', 'الآنسة'

    class Sexe(models.TextChoices):
        """Sexe / الجنس"""
        M = 'ذكر', 'ذكر'
        F = 'أنثى', 'أنثى'

    # ══════════════════════════════════════════════════════════
    # RELATION AVEC UTILISATEUR
    # ══════════════════════════════════════════════════════════

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'poste_principal__type': 'etudiant'},
        null=True,
        blank=True,
        verbose_name="المستخدم / Utilisateur",
        related_name='etudiant_profile',
        help_text="Compte utilisateur lié à cet étudiant"
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS PERSONNELLES / PERSONAL INFORMATION
    # ══════════════════════════════════════════════════════════

    civilite = models.CharField(
        max_length=10,
        verbose_name="حضرة / Civilité",
        choices=Civilite.choices,
        default=Civilite.MR
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

    sexe = models.CharField(
        max_length=10,
        verbose_name="الجنس / Sexe",
        choices=Sexe.choices,
        default=Sexe.M
    )

    sit_fam = models.CharField(
        max_length=10,
        verbose_name="الحالة العائلية / Situation familiale",
        choices=SituationFamiliale.choices,
        default=SituationFamiliale.CELIBATAIRE
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS ACADÉMIQUES / ACADEMIC INFORMATION
    # ══════════════════════════════════════════════════════════

    matricule = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="الرقم التسلسلي / Matricule",
        help_text="Ex: ETU2024001"
    )

    num_ins = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="رقم التسجيل / Numéro d'inscription",
        help_text="Numéro d'inscription national"
    )

    bac_annee = models.CharField(
        max_length=4,
        verbose_name="سنة البكالوريا / Année du bac",
        blank=True,
        default="",
        help_text="Ex: 2020"
    )

    niv_spe_dep_sg = models.ForeignKey(
        NivSpeDep_SG,
        on_delete=models.PROTECT,
        related_name='etudiants',
        verbose_name="المستوى، التخصص، القسم، والفوج / Niveau-Spé-Dép-SG",
        help_text="Niveau, Spécialité, Département, Section et Groupe"
    )

    delegue = models.BooleanField(
        verbose_name="مندوب الطلبة / Étudiant délégué",
        default=False
    )

    # ══════════════════════════════════════════════════════════
    # COORDONNÉES / CONTACT INFORMATION
    # ══════════════════════════════════════════════════════════

    tel_mobile1 = models.CharField(
        max_length=20,
        verbose_name="الهاتف المحمول 1 / Tel mobile 1",
        blank=True,
        default=""
    )

    tel_mobile2 = models.CharField(
        max_length=20,
        verbose_name="الهاتف المحمول 2 / Tel mobile 2",
        blank=True,
        default=""
    )

    tel_fix = models.CharField(
        max_length=20,
        verbose_name="الهاتف الثابت / Tel fixe",
        blank=True,
        default=""
    )

    fax = models.CharField(
        max_length=20,
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
        related_name='etudiants_wilaya'
    )

    # ══════════════════════════════════════════════════════════
    # PLATEFORMES ACADÉMIQUES / ACADEMIC PLATFORMS
    # ══════════════════════════════════════════════════════════

    inscrit_progres = models.BooleanField(
        verbose_name="مسجل بمنصة PROGRES / Inscrit PROGRES",
        default=False
    )

    inscrit_moodle = models.BooleanField(
        verbose_name="مسجل بمنصة MOODLE / Inscrit MOODLE",
        default=False
    )

    inscrit_sndl = models.BooleanField(
        verbose_name="مسجل بمنصة SNDL / Inscrit SNDL",
        default=False
    )

    est_inscrit = models.BooleanField(
        default=True,
        verbose_name="مسجل بمنصة Inscrit sur UNIV"
    )

    # ══════════════════════════════════════════════════════════
    # RÉSEAUX SOCIAUX ET ACADÉMIQUES / SOCIAL & ACADEMIC NETWORKS
    # ══════════════════════════════════════════════════════════

    google_scholar = models.URLField(
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

    linkedin = models.URLField(
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

    en_vac_aca = models.BooleanField(
        verbose_name="عطلة أكاديمية / Vacances académiques",
        default=False
    )

    en_maladie = models.BooleanField(
        verbose_name="عطلة مرضية / Congé maladie",
        default=False
    )

    est_actif = models.BooleanField(
        verbose_name="نشط / Actif",
        default=False
    )

    # ══════════════════════════════════════════════════════════
    # META
    # ══════════════════════════════════════════════════════════

    class Meta:
        verbose_name = "طالب / Étudiant"
        verbose_name_plural = "الطلبة / Étudiants"
        ordering = ['nom_ar', 'prenom_ar']
        indexes = [
            models.Index(fields=['matricule']),
            models.Index(fields=['num_ins']),
            models.Index(fields=['user']),
            models.Index(fields=['niv_spe_dep_sg']),
            models.Index(fields=['wilaya']),
            models.Index(fields=['est_actif']),
        ]

    # ══════════════════════════════════════════════════════════
    # MÉTHODES / METHODS
    # ══════════════════════════════════════════════════════════

    def __str__(self):
        """Représentation string de l'étudiant."""
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

    def get_niveau_info(self):
        """Retourne les informations du niveau, spécialité, département."""
        if self.niv_spe_dep_sg:
            return str(self.niv_spe_dep_sg)
        return "-"

    def clean(self):
        """Validation des données."""
        super().clean()

        # Validation du matricule
        if not self.matricule:
            raise ValidationError({
                'matricule': "Le matricule est obligatoire."
            })

        # Validation du numéro d'inscription
        if not self.num_ins:
            raise ValidationError({
                'num_ins': "Le numéro d'inscription est obligatoire."
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

        # Validation année bac (4 chiffres)
        if self.bac_annee and len(self.bac_annee) != 4:
            raise ValidationError({
                'bac_annee': "L'année du bac doit être composée de 4 chiffres."
            })
