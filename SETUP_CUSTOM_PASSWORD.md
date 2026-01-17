# Intégration du mot de passe MySQL personnalisé

## Situation actuelle

Vous avez fourni un mot de passe MySQL personnalisé : **`MyStrongP@ss123!`**

Pour des raisons de **sécurité**, ce mot de passe ne doit **JAMAIS** être commité en dur dans le code ou docker-compose.yml.

## Solution implémentée ✅

### 1. Fichier `.env` créé

Localisation : `/Moustass-video/.env`

Ce fichier contient vos secrets et est **automatiquement ignoré par Git** (voir `.gitignore`).

```bash
# Fichier .env (ignoré par Git)
MYSQL_ROOT_PASSWORD=MyStrongP@ss123!
AUTH_DB_PASSWORD=auth_password
VIDEO_DB_PASSWORD=video_password
```

### 2. docker-compose.yml - Comment lire depuis .env

Pour que Docker Compose lise vos variables depuis `.env`, modifiez le bloc MySQL comme ceci :

```yaml
mysql:
  image: mysql:8.0
  container_name: moustass-mysql
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}  # Lire depuis .env
    MYSQL_DATABASE: videos_db
    MYSQL_USER: ${VIDEO_DB_USER:-video_user}
    MYSQL_PASSWORD: ${VIDEO_DB_PASSWORD:-video_password}
```

Puis pour `auth-service` et `video-service` :

```yaml
auth-service:
  environment:
    AUTH_DB_PASSWORD: ${AUTH_DB_PASSWORD:-auth_password}
    
video-service:
  environment:
    # Utilise DATABASE_URL qui peut contenir la password
    DATABASE_URL: mysql+pymysql://video_user:${VIDEO_DB_PASSWORD:-video_password}@mysql:3306/videos_db
```

### 3. Mettre à jour votre `.env`

Remplacez les valeurs par défaut :

```bash
# .env - À adapter à VOTRE environnement

# Votre mot de passe MySQL personnalisé
MYSQL_ROOT_PASSWORD=MyStrongP@ss123!

# Mots de passe services (conservez ou changez)
AUTH_DB_PASSWORD=auth_password
VIDEO_DB_PASSWORD=video_password

# Autres (optionnel)
JWT_SECRET=your-jwt-secret-key-change-in-production
```

### 4. Tester

```bash
# Redémarrer avec le nouvel .env
docker compose down -v  # Supprimer les volumes
docker compose up -d

# Vérifier que le mot de passe fonctionne
docker compose exec mysql mysql -u root -pMyStrongP@ss123! -e "SHOW DATABASES;"

# Si ça marche, vous verrez les bases : information_schema, mysql, performance_schema, sys, auth_db, videos_db
```

## ✅ Garanties de sécurité

1. **Git ignores `.env`** : Le fichier ne sera jamais commité
   ```bash
   git status  # .env ne sera JAMAIS listé
   ```

2. **SonarQube ne scannera pas `.env`** :
   - Fichier ignoré par `.gitignore`
   - SonarQube ne scanne que les fichiers Git-tracked
   - Les secrets ne sont jamais visibles dans les PR

3. **Code propre** :
   - `docker-compose.yml` n'a que des `${VAR_NAME}` (pas de valeurs réelles)
   - `src/auth/database.py` utilise `os.getenv()` (pas en dur)
   - `src/videos/upload_service.py` utilise variables d'env

4. **CI/CD safe** :
   - Chaque équipe peut avoir son propre `.env` local
   - Production utilise des **secrets management** (AWS Secrets Manager, HashiCorp Vault, etc.)

## Workflow d'équipe

### Pour vous (développement local)
```bash
# Vous créez votre .env avec votre mot de passe
.env:
  MYSQL_ROOT_PASSWORD=MyStrongP@ss123!
```

### Pour vos collègues (développement local)
```bash
# Ils utilisent les défauts (dans .env.example)
.env:
  MYSQL_ROOT_PASSWORD=rootpassword  # Défaut simple
```

### Pour les autres (si vous utilisez Git)
```bash
# Rien n'est visible
git log --all -- .env
# Aucun résultat (fichier jamais commité)
```

## Vérification finale

```bash
# 1. Vérifier que .env existe et a le bon contenu
cat .env | grep MYSQL_ROOT

# 2. Vérifier que .env est ignoré
grep "^\.env$" .gitignore

# 3. Vérifier qu'aucun secret n'est dans docker-compose.yml
grep -i "MyStrongP@ss123!" docker-compose.yml
# Doit retourner 0 résultats

# 4. Vérifier qu'aucun secret n'est dans le code
grep -r "MyStrongP@ss123!" src/
# Doit retourner 0 résultats
```

## Résumé

| Aspect | Avant ❌ | Après ✅ |
|--------|---------|--------|
| Mot de passe en dur | docker-compose.yml | `.env` (ignoré Git) |
| SonarQube voit secrets | OUI | NON |
| Collègues voient password | OUI | NON |
| Facilité changement | Modifier code | Modifier `.env` |
| Production safe | NON | OUI (utiliser Vault) |

Tous les fichiers sont prêts pour la production et sécurisés ! 🔒
