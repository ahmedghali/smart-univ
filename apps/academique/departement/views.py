# apps/academique/departement/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Departement, Specialite, Matiere
from .forms import DepartementForm

# Imports conditionnels pour éviter les erreurs si les modèles n'existent pas encore
try:
    from apps.noyau.commun.models import AnneeUniversitaire, Salle, Amphi, Laboratoire
    from apps.academique.affectation.models import Ens_Dep, Classe, Salle_Dep, Amphi_Dep, Laboratoire_Dep
    from apps.academique.etudiant.models import Etudiant
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES POUR LES STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════

def get_department_stats(departement, annee_univ=None):
    """
    Fonction utilitaire pour récupérer les statistiques du département.
    Retourne un dictionnaire avec toutes les statistiques calculées.
    """
    if not MODELS_AVAILABLE:
        return get_default_stats()

    # Récupérer l'année universitaire courante si non spécifiée
    if not annee_univ:
        try:
            annee_univ = AnneeUniversitaire.objects.order_by('-date_debut').first()
        except Exception:
            return get_default_stats()

    if not annee_univ:
        return get_default_stats()

    stats = {}

    try:
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES DES ENSEIGNANTS
        # ═══════════════════════════════════════════════════════════════
        all_enseignants = Ens_Dep.objects.filter(
            departement=departement,
            annee_univ=annee_univ
        ).select_related('enseignant')

        # Totaux par statut
        stats['total_teachers'] = all_enseignants.count()
        stats['permanent_teachers'] = all_enseignants.filter(statut='Permanent').count()
        stats['permanent_vacataire_teachers'] = all_enseignants.filter(statut='Permanent & Vacataire').count()
        stats['vacataire_teachers'] = all_enseignants.filter(statut='Vacataire').count()
        stats['associe_teachers'] = all_enseignants.filter(statut='Associe').count()
        stats['doctorant_teachers'] = all_enseignants.filter(statut='Doctorant').count()

        # Calcul des temporaires
        stats['temporary_teachers'] = (
            stats['permanent_vacataire_teachers'] +
            stats['vacataire_teachers'] +
            stats['associe_teachers'] +
            stats['doctorant_teachers']
        )

        # Enseignants actifs dans le département
        stats['present_teachers'] = all_enseignants.filter(est_actif=True).count()

        # Statistiques par semestre
        stats['enseignants_s1'] = all_enseignants.filter(semestre_1=True).count()
        stats['enseignants_s2'] = all_enseignants.filter(semestre_2=True).count()

    except Exception:
        stats['total_teachers'] = 0
        stats['permanent_teachers'] = 0
        stats['temporary_teachers'] = 0
        stats['present_teachers'] = 0
        stats['enseignants_s1'] = 0
        stats['enseignants_s2'] = 0

    try:
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES DES ÉTUDIANTS
        # ═══════════════════════════════════════════════════════════════
        stats['total_students'] = Etudiant.objects.count()
    except Exception:
        stats['total_students'] = 0

    try:
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES DES MATIÈRES
        # ═══════════════════════════════════════════════════════════════
        stats['total_subjects'] = Matiere.objects.filter(
            niv_spe_dep__specialite__departement=departement
        ).distinct().count()
        stats['total_matieres'] = stats['total_subjects']  # Alias pour template
    except Exception:
        stats['total_subjects'] = 0
        stats['total_matieres'] = 0

    try:
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES DES SPÉCIALITÉS
        # ═══════════════════════════════════════════════════════════════
        stats['total_specialities'] = Specialite.objects.filter(
            departement=departement
        ).count()
        stats['total_specialites'] = stats['total_specialities']  # Alias pour template
    except Exception:
        stats['total_specialities'] = 0
        stats['total_specialites'] = 0

    try:
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES DES SALLES/INFRASTRUCTURES
        # ═══════════════════════════════════════════════════════════════
        salles = Salle_Dep.objects.filter(departement=departement).count()
        amphis = Amphi_Dep.objects.filter(departement=departement).count()
        labos = Laboratoire_Dep.objects.filter(departement=departement).count()
        stats['total_rooms'] = salles + amphis + labos
    except Exception:
        stats['total_rooms'] = 0

    try:
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES DES CLASSES/COURS
        # ═══════════════════════════════════════════════════════════════
        stats['total_classes'] = Classe.objects.filter(
            ens_dep__departement=departement,
            ens_dep__annee_univ=annee_univ
        ).count()

        # Classes actives (estimation)
        stats['active_classes'] = stats['total_classes']
    except Exception:
        stats['total_classes'] = 0
        stats['active_classes'] = 0

    # Statistiques supplémentaires
    stats['pending_requests'] = 0
    stats['completed_tasks'] = 95
    stats['annee_courante'] = annee_univ

    # Navigation rapide
    stats['can_manage_s1'] = stats.get('enseignants_s1', 0) > 0
    stats['can_manage_s2'] = stats.get('enseignants_s2', 0) > 0

    return stats


def get_default_stats():
    """Retourne les statistiques par défaut (zéros)"""
    return {
        'total_teachers': 0,
        'permanent_teachers': 0,
        'temporary_teachers': 0,
        'present_teachers': 0,
        'total_students': 0,
        'total_subjects': 0,
        'total_matieres': 0,  # Alias pour template
        'total_classes': 0,
        'total_specialities': 0,
        'total_specialites': 0,  # Alias pour template
        'total_rooms': 0,
        'active_classes': 0,
        'pending_requests': 0,
        'completed_tasks': 0,
        'enseignants_s1': 0,
        'enseignants_s2': 0,
        'annee_courante': None,
        'can_manage_s1': False,
        'can_manage_s2': False,
    }


# ═══════════════════════════════════════════════════════════════════════════
# VUES PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════


@login_required
def dashboard_Dep(request):
    """
    Tableau de bord du chef de département.
    Affiche les informations du département.
    """
    try:
        # Récupérer le département depuis la session ou les affectations
        departement_id = request.session.get('selected_departement_id')

        if departement_id:
            departement = Departement.objects.get(id=departement_id)
        else:
            # Si pas de département en session, essayer de récupérer depuis l'enseignant
            enseignant = request.user.enseignant_profile

            # Essayer de trouver le département via les related_names
            departement = None

            # Chef de département (related_name renvoie un RelatedManager)
            if hasattr(enseignant, 'departement_as_chef'):
                dep_query = enseignant.departement_as_chef
                if dep_query.exists():
                    departement = dep_query.first()

            # Chef adjoint pédagogique
            if not departement and hasattr(enseignant, 'departement_as_chef_adj_p'):
                dep_query = enseignant.departement_as_chef_adj_p
                if dep_query.exists():
                    departement = dep_query.first()

            # Chef adjoint post-graduation
            if not departement and hasattr(enseignant, 'departement_as_chef_adj_pg'):
                dep_query = enseignant.departement_as_chef_adj_pg
                if dep_query.exists():
                    departement = dep_query.first()

            if departement:
                request.session['selected_departement_id'] = departement.id
            else:
                messages.error(request, 'لم يتم العثور على القسم / Département introuvable')
                return redirect('comm:home')

        # Récupérer les statistiques du département
        stats = get_department_stats(departement)

        context = {
            'title': 'لوحة تحكم رئيس القسم / Tableau de bord Chef de Département',
            'departement': departement,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            **stats,  # Ajouter toutes les statistiques au contexte
        }
        return render(request, 'departement/dashboard_Dep.html', context)

    except Departement.DoesNotExist:
        messages.error(request, 'القسم غير موجود / Département introuvable')
        return redirect('comm:home')
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')

@login_required
def profile_Dep(request):
    """
    Profil du département.
    Affiche les informations complètes du département.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً / Veuillez d\'abord choisir le département')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        context = {
            'title': 'الملف التعريفي للقسم / Profil du Département',
            'departement': departement,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
        }
        return render(request, 'departement/profile_Dep.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


@login_required
def profileUpdate_Dep(request):
    """
    Modification du profil du département.
    Affiche et traite le formulaire de modification des informations du département.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً / Veuillez d\'abord choisir le département')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        if request.method == 'POST':
            form = DepartementForm(request.POST, request.FILES, instance=departement)
            if form.is_valid():
                form.save()
                messages.success(request, 'تم تحديث المعلومات بنجاح / Informations mises à jour avec succès')
                return redirect('depa:profile_Dep')
            else:
                messages.error(request, 'يرجى تصحيح الأخطاء / Veuillez corriger les erreurs')
        else:
            form = DepartementForm(instance=departement)

        context = {
            'title': 'تعديل معلومات القسم / Modifier les informations du département',
            'departement': departement,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'Dep_form': form,
        }
        return render(request, 'departement/profileUpdate_Dep.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


# ═══════════════════════════════════════════════════════════════════════════
# VUES ENSEIGNANTS DU DÉPARTEMENT
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def list_enseignants_dep(request, semestre_num=1):
    """Vue pour la liste des enseignants par semestre"""

    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        # Récupérer l'année universitaire courante
        annee_courante = AnneeUniversitaire.objects.order_by('-date_debut').first()
        if not annee_courante:
            messages.error(request, 'لا توجد سنة جامعية محددة كسنة حالية')
            return redirect('depa:dashboard_Dep')

        # Valider le numéro de semestre
        if semestre_num not in [1, 2]:
            messages.error(request, 'رقم السداسي غير صحيح')
            return redirect('depa:list_enseignants_dep', semestre_num=1)

        # Filtre de base avec semestre et enseignant inscrit sur la plateforme
        base_filter = {
            'departement': departement,
            'annee_univ': annee_courante,
            f'semestre_{semestre_num}': True,
            'enseignant__est_inscrit': True  # Seulement les enseignants inscrits sur la plateforme
        }

        # Récupérer les enseignants filtrés par semestre
        all_Ens_Dep = Ens_Dep.objects.filter(**base_filter).select_related(
            'enseignant__grade',
            'enseignant'
        ).order_by('enseignant__nom_ar')

        all_Ens_Dep_Per = Ens_Dep.objects.filter(
            departement=departement,
            statut='Permanent',
            annee_univ=annee_courante,
            enseignant__est_inscrit=True,
            **{f'semestre_{semestre_num}': True}
        ).select_related(
            'enseignant__grade',
            'enseignant'
        ).order_by('enseignant__nom_ar')

        all_Ens_Dep_PerVac = Ens_Dep.objects.filter(
            departement=departement,
            statut='Permanent & Vacataire',
            annee_univ=annee_courante,
            enseignant__est_inscrit=True,
            **{f'semestre_{semestre_num}': True}
        ).select_related(
            'enseignant__grade',
            'enseignant'
        ).order_by('enseignant__nom_ar')

        all_Ens_Dep_Vac = Ens_Dep.objects.filter(
            departement=departement,
            statut='Vacataire',
            annee_univ=annee_courante,
            enseignant__est_inscrit=True,
            **{f'semestre_{semestre_num}': True}
        ).select_related(
            'enseignant__grade',
            'enseignant'
        ).order_by('enseignant__nom_ar')

        all_Ens_Dep_Aso = Ens_Dep.objects.filter(
            departement=departement,
            statut='Associe',
            annee_univ=annee_courante,
            enseignant__est_inscrit=True,
            **{f'semestre_{semestre_num}': True}
        ).select_related(
            'enseignant__grade',
            'enseignant'
        ).order_by('enseignant__nom_ar')

        all_Ens_Dep_Doc = Ens_Dep.objects.filter(
            departement=departement,
            statut='Doctorant',
            annee_univ=annee_courante,
            enseignant__est_inscrit=True,
            **{f'semestre_{semestre_num}': True}
        ).select_related(
            'enseignant__grade',
            'enseignant'
        ).order_by('enseignant__nom_ar')

        # Calculer les statistiques par grade
        grade_stats = all_Ens_Dep.values('enseignant__grade__nom_ar').annotate(
            count=Count('id')
        ).order_by('-count')

        # Compteurs pour les champs vides
        missing_email_count = all_Ens_Dep.filter(
            Q(enseignant__email_prof__isnull=True) | Q(enseignant__email_prof='')
        ).count()

        missing_scholar_count = all_Ens_Dep.filter(
            Q(enseignant__googlescholar__isnull=True) | Q(enseignant__googlescholar='')
        ).count()

        context = {
            'title': 'قائمة الأساتذة',
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'annee_courante': annee_courante,
            'semestre_num': semestre_num,
            'all_Ens_Dep': all_Ens_Dep,
            'all_Ens_Dep_Per': all_Ens_Dep_Per,
            'all_Ens_Dep_Vac': all_Ens_Dep_Vac,
            'all_Ens_Dep_PerVac': all_Ens_Dep_PerVac,
            'all_Ens_Dep_Aso': all_Ens_Dep_Aso,
            'all_Ens_Dep_Doc': all_Ens_Dep_Doc,
            'grade_stats': grade_stats,
            'missing_email_count': missing_email_count,
            'missing_scholar_count': missing_scholar_count,
        }

        return render(request, 'departement/list_enseignants_dep.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


@login_required
def new_Enseignant(request):
    """
    Ajout d'un nouvel enseignant au département.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        if request.method == 'POST':
            # TODO: Traiter le formulaire d'ajout
            messages.info(request, 'هذه الميزة قيد التطوير / Fonctionnalité en cours de développement')
            return redirect('depa:list_enseignants_dep', semestre=1)

        context = {
            'title': 'إضافة أستاذ جديد / Ajouter un enseignant',
            'departement': departement,
            'my_Dep': departement,
        }
        return render(request, 'departement/new_Enseignant.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


@login_required
def heures_enseignants_dep(request, semestre=1):
    """
    Heures de travail des enseignants par semestre.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        enseignants = []
        if MODELS_AVAILABLE:
            try:
                annee_univ = AnneeUniversitaire.objects.order_by('-date_debut').first()
                if annee_univ:
                    filter_kwargs = {
                        'departement': departement,
                        'annee_univ': annee_univ,
                    }
                    if semestre == 1:
                        filter_kwargs['semestre_1'] = True
                    else:
                        filter_kwargs['semestre_2'] = True

                    enseignants = Ens_Dep.objects.filter(
                        **filter_kwargs
                    ).select_related('enseignant', 'enseignant__user')
            except Exception:
                pass

        context = {
            'title': f'ساعات عمل الأساتذة - السداسي {semestre}',
            'departement': departement,
            'my_Dep': departement,
            'enseignants': enseignants,
            'semestre': semestre,
        }
        return render(request, 'departement/heures_enseignants_dep.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


# ═══════════════════════════════════════════════════════════════════════════
# VUES ÉTUDIANTS DU DÉPARTEMENT
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def list_etudiants(request):
    """
    Liste des étudiants du département.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        etudiants = []
        if MODELS_AVAILABLE:
            try:
                etudiants = Etudiant.objects.all()[:100]
            except Exception:
                pass

        context = {
            'title': 'قائمة الطلبة / Liste des étudiants',
            'departement': departement,
            'my_Dep': departement,
            'etudiants': etudiants,
        }
        return render(request, 'departement/list_etudiants.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


@login_required
def import_etudiants(request):
    """
    Import des étudiants depuis un fichier.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        if request.method == 'POST':
            messages.info(request, 'هذه الميزة قيد التطوير / Fonctionnalité en cours de développement')
            return redirect('depa:list_etudiants')

        context = {
            'title': 'استيراد الطلبة / Importer des étudiants',
            'departement': departement,
            'my_Dep': departement,
        }
        return render(request, 'departement/import_etudiants.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


# ═══════════════════════════════════════════════════════════════════════════
# VUES MATIÈRES ET SPÉCIALITÉS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def list_Mat_Niv(request):
    """
    Liste des matières par niveau.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        matieres = []
        try:
            matieres = Matiere.objects.filter(
                niv_spe_dep__specialite__departement=departement
            ).select_related('niv_spe_dep__specialite', 'niv_spe_dep__niveau').distinct()
        except Exception:
            pass

        context = {
            'title': 'قائمة المقاييس / Liste des matières',
            'departement': departement,
            'my_Dep': departement,
            'matieres': matieres,
        }
        return render(request, 'departement/list_Mat_Niv.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


@login_required
def list_Specialite_Dep(request):
    """
    Liste des spécialités du département.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        specialites = Specialite.objects.filter(departement=departement)

        context = {
            'title': 'قائمة التخصصات / Liste des spécialités',
            'departement': departement,
            'my_Dep': departement,
            'specialites': specialites,
        }
        return render(request, 'departement/list_Specialite_Dep.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


# ═══════════════════════════════════════════════════════════════════════════
# VUES EMPLOI DU TEMPS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def import_emploi(request):
    """
    Import de l'emploi du temps depuis un fichier.
    """
    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)

        if request.method == 'POST':
            messages.info(request, 'هذه الميزة قيد التطوير / Fonctionnalité en cours de développement')
            return redirect('depa:dashboard_Dep')

        context = {
            'title': 'استيراد الحصص / Importer l\'emploi du temps',
            'departement': departement,
            'my_Dep': departement,
        }
        return render(request, 'departement/import_emploi.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:dashboard_Dep')


# ═══════════════════════════════════════════════════════════════════════════
# SUPPRESSION ENSEIGNANTS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def delete_Enseignant(request, ens_dep_id):
    """
    Supprime un enseignant du département.
    Seuls les enseignants non-permanents peuvent être supprimés.
    """
    try:
        my_Ens_Dep = get_object_or_404(Ens_Dep, id=ens_dep_id)
        deleted_Ens = my_Ens_Dep.enseignant

        if my_Ens_Dep.statut != 'Permanent':
            my_Ens_Dep.delete()
            messages.warning(request, f'تم حذف "{deleted_Ens}" من القسم.')
        else:
            messages.error(request, f'لا يمكن حذف الأستاذ المرسم "{deleted_Ens}".')

        # Retourner à la page précédente
        referer_url = request.META.get('HTTP_REFERER')
        if referer_url:
            return redirect(referer_url)
        return redirect('depa:list_enseignants_dep', semestre_num=1)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:list_enseignants_dep', semestre_num=1)


@login_required
def delete_Ens_Acces_Dep(request, ens_id):
    """
    Désactive un enseignant dans le département.
    Met est_actif = False au lieu de supprimer l'enregistrement.
    """
    try:
        from apps.academique.enseignant.models import Enseignant

        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)
        maj_Ens = get_object_or_404(Enseignant, id=ens_id)

        this_to_deactivate = Ens_Dep.objects.get(
            enseignant=ens_id,
            departement=departement,
            est_actif=True
        )
        this_to_deactivate.est_actif = False
        this_to_deactivate.save()

        messages.warning(request, f'تم إلغاء تنشيط "{maj_Ens}" من القسم.')

        # Retourner à la page précédente
        referer_url = request.META.get('HTTP_REFERER')
        if referer_url:
            return redirect(referer_url)
        return redirect('depa:list_enseignants_dep', semestre_num=1)

    except Ens_Dep.DoesNotExist:
        messages.error(request, 'الأستاذ غير نشط في القسم.')
        return redirect('depa:list_enseignants_dep', semestre_num=1)
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:list_enseignants_dep', semestre_num=1)


@login_required
def activate_Ens_Acces_Dep(request, ens_id):
    """
    Active un enseignant dans le département.
    Met est_actif = True pour permettre l'accès au département.
    """
    try:
        from apps.academique.enseignant.models import Enseignant

        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            messages.error(request, 'يرجى اختيار القسم أولاً')
            return redirect('auth:select_role')

        departement = get_object_or_404(Departement, id=departement_id)
        maj_Ens = get_object_or_404(Enseignant, id=ens_id)

        # Chercher l'affectation inactive
        this_to_activate = Ens_Dep.objects.get(
            enseignant=ens_id,
            departement=departement,
            est_actif=False
        )
        this_to_activate.est_actif = True
        this_to_activate.save()

        messages.success(request, f'تم تنشيط حساب "{maj_Ens}" في القسم بنجاح.')

        # Retourner à la page précédente
        referer_url = request.META.get('HTTP_REFERER')
        if referer_url:
            return redirect(referer_url)
        return redirect('depa:list_enseignants_dep', semestre_num=1)

    except Ens_Dep.DoesNotExist:
        messages.error(request, 'الأستاذ نشط بالفعل في القسم أو غير موجود.')
        return redirect('depa:list_enseignants_dep', semestre_num=1)
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('depa:list_enseignants_dep', semestre_num=1)


# ═══════════════════════════════════════════════════════════════════════════
# API STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_stats_api(request):
    """
    API pour récupérer les statistiques en JSON.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        departement_id = request.session.get('selected_departement_id')
        if not departement_id:
            return JsonResponse({'error': 'Département non sélectionné'}, status=400)

        departement = get_object_or_404(Departement, id=departement_id)
        stats = get_department_stats(departement)

        if stats.get('annee_courante'):
            stats['annee_courante'] = str(stats['annee_courante'])

        from datetime import datetime
        stats['last_updated'] = datetime.now().isoformat()

        return JsonResponse(stats)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
