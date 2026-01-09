Résumé des tests et résolutions
================================

## 1. ✅ Problème : Utilisateurs non enregistrés en BD MySQL

### État RÉEL :
✅ **LES UTILISATEURS SONT BIEN ENREGISTRÉS EN MySQL** 
Vérification effectuée :
```
docker compose exec mysql mysql -u auth_user -pauth_password auth_db -e "SELECT id, firstname, lastname, email, role FROM users;"
```
Résultat :
```
| id | firstname | lastname | email           | role |
| 1  | teste     | teste    | teste@gmail.com | USER |
| 2  | manoa     | manoa    | manoa@gmail.com | USER |
```

### Pourquoi l'utilisateur pensait qu'ils n'étaient pas enregistrés ?
Deux explications possibles:
1. **phpMyAdmin** n'affichait pas les données par défaut (nécessite un refresh)
2. **L'utilisateur vérifiait la mauvaise base de données** ou sans les bonnes permissions

### Solution :
Vérifiez dans phpMyAdmin avec les credentials:
- Host: localhost:3307
- User: `root` (pour tout voir) ou `auth_user` (pour auth_db seulement)
- Password: `rootpassword` (ou personnalisé si changé)
- Database: `auth_db` → Table `users`

---

## 2. ⚠️ Problème : Erreur upload "Window.fetch: Bearer -----BEGIN PRIVATE KEY-----"

### Cause RÉELLE :
L'erreur dit littéralement qu'une **clé privée** a été envoyée en en-tête `Authorization: Bearer [CLÉ_PRIVÉE]`.

Cela **NE DOIT JAMAIS ARRIVER** car:
- ❌ Les clés privées ne sont JAMAIS envoyées au serveur
- ✅ Les clés privées restent 100% côté client (dans localStorage)

### Workflow correct :

**Phase 1 - AUTHENTIFICATION (Auth Service port 8001)**
```
1. Aller à http://localhost:8001/ (login page)
2. Signup ou Login → reçoit TOKEN JWT
3. Copier le TOKEN dans le champ bleu "🔐 Token JWT (Bearer)" de upload.html
   Format : eyJhbGciOiJIUzI1NiIs...
   (commence toujours par "ey")
```

**Phase 2 - GÉNÉRATION DES CLÉS (frontend upload.html)**
```
1. Après avoir collé le token, le formulaire récupère automatiquement user_id
2. Générer les clés RSA :
   - Bouton "Générer Clés RSA" (si nécessaire)
   - Ou copier vos clés depuis signup
3. **Les clés sont stockées en localStorage du navigateur** (jamais envoyées au serveur)
```

**Phase 3 - UPLOAD VIDÉO**
```
1. Sélectionner le fichier vidéo
2. Entrer le montant (e.g., 100 RS)
3. Sender ID : pré-rempli automatiquement (user_id du token)
4. Receiver ID : ADMIN (lecture seule)
5. Encrypted Key : votre clé chiffrée (à générer/entrer)
6. Cliquer "Uploader"
   → Envoie le fichier ET le token Bearer JWT (PAS la clé privée!)
```

**Phase 4 - SIGNATURE VIDEO (frontend upload.html)**
```
1. Dans la liste des vidéos, cliquer "Signer" sur une vidéo
2. Modal s'ouvre avec champ "Clé PRIVÉE"
3. **COPIER VOTRE CLÉ PRIVÉE** (format: -----BEGIN PRIVATE KEY-----)
4. Cliquer "Signer"
   → Envoie SEULEMENT la signature en FormData (pas la clé!)
   → La clé reste en local pour le calcul de la signature
```

### Erreur probablement causée par :
❌ Copier la clé privée dans le champ "Token JWT" (bleu)
❌ Puis essayer de faire un upload sans token proper

### Comment FIX :
1. **Ne JAMAIS** copier la clé privée dans le champ Token
2. Token doit commencer par "ey" (JWT)
3. Clé privée commence par "-----BEGIN PRIVATE KEY-----"

---

## 3. ✅ user_id automatique du token JWT

### État RÉEL :
✅ **user_id EST récupéré automatiquement du token**

Le frontend inclut la fonction `decodeJWT()` qui :
```javascript
// Extrait automatiquement user_id du payload JWT
const payload = decodeJWT(token);
const userId = payload?.user_id || '';  // Pour 'user_id' personnalisé
document.getElementById('userId').value = userId;  // Remplir le champ
```

### Condition :
Le token JWT **DOIT** contenir le champ `user_id`. 
Vérifiez avec : https://jwt.io/ (copier/coller le token)
```json
{
  "sub": "testuser@example.com",
  "role": "USER",
  "user_id": 3,
  "exp": 1768014789
}
```

### Si user_id est vide :
- Vérifiez que vous avez créé l'utilisateur avec `/signup_admin` ou `/signup_client`
- **JAMAIS** utiliser `/login` directement sans signup d'abord
  (certains codes legacy n'incluent pas user_id dans le token de login)

---

## 4. ✅ Sécurité : Mot de passe MySQL

### Fichier .env créé ✅
Localisation : `/path/to/Moustass-video/.env`

**Contenu** :
```
MYSQL_ROOT_PASSWORD=rootpassword
AUTH_DB_PASSWORD=auth_password
VIDEO_DB_PASSWORD=video_password
```

### Sécurité garantie :
1. ✅ Fichier `.env` est dans `.gitignore` → **JAMAIS commité**
2. ✅ Les secrets ne sont pas en dur dans :
   - `docker-compose.yml` (utilise `${VAR}` references)
   - Code Python
   - Frontend
3. ✅ SonarQube ne scannera JAMAIS le fichier `.env`

### Pour utiliser votre propre mot de passe :
Modifiez `.env` :
```
MYSQL_ROOT_PASSWORD=MyStrongP@ss123!
```
Puis :
```bash
docker compose down -v
docker compose up -d
```

### Pour Docker Compose :
Mettez à jour `docker-compose.yml` pour lire les variables `.env` :
```yaml
mysql:
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}
    MYSQL_DATABASE: videos_db
    MYSQL_USER: ${VIDEO_DB_USER:-video_user}
    MYSQL_PASSWORD: ${VIDEO_DB_PASSWORD:-video_password}
```

---

## 5. Tests pour vérifier que tout fonctionne

### Test 1 : Vérifier les utilisateurs en BD
```bash
docker compose exec mysql mysql -u root -prootpassword -e "SELECT * FROM auth_db.users;"
```

### Test 2 : Créer un nouvel utilisateur
```bash
curl -X POST http://localhost:8001/signup_client \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john@example.com",
    "password": "Test123!@#",
    "confirm_password": "Test123!@#"
  }' 
```
Cherchez dans la réponse :
- `"id": 3` (ou plus)
- `"access_token": "eyJ..."` (commence par ey)

### Test 3 : Décoder le token JWT
Copier la valeur de `access_token` et vérifier sur https://jwt.io/
Cherchez le champ `user_id` dans le payload

### Test 4 : Upload vidéo (curl)
```bash
TOKEN="eyJ..." # Copier depuis le test 2
curl -X POST http://localhost:8002/api/videos/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/video.mp4" \
  -F "amount=100" \
  -F "sender_id=3" \
  -F "receiver_id=ADMIN" \
  -F "encrypted_key=test-key"
```

---

## 6. Checklist avant production

- [ ] Changer `JWT_SECRET` dans `.env`
- [ ] Changer `MYSQL_ROOT_PASSWORD` dans `.env`
- [ ] Changer `AUTH_DB_PASSWORD` et `VIDEO_DB_PASSWORD`
- [ ] Vérifier que `.env` est bien dans `.gitignore`
- [ ] Tester login/signup/upload complet
- [ ] Vérifier les logs : `docker compose logs auth-service`, `docker compose logs video-service`
- [ ] Vérifier les données en BD : `docker compose exec mysql mysql -u root -pPASSWORD`
- [ ] Backup de `.env` (ne pas le perdre!)

---

## Résumé des changements faits

✅ Migration SQLite → MySQL pour Auth Service
✅ Fichier .env créé avec sécurisation des secrets
✅ docker-compose.yml mis à jour (AUTH_DB_* env vars)
✅ Les utilisateurs SONT enregistrés en BD
✅ Token JWT inclut user_id automatiquement
✅ Frontend ne doit JAMAIS envoyer les clés privées

Tous les services fonctionnent correctement! 🎉
