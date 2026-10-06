# apps/academique/departement/views.py
"""
Vues du département - Version optimisée.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.academique.affectation.models import Amphi_Dep, Classe, Ens_Dep, Laboratoire_Dep, Salle_Dep
from apps.academique.etudiant.models import Etudiant
from apps.noyau.commun.models import AffectationPoste, AnneeUniversitaire, PostePermission

from .forms import DepartementForm
from .models import Departement, Matiere, Specialite

# ═══════════════════════════════════════════════════════════════════════════
# MIXINS ET DÉCORATEURS
# ═══════════════════════════════════════════════════════════════════════════


class DepartementMixin:
    """Mixin pour récupérer le département et l'année courante."""

    def get_departement(self, request):
        """Récupère le département de la session ou des affectations."""
        dep_id = request.session.get("selected_departement_id")
        if dep_id:
            return Departement.objects.filter(id=dep_id).first()

        deps = AffectationPoste.get_departements_user(request.user)
        if deps.exists():
            dep = deps.first()
            request.session["selected_departement_id"] = dep.id
            return dep
        return None

    def get_annee_courante(self):
        """Récupère l'année universitaire courante."""
        return AnneeUniversitaire.objects.filter(est_courante=True).first()

    def get_context(self, request):
        """Retourne le contexte de base avec département et année."""
        departement = self.get_departement(request)
        annee = self.get_annee_courante()
        return {
            "departement": departement,
            "annee_courante": annee,
            "permissions": PostePermission.get_permissions(request),
        }


def with_departement(view_func):
    """Décorateur qui injecte le département dans la vue."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        dep_id = request.session.get("selected_departement_id")
        departement = Departement.objects.filter(id=dep_id).first() if dep_id else None

        if not departement:
            deps = AffectationPoste.get_departements_user(request.user)
            if deps.exists():
                departement = deps.first()
                request.session["selected_departement_id"] = departement.id

        if not departement:
            messages.error(request, "لم يتم تحديد القسم")
            return redirect("auth:login")

        request.departement = departement
        request.annee_courante = AnneeUniversitaire.objects.filter(est_courante=True).first()
        return view_func(request, *args, **kwargs)

    return wrapper


def get_dep_sidebar_context(request, departement):
    """
    Retourne le contexte commun pour le menu latéral département.
    À utiliser dans toutes les vues département pour avoir un sidebar cohérent.
    """
    context = {
        "my_Dep": departement,
        "my_Fac": departement.faculte if departement else None,
        "departement": departement,
        "active_menu": "dashboard",
    }
    # Ajouter les permissions et is_admin_poste
    PostePermission.add_to_context(request, context)
    return context


# ═══════════════════════════════════════════════════════════════════════════
# STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════


class StatsCalculator:
    """Calcule les statistiques du département de manière optimisée."""

    def __init__(self, departement, annee_univ):
        self.departement = departement
        self.annee = annee_univ
        self._enseignants = None

    @property
    def enseignants(self):
        """Cache la requête des enseignants."""
        if self._enseignants is None:
            self._enseignants = Ens_Dep.objects.filter(
                departement=self.departement, annee_univ=self.annee
            ).select_related("enseignant")
        return self._enseignants

    def get_teacher_stats(self):
        """Statistiques des enseignants avec une seule requête."""
        qs = self.enseignants
        stats = qs.aggregate(
            total=Count("id"),
            actifs=Count("id", filter=Q(est_actif=True)),
            s1=Count("id", filter=Q(semestre_1=True)),
            s2=Count("id", filter=Q(semestre_2=True)),
        )

        # Comptage par statut
        by_status = qs.values("statut").annotate(count=Count("id"))
        status_map = {s["statut"]: s["count"] for s in by_status}

        return {
            "total_teachers": stats["total"],
            "present_teachers": stats["actifs"],
            "enseignants_s1": stats["s1"],
            "enseignants_s2": stats["s2"],
            "permanent_teachers": status_map.get("Permanent", 0),
            "vacataire_teachers": status_map.get("Vacataire", 0),
            "associe_teachers": status_map.get("Associe", 0),
            "doctorant_teachers": status_map.get("Doctorant", 0),
            "permanent_vacataire_teachers": status_map.get("Permanent & Vacataire", 0),
        }

    def get_all_stats(self):
        """Retourne toutes les statistiques."""
        stats = self.get_teacher_stats()

        # Temporaires = tous sauf permanents
        stats["temporary_teachers"] = (
            stats["vacataire_teachers"]
            + stats["associe_teachers"]
            + stats["doctorant_teachers"]
            + stats["permanent_vacataire_teachers"]
        )

        # Autres statistiques
        stats["total_students"] = Etudiant.objects.count()
        stats["total_matieres"] = (
            Matiere.objects.filter(niv_spe_dep__specialite__departement=self.departement).distinct().count()
        )
        stats["total_specialites"] = Specialite.objects.filter(departement=self.departement).count()

        # Infrastructures
        stats["total_rooms"] = (
            Salle_Dep.objects.filter(departement=self.departement).count()
            + Amphi_Dep.objects.filter(departement=self.departement).count()
            + Laboratoire_Dep.objects.filter(departement=self.departement).count()
        )

        # Classes
        stats["total_classes"] = Classe.objects.filter(
            ens_dep__departement=self.departement, ens_dep__annee_univ=self.annee
        ).count()

        stats["annee_courante"] = self.annee
        return stats


def get_department_stats(departement, annee_univ=None):
    """Fonction utilitaire pour la compatibilité."""
    if not annee_univ:
        annee_univ = AnneeUniversitaire.objects.filter(est_courante=True).first()

    if not departement or not annee_univ:
        return get_default_stats()

    try:
        return StatsCalculator(departement, annee_univ).get_all_stats()
    except Exception:
        return get_default_stats()


def get_default_stats():
    """Retourne les statistiques par défaut."""
    return {
        "total_teachers": 0,
        "permanent_teachers": 0,
        "temporary_teachers": 0,
        "present_teachers": 0,
        "total_students": 0,
        "total_matieres": 0,
        "total_classes": 0,
        "total_specialites": 0,
        "total_rooms": 0,
        "enseignants_s1": 0,
        "enseignants_s2": 0,
        "annee_courante": None,
    }


# ═══════════════════════════════════════════════════════════════════════════
# VUES PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════


@login_required
@with_departement
def dashboard_Dep(request):
    """Tableau de bord du chef de département."""
    stats = get_department_stats(request.departement, request.annee_courante)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "لوحة التحكم",
            "active_menu": "dashboard",
            "stats": stats,
            **stats,  # Pour compatibilité avec les anciens templates
        }
    )
    return render(request, "departement/dashboard_Dep.html", context)


@login_required
@with_departement
def profile_Dep(request):
    """Affiche le profil du département."""
    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "الملف الشخصي",
            "active_menu": "profile",
        }
    )
    return render(request, "departement/profile_Dep.html", context)


@login_required
@with_departement
def profileUpdate_Dep(request):
    """Modifie le profil du département."""
    if request.method == "POST":
        form = DepartementForm(request.POST, instance=request.departement)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث معلومات القسم بنجاح")
            return redirect("depa:profile_Dep")
    else:
        form = DepartementForm(instance=request.departement)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "تعديل الملف الشخصي",
            "active_menu": "profile",
            "form": form,
        }
    )
    return render(request, "departement/profileUpdate_Dep.html", context)


@login_required
@with_departement
def list_enseignants_dep(request, semestre_num=1):
    """Liste des enseignants du département par semestre et statut."""
    # Base queryset filtré par semestre
    sem_filter = {f"semestre_{semestre_num}": True}
    qs = Ens_Dep.objects.filter(
        departement=request.departement, annee_univ=request.annee_courante, **sem_filter
    ).select_related("enseignant", "enseignant__grade", "enseignant__user")

    # Querysets par statut (ordre alphabétique)
    order = "enseignant__nom_ar"
    by_status = {
        "all_Ens_Dep_Per": qs.filter(statut="Permanent").order_by(order),
        "all_Ens_Dep_PerVac": qs.filter(statut="Permanent & Vacataire").order_by(order),
        "all_Ens_Dep_Vac": qs.filter(statut="Vacataire").order_by(order),
        "all_Ens_Dep_Aso": qs.filter(statut="Associe").order_by(order),
        "all_Ens_Dep_Doc": qs.filter(statut="Doctorant").order_by(order),
    }

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة الأساتذة",
            "active_menu": "enseignants",
            "semestre_num": semestre_num,
            "all_Ens_Dep": qs,
            **by_status,
            "grade_stats": qs.values("enseignant__grade__nom_ar").annotate(count=Count("id")).order_by("-count"),
            "missing_email_count": qs.filter(
                Q(enseignant__email_prof__isnull=True) | Q(enseignant__email_prof="")
            ).count(),
            "missing_scholar_count": qs.filter(
                Q(enseignant__googlescholar__isnull=True) | Q(enseignant__googlescholar="")
            ).count(),
        }
    )
    return render(request, "departement/list_enseignants_dep.html", context)


@login_required
@with_departement
def new_Enseignant(request):
    """Ajout d'un nouvel enseignant au département."""
    if request.method == "POST":
        messages.info(request, "هذه الميزة قيد التطوير / Fonctionnalité en cours de développement")
        return redirect("depa:list_enseignants_dep", semestre_num=1)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "إضافة أستاذ جديد",
            "active_menu": "new_enseignant",
        }
    )
    return render(request, "departement/new_Enseignant.html", context)


@login_required
@with_departement
def heures_enseignants_dep(request, semestre=1):
    """Heures de travail des enseignants par semestre."""
    filter_kwargs = {
        "departement": request.departement,
        "annee_univ": request.annee_courante,
        f"semestre_{semestre}": True,
    }

    enseignants = (
        Ens_Dep.objects.filter(**filter_kwargs).select_related("enseignant", "enseignant__user")
        if request.annee_courante
        else []
    )

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "ساعات العمل",
            "active_menu": "heures",
            "enseignants": enseignants,
            "semestre": semestre,
        }
    )
    return render(request, "departement/heures_enseignants_dep.html", context)


@login_required
@with_departement
def list_etudiants(request):
    """Liste des étudiants."""
    etudiants = Etudiant.objects.select_related(
        "niv_spe_dep_sg__niv_spe_dep__specialite", "niv_spe_dep_sg__niv_spe_dep__niveau"
    ).filter(niv_spe_dep_sg__niv_spe_dep__departement=request.departement)

    search = request.GET.get("q")
    if search:
        etudiants = etudiants.filter(
            Q(nom_ar__icontains=search) | Q(prenom_ar__icontains=search) | Q(matricule__icontains=search)
        )

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة الطلبة",
            "active_menu": "etudiants",
            "etudiants": etudiants.order_by("nom_ar"),
        }
    )
    return render(request, "departement/list_etudiants.html", context)


@login_required
@with_departement
def import_etudiants(request):
    """Import des étudiants depuis un fichier."""
    if request.method == "POST":
        messages.info(request, "هذه الميزة قيد التطوير / Fonctionnalité en cours de développement")
        return redirect("depa:list_etudiants")

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "استيراد الطلبة",
            "active_menu": "import_etudiants",
        }
    )
    return render(request, "departement/import_etudiants.html", context)


@login_required
@with_departement
def list_Specialite_Dep(request):
    """Liste des spécialités du département."""
    specialites = Specialite.objects.filter(departement=request.departement).annotate(
        nb_matieres=Count("nivspedep__matieres", distinct=True),
        nb_etudiants=Count("nivspedep__sections_groupes__etudiants", distinct=True),
    )

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة التخصصات",
            "active_menu": "specialites",
            "specialites": specialites,
        }
    )
    return render(request, "departement/list_Specialite_Dep.html", context)


@login_required
@with_departement
def list_Mat_Niv(request):
    """Liste des matières par niveau."""
    matieres = (
        Matiere.objects.filter(niv_spe_dep__specialite__departement=request.departement)
        .select_related("niv_spe_dep__specialite", "niv_spe_dep__niveau")
        .distinct()
    )

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة المواد",
            "active_menu": "matieres",
            "matieres": matieres,
        }
    )
    return render(request, "departement/list_Mat_Niv.html", context)


@login_required
@with_departement
def import_emploi(request):
    """Import de l'emploi du temps depuis un fichier."""
    if request.method == "POST":
        messages.info(request, "هذه الميزة قيد التطوير / Fonctionnalité en cours de développement")
        return redirect("depa:dashboard_Dep")

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "استيراد الحصص",
            "active_menu": "emploi",
        }
    )
    return render(request, "departement/import_emploi.html", context)


@login_required
@with_departement
def dashboard_stats_api(request):
    """API pour les statistiques du dashboard (AJAX)."""
    stats = get_department_stats(request.departement, request.annee_courante)
    return JsonResponse(stats)


# ═══════════════════════════════════════════════════════════════════════════
# ACTIONS (DELETE, ACTIVATE, etc.)
# ═══════════════════════════════════════════════════════════════════════════


@login_required
@with_departement
def delete_Enseignant(request, ens_dep_id):
    """Supprime une affectation enseignant-département."""
    ens_dep = get_object_or_404(Ens_Dep, id=ens_dep_id, departement=request.departement)

    if request.method == "POST":
        nom = f"{ens_dep.enseignant.nom_ar} {ens_dep.enseignant.prenom_ar}"
        ens_dep.delete()
        messages.success(request, f"تم حذف {nom} من القسم")
        return redirect("depa:list_enseignants_dep")

    return render(
        request,
        "departement/confirm_delete.html",
        {
            "object": ens_dep,
            "object_name": f"{ens_dep.enseignant.nom_ar} {ens_dep.enseignant.prenom_ar}",
        },
    )


@login_required
@with_departement
def delete_Ens_Acces_Dep(request, ens_id):
    """Désactive l'accès d'un enseignant au département."""
    ens_dep = get_object_or_404(
        Ens_Dep, enseignant_id=ens_id, departement=request.departement, annee_univ=request.annee_courante
    )

    ens_dep.est_actif = False
    ens_dep.save(update_fields=["est_actif"])

    messages.success(request, "تم إلغاء تنشيط الوصول بنجاح")
    return redirect("depa:list_enseignants_dep")


@login_required
@with_departement
def activate_Ens_Acces_Dep(request, ens_id):
    """Active l'accès d'un enseignant au département."""
    ens_dep = get_object_or_404(
        Ens_Dep, enseignant_id=ens_id, departement=request.departement, annee_univ=request.annee_courante
    )

    ens_dep.est_actif = True
    ens_dep.save(update_fields=["est_actif"])

    messages.success(request, "تم تنشيط الوصول بنجاح")
    return redirect("depa:list_enseignants_dep")
