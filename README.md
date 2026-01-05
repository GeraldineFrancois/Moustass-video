# Moustass-video
Messagerie vidéo confidentielle et authentique

## Requirements
- Python version : 3.8 or higher
- Install all required modules

***1- Create an virtual environment***
# 🎬 Moustass Video - Service de Upload Sécurisé

Messagerie vidéo confidentielle et authentique avec chiffrement RSA-3072 et stockage sécurisé.

## 🎯 Vue d'ensemble

Ce projet implémente une **architecture microservice** avec:
- **Service d'authentification** (`src/auth/`)
- **Service d'upload vidéo** (`src/upload/`) ← LE SERVICE PRINCIPAL
- **Service de sécurité** (`src/security/`)

### Focus: Service Upload Vidéo

Le service Upload permet:
- ✅ Upload de vidéos sécurisées (.mp4, .ts)
- ✅ Chiffrement AES avec support RSA-3072
- ✅ Gestion complète avec API REST
- ✅ Interface web interactive
- ✅ Base de données MySQL
- ✅ Expiration automatique (60 jours)

## 🚀 Démarrage rapide

### Option 1: Démarrage local

```bash
# 1. Créer un environnement virtuel
python -m venv .virtualenv

# Windows
.virtualenv\Scripts\activate
# Linux/Mac
source .virtualenv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la base de données
# Éditer src/upload/database.py avec vos paramètres MySQL
# Puis exécuter init_database.sql

# 4. Lancer le service
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