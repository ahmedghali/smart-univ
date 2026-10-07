"""Middlewares transverses."""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
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
        if not isinstance(exception, ObjectDoesNotExist):
            return None
        logger.warning("Objet introuvable sur %s (utilisateur %s) : %s", request.path, request.user, exception)
        return page_not_found(request, Http404(str(exception)))


class MustChangePasswordMiddleware:
    """
    Redirige les utilisateurs dont doit_changer_mot_de_passe=True
    vers la page de changement de mot de passe à la connexion tant qu'il vaut vrai (A01).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "doit_changer_mot_de_passe", False):
            path = request.path
            allowed_prefixes = (
                "/authentification/logout/",
                "/etudiant/profile/change-password/",
                "/enseignant/change-password/",
                "/admin/password_change/",
                "/static/",
                "/media/",
            )
            if not any(path.startswith(prefix) for prefix in allowed_prefixes):
                from django.shortcuts import redirect

                if hasattr(user, "etudiant_profile"):
                    return redirect("etudiant:changePassword_Etud")
                elif hasattr(user, "enseignant_profile"):
                    return redirect("ense:change_password_Ens_simple")
        return self.get_response(request)
