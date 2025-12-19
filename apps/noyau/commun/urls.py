from django.urls import path
from . import views

app_name = 'commun'

urlpatterns = [
    path('', views.home, name='home'),
]
