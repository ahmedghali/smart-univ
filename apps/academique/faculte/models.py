# apps/academique/faculte/models.py

from django.db import models

from apps.academique.universite.models import Domaine, Universite
from apps.noyau.commun.models import BaseModel


class Faculte(BaseModel):
    """
    Modèle représentant une faculté universitaire.
    Une faculté regroupe plusieurs départements et est rattachée à une université.
    """

    # ══════════════════════════════════════════════════════════════
    # INFORMATIONS DE BASE
    # ══════════════════════════════════════════════════════════════

    code = models.CharField(
        blank=True, null=True, max_length=20, unique=True, verbose_name="الرمز / Code", help_text="Ex: FSI, FSNV"
    )
    nom_ar = models.CharField(max_length=200, verbose_name="الكلية / Faculté", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Faculté", blank=True, default="")
    sigle = models.CharField(
        max_length=50, verbose_name="الاختصار / Sigle", blank=True, default="", help_text="Ex: FSI, FSNV"
    )
    logo = models.ImageField(upload_to="facultes/logos/%Y/", null=True, blank=True, verbose_name="الشعار / Logo")
    universite = models.ForeignKey(
        Universite, on_delete=models.PROTECT, verbose_name="الجامعة / Université", related_name="facultes"
    )

    # ══════════════════════════════════════════════════════════════
    # RESPONSABLES
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # COORDONNÉES
    # ══════════════════════════════════════════════════════════════

    adresse = models.CharField(max_length=200, verbose_name="العنوان / Adresse", blank=True, default="")
    telmobile = models.CharField(max_length=20, verbose_name="المحمول / Mobile", blank=True, default="")
    telfix1 = models.CharField(max_length=20, verbose_name="الهاتف 1 / Tél 1", blank=True, default="")
    telfix2 = models.CharField(max_length=20, verbose_name="الهاتف 2 / Tél 2", blank=True, default="")
    tel3chiffre = models.CharField(
        max_length=10,
        verbose_name="رقم داخلي / Tél 3 chiffres",
        blank=True,
        default="",
        help_text="Numéro interne à 3 chiffres",
    )
    fax = models.CharField(max_length=20, verbose_name="الفاكس / Fax", blank=True, default="")
    email = models.EmailField(max_length=100, verbose_name="الإيميل / Email", blank=True, default="")
    siteweb = models.URLField(max_length=200, verbose_name="الموقع / Site Web", blank=True, default="")

    # ══════════════════════════════════════════════════════════════
    # RÉSEAUX SOCIAUX
    # ══════════════════════════════════════════════════════════════

    facebook = models.URLField(max_length=200, verbose_name="Facebook", blank=True, default="")
    x_twitter = models.URLField(max_length=200, verbose_name="X (Twitter)", blank=True, default="")
    linkedIn = models.URLField(max_length=200, verbose_name="LinkedIn", blank=True, default="")
    tikTok = models.URLField(max_length=200, verbose_name="TikTok", blank=True, default="")
    telegram = models.URLField(max_length=200, verbose_name="Telegram", blank=True, default="")

    # ══════════════════════════════════════════════════════════════
    # STATUT
    # ══════════════════════════════════════════════════════════════

    class Meta:
        verbose_name = "كلية / Faculté"
        verbose_name_plural = "كليات / Facultés"
        ordering = ["universite", "code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["universite", "code"]),
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
    def doyen(self):
        return self.titulaire("doyen")

    @property
    def vice_doyen_p(self):
        return self.titulaire("vice_doyen_p")

    @property
    def vice_doyen_pg(self):
        return self.titulaire("vice_doyen_pg")

    @property
    def nom_complet_ar(self):
        """
        Retourne le nom complet en arabe avec le préfixe 'كلية' si non présent.
        Exemple: 'كلية المحروقات والطاقات المتجددة وعلوم الأرض والكون'.
        """
        if not self.nom_ar:
            return ""
        clean_name = self.nom_ar.strip()
        if clean_name.startswith("كلية"):
            return clean_name
        return f"كلية {clean_name}"

    def __str__(self):
        return self.nom_ar or self.nom_fr or self.code

    def clean(self):
        """Validation des responsables."""

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code


class Filiere(BaseModel):
    """
    Modèle représentant une filière d'études.
    Une filière appartient à un domaine et regroupe plusieurs spécialités.
    """

    code = models.CharField(blank=True, null=True, max_length=20, verbose_name="الرمز / Code", help_text="Ex: MI, INFO")
    nom_ar = models.CharField(max_length=200, verbose_name="الشعبة / Filière", blank=True, default="")
    nom_fr = models.CharField(max_length=200, verbose_name="Filière", blank=True, default="")
    domaine = models.ForeignKey(
        Domaine, on_delete=models.PROTECT, verbose_name="الميدان / Domaine", related_name="filieres"
    )

    class Meta:
        verbose_name = "شعبة / Filière"
        verbose_name_plural = "شعب / Filières"
        ordering = ["domaine", "code"]
        unique_together = ["code", "domaine"]
        indexes = [
            models.Index(fields=["domaine", "code"]),
        ]

    def __str__(self):
        return self.nom_ar or self.nom_fr or f"Filière {self.code}"

    def get_nom(self, langue="ar"):
        """Retourne le nom selon la langue."""
        if langue == "ar":
            return self.nom_ar or self.nom_fr or self.code
        return self.nom_fr or self.nom_ar or self.code
