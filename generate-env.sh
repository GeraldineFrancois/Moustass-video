#!/bin/bash
# Script de génération automatique du fichier .env avec des mots de passe sécurisés

set -e

echo "🔐 Générateur de Configuration Sécurisée - Moustass Video"
echo "=========================================================="
echo ""

# Vérifier si .env existe déjà
if [ -f .env ]; then
    echo "⚠️  Le fichier .env existe déjà."
    read -p "Voulez-vous le remplacer ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Annulé. Conservez votre fichier .env existant."
        exit 0
    fi
    cp .env .env.backup.$(date +%s)
    echo "✅ Backup créé: .env.backup.*"
fi

# Fonction pour générer un mot de passe aléatoire
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Fonction pour générer un secret JWT (plus long)
generate_jwt_secret() {
    openssl rand -base64 64 | tr -d "=+/\n" | cut -c1-64
}

echo "🔑 Génération des secrets aléatoires..."
echo ""

# Générer les secrets
JWT_SECRET=$(generate_jwt_secret)
MYSQL_ROOT_PASSWORD=$(generate_password)
VIDEO_DB_PASSWORD=$(generate_password)
AUTH_DB_PASSWORD=$(generate_password)
SECURITY_DB_PASSWORD=$(generate_password)

# Créer le fichier .env
cat > .env << EOF
# ==========================================
# MOUSTASS VIDEO - CONFIGURATION
# ==========================================
# Généré automatiquement le $(date)
# ⚠️  Ne commitez JAMAIS ce fichier dans git
# ==========================================

# ==========================================
# JWT SECRET
# ==========================================
JWT_SECRET=${JWT_SECRET}

# ==========================================
# MYSQL ROOT
# ==========================================
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}

# ==========================================
# BASE DE DONNÉES VIDÉOS
# ==========================================
MYSQL_DATABASE=videos_db
VIDEO_DB_USER=video_user
VIDEO_DB_PASSWORD=${VIDEO_DB_PASSWORD}
VIDEO_DB_HOST=mysql
VIDEO_DB_PORT=3306
VIDEO_DB_NAME=videos_db

# URL complète de connexion
VIDEO_DATABASE_URL=mysql+pymysql://\${VIDEO_DB_USER}:\${VIDEO_DB_PASSWORD}@\${VIDEO_DB_HOST}:\${VIDEO_DB_PORT}/\${VIDEO_DB_NAME}

# ==========================================
# BASE DE DONNÉES AUTHENTIFICATION
# ==========================================
AUTH_DB_USER=auth_user
AUTH_DB_PASSWORD=${AUTH_DB_PASSWORD}
AUTH_DB_NAME=auth_db

# ==========================================
# BASE DE DONNÉES SÉCURITÉ
# ==========================================
SECURITY_DB_USER=security_user
SECURITY_DB_PASSWORD=${SECURITY_DB_PASSWORD}

# ==========================================
# CONFIGURATION OPTIONNELLE
# ==========================================
RSA_KEY_SIZE=3072
VIDEO_EXPIRATION_DAYS=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8002

# ==========================================
# SNYK & SONARQUBE (Optionnel)
# ==========================================
SNYK_TOKEN=
SONAR_TOKEN=
SONAR_HOST_URL=http://localhost:9000
EOF

echo "✅ Fichier .env créé avec succès !"
echo ""
echo "📋 Résumé de la configuration :"
echo "   - JWT_SECRET: ${JWT_SECRET:0:20}... (64 caractères)"
echo "   - MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:0:10}... (32 caractères)"
echo "   - VIDEO_DB_PASSWORD: ${VIDEO_DB_PASSWORD:0:10}... (32 caractères)"
echo "   - AUTH_DB_PASSWORD: ${AUTH_DB_PASSWORD:0:10}... (32 caractères)"
echo "   - SECURITY_DB_PASSWORD: ${SECURITY_DB_PASSWORD:0:10}... (32 caractères)"
echo ""
echo "⚠️  IMPORTANT : Sauvegardez ces secrets dans un gestionnaire de mots de passe !"
echo ""
echo "🚀 Vous pouvez maintenant démarrer les services :"
echo "   docker compose up -d"
echo ""
echo "🔒 Vérifiez que .env est bien ignoré par git :"
echo "   git status"
echo ""
