"""Middlewares transverses."""

import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.defaults import page_not_found

logger = logging.getLogger(__name__)


class ObjectDoesNotExistMiddleware:
    """Renvoie une 404 au lieu d'une erreur 500 quand un objet ou un profil attendu n'existe pas.

    Cas typique : un utilisateur sans profil enseignant qui ouvre une page de département
    (`request.user.enseignant_profile` lève RelatedObjectDoesNotExist).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # A29 : ne convertit en 404 que RelatedObjectDoesNotExist sur enseignant_profile / etudiant_profile.
        # Les autres DoesNotExist remontent normalement (500 et log).
        exc_type = type(exception).__name__
        exc_msg = str(exception).lower()
        if exc_type == "RelatedObjectDoesNotExist" and (
            "enseignant_profile" in exc_msg or "etudiant_profile" in exc_msg
        ):
            logger.warning("Profil manquant sur %s (utilisateur %s) : %s", request.path, request.user, exception)
            return page_not_found(request, Http404(str(exception)))
        return None


class MustChangePasswordMiddleware:
    """Redirige les utilisateurs dont doit_changer_mot_de_passe=True

    vers la page de changement de mot de passe à la connexion tant qu'il vaut vrai (A01, R2).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "doit_changer_mot_de_passe", False):
            path = request.path
            allowed_exact = set()
            allowed_prefixes = []

            for route_name in (
                "auth:logout",
                "etud:changePassword_Etud",
                "ense:change_password_Ens_simple",
                "admin:password_change",
            ):
                try:
                    url = reverse(route_name)
                    allowed_exact.add(url)
                    if route_name == "ense:change_password_Ens_simple":
                        allowed_prefixes.append(url)
                except Exception:
                    pass

            if getattr(settings, "STATIC_URL", None):
                allowed_prefixes.append(settings.STATIC_URL)
            if getattr(settings, "MEDIA_URL", None):
                allowed_prefixes.append(settings.MEDIA_URL)

            if path in allowed_exact or any(path.startswith(prefix) for prefix in allowed_prefixes):
                return self.get_response(request)

            if hasattr(user, "etudiant_profile"):
                return redirect("etud:changePassword_Etud")
            elif hasattr(user, "enseignant_profile"):
                return redirect("ense:change_password_Ens_simple")
            else:
                try:
                    return redirect("admin:password_change")
                except Exception:
                    pass

        return self.get_response(request)
