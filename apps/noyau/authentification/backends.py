# apps/noyau/authentification/backends.py

import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend d'authentification robuste pour Smart-Univ :
    1. Authentification par nom d'utilisateur (sensible et insensible à la casse).
    2. Authentification par adresse email (insensible à la casse).
    3. Authentification par alias de rôle (ex: 'doyen' -> titulaire actif du poste).
    4. Auto-réparation de sécurité : si un mot de passe a été accidentellement enregistré
       en texte brut (via un formulaire admin sans hachage), le système valide le mot de passe
       et le convertit automatiquement en hash PBKDF2 sécurisé.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if not username or not password:
            return None

        username = str(username).strip()
        user = None

        # 1. Recherche par nom d'utilisateur exact
        user = UserModel.objects.filter(username=username).first()

        # 2. Recherche par nom d'utilisateur insensible à la casse
        if not user:
            user = UserModel.objects.filter(username__iexact=username).first()

        # 3. Recherche par email insensible à la casse
        if not user and "@" in username:
            user = UserModel.objects.filter(email__iexact=username).first()

        # 4. Recherche par alias de rôle (ex: username='doyen' ou 'chef_departement')
        if not user:
            role_aliases = {
                "doyen": ["doyen"],
                "chef_departement": ["chef_departement"],
                "chef_dep": ["chef_departement"],
            }
            poste_codes = role_aliases.get(username.lower())
            if poste_codes:
                try:
                    from apps.noyau.commun.models import AffectationPoste
                    aff = AffectationPoste.objects.filter(
                        poste__code__in=poste_codes, est_actif=True
                    ).select_related("user").first()
                    if aff and aff.user:
                        user = aff.user
                except Exception:
                    pass

        if not user:
            return None

        # Vérification standard du mot de passe
        if user.check_password(password):
            return user if self.user_can_authenticate(user) else None

        # Filet de sécurité auto-réparation : mot de passe en texte brut
        if user.password == password:
            logger.warning(
                f"[SECURITY] Mot de passe en texte brut détecté pour '{user.username}'. "
                "Hachage et mise à niveau automatique vers PBKDF2."
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            return user if self.user_can_authenticate(user) else None

        return None
