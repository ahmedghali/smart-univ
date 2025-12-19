# apps/noyau/authentification/constants.py

"""
Constantes pour la gestion des rôles et des redirections.
Ce fichier centralise toutes les définitions de rôles pour faciliter la maintenance.
"""

# ══════════════════════════════════════════════════════════════
# DÉFINITION DES RÔLES ET LEURS DASHBOARDS
# ══════════════════════════════════════════════════════════════

ROLE_ETUDIANT = 'etudiant'
ROLE_ENSEIGNANT = 'enseignant'
ROLE_CHEF_DEP = 'chef_departement'
ROLE_CHEF_DEP_ADJ_P = 'chef_dep_adj_p'
ROLE_CHEF_DEP_ADJ_PG = 'chef_dep_adj_pg'
ROLE_DOYEN = 'doyen'
ROLE_VICE_DOYEN_P = 'vice_doyen_p'
ROLE_VICE_DOYEN_PG = 'vice_doyen_pg'
ROLE_RECTEUR = 'recteur'
ROLE_VICE_RECT_P = 'vice_rect_p'
ROLE_VICE_RECT_PG = 'vice_rect_pg'

# ══════════════════════════════════════════════════════════════
# MAPPING RÔLES → LABELS (ARABE)
# ══════════════════════════════════════════════════════════════

ROLE_LABELS = {
    ROLE_ETUDIANT: 'لوحة تحكم الطالب',
    ROLE_ENSEIGNANT: 'لوحة تحكم الأستاذ',
    ROLE_CHEF_DEP: 'لوحة تحكم رئيس القسم',
    ROLE_CHEF_DEP_ADJ_P: 'لوحة تحكم ن.ر.ق بيداغوجيا',
    ROLE_CHEF_DEP_ADJ_PG: 'لوحة تحكم ن.ر.ق ما بعد التدرج',
    ROLE_DOYEN: 'لوحة تحكم عميد الكلية',
    ROLE_VICE_DOYEN_P: 'لوحة تحكم ن.ع.ك بيداغوجيا',
    ROLE_VICE_DOYEN_PG: 'لوحة تحكم ن.ع.ك ما بعد التدرج',
    ROLE_RECTEUR: 'لوحة تحكم رئيس الجامعة',
    ROLE_VICE_RECT_P: 'لوحة تحكم ن.ر.ج بيداغوجيا',
    ROLE_VICE_RECT_PG: 'لوحة تحكم ن.ر.ج ما بعد التدرج',
}

# ══════════════════════════════════════════════════════════════
# MAPPING RÔLES → URLS DE REDIRECTION
# ══════════════════════════════════════════════════════════════

ROLE_DASHBOARDS = {
    ROLE_ETUDIANT: 'etud:dashboard_Etud',
    ROLE_ENSEIGNANT: None,  # Nécessite gestion spéciale (départements)
    ROLE_CHEF_DEP: 'depa:dashboard_Dep',
    ROLE_CHEF_DEP_ADJ_P: 'depa:dashboard_Dep',  # Même dashboard que chef_dep
    ROLE_CHEF_DEP_ADJ_PG: 'depa:dashboard_Dep',  # Même dashboard que chef_dep
    ROLE_DOYEN: 'facu:dashboard_Fac',
    ROLE_VICE_DOYEN_P: 'facu:dashboard_Fac',  # Même dashboard que doyen
    ROLE_VICE_DOYEN_PG: 'facu:dashboard_Fac',  # Même dashboard que doyen
    ROLE_RECTEUR: 'univ:dashboard_Uni',
    ROLE_VICE_RECT_P: 'univ:vice_rect_p_dashboard',
    ROLE_VICE_RECT_PG: 'univ:vice_rect_pg_dashboard',
}

# ══════════════════════════════════════════════════════════════
# MAPPING RÔLES → CODES DE POSTES
# ══════════════════════════════════════════════════════════════
# Ces codes correspondent aux codes dans la table Poste

ROLE_POSTE_CODES = {
    ROLE_ETUDIANT: 'etudiant',
    ROLE_ENSEIGNANT: 'enseignant',
    ROLE_CHEF_DEP: 'chef_departement',
    ROLE_CHEF_DEP_ADJ_P: 'chef_dep_adj_p',
    ROLE_CHEF_DEP_ADJ_PG: 'chef_dep_adj_pg',
    ROLE_DOYEN: 'doyen',
    ROLE_VICE_DOYEN_P: 'vice_doyen_p',
    ROLE_VICE_DOYEN_PG: 'vice_doyen_pg',
    ROLE_RECTEUR: 'recteur',
    ROLE_VICE_RECT_P: 'vice_rect_p',
    ROLE_VICE_RECT_PG: 'vice_rect_pg',
}

# ══════════════════════════════════════════════════════════════
# MAPPING RELATED_NAME → RÔLES
# ══════════════════════════════════════════════════════════════
# Pour vérifier les relations ForeignKey dans les modèles

ENSEIGNANT_RELATIONS_TO_ROLES = {
    'departement_as_chef': ROLE_CHEF_DEP,
    'departement_as_chef_adj_p': ROLE_CHEF_DEP_ADJ_P,
    'departement_as_chef_adj_pg': ROLE_CHEF_DEP_ADJ_PG,
    'fac_doyen': ROLE_DOYEN,
    'fac_vice_doyen_p': ROLE_VICE_DOYEN_P,
    'fac_vice_doyen_pg': ROLE_VICE_DOYEN_PG,
    'univ_recteur': ROLE_RECTEUR,
    'univ_vice_rect_p': ROLE_VICE_RECT_P,
    'univ_vice_rect_pg': ROLE_VICE_RECT_PG,
}

# ══════════════════════════════════════════════════════════════
# MESSAGES D'ERREUR
# ══════════════════════════════════════════════════════════════

ERROR_NO_ROLES = "لم يتم العثور على مناصب لهذا المستخدم. يرجى الاتصال بالمسؤول."
ERROR_NO_ENSEIGNANT_PROFILE = "لم يتم العثور على ملف تعريف الأستاذ. يرجى الاتصال بالمسؤول."
ERROR_NO_DEPARTEMENT = "ليس لديك أي انتماء إلى قسم. يرجى الاتصال بالمسؤول."
ERROR_INVALID_ROLE = "المنصب المختار غير صالح."
ERROR_INVALID_DEPARTEMENT = "القسم المختار غير صالح."
ERROR_DEPARTEMENT_NOT_FOUND = "القسم المختار غير موجود. يرجى اختيار قسم آخر."
