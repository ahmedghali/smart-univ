# apps/noyau/authentification/utils.py

"""
Fonctions utilitaires pour la gestion de l'authentification et des rôles.
Ce fichier contient toute la logique métier pour déterminer les rôles et gérer les redirections.
"""

from django.shortcuts import redirect
from django.urls import reverse
from apps.academique.affectation.models import Ens_Dep
from .constants import (
    ROLE_ETUDIANT,
    ROLE_ENSEIGNANT,
    ROLE_LABELS,
    ROLE_DASHBOARDS,
    ENSEIGNANT_RELATIONS_TO_ROLES,
    ROLE_POSTE_CODES,
)


# ══════════════════════════════════════════════════════════════
# RÉCUPÉRATION DES RÔLES DISPONIBLES
# ══════════════════════════════════════════════════════════════

def get_user_roles(user):
    """
    Retourne tous les rôles disponibles pour un utilisateur donné.

    Args:
        user (CustomUser): L'utilisateur connecté

    Returns:
        list: Liste de tuples (code_role, label_role)

    Exemple:
        >>> roles = get_user_roles(request.user)
        >>> [('etudiant', 'لوحة تحكم الطالب'), ('enseignant', 'لوحة تحكم الأستاذ')]
    """
    roles = []

    # Vérifier si l'utilisateur est un étudiant
    if hasattr(user, 'etudiant_profile') and user.etudiant_profile:
        roles.append((ROLE_ETUDIANT, ROLE_LABELS[ROLE_ETUDIANT]))

    # Vérifier si l'utilisateur est un enseignant
    if hasattr(user, 'enseignant_profile') and user.enseignant_profile:
        roles.append((ROLE_ENSEIGNANT, ROLE_LABELS[ROLE_ENSEIGNANT]))

        # Ajouter les rôles administratifs basés sur les relations ForeignKey
        enseignant = user.enseignant_profile
        for relation_name, role_code in ENSEIGNANT_RELATIONS_TO_ROLES.items():
            if hasattr(enseignant, relation_name):
                relation = getattr(enseignant, relation_name)
                # Vérifier si la relation existe (peut être un RelatedManager ou un objet)
                if hasattr(relation, 'exists'):
                    if relation.exists():
                        roles.append((role_code, ROLE_LABELS[role_code]))
                elif relation is not None:
                    roles.append((role_code, ROLE_LABELS[role_code]))

    return roles


def user_has_role_via_poste(user, role_code):
    """
    Vérifie si un utilisateur a un rôle spécifique via son poste_principal ou postes_secondaires.

    Args:
        user (CustomUser): L'utilisateur à vérifier
        role_code (str): Le code du rôle à vérifier (ex: 'chef_departement')

    Returns:
        bool: True si l'utilisateur a ce rôle, False sinon
    """
    if role_code not in ROLE_POSTE_CODES:
        return False

    poste_code = ROLE_POSTE_CODES[role_code]

    # Vérifier poste_principal
    if user.poste_principal and user.poste_principal.code == poste_code:
        return True

    # Vérifier postes_secondaires
    return user.postes_secondaires.filter(code=poste_code).exists()


# ══════════════════════════════════════════════════════════════
# GESTION DES AFFECTATIONS ENSEIGNANT
# ══════════════════════════════════════════════════════════════

def get_enseignant_affectations(user):
    """
    Retourne les affectations départementales d'un enseignant.

    Args:
        user (CustomUser): L'utilisateur enseignant

    Returns:
        QuerySet: Les affectations Ens_Dep, ou None si erreur

    Raises:
        AttributeError: Si l'utilisateur n'a pas de profil enseignant
    """
    if not hasattr(user, 'enseignant_profile') or not user.enseignant_profile:
        raise AttributeError("L'utilisateur n'a pas de profil enseignant")

    enseignant = user.enseignant_profile
    return Ens_Dep.objects.filter(enseignant=enseignant)


def handle_enseignant_redirect(user, request):
    """
    Gère la redirection d'un enseignant vers son dashboard.
    Prend en compte les affectations multiples aux départements.

    Args:
        user (CustomUser): L'utilisateur enseignant
        request: L'objet request Django

    Returns:
        HttpResponse: Redirection vers le dashboard approprié
        dict: Informations d'erreur si échec

    Exemple:
        >>> redirect_or_error = handle_enseignant_redirect(user, request)
        >>> if isinstance(redirect_or_error, dict):
        >>>     # Erreur
        >>>     messages.error(request, redirect_or_error['message'])
    """
    try:
        affectations = get_enseignant_affectations(user)

        if not affectations.exists():
            return {
                'error': True,
                'message': "ليس لديك أي انتماء إلى قسم. يرجى الاتصال بالمسؤول."
            }

        # Sauvegarder le nombre d'affectations dans la session
        affectations_count = affectations.count()
        request.session['affectations_count'] = affectations_count

        if affectations_count == 1:
            # Une seule affectation : vérifier si elle est active
            affectation = affectations.first()
            if not affectation.est_actif:
                return {
                    'error': True,
                    'message': "عذراً، حسابك غير مفعّل في هذا القسم. يرجى التواصل مع رئيس القسم لتفعيل حسابك."
                }
            departement_id = affectation.departement.id
            request.session['selected_departement_id'] = departement_id
            return redirect('ense:dashboard_Ens', dep_id=departement_id)

        else:
            # Plusieurs affectations : rediriger vers la sélection
            return redirect('auth:select_departement')

    except AttributeError:
        return {
            'error': True,
            'message': "لم يتم العثور على ملف تعريف الأستاذ. يرجى الاتصال بالمسؤول."
        }


# ══════════════════════════════════════════════════════════════
# REDIRECTION VERS LES DASHBOARDS
# ══════════════════════════════════════════════════════════════

def redirect_to_dashboard(role_code, user, request):
    """
    Redirige un utilisateur vers le dashboard correspondant à son rôle.

    Args:
        role_code (str): Le code du rôle (ex: 'etudiant', 'enseignant', 'recteur')
        user (CustomUser): L'utilisateur connecté
        request: L'objet request Django

    Returns:
        HttpResponse: Redirection vers le dashboard
        dict: Informations d'erreur si le rôle nécessite un traitement spécial
    """
    # Cas spécial : enseignant nécessite la gestion des affectations
    if role_code == ROLE_ENSEIGNANT:
        return handle_enseignant_redirect(user, request)

    # Cas standard : redirection directe
    dashboard_url = ROLE_DASHBOARDS.get(role_code)

    if dashboard_url:
        return redirect(dashboard_url)

    # Rôle inconnu
    return {
        'error': True,
        'message': "المنصب المختار غير صالح."
    }


def redirect_single_role(role_code, user, request):
    """
    Gère la redirection automatique quand l'utilisateur n'a qu'un seul rôle.

    Args:
        role_code (str): Le code du rôle unique
        user (CustomUser): L'utilisateur connecté
        request: L'objet request Django

    Returns:
        HttpResponse: Redirection vers le dashboard approprié
        dict: Informations d'erreur si échec
    """
    return redirect_to_dashboard(role_code, user, request)


# ══════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════

def validate_role_for_user(user, role_code):
    """
    Vérifie qu'un utilisateur a bien accès à un rôle donné.

    Args:
        user (CustomUser): L'utilisateur à vérifier
        role_code (str): Le code du rôle à valider

    Returns:
        bool: True si valide, False sinon
    """
    user_roles = get_user_roles(user)
    user_role_codes = [role[0] for role in user_roles]
    return role_code in user_role_codes


def validate_departement_for_enseignant(user, departement_id):
    """
    Vérifie qu'un enseignant a bien accès à un département donné.

    Args:
        user (CustomUser): L'utilisateur enseignant
        departement_id (int): L'ID du département à valider

    Returns:
        bool: True si valide, False sinon
    """
    try:
        affectations = get_enseignant_affectations(user)
        return affectations.filter(departement_id=departement_id).exists()
    except AttributeError:
        return False
