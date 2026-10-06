from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import Ens_Dep
from apps.noyau.authentification.decorators import enseignant_access_required

from ..forms import ProfileUpdateEnsForm, UserUpdateForm
from ..models import Enseignant


@login_required
def profile_Ens(request, enseignant_id=None):
    """
    Affichage du profil de l'enseignant.
    Montre toutes les informations détaillées de l'enseignant.
    """
    try:
        if enseignant_id:
            # Affichage du profil d'un autre enseignant (par ID)
            enseignant = get_object_or_404(Enseignant, id=enseignant_id)
        else:
            # Affichage du propre profil de l'utilisateur
            enseignant = request.user.enseignant_profile

        # Récupérer le département principal
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        # Département courant (pour compatibilité avec base_Ens.html)
        departement = real_Dep.departement if real_Dep else None

        # Autres départements
        ALL_Dep = Ens_Dep.objects.filter(enseignant=enseignant).exclude(departement=departement) if departement else []

        context = {
            "title": "الملف الشخصي",
            "active_menu": "profile",
            "enseignant": enseignant,
            "my_Ens": enseignant,
            "my_Dep": departement,
            "my_Fac": departement.faculte if departement else None,
            "real_Dep": real_Dep,
            "ALL_Dep": ALL_Dep,
        }
        return render(request, "enseignant/profile_Ens.html", context)

    except Enseignant.DoesNotExist:
        messages.error(request, "لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable")
        return redirect("comm:home")
    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@login_required
def profileUpdate_Ens(request):
    """
    Mise à jour du profil de l'enseignant.
    Permet à l'enseignant de modifier ses informations personnelles et de contact.
    """
    try:
        enseignant = request.user.enseignant_profile

        # Récupérer le département principal
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        departement = real_Dep.departement if real_Dep else None

        if request.method == "POST":
            User_form = UserUpdateForm(request.POST, instance=request.user)
            Ens_form = ProfileUpdateEnsForm(request.POST, request.FILES, instance=enseignant)

            if User_form.is_valid() and Ens_form.is_valid():
                User_form.save()
                Ens_form.save()
                messages.success(request, "تم تحديث المعلومات بنجاح")
                return redirect("ense:profile_Ens")
            else:
                messages.error(request, "يرجى تصحيح الأخطاء في النموذج")
        else:
            User_form = UserUpdateForm(instance=request.user)
            Ens_form = ProfileUpdateEnsForm(instance=enseignant)

        context = {
            "title": "تعديل الملف الشخصي",
            "active_menu": "profile",
            "enseignant": enseignant,
            "my_Ens": enseignant,
            "my_Dep": departement,
            "my_Fac": departement.faculte if departement else None,
            "real_Dep": real_Dep,
            "User_form": User_form,
            "Ens_form": Ens_form,
        }
        return render(request, "enseignant/profileUpdate_Ens.html", context)

    except Enseignant.DoesNotExist:
        messages.error(request, "لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable")
        return redirect("comm:home")
    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@login_required
def change_password_Ens(request):
    """
    Changement de mot de passe de l'enseignant (sans dep_id).
    """
    try:
        enseignant = request.user.enseignant_profile

        # Récupérer le département principal
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        departement = real_Dep.departement if real_Dep else None

        if request.method == "POST":
            old_password = request.POST.get("old_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            # Vérifier l'ancien mot de passe
            if not request.user.check_password(old_password):
                messages.error(request, "كلمة المرور الحالية غير صحيحة / Mot de passe actuel incorrect")
            elif new_password != confirm_password:
                messages.error(
                    request, "كلمة المرور الجديدة وتأكيدها غير متطابقين / Les mots de passe ne correspondent pas"
                )
            elif len(new_password) < 8:
                messages.error(
                    request,
                    "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل / Le mot de passe doit contenir au moins 8 caractères",
                )
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès")
                return redirect("ense:profile_Ens")

        context = {
            "title": "تغيير كلمة المرور",
            "active_menu": "profile",
            "enseignant": enseignant,
            "my_Ens": enseignant,
            "my_Dep": departement,
            "my_Fac": departement.faculte if departement else None,
            "real_Dep": real_Dep,
        }
        return render(request, "enseignant/change_password_Ens.html", context)

    except Enseignant.DoesNotExist:
        messages.error(request, "لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable")
        return redirect("comm:home")
    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@enseignant_access_required
def profile_ens_dep(request, dep_id, enseignant, departement):
    """Afficher le profil de l'enseignant avec contexte département."""
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
    except Ens_Dep.DoesNotExist:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    # Autres départements où l'enseignant enseigne
    ALL_Dep = Ens_Dep.objects.filter(enseignant=enseignant).exclude(
        departement=real_Dep.departement if real_Dep else None
    )

    context = {
        "title": "الملف الشخصي",
        "active_menu": "profile",
        "my_Ens": enseignant,
        "my_Dep": departement,
        "my_Fac": departement.faculte,
        "real_Dep": real_Dep,
        "ALL_Dep": ALL_Dep,
    }
    return render(request, "enseignant/profile_Ens.html", context)


@enseignant_access_required
def profileUpdate_ens_dep(request, dep_id, enseignant, departement):
    """Mise à jour du profil de l'enseignant avec contexte département."""
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
    except Ens_Dep.DoesNotExist:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    if request.method == "POST":
        User_form = UserUpdateForm(request.POST, instance=request.user)
        Ens_form = ProfileUpdateEnsForm(request.POST, instance=enseignant)

        if User_form.is_valid() and Ens_form.is_valid():
            User_form.save()
            Ens_form.save()
            messages.success(request, "تم تحديث المعلومات بنجاح")
            return redirect("ense:profile_ens_dep", dep_id=departement.id)
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج")
    else:
        User_form = UserUpdateForm(instance=request.user)
        Ens_form = ProfileUpdateEnsForm(instance=enseignant)

    context = {
        "title": "تعديل الملف الشخصي",
        "active_menu": "profile",
        "User_form": User_form,
        "Ens_form": Ens_form,
        "my_Ens": enseignant,
        "my_Dep": departement,
        "my_Fac": departement.faculte,
        "real_Dep": real_Dep,
    }
    return render(request, "enseignant/profileUpdate_Ens.html", context)


@enseignant_access_required
def change_password_ens_dep(request, dep_id, enseignant, departement):
    """Changement de mot de passe de l'enseignant avec contexte département."""
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
    except Ens_Dep.DoesNotExist:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Vérifier l'ancien mot de passe
        if not request.user.check_password(old_password):
            messages.error(request, "كلمة المرور الحالية غير صحيحة / Mot de passe actuel incorrect")
        elif new_password != confirm_password:
            messages.error(
                request, "كلمة المرور الجديدة وتأكيدها غير متطابقين / Les mots de passe ne correspondent pas"
            )
        elif len(new_password) < 8:
            messages.error(
                request,
                "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل / Le mot de passe doit contenir au moins 8 caractères",
            )
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès")
            return redirect("ense:profile_ens_dep", dep_id=departement.id)

    context = {
        "title": "تغيير كلمة المرور",
        "active_menu": "profile",
        "my_Ens": enseignant,
        "my_Dep": departement,
        "my_Fac": departement.faculte,
        "real_Dep": real_Dep,
    }
    return render(request, "enseignant/change_password_Ens.html", context)
