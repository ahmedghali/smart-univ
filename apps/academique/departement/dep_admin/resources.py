# apps/academique/departement/dep_admin/resources.py
"""
Resources pour import/export Excel des données du département.
"""

import io

import openpyxl
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from apps.academique.affectation.models import Classe, Ens_Dep
from apps.academique.departement.models import Matiere, NivSpeDep, NivSpeDep_SG, Specialite
from apps.academique.enseignant.models import Enseignant
from apps.academique.etudiant.models import Etudiant
from apps.noyau.authentification.models import CustomUser
from apps.noyau.commun.models import Grade, Semestre, Unite, Wilaya

# Dictionnaire de translitération Arabe -> Français
ARABIC_TO_FRENCH = {
    "ا": "a",
    "أ": "a",
    "إ": "i",
    "آ": "a",
    "ء": "",
    "ب": "b",
    "ت": "t",
    "ث": "th",
    "ج": "dj",
    "ح": "h",
    "خ": "kh",
    "د": "d",
    "ذ": "dh",
    "ر": "r",
    "ز": "z",
    "س": "s",
    "ش": "ch",
    "ص": "s",
    "ض": "d",
    "ط": "t",
    "ظ": "dh",
    "ع": "a",
    "غ": "gh",
    "ف": "f",
    "ق": "k",
    "ك": "k",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "ه": "h",
    "و": "ou",
    "ي": "i",
    "ى": "a",
    "ة": "a",
    "ئ": "i",
    "ؤ": "ou",
    "ـ": "",
    " ": " ",
    "َ": "a",
    "ُ": "ou",
    "ِ": "i",
    "ً": "an",
    "ٌ": "oun",
    "ٍ": "in",
    "ّ": "",
    "ْ": "",
}


def transliterate_arabic_to_french(arabic_text):
    """Translitère un texte arabe en français."""
    if not arabic_text:
        return ""
    result = ""
    for char in arabic_text:
        result += ARABIC_TO_FRENCH.get(char, char)
    return result.strip().title() if result else ""


def generate_credentials_excel(accounts):
    """Génère en mémoire un fichier Excel contenant les identifiants temporaires des comptes créés."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Identifiants"
    ws.append(["Nom", "Prénom", "Identifiant", "Mot de passe temporaire"])

    for acc in accounts:
        ws.append(
            [
                acc.get("nom", ""),
                acc.get("prenom", ""),
                acc.get("username", ""),
                acc.get("password", ""),
            ]
        )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class EnseignantResource(resources.ModelResource):
    """Resource pour import/export des enseignants."""

    _departement_cache = None
    _annee_cache = None
    _poste_cache = None

    grade = fields.Field(column_name="grade", attribute="grade", widget=ForeignKeyWidget(Grade, "code"))
    wilaya = fields.Field(column_name="wilaya", attribute="wilaya", widget=ForeignKeyWidget(Wilaya, "code"))

    class Meta:
        model = Enseignant
        import_id_fields = ["nom_fr", "prenom_fr"]
        skip_unchanged = True
        report_skipped = True
        from_encoding = "utf-8-sig"

    def __init__(self, departement_id=None, **kwargs):
        super().__init__(**kwargs)
        self.departement_id = departement_id
        self._departement_cache = None
        self._annee_cache = None
        self._poste_cache = None
        self.created_accounts = []

    def before_import(self, dataset, **kwargs):
        self.created_accounts = []
        super().before_import(dataset, **kwargs)

    def _get_departement(self):
        if self._departement_cache is None and self.departement_id:
            from apps.academique.departement.models import Departement

            try:
                self._departement_cache = Departement.objects.get(pk=self.departement_id)
            except Departement.DoesNotExist:
                self._departement_cache = False
        return self._departement_cache if self._departement_cache is not False else None

    def _get_annee(self):
        if self._annee_cache is None:
            from apps.noyau.commun.models import AnneeUniversitaire

            self._annee_cache = AnneeUniversitaire.objects.filter(est_courante=True).first()
        return self._annee_cache

    def _get_poste_enseignant(self):
        if self._poste_cache is None:
            from apps.noyau.commun.models import Poste

            self._poste_cache, _ = Poste.objects.get_or_create(
                code="enseignant",
                defaults={
                    "type": "enseignant",
                    "nom_ar": "أستاذ",
                    "nom_fr": "Enseignant",
                    "nom_ar_mini": "أ",
                    "nom_fr_mini": "Ens",
                    "niveau": 1,
                    "est_actif": True,
                },
            )
        return self._poste_cache

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        if kwargs.get("dry_run", False):
            return
        if not row_result.object_id:
            return
        try:
            enseignant = Enseignant.objects.get(pk=row_result.object_id)
            if not enseignant.user:
                self._create_user_optimized(enseignant)
            departement = self._get_departement()
            annee = self._get_annee()
            if departement and annee:
                Ens_Dep.objects.get_or_create(
                    enseignant=enseignant,
                    departement=departement,
                    annee_univ=annee,
                    defaults={
                        "statut": "مرسم",
                        "est_actif": True,
                        "semestre_1": True,
                        "semestre_2": True,
                    },
                )
        except Enseignant.DoesNotExist:
            pass

    def _create_user_optimized(self, enseignant):
        from apps.academique.enseignant.utils import generate_login, generate_password

        login = generate_login(enseignant.nom_fr, enseignant.nom_ar, enseignant.prenom_fr, enseignant.prenom_ar)
        password = generate_password(enseignant.nom_fr, enseignant.nom_ar, enseignant.prenom_fr, enseignant.prenom_ar)
        try:
            user = CustomUser.objects.create_user(
                username=login,
                password=password,
                email=enseignant.email_prof or enseignant.email_perso or f"{login}@univ.dz",
                first_name=enseignant.prenom_fr or enseignant.prenom_ar or "",
                last_name=enseignant.nom_fr or enseignant.nom_ar or "",
                telephone=enseignant.telmobile1 or "",
                doit_changer_mot_de_passe=True,
            )
            enseignant.user = user
            enseignant.save(update_fields=["user"])
            if not hasattr(self, "created_accounts"):
                self.created_accounts = []
            self.created_accounts.append(
                {
                    "nom": enseignant.nom_fr or enseignant.nom_ar or "",
                    "prenom": enseignant.prenom_fr or enseignant.prenom_ar or "",
                    "username": login,
                    "password": password,
                }
            )
        except Exception:
            pass

    def after_import(self, dataset, result, **kwargs):
        super().after_import(dataset, result, **kwargs)
        result.created_accounts = getattr(self, "created_accounts", [])

    def before_import_row(self, row, row_number=None, **_kwargs):
        import uuid
        from datetime import datetime

        matricule = row.get("matricule", "").strip() if row.get("matricule") else ""
        if not matricule:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:6].upper()
            row_num = row_number if row_number else 0
            row["matricule"] = f"ENS{timestamp}{row_num:03d}{unique_id}"
        nom_fr = row.get("nom_fr", "").strip() if row.get("nom_fr") else ""
        nom_ar = row.get("nom_ar", "").strip() if row.get("nom_ar") else ""
        if not nom_fr and nom_ar:
            row["nom_fr"] = transliterate_arabic_to_french(nom_ar)
        prenom_fr = row.get("prenom_fr", "").strip() if row.get("prenom_fr") else ""
        prenom_ar = row.get("prenom_ar", "").strip() if row.get("prenom_ar") else ""
        if not prenom_fr and prenom_ar:
            row["prenom_fr"] = transliterate_arabic_to_french(prenom_ar)

    def get_instance(self, _instance_loader, row):
        nom_fr = row.get("nom_fr", "").strip() if row.get("nom_fr") else ""
        prenom_fr = row.get("prenom_fr", "").strip() if row.get("prenom_fr") else ""
        date_nais = row.get("date_nais")
        if not nom_fr or not prenom_fr:
            return None
        queryset = Enseignant.objects.filter(nom_fr__iexact=nom_fr, prenom_fr__iexact=prenom_fr)
        if queryset.count() == 0:
            return None
        elif queryset.count() == 1:
            return queryset.first()
        else:
            if date_nais:
                queryset_with_date = queryset.filter(date_nais=date_nais)
                if queryset_with_date.count() == 1:
                    return queryset_with_date.first()
                elif queryset_with_date.count() > 1:
                    raise Exception(
                        f"تكرار: يوجد عدة أساتذة بنفس الاسم ({nom_fr} {prenom_fr}) وتاريخ الميلاد ({date_nais})."
                    )
            raise Exception(
                f"تكرار: يوجد عدة أساتذة بنفس الاسم ({nom_fr} {prenom_fr}). يرجى إضافة تاريخ الميلاد للتمييز."
            )


class EtudiantResource(resources.ModelResource):
    """Resource pour import/export des étudiants - OPTIMISÉ."""

    _niv_spe_dep_sg_cache = None
    _imported_etudiant_ids = []  # Liste des IDs importés pour traitement batch

    wilaya = fields.Field(column_name="wilaya", attribute="wilaya", widget=ForeignKeyWidget(Wilaya, "code"))

    class Meta:
        model = Etudiant
        import_id_fields = ["matricule"]
        skip_unchanged = True
        report_skipped = True
        use_bulk = False  # Désactivé car num_ins unique pose problème avec bulk
        batch_size = 500

    def __init__(self, niv_spe_dep_sg_id=None, **kwargs):
        super().__init__(**kwargs)
        self.niv_spe_dep_sg_id = niv_spe_dep_sg_id
        self._niv_spe_dep_sg_cache = None
        self._imported_etudiant_ids = []
        self.created_accounts = []

    def before_import(self, dataset, **kwargs):
        self._imported_etudiant_ids = []
        self.created_accounts = []
        super().before_import(dataset, **kwargs)

    def _get_niv_spe_dep_sg(self):
        if self._niv_spe_dep_sg_cache is None and self.niv_spe_dep_sg_id:
            try:
                self._niv_spe_dep_sg_cache = NivSpeDep_SG.objects.get(pk=self.niv_spe_dep_sg_id)
            except NivSpeDep_SG.DoesNotExist:
                self._niv_spe_dep_sg_cache = False
        return self._niv_spe_dep_sg_cache if self._niv_spe_dep_sg_cache is not False else None

    def before_import_row(self, row, row_number=None, **kwargs):
        niv_spe_dep_sg = self._get_niv_spe_dep_sg()
        if niv_spe_dep_sg:
            row["niv_spe_dep_sg"] = niv_spe_dep_sg.id

        # Validation matricule obligatoire (A11)
        matricule = row.get("matricule", "").strip() if row.get("matricule") else ""
        if not matricule:
            from django.core.exceptions import ValidationError

            line_info = f" (ligne {row_number})" if row_number else ""
            raise ValidationError(f"Le matricule est obligatoire pour chaque étudiant{line_info}.")
        row["matricule"] = matricule

        # num_ins vide reste None (A11)
        num_ins = row.get("num_ins", "").strip() if row.get("num_ins") else ""
        row["num_ins"] = num_ins if num_ins else None

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        """Collecte les IDs pour traitement batch."""
        if row_result.object_id:
            self._imported_etudiant_ids.append(row_result.object_id)

    def after_import(self, dataset, result, using_transactions=True, dry_run=False, **kwargs):
        """Crée les utilisateurs en batch après l'import."""
        if dry_run or not self._imported_etudiant_ids:
            result.created_accounts = getattr(self, "created_accounts", [])
            return

        from django.db import transaction

        from apps.academique.etudiant.utils import generate_login, generate_password

        # Récupérer tous les étudiants sans user en une seule requête
        etudiants = Etudiant.objects.filter(pk__in=self._imported_etudiant_ids, user__isnull=True).only(
            "id", "nom_fr", "nom_ar", "prenom_fr", "prenom_ar", "email_prof", "email_perso", "tel_mobile1"
        )

        if not etudiants:
            result.created_accounts = getattr(self, "created_accounts", [])
            return

        # Charger tous les usernames existants en mémoire (cache)
        existing_usernames = set(CustomUser.objects.values_list("username", flat=True))

        users_to_create = []
        etudiant_user_map = {}  # {etudiant_id: username}

        for etudiant in etudiants:
            login = generate_login(etudiant.nom_fr, etudiant.nom_ar, etudiant.prenom_fr, etudiant.prenom_ar)

            # Assurer l'unicité du username
            base_login = login
            counter = 1
            while login in existing_usernames:
                login = f"{base_login}{counter}"
                counter += 1

            existing_usernames.add(login)

            password = generate_password(etudiant.nom_fr, etudiant.nom_ar, etudiant.prenom_fr, etudiant.prenom_ar)

            user = CustomUser(
                username=login,
                email=etudiant.email_prof or etudiant.email_perso or f"{login}@etu.univ.dz",
                first_name=etudiant.prenom_fr or etudiant.prenom_ar or "",
                last_name=etudiant.nom_fr or etudiant.nom_ar or "",
                telephone=etudiant.tel_mobile1 or "",
                doit_changer_mot_de_passe=True,
            )
            user.set_password(password)
            users_to_create.append(user)
            etudiant_user_map[etudiant.id] = login

            if not hasattr(self, "created_accounts"):
                self.created_accounts = []
            self.created_accounts.append(
                {
                    "nom": etudiant.nom_fr or etudiant.nom_ar or "",
                    "prenom": etudiant.prenom_fr or etudiant.prenom_ar or "",
                    "username": login,
                    "password": password,
                }
            )

        # Création batch des utilisateurs
        with transaction.atomic():
            # Bulk create users
            CustomUser.objects.bulk_create(users_to_create, batch_size=200, ignore_conflicts=True)

            # Récupérer les users créés par username
            created_users = {u.username: u for u in CustomUser.objects.filter(username__in=etudiant_user_map.values())}

            # Mise à jour batch des étudiants
            etudiants_to_update = []
            for etudiant in Etudiant.objects.filter(pk__in=etudiant_user_map.keys()):
                username = etudiant_user_map.get(etudiant.id)
                if username and username in created_users:
                    etudiant.user = created_users[username]
                    etudiants_to_update.append(etudiant)

            # Bulk update des étudiants
            if etudiants_to_update:
                Etudiant.objects.bulk_update(etudiants_to_update, ["user"], batch_size=200)

        # Nettoyer la liste
        result.created_accounts = getattr(self, "created_accounts", [])
        self._imported_etudiant_ids = []


class EnsDepResource(resources.ModelResource):
    """Resource pour import/export des affectations enseignant-département."""

    enseignant = fields.Field(
        column_name="matricule_enseignant", attribute="enseignant", widget=ForeignKeyWidget(Enseignant, "matricule")
    )

    class Meta:
        model = Ens_Dep
        import_id_fields = ["enseignant", "departement", "annee_univ"]


class SpecialiteResource(resources.ModelResource):
    """Resource pour import/export des spécialités."""

    class Meta:
        model = Specialite
        import_id_fields = ["code"]


class MatiereResource(resources.ModelResource):
    """Resource pour import/export des matières."""

    # Widget pour le champ unite (lookup par code)
    unite = fields.Field(column_name="unite", attribute="unite", widget=ForeignKeyWidget(Unite, "code"))

    # Widget pour niv_spe_dep (lookup par ID)
    niv_spe_dep = fields.Field(
        column_name="niv_spe_dep", attribute="niv_spe_dep", widget=ForeignKeyWidget(NivSpeDep, "id")
    )

    # Widget pour semestre (lookup par ID)
    semestre = fields.Field(column_name="semestre", attribute="semestre", widget=ForeignKeyWidget(Semestre, "id"))

    class Meta:
        model = Matiere
        import_id_fields = ["code", "niv_spe_dep", "semestre"]
        skip_unchanged = True
        report_skipped = True
        fields = ("code", "nom_ar", "nom_fr", "coeff", "credit", "unite", "niv_spe_dep", "semestre")

    def __init__(self, niv_spe_dep_id=None, semestre_id=None, **kwargs):
        super().__init__(**kwargs)
        self.niv_spe_dep_id = niv_spe_dep_id
        self.semestre_id = semestre_id

    def before_import_row(self, row, row_number=None, **kwargs):
        """Ajoute le niv_spe_dep et semestre à chaque ligne importée."""
        from datetime import datetime

        # Ajouter niv_spe_dep et semestre depuis le formulaire
        if self.niv_spe_dep_id:
            row["niv_spe_dep"] = self.niv_spe_dep_id
        if self.semestre_id:
            row["semestre"] = self.semestre_id

        # Générer un code unique si absent
        code = row.get("code", "").strip() if row.get("code") else ""
        if not code:
            nom = row.get("nom_fr", "") or row.get("nom_ar", "") or ""
            # Créer un code à partir du nom
            code_base = "".join(c for c in nom[:10].upper() if c.isalnum())
            if not code_base:
                code_base = "MAT"
            timestamp = datetime.now().strftime("%H%M%S")
            row["code"] = f"{code_base}_{timestamp}"


class ClasseResource(resources.ModelResource):
    """Resource pour import/export des classes."""

    # Widget pour semestre (lookup par ID)
    semestre = fields.Field(column_name="semestre", attribute="semestre", widget=ForeignKeyWidget(Semestre, "id"))

    # Widget pour niv_spe_dep_sg (lookup par ID)
    niv_spe_dep_sg = fields.Field(
        column_name="niv_spe_dep_sg", attribute="niv_spe_dep_sg", widget=ForeignKeyWidget(NivSpeDep_SG, "id")
    )

    # Widget pour matiere (lookup par code)
    matiere = fields.Field(column_name="matiere", attribute="matiere", widget=ForeignKeyWidget(Matiere, "code"))

    # Widget pour enseignant (lookup par ID de Ens_Dep)
    enseignant = fields.Field(column_name="enseignant", attribute="enseignant", widget=ForeignKeyWidget(Ens_Dep, "id"))

    class Meta:
        model = Classe
        import_id_fields = ["matiere", "enseignant", "niv_spe_dep_sg", "jour", "temps"]
        skip_unchanged = True
        report_skipped = True
        fields = ("matiere", "enseignant", "niv_spe_dep_sg", "semestre", "jour", "temps", "type")

    def __init__(self, semestre_id=None, niveau_id=None, specialite_id=None, departement_id=None, **kwargs):
        super().__init__(**kwargs)
        self.semestre_id = semestre_id
        self.niveau_id = niveau_id
        self.specialite_id = specialite_id
        self.departement_id = departement_id
        self._niv_spe_dep = None

    def _get_niv_spe_dep(self):
        """Récupère le NivSpeDep correspondant aux paramètres sélectionnés."""
        if self._niv_spe_dep is None and self.niveau_id and self.specialite_id and self.departement_id:
            self._niv_spe_dep = NivSpeDep.objects.filter(
                niveau_id=self.niveau_id, specialite_id=self.specialite_id, departement_id=self.departement_id
            ).first()
        return self._niv_spe_dep

    def before_import_row(self, row, row_number=None, **kwargs):
        """Ajoute le semestre et niv_spe_dep_sg à chaque ligne importée."""
        if self.semestre_id:
            row["semestre"] = self.semestre_id

        # Si niv_spe_dep_sg n'est pas fourni, essayer de trouver un par défaut
        if not row.get("niv_spe_dep_sg"):
            niv_spe_dep = self._get_niv_spe_dep()
            if niv_spe_dep:
                # Chercher un NivSpeDep_SG par défaut (type "tous_etudiants" ou le premier)
                sg = NivSpeDep_SG.objects.filter(niv_spe_dep=niv_spe_dep).first()
                if sg:
                    row["niv_spe_dep_sg"] = sg.id
