# apps/academique/etudiant/views.py

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from .models import Etudiant
from .forms import ProfileUpdateEtudForm

# Imports pour les modèles nécessaires
from apps.academique.affectation.models import Classe, Gestion_Etu_Classe, Abs_Etu_Seance, Seance
from apps.noyau.commun.models import Semestre
from apps.academique.departement.models import NivSpeDep_SG
from django.db.models import Q


# ══════════════════════════════════════════════════════════════
# HELPERS - Fonctions utilitaires
# ══════════════════════════════════════════════════════════════

def get_etudiant_context(etudiant):
    """Retourne le contexte commun pour l'étudiant."""
    my_Dep = None
    my_Fac = None

    if etudiant.niv_spe_dep_sg:
        niv_spe_dep = etudiant.niv_spe_dep_sg.niv_spe_dep
        if niv_spe_dep:
            my_Dep = niv_spe_dep.departement
            if my_Dep:
                my_Fac = my_Dep.faculte

    return {
        'my_Etu': etudiant,
        'my_Dep': my_Dep,
        'my_Fac': my_Fac,
    }


def get_jour_actuel():
    """Retourne le jour actuel en format arabe."""
    jours_map = {
        0: 'الإثنين',
        1: 'الثلاثاء',
        2: 'الأربعاء',
        3: 'الخميس',
        4: 'الجمعة',
        5: 'السبت',
        6: 'الأحد',
    }
    return jours_map.get(datetime.now().weekday(), 'السبت')


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════

@login_required
def dashboard_Etud(request):
    """Tableau de bord de l'étudiant."""
    try:
        etudiant = request.user.etudiant_profile

        # Contexte de base
        context = get_etudiant_context(etudiant)
        context['title'] = 'لوحة التحكم / Tableau de bord'
        context['active_menu'] = 'dashboard'

        # Récupérer le semestre sélectionné
        semestre_selected = request.GET.get('semestre', '1')
        context['semestre_selected'] = semestre_selected

        # Récupérer les semestres disponibles
        all_semestres = Semestre.objects.all().order_by('numero')
        context['all_semestres'] = all_semestres

        # Récupérer les classes de l'étudiant pour ce semestre
        mes_matieres = []
        classes_today = []
        all_classes_etu = []

        if etudiant.niv_spe_dep_sg:
            etu_niv_spe_dep_sg = etudiant.niv_spe_dep_sg

            # Récupérer les classes du groupe de l'étudiant
            classes_groupe = Classe.objects.filter(
                niv_spe_dep_sg=etu_niv_spe_dep_sg
            ).select_related('matiere', 'enseignant__enseignant')

            # Récupérer aussi les classes de section (Cours) si l'étudiant a un groupe
            classes_section = Classe.objects.none()
            if etu_niv_spe_dep_sg.section and etu_niv_spe_dep_sg.groupe:
                section_niv_spe_dep_sg = NivSpeDep_SG.objects.filter(
                    niv_spe_dep=etu_niv_spe_dep_sg.niv_spe_dep,
                    section=etu_niv_spe_dep_sg.section,
                    groupe__isnull=True
                ).first()
                if section_niv_spe_dep_sg:
                    classes_section = Classe.objects.filter(
                        niv_spe_dep_sg=section_niv_spe_dep_sg
                    ).select_related('matiere', 'enseignant__enseignant')

            # Combiner toutes les classes
            all_classes_etu = list(classes_groupe) + list(classes_section)

            # Filtrer par semestre si disponible
            try:
                semestre_num = int(semestre_selected)
                mes_matieres = [c for c in all_classes_etu if c.matiere and hasattr(c.matiere, 'semestre') and c.matiere.semestre and c.matiere.semestre.numero == semestre_num]
            except (ValueError, AttributeError):
                mes_matieres = all_classes_etu

            # Classes d'aujourd'hui
            jour_actuel = get_jour_actuel()
            jour_map = {
                'الأحد': 'Dimanche', 'الإثنين': 'Lundi', 'الثلاثاء': 'Mardi',
                'الأربعاء': 'Mercredi', 'الخميس': 'Jeudi', 'الجمعة': 'Vendredi', 'السبت': 'Samedi'
            }
            classes_today = [c for c in mes_matieres if c.jour == jour_actuel or c.get_jour_display() == jour_actuel]

        context['mes_matieres'] = mes_matieres
        context['classes_today'] = classes_today

        # Calculer les statistiques réelles de l'étudiant
        total_absences = 0
        absences_justifiees = 0
        total_sessions = 0
        notes_list = []

        # Récupérer les données de gestion pour toutes les classes
        for classe in mes_matieres:
            try:
                gestion = Gestion_Etu_Classe.objects.get(classe=classe, etudiant=etudiant)
                total_absences += gestion.nbr_absence or 0
                absences_justifiees += gestion.nbr_absence_justifiee or 0
                if gestion.note_finale is not None:
                    notes_list.append(float(gestion.note_finale))
            except Gestion_Etu_Classe.DoesNotExist:
                pass

            # Compter les séances faites pour cette classe
            if classe.seance_created:
                total_sessions += Seance.objects.filter(classe=classe, fait=True).count()

        # Calculer le taux de présence
        taux_presence = 0
        if total_sessions > 0:
            taux_presence = int(round(((total_sessions - total_absences) / total_sessions) * 100))
            if taux_presence < 0:
                taux_presence = 0

        # Calculer la moyenne générale
        moyenne_generale = None
        if notes_list:
            moyenne_generale = round(sum(notes_list) / len(notes_list), 2)

        # Statistiques de l'étudiant
        context['stats_etudiant'] = {
            'total_classes': len(mes_matieres),
            'volume_horaire': round(len(mes_matieres) * 1.5, 1),
            'taux_presence': taux_presence,
            'total_absences': total_absences,
            'absences_justifiees': absences_justifiees,
            'moyenne_generale': moyenne_generale,
            'progres_matieres': 0,
            'participation': 0,
        }

        return render(request, 'etudiant/dashboard_Etu.html', context)
    except Etudiant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للطالب / Profil étudiant introuvable')
        return redirect('comm:home')


@login_required
def profile_Etud(request, etudiant_id=None):
    """Affichage du profil de l'étudiant."""
    try:
        if etudiant_id:
            etudiant = get_object_or_404(Etudiant, id=etudiant_id)
        else:
            etudiant = request.user.etudiant_profile

        # Contexte de base
        context = get_etudiant_context(etudiant)
        context['title'] = 'صفحة التعريف / Profil'
        context['active_menu'] = 'profile'
        context['etudiant'] = etudiant

        return render(request, 'etudiant/profile_Etu.html', context)
    except Etudiant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للطالب / Profil étudiant introuvable')
        return redirect('comm:home')


@login_required
def profileUpdate_Etud(request):
    """Mise à jour du profil de l'étudiant."""
    try:
        etudiant = request.user.etudiant_profile

        if request.method == 'POST':
            form = ProfileUpdateEtudForm(request.POST, request.FILES, instance=etudiant)
            if form.is_valid():
                form.save()
                messages.success(request, 'تم تحديث المعلومات بنجاح / Informations mises à jour avec succès')
                return redirect('etudiant:profile_Etud')
            else:
                messages.error(request, 'خطأ في النموذج / Erreur dans le formulaire')
        else:
            form = ProfileUpdateEtudForm(instance=etudiant)

        # Contexte de base
        context = get_etudiant_context(etudiant)
        context['title'] = 'تعديل المعلومات / Modifier le profil'
        context['active_menu'] = 'profile'
        context['etudiant'] = etudiant
        context['form'] = form

        return render(request, 'etudiant/profileUpdate_Etu.html', context)
    except Etudiant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للطالب / Profil étudiant introuvable')
        return redirect('comm:home')


@login_required
def changePassword_Etud(request):
    """Changement de mot de passe de l'étudiant."""
    try:
        etudiant = request.user.etudiant_profile

        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            # Vérifier l'ancien mot de passe
            if not request.user.check_password(old_password):
                messages.error(request, 'كلمة المرور الحالية غير صحيحة / Mot de passe actuel incorrect')
                return redirect('etudiant:changePassword_Etud')

            # Vérifier que les nouveaux mots de passe correspondent
            if new_password != confirm_password:
                messages.error(request, 'كلمات المرور الجديدة غير متطابقة / Les nouveaux mots de passe ne correspondent pas')
                return redirect('etudiant:changePassword_Etud')

            # Vérifier la longueur minimale
            if len(new_password) < 8:
                messages.error(request, 'كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل / Le mot de passe doit contenir au moins 8 caractères')
                return redirect('etudiant:changePassword_Etud')

            # Changer le mot de passe
            request.user.set_password(new_password)
            request.user.save()

            # Reconnecter l'utilisateur
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)

            messages.success(request, 'تم تغيير كلمة المرور بنجاح / Mot de passe modifié avec succès')
            return redirect('etudiant:profile_Etud')

        # Contexte de base
        context = get_etudiant_context(etudiant)
        context['title'] = 'تغيير كلمة المرور / Changer le mot de passe'
        context['active_menu'] = 'profile'
        context['etudiant'] = etudiant

        return render(request, 'etudiant/change_password_Etu.html', context)
    except Etudiant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للطالب / Profil étudiant introuvable')
        return redirect('comm:home')


@login_required
def list_Etud(request):
    """Liste de tous les étudiants."""
    try:
        etudiants = Etudiant.objects.select_related('user', 'niv_spe_dep_sg', 'wilaya').all()
        context = {
            'title': 'قائمة الطلبة / Liste des étudiants',
            'etudiants': etudiants,
        }
        return render(request, 'etudiant/list_Etud.html', context)
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


@login_required
def detail_Etud(request, etudiant_id):
    """Détails complets d'un étudiant."""
    try:
        etudiant = get_object_or_404(
            Etudiant.objects.select_related('user', 'niv_spe_dep_sg', 'wilaya'),
            id=etudiant_id
        )
        # Contexte de base
        context = get_etudiant_context(etudiant)
        context['title'] = f'تفاصيل الطالب / Détails étudiant - {etudiant.get_nom_complet()}'
        context['etudiant'] = etudiant

        return render(request, 'etudiant/detail_Etud.html', context)
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('etudiant:list_Etud')


# ══════════════════════════════════════════════════════════════
# EMPLOI DU TEMPS
# ══════════════════════════════════════════════════════════════

@login_required
def timeTable_Etu(request):
    """Emploi du temps de l'étudiant."""
    try:
        etudiant = request.user.etudiant_profile

        # Contexte de base
        context = get_etudiant_context(etudiant)
        context['title'] = 'إستعمال الزمن / Emploi du temps'
        context['active_menu'] = 'timetable'

        # Récupérer le semestre sélectionné
        semestre_selected = request.GET.get('semestre', '1')
        context['semestre_selected'] = semestre_selected

        # Récupérer les semestres disponibles
        all_semestres = Semestre.objects.all().order_by('numero')
        context['all_semestres'] = all_semestres

        # Définir les horaires et jours (valeurs du modèle Classe.Dayblock)
        horaires = [
            '08:00-09:30',
            '09:40-11:10',
            '11:20-12:50',
            '13:10-14:40',
            '14:50-16:20',
            '16:30-18:00'
        ]

        # Jours avec valeurs françaises (pour comparaison) et labels arabes (pour affichage)
        jours_data = [
            {'value': 'Samedi', 'label': 'السبت'},
            {'value': 'Dimanche', 'label': 'الأحد'},
            {'value': 'Lundi', 'label': 'الإثنين'},
            {'value': 'Mardi', 'label': 'الثلاثاء'},
            {'value': 'Mercredi', 'label': 'الأربعاء'},
            {'value': 'Jeudi', 'label': 'الخميس'},
        ]

        # Variables pour le template (deux noms pour compatibilité)
        context['sixClasses'] = horaires
        context['sixClassesTimes'] = horaires
        context['sevenDays'] = jours_data  # Liste de dictionnaires avec value et label

        # Récupérer les classes de l'étudiant
        all_Classe_Time = []

        if etudiant.niv_spe_dep_sg:
            from django.db.models import Q
            from apps.academique.departement.models import NivSpeDep_SG

            etu_niv_spe_dep_sg = etudiant.niv_spe_dep_sg

            # Construire le filtre pour inclure:
            # 1. Classes du groupe spécifique de l'étudiant (TD/TP)
            # 2. Classes de la section (Cours) - même niv_spe_dep, même section, mais groupe=None
            filter_conditions = Q(niv_spe_dep_sg=etu_niv_spe_dep_sg)

            # Si l'étudiant a un groupe ET une section, chercher aussi les classes de section (Cours)
            if etu_niv_spe_dep_sg.section and etu_niv_spe_dep_sg.groupe:
                # Trouver le NivSpeDep_SG de la section (sans groupe)
                section_niv_spe_dep_sg = NivSpeDep_SG.objects.filter(
                    niv_spe_dep=etu_niv_spe_dep_sg.niv_spe_dep,
                    section=etu_niv_spe_dep_sg.section,
                    groupe__isnull=True
                ).first()

                if section_niv_spe_dep_sg:
                    # Ajouter les classes de la section (principalement les Cours)
                    filter_conditions |= Q(niv_spe_dep_sg=section_niv_spe_dep_sg)

            classes_qs = Classe.objects.filter(
                filter_conditions
            ).select_related(
                'matiere', 'enseignant__enseignant', 'niv_spe_dep_sg__niv_spe_dep'
            )

            # Filtrer par semestre si disponible
            try:
                semestre_num = int(semestre_selected)
                classes_qs = classes_qs.filter(
                    matiere__semestre__numero=semestre_num
                )
            except (ValueError, AttributeError):
                pass

            all_Classe_Time = list(classes_qs)

        context['all_Classe_Time'] = all_Classe_Time
        context['all_Classe_Etu'] = all_Classe_Time  # Alias pour le tableau détaillé
        context['all_classes'] = len(all_Classe_Time)

        # Compter par type
        nbr_Cours = len([c for c in all_Classe_Time if c.type == 'Cours'])
        nbr_TD = len([c for c in all_Classe_Time if c.type == 'TD'])
        nbr_TP = len([c for c in all_Classe_Time if c.type == 'TP'])
        nbr_SS = len([c for c in all_Classe_Time if c.type == 'SS'])

        context['nbr_Cours'] = nbr_Cours
        context['nbr_TD'] = nbr_TD
        context['nbr_TP'] = nbr_TP
        context['nbr_SS'] = nbr_SS

        # Calcul du taux d'avancement, absences et notes pour chaque classe
        for classe in all_Classe_Time:
            # Taux d'avancement
            if classe.seance_created:
                all_seances = Seance.objects.filter(classe=classe)
                seances_faites = all_seances.filter(fait=True).count()
                total_seances = all_seances.count()
                if total_seances > 0:
                    classe.taux_avancement = round((seances_faites / total_seances) * 100)
                else:
                    classe.taux_avancement = 0
            else:
                classe.taux_avancement = 0

            # Vérifier les absences de l'étudiant dans cette classe
            try:
                gestion = Gestion_Etu_Classe.objects.get(classe=classe, etudiant=etudiant)
                classe.total_absences = gestion.nbr_absence or 0
                classe.has_notes = gestion.note_finale is not None
            except Gestion_Etu_Classe.DoesNotExist:
                classe.total_absences = 0
                classe.has_notes = False

        # Statistiques supplémentaires
        jours_uniques = set(c.jour for c in all_Classe_Time if c.jour)
        context['stats_classes'] = {
            'total': len(all_Classe_Time),
            'jours': len(jours_uniques),
            'vol_horaire': len(all_Classe_Time) * 1.5,  # 1h30 par séance
        }

        return render(request, 'etudiant/timeTable_Etu.html', context)
    except Etudiant.DoesNotExist:
        messages.error(request, 'لا يوجد ملف تعريف للطالب / Profil étudiant introuvable')
        return redirect('comm:home')


# ══════════════════════════════════════════════════════════════
# ABSENCES DE L'ÉTUDIANT
# ══════════════════════════════════════════════════════════════

@login_required
def abs_Etu_Classe(request, clas_id):
    """
    Affiche les absences d'un étudiant dans une classe spécifique.
    """
    try:
        etudiant = request.user.etudiant_profile
    except Etudiant.DoesNotExist:
        messages.warning(request, 'لا تملك إذن الدخول - ملف الطالب غير موجود')
        return redirect('comm:home')

    # Contexte de base
    context = get_etudiant_context(etudiant)
    context['title'] = 'غيابات الطالب / Absences'
    context['active_menu'] = 'absences'

    # Récupérer la classe
    my_Classe = get_object_or_404(Classe, id=clas_id)

    # Vérification que l'étudiant a accès à cette classe
    etu_niv_spe_dep_sg = etudiant.niv_spe_dep_sg
    has_access = False

    if my_Classe.niv_spe_dep_sg == etu_niv_spe_dep_sg:
        has_access = True
    elif etu_niv_spe_dep_sg.section and etu_niv_spe_dep_sg.groupe:
        # Vérifier si c'est une classe de section (Cours)
        section_niv_spe_dep_sg = NivSpeDep_SG.objects.filter(
            niv_spe_dep=etu_niv_spe_dep_sg.niv_spe_dep,
            section=etu_niv_spe_dep_sg.section,
            groupe__isnull=True
        ).first()
        if section_niv_spe_dep_sg and my_Classe.niv_spe_dep_sg == section_niv_spe_dep_sg:
            has_access = True

    if not has_access:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الحصة')
        return redirect('etud:timeTable_Etu')

    # Récupération des séances effectuées
    all_sea_fait = Seance.objects.filter(
        classe=my_Classe,
        fait=True
    ).order_by('date')

    # Structurer les données avec les absences
    seances_with_absences = []

    for sea in all_sea_fait:
        try:
            absence = Abs_Etu_Seance.objects.get(
                seance=sea,
                etudiant=etudiant
            )
            seance_data = {
                'seance': sea,
                'absence': absence,
                'status': 'absent_justifie' if (not absence.present and absence.justifiee)
                         else 'absent' if not absence.present
                         else 'present'
            }
        except Abs_Etu_Seance.DoesNotExist:
            seance_data = {
                'seance': sea,
                'absence': None,
                'status': 'no_data'
            }

        seances_with_absences.append(seance_data)

    # Récupération des statistiques
    try:
        abs_classe_stats = Gestion_Etu_Classe.objects.get(
            classe=my_Classe,
            etudiant=etudiant
        )
        total_absences = abs_classe_stats.nbr_absence or 0
        absences_justifiees = abs_classe_stats.nbr_absence_justifiee or 0
    except Gestion_Etu_Classe.DoesNotExist:
        total_absences = sum(1 for s in seances_with_absences
                           if s['status'] in ['absent', 'absent_justifie'])
        absences_justifiees = sum(1 for s in seances_with_absences
                                if s['status'] == 'absent_justifie')
        abs_classe_stats = None

    # Calculs des statistiques
    absences_non_justifiees = total_absences - absences_justifiees
    total_sessions = all_sea_fait.count()
    taux_presence = 0
    if total_sessions > 0:
        taux_presence = int(round(((total_sessions - total_absences) / total_sessions) * 100))

    # Titres
    titre_00 = my_Classe.niv_spe_dep_sg
    titre_01 = my_Classe.matiere.nom_fr if my_Classe.matiere else 'Matière'

    context.update({
        'my_Classe': my_Classe,
        'all_sea_fait': all_sea_fait,
        'seances_with_absences': seances_with_absences,
        'abs_classe_stats': abs_classe_stats,
        'titre_00': titre_00,
        'titre_01': titre_01,
        'total_sessions': total_sessions,
        'total_absences': total_absences,
        'absences_justifiees': absences_justifiees,
        'absences_non_justifiees': absences_non_justifiees,
        'taux_presence': taux_presence,
    })

    return render(request, 'etudiant/abs_Etu_Classe.html', context)


# ══════════════════════════════════════════════════════════════
# NOTES DE L'ÉTUDIANT
# ══════════════════════════════════════════════════════════════

@login_required
def notes_Etu_Classe(request, clas_id):
    """
    Affiche les notes de l'étudiant pour une classe spécifique (lecture seule).
    """
    try:
        etudiant = request.user.etudiant_profile
    except Etudiant.DoesNotExist:
        messages.warning(request, 'لا تملك إذن الدخول - ملف الطالب غير موجود')
        return redirect('comm:home')

    # Contexte de base
    context = get_etudiant_context(etudiant)
    context['title'] = 'نقاطي في المادة / Mes notes'
    context['active_menu'] = 'notes'

    # Récupérer la classe
    my_Clas = get_object_or_404(Classe, id=clas_id)

    # Vérification d'accès
    etu_niv_spe_dep_sg = etudiant.niv_spe_dep_sg
    has_access = False

    if my_Clas.niv_spe_dep_sg == etu_niv_spe_dep_sg:
        has_access = True
    elif etu_niv_spe_dep_sg.section and etu_niv_spe_dep_sg.groupe:
        section_niv_spe_dep_sg = NivSpeDep_SG.objects.filter(
            niv_spe_dep=etu_niv_spe_dep_sg.niv_spe_dep,
            section=etu_niv_spe_dep_sg.section,
            groupe__isnull=True
        ).first()
        if section_niv_spe_dep_sg and my_Clas.niv_spe_dep_sg == section_niv_spe_dep_sg:
            has_access = True

    if not has_access:
        messages.error(request, "غير مصرح لك بعرض نقاط هذه الحصة")
        return redirect('etud:timeTable_Etu')

    # Récupérer les notes de l'étudiant
    try:
        ma_Note = Gestion_Etu_Classe.objects.get(
            classe=my_Clas,
            etudiant=etudiant
        )
    except Gestion_Etu_Classe.DoesNotExist:
        messages.info(request, "لا توجد نقاط مسجلة لك في هذه المادة بعد")
        ma_Note = None

    # Récupérer toutes les notes de la classe pour les statistiques
    all_Notes_Classe = Gestion_Etu_Classe.objects.filter(
        classe=my_Clas
    ).select_related('etudiant')

    # Calculer les statistiques
    statistiques = None
    rang_etudiant = None
    try:
        if hasattr(Gestion_Etu_Classe, 'get_statistiques_classe'):
            statistiques = Gestion_Etu_Classe.get_statistiques_classe(my_Clas)

        if ma_Note and ma_Note.note_finale:
            notes_finales = list(all_Notes_Classe.exclude(note_finale__isnull=True).values_list('note_finale', flat=True))
            notes_finales.sort(reverse=True)
            try:
                rang_etudiant = notes_finales.index(ma_Note.note_finale) + 1
            except ValueError:
                rang_etudiant = None
    except Exception:
        pass

    # Titres
    titre_00 = my_Clas.niv_spe_dep_sg
    titre_01 = my_Clas.matiere.nom_fr if my_Clas.matiere else 'Matière'

    context.update({
        'titre_00': titre_00,
        'titre_01': titre_01,
        'my_Clas': my_Clas,
        'ma_Note': ma_Note,
        'statistiques': statistiques,
        'rang_etudiant': rang_etudiant,
        'enseignant_info': my_Clas.enseignant,
        'nombre_etudiants_classe': all_Notes_Classe.count(),
    })

    return render(request, 'etudiant/notes_Etu_Classe.html', context)


# ══════════════════════════════════════════════════════════════
# LISTE DES SÉANCES
# ══════════════════════════════════════════════════════════════

@login_required
def list_Seance_Etu(request, clas_id):
    """
    Affiche la liste des séances d'une classe pour un étudiant.
    """
    try:
        etudiant = request.user.etudiant_profile
    except Etudiant.DoesNotExist:
        messages.warning(request, 'لا تملك إذن الدخول - ملف الطالب غير موجود')
        return redirect('comm:home')

    # Contexte de base
    context = get_etudiant_context(etudiant)
    context['title'] = 'جميع الحصص / Liste des séances'
    context['active_menu'] = 'seances'

    # Récupérer la classe
    try:
        classe = Classe.objects.get(id=clas_id)
    except Classe.DoesNotExist:
        messages.error(request, "الحصة غير موجودة")
        return redirect('etud:timeTable_Etu')

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

    context.update({
        'sea_name': classe,
        'all_Seances': all_Seances,
        'nbr_Sea_fait': nbr_Sea_fait,
        'nbr_Sea_annuler': nbr_Sea_annuler,
        'nbr_Sea_reste': nbr_Sea_reste,
        'taux_avancement': taux_avancement,
    })

    return render(request, 'etudiant/list_Seance_Etu.html', context)
