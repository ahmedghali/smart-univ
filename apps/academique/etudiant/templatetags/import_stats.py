# apps/academique/etudiant/templatetags/import_stats.py

from django import template

register = template.Library()


@register.filter
def count_import_type(valid_rows, import_type):
    """
    Compte le nombre de lignes d'un type d'import spécifique.

    Usage: {{ result.valid_rows|count_import_type:"new" }}
    """
    if not valid_rows:
        return 0
    return sum(1 for row in valid_rows if row.import_type == import_type)


@register.filter
def count_total(valid_rows):
    """
    Compte le nombre total de lignes valides.

    Usage: {{ result.valid_rows|count_total }}
    """
    if not valid_rows:
        return 0
    return len(list(valid_rows))


@register.filter
def get_student_name(row_diff, index):
    """
    Récupère un champ du diff par index.

    Usage: {{ row.diff|get_student_name:1 }}
    """
    try:
        diff_list = list(row_diff)
        if index < len(diff_list):
            return diff_list[index]
        return ""
    except (TypeError, IndexError):
        return ""


@register.simple_tag
def import_statistics(valid_rows):
    """
    Retourne un dictionnaire avec les statistiques d'import.

    Usage: {% import_statistics result.valid_rows as stats %}
    """
    if not valid_rows:
        return {
            'total': 0,
            'new': 0,
            'update': 0,
            'skip': 0,
            'delete': 0,
            'error': 0
        }

    rows_list = list(valid_rows)
    stats = {
        'total': len(rows_list),
        'new': sum(1 for row in rows_list if row.import_type == 'new'),
        'update': sum(1 for row in rows_list if row.import_type == 'update'),
        'skip': sum(1 for row in rows_list if row.import_type == 'skip'),
        'delete': sum(1 for row in rows_list if row.import_type == 'delete'),
        'error': sum(1 for row in rows_list if row.import_type == 'error'),
    }
    return stats
