#!/bin/bash
# Script d'utilisation du système Moustass Video
# Exemples de requêtes cURL pour tester l'intégration

set -e

BASE_AUTH="http://localhost:8001"
BASE_VIDEO="http://localhost:8002/api/videos"

echo "═══════════════════════════════════════════════════════════"
echo "  Moustass Video - Script de Test d'Intégration"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. Créer un utilisateur admin
echo "1️⃣  Créer un utilisateur admin..."
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_AUTH/signup_admin" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "firstname=Alice&lastname=Admin&email=alice@example.com&password=SecurePass123!&confirm_password=SecurePass123!")

echo "$ADMIN_RESPONSE" | jq .
ADMIN_ID=$(echo "$ADMIN_RESPONSE" | jq -r '.user.id // empty')
ADMIN_PRIVATE_KEY=$(echo "$ADMIN_RESPONSE" | jq -r '.private_key // empty')

if [[ -z "$ADMIN_PRIVATE_KEY" ]]; then
  echo "❌ Erreur: Impossible de créer l'admin"
  exit 1
fi

# Sauvegarder la clé privée
echo "$ADMIN_PRIVATE_KEY" > /tmp/admin_private_key.pem
echo "✅ Clé privée sauvegardée: /tmp/admin_private_key.pem"
echo ""

# 2. Connecter l'utilisateur
echo "2️⃣  Connecter l'utilisateur..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_AUTH/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=alice@example.com&password=SecurePass123!")

echo "$LOGIN_RESPONSE" | jq .
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [[ -z "$TOKEN" ]]; then
  echo "❌ Erreur: Impossible de se connecter"
  exit 1
fi

echo "✅ Token obtenu"
echo ""

# 3. Uploader une vidéo de test
echo "3️⃣  Créer une vidéo de test..."
# Créer un fichier vidéo fictif (pour les tests)
echo "fake video content for testing" > /tmp/test_video.mp4

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_VIDEO/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_video.mp4" \
  -F "sender_id=alice@example.com" \
  -F "receiver_id=bob@example.com" \
  -F "encrypted_key=test_encrypted_key_base64" \
  -F "amount=100.00")

echo "$UPLOAD_RESPONSE" | jq .
VIDEO_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.video_id // empty')

if [[ -z "$VIDEO_ID" ]]; then
  echo "❌ Erreur: Impossible d'uploader la vidéo"
  exit 1
fi

echo "✅ Vidéo uploadée: $VIDEO_ID"
echo ""

# 4. Récupérer les infos de la vidéo
echo "4️⃣  Récupérer les infos de la vidéo..."
curl -s -X GET "$BASE_VIDEO/$VIDEO_ID" | jq .
echo ""

# 5. Signer la vidéo
echo "5️⃣  Signer la vidéo avec la clé privée..."
SIGN_RESPONSE=$(curl -s -X POST "$BASE_VIDEO/$VIDEO_ID/sign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "private_key_pem@/tmp/admin_private_key.pem")

echo "$SIGN_RESPONSE" | jq .
echo "✅ Vidéo signée avec succès"
echo ""

# 6. Vérifier la signature
echo "6️⃣  Vérifier la signature de la vidéo..."
# Récupérer la clé publique de l'utilisateur
PUBLIC_KEY_RESPONSE=$(curl -s -X GET "$BASE_AUTH/me" \
  -H "Authorization: Bearer $TOKEN")

PUBLIC_KEY=$(echo "$PUBLIC_KEY_RESPONSE" | jq -r '.public_key // empty')
echo "Clé publique obtenue"

# Vérifier la signature
VERIFY_RESPONSE=$(curl -s -X POST "$BASE_VIDEO/$VIDEO_ID/verify-signature" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "public_key_pem=<(echo \"$PUBLIC_KEY\")")

echo "$VERIFY_RESPONSE" | jq .
echo ""

# 7. Télécharger la vidéo
echo "7️⃣  Télécharger la vidéo..."
curl -s -X GET "$BASE_VIDEO/$VIDEO_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/downloaded_video.mp4

if [[ -f /tmp/downloaded_video.mp4 ]]; then
  echo "✅ Vidéo téléchargée: /tmp/downloaded_video.mp4"
else
  echo "❌ Erreur lors du téléchargement"
fi
echo ""

# 8. Essayer de supprimer la vidéo signée
echo "8️⃣  Essayer de supprimer la vidéo signée (devrait échouer)..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_VIDEO/$VIDEO_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$DELETE_RESPONSE" | jq .
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Test terminé avec succès!"
echo "═══════════════════════════════════════════════════════════"
