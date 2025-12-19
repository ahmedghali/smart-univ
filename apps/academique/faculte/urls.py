# apps/academique/faculte/urls.py

from django.urls import path
from . import views

app_name = 'faculte'

urlpatterns = [
    # Tableau de bord de la faculté
    path('dashboard/', views.dashboard_Fac, name='dashboard_Fac'),

    # Profil de la faculté
    path('profile/', views.profile_Fac, name='profile_Fac'),
    path('profile/<int:faculte_id>/', views.profile_Fac, name='profile_Fac_by_id'),

    # Mise à jour du profil
    path('profile/update/', views.profileUpdate_Fac, name='profileUpdate_Fac'),
    path('profile/update/<int:faculte_id>/', views.profileUpdate_Fac, name='profileUpdate_Fac_by_id'),
]
