from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Min
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import Classe, Ens_Dep
from apps.academique.departement.models import Matiere, NivSpeDep, NivSpeDep_SG, Specialite
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import AnneeUniversitaire, Semestre

from ..models import Enseignant
from ..services import _safe_str


@login_required
def list_Ens(request):
    """
    Liste de tous les enseignants.
    Affiche la liste complète des enseignants avec possibilité de recherche et filtrage.
    """
    try:
        # Récupérer tous les enseignants actifs
        enseignants = Enseignant.objects.select_related("user", "grade", "diplome", "wilaya").all()

        # TODO: Ajouter des filtres et recherche selon les besoins
        # Par exemple: filter par grade, diplome, wilaya, etc.

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
    Détails complets d'un enseignant.
    Affiche toutes les informations détaillées d'un enseignant spécifique.
    """
    try:
        enseignant = get_object_or_404(
            Enseignant.objects.select_related("user", "grade", "diplome", "wilaya"), id=enseignant_id
        )

        context = {
            "title": f"تفاصيل الأستاذ / Détails enseignant - {enseignant.get_nom_complet()}",
            "enseignant": enseignant,
        }
        return render(request, "enseignant/detail_Ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)} / Erreur: {str(e)}")
        return redirect("ense:list_Ens")


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
            "enseignant__grade", "enseignant__user__poste_principal", "enseignant"
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

        context = {
            "title": "قائمة الأساتذة",
            "my_Dep": departement,
            "my_Fac": departement.faculte,
            "my_Ens": enseignant,
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
    context = {
        "title": "قائمة الطلبة",
        "my_Dep": departement,
        "my_Fac": departement.faculte,
        "my_Ens": enseignant,
        "active_menu": "etudiants",
    }
    return render(request, "enseignant/list_etudiants_ens.html", context)


@enseignant_access_required
def list_Mat_Niv_Ens(request, dep_id, enseignant, departement):
    """
    Liste des matières/modules adaptée pour l'enseignant.
    Affiche un formulaire de filtrage en cascade et la liste des matières.
    """
    context = {
        "title": "قائمة المواد",
        "my_Dep": departement,
        "my_Fac": departement.faculte,
        "my_Ens": enseignant,
        "active_menu": "matieres",
    }
    return render(request, "enseignant/list_Mat_Niv_Ens.html", context)


@enseignant_access_required
def list_Specialite_Ens(request, dep_id, enseignant, departement):
    """
    Liste des spécialités du département adaptée pour l'enseignant.
    Affiche toutes les spécialités avec statistiques.
    """
    try:
        # Récupérer toutes les spécialités du département
        queryset = (
            Specialite.objects.filter(departement=departement)
            .select_related("reforme", "identification", "parcours")
            .order_by("reforme__code", "nom_ar")
        )

        # Statistiques de base
        total_count = queryset.count()
        count_with_reforme = queryset.filter(reforme__isnull=False).count()
        count_with_identification = queryset.filter(identification__isnull=False).count()
        reformes_count = queryset.values("reforme").distinct().count()

        # Convertir le queryset en liste de dictionnaires pour éviter les problèmes d'encodage dans le template
        all_Specialite_Ens = []
        for spe in queryset:
            try:
                spe_data = {
                    "id": spe.id,
                    "nom_ar": _safe_str(spe.nom_ar),
                    "nom_fr": _safe_str(spe.nom_fr),
                    "code": _safe_str(spe.code),
                    "reforme": None,
                    "identification": None,
                    "parcours": None,
                }
                if spe.reforme:
                    spe_data["reforme"] = {
                        "nom_ar": _safe_str(spe.reforme.nom_ar),
                        "code": _safe_str(spe.reforme.code),
                    }
                if spe.identification:
                    spe_data["identification"] = {
                        "nom_ar": _safe_str(
                            spe.identification.nom_ar if hasattr(spe.identification, "nom_ar") else None
                        ),
                        "code": _safe_str(spe.identification.code if hasattr(spe.identification, "code") else None),
                    }
                if spe.parcours:
                    spe_data["parcours"] = {
                        "nom_ar": _safe_str(spe.parcours.nom_ar if hasattr(spe.parcours, "nom_ar") else None),
                        "code": _safe_str(spe.parcours.code if hasattr(spe.parcours, "code") else None),
                    }
                all_Specialite_Ens.append(spe_data)
            except Exception:
                # Skip problematic records
                continue

        # Statistiques par réforme
        reforme_stats = []
        try:
            stats = (
                queryset.exclude(reforme__isnull=True)
                .values("reforme__code", "reforme__nom_ar")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            for stat in stats:
                reforme_stats.append(
                    {
                        "reforme__code": _safe_str(stat.get("reforme__code")),
                        "reforme__nom_ar": _safe_str(stat.get("reforme__nom_ar")),
                        "count": stat.get("count", 0),
                    }
                )
        except Exception:
            reforme_stats = []

        context = {
            "title": "قائمة التخصصات",
            "my_Fac": departement.faculte,
            "my_Dep": departement,
            "my_Ens": enseignant,
            "active_menu": "specialites",
            "all_Specialite_Ens": all_Specialite_Ens,
            "total_count": total_count,
            "count_with_reforme": count_with_reforme,
            "count_with_identification": count_with_identification,
            "reformes_count": reformes_count,
            "reforme_stats": reforme_stats,
        }
        return render(request, "enseignant/list_Specialite_Ens.html", context)

    except Exception as e:
        import traceback

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

    # Calcul pour NivSpeDep (nbr_matieres et nbr_etudiants)
    for x in all_NivSpeDep:
        x.nbr_matieres_s1 = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=1).count()
        x.nbr_matieres_s2 = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=2).count()
        x.nbr_etudiants = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep=x).count()
        x.save()

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
        niv_spe_dep_sg.save()

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

    context = {
        "title": "قائمة المستويات",
        "active_menu": "niveaux",
        "my_Fac": departement.faculte,
        "my_Dep": departement,
        "my_Ens": enseignant,
        "all_NivSpeDep": all_NivSpeDep,
        "all_NivSpeDep_S1": all_NivSpeDep_S1,
        "all_NivSpeDep_S2": all_NivSpeDep_S2,
    }
    return render(request, "enseignant/list_NivSpeDep_Ens.html", context)
