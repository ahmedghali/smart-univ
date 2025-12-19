# apps/academique/affectation/views.py

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Ens_Dep, Amphi_Dep, Salle_Dep, Laboratoire_Dep
from .forms import Ens_DepForm, Ens_DepStatistiquesS1Form, Ens_DepStatistiquesS2Form


@login_required
def list_affectations(request):
    """Liste de toutes les affectations enseignant-département."""
    try:
        affectations = Ens_Dep.objects.select_related(
            'enseignant', 'departement', 'annee_univ'
        ).all()

        # Recherche
        query = request.GET.get('q', '')
        if query:
            affectations = affectations.filter(
                Q(enseignant__nom_ar__icontains=query) |
                Q(enseignant__nom_fr__icontains=query) |
                Q(enseignant__prenom_ar__icontains=query) |
                Q(enseignant__prenom_fr__icontains=query) |
                Q(enseignant__matricule__icontains=query) |
                Q(departement__nom_ar__icontains=query) |
                Q(departement__nom_fr__icontains=query) |
                Q(departement__code__icontains=query)
            )

        context = {
            'title': 'قائمة الإنتسابات / Liste des affectations',
            'affectations': affectations,
            'query': query,
        }
        return render(request, 'affectation/list_affectations.html', context)
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('comm:home')


@login_required
def detail_affectation(request, affectation_id):
    """Détails d'une affectation enseignant-département."""
    try:
        affectation = get_object_or_404(
            Ens_Dep.objects.select_related('enseignant', 'departement', 'annee_univ'),
            id=affectation_id
        )
        context = {
            'title': f'تفاصيل الإنتساب / Détails affectation - {affectation}',
            'affectation': affectation,
        }
        return render(request, 'affectation/detail_affectation.html', context)
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        return redirect('affectation:list_affectations')


@login_required
def create_affectation(request):
    """Création d'une nouvelle affectation."""
    if request.method == 'POST':
        form = Ens_DepForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'تم إنشاء الإنتساب بنجاح / Affectation créée avec succès')
                return redirect('affectation:list_affectations')
            except Exception as e:
                messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        else:
            messages.error(request, 'خطأ في النموذج / Erreur dans le formulaire')
    else:
        form = Ens_DepForm()

    context = {
        'title': 'إنشاء إنتساب / Créer une affectation',
        'form': form,
    }
    return render(request, 'affectation/create_affectation.html', context)


@login_required
def update_affectation(request, affectation_id):
    """Modification d'une affectation."""
    affectation = get_object_or_404(Ens_Dep, id=affectation_id)

    if request.method == 'POST':
        form = Ens_DepForm(request.POST, instance=affectation)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'تم تحديث الإنتساب بنجاح / Affectation mise à jour avec succès')
                return redirect('affectation:detail_affectation', affectation_id=affectation.id)
            except Exception as e:
                messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        else:
            messages.error(request, 'خطأ في النموذج / Erreur dans le formulaire')
    else:
        form = Ens_DepForm(instance=affectation)

    context = {
        'title': 'تعديل الإنتساب / Modifier l\'affectation',
        'form': form,
        'affectation': affectation,
    }
    return render(request, 'affectation/update_affectation.html', context)


@login_required
def update_statistiques_s1(request, affectation_id):
    """Mise à jour des statistiques du semestre 1."""
    affectation = get_object_or_404(Ens_Dep, id=affectation_id)

    if request.method == 'POST':
        form = Ens_DepStatistiquesS1Form(request.POST, instance=affectation)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'تم تحديث إحصائيات السداسي الأول بنجاح / Statistiques S1 mises à jour avec succès')
                return redirect('affectation:detail_affectation', affectation_id=affectation.id)
            except Exception as e:
                messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        else:
            messages.error(request, 'خطأ في النموذج / Erreur dans le formulaire')
    else:
        form = Ens_DepStatistiquesS1Form(instance=affectation)

    context = {
        'title': 'تعديل إحصائيات السداسي الأول / Modifier statistiques S1',
        'form': form,
        'affectation': affectation,
    }
    return render(request, 'affectation/update_statistiques_s1.html', context)


@login_required
def update_statistiques_s2(request, affectation_id):
    """Mise à jour des statistiques du semestre 2."""
    affectation = get_object_or_404(Ens_Dep, id=affectation_id)

    if request.method == 'POST':
        form = Ens_DepStatistiquesS2Form(request.POST, instance=affectation)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'تم تحديث إحصائيات السداسي الثاني بنجاح / Statistiques S2 mises à jour avec succès')
                return redirect('affectation:detail_affectation', affectation_id=affectation.id)
            except Exception as e:
                messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
        else:
            messages.error(request, 'خطأ في النموذج / Erreur dans le formulaire')
    else:
        form = Ens_DepStatistiquesS2Form(instance=affectation)

    context = {
        'title': 'تعديل إحصائيات السداسي الثاني / Modifier statistiques S2',
        'form': form,
        'affectation': affectation,
    }
    return render(request, 'affectation/update_statistiques_s2.html', context)


@login_required
def delete_affectation(request, affectation_id):
    """Suppression d'une affectation."""
    affectation = get_object_or_404(Ens_Dep, id=affectation_id)

    if request.method == 'POST':
        try:
            affectation.delete()
            messages.success(request, 'تم حذف الإنتساب بنجاح / Affectation supprimée avec succès')
            return redirect('affectation:list_affectations')
        except Exception as e:
            messages.error(request, f'خطأ: {str(e)} / Erreur: {str(e)}')
            return redirect('affectation:detail_affectation', affectation_id=affectation.id)

    context = {
        'title': 'حذف الإنتساب / Supprimer l\'affectation',
        'affectation': affectation,
    }
    return render(request, 'affectation/delete_affectation.html', context)


# ══════════════════════════════════════════════════════════════
# VUES AJAX POUR L'ADMIN
# ══════════════════════════════════════════════════════════════

@staff_member_required
def ajax_get_lieux_by_departement(request):
    """
    Retourne les lieux (Amphi, Salle, Labo) disponibles pour un département.
    Utilisé par l'admin Classe pour faciliter la sélection du lieu.

    GET params:
        - departement_id: ID du département
        - lieu_type: 'amphi', 'salle', ou 'laboratoire'
    """
    departement_id = request.GET.get('departement_id')
    lieu_type = request.GET.get('lieu_type', '')

    result = {
        'amphis': [],
        'salles': [],
        'laboratoires': []
    }

    if not departement_id:
        return JsonResponse(result)

    try:
        # Récupérer les amphithéâtres du département
        if not lieu_type or lieu_type == 'amphi':
            amphis = Amphi_Dep.objects.filter(
                departement_id=departement_id,
                est_actif=True
            ).select_related('amphi')

            result['amphis'] = [
                {
                    'id': a.id,
                    'label': f"{a.amphi.numero} - {a.amphi.nom_ar or a.amphi.nom_fr or ''} (Cap: {a.amphi.capacite})",
                    'semestres': a.get_semestres_display()
                }
                for a in amphis
            ]

        # Récupérer les salles du département
        if not lieu_type or lieu_type == 'salle':
            salles = Salle_Dep.objects.filter(
                departement_id=departement_id,
                est_actif=True
            ).select_related('salle')

            result['salles'] = [
                {
                    'id': s.id,
                    'label': f"{s.salle.numero} - {s.salle.nom_ar or s.salle.nom_fr or ''} (Cap: {s.salle.capacite})",
                    'semestres': s.get_semestres_display()
                }
                for s in salles
            ]

        # Récupérer les laboratoires du département
        if not lieu_type or lieu_type == 'laboratoire':
            laboratoires = Laboratoire_Dep.objects.filter(
                departement_id=departement_id,
                est_actif=True
            ).select_related('laboratoire')

            result['laboratoires'] = [
                {
                    'id': l.id,
                    'label': f"{l.laboratoire.numero} - {l.laboratoire.nom_ar or l.laboratoire.nom_fr or ''} (Cap: {l.laboratoire.capacite})",
                    'semestres': l.get_semestres_display()
                }
                for l in laboratoires
            ]

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse(result)


@staff_member_required
def ajax_get_lieux_by_enseignant(request):
    """
    Retourne les lieux disponibles pour le département d'un enseignant (Ens_Dep).

    GET params:
        - enseignant_id: ID de l'affectation Ens_Dep
    """
    enseignant_id = request.GET.get('enseignant_id')

    result = {
        'departement_id': None,
        'departement_nom': '',
        'amphis': [],
        'salles': [],
        'laboratoires': []
    }

    if not enseignant_id:
        return JsonResponse(result)

    try:
        ens_dep = Ens_Dep.objects.select_related('departement').get(id=enseignant_id)
        departement = ens_dep.departement

        result['departement_id'] = departement.id
        result['departement_nom'] = departement.nom_ar or departement.nom_fr or departement.code

        # Récupérer les amphithéâtres
        amphis = Amphi_Dep.objects.filter(
            departement=departement,
            est_actif=True
        ).select_related('amphi')

        result['amphis'] = [
            {
                'id': a.id,
                'label': f"🏛️ {a.amphi.numero} - {a.amphi.nom_ar or a.amphi.nom_fr or ''} (Cap: {a.amphi.capacite})",
                'semestres': a.get_semestres_display()
            }
            for a in amphis
        ]

        # Récupérer les salles
        salles = Salle_Dep.objects.filter(
            departement=departement,
            est_actif=True
        ).select_related('salle')

        result['salles'] = [
            {
                'id': s.id,
                'label': f"🚪 {s.salle.numero} - {s.salle.nom_ar or s.salle.nom_fr or ''} (Cap: {s.salle.capacite})",
                'semestres': s.get_semestres_display()
            }
            for s in salles
        ]

        # Récupérer les laboratoires
        laboratoires = Laboratoire_Dep.objects.filter(
            departement=departement,
            est_actif=True
        ).select_related('laboratoire')

        result['laboratoires'] = [
            {
                'id': l.id,
                'label': f"🔬 {l.laboratoire.numero} - {l.laboratoire.nom_ar or l.laboratoire.nom_fr or ''} (Cap: {l.laboratoire.capacite})",
                'semestres': l.get_semestres_display()
            }
            for l in laboratoires
        ]

    except Ens_Dep.DoesNotExist:
        return JsonResponse({'error': 'Enseignant non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse(result)
