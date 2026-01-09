# Security Service - Tests

Exemples de tests pour le Security Service

## Test 1: Génération de clés RSA

```bash
curl -X POST "http://localhost:8003/api/security/keys/generate" \
  -F "key_size=3072" \
  -F "service_name=test"
```

**Réponse attendue:**
```json
{
  "private_key": "-----BEGIN PRIVATE KEY-----...",
  "public_key": "-----BEGIN PUBLIC KEY-----...",
  "key_size": 3072
}
```

## Test 2: Signature de données

```bash
# Préparer les données
echo -n "Hello World" | base64
# Résultat: SGVsbG8gV29ybGQ=

curl -X POST "http://localhost:8003/api/security/sign?service_name=test" \
  -H "Content-Type: application/json" \
  -d '{
    "data_b64": "SGVsbG8gV29ybGQ=",
    "private_key_pem": "<YOUR_PRIVATE_KEY>"
  }'
```

**Réponse attendue:**
```json
{
  "signature_b64": "base64-encoded-signature..."
}
```

## Test 3: Vérification de signature

```bash
curl -X POST "http://localhost:8003/api/security/verify?service_name=test" \
  -H "Content-Type: application/json" \
  -d '{
    "data_b64": "SGVsbG8gV29ybGQ=",
    "signature_b64": "<SIGNATURE_FROM_TEST2>",
    "public_key_pem": "<YOUR_PUBLIC_KEY>"
  }'
```

**Réponse attendue:**
```json
{
  "is_valid": true
}
```

## Test 4: Génération clé AES

```bash
curl -X POST "http://localhost:8003/api/security/aes/generate-key?key_size=256"
```

**Réponse attendue:**
```json
{
  "key_b64": "base64-encoded-aes-key...",
  "key_size": 256
}
```

## Test 5: Chiffrement AES-GCM

```bash
curl -X POST "http://localhost:8003/api/security/aes/encrypt?service_name=test" \
  -H "Content-Type: application/json" \
  -d '{
    "data_b64": "SGVsbG8gV29ybGQ=",
    "key_b64": "<AES_KEY_FROM_TEST4>"
  }'
```

**Réponse attendue:**
```json
{
  "ciphertext_b64": "encrypted-data...",
  "iv_b64": "initialization-vector..."
}
```

## Test 6: Déchiffrement AES-GCM

```bash
curl -X POST "http://localhost:8003/api/security/aes/decrypt?service_name=test" \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext_b64": "<CIPHERTEXT_FROM_TEST5>",
    "key_b64": "<AES_KEY_FROM_TEST4>",
    "iv_b64": "<IV_FROM_TEST5>"
  }'
```

**Réponse attendue:**
```json
{
  "plaintext_b64": "SGVsbG8gV29ybGQ="
}
```

## Test 7: Scan Snyk Code

```bash
curl -X POST "http://localhost:8003/api/security/scan/snyk-code"
```

**Réponse (si SNYK_TOKEN configuré):**
```json
{
  "status": "completed",
  "scan_type": "snyk_code",
  "vulnerabilities": {
    "total": 5,
    "by_severity": {
      "critical": 0,
      "high": 2,
      "medium": 3,
      "low": 0
    }
  }
}
```

**Réponse (si SNYK_TOKEN manquant):**
```json
{
  "status": "skipped",
  "message": "SNYK_TOKEN not configured"
}
```

## Test 8: Historique des scans

```bash
curl -X GET "http://localhost:8003/api/security/scan/history?limit=10"
```

**Réponse attendue:**
```json
{
  "scans": [
    {
      "id": 1,
      "scan_type": "snyk_code",
      "service_name": "all",
      "total_issues": 5,
      "critical": 0,
      "high": 2,
      "medium": 3,
      "low": 0,
      "status": "completed",
      "created_at": "2026-01-09T10:30:00"
    }
  ]
}
```

## Test 9: Logs d'audit

```bash
curl -X GET "http://localhost:8003/api/security/audit/logs?limit=20"
```

**Réponse attendue:**
```json
{
  "logs": [
    {
      "id": 1,
      "event_type": "KEY_GENERATED",
      "service_name": "auth",
      "user_id": null,
      "operation_details": "RSA-3072 keypair generated",
      "success": true,
      "timestamp": "2026-01-09T10:25:00"
    },
    {
      "id": 2,
      "event_type": "SIGNATURE_CREATED",
      "service_name": "video",
      "user_id": 42,
      "operation_details": "Data signed (32 bytes)",
      "success": true,
      "timestamp": "2026-01-09T10:26:00"
    }
  ]
}
```

## Test 10: Health Check

```bash
curl -X GET "http://localhost:8003/health"
```

**Réponse attendue:**
```json
{
  "status": "healthy",
  "service": "security-microservice",
  "version": "1.0.0"
}
```

---

## Tests d'intégration

### Test complet: Auth + Security

```bash
# 1. Signup via Auth (génère clés via Security)
curl -X POST "http://localhost:8001/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
  }'

# Réponse contient: private_key, public_key, token
```

### Test complet: Video + Security

```bash
# 1. Upload vidéo (nécessite token JWT)
curl -X POST "http://localhost:8002/api/videos/upload" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -F "file=@video.mp4" \
  -F "sender_id=user123" \
  -F "receiver_id=ADMIN" \
  -F "encrypted_key=base64-encrypted-aes-key" \
  -F "amount=100.00"

# 2. Signer vidéo (via Security service)
curl -X POST "http://localhost:8002/api/videos/<VIDEO_ID>/sign" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -F "private_key_pem=<YOUR_PRIVATE_KEY>"

# 3. Vérifier signature (via Security service)
curl -X POST "http://localhost:8002/api/videos/<VIDEO_ID>/verify-signature" \
  -F "public_key_pem=<YOUR_PUBLIC_KEY>"
```

---

## Configuration pour tests

### Variables d'environnement

```bash
# Dans docker-compose.yml ou .env
SNYK_TOKEN=your-snyk-token-here
SONAR_TOKEN=your-sonar-token-here
SONAR_HOST_URL=http://localhost:9000
JWT_SECRET=test-secret-change-in-production
```

### Installation Snyk CLI (optionnel pour tests locaux)

```bash
curl -Lo /usr/local/bin/snyk https://static.snyk.io/cli/latest/snyk-linux
chmod +x /usr/local/bin/snyk
snyk auth  # Configure avec votre token
```

### Installation SonarQube Scanner (optionnel)

```bash
# Via Docker
docker run -d --name sonarqube -p 9000:9000 sonarqube:latest

# Attendre démarrage puis accéder http://localhost:9000
# Créer token dans My Account > Security > Generate Tokens
```

---

## Résolution de problèmes

### Erreur: "SNYK_TOKEN not configured"
➜ Normal si variable non définie. Scans retournent "skipped".

### Erreur: "Failed to connect to security-service"
➜ Vérifier que Security service est démarré: `docker-compose ps`

### Erreur: "Invalid private key"
➜ Vérifier format PEM: doit commencer par `-----BEGIN PRIVATE KEY-----`

### Base de données connection error
➜ Vérifier MySQL health: `docker-compose logs mysql`
