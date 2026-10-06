from collections import defaultdict

from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import (
    Classe,
    Ens_Dep,
    EtudiantSousGroupe,
    Seance,
    SousGroupe,
    SousGroupeManager,
)
from apps.academique.departement.models import NivSpeDep_SG
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import Semestre


@enseignant_access_required
def update_classe_moodle(request, dep_id, classe_id, enseignant, departement):
    """
    Vue pour mettre a jour le lien Moodle et l'observation d'une classe.
    """
    if request.method == "POST":
        try:
            classe = Classe.objects.get(
                id=classe_id, enseignant__enseignant=enseignant, enseignant__departement=departement
            )

            # Mettre a jour les champs
            lien_moodle = request.POST.get("lien_moodle", "").strip()
            observation = request.POST.get("observation", "").strip()

            classe.lien_moodle = lien_moodle if lien_moodle else None
            classe.observation = observation
            classe.save()

            return JsonResponse({"success": True, "message": "تم حفظ التعديلات بنجاح"})

        except Classe.DoesNotExist:
            return JsonResponse({"success": False, "error": "الحصة غير موجودة"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "طريقة غير مسموحة"}, status=405)


@enseignant_access_required
def niveaux_enseigner(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des niveaux enseignés par un enseignant
    selon ses affectations (sections et groupes)
    """
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
    except Exception:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    semestre_selected = request.GET.get("semestre", "1")

    try:
        semestre_obj = Semestre.objects.get(numero=semestre_selected)
    except Exception:
        semestre_obj = Semestre.objects.filter(numero="1").first()
        semestre_selected = "1"

    def traduire_jour_en_arabe(jour_francais):
        traduction_jours = {
            "Samedi": "السبت",
            "Dimanche": "الأحد",
            "Lundi": "الإثنين",
            "Mardi": "الثلاثاء",
            "Mercredi": "الأربعاء",
            "Jeudi": "الخميس",
            "Vendredi": "الجمعة",
        }
        return traduction_jours.get(jour_francais, jour_francais)

    def compter_etudiants_section_ou_groupe(niv_spe_dep_sg, type_affectation, section_numero=None):
        try:
            if type_affectation == "par_section" and section_numero is not None:
                groupes_de_la_section = NivSpeDep_SG.objects.filter(
                    niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                    section__numero=section_numero,
                    type_affectation="par_groupe",
                )
                return sum(Etudiant.objects.filter(niv_spe_dep_sg=g).count() for g in groupes_de_la_section)
            elif type_affectation == "par_groupe":
                return Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).count()
            return 0
        except Exception:
            return 0

    all_classes = Classe.objects.filter(
        enseignant__departement=departement.id, enseignant__enseignant=enseignant.id, semestre=semestre_obj
    ).select_related(
        "niv_spe_dep_sg",
        "niv_spe_dep_sg__niv_spe_dep__niveau",
        "niv_spe_dep_sg__niv_spe_dep__specialite",
        "niv_spe_dep_sg__niv_spe_dep__departement",
        "niv_spe_dep_sg__section",
        "niv_spe_dep_sg__groupe",
        "matiere",
    )

    niveaux_data = defaultdict(
        lambda: {
            "niveau": None,
            "specialite": None,
            "departement": None,
            "sections": defaultdict(
                lambda: {
                    "matiere_count": 0,
                    "matieres": [],
                    "types_cours": set(),
                    "total_heures": 0,
                    "section_numero": None,
                }
            ),
            "groupes": defaultdict(
                lambda: {
                    "matiere_count": 0,
                    "matieres": [],
                    "types_cours": set(),
                    "total_heures": 0,
                    "groupe_numero": None,
                }
            ),
        }
    )

    for classe in all_classes:
        niv_spe_dep_sg = classe.niv_spe_dep_sg
        key = f"{niv_spe_dep_sg.niv_spe_dep.niveau.nom_fr}_{niv_spe_dep_sg.niv_spe_dep.specialite.nom_fr}_{niv_spe_dep_sg.niv_spe_dep.departement.nom_fr}"

        niveaux_data[key]["niveau"] = niv_spe_dep_sg.niv_spe_dep.niveau
        niveaux_data[key]["specialite"] = niv_spe_dep_sg.niv_spe_dep.specialite
        niveaux_data[key]["departement"] = niv_spe_dep_sg.niv_spe_dep.departement

        nbr_seances_total, nbr_seances_faites = 0, 0
        if classe.seance_created:
            seances = Seance.objects.filter(classe=classe)
            nbr_seances_total = seances.count()
            nbr_seances_faites = seances.filter(fait=True).count()

        sous_groupes_count = 0
        if niv_spe_dep_sg.type_affectation == "par_groupe":
            sous_groupes_count = SousGroupe.objects.filter(groupe_principal=niv_spe_dep_sg, actif=True).count()

        if niv_spe_dep_sg.type_affectation == "par_groupe":
            groupe_nom = niv_spe_dep_sg.groupe.nom_ar
            container = niveaux_data[key]["groupes"][groupe_nom]
            container["groupe_numero"] = niv_spe_dep_sg.groupe.numero
            nb_etudiants = compter_etudiants_section_ou_groupe(niv_spe_dep_sg, "par_groupe")
        else:
            section_nom = (
                niv_spe_dep_sg.section.nom_ar if niv_spe_dep_sg.section else f"Section {niv_spe_dep_sg.numero_section}"
            )
            container = niveaux_data[key]["sections"][section_nom]
            section_numero = niv_spe_dep_sg.section.numero if niv_spe_dep_sg.section else niv_spe_dep_sg.numero_section
            container["section_numero"] = section_numero
            nb_etudiants = compter_etudiants_section_ou_groupe(niv_spe_dep_sg, "par_section", section_numero)

        matiere_info = {
            "matiere": classe.matiere,
            "type_cours": classe.type,
            "jour": traduire_jour_en_arabe(classe.jour),
            "temps": classe.temps,
            "taux_avancement": classe.taux_avancement,
            "seances_total": nbr_seances_total,
            "seances_faites": nbr_seances_faites,
            "lieu": classe.lieu,
            "classe_id": classe.id,
            "sous_groupes_count": sous_groupes_count,
            "niv_spe_dep_sg_id": niv_spe_dep_sg.id,
            "nb_etudiants": nb_etudiants,
        }

        container["matieres"].append(matiere_info)
        container["types_cours"].add(classe.type)
        container["matiere_count"] += 1
        container["total_heures"] += 1.5

    niveaux_final = []
    for key, data in niveaux_data.items():
        sections_sorted = dict(
            sorted(data["sections"].items(), key=lambda x: x[1]["section_numero"] if x[1]["section_numero"] else 999)
        )
        groupes_sorted = dict(
            sorted(data["groupes"].items(), key=lambda x: x[1]["groupe_numero"] if x[1]["groupe_numero"] else 999)
        )
        niveaux_final.append(
            {
                "niveau": data["niveau"],
                "specialite": data["specialite"],
                "departement": data["departement"],
                "sections": sections_sorted,
                "groupes": groupes_sorted,
                "total_sections": len(data["sections"]),
                "total_groupes": len(data["groupes"]),
                "total_matieres": sum(s["matiere_count"] for s in data["sections"].values())
                + sum(g["matiere_count"] for g in data["groupes"].values()),
            }
        )

    niveaux_final.sort(key=lambda x: (x["niveau"].nom_fr, x["specialite"].nom_fr))

    stats = {
        "total_niveaux": len(niveaux_final),
        "total_sections": sum(n["total_sections"] for n in niveaux_final),
        "total_groupes": sum(n["total_groupes"] for n in niveaux_final),
        "total_matieres": sum(n["total_matieres"] for n in niveaux_final),
        "total_classes": all_classes.count(),
    }

    context = {
        "title": "المستويات المدرسة",
        "niveaux_enseigner": niveaux_final,
        "stats": stats,
        "type_repartition": all_classes.values("type").annotate(count=Count("id")).order_by("type"),
        "semestre_selected": semestre_selected,
        "semestre_obj": semestre_obj,
        "all_semestres": Semestre.objects.all().order_by("numero"),
        "my_Dep": departement,
        "my_Fac": departement.faculte,
        "my_Ens": enseignant,
        "real_Dep": real_Dep,
    }
    return render(request, "enseignant/niveaux_enseigner.html", context)


@enseignant_access_required
def page_nombre_sous_groupes(request, dep_id, classe_id, enseignant, departement):
    """Page pour choisir le nombre de sous-groupes"""
    classe = get_object_or_404(Classe, id=classe_id)
    if request.method == "POST":
        nombre = int(request.POST.get("nombre", 2))
        SousGroupeManager.creer_sous_groupes_automatiques(
            groupe_principal=classe.niv_spe_dep_sg, nombre_sous_groupes=nombre, enseignant=enseignant
        )
        return redirect("ense:affecter_etudiants_sous_groupes", dep_id=dep_id, classe_id=classe_id)
    return render(
        request,
        "enseignant/choisir_nombre_sous_groupes.html",
        {"classe": classe, "my_Dep": departement, "my_Ens": enseignant},
    )


@enseignant_access_required
def affecter_etudiants_sous_groupes(request, dep_id, classe_id, enseignant, departement):
    """Page pour affecter les étudiants aux sous-groupes"""
    classe = get_object_or_404(Classe, id=classe_id)
    sous_groupes = SousGroupe.objects.filter(groupe_principal=classe.niv_spe_dep_sg, actif=True).order_by(
        "ordre_affichage"
    )
    etudiants = Etudiant.objects.filter(niv_spe_dep_sg=classe.niv_spe_dep_sg).order_by("nom_ar", "prenom_ar")

    if request.method == "POST":
        for etudiant in etudiants:
            sous_groupe_id = request.POST.get(f"etudiant_{etudiant.id}")
            if sous_groupe_id:
                EtudiantSousGroupe.objects.filter(etudiant=etudiant).delete()
                EtudiantSousGroupe.objects.create(
                    etudiant=etudiant, sous_groupe_id=sous_groupe_id, affecte_par=enseignant
                )
        messages.success(request, "تم توزيع الطلاب على المجموعات الفرعية بنجاح!")
        return redirect("ense:niveaux_enseigner", dep_id=dep_id)

    return render(
        request,
        "enseignant/affecter_etudiants_sous_groupes.html",
        {
            "classe": classe,
            "sous_groupes": sous_groupes,
            "etudiants": etudiants,
            "my_Dep": departement,
            "my_Ens": enseignant,
        },
    )


@enseignant_access_required
def liste_sous_groupes(request, dep_id, niv_spe_dep_sg_id, enseignant, departement):
    """Afficher la liste des sous-groupes et leurs étudiants"""
    niv_spe_dep_sg = get_object_or_404(NivSpeDep_SG, id=niv_spe_dep_sg_id)
    sous_groupes = SousGroupe.objects.filter(groupe_principal=niv_spe_dep_sg, actif=True).order_by("ordre_affichage")
    tous_etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).order_by("nom_ar", "prenom_ar")
    etudiants_affectes_ids = EtudiantSousGroupe.objects.filter(sous_groupe__in=sous_groupes, actif=True).values_list(
        "etudiant_id", flat=True
    )
    etudiants_non_affectes = tous_etudiants.exclude(id__in=etudiants_affectes_ids)

    sous_groupes_avec_etudiants = []
    for sg in sous_groupes:
        etudiants = Etudiant.objects.filter(
            affectations_sous_groupes__sous_groupe=sg, affectations_sous_groupes__actif=True
        ).order_by("nom_ar", "prenom_ar")
        sous_groupes_avec_etudiants.append({"sous_groupe": sg, "etudiants": etudiants})

    return render(
        request,
        "enseignant/liste_sous_groupes.html",
        {
            "niv_spe_dep_sg": niv_spe_dep_sg,
            "sous_groupes_avec_etudiants": sous_groupes_avec_etudiants,
            "etudiants_non_affectes": etudiants_non_affectes,
            "my_Dep": departement,
            "my_Ens": enseignant,
        },
    )


@enseignant_access_required
def affecter_direct_sous_groupes(request, dep_id, niv_spe_dep_sg_id, enseignant, departement):
    """Traiter l'affectation directe des étudiants aux sous-groupes"""
    if request.method == "POST":
        niv_spe_dep_sg = get_object_or_404(NivSpeDep_SG, id=niv_spe_dep_sg_id)
        tous_etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg)
        affectations_reussies, modifications_reussies = 0, 0

        for etudiant in tous_etudiants:
            sous_groupe_id = request.POST.get(f"etudiant_{etudiant.id}")
            if sous_groupe_id:
                try:
                    sous_groupe = get_object_or_404(SousGroupe, id=sous_groupe_id)
                    if sous_groupe.groupe_principal == niv_spe_dep_sg:
                        affectation = EtudiantSousGroupe.objects.filter(
                            etudiant=etudiant, sous_groupe__groupe_principal=niv_spe_dep_sg, actif=True
                        ).first()
                        if affectation:
                            if affectation.sous_groupe.id != int(sous_groupe_id):
                                affectation.delete()
                                EtudiantSousGroupe.objects.create(
                                    etudiant=etudiant, sous_groupe=sous_groupe, affecte_par=enseignant
                                )
                                modifications_reussies += 1
                        else:
                            EtudiantSousGroupe.objects.create(
                                etudiant=etudiant, sous_groupe=sous_groupe, affecte_par=enseignant
                            )
                            affectations_reussies += 1
                except Exception:
                    pass  # Ignorer les erreurs individuelles

        if affectations_reussies and modifications_reussies:
            messages.success(
                request,
                f"تم تعيين {affectations_reussies} طالب جديد وتعديل {modifications_reussies} تعيين موجود بنجاح!",
            )
        elif affectations_reussies:
            messages.success(request, f"تم تعيين {affectations_reussies} طالب جديد بنجاح!")
        elif modifications_reussies:
            messages.success(request, f"تم تعديل {modifications_reussies} تعيين بنجاح!")
        else:
            messages.warning(request, "لم يتم إجراء أي تغييرات.")

        return redirect("ense:liste_sous_groupes", dep_id=dep_id, niv_spe_dep_sg_id=niv_spe_dep_sg_id)
    return redirect("ense:liste_sous_groupes", dep_id=dep_id, niv_spe_dep_sg_id=niv_spe_dep_sg_id)
