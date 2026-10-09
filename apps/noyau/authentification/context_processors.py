# apps/noyau/authentification/context_processors.py

from apps.noyau.authentification.constants import ROLE_LABELS, ROLE_TITLES


def auth_roles_context(request):
    """
    Injecte automatiquement dans tous les templates :
    - current_role : code du rôle actif
    - current_role_label : intitulé complet du rôle (ex: لوحة تحكم الأستاذ)
    - current_role_title : titre précis du poste (ex: أستاذ، رئيس القسم، مسؤول النظام)
    - roles_count : nombre de rôles disponibles
    Évite tout fallback générique tel que 'عضو' ou 'مستخدم'.
    """
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {}

    user = request.user
    current_role = request.session.get("current_role", "")
    roles_count = request.session.get("roles_count", 1)

    my_Ens = getattr(user, "enseignant_profile", None)
    my_Etu = getattr(user, "etudiant_profile", None)

    # Titre précis du rôle / poste selon le genre
    role_title = ROLE_TITLES.get(current_role, "")
    if current_role == "enseignant" and my_Ens and getattr(my_Ens, "is_feminin", False):
        role_title = "أستاذة"
    elif current_role == "etudiant" and my_Etu and getattr(my_Etu, "is_feminin", False):
        role_title = "طالبة"
    elif not role_title:
        if user.is_superuser or user.is_staff:
            role_title = "مسؤول النظام"
        elif my_Ens:
            role_title = "أستاذة" if getattr(my_Ens, "is_feminin", False) else "أستاذ"
        elif my_Etu:
            role_title = "طالبة" if getattr(my_Etu, "is_feminin", False) else "طالب"
        else:
            role_title = "مسؤول النظام"

    role_label = ROLE_LABELS.get(current_role, role_title)
    if current_role == "enseignant" and my_Ens and getattr(my_Ens, "is_feminin", False):
        role_label = "لوحة تحكم الأستاذة"
    elif current_role == "etudiant" and my_Etu and getattr(my_Etu, "is_feminin", False):
        role_label = "لوحة تحكم الطالبة"

    # Année universitaire courante depuis la base de données
    annee_courante = None
    try:
        from apps.noyau.commun.models import AnneeUniversitaire
        annee_courante = AnneeUniversitaire.get_courante()
    except Exception:
        pass

    # Détection si l'utilisateur occupe un poste administratif actif
    is_admin_poste = False
    if user.is_superuser:
        is_admin_poste = True
    elif current_role in [
        "chef_departement", "chef_dep_adj_p", "chef_dep_adj_pg",
        "doyen", "vice_doyen_p", "vice_doyen_pg",
        "recteur", "vice_rect_p", "vice_rect_pg",
    ]:
        is_admin_poste = True
    else:
        try:
            from apps.noyau.commun.models import AffectationPoste, PostePermission
            if AffectationPoste.actives(user).filter(niveau_contexte=AffectationPoste.NIVEAU_DEPARTEMENT).exists():
                perms = PostePermission.get_permissions(request)
                is_admin_poste = any(perms.values())
        except Exception:
            pass

    # Récupération automatique du département et de la faculté pour toutes les pages
    shell_my_Dep = None
    shell_my_Fac = None
    selected_dep_id = request.session.get("selected_departement_id")
    if selected_dep_id:
        try:
            from apps.academique.departement.models import Departement
            shell_my_Dep = Departement.objects.select_related("faculte").filter(id=selected_dep_id).first()
            if shell_my_Dep:
                shell_my_Fac = shell_my_Dep.faculte
        except Exception:
            pass
    elif my_Ens and getattr(my_Ens, "departement", None):
        shell_my_Dep = my_Ens.departement
        shell_my_Fac = shell_my_Dep.faculte if shell_my_Dep else None
    elif my_Etu and getattr(my_Etu, "departement", None):
        shell_my_Dep = my_Etu.departement
        shell_my_Fac = shell_my_Dep.faculte if shell_my_Dep else None

    return {
        "current_role": current_role,
        "current_role_label": role_label,
        "current_role_title": role_title,
        "roles_count": roles_count,
        "annee_courante": annee_courante,
        "is_admin_poste": is_admin_poste,
        "my_Ens": my_Ens,
        "my_Etu": my_Etu,
        "shell_my_Dep": shell_my_Dep,
        "shell_my_Fac": shell_my_Fac,
        "departement": shell_my_Dep,
        "faculte": shell_my_Fac,
    }
