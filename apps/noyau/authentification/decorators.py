# apps/noyau/authentification/decorators.py

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect

from apps.academique.affectation.models import Ens_Dep
from apps.academique.departement.models import Departement
from apps.academique.etudiant.models import Etudiant


def enseignant_access_required(view_func):
    """
    Décorateur pour vérifier l'accès enseignant à un département.

    Injecte automatiquement 'enseignant' et 'departement' dans les kwargs de la vue.
    Vérifie que l'enseignant est bien inscrit au département demandé.
    Redirige avec élégance vers son département actif au lieu d'une erreur 404 brute.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        dep_id = kwargs.get("id") or kwargs.get("dep_id")

        try:
            # Récupérer le profil enseignant de l'utilisateur
            enseignant = getattr(user, "enseignant_profile", None)
            if not enseignant:
                messages.error(request, "لا يوجد ملف تعريف للأستاذ مرتبط بهذا الحساب / Aucun profil enseignant associé")
                return redirect("comm:home")

            # Si dep_id n'est pas dans l'URL (URL propre sans ID), le récupérer de la session ou de l'affectation active
            if not dep_id:
                dep_id = request.session.get("selected_departement_id")
            if not dep_id:
                ens_dep_first = Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True).first()
                if ens_dep_first:
                    dep_id = ens_dep_first.departement_id
                elif getattr(enseignant, "departement_id", None):
                    dep_id = enseignant.departement_id

            departement = None

            if dep_id:
                # Vérifier l'affectation et l'inscription active
                ens_dep = Ens_Dep.objects.filter(enseignant=enseignant, departement_id=dep_id, est_actif=True).first()
                if not ens_dep:
                    # Trouver le département principal ou actif de l'enseignant
                    valid_dep = Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True).first()
                    try:
                        target_dep = Departement.objects.filter(id=dep_id).first()
                        target_name = f"« {target_dep.nom_ar} »" if target_dep else f"(ID: {dep_id})"
                    except Exception:
                        target_name = f"(ID: {dep_id})"

                    messages.warning(
                        request,
                        f"غير مصرح لك بالوصول إلى قسم {target_name} لأنك غير مسجل به. تم توجيهك إلى قسمك المعتمد."
                    )
                    if valid_dep:
                        request.session["selected_departement_id"] = valid_dep.departement_id
                        return redirect("ense:dashboard_Ens_clean")
                    return redirect("ense:profile_Ens")

                departement = Departement.objects.get(id=dep_id)
                request.session["selected_departement_id"] = departement.id

            # Injecter enseignant et departement dans les kwargs
            kwargs["dep_id"] = dep_id
            kwargs["enseignant"] = enseignant
            kwargs["departement"] = departement
            return view_func(request, *args, **kwargs)
        except Departement.DoesNotExist:
            messages.error(request, f"القسم غير موجود (المعرف: {dep_id})")
            return redirect("ense:profile_Ens")
        except Exception as e:
            messages.error(request, f"خطأ: {str(e)}")
            return redirect("ense:profile_Ens")

    return wrapper


def etudiant_access_required(view_func):
    """
    Décorateur pour vérifier l'accès étudiant.

    Injecte automatiquement 'etudiant' et 'departement' dans les kwargs de la vue.
    Vérifie que l'étudiant est bien inscrit.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        try:
            # Récupérer le profil étudiant de l'utilisateur
            etudiant = getattr(user, "etudiant_profile", None)
            if not etudiant:
                raise Http404("Vous n'êtes pas autorisé à accéder à cette page. (Pas d'étudiant lié)")

            # Récupérer l'ID du département depuis le profil étudiant
            dep_id = etudiant.niv_spe_dep_sg.niv_spe_dep.departement.id
            departement = None

            if dep_id:
                # Vérifier l'inscription de l'étudiant (est_actif au lieu de est_inscrit)
                etu_dep = Etudiant.objects.filter(
                    id=etudiant.id,
                    est_actif=True,  # Champ correspondant dans le modèle Etudiant
                ).first()
                if not etu_dep:
                    raise Http404(f"Vous n'êtes pas autorisé à accéder à ce département. (ID : {dep_id}, non actif)")
                departement = Departement.objects.get(id=dep_id)

            # Injecter etudiant et departement dans les kwargs
            kwargs["etudiant"] = etudiant
            kwargs["departement"] = departement
            return view_func(request, *args, **kwargs)
        except Departement.DoesNotExist:
            raise Http404("Département non trouvé.")
        except Exception as e:
            raise Http404(f"Erreur : {str(e)}")

    return wrapper
