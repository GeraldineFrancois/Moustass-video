#!/bin/bash
# Script pour lancer tous les services Moustass Video

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ Moustass Video - Lancement des Services            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ docker-compose n'est pas installé. Veuillez installer docker-compose."
    exit 1
fi

# Charger les variables d'environnement si elles existent
if [ -f .env ]; then
    echo "📝 Chargement de .env..."
    export $(cat .env | grep -v '#' | xargs)
else
    echo "⚠️  Fichier .env non trouvé. Utilisation des valeurs par défaut."
    export JWT_SECRET="your-jwt-secret-change-in-production"
fi

echo ""
echo "📦 Construire les images Docker..."
docker compose build --no-cache

echo ""
echo "🚀 Démarrer tous les services..."
docker compose up -d

echo ""
echo "⏳ Attendre que les services démarrent..."
sleep 5

# Vérifier l'état des services
echo ""
echo "🔍 Vérification de l'état des services..."
echo ""

# Tester le service d'authentification
echo "📌 Service d'authentification (port 8001):"
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "   ✅ OK - http://localhost:8001"
else
    echo "   ❌ ERREUR - Service non accessible"
fi

# Tester le service vidéo
echo "📌 Service vidéo (port 8002):"
if curl -s http://localhost:8002/api/videos/health/status > /dev/null 2>&1; then
    echo "   ✅ OK - http://localhost:8002"
else
    echo "   ❌ ERREUR - Service non accessible"
fi

# Tester MySQL
echo "📌 Base de données MySQL (port 3306):"
if docker exec moustass-mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
    echo "   ✅ OK"
else
    echo "   ⚠️  Base de données en cours d'initialisation..."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   Services Démarrés                        ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  🔐 Auth Service:  http://localhost:8001                  ║"
echo "║  🎥 Video Service: http://localhost:8002                  ║"
echo "║  💾 MySQL:         localhost:3306                         ║"
echo "║                                                            ║"
echo "║  📊 Logs:                                                  ║"
echo "║     docker-compose logs -f                                ║"
echo "║                                                            ║"
echo "║  🛑 Arrêter:                                              ║"
echo "║     docker-compose down                                   ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
