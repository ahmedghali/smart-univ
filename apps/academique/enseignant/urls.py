# apps/academique/enseignant/urls.py

from django.urls import path
from . import views

app_name = 'enseignant'

urlpatterns = [
    # ══════════════════════════════════════════════════════════════
    # DASHBOARD (avec dep_id pour le décorateur enseignant_access_required)
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/dashboard/', views.dashboard_Ens, name='dashboard_Ens'),

    # ══════════════════════════════════════════════════════════════
    # PROFIL
    # ══════════════════════════════════════════════════════════════
    path('profile/', views.profile_Ens, name='profile_Ens'),
    path('profile/<int:enseignant_id>/', views.profile_Ens, name='profile_Ens_id'),
    path('profile/update/', views.profileUpdate_Ens, name='profileUpdate_Ens'),
    path('change-password/', views.change_password_Ens, name='change_password_Ens_simple'),

    # ══════════════════════════════════════════════════════════════
    # LISTE ET DÉTAILS
    # ══════════════════════════════════════════════════════════════
    path('list/', views.list_Ens, name='list_Ens'),
    path('detail/<int:enseignant_id>/', views.detail_Ens, name='detail_Ens'),

    # ══════════════════════════════════════════════════════════════
    # EMPLOI DU TEMPS
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/timetable/', views.timeTable_Ens, name='timeTable_Ens'),
    path('<int:dep_id>/classe/<int:classe_id>/update-moodle/', views.update_classe_moodle, name='update_classe_moodle'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES ENSEIGNANTS DU DÉPARTEMENT
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/enseignants/', views.list_enseignants_ens, name='list_enseignants_ens'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES ÉTUDIANTS DU DÉPARTEMENT
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/etudiants/', views.list_Etudiant_Ens, name='list_etudiants_ens'),
    path('<int:dep_id>/ajax/etudiants/', views.etudiants_json_ens, name='etudiants_json_ens'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES MATIÈRES
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/matieres/', views.list_Mat_Niv_Ens, name='list_matieres_ens'),
    path('<int:dep_id>/ajax/matieres/', views.matieres_json_ens, name='matieres_json_ens'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES SPÉCIALITÉS
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/specialites/', views.list_Specialite_Ens, name='list_specialites_ens'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES AMPHITHÉÂTRES
    # ══════════════════════════════════════════════════════════════
    path('amphi/list/<int:dep_id>/', views.list_Amphi_Ens, name='list_Amphi_Ens'),
    path('amphi/timetable/<int:dep_id>/<int:amphi_dep_id>/<int:semestre_numero>/', views.timeTable_Amphi_Ens, name='timeTable_Amphi_Ens'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES SALLES
    # ══════════════════════════════════════════════════════════════
    path('salle/list/<int:dep_id>/', views.list_Salle_Ens, name='list_Salle_Ens'),
    path('salle/timetable/<int:dep_id>/<int:salle_dep_id>/<int:semestre_numero>/', views.timeTable_Salle_Ens, name='timeTable_Salle_Ens'),

    # ══════════════════════════════════════════════════════════════
    # LISTE DES LABORATOIRES
    # ══════════════════════════════════════════════════════════════
    path('labo/list/<int:dep_id>/', views.list_Labo_Ens, name='list_Labo_Ens'),
    path('labo/timetable/<int:dep_id>/<int:labo_dep_id>/<int:semestre_numero>/', views.timeTable_Labo_Ens, name='timeTable_Labo_Ens'),

    # ══════════════════════════════════════════════════════════════
    # FICHE PÉDAGOGIQUE
    # ══════════════════════════════════════════════════════════════
    path('fichPeda_Ens_Semestre/<int:dep_id>/', views.fichPeda_Ens_Semestre, name='fichPeda_Ens_Semestre'),
    path('fichePedagogique/<int:dep_id>/', views.fichePedagogique, name='fichePedagogique'),

    # ══════════════════════════════════════════════════════════════
    # NIVEAUX ENSEIGNÉS
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/niveaux-enseigner/', views.niveaux_enseigner, name='niveaux_enseigner'),
    path('<int:dep_id>/niveaux/', views.list_NivSpeDep_Ens, name='list_NivSpeDep_Ens'),
    path('<int:dep_id>/niveaux/<int:niv_spe_dep_id>/timetable/<int:semestre_num>/', views.timeTable_Niv_Ens, name='timeTable_Niv_Ens'),

    # ══════════════════════════════════════════════════════════════
    # GESTION DES SOUS-GROUPES
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/sous-groupes/nombre/<int:classe_id>/', views.page_nombre_sous_groupes, name='page_nombre_sous_groupes'),
    path('<int:dep_id>/sous-groupes/affecter/<int:classe_id>/', views.affecter_etudiants_sous_groupes, name='affecter_etudiants_sous_groupes'),
    path('<int:dep_id>/sous-groupes/liste/<int:niv_spe_dep_sg_id>/', views.liste_sous_groupes, name='liste_sous_groupes'),
    path('<int:dep_id>/sous-groupes/affecter-direct/<int:niv_spe_dep_sg_id>/', views.affecter_direct_sous_groupes, name='affecter_direct_sous_groupes'),

    # ══════════════════════════════════════════════════════════════
    # PROFIL ENSEIGNANT
    # ══════════════════════════════════════════════════════════════
    path('profile/<int:dep_id>/', views.profile_ens_dep, name='profile_ens_dep'),
    path('profileUpdate/<int:dep_id>/', views.profileUpdate_ens_dep, name='profileUpdate_ens_dep'),
    path('change-password/<int:dep_id>/', views.change_password_ens_dep, name='change_password_Ens'),

    # ══════════════════════════════════════════════════════════════
    # GESTION DES SÉANCES
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/classe/<int:clas_id>/seances/', views.list_Sea_Ens, name='list_Sea_Ens'),
    path('<int:dep_id>/classe/<int:clas_id>/seances/new/', views.new_Seance_Ens, name='new_Seance_Ens'),
    path('<int:dep_id>/seance/<int:sea_id>/update/', views.update_seance, name='update_seance'),
    path('<int:dep_id>/seance/<int:sea_id>/delete/', views.delete_seance, name='delete_seance'),

    # ══════════════════════════════════════════════════════════════
    # GESTION DES ABSENCES
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/seance/<int:sea_id>/absences/', views.list_Abs_Etu, name='list_Abs_Etu'),
    path('<int:dep_id>/classe/<int:clas_id>/absences/', views.list_Abs_Etu_Classe, name='list_Abs_Etu_Classe'),

    # ══════════════════════════════════════════════════════════════
    # GESTION DES NOTES
    # ══════════════════════════════════════════════════════════════
    path('<int:dep_id>/classe/<int:clas_id>/notes/', views.list_Notes_Etu_Classe, name='list_Notes_Etu_Classe'),
    path('<int:dep_id>/classe/<int:clas_id>/notes/valider/', views.valider_notes_classe, name='valider_notes_classe'),
    path('<int:dep_id>/classe/<int:clas_id>/notes/creer/', views.creer_notes_classe, name='creer_notes_classe'),
]
