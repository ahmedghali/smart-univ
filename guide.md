# Guide de Développement - Smart-Univ

## Checklist des Tâches Réalisées

### 2025-12-10

#### Phase 1 : Création des applications académiques (17:11-17:12)
- [x] Création de la structure apps/academique/ - 2025-12-10 17:11
- [x] Création de l'application universite - 2025-12-10 17:11
- [x] Création de l'application faculte - 2025-12-10 17:12
- [x] Création de l'application departement - 2025-12-10 17:12
- [x] Création de l'application enseignant - 2025-12-10 17:12
- [x] Création de l'application etudiant - 2025-12-10 17:12
- [x] Création de l'application affectation - 2025-12-10 17:12
- [x] Configuration des chemins de modules dans apps.py - 2025-12-10 17:12
- [x] Ajout des applications dans INSTALLED_APPS (settings.py) - 2025-12-10 17:12
- [x] Vérification de la configuration Django (python manage.py check) - 2025-12-10 17:12

#### Phase 2 : Création des applications noyau et configuration (17:15-17:20)
- [x] Création du fichier guide.md avec checklist - 2025-12-10 17:15
- [x] Création de la structure apps/noyau/ - 2025-12-10 17:15
- [x] Création de l'application authentification - 2025-12-10 17:16
- [x] Création de l'application commun - 2025-12-10 17:16
- [x] Configuration des chemins de modules pour authentification et commun - 2025-12-10 17:16
- [x] Ajout de urls.py et forms.py pour universite - 2025-12-10 17:17
- [x] Ajout de urls.py et forms.py pour faculte - 2025-12-10 17:17
- [x] Ajout de urls.py et forms.py pour departement - 2025-12-10 17:17
- [x] Ajout de urls.py et forms.py pour enseignant - 2025-12-10 17:17
- [x] Ajout de urls.py et forms.py pour etudiant - 2025-12-10 17:18
- [x] Ajout de urls.py et forms.py pour affectation - 2025-12-10 17:18
- [x] Ajout de urls.py et forms.py pour authentification - 2025-12-10 17:18
- [x] Ajout de urls.py et forms.py pour commun - 2025-12-10 17:18
- [x] Configuration des URLs dans config/urls.py - 2025-12-10 17:19
- [x] Mise à jour de INSTALLED_APPS avec les apps noyau - 2025-12-10 17:19
- [x] Vérification finale de la configuration Django - 2025-12-10 17:20

#### Phase 3 : Configuration PostgreSQL et variables d'environnement (17:25-17:35)
- [x] Création du fichier requirements.txt avec toutes les dépendances - 2025-12-10 17:25
- [x] Création du fichier .env avec les credentials PostgreSQL - 2025-12-10 17:26
- [x] Création du fichier .env.example comme template - 2025-12-10 17:26
- [x] Création du fichier .gitignore - 2025-12-10 17:27
- [x] Configuration de settings.py pour utiliser python-decouple - 2025-12-10 17:28
- [x] Migration de SQLite vers PostgreSQL dans settings.py - 2025-12-10 17:29
- [x] Configuration de la langue (fr-fr) et timezone (Africa/Algiers) - 2025-12-10 17:30
- [x] Installation de toutes les dépendances (pip install -r requirements.txt) - 2025-12-10 17:31
- [x] Test de connexion à la base PostgreSQL - 2025-12-10 17:33
- [x] Application des migrations Django vers PostgreSQL - 2025-12-10 17:34

#### Phase 4 : Interface en arabe et design responsive (17:50-18:00)
- [x] Configuration de la langue arabe (ar) dans settings.py - 2025-12-10 17:52
- [x] Ajout du support multilingue (ar, fr, en) - 2025-12-10 17:52
- [x] Configuration des dossiers templates et static - 2025-12-10 17:53
- [x] Création du template de base (base.html) avec Bootstrap 5 RTL - 2025-12-10 17:54
- [x] Intégration de la police Cairo pour l'arabe - 2025-12-10 17:54
- [x] Création de la vue home dans l'app commun - 2025-12-10 17:56
- [x] Configuration de l'URL racine (/) - 2025-12-10 17:57
- [x] Création du template home.html avec contenu en arabe - 2025-12-10 17:58
- [x] Test et vérification de la configuration - 2025-12-10 17:59

#### Phase 5 : Modèles utilisateur et système de postes (18:00-18:30)
- [x] Création du modèle BaseModel dans apps/noyau/commun/models.py - 2025-12-10 18:05
- [x] Création du modèle Poste avec support bilingue - 2025-12-10 18:05
- [x] Création du modèle CustomUser dans apps/noyau/authentification/models.py - 2025-12-10 18:10
- [x] Configuration AUTH_USER_MODEL = 'authentification.CustomUser' - 2025-12-10 18:10
- [x] Ajout de Pillow dans requirements.txt pour ImageField - 2025-12-10 18:15
- [x] Création de la commande populate_postes.py (24 postes prédéfinis) - 2025-12-10 18:20
- [x] Revue et validation des modèles avant migration - 2025-12-10 18:25

#### Phase 6 : Résolution des erreurs de migration (18:30-18:45)
- [x] Détection de l'erreur InconsistentMigrationHistory - 2025-12-10 18:32
- [x] Suppression de la base de données PostgreSQL - 2025-12-10 18:35
- [x] Recréation de la base smart_univ___db - 2025-12-10 18:35
- [x] Création des migrations pour commun et authentification - 2025-12-10 18:38
- [x] Application des migrations avec succès - 2025-12-10 18:40
- [x] Exécution de populate_postes (24 postes créés) - 2025-12-10 18:42
- [x] Création du superutilisateur - 2025-12-10 18:45

#### Phase 7 : Interfaces d'administration (18:45-19:00)
- [x] Création de commun/admin.py avec PosteAdmin - 2025-12-10 18:48
- [x] Ajout du modèle Wilaya dans commun/models.py - 2025-12-10 18:50
- [x] Création de WilayaAdmin dans commun/admin.py - 2025-12-10 18:52
- [x] Création de authentification/admin.py avec CustomUserAdmin - 2025-12-10 18:55
- [x] Messages bilingues dans populate_postes.py - 2025-12-10 18:58

#### Phase 8 : Intégration du module Université (19:00-20:00)
- [x] Lecture et analyse du code existant (code/models.py et views.py) - 2025-12-10 19:05
- [x] Création/optimisation de universite/models.py - 2025-12-10 19:15
  - Modèle Universite avec tous les champs nécessaires
  - Modèle Domaine pour les domaines d'études
  - ForeignKey en string pour éviter les imports circulaires
  - Validation des postes dans clean()
  - Support bilingue (arabe/français)
- [x] Création de universite/forms.py - 2025-12-10 19:25
  - UniversiteForm (formulaire complet pour admin)
  - UniversiteProfileUpdateForm (pour recteur)
  - DomaineForm (pour les domaines)
  - Bootstrap 5 avec direction RTL/LTR
- [x] Correction et optimisation de universite/views.py - 2025-12-10 19:35
  - Fonction get_user_universite() pour récupérer l'université de l'utilisateur
  - Vue dashboard_Uni (tableau de bord)
  - Vue profile_Uni (profil de l'université)
  - Vue profileUpdate_Uni (mise à jour du profil)
  - Messages bilingues
- [x] Création de universite/admin.py - 2025-12-10 19:45
  - UniversiteAdmin avec export CSV
  - DomaineAdmin
  - DomaineInline pour gestion inline
  - Affichage du logo avec format_html
- [x] Mise à jour de universite/urls.py - 2025-12-10 19:50
  - URL dashboard/ → dashboard_Uni
  - URL profile/ → profile_Uni
  - URL profile/update/ → profileUpdate_Uni
- [x] Création des templates - 2025-12-10 19:55
  - templates/universite/dashboard_Uni.html
  - templates/universite/profile_Uni.html
  - templates/universite/profileUpdate_Uni.html
  - Design responsive avec Bootstrap 5 RTL
- [x] Mise à jour de guide.md - 2025-12-10 20:00

#### Phase 9 : Intégration du module Commun et création de l'app Enseignant (20:00-20:30)
- [x] Lecture et analyse de code/models.py (19 modèles) - 2025-12-10 20:05
- [x] Lecture et analyse de code/views.py (vue home simple) - 2025-12-10 20:05
- [x] Intégration de 17 nouveaux modèles dans commun/models.py - 2025-12-10 20:10
  - AnneeUniversitaire (avec méthode get_courante())
  - Pays (avec code ISO)
  - Amphi, Salle, Laboratoire (infrastructures)
  - Semestre, Grade, Diplome, Cycle, Niveau, Parcours, Unite (pédagogie)
  - Groupe, Section, Session, Reforme, Identification
  - Optimisation : réduction de null=True, ajout d'indexes, validation
  - Support bilingue complet (arabe/français)
- [x] Amélioration de BaseModel (ajout du champ observation) - 2025-12-10 20:10
- [x] Création de commun/admin.py complet - 2025-12-10 20:12
  - BaseOrganisationAdmin (classe de base DRY)
  - 19 admin classes avec support bilingue
  - Logique spéciale pour AnneeUniversitaire (auto-disable autres années courantes)
- [x] Correction de l'erreur NameError dans admin.py - 2025-12-10 20:15
  - Redéfinition de get_nom_bilingue() dans 9 classes enfants
  - SemestreAdmin, GradeAdmin, DiplomeAdmin, CycleAdmin, NiveauAdmin, ParcoursAdmin, UniteAdmin, SessionAdmin, IdentificationAdmin
- [x] Création du modèle Enseignant dans enseignant/models.py - 2025-12-10 20:18
  - Relation OneToOne avec CustomUser
  - Champs bilingues (nom_ar, nom_fr, prenom_ar, prenom_fr)
  - Grade académique, coordonnées professionnelles, statut
  - Indexes sur matricule, user, est_actif
- [x] Création de enseignant/admin.py (EnseignantAdmin) - 2025-12-10 20:20
  - Affichage bilingue des noms complets
  - Filtres par statut, grade, date
  - Fieldsets organisés par catégorie
- [x] Création des migrations pour commun et enseignant - 2025-12-10 20:22
  - commun: 17 nouveaux modèles + modification de Poste
  - enseignant: 1 nouveau modèle Enseignant
- [x] Application des migrations à PostgreSQL - 2025-12-10 20:23
- [x] Réactivation des champs recteur dans universite/forms.py - 2025-12-10 20:25
- [x] Vérification finale (python manage.py check) - 2025-12-10 20:28
- [x] Mise à jour de guide.md - 2025-12-10 20:30

---

## Structure du Projet

```
smart-univ/
├── apps/
│   ├── academique/
│   │   ├── universite/
│   │   │   ├── urls.py
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   ├── faculte/
│   │   │   ├── urls.py
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   ├── departement/
│   │   │   ├── urls.py
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   ├── enseignant/
│   │   │   ├── urls.py
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   ├── etudiant/
│   │   │   ├── urls.py
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   └── affectation/
│   │       ├── urls.py
│   │       ├── forms.py
│   │       ├── models.py
│   │       └── views.py
│   └── noyau/
│       ├── authentification/
│       │   ├── urls.py
│       │   ├── forms.py
│       │   ├── models.py
│       │   └── views.py
│       └── commun/
│           ├── urls.py
│           ├── forms.py
│           ├── models.py
│           └── views.py
├── config/
│   ├── settings.py
│   └── urls.py
└── manage.py
```

---

## Notes de Développement

### Applications Noyau
Les applications suivantes ont été créées dans `apps/noyau/` :
- **authentification** : Gestion de l'authentification et des utilisateurs
- **commun** : Fonctionnalités communes et partagées

### Applications Académiques
Les applications suivantes ont été créées dans `apps/academique/` :
- **universite** : Gestion des universités
- **faculte** : Gestion des facultés
- **departement** : Gestion des départements
- **enseignant** : Gestion des enseignants
- **etudiant** : Gestion des étudiants
- **affectation** : Gestion des affectations

### Configuration

#### Applications Django
- Toutes les applications utilisent le chemin complet :
  - Noyau : `apps.noyau.xxx`
  - Académique : `apps.academique.xxx`
- Toutes les applications ont des fichiers `urls.py` et `forms.py`
- Les URLs sont configurées dans `config/urls.py` :
  - `/auth/` pour authentification
  - `/commun/` pour fonctionnalités communes
  - `/universite/`, `/faculte/`, `/departement/`, `/enseignant/`, `/etudiant/`, `/affectation/` pour les apps académiques

#### Base de Données PostgreSQL
- **SGBD** : PostgreSQL
- **Nom de la base** : smart_univ___db
- **Utilisateur** : smart_univ___user
- **Host** : localhost
- **Port** : 5432
- Les credentials sont stockés dans le fichier `.env` (non versionné)
- Un fichier `.env.example` est fourni comme template

#### Variables d'Environnement
- Utilisation de `python-decouple` pour gérer les variables sensibles
- Fichier `.env` contient :
  - `SECRET_KEY` : Clé secrète Django
  - `DEBUG` : Mode debug (True/False)
  - `ALLOWED_HOSTS` : Hôtes autorisés
  - Configuration de la base de données (DB_NAME, DB_USER, DB_PASSWORD, etc.)
- Le fichier `.env` est dans `.gitignore` pour la sécurité

#### Internationalisation
- **Langue principale** : Arabe (ar)
- **Langues supportées** : Arabe, Français, Anglais
- **Fuseau horaire** : Africa/Algiers
- **Direction du texte** : RTL (Right-to-Left) pour l'arabe
- Support i18n et l10n activés

#### Interface Utilisateur
- **Framework CSS** : Bootstrap 5 RTL
- **Police arabe** : Cairo (Google Fonts)
- **Icônes** : Font Awesome 6.5.1
- **Design** : Responsive (PC, tablette, smartphone)
- **Template de base** : templates/base.html
- **Page d'accueil** : templates/commun/home.html
- **Navigation** : Menu responsive avec support mobile

#### Dépendances (requirements.txt)
- Django 5.2.9
- psycopg2-binary 2.9.10 (driver PostgreSQL)
- python-decouple 3.8 (variables d'environnement)
- django-debug-toolbar 4.4.6 (debug)
- djangorestframework 3.15.2 (API REST)
- django-crispy-forms 2.3 (formulaires)
- pytz 2024.2 (timezone)

#### Vérifications
- Configuration vérifiée sans erreurs avec `python manage.py check`
- Connexion PostgreSQL testée et fonctionnelle
- Migrations Django appliquées avec succès

### Modèles Implémentés

#### Noyau - Authentification
- **CustomUser** : Modèle utilisateur personnalisé étendant AbstractUser
  - Champs personnalisés : photo, telephone, date_naissance, langue_preferee
  - Relation avec Poste (poste_principal et postes_secondaires)
  - Méthode nom_complet pour affichage bilingue

#### Noyau - Commun
- **BaseModel** : Modèle abstrait avec created_at et updated_at
- **Poste** : Système de rôles/postes universitaires
  - 24 postes prédéfinis (Enseignant → Recteur)
  - Support bilingue (nom_ar, nom_fr, nom_ar_mini, nom_fr_mini)
  - Hiérarchie avec niveau (0-10)
  - Types : enseignant, etudiant, admin, personnel, invite
- **Wilaya** : Provinces algériennes (58 wilayas)
  - Code (01-58)
  - Noms bilingues (arabe/français)

#### Académique - Université
- **Universite** : Gestion des universités
  - Informations de base : code, nom_ar, nom_fr, sigle, logo
  - Responsables : recteur, vice_rect_p, vice_rect_pg (ForeignKey vers Enseignant)
  - Localisation : wilaya, adresse
  - Contacts : téléphones, fax, email, site web
  - Réseaux sociaux : Facebook, X (Twitter), LinkedIn, TikTok, Telegram
  - Validation des postes dans clean()
- **Domaine** : Domaines d'études (ST, SNV, etc.)
  - Relations avec Universite
  - unique_together sur (code, universite)

### Interfaces d'Administration
- **PosteAdmin** : Gestion des postes avec filtres par type et niveau
- **WilayaAdmin** : Gestion des wilayas
- **CustomUserAdmin** : Gestion des utilisateurs avec champs personnalisés
- **UniversiteAdmin** : Gestion des universités avec :
  - Export CSV
  - Affichage du logo
  - DomaineInline pour gestion des domaines
- **DomaineAdmin** : Gestion des domaines d'études

### Vues et Templates Implémentés

#### Université
- **dashboard_Uni** : Tableau de bord du recteur
  - Affichage des informations principales
  - Actions rapides
  - Liste des responsables et domaines
- **profile_Uni** : Profil complet de l'université
  - Toutes les informations détaillées
  - Contacts et réseaux sociaux
- **profileUpdate_Uni** : Mise à jour du profil
  - Formulaire complet avec Bootstrap 5
  - Validation côté client et serveur
  - Support upload d'images (logo)

### Prochaines Étapes
- Créer les migrations pour Wilaya, Universite et Domaine
- Créer les modèles Enseignant, Faculte, Departement
- Implémenter les modules faculte et departement
- Créer le système d'affectation (Ens_Dep)
- Implémenter l'authentification (login/logout)
- Créer le système de permissions basé sur les postes
- Ajouter les statistiques et rapports
