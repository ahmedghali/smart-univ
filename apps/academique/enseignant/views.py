# apps/academique/enseignant/views.py

from collections import defaultdict
from datetime import timedelta
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, Min, Sum
from django.contrib.contenttypes.models import ContentType
from .models import Enseignant
from .forms import ProfileUpdateEnsForm, UserUpdateForm
from apps.noyau.authentification.decorators import enseignant_access_required
from apps.noyau.commun.models import Semestre, AnneeUniversitaire, Niveau, Reforme
from apps.academique.affectation.models import Classe, Seance, Gestion_Etu_Classe, Ens_Dep, Amphi_Dep, Salle_Dep, Laboratoire_Dep, SousGroupe, EtudiantSousGroupe, SousGroupeManager, Abs_Etu_Seance
from apps.academique.etudiant.models import Etudiant
from apps.academique.departement.models import Departement, Specialite, Matiere, NivSpeDep_SG, NivSpeDep


# ══════════════════════════════════════════════════════════════
# VUES POUR LE TABLEAU DE BORD DE L'ENSEIGNANT
# ══════════════════════════════════════════════════════════════

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

        # Mapping des jours pour aujourd'hui
        day_mapping = {
            'Monday': 'Lundi',
            'Tuesday': 'Mardi',
            'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi',
            'Friday': 'Vendredi',
            'Saturday': 'Samedi',
            'Sunday': 'Dimanche'
        }
        today_french = day_mapping.get(today.strftime('%A'), 'Lundi')

        # Gestion du semestre
        semestre_selected = request.GET.get('semestre', '1')
        try:
            semestre_obj = Semestre.objects.get(numero=semestre_selected)
        except Semestre.DoesNotExist:
            semestre_obj = Semestre.objects.filter(numero='1').first()
            if not semestre_obj:
                semestre_obj = Semestre.objects.create(numero='1', nom='السداسي الأول')
            semestre_selected = str(semestre_obj.numero)

        all_semestres = Semestre.objects.all().order_by('numero')

        # Classes de l'enseignant
        try:
            mes_classes = Classe.objects.filter(
                enseignant__enseignant=my_Ens,
                semestre=semestre_obj
            ).select_related('matiere', 'niv_spe_dep_sg', 'semestre').order_by('jour', 'temps', 'matiere__nom_fr')
        except Exception:
            mes_classes = Classe.objects.none()

        # ========== STATISTIQUES DE BASE ==========

        # Comptage sécurisé des étudiants
        total_etudiants = 0
        try:
            niv_spe_dep_sgs = mes_classes.values_list('niv_spe_dep_sg', flat=True).distinct()
            for niv_spe_dep_sg_id in niv_spe_dep_sgs:
                count = Etudiant.objects.filter(niv_spe_dep_sg_id=niv_spe_dep_sg_id).count()
                total_etudiants += count
        except Exception:
            total_etudiants = 0

        # Statistiques principales
        stats_enseignant = {
            'total_classes': mes_classes.count(),
            'total_matieres': mes_classes.values('matiere').distinct().count(),
            'total_etudiants': total_etudiants,
            'niveaux_count': mes_classes.values('niv_spe_dep_sg__niv_spe_dep').distinct().count(),
            'specialites_count': mes_classes.values('niv_spe_dep_sg__niv_spe_dep__specialite').distinct().count(),
            'volume_horaire': round(mes_classes.count() * 1.5, 1),
        }

        # Taux de réalisation
        classes_avec_seances = mes_classes.filter(seance_created=True).count()
        if mes_classes.count() > 0:
            taux_realisation = round((classes_avec_seances / mes_classes.count()) * 100, 1)
        else:
            taux_realisation = 0
        stats_enseignant['taux_realisation'] = taux_realisation

        # Répartition par type
        stats_repartition = {
            'cours': mes_classes.filter(type='Cours').count(),
            'td': mes_classes.filter(type='TD').count(),
            'tp': mes_classes.filter(type='TP').count(),
            'ss': mes_classes.filter(type='Sortie').count(),
        }

        # ========== EMPLOI DU TEMPS AUJOURD'HUI ==========

        try:
            classes_today = mes_classes.filter(jour=today_french).order_by('temps')

            # Mise à jour des taux d'avancement
            for classe in classes_today:
                if classe.seance_created and not hasattr(classe, 'taux_avancement'):
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
            'taux_presence_general': 85.0,
            'total_absences': 0,
            'absences_justifiees': 0,
            'etudiants_risque': 0,
        }

        try:
            absences_total = 0
            absences_justifiees_total = 0

            for classe in mes_classes:
                if classe.abs_liste_Etu:
                    absences_classe = Gestion_Etu_Classe.objects.filter(classe=classe)
                    absences_total += sum([abs_obj.nbr_absence or 0 for abs_obj in absences_classe])
                    absences_justifiees_total += sum([abs_obj.nbr_absence_justifiee or 0 for abs_obj in absences_classe])

            stats_assiduite.update({
                'total_absences': absences_total,
                'absences_justifiees': absences_justifiees_total,
                'etudiants_risque': max(0, absences_total - absences_justifiees_total) // 3,
            })

            if absences_total > 0:
                total_seances_estimees = mes_classes.count() * 10
                taux_presence = max(0, ((total_seances_estimees - absences_total) / total_seances_estimees) * 100)
                stats_assiduite['taux_presence_general'] = round(taux_presence, 1)

        except Exception:
            pass

        # ========== ACTIVITÉS RÉCENTES ==========

        activites_recentes = []
        try:
            for i, classe in enumerate(mes_classes[:3]):
                activites_recentes.append({
                    'type': 'classe',
                    'titre': f'{classe.matiere.nom_fr}',
                    'description': f'{classe.type} - {classe.niv_spe_dep_sg}',
                    'date': today - timedelta(days=i),
                })
        except Exception:
            pass

        # ========== NOTIFICATIONS ==========

        notifications = []

        classes_sans_seances = mes_classes.filter(seance_created=False).count()
        if classes_sans_seances > 0:
            notifications.append({
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'titre': 'تنبيه:',
                'message': f'لديك {classes_sans_seances} حصة بدون دروس منشأة'
            })

        if classes_today:
            notifications.append({
                'type': 'info',
                'icon': 'calendar-day',
                'titre': 'تذكير:',
                'message': f'لديك {len(list(classes_today))} حصة مجدولة اليوم'
            })

        if not notifications:
            notifications.append({
                'type': 'success',
                'icon': 'check-circle',
                'titre': 'ممتاز!',
                'message': 'جميع حصصك منظمة بشكل جيد'
            })

        # ========== CONTEXTE FINAL ==========

        context = {
            'title': 'لوحة التحكم - الأستاذ',
            'my_Ens': my_Ens,
            'my_Dep': my_Dep,
            'my_Fac': my_Fac,
            'today': today,
            'all_semestres': all_semestres,
            'semestre_selected': semestre_selected,
            'semestre_obj': semestre_obj,
            'mes_classes': mes_classes,
            'classes_today': classes_today,
            'stats_enseignant': stats_enseignant,
            'stats_repartition': stats_repartition,
            'stats_assiduite': stats_assiduite,
            'activites_recentes': activites_recentes,
            'notifications': notifications,
            # Compatibilité avec l'ancien template
            'enseignant': my_Ens,
            'departement': my_Dep,
        }

        return render(request, 'enseignant/dashboard_Ens.html', context)

    except Exception as e:
        messages.error(request, f'حدث خطأ في تحميل لوحة التحكم: {str(e)}')

        # Context minimal de fallback
        context = {
            'title': 'لوحة التحكم - الأستاذ',
            'my_Ens': enseignant,
            'my_Dep': departement,
            'my_Fac': departement.faculte if departement else None,
            'active_menu': 'dashboard',
            'today': timezone.now().date(),
            'all_semestres': Semestre.objects.all().order_by('numero'),
            'semestre_selected': '1',
            'mes_classes': [],
            'classes_today': [],
            'stats_enseignant': {
                'total_classes': 0,
                'total_matieres': 0,
                'total_etudiants': 0,
                'niveaux_count': 0,
                'specialites_count': 0,
                'volume_horaire': 0,
                'taux_realisation': 0,
            },
            'stats_repartition': {'cours': 0, 'td': 0, 'tp': 0, 'ss': 0},
            'stats_assiduite': {
                'taux_presence_general': 0,
                'total_absences': 0,
                'absences_justifiees': 0,
                'etudiants_risque': 0,
            },
            'activites_recentes': [],
            'notifications': [{
                'type': 'danger',
                'icon': 'exclamation-circle',
                'titre': 'خطأ:',
                'message': 'حدث خطأ في تحميل البيانات'
            }],
            # Compatibilité avec l'ancien template
            'enseignant': enseignant,
            'departement': departement,
        }
        return render(request, 'enseignant/dashboard_Ens.html', context)


# ══════════════════════════════════════════════════════════════
# VUES POUR LE PROFIL DE L'ENSEIGNANT
# ══════════════════════════════════════════════════════════════

@login_required
def profile_Ens(request, enseignant_id=None):
    """
    Affichage du profil de l'enseignant.
    Montre toutes les informations détaillées de l'enseignant.
    """
    try:
        if enseignant_id:
            # Affichage du profil d'un autre enseignant (par ID)
            enseignant = get_object_or_404(Enseignant, id=enseignant_id)
        else:
            # Affichage du propre profil de l'utilisateur
            enseignant = request.user.enseignant_profile

        # Récupérer le département principal
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        # Département courant (pour compatibilité avec base_Ens.html)
        departement = real_Dep.departement if real_Dep else None

        # Autres départements
        ALL_Dep = Ens_Dep.objects.filter(
            enseignant=enseignant
        ).exclude(departement=departement) if departement else []

        context = {
            'title': 'الملف الشخصي',
            'active_menu': 'profile',
            'enseignant': enseignant,
            'my_Ens': enseignant,
            'my_Dep': departement,
            'my_Fac': departement.faculte if departement else None,
            'real_Dep': real_Dep,
            'ALL_Dep': ALL_Dep,
        }
        return render(request, 'enseignant/profile_Ens.html', context)

    except Enseignant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable')
        return redirect('comm:home')
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


@login_required
def profileUpdate_Ens(request):
    """
    Mise à jour du profil de l'enseignant.
    Permet à l'enseignant de modifier ses informations personnelles et de contact.
    """
    try:
        enseignant = request.user.enseignant_profile

        # Récupérer le département principal
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        departement = real_Dep.departement if real_Dep else None

        if request.method == 'POST':
            User_form = UserUpdateForm(request.POST, instance=request.user)
            Ens_form = ProfileUpdateEnsForm(request.POST, request.FILES, instance=enseignant)

            if User_form.is_valid() and Ens_form.is_valid():
                User_form.save()
                Ens_form.save()
                messages.success(request, 'تم تحديث المعلومات بنجاح')
                return redirect('ense:profile_Ens')
            else:
                messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
        else:
            User_form = UserUpdateForm(instance=request.user)
            Ens_form = ProfileUpdateEnsForm(instance=enseignant)

        context = {
            'title': 'تعديل الملف الشخصي',
            'active_menu': 'profile',
            'enseignant': enseignant,
            'my_Ens': enseignant,
            'my_Dep': departement,
            'my_Fac': departement.faculte if departement else None,
            'real_Dep': real_Dep,
            'User_form': User_form,
            'Ens_form': Ens_form,
        }
        return render(request, 'enseignant/profileUpdate_Ens.html', context)

    except Enseignant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable')
        return redirect('comm:home')
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


@login_required
def change_password_Ens(request):
    """
    Changement de mot de passe de l'enseignant (sans dep_id).
    """
    try:
        enseignant = request.user.enseignant_profile

        # Récupérer le département principal
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        departement = real_Dep.departement if real_Dep else None

        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            # Vérifier l'ancien mot de passe
            if not request.user.check_password(old_password):
                messages.error(request, 'كلمة المرور الحالية غير صحيحة / Mot de passe actuel incorrect')
            elif new_password != confirm_password:
                messages.error(request, 'كلمة المرور الجديدة وتأكيدها غير متطابقين / Les mots de passe ne correspondent pas')
            elif len(new_password) < 8:
                messages.error(request, 'كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل / Le mot de passe doit contenir au moins 8 caractères')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès')
                return redirect('ense:profile_Ens')

        context = {
            'title': 'تغيير كلمة المرور',
            'active_menu': 'profile',
            'enseignant': enseignant,
            'my_Ens': enseignant,
            'my_Dep': departement,
            'my_Fac': departement.faculte if departement else None,
            'real_Dep': real_Dep,
        }
        return render(request, 'enseignant/change_password_Ens.html', context)

    except Enseignant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للأستاذ / Profil enseignant introuvable')
        return redirect('comm:home')
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


# ══════════════════════════════════════════════════════════════
# VUES POUR LA LISTE DES ENSEIGNANTS
# ══════════════════════════════════════════════════════════════

@login_required
def list_Ens(request):
    """
    Liste de tous les enseignants.
    Affiche la liste complète des enseignants avec possibilité de recherche et filtrage.
    """
    try:
        # Récupérer tous les enseignants actifs
        enseignants = Enseignant.objects.select_related(
            'user', 'grade', 'diplome', 'wilaya'
        ).all()

        # TODO: Ajouter des filtres et recherche selon les besoins
        # Par exemple: filter par grade, diplome, wilaya, etc.

        context = {
            'title': 'قائمة الأساتذة / Liste des enseignants',
            'enseignants': enseignants,
        }
        return render(request, 'enseignant/list_Ens.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


# ══════════════════════════════════════════════════════════════
# VUES POUR LES DÉTAILS D'UN ENSEIGNANT
# ══════════════════════════════════════════════════════════════

@login_required
def detail_Ens(request, enseignant_id):
    """
    Détails complets d'un enseignant.
    Affiche toutes les informations détaillées d'un enseignant spécifique.
    """
    try:
        enseignant = get_object_or_404(
            Enseignant.objects.select_related('user', 'grade', 'diplome', 'wilaya'),
            id=enseignant_id
        )

        context = {
            'title': f'تفاصيل الأستاذ / Détails enseignant - {enseignant.get_nom_complet()}',
            'enseignant': enseignant,
        }
        return render(request, 'enseignant/detail_Ens.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('ense:list_Ens')


# ══════════════════════════════════════════════════════════════
# VUES POUR L'EMPLOI DU TEMPS DE L'ENSEIGNANT
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def timeTable_Ens(request, dep_id, enseignant, departement):
    """
    Affiche l'emploi du temps de l'enseignant avec statistiques par semestre.
    """
    try:
        # Recuperer le departement permanent de l'enseignant
        try:
            real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
        except Ens_Dep.DoesNotExist:
            real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

        # Recuperer le parametre semestre (par defaut S1)
        semestre_selected = request.GET.get('semestre', '1')

        # Recuperer l'objet semestre
        try:
            semestre_obj = Semestre.objects.get(numero=semestre_selected)
        except Semestre.DoesNotExist:
            semestre_obj = Semestre.objects.filter(numero='1').first()
            semestre_selected = '1'

        my_Dep = departement

        # Variables communes
        all_Classe_Ens = []
        nbr_Cours = 0
        nbr_TP = 0
        nbr_TD = 0
        nbr_SS = 0

        all_Ens_Dep = Ens_Dep.objects.filter(departement=departement.id).order_by('enseignant__nom_ar')

        # Filtre de base pour les classes
        base_filter = {
            'enseignant__departement': my_Dep.id,
            'enseignant__enseignant': enseignant.id,
            'semestre': semestre_obj
        }

        # Recuperer les classes par jour
        jours = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']
        for jour in jours:
            classes_jour = Classe.objects.filter(
                **base_filter,
                jour=jour
            ).select_related('matiere', 'niv_spe_dep_sg').order_by('temps')
            all_Classe_Ens.extend(classes_jour)

        # Recuperer les classes par horaire
        all_Classe_Time = []
        horaires = [
            '08:00-09:30',
            '09:40-11:10',
            '11:20-12:50',
            '13:10-14:40',
            '14:50-16:20',
            '16:30-18:00'
        ]

        for horaire in horaires:
            classes_horaire = Classe.objects.filter(
                **base_filter,
                temps=horaire
            ).select_related('matiere', 'niv_spe_dep_sg')
            all_Classe_Time.extend(classes_horaire)

        sixClasses = horaires

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
            total_abs = Abs_Etu_Seance.objects.filter(
                seance__classe=idx1,
                present=False
            ).count()
            idx1.total_absences = total_abs

        all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

        sevenDays = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']

        # Recuperer les statistiques depuis Ens_Dep selon le semestre
        stats_classes = {'total': 0, 'cours': 0, 'td': 0, 'tp': 0, 'ss': 0, 'jours': 0, 'vol_horaire': 0}
        if real_Dep:
            if semestre_selected == '1':
                stats_classes = {
                    'total': getattr(real_Dep, 'nbrClas_in_Dep_S1', 0) or 0,
                    'cours': getattr(real_Dep, 'nbrClas_Cours_in_Dep_S1', 0) or 0,
                    'td': getattr(real_Dep, 'nbrClas_TD_in_Dep_S1', 0) or 0,
                    'tp': getattr(real_Dep, 'nbrClas_TP_in_Dep_S1', 0) or 0,
                    'ss': getattr(real_Dep, 'nbrClas_SS_in_Dep_S1', 0) or 0,
                    'jours': getattr(real_Dep, 'nbrJour_in_Dep_S1', 0) or 0,
                    'vol_horaire': getattr(real_Dep, 'volHor_in_Dep_S1', 0) or 0
                }
            else:
                stats_classes = {
                    'total': getattr(real_Dep, 'nbrClas_in_Dep_S2', 0) or 0,
                    'cours': getattr(real_Dep, 'nbrClas_Cours_in_Dep_S2', 0) or 0,
                    'td': getattr(real_Dep, 'nbrClas_TD_in_Dep_S2', 0) or 0,
                    'tp': getattr(real_Dep, 'nbrClas_TP_in_Dep_S2', 0) or 0,
                    'ss': getattr(real_Dep, 'nbrClas_SS_in_Dep_S2', 0) or 0,
                    'jours': getattr(real_Dep, 'nbrJour_in_Dep_S2', 0) or 0,
                    'vol_horaire': getattr(real_Dep, 'volHor_in_Dep_S2', 0) or 0
                }

        # Recuperer tous les semestres disponibles
        all_semestres = Semestre.objects.all().order_by('numero')

        context = {
            'title': 'استعمال الزمن',
            'all_Classe_Ens': all_Classe_Ens,
            'all_Ens_Dep': all_Ens_Dep,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'my_Ens': enseignant,
            'active_menu': 'timetable',
            'all_Classe_Time': all_Classe_Time,
            'nbr_Cours': nbr_Cours,
            'nbr_TP': nbr_TP,
            'sevenDays': sevenDays,
            'sixClasses': sixClasses,
            'nbr_TD': nbr_TD,
            'nbr_SS': nbr_SS,
            'all_classes': all_classes,
            'semestre_selected': semestre_selected,
            'semestre_obj': semestre_obj,
            'all_semestres': all_semestres,
            'stats_classes': stats_classes,
        }
        return render(request, 'enseignant/timeTable_Ens.html', context)

    except Exception as e:
        messages.error(request, f'خطأ في تحميل استعمال الزمن: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


@enseignant_access_required
def update_classe_moodle(request, dep_id, classe_id, enseignant, departement):
    """
    Vue pour mettre a jour le lien Moodle et l'observation d'une classe.
    """
    if request.method == 'POST':
        try:
            classe = Classe.objects.get(
                id=classe_id,
                enseignant__enseignant=enseignant,
                enseignant__departement=departement
            )

            # Mettre a jour les champs
            lien_moodle = request.POST.get('lien_moodle', '').strip()
            observation = request.POST.get('observation', '').strip()

            classe.lien_moodle = lien_moodle if lien_moodle else None
            classe.observation = observation
            classe.save()

            return JsonResponse({
                'success': True,
                'message': 'تم حفظ التعديلات بنجاح'
            })

        except Classe.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'الحصة غير موجودة'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'طريقة غير مسموحة'
    }, status=405)


# ══════════════════════════════════════════════════════════════
# VUES POUR LA GESTION DES SÉANCES
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Sea_Ens(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour afficher la liste des séances d'une classe.
    """
    try:
        # Récupérer la classe
        myClasse = get_object_or_404(
            Classe.objects.select_related(
                'matiere', 'semestre', 'enseignant__enseignant',
                'niv_spe_dep_sg__niv_spe_dep__specialite'
            ),
            id=clas_id,
            enseignant__enseignant=enseignant,
            enseignant__departement=departement
        )

        # Récupérer toutes les séances de cette classe
        all_Seances = Seance.objects.filter(
            classe=myClasse
        ).order_by('date', 'temps')

        # Ajouter les statistiques d'absences pour chaque séance
        seances_with_stats = []
        for seance in all_Seances:
            # Récupérer les statistiques d'absences pour cette séance
            absences = Abs_Etu_Seance.objects.filter(seance=seance)
            seance.nbr_presents = absences.filter(present=True).count()
            seance.nbr_absents = absences.filter(present=False, justifiee=False).count()
            seance.nbr_justifies = absences.filter(justifiee=True).count()
            seance.nbr_participations = absences.filter(participation=True).count()
            seance.total_etudiants = absences.count()
            seances_with_stats.append(seance)

        # Statistiques globales
        nbr_Sea_fait = all_Seances.filter(fait=True).count()
        nbr_Sea_annuler = all_Seances.filter(annuler=True).count()
        nbr_Sea_reste = all_Seances.filter(fait=False, annuler=False).count()

        # Taux d'avancement
        total_seances = all_Seances.count()
        taux_avancement = round((nbr_Sea_fait / total_seances) * 100) if total_seances > 0 else 0

        context = {
            'title': f'قائمة الحصص - {myClasse.matiere.nom_ar}',
            'active_menu': 'timetable',
            'my_Ens': enseignant,
            'my_Dep': departement,
            'myClasse': myClasse,
            'all_Seances': seances_with_stats,
            'nbr_Sea_fait': nbr_Sea_fait,
            'nbr_Sea_annuler': nbr_Sea_annuler,
            'nbr_Sea_reste': nbr_Sea_reste,
            'taux_avancement': taux_avancement,
        }

        return render(request, 'enseignant/list_Sea_Ens.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


@enseignant_access_required
def new_Seance_Ens(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour créer de nouvelles séances pour une classe.
    """
    try:
        # Récupérer la classe
        myClasse = get_object_or_404(
            Classe.objects.select_related(
                'matiere', 'semestre', 'enseignant__enseignant',
                'niv_spe_dep_sg__niv_spe_dep__specialite'
            ),
            id=clas_id,
            enseignant__enseignant=enseignant,
            enseignant__departement=departement
        )

        # Récupérer les sous-groupes disponibles
        sous_groupes_disponibles = SousGroupe.objects.filter(
            groupe_principal=myClasse.niv_spe_dep_sg
        ).order_by('ordre_affichage')

        # Création automatique ou complétion des séances manquantes
        action = request.GET.get('action')
        if action in ['auto_create', 'auto_complete']:
            from datetime import timedelta

            # Pour auto_create, vérifier si les séances n'ont pas déjà été créées
            if action == 'auto_create' and myClasse.seance_created:
                messages.warning(request, 'تم إنشاء الحصص مسبقاً لهذه المادة. استخدم "إكمال الحصص المفقودة" لإضافة الحصص الناقصة.')
                return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=clas_id)

            # Récupérer les dates du semestre
            semestre = myClasse.semestre
            if not semestre or not semestre.date_debut or not semestre.date_fin:
                messages.error(request, 'لم يتم تحديد تواريخ السداسي. يرجى التواصل مع الإدارة.')
                return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=clas_id)

            # Mapper les jours français vers les numéros de jour Python (weekday)
            jour_mapping = {
                'Samedi': 5,      # Saturday
                'Dimanche': 6,    # Sunday
                'Lundi': 0,       # Monday
                'Mardi': 1,       # Tuesday
                'Mercredi': 2,    # Wednesday
                'Jeudi': 3,       # Thursday
            }

            jour_classe = myClasse.jour
            temps_classe = myClasse.temps

            if jour_classe not in jour_mapping:
                messages.error(request, f'يوم الحصة غير صالح: {jour_classe}')
                return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=clas_id)

            target_weekday = jour_mapping[jour_classe]

            # Trouver la première date du jour cible dans le semestre
            current_date = semestre.date_debut
            while current_date.weekday() != target_weekday:
                current_date += timedelta(days=1)

            # Créer les séances pour chaque semaine (uniquement celles qui n'existent pas)
            seances_created = 0
            seances_existing = 0
            while current_date <= semestre.date_fin:
                # Vérifier si une séance existe déjà pour cette date
                if not Seance.objects.filter(classe=myClasse, date=current_date, temps=temps_classe).exists():
                    Seance.objects.create(
                        classe=myClasse,
                        date=current_date,
                        temps=temps_classe,
                        type_audience='groupe_complet',
                        intitule=None
                    )
                    seances_created += 1
                else:
                    seances_existing += 1

                # Passer à la semaine suivante
                current_date += timedelta(days=7)

            # Marquer la classe comme ayant ses séances créées
            if not myClasse.seance_created:
                myClasse.seance_created = True
                myClasse.save()

            if seances_created > 0:
                messages.success(request, f'تم إنشاء {seances_created} حصة جديدة. ({seances_existing} حصة موجودة مسبقاً)')
            else:
                messages.info(request, f'جميع الحصص موجودة بالفعل ({seances_existing} حصة)')

            return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=clas_id)

        if request.method == 'POST':
            date_seance = request.POST.get('date_seance')
            temps_seance = request.POST.get('temps_seance')
            intitule = request.POST.get('intitule', '').strip()
            type_audience = request.POST.get('type_audience', 'groupe_complet')

            # Créer la séance
            seance = Seance.objects.create(
                classe=myClasse,
                date=date_seance,
                temps=temps_seance,
                intitule=intitule if intitule else None,
                type_audience=type_audience
            )

            # Gérer les sous-groupes si nécessaire
            if type_audience == 'sous_groupe':
                sous_groupe_id = request.POST.get('sous_groupe_unique')
                if sous_groupe_id:
                    seance.sous_groupe_unique_id = sous_groupe_id
                    seance.save()
            elif type_audience == 'multi_sous_groupes':
                sous_groupes_ids = request.POST.getlist('sous_groupes_multiples')
                if sous_groupes_ids:
                    seance.sous_groupes_multiples.set(sous_groupes_ids)

            messages.success(request, 'تم إنشاء الحصة بنجاح')
            return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=clas_id)

        # Statistiques des séances existantes
        seances_existantes = Seance.objects.filter(classe=myClasse)
        nbr_seances_total = seances_existantes.count()
        nbr_seances_fait = seances_existantes.filter(fait=True).count()
        nbr_seances_reste = seances_existantes.filter(fait=False, annuler=False).count()
        taux_avancement = round((nbr_seances_fait / nbr_seances_total) * 100) if nbr_seances_total > 0 else 0

        context = {
            'title': f'إنشاء حصص - {myClasse.matiere.nom_ar}',
            'active_menu': 'timetable',
            'my_Ens': enseignant,
            'my_Dep': departement,
            'myClasse': myClasse,
            'sous_groupes_disponibles': sous_groupes_disponibles,
            'nbr_seances_total': nbr_seances_total,
            'nbr_seances_fait': nbr_seances_fait,
            'nbr_seances_reste': nbr_seances_reste,
            'taux_avancement': taux_avancement,
        }

        return render(request, 'enseignant/new_Seance_Ens.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


@enseignant_access_required
def update_seance(request, dep_id, sea_id, enseignant, departement):
    """
    Vue pour modifier une séance existante.
    """
    try:
        seance = get_object_or_404(
            Seance.objects.select_related(
                'classe__enseignant__enseignant',
                'classe__matiere',
                'classe__semestre',
                'classe__niv_spe_dep_sg'
            ),
            id=sea_id,
            classe__enseignant__enseignant=enseignant,
            classe__enseignant__departement=departement
        )

        if request.method == 'POST':
            try:
                from datetime import datetime

                # Mise à jour des champs de date et temps
                date_seance = request.POST.get('date')
                temps_seance = request.POST.get('temps')

                if date_seance:
                    # Convertir explicitement la date
                    seance.date = datetime.strptime(date_seance, '%Y-%m-%d').date()
                if temps_seance:
                    seance.temps = temps_seance

                # Mise à jour des autres champs
                seance.intitule = request.POST.get('intitule', '').strip() or None
                fait_checked = request.POST.get('fait') == 'on'
                seance.fait = fait_checked
                seance.annuler = request.POST.get('annuler') == 'on'
                seance.remplacer = request.POST.get('remplacer') == 'on'
                seance.obs = request.POST.get('obs', '').strip()

                # Générer la liste des absences si la séance est marquée comme faite
                # et que la liste n'a pas encore été générée
                # Pour les séances de type "Cours", vérifier si l'utilisateur a confirmé
                create_absence_list = request.POST.get('create_absence_list', 'no')

                if fait_checked and not seance.list_abs_etudiant_generee and create_absence_list == 'yes':
                    myClasse = seance.classe
                    niv_spe_dep_sg = myClasse.niv_spe_dep_sg

                    # Récupérer les étudiants selon le type de la classe et l'audience
                    etudiants = []

                    # Pour les séances de type "Cours" avec une Section
                    # Les étudiants sont dans les Groupes de cette Section
                    if myClasse.type == 'Cours' and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
                        # Récupérer tous les NivSpeDep_SG qui ont le même niv_spe_dep et la même section
                        from apps.academique.departement.models import NivSpeDep_SG
                        groupes_de_section = NivSpeDep_SG.objects.filter(
                            niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                            section=niv_spe_dep_sg.section,
                            groupe__isnull=False  # Seulement les groupes (pas les sections)
                        )
                        # Récupérer tous les étudiants de ces groupes
                        etudiants = Etudiant.objects.filter(
                            niv_spe_dep_sg__in=groupes_de_section,
                            est_actif=True
                        ).distinct()

                    elif seance.type_audience == 'groupe_complet':
                        # Tous les étudiants du groupe/section direct
                        etudiants = Etudiant.objects.filter(
                            niv_spe_dep_sg=niv_spe_dep_sg,
                            est_actif=True
                        )
                    elif seance.type_audience == 'sous_groupe' and seance.sous_groupe_unique:
                        # Étudiants du sous-groupe spécifique
                        etu_sg = EtudiantSousGroupe.objects.filter(
                            sous_groupe=seance.sous_groupe_unique
                        ).values_list('etudiant_id', flat=True)
                        etudiants = Etudiant.objects.filter(id__in=etu_sg, est_actif=True)
                    elif seance.type_audience == 'multi_sous_groupes':
                        # Étudiants de plusieurs sous-groupes
                        etu_sg = EtudiantSousGroupe.objects.filter(
                            sous_groupe__in=seance.sous_groupes_multiples.all()
                        ).values_list('etudiant_id', flat=True)
                        etudiants = Etudiant.objects.filter(id__in=etu_sg, est_actif=True)
                    else:
                        # Par défaut, tous les étudiants du groupe
                        etudiants = Etudiant.objects.filter(
                            niv_spe_dep_sg=niv_spe_dep_sg,
                            est_actif=True
                        )

                    # Créer les entrées d'absence pour chaque étudiant
                    for etudiant in etudiants:
                        Abs_Etu_Seance.objects.get_or_create(
                            seance=seance,
                            etudiant=etudiant,
                            defaults={
                                'present': False,
                                'justifiee': False,
                                'participation': False,
                                'type_audience_lors_creation': seance.type_audience or 'groupe_complet',
                            }
                        )

                    # Marquer que la liste a été générée
                    seance.list_abs_etudiant_generee = True

                seance.save()

                messages.success(request, 'تم تحديث الحصة بنجاح')
                return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=seance.classe.id)
            except Exception as save_error:
                messages.error(request, f'خطأ في حفظ البيانات: {str(save_error)}')

        context = {
            'title': 'تعديل الحصة',
            'active_menu': 'timetable',
            'my_Ens': enseignant,
            'my_Dep': departement,
            'seance': seance,
            'myClasse': seance.classe,
        }

        return render(request, 'enseignant/update_seance.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


@enseignant_access_required
def delete_seance(request, dep_id, sea_id, enseignant, departement):
    """
    Vue pour supprimer une séance.
    """
    try:
        seance = get_object_or_404(
            Seance.objects.select_related('classe__enseignant__enseignant'),
            id=sea_id,
            classe__enseignant__enseignant=enseignant,
            classe__enseignant__departement=departement
        )

        clas_id = seance.classe.id
        seance.delete()

        messages.success(request, 'تم حذف الحصة بنجاح')
        return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=clas_id)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE POUR LA LISTE DES ABSENCES DES ÉTUDIANTS
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Abs_Etu(request, dep_id, sea_id, enseignant, departement):
    """
    Vue pour gérer les absences des étudiants pour une séance donnée.
    Permet de marquer la présence, l'absence justifiée, la participation et les points bonus.
    """
    from decimal import Decimal

    try:
        # Récupérer la séance avec vérification des permissions
        mySeance = get_object_or_404(
            Seance.objects.select_related(
                'classe__enseignant__enseignant',
                'classe__matiere',
                'classe__semestre',
                'classe__niv_spe_dep_sg'
            ),
            id=sea_id,
            classe__enseignant__enseignant=enseignant,
            classe__enseignant__departement=departement
        )

        # Récupérer toutes les absences pour cette séance
        all_Abs_Etu = Abs_Etu_Seance.objects.filter(
            seance=mySeance
        ).select_related('etudiant').order_by('etudiant__nom_ar', 'etudiant__prenom_ar')

        if request.method == 'POST':
            try:
                # Traitement des données du formulaire
                for abs_etu in all_Abs_Etu:
                    abs_id = abs_etu.id

                    # Récupérer les valeurs du formulaire
                    present = request.POST.get(f'present_{abs_id}') == '1'
                    justifiee = request.POST.get(f'justifiee_{abs_id}') == '1'
                    participation = request.POST.get(f'participation_{abs_id}') == '1'
                    points_str = request.POST.get(f'points_sup_seance_{abs_id}', '0')
                    observation = request.POST.get(f'observation_{abs_id}', '').strip()

                    # Convertir les points
                    try:
                        points = Decimal(points_str) if points_str else Decimal('0.0')
                        points = max(Decimal('0.0'), min(Decimal('2.0'), points))
                    except:
                        points = Decimal('0.0')

                    # Mise à jour des données
                    abs_etu.present = present
                    abs_etu.justifiee = justifiee if not present else False
                    abs_etu.participation = participation if present else False
                    abs_etu.points_sup_seance = points if present else Decimal('0.0')
                    abs_etu.obs = observation
                    abs_etu.save()

                # Mettre à jour les compteurs d'absences dans Gestion_Etu_Classe
                # pour chaque étudiant de cette classe
                myClasse = mySeance.classe
                etudiants_ids = all_Abs_Etu.values_list('etudiant_id', flat=True).distinct()

                for etudiant_id in etudiants_ids:
                    # Compter les absences totales (present=False) pour cet étudiant dans cette classe
                    absences_seances = Abs_Etu_Seance.objects.filter(
                        seance__classe=myClasse,
                        etudiant_id=etudiant_id
                    )
                    total_absences = absences_seances.filter(present=False).count()
                    absences_justifiees = absences_seances.filter(present=False, justifiee=True).count()
                    total_seances = absences_seances.count()
                    total_points_sup = absences_seances.aggregate(
                        total=Sum('points_sup_seance')
                    )['total'] or Decimal('0')

                    # Mettre à jour ou créer Gestion_Etu_Classe
                    gestion, _ = Gestion_Etu_Classe.objects.get_or_create(
                        classe=myClasse,
                        etudiant_id=etudiant_id
                    )
                    gestion.nbr_absence = total_absences
                    gestion.nbr_absence_justifiee = absences_justifiees
                    gestion.nbr_seances_totales = total_seances
                    gestion.total_sup_seance = total_points_sup

                    # Calculer automatiquement la note de présence (max 0, 5 - absences non justifiées)
                    absences_non_justifiees = total_absences - absences_justifiees
                    gestion.note_presence = max(Decimal('0'), Decimal('5') - Decimal(absences_non_justifiees))

                    gestion.save()

                messages.success(request, 'تم حفظ الغيابات بنجاح')
                return redirect('ense:list_Sea_Ens', dep_id=dep_id, clas_id=mySeance.classe.id)

            except Exception as save_error:
                messages.error(request, f'خطأ في حفظ البيانات: {str(save_error)}')

        # Calculer les statistiques
        present_count = all_Abs_Etu.filter(present=True).count()
        justified_count = all_Abs_Etu.filter(justifiee=True).count()
        absent_count = all_Abs_Etu.count() - present_count - justified_count

        context = {
            'title': 'قائمة الغيابات',
            'active_menu': 'timetable',
            'my_Ens': enseignant,
            'my_Dep': departement,
            'mySeance': mySeance,
            'all_Abs_Etu': all_Abs_Etu,
            'present_count': present_count,
            'justified_count': justified_count,
            'absent_count': max(0, absent_count),
            'titre_00': mySeance.classe.niv_spe_dep_sg,
            'titre_01': mySeance.classe.matiere.nom_ar,
            'titre_02': mySeance.date,
        }

        return render(request, 'enseignant/list_Abs_Etu.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUES POUR LA LISTE DES ENSEIGNANTS DU DÉPARTEMENT
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_enseignants_ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des enseignants du département par semestre.
    Version simplifiée pour les enseignants.
    """
    try:
        # Récupérer l'année universitaire courante
        annee_courante = AnneeUniversitaire.get_courante()

        if not annee_courante:
            messages.warning(request, 'لا توجد سنة جامعية محددة كسنة حالية')
            # Continuer sans filtrer par année

        # Récupérer le paramètre semestre (par défaut 1)
        semestre_num = int(request.GET.get('semestre', '1'))
        if semestre_num not in [1, 2]:
            semestre_num = 1

        # Construire le filtre dynamique pour le semestre
        filter_kwargs = {
            'departement': departement,
        }

        # Ajouter le filtre année si disponible
        if annee_courante:
            filter_kwargs['annee_univ'] = annee_courante

        # Ajouter le filtre semestre
        if semestre_num == 1:
            filter_kwargs['semestre_1'] = True
        else:
            filter_kwargs['semestre_2'] = True

        # Récupérer tous les enseignants du département
        all_Ens_Dep = Ens_Dep.objects.filter(**filter_kwargs).select_related(
            'enseignant__grade',
            'enseignant__user__poste_principal',
            'enseignant'
        )

        # Calculer les taux d'avancement pour le semestre sélectionné
        try:
            semestre_obj = Semestre.objects.get(numero=str(semestre_num))
        except Semestre.DoesNotExist:
            semestre_obj = None

        for ens_dep in all_Ens_Dep:
            # Filtrer les classes de cet enseignant dans ce département
            classes_filter = {
                'enseignant__enseignant': ens_dep.enseignant,
                'enseignant__departement': departement,
            }
            if semestre_obj:
                classes_filter['semestre'] = semestre_obj

            classes = Classe.objects.filter(**classes_filter)

            if classes.exists():
                stats = classes.aggregate(
                    taux_min=Min('taux_avancement'),
                    taux_moy=Avg('taux_avancement')
                )
                ens_dep.taux_min_display = int(stats.get('taux_min') or 0)
                ens_dep.taux_moy_display = round(stats.get('taux_moy') or 0, 1)
            else:
                ens_dep.taux_min_display = 0
                ens_dep.taux_moy_display = 0.0

        # Tri personnalisé: statut puis nom alphabétique
        statut_order = {
            'Permanent': 1,
            'Permanent & Vacataire': 2,
            'Vacataire': 3,
            'Associe': 4,
            'Doctorant': 5
        }

        all_Ens_Dep_sorted = sorted(
            all_Ens_Dep,
            key=lambda x: (
                statut_order.get(x.statut, 99),
                x.enseignant.nom_ar or '',
                x.enseignant.prenom_ar or ''
            )
        )

        # Statistiques
        total_enseignants = len(all_Ens_Dep_sorted)
        count_per = len([x for x in all_Ens_Dep_sorted if x.statut == 'Permanent'])
        count_temp = len([x for x in all_Ens_Dep_sorted if x.statut != 'Permanent'])
        count_scholar = len([x for x in all_Ens_Dep_sorted if x.enseignant.googlescholar])

        # Statistiques par grade
        grade_stats = all_Ens_Dep.values('enseignant__grade__nom_ar').annotate(
            count=Count('id')
        ).order_by('-count')

        context = {
            'title': 'قائمة الأساتذة',
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'my_Ens': enseignant,
            'active_menu': 'enseignants',
            'annee_courante': annee_courante,
            'semestre_num': semestre_num,
            'all_Ens_Dep': all_Ens_Dep_sorted,
            'total_enseignants': total_enseignants,
            'count_per': count_per,
            'count_temp': count_temp,
            'count_scholar': count_scholar,
            'grade_stats': grade_stats,
        }

        return render(request, 'enseignant/list_enseignants_ens.html', context)

    except Exception as e:
        messages.error(request, f'خطأ في تحميل قائمة الأساتذة: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUES POUR LA LISTE DES MATIÈRES
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Mat_Niv_Ens(request, dep_id, enseignant, departement):
    """
    Liste des matières/modules adaptée pour l'enseignant.
    Affiche un formulaire de filtrage en cascade et la liste des matières.
    """
    context = {
        'title': 'قائمة المواد',
        'my_Dep': departement,
        'my_Fac': departement.faculte,
        'my_Ens': enseignant,
        'active_menu': 'matieres',
    }
    return render(request, 'enseignant/list_Mat_Niv_Ens.html', context)


@enseignant_access_required
def matieres_json_ens(request, dep_id, enseignant, departement):
    """
    Vue AJAX pour charger les données en cascade (réformes, niveaux, spécialités, semestres, matières).
    """
    try:
        if request.method == 'POST':
            action = request.POST.get('action', '')

            # Charger les réformes disponibles pour ce département
            if action == 'get_reformes':
                # Récupérer les réformes qui ont des spécialités dans ce département
                # Note: related_name='specialites' sur Specialite.reforme
                reformes = Reforme.objects.filter(
                    specialites__departement=departement
                ).distinct().values('id', 'code', 'nom_ar', 'nom_fr').order_by('code')
                return JsonResponse({'data': list(reformes)})

            # Charger les niveaux pour une réforme
            elif action == 'get_niveaux':
                reforme_id = request.POST.get('reforme')
                if reforme_id:
                    # Récupérer les niveaux via NivSpeDep (relation inverse depuis Niveau)
                    niveaux = Niveau.objects.filter(
                        nivspedep__specialite__reforme_id=reforme_id,
                        nivspedep__departement=departement
                    ).distinct().values('id', 'code', 'nom_ar', 'nom_fr').order_by('code')
                    return JsonResponse({'data': list(niveaux)})
                return JsonResponse({'data': []})

            # Charger les spécialités pour un niveau et une réforme
            elif action == 'get_specialites':
                reforme_id = request.POST.get('reforme')
                niveau_id = request.POST.get('niveau')
                if reforme_id and niveau_id:
                    specialites = Specialite.objects.filter(
                        reforme_id=reforme_id,
                        departement=departement,
                        nivspedep__niveau_id=niveau_id
                    ).distinct().values('id', 'code', 'nom_ar', 'nom_fr').order_by('nom_ar')
                    return JsonResponse({'data': list(specialites)})
                return JsonResponse({'data': []})

            # Charger les semestres
            elif action == 'get_semestres':
                semestres = Semestre.objects.all().values('id', 'numero', 'nom_ar', 'nom_fr').order_by('numero')
                return JsonResponse({'data': list(semestres)})

            # Charger les matières
            elif action == 'get_matieres':
                reforme_id = request.POST.get('reforme')
                niveau_id = request.POST.get('niveau')
                specialite_id = request.POST.get('specialite')
                semestre_id = request.POST.get('semestre')

                # Construire les filtres
                filters = {'niv_spe_dep__departement': departement}

                if reforme_id:
                    filters['niv_spe_dep__specialite__reforme_id'] = reforme_id
                if niveau_id:
                    filters['niv_spe_dep__niveau_id'] = niveau_id
                if specialite_id:
                    filters['niv_spe_dep__specialite_id'] = specialite_id
                if semestre_id:
                    filters['semestre_id'] = semestre_id

                # Récupérer les matières
                matieres = Matiere.objects.filter(**filters).values(
                    'id', 'nom_ar', 'nom_fr', 'code', 'coeff', 'credit'
                ).order_by('code')

                return JsonResponse({'data': list(matieres)})

            return JsonResponse({'data': []})

        return JsonResponse({'data': []})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# VUE POUR LA LISTE DES SPÉCIALITÉS
# ══════════════════════════════════════════════════════════════

def _safe_str(value, default='-'):
    """Helper function to safely convert value to string, handling encoding errors."""
    if value is None:
        return default
    try:
        return str(value)
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            # Try to decode as latin-1 if utf-8 fails
            if isinstance(value, bytes):
                return value.decode('latin-1', errors='replace')
            return str(value).encode('latin-1', errors='replace').decode('utf-8', errors='replace')
        except Exception:
            return default


@enseignant_access_required
def list_Specialite_Ens(request, dep_id, enseignant, departement):
    """
    Liste des spécialités du département adaptée pour l'enseignant.
    Affiche toutes les spécialités avec statistiques.
    """
    try:
        # Récupérer toutes les spécialités du département
        queryset = Specialite.objects.filter(
            departement=departement
        ).select_related('reforme', 'identification', 'parcours').order_by('reforme__code', 'nom_ar')

        # Statistiques de base
        total_count = queryset.count()
        count_with_reforme = queryset.filter(reforme__isnull=False).count()
        count_with_identification = queryset.filter(identification__isnull=False).count()
        reformes_count = queryset.values('reforme').distinct().count()

        # Convertir le queryset en liste de dictionnaires pour éviter les problèmes d'encodage dans le template
        all_Specialite_Ens = []
        for spe in queryset:
            try:
                spe_data = {
                    'id': spe.id,
                    'nom_ar': _safe_str(spe.nom_ar),
                    'nom_fr': _safe_str(spe.nom_fr),
                    'code': _safe_str(spe.code),
                    'reforme': None,
                    'identification': None,
                    'parcours': None,
                }
                if spe.reforme:
                    spe_data['reforme'] = {
                        'nom_ar': _safe_str(spe.reforme.nom_ar),
                        'code': _safe_str(spe.reforme.code),
                    }
                if spe.identification:
                    spe_data['identification'] = {
                        'nom_ar': _safe_str(spe.identification.nom_ar if hasattr(spe.identification, 'nom_ar') else None),
                        'code': _safe_str(spe.identification.code if hasattr(spe.identification, 'code') else None),
                    }
                if spe.parcours:
                    spe_data['parcours'] = {
                        'nom_ar': _safe_str(spe.parcours.nom_ar if hasattr(spe.parcours, 'nom_ar') else None),
                        'code': _safe_str(spe.parcours.code if hasattr(spe.parcours, 'code') else None),
                    }
                all_Specialite_Ens.append(spe_data)
            except Exception:
                # Skip problematic records
                continue

        # Statistiques par réforme
        reforme_stats = []
        try:
            stats = queryset.exclude(reforme__isnull=True).values(
                'reforme__code', 'reforme__nom_ar'
            ).annotate(count=Count('id')).order_by('-count')
            for stat in stats:
                reforme_stats.append({
                    'reforme__code': _safe_str(stat.get('reforme__code')),
                    'reforme__nom_ar': _safe_str(stat.get('reforme__nom_ar')),
                    'count': stat.get('count', 0),
                })
        except Exception:
            reforme_stats = []

        context = {
            'title': 'قائمة التخصصات',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'active_menu': 'specialites',
            'all_Specialite_Ens': all_Specialite_Ens,
            'total_count': total_count,
            'count_with_reforme': count_with_reforme,
            'count_with_identification': count_with_identification,
            'reformes_count': reformes_count,
            'reforme_stats': reforme_stats,
        }
        return render(request, 'enseignant/list_Specialite_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل قائمة التخصصات: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE POUR LA LISTE DES AMPHITHÉÂTRES
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Amphi_Ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des amphithéâtres du département pour un enseignant.
    Affiche les amphithéâtres par semestre avec leurs capacités.
    """
    try:
        # Récupération des amphithéâtres par semestre
        all_Amphi_Dep_S1 = Amphi_Dep.objects.filter(
            departement=departement,
            semestre_1=True,
            est_actif=True
        ).select_related('amphi').order_by('amphi__numero')

        all_Amphi_Dep_S2 = Amphi_Dep.objects.filter(
            departement=departement,
            semestre_2=True,
            est_actif=True
        ).select_related('amphi').order_by('amphi__numero')

        # Statistiques
        total_amphi_s1 = all_Amphi_Dep_S1.count()
        total_amphi_s2 = all_Amphi_Dep_S2.count()
        total_amphi = total_amphi_s1 + total_amphi_s2

        # Capacité totale
        capacite_s1 = sum(a.amphi.capacite or 0 for a in all_Amphi_Dep_S1)
        capacite_s2 = sum(a.amphi.capacite or 0 for a in all_Amphi_Dep_S2)

        context = {
            'title': 'قائمة المدرجات',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'active_menu': 'amphi',
            'all_Amphi_Dep_S1': all_Amphi_Dep_S1,
            'all_Amphi_Dep_S2': all_Amphi_Dep_S2,
            'total_amphi_s1': total_amphi_s1,
            'total_amphi_s2': total_amphi_s2,
            'total_amphi': total_amphi,
            'capacite_s1': capacite_s1,
            'capacite_s2': capacite_s2,
        }

        return render(request, 'enseignant/list_Amphi_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل قائمة المدرجات: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE POUR LA LISTE DES SALLES
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Salle_Ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des salles du département pour un enseignant.
    Affiche les salles par semestre avec leurs capacités.
    """
    try:
        # Récupération des salles par semestre
        all_Salle_Dep_S1 = Salle_Dep.objects.filter(
            departement=departement,
            semestre_1=True,
            est_actif=True
        ).select_related('salle').order_by('salle__numero')

        all_Salle_Dep_S2 = Salle_Dep.objects.filter(
            departement=departement,
            semestre_2=True,
            est_actif=True
        ).select_related('salle').order_by('salle__numero')

        # Statistiques
        total_salle_s1 = all_Salle_Dep_S1.count()
        total_salle_s2 = all_Salle_Dep_S2.count()
        total_salle = total_salle_s1 + total_salle_s2

        # Capacité totale
        capacite_s1 = sum(s.salle.capacite or 0 for s in all_Salle_Dep_S1)
        capacite_s2 = sum(s.salle.capacite or 0 for s in all_Salle_Dep_S2)

        context = {
            'title': 'قائمة القاعات',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'active_menu': 'salle',
            'all_Salle_Dep_S1': all_Salle_Dep_S1,
            'all_Salle_Dep_S2': all_Salle_Dep_S2,
            'total_salle_s1': total_salle_s1,
            'total_salle_s2': total_salle_s2,
            'total_salle': total_salle,
            'capacite_s1': capacite_s1,
            'capacite_s2': capacite_s2,
        }

        return render(request, 'enseignant/list_Salle_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل قائمة القاعات: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE LISTE DES LABORATOIRES
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Labo_Ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des laboratoires du département pour un enseignant.
    Affiche les laboratoires par semestre avec leurs équipements.
    """
    try:
        # Récupération des laboratoires par semestre
        all_Labo_Dep_S1 = Laboratoire_Dep.objects.filter(
            departement=departement,
            semestre_1=True,
            est_actif=True
        ).select_related('laboratoire').order_by('laboratoire__numero')

        all_Labo_Dep_S2 = Laboratoire_Dep.objects.filter(
            departement=departement,
            semestre_2=True,
            est_actif=True
        ).select_related('laboratoire').order_by('laboratoire__numero')

        # Statistiques
        total_labo_s1 = all_Labo_Dep_S1.count()
        total_labo_s2 = all_Labo_Dep_S2.count()
        total_labo = total_labo_s1 + total_labo_s2

        # Capacité totale
        capacite_s1 = sum(l.laboratoire.capacite or 0 for l in all_Labo_Dep_S1)
        capacite_s2 = sum(l.laboratoire.capacite or 0 for l in all_Labo_Dep_S2)

        context = {
            'title': 'قائمة المخابر',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'active_menu': 'labo',
            'all_Labo_Dep_S1': all_Labo_Dep_S1,
            'all_Labo_Dep_S2': all_Labo_Dep_S2,
            'total_labo_s1': total_labo_s1,
            'total_labo_s2': total_labo_s2,
            'total_labo': total_labo,
            'capacite_s1': capacite_s1,
            'capacite_s2': capacite_s2,
        }

        return render(request, 'enseignant/list_Labo_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل قائمة المخابر: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE EMPLOI DU TEMPS AMPHITHÉÂTRE
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def timeTable_Amphi_Ens(request, dep_id, amphi_dep_id, semestre_numero, enseignant, departement):
    """
    Vue pour afficher l'emploi du temps d'un amphithéâtre spécifique.
    Affiche les classes programmées par jour et créneau horaire.
    """
    try:
        # Récupération de l'amphithéâtre-département
        amphi_dep = get_object_or_404(
            Amphi_Dep,
            id=amphi_dep_id,
            departement=departement,
            est_actif=True
        )

        # Vérification du semestre
        if semestre_numero == 1 and not amphi_dep.semestre_1:
            messages.error(request, 'هذا المدرج غير متاح في السداسي الأول')
            return redirect('ense:list_Amphi_Ens', dep_id=dep_id)
        if semestre_numero == 2 and not amphi_dep.semestre_2:
            messages.error(request, 'هذا المدرج غير متاح في السداسي الثاني')
            return redirect('ense:list_Amphi_Ens', dep_id=dep_id)

        # Initialisation des compteurs
        nbr_Cours = 0
        nbr_TP = 0
        nbr_TD = 0
        nbr_SS = 0

        # Définition des créneaux horaires
        sixClasses = [
            '08:00-09:30',
            '09:40-11:10',
            '11:20-12:50',
            '13:10-14:40',
            '14:50-16:20',
            '16:30-18:00',
        ]

        # Définition des jours
        sevenDays = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']

        # ContentType pour Amphi_Dep
        lieu_content_type = ContentType.objects.get_for_model(Amphi_Dep)

        # Récupération de toutes les classes pour cet amphithéâtre
        all_Classe_Amp = Classe.objects.filter(
            content_type=lieu_content_type,
            object_id=amphi_dep_id,
            semestre__numero=semestre_numero
        ).select_related(
            'enseignant__enseignant',
            'matiere',
            'semestre',
            'niv_spe_dep_sg__niv_spe_dep__niveau',
            'niv_spe_dep_sg__niv_spe_dep__specialite',
            'niv_spe_dep_sg__niv_spe_dep__departement'
        ).order_by('jour', 'temps')

        # Création d'un dictionnaire pour accès rapide par jour/temps
        classes_by_slot = {}
        for classe in all_Classe_Amp:
            key = (classe.jour, classe.temps)
            if key not in classes_by_slot:
                classes_by_slot[key] = []
            classes_by_slot[key].append(classe)

            # Comptage par type
            if classe.type == "Cours":
                nbr_Cours += 1
            elif classe.type == "TP":
                nbr_TP += 1
            elif classe.type == "TD":
                nbr_TD += 1
            elif classe.type == "Sortie Scientifique":
                nbr_SS += 1

        all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

        context = {
            'title': f'استعمال الزمن - {amphi_dep.amphi.nom_ar or amphi_dep.amphi.nom_fr}',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'active_menu': 'amphi',
            'amphi_dep': amphi_dep,
            'semestre_numero': semestre_numero,
            'all_Classe_Amp': all_Classe_Amp,
            'classes_by_slot': classes_by_slot,
            'sevenDays': sevenDays,
            'sixClasses': sixClasses,
            'nbr_Cours': nbr_Cours,
            'nbr_TP': nbr_TP,
            'nbr_TD': nbr_TD,
            'nbr_SS': nbr_SS,
            'all_classes': all_classes,
        }

        return render(request, 'enseignant/timeTable_Amphi_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل استعمال الزمن: {str(e)}')
        return redirect('ense:list_Amphi_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE EMPLOI DU TEMPS SALLE
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def timeTable_Salle_Ens(request, dep_id, salle_dep_id, semestre_numero, enseignant, departement):
    """
    Vue pour afficher l'emploi du temps d'une salle spécifique.
    Affiche les classes programmées par jour et créneau horaire.
    """
    try:
        # Récupération de la salle-département
        salle_dep = get_object_or_404(
            Salle_Dep,
            id=salle_dep_id,
            departement=departement,
            est_actif=True
        )

        # Vérification du semestre
        if semestre_numero == 1 and not salle_dep.semestre_1:
            messages.error(request, 'هذه القاعة غير متاحة في السداسي الأول')
            return redirect('ense:list_Salle_Ens', dep_id=dep_id)
        if semestre_numero == 2 and not salle_dep.semestre_2:
            messages.error(request, 'هذه القاعة غير متاحة في السداسي الثاني')
            return redirect('ense:list_Salle_Ens', dep_id=dep_id)

        # Initialisation des compteurs
        nbr_Cours = 0
        nbr_TP = 0
        nbr_TD = 0
        nbr_SS = 0

        # Définition des créneaux horaires
        sixClasses = [
            '08:00-09:30',
            '09:40-11:10',
            '11:20-12:50',
            '13:10-14:40',
            '14:50-16:20',
            '16:30-18:00',
        ]

        # Définition des jours
        sevenDays = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']

        # ContentType pour Salle_Dep
        lieu_content_type = ContentType.objects.get_for_model(Salle_Dep)

        # Récupération de toutes les classes pour cette salle
        all_Classe_Salle = Classe.objects.filter(
            content_type=lieu_content_type,
            object_id=salle_dep_id,
            semestre__numero=semestre_numero
        ).select_related(
            'enseignant__enseignant',
            'matiere',
            'semestre',
            'niv_spe_dep_sg__niv_spe_dep__niveau',
            'niv_spe_dep_sg__niv_spe_dep__specialite',
            'niv_spe_dep_sg__niv_spe_dep__departement'
        ).order_by('jour', 'temps')

        # Création d'un dictionnaire pour accès rapide par jour/temps
        classes_by_slot = {}
        for classe in all_Classe_Salle:
            key = (classe.jour, classe.temps)
            if key not in classes_by_slot:
                classes_by_slot[key] = []
            classes_by_slot[key].append(classe)

            # Comptage par type
            if classe.type == "Cours":
                nbr_Cours += 1
            elif classe.type == "TP":
                nbr_TP += 1
            elif classe.type == "TD":
                nbr_TD += 1
            elif classe.type == "Sortie Scientifique":
                nbr_SS += 1

        all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

        context = {
            'title': f'استعمال الزمن - {salle_dep.salle.nom_ar or salle_dep.salle.nom_fr}',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'active_menu': 'salle',
            'salle_dep': salle_dep,
            'semestre_numero': semestre_numero,
            'all_Classe_Salle': all_Classe_Salle,
            'classes_by_slot': classes_by_slot,
            'sevenDays': sevenDays,
            'sixClasses': sixClasses,
            'nbr_Cours': nbr_Cours,
            'nbr_TP': nbr_TP,
            'nbr_TD': nbr_TD,
            'nbr_SS': nbr_SS,
            'all_classes': all_classes,
        }

        return render(request, 'enseignant/timeTable_Salle_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل استعمال الزمن: {str(e)}')
        return redirect('ense:list_Salle_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOI DU TEMPS LABORATOIRE
# ══════════════════════════════════════════════════════════════════════════════
@enseignant_access_required
def timeTable_Labo_Ens(request, dep_id, labo_dep_id, semestre_numero, enseignant, departement):
    """
    Vue pour afficher l'emploi du temps d'un laboratoire spécifique pour un enseignant
    """
    try:
        # Récupération du laboratoire-département
        labo_dep = get_object_or_404(
            Laboratoire_Dep,
            id=labo_dep_id,
            departement=departement,
            est_actif=True
        )

        # Vérification du semestre (champs boolean)
        if semestre_numero == 1 and not labo_dep.semestre_1:
            messages.error(request, 'هذا المخبر غير متاح في السداسي الأول')
            return redirect('ense:list_Labo_Ens', dep_id=dep_id)
        elif semestre_numero == 2 and not labo_dep.semestre_2:
            messages.error(request, 'هذا المخبر غير متاح في السداسي الثاني')
            return redirect('ense:list_Labo_Ens', dep_id=dep_id)

        # Initialisation des variables
        nbr_Cours = 0
        nbr_TP = 0
        nbr_TD = 0
        nbr_SS = 0

        # Définition des créneaux horaires
        sixClasses = [
            '08:00-09:30',
            '09:40-11:10',
            '11:20-12:50',
            '13:10-14:40',
            '14:50-16:20',
            '16:30-18:00',
        ]

        # Définition des jours
        sevenDays = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']

        # ContentType pour Laboratoire_Dep
        lieu_content_type = ContentType.objects.get_for_model(Laboratoire_Dep)

        # Récupération de toutes les classes pour ce laboratoire
        all_Classe_Labo = Classe.objects.filter(
            content_type=lieu_content_type,
            object_id=labo_dep_id,
            semestre__numero=semestre_numero
        ).select_related(
            'enseignant__enseignant',
            'matiere',
            'semestre',
            'niv_spe_dep_sg__niv_spe_dep__niveau',
            'niv_spe_dep_sg__niv_spe_dep__specialite',
            'niv_spe_dep_sg__niv_spe_dep__departement'
        ).order_by('jour', 'temps')

        # Créer une copie pour l'affichage par temps (même queryset)
        all_Classe_Time = all_Classe_Labo

        # Calcul des statistiques
        for classe in all_Classe_Labo:
            if classe.type == "Cours":
                nbr_Cours += 1
            elif classe.type == "TP":
                nbr_TP += 1
            elif classe.type == "TD":
                nbr_TD += 1
            elif classe.type == "Sortie Scientifique":
                nbr_SS += 1

        all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

        context = {
            'title': f'استعمال الزمن - {labo_dep.laboratoire.nom_ar}',
            'active_menu': 'labo',
            'my_Fac': departement.faculte,
            'my_Dep': departement,
            'my_Ens': enseignant,
            'labo_dep': labo_dep,
            'semestre_numero': semestre_numero,
            'all_Classe_Labo': all_Classe_Labo,
            'all_Classe_Time': all_Classe_Time,
            'sevenDays': sevenDays,
            'sixClasses': sixClasses,
            'nbr_Cours': nbr_Cours,
            'nbr_TP': nbr_TP,
            'nbr_TD': nbr_TD,
            'nbr_SS': nbr_SS,
            'all_classes': all_classes,
        }

        return render(request, 'enseignant/timeTable_Labo_Ens.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل استعمال الزمن: {str(e)}')
        return redirect('ense:list_Labo_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════════════════════
# FICHE PÉDAGOGIQUE SEMESTRIELLE
# ══════════════════════════════════════════════════════════════════════════════
@enseignant_access_required
def fichPeda_Ens_Semestre(request, dep_id, enseignant, departement):
    """
    Vue pour la fiche pédagogique semestrielle de l'enseignant
    """
    try:
        # Récupérer l'enseignant-département
        try:
            my_Ens = Ens_Dep.objects.select_related(
                'enseignant', 'departement'
            ).get(enseignant=enseignant, departement=departement)
        except Ens_Dep.DoesNotExist:
            messages.error(request, 'غير مصرح لك بالوصول إلى هذا القسم')
            return redirect('ense:dashboard_Ens', dep_id=dep_id)

        # Récupérer le semestre sélectionné (défaut: 1)
        semestre_selected = request.GET.get('semestre', '1')

        # Filtre de base pour les classes
        base_filter = {
            'enseignant__enseignant': my_Ens.enseignant,
            'enseignant__departement': departement,
            'semestre__numero': semestre_selected
        }

        # Récupérer les classes par jour dans l'ordre souhaité
        jours = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']
        all_Classe_Ens = []

        for jour in jours:
            classes_jour = Classe.objects.filter(
                **base_filter,
                jour=jour
            ).select_related(
                'matiere__unite',
                'niv_spe_dep_sg__niv_spe_dep__niveau',
                'niv_spe_dep_sg__niv_spe_dep__specialite',
                'niv_spe_dep_sg__section',
                'niv_spe_dep_sg__groupe'
            ).order_by('temps')
            all_Classe_Ens.extend(classes_jour)

        # Calculer les statistiques
        all_classes = len(all_Classe_Ens)

        # Calculer les volumes horaires
        vol_hor_cours = sum([2.25 for x in all_Classe_Ens if x.type == 'Cours'])
        vol_hor_TD = sum([1.5 for x in all_Classe_Ens if x.type == 'TD'])
        vol_hor_TP = sum([1.5 for x in all_Classe_Ens if x.type == 'TP'])
        vol_hor_Total = vol_hor_cours + vol_hor_TD + vol_hor_TP

        # Informations de l'université
        univ = "جامعة قاصدي مرباح ورقلة"

        # Année universitaire courante
        annee_univ = AnneeUniversitaire.objects.filter(est_courante=True).first()

        context = {
            'title': f'البطاقة البيداغوجية - السداسي {semestre_selected}',
            'active_menu': 'dashboard',
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'my_Ens': my_Ens,
            'semestre_selected': semestre_selected,
            'all_Classe_Ens': all_Classe_Ens,
            'all_classes': all_classes,
            'vol_hor_cours': vol_hor_cours,
            'vol_hor_TD': vol_hor_TD,
            'vol_hor_TP': vol_hor_TP,
            'vol_hor_Total': vol_hor_Total,
            'univ': univ,
            'annee_univ': annee_univ,
        }

        return render(request, 'enseignant/fichPeda_Ens_Semestre.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل البطاقة البيداغوجية: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════════════════════
# FICHE PÉDAGOGIQUE GLOBALE (DEUX SEMESTRES)
# ══════════════════════════════════════════════════════════════════════════════
@enseignant_access_required
def fichePedagogique(request, dep_id, enseignant, departement):
    """
    Vue pour la fiche pédagogique globale (deux semestres sur une page A4 paysage)
    """
    try:
        # Récupérer l'enseignant-département
        try:
            my_Ens = Ens_Dep.objects.select_related(
                'enseignant', 'departement'
            ).get(enseignant=enseignant, departement=departement)
        except Ens_Dep.DoesNotExist:
            messages.error(request, 'غير مصرح لك بالوصول إلى هذا القسم')
            return redirect('ense:dashboard_Ens', dep_id=dep_id)

        # Filtre de base pour les classes S1
        base_filter_S1 = {
            'enseignant__enseignant': my_Ens.enseignant,
            'enseignant__departement': departement,
            'semestre__numero': 1
        }

        # Filtre de base pour les classes S2
        base_filter_S2 = {
            'enseignant__enseignant': my_Ens.enseignant,
            'enseignant__departement': departement,
            'semestre__numero': 2
        }

        # Liste des jours dans l'ordre souhaité
        jours = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']

        # Récupérer les classes pour le semestre 1 par jour
        all_Classe_Ens_S1 = []
        for jour in jours:
            classes_jour = Classe.objects.filter(
                **base_filter_S1,
                jour=jour
            ).select_related(
                'matiere__unite',
                'niv_spe_dep_sg__niv_spe_dep__niveau',
                'niv_spe_dep_sg__niv_spe_dep__specialite',
                'niv_spe_dep_sg__section',
                'niv_spe_dep_sg__groupe'
            ).order_by('temps')
            all_Classe_Ens_S1.extend(classes_jour)

        # Récupérer les classes pour le semestre 2 par jour
        all_Classe_Ens_S2 = []
        for jour in jours:
            classes_jour = Classe.objects.filter(
                **base_filter_S2,
                jour=jour
            ).select_related(
                'matiere__unite',
                'niv_spe_dep_sg__niv_spe_dep__niveau',
                'niv_spe_dep_sg__niv_spe_dep__specialite',
                'niv_spe_dep_sg__section',
                'niv_spe_dep_sg__groupe'
            ).order_by('temps')
            all_Classe_Ens_S2.extend(classes_jour)

        # Calculer les statistiques S1
        all_classes_S1 = len(all_Classe_Ens_S1)
        vol_hor_cours_S1 = sum([2.25 for x in all_Classe_Ens_S1 if x.type == 'Cours'])
        vol_hor_TD_S1 = sum([1.5 for x in all_Classe_Ens_S1 if x.type == 'TD'])
        vol_hor_TP_S1 = sum([1.5 for x in all_Classe_Ens_S1 if x.type == 'TP'])
        vol_hor_Total_S1 = vol_hor_cours_S1 + vol_hor_TD_S1 + vol_hor_TP_S1

        # Calculer les statistiques S2
        all_classes_S2 = len(all_Classe_Ens_S2)
        vol_hor_cours_S2 = sum([2.25 for x in all_Classe_Ens_S2 if x.type == 'Cours'])
        vol_hor_TD_S2 = sum([1.5 for x in all_Classe_Ens_S2 if x.type == 'TD'])
        vol_hor_TP_S2 = sum([1.5 for x in all_Classe_Ens_S2 if x.type == 'TP'])
        vol_hor_Total_S2 = vol_hor_cours_S2 + vol_hor_TD_S2 + vol_hor_TP_S2

        # Total général
        vol_hor_Total_General = vol_hor_Total_S1 + vol_hor_Total_S2

        # Informations de l'université
        univ = "جامعة قاصدي مرباح ورقلة"

        # Année universitaire courante
        annee_univ = AnneeUniversitaire.objects.filter(est_courante=True).first()

        context = {
            'title': 'البطاقة البيداغوجية الشاملة',
            'active_menu': 'dashboard',
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'my_Ens': my_Ens,
            'all_Classe_Ens_S1': all_Classe_Ens_S1,
            'all_Classe_Ens_S2': all_Classe_Ens_S2,
            'all_classes_S1': all_classes_S1,
            'all_classes_S2': all_classes_S2,
            'vol_hor_cours_S1': vol_hor_cours_S1,
            'vol_hor_TD_S1': vol_hor_TD_S1,
            'vol_hor_TP_S1': vol_hor_TP_S1,
            'vol_hor_Total_S1': vol_hor_Total_S1,
            'vol_hor_cours_S2': vol_hor_cours_S2,
            'vol_hor_TD_S2': vol_hor_TD_S2,
            'vol_hor_TP_S2': vol_hor_TP_S2,
            'vol_hor_Total_S2': vol_hor_Total_S2,
            'vol_hor_Total_General': vol_hor_Total_General,
            'univ': univ,
            'annee_univ': annee_univ,
        }

        return render(request, 'enseignant/fichePedagogique.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'خطأ في تحميل البطاقة البيداغوجية الشاملة: {str(e)}')
        return redirect('ense:dashboard_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUES POUR LA LISTE DES ÉTUDIANTS
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Etudiant_Ens(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des étudiants du département.
    Gère les requêtes POST pour le filtrage AJAX des étudiants.
    """
    if request.method == 'POST':
        niv_spe_dep_sg_id = request.POST.get('niv_spe_dep_sg')

        if niv_spe_dep_sg_id:
            # Cas 1: Tous les étudiants d'un niveau
            if niv_spe_dep_sg_id.startswith('tous_'):
                parts = niv_spe_dep_sg_id.replace('tous_', '').split('_')
                niveau_id = parts[0]
                reforme_id = parts[1] if len(parts) > 1 else None

                # Filtres pour tous les groupes du niveau
                groupes_filters = {
                    'niv_spe_dep__departement': departement,
                    'niv_spe_dep__niveau_id': niveau_id
                }
                if reforme_id:
                    groupes_filters['niv_spe_dep__specialite__reforme_id'] = reforme_id

                # Récupérer TOUS les NivSpeDep_SG (sans exclure les sections)
                # car les étudiants peuvent être assignés à n'importe quel type
                groupes_niveau = NivSpeDep_SG.objects.filter(**groupes_filters).values_list('id', flat=True)

                etudiants_qs = Etudiant.objects.filter(
                    niv_spe_dep_sg_id__in=groupes_niveau
                ).select_related(
                    'niv_spe_dep_sg__section', 'niv_spe_dep_sg__groupe'
                ).distinct().order_by('nom_ar')

                etudiants = []
                for e in etudiants_qs:
                    etudiants.append({
                        'id': e.id,
                        'nom_ar': e.nom_ar,
                        'prenom_ar': e.prenom_ar,
                        'nom_fr': e.nom_fr,
                        'prenom_fr': e.prenom_fr,
                        'matricule': e.matricule,
                        'est_inscrit': e.est_inscrit,
                        'tel_mobile1': e.tel_mobile1,
                        'email_prof': e.email_prof,
                        'date_nais': str(e.date_nais) if e.date_nais else None,
                        'section_nom': e.niv_spe_dep_sg.section.nom_ar if e.niv_spe_dep_sg and e.niv_spe_dep_sg.section else None,
                        'groupe_nom': e.niv_spe_dep_sg.groupe.nom_ar if e.niv_spe_dep_sg and e.niv_spe_dep_sg.groupe else None,
                    })

            # Cas 2: Tous les étudiants d'une section
            elif niv_spe_dep_sg_id.startswith('section_'):
                parts = niv_spe_dep_sg_id.replace('section_', '').split('_')
                section_name = parts[0]
                reforme_id = parts[1] if len(parts) > 1 else None

                # Filtres pour la section - inclure aussi les sections conteneurs
                section_filters = {
                    'niv_spe_dep__departement': departement,
                    'section__nom_ar': section_name,
                    'section__isnull': False
                }
                if reforme_id:
                    section_filters['niv_spe_dep__specialite__reforme_id'] = reforme_id

                groupes_section = NivSpeDep_SG.objects.filter(**section_filters)
                groupes_ids = list(groupes_section.values_list('id', flat=True))

                etudiants_qs = Etudiant.objects.filter(
                    niv_spe_dep_sg_id__in=groupes_ids
                ).select_related(
                    'niv_spe_dep_sg__section', 'niv_spe_dep_sg__groupe'
                ).distinct().order_by('nom_ar')

                etudiants = []
                for e in etudiants_qs:
                    etudiants.append({
                        'id': e.id,
                        'nom_ar': e.nom_ar,
                        'prenom_ar': e.prenom_ar,
                        'nom_fr': e.nom_fr,
                        'prenom_fr': e.prenom_fr,
                        'matricule': e.matricule,
                        'est_inscrit': e.est_inscrit,
                        'tel_mobile1': e.tel_mobile1,
                        'email_prof': e.email_prof,
                        'date_nais': str(e.date_nais) if e.date_nais else None,
                        'section_nom': e.niv_spe_dep_sg.section.nom_ar if e.niv_spe_dep_sg and e.niv_spe_dep_sg.section else None,
                        'groupe_nom': e.niv_spe_dep_sg.groupe.nom_ar if e.niv_spe_dep_sg and e.niv_spe_dep_sg.groupe else None,
                    })

            # Cas 3: Groupe individuel ou Section container
            else:
                # Vérifier si c'est un section container (a une section mais pas de groupe)
                try:
                    selected_sg = NivSpeDep_SG.objects.select_related('section', 'groupe', 'niv_spe_dep').get(id=niv_spe_dep_sg_id)

                    if selected_sg.section and not selected_sg.groupe:
                        # C'est un section container: récupérer TOUS les étudiants de cette section
                        groupes_section_ids = NivSpeDep_SG.objects.filter(
                            niv_spe_dep=selected_sg.niv_spe_dep,
                            section=selected_sg.section
                        ).values_list('id', flat=True)

                        etudiants_qs = Etudiant.objects.filter(
                            niv_spe_dep_sg_id__in=groupes_section_ids
                        ).select_related(
                            'niv_spe_dep_sg__section', 'niv_spe_dep_sg__groupe'
                        ).order_by('nom_ar')
                    else:
                        # C'est un groupe individuel
                        etudiants_qs = Etudiant.objects.filter(
                            niv_spe_dep_sg_id=niv_spe_dep_sg_id
                        ).select_related(
                            'niv_spe_dep_sg__section', 'niv_spe_dep_sg__groupe'
                        ).order_by('nom_ar')
                except NivSpeDep_SG.DoesNotExist:
                    etudiants_qs = Etudiant.objects.none()

                etudiants = []
                for e in etudiants_qs:
                    etudiants.append({
                        'id': e.id,
                        'nom_ar': e.nom_ar,
                        'prenom_ar': e.prenom_ar,
                        'nom_fr': e.nom_fr,
                        'prenom_fr': e.prenom_fr,
                        'matricule': e.matricule,
                        'est_inscrit': e.est_inscrit,
                        'tel_mobile1': e.tel_mobile1,
                        'email_prof': e.email_prof,
                        'date_nais': str(e.date_nais) if e.date_nais else None,
                        'section_nom': e.niv_spe_dep_sg.section.nom_ar if e.niv_spe_dep_sg and e.niv_spe_dep_sg.section else None,
                        'groupe_nom': e.niv_spe_dep_sg.groupe.nom_ar if e.niv_spe_dep_sg and e.niv_spe_dep_sg.groupe else None,
                    })

            return JsonResponse({'data': etudiants})

        return JsonResponse({'data': []})

    # Requête GET: afficher le template
    context = {
        'title': 'قائمة الطلبة',
        'my_Dep': departement,
        'my_Fac': departement.faculte,
        'my_Ens': enseignant,
        'active_menu': 'etudiants',
    }
    return render(request, 'enseignant/list_etudiants_ens.html', context)


@enseignant_access_required
def etudiants_json_ens(request, dep_id, enseignant, departement):
    """
    Vue AJAX pour charger les données en cascade (réformes, niveaux, groupes).
    Utilisée par la page de liste des étudiants.
    """
    try:
        if request.method == 'POST':
            action = request.POST.get('action', '')

            # Charger les réformes disponibles pour ce département
            if action == 'get_reformes':
                reformes = Reforme.objects.filter(
                    specialites__departement=departement
                ).distinct().values('id', 'code', 'nom_ar', 'nom_fr').order_by('code')
                return JsonResponse({'data': list(reformes)})

            # Charger les niveaux pour une réforme
            elif action == 'get_niveaux':
                reforme_id = request.POST.get('reforme')
                if reforme_id:
                    niveaux = Niveau.objects.filter(
                        nivspedep__specialite__reforme_id=reforme_id,
                        nivspedep__departement=departement
                    ).distinct().values('id', 'code', 'nom_ar', 'nom_fr').order_by('code')
                    return JsonResponse({'data': list(niveaux)})
                return JsonResponse({'data': []})

            # Charger les groupes (NivSpeDep_SG) pour un niveau et une réforme
            elif action == 'get_groupes':
                reforme_id = request.POST.get('reforme')
                niveau_id = request.POST.get('niveau')

                if reforme_id and niveau_id:
                    # Récupérer TOUS les NivSpeDep_SG (y compris sections containers)
                    groupes = NivSpeDep_SG.objects.filter(
                        niv_spe_dep__departement=departement,
                        niv_spe_dep__niveau_id=niveau_id,
                        niv_spe_dep__specialite__reforme_id=reforme_id
                    ).select_related(
                        'section', 'groupe', 'niv_spe_dep__specialite'
                    ).order_by('section__nom_ar', 'groupe__nom_ar')

                    data = []
                    for g in groupes:
                        # Déterminer le nom à afficher et compter les étudiants
                        if g.groupe:
                            # Groupe individuel: compter directement
                            display_nom = g.groupe.nom_ar
                            nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg_id=g.id).count()
                        elif g.section:
                            # Section container: compter TOUS les étudiants de cette section
                            display_nom = f"{g.section.nom_ar} (قطاع كامل)"
                            # Récupérer tous les groupes de cette section
                            groupes_section_ids = NivSpeDep_SG.objects.filter(
                                niv_spe_dep=g.niv_spe_dep,
                                section=g.section
                            ).values_list('id', flat=True)
                            nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg_id__in=groupes_section_ids).count()
                        else:
                            display_nom = "بدون تحديد"
                            nbr_etu = Etudiant.objects.filter(niv_spe_dep_sg_id=g.id).count()

                        # Fallback sur nbr_etudiants_SG si pas d'étudiants trouvés
                        if nbr_etu == 0 and g.nbr_etudiants_SG:
                            nbr_etu = g.nbr_etudiants_SG

                        data.append({
                            'id': g.id,
                            'section_nom': g.section.nom_ar if g.section else None,
                            'groupe_nom': display_nom,
                            'specialite_nom': g.niv_spe_dep.specialite.nom_ar if g.niv_spe_dep.specialite else None,
                            'nbr_etudiants': nbr_etu
                        })

                    return JsonResponse({'data': data})
                return JsonResponse({'data': []})

            return JsonResponse({'data': []})

        return JsonResponse({'data': []})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# NIVEAUX ENSEIGNÉS PAR L'ENSEIGNANT
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def niveaux_enseigner(request, dep_id, enseignant, departement):
    """
    Vue pour afficher la liste des niveaux enseignés par un enseignant
    selon ses affectations (sections et groupes)
    """
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
    except:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    semestre_selected = request.GET.get('semestre', '1')

    try:
        semestre_obj = Semestre.objects.get(numero=semestre_selected)
    except:
        semestre_obj = Semestre.objects.filter(numero='1').first()
        semestre_selected = '1'

    def traduire_jour_en_arabe(jour_francais):
        traduction_jours = {
            'Samedi': 'السبت', 'Dimanche': 'الأحد', 'Lundi': 'الإثنين',
            'Mardi': 'الثلاثاء', 'Mercredi': 'الأربعاء', 'Jeudi': 'الخميس', 'Vendredi': 'الجمعة'
        }
        return traduction_jours.get(jour_francais, jour_francais)

    def compter_etudiants_section_ou_groupe(niv_spe_dep_sg, type_affectation, section_numero=None):
        try:
            if type_affectation == 'par_section' and section_numero is not None:
                groupes_de_la_section = NivSpeDep_SG.objects.filter(
                    niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                    section__numero=section_numero,
                    type_affectation='par_groupe'
                )
                return sum(Etudiant.objects.filter(niv_spe_dep_sg=g).count() for g in groupes_de_la_section)
            elif type_affectation == 'par_groupe':
                return Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).count()
            return 0
        except:
            return 0

    all_classes = Classe.objects.filter(
        enseignant__departement=departement.id,
        enseignant__enseignant=enseignant.id,
        semestre=semestre_obj
    ).select_related(
        'niv_spe_dep_sg', 'niv_spe_dep_sg__niv_spe_dep__niveau',
        'niv_spe_dep_sg__niv_spe_dep__specialite', 'niv_spe_dep_sg__niv_spe_dep__departement',
        'niv_spe_dep_sg__section', 'niv_spe_dep_sg__groupe', 'matiere'
    )

    niveaux_data = defaultdict(lambda: {
        'niveau': None, 'specialite': None, 'departement': None,
        'sections': defaultdict(lambda: {'matiere_count': 0, 'matieres': [], 'types_cours': set(), 'total_heures': 0, 'section_numero': None}),
        'groupes': defaultdict(lambda: {'matiere_count': 0, 'matieres': [], 'types_cours': set(), 'total_heures': 0, 'groupe_numero': None})
    })

    for classe in all_classes:
        niv_spe_dep_sg = classe.niv_spe_dep_sg
        key = f"{niv_spe_dep_sg.niv_spe_dep.niveau.nom_fr}_{niv_spe_dep_sg.niv_spe_dep.specialite.nom_fr}_{niv_spe_dep_sg.niv_spe_dep.departement.nom_fr}"

        niveaux_data[key]['niveau'] = niv_spe_dep_sg.niv_spe_dep.niveau
        niveaux_data[key]['specialite'] = niv_spe_dep_sg.niv_spe_dep.specialite
        niveaux_data[key]['departement'] = niv_spe_dep_sg.niv_spe_dep.departement

        nbr_seances_total, nbr_seances_faites = 0, 0
        if classe.seance_created:
            seances = Seance.objects.filter(classe=classe)
            nbr_seances_total = seances.count()
            nbr_seances_faites = seances.filter(fait=True).count()

        sous_groupes_count = 0
        if niv_spe_dep_sg.type_affectation == 'par_groupe':
            sous_groupes_count = SousGroupe.objects.filter(groupe_principal=niv_spe_dep_sg, actif=True).count()

        if niv_spe_dep_sg.type_affectation == 'par_groupe':
            groupe_nom = niv_spe_dep_sg.groupe.nom_ar
            container = niveaux_data[key]['groupes'][groupe_nom]
            container['groupe_numero'] = niv_spe_dep_sg.groupe.numero
            nb_etudiants = compter_etudiants_section_ou_groupe(niv_spe_dep_sg, 'par_groupe')
        else:
            section_nom = niv_spe_dep_sg.section.nom_ar if niv_spe_dep_sg.section else f"Section {niv_spe_dep_sg.numero_section}"
            container = niveaux_data[key]['sections'][section_nom]
            section_numero = niv_spe_dep_sg.section.numero if niv_spe_dep_sg.section else niv_spe_dep_sg.numero_section
            container['section_numero'] = section_numero
            nb_etudiants = compter_etudiants_section_ou_groupe(niv_spe_dep_sg, 'par_section', section_numero)

        matiere_info = {
            'matiere': classe.matiere, 'type_cours': classe.type, 'jour': traduire_jour_en_arabe(classe.jour),
            'temps': classe.temps, 'taux_avancement': classe.taux_avancement,
            'seances_total': nbr_seances_total, 'seances_faites': nbr_seances_faites,
            'lieu': classe.lieu, 'classe_id': classe.id,
            'sous_groupes_count': sous_groupes_count, 'niv_spe_dep_sg_id': niv_spe_dep_sg.id, 'nb_etudiants': nb_etudiants
        }

        container['matieres'].append(matiere_info)
        container['types_cours'].add(classe.type)
        container['matiere_count'] += 1
        container['total_heures'] += 1.5

    niveaux_final = []
    for key, data in niveaux_data.items():
        sections_sorted = dict(sorted(data['sections'].items(), key=lambda x: x[1]['section_numero'] if x[1]['section_numero'] else 999))
        groupes_sorted = dict(sorted(data['groupes'].items(), key=lambda x: x[1]['groupe_numero'] if x[1]['groupe_numero'] else 999))
        niveaux_final.append({
            'niveau': data['niveau'], 'specialite': data['specialite'], 'departement': data['departement'],
            'sections': sections_sorted, 'groupes': groupes_sorted,
            'total_sections': len(data['sections']), 'total_groupes': len(data['groupes']),
            'total_matieres': sum(s['matiere_count'] for s in data['sections'].values()) + sum(g['matiere_count'] for g in data['groupes'].values())
        })

    niveaux_final.sort(key=lambda x: (x['niveau'].nom_fr, x['specialite'].nom_fr))

    stats = {
        'total_niveaux': len(niveaux_final),
        'total_sections': sum(n['total_sections'] for n in niveaux_final),
        'total_groupes': sum(n['total_groupes'] for n in niveaux_final),
        'total_matieres': sum(n['total_matieres'] for n in niveaux_final),
        'total_classes': all_classes.count()
    }

    context = {
        'title': 'المستويات المدرسة', 'niveaux_enseigner': niveaux_final, 'stats': stats,
        'type_repartition': all_classes.values('type').annotate(count=Count('id')).order_by('type'),
        'semestre_selected': semestre_selected, 'semestre_obj': semestre_obj,
        'all_semestres': Semestre.objects.all().order_by('numero'),
        'my_Dep': departement, 'my_Fac': departement.faculte, 'my_Ens': enseignant, 'real_Dep': real_Dep,
    }
    return render(request, 'enseignant/niveaux_enseigner.html', context)


@enseignant_access_required
def page_nombre_sous_groupes(request, dep_id, classe_id, enseignant, departement):
    """Page pour choisir le nombre de sous-groupes"""
    classe = get_object_or_404(Classe, id=classe_id)
    if request.method == 'POST':
        nombre = int(request.POST.get('nombre', 2))
        SousGroupeManager.creer_sous_groupes_automatiques(
            groupe_principal=classe.niv_spe_dep_sg, nombre_sous_groupes=nombre, enseignant=enseignant
        )
        return redirect('ense:affecter_etudiants_sous_groupes', dep_id=dep_id, classe_id=classe_id)
    return render(request, 'enseignant/choisir_nombre_sous_groupes.html', {'classe': classe, 'my_Dep': departement, 'my_Ens': enseignant})


@enseignant_access_required
def affecter_etudiants_sous_groupes(request, dep_id, classe_id, enseignant, departement):
    """Page pour affecter les étudiants aux sous-groupes"""
    classe = get_object_or_404(Classe, id=classe_id)
    sous_groupes = SousGroupe.objects.filter(groupe_principal=classe.niv_spe_dep_sg, actif=True).order_by('ordre_affichage')
    etudiants = Etudiant.objects.filter(niv_spe_dep_sg=classe.niv_spe_dep_sg).order_by('nom_ar', 'prenom_ar')

    if request.method == 'POST':
        for etudiant in etudiants:
            sous_groupe_id = request.POST.get(f'etudiant_{etudiant.id}')
            if sous_groupe_id:
                EtudiantSousGroupe.objects.filter(etudiant=etudiant).delete()
                EtudiantSousGroupe.objects.create(etudiant=etudiant, sous_groupe_id=sous_groupe_id, affecte_par=enseignant)
        messages.success(request, "تم توزيع الطلاب على المجموعات الفرعية بنجاح!")
        return redirect('ense:niveaux_enseigner', dep_id=dep_id)

    return render(request, 'enseignant/affecter_etudiants_sous_groupes.html', {
        'classe': classe, 'sous_groupes': sous_groupes, 'etudiants': etudiants, 'my_Dep': departement, 'my_Ens': enseignant
    })


@enseignant_access_required
def liste_sous_groupes(request, dep_id, niv_spe_dep_sg_id, enseignant, departement):
    """Afficher la liste des sous-groupes et leurs étudiants"""
    niv_spe_dep_sg = get_object_or_404(NivSpeDep_SG, id=niv_spe_dep_sg_id)
    sous_groupes = SousGroupe.objects.filter(groupe_principal=niv_spe_dep_sg, actif=True).order_by('ordre_affichage')
    tous_etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg).order_by('nom_ar', 'prenom_ar')
    etudiants_affectes_ids = EtudiantSousGroupe.objects.filter(sous_groupe__in=sous_groupes, actif=True).values_list('etudiant_id', flat=True)
    etudiants_non_affectes = tous_etudiants.exclude(id__in=etudiants_affectes_ids)

    sous_groupes_avec_etudiants = []
    for sg in sous_groupes:
        etudiants = Etudiant.objects.filter(affectations_sous_groupes__sous_groupe=sg, affectations_sous_groupes__actif=True).order_by('nom_ar', 'prenom_ar')
        sous_groupes_avec_etudiants.append({'sous_groupe': sg, 'etudiants': etudiants})

    return render(request, 'enseignant/liste_sous_groupes.html', {
        'niv_spe_dep_sg': niv_spe_dep_sg, 'sous_groupes_avec_etudiants': sous_groupes_avec_etudiants,
        'etudiants_non_affectes': etudiants_non_affectes, 'my_Dep': departement, 'my_Ens': enseignant
    })


@enseignant_access_required
def affecter_direct_sous_groupes(request, dep_id, niv_spe_dep_sg_id, enseignant, departement):
    """Traiter l'affectation directe des étudiants aux sous-groupes"""
    if request.method == 'POST':
        niv_spe_dep_sg = get_object_or_404(NivSpeDep_SG, id=niv_spe_dep_sg_id)
        tous_etudiants = Etudiant.objects.filter(niv_spe_dep_sg=niv_spe_dep_sg)
        affectations_reussies, modifications_reussies = 0, 0

        for etudiant in tous_etudiants:
            sous_groupe_id = request.POST.get(f'etudiant_{etudiant.id}')
            if sous_groupe_id:
                try:
                    sous_groupe = get_object_or_404(SousGroupe, id=sous_groupe_id)
                    if sous_groupe.groupe_principal == niv_spe_dep_sg:
                        affectation = EtudiantSousGroupe.objects.filter(
                            etudiant=etudiant, sous_groupe__groupe_principal=niv_spe_dep_sg, actif=True
                        ).first()
                        if affectation:
                            if affectation.sous_groupe.id != int(sous_groupe_id):
                                affectation.delete()
                                EtudiantSousGroupe.objects.create(etudiant=etudiant, sous_groupe=sous_groupe, affecte_par=enseignant)
                                modifications_reussies += 1
                        else:
                            EtudiantSousGroupe.objects.create(etudiant=etudiant, sous_groupe=sous_groupe, affecte_par=enseignant)
                            affectations_reussies += 1
                except Exception:
                    pass  # Ignorer les erreurs individuelles

        if affectations_reussies and modifications_reussies:
            messages.success(request, f"تم تعيين {affectations_reussies} طالب جديد وتعديل {modifications_reussies} تعيين موجود بنجاح!")
        elif affectations_reussies:
            messages.success(request, f"تم تعيين {affectations_reussies} طالب جديد بنجاح!")
        elif modifications_reussies:
            messages.success(request, f"تم تعديل {modifications_reussies} تعيين بنجاح!")
        else:
            messages.warning(request, "لم يتم إجراء أي تغييرات.")

        return redirect('ense:liste_sous_groupes', dep_id=dep_id, niv_spe_dep_sg_id=niv_spe_dep_sg_id)
    return redirect('ense:liste_sous_groupes', dep_id=dep_id, niv_spe_dep_sg_id=niv_spe_dep_sg_id)


# ══════════════════════════════════════════════════════════════
# PROFIL ENSEIGNANT (avec dep_id)
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def profile_ens_dep(request, dep_id, enseignant, departement):
    """Afficher le profil de l'enseignant avec contexte département."""
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
    except Ens_Dep.DoesNotExist:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    # Autres départements où l'enseignant enseigne
    ALL_Dep = Ens_Dep.objects.filter(
        enseignant=enseignant
    ).exclude(departement=real_Dep.departement if real_Dep else None)

    context = {
        'title': 'الملف الشخصي',
        'active_menu': 'profile',
        'my_Ens': enseignant,
        'my_Dep': departement,
        'my_Fac': departement.faculte,
        'real_Dep': real_Dep,
        'ALL_Dep': ALL_Dep,
    }
    return render(request, 'enseignant/profile_Ens.html', context)


@enseignant_access_required
def profileUpdate_ens_dep(request, dep_id, enseignant, departement):
    """Mise à jour du profil de l'enseignant avec contexte département."""
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
    except Ens_Dep.DoesNotExist:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    if request.method == 'POST':
        User_form = UserUpdateForm(request.POST, instance=request.user)
        Ens_form = ProfileUpdateEnsForm(request.POST, instance=enseignant)

        if User_form.is_valid() and Ens_form.is_valid():
            User_form.save()
            Ens_form.save()
            messages.success(request, 'تم تحديث المعلومات بنجاح')
            return redirect('ense:profile_ens_dep', dep_id=departement.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        User_form = UserUpdateForm(instance=request.user)
        Ens_form = ProfileUpdateEnsForm(instance=enseignant)

    context = {
        'title': 'تعديل الملف الشخصي',
        'active_menu': 'profile',
        'User_form': User_form,
        'Ens_form': Ens_form,
        'my_Ens': enseignant,
        'my_Dep': departement,
        'my_Fac': departement.faculte,
        'real_Dep': real_Dep,
    }
    return render(request, 'enseignant/profileUpdate_Ens.html', context)


@enseignant_access_required
def change_password_ens_dep(request, dep_id, enseignant, departement):
    """Changement de mot de passe de l'enseignant avec contexte département."""
    try:
        real_Dep = Ens_Dep.objects.get(enseignant=enseignant, statut='Permanent')
    except Ens_Dep.DoesNotExist:
        real_Dep = Ens_Dep.objects.filter(enseignant=enseignant).first()

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Vérifier l'ancien mot de passe
        if not request.user.check_password(old_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة / Mot de passe actuel incorrect')
        elif new_password != confirm_password:
            messages.error(request, 'كلمة المرور الجديدة وتأكيدها غير متطابقين / Les mots de passe ne correspondent pas')
        elif len(new_password) < 8:
            messages.error(request, 'كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل / Le mot de passe doit contenir au moins 8 caractères')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès')
            return redirect('ense:profile_ens_dep', dep_id=departement.id)

    context = {
        'title': 'تغيير كلمة المرور',
        'active_menu': 'profile',
        'my_Ens': enseignant,
        'my_Dep': departement,
        'my_Fac': departement.faculte,
        'real_Dep': real_Dep,
    }
    return render(request, 'enseignant/change_password_Ens.html', context)


# ══════════════════════════════════════════════════════════════
# VUE LISTE DES NIVEAUX/SPECIALITES DU DEPARTEMENT
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_NivSpeDep_Ens(request, dep_id, enseignant, departement):
    """
    Liste des niveaux/spécialités pour l'enseignant.
    Affiche tous les NivSpeDep du département avec statistiques par semestre.
    """
    # Récupérer tous les NivSpeDep du département
    all_NivSpeDep = NivSpeDep.objects.filter(
        departement=departement
    ).select_related(
        'niveau', 'specialite', 'specialite__reforme',
        'specialite__identification', 'specialite__parcours'
    ).order_by('specialite__reforme', 'niveau', 'specialite__identification')

    # Calcul pour NivSpeDep (nbr_matieres et nbr_etudiants)
    for x in all_NivSpeDep:
        x.nbr_matieres_s1 = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=1).count()
        x.nbr_matieres_s2 = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=2).count()
        x.nbr_etudiants = Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep=x).count()
        x.save()

    # Calcul intelligent pour NivSpeDep_SG selon le type d'affectation
    all_niv_spe_dep_sg = NivSpeDep_SG.objects.filter(niv_spe_dep__departement=departement)

    for niv_spe_dep_sg in all_niv_spe_dep_sg:
        if niv_spe_dep_sg.type_affectation == 'par_groupe':
            niv_spe_dep_sg.nbr_etudiants_SG = Etudiant.objects.filter(
                niv_spe_dep_sg=niv_spe_dep_sg
            ).count()
        elif niv_spe_dep_sg.type_affectation == 'par_section':
            niv_spe_dep_sg.nbr_etudiants_SG = Etudiant.objects.filter(
                niv_spe_dep_sg__niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                niv_spe_dep_sg__section=niv_spe_dep_sg.section,
                niv_spe_dep_sg__type_affectation='par_groupe'
            ).count()
        elif niv_spe_dep_sg.type_affectation == 'tous_etudiants':
            niv_spe_dep_sg.nbr_etudiants_SG = Etudiant.objects.filter(
                niv_spe_dep_sg__niv_spe_dep=niv_spe_dep_sg.niv_spe_dep
            ).count()
        niv_spe_dep_sg.save()

    # Construction des listes pour l'affichage par semestre
    all_NivSpeDep_S1 = []
    all_NivSpeDep_S2 = []

    for x in all_NivSpeDep:
        # Pour S1 - vérifier s'il y a des matières
        s1_matieres = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=1)
        if s1_matieres.exists():
            fake_obj_s1 = type('obj', (object,), {
                'id': x.id,
                'niv_spe_dep': x,
                'semestre': type('semestre', (object,), {'numero': 1})()
            })()
            all_NivSpeDep_S1.append(fake_obj_s1)

        # Pour S2 - vérifier s'il y a des matières
        s2_matieres = Matiere.objects.filter(niv_spe_dep=x, semestre__numero=2)
        if s2_matieres.exists():
            fake_obj_s2 = type('obj', (object,), {
                'id': x.id,
                'niv_spe_dep': x,
                'semestre': type('semestre', (object,), {'numero': 2})()
            })()
            all_NivSpeDep_S2.append(fake_obj_s2)

    context = {
        'title': 'قائمة المستويات',
        'active_menu': 'niveaux',
        'my_Fac': departement.faculte,
        'my_Dep': departement,
        'my_Ens': enseignant,
        'all_NivSpeDep': all_NivSpeDep,
        'all_NivSpeDep_S1': all_NivSpeDep_S1,
        'all_NivSpeDep_S2': all_NivSpeDep_S2,
    }
    return render(request, 'enseignant/list_NivSpeDep_Ens.html', context)


@enseignant_access_required
def timeTable_Niv_Ens(request, dep_id, niv_spe_dep_id, semestre_num, enseignant, departement):
    """
    Emploi du temps d'un NivSpeDep (niveau/spécialité) pour un semestre donné.
    Affiche le planning hebdomadaire des classes.
    """
    # Récupérer le NivSpeDep
    try:
        niv_spe_dep = NivSpeDep.objects.select_related(
            'niveau', 'specialite', 'specialite__reforme',
            'specialite__identification', 'specialite__parcours'
        ).get(id=niv_spe_dep_id)
    except NivSpeDep.DoesNotExist:
        return render(request, 'enseignant/timeTable_Niv_Ens.html', {
            'error': f'المستوى/التخصص برقم {niv_spe_dep_id} غير موجود',
            'all_classes': 0,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'my_Ens': enseignant,
        })

    # Vérifier le semestre
    try:
        semestre = Semestre.objects.get(numero=semestre_num)
    except Semestre.DoesNotExist:
        return render(request, 'enseignant/timeTable_Niv_Ens.html', {
            'error': f'السداسي رقم {semestre_num} غير موجود',
            'all_classes': 0,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'my_Ens': enseignant,
        })

    # Récupérer toutes les classes avec préchargement des relations
    all_Classe_Niv = Classe.objects.filter(
        enseignant__departement=departement,
        niv_spe_dep_sg__niv_spe_dep=niv_spe_dep,
        semestre__numero=semestre_num
    ).select_related(
        'enseignant__enseignant',
        'matiere',
        'niv_spe_dep_sg__niv_spe_dep__niveau',
        'niv_spe_dep_sg__niv_spe_dep__specialite__reforme',
        'niv_spe_dep_sg__section',
        'niv_spe_dep_sg__groupe',
    ).order_by('jour', 'temps')

    # Même queryset pour all_Classe_Time
    all_Classe_Time = all_Classe_Niv

    # Statistiques optimisées
    nbr_Cours = all_Classe_Niv.filter(type="Cours").count()
    nbr_TP = all_Classe_Niv.filter(type="TP").count()
    nbr_TD = all_Classe_Niv.filter(type="TD").count()
    nbr_SS = all_Classe_Niv.filter(type="Sortie Scientifique").count()

    all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

    # Horaires corrigés (format correct)
    sixClassesTimes = [
        '08:00-09:30',
        '09:40-11:10',
        '11:20-12:50',
        '13:10-14:40',
        '14:50-16:20',
        '16:30-18:00',
    ]
    sevenDays = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']

    context = {
        'title': 'إستعمال الزمن للمستوى',
        'active_menu': 'niveaux',
        'all_Classe_Niv': all_Classe_Niv,
        'my_Dep': departement,
        'my_Fac': departement.faculte,
        'my_Ens': enseignant,
        'all_Classe_Time': all_Classe_Time,
        'nbr_Cours': nbr_Cours,
        'nbr_TP': nbr_TP,
        'nbr_TD': nbr_TD,
        'nbr_SS': nbr_SS,
        'all_classes': all_classes,
        'sevenDays': sevenDays,
        'sixClassesTimes': sixClassesTimes,
        'niv_spe_dep': niv_spe_dep,
        'niv_spe_dep_id': niv_spe_dep_id,
        'semestre_num': semestre_num,
    }

    return render(request, 'enseignant/timeTable_Niv_Ens.html', context)


# ══════════════════════════════════════════════════════════════
# GESTION DES NOTES DES ÉTUDIANTS PAR CLASSE
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Notes_Etu_Classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour afficher et gérer les notes des étudiants d'une classe.
    """
    try:
        # Récupérer la classe
        myClasse = get_object_or_404(
            Classe.objects.select_related(
                'matiere', 'semestre', 'enseignant__enseignant',
                'niv_spe_dep_sg__niv_spe_dep__specialite'
            ),
            id=clas_id,
            enseignant__enseignant=enseignant,
            enseignant__departement=departement
        )

        # Récupérer ou créer les entrées de notes pour tous les étudiants
        niv_spe_dep_sg = myClasse.niv_spe_dep_sg

        # Pour les Cours, récupérer les étudiants de tous les groupes de la section
        if myClasse.type == 'Cours' and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
            from apps.academique.departement.models import NivSpeDep_SG
            groupes_de_section = NivSpeDep_SG.objects.filter(
                niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                section=niv_spe_dep_sg.section,
                groupe__isnull=False
            )
            etudiants = Etudiant.objects.filter(
                niv_spe_dep_sg__in=groupes_de_section,
                est_actif=True
            ).distinct()
        else:
            etudiants = Etudiant.objects.filter(
                niv_spe_dep_sg=niv_spe_dep_sg,
                est_actif=True
            )

        # Créer les entrées Gestion_Etu_Classe pour les étudiants qui n'en ont pas
        for etudiant in etudiants:
            Gestion_Etu_Classe.objects.get_or_create(
                classe=myClasse,
                etudiant=etudiant
            )

        # Récupérer toutes les notes de la classe
        # Note: taux_presence_pourcentage et nombre_participations sont des @property
        # calculées automatiquement par le modèle, pas besoin de les assigner
        all_Notes_Classe = Gestion_Etu_Classe.objects.filter(
            classe=myClasse
        ).select_related('etudiant').order_by('etudiant__nom_fr', 'etudiant__prenom_fr')

        # Statistiques de la classe
        statistiques = Gestion_Etu_Classe.get_statistiques_classe(myClasse)

        if request.method == 'POST':
            # Sauvegarde des notes (note_presence est calculée automatiquement)
            from decimal import Decimal, InvalidOperation

            def safe_decimal(value, default=Decimal('0')):
                """
                Convertit une valeur en Decimal de manière sûre.
                Retourne default si vide ou invalide.
                """
                if value is None:
                    return default
                value_str = str(value).strip()
                if value_str == '':
                    return default
                try:
                    return Decimal(value_str)
                except (InvalidOperation, ValueError):
                    return default

            notes_saved = 0

            for note in all_Notes_Classe:
                if note.validee_par_enseignant:
                    continue  # Ne pas modifier les notes validées

                etudiant_id = note.etudiant.id

                # Récupérer les valeurs POST
                hw_raw = request.POST.get(f'note_participe_HW_{etudiant_id}')
                c1_raw = request.POST.get(f'note_controle_1_{etudiant_id}')
                c2_raw = request.POST.get(f'note_controle_2_{etudiant_id}')
                obs_raw = request.POST.get(f'obs_{etudiant_id}', '')

                # Convertir en Decimal (utiliser la valeur existante si vide)
                note.note_participe_HW = safe_decimal(hw_raw, note.note_participe_HW or Decimal('0'))
                note.note_controle_1 = safe_decimal(c1_raw, note.note_controle_1 or Decimal('0'))
                note.note_controle_2 = safe_decimal(c2_raw, note.note_controle_2 or Decimal('0'))
                note.obs = obs_raw if obs_raw is not None else (note.obs or '')

                note.save()
                notes_saved += 1

            messages.success(request, f'تم حفظ النقاط بنجاح ({notes_saved} طالب)')
            return redirect('ense:list_Notes_Etu_Classe', dep_id=dep_id, clas_id=clas_id)

        # Vérifier si les notes sont validées
        notes_validees = all_Notes_Classe.filter(validee_par_enseignant=True).exists()

        # Préparer les valeurs avec des fallbacks pour éviter les erreurs
        matiere_nom = myClasse.matiere.nom_ar if myClasse.matiere else 'غير محدد'
        matiere_nom_fr = myClasse.matiere.nom_fr if myClasse.matiere else ''
        niv_spe_dep_sg_str = str(myClasse.niv_spe_dep_sg) if myClasse.niv_spe_dep_sg else 'غير محدد'

        # Nom complet de la matière avec type
        matiere_complet = f"{matiere_nom}"
        if matiere_nom_fr:
            matiere_complet += f" / {matiere_nom_fr}"

        # Calculer la note de présence automatiquement pour chaque étudiant
        # Formule: commence à 5, -1 pour chaque absence (minimum 0)
        # Utiliser une mise à jour directe en base de données avec Case/When
        from django.db.models import Case, When, Value
        from decimal import Decimal

        # Mise à jour directe en base de données pour les notes non validées
        # Calcul: max(0, 5 - nbr_absence)
        Gestion_Etu_Classe.objects.filter(
            classe=myClasse,
            validee_par_enseignant=False
        ).update(
            note_presence=Case(
                When(nbr_absence__gte=5, then=Value(Decimal('0.00'))),
                When(nbr_absence=4, then=Value(Decimal('1.00'))),
                When(nbr_absence=3, then=Value(Decimal('2.00'))),
                When(nbr_absence=2, then=Value(Decimal('3.00'))),
                When(nbr_absence=1, then=Value(Decimal('4.00'))),
                default=Value(Decimal('5.00')),  # 0 absences = 5 points
            )
        )

        # Récupérer les notes avec valeurs fraîches depuis la base de données
        all_Notes_Classe = list(Gestion_Etu_Classe.objects.filter(
            classe=myClasse
        ).select_related('etudiant').order_by('etudiant__nom_fr', 'etudiant__prenom_fr'))

        context = {
            'title': f'نقاط الطلاب - {matiere_nom}',
            'active_menu': 'timetable',
            'my_Ens': enseignant,
            'my_Dep': departement,
            'my_Fac': departement.faculte if departement else None,
            'my_Clas': myClasse,
            'all_Notes_Classe': all_Notes_Classe,
            'statistiques': statistiques,
            'titre_00': niv_spe_dep_sg_str,
            'titre_01': matiere_complet,
            'type_classe': myClasse.type,
            'notes_validees': notes_validees,
        }

        return render(request, 'enseignant/list_Notes_Etu_Classe.html', context)

    except Exception as e:
        messages.error(request, f'خطأ في صفحة النقاط: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


@enseignant_access_required
def valider_notes_classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour valider toutes les notes d'une classe.
    Nécessite la vérification du mot de passe de l'utilisateur.
    """
    if request.method == 'POST':
        try:
            # Vérifier le mot de passe de l'utilisateur
            password = request.POST.get('password', '')
            user = request.user

            if not user.check_password(password):
                messages.error(request, 'كلمة المرور غير صحيحة')
                return redirect('ense:list_Notes_Etu_Classe', dep_id=dep_id, clas_id=clas_id)

            myClasse = get_object_or_404(
                Classe,
                id=clas_id,
                enseignant__enseignant=enseignant,
                enseignant__departement=departement
            )

            # Valider toutes les notes de la classe
            Gestion_Etu_Classe.objects.filter(
                classe=myClasse,
                validee_par_enseignant=False
            ).update(
                validee_par_enseignant=True,
                date_validation=timezone.now()
            )

            # Marquer la classe comme ayant ses notes validées
            myClasse.notes_liste_Etu = True
            myClasse.save()

            messages.success(request, 'تم تصديق جميع النقاط بنجاح')
        except Exception as e:
            messages.error(request, f'خطأ: {str(e)}')

    return redirect('ense:list_Notes_Etu_Classe', dep_id=dep_id, clas_id=clas_id)


@enseignant_access_required
def creer_notes_classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour créer les entrées de notes pour tous les étudiants d'une classe.
    """
    try:
        myClasse = get_object_or_404(
            Classe,
            id=clas_id,
            enseignant__enseignant=enseignant,
            enseignant__departement=departement
        )

        niv_spe_dep_sg = myClasse.niv_spe_dep_sg

        # Pour les Cours, récupérer les étudiants de tous les groupes de la section
        if myClasse.type == 'Cours' and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
            from apps.academique.departement.models import NivSpeDep_SG
            groupes_de_section = NivSpeDep_SG.objects.filter(
                niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                section=niv_spe_dep_sg.section,
                groupe__isnull=False
            )
            etudiants = Etudiant.objects.filter(
                niv_spe_dep_sg__in=groupes_de_section,
                est_actif=True
            ).distinct()
        else:
            etudiants = Etudiant.objects.filter(
                niv_spe_dep_sg=niv_spe_dep_sg,
                est_actif=True
            )

        # Créer les entrées pour chaque étudiant
        created_count = 0
        for etudiant in etudiants:
            _, created = Gestion_Etu_Classe.objects.get_or_create(
                classe=myClasse,
                etudiant=etudiant
            )
            if created:
                created_count += 1

        if created_count > 0:
            messages.success(request, f'تم إنشاء قائمة النقاط ({created_count} طالب)')
        else:
            messages.info(request, 'قائمة النقاط موجودة بالفعل')

        return redirect('ense:list_Notes_Etu_Classe', dep_id=dep_id, clas_id=clas_id)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)


# ══════════════════════════════════════════════════════════════
# VUE LISTE DES ABSENCES PAR CLASSE
# ══════════════════════════════════════════════════════════════

@enseignant_access_required
def list_Abs_Etu_Classe(request, dep_id, clas_id, enseignant, departement):
    """
    Vue pour afficher la liste des absences de tous les étudiants pour une classe donnée.
    Affiche un résumé par étudiant de toutes les séances.
    """
    try:
        # Récupérer la classe
        myClasse = get_object_or_404(
            Classe.objects.select_related(
                'matiere', 'semestre', 'enseignant__enseignant',
                'niv_spe_dep_sg__niv_spe_dep__specialite'
            ),
            id=clas_id,
            enseignant__enseignant=enseignant,
            enseignant__departement=departement
        )

        # Récupérer les séances faites de cette classe (pour afficher les colonnes)
        all_seances = Seance.objects.filter(
            classe=myClasse,
            fait=True
        ).order_by('date', 'temps')

        # Récupérer les notes/gestion des étudiants avec les absences agrégées
        niv_spe_dep_sg = myClasse.niv_spe_dep_sg

        # Pour les Cours, récupérer les étudiants de tous les groupes de la section
        if myClasse.type == 'Cours' and niv_spe_dep_sg.section and not niv_spe_dep_sg.groupe:
            from apps.academique.departement.models import NivSpeDep_SG
            groupes_de_section = NivSpeDep_SG.objects.filter(
                niv_spe_dep=niv_spe_dep_sg.niv_spe_dep,
                section=niv_spe_dep_sg.section,
                groupe__isnull=False
            )
            etudiants_ids = Etudiant.objects.filter(
                niv_spe_dep_sg__in=groupes_de_section,
                est_actif=True
            ).values_list('id', flat=True)
        else:
            etudiants_ids = Etudiant.objects.filter(
                niv_spe_dep_sg=niv_spe_dep_sg,
                est_actif=True
            ).values_list('id', flat=True)

        # Récupérer toutes les absences pour cette classe
        all_absences = Abs_Etu_Seance.objects.filter(
            seance__classe=myClasse,
            etudiant_id__in=etudiants_ids
        ).select_related('etudiant', 'seance').order_by('etudiant__nom_ar', 'seance__date')

        # Regrouper les absences par étudiant
        absences_par_etudiant = defaultdict(list)
        for abs_record in all_absences:
            absences_par_etudiant[abs_record.etudiant].append(abs_record)

        # Calculer les statistiques par étudiant
        etudiants_stats = []
        for etudiant, absences in absences_par_etudiant.items():
            total_seances = len(absences)
            presents = sum(1 for a in absences if a.present)
            absents = sum(1 for a in absences if not a.present and not a.justifiee)
            justifies = sum(1 for a in absences if not a.present and a.justifiee)
            participations = sum(1 for a in absences if a.participation)

            taux_presence = (presents / total_seances * 100) if total_seances > 0 else 0

            # Créer un dictionnaire des absences indexé par seance_id
            absences_by_seance = {abs_rec.seance_id: abs_rec for abs_rec in absences}

            etudiants_stats.append({
                'etudiant': etudiant,
                'absences': absences,
                'absences_by_seance': absences_by_seance,
                'total_seances': total_seances,
                'presents': presents,
                'absents': absents,
                'justifies': justifies,
                'participations': participations,
                'taux_presence': round(taux_presence, 1)
            })

        # Trier par nom_fr, prenom_fr (français d'abord)
        etudiants_stats.sort(key=lambda x: (x['etudiant'].nom_fr or '', x['etudiant'].prenom_fr or ''))

        # Convertir all_seances en liste pour pouvoir l'utiliser dans la boucle
        seances_list = list(all_seances)

        # Ajouter les statuts de séance pour chaque étudiant (dans l'ordre des séances)
        for stat in etudiants_stats:
            seance_statuses = []
            for seance in seances_list:
                abs_record = stat['absences_by_seance'].get(seance.id)
                if abs_record:
                    if abs_record.present:
                        seance_statuses.append('P')  # Présent
                    elif abs_record.justifiee:
                        seance_statuses.append('J')  # Justifié
                    else:
                        seance_statuses.append('A')  # Absent
                else:
                    seance_statuses.append('-')  # Pas de données
            stat['seance_statuses'] = seance_statuses

        # Statistiques globales
        total_etudiants = len(etudiants_stats)
        total_seances = len(seances_list)
        avg_presence = sum(e['taux_presence'] for e in etudiants_stats) / total_etudiants if total_etudiants > 0 else 0

        context = {
            'myClasse': myClasse,
            'all_seances': seances_list,
            'etudiants_stats': etudiants_stats,
            'total_etudiants': total_etudiants,
            'total_seances': total_seances,
            'avg_presence': round(avg_presence, 1),
            'my_Ens': enseignant,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
        }

        return render(request, 'enseignant/list_Abs_Etu_Classe.html', context)

    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
        return redirect('ense:timeTable_Ens', dep_id=dep_id)