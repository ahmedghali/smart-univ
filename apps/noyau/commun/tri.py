# apps/noyau/commun/tri.py
"""
Tri « naturel » pour tous les modèles du projet.

Les champs texte contenant des nombres (numero, code, matricule…) sont triés
numériquement : « 2 » avant « 10 », « G-2 » avant « G-10 ». Le champ « jour »
suit l'ordre de la semaine universitaire (samedi → jeudi).

Appliqué au chargement (CommunConfig.ready) à l'ordre par défaut des modèles
(Meta.ordering) et aux listes de l'admin (y compris le tri au clic sur une colonne).
"""

from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import FieldDoesNotExist
from django.db.models import CharField, F, Func, IntegerField, Value
from django.db.models.expressions import OrderBy

# Largeur à laquelle chaque suite de chiffres est complétée par des zéros
LARGEUR_NOMBRES = 20
JOURS = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]


def _regexp_replace(expr, motif, remplacement):
    return Func(
        expr, Value(motif), Value(remplacement), Value("g"), function="REGEXP_REPLACE", output_field=CharField()
    )


def cle_naturelle(chemin):
    """Expression où chaque nombre est complété à LARGEUR_NOMBRES chiffres (tri texte = tri numérique)."""
    zeros = "0" * LARGEUR_NOMBRES
    etape1 = _regexp_replace(F(chemin), r"(\d+)", zeros + r"\1")
    return _regexp_replace(etape1, rf"0*(\d{{{LARGEUR_NOMBRES}}})(?!\d)", r"\1")


def cle_jour(chemin):
    """Rang du jour dans la semaine universitaire (array_position, compatible avec les tris via relations)."""
    jours = ", ".join(f"'{j}'" for j in JOURS)
    return Func(
        F(chemin),
        template=f"COALESCE(array_position(ARRAY[{jours}]::text[], %(expressions)s::text), {len(JOURS) + 1})",
        output_field=IntegerField(),
    )


def _champ(model, chemin):
    """Champ final d'un chemin « a__b__c », ou None."""
    try:
        for partie in chemin.split("__"):
            champ = model._meta.get_field(partie)
            model = champ.related_model or model
        return champ
    except FieldDoesNotExist:
        return None


def convertir_ordering(model, ordering):
    """Remplace les champs texte d'un ordering par leur clé de tri naturel."""
    resultat = []
    for item in ordering:
        if not isinstance(item, str) or item in ("?", "pk", "-pk"):
            resultat.append(item)
            continue
        desc = item.startswith("-")
        chemin = item.lstrip("-")
        champ = _champ(model, chemin)
        if champ is None or champ.get_internal_type() not in ("CharField", "TextField"):
            resultat.append(item)
        elif champ.name == "jour":
            resultat.append(OrderBy(cle_jour(chemin), descending=desc))
        else:
            resultat.append(OrderBy(cle_naturelle(chemin), descending=desc))
    return resultat


def installer():
    from django.apps import apps

    for model in apps.get_models():
        if model._meta.ordering:
            model._meta.ordering = convertir_ordering(model, model._meta.ordering)

    origine = ChangeList._get_deterministic_ordering

    def _get_deterministic_ordering(self, ordering):
        return origine(self, convertir_ordering(self.model, ordering))

    ChangeList._get_deterministic_ordering = _get_deterministic_ordering
