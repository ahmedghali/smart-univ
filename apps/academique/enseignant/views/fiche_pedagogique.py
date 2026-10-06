import traceback

from django.contrib import messages
from django.shortcuts import redirect, render

from apps.academique.affectation.models import (
    Classe,
    Ens_Dep,
)
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import AnneeUniversitaire

from ..services import get_sidebar_context


@enseignant_access_required
def fichPeda_Ens_Semestre(request, dep_id, enseignant, departement):
    """
    Vue pour la fiche pédagogique semestrielle de l'enseignant
    """
    try:
        # Récupérer l'enseignant-département
        try:
            my_Ens = Ens_Dep.objects.select_related("enseignant", "departement").get(
                enseignant=enseignant, departement=departement
            )
        except Ens_Dep.DoesNotExist:
            messages.error(request, "غير مصرح لك بالوصول إلى هذا القسم")
            return redirect("ense:dashboard_Ens", dep_id=dep_id)

        # Récupérer le semestre sélectionné (défaut: 1)
        semestre_selected = request.GET.get("semestre", "1")

        # Filtre de base pour les classes
        base_filter = {
            "enseignant__enseignant": my_Ens.enseignant,
            "enseignant__departement": departement,
            "semestre__numero": semestre_selected,
        }

        # Récupérer les classes par jour dans l'ordre souhaité
        jours = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]
        all_Classe_Ens = []

        for jour in jours:
            classes_jour = (
                Classe.objects.filter(**base_filter, jour=jour)
                .select_related(
                    "matiere__unite",
                    "niv_spe_dep_sg__niv_spe_dep__niveau",
                    "niv_spe_dep_sg__niv_spe_dep__specialite",
                    "niv_spe_dep_sg__section",
                    "niv_spe_dep_sg__groupe",
                )
                .order_by("temps")
            )
            all_Classe_Ens.extend(classes_jour)

        # Calculer les statistiques
        all_classes = len(all_Classe_Ens)

        # Calculer les volumes horaires
        vol_hor_cours = sum([2.25 for x in all_Classe_Ens if x.type == "Cours"])
        vol_hor_TD = sum([1.5 for x in all_Classe_Ens if x.type == "TD"])
        vol_hor_TP = sum([1.5 for x in all_Classe_Ens if x.type == "TP"])
        vol_hor_Total = vol_hor_cours + vol_hor_TD + vol_hor_TP

        # Informations de l'université
        univ = "جامعة قاصدي مرباح ورقلة"

        # Année universitaire courante
        annee_univ = AnneeUniversitaire.objects.filter(est_courante=True).first()

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": f"البطاقة البيداغوجية - السداسي {semestre_selected}",
                "active_menu": "dashboard",
                "semestre_selected": semestre_selected,
                "all_Classe_Ens": all_Classe_Ens,
                "all_classes": all_classes,
                "vol_hor_cours": vol_hor_cours,
                "vol_hor_TD": vol_hor_TD,
                "vol_hor_TP": vol_hor_TP,
                "vol_hor_Total": vol_hor_Total,
                "univ": univ,
                "annee_univ": annee_univ,
            }
        )

        return render(request, "enseignant/fichPeda_Ens_Semestre.html", context)

    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل البطاقة البيداغوجية: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)


@enseignant_access_required
def fichePedagogique(request, dep_id, enseignant, departement):
    """
    Vue pour la fiche pédagogique globale (deux semestres sur une page A4 paysage)
    """
    try:
        # Récupérer l'enseignant-département
        try:
            my_Ens = Ens_Dep.objects.select_related("enseignant", "departement").get(
                enseignant=enseignant, departement=departement
            )
        except Ens_Dep.DoesNotExist:
            messages.error(request, "غير مصرح لك بالوصول إلى هذا القسم")
            return redirect("ense:dashboard_Ens", dep_id=dep_id)

        # Filtre de base pour les classes S1
        base_filter_S1 = {
            "enseignant__enseignant": my_Ens.enseignant,
            "enseignant__departement": departement,
            "semestre__numero": 1,
        }

        # Filtre de base pour les classes S2
        base_filter_S2 = {
            "enseignant__enseignant": my_Ens.enseignant,
            "enseignant__departement": departement,
            "semestre__numero": 2,
        }

        # Liste des jours dans l'ordre souhaité
        jours = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]

        # Récupérer les classes pour le semestre 1 par jour
        all_Classe_Ens_S1 = []
        for jour in jours:
            classes_jour = (
                Classe.objects.filter(**base_filter_S1, jour=jour)
                .select_related(
                    "matiere__unite",
                    "niv_spe_dep_sg__niv_spe_dep__niveau",
                    "niv_spe_dep_sg__niv_spe_dep__specialite",
                    "niv_spe_dep_sg__section",
                    "niv_spe_dep_sg__groupe",
                )
                .order_by("temps")
            )
            all_Classe_Ens_S1.extend(classes_jour)

        # Récupérer les classes pour le semestre 2 par jour
        all_Classe_Ens_S2 = []
        for jour in jours:
            classes_jour = (
                Classe.objects.filter(**base_filter_S2, jour=jour)
                .select_related(
                    "matiere__unite",
                    "niv_spe_dep_sg__niv_spe_dep__niveau",
                    "niv_spe_dep_sg__niv_spe_dep__specialite",
                    "niv_spe_dep_sg__section",
                    "niv_spe_dep_sg__groupe",
                )
                .order_by("temps")
            )
            all_Classe_Ens_S2.extend(classes_jour)

        # Calculer les statistiques S1
        all_classes_S1 = len(all_Classe_Ens_S1)
        vol_hor_cours_S1 = sum([2.25 for x in all_Classe_Ens_S1 if x.type == "Cours"])
        vol_hor_TD_S1 = sum([1.5 for x in all_Classe_Ens_S1 if x.type == "TD"])
        vol_hor_TP_S1 = sum([1.5 for x in all_Classe_Ens_S1 if x.type == "TP"])
        vol_hor_Total_S1 = vol_hor_cours_S1 + vol_hor_TD_S1 + vol_hor_TP_S1

        # Calculer les statistiques S2
        all_classes_S2 = len(all_Classe_Ens_S2)
        vol_hor_cours_S2 = sum([2.25 for x in all_Classe_Ens_S2 if x.type == "Cours"])
        vol_hor_TD_S2 = sum([1.5 for x in all_Classe_Ens_S2 if x.type == "TD"])
        vol_hor_TP_S2 = sum([1.5 for x in all_Classe_Ens_S2 if x.type == "TP"])
        vol_hor_Total_S2 = vol_hor_cours_S2 + vol_hor_TD_S2 + vol_hor_TP_S2

        # Total général
        vol_hor_Total_General = vol_hor_Total_S1 + vol_hor_Total_S2

        # Informations de l'université
        univ = "جامعة قاصدي مرباح ورقلة"

        # Année universitaire courante
        annee_univ = AnneeUniversitaire.objects.filter(est_courante=True).first()

        # Contexte avec sidebar commun
        context = get_sidebar_context(request, enseignant, departement)
        context.update(
            {
                "title": "البطاقة البيداغوجية الشاملة",
                "active_menu": "dashboard",
                "all_Classe_Ens_S1": all_Classe_Ens_S1,
                "all_Classe_Ens_S2": all_Classe_Ens_S2,
                "all_classes_S1": all_classes_S1,
                "all_classes_S2": all_classes_S2,
                "vol_hor_cours_S1": vol_hor_cours_S1,
                "vol_hor_TD_S1": vol_hor_TD_S1,
                "vol_hor_TP_S1": vol_hor_TP_S1,
                "vol_hor_Total_S1": vol_hor_Total_S1,
                "vol_hor_cours_S2": vol_hor_cours_S2,
                "vol_hor_TD_S2": vol_hor_TD_S2,
                "vol_hor_TP_S2": vol_hor_TP_S2,
                "vol_hor_Total_S2": vol_hor_Total_S2,
                "vol_hor_Total_General": vol_hor_Total_General,
                "univ": univ,
                "annee_univ": annee_univ,
            }
        )

        return render(request, "enseignant/fichePedagogique.html", context)

    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"خطأ في تحميل البطاقة البيداغوجية الشاملة: {str(e)}")
        return redirect("ense:dashboard_Ens", dep_id=dep_id)
