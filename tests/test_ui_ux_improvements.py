import pytest
from django.conf import settings
from django.contrib import admin
from django.urls import reverse

from tests.factories import DepartementFactory, SpecialiteFactory, UserFactory


@pytest.mark.django_db
class TestUiUxImprovements:
    """Tests automatisés pour les améliorations UI/UX et la navigation SAP Tree."""

    def test_point1_login_error_message_tagged_danger(self, client):
        """Point 1: Le message d'erreur d'authentification utilise le tag danger/rouge."""
        response = client.post(
            reverse("auth:login"),
            {"username": "non_existent_user", "password": "WrongPassword123!"},
        )
        assert response.status_code == 200
        # Vérifier que le message d'erreur est affiché avec le style rouge
        content = response.content.decode("utf-8")
        assert "alert-auth-danger" in content or "alert-danger" in content
        assert "اسم المستخدم أو كلمة المرور غير صحيحة" in content

    def test_point2_django_admin_french_and_custom_header(self):
        """Point 2: L'administration Django est en français et sans 'إدارة جانغو'."""
        assert settings.LANGUAGE_CODE == "fr"
        assert admin.site.site_header == "Administration Smart-Univ"
        assert admin.site.site_title == "Smart-Univ Admin"

    def test_point3_sidebar_does_not_contain_profile_menu_item(self, client):
        """Point 3: [الملف الشخصي] n'est plus présent dans le menu vertical latéral."""
        user = UserFactory()
        dep = DepartementFactory()
        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        response = client.get(reverse("depa:dashboard_Dep"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Le sidebar tree ne doit pas contenir الملف الشخصي comme lien de menu
        assert '<a class="sap-tree-item" href="/departement/profile/">' not in content
        assert '<a class="sap-tree-leaf" href="/departement/profile/">' not in content

    def test_point4_return_dashboard_button_present_on_pages(self, client):
        """Point 4: Le bouton de retour au tableau de bord est présent et accessible."""
        user = UserFactory()
        dep = DepartementFactory()
        SpecialiteFactory(departement=dep)
        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        # Sur la page des spécialités
        response = client.get(reverse("depa:list_Specialite_Dep"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Bouton dans la barre d'action et dans le shell top navbar
        assert "btn-return-dashboard" in content or "btn-shell-home" in content
        assert reverse("depa:dashboard_Dep") in content

    def test_point5_compact_role_switcher_present_in_sidebar_footer(self, client):
        """Point 5: La section de basculement de poste est présente en bas du menu latéral."""
        user = UserFactory()
        dep = DepartementFactory()
        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        response = client.get(reverse("depa:dashboard_Dep"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "compact-role-box" in content
        assert "المنصب النشط" in content

    def test_point6_select_role_instant_click_submission(self, client):
        """Point 6: La page select-role dispose du script et balisage pour soumission immédiate au clic."""
        user = UserFactory()
        client.force_login(user)

        # Simuler plusieurs rôles en session
        session = client.session
        session["roles_count"] = 2
        session.save()

        response = client.get(reverse("auth:select_role"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "1-Click Role Selection" in content
        assert "roleForm" in content

    def test_faculte_nom_complet_ar_prepends_kulliya(self):
        """Vérifie que nom_complet_ar ajoute 'كلية' si absent et ne double pas si présent."""
        from apps.academique.faculte.models import Faculte

        f1 = Faculte(nom_ar="المحروقات والطاقات المتجددة وعلوم الأرض والكون")
        assert f1.nom_complet_ar == "كلية المحروقات والطاقات المتجددة وعلوم الأرض والكون"

        f2 = Faculte(nom_ar="كلية العلوم الدقيقة والتطبيقية")
        assert f2.nom_complet_ar == "كلية العلوم الدقيقة والتطبيقية"

        f3 = Faculte(nom_ar="")
        assert f3.nom_complet_ar == ""

    def test_auth_roles_context_processor(self, rf):
        """Vérifie que auth_roles_context fournit un titre précis sans fallback générique عضو/مستخدم."""
        from apps.noyau.authentification.constants import ROLE_CHEF_DEP, ROLE_ENSEIGNANT, ROLE_ETUDIANT
        from apps.noyau.authentification.context_processors import auth_roles_context

        user = UserFactory()
        request = rf.get("/")
        request.user = user
        request.session = {"current_role": ROLE_CHEF_DEP, "roles_count": 2}

        ctx = auth_roles_context(request)
        assert ctx["current_role_title"] == "رئيس القسم"
        assert ctx["current_role"] == ROLE_CHEF_DEP
        assert ctx["roles_count"] == 2

        # Rôle enseignant
        request.session = {"current_role": ROLE_ENSEIGNANT}
        ctx_ens = auth_roles_context(request)
        assert ctx_ens["current_role_title"] == "أستاذ"

        # Rôle étudiant
        request.session = {"current_role": ROLE_ETUDIANT}
        ctx_etud = auth_roles_context(request)
        assert ctx_etud["current_role_title"] == "طالب"

    def test_dashboard_no_erp_branding_and_no_generic_fallback(self, client):
        """Vérifie l'absence de 'ERP' dans l'en-tête et l'absence de 'عضو' ou 'مستخدم' par défaut."""
        user = UserFactory(first_name="أحمد", last_name="غالي")
        dep = DepartementFactory()
        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        response = client.get(reverse("depa:dashboard_Dep"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Pas de badge ERP
        assert "Smart-Univ ERP" not in content
        assert '<span class="erp-badge">ERP</span>' not in content

        # Pas de mention générique عضو ou مستخدم
        assert ">عضو<" not in content
        assert ">مستخدم<" not in content

    def test_dashboard_dep_modern_hero_and_faculty_prefix(self, client):
        """Vérifie la présence de la bannière Hero, du préfixe كلية et l'absence de l'ancien format brut."""
        user = UserFactory(first_name="أحمد", last_name="غالي")
        dep = DepartementFactory()
        client.force_login(user)
        session = client.session
        session["selected_departement_id"] = dep.id
        session.save()

        response = client.get(reverse("depa:dashboard_Dep"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Bannière Hero moderne et cartes KPI
        assert "dep-hero-banner" in content
        assert "kpi-stat-card" in content
        assert "actions-grid-modern" in content

        # Présence de 'كلية' dans l'intitulé de la faculté
        if dep.faculte and dep.faculte.nom_ar:
            assert dep.faculte.nom_complet_ar in content
            assert "كلية" in content

        # Absence de l'ancien format brut
        assert "القسم الحالي:" not in content
