#!/bin/bash
# Script de configuration interactive pour .env
# Permet à chaque développeur/collègue de configurer ses accès MySQL
# ⚠️  Les credentials ne sont JAMAIS stockés dans git (.gitignore)

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🔐 Configuration Sécurisée - Moustass Video              ║"
echo "║     Chaque développeur configure ses propres accès         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier si .env existe
if [[ -f .env ]]; then
    echo "⚠️  Le fichier .env existe déjà."
    read -p "Voulez-vous le reconfigurer ? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Annulé. Votre .env existant est conservé."
        exit 0
    fi
    cp .env ".env.backup.$(date +%s)"
    echo "✅ Backup créé"
    echo ""
fi

# ==============================================================
# ÉTAPE 1: Mode de déploiement
# ==============================================================

echo "🔧 ÉTAPE 1 - Mode de déploiement"
echo "=================================="
echo ""
echo "1 = Docker Compose (MySQL en conteneur - recommandé en dev)"
echo "2 = MySQL Existant (Utilisez votre MySQL local/externe)"
echo ""
read -p "Choisissez l'option (1 ou 2): " mysql_mode

if [[ "$mysql_mode" != "1" && "$mysql_mode" != "2" ]]; then
    echo "❌ Option invalide"
    exit 1
fi

# Fonction pour générer mot de passe aléatoire
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Fonction pour générer JWT secret
generate_jwt_secret() {
    openssl rand -base64 64 | tr -d "=+/\n" | cut -c1-64
}

# ==============================================================
# ÉTAPE 2: Configuration
# ==============================================================

echo ""
echo "🔑 ÉTAPE 2 - Configuration des secrets"
echo "========================================"
echo ""

# JWT Secret
JWT_SECRET=$(generate_jwt_secret)
echo "✅ JWT Secret généré"

# MySQL Root Password
if [[ "$mysql_mode" == "1" ]]; then
    # Docker mode: générer aléatoirement
    MYSQL_ROOT_PASSWORD=$(generate_password)
    echo "✅ MySQL Root Password généré (Docker)"
else
    # Mode existant: demander à l'utilisateur
    echo ""
    echo "Vous utilisez MySQL existant."
    read -sp "Entrez le mot de passe root MySQL: " MYSQL_ROOT_PASSWORD
    echo ""
fi

# Database passwords
if [[ "$mysql_mode" == "1" ]]; then
    # Docker: générer aléatoirement
    VIDEO_DB_PASSWORD=$(generate_password)
    AUTH_DB_PASSWORD=$(generate_password)
    SECURITY_DB_PASSWORD=$(generate_password)
    echo "✅ Mots de passe des services générés"
else
    # Mode existant: demander
    echo ""
    echo "Comptes de service (video_user, auth_user, security_user):"
    echo "Utilisent-ils les mêmes mots de passe ou différents ?"
    echo ""
    echo "1 = Mêmes mots de passe (plus simple)"
    echo "2 = Différents (plus sécurisé)"
    read -p "Choisissez (1 ou 2): " password_mode
    
    if [[ "$password_mode" == "1" ]]; then
        read -sp "Entrez le mot de passe partagé: " common_pass
        echo ""
        VIDEO_DB_PASSWORD="$common_pass"
        AUTH_DB_PASSWORD="$common_pass"
        SECURITY_DB_PASSWORD="$common_pass"
    else
        read -sp "Mot de passe video_user: " VIDEO_DB_PASSWORD
        echo ""
        read -sp "Mot de passe auth_user: " AUTH_DB_PASSWORD
        echo ""
        read -sp "Mot de passe security_user: " SECURITY_DB_PASSWORD
        echo ""
    fi
fi

# ==============================================================
# ÉTAPE 3: Options MySQL
# ==============================================================

if [[ "$mysql_mode" == "2" ]]; then
    echo ""
    echo "🌐 ÉTAPE 3 - Connexion MySQL"
    echo "============================="
    echo ""
    
    read -p "Host MySQL [localhost]: " DB_HOST
    DB_HOST="${DB_HOST:-localhost}"
    
    read -p "Port MySQL [3306]: " DB_PORT
    DB_PORT="${DB_PORT:-3306}"
    
    echo "✅ Configuration MySQL: $DB_HOST:$DB_PORT"
else
    # Docker Compose
    DB_HOST="mysql"
    DB_PORT="3306"
fi

# ==============================================================
# ÉTAPE 4: Générer le fichier .env
# ==============================================================

echo ""
echo "📝 ÉTAPE 4 - Génération de .env"
echo "==============================="
echo ""

cat > .env << EOF
# ==========================================
# MOUSTASS VIDEO - CONFIGURATION
# ==========================================
# Généré le $(date)
# Mode: $([ "$mysql_mode" = "1" ] && echo "Docker Compose" || echo "MySQL Existant")
# ⚠️  CONFIDENTIEL - Ne JAMAIS commiter (voir .gitignore)
# ==========================================

# JWT Secret
JWT_SECRET=${JWT_SECRET}

# MySQL Root
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}

# Base de données Vidéos
MYSQL_DATABASE=videos_db
VIDEO_DB_USER=video_user
VIDEO_DB_PASSWORD=${VIDEO_DB_PASSWORD}
VIDEO_DB_HOST=${DB_HOST}
VIDEO_DB_PORT=${DB_PORT}
VIDEO_DB_NAME=videos_db
VIDEO_DATABASE_URL=mysql+pymysql://\${VIDEO_DB_USER}:\${VIDEO_DB_PASSWORD}@\${VIDEO_DB_HOST}:\${VIDEO_DB_PORT}/\${VIDEO_DB_NAME}

# Base de données Authentification
AUTH_DB_USER=auth_user
AUTH_DB_PASSWORD=${AUTH_DB_PASSWORD}
AUTH_DB_HOST=${DB_HOST}
AUTH_DB_PORT=${DB_PORT}
AUTH_DB_NAME=auth_db

# Base de données Sécurité
SECURITY_DB_USER=security_user
SECURITY_DB_PASSWORD=${SECURITY_DB_PASSWORD}
MYSQL_HOST=${DB_HOST}
MYSQL_PORT=${DB_PORT}
SECURITY_DB_NAME=security_db

# Configuration optionnelle
RSA_KEY_SIZE=3072
VIDEO_EXPIRATION_DAYS=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8002

# Scans de sécurité (optionnel)
SNYK_TOKEN=
SONAR_TOKEN=
SONAR_HOST_URL=http://localhost:9000
EOF

echo "✅ Fichier .env créé avec succès"
echo ""

# ==============================================================
# ÉTAPE 5: Vérification et étapes suivantes
# ==============================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ Configuration Complète              ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  📋 Prochaines étapes:                                     ║"
echo "║                                                            ║"
if [[ "$mysql_mode" == "1" ]]; then
    echo "║  1. docker compose down -v  (réinitialiser si besoin) ║"
    echo "║  2. docker compose up -d --build                       ║"
elif [[ "$mysql_mode" == "2" ]]; then
    echo "║  1. Vérifiez que les bases existent:                   ║"
    echo "║     mysql -u root -p -h $DB_HOST                       ║"
    echo "║     SHOW DATABASES;                                    ║"
    echo "║                                                        ║"
    echo "║  2. Si bases manquantes, créez-les:                    ║"
    echo "║     mysql -u root -p -h $DB_HOST < src/videos/init_database.sql        ║"
    echo "║     mysql -u root -p -h $DB_HOST < src/auth/init_database.sql          ║"
    echo "║     mysql -u root -p -h $DB_HOST < src/security/init_database.sql      ║"
    echo "║                                                        ║"
    echo "║  3. Lancez les services localement                     ║"
fi
echo "║                                                            ║"
echo "║  3. Vérifiez les services:                                 ║"
echo "║     curl http://localhost:8001/health  (Auth)             ║"
echo "║     curl http://localhost:8002/health  (Video)            ║"
echo "║     curl http://localhost:8003/health  (Security)         ║"
echo "║                                                            ║"
echo "║  📖 Voir SETUP_CUSTOM_PASSWORD.md pour plus d'info        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
