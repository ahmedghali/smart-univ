# apps/academique/enseignant/utils.py

from apps.noyau.authentification.models import CustomUser
from apps.noyau.commun.models import Poste


# Dictionnaire de translitération Arabe → Français
ARABIC_TO_FRENCH = {
    'ا': 'a', 'أ': 'a', 'إ': 'i', 'آ': 'a', 'ؤ': 'ou',
    'ب': 'b',
    'ت': 't', 'ة': 't',
    'ث': 'th',
    'ج': 'dj',
    'ح': 'h',
    'خ': 'kh',
    'د': 'd',
    'ذ': 'dh',
    'ر': 'r',
    'ز': 'z',
    'س': 's',
    'ش': 'sh',
    'ص': 's',
    'ض': 'd',
    'ط': 't',
    'ظ': 'dh',
    'ع': 'a',
    'غ': 'gh',
    'ف': 'f',
    'ق': 'q',
    'ك': 'k',
    'ل': 'l',
    'م': 'm',
    'ن': 'n',
    'ه': 'h',
    'و': 'ou',
    'ي': 'i', 'ى': 'a',
    'ئ': 'i',
    ' ': '', '-': '', '_': '',
}


def transliterate_arabic_to_french(text):
    """Convertit un texte arabe en français en utilisant le dictionnaire."""
    if not text:
        return ""

    result = ""
    for char in text:
        result += ARABIC_TO_FRENCH.get(char, char)
    return result


def get_french_name(nom_fr, nom_ar, max_length=7):
    """
    Retourne le nom en français, soit directement soit par translitération.
    Supprime les espaces et convertit en minuscules.
    """
    if nom_fr and nom_fr.strip():
        nom = nom_fr.strip()
    elif nom_ar and nom_ar.strip():
        nom = transliterate_arabic_to_french(nom_ar.strip())
    else:
        nom = "user"

    # Supprimer espaces, tirets et convertir en minuscules
    nom = nom.lower().replace(" ", "").replace("-", "").replace("_", "")

    # Limiter à max_length caractères
    return nom[:max_length]


def generate_login(nom_fr, nom_ar, prenom_fr, prenom_ar):
    """
    Génère un login unique au format: nom.prenom
    Si le login existe déjà, ajoute un numéro incrémental.
    """
    nom = get_french_name(nom_fr, nom_ar, max_length=7)
    prenom = get_french_name(prenom_fr, prenom_ar, max_length=7)

    base_login = f"{nom}.{prenom}"
    login = base_login

    # Vérifier si le login existe déjà
    counter = 1
    while CustomUser.objects.filter(username=login).exists():
        login = f"{base_login}{counter}"
        counter += 1

    return login


def generate_password(nom_fr, nom_ar, prenom_fr, prenom_ar):
    """
    Génère un mot de passe au format: ...abcd123
    ab = 2 premières lettres du nom
    cd = 2 premières lettres du prénom
    """
    nom = get_french_name(nom_fr, nom_ar, max_length=7)
    prenom = get_french_name(prenom_fr, prenom_ar, max_length=7)

    # Prendre les 2 premières lettres (ou compléter avec 'x' si moins de 2)
    ab = (nom[:2] if len(nom) >= 2 else nom + 'x' * (2 - len(nom))).lower()
    cd = (prenom[:2] if len(prenom) >= 2 else prenom + 'x' * (2 - len(prenom))).lower()

    password = f"...{ab}{cd}123"
    return password


def create_user_for_enseignant(enseignant):
    """
    Crée automatiquement un utilisateur pour un enseignant s'il n'en a pas déjà un.

    Retourne un tuple (user, error_message):
    - (user, None) si succès
    - (None, "message d'erreur") si échec
    """
    # Si l'enseignant a déjà un utilisateur, ne rien faire
    if enseignant.user:
        return (None, "Cet enseignant a déjà un utilisateur.")

    # Générer login et mot de passe
    login = generate_login(
        enseignant.nom_fr,
        enseignant.nom_ar,
        enseignant.prenom_fr,
        enseignant.prenom_ar
    )

    password = generate_password(
        enseignant.nom_fr,
        enseignant.nom_ar,
        enseignant.prenom_fr,
        enseignant.prenom_ar
    )

    # Créer l'utilisateur
    try:
        # Récupérer ou créer le poste "enseignant"
        poste_enseignant, _ = Poste.objects.get_or_create(
            code='enseignant',
            defaults={
                'type': 'enseignant',
                'nom_ar': 'أستاذ',
                'nom_fr': 'Enseignant',
                'nom_ar_mini': 'أ',
                'nom_fr_mini': 'Ens',
                'niveau': 1,
                'est_actif': True
            }
        )

        user = CustomUser.objects.create_user(
            username=login,
            password=password,
            email=enseignant.email_prof or enseignant.email_perso or f"{login}@univ.dz",
            first_name=enseignant.prenom_fr or enseignant.prenom_ar or "",
            last_name=enseignant.nom_fr or enseignant.nom_ar or "",
            telephone=enseignant.telmobile1 or "",
        )

        # Affecter le poste principal
        user.poste_principal = poste_enseignant
        user.save(update_fields=['poste_principal'])

        # Lier l'utilisateur à l'enseignant
        enseignant.user = user
        enseignant.save(update_fields=['user'])

        return (user, None)
    except Exception as e:
        error_msg = f"Erreur: {str(e)}"
        print(f"Erreur lors de la création de l'utilisateur pour {enseignant}: {e}")
        return (None, error_msg)
