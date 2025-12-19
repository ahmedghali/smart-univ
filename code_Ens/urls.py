from django.urls import path
from django.http import HttpResponse
from apps.academique.departement.views import *
from .views import *
from django.conf.urls.static import static
from django.conf import settings

app_name = 'ense'

urlpatterns = [
     # ================ DASHBOARD ET PROFIL ================
     path('dashboard/<int:dep_id>/', dashboard_Ens, name='dashboard_Ens'),
     path('profile/<int:dep_id>/', profile_Ens, name='profile_Ens'),
     path('profileUpdate/<int:dep_id>/', profileUpdate_Ens, name='profileUpdate_Ens'),
     path('change_password/<int:dep_id>/', change_password_Ens, name='change_password_Ens'),
     path('timeTable/<int:dep_id>/', timeTable_Ens, name='timeTable_Ens'),

     # ================ MATIÈRES ET NIVEAUX ENSEIGNÉS ================
     path('<int:dep_id>/matieres/', list_Mat_Niv_Ens, name='list_matieres_ens'),
     path('<int:dep_id>/niveaux-enseigner/', niveaux_enseigner, name='niveaux_enseigner'),

     # ================ INFRASTRUCTURE ================
     path('amphi/list/<int:dep_id>/', list_Amphi_Ens, name='list_Amphi_Ens'),
     path('amphi/timetable/<int:dep_id>/<int:amphi_dep_id>/<int:semestre_numero>/', timeTable_Amphi_Ens, name='timeTable_Amphi_Ens'),
     path('salle/list/<int:dep_id>/', list_Salle_Ens, name='list_Salle_Ens'),
     path('salle/timetable/<int:dep_id>/<int:salle_dep_id>/<int:semestre_numero>/', timeTable_Salle_Ens, name='timeTable_Salle_Ens'),
     path('labo/list/<int:dep_id>/', list_Labo_Ens, name='list_Labo_Ens'),
     path('labo/timetable/<int:dep_id>/<int:labo_dep_id>/<int:semestre_numero>/', timeTable_Labo_Ens, name='timeTable_Labo_Ens'),

     # ================ FICHES PÉDAGOGIQUES ================
     path('fichePedagogique/<int:dep_id>/', fichePedagogique, name='fichePedagogique'),
     path('fichPeda_Ens_Semestre/<int:dep_id>/', fichPeda_Ens_Semestre, name='fichPeda_Ens_Semestre'),

     # ================ SÉANCES CLASSIQUES ================
     path('new_Sceance_Ens/<int:dep_id>/<int:clas_id>/', new_Sceance_Ens, name='new_Sceance_Ens'),
     path('list_Sea_Ens/<int:dep_id>/<int:clas_id>/', list_Sea_Ens, name='list_Sea_Ens'),
     path('update_seance/<int:dep_id>/<int:sea_id>/', update_seance, name='update_seance'),
     path('list_Abs_Etu/<int:dep_id>/<int:sea_id>/', list_Abs_Etu, name='list_Abs_Etu'),
     path('list_Abs_Etu_Classe/<int:dep_id>/<int:clas_id>/', list_Abs_Etu_Classe, name='list_Abs_Etu_Classe'),
     path('delete-seance/<int:dep_id>/<int:sea_id>/', delete_seance, name='delete_seance'),

     # ================ NIVEAUX ET ÉTUDIANTS ================
     path('<int:dep_id>/niveaux/', list_NivSpeDep_Ens, name='list_NivSpeDep_Ens'),
     
     # ✅ URL CORRIGÉE : niv_spe_dep_id au lieu de niv_id
     path('<int:dep_id>/niveau/<int:niv_spe_dep_id>/emploi/<int:semestre_num>/', 
          timeTable_Niv_Ens, 
          name='timeTable_Niv_Ens'),
     
     path('<int:dep_id>/etudiants/', list_Etudiant_Ens, name='list_etudiants_ens'),
     path('<int:dep_id>/etudiant/<int:etudiant_id>/profile/', profile_Etu_Ens, name='profile_Etu_Ens'),

     # ================ SPÉCIALITÉS ================
     path('<int:dep_id>/specialites/', list_Specialite_Ens, name='list_specialites_ens'),

     # ================ AJAX ENDPOINTS ================
     path('<int:dep_id>/ajax/reformes/', get_reformes_json_ens, name='get_reformes_json_ens'),
     path('<int:dep_id>/ajax/niveaux/<int:reforme_id>/', get_niveaux_json_ens, name='get_niveaux_json_ens'),
     path('<int:dep_id>/ajax/groupes/<int:niveau_id>/', get_niv_spe_dep_sg_json_ens, name='get_niv_spe_dep_sg_json_ens'),
     path('<int:dep_id>/ajax/refs/', refs_json_ens, name='refs_json_ens'),
     path('<int:dep_id>/ajax/nivs/<int:reforme_id>/', nivs_json_ens, name='nivs_json_ens'),
     path('<int:dep_id>/ajax/spts/<int:niveau_id>/', spts_json_ens, name='spts_json_ens'),
     path('<int:dep_id>/ajax/semestres/', semestres_json_ens, name='semestres_json_ens'),
     path('<int:dep_id>/ajax/matieres/', matieres_json_ens, name='matieres_json_ens'),

     # ================ SOUS-GROUPES ================
     path('nombre-sous-groupes/<int:dep_id>/<int:classe_id>/', page_nombre_sous_groupes, name='page_nombre_sous_groupes'),
     path('affecter-etudiants/<int:dep_id>/<int:classe_id>/', affecter_etudiants_sous_groupes, name='affecter_etudiants_sous_groupes'),
     path('liste-sous-groupes/<int:dep_id>/<int:niv_spe_dep_sg_id>/', liste_sous_groupes, name='liste_sous_groupes'),
     path('affecter-direct/<int:dep_id>/<int:niv_spe_dep_sg_id>/', affecter_direct_sous_groupes, name='affecter_direct_sous_groupes'),

     # ================ GESTION DES NOTES ================
     path('init_Notes_Etu_Classe/<int:dep_id>/<int:clas_id>/', 
          init_Notes_Etu_Classe, 
          name='init_Notes_Etu_Classe'),
     
     path('list_Notes_Etu_Classe/<int:dep_id>/<int:clas_id>/', 
          list_Notes_Etu_Classe, 
          name='list_Notes_Etu_Classe'),
     
     path('valider_notes_classe/<int:dep_id>/<int:clas_id>/', 
          valider_notes_classe, 
          name='valider_notes_classe'),
     
     path('export_notes_classe/<int:dep_id>/<int:clas_id>/', 
          export_notes_classe, 
          name='export_notes_classe'),

     # ================ LISTE DES ENSEIGNANTS ================
     path('list-enseignants/<int:dep_id>/<int:semestre_num>/', 
          list_enseignants_ens, 
          name='list_enseignants_ens'),



     path('<int:dep_id>/update-classe-moodle/<int:classe_id>/', 
         update_classe_moodle, 
         name='update_classe_moodle'),


]

# Fichiers statiques pour le développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)