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
    
    photo = models.ImageField(
        upload_to='users/photos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="الصورة الشخصية"
    )

    telephone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="رقم الهاتف"
    )

    date_naissance = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ الميلاد"
    )

    # ══════════════════════════════════════════════════════════════
    # GESTION DES RÔLES/POSTES
    # ══════════════════════════════════════════════════════════════
    
    poste_principal = models.ForeignKey(
        'commun.Poste',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs_principaux',
        verbose_name="المنصب الرئيسي"
    )
    postes_secondaires = models.ManyToManyField(
        'commun.Poste',
        blank=True,
        related_name='utilisateurs_secondaires',
        verbose_name="المناصب الثانوية"
    )
    
    # ══════════════════════════════════════════════════════════════
    # PRÉFÉRENCES
    # ══════════════════════════════════════════════════════════════
    
    LANGUE_CHOICES = [
        ('ar', 'العربية'),
        ('fr', 'Français'),
    ]
    langue_preferee = models.CharField(
        max_length=2,
        choices=LANGUE_CHOICES,
        default='ar',  # Arabe par défaut
        verbose_name="اللغة المفضلة"
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
        'auth.Group',
        blank=True,
        related_name='custom_users',
        related_query_name='custom_user',
        verbose_name="المجموعات",
        help_text="المجموعات التي ينتمي إليها هذا المستخدم."
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='custom_users',
        related_query_name='custom_user',
        verbose_name="الصلاحيات",
        help_text="الصلاحيات الخاصة بهذا المستخدم."
    )

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"
        ordering = ['last_name', 'first_name']

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
    def tous_les_postes(self):
        """Retourne tous les postes (principal + secondaires)."""
        postes = list(self.postes_secondaires.all())
        if self.poste_principal:
            postes.insert(0, self.poste_principal)
        return postes
    
    def a_poste(self, code_poste):
        """Vérifie si l'utilisateur a un poste spécifique."""
        if self.poste_principal and self.poste_principal.code == code_poste:
            return True
        return self.postes_secondaires.filter(code=code_poste).exists()
    
    @property
    def est_enseignant(self):
        """Vérifie si l'utilisateur est un enseignant."""
        return hasattr(self, 'enseignant')
    
    @property
    def est_etudiant(self):
        """Vérifie si l'utilisateur est un étudiant."""
        return hasattr(self, 'etudiant')
    
    def get_profile(self):
        """Retourne le profil associé (Enseignant ou Etudiant)."""
        if hasattr(self, 'enseignant'):
            return self.enseignant
        if hasattr(self, 'etudiant'):
            return self.etudiant
        return None