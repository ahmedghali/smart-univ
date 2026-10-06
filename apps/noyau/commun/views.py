from django.shortcuts import render


def home(request):
    """Vue de la page d'accueil"""
    context = {
        'page_title': 'الرئيسية',
    }
    return render(request, 'commun/home.html', context)
