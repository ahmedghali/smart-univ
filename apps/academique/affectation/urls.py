# apps/academique/affectation/urls.py

from django.urls import path
from . import views

app_name = 'affectation'

urlpatterns = [
    # Liste et détails
    path('list/', views.list_affectations, name='list_affectations'),
    path('detail/<int:affectation_id>/', views.detail_affectation, name='detail_affectation'),

    # CRUD
    path('create/', views.create_affectation, name='create_affectation'),
    path('update/<int:affectation_id>/', views.update_affectation, name='update_affectation'),
    path('delete/<int:affectation_id>/', views.delete_affectation, name='delete_affectation'),

    # Statistiques
    path('update-stats-s1/<int:affectation_id>/', views.update_statistiques_s1, name='update_statistiques_s1'),
    path('update-stats-s2/<int:affectation_id>/', views.update_statistiques_s2, name='update_statistiques_s2'),

    # AJAX pour l'admin Classe
    path('ajax/lieux-by-departement/', views.ajax_get_lieux_by_departement, name='ajax_lieux_by_departement'),
    path('ajax/lieux-by-enseignant/', views.ajax_get_lieux_by_enseignant, name='ajax_lieux_by_enseignant'),
]
