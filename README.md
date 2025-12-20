# Smart-Univ - Système de Gestion Universitaire

Système de gestion universitaire développé avec Django et PostgreSQL.

## Prérequis

- Python 3.11+
- PostgreSQL 12+
- pip (gestionnaire de paquets Python)

## Installation

### 1. Cloner le projet

```bash
cd d:\PROJETCS\smart-univ
```

### 2. Créer et activer l'environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows
venv\Scripts\activate

# Sur Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données PostgreSQL

Créez la base de données PostgreSQL :

```sql
CREATE USER your_db_user WITH PASSWORD 'your_password';
CREATE DATABASE your_db_name WITH OWNER your_db_user;
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
\c your_db_name
GRANT ALL ON SCHEMA public TO your_db_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO your_db_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO your_db_user;
GRANT CREATE ON SCHEMA public TO your_db_user;
```

### 5. Configuration des variables d'environnement

Copiez le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

Modifiez le fichier `.env` avec vos paramètres :

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 6. Appliquer les migrations

```bash
python manage.py migrate
```

### 7. Créer un superutilisateur (optionnel)

```bash
python manage.py createsuperuser
```

### 8. Lancer le serveur de développement

```bash
python manage.py runserver
```

Le projet sera accessible à l'adresse : http://127.0.0.1:8000/

Interface d'administration : http://127.0.0.1:8000/admin/

## Structure du Projet

```
smart-univ/
├── apps/
│   ├── academique/          # Applications académiques
│   │   ├── universite/      # Gestion des universités
│   │   ├── faculte/         # Gestion des facultés
│   │   ├── departement/     # Gestion des départements
│   │   ├── enseignant/      # Gestion des enseignants
│   │   ├── etudiant/        # Gestion des étudiants
│   │   └── affectation/     # Gestion des affectations
│   └── noyau/              # Applications noyau
│       ├── authentification/ # Authentification et utilisateurs
│       └── commun/          # Fonctionnalités communes
├── config/                  # Configuration Django
│   ├── settings.py         # Paramètres du projet
│   └── urls.py             # URLs principales
├── venv/                    # Environnement virtuel (non versionné)
├── .env                     # Variables d'environnement (non versionné)
├── .env.example            # Template des variables d'environnement
├── .gitignore              # Fichiers à ignorer par Git
├── requirements.txt        # Dépendances Python
├── manage.py              # Script de gestion Django
└── README.md              # Ce fichier
```

## Applications

### Applications Noyau
- **authentification** : Gestion de l'authentification et des utilisateurs
- **commun** : Fonctionnalités communes et partagées

### Applications Académiques
- **universite** : Gestion des universités
- **faculte** : Gestion des facultés
- **departement** : Gestion des départements
- **enseignant** : Gestion des enseignants
- **etudiant** : Gestion des étudiants
- **affectation** : Gestion des affectations

## Technologies Utilisées

- **Backend** : Django 5.2.9
- **Base de données** : PostgreSQL
- **Driver BDD** : psycopg2-binary 2.9.10
- **Variables d'environnement** : python-decouple 3.8
- **Debug** : django-debug-toolbar 4.4.6
- **API REST** : djangorestframework 3.15.2
- **Formulaires** : django-crispy-forms 2.3
- **Timezone** : pytz 2024.2

## Commandes Utiles

```bash
# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver

# Vérifier la configuration
python manage.py check

# Lancer le shell Django
python manage.py shell

# Collecter les fichiers statiques
python manage.py collectstatic
```

## Développement

Ce projet suit les bonnes pratiques Django avec une architecture modulaire.

## Sécurité

- Le fichier `.env` contient des informations sensibles et ne doit **jamais** être versionné
- Assurez-vous que `.env` est dans `.gitignore`
- Changez la `SECRET_KEY` en production
- Mettez `DEBUG=False` en production
- Configurez correctement `ALLOWED_HOSTS` en production

## Licence

Projet académique - Smart-Univ

## Auteurs

Projet de gestion universitaire développé pour [nom de votre institution]
