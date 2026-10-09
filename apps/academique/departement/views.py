# apps/academique/departement/views.py
"""
Vues du département - Version optimisée.
"""

import logging
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import Length
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.academique.affectation.models import Amphi_Dep, Classe, Ens_Dep, Laboratoire_Dep, Salle_Dep, Seance
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.constants import ROLE_LABELS
from apps.noyau.authentification.utils import get_user_roles
from apps.noyau.commun.models import AffectationPoste, AnneeUniversitaire, PostePermission, Semestre

from .forms import DepartementForm
from .models import Departement, Matiere, Specialite

logger = logging.getLogger(__name__)

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
    """Décorateur qui injecte le département dans la vue et vérifie les droits d'administration."""

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

        # Vérification d'accès : les pages de gestion du département sont réservées à l'administration
        if not request.user.is_superuser:
            current_role = request.session.get("current_role", "")
            admin_roles = ["chef_departement", "chef_dep_adj_p", "chef_dep_adj_pg", "doyen", "recteur"]
            has_admin_role = current_role in admin_roles
            has_admin_poste = AffectationPoste.actives(request.user).filter(
                niveau_contexte=AffectationPoste.NIVEAU_DEPARTEMENT,
                departement=departement,
            ).exists()
            perms = PostePermission.get_permissions(request)
            has_view_perm = any(perms.get(k, False) for k in perms.keys() if k.endswith("_view"))

            if not has_admin_role and not has_admin_poste and not has_view_perm:
                messages.warning(
                    request,
                    "صفحات إدارة القسم مخصصة لرئيس القسم والإدارة فقط. تم توجيهك إلى فضائك كأستاذ."
                )
                if hasattr(request.user, "enseignant_profile") and request.user.enseignant_profile:
                    return redirect("ense:dashboard_Ens", dep_id=departement.id)
                return redirect("auth:dashboard")

        request.departement = departement
        request.annee_courante = AnneeUniversitaire.objects.filter(est_courante=True).first()
        return view_func(request, *args, **kwargs)

    return wrapper


def get_dep_sidebar_context(request, departement):
    """
    Retourne le contexte commun pour le menu latéral département.
    À utiliser dans toutes les vues département pour avoir un sidebar cohérent.
    """
    annee_courante = getattr(request, "annee_courante", None)
    if not annee_courante:
        annee_courante = AnneeUniversitaire.objects.filter(est_courante=True).first()

    user_roles = get_user_roles(request.user) if request.user.is_authenticated else []
    current_role = request.session.get("current_role", "")
    current_role_label = ROLE_LABELS.get(current_role, current_role)

    # Récupérer les postes actifs de l'utilisateur
    user_postes = []
    if request.user.is_authenticated:
        user_postes = list(AffectationPoste.actives(request.user).select_related("poste", "departement"))

    is_doyen_or_above = False
    if request.user.is_authenticated:
        is_doyen_or_above = (
            request.user.is_superuser
            or current_role in ["doyen", "vice_doyen_p", "vice_doyen_pg", "recteur", "vice_rect_p", "vice_rect_pg"]
            or AffectationPoste.actives(request.user).filter(
                poste__code__in=["doyen", "vice_doyen_p", "vice_doyen_pg", "recteur", "vice_rect_p", "vice_rect_pg"]
            ).exists()
        )

    context = {
        "my_Dep": departement,
        "my_Fac": departement.faculte if departement else None,
        "departement": departement,
        "active_menu": "dashboard",
        "annee_courante": annee_courante,
        "user_roles": user_roles,
        "roles_count": len(user_roles),
        "current_role": current_role,
        "current_role_label": current_role_label,
        "user_postes": user_postes,
        "is_doyen_or_above": is_doyen_or_above,
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
        stats["total_students"] = (
            Etudiant.objects.filter(niv_spe_dep_sg__niv_spe_dep__departement=self.departement).distinct().count()
        )
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
            enseignant__departement=self.departement, enseignant__annee_univ=self.annee
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
        logger.exception("Erreur lors du calcul des statistiques du département")
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

    # Responsables du département : lus depuis les postes attribués (Affectations de postes)
    postes_direction = ["chef_departement", "chef_dep_adj_p", "chef_dep_adj_pg"]
    responsables = sorted(
        (
            AffectationPoste.objects.filter(
                departement=request.departement, poste__code__in=postes_direction, est_actif=True
            )
            .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=timezone.localdate()))
            .select_related("poste", "user", "user__enseignant_profile")
        ),
        key=lambda a: postes_direction.index(a.poste.code),
    )

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "لوحة التحكم",
            "active_menu": "dashboard",
            "responsables": responsables,
            "stats": stats,
            **stats,  # Pour compatibilité avec les anciens templates
        }
    )
    return render(request, "departement/dashboard_Dep.html", context)


@login_required
@with_departement
def profile_Dep(request):
    """Affiche le profil du département."""
    # Vérification d'accès : réservé aux chefs de département, administrateurs et superutilisateurs
    if not request.user.is_superuser:
        has_admin_poste = AffectationPoste.actives(request.user).filter(
            niveau_contexte=AffectationPoste.NIVEAU_DEPARTEMENT,
            departement=request.departement,
        ).exists()
        perms = PostePermission.get_permissions(request)
        if not has_admin_poste and not perms.get("departement_view", False):
            messages.warning(
                request,
                "صفحة إدارة القسم مخصصة لرئيس القسم والإدارة فقط. تم توجيهك إلى ملفك الشخصي كأستاذ."
            )
            return redirect("ense:profile_Ens")

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
    # Vérification stricte des droits de modification du département
    if not request.user.is_superuser:
        has_admin_poste = AffectationPoste.actives(request.user).filter(
            niveau_contexte=AffectationPoste.NIVEAU_DEPARTEMENT,
            departement=request.departement,
            poste__code__in=["chef_departement", "chef_dep_adj_p", "chef_dep_adj_pg"],
        ).exists()
        perms = PostePermission.get_permissions(request)
        if not has_admin_poste and not perms.get("departement_change", False):
            messages.error(
                request,
                "ليس لديك صلاحية تعديل بيانات هذا القسم. هذه العملية مخصصة لرئيس القسم والإدارة."
            )
            return redirect("ense:profile_Ens")

    if request.method == "POST":
        form = DepartementForm(request.POST, request.FILES, instance=request.departement)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث معلومات القسم بنجاح")
            return redirect("depa:profile_Dep")
    else:
        form = DepartementForm(instance=request.departement)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "تعديل الملف التعريفي للقسم",
            "active_menu": "profile",
            "form": form,
            "Dep_form": form,
        }
    )
    return render(request, "departement/profileUpdate_Dep.html", context)


@login_required
@with_departement
def list_enseignants_dep(request, semestre_num=1):
    """Liste des enseignants du département par semestre et statut."""
    # Validation stricte du semestre : seuls S1 et S2 existent
    if semestre_num not in [1, 2]:
        messages.warning(request, f"السداسي {semestre_num} غير متاح في النظام، تم تحويلك تلقائياً إلى السداسي الأول.")
        return redirect("depa:list_enseignants_dep", semestre_num=1)

    # Base queryset filtré par semestre (uniquement les enseignants actifs)
    sem_filter = {f"semestre_{semestre_num}": True}
    qs = Ens_Dep.objects.filter(
        departement=request.departement, annee_univ=request.annee_courante, est_actif=True, **sem_filter
    ).select_related("enseignant", "enseignant__grade", "enseignant__diplome", "enseignant__user")

    # Nombre d'enseignants archivés pour ce département
    archived_count = Ens_Dep.objects.filter(
        departement=request.departement, annee_univ=request.annee_courante, est_actif=False
    ).count()

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
            "archived_count": archived_count,
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
    """
    Ajout et recrutement d'enseignants dans le département:
    1. Importation / Affectation d'un enseignant depuis un autre département (statut devient Permanent & Vacataire).
    2. Création d'un nouvel enseignant pour le département (statut Permanent, Vacataire, etc.).
    """
    from apps.academique.enseignant.models import Enseignant
    from apps.academique.enseignant.utils import create_user_for_enseignant
    from apps.noyau.commun.models import Diplome, Grade

    annee = request.annee_courante or AnneeUniversitaire.objects.filter(est_courante=True).first()

    if request.method == "POST":
        action = request.POST.get("action", "import_teacher")

        if action == "import_teacher":
            enseignant_id = request.POST.get("enseignant_id")
            if not enseignant_id:
                messages.error(request, "يرجى تحديد الأستاذ المراد استقدامه للقسم.")
                return redirect("depa:new_Enseignant")

            enseignant = get_object_or_404(Enseignant, id=enseignant_id)
            semestre_1 = "semestre_1" in request.POST
            semestre_2 = "semestre_2" in request.POST
            observation = request.POST.get("observation", "").strip()

            # Statut choisi pour ce département (interdiction du statut 'Permanent' pur réservé au doyen)
            statut_demande = request.POST.get("statut", "").strip()
            if not statut_demande or statut_demande == Ens_Dep.StatutEnseignant.PERMANENT:
                statut_demande = Ens_Dep.StatutEnseignant.PERMANENT_VACATAIRE

            # Obtenir le département d'origine
            home_dep = enseignant.get_departement_origine(annee)
            origin_name = home_dep.nom_ar if home_dep else "قسم آخر"

            ens_dep, created = Ens_Dep.objects.get_or_create(
                enseignant=enseignant,
                departement=request.departement,
                annee_univ=annee,
                defaults={
                    "statut": statut_demande,
                    "est_actif": True,
                    "semestre_1": semestre_1,
                    "semestre_2": semestre_2,
                    "observation": observation or f"استقدام وانتداب تدريس من {origin_name}",
                },
            )
            if not created:
                ens_dep.statut = statut_demande
                ens_dep.est_actif = True
                ens_dep.semestre_1 = semestre_1
                ens_dep.semestre_2 = semestre_2
                if observation:
                    ens_dep.observation = observation
                ens_dep.save()

            messages.success(
                request,
                f"تم استقدام الأستاذ {enseignant.nom_ar} {enseignant.prenom_ar} من {origin_name} بنجاح، وتم تسجيله بالقسم بصفة ({ens_dep.get_statut_display()})."
            )
            return redirect("depa:list_enseignants_dep", semestre_num=1)

        elif action == "create_teacher":
            nom_ar = request.POST.get("nom_ar", "").strip()
            prenom_ar = request.POST.get("prenom_ar", "").strip()
            nom_fr = request.POST.get("nom_fr", "").strip()
            prenom_fr = request.POST.get("prenom_fr", "").strip()
            diplome_id = request.POST.get("diplome_id")
            specialite_ar = request.POST.get("specialite_ar", "").strip()
            specialite_fr = request.POST.get("specialite_fr", "").strip()
            email_prof = request.POST.get("email_prof", "").strip()
            statut = request.POST.get("statut", Ens_Dep.StatutEnseignant.VACATAIRE)
            semestre_1 = "semestre_1" in request.POST
            semestre_2 = "semestre_2" in request.POST
            observation = request.POST.get("observation", "").strip()

            # Vérification des prérogatives : le statut Permanent est strictement réservé au Doyen
            if statut == Ens_Dep.StatutEnseignant.PERMANENT:
                messages.error(
                    request,
                    "تسجيل وتعيين أستاذ مرسم (دائم / Permanent) بالقسم هو من الصلاحيات الحصرية للسيد عميد الكلية. يمكن لرئيس القسم فقط تسجيل الأساتذة غير الدائمين (مؤقت، مشارك، طالب دكتوراه) أو استقدام الأساتذة من الأقسام والكليات الأخرى."
                )
                return redirect("depa:new_Enseignant")

            # Autoriser uniquement les statuts non permanents pour le département
            allowed_statuts = [
                Ens_Dep.StatutEnseignant.VACATAIRE,
                Ens_Dep.StatutEnseignant.ASSOCIE,
                Ens_Dep.StatutEnseignant.DOCTORANT,
            ]
            if statut not in allowed_statuts:
                statut = Ens_Dep.StatutEnseignant.VACATAIRE

            if not (nom_ar and prenom_ar) and not (nom_fr and prenom_fr):
                messages.error(request, "يرجى إدخال اسم ولقب الأستاذ على الأقل.")
                return redirect("depa:new_Enseignant")

            # Les candidats non permanents ont un diplôme et non un grade académique
            diplome = Diplome.objects.filter(id=diplome_id).first() if diplome_id else None

            new_ens = Enseignant.objects.create(
                nom_ar=nom_ar,
                prenom_ar=prenom_ar,
                nom_fr=nom_fr,
                prenom_fr=prenom_fr,
                diplome=diplome,
                grade=None,  # Pas de grade académique pour les candidats non permanents
                specialite_ar=specialite_ar,
                specialite_fr=specialite_fr,
                email_prof=email_prof,
                est_inscrit=True,
            )
            user, _err = create_user_for_enseignant(new_ens)

            Ens_Dep.objects.create(
                enseignant=new_ens,
                departement=request.departement,
                annee_univ=annee,
                statut=statut,
                est_actif=True,
                semestre_1=semestre_1,
                semestre_2=semestre_2,
                observation=observation,
            )
            messages.success(
                request,
                f"تم تسجيل الأستاذ غير الدائم {new_ens.nom_ar} {new_ens.prenom_ar} وتعيينه بالقسم بصفة ({Ens_Dep.StatutEnseignant(statut).label}) بنجاح."
            )
            if user:
                # Identifiants affichés une seule fois sur la page suivante (le mot de passe n'est pas relisible)
                request.session["nouveau_compte_enseignant"] = {
                    "nom": f"{new_ens.nom_ar} {new_ens.prenom_ar}".strip() or f"{new_ens.nom_fr} {new_ens.prenom_fr}",
                    "login": user.username,
                    "mot_de_passe": user._generated_password,
                }
            return redirect("depa:new_Enseignant")

    # Récupérer les enseignants déjà actifs dans ce département pour l'année courante
    assigned_ids = Ens_Dep.objects.filter(
        departement=request.departement,
        annee_univ=annee,
        est_actif=True,
    ).values_list("enseignant_id", flat=True)

    other_teachers_qs = (
        Enseignant.objects.exclude(id__in=assigned_ids)
        .select_related("grade", "diplome")
        .order_by("nom_ar", "prenom_ar")
    )

    # Récupérer la liste des enseignants archivés pour ce département
    archived_teachers_qs = (
        Ens_Dep.objects.filter(
            departement=request.departement,
            annee_univ=annee,
            est_actif=False,
        )
        .select_related("enseignant", "enseignant__grade", "enseignant__diplome")
        .order_by("-updated_at")
    )
    archived_ens_ids = set(archived_teachers_qs.values_list("enseignant_id", flat=True))

    other_teachers_list = []
    for t in other_teachers_qs:
        home_dep = t.get_departement_origine(annee)
        origin_aff = None
        if not home_dep:
            origin_aff = (
                t.affectations_departement.filter(annee_univ=annee, est_actif=True)
                .select_related("departement", "departement__faculte")
                .first()
            )
            home_dep = origin_aff.departement if origin_aff else None
        else:
            origin_aff = (
                t.affectations_departement.filter(
                    departement=home_dep, annee_univ=annee, est_actif=True
                ).first()
            )

        origin_statut = origin_aff.statut if origin_aff else Ens_Dep.StatutEnseignant.PERMANENT
        origin_statut_display = origin_aff.get_statut_display() if origin_aff else "مرسم"

        home_fac = getattr(home_dep, "faculte", None)
        is_same_faculty = bool(
            home_fac and request.departement.faculte_id and home_fac.id == request.departement.faculte_id
        )

        # Statut suggéré selon l'état d'origine
        if origin_statut == Ens_Dep.StatutEnseignant.PERMANENT:
            suggested_statut = Ens_Dep.StatutEnseignant.PERMANENT_VACATAIRE
        else:
            suggested_statut = origin_statut

        other_teachers_list.append(
            {
                "enseignant": t,
                "home_dep": home_dep,
                "home_faculte": home_fac,
                "is_same_faculty": is_same_faculty,
                "is_previously_archived": t.id in archived_ens_ids,
                "origin_statut": origin_statut,
                "origin_statut_display": origin_statut_display,
                "suggested_statut": suggested_statut,
                "initiales": t.initiales,
            }
        )

    # Départements de la même faculté
    departements_meme_fac = (
        Departement.objects.filter(faculte=request.departement.faculte)
        .exclude(id=request.departement.id)
        .order_by("nom_ar")
    )

    # Départements des autres facultés
    departements_autres_facs = (
        Departement.objects.exclude(faculte=request.departement.faculte)
        .select_related("faculte")
        .order_by("faculte__nom_ar", "nom_ar")
    )

    other_departements = (
        Departement.objects.exclude(id=request.departement.id)
        .select_related("faculte")
        .order_by("faculte__nom_ar", "nom_ar")
    )

    diplomes = Diplome.objects.all().order_by("code")
    grades = Grade.objects.all().order_by("id")

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "استقدام وإضافة أستاذ للقسم",
            "active_menu": "new_enseignant",
            "other_teachers": other_teachers_list,
            "archived_teachers": archived_teachers_qs,
            "departements_meme_fac": departements_meme_fac,
            "departements_autres_facs": departements_autres_facs,
            "other_departements": other_departements,
            "diplomes": diplomes,
            "grades": grades,
            "annee_univ": annee,
            "nouveau_compte": request.session.pop("nouveau_compte_enseignant", None),
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


TIME_SLOTS = [
    "08:00-09:30",
    "09:40-11:10",
    "11:20-12:50",
    "13:10-14:40",
    "14:50-16:20",
    "16:30-18:00",
    "18:00-19:30",
    "19:40-21:10",
]

WEEK_DAYS = [
    ("Samedi", "السبت"),
    ("Dimanche", "الأحد"),
    ("Lundi", "الإثنين"),
    ("Mardi", "الثلاثاء"),
    ("Mercredi", "الأربعاء"),
    ("Jeudi", "الخميس"),
]


@login_required
@with_departement
def timetable_enseignant_dep(request, ens_id, semestre_num=1):
    """
    Affiche l'emploi du temps détaillé d'un enseignant spécifique du département.
    """
    if semestre_num not in [1, 2]:
        semestre_num = 1

    ens_dep = (
        Ens_Dep.objects.filter(departement=request.departement, enseignant_id=ens_id)
        .select_related("enseignant", "enseignant__grade", "enseignant__user")
        .first()
    )
    if not ens_dep:
        ens_dep = (
            Ens_Dep.objects.filter(departement=request.departement, id=ens_id)
            .select_related("enseignant", "enseignant__grade", "enseignant__user")
            .first()
        )

    if not ens_dep:
        messages.error(request, "الأستاذ غير مسجل في هذا القسم أو غير موجود.")
        return redirect("depa:list_enseignants_dep", semestre_num=semestre_num)

    enseignant = ens_dep.enseignant
    semestre_obj = Semestre.objects.filter(numero=str(semestre_num)).first()

    base_filter = {
        "enseignant__departement": request.departement.id,
        "enseignant__enseignant": enseignant.id,
    }
    if semestre_obj:
        base_filter["semestre"] = semestre_obj

    classes_qs = (
        Classe.objects.filter(**base_filter)
        .select_related(
            "matiere",
            "niv_spe_dep_sg__niv_spe_dep__specialite",
            "niv_spe_dep_sg__niv_spe_dep__niveau",
            "content_type",
        )
        .order_by("temps")
    )

    all_Classe_Ens = list(classes_qs)

    nbr_Cours = 0
    nbr_TD = 0
    nbr_TP = 0
    nbr_SS = 0

    for idx1 in all_Classe_Ens:
        if idx1.type == "Cours":
            nbr_Cours += 1
        elif idx1.type == "TD":
            nbr_TD += 1
        elif idx1.type == "TP":
            nbr_TP += 1
        elif idx1.type in ["Sortie", "Sortie Scientifique", "SS"]:
            nbr_SS += 1

        if idx1.seance_created:
            all_Seances = Seance.objects.filter(classe=idx1.id)
            nbr_Sea_fait = Seance.objects.filter(classe=idx1.id, fait=True)
            if nbr_Sea_fait.exists() and all_Seances.exists():
                taux_avancement = ((nbr_Sea_fait.count()) / all_Seances.count()) * 100
                idx1.taux_avancement = round(taux_avancement)

    all_classes = nbr_Cours + nbr_TP + nbr_TD + nbr_SS

    grid_rows = []
    for slot in TIME_SLOTS:
        row_days = []
        for day_code, day_label in WEEK_DAYS:
            matching = [c for c in all_Classe_Ens if c.temps == slot and c.jour == day_code]
            row_days.append({
                "code": day_code,
                "label": day_label,
                "classes": matching,
            })
        grid_rows.append({
            "slot": slot,
            "days": row_days,
        })

    if semestre_num == 1:
        stats_classes = {
            "total": getattr(ens_dep, "nbrClas_in_Dep_S1", 0) or all_classes,
            "cours": getattr(ens_dep, "nbrClas_Cours_in_Dep_S1", 0) or nbr_Cours,
            "td": getattr(ens_dep, "nbrClas_TD_in_Dep_S1", 0) or nbr_TD,
            "tp": getattr(ens_dep, "nbrClas_TP_in_Dep_S1", 0) or nbr_TP,
            "ss": getattr(ens_dep, "nbrClas_SS_in_Dep_S1", 0) or nbr_SS,
            "jours": getattr(ens_dep, "nbrJour_in_Dep_S1", 0) or len(set(c.jour for c in all_Classe_Ens)),
            "vol_horaire": getattr(ens_dep, "volHor_in_Dep_S1", 0) or (all_classes * 1.5),
        }
    else:
        stats_classes = {
            "total": getattr(ens_dep, "nbrClas_in_Dep_S2", 0) or all_classes,
            "cours": getattr(ens_dep, "nbrClas_Cours_in_Dep_S2", 0) or nbr_Cours,
            "td": getattr(ens_dep, "nbrClas_TD_in_Dep_S2", 0) or nbr_TD,
            "tp": getattr(ens_dep, "nbrClas_TP_in_Dep_S2", 0) or nbr_TP,
            "ss": getattr(ens_dep, "nbrClas_SS_in_Dep_S2", 0) or nbr_SS,
            "jours": getattr(ens_dep, "nbrJour_in_Dep_S2", 0) or len(set(c.jour for c in all_Classe_Ens)),
            "vol_horaire": getattr(ens_dep, "volHor_in_Dep_S2", 0) or (all_classes * 1.5),
        }

    all_teachers_dep = (
        Ens_Dep.objects.filter(
            departement=request.departement,
            annee_univ=request.annee_courante,
            **{f"semestre_{semestre_num}": True}
        )
        .select_related("enseignant")
        .order_by("enseignant__nom_ar")
    )

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": f"استعمال الزمن - {enseignant.nom_ar} {enseignant.prenom_ar}",
            "active_menu": "enseignants",
            "ens_dep": ens_dep,
            "enseignant": enseignant,
            "semestre_num": semestre_num,
            "semestre_obj": semestre_obj,
            "all_Classe_Ens": all_Classe_Ens,
            "all_classes": all_classes,
            "nbr_Cours": nbr_Cours,
            "nbr_TD": nbr_TD,
            "nbr_TP": nbr_TP,
            "nbr_SS": nbr_SS,
            "stats_classes": stats_classes,
            "grid_rows": grid_rows,
            "week_days": WEEK_DAYS,
            "all_teachers_dep": all_teachers_dep,
        }
    )
    return render(request, "departement/timetable_enseignant_dep.html", context)


@login_required
@with_departement
def list_etudiants(request):
    """Liste des étudiants avec pagination (A27)."""
    etudiants = Etudiant.objects.select_related(
        "niv_spe_dep_sg__niv_spe_dep__specialite", "niv_spe_dep_sg__niv_spe_dep__niveau"
    ).filter(niv_spe_dep_sg__niv_spe_dep__departement=request.departement)

    search = request.GET.get("q")
    if search:
        etudiants = etudiants.filter(
            Q(nom_ar__icontains=search) | Q(prenom_ar__icontains=search) | Q(matricule__icontains=search)
        )

    paginator = Paginator(etudiants.order_by("nom_ar"), 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة الطلبة",
            "active_menu": "etudiants",
            "etudiants": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
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
    """Liste des spécialités du département avec pagination (A27)."""
    specialites = (
        Specialite.objects.filter(departement=request.departement)
        .annotate(
            nb_matieres=Count("nivspedep__matieres", distinct=True),
            nb_etudiants=Count("nivspedep__sections_groupes__etudiants", distinct=True),
        )
        .order_by(Length("code"), "code", "id")
    )

    paginator = Paginator(specialites, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة التخصصات",
            "active_menu": "specialites",
            "specialites": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
        }
    )
    return render(request, "departement/list_Specialite_Dep.html", context)


@login_required
@with_departement
def list_Mat_Niv(request):
    """Liste des matières par niveau avec pagination (A27) - classée selon le code/numéro."""
    matieres = (
        Matiere.objects.filter(niv_spe_dep__specialite__departement=request.departement)
        .select_related("niv_spe_dep__specialite", "niv_spe_dep__niveau", "semestre")
        .order_by("semestre__numero", Length("code"), "code", "id")
        .distinct()
    )

    paginator = Paginator(matieres, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة المواد",
            "active_menu": "matieres",
            "matieres": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
        }
    )
    return render(request, "departement/list_Mat_Niv.html", context)


@login_required
@with_departement
def list_Amphi_Dep(request):
    """Liste des amphithéâtres alloués au département (الهياكل والمقررات) - classée selon le numéro."""
    amphis = (
        Amphi_Dep.objects.filter(departement=request.departement)
        .select_related("amphi")
        .order_by(Length("amphi__numero"), "amphi__numero")
    )
    total_amphis = amphis.count()
    amphis_s1 = amphis.filter(semestre_1=True, est_actif=True).count()
    amphis_s2 = amphis.filter(semestre_2=True, est_actif=True).count()
    capacite_totale = sum(a.amphi.capacite or 0 for a in amphis)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة المدرجات - الهياكل والمقررات",
            "active_menu": "amphis",
            "amphis": amphis,
            "total_amphis": total_amphis,
            "amphis_s1": amphis_s1,
            "amphis_s2": amphis_s2,
            "capacite_totale": capacite_totale,
        }
    )
    return render(request, "departement/list_Amphi_Dep.html", context)


@login_required
@with_departement
def list_Salle_Dep(request):
    """Liste des salles de cours allouées au département (الهياكل والمقررات) - classée selon le numéro."""
    salles = (
        Salle_Dep.objects.filter(departement=request.departement)
        .select_related("salle")
        .order_by(Length("salle__numero"), "salle__numero")
    )
    total_salles = salles.count()
    salles_s1 = salles.filter(semestre_1=True, est_actif=True).count()
    salles_s2 = salles.filter(semestre_2=True, est_actif=True).count()
    capacite_totale = sum(s.salle.capacite or 0 for s in salles)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة القاعات الدراسية - الهياكل والمقررات",
            "active_menu": "salles",
            "salles": salles,
            "total_salles": total_salles,
            "salles_s1": salles_s1,
            "salles_s2": salles_s2,
            "capacite_totale": capacite_totale,
        }
    )
    return render(request, "departement/list_Salle_Dep.html", context)


@login_required
@with_departement
def list_Labo_Dep(request):
    """Liste des laboratoires de TP alloués au département (الهياكل والمقررات) - classée selon le numéro."""
    labos = (
        Laboratoire_Dep.objects.filter(departement=request.departement)
        .select_related("laboratoire")
        .order_by(Length("laboratoire__numero"), "laboratoire__numero")
    )
    total_labos = labos.count()
    labos_s1 = labos.filter(semestre_1=True, est_actif=True).count()
    labos_s2 = labos.filter(semestre_2=True, est_actif=True).count()
    capacite_totale = sum(l.laboratoire.capacite or 0 for l in labos)

    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "قائمة المخابر - الهياكل والمقررات",
            "active_menu": "labos",
            "labos": labos,
            "total_labos": total_labos,
            "labos_s1": labos_s1,
            "labos_s2": labos_s2,
            "capacite_totale": capacite_totale,
        }
    )
    return render(request, "departement/list_Labo_Dep.html", context)


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
    if "annee_courante" in stats and stats["annee_courante"] is not None:
        stats["annee_courante"] = str(stats["annee_courante"])
    return JsonResponse(stats)


# ═══════════════════════════════════════════════════════════════════════════
# ACTIONS (DELETE, ACTIVATE, etc.)
# ═══════════════════════════════════════════════════════════════════════════


@login_required
@with_departement
def delete_Enseignant(request, ens_dep_id):
    """Supprime une affectation enseignant-département."""
    ens_dep = get_object_or_404(Ens_Dep, id=ens_dep_id, departement=request.departement)

    current_role = request.session.get("current_role", "")
    is_doyen_or_above = (
        request.user.is_superuser
        or current_role in ["doyen", "vice_doyen_p", "vice_doyen_pg", "recteur", "vice_rect_p", "vice_rect_pg"]
        or AffectationPoste.actives(request.user).filter(
            poste__code__in=["doyen", "vice_doyen_p", "vice_doyen_pg", "recteur", "vice_rect_p", "vice_rect_pg"]
        ).exists()
    )

    # Restriction statutaire : les enseignants permanents (مرسم) ne peuvent être supprimés que par le Doyen
    if ens_dep.statut == Ens_Dep.StatutEnseignant.PERMANENT and not is_doyen_or_above:
        messages.error(
            request,
            "عملية غير مصرح بها: لا يحق لرئيس القسم حذف أستاذ دائم (مرسم) من القسم. هذه الصلاحية مخولة قانونياً لعميد الكلية فقط."
        )
        referer = request.META.get("HTTP_REFERER")
        if referer and "/departement/enseignants/" in referer:
            return redirect(referer)
        return redirect("depa:list_enseignants_dep")

    if request.method == "POST":
        nom = f"{ens_dep.enseignant.nom_ar} {ens_dep.enseignant.prenom_ar}"
        # Archivage sécurisé pour ce département UNIQUEMENT :
        # 1. On ne supprime pas l'entité Enseignant
        # 2. Aucun autre département n'est affecté
        # 3. L'affectation de ce département passe à est_actif = False (archivé)
        ens_dep.est_actif = False
        today_str = timezone.now().strftime("%Y-%m-%d")
        note = f"أرشفة وإلغاء تعيين بالقسم بتاريخ {today_str}"
        ens_dep.observation = f"{ens_dep.observation or ''} - {note}".strip(" -")
        ens_dep.save(update_fields=["est_actif", "observation"])
        messages.success(
            request,
            f"تمت أرشفة الأستاذ {nom} وإلغاء تعيينه بقسم {request.departement.nom_ar} فقط بنجاح. ملف الأستاذ محفوظ في الأرشيف ويمكن استعادته في أي وقت دون التأثير على أي قسم آخر."
        )
    else:
        messages.warning(request, "يرجى تأكيد الحذف عبر النموذج المخصص.")

    referer = request.META.get("HTTP_REFERER")
    if referer and "/departement/enseignants/" in referer:
        return redirect(referer)
    return redirect("depa:list_enseignants_dep")


@login_required
@with_departement
def profile_enseignant_dep(request, ens_id):
    """Fiche d'un enseignant consultée depuis l'espace département (sans quitter cet espace).

    Réservée aux enseignants affectés (ou archivés) dans ce département.
    """
    from apps.academique.enseignant.models import Enseignant
    from apps.academique.enseignant.services import get_real_department

    enseignant = get_object_or_404(Enseignant, id=ens_id)
    if not Ens_Dep.objects.filter(enseignant=enseignant, departement=request.departement).exists():
        messages.error(request, "هذا الأستاذ غير معيّن بهذا القسم.")
        return redirect("depa:list_enseignants_dep", semestre_num=1)

    real_Dep = get_real_department(enseignant)
    context = get_dep_sidebar_context(request, request.departement)
    context.update(
        {
            "title": "ملف الأستاذ",
            "active_menu": "enseignants",
            "base_template": "departement/base_Dep.html",
            "in_departement": True,
            "my_Ens": enseignant,
            "enseignant": enseignant,
            "real_Dep": real_Dep,
            "ALL_Dep": Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True)
            .exclude(departement=real_Dep.departement if real_Dep else None)
            .select_related("departement", "departement__faculte"),
        }
    )
    return render(request, "enseignant/profile_Ens.html", context)


@login_required
@with_departement
def restore_Enseignant(request, ens_dep_id):
    """Restaure et réactive un enseignant archivé pour ce département."""
    ens_dep = get_object_or_404(Ens_Dep, id=ens_dep_id, departement=request.departement)
    if request.method == "POST":
        ens_dep.est_actif = True
        today_str = timezone.now().strftime("%Y-%m-%d")
        note = f"استعادة وتنشيط بالقسم بتاريخ {today_str}"
        ens_dep.observation = f"{ens_dep.observation or ''} - {note}".strip(" -")
        ens_dep.save(update_fields=["est_actif", "observation"])
        nom = f"{ens_dep.enseignant.nom_ar} {ens_dep.enseignant.prenom_ar}"
        messages.success(
            request,
            f"تمت استعادة وتنشيط الأستاذ {nom} بقسم {request.departement.nom_ar} بنجاح."
        )
    else:
        messages.warning(request, "يرجى تأكيد الاستعادة عبر النموذج المخصص.")

    referer = request.META.get("HTTP_REFERER")
    if referer and "/departement/enseignants/" in referer:
        return redirect(referer)
    return redirect("depa:new_Enseignant")


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
    referer = request.META.get("HTTP_REFERER")
    if referer and "/departement/enseignants/" in referer:
        return redirect(referer)
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
    referer = request.META.get("HTTP_REFERER")
    if referer and "/departement/enseignants/" in referer:
        return redirect(referer)
    return redirect("depa:list_enseignants_dep")


@login_required
@with_departement
def update_scholar_enseignant(request, ens_id):
    """
    Met à jour les métriques Google Scholar d'un enseignant (publications, citations, h-index, i10-index).
    Supporte les requêtes AJAX (JSON) et standard.
    """
    ens_dep = get_object_or_404(Ens_Dep, enseignant_id=ens_id, departement=request.departement)
    enseignant = ens_dep.enseignant

    from apps.academique.enseignant.services import fetch_and_update_scholar

    res = fetch_and_update_scholar(enseignant)

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json"
    if is_ajax:
        return JsonResponse(res)

    if res.get("success"):
        messages.success(request, res.get("message"))
    else:
        messages.warning(request, res.get("message"))

    referer = request.META.get("HTTP_REFERER")
    if referer and "/departement/enseignants/" in referer:
        return redirect(referer)
    return redirect("depa:list_enseignants_dep")

