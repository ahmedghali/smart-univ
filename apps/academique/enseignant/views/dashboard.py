from datetime import timedelta

from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone

from apps.academique.affectation.models import Classe, Ens_Dep, Gestion_Etu_Classe, Seance
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.authentification.utils import get_user_postes_in_departement
from apps.noyau.commun.models import Semestre

from ..services import get_sidebar_context


@enseignant_access_required
def dashboard_Ens(request, dep_id, enseignant, departement):
    """
    Tableau de bord de l'enseignant avec statistiques complètes.
    Affiche les classes, séances, statistiques d'assiduité et graphiques.

    Args:
        dep_id: ID du département (passé par l'URL)
        enseignant: Profil enseignant (injecté par le décorateur)
        departement: Département (injecté par le décorateur)
    """
    try:
        # Données de base
        my_Ens = enseignant
        my_Dep = departement
        my_Fac = my_Dep.faculte
        today = timezone.now().date()

        # Mettre à jour la session avec le département actuel
        request.session["selected_departement_id"] = my_Dep.id

        # Mapping des jours pour aujourd'hui
        day_mapping = {
            "Monday": "Lundi",
            "Tuesday": "Mardi",
            "Wednesday": "Mercredi",
            "Thursday": "Jeudi",
            "Friday": "Vendredi",
            "Saturday": "Samedi",
            "Sunday": "Dimanche",
        }
        today_french = day_mapping.get(today.strftime("%A"), "Lundi")

        # Gestion du semestre
        semestre_selected = request.GET.get("semestre", "1")
        try:
            semestre_obj = Semestre.objects.get(numero=semestre_selected)
        except Semestre.DoesNotExist:
            semestre_obj = Semestre.objects.filter(numero="1").first()
            if not semestre_obj:
                semestre_obj = Semestre.objects.create(numero="1", nom="السداسي الأول")
            semestre_selected = str(semestre_obj.numero)

        all_semestres = Semestre.objects.all().order_by("numero")

        # Classes de l'enseignant
        try:
            mes_classes = (
                Classe.objects.filter(enseignant__enseignant=my_Ens, semestre=semestre_obj)
                .select_related("matiere", "niv_spe_dep_sg", "semestre")
                .order_by("jour", "temps", "matiere__nom_fr")
            )
        except Exception:
            mes_classes = Classe.objects.none()

        # ========== STATISTIQUES DE BASE ==========

        # Comptage sécurisé des étudiants
        total_etudiants = 0
        try:
            niv_spe_dep_sgs = mes_classes.values_list("niv_spe_dep_sg", flat=True).distinct()
            for niv_spe_dep_sg_id in niv_spe_dep_sgs:
                count = Etudiant.objects.filter(niv_spe_dep_sg_id=niv_spe_dep_sg_id).count()
                total_etudiants += count
        except Exception:
            total_etudiants = 0

        # Statistiques principales
        stats_enseignant = {
            "total_classes": mes_classes.count(),
            "total_matieres": mes_classes.values("matiere").distinct().count(),
            "total_etudiants": total_etudiants,
            "niveaux_count": mes_classes.values("niv_spe_dep_sg__niv_spe_dep").distinct().count(),
            "specialites_count": mes_classes.values("niv_spe_dep_sg__niv_spe_dep__specialite").distinct().count(),
            "volume_horaire": round(mes_classes.count() * 1.5, 1),
        }

        # Taux de réalisation
        classes_avec_seances = mes_classes.filter(seance_created=True).count()
        if mes_classes.count() > 0:
            taux_realisation = round((classes_avec_seances / mes_classes.count()) * 100, 1)
        else:
            taux_realisation = 0
        stats_enseignant["taux_realisation"] = taux_realisation

        # Répartition par type
        stats_repartition = {
            "cours": mes_classes.filter(type="Cours").count(),
            "td": mes_classes.filter(type="TD").count(),
            "tp": mes_classes.filter(type="TP").count(),
            "ss": mes_classes.filter(type="Sortie").count(),
        }

        # ========== EMPLOI DU TEMPS AUJOURD'HUI ==========

        try:
            classes_today = mes_classes.filter(jour=today_french).order_by("temps")

            # Mise à jour des taux d'avancement
            for classe in classes_today:
                if classe.seance_created and not hasattr(classe, "taux_avancement"):
                    try:
                        all_seances = Seance.objects.filter(classe=classe).count()
                        seances_faites = Seance.objects.filter(classe=classe, fait=True).count()
                        if all_seances > 0:
                            classe.taux_avancement = round((seances_faites / all_seances) * 100)
                        else:
                            classe.taux_avancement = 0
                    except Exception:
                        classe.taux_avancement = 0
        except Exception:
            classes_today = []

        # ========== STATISTIQUES D'ASSIDUITÉ ==========

        stats_assiduite = {
            "taux_presence_general": 85.0,
            "total_absences": 0,
            "absences_justifiees": 0,
            "etudiants_risque": 0,
        }

        try:
            absences_total = 0
            absences_justifiees_total = 0

            for classe in mes_classes:
                if classe.abs_liste_Etu:
                    absences_classe = Gestion_Etu_Classe.objects.filter(classe=classe)
                    absences_total += sum([abs_obj.nbr_absence or 0 for abs_obj in absences_classe])
                    absences_justifiees_total += sum(
                        [abs_obj.nbr_absence_justifiee or 0 for abs_obj in absences_classe]
                    )

            stats_assiduite.update(
                {
                    "total_absences": absences_total,
                    "absences_justifiees": absences_justifiees_total,
                    "etudiants_risque": max(0, absences_total - absences_justifiees_total) // 3,
                }
            )

            if absences_total > 0:
                total_seances_estimees = mes_classes.count() * 10
                taux_presence = max(0, ((total_seances_estimees - absences_total) / total_seances_estimees) * 100)
                stats_assiduite["taux_presence_general"] = round(taux_presence, 1)

        except Exception:
            pass

        # ========== ACTIVITÉS RÉCENTES ==========

        activites_recentes = []
        try:
            for i, classe in enumerate(mes_classes[:3]):
                activites_recentes.append(
                    {
                        "type": "classe",
                        "titre": f"{classe.matiere.nom_fr}",
                        "description": f"{classe.type} - {classe.niv_spe_dep_sg}",
                        "date": today - timedelta(days=i),
                    }
                )
        except Exception:
            pass

        # ========== NOTIFICATIONS ==========

        notifications = []

        classes_sans_seances = mes_classes.filter(seance_created=False).count()
        if classes_sans_seances > 0:
            notifications.append(
                {
                    "type": "warning",
                    "icon": "exclamation-triangle",
                    "titre": "تنبيه:",
                    "message": f"لديك {classes_sans_seances} حصة بدون دروس منشأة",
                }
            )

        if classes_today:
            notifications.append(
                {
                    "type": "info",
                    "icon": "calendar-day",
                    "titre": "تذكير:",
                    "message": f"لديك {len(list(classes_today))} حصة مجدولة اليوم",
                }
            )

        if not notifications:
            notifications.append(
                {"type": "success", "icon": "check-circle", "titre": "ممتاز!", "message": "جميع حصصك منظمة بشكل جيد"}
            )

        # ========== CONTEXTE FINAL ==========

        # Récupérer les postes administratifs de l'enseignant dans ce département
        admin_postes = get_user_postes_in_departement(request.user, my_Dep.id)

        # Récupérer les autres départements de l'enseignant (hors département actuel)
        autres_departements = (
            Ens_Dep.objects.filter(enseignant=my_Ens, est_actif=True)
            .exclude(departement=my_Dep)
            .select_related("departement", "departement__faculte")
        )

        context = {
            "title": "لوحة التحكم - الأستاذ",
            "my_Ens": my_Ens,
            "my_Dep": my_Dep,
            "my_Fac": my_Fac,
            "today": today,
            "all_semestres": all_semestres,
            "semestre_selected": semestre_selected,
            "semestre_obj": semestre_obj,
            "mes_classes": mes_classes,
            "classes_today": classes_today,
            "stats_enseignant": stats_enseignant,
            "stats_repartition": stats_repartition,
            "stats_assiduite": stats_assiduite,
            "activites_recentes": activites_recentes,
            "notifications": notifications,
            # Postes administratifs pour le basculement
            "admin_postes": admin_postes,
            "has_admin_postes": admin_postes.exists(),
            # Autres départements pour le basculement
            "autres_departements": autres_departements,
            "has_autres_departements": autres_departements.exists(),
            # Compatibilité avec l'ancien template
            "enseignant": my_Ens,
            "departement": my_Dep,
        }

        return render(request, "enseignant/dashboard_Ens.html", context)

    except Exception as e:
        messages.error(request, f"حدث خطأ في تحميل لوحة التحكم: {str(e)}")

        # Context minimal de fallback avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "لوحة التحكم - الأستاذ",
                "active_menu": "dashboard",
                "today": timezone.now().date(),
                "all_semestres": Semestre.objects.all().order_by("numero"),
                "semestre_selected": "1",
                "mes_classes": [],
                "classes_today": [],
                "stats_enseignant": {
                    "total_classes": 0,
                    "total_matieres": 0,
                    "total_etudiants": 0,
                    "niveaux_count": 0,
                    "specialites_count": 0,
                    "volume_horaire": 0,
                    "taux_realisation": 0,
                },
                "stats_repartition": {"cours": 0, "td": 0, "tp": 0, "ss": 0},
                "stats_assiduite": {
                    "taux_presence_general": 0,
                    "total_absences": 0,
                    "absences_justifiees": 0,
                    "etudiants_risque": 0,
                },
                "activites_recentes": [],
                "notifications": [
                    {
                        "type": "danger",
                        "icon": "exclamation-circle",
                        "titre": "خطأ:",
                        "message": "حدث خطأ في تحميل البيانات",
                    }
                ],
                # Compatibilité avec l'ancien template
                "enseignant": enseignant,
                "departement": departement,
            }
        )
        return render(request, "enseignant/dashboard_Ens.html", context)
