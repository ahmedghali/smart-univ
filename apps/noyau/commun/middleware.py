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
