#!/bin/bash
# Script de démarrage complet - Moustass Video Platform

echo "=========================================="
echo "🎬 MOUSTASS VIDEO - Démarrage plateforme"
echo "=========================================="
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

echo "✅ Docker et Docker Compose trouvés"
echo ""

# Nettoyer les anciens conteneurs
echo "🧹 Nettoyage des anciens conteneurs..."
docker-compose down -v 2>/dev/null

echo ""
echo "🔧 Construction et démarrage des services..."
echo "   - MySQL (Base de données)"
echo "   - Security Service (Port 8003)"
echo "   - Auth Service (Port 8001)"
echo "   - Video Service (Port 8002)"
echo ""

# Lancer avec build
docker-compose up --build -d

# Attendre que les services soient prêts
echo ""
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier les health checks
echo ""
echo "🏥 Vérification de la santé des services..."

check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✅ $service_name : OK"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    echo "❌ $service_name : TIMEOUT"
    return 1
}

check_service "Auth Service" "http://localhost:8001/health"
check_service "Video Service" "http://localhost:8002/health"
check_service "Security Service" "http://localhost:8003/health"

echo ""
echo "=========================================="
echo "🚀 Plateforme Moustass Video opérationnelle!"
echo "=========================================="
echo ""
echo "📚 Accès services:"
echo "   • Auth Service:     http://localhost:8001"
echo "   • Video Service:    http://localhost:8002"
echo "   • Security Service: http://localhost:8003"
echo ""
echo "📖 Documentation API:"
echo "   • Auth:     http://localhost:8001/docs"
echo "   • Video:    http://localhost:8002/docs"
echo "   • Security: http://localhost:8003/docs"
echo ""
echo "🗄️  Base de données MySQL:"
echo "   • Host: localhost:3307"
echo "   • User: root"
echo "   • Password: rootpassword"
echo ""
echo "🛡️  Fonctionnalités Security Service:"
echo "   • Génération clés RSA-3072"
echo "   • Signature/Vérification digitale"
echo "   • Chiffrement AES-GCM"
echo "   • Validation JWT"
echo "   • Scans Snyk & SonarQube"
echo ""
echo "📊 Pour voir les logs:"
echo "   docker-compose logs -f [service-name]"
echo ""
echo "🛑 Pour arrêter:"
echo "   docker-compose down"
echo ""
echo "=========================================="
