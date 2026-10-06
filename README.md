# Smart-Univ - Système de Gestion Universitaire

Système de gestion universitaire (université, facultés, départements, enseignants, étudiants,
emplois du temps, séances, absences, notes), bilingue arabe / français, développé avec Django et PostgreSQL.

## Prérequis

- Python 3.13
- PostgreSQL 15+
- Git

## Installation

```bash
git clone https://github.com/ahmedghali/smart-univ.git
cd smart-univ
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Linux / macOS
pip install -r requirements/dev.txt
copy .env.example .env            # Windows (cp sous Linux / macOS), puis renseigner les valeurs
pre-commit install
python manage.py migrate
python manage.py populate_postes  # postes de base (enseignant, chef de département, doyen...)
python manage.py createsuperuser
python manage.py runserver
```

- Application : http://localhost:8000
- Administration générale : http://localhost:8000/admin/
- Administration du département (chef de département) : http://localhost:8000/departement/admin/

## Tests et qualité du code

```bash
pytest
ruff check .
ruff format --check .
```

pytest crée sa propre base de test : l'utilisateur PostgreSQL doit avoir le droit `CREATEDB`.
La CI GitHub Actions lance les mêmes contrôles à chaque push.

## Déploiement (Railway)

1. Créer un projet Railway avec un service PostgreSQL et lier ce dépôt.
2. Définir les variables du service :

| Variable | Valeur |
|----------|--------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `SECRET_KEY` | valeur longue et aléatoire |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `ALLOWED_HOSTS` | domaines personnalisés, séparés par des virgules (le domaine Railway est ajouté automatiquement) |
| `MEDIA_ROOT` | chemin d'un volume Railway pour les logos (optionnel) |

`railway.toml` applique les migrations avant chaque déploiement, collecte les fichiers statiques
et démarre Gunicorn. La version de Python vient de `.python-version`.

## Structure du projet

```
smart-univ/
├── apps/
│   ├── noyau/
│   │   ├── authentification/   # Utilisateurs, connexion, choix du rôle et du poste
│   │   └── commun/             # Référentiels, postes, affectations de postes, permissions
│   └── academique/
│       ├── universite/
│       ├── faculte/
│       ├── departement/
│       │   ├── dep_admin/      # Admin du chef de département (site, mixins, admins, import)
│       │   └── templates/departement/
│       ├── enseignant/
│       │   ├── views/          # Vues par fonctionnalité (emploi du temps, séances, notes...)
│       │   └── services.py     # Logique partagée
│       ├── etudiant/
│       └── affectation/        # Classes, séances, absences, notes, affectations enseignant-département
├── config/
│   ├── settings/               # base.py, dev.py, prod.py, test.py
│   └── urls.py
├── requirements.txt            # Dépendances de production
├── requirements/dev.txt        # + outils de développement
├── templates/                  # Gabarits communs et surcharges de l'admin
├── static/
├── tests/
├── pyproject.toml              # Configuration de ruff et pytest
└── railway.toml
```

## Rôles et permissions

- Un **poste** (chef de département, doyen, recteur, adjoints...) est attribué à un utilisateur par une
  **affectation de poste** (`AffectationPoste`) : dans une université, une faculté ou un département,
  pour une année universitaire.
- Les droits de chaque poste (voir / ajouter / modifier / supprimer, module par module) se règlent dans
  l'administration, sur la fiche du poste (`PostePermission`).
- À la connexion, l'utilisateur choisit son rôle ; un enseignant qui occupe un poste peut basculer vers
  son tableau de bord administratif.

## Sécurité

- Le fichier `.env` contient des informations sensibles et n'est jamais versionné.
- En production : `SECRET_KEY` propre, `DEBUG=False`, HTTPS forcé (déjà configuré dans `config/settings/prod.py`).

## Licence

Projet académique - Smart-Univ
