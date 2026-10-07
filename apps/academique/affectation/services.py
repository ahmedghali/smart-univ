from decimal import Decimal


def get_classe_duration_hours(classe):
    """Calcule la durée d'une classe en heures (ex: 1h30 = 1.50)."""
    try:
        if classe.temps and "-" in classe.temps:
            start_str, end_str = classe.temps.split("-")
            h1, m1 = map(int, start_str.strip().split(":"))
            h2, m2 = map(int, end_str.strip().split(":"))
            diff_minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
            if diff_minutes > 0:
                return Decimal(str(round(diff_minutes / 60.0, 2)))
    except Exception:
        pass
    return Decimal("1.50")


def recalculer_statistiques_ens_dep(ens_dep):
    """
    Recalcule l'ensemble des compteurs de séances et de volumes horaires
    d'un objet Ens_Dep à partir de ses classes réelles (A09).
    """
    from apps.academique.affectation.models import Classe

    classes = Classe.objects.filter(enseignant=ens_dep).select_related("semestre", "niv_spe_dep_sg__niv_spe_dep")

    def init_stats():
        return {
            "all": 0,
            "in": 0,
            "out": 0,
            "cours_in": 0,
            "td_in": 0,
            "tp_in": 0,
            "ss_in": 0,
            "cours_out": 0,
            "td_out": 0,
            "tp_out": 0,
            "ss_out": 0,
            "jours_in": set(),
            "vol_in": Decimal("0.00"),
            "vol_out": Decimal("0.00"),
        }

    s1_stats = init_stats()
    s2_stats = init_stats()

    for c in classes:
        # Déterminer si Semestre 1 ou Semestre 2
        sem_num = getattr(c.semestre, "numero", 1) or 1
        sem_code = (getattr(c.semestre, "code", "") or "").upper()
        is_s1 = True
        if "2" in sem_code or "4" in sem_code or "6" in sem_code or sem_num % 2 == 0:
            is_s1 = False

        stats = s1_stats if is_s1 else s2_stats
        stats["all"] += 1

        duration = get_classe_duration_hours(c)

        # Vérifier si la classe se déroule dans le département de rattachement
        classe_dep_id = None
        if c.niv_spe_dep_sg and c.niv_spe_dep_sg.niv_spe_dep:
            classe_dep_id = c.niv_spe_dep_sg.niv_spe_dep.departement_id

        is_in_dep = (classe_dep_id == ens_dep.departement_id) or (classe_dep_id is None)
        ctype = (c.type or "").lower()

        if is_in_dep:
            stats["in"] += 1
            stats["vol_in"] += duration
            if c.jour:
                stats["jours_in"].add(c.jour)

            if "cours" in ctype:
                stats["cours_in"] += 1
            elif "td" in ctype:
                stats["td_in"] += 1
            elif "tp" in ctype:
                stats["tp_in"] += 1
            elif "sortie" in ctype or "ss" in ctype:
                stats["ss_in"] += 1
        else:
            stats["out"] += 1
            stats["vol_out"] += duration

            if "cours" in ctype:
                stats["cours_out"] += 1
            elif "td" in ctype:
                stats["td_out"] += 1
            elif "tp" in ctype:
                stats["tp_out"] += 1
            elif "sortie" in ctype or "ss" in ctype:
                stats["ss_out"] += 1

    # Affecter Semestre 1
    ens_dep.nbrClas_ALL_Dep_S1 = s1_stats["all"]
    ens_dep.nbrClas_in_Dep_S1 = s1_stats["in"]
    ens_dep.nbrClas_out_Dep_S1 = s1_stats["out"]
    ens_dep.nbrClas_Cours_in_Dep_S1 = s1_stats["cours_in"]
    ens_dep.nbrClas_TD_in_Dep_S1 = s1_stats["td_in"]
    ens_dep.nbrClas_TP_in_Dep_S1 = s1_stats["tp_in"]
    ens_dep.nbrClas_SS_in_Dep_S1 = s1_stats["ss_in"]
    ens_dep.nbrClas_Cours_out_Dep_S1 = s1_stats["cours_out"]
    ens_dep.nbrClas_TD_out_Dep_S1 = s1_stats["td_out"]
    ens_dep.nbrClas_TP_out_Dep_S1 = s1_stats["tp_out"]
    ens_dep.nbrClas_SS_out_Dep_S1 = s1_stats["ss_out"]
    ens_dep.nbrJour_in_Dep_S1 = len(s1_stats["jours_in"])
    ens_dep.volHor_in_Dep_S1 = s1_stats["vol_in"]
    ens_dep.volHor_out_Dep_S1 = s1_stats["vol_out"]

    # Affecter Semestre 2
    ens_dep.nbrClas_ALL_Dep_S2 = s2_stats["all"]
    ens_dep.nbrClas_in_Dep_S2 = s2_stats["in"]
    ens_dep.nbrClas_out_Dep_S2 = s2_stats["out"]
    ens_dep.nbrClas_Cours_in_Dep_S2 = s2_stats["cours_in"]
    ens_dep.nbrClas_TD_in_Dep_S2 = s2_stats["td_in"]
    ens_dep.nbrClas_TP_in_Dep_S2 = s2_stats["tp_in"]
    ens_dep.nbrClas_SS_in_Dep_S2 = s2_stats["ss_in"]
    ens_dep.nbrClas_Cours_out_Dep_S2 = s2_stats["cours_out"]
    ens_dep.nbrClas_TD_out_Dep_S2 = s2_stats["td_out"]
    ens_dep.nbrClas_TP_out_Dep_S2 = s2_stats["tp_out"]
    ens_dep.nbrClas_SS_out_Dep_S2 = s2_stats["ss_out"]
    ens_dep.nbrJour_in_Dep_S2 = len(s2_stats["jours_in"])
    ens_dep.volHor_in_Dep_S2 = s2_stats["vol_in"]
    ens_dep.volHor_out_Dep_S2 = s2_stats["vol_out"]

    ens_dep.save()
    return ens_dep


def recalculer_avancement_classe(classe):
    """Recalcule et met à jour le taux d'avancement de la classe en fonction des séances effectuées (R3)."""
    if not classe:
        return 0
    from apps.academique.affectation.models import Classe

    total = classe.seances_classe.count()
    if total > 0:
        fait = classe.seances_classe.filter(fait=True).count()
        taux = round((fait / total) * 100)
    else:
        taux = 0
    Classe.objects.filter(pk=classe.pk).update(taux_avancement=taux)
    classe.taux_avancement = taux
    return taux


def recalculer_statistiques_nivspedep(niv_spe_dep):
    """Recalcule le nombre de matières S1, S2 et le nombre d'étudiants pour un NivSpeDep (R3)."""
    if not niv_spe_dep:
        return None
    from apps.academique.departement.models import Matiere, NivSpeDep
    from apps.academique.etudiant.models import Etudiant

    s1 = Matiere.objects.filter(niv_spe_dep=niv_spe_dep, semestre__numero=1).count()
    s2 = Matiere.objects.filter(niv_spe_dep=niv_spe_dep, semestre__numero=2).count()
    nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep=niv_spe_dep).count()

    NivSpeDep.objects.filter(pk=niv_spe_dep.pk).update(
        nbr_matieres_s1=s1,
        nbr_matieres_s2=s2,
        nbr_etudiants=nbr_etu,
    )
    niv_spe_dep.nbr_matieres_s1 = s1
    niv_spe_dep.nbr_matieres_s2 = s2
    niv_spe_dep.nbr_etudiants = nbr_etu
    return niv_spe_dep


def recalculer_statistiques_nivspedep_sg(niv_spe_dep_sg):
    """Recalcule le nombre d'étudiants pour un NivSpeDep_SG selon le type d'affectation (R3)."""
    if not niv_spe_dep_sg:
        return None
    from apps.academique.departement.models import NivSpeDep_SG
    from apps.academique.etudiant.models import Etudiant

    type_aff = getattr(niv_spe_dep_sg, "type_affectation", "par_groupe")
    if type_aff == "par_groupe":
        nbr = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).count()
    elif type_aff == "par_section":
        nbr = Etudiant.objects.filter(
            niv_spe_dep_sg__niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
            niv_spe_dep_sg__section=niv_spe_dep_sg.section,
            niv_spe_dep_sg__type_affectation="par_groupe",
        ).count()
    elif type_aff == "tous_etudiants":
        nbr = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep=niv_spe_dep_sg.niv_spe_dep).count()
    else:
        nbr = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).count()

    NivSpeDep_SG.objects.filter(pk=niv_spe_dep_sg.pk).update(nbr_etudiants_SG=nbr)
    niv_spe_dep_sg.nbr_etudiants_SG = nbr
    return niv_spe_dep_sg


def recalculer_tous_les_compteurs():
    """Recalcule l'ensemble des statistiques et compteurs existants (A09, R3)."""
    from apps.academique.affectation.models import Classe, Ens_Dep
    from apps.academique.departement.models import NivSpeDep, NivSpeDep_SG

    counts = {
        "ens_dep": 0,
        "classes": 0,
        "niv_spe_dep": 0,
        "niv_spe_dep_sg": 0,
    }

    for ens_dep in Ens_Dep.objects.all():
        recalculer_statistiques_ens_dep(ens_dep)
        counts["ens_dep"] += 1

    for classe in Classe.objects.all():
        recalculer_avancement_classe(classe)
        counts["classes"] += 1

    for nsd in NivSpeDep.objects.all():
        recalculer_statistiques_nivspedep(nsd)
        counts["niv_spe_dep"] += 1

    for nsd_sg in NivSpeDep_SG.objects.all():
        recalculer_statistiques_nivspedep_sg(nsd_sg)
        counts["niv_spe_dep_sg"] += 1

    return counts
