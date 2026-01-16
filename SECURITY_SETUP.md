# 🔐 Configuration Sécurisée - Moustass Video

## ✅ Corrections de Sécurité Appliquées

### Problèmes Corrigés

1. ❌ **Mots de passe en clair dans docker-compose.yml**
   - `auth_password`, `video_password`, `security_password`, `rootpassword`
   - JWT secret exposé : `KAI9JHKCZjgIt157saWm_vLKlcylvfHOi9PVQbKFzXQ`

2. ❌ **Mot de passe hardcodé dans src/videos/database_old.py**
   - `MyStrongP@ss123!` visible en clair dans le code source

### Solutions Implémentées

✅ **Utilisation de variables d'environnement**
- Tous les mots de passe sont maintenant dans des variables d'environnement
- Fichier `.env.example` créé avec des valeurs d'exemple
- `.env` déjà présent dans `.gitignore`

## 📋 Installation et Configuration

### 1️⃣ Créer le fichier .env

```bash
cp .env.example .env
```

### 2️⃣ Générer des mots de passe sécurisés

```bash
# Générer un mot de passe aléatoire (Linux/Mac)
openssl rand -base64 32

# Ou utilisez un générateur de mots de passe en ligne
# https://passwordsgenerator.net/
```

### 3️⃣ Modifier le fichier .env

Ouvrez `.env` et remplacez **TOUS** les mots de passe :

```bash
# ❌ NE PAS FAIRE
JWT_SECRET=CHANGEZ_CETTE_CLE_AVEC_UNE_VALEUR_ALEATOIRE_LONGUE_ET_SECURISEE

# ✅ FAIRE
JWT_SECRET=x8jK2nP9vL4mQ7sW3tY6uA5bC8dE1fG4hJ7kN0pR2sT5vX8yZ1aB4cD6eF9gH2iJ
```

**Variables à configurer obligatoirement :**
- `JWT_SECRET` - Clé de signature des tokens JWT (32+ caractères)
- `MYSQL_ROOT_PASSWORD` - Mot de passe root MySQL
- `VIDEO_DB_PASSWORD` - Mot de passe base vidéos
- `AUTH_DB_PASSWORD` - Mot de passe base auth
- `SECURITY_DB_PASSWORD` - Mot de passe base sécurité

### 4️⃣ Vérifier que .env est ignoré par git

```bash
# Le fichier .env NE DOIT PAS apparaître dans git status
git status

# Si .env apparaît, ajoutez-le au .gitignore
echo ".env" >> .gitignore
```

### 5️⃣ Démarrer les services

```bash
docker compose up -d
```

## 🚨 Bonnes Pratiques de Sécurité

### ✅ À FAIRE

- ✅ Utiliser des mots de passe différents pour chaque service
- ✅ Mots de passe d'au moins 32 caractères aléatoires
- ✅ Changer tous les mots de passe par défaut
- ✅ Garder le fichier `.env` local uniquement
- ✅ Documenter les variables d'environnement dans `.env.example`
- ✅ Utiliser un gestionnaire de secrets en production (Vault, AWS Secrets Manager, etc.)

### ❌ À NE PAS FAIRE

- ❌ Committer le fichier `.env` dans git
- ❌ Partager les mots de passe par email/Slack
- ❌ Réutiliser les mots de passe d'exemple
- ❌ Utiliser des mots de passe courts ou prévisibles
- ❌ Hardcoder des secrets dans le code source
- ❌ Laisser les valeurs par défaut en production

## 🔍 Vérification de Sécurité

### Vérifier qu'aucun secret n'est dans git

```bash
# Chercher des mots de passe potentiels dans l'historique git
git log -p | grep -i "password"
git log -p | grep -i "secret"

# Scanner le projet avec Snyk
snyk test
```

### Vérifier la configuration actuelle

```bash
# Afficher les variables d'environnement (sans les valeurs sensibles)
docker compose config | grep -E "(MYSQL_|JWT_|PASSWORD)" | sed 's/:.*/: ****/'
```

## 📁 Structure des Fichiers

```
.
├── .env                    # ❌ Git ignoré - Contient les vrais secrets
├── .env.example            # ✅ Git tracké - Valeurs d'exemple
├── .gitignore              # ✅ Contient .env
├── docker-compose.yml      # ✅ Utilise ${VARIABLES}
└── src/
    └── videos/
        └── database_old.py # ✅ Utilise os.environ
```

## 🛡️ En Production

### Variables d'environnement recommandées

1. **Kubernetes** : Utilisez des Secrets Kubernetes
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: moustass-secrets
   type: Opaque
   data:
     jwt-secret: <base64_encoded>
   ```

2. **Docker Swarm** : Utilisez Docker Secrets
   ```bash
   echo "mot_de_passe_fort" | docker secret create mysql_root_password -
   ```

3. **Cloud** : Utilisez les services de secrets natifs
   - AWS: Secrets Manager / Parameter Store
   - GCP: Secret Manager
   - Azure: Key Vault

## 📚 Références

- [OWASP - Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [12 Factor App - Config](https://12factor.net/config)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
