# Guide d'Import/Export Excel - Smart-Univ

## Configuration réussie ✅

django-import-export est maintenant configuré pour tous les modèles de l'application.

## Comment utiliser l'import/export

### 1. Accéder à l'interface admin

1. Lancez le serveur : `python manage.py runserver`
2. Connectez-vous à l'admin : http://127.0.0.1:8000/admin/
3. Sélectionnez le modèle que vous souhaitez importer/exporter

### 2. Exporter des données

Dans la page de liste de n'importe quel modèle :
1. Cliquez sur le bouton **"Export"** en haut à droite
2. Choisissez le format : **Excel (xlsx)**, CSV, JSON, etc.
3. Le fichier est téléchargé automatiquement

### 3. Importer des données

Dans la page de liste de n'importe quel modèle :
1. Cliquez sur le bouton **"Import"** en haut à droite
2. Choisissez votre fichier Excel (.xlsx) ou CSV
3. Prévisualisez les données
4. Confirmez l'import

## Formats de fichiers Excel requis

### 📊 Wilayas (58 wilayas algériennes)

**Fichier : wilayas.xlsx**

| id | code | nom_ar | nom_fr |
|----|------|--------|--------|
| 1 | 01 | الجزائر | Alger |
| 2 | 02 | البليدة | Blida |
| 3 | 03 | البويرة | Bouira |
| ... | ... | ... | ... |

**Colonnes requises :**
- `code` : Code wilaya (01-58)
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français

---

### 🌍 Pays

**Fichier : pays.xlsx**

| id | code | nom_ar | nom_fr |
|----|------|--------|--------|
| 1 | DZA | الجزائر | Algérie |
| 2 | FRA | فرنسا | France |
| 3 | TUN | تونس | Tunisie |
| 4 | MAR | المغرب | Maroc |

**Colonnes requises :**
- `code` : Code ISO 3 lettres
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français

---

### 🎓 Grades académiques

**Fichier : grades.xlsx**

| id | code | nom_ar | nom_fr |
|----|------|--------|--------|
| 1 | PROF | أستاذ التعليم العالي | Professeur |
| 2 | MCA | أستاذ محاضر أ | Maître de Conférences A |
| 3 | MCB | أستاذ محاضر ب | Maître de Conférences B |
| 4 | MAA | أستاذ مساعد أ | Maître Assistant A |
| 5 | MAB | أستاذ مساعد ب | Maître Assistant B |

**Colonnes requises :**
- `code` : Code unique
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français

---

### 📚 Cycles d'études

**Fichier : cycles.xlsx**

| id | code | nom_ar | nom_fr |
|----|------|--------|--------|
| 1 | L | ليسانس | Licence |
| 2 | M | ماستر | Master |
| 3 | D | دكتوراه | Doctorat |

**Colonnes requises :**
- `code` : L, M, D
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français

---

### 📖 Niveaux d'études

**Fichier : niveaux.xlsx**

| id | code | nom_ar | nom_fr |
|----|------|--------|--------|
| 1 | L1 | السنة الأولى ليسانس | Première année Licence |
| 2 | L2 | السنة الثانية ليسانس | Deuxième année Licence |
| 3 | L3 | السنة الثالثة ليسانس | Troisième année Licence |
| 4 | M1 | السنة الأولى ماستر | Première année Master |
| 5 | M2 | السنة الثانية ماستر | Deuxième année Master |
| 6 | D | دكتوراه | Doctorat |

**Colonnes requises :**
- `code` : L1, L2, L3, M1, M2, D
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français

---

### 📝 Sessions d'examens

**Fichier : sessions.xlsx**

| id | code | nom_ar | nom_fr |
|----|------|--------|--------|
| 1 | NORM | دورة عادية | Session Normale |
| 2 | RATT | دورة استدراكية | Session de Rattrapage |

**Colonnes requises :**
- `code` : NORM, RATT
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français

---

### 🏛️ Universités

**Fichier : universites.xlsx**

| id | code | nom_ar | nom_fr | sigle | wilaya | adresse | telmobile | email | siteweb |
|----|------|--------|--------|-------|--------|---------|-----------|-------|---------|
| 1 | USTHB | جامعة هواري بومدين | Université Houari Boumediene | USTHB | 01 | Bab Ezzouar | 0555123456 | contact@usthb.dz | https://usthb.dz |

**Colonnes requises :**
- `code` : Code unique de l'université
- `nom_ar` : Nom en arabe
- `nom_fr` : Nom en français
- `sigle` : Sigle de l'université
- `wilaya` : Code wilaya (doit exister dans la table Wilaya)
- `email` : Email de contact
- `siteweb` : Site web

**Colonnes optionnelles :**
- `adresse`, `telmobile`, `telfix1`, `telfix2`, `fax`
- `facebook`, `x_twitter`, `linkedIn`, `tiktok`, `telegram`

---

### 👨‍🏫 Enseignants

**Fichier : enseignants.xlsx**

| id | matricule | nom_ar | nom_fr | prenom_ar | prenom_fr | grade | email_pro | telephone_pro | bureau | est_actif |
|----|-----------|--------|--------|-----------|-----------|-------|-----------|---------------|--------|-----------|
| 1 | ENS2024001 | بن علي | Ben Ali | محمد | Mohamed | Professeur | m.benali@univ.dz | 0555123456 | A201 | TRUE |

**Colonnes requises :**
- `matricule` : Matricule unique
- `nom_ar` / `nom_fr` : Nom en arabe/français
- `prenom_ar` / `prenom_fr` : Prénom en arabe/français
- `est_actif` : TRUE/FALSE

**Colonnes optionnelles :**
- `grade`, `email_pro`, `telephone_pro`, `bureau`

---

## Conseils pour l'import

### ✅ Bonnes pratiques

1. **Exportez d'abord un fichier vide** pour voir la structure exacte
2. **Respectez les types de données** :
   - Dates : Format YYYY-MM-DD (ex: 2024-09-15)
   - Booléens : TRUE/FALSE ou 1/0
   - Nombres : Sans espace ni virgule
3. **Vérifiez les relations** :
   - Les ForeignKey doivent référencer des IDs existants
   - Ex: Pour `wilaya`, utilisez le code wilaya existant
4. **Encodez en UTF-8** pour les caractères arabes
5. **Évitez les cellules vides** pour les champs requis

### ⚠️ Erreurs communes

- **Doublons** : Code ou ID déjà existant
- **Relations invalides** : ForeignKey vers un objet inexistant
- **Format de date incorrect** : Utilisez YYYY-MM-DD
- **Caractères mal encodés** : Vérifiez l'encodage UTF-8

### 🔄 Mise à jour de données existantes

Pour mettre à jour des données existantes :
1. Incluez la colonne `id` dans votre fichier Excel
2. Utilisez l'ID de l'objet existant
3. Lors de l'import, choisissez "Update existing records"

---

## Exemples de fichiers prêts à l'emploi

Créez ces fichiers Excel dans un dossier `data/` :

```
smart-univ/
├── data/
│   ├── wilayas.xlsx          # 58 wilayas algériennes
│   ├── pays.xlsx             # Liste des pays
│   ├── grades.xlsx           # Grades académiques
│   ├── cycles.xlsx           # Cycles d'études
│   ├── niveaux.xlsx          # Niveaux d'études
│   ├── sessions.xlsx         # Sessions d'examens
│   ├── diplomes.xlsx         # Diplômes
│   ├── universites.xlsx      # Universités
│   └── enseignants.xlsx      # Enseignants
```

---

## Support et Documentation

- **Documentation officielle** : https://django-import-export.readthedocs.io/
- **Formats supportés** : Excel (.xlsx), CSV, JSON, YAML, ODS, HTML
- **Encodage recommandé** : UTF-8 avec BOM pour Excel

---

## Commandes utiles

```bash
# Vérifier la configuration
python manage.py check

# Lancer le serveur
python manage.py runserver

# Accéder à l'admin
# http://127.0.0.1:8000/admin/
```

---

✅ **Configuration terminée avec succès !**

Vous pouvez maintenant importer/exporter des données Excel dans tous les modèles de l'application.
