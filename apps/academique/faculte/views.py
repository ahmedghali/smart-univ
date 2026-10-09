# apps/academique/faculte/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Length
from django.shortcuts import get_object_or_404, redirect, render

from .forms import profileUpdate_Fac_Form
from .models import Faculte

# ══════════════════════════════════════════════════════════════
# VUES POUR LE TABLEAU DE BORD DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════


def get_user_faculte(user):
    """Faculté où l'utilisateur occupe un poste de direction (doyen ou vice-doyen)."""
    faculte = Faculte.objects.filter(
        affectations_postes__user=user,
        affectations_postes__est_actif=True,
        affectations_postes__poste__code__in=["doyen", "vice_doyen_p", "vice_doyen_pg"],
    ).first()
    if faculte is None and user.is_superuser:
        faculte = Faculte.objects.first()
    return faculte


def get_fac_context(request, faculte):
    """Contexte commun de l'espace faculté (menu latéral, bandeau, poste actif)."""
    from apps.noyau.authentification.constants import ROLE_LABELS
    from apps.noyau.authentification.utils import get_user_roles
    from apps.noyau.commun.models import AnneeUniversitaire

    current_role = request.session.get("current_role", "")
    user_roles = get_user_roles(request.user)
    return {
        "my_Fac": faculte,
        "annee_courante": AnneeUniversitaire.objects.filter(est_courante=True).first(),
        "current_role": current_role,
        "current_role_label": ROLE_LABELS.get(current_role, current_role),
        "user_roles": user_roles,
        "roles_count": len(user_roles),
    }


@login_required
def dashboard_Fac(request):
    """Tableau de bord du doyen : chiffres de la faculté, départements et équipe de direction."""
    from django.db.models import Q
    from django.utils import timezone

    from apps.academique.affectation.models import Amphi_Dep, Ens_Dep, Laboratoire_Dep, Salle_Dep
    from apps.academique.departement.models import Matiere, Specialite
    from apps.academique.etudiant.models import Etudiant
    from apps.noyau.commun.models import AffectationPoste

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك / Aucune faculté liée à votre poste")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    annee = context["annee_courante"]

    departements = []
    totaux = {"enseignants": 0, "etudiants": 0, "specialites": 0, "matieres": 0, "rooms": 0, "amphis": 0, "salles": 0, "labos": 0}
    for dep in my_fac.departements.order_by("nom_ar"):
        amphi_c = Amphi_Dep.objects.filter(departement=dep, est_actif=True).count()
        salle_c = Salle_Dep.objects.filter(departement=dep, est_actif=True).count()
        labo_c = Laboratoire_Dep.objects.filter(departement=dep, est_actif=True).count()
        rooms_c = amphi_c + salle_c + labo_c

        ligne = {
            "dep": dep,
            "enseignants": Ens_Dep.objects.filter(departement=dep, annee_univ=annee, est_actif=True)
            .values("enseignant").distinct().count(),
            "etudiants": Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep__departement=dep).count(),
            "specialites": Specialite.objects.filter(departement=dep).count(),
            "matieres": Matiere.objects.filter(niv_spe_dep__departement=dep).count(),
            "rooms": rooms_c,
            "amphis": amphi_c,
            "salles": salle_c,
            "labos": labo_c,
        }
        for k in totaux:
            totaux[k] += ligne[k]
        departements.append(ligne)

    postes_direction = ["doyen", "vice_doyen_p", "vice_doyen_pg"]
    direction = sorted(
        AffectationPoste.objects.filter(faculte=my_fac, poste__code__in=postes_direction, est_actif=True)
        .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=timezone.localdate()))
        .select_related("poste", "user", "user__enseignant_profile"),
        key=lambda a: postes_direction.index(a.poste.code),
    )

    context.update(
        {
            "title": "لوحة التحكم",
            "active_menu": "dashboard",
            "departements": departements,
            "totaux": totaux,
            "direction": direction,
        }
    )
    return render(request, "faculte/dashboard_Fac.html", context)


@login_required
def list_Specialite_Fac(request):
    """Liste des spécialités et filières de la faculté (الهياكل والمقررات)."""
    from django.db.models import Count
    from apps.academique.departement.models import Specialite

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")

    specialites_qs = Specialite.objects.filter(departement__faculte=my_fac).select_related("departement").annotate(
        nb_matieres=Count("nivspedep__matieres", distinct=True),
        nb_etudiants=Count("nivspedep__sections_groupes__etudiants", distinct=True),
    ).order_by(Length("code"), "code", "id", "departement__nom_ar")

    if dep_id:
        specialites_qs = specialites_qs.filter(departement_id=dep_id)

    context.update(
        {
            "title": "تخصصات الكلية - الهياكل والمقررات",
            "active_menu": "specialites",
            "specialites": specialites_qs,
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
            "total_specialites": specialites_qs.count(),
        }
    )
    return render(request, "faculte/list_Specialite_Fac.html", context)


@login_required
def list_Mat_Fac(request):
    """Liste des matières et modules de la faculté (الهياكل والمقررات) - classée selon le code/numéro."""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from apps.academique.departement.models import Matiere

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")
    query = request.GET.get("q", "").strip()

    matieres_qs = (
        Matiere.objects.filter(niv_spe_dep__departement__faculte=my_fac)
        .select_related(
            "niv_spe_dep__departement",
            "niv_spe_dep__specialite",
            "niv_spe_dep__niveau",
            "semestre",
        )
        .distinct()
        .order_by("semestre__numero", Length("code"), "code", "id", "niv_spe_dep__departement__nom_ar")
    )

    if dep_id:
        matieres_qs = matieres_qs.filter(niv_spe_dep__departement_id=dep_id)
    if query:
        matieres_qs = matieres_qs.filter(
            Q(nom_ar__icontains=query) | Q(nom_fr__icontains=query) | Q(code__icontains=query)
        )

    paginator = Paginator(matieres_qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context.update(
        {
            "title": "المقررات والمواد الدراسية - الهياكل والمقررات",
            "active_menu": "matieres",
            "matieres": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
            "query": query,
            "total_matieres": matieres_qs.count(),
        }
    )
    return render(request, "faculte/list_Mat_Fac.html", context)


@login_required
def infrastructures_Fac(request):
    """Vue des infrastructures (amphis, salles, labos) de la faculté (الهياكل والمقررات) - classée selon le numéro."""
    from apps.academique.affectation.models import Amphi_Dep, Laboratoire_Dep, Salle_Dep

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")

    amphis_qs = Amphi_Dep.objects.filter(departement__faculte=my_fac).select_related("amphi", "departement").order_by(Length("amphi__numero"), "amphi__numero", "departement__nom_ar")
    salles_qs = Salle_Dep.objects.filter(departement__faculte=my_fac).select_related("salle", "departement").order_by(Length("salle__numero"), "salle__numero", "departement__nom_ar")
    labos_qs = Laboratoire_Dep.objects.filter(departement__faculte=my_fac).select_related("laboratoire", "departement").order_by(Length("laboratoire__numero"), "laboratoire__numero", "departement__nom_ar")

    if dep_id:
        amphis_qs = amphis_qs.filter(departement_id=dep_id)
        salles_qs = salles_qs.filter(departement_id=dep_id)
        labos_qs = labos_qs.filter(departement_id=dep_id)

    total_amphis = amphis_qs.count()
    total_salles = salles_qs.count()
    total_labos = labos_qs.count()
    total_rooms = total_amphis + total_salles + total_labos

    capacite_amphis = sum(a.amphi.capacite or 0 for a in amphis_qs)
    capacite_salles = sum(s.salle.capacite or 0 for s in salles_qs)
    capacite_labos = sum(l.laboratoire.capacite or 0 for l in labos_qs)
    capacite_totale = capacite_amphis + capacite_salles + capacite_labos

    context.update(
        {
            "title": "هياكل وقاعات الكلية - الهياكل والمقررات",
            "active_menu": "infrastructures",
            "amphis": amphis_qs,
            "salles": salles_qs,
            "labos": labos_qs,
            "total_amphis": total_amphis,
            "total_salles": total_salles,
            "total_labos": total_labos,
            "total_rooms": total_rooms,
            "capacite_totale": capacite_totale,
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
        }
    )
    return render(request, "faculte/infrastructures_Fac.html", context)


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
        if faculte_id:
            my_fac = get_object_or_404(Faculte, id=faculte_id)
        else:
            facultes = Faculte.objects.all()
            if facultes.exists():
                my_fac = get_user_faculte(request.user)
            else:
                messages.warning(request, "لا توجد كليات متاحة / Aucune faculté disponible")
                return redirect("comm:home")

        context = get_fac_context(request, my_fac)
        context.update({"title": "بطاقة الكلية", "active_menu": "profile"})
        return render(request, "faculte/profile_Fac.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@login_required
def profileUpdate_Fac(request, faculte_id=None):
    """
    Mise à jour du profil de la faculté.
    Permet au doyen de modifier les informations de contact et autres détails.

    TODO: Update this view when Ens_Dep and Departement models are ready.
    For now, accepts faculte_id as parameter or updates first faculty.
    """
    try:
        if faculte_id:
            my_fac = get_object_or_404(Faculte, id=faculte_id)
        else:
            facultes = Faculte.objects.all()
            if facultes.exists():
                my_fac = get_user_faculte(request.user)
            else:
                messages.warning(request, "لا توجد كليات متاحة / Aucune faculté disponible")
                return redirect("comm:home")

        if request.method == "POST":
            Fac_form = profileUpdate_Fac_Form(request.POST, request.FILES, instance=my_fac)

            if Fac_form.is_valid():
                Fac_form.save()
                messages.success(request, "تم تحديث المعلومات بنجاح / Informations mises à jour avec succès")
                return redirect("faculte:profile_Fac")
            else:
                messages.error(request, "خطأ في النموذج / Erreur dans le formulaire")
        else:
            Fac_form = profileUpdate_Fac_Form(instance=my_fac)

        context = get_fac_context(request, my_fac)
        context.update({"title": "تعديل بطاقة الكلية", "active_menu": "profile", "Fac_form": Fac_form})
        return render(request, "faculte/profileUpdate_Fac.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


# ══════════════════════════════════════════════════════════════
# DÉPARTEMENTS DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

@login_required
def list_departements_fac(request):
    """Liste complète des départements de la faculté avec statistiques et liens."""
    from apps.academique.affectation.models import Amphi_Dep, Ens_Dep, Laboratoire_Dep, Salle_Dep
    from apps.academique.departement.models import Matiere, Specialite
    from apps.academique.etudiant.models import Etudiant
    from apps.noyau.commun.models import AffectationPoste

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    annee = context["annee_courante"]

    departements_data = []
    totaux = {"enseignants": 0, "etudiants": 0, "specialites": 0, "matieres": 0, "rooms": 0, "amphis": 0, "salles": 0, "labos": 0}

    for dep in my_fac.departements.order_by("nom_ar"):
        amphi_c = Amphi_Dep.objects.filter(departement=dep, est_actif=True).count()
        salle_c = Salle_Dep.objects.filter(departement=dep, est_actif=True).count()
        labo_c = Laboratoire_Dep.objects.filter(departement=dep, est_actif=True).count()
        rooms_c = amphi_c + salle_c + labo_c

        chef_aff = AffectationPoste.objects.filter(
            departement=dep, poste__code="chef_departement", est_actif=True
        ).select_related("user", "user__enseignant_profile").first()

        nb_ens = Ens_Dep.objects.filter(departement=dep, annee_univ=annee, est_actif=True).values("enseignant").distinct().count()
        nb_etu = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep__departement=dep).count()
        nb_spe = Specialite.objects.filter(departement=dep).count()
        nb_mat = Matiere.objects.filter(niv_spe_dep__departement=dep).count()

        item = {
            "dep": dep,
            "chef": chef_aff,
            "enseignants": nb_ens,
            "etudiants": nb_etu,
            "specialites": nb_spe,
            "matieres": nb_mat,
            "rooms": rooms_c,
            "amphis": amphi_c,
            "salles": salle_c,
            "labos": labo_c,
        }
        for k in ["enseignants", "etudiants", "specialites", "matieres", "rooms", "amphis", "salles", "labos"]:
            totaux[k] += item[k]
        departements_data.append(item)

    context.update(
        {
            "title": "أقسام الكلية",
            "active_menu": "departements",
            "departements_data": departements_data,
            "totaux": totaux,
            "total_departements": len(departements_data),
        }
    )
    return render(request, "faculte/list_departements_fac.html", context)


# ══════════════════════════════════════════════════════════════
# ENSEIGNANTS DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

@login_required
def list_enseignants_fac(request, semestre_num=1):
    """Liste de tous les enseignants des départements de la faculté."""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from apps.academique.affectation.models import Ens_Dep

    if semestre_num not in [1, 2]:
        return redirect("facu:list_enseignants_fac", semestre_num=1)

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    annee = context["annee_courante"]
    dep_id = request.GET.get("dep")
    statut_filter = request.GET.get("statut")
    search = request.GET.get("q", "").strip()

    sem_filter = {f"semestre_{semestre_num}": True}
    qs = Ens_Dep.objects.filter(
        departement__faculte=my_fac, annee_univ=annee, est_actif=True, **sem_filter
    ).select_related("enseignant", "enseignant__grade", "enseignant__diplome", "enseignant__user", "departement")

    if dep_id and dep_id.isdigit():
        qs = qs.filter(departement_id=int(dep_id))
    if statut_filter:
        qs = qs.filter(statut=statut_filter)
    if search:
        qs = qs.filter(
            Q(enseignant__nom_ar__icontains=search)
            | Q(enseignant__prenom_ar__icontains=search)
            | Q(enseignant__nom_fr__icontains=search)
            | Q(enseignant__prenom_fr__icontains=search)
            | Q(enseignant__matricule__icontains=search)
        )

    # Statistiques globales
    base_qs = Ens_Dep.objects.filter(departement__faculte=my_fac, annee_univ=annee, est_actif=True, **sem_filter)
    total_enseignants = base_qs.values("enseignant").distinct().count()
    permanents_count = base_qs.filter(statut="Permanent").values("enseignant").distinct().count()
    vacataires_count = base_qs.filter(statut__in=["Vacataire", "Permanent & Vacataire"]).values("enseignant").distinct().count()
    associes_count = base_qs.filter(statut="Associe").values("enseignant").distinct().count()

    paginator = Paginator(qs.order_by("departement__nom_ar", "enseignant__nom_ar"), 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context.update(
        {
            "title": f"قائمة أساتذة الكلية - السداسي {semestre_num}",
            "active_menu": "enseignants",
            "semestre_num": semestre_num,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
            "statut_filter": statut_filter,
            "search": search,
            "total_enseignants": total_enseignants,
            "permanents_count": permanents_count,
            "vacataires_count": vacataires_count,
            "associes_count": associes_count,
        }
    )
    return render(request, "faculte/list_enseignants_fac.html", context)


@login_required
def heures_enseignants_fac(request, semestre=1):
    """Vue des heures de travail des enseignants de la faculté par semestre."""
    from apps.academique.affectation.models import Ens_Dep

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    annee = context["annee_courante"]
    dep_id = request.GET.get("dep")

    filter_kwargs = {
        "departement__faculte": my_fac,
        "annee_univ": annee,
        f"semestre_{semestre}": True,
        "est_actif": True,
    }
    if dep_id and dep_id.isdigit():
        filter_kwargs["departement_id"] = int(dep_id)

    enseignants = Ens_Dep.objects.filter(**filter_kwargs).select_related(
        "enseignant", "enseignant__user", "enseignant__grade", "departement"
    ).order_by("departement__nom_ar", "enseignant__nom_ar")

    context.update(
        {
            "title": f"ساعات العمل والأنصبة - السداسي {semestre}",
            "active_menu": "heures",
            "enseignants": enseignants,
            "semestre": semestre,
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
        }
    )
    return render(request, "faculte/heures_enseignants_fac.html", context)


# ══════════════════════════════════════════════════════════════
# ÉTUDIANTS DE LA FACULTÉ
# ══════════════════════════════════════════════════════════════

@login_required
def list_etudiants_fac(request):
    """Liste complète des étudiants de la faculté avec pagination et filtres."""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from apps.academique.etudiant.models import Etudiant

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")
    search = request.GET.get("q", "").strip()

    etudiants_qs = Etudiant.objects.filter(
        niv_spe_dep_sg__niv_spe_dep__departement__faculte=my_fac
    ).select_related(
        "niv_spe_dep_sg__niv_spe_dep__departement",
        "niv_spe_dep_sg__niv_spe_dep__specialite",
        "niv_spe_dep_sg__niv_spe_dep__niveau",
    ).distinct()

    if dep_id and dep_id.isdigit():
        etudiants_qs = etudiants_qs.filter(niv_spe_dep_sg__niv_spe_dep__departement_id=int(dep_id))
    if search:
        etudiants_qs = etudiants_qs.filter(
            Q(nom_ar__icontains=search)
            | Q(prenom_ar__icontains=search)
            | Q(nom_fr__icontains=search)
            | Q(prenom_fr__icontains=search)
            | Q(matricule__icontains=search)
        )

    total_etudiants = Etudiant.objects.filter(
        niv_spe_dep_sg__niv_spe_dep__departement__faculte=my_fac
    ).distinct().count()

    paginator = Paginator(etudiants_qs.order_by("niv_spe_dep_sg__niv_spe_dep__departement__nom_ar", "nom_ar"), 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context.update(
        {
            "title": "قوائم طلبة الكلية",
            "active_menu": "etudiants",
            "etudiants": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
            "search": search,
            "total_etudiants": total_etudiants,
        }
    )
    return render(request, "faculte/list_etudiants_fac.html", context)


@login_required
def import_etudiants_fac(request):
    """Import groupé d'étudiants pour la faculté."""
    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    if request.method == "POST":
        messages.info(request, "يرجى استخدام بوابة المشرف الإداري للكلية للاستيراد المتقدم للطلبة.")
        return redirect("/faculte/admin/etudiant/etudiant/import/")

    context = get_fac_context(request, my_fac)
    context.update(
        {
            "title": "استيراد الطلبة - الكلية",
            "active_menu": "import_etudiants",
            "departements": my_fac.departements.order_by("nom_ar"),
        }
    )
    return render(request, "faculte/import_etudiants_fac.html", context)


# ══════════════════════════════════════════════════════════════
# INFRASTRUCTURES DÉDIÉES (AMPHIS, SALLES, LABOS)
# ══════════════════════════════════════════════════════════════

@login_required
def list_Amphi_Fac(request):
    """Liste détaillée des مدرجات de la faculté."""
    from apps.academique.affectation.models import Amphi_Dep

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")

    qs = Amphi_Dep.objects.filter(departement__faculte=my_fac).select_related("amphi", "departement").order_by(Length("amphi__numero"), "amphi__numero", "departement__nom_ar")
    if dep_id and dep_id.isdigit():
        qs = qs.filter(departement_id=int(dep_id))

    total = qs.count()
    amphis_s1 = qs.filter(semestre_1=True).count()
    amphis_s2 = qs.filter(semestre_2=True).count()
    capacite = sum(a.amphi.capacite or 0 for a in qs)

    context.update(
        {
            "title": "مدرجات الكلية - الهياكل والمقررات",
            "active_menu": "amphis",
            "amphis": qs,
            "total_amphis": total,
            "amphis_s1": amphis_s1,
            "amphis_s2": amphis_s2,
            "capacite_totale": capacite,
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
        }
    )
    return render(request, "faculte/list_Amphi_Fac.html", context)


@login_required
def list_Salle_Fac(request):
    """Liste détaillée des قاعات de la faculté - classée selon le numéro."""
    from apps.academique.affectation.models import Salle_Dep

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")

    qs = Salle_Dep.objects.filter(departement__faculte=my_fac).select_related("salle", "departement").order_by(Length("salle__numero"), "salle__numero", "departement__nom_ar")
    if dep_id and dep_id.isdigit():
        qs = qs.filter(departement_id=int(dep_id))

    total = qs.count()
    salles_s1 = qs.filter(semestre_1=True).count()
    salles_s2 = qs.filter(semestre_2=True).count()
    capacite = sum(s.salle.capacite or 0 for s in qs)

    context.update(
        {
            "title": "القاعات الدراسية بالكلية - الهياكل والمقررات",
            "active_menu": "salles",
            "salles": qs,
            "total_salles": total,
            "salles_s1": salles_s1,
            "salles_s2": salles_s2,
            "capacite_totale": capacite,
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
        }
    )
    return render(request, "faculte/list_Salle_Fac.html", context)


@login_required
def list_Labo_Fac(request):
    """Liste détaillée des مخابر de la faculté - classée selon le numéro."""
    from apps.academique.affectation.models import Laboratoire_Dep

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)
    dep_id = request.GET.get("dep")

    qs = Laboratoire_Dep.objects.filter(departement__faculte=my_fac).select_related("laboratoire", "departement").order_by(Length("laboratoire__numero"), "laboratoire__numero", "departement__nom_ar")
    if dep_id and dep_id.isdigit():
        qs = qs.filter(departement_id=int(dep_id))

    total = qs.count()
    labos_s1 = qs.filter(semestre_1=True).count()
    labos_s2 = qs.filter(semestre_2=True).count()
    capacite = sum(l.laboratoire.capacite or 0 for l in qs)

    context.update(
        {
            "title": "مخابر الأعمال التطبيقية بالكلية - الهياكل والمقررات",
            "active_menu": "labos",
            "labos": qs,
            "total_labos": total,
            "labos_s1": labos_s1,
            "labos_s2": labos_s2,
            "capacite_totale": capacite,
            "departements": my_fac.departements.order_by("nom_ar"),
            "selected_dep": int(dep_id) if dep_id and dep_id.isdigit() else None,
        }
    )
    return render(request, "faculte/list_Labo_Fac.html", context)


# ══════════════════════════════════════════════════════════════
# CHANGEMENT DE MOT DE PASSE DU DOYEN
# ══════════════════════════════════════════════════════════════

@login_required
def change_password_Fac(request):
    """Permet au doyen ou membre de la direction de la faculté de modifier son mot de passe."""
    from django.contrib.auth import update_session_auth_hash

    my_fac = get_user_faculte(request.user)
    if my_fac is None:
        messages.error(request, "لا توجد كلية مرتبطة بمنصبك")
        return redirect("auth:select_role")

    context = get_fac_context(request, my_fac)

    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

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
            return redirect("facu:profile_Fac")

    context.update(
        {
            "title": "تغيير كلمة المرور",
            "active_menu": "change_password",
        }
    )
    return render(request, "faculte/change_password_Fac.html", context)

