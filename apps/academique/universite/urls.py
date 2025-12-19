# apps/academique/universite/urls.py

from django.urls import path
from . import views

app_name = 'universite'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_Uni, name='dashboard_Uni'),

    # Profil de l'université
    path('profile/', views.profile_Uni, name='profile_Uni'),

    # Mise à jour du profil
    path('profile/update/', views.profileUpdate_Uni, name='profileUpdate_Uni'),
]
