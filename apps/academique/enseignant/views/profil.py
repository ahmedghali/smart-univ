from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import Ens_Dep
from apps.noyau.authentification.decorators import enseignant_access_required

from ..forms import ProfileUpdateEnsForm, UserUpdateForm
from ..models import Enseignant
from ..services import get_departement_from_session_or_enseignant, get_real_department, get_sidebar_context


@login_required
def profile_Ens(request, enseignant_id=None):
    """
    Affichage du profil de l'enseignant.
    Montre toutes les informations détaillées de l'enseignant.
    """
    try:
        if enseignant_id:
            enseignant = get_object_or_404(Enseignant, id=enseignant_id)
        else:
            enseignant = request.user.enseignant_profile

        # Récupérer le département principal (Permanent / Tâches principales)
        real_Dep = get_real_department(enseignant)
        primary_dep = real_Dep.departement if real_Dep else None

        # Département pour le menu contextuel (session s'il existe, sinon département principal)
        departement = get_departement_from_session_or_enseignant(request, enseignant)
        if not departement and primary_dep:
            departement = primary_dep

        # Autres départements où l'enseignant enseigne (exclure le département d'origine principal)
        if primary_dep:
            ALL_Dep = (
                Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True)
                .exclude(departement=primary_dep)
                .select_related("departement", "departement__faculte")
            )
        elif departement:
            ALL_Dep = (
                Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True)
                .exclude(departement=departement)
                .select_related("departement", "departement__faculte")
            )
        else:
            ALL_Dep = []

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "الملف الشخصي",
                "active_menu": "profile",
                "enseignant": enseignant,
                "real_Dep": real_Dep,
                "ALL_Dep": ALL_Dep,
            }
        )
        return render(request, "enseignant/profile_Ens.html", context)

    except Enseignant.DoesNotExist:
        messages.error(request, "لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable")
        return redirect("comm:home")
    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@login_required
def profileUpdate_Ens(request, enseignant_id=None):
    """
    Mise à jour du profil de l'enseignant.
    Permet à l'enseignant de modifier ses informations personnelles et de contact.
    """
    try:
        if enseignant_id:
            enseignant = get_object_or_404(Enseignant, id=enseignant_id)
            target_user = enseignant.user
        else:
            enseignant = request.user.enseignant_profile
            target_user = request.user

        # Vérification des autorisations : propriétaire, superuser ou responsable administratif
        from apps.noyau.commun.models import AffectationPoste
        is_owner = bool(enseignant.user and request.user == enseignant.user)
        is_admin = request.user.is_superuser
        has_post = AffectationPoste.actives(request.user).filter(
            poste__code__in=["chef_dep", "doyen", "vice_doyen_p", "vice_doyen_pg", "recteur"]
        ).exists()

        if not (is_owner or is_admin or has_post):
            messages.error(request, "غير مصرح لك بتعديل هذا الملف الشخصي / Vous n'êtes pas autorisé à modifier ce profil.")
            if enseignant_id:
                return redirect("ense:profile_Ens_id", enseignant_id=enseignant.id)
            return redirect("ense:profile_Ens")

        # Récupérer le département principal
        real_Dep = get_real_department(enseignant)

        # Département: session d'abord, puis affectation
        departement = get_departement_from_session_or_enseignant(request, enseignant)
        if not departement and real_Dep:
            departement = real_Dep.departement

        if request.method == "POST":
            User_form = UserUpdateForm(request.POST, instance=target_user) if target_user else None
            Ens_form = ProfileUpdateEnsForm(request.POST, request.FILES, instance=enseignant)

            user_valid = User_form.is_valid() if User_form else True
            if user_valid and Ens_form.is_valid():
                if User_form:
                    User_form.save()
                Ens_form.save()
                messages.success(request, f"تم تحديث بيانات الأستاذ ({enseignant.nom_ar} {enseignant.prenom_ar}) بنجاح")

                # Lien Google Scholar ajouté ou modifié : mise à jour automatique des indicateurs
                if "googlescholar" in Ens_form.changed_data:
                    if enseignant.googlescholar:
                        from ..services import fetch_and_update_scholar

                        res = fetch_and_update_scholar(enseignant)
                        (messages.success if res.get("success") else messages.warning)(request, res.get("message", ""))
                    else:
                        enseignant.scholar_publications_count = 0
                        enseignant.scholar_citations_count = 0
                        enseignant.scholar_h_index = 0
                        enseignant.scholar_i10_index = 0
                        enseignant.save(
                            update_fields=[
                                "scholar_publications_count",
                                "scholar_citations_count",
                                "scholar_h_index",
                                "scholar_i10_index",
                            ]
                        )
                if enseignant_id:
                    return redirect("ense:profile_Ens_id", enseignant_id=enseignant.id)
                return redirect("ense:profile_Ens")
            else:
                messages.error(request, "يرجى تصحيح الأخطاء في النموذج")
        else:
            User_form = UserUpdateForm(instance=target_user) if target_user else None
            Ens_form = ProfileUpdateEnsForm(instance=enseignant)

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": f"تعديل الملف الشخصي - {enseignant.nom_ar} {enseignant.prenom_ar}",
                "active_menu": "profile",
                "enseignant": enseignant,
                "real_Dep": real_Dep,
                "User_form": User_form,
                "Ens_form": Ens_form,
            }
        )
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
        real_Dep = get_real_department(enseignant)

        # Département: session d'abord, puis affectation
        departement = get_departement_from_session_or_enseignant(request, enseignant)
        if not departement and real_Dep:
            departement = real_Dep.departement

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
                request.user.doit_changer_mot_de_passe = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès")
                return redirect("ense:profile_Ens")

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "تغيير كلمة المرور",
                "active_menu": "profile",
                "enseignant": enseignant,
                "real_Dep": real_Dep,
            }
        )
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
    real_Dep = get_real_department(enseignant)

    # Autres départements où l'enseignant enseigne
    ALL_Dep = Ens_Dep.objects.filter(enseignant=enseignant).exclude(
        departement=real_Dep.departement if real_Dep else None
    )

    # Contexte avec sidebar commun
    context = get_sidebar_context(request, enseignant, departement)
    context.update(
        {
            "title": "الملف الشخصي",
            "active_menu": "profile",
            "real_Dep": real_Dep,
            "ALL_Dep": ALL_Dep,
        }
    )
    return render(request, "enseignant/profile_Ens.html", context)


@login_required
def profileUpdate_ens_dep(request, dep_id, **kwargs):
    """Redirection de compatibilité vers la mise à jour du profil enseignant."""
    ens = Enseignant.objects.filter(id=dep_id).first()
    if ens:
        return redirect("ense:profileUpdate_Ens_id", enseignant_id=ens.id)
    enseignant = getattr(request.user, "enseignant_profile", None)
    if enseignant:
        return redirect("ense:profileUpdate_Ens_id", enseignant_id=enseignant.id)
    return redirect("ense:profileUpdate_Ens")


@enseignant_access_required
def change_password_ens_dep(request, dep_id, enseignant, departement):
    """Changement de mot de passe de l'enseignant avec contexte département."""
    real_Dep = get_real_department(enseignant)

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
            request.user.doit_changer_mot_de_passe = False
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès")
            return redirect("ense:profile_ens_dep", dep_id=departement.id)

    # Contexte avec sidebar commun
    context = get_sidebar_context(request, enseignant, departement)
    context.update(
        {
            "title": "تغيير كلمة المرور",
            "active_menu": "profile",
            "real_Dep": real_Dep,
        }
    )
    return render(request, "enseignant/change_password_Ens.html", context)


@login_required
def update_scholar_ens(request, enseignant_id=None):
    """Met à jour les métriques Google Scholar pour l'enseignant connecté ou ciblé."""
    from django.http import JsonResponse
    from ..services import fetch_and_update_scholar

    if enseignant_id and (request.user.is_superuser or request.user.is_staff):
        enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    else:
        enseignant = getattr(request.user, "enseignant_profile", None)
        if not enseignant and enseignant_id:
            enseignant = get_object_or_404(Enseignant, id=enseignant_id)

    if not enseignant:
        return JsonResponse({"success": False, "message": "ملف الأستاذ غير موجود."})

    res = fetch_and_update_scholar(enseignant)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json"
    if is_ajax:
        return JsonResponse(res)

    if res.get("success"):
        messages.success(request, res.get("message"))
    else:
        messages.warning(request, res.get("message"))

    return redirect(request.META.get("HTTP_REFERER", "ense:profile_Ens"))

