# 📮 Exemples d'utilisation API

## 🔍 Base de l'API

```
Base URL: http://localhost:8002
Prefix: /api/videos
Version: 1.0
```

## 📝 Exemples cURL

### 1. Upload une vidéo

```bash
curl -X POST "http://localhost:8002/api/videos/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/video.mp4" \
  -F "sender_id=user-123" \
  -F "receiver_id=ADMIN" \
  -F "encrypted_key=MIIEpAIBAAKCAQEA..." \
  -F "amount=250.50"
```

**Réponse (200):**
```json
{
  "message": "Upload réussi",
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "UPLOADED"
}
```

### 2. Lister toutes les vidéos

```bash
curl -X GET "http://localhost:8002/api/videos/list"
```

**Réponse (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sender_id": "user-123",
    "receiver_id": "ADMIN",
    "status": "UPLOADED",
    "amount": 250.50,
    "created_at": "2026-01-05T10:30:00",
    "expires_at": "2026-03-06T10:30:00"
  },
  {
    "id": "660f9401-f30c-52e5-b827-557766551111",
    "sender_id": "user-456",
    "receiver_id": "ADMIN",
    "status": "UPLOADED",
    "amount": 150.00,
    "created_at": "2026-01-04T15:45:00",
    "expires_at": "2026-03-05T15:45:00"
  }
]
```

### 3. Obtenir les infos d'une vidéo

```bash
curl -X GET "http://localhost:8002/api/videos/550e8400-e29b-41d4-a716-446655440000"
```

**Réponse (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_id": "user-123",
  "receiver_id": "ADMIN",
  "status": "UPLOADED",
  "amount": 250.50,
  "created_at": "2026-01-05T10:30:00",
  "expires_at": "2026-03-06T10:30:00"
}
```

### 4. Télécharger une vidéo

```bash
curl -X GET "http://localhost:8002/api/videos/550e8400-e29b-41d4-a716-446655440000/download" \
  -o downloaded-video.mp4
```

### 5. Supprimer une vidéo

```bash
curl -X DELETE "http://localhost:8002/api/videos/550e8400-e29b-41d4-a716-446655440000"
```

**Réponse (200):**
```json
{
  "message": "Vidéo supprimée avec succès"
}
```

### 6. Vérifier la santé du service

```bash
curl -X GET "http://localhost:8002/api/videos/health/status"
```

**Réponse (200):**
```json
{
  "status": "healthy",
  "service": "upload-service"
}
```

## 📌 Collection Postman

### Environnement

Créer un nouvel environnement avec:

```json
{
  "base_url": "http://localhost:8002",
  "api_path": "/api/videos",
  "video_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Requests

#### 1. Upload Vidéo

```
Method: POST
URL: {{base_url}}{{api_path}}/upload
Headers:
  - Content-Type: multipart/form-data

Form Data:
  - file: [fichier video.mp4]
  - sender_id: user-123
  - receiver_id: ADMIN
  - encrypted_key: MIIEpAIBAAKCAQEA...
  - amount: 250.50
```

**Test Script:**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("video_id", response.video_id);
    console.log("✅ Upload réussi! Video ID: " + response.video_id);
}
```

#### 2. Lister les Vidéos

```
Method: GET
URL: {{base_url}}{{api_path}}/list
```

**Test Script:**
```javascript
if (pm.response.code === 200) {
    const videos = pm.response.json();
    pm.collectionVariables.set("video_count", videos.length);
    console.log("📊 " + videos.length + " vidéos trouvées");
}
```

#### 3. Obtenir les Détails

```
Method: GET
URL: {{base_url}}{{api_path}}/{{video_id}}
```

#### 4. Télécharger une Vidéo

```
Method: GET
URL: {{base_url}}{{api_path}}/{{video_id}}/download
```

#### 5. Supprimer une Vidéo

```
Method: DELETE
URL: {{base_url}}{{api_path}}/{{video_id}}
```

**Test Script:**
```javascript
if (pm.response.code === 200) {
    console.log("✅ Vidéo supprimée avec succès");
}
```

#### 6. Santé Service

```
Method: GET
URL: {{base_url}}{{api_path}}/health/status
```

## 🐍 Exemples Python

### Avec `requests`

```python
import requests

BASE_URL = "http://localhost:8002/api/videos"

# 1. Upload une vidéo
with open("video.mp4", "rb") as f:
    files = {"file": f}
    data = {
        "sender_id": "user-123",
        "receiver_id": "ADMIN",
        "encrypted_key": "MIIEpAIBAAKCAQEA...",
        "amount": "250.50"
    }
    response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    print(response.json())
    video_id = response.json()["video_id"]

# 2. Lister les vidéos
response = requests.get(f"{BASE_URL}/list")
videos = response.json()
print(f"Nombre de vidéos: {len(videos)}")

# 3. Obtenir les infos
response = requests.get(f"{BASE_URL}/{video_id}")
print(response.json())

# 4. Supprimer
response = requests.delete(f"{BASE_URL}/{video_id}")
print(response.json())
```

### Avec `httpx` (async)

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Upload
        with open("video.mp4", "rb") as f:
            files = {"file": f}
            data = {
                "sender_id": "user-123",
                "receiver_id": "ADMIN",
                "encrypted_key": "MIIEpAIBAAKCAQEA...",
                "amount": "250.50"
            }
            response = await client.post(
                "http://localhost:8002/api/videos/upload",
                files=files,
                data=data
            )
            print(response.json())

asyncio.run(main())
```

## 🎯 Scénario Complet d'Test

```bash
#!/bin/bash

API="http://localhost:8002/api/videos"

echo "🎬 Test du Service Upload Vidéo"
echo "==============================="

# 1. Vérifier la santé
echo -e "\n1️⃣  Vérifier la santé..."
curl -s "$API/health/status" | jq '.'

# 2. Créer un fichier de test
echo -e "\n2️⃣  Créer un fichier de test..."
dd if=/dev/zero bs=1M count=10 of=test-video.mp4 2>/dev/null
echo "✅ Fichier créé"

# 3. Uploader
echo -e "\n3️⃣  Uploader la vidéo..."
UPLOAD=$(curl -s -X POST "$API/upload" \
  -F "file=@test-video.mp4" \
  -F "sender_id=test-user" \
  -F "receiver_id=ADMIN" \
  -F "encrypted_key=test-key-base64" \
  -F "amount=100.00")

VIDEO_ID=$(echo $UPLOAD | jq -r '.video_id')
echo "Video ID: $VIDEO_ID"

# 4. Lister
echo -e "\n4️⃣  Lister les vidéos..."
curl -s "$API/list" | jq '.'

# 5. Détails
echo -e "\n5️⃣  Détails de la vidéo..."
curl -s "$API/$VIDEO_ID" | jq '.'

# 6. Supprimer
echo -e "\n6️⃣  Supprimer la vidéo..."
curl -s -X DELETE "$API/$VIDEO_ID" | jq '.'

# 7. Cleanup
echo -e "\n7️⃣  Nettoyage..."
rm test-video.mp4
echo "✅ Test terminé"
```

## ⚠️ Codes d'erreur

```
200 OK - Succès
201 Created - Ressource créée
204 No Content - Suppression réussie
400 Bad Request - Format de fichier invalide
401 Unauthorized - Non authentifié
403 Forbidden - Non autorisé
404 Not Found - Vidéo non trouvée
422 Unprocessable Entity - Paramètre manquant
500 Internal Server Error - Erreur serveur
```

## 🔑 Paramètres acceptés

### Upload
- `file` (UploadFile, required) - Fichier vidéo (.mp4, .ts)
- `sender_id` (string, required) - UUID ou ID utilisateur
- `receiver_id` (string, required) - ID du destinataire
- `encrypted_key` (string, required) - Clé AES chiffrée en base64
- `amount` (float, required) - Montant en EUR

### Query Parameters (si besoin)
- `limit` - Limiter le nombre de résultats
- `offset` - Pagination
- `status` - Filtrer par statut (UPLOADED, VERIFIED, etc)
- `sender_id` - Filtrer par expéditeur

## 📊 Réponses Type

### Succès Upload
```json
{
  "message": "Upload réussi",
  "video_id": "uuid-string",
  "status": "UPLOADED"
}
```

### Erreur Format
```json
{
  "detail": "Format non autorisé (.mp4, .ts uniquement)"
}
```

### Erreur Non Trouvé
```json
{
  "detail": "Vidéo non trouvée"
}
```

---

**Documentation API** - Janvier 2026  
Pour plus d'infos: http://localhost:8002/docs (Swagger UI)
