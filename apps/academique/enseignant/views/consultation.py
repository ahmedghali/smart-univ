import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Min
from django.db.models.functions import Length
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import (
    Classe,
    Ens_Dep,
)
from apps.academique.departement.models import Matiere, NivSpeDep, NivSpeDep_SG, Specialite
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import AnneeUniversitaire, Semestre

from ..models import Enseignant
from ..services import _safe_str, get_sidebar_context


@login_required
def list_Ens(request):
    """
    Liste des enseignants accessible uniquement aux utilisateurs autorisés du département (A06).
    """
    from django.core.exceptions import PermissionDenied

    from apps.noyau.authentification.utils import get_active_departement
    from apps.noyau.commun.models import PostePermission

    perms = PostePermission.get_permissions(request)
    is_super = request.user.is_superuser
    has_perm = perms.get("enseignant_view", False)

    if not is_super and not has_perm:
        raise PermissionDenied("Vous n'avez pas la permission de consulter la liste des enseignants.")

    dep = get_active_departement(request)
    if not is_super and not dep:
        raise PermissionDenied("Aucun département actif sélectionné.")

    try:
        enseignants = Enseignant.objects.select_related("user", "grade", "diplome", "wilaya")
        if not is_super:
            enseignants = enseignants.filter(ens_dep__departement=dep).distinct()

        context = {
            "title": "قائمة الأساتذة / Liste des enseignants",
            "enseignants": enseignants,
        }
        return render(request, "enseignant/list_Ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@login_required
def detail_Ens(request, enseignant_id):
    """
    Détails complets d'un enseignant (A06).
    """
    from django.core.exceptions import PermissionDenied

    from apps.noyau.authentification.utils import get_active_departement
    from apps.noyau.commun.models import PostePermission

    enseignant = get_object_or_404(
        Enseignant.objects.select_related("user", "grade", "diplome", "wilaya"), id=enseignant_id
    )

    is_self = (
        hasattr(request.user, "enseignant_profile")
        and request.user.enseignant_profile
        and request.user.enseignant_profile.id == enseignant.id
    )

    if not is_self and not request.user.is_superuser:
        perms = PostePermission.get_permissions(request)
        if not perms.get("enseignant_view", False):
            raise PermissionDenied("Vous n'avez pas la permission de consulter ce profil enseignant.")

        dep = get_active_departement(request)
        if not dep or not Ens_Dep.objects.filter(enseignant=enseignant, departement=dep).exists():
            raise PermissionDenied("Cet enseignant n'appartient pas à votre département.")

    try:
        context = {
            "title": f"تفاصيل الأستاذ / Détails enseignant - {enseignant.get_nom_complet()}",
            "enseignant": enseignant,
        }
        return render(request, "enseignant/detail_Ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("comm:home")


@enseignant_access_required
def list_enseignants_ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des enseignants du département par semestre.
    Version simplifiée pour les enseignants.
    """
    try:
        # Récupérer l'année universitaire courante
        annee_courante = AnneeUniversitaire.get_courante()

        if not annee_courante:
            messages.warning(request, "لا توجد سنة جامعية محددة كسنة حالية")
            # Continuer sans filtrer par année

        # Récupérer le paramètre semestre (par défaut 1)
        semestre_num = int(request.GET.get("semestre", "1"))
        if semestre_num not in [1, 2]:
            semestre_num = 1

        # Construire le filtre dynamique pour le semestre
        filter_kwargs = {
            "departement": departement,
        }

        # Ajouter le filtre année si disponible
        if annee_courante:
            filter_kwargs["annee_univ"] = annee_courante

        # Ajouter le filtre semestre
        if semestre_num == 1:
            filter_kwargs["semestre_1"] = True
        else:
            filter_kwargs["semestre_2"] = True

        # Récupérer tous les enseignants du département
        all_Ens_Dep = Ens_Dep.objects.filter(**filter_kwargs).select_related(
            "enseignant__grade", "enseignant__user", "enseignant"
        )

        # Calculer les taux d'avancement pour le semestre sélectionné
        try:
            semestre_obj = Semestre.objects.get(numero=str(semestre_num))
        except Semestre.DoesNotExist:
            semestre_obj = None

        for ens_dep in all_Ens_Dep:
            # Filtrer les classes de cet enseignant dans ce département
            classes_filter = {
                "enseignant__enseignant": ens_dep.enseignant,
                "enseignant__departement": departement,
            }
            if semestre_obj:
                classes_filter["semestre"] = semestre_obj

            classes = Classe.objects.filter(**classes_filter)

            if classes.exists():
                stats = classes.aggregate(taux_min=Min("taux_avancement"), taux_moy=Avg("taux_avancement"))
                ens_dep.taux_min_display = int(stats.get("taux_min") or 0)
                ens_dep.taux_moy_display = round(stats.get("taux_moy") or 0, 1)
            else:
                ens_dep.taux_min_display = 0
                ens_dep.taux_moy_display = 0.0

        # Tri personnalisé: statut puis nom alphabétique
        statut_order = {"Permanent": 1, "Permanent & Vacataire": 2, "Vacataire": 3, "Associe": 4, "Doctorant": 5}

        all_Ens_Dep_sorted = sorted(
            all_Ens_Dep,
            key=lambda x: (statut_order.get(x.statut, 99), x.enseignant.nom_ar or "", x.enseignant.prenom_ar or ""),
        )

        # Statistiques
        total_enseignants = len(all_Ens_Dep_sorted)
        count_per = len([x for x in all_Ens_Dep_sorted if x.statut == "Permanent"])
        count_temp = len([x for x in all_Ens_Dep_sorted if x.statut != "Permanent"])
        count_scholar = len([x for x in all_Ens_Dep_sorted if x.enseignant.googlescholar])

        # Statistiques par grade
        grade_stats = all_Ens_Dep.values("enseignant__grade__nom_ar").annotate(count=Count("id")).order_by("-count")

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "قائمة الأساتذة",
                "active_menu": "enseignants",
                "annee_courante": annee_courante,
                "semestre_num": semestre_num,
                "all_Ens_Dep": all_Ens_Dep_sorted,
                "total_enseignants": total_enseignants,
                "count_per": count_per,
                "count_temp": count_temp,
                "count_scholar": count_scholar,
                "grade_stats": grade_stats,
            }
        )

        return render(request, "enseignant/list_enseignants_ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ في تحميل قائمة الأساتذة: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def list_Etudiant_Ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des étudiants du département.
    Gère les requêtes POST pour le filtrage AJAX des étudiants.
    """
    if request.method == "POST":
        niv_spe_dep_sg_id = request.POST.get("niv_spe_dep_sg")

        if niv_spe_dep_sg_id:
            # Cas 1: Tous les étudiants d'un niveau
            if niv_spe_dep_sg_id.startswith("tous_"):
                parts = niv_spe_dep_sg_id.replace("tous_", "").split("_")
                niveau_id = parts[0]
                reforme_id = parts[1] if len(parts) > 1 else None

                # Filtres pour tous les groupes du niveau
                groupes_filters = {"niv_spe_dep__departement": departement, "niv_spe_dep__niveau_id": niveau_id}
                if reforme_id:
                    groupes_filters["niv_spe_dep__specialite__reforme_id"] = reforme_id

                # Récupérer TOUS les NivSpeDep_SG (sans exclure les sections)
                # car les étudiants peuvent être assignés à n'importe quel type
                groupes_niveau = NivSpeDep_SG.objects.filter(**groupes_filters).values_list("id", flat=True)

                etudiants_qs = (
                    Etudiant.objects.filter(niv_spe_dep_sg_id__in=groupes_niveau)
                    .select_related("niv_spe_dep_sg__section", "niv_spe_dep_sg__groupe")
                    .distinct()
                    .order_by("nom_ar")
                )

                etudiants = []
                for e in etudiants_qs:
                    etudiants.append(
                        {
                            "id": e.id,
                            "nom_ar": e.nom_ar,
                            "prenom_ar": e.prenom_ar,
                            "nom_fr": e.nom_fr,
                            "prenom_fr": e.prenom_fr,
                            "matricule": e.matricule,
                            "est_inscrit": e.est_inscrit,
                            "tel_mobile1": e.tel_mobile1,
                            "email_prof": e.email_prof,
                            "date_nais": str(e.date_nais) if e.date_nais else None,
                            "section_nom": e.niv_spe_dep_sg.section.nom_ar
                            if e.niv_spe_dep_sg and e.niv_spe_dep_sg.section
                            else None,
                            "groupe_nom": e.niv_spe_dep_sg.groupe.nom_ar
                            if e.niv_spe_dep_sg and e.niv_spe_dep_sg.groupe
                            else None,
                        }
                    )

            # Cas 2: Tous les étudiants d'une section
            elif niv_spe_dep_sg_id.startswith("section_"):
                parts = niv_spe_dep_sg_id.replace("section_", "").split("_")
                section_name = parts[0]
                reforme_id = parts[1] if len(parts) > 1 else None

                # Filtres pour la section - inclure aussi les sections conteneurs
                section_filters = {
                    "niv_spe_dep__departement": departement,
                    "section__nom_ar": section_name,
                    "section__isnull": False,
                }
                if reforme_id:
                    section_filters["niv_spe_dep__specialite__reforme_id"] = reforme_id

                groupes_section = NivSpeDep_SG.objects.filter(**section_filters)
                groupes_ids = list(groupes_section.values_list("id", flat=True))

                etudiants_qs = (
                    Etudiant.objects.filter(niv_spe_dep_sg_id__in=groupes_ids)
                    .select_related("niv_spe_dep_sg__section", "niv_spe_dep_sg__groupe")
                    .distinct()
                    .order_by("nom_ar")
                )

                etudiants = []
                for e in etudiants_qs:
                    etudiants.append(
                        {
                            "id": e.id,
                            "nom_ar": e.nom_ar,
                            "prenom_ar": e.prenom_ar,
                            "nom_fr": e.nom_fr,
                            "prenom_fr": e.prenom_fr,
                            "matricule": e.matricule,
                            "est_inscrit": e.est_inscrit,
                            "tel_mobile1": e.tel_mobile1,
                            "email_prof": e.email_prof,
                            "date_nais": str(e.date_nais) if e.date_nais else None,
                            "section_nom": e.niv_spe_dep_sg.section.nom_ar
                            if e.niv_spe_dep_sg and e.niv_spe_dep_sg.section
                            else None,
                            "groupe_nom": e.niv_spe_dep_sg.groupe.nom_ar
                            if e.niv_spe_dep_sg and e.niv_spe_dep_sg.groupe
                            else None,
                        }
                    )

            # Cas 3: Groupe individuel ou Section container
            else:
                # Vérifier si c'est un section container (a une section mais pas de groupe)
                try:
                    selected_sg = NivSpeDep_SG.objects.select_related("section", "groupe", "niv_spe_dep").get(
                        id=niv_spe_dep_sg_id
                    )

                    if selected_sg.section and not selected_sg.groupe:
                        # C'est un section container: récupérer TOUS les étudiants de cette section
                        groupes_section_ids = NivSpeDep_SG.objects.filter(
                            niv_spe_dep=selected_sg.niv_spe_dep, section=selected_sg.section
                        ).values_list("id", flat=True)

                        etudiants_qs = (
                            Etudiant.objects.filter(niv_spe_dep_sg_id__in=groupes_section_ids)
                            .select_related("niv_spe_dep_sg__section", "niv_spe_dep_sg__groupe")
                            .order_by("nom_ar")
                        )
                    else:
                        # C'est un groupe individuel
                        etudiants_qs = (
                            Etudiant.objects.filter(niv_spe_dep_sg_id=niv_spe_dep_sg_id)
                            .select_related("niv_spe_dep_sg__section", "niv_spe_dep_sg__groupe")
                            .order_by("nom_ar")
                        )
                except NivSpeDep_SG.DoesNotExist:
                    etudiants_qs = Etudiant.objects.none()

                etudiants = []
                for e in etudiants_qs:
                    etudiants.append(
                        {
                            "id": e.id,
                            "nom_ar": e.nom_ar,
                            "prenom_ar": e.prenom_ar,
                            "nom_fr": e.nom_fr,
                            "prenom_fr": e.prenom_fr,
                            "matricule": e.matricule,
                            "est_inscrit": e.est_inscrit,
                            "tel_mobile1": e.tel_mobile1,
                            "email_prof": e.email_prof,
                            "date_nais": str(e.date_nais) if e.date_nais else None,
                            "section_nom": e.niv_spe_dep_sg.section.nom_ar
                            if e.niv_spe_dep_sg and e.niv_spe_dep_sg.section
                            else None,
                            "groupe_nom": e.niv_spe_dep_sg.groupe.nom_ar
                            if e.niv_spe_dep_sg and e.niv_spe_dep_sg.groupe
                            else None,
                        }
                    )

            return JsonResponse({"data": etudiants})

        return JsonResponse({"data": []})

    # Requête GET: afficher le template
    # Contexte avec sidebar commun
    context = get_sidebar_context(request, enseignant, departement)
    context.update(
        {
            "title": "قائمة الطلبة",
            "active_menu": "etudiants",
        }
    )
    return render(request, "enseignant/list_etudiants_ens.html", context)


@enseignant_access_required
def list_Mat_Niv_Ens(request, dep_id, enseignant, departement):
    """
    Liste des matières et modules du département (الهياكل والمقررات) - classée selon le code/numéro.
    Présentation unifiée identique au chef de département avec pagination et recherche directe.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q

    query = request.GET.get("q", "").strip()

    matieres_qs = (
        Matiere.objects.filter(niv_spe_dep__specialite__departement=departement)
        .select_related("niv_spe_dep__specialite", "niv_spe_dep__niveau", "semestre")
        .order_by("semestre__numero", Length("code"), "code", "id")
        .distinct()
    )

    if query:
        matieres_qs = matieres_qs.filter(
            Q(nom_ar__icontains=query) | Q(nom_fr__icontains=query) | Q(code__icontains=query)
        )

    paginator = Paginator(matieres_qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = get_sidebar_context(request, enseignant, departement)
    context.update(
        {
            "title": "قائمة المواد والمقررات الدراسية - الهياكل والمقررات",
            "active_menu": "matieres",
            "matieres": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "query": query,
            "total_matieres": matieres_qs.count(),
        }
    )
    return render(request, "enseignant/list_Mat_Niv_Ens.html", context)


@enseignant_access_required
def list_Specialite_Ens(request, dep_id, enseignant, departement):
    """
    Liste des spécialités du département (الهياكل والمقررات) - classée selon le code/numéro.
    Présentation unifiée identique au chef de département avec pagination, statistiques et recherche.
    """
    try:
        from django.core.paginator import Paginator
        from django.db.models import Count, Q

        query = request.GET.get("q", "").strip()

        specialites_qs = (
            Specialite.objects.filter(departement=departement)
            .annotate(
                nb_matieres=Count("nivspedep__matieres", distinct=True),
                nb_etudiants=Count("nivspedep__sections_groupes__etudiants", distinct=True),
            )
            .order_by(Length("code"), "code", "id")
        )

        if query:
            specialites_qs = specialites_qs.filter(
                Q(nom_ar__icontains=query) | Q(nom_fr__icontains=query) | Q(code__icontains=query)
            )

        paginator = Paginator(specialites_qs, 25)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "قائمة التخصصات والشعب - الهياكل والمقررات",
                "active_menu": "specialites",
                "specialites": page_obj,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "query": query,
                "total_count": specialites_qs.count(),
            }
        )
        return render(request, "enseignant/list_Specialite_Ens.html", context)

    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل قائمة التخصصات: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def list_NivSpeDep_Ens(request, dep_id, enseignant, departement):
    """
    Liste des niveaux/spécialités pour l'enseignant.
    Affiche tous les NivSpeDep du département avec statistiques par semestre.
    """
    # Récupérer tous les NivSpeDep du département
    all_NivSpeDep = (
        NivSpeDep.objects.filter(departement=departement)
        .select_related(
            "niveau", "specialite", "specialite__reforme", "specialite__identification", "specialite__parcours"
        )
        .order_by("specialite__reforme", "niveau", "specialite__identification")
    )

    # Calcul pour NivSpeDep (nbr_matieres et nbr_etudiants) en mémoire pour l'affichage (A15)
    for x in all_NivSpeDep:
        x.nbr_matieres_s1 = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=1).count()
        x.nbr_matieres_s2 = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=2).count()
        x.nbr_etudiants = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep=x).count()

    # Calcul intelligent pour NivSpeDep_SG selon le type d'affectation
    all_niv_spe_dep_sg = NivSpeDep_SG.objects.filter(niv_spe_dep__departement=departement)

    for niv_spe_dep_sg in all_niv_spe_dep_sg:
        if niv_spe_dep_sg.type_affectation == "par_groupe":
            niv_spe_dep_sg.nbr_etudiants_SG = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).count()
        elif niv_spe_dep_sg.type_affectation == "par_section":
            niv_spe_dep_sg.nbr_etudiants_SG = Etudiant.objects.filter(
                niv_spe_dep_sg__niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                niv_spe_dep_sg__section=niv_spe_dep_sg.section,
                niv_spe_dep_sg__type_affectation="par_groupe",
            ).count()
        elif niv_spe_dep_sg.type_affectation == "tous_etudiants":
            niv_spe_dep_sg.nbr_etudiants_SG = Etudiant.objects.filter(
                niv_spe_dep_sg__niv_spe_dep=niv_spe_dep_sg.niv_spe_dep
            ).count()

    # Construction des listes pour l'affichage par semestre
    all_NivSpeDep_S1 = []
    all_NivSpeDep_S2 = []

    for x in all_NivSpeDep:
        # Pour S1 - vérifier s'il y a des matières
        s1_matieres = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=1)
        if s1_matieres.exists():
            fake_obj_s1 = type(
                "obj",
                (object,),
                {"id": x.id, "niv_spe_dep": x, "semestre": type("semestre", (object,), {"numero": 1})()},
            )()
            all_NivSpeDep_S1.append(fake_obj_s1)

        # Pour S2 - vérifier s'il y a des matières
        s2_matieres = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=2)
        if s2_matieres.exists():
            fake_obj_s2 = type(
                "obj",
                (object,),
                {"id": x.id, "niv_spe_dep": x, "semestre": type("semestre", (object,), {"numero": 2})()},
            )()
            all_NivSpeDep_S2.append(fake_obj_s2)

    # Contexte avec sidebar commun
    context = get_sidebar_context(request, enseignant, departement)
    context.update(
        {
            "title": "قائمة المستويات",
            "active_menu": "niveaux",
            "all_NivSpeDep": all_NivSpeDep,
            "all_NivSpeDep_S1": all_NivSpeDep_S1,
            "all_NivSpeDep_S2": all_NivSpeDep_S2,
        }
    )
    return render(request, "enseignant/list_NivSpeDep_Ens.html", context)
