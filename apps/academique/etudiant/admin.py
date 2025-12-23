# apps/academique/etudiant/admin.py

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.forms import ImportForm, ConfirmImportForm
from .models import Etudiant
from .utils import create_user_for_etudiant
from apps.academique.departement.models import NivSpeDep_SG


# ══════════════════════════════════════════════════════════════
# FORMULAIRES D'IMPORT PERSONNALISÉS
# ══════════════════════════════════════════════════════════════

class EtudiantImportForm(ImportForm):
    """Formulaire d'import avec sélection du NivSpeDep_SG."""
    niv_spe_dep_sg = forms.ModelChoiceField(
        queryset=NivSpeDep_SG.objects.select_related(
            'niv_spe_dep__niveau',
            'niv_spe_dep__specialite',
            'niv_spe_dep__departement'
        ).all(),
        required=True,
        label="المستوى، التخصص، القسم، والفوج / Niveau-Spé-Dép-SG",
        help_text="سيتم تطبيق هذا الاختيار على جميع الطلبة المستوردين / Ce choix sera appliqué à tous les étudiants importés"
    )

    def __init__(self, import_formats=None, *args, **kwargs):
        # Extraire queryset_filter s'il existe
        queryset_filter = kwargs.pop('queryset_filter', None)
        super().__init__(import_formats, *args, **kwargs)

        # Appliquer le filtre si fourni
        if queryset_filter:
            self.fields['niv_spe_dep_sg'].queryset = NivSpeDep_SG.objects.filter(
                **queryset_filter
            ).select_related(
                'niv_spe_dep__niveau',
                'niv_spe_dep__specialite',
                'niv_spe_dep__departement'
            )


class EtudiantConfirmImportForm(ConfirmImportForm):
    """Formulaire de confirmation d'import avec le NivSpeDep_SG."""
    niv_spe_dep_sg = forms.ModelChoiceField(
        queryset=NivSpeDep_SG.objects.all(),
        required=True,
        widget=forms.HiddenInput()
    )


# ══════════════════════════════════════════════════════════════
# RESOURCES POUR IMPORT/EXPORT
# ══════════════════════════════════════════════════════════════

class EtudiantResource(resources.ModelResource):
    """Resource pour l'import/export Excel des étudiants."""

    def __init__(self, niv_spe_dep_sg=None, **kwargs):
        super().__init__(**kwargs)
        self.niv_spe_dep_sg = niv_spe_dep_sg

    def before_import_row(self, row, **kwargs):
        """Applique le NivSpeDep_SG sélectionné à chaque ligne importée."""
        if self.niv_spe_dep_sg:
            row['niv_spe_dep_sg'] = self.niv_spe_dep_sg.id

        # Convertir num_ins vide en None pour éviter les violations de contrainte unique
        if 'num_ins' in row and (row['num_ins'] == '' or row['num_ins'] is None):
            row['num_ins'] = None

    def after_import_row(self, row, row_result, **kwargs):
        """
        Crée automatiquement un utilisateur pour chaque étudiant importé.
        """
        if row_result.object_id:
            try:
                etudiant = Etudiant.objects.get(pk=row_result.object_id)
                if not etudiant.user:
                    create_user_for_etudiant(etudiant)
            except Etudiant.DoesNotExist:
                pass

    class Meta:
        model = Etudiant
        fields = (
            'id', 'civilite', 'matricule', 'nom_fr', 'prenom_fr', 'nom_ar', 'prenom_ar',
            'date_nais', 'sexe', 'sit_fam',
            'num_ins', 'bac_annee', 'niv_spe_dep_sg', 'delegue',
            'tel_mobile1', 'tel_mobile2', 'tel_fix', 'fax',
            'email_perso', 'email_prof', 'adresse', 'wilaya',
            'inscrit_progres', 'inscrit_moodle', 'inscrit_sndl', 'est_inscrit',
            'google_scholar', 'researchgate', 'orcid_id',
            'linkedin', 'facebook', 'x_twitter', 'tiktok', 'telegram',
            'en_vac_aca', 'en_maladie', 'est_actif',
            'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['matricule']  # Utiliser matricule comme identifiant unique
        skip_unchanged = True
        report_skipped = True


# ══════════════════════════════════════════════════════════════
# ADMIN ETUDIANT
# ══════════════════════════════════════════════════════════════

@admin.register(Etudiant)
class EtudiantAdmin(ImportExportModelAdmin):
    """Administration des étudiants avec import/export Excel."""

    resource_class = EtudiantResource
    import_form_class = EtudiantImportForm
    confirm_form_class = EtudiantConfirmImportForm

    # Template personnalisé pour l'import avec statistiques
    import_template_name = 'admin/etudiant/etudiant/import.html'

    def get_import_form_class(self, request):
        """Retourne le formulaire d'import personnalisé."""
        return EtudiantImportForm

    def get_confirm_form_class(self, request):
        """Retourne le formulaire de confirmation personnalisé."""
        return EtudiantConfirmImportForm

    def get_import_form_kwargs(self, request, *args, **kwargs):
        """Ajoute la request au formulaire pour filtrer par département."""
        form_kwargs = super().get_import_form_kwargs(request, *args, **kwargs)
        # Filtrer les NivSpeDep_SG par département si non superuser
        if not request.user.is_superuser:
            departement_id = request.session.get('selected_departement_id')
            if departement_id:
                form_kwargs['queryset_filter'] = {'niv_spe_dep__departement_id': departement_id}
        return form_kwargs

    def get_confirm_form_initial(self, request, import_form):
        """Passe le NivSpeDep_SG sélectionné au formulaire de confirmation."""
        initial = super().get_confirm_form_initial(request, import_form)
        if import_form and import_form.is_valid():
            initial['niv_spe_dep_sg'] = import_form.cleaned_data.get('niv_spe_dep_sg')
        return initial

    def get_resource_kwargs(self, request, *args, **kwargs):
        """Passe le NivSpeDep_SG sélectionné à la ressource."""
        resource_kwargs = super().get_resource_kwargs(request, *args, **kwargs)

        # Récupérer le niv_spe_dep_sg depuis le formulaire POST
        if request.method == 'POST':
            niv_spe_dep_sg_id = request.POST.get('niv_spe_dep_sg')
            if niv_spe_dep_sg_id:
                try:
                    niv_spe_dep_sg = NivSpeDep_SG.objects.get(id=niv_spe_dep_sg_id)
                    resource_kwargs['niv_spe_dep_sg'] = niv_spe_dep_sg
                except NivSpeDep_SG.DoesNotExist:
                    pass

        return resource_kwargs

    list_display = (
        'matricule',
        'nom_fr',
        'prenom_fr',
        'nom_ar',
        'prenom_ar',
        'delegue',
        'get_status_display',
        'get_user_creation_button',
    )

    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
        'est_actif',
        'delegue',
        'sexe',
        'sit_fam',
        'niv_spe_dep_sg__niv_spe_dep__niveau',
        'niv_spe_dep_sg__niv_spe_dep__specialite',
        'niv_spe_dep_sg__niv_spe_dep__departement',
        'wilaya',
        'en_vac_aca',
        'en_maladie',
        'inscrit_progres',
        'inscrit_moodle',
        'inscrit_sndl',
        'est_inscrit',
    )

    search_fields = (
        'matricule',
        'num_ins',
        'nom_ar',
        'nom_fr',
        'prenom_ar',
        'prenom_fr',
        'email_prof',
        'email_perso',
        'tel_mobile1',
        'tel_mobile2',
        'user__username',
        'user__email'
    )

    # Tri par défaut: nom_fr, prenom_fr, nom_ar, prenom_ar
    ordering = ('nom_fr', 'prenom_fr', 'nom_ar', 'prenom_ar')

    # Template personnalisé pour la liste avec statistiques
    change_list_template = 'admin/etudiant/etudiant/change_list.html'

    readonly_fields = (
        'created_at',
        'updated_at',
        'get_user_link',
    )

    fieldsets = (
        ('المستخدم / Utilisateur', {
            'fields': ('get_user_link',),
            'description': 'Compte utilisateur lié à cet étudiant'
        }),
        ('معلومات شخصية / Informations personnelles', {
            'fields': (
                'civilite',
                ('nom_ar', 'prenom_ar'),
                ('nom_fr', 'prenom_fr'),
                'date_nais',
                'sexe',
                'sit_fam'
            )
        }),
        ('معلومات أكاديمية / Informations académiques', {
            'fields': (
                'matricule',
                'num_ins',
                'bac_annee',
                'niv_spe_dep_sg',
                'delegue'
            )
        }),
        ('معلومات الاتصال / Coordonnées', {
            'fields': (
                ('tel_mobile1', 'tel_mobile2'),
                'tel_fix',
                'fax',
                'email_prof',
                'email_perso',
                'adresse',
                'wilaya'
            )
        }),
        ('المنصات الأكاديمية / Plateformes académiques', {
            'fields': (
                'inscrit_progres',
                'inscrit_moodle',
                'inscrit_sndl',
                'est_inscrit'
            )
        }),
        ('الشبكات الاجتماعية والأكاديمية / Réseaux sociaux et académiques', {
            'fields': (
                'google_scholar',
                'researchgate',
                'orcid_id',
                'linkedin',
                'facebook',
                'x_twitter',
                'tiktok',
                'telegram'
            ),
            'classes': ('collapse',)
        }),
        ('الحالة / Statut', {
            'fields': (
                'est_actif',
                'en_vac_aca',
                'en_maladie'
            )
        }),
        ('الملاحظات / Observations', {
            'fields': ('observation',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام / Informations système', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def get_nom_display(self, obj):
        """Affichage bilingue du nom complet."""
        nom_ar = f"{obj.nom_ar} {obj.prenom_ar}".strip() if obj.nom_ar and obj.prenom_ar else ""
        nom_fr = f"{obj.nom_fr} {obj.prenom_fr}".strip() if obj.nom_fr and obj.prenom_fr else ""

        if nom_ar and nom_fr:
            return f"{nom_ar} / {nom_fr}"
        return nom_ar or nom_fr or obj.matricule
    get_nom_display.short_description = "الاسم / Nom"

    def get_niveau_display(self, obj):
        """Affichage du niveau-spécialité-département-SG."""
        return obj.get_niveau_info()
    get_niveau_display.short_description = "المستوى / Niveau"

    def get_status_display(self, obj):
        """Affichage du statut."""
        statuses = []
        if obj.en_vac_aca:
            statuses.append("عطلة أكاديمية")
        if obj.en_maladie:
            statuses.append("عطلة مرضية")
        if obj.delegue:
            statuses.append("مندوب")
        return " / ".join(statuses) if statuses else "نشط"
    get_status_display.short_description = "الحالة / Statut"

    def get_user_link(self, obj):
        """Affiche les informations de l'utilisateur avec lien vers la modification."""
        if obj.user:
            user = obj.user
            status_icon = '✅' if user.is_active else '❌'
            status_text = 'نشط / Actif' if user.is_active else 'غير نشط / Inactif'
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'لم يسجل الدخول بعد'

            return format_html(
                '<div style="background: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #e0e0e0;">'
                '<div style="margin-bottom: 8px;">'
                '<strong style="color: #417690; font-size: 14px;">👤 {}</strong>'
                '<span style="margin-right: 10px; color: #666;"> - {}</span>'
                '</div>'
                '<table style="font-size: 12px; width: 100%;">'
                '<tr><td style="color: #888; width: 120px;">اسم المستخدم:</td><td><strong>{}</strong></td></tr>'
                '<tr><td style="color: #888;">البريد الإلكتروني:</td><td>{}</td></tr>'
                '<tr><td style="color: #888;">الحالة:</td><td>{} {}</td></tr>'
                '<tr><td style="color: #888;">آخر دخول:</td><td>{}</td></tr>'
                '</table>'
                '</div>',
                user.nom_complet,
                user.username,
                user.username,
                user.email or '-',
                status_icon,
                status_text,
                last_login
            )
        return format_html(
            '<span style="color: #999; padding: 10px; display: block;">'
            '⚠️ لا يوجد حساب مرتبط / Aucun compte lié</span>'
        )
    get_user_link.short_description = "المستخدم / Utilisateur"
    get_user_link.allow_tags = True

    def get_user_creation_button(self, obj):
        """Affiche le nom d'utilisateur ou un bouton pour créer un utilisateur."""
        if obj.user:
            from django.utils.html import format_html
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ {}</span>',
                obj.user.username
            )
        else:
            from django.utils.html import format_html
            from django.urls import reverse
            url = reverse('admin:etudiant_create_user', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Créer utilisateur</a>',
                url
            )
    get_user_creation_button.short_description = "Utilisateur"
    get_user_creation_button.allow_tags = True

    def save_model(self, request, obj, form, change):
        """
        Override save_model pour créer automatiquement un utilisateur
        lors de l'ajout d'un étudiant.
        """
        # Sauvegarder l'étudiant d'abord
        super().save_model(request, obj, form, change)

        # Si c'est une création (pas une modification) ou si pas d'utilisateur
        if not change or not obj.user:
            user = create_user_for_etudiant(obj)
            if user:
                self.message_user(
                    request,
                    f"Utilisateur créé automatiquement - Login: {user.username}",
                    messages.SUCCESS
                )

    def get_urls(self):
        """Ajoute une URL personnalisée pour créer un utilisateur."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:etudiant_id>/create-user/',
                self.admin_site.admin_view(self.create_user_view),
                name='etudiant_create_user',
            ),
        ]
        return custom_urls + urls

    def create_user_view(self, request, etudiant_id):
        """Vue pour créer un utilisateur pour un étudiant."""
        from django.shortcuts import redirect
        from django.contrib import messages as django_messages

        try:
            etudiant = Etudiant.objects.get(pk=etudiant_id)

            if etudiant.user:
                django_messages.warning(request, "Cet étudiant a déjà un utilisateur.")
            else:
                user = create_user_for_etudiant(etudiant)
                if user:
                    django_messages.success(
                        request,
                        f"Utilisateur créé avec succès - Login: {user.username}, Mot de passe: (voir utils.py)"
                    )
                else:
                    django_messages.error(request, "Erreur lors de la création de l'utilisateur.")

        except Etudiant.DoesNotExist:
            django_messages.error(request, "Étudiant introuvable.")

        return redirect('admin:etudiant_etudiant_changelist')

    def get_queryset(self, request):
        """
        Filtre les étudiants par département pour les non-superusers.
        Les chefs de département ne voient que les étudiants de leur département.
        """
        qs = super().get_queryset(request)

        # Les superusers voient tout
        if request.user.is_superuser:
            return qs

        # Pour les autres, filtrer par département
        departement_id = request.session.get('selected_departement_id')
        if departement_id:
            return qs.filter(
                niv_spe_dep_sg__niv_spe_dep__departement_id=departement_id
            )

        return qs.none()

    def changelist_view(self, request, extra_context=None):
        """Ajoute les statistiques au contexte de la liste."""
        extra_context = extra_context or {}

        # Récupérer le queryset filtré
        qs = self.get_queryset(request)

        # Statistiques générales
        total = qs.count()
        total_actifs = qs.filter(est_actif=True).count()
        total_inactifs = total - total_actifs

        # Statistiques par sexe
        stats_sexe = qs.values('sexe').annotate(count=Count('id'))
        hommes = next((s['count'] for s in stats_sexe if s['sexe'] == 'ذكر'), 0)
        femmes = next((s['count'] for s in stats_sexe if s['sexe'] == 'أنثى'), 0)

        # Statistiques par statut
        delegues = qs.filter(delegue=True).count()
        en_vacances = qs.filter(en_vac_aca=True).count()
        en_maladie = qs.filter(en_maladie=True).count()
        inscrits = qs.filter(est_inscrit=True).count()

        # Statistiques utilisateurs
        avec_compte = qs.filter(user__isnull=False).count()
        sans_compte = total - avec_compte

        # Pourcentages
        pct_hommes = round((hommes / total * 100), 1) if total > 0 else 0
        pct_femmes = round((femmes / total * 100), 1) if total > 0 else 0
        pct_actifs = round((total_actifs / total * 100), 1) if total > 0 else 0
        pct_avec_compte = round((avec_compte / total * 100), 1) if total > 0 else 0

        extra_context['etudiant_stats'] = {
            'total': total,
            'total_actifs': total_actifs,
            'total_inactifs': total_inactifs,
            'hommes': hommes,
            'femmes': femmes,
            'pct_hommes': pct_hommes,
            'pct_femmes': pct_femmes,
            'pct_actifs': pct_actifs,
            'delegues': delegues,
            'en_vacances': en_vacances,
            'en_maladie': en_maladie,
            'inscrits': inscrits,
            'avec_compte': avec_compte,
            'sans_compte': sans_compte,
            'pct_avec_compte': pct_avec_compte,
        }

        return super().changelist_view(request, extra_context=extra_context)
