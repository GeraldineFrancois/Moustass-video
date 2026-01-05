# Service Upload Vidéo - Moustass

Service de microservice pour la gestion sécurisée d'upload et de téléchargement de vidéos dans l'écosystème Moustass.

## 🎯 Fonctionnalités

- ✅ **Upload sécurisé** de vidéos (.mp4, .ts)
- ✅ **Chiffrement AES** avec support RSA-3072
- ✅ **Gestion de base de données** avec SQLAlchemy
- ✅ **API REST** complète avec FastAPI
- ✅ **Interface web** moderne avec Bootstrap 5
- ✅ **Suivi de l'expiration** des vidéos (60 jours)
- ✅ **Suppression sécurisée** des fichiers

## 📋 Architecture

```
src/upload/
├── __init__.py              # Initialisation du service
├── upload_service.py        # Logique métier & routes FastAPI
├── upload_api.py            # Routeur API avec endpoints
├── models.py                # Modèle de données (ORM)
├── database.py              # Configuration de la base de données
└── README_UPLOAD.md         # Documentation technique

src/ui/
└── upload.html              # Interface web interactive

main_upload.py               # Point d'entrée du service
run_service.sh               # Script de lancement
```

## 🚀 Installation et Démarrage

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer la base de données

Modifiez `src/upload/database.py` avec vos paramètres MySQL:

```python
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/videos_db"
```

### 3. Créer la base de données

```bash
# MySQL
mysql -u root -p
CREATE DATABASE videos_db;
```

### 4. Lancer le service

**Option 1: Avec le script**
```bash
bash run_service.sh
```

**Option 2: Directement**
```bash
python main_upload.py
```

Le service sera accessible à: `http://localhost:8002`

## 📚 API Endpoints

### Upload une vidéo
```http
POST /api/videos/upload
Content-Type: multipart/form-data

file: <fichier binaire>
sender_id: <string>
receiver_id: <string>
encrypted_key: <string>
amount: <float>
```

**Réponse (201):**
```json
{
  "message": "Upload réussi",
  "video_id": "uuid-xxxx",
  "status": "UPLOADED"
}
```

### Lister les vidéos
```http
GET /api/videos/list
```

**Réponse:**
```json
[
  {
    "id": "uuid-xxxx",
    "sender_id": "user-123",
    "receiver_id": "ADMIN",
    "status": "UPLOADED",
    "amount": 250.00,
    "created_at": "2026-01-05T10:30:00",
    "expires_at": "2026-03-06T10:30:00"
  }
]
```

### Obtenir les infos d'une vidéo
```http
GET /api/videos/{video_id}
```

### Télécharger une vidéo
```http
GET /api/videos/{video_id}/download
```

### Supprimer une vidéo
```http
DELETE /api/videos/{video_id}
```

### Vérifier la santé du service
```http
GET /api/videos/health/status
```

## 🌐 Interface Web

L'interface web (http://localhost:8002) permet:

1. **Upload**: Formulaire pour uploader une vidéo avec:
   - Sélection du fichier (.mp4, .ts)
   - ID expéditeur
   - Destinataire (ADMIN par défaut)
   - Clé chiffrée AES
   - Montant en EUR

2. **Gestion**: Tableau avec:
   - Liste des vidéos uploadées
   - Statut de chaque vidéo
   - Date d'expiration
   - Actions (voir détails, supprimer)

## 🔐 Sécurité

- ✅ Validation des formats de fichier (.mp4, .ts)
- ✅ Génération d'UUID unique pour chaque vidéo
- ✅ Support du chiffrement RSA-3072 pour les clés AES
- ✅ Stockage sécurisé en base de données
- ✅ Expiration automatique après 60 jours
- ✅ Suppression sécurisée des fichiers

## 📊 Modèle de Données

```python
class Video:
    id: String(36) - UUID unique
    sender_id: String(36) - ID de l'expéditeur
    receiver_id: String(36) - ID du destinataire
    storage_path: String(255) - Chemin du fichier
    encrypted_key: Text - Clé AES chiffrée
    amount: Decimal(15,2) - Montant
    status: Enum - UPLOADED|VERIFIED|DOWNLOADED|EXPIRED
    created_at: Timestamp - Date de création
    expires_at: Timestamp - Date d'expiration
```

## 📖 Documentation API Interactive

Accédez à la documentation Swagger à: `http://localhost:8002/docs`

## 🔧 Troubleshooting

### Erreur d'importation `aiofiles`
```bash
pip install aiofiles
```

### Erreur de connexion à la base de données
- Vérifier que MySQL est en cours d'exécution
- Vérifier les identifiants dans `src/upload/database.py`
- Vérifier que la base de données existe

### Erreur de permissions sur les fichiers
```bash
chmod +x run_service.sh
mkdir -p uploads
chmod 755 uploads
```

## 🎓 Intégration Microservice

Ce service fait partie de l'architecture microservice Moustass:
- **Service d'authentification**: `src/auth/`
- **Service d'upload**: `src/upload/`
- **Service de sécurité**: `src/security/`

## 📝 Licence

Projet Moustass - 2026
