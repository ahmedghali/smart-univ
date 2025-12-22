# Correction dans admin.py

from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin
from apps.noyau.authentification.models import CustomUser
from django.utils.translation import ngettext
from django.contrib import messages

# Register your models here.

@admin.register(Departement)
class DepartementAdmin(ImportExportModelAdmin):
    list_display = ('nom_ar', 'nom_fr', 'chef_departement', 'chef_dep_adj_p', 'chef_dep_adj_pg', 'faculte')
    search_fields = ('nom_ar', 'nom_fr')
    list_filter = ('faculte',)
    readonly_fields = ('date_creation', 'date_modification')

@admin.register(Specialite)
class SpecialiteAdmin(ImportExportModelAdmin):
    list_display = ('nom_ar', 'nom_fr', 'code', 'departement', 'reforme', 'identification', 'parcours')
    search_fields = ('nom_ar', 'nom_fr')
    list_filter = ('departement', 'reforme')
    readonly_fields = ('date_creation', 'date_modification')

@admin.register(NivSpeDep_SG)
class NivSpeDepSGAdmin(admin.ModelAdmin):
    list_display = ('niv_spe_dep', 'section', 'groupe', 'nbr_etudiants_SG', 'type_affectation')
    list_filter = ('type_affectation', 'niv_spe_dep__departement')
    search_fields = ('niv_spe_dep__niveau__nom_ar', 'niv_spe_dep__specialite__nom_ar')
    ordering = ('niv_spe_dep', 'section', 'groupe', 'type_affectation')
    
    # Ajout de fieldsets pour une meilleure organisation
    fieldsets = (
        ('Configuration de base', {
            'fields': ('niv_spe_dep', 'type_affectation')
        }),
        ('Affectation spécifique', {
            'fields': ('section', 'groupe', 'nbr_etudiants_SG'),
            'description': 'Sélectionnez selon le type d\'affectation choisi'
        }),
    )

@admin.register(NivSpeDep)
class NivSpeDepAdmin(admin.ModelAdmin):
    # list_display = ('niveau', 'specialite', 'departement')
    list_filter = ('niveau', 'specialite', 'departement')
    search_fields = ('niveau__nom_ar', 'specialite__nom_ar', 'departement__nom_ar')
    ordering = ('niveau', 'specialite', 'departement')

# CORRECTION: Supprimer readonly_fields qui n'existent pas dans le modèle Matiere
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom_ar', 'nom_fr', 'code', 'coeff', 'credit', 'niv_spe_dep', 'semestre', 'unite')
    search_fields = ('nom_ar', 'nom_fr', 'code')
    list_filter = ('niv_spe_dep__departement', 'niv_spe_dep__niveau', 'niv_spe_dep__specialite', 'semestre', 'unite')
    ordering = ('niv_spe_dep', 'semestre', 'code')
    
    # Ajout de fieldsets pour une meilleure organisation
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom_ar', 'nom_fr', 'code')
        }),
        ('Paramètres académiques', {
            'fields': ('coeff', 'credit', 'unite')
        }),
        ('Affectation', {
            'fields': ('niv_spe_dep', 'semestre')
        }),
    )
    
    # Optimisation des requêtes
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'niv_spe_dep', 
            'niv_spe_dep__niveau', 
            'niv_spe_dep__specialite', 
            'niv_spe_dep__departement',
            'semestre', 
            'unite'
        )
    
    # Méthode pour afficher le département dans la liste
    def get_departement(self, obj):
        return obj.niv_spe_dep.departement.nom_ar if obj.niv_spe_dep and obj.niv_spe_dep.departement else '-'
    get_departement.short_description = 'القسم'
    get_departement.admin_order_field = 'niv_spe_dep__departement__nom_ar'
    
    # Ajouter la méthode à list_display si vous le souhaitez
    # list_display = ('nom_ar', 'nom_fr', 'code', 'coeff', 'credit', 'get_departement', 'semestre', 'unite')

# SOLUTION ALTERNATIVE: Si votre modèle Matiere hérite bien de BaseModel
# et que les champs existent, utilisez cette version à la place :

"""
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom_ar', 'nom_fr', 'code', 'coeff', 'credit', 'niv_spe_dep', 'semestre', 'unite')
    search_fields = ('nom_ar', 'nom_fr', 'code')
    list_filter = ('niv_spe_dep__departement', 'semestre', 'unite')
    ordering = ('niv_spe_dep', 'semestre', 'code')
    
    # Vérifiez d'abord si ces champs existent dans votre modèle
    # readonly_fields = ('date_creation', 'date_modification')
"""

# VERIFICATION: Pour savoir quels champs existent dans votre modèle Matiere,
# vous pouvez utiliser cette commande dans le shell Django :
# python manage.py shell
# >>> from apps.academique.departement.models import Matiere
# >>> # print([field.name for field in Matiere._meta.fields])

# Configuration CustomUser (optionnelle)
"""
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    actions = ['delete_recent_users']

    def delete_recent_users(self, request, queryset):
        recent_users = CustomUser.objects.order_by('-date_joined')[:10]
        recent_user_ids = recent_users.values_list('id', flat=True)
        users_to_delete = queryset.filter(id__in=recent_user_ids)
        count = users_to_delete.count()
        
        if count > 0:
            users_to_delete.delete()
            self.message_user(
                request,
                ngettext(
                    "%d utilisateur récemment ajouté a été supprimé avec succès.",
                    "%d utilisateurs récemment ajoutés ont été supprimés avec succès.",
                    count
                ) % count,
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "Aucun utilisateur récemment ajouté n'a été sélectionné.",
                messages.WARNING
            )

    delete_recent_users.short_description = "Supprimer les utilisateurs récemment ajoutés"
    list_display = ('username', 'email', 'date_joined', 'is_staff', 'poste_principal')
    list_filter = ('date_joined', 'is_staff')
    ordering = ('-date_joined',)
"""