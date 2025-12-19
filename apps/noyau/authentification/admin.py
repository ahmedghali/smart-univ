# apps/noyau/authentification/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Administration personnalisée pour CustomUser.
    """

    # Champs affichés dans la liste
    list_display = [
        'username',
        'get_nom_complet',
        'email',
        'poste_principal',
        'langue_preferee',
        'is_staff',
        'is_active'
    ]

    # Filtres dans la barre latérale
    list_filter = [
        'is_staff',
        'is_active',
        'poste_principal',
        'langue_preferee',
        'date_joined'
    ]

    # Champs de recherche
    search_fields = [
        'username',
        'first_name',
        'last_name',
        'email'
    ]

    # Ordre d'affichage
    ordering = ['last_name', 'first_name']

    # Organisation des champs dans le formulaire
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات شخصية / Informations personnelles', {
            'fields': ('photo',)
        }),
        ('المناصب / Postes', {
            'fields': ('poste_principal', 'postes_secondaires')
        }),
        ('التفضيلات / Préférences', {
            'fields': ('langue_preferee',)
        }),
        ('التدقيق / Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Champs en lecture seule
    readonly_fields = ['created_at', 'updated_at']

    # Widget horizontal pour les postes secondaires
    filter_horizontal = ['postes_secondaires']

    # Champs affichés lors de l'ajout d'un utilisateur
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات إضافية / Informations supplémentaires', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'poste_principal',
                'langue_preferee',
            )
        }),
    )

    def get_nom_complet(self, obj):
        """Affiche le nom complet."""
        return obj.nom_complet
    get_nom_complet.short_description = 'الاسم الكامل / Nom complet'
