from django.http import JsonResponse

from apps.academique.departement.models import Matiere, NivSpeDep_SG, Specialite
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import Niveau, Reforme, Semestre


@enseignant_access_required
def matieres_json_ens(request, dep_id, enseignant, departement):
    """
    Vue AJAX pour charger les données en cascade (réformes, niveaux, spécialités, semestres, matières).
    """
    try:
        if request.method == "POST":
            action = request.POST.get("action", "")

            # Charger les réformes disponibles pour ce département
            if action == "get_reformes":
                # Récupérer les réformes qui ont des spécialités dans ce département
                # Note: related_name='specialites' sur Specialite.reforme
                reformes = (
                    Reforme.objects.filter(specialites__departement=departement)
                    .distinct()
                    .values("id", "code", "nom_ar", "nom_fr")
                    .order_by("code")
                )
                return JsonResponse({"data": list(reformes)})

            # Charger les niveaux pour une réforme
            elif action == "get_niveaux":
                reforme_id = request.POST.get("reforme")
                if reforme_id:
                    # Récupérer les niveaux via NivSpeDep (relation inverse depuis Niveau)
                    niveaux = (
                        Niveau.objects.filter(
                            nivspedep__specialite__reforme_id=reforme_id, nivspedep__departement=departement
                        )
                        .distinct()
                        .values("id", "code", "nom_ar", "nom_fr")
                        .order_by("code")
                    )
                    return JsonResponse({"data": list(niveaux)})
                return JsonResponse({"data": []})

            # Charger les spécialités pour un niveau et une réforme
            elif action == "get_specialites":
                reforme_id = request.POST.get("reforme")
                niveau_id = request.POST.get("niveau")
                if reforme_id and niveau_id:
                    specialites = (
                        Specialite.objects.filter(
                            reforme_id=reforme_id, departement=departement, nivspedep__niveau_id=niveau_id
                        )
                        .distinct()
                        .values("id", "code", "nom_ar", "nom_fr")
                        .order_by("nom_ar")
                    )
                    return JsonResponse({"data": list(specialites)})
                return JsonResponse({"data": []})

            # Charger les semestres
            elif action == "get_semestres":
                semestres = Semestre.objects.all().values("id", "numero", "nom_ar", "nom_fr").order_by("numero")
                return JsonResponse({"data": list(semestres)})

            # Charger les matières
            elif action == "get_matieres":
                reforme_id = request.POST.get("reforme")
                niveau_id = request.POST.get("niveau")
                specialite_id = request.POST.get("specialite")
                semestre_id = request.POST.get("semestre")

                # Construire les filtres
                filters = {"niv_spe_dep__departement": departement}

                if reforme_id:
                    filters["niv_spe_dep__specialite__reforme_id"] = reforme_id
                if niveau_id:
                    filters["niv_spe_dep__niveau_id"] = niveau_id
                if specialite_id:
                    filters["niv_spe_dep__specialite_id"] = specialite_id
                if semestre_id:
                    filters["semestre_id"] = semestre_id

                # Récupérer les matières
                matieres = (
                    Matiere.objects.filter(**filters)
                    .values("id", "nom_ar", "nom_fr", "code", "coeff", "credit")
                    .order_by("code")
                )

                return JsonResponse({"data": list(matieres)})

            return JsonResponse({"data": []})

        return JsonResponse({"data": []})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@enseignant_access_required
def etudiants_json_ens(request, dep_id, enseignant, departement):
    """
    Vue AJAX pour charger les données en cascade (réformes, niveaux, groupes).
    Utilisée par la page de liste des étudiants.
    """
    try:
        if request.method == "POST":
            action = request.POST.get("action", "")

            # Charger les réformes disponibles pour ce département
            if action == "get_reformes":
                reformes = (
                    Reforme.objects.filter(specialites__departement=departement)
                    .distinct()
                    .values("id", "code", "nom_ar", "nom_fr")
                    .order_by("code")
                )
                return JsonResponse({"data": list(reformes)})

            # Charger les niveaux pour une réforme
            elif action == "get_niveaux":
                reforme_id = request.POST.get("reforme")
                if reforme_id:
                    niveaux = (
                        Niveau.objects.filter(
                            nivspedep__specialite__reforme_id=reforme_id, nivspedep__departement=departement
                        )
                        .distinct()
                        .values("id", "code", "nom_ar", "nom_fr")
                        .order_by("code")
                    )
                    return JsonResponse({"data": list(niveaux)})
                return JsonResponse({"data": []})

            # Charger les groupes (NivSpeDep_SG) pour un niveau et une réforme
            elif action == "get_groupes":
                reforme_id = request.POST.get("reforme")
                niveau_id = request.POST.get("niveau")

                if reforme_id and niveau_id:
                    # Récupérer TOUS les NivSpeDep_SG (y compris sections containers)
                    groupes = (
                        NivSpeDep_SG.objects.filter(
                            niv_spe_dep__departement=departement,
                            niv_spe_dep__niveau_id=niveau_id,
                            niv_spe_dep__specialite__reforme_id=reforme_id,
                        )
                        .select_related("section", "groupe", "niv_spe_dep__specialite")
                        .order_by("section__nom_ar", "groupe__nom_ar")
                    )

                    data = []
                    for g in groupes:
                        # Déterminer le nom à afficher et compter les étudiants
                        if g.groupe:
                            # Groupe individuel: compter directement
                            display_nom = g.groupe.nom_ar
                            nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg_id=g.id).count()
                        elif g.section:
                            # Section container: compter TOUS les étudiants de cette section
                            display_nom = f"{g.section.nom_ar} (قطاع كامل)"
                            # Récupérer tous les groupes de cette section
                            groupes_section_ids = NivSpeDep_SG.objects.filter(
                                niv_spe_dep=g.niv_spe_dep, section=g.section
                            ).values_list("id", flat=True)
                            nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg_id__in=groupes_section_ids).count()
                        else:
                            display_nom = "بدون تحديد"
                            nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg_id=g.id).count()

                        # Fallback sur nbr_etudiants_SG si pas d'étudiants trouvés
                        if nbr_etu == 0 and g.nbr_etudiants_SG:
                            nbr_etu = g.nbr_etudiants_SG

                        data.append(
                            {
                                "id": g.id,
                                "section_nom": g.section.nom_ar if g.section else None,
                                "groupe_nom": display_nom,
                                "specialite_nom": g.niv_spe_dep.specialite.nom_ar if g.niv_spe_dep.specialite else None,
                                "nbr_etudiants": nbr_etu,
                            }
                        )

                    return JsonResponse({"data": data})
                return JsonResponse({"data": []})

            return JsonResponse({"data": []})

        return JsonResponse({"data": []})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
