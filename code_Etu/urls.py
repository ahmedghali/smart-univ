from django.urls import path
from .views import *
# from django.contrib.auth.views import LoginView, LogoutView
from django.conf.urls.static import static
from django.conf import settings
# from .views import login_view, select_rol


app_name = 'etudiant'  # ← Ici c'est 'faculte'

urlpatterns = [
    #    sur site      sur views             sur CALL
    path('dashboard/', dashboard_Etu, name='dashboard_Etu'),
    path('profile/', profile_Etu, name='profile_Etu'),
    path('profileUpdate/', profileUpdate_Etu, name='profileUpdate_Etu'),
    path('change_password/', change_password_Etu, name='change_password_Etu'),

]
# Ajouter les URLs pour les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)




from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings

app_name = 'etudiant'

urlpatterns = [
    # Dashboard et profil
    path('dashboard/', dashboard_Etu, name='dashboard_Etu'),
    path('profile/', profile_Etu, name='profile_Etu'),
    path('profileUpdate/', profileUpdate_Etu, name='profileUpdate_Etu'),
    path('change_password/', change_password_Etu, name='change_password_Etu'),
    
    # Emploi du temps
    path('timeTable/', timeTable_Etu, name='timeTable_Etu'),
    
    # Absences
    path('absences/classe/<int:clas_id>/', abs_Etu_Classe, name='abs_Etu_Classe'),
    
    # Détails d'une classe (optionnel)
    path('classe/detail/<int:classe_id>/', classe_detail_etu, name='classe_detail_etu'),
    
    # Académique - Résultats et notes
    # path('notes/', notes_Etu, name='notes_Etu'),
    # path('notes/matiere/<int:matiere_id>/', notes_matiere_Etu, name='notes_matiere_Etu'),
    # path('bulletin/', bulletin_Etu, name='bulletin_Etu'),
    # path('bulletin/semestre/<int:semestre_id>/', bulletin_semestre_Etu, name='bulletin_semestre_Etu'),
    
    # Cours et contenu pédagogique
    # path('cours/', cours_Etu, name='cours_Etu'),
    # path('cours/matiere/<int:matiere_id>/', cours_matiere_Etu, name='cours_matiere_Etu'),
    # path('cours/document/<int:document_id>/', document_detail_Etu, name='document_detail_Etu'),
    
    # Examens et évaluations
    # path('examens/', examens_Etu, name='examens_Etu'),
    # path('examens/calendrier/', calendrier_examens_Etu, name='calendrier_examens_Etu'),
    # path('examens/resultat/<int:examen_id>/', resultat_examen_Etu, name='resultat_examen_Etu'),
    
    # Communication
    # path('messages/', messages_Etu, name='messages_Etu'),
    # path('messages/nouveau/', nouveau_message_Etu, name='nouveau_message_Etu'),
    # path('messages/conversation/<int:conversation_id>/', conversation_Etu, name='conversation_Etu'),
    # path('annonces/', annonces_Etu, name='annonces_Etu'),
    # path('annonces/detail/<int:annonce_id>/', annonce_detail_Etu, name='annonce_detail_Etu'),
    
    # Services étudiants
    # path('bibliotheque/', bibliotheque_Etu, name='bibliotheque_Etu'),
    # path('bibliotheque/livre/<int:livre_id>/', livre_detail_Etu, name='livre_detail_Etu'),
    # path('bibliotheque/emprunts/', emprunts_Etu, name='emprunts_Etu'),
    
    # Demandes administratives
    # path('demandes/', demandes_Etu, name='demandes_Etu'),
    # path('demandes/nouvelle/', nouvelle_demande_Etu, name='nouvelle_demande_Etu'),
    # path('demandes/suivi/<int:demande_id>/', suivi_demande_Etu, name='suivi_demande_Etu'),
    # path('attestations/', attestations_Etu, name='attestations_Etu'),
    # path('attestations/demande/<str:type_attestation>/', demande_attestation_Etu, name='demande_attestation_Etu'),
    
    # Orientation et stage
    # path('orientation/', orientation_Etu, name='orientation_Etu'),
    # path('stages/', stages_Etu, name='stages_Etu'),
    # path('stages/offre/<int:offre_id>/', offre_stage_detail_Etu, name='offre_stage_detail_Etu'),
    # path('stages/candidature/<int:offre_id>/', candidature_stage_Etu, name='candidature_stage_Etu'),
    
    # Activités et vie étudiante
    # path('activites/', activites_Etu, name='activites_Etu'),
    # path('activites/inscription/<int:activite_id>/', inscription_activite_Etu, name='inscription_activite_Etu'),
    # path('clubs/', clubs_Etu, name='clubs_Etu'),
    # path('clubs/detail/<int:club_id>/', club_detail_Etu, name='club_detail_Etu'),
    
    # Feedback et évaluation
    # path('evaluation/enseignant/<int:enseignant_id>/', evaluation_enseignant_Etu, name='evaluation_enseignant_Etu'),
    # path('evaluation/cours/<int:cours_id>/', evaluation_cours_Etu, name='evaluation_cours_Etu'),
    # path('suggestions/', suggestions_Etu, name='suggestions_Etu'),
    
    # Paramètres et préférences
    # path('parametres/', parametres_Etu, name='parametres_Etu'),
    # path('notifications/', notifications_Etu, name='notifications_Etu'),
    # path('notifications/marquer-lu/<int:notification_id>/', marquer_notification_lue, name='marquer_notification_lue'),
    
    # API endpoints (optionnels)
    # path('api/absences/stats/', api_absences_stats_Etu, name='api_absences_stats_Etu'),
    # path('api/notes/moyenne/', api_notes_moyenne_Etu, name='api_notes_moyenne_Etu'),
    # path('api/planning/semaine/', api_planning_semaine_Etu, name='api_planning_semaine_Etu'),
    
    # Exports et impressions
    # path('export/planning/pdf/', export_planning_pdf_Etu, name='export_planning_pdf_Etu'),
    # path('export/bulletin/pdf/<int:semestre_id>/', export_bulletin_pdf_Etu, name='export_bulletin_pdf_Etu'),
    # path('export/absences/pdf/<int:matiere_id>/', export_absences_pdf_Etu, name='export_absences_pdf_Etu'),

    # URL pour consulter les notes d'une classe (lecture seule pour l'étudiant)
    path('notes-classe/<int:clas_id>/', notes_Etu_Classe, name='notes_Etu_Classe'),

    path('list-seances/<int:clas_id>/', 
         list_Seance_Etu, 
         name='list_Seance_Etu'),
]

# Ajouter les URLs pour les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
