# apps/noyau/authentification/decorators.py

from django.http import Http404
from functools import wraps
from django.contrib.auth.decorators import login_required
from apps.academique.affectation.models import Ens_Dep
from apps.academique.departement.models import Departement
from apps.academique.etudiant.models import Etudiant


def enseignant_access_required(view_func):
    """
    Décorateur pour vérifier l'accès enseignant à un département.

    Injecte automatiquement 'enseignant' et 'departement' dans les kwargs de la vue.
    Vérifie que l'enseignant est bien inscrit au département demandé.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        try:
            # Récupérer le profil enseignant de l'utilisateur
            enseignant = getattr(user, 'enseignant_profile', None)
            if not enseignant:
                raise Http404("Vous n'êtes pas autorisé à accéder à cette page. (Pas d'enseignant lié)")

            # Récupérer l'ID du département depuis les kwargs
            dep_id = kwargs.get('id') or kwargs.get('dep_id')
            departement = None

            if dep_id:
                # Vérifier l'affectation et l'inscription (est_actif au lieu de est_inscrit)
                ens_dep = Ens_Dep.objects.filter(
                    enseignant=enseignant,
                    departement_id=dep_id,
                    est_actif=True
                ).first()
                if not ens_dep:
                    raise Http404(f"Vous n'êtes pas autorisé à accéder à ce département. (ID : {dep_id}, non actif)")
                departement = Departement.objects.get(id=dep_id)

            # Injecter enseignant et departement dans les kwargs
            kwargs['enseignant'] = enseignant
            kwargs['departement'] = departement
            return view_func(request, *args, **kwargs)
        except Departement.DoesNotExist:
            raise Http404("Département non trouvé.")
        except Exception as e:
            raise Http404(f"Erreur : {str(e)}")
    return wrapper


def etudiant_access_required(view_func):
    """
    Décorateur pour vérifier l'accès étudiant.

    Injecte automatiquement 'etudiant' et 'departement' dans les kwargs de la vue.
    Vérifie que l'étudiant est bien inscrit.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        try:
            # Récupérer le profil étudiant de l'utilisateur
            etudiant = getattr(user, 'etudiant_profile', None)
            if not etudiant:
                raise Http404("Vous n'êtes pas autorisé à accéder à cette page. (Pas d'étudiant lié)")

            # Récupérer l'ID du département depuis le profil étudiant
            dep_id = etudiant.niv_spe_dep_sg.niv_spe_dep.departement.id
            departement = None

            if dep_id:
                # Vérifier l'inscription de l'étudiant (est_actif au lieu de est_inscrit)
                etu_dep = Etudiant.objects.filter(
                    id=etudiant.id,
                    est_actif=True  # Champ correspondant dans le modèle Etudiant
                ).first()
                if not etu_dep:
                    raise Http404(f"Vous n'êtes pas autorisé à accéder à ce département. (ID : {dep_id}, non actif)")
                departement = Departement.objects.get(id=dep_id)

            # Injecter etudiant et departement dans les kwargs
            kwargs['etudiant'] = etudiant
            kwargs['departement'] = departement
            return view_func(request, *args, **kwargs)
        except Departement.DoesNotExist:
            raise Http404("Département non trouvé.")
        except Exception as e:
            raise Http404(f"Erreur : {str(e)}")
    return wrapper