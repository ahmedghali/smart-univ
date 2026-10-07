from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.academique.affectation.models import Classe, Gestion_Etu_Classe
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required

from ..services import get_sidebar_context


@enseignant_access_required
def list_Notes_Etu_Classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour afficher et gérer les notes des étudiants d'une classe.
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

        # Récupérer ou créer les entrées de notes pour tous les étudiants
        niv_spe_dep_sg = myClasse.niv_spe_dep_sg

        # Pour les Cours, récupérer les étudiants de tous les groupes de la section
        if myClasse.type == "Cours" and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
            from apps.academique.departement.models import NivSpeDep_SG

            groupes_de_section = NivSpeDep_SG.objects.filter(
                niv_spe_dep=niv_spe_dep_sg.niv_spe_dep, section=niv_spe_dep_sg.section, groupe__isnull=False
            )
            etudiants = Etudiant.objects.filter(niv_spe_dep_sg__in=groupes_de_section, est_actif=True).distinct()
        else:
            etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg, est_actif=True)

        # Créer les entrées Gestion_Etu_Classe pour les étudiants qui n'en ont pas
        for etudiant in etudiants:
            Gestion_Etu_Classe.objects.get_or_create(classe=myClasse, etudiant=etudiant)

        # Récupérer toutes les notes de la classe
        # Note: taux_presence_pourcentage et nombre_participations sont des @property
        # calculées automatiquement par le modèle, pas besoin de les assigner
        all_Notes_Classe = (
            Gestion_Etu_Classe.objects.filter(classe=myClasse)
            .select_related("etudiant")
            .order_by("etudiant__nom_fr", "etudiant__prenom_fr")
        )

        # Statistiques de la classe
        statistiques = Gestion_Etu_Classe.get_statistiques_classe(myClasse)

        if request.method == "POST":
            # Sauvegarde des notes (note_presence est calculée automatiquement)
            from decimal import Decimal, InvalidOperation

            def safe_decimal(value, default=Decimal("0")):
                """
                Convertit une valeur en Decimal de manière sûre.
                Retourne default si vide ou invalide.
                """
                if value is None:
                    return default
                value_str = str(value).strip()
                if value_str == "":
                    return default
                try:
                    return Decimal(value_str)
                except (InvalidOperation, ValueError):
                    return default

            notes_saved = 0

            for note in all_Notes_Classe:
                if note.validee_par_enseignant:
                    continue  # Ne pas modifier les notes validées

                etudiant_id = note.etudiant.id

                # Récupérer les valeurs POST
                hw_raw = request.POST.get(f"note_participe_HW_{etudiant_id}")
                c1_raw = request.POST.get(f"note_controle_1_{etudiant_id}")
                c2_raw = request.POST.get(f"note_controle_2_{etudiant_id}")
                obs_raw = request.POST.get(f"obs_{etudiant_id}", "")

                # Convertir en Decimal (utiliser la valeur existante si vide)
                note.note_participe_HW = safe_decimal(hw_raw, note.note_participe_HW or Decimal("0"))
                note.note_controle_1 = safe_decimal(c1_raw, note.note_controle_1 or Decimal("0"))
                note.note_controle_2 = safe_decimal(c2_raw, note.note_controle_2 or Decimal("0"))
                note.obs = obs_raw if obs_raw is not None else (note.obs or "")

                note.save()
                notes_saved += 1

            messages.success(request, f"تم حفظ النقاط بنجاح ({notes_saved} طالب)")
            return redirect("ense:list_Notes_Etu_Classe", dep_id=dep_id, clas_id=clas_id)

        # Vérifier si les notes sont validées
        notes_validees = all_Notes_Classe.filter(validee_par_enseignant=True).exists()

        # Préparer les valeurs avec des fallbacks pour éviter les erreurs
        matiere_nom = myClasse.matiere.nom_ar if myClasse.matiere else "غير محدد"
        matiere_nom_fr = myClasse.matiere.nom_fr if myClasse.matiere else ""
        niv_spe_dep_sg_str = str(myClasse.niv_spe_dep_sg) if myClasse.niv_spe_dep_sg else "غير محدد"

        # Nom complet de la matière avec type
        matiere_complet = f"{matiere_nom}"
        if matiere_nom_fr:
            matiere_complet += f" / {matiere_nom_fr}"

        # Recalculer les notes de présence et finales via le modèle (A10)
        Gestion_Etu_Classe.update_all_presence_notes_for_classe(myClasse)

        # Récupérer les notes avec valeurs fraîches depuis la base de données
        all_Notes_Classe = list(
            Gestion_Etu_Classe.objects.filter(classe=myClasse)
            .select_related("etudiant")
            .order_by("etudiant__nom_fr", "etudiant__prenom_fr")
        )

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": f"نقاط الطلاب - {matiere_nom}",
                "active_menu": "timetable",
                "my_Clas": myClasse,
                "all_Notes_Classe": all_Notes_Classe,
                "statistiques": statistiques,
                "titre_00": niv_spe_dep_sg_str,
                "titre_01": matiere_complet,
                "type_classe": myClasse.type,
                "notes_validees": notes_validees,
            }
        )

        return render(request, "enseignant/list_Notes_Etu_Classe.html", context)

    except Exception as e:
        messages.error(request, f"خطأ في صفحة النقاط: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)


@enseignant_access_required
def valider_notes_classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour valider toutes les notes d'une classe.
    Nécessite la vérification du mot de passe de l'utilisateur.
    """
    if request.method == "POST":
        try:
            # Vérifier le mot de passe de l'utilisateur
            password = request.POST.get("password", "")
            user = request.user

            if not user.check_password(password):
                messages.error(request, "كلمة المرور غير صحيحة")
                return redirect("ense:list_Notes_Etu_Classe", dep_id=dep_id, clas_id=clas_id)

            myClasse = get_object_or_404(
                Classe, id=clas_id, enseignant__enseignant=enseignant, enseignant__departement=departement
            )

            # Valider toutes les notes de la classe
            Gestion_Etu_Classe.objects.filter(classe=myClasse, validee_par_enseignant=False).update(
                validee_par_enseignant=True, date_validation=timezone.now()
            )

            # Marquer la classe comme ayant ses notes validées
            myClasse.notes_liste_Etu = True
            myClasse.save()

            messages.success(request, "تم تصديق جميع النقاط بنجاح")
        except Exception as e:
            messages.error(request, f"خطأ: {str(e)}")

    return redirect("ense:list_Notes_Etu_Classe", dep_id=dep_id, clas_id=clas_id)


@enseignant_access_required
def creer_notes_classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour créer les entrées de notes pour tous les étudiants d'une classe.
    """
    try:
        myClasse = get_object_or_404(
            Classe, id=clas_id, enseignant__enseignant=enseignant, enseignant__departement=departement
        )

        niv_spe_dep_sg = myClasse.niv_spe_dep_sg

        # Pour les Cours, récupérer les étudiants de tous les groupes de la section
        if myClasse.type == "Cours" and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
            from apps.academique.departement.models import NivSpeDep_SG

            groupes_de_section = NivSpeDep_SG.objects.filter(
                niv_spe_dep=niv_spe_dep_sg.niv_spe_dep, section=niv_spe_dep_sg.section, groupe__isnull=False
            )
            etudiants = Etudiant.objects.filter(niv_spe_dep_sg__in=groupes_de_section, est_actif=True).distinct()
        else:
            etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg, est_actif=True)

        # Créer les entrées pour chaque étudiant
        created_count = 0
        for etudiant in etudiants:
            _, created = Gestion_Etu_Classe.objects.get_or_create(classe=myClasse, etudiant=etudiant)
            if created:
                created_count += 1

        if created_count > 0:
            messages.success(request, f"تم إنشاء قائمة النقاط ({created_count} طالب)")
        else:
            messages.info(request, "قائمة النقاط موجودة بالفعل")

        return redirect("ense:list_Notes_Etu_Classe", dep_id=dep_id, clas_id=clas_id)

    except Exception as e:
        messages.error(request, f"خطأ: {str(e)}")
        return redirect("ense:timeTable_Ens", dep_id=dep_id)
