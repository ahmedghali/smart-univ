"""Routes racine du projet."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.noyau.commun.urls", namespace="comm")),
    path("", include("apps.noyau.authentification.urls", namespace="auth")),
    path("universite/", include("apps.academique.universite.urls", namespace="univ")),
    path("faculte/", include("apps.academique.faculte.urls", namespace="facu")),
    path("departement/", include("apps.academique.departement.urls", namespace="depa")),
    path("enseignant/", include("apps.academique.enseignant.urls", namespace="ense")),
    path("etudiant/", include("apps.academique.etudiant.urls", namespace="etud")),
    path("affectation/", include("apps.academique.affectation.urls", namespace="affe")),
    # Fichiers envoyés par les utilisateurs (logos) : peu nombreux, servis par Django
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
