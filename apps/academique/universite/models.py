# apps/academique/universite/models.py

from django.db import models

from apps.noyau.commun.models import BaseModel, Wilaya


class Universite(BaseModel):
    """
    Modèle représentant une université.
    Gère les informations de base, contacts et responsables.
    """

    # ══════════════════════════════════════════════════════════════
    # INFORMATIONS DE BASE
    # ══════════════════════════════════════════════════════════════

    code = models.CharField(
        blank=True, null=True, max_length=20, unique=True, verbose_name="الرمز / Code", help_text="Ex: USTHB, UNIV-ALG1"
    )
    nom_ar = models.CharField(max_length=200, verbose_name="الجامعة", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Université", blank=True, default="")
    sigle = models.CharField(
        max_length=50, verbose_name="الاختصار / Sigle", blank=True, default="", help_text="Ex: USTHB"
    )
    logo = models.ImageField(upload_to="universites/logos/%Y/", null=True, blank=True, verbose_name="الشعار / Logo")

    # ══════════════════════════════════════════════════════════════
    # RESPONSABLES (ForeignKey vers Enseignant - définies en string pour éviter les imports circulaires)
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # LOCALISATION
    # ══════════════════════════════════════════════════════════════

    wilaya = models.ForeignKey(
        Wilaya,
        on_delete=models.PROTECT,
        verbose_name="الولاية / Wilaya",
        null=True,
        blank=True,
        related_name="universites",
    )
    adresse = models.CharField(max_length=200, verbose_name="العنوان / Adresse", blank=True, default="")

    # ══════════════════════════════════════════════════════════════
    # CONTACTS
    # ══════════════════════════════════════════════════════════════

    telmobile = models.CharField(max_length=20, verbose_name="المحمول / Mobile", blank=True, default="")
    telfix1 = models.CharField(max_length=20, verbose_name="الهاتف 1 / Tél 1", blank=True, default="")
    telfix2 = models.CharField(max_length=20, verbose_name="الهاتف 2 / Tél 2", blank=True, default="")
    fax = models.CharField(max_length=20, verbose_name="الفاكس / Fax", blank=True, default="")
    email = models.EmailField(max_length=100, verbose_name="الإيميل / Email", blank=True, default="")
    siteweb = models.URLField(max_length=200, verbose_name="الموقع / Site Web", blank=True, default="")

    # ══════════════════════════════════════════════════════════════
    # RÉSEAUX SOCIAUX
    # ══════════════════════════════════════════════════════════════

    facebook = models.URLField(max_length=200, verbose_name="Facebook", blank=True, default="")
    x_twitter = models.URLField(max_length=200, verbose_name="X (Twitter)", blank=True, default="")
    linkedIn = models.URLField(max_length=200, verbose_name="LinkedIn", blank=True, default="")
    tiktok = models.URLField(max_length=200, verbose_name="TikTok", blank=True, default="")
    telegram = models.URLField(max_length=200, verbose_name="Telegram", blank=True, default="")

    class Meta:
        verbose_name = "جامعة / Université"
        verbose_name_plural = "الجامعات / Universités"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["wilaya"]),
        ]

    # ══════════════════════════════════════════════════════════════
    # RESPONSABLES (postes affectés via AffectationPoste)
    # ══════════════════════════════════════════════════════════════

    def titulaire(self, poste_code):
        """Enseignant qui occupe actuellement ce poste dans cet établissement, ou None."""
        affectation = (
            self.affectations_postes.filter(est_actif=True, poste__code=poste_code).select_related("user").first()
        )
        return getattr(affectation.user, "enseignant_profile", None) if affectation else None

    @property
    def recteur(self):
        return self.titulaire("recteur")

    @property
    def vice_rect_p(self):
        return self.titulaire("vice_rect_p")

    @property
    def vice_rect_pg(self):
        return self.titulaire("vice_rect_pg")

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Validation des postes des responsables."""

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class Domaine(BaseModel):
    """
    Modèle représentant un domaine d'études.
    Un domaine regroupe plusieurs filières.
    """

    code = models.CharField(blank=True, null=True, max_length=20, verbose_name="الرمز / Code", help_text="Ex: ST, SNV")
    nom_ar = models.CharField(max_length=200, verbose_name="الميدان", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Domaine", blank=True, default="")
    universite = models.ForeignKey(
        Universite, on_delete=models.CASCADE, verbose_name="الجامعة / Université", related_name="domaines"
    )

    class Meta:
        verbose_name = "ميدان / Domaine"
        verbose_name_plural = "الميادين / Domaines"
        ordering = ["universite", "code"]
        unique_together = ["code", "universite"]
        indexes = [
            models.Index(fields=["universite", "code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Domaine {self.code}"

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code
