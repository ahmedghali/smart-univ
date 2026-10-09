from django.urls import path

from . import views
from .dep_admin import dep_admin_site

app_name = "departement"

urlpatterns = [
    # Admin personnalisé pour le chef de département
    path("admin/", dep_admin_site.urls),
    # Dashboard
    path("dashboard/", views.dashboard_Dep, name="dashboard_Dep"),
    path("api/dashboard-stats/", views.dashboard_stats_api, name="dashboard_stats_api"),
    # Profil
    path("profile/", views.profile_Dep, name="profile_Dep"),
    path("profile/update/", views.profileUpdate_Dep, name="profileUpdate_Dep"),
    # Enseignants
    path("enseignants/", views.list_enseignants_dep, name="list_enseignants_dep"),
    path("enseignants/<int:semestre_num>/", views.list_enseignants_dep, name="list_enseignants_dep"),
    path("enseignants/new/", views.new_Enseignant, name="new_Enseignant"),
    path("enseignants/profil/<int:ens_id>/", views.profile_enseignant_dep, name="profile_enseignant_dep"),
    path("enseignants/heures/<int:semestre>/", views.heures_enseignants_dep, name="heures_enseignants_dep"),
    path("enseignants/<int:ens_id>/timetable/", views.timetable_enseignant_dep, name="timetable_enseignant_dep"),
    path("enseignants/<int:ens_id>/timetable/<int:semestre_num>/", views.timetable_enseignant_dep, name="timetable_enseignant_dep"),
    path("enseignants/delete/<int:ens_dep_id>/", views.delete_Enseignant, name="delete_Enseignant"),
    path("enseignants/restore/<int:ens_dep_id>/", views.restore_Enseignant, name="restore_Enseignant"),
    path("enseignants/delete-acces/<int:ens_id>/", views.delete_Ens_Acces_Dep, name="delete_Ens_Acces_Dep"),
    path("enseignants/activate/<int:ens_id>/", views.activate_Ens_Acces_Dep, name="activate_Ens_Acces_Dep"),
    path("enseignants/<int:ens_id>/update-scholar/", views.update_scholar_enseignant, name="update_scholar_enseignant"),
    # Étudiants
    path("etudiants/", views.list_etudiants, name="list_etudiants"),
    path("etudiants/import/", views.import_etudiants, name="import_etudiants"),
    # Matières, Spécialités et Infrastructures (الهياكل والمقررات)
    path("matieres/", views.list_Mat_Niv, name="list_Mat_Niv"),
    path("specialites/", views.list_Specialite_Dep, name="list_Specialite_Dep"),
    path("amphis/", views.list_Amphi_Dep, name="list_Amphi_Dep"),
    path("salles/", views.list_Salle_Dep, name="list_Salle_Dep"),
    path("labos/", views.list_Labo_Dep, name="list_Labo_Dep"),
    # Emploi du temps
    path("emploi/import/", views.import_emploi, name="import_emploi"),
]
