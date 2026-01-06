# 🎬 Guide Complet - Service Upload Vidéo Moustass

## 📊 Vue d'ensemble du système

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (HTML/JS)                        │
│              src/ui/upload.html                             │
│         • Formulaire d'upload                               │
│         • Liste des vidéos                                  │
│         • Actions (voir, supprimer)                         │
└────────────────┬────────────────────────────────────────────┘
                 │ API Fetch Requests
                 ↓ (localhost:8002/api/videos)
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│                                                              │
│    main_upload.py → upload_service.py → upload_api.py      │
│                                                              │
│    Routes:                                                   │
│    • POST   /api/videos/upload          (Uploader)         │
│    • GET    /api/videos/list             (Lister)          │
│    • GET    /api/videos/{id}             (Détails)         │
│    • DELETE /api/videos/{id}             (Supprimer)       │
│    • GET    /api/videos/{id}/download    (Télécharger)    │
└────────────────┬────────────────────────────────────────────┘
                 │ SQLAlchemy ORM
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                             │
│                                                              │
│    database.py ← → models.py (Video Model)                 │
│                                                              │
│    MySQL Connection: mysql+pymysql://user:pass@host:3306   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                    MySQL Database                            │
│                                                              │
│    Table: videos                                             │
│    • Métadonnées des vidéos                                 │
│    • Clés chiffrées (RSA-3072)                              │
│    • Statuts et dates d'expiration                          │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Flux d'upload complet

```
1. FRONTEND (upload.html)
   └─ Utilisateur remplit le formulaire
      ├─ Sélectionne un fichier vidéo
      ├─ Entre son ID
      ├─ Entre la clé AES chiffrée
      └─ Entre le montant

2. API REQUEST
   └─ POST /api/videos/upload (FormData)
      ├─ file: binary data
      ├─ sender_id: string
      ├─ receiver_id: string
      ├─ encrypted_key: string
      └─ amount: float

3. BACKEND (upload_service.py)
   └─ Handler: upload_video()
      ├─ Valide le format (mp4, ts)
      ├─ Génère un UUID unique
      ├─ Sauvegarde le fichier avec aiofiles
      ├─ Crée un enregistrement en BD
      └─ Retourne video_id

4. DATABASE (MySQL)
   └─ INSERT INTO videos
      ├─ id: uuid-xxxx
      ├─ sender_id: user-123
      ├─ storage_path: uploads/uuid-xxxx.mp4
      ├─ encrypted_key: clé en base64
      ├─ created_at: NOW()
      └─ expires_at: NOW() + 60 jours

5. RESPONSE
   └─ JSON avec video_id
      └─ Frontend affiche: "Vidéo uploadée ✅"

6. REFRESH
   └─ GET /api/videos/list
      └─ Tableau affiche la nouvelle vidéo
```

## 📁 Structure des fichiers

```
Moustass-video/
├── main_upload.py                    # Point d'entrée principal
├── run_service.sh                    # Script de démarrage
├── requirements.txt                  # Dépendances Python
├── README_UPLOAD_SERVICE.md          # Documentation du service
├── .env.example                      # Variables d'environnement exemple
│
├── docker-compose.yml                # Configuration Docker Compose
├── Dockerfile                        # Image Docker du service
├── init_database.sql                 # Schéma de la base de données
│
├── src/
│   ├── upload/                       # Service d'upload
│   │   ├── __init__.py              # Initialisation du package
│   │   ├── upload_service.py        # Logique métier + routes FastAPI
│   │   ├── upload_api.py            # Routeur avec endpoints
│   │   ├── models.py                # Modèle Video (ORM)
│   │   ├── database.py              # Configuration SQLAlchemy
│   │   └── README_AUTH.md           # Docs techniques
│   │
│   └── ui/
│       └── upload.html              # Interface web interactive
│
├── uploads/                          # Stockage des vidéos (runtime)
└── test_upload_service.py           # Tests unitaires
```

## 🛠️ Installation par étapes

### 1️⃣ Prérequis
```bash
# Python 3.9+
python --version

# MySQL 8.0+
mysql --version
```

### 2️⃣ Installation locale
```bash
# Cloner/télécharger le projet
cd Moustass-video

# Créer un env virtuel (optionnel)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3️⃣ Configurer la base de données
```bash
# Créer la DB avec le script SQL
mysql -u root -p < init_database.sql

# OU manuellement
mysql -u root -p
mysql> CREATE DATABASE videos_db;
mysql> CREATE USER 'videos_user'@'%' IDENTIFIED BY 'videos_password';
mysql> GRANT ALL PRIVILEGES ON videos_db.* TO 'videos_user'@'%';
mysql> FLUSH PRIVILEGES;
```

### 4️⃣ Mettre à jour la configuration
```bash
# Éditer src/upload/database.py
# Remplacer les identifiants par vos paramètres MySQL
```

### 5️⃣ Lancer le service
```bash
# Option 1: Avec le script
bash run_service.sh

# Option 2: Directement
python main_upload.py

# Option 3: Avec Docker Compose
docker-compose up -d
```

### 6️⃣ Accéder à l'application
- **Interface web**: http://localhost:8002
- **Swagger Docs**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## 🔑 Endpoints Clés

### Upload une vidéo
```bash
curl -X POST "http://localhost:8002/api/videos/upload" \
  -F "file=@video.mp4" \
  -F "sender_id=user-123" \
  -F "receiver_id=ADMIN" \
  -F "encrypted_key=<clé-base64>" \
  -F "amount=100.50"
```

### Lister toutes les vidéos
```bash
curl -X GET "http://localhost:8002/api/videos/list"
```

### Obtenir les détails d'une vidéo
```bash
curl -X GET "http://localhost:8002/api/videos/{video_id}"
```

### Supprimer une vidéo
```bash
curl -X DELETE "http://localhost:8002/api/videos/{video_id}"
```

## 📱 Frontend - Fonctionnement

### Formulaire d'upload
```javascript
// upload.html - Gestion du submit
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(uploadForm);
    
    // Requête au backend
    const response = await fetch(
        'http://localhost:8002/api/videos/upload',
        {
            method: 'POST',
            body: formData
        }
    );
    
    // Affiche le résultat
    if (response.ok) {
        showAlert('Vidéo uploadée ✅');
        loadVideos();
    } else {
        showAlert('Erreur ❌');
    }
});
```

### Tableau des vidéos
```javascript
async function loadVideos() {
    const response = await fetch('http://localhost:8002/api/videos/list');
    const videos = await response.json();
    
    // Afficher chaque vidéo dans le tableau
    videos.forEach(video => {
        // Créer une ligne avec ID, statut, montant, date d'expiration
        // + boutons d'action (voir, supprimer)
    });
}
```

## 🔐 Sécurité - Points clés

```
1. UPLOAD
   ✓ Validation des formats (.mp4, .ts)
   ✓ UUID unique par vidéo (pas de collision)
   ✓ Stockage en dossier isolé

2. CHIFFREMENT
   ✓ Support RSA-3072 (asymétrique)
   ✓ Clés AES (symétriques) chiffrées
   ✓ Stockage en BD avec hash

3. EXPIRATION
   ✓ Auto-expiration après 60 jours
   ✓ Cleanup automatique via cron MySQL
   ✓ Changement de statut à EXPIRED

4. API
   ✓ Validation des paramètres
   ✓ Gestion des erreurs appropriée
   ✓ Logs d'audit potentiels
```

## 📊 Base de Données - Schéma

```sql
Table: videos
├─ id (VARCHAR 36) - UUID primaire
├─ sender_id (VARCHAR 36) - Qui a uploadé
├─ receiver_id (VARCHAR 36) - Qui reçoit
├─ storage_path (VARCHAR 255) - Chemin du fichier
├─ encrypted_key (LONGTEXT) - Clé AES chiffrée
├─ amount (DECIMAL 15,2) - Montant EUR
├─ status (ENUM) - UPLOADED|VERIFIED|DOWNLOADED|EXPIRED
├─ created_at (TIMESTAMP) - Date création
└─ expires_at (TIMESTAMP) - Date d'expiration

Indexes:
├─ idx_sender (sender_id)
├─ idx_receiver (receiver_id)
├─ idx_status (status)
├─ idx_expires (expires_at)
└─ idx_created (created_at)

Views:
└─ active_videos - Vidéos non expirées

Events:
└─ cleanup_expired_videos_event - Nettoyage quotidien
```

## 🐳 Déploiement Docker

```bash
# Démarrer avec Docker Compose
docker-compose up -d

# Logs
docker-compose logs -f upload-service

# Arrêter
docker-compose down
```

## ❓ Troubleshooting

### "Impossible de résoudre l'importation aiofiles"
```bash
pip install aiofiles
```

### Erreur de connexion MySQL
```bash
# Vérifier que MySQL tourne
mysql -u root -p -e "SELECT 1"

# Vérifier les identifiants dans database.py
```

### Port 8002 déjà utilisé
```bash
# Trouver le processus
lsof -i :8002

# Ou changer le port dans main_upload.py
uvicorn.run(..., port=8003)
```

## 📈 Monitoring

```bash
# Vérifier la santé du service
curl http://localhost:8002/health

# Voir les logs
tail -f logs/upload-service.log

# Accéder à Swagger UI
open http://localhost:8002/docs
```

## 🚀 Prochaines étapes

- [ ] Ajouter authentification JWT
- [ ] Implémenter quota de stockage par utilisateur
- [ ] Ajouter compression vidéo
- [ ] Implémenter watermarking
- [ ] Ajouter notifications par email
- [ ] Configurer S3/Cloud storage
- [ ] Monitoring avec Prometheus
- [ ] Logs centralisés (ELK Stack)

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [Python aiofiles](https://github.com/Tinche/aiofiles)
- [MySQL Documentation](https://dev.mysql.com/doc)

---

**Service créé**: 5 janvier 2026  
**Projet**: Moustass Video - Architecture Microservice
