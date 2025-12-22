from django.urls import path
from . import views

app_name = 'departement'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_Dep, name='dashboard_Dep'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),

    # Profil
    path('profile/', views.profile_Dep, name='profile_Dep'),
    path('profile/update/', views.profileUpdate_Dep, name='profileUpdate_Dep'),

    # Enseignants
    path('enseignants/<int:semestre_num>/', views.list_enseignants_dep, name='list_enseignants_dep'),
    path('enseignants/new/', views.new_Enseignant, name='new_Enseignant'),
    path('enseignants/heures/<int:semestre>/', views.heures_enseignants_dep, name='heures_enseignants_dep'),
    path('enseignants/delete/<int:ens_dep_id>/', views.delete_Enseignant, name='delete_Enseignant'),
    path('enseignants/delete-acces/<int:ens_id>/', views.delete_Ens_Acces_Dep, name='delete_Ens_Acces_Dep'),
    path('enseignants/activate/<int:ens_id>/', views.activate_Ens_Acces_Dep, name='activate_Ens_Acces_Dep'),

    # Étudiants
    path('etudiants/', views.list_etudiants, name='list_etudiants'),
    path('etudiants/import/', views.import_etudiants, name='import_etudiants'),

    # Matières et Spécialités
    path('matieres/', views.list_Mat_Niv, name='list_Mat_Niv'),
    path('specialites/', views.list_Specialite_Dep, name='list_Specialite_Dep'),

    # Emploi du temps
    path('emploi/import/', views.import_emploi, name='import_emploi'),
]
