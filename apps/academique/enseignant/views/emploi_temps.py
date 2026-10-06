import traceback
from collections import defaultdict

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import (
    Abs_Etu_Seance,
    Amphi_Dep,
    Classe,
    Ens_Dep,
    Gestion_Etu_Classe,
    Laboratoire_Dep,
    Salle_Dep,
    Seance,
)
from apps.academique.departement.models import NivSpeDep
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import Semestre

from ..services import TIME_SLOTS, WEEK_DAYS, count_classes_by_type, get_real_department, get_sidebar_context


@enseignant_access_required
def timeTable_Ens(request, dep_id, enseignant, departement):
    """
    Affiche l'emploi du temps de l'enseignant avec statistiques par semestre.
    """
    try:
        # Recuperer le departement permanent de l'enseignant
        real_Dep = get_real_department(enseignant)

        # Recuperer le parametre semestre (par defaut S1)
        semestre_selected = request.GET.get("semestre", "1")

        # Recuperer l'objet semestre
        try:
            semestre_obj = Semestre.objects.get(numero=semestre_selected)
        except Semestre.DoesNotExist:
            semestre_obj = Semestre.objects.filter(numero="1").first()
            semestre_selected = "1"

        my_Dep = departement

        # Variables communes
        all_Classe_Ens = []
        nbr_Cours = 0
        nbr_TP = 0
        nbr_TD = 0
        nbr_SS = 0

        all_Ens_Dep = Ens_Dep.objects.filter(departement=departement.id).order_by("enseignant__nom_ar")

        # Filtre de base pour les classes
        base_filter = {
            "enseignant__departement": my_Dep.id,
            "enseignant__enseignant": enseignant.id,
            "semestre": semestre_obj,
        }

        # Recuperer les classes par jour
        jours = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]
        for jour in jours:
            classes_jour = (
                Classe.objects.filter(**base_filter, jour=jour)
                .select_related("matiere", "niv_spe_dep_sg")
                .order_by("temps")
            )
            all_Classe_Ens.extend(classes_jour)

        # Recuperer les classes par horaire
        all_Classe_Time = []
        for horaire in TIME_SLOTS:
            classes_horaire = Classe.objects.filter(**base_filter, temps=horaire).select_related(
                "matiere", "niv_spe_dep_sg"
            )
            all_Classe_Time.extend(classes_horaire)

        # Compter les types de classes et calculer les taux d'avancement
        for idx1 in all_Classe_Ens:
            if idx1.type == "Cours":
                nbr_Cours += 1
            elif idx1.type == "TP":
                nbr_TP += 1
            elif idx1.type == "TD":
                nbr_TD += 1
            elif idx1.type == "Sortie Scientifique":
                nbr_SS += 1

            # Calculer le taux d'avancement pour les classes avec seances
            if idx1.seance_created:
                all_Seances = Seance.objects.filter(classe=idx1.id)
                nbr_Sea_fait = Seance.objects.filter(classe=idx1.id, fait=True)

                if nbr_Sea_fait.exists() and all_Seances.exists():
                    taux_avancement = ((nbr_Sea_fait.count()) / all_Seances.count()) * 100
                    taux_avancement = round(taux_avancement)
                    idx1.taux_avancement = taux_avancement
                    idx1.save()

            # Vérifier si la classe a des notes et si elles sont validées
            notes_classe = Gestion_Etu_Classe.objects.filter(classe=idx1)
            idx1.has_notes = notes_classe.exists()
            idx1.notes_validees = notes_classe.filter(validee_par_enseignant=True).exists() if idx1.has_notes else False

            # Calculer le total des absences directement depuis Abs_Etu_Seance
            # (plus fiable car mis à jour en temps réel)
            total_abs = Abs_Etu_Seance.objects.filter(seance__classe=idx1, present=False).count()
            idx1.total_absences = total_abs

        all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

        # Recuperer les statistiques depuis Ens_Dep selon le semestre
        stats_classes = {"total": 0, "cours": 0, "td": 0, "tp": 0, "ss": 0, "jours": 0, "vol_horaire": 0}
        if real_Dep:
            if semestre_selected == "1":
                stats_classes = {
                    "total": getattr(real_Dep, "nbrClas_in_Dep_S1", 0) or 0,
                    "cours": getattr(real_Dep, "nbrClas_Cours_in_Dep_S1", 0) or 0,
                    "td": getattr(real_Dep, "nbrClas_TD_in_Dep_S1", 0) or 0,
                    "tp": getattr(real_Dep, "nbrClas_TP_in_Dep_S1", 0) or 0,
                    "ss": getattr(real_Dep, "nbrClas_SS_in_Dep_S1", 0) or 0,
                    "jours": getattr(real_Dep, "nbrJour_in_Dep_S1", 0) or 0,
                    "vol_horaire": getattr(real_Dep, "volHor_in_Dep_S1", 0) or 0,
                }
            else:
                stats_classes = {
                    "total": getattr(real_Dep, "nbrClas_in_Dep_S2", 0) or 0,
                    "cours": getattr(real_Dep, "nbrClas_Cours_in_Dep_S2", 0) or 0,
                    "td": getattr(real_Dep, "nbrClas_TD_in_Dep_S2", 0) or 0,
                    "tp": getattr(real_Dep, "nbrClas_TP_in_Dep_S2", 0) or 0,
                    "ss": getattr(real_Dep, "nbrClas_SS_in_Dep_S2", 0) or 0,
                    "jours": getattr(real_Dep, "nbrJour_in_Dep_S2", 0) or 0,
                    "vol_horaire": getattr(real_Dep, "volHor_in_Dep_S2", 0) or 0,
                }

        # Recuperer tous les semestres disponibles
        all_semestres = Semestre.objects.all().order_by("numero")

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "استعمال الزمن",
                "active_menu": "timetable",
                "all_Classe_Ens": all_Classe_Ens,
                "all_Ens_Dep": all_Ens_Dep,
                "all_Classe_Time": all_Classe_Time,
                "nbr_Cours": nbr_Cours,
                "nbr_TP": nbr_TP,
                "sevenDays": WEEK_DAYS,
                "sixClasses": TIME_SLOTS,
                "nbr_TD": nbr_TD,
                "nbr_SS": nbr_SS,
                "all_classes": all_classes,
                "semestre_selected": semestre_selected,
                "semestre_obj": semestre_obj,
                "all_semestres": all_semestres,
                "stats_classes": stats_classes,
            }
        )
        return render(request, "enseignant/timeTable_Ens.html", context)

    except Exception as e:
        messages.error(request, f"خطأ في تحميل استعمال الزمن: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def timeTable_Niv_Ens(request, dep_id, niv_spe_dep_id, semestre_num, enseignant, departement):
    """
    Emploi du temps d'un NivSpeDep (niveau/spécialité) pour un semestre donné.
    Affiche le planning hebdomadaire des classes.
    """
    # Récupérer le NivSpeDep
    try:
        niv_spe_dep = NivSpeDep.objects.select_related(
            "niveau", "specialite", "specialite__reforme", "specialite__identification", "specialite__parcours"
        ).get(id=niv_spe_dep_id)
    except NivSpeDep.DoesNotExist:
        ctx = get_sidebar_context(request, enseignant, departement)
        ctx.update(
            {
                "error": f"المستوى/التخصص برقم {niv_spe_dep_id} غير موجود",
                "all_classes": 0,
            }
        )
        return render(request, "enseignant/timeTable_Niv_Ens.html", ctx)

    # Vérifier le semestre
    try:
        semestre = Semestre.objects.get(numero=semestre_num)
    except Semestre.DoesNotExist:
        ctx = get_sidebar_context(request, enseignant, departement)
        ctx.update(
            {
                "error": f"السداسي رقم {semestre_num} غير موجود",
                "all_classes": 0,
            }
        )
        return render(request, "enseignant/timeTable_Niv_Ens.html", ctx)

    # Récupérer toutes les classes avec préchargement des relations
    all_Classe_Niv = (
        Classe.objects.filter(
            enseignant__departement=departement, niv_spe_dep_sg__niv_spe_dep=niv_spe_dep, semestre__numero=semestre_num
        )
        .select_related(
            "enseignant__enseignant",
            "matiere",
            "niv_spe_dep_sg__niv_spe_dep__niveau",
            "niv_spe_dep_sg__niv_spe_dep__specialite__reforme",
            "niv_spe_dep_sg__section",
            "niv_spe_dep_sg__groupe",
        )
        .order_by("jour", "temps")
    )

    # Même queryset pour all_Classe_Time
    all_Classe_Time = all_Classe_Niv

    # Statistiques optimisées
    nbr_Cours = all_Classe_Niv.filter(type="Cours").count()
    nbr_TP = all_Classe_Niv.filter(type="TP").count()
    nbr_TD = all_Classe_Niv.filter(type="TD").count()
    nbr_SS = all_Classe_Niv.filter(type="Sortie Scientifique").count()

    all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

    # Contexte avec sidebar commun
    context = get_sidebar_context(request, enseignant, departement)
    context.update(
        {
            "title": "إستعمال الزمن للمستوى",
            "active_menu": "niveaux",
            "all_Classe_Niv": all_Classe_Niv,
            "all_Classe_Time": all_Classe_Time,
            "nbr_Cours": nbr_Cours,
            "nbr_TP": nbr_TP,
            "nbr_TD": nbr_TD,
            "nbr_SS": nbr_SS,
            "all_classes": all_classes,
            "sevenDays": WEEK_DAYS,
            "sixClassesTimes": TIME_SLOTS,
            "niv_spe_dep": niv_spe_dep,
            "niv_spe_dep_id": niv_spe_dep_id,
            "semestre_num": semestre_num,
        }
    )

    return render(request, "enseignant/timeTable_Niv_Ens.html", context)


@enseignant_access_required
def list_Amphi_Ens(request, dep_id, enseignant, departement):
    """Liste des amphithéâtres du département."""
    try:
        base_qs = Amphi_Dep.objects.filter(departement=departement, est_actif=True).select_related("amphi")
        all_S1 = base_qs.filter(semestre_1=True).order_by("amphi__numero")
        all_S2 = base_qs.filter(semestre_2=True).order_by("amphi__numero")

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "قائمة المدرجات",
                "active_menu": "amphi",
                "all_Amphi_Dep_S1": all_S1,
                "all_Amphi_Dep_S2": all_S2,
                "total_amphi_s1": all_S1.count(),
                "total_amphi_s2": all_S2.count(),
                "total_amphi": all_S1.count() + all_S2.count(),
                "capacite_s1": sum(a.amphi.capacite or 0 for a in all_S1),
                "capacite_s2": sum(a.amphi.capacite or 0 for a in all_S2),
            }
        )
        return render(request, "enseignant/list_Amphi_Ens.html", context)
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل قائمة المدرجات: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def list_Salle_Ens(request, dep_id, enseignant, departement):
    """Liste des salles du département."""
    try:
        base_qs = Salle_Dep.objects.filter(departement=departement, est_actif=True).select_related("salle")
        all_S1 = base_qs.filter(semestre_1=True).order_by("salle__numero")
        all_S2 = base_qs.filter(semestre_2=True).order_by("salle__numero")

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "قائمة القاعات",
                "active_menu": "salle",
                "all_Salle_Dep_S1": all_S1,
                "all_Salle_Dep_S2": all_S2,
                "total_salle_s1": all_S1.count(),
                "total_salle_s2": all_S2.count(),
                "total_salle": all_S1.count() + all_S2.count(),
                "capacite_s1": sum(s.salle.capacite or 0 for s in all_S1),
                "capacite_s2": sum(s.salle.capacite or 0 for s in all_S2),
            }
        )
        return render(request, "enseignant/list_Salle_Ens.html", context)
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل قائمة القاعات: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def list_Labo_Ens(request, dep_id, enseignant, departement):
    """Liste des laboratoires du département."""
    try:
        base_qs = Laboratoire_Dep.objects.filter(departement=departement, est_actif=True).select_related("laboratoire")
        all_S1 = base_qs.filter(semestre_1=True).order_by("laboratoire__numero")
        all_S2 = base_qs.filter(semestre_2=True).order_by("laboratoire__numero")

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "قائمة المخابر",
                "active_menu": "labo",
                "all_Labo_Dep_S1": all_S1,
                "all_Labo_Dep_S2": all_S2,
                "total_labo_s1": all_S1.count(),
                "total_labo_s2": all_S2.count(),
                "total_labo": all_S1.count() + all_S2.count(),
                "capacite_s1": sum(l.laboratoire.capacite or 0 for l in all_S1),
                "capacite_s2": sum(l.laboratoire.capacite or 0 for l in all_S2),
            }
        )
        return render(request, "enseignant/list_Labo_Ens.html", context)
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل قائمة المخابر: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def timeTable_Amphi_Ens(request, dep_id, amphi_dep_id, semestre_numero, enseignant, departement):
    """Emploi du temps d'un amphithéâtre."""
    try:
        amphi_dep = get_object_or_404(Amphi_Dep, id=amphi_dep_id, departement=departement, est_actif=True)

        # Vérification semestre
        if (semestre_numero == 1 and not amphi_dep.semestre_1) or (semestre_numero == 2 and not amphi_dep.semestre_2):
            messages.error(request, f"هذا المدرج غير متاح في السداسي {'الأول' if semestre_numero == 1 else 'الثاني'}")
            return redirect("ense:list_Amphi_Ens", dep_id=dep_id)

        # Récupération des classes
        all_Classe_Amp = (
            Classe.objects.filter(
                content_type=ContentType.objects.get_for_model(Amphi_Dep),
                object_id=amphi_dep_id,
                semestre__numero=semestre_numero,
            )
            .select_related(
                "enseignant__enseignant",
                "matiere",
                "semestre",
                "niv_spe_dep_sg__niv_spe_dep__niveau",
                "niv_spe_dep_sg__niv_spe_dep__specialite",
                "niv_spe_dep_sg__niv_spe_dep__departement",
            )
            .order_by("jour", "temps")
        )

        # Groupement par slot et comptage
        classes_by_slot = defaultdict(list)
        for c in all_Classe_Amp:
            classes_by_slot[(c.jour, c.temps)].append(c)
        counts = count_classes_by_type(all_Classe_Amp)

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": f"استعمال الزمن - {amphi_dep.amphi.nom_ar or amphi_dep.amphi.nom_fr}",
                "active_menu": "amphi",
                "amphi_dep": amphi_dep,
                "semestre_numero": semestre_numero,
                "all_Classe_Amp": all_Classe_Amp,
                "classes_by_slot": dict(classes_by_slot),
                "sevenDays": WEEK_DAYS,
                "sixClasses": TIME_SLOTS,
                "nbr_Cours": counts["Cours"],
                "nbr_TP": counts["TP"],
                "nbr_TD": counts["TD"],
                "nbr_SS": counts["SS"],
                "all_classes": counts["total"],
            }
        )
        return render(request, "enseignant/timeTable_Amphi_Ens.html", context)
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل استعمال الزمن: {str(e)}")
        return redirect("ense:list_Amphi_Ens", dep_id=dep_id)


@enseignant_access_required
def timeTable_Salle_Ens(request, dep_id, salle_dep_id, semestre_numero, enseignant, departement):
    """Emploi du temps d'une salle."""
    try:
        salle_dep = get_object_or_404(Salle_Dep, id=salle_dep_id, departement=departement, est_actif=True)

        # Vérification semestre
        if (semestre_numero == 1 and not salle_dep.semestre_1) or (semestre_numero == 2 and not salle_dep.semestre_2):
            messages.error(request, f"هذه القاعة غير متاحة في السداسي {'الأول' if semestre_numero == 1 else 'الثاني'}")
            return redirect("ense:list_Salle_Ens", dep_id=dep_id)

        # Récupération des classes
        all_Classe_Salle = (
            Classe.objects.filter(
                content_type=ContentType.objects.get_for_model(Salle_Dep),
                object_id=salle_dep_id,
                semestre__numero=semestre_numero,
            )
            .select_related(
                "enseignant__enseignant",
                "matiere",
                "semestre",
                "niv_spe_dep_sg__niv_spe_dep__niveau",
                "niv_spe_dep_sg__niv_spe_dep__specialite",
                "niv_spe_dep_sg__niv_spe_dep__departement",
            )
            .order_by("jour", "temps")
        )

        # Groupement par slot et comptage
        classes_by_slot = defaultdict(list)
        for c in all_Classe_Salle:
            classes_by_slot[(c.jour, c.temps)].append(c)
        counts = count_classes_by_type(all_Classe_Salle)

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": f"استعمال الزمن - {salle_dep.salle.nom_ar or salle_dep.salle.nom_fr}",
                "active_menu": "salle",
                "salle_dep": salle_dep,
                "semestre_numero": semestre_numero,
                "all_Classe_Salle": all_Classe_Salle,
                "classes_by_slot": dict(classes_by_slot),
                "sevenDays": WEEK_DAYS,
                "sixClasses": TIME_SLOTS,
                "nbr_Cours": counts["Cours"],
                "nbr_TP": counts["TP"],
                "nbr_TD": counts["TD"],
                "nbr_SS": counts["SS"],
                "all_classes": counts["total"],
            }
        )
        return render(request, "enseignant/timeTable_Salle_Ens.html", context)
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل استعمال الزمن: {str(e)}")
        return redirect("ense:list_Salle_Ens", dep_id=dep_id)


@enseignant_access_required
def timeTable_Labo_Ens(request, dep_id, labo_dep_id, semestre_numero, enseignant, departement):
    """Emploi du temps d'un laboratoire."""
    try:
        labo_dep = get_object_or_404(Laboratoire_Dep, id=labo_dep_id, departement=departement, est_actif=True)

        # Vérification semestre
        if (semestre_numero == 1 and not labo_dep.semestre_1) or (semestre_numero == 2 and not labo_dep.semestre_2):
            messages.error(request, f"هذا المخبر غير متاح في السداسي {'الأول' if semestre_numero == 1 else 'الثاني'}")
            return redirect("ense:list_Labo_Ens", dep_id=dep_id)

        # Récupération des classes
        all_Classe_Labo = (
            Classe.objects.filter(
                content_type=ContentType.objects.get_for_model(Laboratoire_Dep),
                object_id=labo_dep_id,
                semestre__numero=semestre_numero,
            )
            .select_related(
                "enseignant__enseignant",
                "matiere",
                "semestre",
                "niv_spe_dep_sg__niv_spe_dep__niveau",
                "niv_spe_dep_sg__niv_spe_dep__specialite",
                "niv_spe_dep_sg__niv_spe_dep__departement",
            )
            .order_by("jour", "temps")
        )

        counts = count_classes_by_type(all_Classe_Labo)

        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": f"استعمال الزمن - {labo_dep.laboratoire.nom_ar}",
                "active_menu": "labo",
                "labo_dep": labo_dep,
                "semestre_numero": semestre_numero,
                "all_Classe_Labo": all_Classe_Labo,
                "all_Classe_Time": all_Classe_Labo,
                "sevenDays": WEEK_DAYS,
                "sixClasses": TIME_SLOTS,
                "nbr_Cours": counts["Cours"],
                "nbr_TP": counts["TP"],
                "nbr_TD": counts["TD"],
                "nbr_SS": counts["SS"],
                "all_classes": counts["total"],
            }
        )
        return render(request, "enseignant/timeTable_Labo_Ens.html", context)
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل استعمال الزمن: {str(e)}")
        return redirect("ense:list_Labo_Ens", dep_id=dep_id)
