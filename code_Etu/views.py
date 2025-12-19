from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from apps.academique.affectation.models import Abs_Etu_Classe, Abs_Etu_Seance, Classe, Seance
from apps.academique.departement.models import NivSpeDep_SG
import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from apps.academique.etudiant.forms import profileUpdate_Etu_Form
from apps.noyau.authentification.forms import UserUpdateForm
from apps.noyau.commun.models import Semestre
from .models import *
from django.urls import reverse
from apps.noyau.authentification.decorators import etudiant_access_required
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q


# # @login_required
# @etudiant_access_required
# def dashboard_Etu(request, etudiant, departement):       

#     context = {
#         'title': 'لوحة التحكم',
#         'my_Etu': etudiant,
#         'my_Dep': departement,  # Passer le département au template
#         'my_Fac': departement.faculte,  # Passer le département au template
#     }
#     return render(request, 'etudiant/dashboard_Etu.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta


@etudiant_access_required
def dashboard_Etu(request, etudiant, departement):
    """
    Dashboard principal pour l'étudiant
    Vue complète avec statistiques personnelles, emploi du temps, performance
    """
    try:
        # Récupération de l'étudiant connecté
        my_Etu = Etudiant.objects.get(user=request.user)
        my_Dep = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement
        my_Fac = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement.faculte
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
        
        # Récupération de tous les semestres disponibles pour cet étudiant
        all_semestres = Semestre.objects.filter(
            classe__niv_spe_dep_sg=my_Etu.niv_spe_dep_sg
        ).distinct().order_by('numero')
        
        if not all_semestres.exists():
            all_semestres = Semestre.objects.all().order_by('numero')
        
        # ========== CLASSES DE L'ÉTUDIANT (CORRIGÉ) ==========
        
        # Filtre pour les classes du groupe de l'étudiant
        group_filter = {
            'niv_spe_dep_sg': my_Etu.niv_spe_dep_sg,
            'semestre': semestre_obj
        }
        
        # On recherche un NivSpeDep_SG qui a le même NivSpeDep et un groupe nul (ce qui indique une section)
        section_niv_spe_dep_sg_queryset = NivSpeDep_SG.objects.filter(
            niv_spe_dep=my_Etu.niv_spe_dep_sg.niv_spe_dep,
            groupe__isnull=True
        )

        section_niv_spe_dep_sg = section_niv_spe_dep_sg_queryset.first()

        section_filter = {}
        if section_niv_spe_dep_sg:
            section_filter = {
                'niv_spe_dep_sg': section_niv_spe_dep_sg,
                'semestre': semestre_obj
            }
        
        # Exécuter les requêtes et les combiner
        group_classes = Classe.objects.filter(**group_filter).select_related(
            'matiere', 'enseignant__enseignant', 'semestre'
        )
        section_classes = Classe.objects.filter(**section_filter).select_related(
            'matiere', 'enseignant__enseignant', 'semestre'
        ) if section_filter else Classe.objects.none()

        mes_matieres = (group_classes | section_classes).distinct()
        
        # ========== STATISTIQUES PRINCIPALES ==========
        
        # Statistiques de base
        total_classes = mes_matieres.count()
        volume_horaire = round(total_classes * 1.5, 1)  # 1.5h par classe
        
        # Calcul du taux de présence de l'étudiant
        total_absences = 0
        absences_justifiees = 0
        total_seances = 0
        
        try:
            for matiere in mes_matieres:
                if matiere.abs_liste_Etu:
                    try:
                        abs_etu_classe = Abs_Etu_Classe.objects.get(
                            classe=matiere,
                            etudiant=my_Etu
                        )
                        total_absences += abs_etu_classe.nbr_absence or 0
                        absences_justifiees += abs_etu_classe.nbr_absence_justifiee or 0
                    except Abs_Etu_Classe.DoesNotExist:
                        pass
                
                # Compter les séances effectuées
                seances_count = Seance.objects.filter(classe=matiere, fait=True).count()
                total_seances += seances_count
        except Exception as e:
            pass
        
        # Calcul du taux de présence
        if total_seances > 0:
            taux_presence = round(((total_seances - total_absences) / total_seances) * 100, 1)
        else:
            taux_presence = 100.0
        
        # Calcul du progrès dans les matières
        matieres_avec_seances = mes_matieres.filter(seance_created=True).count()
        if total_classes > 0:
            progres_matieres = round((matieres_avec_seances / total_classes) * 100, 1)
        else:
            progres_matieres = 0
        
        # Moyenne générale (simulée - à adapter selon votre modèle de notes)
        try:
            moyenne_generale = 15.5
        except:
            moyenne_generale = None
        
        # Statistiques de l'étudiant
        stats_etudiant = {
            'total_classes': total_classes,
            'volume_horaire': volume_horaire,
            'taux_presence': max(0, min(100, taux_presence)),
            'total_absences': total_absences,
            'absences_justifiees': absences_justifiees,
            'moyenne_generale': moyenne_generale,
            'progres_matieres': progres_matieres,
            'participation': 85,
        }
        
        # ========== EMPLOI DU TEMPS AUJOURD'HUI (CORRIGÉ) ==========
        # Filtrer les classes aujourd'hui à partir du queryset combiné
        
        try:
            classes_today = mes_matieres.filter(jour=today_french).order_by('temps')
            
            # Enrichir les données avec les taux d'avancement
            for classe in classes_today:
                if classe.seance_created:
                    try:
                        all_seances = Seance.objects.filter(classe=classe).count()
                        seances_faites = Seance.objects.filter(classe=classe, fait=True).count()
                        if all_seances > 0:
                            classe.taux_avancement = round((seances_faites / all_seances) * 100)
                        else:
                            classe.taux_avancement = 0
                    except:
                        classe.taux_avancement = 0
        except Exception as e:
            classes_today = []
        
        # Enrichir mes_matieres avec taux de présence individuel
        for matiere in mes_matieres:
            try:
                if matiere.abs_liste_Etu:
                    abs_etu = Abs_Etu_Classe.objects.get(classe=matiere, etudiant=my_Etu)
                    seances_matiere = Seance.objects.filter(classe=matiere, fait=True).count()
                    if seances_matiere > 0:
                        absences_matiere = abs_etu.nbr_absence or 0
                        matiere.taux_presence = round(((seances_matiere - absences_matiere) / seances_matiere) * 100, 1)
                    else:
                        matiere.taux_presence = 100
                else:
                    matiere.taux_presence = None
            except Abs_Etu_Classe.DoesNotExist:
                matiere.taux_presence = 100
            except Exception as e:
                matiere.taux_presence = None
    
        # ========== ACTIVITÉS RÉCENTES ==========
        
        activites_recentes = []
        try:
            for matiere in mes_matieres[:3]:
                activites_recentes.append({
                    'type': 'cours',
                    'titre': f'حصة {matiere.matiere.nom_fr}',
                    'description': f'{matiere.type} - {matiere.enseignant.enseignant.nom_ar}',
                    'date': today - timedelta(days=len(activites_recentes)),
                })
        
            if total_absences > 0:
                activites_recentes.append({
                    'type': 'absence',
                    'titre': 'تسجيل غياب',
                    'description': f'غياب في إحدى المواد',
                    'date': today - timedelta(days=1),
                })
            
            if moyenne_generale:
                activites_recentes.append({
                    'type': 'note',
                    'titre': 'نتيجة جديدة',
                    'description': f'معدل: {moyenne_generale}',
                    'date': today - timedelta(days=2),
                })
                
        except Exception as e:
            pass
        
        # ========== NOTIFICATIONS ==========
        
        notifications = []
        
        if taux_presence < 75:
            notifications.append({
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'titre': 'تحذير:',
                'message': f'نسبة حضورك منخفضة: {taux_presence}%. يجب تحسين الحضور'
            })
        
        if classes_today:
            notifications.append({
                'type': 'info',
                'icon': 'calendar-day',
                'titre': 'تذكير:',
                'message': f'لديك {len(classes_today)} حصة مجدولة اليوم'
            })
        
        absences_non_justifiees = total_absences - absences_justifiees
        if absences_non_justifiees > 3:
            notifications.append({
                'type': 'danger',
                'icon': 'user-times',
                'titre': 'انتباه:',
                'message': f'لديك {absences_non_justifiees} غياب غير مبرر'
            })
        
        if moyenne_generale and moyenne_generale < 10:
            notifications.append({
                'type': 'warning',
                'icon': 'chart-line',
                'titre': 'أكاديمي:',
                'message': f'معدلك الحالي {moyenne_generale} يحتاج تحسين'
            })
        
        # if not notifications:
        #     notifications.append({
        #         'type': 'success',
        #         'icon': 'check-circle',
        #         'titre': 'ممتاز!',
        #         'message': 'أداؤك الأكاديمي جيد، استمر في التفوق'
        #     })
        
        # ========== CONTEXTE FINAL ==========
        
        context = {
            'title': 'لوحة التحكم - الطالب',
            'my_Etu': my_Etu,
            'my_Dep': my_Dep,
            'my_Fac': my_Fac,
            'today': today,
            'all_semestres': all_semestres,
            'semestre_selected': semestre_selected,
            'semestre_obj': semestre_obj,
            'mes_matieres': mes_matieres,
            'classes_today': classes_today,
            'stats_etudiant': stats_etudiant,
            'activites_recentes': activites_recentes[:5],
            'notifications': notifications,
        }
        
        return render(request, 'etudiant/dashboard_Etu.html', context)
        
    except Exception as e:
        messages.error(request, f'حدث خطأ في تحميل لوحة التحكم: {str(e)}')
        
        # Context minimal de fallback
        context = {
            'title': 'لوحة التحكم - الطالب',
            'my_Etu': my_Etu if 'my_Etu' in locals() else etudiant,
            'my_Dep': departement,
            'my_Fac': departement.faculte,
            'today': timezone.now().date(),
            'all_semestres': Semestre.objects.all().order_by('numero'),
            'semestre_selected': '1',
            'mes_matieres': [],
            'classes_today': [],
            'stats_etudiant': {
                'total_classes': 0,
                'volume_horaire': 0,
                'taux_presence': 0,
                'total_absences': 0,
                'absences_justifiees': 0,
                'moyenne_generale': None,
                'progres_matieres': 0,
                'participation': 0,
            },
            'activites_recentes': [],
            'notifications': [{
                'type': 'danger',
                'icon': 'exclamation-circle',
                'titre': 'خطأ:',
                'message': 'حدث خطأ في تحميل البيانات'
            }],
        }
        return render(request, 'etudiant/dashboard_Etu.html', context)
    

    







@login_required
def list_Seance_Etu(request, clas_id):
    """
    Vue pour afficher la liste des séances d'une classe pour un étudiant
    """
    etudiant = request.user.etudiant_profile
    my_Etu = Etudiant.objects.get(user=request.user)
    my_Dep = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement
    my_Fac = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement.faculte
    
    # Vérifier que l'étudiant a accès à cette classe
    try:
        classe = Classe.objects.get(id=clas_id)
        
        # Vérifier que l'étudiant fait partie de cette classe
        # ATTENTION : Adaptez cette vérification selon votre logique métier
        # Par exemple, vérifier si l'étudiant est dans le même niv_spe_dep_sg
        
    except Classe.DoesNotExist:
        messages.error(request, "الحصة غير موجودة")
        return redirect('etudiant:timeTable_Etu')

    # Statistiques
    all_Seances = Seance.objects.filter(classe=clas_id).order_by('date')
    nbr_Sea_fait = Seance.objects.filter(classe=clas_id, fait=True)
    nbr_Sea_remplacer = Seance.objects.filter(classe=clas_id, remplacer=True)
    nbr_Sea_annuler = Seance.objects.filter(classe=clas_id, annuler=True)
    nbr_Sea_reste = all_Seances.count() - nbr_Sea_fait.count()

    # Calculer le taux d'avancement
    taux_avancement = 0
    if nbr_Sea_fait.count() != 0 and all_Seances.count() != 0:
        taux_avancement = (nbr_Sea_fait.count() / all_Seances.count()) * 100
        taux_avancement = round(taux_avancement)
    
    sea_name = classe

    context = {
        'title': 'جميع الدروس',
        'my_Dep': my_Dep,
        'my_Fac': my_Fac,
        'sea_name': sea_name,
        'all_Seances': all_Seances,
        'nbr_Sea_fait': nbr_Sea_fait,
        'nbr_Sea_annuler': nbr_Sea_annuler,
        'nbr_Sea_reste': nbr_Sea_reste,
        'taux_avancement': taux_avancement,
        'my_Etu': etudiant,
    }
    return render(request, 'etudiant/list_Seance_Etu.html', context)














@etudiant_access_required
def dashboard_etu_ajax_stats(request, etudiant, departement):  
# @etudiant_access_required  
# def dashboard_etu_ajax_stats(request, etudiant, departement):
    """
    Vue AJAX pour mettre à jour les statistiques de l'étudiant en temps réel
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            my_Etu = Etudiant.objects.get(user=request.user)
            semestre_selected = request.GET.get('semestre', '1')
            semestre_obj = Semestre.objects.get(numero=semestre_selected)
            
            # Recalculer les statistiques rapidement
            mes_matieres = Classe.objects.filter(
                niv_spe_dep_sg=my_Etu.niv_spe_dep_sg,
                semestre=semestre_obj
            )
            
            # Calcul rapide du taux de présence
            total_absences = 0
            total_seances = 0
            
            for matiere in mes_matieres:
                if matiere.abs_liste_Etu:
                    try:
                        abs_etu = Abs_Etu_Classe.objects.get(classe=matiere, etudiant=my_Etu)
                        total_absences += abs_etu.nbr_absence or 0
                    except Abs_Etu_Classe.DoesNotExist:
                        pass
                
                total_seances += Seance.objects.filter(classe=matiere, fait=True).count()
            
            if total_seances > 0:
                taux_presence = round(((total_seances - total_absences) / total_seances) * 100, 1)
            else:
                taux_presence = 100
            
            stats = {
                'total_classes': mes_matieres.count(),
                'taux_presence': taux_presence,
                'total_absences': total_absences,
                'timestamp': timezone.now().isoformat(),
            }
            
            return JsonResponse({'success': True, 'stats': stats})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Requête non autorisée'})




























@etudiant_access_required
def profile_Etu(request, etudiant, departement): 

    context = {
        'title': 'لوحة التحكم',
        'my_Etu': etudiant,
        'my_Dep': departement,  # Passer le département au template
        'my_Fac': departement.faculte,  # Passer le département au template
    }
    return render(request, 'etudiant/profile_Etu.html', context)





# ----------------------------------------------------------------------
@etudiant_access_required
def profileUpdate_Etu(request, etudiant, departement):  

    Etu_form = profileUpdate_Etu_Form(instance=etudiant)
    if request.method == 'POST':
        # profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        User_form = UserUpdateForm(request.POST, instance=request.user)
        Etu_form = profileUpdate_Etu_Form(request.POST, instance=etudiant)
        # if user_form.is_valid and profile_form.is_valid and dep_form.is_valid:
        if User_form.is_valid and Etu_form.is_valid:
            User_form.save()
            Etu_form.save()
            messages.success(request, 'تم تحديث المعلومات بنجاح')
            context = {
            'title': 'تعديل المعلومات',
            'User_form': User_form,
            'Etu_form' : Etu_form,
            'my_Etu': etudiant,
            'my_Dep': departement,  # Passer le département au template
            'my_Fac': departement.faculte,  # Passer le département au template
            }
            return render(request, 'etudiant/profile_Etu.html', context)
    else:
        User_form = UserUpdateForm(instance=request.user)
        Etu_form = profileUpdate_Etu_Form(instance=etudiant)

    context = {
        'title': 'تعديل المعلومات',
        'User_form': User_form,
        'Etu_form' : Etu_form,
        'my_Etu': etudiant,
        'my_Dep': departement,  # Passer le département au template
        'my_Fac': departement.faculte,  # Passer le département au template
    }
    return render(request, 'etudiant/profileUpdate_Etu.html', context)





@etudiant_access_required
def change_password_Etu(request, etudiant, departement):

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        user = request.user
        # Vérifier si l'ancien mot de passe est correct
        if not user.check_password(old_password):
            messages.warning(request, "كلمة المرور القديمة خاطئة.")
            # return redirect(reverse('change_password_Ens', kwargs={'dep_id': dep_id}))
            # return redirect('change_password_Etu.html')
            return render(request, 'etudiant/change_password_Etu.html')
        # Vérifier si les deux nouveaux mots de passe correspondent
        if new_password != confirm_password:
            messages.warning(request, "كلمة المرور غير متطابقة.")
            # return redirect(reverse('change_password_Ens', kwargs={'dep_id': dep_id}))
            # return redirect('change_password_Etu.html')
            return render(request, 'etudiant/change_password_Etu.html')
        # Mettre à jour le mot de passe
        user.set_password(new_password)
        user.save()
        # Maintenir l'utilisateur connecté après le changement de mot de passe
        update_session_auth_hash(request, user)
        messages.success(request, "تم تغيير كلمة المرور بنجاح.")
        # return redirect('timeTable_Ens')  # Rediriger vers le profil ou autre page après le succès
        # return render(request, 'app_enseignant/dashboard_Ens.html', context)
        # return redirect(reverse('dashboard_Etu', kwargs={'dep_id': dep_id}))
        # return redirect('dashboard_Etu.html')
        return render(request, 'etudiant/dashboard_Etu.html')

    context = {
        'title': 'تغيير كلمة المرور',
        'my_Etu': etudiant,
        'my_Dep': departement,  # Passer le département au template
        'my_Fac': departement.faculte,  # Passer le département au template
    }
    return render(request, 'etudiant/change_password_Etu.html',context)













# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@etudiant_access_required
def timeTable_Etu(request, etudiant, departement):
    """
    Vue avec débogage complet pour identifier le problème CSS
    """
    try:
        # Récupération de l'étudiant connecté
        my_Etu = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.warning(request, 'لا تملك إذن الدخول - ملف الطالب غير موجود')
        return redirect('login')
    
    # Récupération des données liées
    my_Dep = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement
    my_Fac = my_Dep.faculte

    # Récupérer le paramètre semestre (par défaut S1)
    semestre_selected = request.GET.get('semestre', '1')
    
    # Récupérer l'objet semestre
    try:
        semestre_obj = Semestre.objects.get(numero=semestre_selected)
    except Semestre.DoesNotExist:
        semestre_obj = Semestre.objects.filter(numero='1').first()
        semestre_selected = '1'
    
    # Variables communes
    all_Classe_Etu = []
    nbr_Cours = 0
    nbr_TP = 0
    nbr_TD = 0
    nbr_SS = 0

    # DÉBOGAGE: Vérifier le filtre de base
    # print(f"=== DÉBOGAGE TIMETABLE_ETU ===")
    # print(f"Étudiant: {my_Etu.nom_ar} {my_Etu.prenom_ar}")
    # print(f"Niveau: {my_Etu.niv_spe_dep_sg}")
    # print(f"Semestre sélectionné: {semestre_selected}")
    # print(f"Semestre objet: {semestre_obj}")
  
    # --- LOGIQUE DE FILTRAGE CORRIGÉE ---
    # Pour inclure les cours de la section et du groupe, nous devons effectuer deux requêtes.
    
    # Filtre pour les classes du groupe de l'étudiant
    group_filter = {
        'niv_spe_dep_sg': my_Etu.niv_spe_dep_sg,
        'semestre': semestre_obj
    }
    
    # Filtre pour les classes de la section de l'étudiant
    # On recherche un NivSpeDep_SG qui a le même NivSpeDep et un groupe nul (ce qui indique une section)
    section_niv_spe_dep_sg_queryset = NivSpeDep_SG.objects.filter(
        niv_spe_dep=my_Etu.niv_spe_dep_sg.niv_spe_dep,
        groupe__isnull=True
    )
    
    # On utilise .first() pour récupérer un seul objet ou None, évitant ainsi l'erreur "get() returned more than one"
    section_niv_spe_dep_sg = section_niv_spe_dep_sg_queryset.first()

    section_filter = {}
    if section_niv_spe_dep_sg:
        section_filter = {
            'niv_spe_dep_sg': section_niv_spe_dep_sg,
            'semestre': semestre_obj
        }

    # Récupérer les classes du groupe et de la section séparément
    group_classes = Classe.objects.filter(**group_filter).select_related(
        'matiere', 'enseignant__enseignant', 'semestre', 'niv_spe_dep_sg'
    )
    
    section_classes = Classe.objects.filter(**section_filter).select_related(
        'matiere', 'enseignant__enseignant', 'semestre', 'niv_spe_dep_sg'
    ) if section_filter else Classe.objects.none()

    # Combinaison des deux requêtes en un seul queryset, en retirant les doublons
    all_classes_queryset = (group_classes | section_classes).distinct().order_by('jour', 'temps')
    
    # print(f"Total classes trouvées (groupe et section): {all_classes_queryset.count()}")
    # --- FIN DE LA LOGIQUE DE FILTRAGE CORRIGÉE ---
    
    # Si aucune classe trouvée, essayer sans filtre semestre
    if not all_classes_queryset.exists():
        # print("Aucune classe trouvée avec le semestre, essai sans filtre semestre...")
        base_filter_no_sem = {'niv_spe_dep_sg': my_Etu.niv_spe_dep_sg}
        all_classes_queryset = Classe.objects.filter(**base_filter_no_sem).select_related(
            'matiere', 'enseignant__enseignant', 'semestre', 'niv_spe_dep_sg'
        )
        # print(f"Classes sans filtre semestre: {all_classes_queryset.count()}")

    # Définition des jours et horaires
    jours = ['Samedi', 'Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']
    sevenDays = jours
    
    horaires = [
        '09:30-08:00',
        '11:10-09:40', 
        '12:50-11:20',
        '14:40-13:10',
        '16:20-14:50',
        '18:00-16:30'
    ]
    sixClasses = horaires
    
    # Récupérer les classes par jour
    for jour in jours:
        classes_jour = all_classes_queryset.filter(jour=jour).order_by('temps')
        all_Classe_Etu.extend(classes_jour)
        # print(f"Jour {jour}: {classes_jour.count()} classes")
    
    # Récupérer les classes par horaire pour le mini emploi du temps
    all_Classe_Time = []
    for horaire in horaires:
        classes_horaire = all_classes_queryset.filter(temps=horaire)
        all_Classe_Time.extend(classes_horaire)
        # print(f"Horaire {horaire}: {classes_horaire.count()} classes")
    
    # DÉBOGAGE: Afficher le détail des classes
    # print(f"\n=== DÉTAIL ALL_CLASSE_TIME ===")
    # for i, classe in enumerate(all_Classe_Time):
    #     print(f"{i+1}. Type: {classe.type} | Jour: {classe.jour} | Temps: {classe.temps} | Matière: {classe.matiere.nom_fr}")
    
    # Si all_Classe_Time est vide, utiliser all_Classe_Etu comme fallback
    if not all_Classe_Time:
        # print("FALLBACK: all_Classe_Time vide, utilisation de all_Classe_Etu")
        all_Classe_Time = list(all_Classe_Etu)
    
    # Compter les types de classes
    for classe in all_Classe_Etu:
        if classe.type == "Cours":
            nbr_Cours += 1
        elif classe.type == "TP":
            nbr_TP += 1
        elif classe.type == "TD":
            nbr_TD += 1
        elif classe.type == "Sortie Scientifique":
            nbr_SS += 1
        
        # Calcul du taux d'avancement
        if classe.seance_created == True:
            all_Seances = Seance.objects.filter(classe=classe.id)
            nbr_Sea_fait = Seance.objects.filter(classe=classe.id, fait=True)
            
            if nbr_Sea_fait.exists() and all_Seances.exists():
                taux_avancement = ((nbr_Sea_fait.count()) / all_Seances.count()) * 100
                taux_avancement = round(taux_avancement)
                classe.taux_avancement = taux_avancement
                classe.save()

    all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS
    
    # print(f"\n=== STATISTIQUES ===")
    # print(f"Total: {all_classes} | Cours: {nbr_Cours} | TD: {nbr_TD} | TP: {nbr_TP} | SS: {nbr_SS}")
    
    # Récupérer tous les semestres disponibles
    all_semestres = Semestre.objects.filter(
        classe__niv_spe_dep_sg=my_Etu.niv_spe_dep_sg
    ).distinct().order_by('numero')
    
    if not all_semestres.exists():
        all_semestres = Semestre.objects.all().order_by('numero')
    
    # Statistiques
    stats_classes = {
        'total': all_classes,
        'cours': nbr_Cours,
        'td': nbr_TD,
        'tp': nbr_TP,
        'ss': nbr_SS,
        'jours': len([jour for jour in jours if all_classes_queryset.filter(jour=jour).exists()]),
        'vol_horaire': round(all_classes * 1.5, 1)
    }

    # Contexte final
    context = {
        'title': 'إستعمال الزمن - الطالب',
        'all_Classe_Etu': all_Classe_Etu,
        'my_Dep': my_Dep,
        'my_Fac': my_Fac,
        'my_Etu': my_Etu,
        'all_Classe_Time': all_Classe_Time,  # CRUCIAL!
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
        'my_Classes': all_classes_queryset,
        'niveau_etudiant': my_Etu.niv_spe_dep_sg,
        'semestre_actuel': semestre_obj,
    }
    
    # print(f"\n=== CONTEXTE FINAL ===")
    # print(f"all_Classe_Time count: {len(all_Classe_Time)}")
    # print(f"sevenDays: {sevenDays}")
    # print(f"sixClasses: {sixClasses}")
    
    return render(request, 'etudiant/timeTable_Etu.html', context)










# Vue auxiliaire pour les détails d'une classe (optionnelle)
@etudiant_access_required
def classe_detail_etu(request, classe_id, etudiant, departement):

    """
    Vue pour afficher les détails d'une classe spécifique
    """
    try:
        my_Etu = Etudiant.objects.get(user=request.user)
        classe = get_object_or_404(Classe, id=classe_id)
        
        # Vérifier que l'étudiant a accès à cette classe
        if classe.niv_spe_dep_sg != my_Etu.niv_spe_dep_sg:
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الحصة')
            return redirect('etud:timeTable_Etu')
        
        # Récupérer les séances de cette classe
        seances = Seance.objects.filter(classe=classe).order_by('date')
        
        context = {
            'classe': classe,
            'seances': seances,
            'my_Etu': my_Etu,
        }
        
        return render(request, 'etudiant/classe_detail.html', context)
        
    except Etudiant.DoesNotExist:
        messages.error(request, 'ملف الطالب غير موجود')
        return redirect('auth:login')




# Vue pour les absences de l'étudiant dans une classe
@etudiant_access_required
def abs_Etu_Classe(request, clas_id, etudiant, departement):
    """
    Vue modernisée pour afficher les absences d'un étudiant dans une classe
    Corrigée pour résoudre le problème des absences non affichées
    """
    try:
        # Récupération de l'étudiant connecté avec le nouveau modèle
        my_Etu = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.warning(request, 'لا تملك إذن الدخول - ملف الطالب غير موجود')
        return redirect('auth:login')
    
    try:
        # Récupération des données liées
        my_Dep = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement
        my_Fac = my_Dep.faculte
        my_Classe = get_object_or_404(Classe, id=clas_id)
        
        # Vérification que l'étudiant a accès à cette classe
        if my_Classe.niv_spe_dep_sg != my_Etu.niv_spe_dep_sg:
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الحصة')
            return redirect('etud:timeTable_Etu')
        
        # Récupération des séances effectuées
        all_sea_fait = Seance.objects.filter(
            classe=my_Classe,
            fait=True
        ).order_by('date')
        
        # CORRECTION: Structurer les données différemment
        # Créer un dictionnaire avec les séances et leurs absences
        seances_with_absences = []
        
        for sea in all_sea_fait:
            try:
                absence = Abs_Etu_Seance.objects.get(
                    seance=sea, 
                    etudiant=my_Etu
                )
                seance_data = {
                    'seance': sea,
                    'absence': absence,
                    'status': 'absent_justifie' if (not absence.present and absence.justifiee) 
                             else 'absent' if not absence.present 
                             else 'present'
                }
            except Abs_Etu_Seance.DoesNotExist:
                # Pas d'enregistrement d'absence = présent par défaut
                seance_data = {
                    'seance': sea,
                    'absence': None,
                    'status': 'no_data'
                }
            
            seances_with_absences.append(seance_data)
        
        # Récupération des statistiques de l'étudiant pour cette classe
        try:
            abs_classe_stats = Abs_Etu_Classe.objects.get(
                classe=my_Classe,
                etudiant=my_Etu
            )
            total_absences = abs_classe_stats.nbr_absence or 0
            absences_justifiees = abs_classe_stats.nbr_absence_justifiee or 0
        except Abs_Etu_Classe.DoesNotExist:
            # Calculer les statistiques à partir des données
            total_absences = sum(1 for s in seances_with_absences 
                               if s['status'] in ['absent', 'absent_justifie'])
            absences_justifiees = sum(1 for s in seances_with_absences 
                                    if s['status'] == 'absent_justifie')
            abs_classe_stats = None
        
        # Calcul d'autres statistiques
        absences_non_justifiees = total_absences - absences_justifiees
        total_sessions = all_sea_fait.count()
        taux_presence = 0
        if total_sessions > 0:
            taux_presence = round(((total_sessions - total_absences) / total_sessions) * 100, 1)
        
        # Préparation des titres
        titre_00 = my_Classe.niv_spe_dep_sg
        titre_01 = my_Classe.matiere.nom_fr
        
        # DÉBOGAGE
        # print(f"=== DÉBOGAGE ABSENCES ===")
        # print(f"Classe: {my_Classe}")
        # print(f"Total séances: {total_sessions}")
        # print(f"Séances avec données: {len(seances_with_absences)}")
        # for i, s in enumerate(seances_with_absences[:3]):  # Afficher les 3 premières
        #     print(f"  {i+1}. Date: {s['seance'].date} | Status: {s['status']} | Absence: {s['absence']}")
        
        context = {
            'title': 'غيابات الطالب',
            'my_Fac': my_Fac,
            'my_Dep': my_Dep,
            'my_Etu': my_Etu,
            'my_Classe': my_Classe,
            'all_sea_fait': all_sea_fait,
            'seances_with_absences': seances_with_absences,  # NOUVEAU
            'abs_classe_stats': abs_classe_stats,
            'titre_00': titre_00,
            'titre_01': titre_01,
            
            # Statistiques
            'total_sessions': total_sessions,
            'total_absences': total_absences,
            'absences_justifiees': absences_justifiees,
            'absences_non_justifiees': absences_non_justifiees,
            'taux_presence': taux_presence,
        }
        
        return render(request, 'etudiant/abs_Etu_Classe.html', context)
        
    except Exception as e:
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('etud:timeTable_Etu')







@etudiant_access_required
def notes_Etu_Classe(request, clas_id, etudiant, departement):
    """
    Affiche les notes de l'étudiant pour une classe spécifique (lecture seule)
    """
    try:
        # Récupération de l'étudiant connecté
        my_Etu = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.warning(request, 'لا تملك إذن الدخول - ملف الطالب غير موجود')
        return redirect('login')
    
    # Récupération des données liées
    my_Dep = my_Etu.niv_spe_dep_sg.niv_spe_dep.departement
    my_Fac = my_Dep.faculte

    # Récupérer la classe
    my_Clas = get_object_or_404(Classe, id=clas_id)
    
    # Vérifier que la classe correspond au niveau de l'étudiant
    if my_Clas.niv_spe_dep_sg != my_Etu.niv_spe_dep_sg:
        messages.error(request, "غير مصرح لك بعرض نقاط هذه الحصة")
        return redirect('etudiant:timeTable_Etu')

    # Récupérer les notes de l'étudiant pour cette classe
    try:
        ma_Note = Abs_Etu_Classe.objects.get(
            classe=my_Clas,
            etudiant=my_Etu
        )
    except Abs_Etu_Classe.DoesNotExist:
        messages.info(request, "لا توجد نقاط مسجلة لك في هذه المادة بعد")
        ma_Note = None

    # Récupérer toutes les notes de la classe pour les statistiques (optionnel)
    all_Notes_Classe = Abs_Etu_Classe.objects.filter(
        classe=my_Clas
    ).select_related('etudiant')

    # Calculer les statistiques de la classe
    try:
        statistiques = Abs_Etu_Classe.get_statistiques_classe(my_Clas)
        
        # Calculer le rang de l'étudiant
        if ma_Note and ma_Note.note_finale:
            notes_finales = list(all_Notes_Classe.values_list('note_finale', flat=True))
            notes_finales.sort(reverse=True)  # Trier par ordre décroissant
            try:
                rang_etudiant = notes_finales.index(ma_Note.note_finale) + 1
            except ValueError:
                rang_etudiant = None
        else:
            rang_etudiant = None
    except:
        statistiques = None
        rang_etudiant = None

    # Récupérer les séances pour voir le détail des notes supplémentaires
    seances_etudiant = []
    if ma_Note:
        try:
            # Récupérer les séances où l'étudiant a eu des notes supplémentaires
            seances_etudiant = Seance.objects.filter(
                classe=my_Clas,
                fait=True
            ).order_by('date_seance')
        except:
            seances_etudiant = []

    titre_00 = my_Clas.niv_spe_dep_sg
    titre_01 = my_Clas.matiere.nom_fr

    context = {
        'title': 'نقاطي في المادة',
        'titre_00': titre_00,
        'titre_01': titre_01,
        'my_Clas': my_Clas,
        'ma_Note': ma_Note,
        'statistiques': statistiques,
        'rang_etudiant': rang_etudiant,
        'seances_etudiant': seances_etudiant,
        'my_Dep': my_Dep,
        'my_Fac': my_Fac,
        'my_Etu': my_Etu,
        'enseignant_info': my_Clas.enseignant,  # Informations de l'enseignant
        'nombre_etudiants_classe': all_Notes_Classe.count(),
    }

    return render(request, 'etudiant/notes_Etu_Classe.html', context)