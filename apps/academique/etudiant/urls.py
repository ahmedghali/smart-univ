# apps/academique/etudiant/urls.py

from django.urls import path
from . import views

app_name = 'etudiant'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_Etud, name='dashboard_Etud'),
    path('', views.dashboard_Etud, name='dashboard_Etu'),  # Alias pour dashboard_Etu

    # Emploi du temps
    path('timetable/', views.timeTable_Etu, name='timeTable_Etu'),

    # Profil
    path('profile/', views.profile_Etud, name='profile_Etud'),
    path('profile/', views.profile_Etud, name='profile_Etu'),  # Alias
    path('profile/<int:etudiant_id>/', views.profile_Etud, name='profile_Etud_id'),
    path('profile/update/', views.profileUpdate_Etud, name='profileUpdate_Etud'),
    path('profile/update/', views.profileUpdate_Etud, name='profileUpdate_Etu'),  # Alias
    path('profile/change-password/', views.changePassword_Etud, name='changePassword_Etud'),
    path('profile/change-password/', views.changePassword_Etud, name='changePassword_Etu'),  # Alias

    # Liste et détails
    path('list/', views.list_Etud, name='list_Etud'),
    path('detail/<int:etudiant_id>/', views.detail_Etud, name='detail_Etud'),

    # Absences, Notes et Séances
    path('absences/classe/<int:clas_id>/', views.abs_Etu_Classe, name='abs_Etu_Classe'),
    path('notes-classe/<int:clas_id>/', views.notes_Etu_Classe, name='notes_Etu_Classe'),
    path('list-seances/<int:clas_id>/', views.list_Seance_Etu, name='list_Seance_Etu'),
]
