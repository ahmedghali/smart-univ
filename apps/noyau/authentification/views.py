# apps/noyau/authentification/views.py

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import LoginForm
from .utils import (
    get_user_roles,
    redirect_to_dashboard,
    redirect_single_role,
    get_enseignant_affectations,
    validate_role_for_user,
    validate_departement_for_enseignant,
)
from .constants import (
    ERROR_NO_ROLES,
    ERROR_INVALID_ROLE,
    ERROR_INVALID_DEPARTEMENT,
)


# ══════════════════════════════════════════════════════════════
# VUE DE CONNEXION
# ══════════════════════════════════════════════════════════════

def login_view(request):
    """
    Gère l'authentification des utilisateurs.
    Après une connexion réussie, redirige vers la sélection de rôle.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('auth:select_role')
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة / Nom d\'utilisateur ou mot de passe incorrect')
    else:
        form = LoginForm()

    return render(request, 'authentification/login.html', {'form': form})


# ══════════════════════════════════════════════════════════════
# SÉLECTION DU RÔLE
# ══════════════════════════════════════════════════════════════

@login_required
def select_role(request):
    """
    Permet à l'utilisateur de sélectionner son rôle actif.

    Gère deux scénarios :
    1. Si l'utilisateur n'a qu'un seul rôle → redirection automatique
    2. Si l'utilisateur a plusieurs rôles → affiche le formulaire de sélection
    """
    user = request.user

    # Récupérer tous les rôles disponibles pour cet utilisateur
    roles = get_user_roles(user)

    # Sauvegarder le nombre de rôles dans la session
    request.session['roles_count'] = len(roles)

    # Cas 1 : Aucun rôle trouvé
    if not roles:
        messages.error(request, ERROR_NO_ROLES)
        return render(request, 'authentification/select_role.html', {'roles': roles})

    # Cas 2 : Un seul rôle → redirection automatique
    if len(roles) == 1:
        role_code = roles[0][0]
        # Sauvegarder le rôle dans la session
        request.session['current_role'] = role_code
        result = redirect_single_role(role_code, user, request)

        # Vérifier si c'est une erreur ou une redirection
        if isinstance(result, dict) and result.get('error'):
            messages.error(request, result['message'])
            return render(request, 'authentification/select_role.html', {'roles': roles})

        return result

    # Cas 3 : Plusieurs rôles → l'utilisateur doit choisir
    if request.method == 'POST':
        selected_role = request.POST.get('role')

        # Valider que le rôle sélectionné est bien disponible pour cet utilisateur
        if not validate_role_for_user(user, selected_role):
            messages.error(request, ERROR_INVALID_ROLE)
            return render(request, 'authentification/select_role.html', {'roles': roles})

        # Sauvegarder le rôle sélectionné dans la session
        request.session['current_role'] = selected_role

        # Rediriger vers le dashboard correspondant
        result = redirect_to_dashboard(selected_role, user, request)

        # Vérifier si c'est une erreur ou une redirection
        if isinstance(result, dict) and result.get('error'):
            messages.error(request, result['message'])
            return render(request, 'authentification/select_role.html', {'roles': roles})

        return result

    # GET request : afficher le formulaire de sélection
    return render(request, 'authentification/select_role.html', {'roles': roles})


# ══════════════════════════════════════════════════════════════
# SÉLECTION DU DÉPARTEMENT (POUR ENSEIGNANTS)
# ══════════════════════════════════════════════════════════════

@login_required
def select_departement(request):
    """
    Permet à un enseignant avec plusieurs affectations de choisir son département actif.
    """
    user = request.user

    # Récupérer les affectations de l'enseignant
    try:
        affectations = get_enseignant_affectations(user)

        if not affectations.exists():
            messages.error(request, "ليس لديك أي انتماء إلى قسم. يرجى الاتصال بالمسؤول.")
            return redirect('auth:select_role')

        # Sauvegarder le nombre d'affectations dans la session
        request.session['affectations_count'] = affectations.count()

    except AttributeError:
        messages.error(request, "لم يتم العثور على ملف تعريف الأستاذ. يرجى الاتصال بالمسؤول.")
        return redirect('auth:select_role')

    # Traiter la sélection d'un département
    if request.method == 'POST':
        selected_departement_id = request.POST.get('departement_id')

        # Valider que le département sélectionné est bien dans les affectations
        if not validate_departement_for_enseignant(user, selected_departement_id):
            messages.error(request, ERROR_INVALID_DEPARTEMENT)
            return render(request, 'authentification/select_departement.html', {
                'affectations': affectations
            })

        # Vérifier si l'enseignant est actif dans ce département
        try:
            affectation = affectations.get(departement_id=selected_departement_id)
            if not affectation.est_actif:
                messages.error(request, 'عذراً، حسابك غير مفعّل في هذا القسم. يرجى التواصل مع رئيس القسم لتفعيل حسابك.')
                return render(request, 'authentification/select_departement.html', {
                    'affectations': affectations
                })
        except Exception:
            messages.error(request, 'حدث خطأ أثناء التحقق من حالة حسابك.')
            return render(request, 'authentification/select_departement.html', {
                'affectations': affectations
            })

        # Sauvegarder le département sélectionné en session
        request.session['selected_departement_id'] = selected_departement_id

        # Rediriger vers le dashboard enseignant avec l'ID du département
        return redirect('ense:dashboard_Ens', dep_id=selected_departement_id)

    # GET request : afficher le formulaire de sélection
    return render(request, 'authentification/select_departement.html', {
        'affectations': affectations
    })


# ══════════════════════════════════════════════════════════════
# PROFIL ET PARAMÈTRES
# ══════════════════════════════════════════════════════════════

@login_required
def profile_redirect(request):
    """
    Redirige l'utilisateur vers sa page de profil appropriée selon son rôle.
    """
    user = request.user
    current_role = request.session.get('current_role')

    # Si le rôle actuel est chef de département ou adjoint, rediriger vers le profil du département
    if current_role in ['chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg']:
        return redirect('depa:profile_Dep')

    # Si l'utilisateur a un profil enseignant, rediriger vers le profil enseignant
    if hasattr(user, 'enseignant_profile') and user.enseignant_profile:
        return redirect('ense:profile_Ens')

    # Si l'utilisateur a un profil étudiant, rediriger vers le profil étudiant
    elif hasattr(user, 'etudiant_profile') and user.etudiant_profile:
        return redirect('etud:profile_Etud')

    # Sinon, rediriger vers la sélection de rôle
    else:
        messages.info(request, 'يرجى اختيار منصبك أولاً / Veuillez d\'abord choisir votre poste')
        return redirect('auth:select_role')


@login_required
def profile_update_redirect(request):
    """
    Redirige l'utilisateur vers sa page de modification de profil selon son rôle actuel.
    """
    user = request.user
    current_role = request.session.get('current_role')

    # Si le rôle actuel est chef de département ou adjoint, rediriger vers l'update du département
    if current_role in ['chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg']:
        return redirect('depa:profileUpdate_Dep')

    # Si l'utilisateur a un profil enseignant, rediriger vers l'update enseignant
    if hasattr(user, 'enseignant_profile') and user.enseignant_profile:
        return redirect('ense:profileUpdate_Ens')

    # Si l'utilisateur a un profil étudiant, rediriger vers l'update étudiant
    elif hasattr(user, 'etudiant_profile') and user.etudiant_profile:
        return redirect('etud:profileUpdate_Etud')

    # Sinon, rediriger vers la sélection de rôle
    else:
        messages.info(request, 'يرجى اختيار منصبك أولاً / Veuillez d\'abord choisir votre poste')
        return redirect('auth:select_role')


@login_required
def dashboard_redirect(request):
    """
    Redirige l'utilisateur vers son tableau de bord selon son rôle actuel.
    """
    user = request.user
    current_role = request.session.get('current_role')

    # Si le rôle actuel est chef de département ou adjoint
    if current_role in ['chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg']:
        return redirect('depa:dashboard_Dep')

    # Si le rôle actuel est doyen ou vice-doyen
    if current_role in ['doyen', 'vice_doyen_p', 'vice_doyen_pg']:
        return redirect('facu:dashboard_Fac')

    # Si le rôle actuel est recteur ou vice-recteur
    if current_role in ['recteur', 'vice_rect_p', 'vice_rect_pg']:
        return redirect('univ:dashboard_Uni')

    # Si l'utilisateur a un profil enseignant
    if hasattr(user, 'enseignant_profile') and user.enseignant_profile:
        # Vérifier si un département est sélectionné dans la session
        dep_id = request.session.get('selected_departement_id')
        if dep_id:
            return redirect('ense:dashboard_Ens', dep_id=dep_id)
        else:
            # Rediriger vers la sélection de département
            return redirect('auth:select_departement')

    # Si l'utilisateur a un profil étudiant
    elif hasattr(user, 'etudiant_profile') and user.etudiant_profile:
        return redirect('etud:dashboard_Etud')

    # Sinon, rediriger vers la sélection de rôle
    else:
        messages.info(request, 'يرجى اختيار منصبك أولاً / Veuillez d\'abord choisir votre poste')
        return redirect('auth:select_role')


# ══════════════════════════════════════════════════════════════
# DÉCONNEXION
# ══════════════════════════════════════════════════════════════

def logout_view(request):
    """
    Déconnecte l'utilisateur et le redirige vers la page d'accueil.
    """
    logout(request)
    return redirect('comm:home')
