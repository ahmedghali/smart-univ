# apps/academique/faculte/urls.py

from django.urls import path

from . import views
from .fac_admin import fac_admin_site

app_name = "faculte"

urlpatterns = [
    # Administration Doyen
    path("admin/", fac_admin_site.urls),
    # Tableau de bord de la faculté
    path("dashboard/", views.dashboard_Fac, name="dashboard_Fac"),
    # Profil de la faculté
    path("profile/", views.profile_Fac, name="profile_Fac"),
    path("profile/<int:faculte_id>/", views.profile_Fac, name="profile_Fac_by_id"),
    path("profile/update/", views.profileUpdate_Fac, name="profileUpdate_Fac"),
    path("profile/update/<int:faculte_id>/", views.profileUpdate_Fac, name="profileUpdate_Fac_by_id"),
    # Changement de mot de passe du doyen
    path("password/", views.change_password_Fac, name="change_password_Fac"),
    # Départements de la faculté
    path("departements/", views.list_departements_fac, name="list_departements_fac"),
    # Enseignants de la faculté
    path("enseignants/", views.list_enseignants_fac, name="list_enseignants_fac"),
    path("enseignants/<int:semestre_num>/", views.list_enseignants_fac, name="list_enseignants_fac"),
    path("enseignants/heures/<int:semestre>/", views.heures_enseignants_fac, name="heures_enseignants_fac"),
    # Étudiants de la faculté
    path("etudiants/", views.list_etudiants_fac, name="list_etudiants_fac"),
    path("etudiants/import/", views.import_etudiants_fac, name="import_etudiants_fac"),
    # الهياكل والمقررات (Faculté / Doyen)
    path("specialites/", views.list_Specialite_Fac, name="list_Specialite_Fac"),
    path("matieres/", views.list_Mat_Fac, name="list_Mat_Fac"),
    path("infrastructures/", views.infrastructures_Fac, name="infrastructures_Fac"),
    path("amphis/", views.list_Amphi_Fac, name="list_Amphi_Fac"),
    path("salles/", views.list_Salle_Fac, name="list_Salle_Fac"),
    path("labos/", views.list_Labo_Fac, name="list_Labo_Fac"),
]

