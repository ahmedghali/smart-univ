"""Routes racine du projet."""

from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

admin.site.site_header = "Administration Smart-Univ"
admin.site.site_title = "Smart-Univ Admin"
admin.site.index_title = "Panneau d'administration"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Icône d'onglet demandée par défaut par les navigateurs
    path("favicon.ico", RedirectView.as_view(url=static("images/smart-univ-logo.svg"), permanent=False)),
    path("", include("apps.noyau.commun.urls", namespace="comm")),
    path("", include("apps.noyau.authentification.urls", namespace="auth")),
    path("universite/", include("apps.academique.universite.urls", namespace="univ")),
    path("faculte/", include("apps.academique.faculte.urls", namespace="facu")),
    path("departement/", include("apps.academique.departement.urls", namespace="depa")),
    path("enseignant/", include("apps.academique.enseignant.urls", namespace="ense")),
    path("etudiant/", include("apps.academique.etudiant.urls", namespace="etud")),
    # Fichiers envoyés par les utilisateurs (logos) : peu nombreux, servis par Django
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
