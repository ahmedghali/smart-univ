from django.shortcuts import render


def home(request):
    """Page d'accueil : présentation de l'application et chiffres réels de l'établissement."""
    from apps.academique.departement.models import Departement, Specialite
    from apps.academique.enseignant.models import Enseignant
    from apps.academique.etudiant.models import Etudiant
    from apps.academique.faculte.models import Faculte

    context = {
        "page_title": "الرئيسية",
        "chiffres": {
            "facultes": Faculte.objects.count(),
            "departements": Departement.objects.count(),
            "specialites": Specialite.objects.count(),
            "enseignants": Enseignant.objects.count(),
            "etudiants": Etudiant.objects.count(),
        },
    }
    return render(request, "commun/home.html", context)
