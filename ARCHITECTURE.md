# Architecture Microservices - Moustass Video

## Vue d'ensemble

Moustass Video est une plateforme de gestion vidéo sécurisée basée sur une architecture microservices.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Auth Service   │      │ Video Service   │      │Security Service │
│   (port 8001)   │◄────►│   (port 8002)   │◄────►│   (port 8003)   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                         │
         └────────────────────────┴─────────────────────────┘
                                  │
                          ┌───────▼────────┐
                          │  MySQL (3307)  │
                          │  - auth_db     │
                          │  - videos_db   │
                          │  - security_db │
                          └────────────────┘
```

## 🔒 Security Service (Port 8003)

**Responsabilité** : Centraliser toutes les opérations de sécurité

### Fonctionnalités

#### 1. Cryptographie RSA
- `POST /api/security/keys/generate` - Générer paire RSA-3072
- `POST /api/security/sign` - Signer des données
- `POST /api/security/verify` - Vérifier signatures

#### 2. Chiffrement AES-GCM
- `POST /api/security/aes/generate-key` - Générer clé AES
- `POST /api/security/aes/encrypt` - Chiffrer données
- `POST /api/security/aes/decrypt` - Déchiffrer données

#### 3. Validation JWT
- `POST /api/security/validate-token` - Valider token JWT

#### 4. Scans de sécurité
- `POST /api/security/scan/snyk-code` - Scanner code source
- `POST /api/security/scan/snyk-deps` - Scanner dépendances
- `POST /api/security/scan/sonarqube` - Analyse qualité code
- `GET /api/security/scan/summary` - Rapport complet
- `GET /api/security/scan/history` - Historique scans

#### 5. Audit
- `GET /api/security/audit/logs` - Logs d'audit sécurité

### Base de données (`security_db`)
- `security_audit_logs` : Logs de toutes les opérations de sécurité
- `scan_results` : Résultats scans Snyk/SonarQube

### Variables d'environnement
```bash
JWT_SECRET=your-jwt-secret
MYSQL_HOST=mysql
MYSQL_USER=security_user
MYSQL_PASSWORD=security_password
SNYK_TOKEN=your-snyk-token          # Optionnel
SONAR_TOKEN=your-sonar-token        # Optionnel
SONAR_HOST_URL=http://localhost:9000
```

---

## 🔐 Auth Service (Port 8001)

**Responsabilité** : Authentification et gestion utilisateurs

### Fonctionnalités
- Signup/Login (CLIENT, ADMIN)
- Gestion clés RSA (délégué à Security service)
- Tokens JWT
- Logs de connexion
- Dashboard admin

### Base de données (`auth_db`)
- `users` : Utilisateurs et clés publiques RSA
- `auth_logs` : Logs de connexion

### Dépendances
- **Security Service** : Génération clés RSA

---

## 🎬 Video Service (Port 8002)

**Responsabilité** : Gestion vidéos (upload, signature, téléchargement)

### Fonctionnalités
- Upload vidéo chiffrée
- Signature vidéo (délégué à Security service)
- Vérification signature (délégué à Security service)
- Téléchargement
- Gestion expiration
- Liste vidéos

### Base de données (`videos_db`)
- `videos` : Métadonnées vidéos

### Dépendances
- **Security Service** : Signature/vérification
- **Auth Service** : Validation JWT (via Security)

---

## 📦 Déploiement Docker

### Lancement complet
```bash
docker-compose up --build
```

### Services
- **auth-service** : `http://localhost:8001`
- **video-service** : `http://localhost:8002`
- **security-service** : `http://localhost:8003`
- **mysql** : `localhost:3307`

### Ordre de démarrage
1. MySQL (healthcheck)
2. Security Service (healthcheck)
3. Auth Service (dépend de MySQL + Security)
4. Video Service (dépend de MySQL + Security + Auth)

---

## 🔄 Flux de données

### 1. Inscription utilisateur (Signup)
```
Client → Auth Service → Security Service (génère RSA) → Auth DB
                            ↓
                       Retourne clé privée (1x seulement)
```

### 2. Upload vidéo
```
Client → Video Service (JWT validé via Security) → Upload fichier → Videos DB
```

### 3. Signature vidéo
```
Client → Video Service → Security Service (signe hash) → Videos DB (stocke signature)
```

### 4. Vérification signature
```
Client → Video Service → Security Service (vérifie signature) → Retourne résultat
```

### 5. Scan sécurité
```
Admin → Security Service → Snyk/SonarQube CLI → Scan DB → Retourne rapport
```

---

## 🛡️ Sécurité

### Principes
- **Clés privées** : Jamais stockées serveur (retour 1x au client)
- **Clés publiques** : Stockées en DB pour vérification
- **JWT** : Secret partagé entre services
- **Crypto** : RSA-3072, AES-256-GCM
- **Audit** : Logs de toutes opérations sensibles

### Scans automatiques
- **Snyk Code** : Vulnérabilités code source
- **Snyk Deps** : Vulnérabilités dépendances
- **SonarQube** : Qualité + sécurité code

---

## 📊 Monitoring

### Health checks
- `http://localhost:8001/health` - Auth
- `http://localhost:8002/health` - Video
- `http://localhost:8003/health` - Security

### Documentation API
- `http://localhost:8001/docs` - Auth Swagger
- `http://localhost:8002/docs` - Video Swagger
- `http://localhost:8003/docs` - Security Swagger

### Logs audit
```bash
# Logs Security service
curl http://localhost:8003/api/security/audit/logs

# Historique scans
curl http://localhost:8003/api/security/scan/history
```

---

## 🚀 Workflow développement

### 1. Lancer l'infrastructure
```bash
docker-compose up -d mysql security-service
```

### 2. Développement local
```bash
# Auth service
cd src/auth
python -m auth_api

# Video service
cd src/videos
python -m upload_service

# Security service
cd src/security
python -m security_service
```

### 3. Tests
```bash
# Tester Security service
curl http://localhost:8003/api/security/keys/generate -X POST -F "key_size=3072"

# Tester Auth
curl http://localhost:8001/signup -X POST -d '{"email":"test@example.com", ...}'

# Scanner sécurité
curl http://localhost:8003/api/security/scan/summary -X GET
```

---

## 🔧 Configuration

### Fichiers clés
- `docker-compose.yml` : Orchestration services
- `src/security/Dockerfile` : Image Security service
- `src/security/init_database.sql` : Init DB Security
- `src/security/scanner.py` : Intégration Snyk/Sonar
- `src/security/crypto.py` : Fonctions cryptographiques

### Variables `.env` (recommandé)
```bash
JWT_SECRET=votre-secret-production
SNYK_TOKEN=votre-token-snyk
SONAR_TOKEN=votre-token-sonarqube
MYSQL_ROOT_PASSWORD=root-password
```

---

## 📝 Notes importantes

1. **Clés Snyk/Sonar** : Optionnelles, scans retournent "skipped" si non configurées
2. **Localhost vs Docker** : Services utilisent noms Docker (`security-service`) en production
3. **CORS** : Configuré pour ports 8001, 8002, 8003
4. **Base de données** : 3 DB séparées pour isolation
5. **Scalabilité** : Chaque service peut scale indépendamment

---

## 🎯 Prochaines étapes

- [ ] Tests end-to-end automatisés
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Rotation automatique clés
- [ ] Rate limiting par service
- [ ] Métriques Prometheus/Grafana
- [ ] Logs centralisés (ELK stack)
