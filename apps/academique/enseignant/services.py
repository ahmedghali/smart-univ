from apps.academique.affectation.models import Ens_Dep
from apps.academique.departement.models import Departement
from apps.noyau.authentification.utils import get_user_postes_in_departement

TIME_SLOTS = [
    "08:00-09:30",
    "09:40-11:10",
    "11:20-12:50",
    "13:10-14:40",
    "14:50-16:20",
    "16:30-18:00",
]


WEEK_DAYS = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]


def get_departement_from_session_or_enseignant(request, enseignant):
    """
    Récupère le département depuis la session ou depuis les affectations de l'enseignant.
    Garantit que my_Dep est toujours disponible pour le menu latéral.
    """
    # 1. Essayer depuis la session
    dep_id = request.session.get("selected_departement_id")
    if dep_id:
        try:
            return Departement.objects.get(id=dep_id)
        except Departement.DoesNotExist:
            pass

    # 2. Essayer depuis les affectations de l'enseignant
    try:
        ens_dep = Ens_Dep.objects.filter(enseignant=enseignant).first()
        if ens_dep:
            # Mettre à jour la session
            request.session["selected_departement_id"] = ens_dep.departement.id
            return ens_dep.departement
    except Exception:
        pass

    return None


def get_sidebar_context(request, enseignant, departement):
    """
    Retourne le contexte commun pour le menu latéral.
    À utiliser dans toutes les vues enseignant pour avoir un sidebar cohérent.
    """
    context = {
        "my_Ens": enseignant,
        "my_Dep": departement,
        "my_Fac": departement.faculte if departement else None,
    }

    # Postes administratifs de l'enseignant dans ce département
    try:
        admin_postes = get_user_postes_in_departement(request.user, departement.id) if departement else []
        context["admin_postes"] = admin_postes
        context["has_admin_postes"] = admin_postes.exists() if hasattr(admin_postes, "exists") else bool(admin_postes)
    except Exception:
        context["admin_postes"] = []
        context["has_admin_postes"] = False

    # Autres départements de l'enseignant (hors département actuel)
    try:
        autres_departements = (
            Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True)
            .exclude(departement=departement)
            .select_related("departement", "departement__faculte")
            if departement
            else []
        )
        context["autres_departements"] = autres_departements
        context["has_autres_departements"] = (
            autres_departements.exists() if hasattr(autres_departements, "exists") else bool(autres_departements)
        )
    except Exception:
        context["autres_departements"] = []
        context["has_autres_departements"] = False

    return context


def get_real_department(enseignant):
    """Récupère le département principal (permanent ou premier) de l'enseignant."""
    try:
        return Ens_Dep.objects.get(enseignant=enseignant, statut="Permanent")
    except Ens_Dep.DoesNotExist:
        return Ens_Dep.objects.filter(enseignant=enseignant).first()


def count_classes_by_type(classes):
    """Compte les classes par type et retourne un dictionnaire."""
    counts = {"Cours": 0, "TP": 0, "TD": 0, "SS": 0}
    for c in classes:
        if c.type == "Cours":
            counts["Cours"] += 1
        elif c.type == "TP":
            counts["TP"] += 1
        elif c.type == "TD":
            counts["TD"] += 1
        elif c.type == "Sortie Scientifique":
            counts["SS"] += 1
    counts["total"] = sum(counts.values())
    return counts


def _safe_str(value, default="-"):
    """Helper function to safely convert value to string, handling encoding errors."""
    if value is None:
        return default
    try:
        return str(value)
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            # Try to decode as latin-1 if utf-8 fails
            if isinstance(value, bytes):
                return value.decode("latin-1", errors="replace")
            return str(value).encode("latin-1", errors="replace").decode("utf-8", errors="replace")
        except Exception:
            return default
