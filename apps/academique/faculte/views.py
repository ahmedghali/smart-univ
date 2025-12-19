# apps/academique/faculte/views.py

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# from apps.academique.affectation.models import Ens_Dep  # TODO: Uncomment when Ens_Dep model is created
# from apps.academique.departement.models import Departement  # TODO: Uncomment when needed
from .models import Faculte, Filiere
from .forms import profileUpdate_Fac_Form


# ══════════════════════════════════════════════════════════════
# VUES POUR LE TABLEAU DE BORD DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

@login_required
def dashboard_Fac(request):
    """
    Tableau de bord du doyen de faculté.
    Affiche les informations générales et statistiques de la faculté.

    TODO: Update this view when Ens_Dep and Departement models are ready.
    For now, assumes user can access all faculties.
    """
    try:
        # TODO: Replace with proper logic using Ens_Dep when available
        # enseignant = request.user.enseignant_profile
        # real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        # my_fac = real_Dep.departement.faculte

        # Temporary: Get first faculty or show all
        facultes = Faculte.objects.all()
        if facultes.exists():
            my_fac = facultes.first()
            messages.success(request, 'مرحبًا بك في لوحة تحكم عميد الكلية')
        else:
            messages.warning(request, 'لا توجد كليات متاحة / Aucune faculté disponible')
            my_fac = None

        context = {
            'title': 'لوحة التحكم',
            'my_Fac': my_fac,
            'all_facultes': facultes,
        }
        return render(request, 'faculte/dashboard_Fac.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


# ══════════════════════════════════════════════════════════════
# VUES POUR LE PROFIL DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

@login_required
def profile_Fac(request, faculte_id=None):
    """
    Affichage du profil de la faculté.
    Montre toutes les informations détaillées de la faculté.

    TODO: Update this view when Ens_Dep and Departement models are ready.
    For now, accepts faculte_id as parameter or shows first faculty.
    """
    try:
        # TODO: Replace with proper logic using Ens_Dep when available
        # enseignant = request.user.enseignant_profile
        # real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        # my_fac = real_Dep.departement.faculte

        if faculte_id:
            my_fac = get_object_or_404(Faculte, id=faculte_id)
        else:
            facultes = Faculte.objects.all()
            if facultes.exists():
                my_fac = facultes.first()
            else:
                messages.warning(request, 'لا توجد كليات متاحة / Aucune faculté disponible')
                return redirect('comm:home')

        context = {
            'title': 'صفحة التعريف',
            'my_Fac': my_fac,
        }
        return render(request, 'faculte/profile_Fac.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


@login_required
def profileUpdate_Fac(request, faculte_id=None):
    """
    Mise à jour du profil de la faculté.
    Permet au doyen de modifier les informations de contact et autres détails.

    TODO: Update this view when Ens_Dep and Departement models are ready.
    For now, accepts faculte_id as parameter or updates first faculty.
    """
    try:
        # TODO: Replace with proper logic using Ens_Dep when available
        # enseignant = request.user.enseignant_profile
        # real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        # my_fac = real_Dep.departement.faculte

        if faculte_id:
            my_fac = get_object_or_404(Faculte, id=faculte_id)
        else:
            facultes = Faculte.objects.all()
            if facultes.exists():
                my_fac = facultes.first()
            else:
                messages.warning(request, 'لا توجد كليات متاحة / Aucune faculté disponible')
                return redirect('comm:home')

        if request.method == 'POST':
            Fac_form = profileUpdate_Fac_Form(
                request.POST,
                request.FILES,
                instance=my_fac
            )

            if Fac_form.is_valid():
                Fac_form.save()
                messages.success(request, 'تم تحديث المعلومات بنجاح / Informations mises à jour avec succès')
                return redirect('faculte:profile_Fac')
            else:
                messages.error(request, 'خطأ في النموذج / Erreur dans le formulaire')
        else:
            Fac_form = profileUpdate_Fac_Form(instance=my_fac)

        context = {
            'title': 'تعديل المعلومات',
            'my_Fac': my_fac,
            'Fac_form': Fac_form,
        }
        return render(request, 'faculte/profileUpdate_Fac.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')
