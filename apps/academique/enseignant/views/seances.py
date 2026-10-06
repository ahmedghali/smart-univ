from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import Abs_Etu_Seance, Classe, EtudiantSousGroupe, Seance, SousGroupe
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required


@enseignant_access_required
def list_Sea_Ens(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour afficher la liste des séances d'une classe.
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

        # Récupérer toutes les séances de cette classe
        all_Seances = Seance.objects.filter(classe=myClasse).order_by("date", "temps")

        # Ajouter les statistiques d'absences pour chaque séance
        seances_with_stats = []
        for seance in all_Seances:
            # Récupérer les statistiques d'absences pour cette séance
            absences = Abs_Etu_Seance.objects.filter(seance=seance)
            seance.nbr_presents = absences.filter(present=True).count()
            seance.nbr_absents = absences.filter(present=False, justifiee=False).count()
            seance.nbr_justifies = absences.filter(justifiee=True).count()
            seance.nbr_participations = absences.filter(participation=True).count()
            seance.total_etudiants = absences.count()
            seances_with_stats.append(seance)

        # Statistiques globales
        nbr_Sea_fait = all_Seances.filter(fait=True).count()
        nbr_Sea_annuler = all_Seances.filter(annuler=True).count()
        nbr_Sea_reste = all_Seances.filter(fait=False, annuler=False).count()

        # Taux d'avancement
        total_seances = all_Seances.count()
        taux_avancement = round((nbr_Sea_fait / total_seances) * 100) if total_seances > 0 else 0

        context = {
            "title": f"قائمة الحصص - {myClasse.matiere.nom_ar}",
            "active_menu": "timetable",
            "my_Ens": enseignant,
            "my_Dep": departement,
            "myClasse": myClasse,
            "all_Seances": seances_with_stats,
            "nbr_Sea_fait": nbr_Sea_fait,
            "nbr_Sea_annuler": nbr_Sea_annuler,
            "nbr_Sea_reste": nbr_Sea_reste,
            "taux_avancement": taux_avancement,
        }

        return render(request, "enseignant/list_Sea_Ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)


@enseignant_access_required
def new_Seance_Ens(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour créer de nouvelles séances pour une classe.
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

        # Récupérer les sous-groupes disponibles
        sous_groupes_disponibles = SousGroupe.objects.filter(groupe_principal=myClasse.niv_spe_dep_sg).order_by(
            "ordre_affichage"
        )

        # Création automatique ou complétion des séances manquantes
        action = request.GET.get("action")
        if action in ["auto_create", "auto_complete"]:
            from datetime import timedelta

            # Pour auto_create, vérifier si les séances n'ont pas déjà été créées
            if action == "auto_create" and myClasse.seance_created:
                messages.warning(
                    request, 'تم إنشاء الحصص مسبقاً لهذه المادة. استخدم "إكمال الحصص المفقودة" لإضافة الحصص الناقصة.'
                )
                return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=clas_id)

            # Récupérer les dates du semestre
            semestre = myClasse.semestre
            if not semestre or not semestre.date_debut or not semestre.date_fin:
                messages.error(request, "لم يتم تحديد تواريخ السداسي. يرجى التواصل مع الإدارة.")
                return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=clas_id)

            # Mapper les jours français vers les numéros de jour Python (weekday)
            jour_mapping = {
                "Samedi": 5,  # Saturday
                "Dimanche": 6,  # Sunday
                "Lundi": 0,  # Monday
                "Mardi": 1,  # Tuesday
                "Mercredi": 2,  # Wednesday
                "Jeudi": 3,  # Thursday
            }

            jour_classe = myClasse.jour
            temps_classe = myClasse.temps

            if jour_classe not in jour_mapping:
                messages.error(request, f"يوم الحصة غير صالح: {jour_classe}")
                return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=clas_id)

            target_weekday = jour_mapping[jour_classe]

            # Trouver la première date du jour cible dans le semestre
            current_date = semestre.date_debut
            while current_date.weekday() != target_weekday:
                current_date += timedelta(days=1)

            # Créer les séances pour chaque semaine (uniquement celles qui n'existent pas)
            seances_created = 0
            seances_existing = 0
            while current_date <= semestre.date_fin:
                # Vérifier si une séance existe déjà pour cette date
                if not Seance.objects.filter(classe=myClasse, date=current_date, temps=temps_classe).exists():
                    Seance.objects.create(
                        classe=myClasse,
                        date=current_date,
                        temps=temps_classe,
                        type_audience="groupe_complet",
                        intitule=None,
                    )
                    seances_created += 1
                else:
                    seances_existing += 1

                # Passer à la semaine suivante
                current_date += timedelta(days=7)

            # Marquer la classe comme ayant ses séances créées
            if not myClasse.seance_created:
                myClasse.seance_created = True
                myClasse.save()

            if seances_created > 0:
                messages.success(
                    request, f"تم إنشاء {seances_created} حصة جديدة. ({seances_existing} حصة موجودة مسبقاً)"
                )
            else:
                messages.info(request, f"جميع الحصص موجودة بالفعل ({seances_existing} حصة)")

            return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=clas_id)

        if request.method == "POST":
            date_seance = request.POST.get("date_seance")
            temps_seance = request.POST.get("temps_seance")
            intitule = request.POST.get("intitule", "").strip()
            type_audience = request.POST.get("type_audience", "groupe_complet")

            # Créer la séance
            seance = Seance.objects.create(
                classe=myClasse,
                date=date_seance,
                temps=temps_seance,
                intitule=intitule if intitule else None,
                type_audience=type_audience,
            )

            # Gérer les sous-groupes si nécessaire
            if type_audience == "sous_groupe":
                sous_groupe_id = request.POST.get("sous_groupe_unique")
                if sous_groupe_id:
                    seance.sous_groupe_unique_id = sous_groupe_id
                    seance.save()
            elif type_audience == "multi_sous_groupes":
                sous_groupes_ids = request.POST.getlist("sous_groupes_multiples")
                if sous_groupes_ids:
                    seance.sous_groupes_multiples.set(sous_groupes_ids)

            messages.success(request, "تم إنشاء الحصة بنجاح")
            return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=clas_id)

        # Statistiques des séances existantes
        seances_existantes = Seance.objects.filter(classe=myClasse)
        nbr_seances_total = seances_existantes.count()
        nbr_seances_fait = seances_existantes.filter(fait=True).count()
        nbr_seances_reste = seances_existantes.filter(fait=False, annuler=False).count()
        taux_avancement = round((nbr_seances_fait / nbr_seances_total) * 100) if nbr_seances_total > 0 else 0

        context = {
            "title": f"إنشاء حصص - {myClasse.matiere.nom_ar}",
            "active_menu": "timetable",
            "my_Ens": enseignant,
            "my_Dep": departement,
            "myClasse": myClasse,
            "sous_groupes_disponibles": sous_groupes_disponibles,
            "nbr_seances_total": nbr_seances_total,
            "nbr_seances_fait": nbr_seances_fait,
            "nbr_seances_reste": nbr_seances_reste,
            "taux_avancement": taux_avancement,
        }

        return render(request, "enseignant/new_Seance_Ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)


@enseignant_access_required
def update_seance(request, dep_id, sea_id, enseignant, departement):
    """
    Vue pour modifier une séance existante.
    """
    try:
        seance = get_object_or_404(
            Seance.objects.select_related(
                "classe__enseignant__enseignant", "classe__matiere", "classe__semestre", "classe__niv_spe_dep_sg"
            ),
            id=sea_id,
            classe__enseignant__enseignant=enseignant,
            classe__enseignant__departement=departement,
        )

        if request.method == "POST":
            try:
                from datetime import datetime

                # Mise à jour des champs de date et temps
                date_seance = request.POST.get("date")
                temps_seance = request.POST.get("temps")

                if date_seance:
                    # Convertir explicitement la date
                    seance.date = datetime.strptime(date_seance, "%Y-%m-%d").date()
                if temps_seance:
                    seance.temps = temps_seance

                # Mise à jour des autres champs
                seance.intitule = request.POST.get("intitule", "").strip() or None
                fait_checked = request.POST.get("fait") == "on"
                seance.fait = fait_checked
                seance.annuler = request.POST.get("annuler") == "on"
                seance.remplacer = request.POST.get("remplacer") == "on"
                seance.obs = request.POST.get("obs", "").strip()

                # Générer la liste des absences si la séance est marquée comme faite
                # et que la liste n'a pas encore été générée
                # Pour les séances de type "Cours", vérifier si l'utilisateur a confirmé
                create_absence_list = request.POST.get("create_absence_list", "no")

                if fait_checked and not seance.list_abs_etudiant_generee and create_absence_list == "yes":
                    myClasse = seance.classe
                    niv_spe_dep_sg = myClasse.niv_spe_dep_sg

                    # Récupérer les étudiants selon le type de la classe et l'audience
                    etudiants = []

                    # Pour les séances de type "Cours" avec une Section
                    # Les étudiants sont dans les Groupes de cette Section
                    if myClasse.type == "Cours" and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
                        # Récupérer tous les NivSpeDep_SG qui ont le même niv_spe_dep et la même section
                        from apps.academique.departement.models import NivSpeDep_SG

                        groupes_de_section = NivSpeDep_SG.objects.filter(
                            niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                            section=niv_spe_dep_sg.section,
                            groupe__isnull=False,  # Seulement les groupes (pas les sections)
                        )
                        # Récupérer tous les étudiants de ces groupes
                        etudiants = Etudiant.objects.filter(
                            niv_spe_dep_sg__in=groupes_de_section, est_actif=True
                        ).distinct()

                    elif seance.type_audience == "groupe_complet":
                        # Tous les étudiants du groupe/section direct
                        etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg, est_actif=True)
                    elif seance.type_audience == "sous_groupe" and seance.sous_groupe_unique:
                        # Étudiants du sous-groupe spécifique
                        etu_sg = EtudiantSousGroupe.objects.filter(sous_groupe=seance.sous_groupe_unique).values_list(
                            "etudiant_id", flat=True
                        )
                        etudiants = Etudiant.objects.filter(id__in=etu_sg, est_actif=True)
                    elif seance.type_audience == "multi_sous_groupes":
                        # Étudiants de plusieurs sous-groupes
                        etu_sg = EtudiantSousGroupe.objects.filter(
                            sous_groupe__in=seance.sous_groupes_multiples.all()
                        ).values_list("etudiant_id", flat=True)
                        etudiants = Etudiant.objects.filter(id__in=etu_sg, est_actif=True)
                    else:
                        # Par défaut, tous les étudiants du groupe
                        etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg, est_actif=True)

                    # Créer les entrées d'absence pour chaque étudiant
                    for etudiant in etudiants:
                        Abs_Etu_Seance.objects.get_or_create(
                            seance=seance,
                            etudiant=etudiant,
                            defaults={
                                "present": False,
                                "justifiee": False,
                                "participation": False,
                                "type_audience_lors_creation": seance.type_audience or "groupe_complet",
                            },
                        )

                    # Marquer que la liste a été générée
                    seance.list_abs_etudiant_generee = True

                seance.save()

                messages.success(request, "تم تحديث الحصة بنجاح")
                return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=seance.classe.id)
            except Exception as save_error:
                messages.error(request, f"خطأ في حفظ البيانات: {str(save_error)}")

        context = {
            "title": "تعديل الحصة",
            "active_menu": "timetable",
            "my_Ens": enseignant,
            "my_Dep": departement,
            "seance": seance,
            "myClasse": seance.classe,
        }

        return render(request, "enseignant/update_seance.html", context)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)


@enseignant_access_required
def delete_seance(request, dep_id, sea_id, enseignant, departement):
    """
    Vue pour supprimer une séance.
    """
    try:
        seance = get_object_or_404(
            Seance.objects.select_related("classe__enseignant__enseignant"),
            id=sea_id,
            classe__enseignant__enseignant=enseignant,
            classe__enseignant__departement=departement,
        )

        clas_id = seance.classe.id
        seance.delete()

        messages.success(request, "تم حذف الحصة بنجاح")
        return redirect("ense:list_Sea_Ens", dep_id=dep_id, clas_id=clas_id)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)
