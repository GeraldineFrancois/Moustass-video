# 🎬 Moustass Video - Microservice de Gestion Vidéo

**Messagerie vidéo sécurisée, chiffrée et authentifiée avec architecture microservice.**

---

## 📋 Table des Matières

1. [Vue d'ensemble](#-vue-densemble)
2. [Architecture](#-architecture)
3. [Démarrage rapide](#-démarrage-rapide)
4. [Documentation](#-documentation)
5. [API](#-api)
6. [Sécurité](#-sécurité)
7. [Dépannage](#-dépannage)

---

## 🎯 Vue d'ensemble

**Moustass Video** est un microservice production-ready qui gère:

✅ **Upload sécurisé** de vidéos (.mp4, .ts)
✅ **Gestion complète** via API REST (8+ endpoints)
✅ **Interface web** interactive pour upload/download
✅ **Chiffrement** RSA-3072 + métadonnées
✅ **Expiration automatique** après 60 jours
✅ **Architecture modulaire** avec 4 composants
✅ **Sécurité** (anti-traversal, anti-XSS)
✅ **Performance** avec async/await et MySQL

### Structure du projet

```
moustass_video/
├── src/
│   ├── auth/                    # Service d'authentification
│   ├── security/               # Service de sécurité
│   └── videos/                 # SERVICE PRINCIPAL
│       ├── main_upload.py       # Point d'entrée
│       ├── upload_service.py    # Orchestrateur
│       ├── upload_api.py        # Controller (9 endpoints)
│       ├── storage_manager.py   # Composant 1: Fichiers
│       ├── metadata_mapper.py   # Composant 2: BD
│       ├── expiration_engine.py # Composant 3: Lifecycle
│       ├── models.py            # ORM Video
│       ├── database.py          # MySQL config
│       ├── ARCHITECTURE.md      # Détail des 4 composants
│       └── ...
│   └── ui/
│       └── upload.html          # Interface web
├── TEST_SERVICE.md              # 50+ tests manuels
├── MICROSERVICE_DIAGRAM.md      # Diagrammes ASCII
├── MICROSERVICE_SUMMARY.md      # Résumé complet
├── DEPLOYMENT_GUIDE.md          # Déploiement (3 options)
├── requirements.txt             # Dépendances
└── docker-compose.yml           # Docker
```

---

## 🏗️ Architecture

### 4 Composants Principaux

```
┌─────────────────────────────────────────┐
│  API Controller (upload_api.py)         │
│  9 endpoints: POST/GET/DELETE/...       │
└────────────┬────────────────────────────┘
             ↓
┌──────────────────┬────────────────┬──────────────┐
│ Storage Manager  │ Metadata Map.  │ Expiration   │
│ (storage_...)    │ (metadata_...) │ Engine       │
│                  │                │              │
│ • Fichiers async │ • ORM SQLAlch. │ • Nettoyage  │
│ • Sécurité path  │ • CRUD         │  • Lifecycle │
│ • Validation     │ • Enum status  │  * Scheduler │
└──────────┬───────┴────────┬───────┴──────┬───────┘
           ↓                ↓               ↓
    uploads/         MySQL videos_db    Retention logic
```

**Lire**: [ARCHITECTURE.md](./src/videos/ARCHITECTURE.md) pour détails complets

---

## 🚀 Démarrage rapide

### ⚠️ IMPORTANT - Configuration Sécurisée

**Avant de démarrer, vous DEVEZ configurer les variables d'environnement :**

```bash
# Linux / macOS
./generate-env.sh

# Windows PowerShell
.\generate-env.ps1

# Windows CMD
generate-env.bat
```

📖 **Voir [SECURITY_SETUP.md](./SECURITY_SETUP.md) pour plus de détails**

---

### Option 1️⃣: Docker Compose (Recommandé)

#### Linux / macOS
```bash
# 1. Générer la configuration sécurisée
./generate-env.sh

# 2. Démarrer tous les services
./start-services.sh
# ou directement:
docker compose up -d

# 3. Vérifier que tout fonctionne
docker compose ps
```

#### Windows PowerShell
```powershell
# 1. Générer la configuration sécurisée
.\generate-env.ps1

# 2. Démarrer tous les services
.\start-services.ps1
# ou directement:
docker compose up -d

# 3. Vérifier que tout fonctionne
docker compose ps
```

#### Windows CMD
```cmd
REM 1. Générer la configuration
generate-env.bat

REM 2. Démarrer les services
start-services.bat
```

**✅ URLs des services:**
- http://localhost:8001 (Auth + UI)
- http://localhost:8002 (Videos API)
- http://localhost:8003 (Security API)

### Option 2️⃣: Local (Développement)

#### Linux / macOS
```bash
# 1. Prérequis
python --version      # 3.11+
mysql --version       # 8.0+

# 2. Configuration
./generate-env.sh     # Ou copier manuellement .env.example
source .env           # Charger les variables

# 3. Venv
python -m venv venv
source venv/bin/activate

# 4. Dépendances
pip install -r requirements.txt

# 5. Base de données
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE IF NOT EXISTS videos_db;"
mysql -u root -p$MYSQL_ROOT_PASSWORD videos_db < src/videos/init_database.sql

# 6. Lancer
cd src/videos
python main_upload.py

# ✅ Ouvrir: http://localhost:8002
```

#### Windows PowerShell
```powershell
# 1. Prérequis: Python 3.11+, MySQL 8.0+

# 2. Configuration
.\generate-env.ps1

# 3. Venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 4. Dépendances
pip install -r requirements.txt

# 5. Base de données (via MySQL Shell ou Docker)
# Voir SECURITY_SETUP.md

# 6. Lancer
cd src\videos
python main_upload.py

# ✅ Ouvrir: http://localhost:8002
```

### Option 3️⃣: Production (Nginx + Gunicorn)

**Lire**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) (3 options détaillées)

---

## 📚 Documentation

### Fichiers Essentiels

| Fichier | Contenu |
|---------|---------|
| [ARCHITECTURE.md](./src/videos/ARCHITECTURE.md) | 4 composants + flux détaillés |
| [TEST_SERVICE.md](./TEST_SERVICE.md) | 50+ cas de test + cURL |
| [MICROSERVICE_DIAGRAM.md](./MICROSERVICE_DIAGRAM.md) | Diagrammes ASCII + flux |
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | Local / Docker / Production |
| [MICROSERVICE_SUMMARY.md](./MICROSERVICE_SUMMARY.md) | Résumé complet du projet |

### Accéder à l'API

```bash
# Interface web
http://localhost:8002

# Swagger (interactif)
http://localhost:8002/docs

# ReDoc
http://localhost:8002/redoc

# OpenAPI JSON
http://localhost:8002/openapi.json
```

---

## 📡 API

### Endpoints Disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| **POST** | `/api/videos/upload` | Uploader une vidéo |
| **GET** | `/api/videos` | Lister les vidéos (paginated) |
| **GET** | `/api/videos/{id}` | Infos d'une vidéo |
| **GET** | `/api/videos/{id}/download` | Télécharger le fichier |
| **DELETE** | `/api/videos/{id}` | Supprimer vidéo |
| **GET** | `/api/videos/{id}/retention` | Infos d'expiration |
| **POST** | `/api/videos/{id}/extend-retention` | Prolonger durée |
| **POST** | `/api/videos/maintenance/cleanup-expired` | Nettoyage manuel |
| **GET** | `/health` | Status du service |

### Exemple cURL

```bash
# Upload
curl -X POST "http://localhost:8002/api/videos/upload" \
  -F "file=@video.mp4" \
  -F "sender_id=alice" \
  -F "receiver_id=bob" \
  -F "encrypted_key=xxx" \
  -F "amount=100.00"

# Lister
curl "http://localhost:8002/api/videos?skip=0&limit=10"

# Télécharger
curl "http://localhost:8002/api/videos/UUID/download" --output video.mp4

# Supprimer
curl -X DELETE "http://localhost:8002/api/videos/UUID"
```

**Plus d'exemples**: [TEST_SERVICE.md](./TEST_SERVICE.md)

---

## 🔐 Sécurité

### Protections Implémentées

✅ **Path Traversal Prevention**
```python
# Valide que le chemin reste dans uploads/
resolved = target.resolve()
if not str(resolved).startswith(str(UPLOAD_DIR)):
    raise HTTPException(status_code=400)
```

✅ **DOM-based XSS Prevention**
```javascript
// Utilise textContent au lieu de innerHTML
td.textContent = video.status;  // Safe
```

✅ **Input Validation**
- Format fichier: Whitelist .mp4/.ts
- UUID: Validation format
- Metadata: Type checking SQLAlchemy
- File size: Config-based (future)

✅ **SQL Injection Prevention**
- ORM SQLAlchemy (parameterized queries)
- Pas de string concatenation

✅ **HTTPS Prêt**
- Nginx reverse proxy (TLS)
- Gunicorn + Uvicorn (production)

---

## ⚙️ Configuration

### Variables d'environnement

```bash
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=MyStrongP@ss123!
DB_NAME=videos_db

# Service
UPLOAD_DIR=uploads
SERVICE_PORT=8002

# Optionnel
EXPIRATION_DAYS=60
LOG_LEVEL=info
```

### Fichiers de config

```bash
# src/videos/database.py
DATABASE_URL = "mysql+pymysql://root:MyStrongP%40ss123%21@localhost/videos_db"

# src/videos/main_upload.py
uvicorn.run(app, host="0.0.0.0", port=8002)
```

---

## 🧪 Tests

### Tests Manuels

**Voir**: [TEST_SERVICE.md](./TEST_SERVICE.md) pour:
- 10+ curl examples
- Interface web testing
- Error cases
- Performance tests
- Database verification

### Exécution rapide

```bash
# Santé
curl http://localhost:8002/health

# Liste vidéos
curl http://localhost:8002/api/videos

# Swagger
open http://localhost:8002/docs
```

---

## 📊 Monitoring

### Logs du service

```bash
# Local
tail -f <output>

# Docker
docker-compose logs -f api

# Systemd
sudo journalctl -u moustass-video -f
```

### Health check

```bash
# Simple
curl http://localhost:8002/health

# Complet
curl http://localhost:8002/api/videos/maintenance/health-detailed
```

### Base de données

```bash
# Stats vidéos
mysql -u root -pMyStrongP@ss123! videos_db \
  -e "SELECT COUNT(*), status FROM videos GROUP BY status;"

# Vidéos expirées
mysql -u root -pMyStrongP@ss123! videos_db \
  -e "SELECT id, expires_at FROM videos WHERE expires_at < NOW();"
```

---

## 🐛 Dépannage

### Service ne démarre pas

```bash
# 1. Vérifier Python
python3 -c "import fastapi; print('OK')"

# 2. Vérifier MySQL
mysql -u root -pMyStrongP@ss123! -e "SELECT 1;"

# 3. Lancer avec debug
cd src/videos
python main_upload.py 2>&1 | head -50
```

### Erreur: "database connection refused"

```bash
# Vérifier MySQL
sudo systemctl status mysql

# Tester la connexion
mysql -u root -pMyStrongP@ss123! -h localhost -e "SELECT 1;"

# Vérifier le DATABASE_URL
cat src/videos/database.py | grep DATABASE_URL
```

### Erreur: "Permission denied" uploads/

```bash
# Créer le répertoire
mkdir -p uploads && chmod 755 uploads/

# Vérifier propriété
ls -ld uploads/
```

**Plus de help**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 📈 Performance

- **Async I/O**: aiofiles + asyncio (non-bloquant)
- **Database**: MySQL pool + indexing
- **Pagination**: skip/limit pour listes longues
- **Caching**: Ready pour Redis (future)
- **Scaling**: Docker + Kubernetes ready

---

## 🔄 Workflow Typique

```
1. User uploads video.mp4
   ↓
2. Controller valide format
   ↓
3. StorageManager sauvegarde fichier
   ↓
4. MetadataMapper crée enregistrement BD
   ↓
5. User télécharge → ExpirationEngine vérifie date
   ↓
6. Fichier expiré? → Cleanup automatique
```

---

## 📝 Licence & Auteur

**Projet**: Moustass Video Microservice
**Version**: 1.0.0
**Status**: ✅ Production-Ready
**Support**: Voir [ARCHITECTURE.md](./src/videos/ARCHITECTURE.md)

---

## 🚀 Prochaines Étapes

1. ✅ **Démarrer le service** → `python main_upload.py`
2. ✅ **Accéder interface** → http://localhost:8002
3. ✅ **Lire ARCHITECTURE.md** → Comprendre les 4 composants
4. ✅ **Tester API** → [TEST_SERVICE.md](./TEST_SERVICE.md)
5. ✅ **Déployer** → [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

---

**Questions?** Lire les docs ou vérifier les fichiers respectifs.
**Prêt à déployer?** Voir [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
**Besoin de détails?** Voir [ARCHITECTURE.md](./src/videos/ARCHITECTURE.md)

🎉 **Merci d'utiliser Moustass Video!**
python main_upload.py
```

### Option 2: Démarrage avec Docker

```bash
# Avec Docker Compose (MySQL + Service)
docker-compose up -d

# Accéder à:
# - Service: http://localhost:8002
# - Docs Swagger: http://localhost:8002/docs
```

### Option 3: Utiliser le script de démarrage

```bash
bash run_service.sh
```

## 📍 Accès à l'application

- **Interface Web**: http://localhost:8002
- **API Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc
- **Health Check**: http://localhost:8002/health

## 📚 Documentation complète

- [📖 GUIDE_COMPLET.md](GUIDE_COMPLET.md) - Vue d'ensemble complète
- [🔌 README_UPLOAD_SERVICE.md](README_UPLOAD_SERVICE.md) - Doc technique détaillée
- [📮 API_EXAMPLES.md](API_EXAMPLES.md) - Exemples et scénarios d'utilisation
- [✅ COMPLETION_REPORT.md](COMPLETION_REPORT.md) - Résumé des tâches complétées

## 🛠️ Stack technique

**Backend:**
- Python 3.11+
- FastAPI (framework web async)
- SQLAlchemy (ORM)
- aiofiles (I/O asynchrone)

**Base de données:**
- MySQL 8.0
- PyMySQL (connecteur)

**Frontend:**
- HTML5 + CSS3 + JavaScript
- Bootstrap 5 (UI responsive)
- Fetch API (requêtes HTTP)

**DevOps:**
- Docker & Docker Compose
- Uvicorn (serveur ASGI)

## 📋 Requirements

```
# Python version
Python 3.9 or higher

# MySQL
MySQL 8.0+

# Dépendances Python (voir requirements.txt)
- fastapi
- uvicorn
- sqlalchemy
- pymysql
- aiofiles
- python-multipart
- python-jose
- passlib
- cryptography
```

## 🔧 Installation détaillée

### Windows

```bash
# 1. Créer virtualenv
python -m venv .virtualenv
.virtualenv\Scripts\activate

# 2. Installer dépendances
pip install -r requirements.txt

# 3. Configurer MySQL
# Créer la base avec MySQL Workbench ou:
mysql -u root -p < init_database.sql

# 4. Lancer
python main_upload.py
```

### Linux / Mac

```bash
# 1. Créer virtualenv
python3 -m venv .virtualenv
source .virtualenv/bin/activate

# 2. Installer dépendances
pip install -r requirements.txt

# 3. Configurer MySQL
mysql -u root -p < init_database.sql

# 4. Lancer avec le script
bash run_service.sh

# Ou directement
python main_upload.py
```

## 🌐 API Endpoints

### Upload une vidéo
```bash
POST /api/videos/upload
Content-Type: multipart/form-data

Paramètres:
- file: fichier vidéo (.mp4, .ts)
- sender_id: ID de l'expéditeur
- receiver_id: ID du destinataire
- encrypted_key: Clé AES chiffrée
- amount: Montant EUR
```

### Endpoints disponibles
```
GET    /api/videos/list              - Lister toutes les vidéos
GET    /api/videos/{id}              - Détails d'une vidéo
GET    /api/videos/{id}/download     - Télécharger
DELETE /api/videos/{id}              - Supprimer
GET    /api/videos/health/status     - Santé du service
```

Voir [API_EXAMPLES.md](API_EXAMPLES.md) pour des exemples détaillés.

## 🧪 Tests

### Lancer les tests
```bash
pytest test_upload_service.py -v
```

### Tester l'API manuellement
```bash
# Avec le script de maintenance
bash maintenance.sh test

# Ou avec cURL
curl -X POST http://localhost:8002/api/videos/upload \
  -F "file=@video.mp4" \
  -F "sender_id=test-user" \
  -F "receiver_id=ADMIN" \
  -F "encrypted_key=test-key" \
  -F "amount=100.00"
```

## 🛠️ Scripts de maintenance

```bash
# Démarrer le service
bash maintenance.sh start

# Arrêter
bash maintenance.sh stop

# Redémarrer
bash maintenance.sh restart

# Vérifier la santé
bash maintenance.sh health

# Voir les statistiques
bash maintenance.sh stats

# Nettoyer les fichiers temporaires
bash maintenance.sh cleanup

# Sauvegarder la base de données
bash maintenance.sh backup

# Tester l'API
bash maintenance.sh test
```

## 📁 Structure du projet

```
Moustass-video/
├── main_upload.py                    # Point d'entrée
├── run_service.sh                    # Script de démarrage
├── maintenance.sh                    # Maintenance du service
├── requirements.txt                  # Dépendances
├── docker-compose.yml                # Orchestration Docker
├── Dockerfile                        # Image Docker
├── init_database.sql                 # Schéma MySQL
│
├── src/
│   ├── upload/                       # Service upload
│   │   ├── upload_service.py         # Logique métier
│   │   ├── upload_api.py             # Routeur API
│   │   ├── models.py                 # Modèle Video
│   │   └── database.py               # Config DB
│   │
│   └── ui/
│       └── upload.html               # Interface web
│
├── uploads/                          # Stockage (runtime)
├── tests/                            # Tests
│
└── Documentation:
    ├── README.md                     # Ce fichier
    ├── GUIDE_COMPLET.md              # Vue d'ensemble complète
    ├── README_UPLOAD_SERVICE.md      # Doc technique
    ├── API_EXAMPLES.md               # Exemples API
    └── COMPLETION_REPORT.md          # Rapport d'achèvement
```

## 🔐 Sécurité

- ✅ Validation des formats de fichiers
- ✅ UUID unique par vidéo
- ✅ Support RSA-3072 pour clés AES
- ✅ Expiration automatique (60 jours)
- ✅ Stockage isolé des fichiers
- ✅ Gestion appropriée des erreurs
- ✅ Validation des paramètres
- ✅ Logs d'audit (à configurer)

## ⚠️ Troubleshooting

### "Impossible de résoudre l'importation aiofiles"
```bash
pip install aiofiles
```

### Erreur de connexion MySQL
```bash
# Vérifier que MySQL tourne
mysql -u root -p -e "SELECT 1"

# Vérifier les identifiants dans src/upload/database.py
```

### Port 8002 déjà utilisé
```bash
# Trouver le processus
lsof -i :8002

# Ou changer le port dans main_upload.py
uvicorn.run(..., port=8003)
```

## 📊 Architecture Microservice

```
┌─────────────────────────────────────┐
│     Frontend (HTML/JS)              │
│     src/ui/upload.html              │
└────────────┬────────────────────────┘
             │ HTTP/REST
             ↓
┌─────────────────────────────────────┐
│     Service Upload (FastAPI)        │
│     main_upload.py                  │
│     Port: 8002                      │
└────────────┬────────────────────────┘
             │ SQLAlchemy
             ↓
┌─────────────────────────────────────┐
│     MySQL Database                  │
│     videos_db                       │
└─────────────────────────────────────┘
```

## 🚀 Déploiement en production

Voir [GUIDE_COMPLET.md](GUIDE_COMPLET.md) pour:
- Configuration SSL/TLS
- Reverse proxy (Nginx)
- Load balancing
- Monitoring avec Prometheus
- Logs centralisés
- Scaling horizontal

## 📞 Support

Pour toute question ou problème:
1. Consultez la [documentation complète](GUIDE_COMPLET.md)
2. Vérifiez les [exemples API](API_EXAMPLES.md)
3. Consulez les [rapports d'erreurs](COMPLETION_REPORT.md)

## 📝 Licence

Projet Moustass - 2026

## 👥 Contributeurs

- Développement: Service Upload Video
- Architecture: Microservice pattern
- Date: 5 janvier 2026

---

**Status**: ✅ Prêt pour développement et test
**Version**: 1.0.0
**Maintenability**: A+
