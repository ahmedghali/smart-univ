# apps/noyau/authentification/urls.py

from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # Connexion et déconnexion
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Sélection du rôle et du département
    path('select-role/', views.select_role, name='select_role'),
    path('select-departement/', views.select_departement, name='select_departement'),

    # Profil
    path('profile/', views.profile_redirect, name='profile'),
    path('profile/update/', views.profile_update_redirect, name='profile_update'),

    # Dashboard
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
]
