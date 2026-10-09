# apps/academique/enseignant/urls.py

from django.urls import path

from .views import (
    absences,
    api,
    classes,
    consultation,
    dashboard,
    emploi_temps,
    fiche_pedagogique,
    notes,
    profil,
    seances,
)

app_name = "enseignant"

urlpatterns = [
    # ══════════════════════════════════════════════════════════════
    # DASHBOARD (Mode propre sans ID dans l'URL + compatibilité)
    # ══════════════════════════════════════════════════════════════
    path("dashboard/", dashboard.dashboard_Ens, name="dashboard_Ens_clean"),
    path("<int:dep_id>/dashboard/", dashboard.dashboard_Ens, name="dashboard_Ens"),
    path("switch-department/<int:dep_id>/", dashboard.switch_department_ens, name="switch_department_ens"),
    # ══════════════════════════════════════════════════════════════
    # PROFIL
    # ══════════════════════════════════════════════════════════════
    path("profile/", profil.profile_Ens, name="profile_Ens"),
    path("profile/<int:enseignant_id>/", profil.profile_Ens, name="profile_Ens_id"),
    path("profile/update/", profil.profileUpdate_Ens, name="profileUpdate_Ens"),
    path("profile/update/<int:enseignant_id>/", profil.profileUpdate_Ens, name="profileUpdate_Ens_id"),
    path("profileUpdate/<int:enseignant_id>/", profil.profileUpdate_Ens, name="profileUpdate_legacy_id"),
    path("profileUpdate/", profil.profileUpdate_Ens, name="profileUpdate_legacy"),
    path("profile/update-scholar/", profil.update_scholar_ens, name="update_scholar_my_profile"),
    path("profile/<int:enseignant_id>/update-scholar/", profil.update_scholar_ens, name="update_scholar_ens"),
    path("change-password/", profil.change_password_Ens, name="change_password_Ens_simple"),
    # ══════════════════════════════════════════════════════════════
    # LISTE ET DÉTAILS
    # ══════════════════════════════════════════════════════════════
    path("list/", consultation.list_Ens, name="list_Ens"),
    path("detail/<int:enseignant_id>/", consultation.detail_Ens, name="detail_Ens"),
    # ══════════════════════════════════════════════════════════════
    # EMPLOI DU TEMPS
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/timetable/", emploi_temps.timeTable_Ens, name="timeTable_Ens"),
    path(
        "<int:dep_id>/classe/<int:classe_id>/update-moodle/", classes.update_classe_moodle, name="update_classe_moodle"
    ),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES ENSEIGNANTS DU DÉPARTEMENT
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/enseignants/", consultation.list_enseignants_ens, name="list_enseignants_ens"),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES ÉTUDIANTS DU DÉPARTEMENT
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/etudiants/", consultation.list_Etudiant_Ens, name="list_etudiants_ens"),
    path("<int:dep_id>/ajax/etudiants/", api.etudiants_json_ens, name="etudiants_json_ens"),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES MATIÈRES
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/matieres/", consultation.list_Mat_Niv_Ens, name="list_matieres_ens"),
    path("<int:dep_id>/ajax/matieres/", api.matieres_json_ens, name="matieres_json_ens"),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES SPÉCIALITÉS
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/specialites/", consultation.list_Specialite_Ens, name="list_specialites_ens"),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES AMPHITHÉÂTRES
    # ══════════════════════════════════════════════════════════════
    path("amphi/list/<int:dep_id>/", emploi_temps.list_Amphi_Ens, name="list_Amphi_Ens"),
    path(
        "amphi/timetable/<int:dep_id>/<int:amphi_dep_id>/<int:semestre_numero>/",
        emploi_temps.timeTable_Amphi_Ens,
        name="timeTable_Amphi_Ens",
    ),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES SALLES
    # ══════════════════════════════════════════════════════════════
    path("salle/list/<int:dep_id>/", emploi_temps.list_Salle_Ens, name="list_Salle_Ens"),
    path(
        "salle/timetable/<int:dep_id>/<int:salle_dep_id>/<int:semestre_numero>/",
        emploi_temps.timeTable_Salle_Ens,
        name="timeTable_Salle_Ens",
    ),
    # ══════════════════════════════════════════════════════════════
    # LISTE DES LABORATOIRES
    # ══════════════════════════════════════════════════════════════
    path("labo/list/<int:dep_id>/", emploi_temps.list_Labo_Ens, name="list_Labo_Ens"),
    path(
        "labo/timetable/<int:dep_id>/<int:labo_dep_id>/<int:semestre_numero>/",
        emploi_temps.timeTable_Labo_Ens,
        name="timeTable_Labo_Ens",
    ),
    # ══════════════════════════════════════════════════════════════
    # FICHE PÉDAGOGIQUE
    # ══════════════════════════════════════════════════════════════
    path("fichPeda_Ens_Semestre/<int:dep_id>/", fiche_pedagogique.fichPeda_Ens_Semestre, name="fichPeda_Ens_Semestre"),
    path("fichePedagogique/<int:dep_id>/", fiche_pedagogique.fichePedagogique, name="fichePedagogique"),
    # ══════════════════════════════════════════════════════════════
    # NIVEAUX ENSEIGNÉS
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/niveaux-enseigner/", classes.niveaux_enseigner, name="niveaux_enseigner"),
    path("<int:dep_id>/niveaux/", consultation.list_NivSpeDep_Ens, name="list_NivSpeDep_Ens"),
    path(
        "<int:dep_id>/niveaux/<int:niv_spe_dep_id>/timetable/<int:semestre_num>/",
        emploi_temps.timeTable_Niv_Ens,
        name="timeTable_Niv_Ens",
    ),
    # ══════════════════════════════════════════════════════════════
    # GESTION DES SOUS-GROUPES
    # ══════════════════════════════════════════════════════════════
    path(
        "<int:dep_id>/sous-groupes/nombre/<int:classe_id>/",
        classes.page_nombre_sous_groupes,
        name="page_nombre_sous_groupes",
    ),
    path(
        "<int:dep_id>/sous-groupes/affecter/<int:classe_id>/",
        classes.affecter_etudiants_sous_groupes,
        name="affecter_etudiants_sous_groupes",
    ),
    path(
        "<int:dep_id>/sous-groupes/liste/<int:niv_spe_dep_sg_id>/",
        classes.liste_sous_groupes,
        name="liste_sous_groupes",
    ),
    path(
        "<int:dep_id>/sous-groupes/affecter-direct/<int:niv_spe_dep_sg_id>/",
        classes.affecter_direct_sous_groupes,
        name="affecter_direct_sous_groupes",
    ),
    # ══════════════════════════════════════════════════════════════
    # PROFIL ENSEIGNANT
    # ══════════════════════════════════════════════════════════════
    path("profile/<int:dep_id>/", profil.profile_ens_dep, name="profile_ens_dep"),
    path("profileUpdate/<int:dep_id>/", profil.profileUpdate_ens_dep, name="profileUpdate_ens_dep"),
    path("change-password/<int:dep_id>/", profil.change_password_ens_dep, name="change_password_Ens"),
    # ══════════════════════════════════════════════════════════════
    # GESTION DES SÉANCES
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/classe/<int:clas_id>/seances/", seances.list_Sea_Ens, name="list_Sea_Ens"),
    path("<int:dep_id>/classe/<int:clas_id>/seances/new/", seances.new_Seance_Ens, name="new_Seance_Ens"),
    path("<int:dep_id>/seance/<int:sea_id>/update/", seances.update_seance, name="update_seance"),
    path("<int:dep_id>/seance/<int:sea_id>/delete/", seances.delete_seance, name="delete_seance"),
    # ══════════════════════════════════════════════════════════════
    # GESTION DES ABSENCES
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/seance/<int:sea_id>/absences/", absences.list_Abs_Etu, name="list_Abs_Etu"),
    path("<int:dep_id>/classe/<int:clas_id>/absences/", absences.list_Abs_Etu_Classe, name="list_Abs_Etu_Classe"),
    # ══════════════════════════════════════════════════════════════
    # GESTION DES NOTES
    # ══════════════════════════════════════════════════════════════
    path("<int:dep_id>/classe/<int:clas_id>/notes/", notes.list_Notes_Etu_Classe, name="list_Notes_Etu_Classe"),
    path("<int:dep_id>/classe/<int:clas_id>/notes/valider/", notes.valider_notes_classe, name="valider_notes_classe"),
    path("<int:dep_id>/classe/<int:clas_id>/notes/creer/", notes.creer_notes_classe, name="creer_notes_classe"),
]
