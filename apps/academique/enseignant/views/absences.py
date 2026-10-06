from collections import defaultdict

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import Abs_Etu_Seance, Classe, Gestion_Etu_Classe, Seance
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required

from ..services import get_sidebar_context


@enseignant_access_required
def list_Abs_Etu(request, dep_id, sea_id, enseignant, departement):
    """
    Vue pour gérer les absences des étudiants pour une séance donnée.
    Permet de marquer la présence, l'absence justifiée, la participation et les points bonus.
    """
    from decimal import Decimal

    try:
        # Récupérer la séance avec vérification des permissions
        mySeance = get_object_or_404(
            Seance.objects.select_related(
                "classe__enseignant__enseignant", "classe__matiere", "classe__semestre", "classe__niv_spe_dep_sg"
            ),
            id=sea_id,
            classe__enseignant__enseignant=enseignant,
            classe__enseignant__departement=departement,
        )

        # Récupérer toutes les absences pour cette séance
        all_Abs_Etu = (
            Abs_Etu_Seance.objects.filter(seance=mySeance)
            .select_related("etudiant")
            .order_by("etudiant__nom_ar", "etudiant__prenom_ar")
        )

        if request.method == "POST":
            try:
                # Traitement des données du formulaire
                for abs_etu in all_Abs_Etu:
                    abs_id = abs_etu.id

                    # Récupérer les valeurs du formulaire
                    present = request.POST.get(f"present_{abs_id}") == "1"
                    justifiee = request.POST.get(f"justifiee_{abs_id}") == "1"
                    participation = request.POST.get(f"participation_{abs_id}") == "1"
                    points_str = request.POST.get(f"points_sup_seance_{abs_id}", "0")
                    observation = request.POST.get(f"observation_{abs_id}", "").strip()

                    # Convertir les points
                    try:
                        points = Decimal(points_str) if points_str else Decimal("0.0")
                        points = max(Decimal("0.0"), min(Decimal("2.0"), points))
                    except Exception:
                        points = Decimal("0.0")

                    # Mise à jour des données
                    abs_etu.present = present
                    abs_etu.justifiee = justifiee if not present else False
                    abs_etu.participation = participation if present else False
                    abs_etu.points_sup_seance = points if present else Decimal("0.0")
                    abs_etu.obs = observation
                    abs_etu.save()

                # Mettre à jour les compteurs d'absences dans Gestion_Etu_Classe
                # pour chaque étudiant de cette classe
                myClasse = mySeance.classe
                etudiants_ids = all_Abs_Etu.values_list("etudiant_id", flat=True).distinct()

                for etudiant_id in etudiants_ids:
                    # Compter les absences totales (present=False) pour cet étudiant dans cette classe
                    absences_seances = Abs_Etu_Seance.objects.filter(seance__classe=myClasse, etudiant_id=etudiant_id)
                    total_absences = absences_seances.filter(present=False).count()
                    absences_justifiees = absences_seances.filter(present=False, justifiee=True).count()
                    total_seances = absences_seances.count()
                    total_points_sup = absences_seances.aggregate(total=Sum("points_sup_seance"))["total"] or Decimal(
                        "0"
                    )

                    # Mettre à jour ou créer Gestion_Etu_Classe
                    gestion, _ = Gestion_Etu_Classe.objects.get_or_create(classe=myClasse, etudiant_id=etudiant_id)
                    gestion.nbr_absence = total_absences
                    gestion.nbr_absence_justifiee = absences_justifiees
                    gestion.nbr_seances_totales = total_seances
                    gestion.total_sup_seance = total_points_sup

                    # Calculer automatiquement la note de présence (max 0, 5 - absences non justifiées)
                    absences_non_justifiees = total_absences - absences_justifiees
                    gestion.note_presence = max(Decimal("0"), Decimal("5") - Decimal(absences_non_justifiees))

                    gestion.save()

                messages.success(request, "تم حفظ الغيابات بنجاح")
                return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=mySeance.classe.id)

            except Exception as save_error:
                messages.error(request, f"خطأ في حفظ البيانات: {str(save_error)}")

        # Calculer les statistiques
        present_count = all_Abs_Etu.filter(present=True).count()
        justified_count = all_Abs_Etu.filter(justifiee=True).count()
        absent_count = all_Abs_Etu.count() - present_count - justified_count

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "قائمة الغيابات",
                "active_menu": "timetable",
                "mySeance": mySeance,
                "all_Abs_Etu": all_Abs_Etu,
                "present_count": present_count,
                "justified_count": justified_count,
                "absent_count": max(0, absent_count),
                "titre_00": mySeance.classe.niv_spe_dep_sg,
                "titre_01": mySeance.classe.matiere.nom_ar,
                "titre_02": mySeance.date,
            }
        )

        return render(request, "enseignant/list_Abs_Etu.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)


@enseignant_access_required
def list_Abs_Etu_Classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour afficher la liste des absences de tous les étudiants pour une classe donnée.
    Affiche un résumé par étudiant de toutes les séances.
    """
    try:
        # Récupérer la classe
        myClasse = get_object_or_404(
            Classe.objects.select_related(
                "matiere", "semestre", "enseignant__enseignant", "niv_spe_dep_sg__niv_spe_dep__specialite"
            ),
            id=clas_id,
            enseignant__enseignant=enseignant,
            enseignant__departement=departement,
        )

        # Récupérer les séances faites de cette classe (pour afficher les colonnes)
        all_seances = Seance.objects.filter(classe=myClasse, fait=True).order_by("date", "temps")

        # Récupérer les notes/gestion des étudiants avec les absences agrégées
        niv_spe_dep_sg = myClasse.niv_spe_dep_sg

        # Pour les Cours, récupérer les étudiants de tous les groupes de la section
        if myClasse.type == "Cours" and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
            from apps.academique.departement.models import NivSpeDep_SG

            groupes_de_section = NivSpeDep_SG.objects.filter(
                niv_spe_dep=niv_spe_dep_sg.niv_spe_dep, section=niv_spe_dep_sg.section, groupe__isnull=False
            )
            etudiants_ids = Etudiant.objects.filter(niv_spe_dep_sg__in=groupes_de_section, est_actif=True).values_list(
                "id", flat=True
            )
        else:
            etudiants_ids = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg, est_actif=True).values_list(
                "id", flat=True
            )

        # Récupérer toutes les absences pour cette classe
        all_absences = (
            Abs_Etu_Seance.objects.filter(seance__classe=myClasse, etudiant_id__in=etudiants_ids)
            .select_related("etudiant", "seance")
            .order_by("etudiant__nom_ar", "seance__date")
        )

        # Regrouper les absences par étudiant
        absences_par_etudiant = defaultdict(list)
        for abs_record in all_absences:
            absences_par_etudiant[abs_record.etudiant].append(abs_record)

        # Calculer les statistiques par étudiant
        etudiants_stats = []
        for etudiant, absences in absences_par_etudiant.items():
            total_seances = len(absences)
            presents = sum(1 for a in absences if a.present)
            absents = sum(1 for a in absences if not a.present and not a.justifiee)
            justifies = sum(1 for a in absences if not a.present and a.justifiee)
            participations = sum(1 for a in absences if a.participation)

            taux_presence = (presents / total_seances * 100) if total_seances > 0 else 0

            # Créer un dictionnaire des absences indexé par seance_id
            absences_by_seance = {abs_rec.seance_id: abs_rec for abs_rec in absences}

            etudiants_stats.append(
                {
                    "etudiant": etudiant,
                    "absences": absences,
                    "absences_by_seance": absences_by_seance,
                    "total_seances": total_seances,
                    "presents": presents,
                    "absents": absents,
                    "justifies": justifies,
                    "participations": participations,
                    "taux_presence": round(taux_presence, 1),
                }
            )

        # Trier par nom_fr, prenom_fr (français d'abord)
        etudiants_stats.sort(key=lambda x: (x["etudiant"].nom_fr or "", x["etudiant"].prenom_fr or ""))

        # Convertir all_seances en liste pour pouvoir l'utiliser dans la boucle
        seances_list = list(all_seances)

        # Ajouter les statuts de séance pour chaque étudiant (dans l'ordre des séances)
        for stat in etudiants_stats:
            seance_statuses = []
            for seance in seances_list:
                abs_record = stat["absences_by_seance"].get(seance.id)
                if abs_record:
                    if abs_record.present:
                        seance_statuses.append("P")  # Présent
                    elif abs_record.justifiee:
                        seance_statuses.append("J")  # Justifié
                    else:
                        seance_statuses.append("A")  # Absent
                else:
                    seance_statuses.append("-")  # Pas de données
            stat["seance_statuses"] = seance_statuses

        # Statistiques globales
        total_etudiants = len(etudiants_stats)
        total_seances = len(seances_list)
        avg_presence = sum(e["taux_presence"] for e in etudiants_stats) / total_etudiants if total_etudiants > 0 else 0

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "myClasse": myClasse,
                "all_seances": seances_list,
                "etudiants_stats": etudiants_stats,
                "total_etudiants": total_etudiants,
                "total_seances": total_seances,
                "avg_presence": round(avg_presence, 1),
            }
        )

        return render(request, "enseignant/list_Abs_Etu_Classe.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)
