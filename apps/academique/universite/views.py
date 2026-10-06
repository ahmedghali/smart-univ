# apps/academique/universite/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UniversiteProfileUpdateForm
from .models import Universite


def get_user_universite(user):
    """Université où l'utilisateur occupe un poste de direction (recteur ou vice-recteur)."""
    universite = Universite.objects.filter(
        affectations_postes__user=user,
        affectations_postes__est_actif=True,
        affectations_postes__poste__code__in=["recteur", "vice_rect_p", "vice_rect_pg"],
    ).first()
    if universite is None and user.is_superuser:
        universite = Universite.objects.first()
    return universite


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════


@login_required
def dashboard_Uni(request):
    """
    Tableau de bord du responsable d'université (recteur ou vice-recteurs).
    """
    # Récupérer l'université de l'utilisateur
    selected_universite = get_user_universite(request.user)

    if not selected_universite:
        messages.error(
            request, "عذرًا، ليس لديك صلاحية الوصول إلى هذه الصفحة / Désolé, vous n'avez pas accès à cette page."
        )
        return redirect("comm:home")

    messages.success(request, "مرحبًا بك في لوحة تحكم الجامعة / Bienvenue dans le tableau de bord")

    context = {
        "title": "لوحة التحكم / Tableau de bord",
        "my_Uni": selected_universite,
    }
    return render(request, "universite/dashboard_Uni.html", context)


# ══════════════════════════════════════════════════════════════
# PROFIL
# ══════════════════════════════════════════════════════════════


@login_required
def profile_Uni(request):
    """
    Affiche le profil de l'université.
    """
    selected_universite = get_user_universite(request.user)

    if not selected_universite:
        messages.error(
            request, "عذرًا، ليس لديك صلاحية الوصول إلى هذه الصفحة / Désolé, vous n'avez pas accès à cette page."
        )
        return redirect("comm:home")

    context = {
        "title": "صفحة التعريف / Profil",
        "my_Uni": selected_universite,
    }
    return render(request, "universite/profile_Uni.html", context)


# ══════════════════════════════════════════════════════════════
# MISE À JOUR DU PROFIL
# ══════════════════════════════════════════════════════════════


@login_required
def profileUpdate_Uni(request):
    """
    Permet au recteur de mettre à jour les informations de l'université.
    """
    selected_universite = get_user_universite(request.user)

    if not selected_universite:
        messages.error(
            request, "عذرًا، ليس لديك صلاحية الوصول إلى هذه الصفحة / Désolé, vous n'avez pas accès à cette page."
        )
        return redirect("comm:home")

    if request.method == "POST":
        Uni_form = UniversiteProfileUpdateForm(request.POST, request.FILES, instance=selected_universite)

        if Uni_form.is_valid():
            Uni_form.save()
            messages.success(request, "تم تحديث المعلومات بنجاح / Informations mises à jour avec succès")
            return redirect("universite:profile_Uni")
        else:
            messages.error(request, "يرجى تصحيح الأخطاء أدناه / Veuillez corriger les erreurs ci-dessous")
    else:
        Uni_form = UniversiteProfileUpdateForm(instance=selected_universite)

    context = {
        "title": "تعديل المعلومات / Modification des informations",
        "my_Uni": selected_universite,
        "Uni_form": Uni_form,
    }
    return render(request, "universite/profileUpdate_Uni.html", context)
