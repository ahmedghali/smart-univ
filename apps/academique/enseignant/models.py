# apps/academique/enseignant/models.py

from django.core.exceptions import ValidationError
from django.db import models

from apps.noyau.authentification.models import CustomUser, get_avatar_palette_for
from apps.noyau.commun.models import BaseModel, Diplome, Grade, Wilaya

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

        CELIBATAIRE = "أعزب", "أعزب"
        MARIE = "متزوج", "متزوج"
        DIVORCE = "مطلق", "مطلق"
        VEUF = "أرمل", "أرمل"

    class Civilite(models.TextChoices):
        """Civilité / حضرة"""

        MR = "Mr", "السيد"
        MME = "Mme", "السيدة"
        MLLE = "Mlle", "الآنسة"

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
        verbose_name="المستخدم / Utilisateur",
        related_name="enseignant_profile",
        help_text="Compte utilisateur lié à cet enseignant",
        null=True,
        blank=True,
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS PERSONNELLES / PERSONAL INFORMATION
    # ══════════════════════════════════════════════════════════

    civilite = models.CharField(
        max_length=50, verbose_name="حضرة / Civilité", choices=Civilite.choices, blank=True, default=""
    )

    nom_fr = models.CharField(max_length=100, verbose_name="Nom", blank=True, default="")

    prenom_fr = models.CharField(max_length=100, verbose_name="Prénom", blank=True, default="")

    nom_ar = models.CharField(max_length=100, verbose_name="اللقب / Nom", blank=True, default="")

    prenom_ar = models.CharField(max_length=100, verbose_name="الإسم / Prénom", blank=True, default="")

    date_nais = models.DateField(verbose_name="تاريخ الميلاد / Date de naissance", null=True, blank=True)

    sex = models.CharField(max_length=50, verbose_name="الجنس / Sexe", choices=Sexe.choices, blank=True, default=Sexe.M)

    sitfam = models.CharField(
        max_length=50,
        verbose_name="الحالة العائلية / Situation familiale",
        choices=SitFam.choices,
        blank=True,
        default=SitFam.CELIBATAIRE,
    )

    # ══════════════════════════════════════════════════════════
    # INFORMATIONS ADMINISTRATIVES / ADMINISTRATIVE INFO
    # ══════════════════════════════════════════════════════════

    matricule = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="رقم التسجيل / Matricule", help_text="Ex: ENS2024001"
    )

    codeIns = models.CharField(max_length=20, verbose_name="كود التسجيل / Code d'inscription", blank=True, default="")

    bac_annee = models.CharField(
        max_length=4, verbose_name="سنة البكالوريا / Année du bac", blank=True, default="", help_text="Ex: 2010"
    )

    date_Recrut = models.DateField(verbose_name="تاريخ الإلتحاق بالجامعة / Date de recrutement", null=True, blank=True)

    # ══════════════════════════════════════════════════════════
    # COORDONNÉES / CONTACT INFORMATION
    # ══════════════════════════════════════════════════════════

    telmobile1 = models.CharField(max_length=50, verbose_name="الهاتف المحمول 1 / Tel mobile 1", blank=True, default="")

    telmobile2 = models.CharField(max_length=50, verbose_name="الهاتف المحمول 2 / Tel mobile 2", blank=True, default="")

    telfix = models.CharField(max_length=50, verbose_name="الهاتف الثابت / Tel fixe", blank=True, default="")

    fax = models.CharField(max_length=50, verbose_name="الفاكس / Fax", blank=True, default="")

    email_perso = models.EmailField(
        max_length=100, verbose_name="البريد الإلكتروني الشخصي / E-mail personnel", blank=True, default=""
    )

    email_prof = models.EmailField(
        max_length=100, verbose_name="البريد الإلكتروني المهني / E-mail professionnel", blank=True, default=""
    )

    adresse = models.CharField(max_length=200, verbose_name="العنوان / Adresse", blank=True, default="")

    wilaya = models.ForeignKey(
        Wilaya,
        on_delete=models.PROTECT,
        verbose_name="الولاية / Wilaya",
        null=True,
        blank=True,
        related_name="enseignants_wilaya",
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
        related_name="enseignants_diplome",
    )

    specialite_ar = models.CharField(max_length=100, verbose_name="التخصص", blank=True, default="")

    specialite_fr = models.CharField(max_length=100, verbose_name="Spécialité", blank=True, default="")

    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        verbose_name="الرتبة / Grade",
        null=True,
        blank=True,
        related_name="enseignants_grade",
        help_text="Ex: Professeur, MCA, MCB, MAA, MAB",
    )

    # ══════════════════════════════════════════════════════════
    # PLATEFORMES ACADÉMIQUES / ACADEMIC PLATFORMS
    # ══════════════════════════════════════════════════════════

    inscritProgres = models.BooleanField(verbose_name="مسجل بمنصة PROGRES / Inscrit PROGRES", default=False)

    inscritMoodle = models.BooleanField(verbose_name="مسجل بمنصة MOODLE / Inscrit MOODLE", default=False)

    inscritSNDL = models.BooleanField(verbose_name="مسجل بمنصة SNDL / Inscrit SNDL", default=False)

    # ══════════════════════════════════════════════════════════
    # RÉSEAUX SOCIAUX ET ACADÉMIQUES / SOCIAL & ACADEMIC NETWORKS
    # ══════════════════════════════════════════════════════════

    googlescholar = models.URLField(
        max_length=200, verbose_name="Google Scholar", blank=True, default="", help_text="URL du profil Google Scholar"
    )

    researchgate = models.URLField(
        max_length=200, verbose_name="Research Gate", blank=True, default="", help_text="URL du profil ResearchGate"
    )

    orcid_id = models.CharField(
        max_length=100, verbose_name="ORCID iD", blank=True, default="", help_text="Ex: 0000-0002-1234-5678"
    )

    linkedIn = models.URLField(max_length=200, verbose_name="LinkedIn", blank=True, default="")

    facebook = models.URLField(max_length=200, verbose_name="Facebook", blank=True, default="")

    x_twitter = models.URLField(max_length=200, verbose_name="X (Twitter)", blank=True, default="")

    tiktok = models.URLField(max_length=200, verbose_name="TikTok", blank=True, default="")

    telegram = models.URLField(max_length=200, verbose_name="Telegram", blank=True, default="")

    # ══════════════════════════════════════════════════════════
    # STATUT / STATUS
    # ══════════════════════════════════════════════════════════

    vacAcademique = models.BooleanField(verbose_name="عطلة أكاديمية / Vacances académiques", default=False)

    maladie = models.BooleanField(verbose_name="عطلة مرضية / Congé maladie", default=False)

    est_inscrit = models.BooleanField(default=True, verbose_name="مسجل بمنصة Inscrit sur UNIV")

    # ══════════════════════════════════════════════════════════
    # MÉTRIQUES GOOGLE SCHOLAR / GOOGLE SCHOLAR METRICS
    # ══════════════════════════════════════════════════════════

    scholar_publications_count = models.IntegerField(default=0, verbose_name="عدد المنشورات / Nombre de publications")

    scholar_citations_count = models.IntegerField(default=0, verbose_name="عدد الاستشهادات / Nombre de citations")

    scholar_h_index = models.IntegerField(default=0, verbose_name="H-index")

    scholar_i10_index = models.IntegerField(default=0, verbose_name="i10-index")

    scholar_last_update = models.DateTimeField(null=True, blank=True, verbose_name="آخر تحديث / Dernière mise à jour")

    # ══════════════════════════════════════════════════════════
    # META
    # ══════════════════════════════════════════════════════════

    class Meta:
        verbose_name = "أستاذ / Enseignant"
        verbose_name_plural = "الأساتذة / Enseignants"
        ordering = ["nom_ar", "prenom_ar"]
        indexes = [
            models.Index(fields=["matricule"]),
            models.Index(fields=["user"]),
            models.Index(fields=["grade"]),
            models.Index(fields=["wilaya"]),
        ]

    # ══════════════════════════════════════════════════════════
    # MÉTHODES / METHODS
    # ══════════════════════════════════════════════════════════

    def __str__(self):
        """Représentation string de l'enseignant."""
        nom = self.nom_ar or self.nom_fr or "Sans nom"
        prenom = self.prenom_ar or self.prenom_fr or ""
        return f"{nom} {prenom}".strip() or self.matricule or ""

    @property
    def is_feminin(self):
        """Vérifie si l'enseignant est de sexe féminin."""
        if self.sex in [self.Sexe.F, "أنثى", "F", "Femme", "femme", "female"]:
            return True
        if self.civilite in [self.Civilite.MME, self.Civilite.MLLE, "Mme", "Mlle", "السيدة", "الآنسة"]:
            return True
        return False

    @property
    def titre_enseignant_ar(self):
        """Retourne 'الأستاذة' si féminin, sinon 'الأستاذ'."""
        return "الأستاذة" if self.is_feminin else "الأستاذ"

    @property
    def initiales(self):
        """
        Retourne les deux premières lettres (en Français) du Nom et Prénom séparées par un point.
        Ex: 'D.A' (DOBBI Abdelmadjid), 'H.T' (HALILAT Tahar), 'A.M' (Atlili Mohamed).
        """
        if self.nom_fr and self.prenom_fr:
            n = self.nom_fr.strip().upper()
            p = self.prenom_fr.strip().upper()
            if n and p:
                return f"{n[0]}.{p[0]}"
        if self.user and self.user.last_name and self.user.first_name:
            n = self.user.last_name.strip().upper()
            p = self.user.first_name.strip().upper()
            if n and p:
                return f"{n[0]}.{p[0]}"
        if self.nom_fr:
            parts = self.nom_fr.strip().split()
            if len(parts) >= 2:
                return f"{parts[0][0].upper()}.{parts[1][0].upper()}"
            elif parts and len(parts[0]) >= 2:
                return f"{parts[0][0].upper()}.{parts[0][1].upper()}"
            elif parts:
                return f"{parts[0][0].upper()}"
        if self.nom_ar and self.prenom_ar:
            n = self.nom_ar.strip()
            p = self.prenom_ar.strip()
            if n and p:
                return f"{n[0]}.{p[0]}"
        return "E.N"

    @property
    def initiales_fr(self):
        """Retourne les initiales en français (ex: 'D.A')."""
        return self.initiales

    @property
    def avatar_palette(self):
        """Palette de couleur harmonieuse et déterministe pour l'enseignant."""
        if self.user:
            return self.user.avatar_palette
        return get_avatar_palette_for(self.id or f"{self.nom_fr} {self.prenom_fr}")

    @property
    def avatar_bg(self):
        return self.avatar_palette["bg"]

    @property
    def avatar_color(self):
        return self.avatar_palette["color"]

    @property
    def avatar_border(self):
        return self.avatar_palette["border"]

    @property
    def avatar_gradient(self):
        return self.avatar_palette["gradient"]

    @property
    def avatar_style(self):
        p = self.avatar_palette
        return f"background: {p['gradient']}; color: {p['color']};"

    def get_nom_complet(self, langue="ar"):
        """Retourne le nom complet selon la langue."""
        if langue == "ar":
            nom = self.nom_ar or self.nom_fr or ""
            prenom = self.prenom_ar or self.prenom_fr or ""
            return f"{nom} {prenom}".strip() or self.matricule or ""
        else:
            nom = self.nom_fr or self.nom_ar or ""
            prenom = self.prenom_fr or self.prenom_ar or ""
            return f"{prenom} {nom}".strip() or self.matricule or ""

    def get_specialite(self, langue="ar"):
        """Retourne la spécialité selon la langue."""
        if langue == "ar":
            return self.specialite_ar or self.specialite_fr or "-"
        return self.specialite_fr or self.specialite_ar or "-"

    @property
    def scholar_user_id(self):
        """Extrait l'ID utilisateur depuis l'URL Google Scholar."""
        if not self.googlescholar:
            return None
        import re

        match = re.search(r"user=([^&]+)", self.googlescholar)
        return match.group(1) if match else None

    def get_departement_origine(self, annee_univ=None):
        """Retourne le département d'origine (où l'enseignant est Permanent)."""
        qs = self.affectations_departement.filter(statut="Permanent", est_actif=True)
        if annee_univ:
            qs = qs.filter(annee_univ=annee_univ)
        aff = qs.select_related("departement").first()
        return aff.departement if aff else None

    def clean(self):
        """Validation des données."""
        super().clean()

        # Au moins un nom doit être renseigné
        if not self.nom_ar and not self.nom_fr:
            raise ValidationError(
                {
                    "nom_ar": "Au moins un nom (arabe ou français) doit être renseigné.",
                    "nom_fr": "Au moins un nom (arabe ou français) doit être renseigné.",
                }
            )

        # Validation de l'ORCID iD format
        if self.orcid_id:
            import re

            pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"
            if not re.match(pattern, self.orcid_id):
                raise ValidationError({"orcid_id": "Format ORCID iD invalide. Format attendu: 0000-0002-1234-5678"})
