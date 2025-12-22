from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

app_name = 'departement'

urlpatterns = [
     path('dashboard/', dashboard_Dep, name='dashboard_Dep'),
     path('profile/', profile_Dep, name='profile_Dep'),
     path('profileUpdate/', profileUpdate_Dep, name='profileUpdate_Dep'),

     path('list_Seance_Ens/<int:clas_id>/', list_Seance_Ens, name='list_Seance_Ens'),
     path('new_Sceance_Ens/<int:clas_id>/<int:Ens_id>/', new_Sceance_Ens, name='new_Sceance_Ens'),

     path('fichePedagogique_Ens_Dep/<int:ens_id>/', fichePedagogique_Ens_Dep, name='fichePedagogique_Ens_Dep'),
     path('FP_Ens_Dep_Semestre/<int:ens_id>/<int:semestre_num>/', fichePedagogique_Ens_Dep_Semestre, name='FP_Ens_Dep_Semestre'),

     # URLs JSON pour les données dynamiques
     path('refs-json/', get_reformes_json, name='refs-json'),
     path('nivs-json/<int:reforme_id>/', get_niveaux_json, name='nivs-json'),
     path('spts-json/<int:niveau_id>/', get_specialites_json, name='spts-json'),
     path('semestres-json/', get_semestres_json, name='semestres-json'),
     path('matieres-json/', get_matieres_json, name='matieres-json'),
     path('list_Mat_Niv/', list_Mat_Niv, name='list_Mat_Niv'),
     path('profile_Ens_Dep/<int:ens_id>/', profile_Ens_Dep, name='profile_Ens_Dep'),

     # URLs pour import/export
     path('import_emploi/', import_emploi, name='import_emploi'),
     path('niv-spe-dep-sg-json/<int:niveau_id>/', get_niv_spe_dep_sg_json, name='niv-spe-dep-sg-json'),
     path('import-etudiants/', import_etudiants, name='import_etudiants'),
     path('import-matieres/', import_matieres, name='import-matieres'),

     # URLs pour étudiants
     path('list-etudiants/', list_etudiants, name='list_etudiants'),
     path('get-reformes/', get_reformes_json, name='get_reformes_json'),
     path('get-niveaux/<int:reforme_id>/', get_niveaux_json, name='get_niveaux_json'),
     path('get-niv-spe-dep-sg/<int:niveau_id>/', get_niv_spe_dep_sg_json, name='get_niv_spe_dep_sg_json'),
     path('desinscrire-univ/', desinscrire_univ, name='desinscrire_univ'),
     path('inscrire-univ/', inscrire_univ, name='inscrire_univ'),
     path('<int:etudiant_id>/profile/', profile_Etu, name='profile_Etu'),
     path('<int:etudiant_id>/profileUpdate_Etu_Dep/', profileUpdate_Etu_Dep, name='profileUpdate_Etu_Dep'),

     # URLs pour gestion des enseignants
     path('new_Enseignant/', new_Enseignant, name='new_Enseignant'),
     path('facs-json/', facs_json, name='facs_json'),
     path('deps-json/', deps_json, name='deps_json'),
     path('enss-json/', enss_json, name='enss_json'),

     path('seance/view/<int:seance_id>/', view_seance_dep, name='view_seance_dep'),

     path('inscription_Ens/<int:ens_id>/', inscription_Ens, name='inscription_Ens'),
     path('delete_Ens_Platform/<int:ens_id>/', delete_Ens_Platform, name='delete_Ens_Platform'),
     path('delete_Enseignant/<int:ens_dep_id>/', delete_Enseignant, name='delete_Enseignant'),

     # Infrastructure
     path('list_Specialite_Dep/', list_Specialite_Dep, name='list_Specialite_Dep'),


     path('list_NivSpeDep/', list_NivSpeDep, name='list_NivSpeDep'),

     path('timeTable_Niv/<int:niv_spe_dep_id>/<int:semestre_num>/', timeTable_Niv, name='timeTable_Niv'),



     path('list_Amphi_Dep/', list_Amphi_Dep, name='list_Amphi_Dep'),
     path('timeTable_Amphi/<int:amp_id>/<int:semestre_num>/', timeTable_Amphi, name='timeTable_Amphi'),
     path('list_Salle_Dep/', list_Salle_Dep, name='list_Salle_Dep'),
     path('timeTable_Salle/<int:salle_id>/<int:semestre_num>/', timeTable_Salle, name='timeTable_Salle'),
     path('list_Labo_Dep/', list_Labo_Dep, name='list_Labo_Dep'),
     path('timeTable_Labo/<int:labo_id>/<int:semestre_num>/', timeTable_Labo, name='timeTable_Labo'),

     # ✅ NOUVELLES URLs - Pages séparées pour liste et heures
     # URL principale - Liste des enseignants
     path('enseignants/liste/', list_enseignants_dep, name='list_enseignants_dep'),
     path('enseignants/liste/<int:semestre_num>/', list_enseignants_dep, name='list_enseignants_dep'),
     
     # URL pour heures de travail
     path('enseignants/heures/', heures_enseignants_dep, name='heures_enseignants_dep'),
     path('enseignants/heures/<int:semestre_num>/', heures_enseignants_dep, name='heures_enseignants_dep'),

     # ⚠️ ANCIENNE URL - Gardée pour compatibilité (redirige vers liste)
     # path('enseignants/', RedirectView.as_view(url='/enseignants/liste/', permanent=False), name='manage_enseignants'),
     path('enseignants/<int:semestre_num>/', lambda request, semestre_num: redirect('depa:list_enseignants_dep', semestre_num=semestre_num)),

     path('emploi_Ens/<int:ens_id>/<int:semestre_num>/', emploi_Ens, name='emploi_Ens_semestre'),
     path('emploi_Ens/<int:ens_id>/', emploi_Ens, name='emploi_Ens'),

     # URLs pour absences
     path('absences/classe/<int:clas_id>/', 
          list_Abs_Etu_Classe_Dep, 
          name='list_absences_classe'),

     path('absences/export/excel/<int:clas_id>/', 
          export_absences_excel, 
          name='export_absences_excel'),

     path('api/absences/stats/<int:clas_id>/', 
          absences_statistics_api, 
          name='absences_stats_api'),
     path('enseignants/update-all-scholars/', 
          update_all_scholars, 
          name='update_all_scholars'),

     # ... autres URLs ...
     path('enseignant/<int:enseignant_id>/update-scholar/', 
          update_scholar_manual, 
          name='update_scholar_manual'),

     # URLs pour notes
     path('notes-classe/<int:clas_id>/', list_Notes_Etu_Classe, name='list_Notes_Etu_Classe'),
     path('export-notes-classe/<int:clas_id>/', export_notes_classe, name='export_notes_classe'),

     # path('enseignant/<int:enseignant_id>/update-scholar/', update_scholar_manual,  name='update_scholar_manual'),

     # ... autres URLs ...
    path('timetable/<int:niv_spe_dep_id>/<int:semestre_num>/', 
         timeTable_Niv, 
         name='timeTable_Niv'),
    
    
    
    # URL pour supprimer une classe
    path('classe/<int:classe_id>/delete/', 
         delete_classe, 
         name='delete_classe'),
    
    # URL AJAX pour charger les lieux
    path('get-lieux/', 
         get_lieux_ajax, 
         name='get_lieux_ajax'),

     # URL pour modifier une classe
    path('classe/<int:classe_id>/edit/', 
         edit_classe, 
         name='edit_classe'),

     path('add-classe/', add_classe, name='add_classe'),

     # URL pour liste des absences par niveau
     path('absences/niveau/<int:niv_spe_dep_id>/<int:semestre_num>/',
          list_absences_niveau,
          name='list_absences_niveau'),

]

# Ajouter les URLs pour les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)