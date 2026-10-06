# apps/academique/universite/models.py

from django.db import models
from django.core.exceptions import ValidationError
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
        max_length=20,
        unique=True,
        verbose_name="الرمز / Code",
        help_text="Ex: USTHB, UNIV-ALG1"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الجامعة",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Université",
        blank=True,
        default=""
    )
    sigle = models.CharField(
        max_length=50,
        verbose_name="الاختصار / Sigle",
        blank=True,
        default="",
        help_text="Ex: USTHB"
    )
    logo = models.ImageField(
        upload_to='universites/logos/%Y/',
        null=True,
        blank=True,
        verbose_name="الشعار / Logo"
    )

    # ══════════════════════════════════════════════════════════════
    # RESPONSABLES (ForeignKey vers Enseignant - définies en string pour éviter les imports circulaires)
    # ══════════════════════════════════════════════════════════════

    recteur = models.ForeignKey(
        'enseignant.Enseignant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='universite_as_recteur',
        verbose_name="المدير / Recteur"
    )
    vice_rect_p = models.ForeignKey(
        'enseignant.Enseignant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='universite_as_vice_rect_p',
        verbose_name="نائب المدير للبيداغوجيا / Vice-Recteur Pédagogique"
    )
    vice_rect_pg = models.ForeignKey(
        'enseignant.Enseignant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='universite_as_vice_rect_pg',
        verbose_name="نائب المدير للدراسات العليا / Vice-Recteur PG"
    )

    # ══════════════════════════════════════════════════════════════
    # LOCALISATION
    # ══════════════════════════════════════════════════════════════

    wilaya = models.ForeignKey(
        Wilaya,
        on_delete=models.PROTECT,
        verbose_name="الولاية / Wilaya",
        null=True,
        blank=True,
        related_name='universites'
    )
    adresse = models.CharField(
        max_length=200,
        verbose_name="العنوان / Adresse",
        blank=True,
        default=""
    )

    # ══════════════════════════════════════════════════════════════
    # CONTACTS
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

    class Meta:
        verbose_name = "جامعة"
        verbose_name_plural = "الجامعات"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['wilaya']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Validation des postes des responsables."""
        # Validation pour le recteur
        if self.recteur and hasattr(self.recteur, 'user') and self.recteur.user.poste_principal:
            if self.recteur.user.poste_principal.code != 'recteur':
                raise ValidationError({
                    'recteur': "المدير يجب أن يكون له منصب 'مدير' / Le recteur doit avoir le poste 'Recteur'."
                })

        # Validation pour le vice-recteur pédagogique
        if self.vice_rect_p and hasattr(self.vice_rect_p, 'user') and self.vice_rect_p.user.poste_principal:
            if self.vice_rect_p.user.poste_principal.code != 'vice_rect_p':
                raise ValidationError({
                    'vice_rect_p': "نائب المدير للبيداغوجيا يجب أن يكون له المنصب المناسب / Le vice-recteur pédagogique doit avoir le poste approprié."
                })

        # Validation pour le vice-recteur post-graduation
        if self.vice_rect_pg and hasattr(self.vice_rect_pg, 'user') and self.vice_rect_pg.user.poste_principal:
            if self.vice_rect_pg.user.poste_principal.code != 'vice_rect_pg':
                raise ValidationError({
                    'vice_rect_pg': "نائب المدير للدراسات العليا يجب أن يكون له المنصب المناسب / Le vice-recteur PG doit avoir le poste approprié."
                })

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class Domaine(BaseModel):
    """
    Modèle représentant un domaine d'études.
    Un domaine regroupe plusieurs filières.
    """

    code = models.CharField(
        max_length=20,
        verbose_name="الرمز / Code",
        help_text="Ex: ST, SNV"
    )
    nom_ar = models.CharField(
        max_length=200,
        verbose_name="الميدان",
        blank=True,
        default=""
    )
    nom_fr = models.CharField(
        max_length=200,
        verbose_name="Domaine",
        blank=True,
        default=""
    )
    universite = models.ForeignKey(
        Universite,
        on_delete=models.CASCADE,
        verbose_name="الجامعة / Université",
        related_name='domaines'
    )

    class Meta:
        verbose_name = "ميدان"
        verbose_name_plural = "الميادين"
        ordering = ['universite', 'code']
        unique_together = ['code', 'universite']
        indexes = [
            models.Index(fields=['universite', 'code']),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Domaine {self.code}"

    def get_nom(self, langue='ar'):
        """Retourne le nom selon la langue."""
        if langue == 'ar':
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code
