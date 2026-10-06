# apps/noyau/authentification/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.noyau.commun.models import AffectationPoste

from .models import CustomUser


class AffectationPosteUserInline(admin.TabularInline):
    """Postes occupés par l'utilisateur (chef de département, doyen...)."""

    model = AffectationPoste
    fk_name = "user"
    fields = (
        "poste",
        "niveau_contexte",
        "universite",
        "faculte",
        "departement",
        "annee_univ",
        "date_debut",
        "date_fin",
        "est_actif",
    )
    extra = 0
    verbose_name = "منصب / Poste"
    verbose_name_plural = "المناصب / Postes"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Administration personnalisée pour CustomUser.
    """

    inlines = [AffectationPosteUserInline]

    # Champs affichés dans la liste
    list_display = ["username", "get_nom_complet", "email", "langue_preferee", "is_staff", "is_active"]

    # Filtres dans la barre latérale
    list_filter = ["is_staff", "is_active", "langue_preferee", "date_joined"]

    # Champs de recherche
    search_fields = ["username", "first_name", "last_name", "email"]

    # Ordre d'affichage
    ordering = ["last_name", "first_name"]

    # Organisation des champs dans le formulaire
    fieldsets = UserAdmin.fieldsets + (
        ("معلومات شخصية / Informations personnelles", {"fields": ("photo",)}),
        ("التفضيلات / Préférences", {"fields": ("langue_preferee",)}),
        ("التدقيق / Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # Champs en lecture seule
    readonly_fields = ["created_at", "updated_at"]

    # Champs affichés lors de l'ajout d'un utilisateur
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "معلومات إضافية / Informations supplémentaires",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "langue_preferee",
                )
            },
        ),
    )

    def get_nom_complet(self, obj):
        """Affiche le nom complet."""
        return obj.nom_complet

    get_nom_complet.short_description = "الاسم الكامل / Nom complet"
