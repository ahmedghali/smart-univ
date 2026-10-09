# apps/noyau/authentification/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé pour Smart-Univ.
    Hérite de AbstractUser pour garder username, email, password, etc.
    """

    # ══════════════════════════════════════════════════════════════
    # INFORMATIONS DE PROFIL
    # ══════════════════════════════════════════════════════════════

    photo = models.ImageField(upload_to="users/photos/%Y/%m/", blank=True, null=True, verbose_name="الصورة الشخصية")

    telephone = models.CharField(max_length=20, blank=True, default="", verbose_name="رقم الهاتف")

    date_naissance = models.DateField(blank=True, null=True, verbose_name="تاريخ الميلاد")

    # ══════════════════════════════════════════════════════════════
    # GESTION DES RÔLES/POSTES
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # PRÉFÉRENCES
    # ══════════════════════════════════════════════════════════════

    LANGUE_CHOICES = [
        ("ar", "العربية"),
        ("fr", "Français"),
    ]
    langue_preferee = models.CharField(
        max_length=2,
        choices=LANGUE_CHOICES,
        default="ar",  # Arabe par défaut
        verbose_name="اللغة المفضلة",
    )

    doit_changer_mot_de_passe = models.BooleanField(
        default=False,
        verbose_name="يجب تغيير كلمة المرور / Doit changer le mot de passe",
        help_text="Si coché, l'utilisateur doit renouveler son mot de passe dès sa prochaine connexion.",
    )

    # ══════════════════════════════════════════════════════════════
    # AUDIT
    # ══════════════════════════════════════════════════════════════

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")

    # ══════════════════════════════════════════════════════════════
    # Résolution des conflits related_name
    # ══════════════════════════════════════════════════════════════

    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="custom_users",
        related_query_name="custom_user",
        verbose_name="المجموعات",
        help_text="المجموعات التي ينتمي إليها هذا المستخدم.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="custom_users",
        related_query_name="custom_user",
        verbose_name="الصلاحيات",
        help_text="الصلاحيات الخاصة بهذا المستخدم.",
    )

    class Meta:
        verbose_name = "مستخدم / Utilisateur"
        verbose_name_plural = "المستخدمون / Utilisateurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.username

    # ══════════════════════════════════════════════════════════════
    # MÉTHODES UTILES
    # ══════════════════════════════════════════════════════════════

    @property
    def nom_complet(self):
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.last_name} {self.first_name}".strip() or self.username

    @property
    def is_feminin(self):
        """Vérifie si l'utilisateur est de sexe féminin via son profil lié (enseignant ou étudiant)."""
        ens = getattr(self, "enseignant_profile", None)
        if ens and getattr(ens, "is_feminin", False):
            return True
        etu = getattr(self, "etudiant_profile", None)
        if etu and getattr(etu, "is_feminin", False):
            return True
        return False

    @property
    def tous_les_postes(self):
        """Postes occupés actuellement (affectations actives), du plus élevé au plus bas."""
        return [a.poste for a in self.affectations_postes.filter(est_actif=True).select_related("poste")]

    def a_poste(self, code_poste):
        """Vérifie si l'utilisateur occupe actuellement un poste donné."""
        return self.affectations_postes.filter(est_actif=True, poste__code=code_poste).exists()

    @property
    def est_enseignant(self):
        """Vérifie si l'utilisateur a un profil enseignant."""
        return hasattr(self, "enseignant_profile")

    @property
    def est_etudiant(self):
        """Vérifie si l'utilisateur a un profil étudiant."""
        return hasattr(self, "etudiant_profile")

    # ══════════════════════════════════════════════════════════════
    # GESTION DE L'AVATAR ET COULEURS ALÉATOIRES / DÉTERMINISTES
    # ══════════════════════════════════════════════════════════════

    @property
    def avatar_initiales(self):
        """
        Retourne les deux premières lettres (en Français) du Nom et Prénom séparées par un point.
        Ex: 'G.A', 'B.M', 'D.A', 'H.T'.
        Fonctionne pour tout utilisateur (enseignant, étudiant, administratif, doyen, etc.).
        """
        # 1. Si lié à un profil enseignant existant
        ens = getattr(self, "enseignant_profile", None)
        if ens and hasattr(ens, "initiales") and ens.initiales:
            return ens.initiales

        # 2. Si lié à un profil étudiant existant
        etu = getattr(self, "etudiant_profile", None)
        if etu:
            if getattr(etu, "nom_fr", "") and getattr(etu, "prenom_fr", ""):
                n = etu.nom_fr.strip().upper()
                p = etu.prenom_fr.strip().upper()
                if n and p:
                    return f"{n[0]}.{p[0]}"

        # 3. Via last_name et first_name du compte
        ln = (self.last_name or "").strip()
        fn = (self.first_name or "").strip()
        if ln and fn:
            return f"{ln[0].upper()}.{fn[0].upper()}"

        # 4. Via username (ex: ghali.ahmed, ahmed_ghali, etc.)
        un = (self.username or "").strip()
        for sep in [".", "_", "-"]:
            if sep in un:
                parts = [p for p in un.split(sep) if p]
                if len(parts) >= 2:
                    return f"{parts[0][0].upper()}.{parts[1][0].upper()}"

        if len(un) >= 2:
            return f"{un[0].upper()}.{un[1].upper()}"
        elif len(un) == 1:
            return f"{un[0].upper()}.U"
        return "U.S"

    @property
    def initiales(self):
        """Alias pour compatibilité templates."""
        return self.avatar_initiales

    @property
    def avatar_palette(self):
        """Palette de couleur attribuée de façon déterministe / pseudo-aléatoire."""
        return get_avatar_palette_for(self.id or self.username)

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
        """Style CSS prêt à l'emploi avec dégradé moderne et couleur de texte."""
        p = self.avatar_palette
        return f"background: {p['gradient']}; color: {p['color']};"


# ══════════════════════════════════════════════════════════════
# PALETTE DE COULEURS HARMONIEUSES ET MODERNES POUR LES AVATARS
# ══════════════════════════════════════════════════════════════

AVATAR_PALETTES = [
    {"bg": "#2563eb", "color": "#ffffff", "border": "#1d4ed8", "gradient": "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)"},  # Royal Blue
    {"bg": "#7c3aed", "color": "#ffffff", "border": "#6d28d9", "gradient": "linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)"},  # Purple
    {"bg": "#059669", "color": "#ffffff", "border": "#047857", "gradient": "linear-gradient(135deg, #059669 0%, #047857 100%)"},  # Emerald
    {"bg": "#d97706", "color": "#ffffff", "border": "#b45309", "gradient": "linear-gradient(135deg, #d97706 0%, #b45309 100%)"},  # Amber
    {"bg": "#dc2626", "color": "#ffffff", "border": "#b91c1c", "gradient": "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)"},  # Crimson
    {"bg": "#0891b2", "color": "#ffffff", "border": "#0e7490", "gradient": "linear-gradient(135deg, #0891b2 0%, #0e7490 100%)"},  # Cyan
    {"bg": "#4f46e5", "color": "#ffffff", "border": "#4338ca", "gradient": "linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)"},  # Indigo
    {"bg": "#0d9488", "color": "#ffffff", "border": "#0f766e", "gradient": "linear-gradient(135deg, #0d9488 0%, #0f766e 100%)"},  # Teal
    {"bg": "#e11d48", "color": "#ffffff", "border": "#be123c", "gradient": "linear-gradient(135deg, #e11d48 0%, #be123c 100%)"},  # Rose
    {"bg": "#c026d3", "color": "#ffffff", "border": "#a21caf", "gradient": "linear-gradient(135deg, #c026d3 0%, #a21caf 100%)"},  # Fuchsia
    {"bg": "#ea580c", "color": "#ffffff", "border": "#c2410c", "gradient": "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)"},  # Orange
    {"bg": "#16a34a", "color": "#ffffff", "border": "#15803d", "gradient": "linear-gradient(135deg, #16a34a 0%, #15803d 100%)"},  # Green
    {"bg": "#475569", "color": "#ffffff", "border": "#334155", "gradient": "linear-gradient(135deg, #475569 0%, #334155 100%)"},  # Slate
    {"bg": "#9333ea", "color": "#ffffff", "border": "#7e22ce", "gradient": "linear-gradient(135deg, #9333ea 0%, #7e22ce 100%)"},  # Violet
    {"bg": "#0284c7", "color": "#ffffff", "border": "#0369a1", "gradient": "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)"},  # Sky
    {"bg": "#db2777", "color": "#ffffff", "border": "#be185d", "gradient": "linear-gradient(135deg, #db2777 0%, #be185d 100%)"},  # Pink
]


def get_avatar_palette_for(seed_val):
    """
    Calcule une couleur et un dégradé déterministes et variés basés sur un identifiant
    (user ID, nom, matricule ou texte). Garantit la persistance visuelle sans clignotement.
    """
    if not seed_val:
        return AVATAR_PALETTES[0]
    if isinstance(seed_val, int):
        num = seed_val * 7
    else:
        seed_str = str(seed_val)
        num = sum((i + 1) * ord(c) for i, c in enumerate(seed_str))
    idx = num % len(AVATAR_PALETTES)
    return AVATAR_PALETTES[idx]

