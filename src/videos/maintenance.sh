#!/bin/bash

# Script de gestion et maintenance du Service Upload Vidéo
# Usage: bash maintenance.sh [command]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="upload-service"
SERVICE_PORT=8002
UPLOADS_DIR="$SCRIPT_DIR/uploads"
LOG_FILE="$SCRIPT_DIR/service.log"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Vérifier la santé du service
health_check() {
    print_header "Vérification de la santé du service"

    if curl -s http://localhost:$SERVICE_PORT/health > /dev/null 2>&1; then
        print_success "Service en bonne santé (port $SERVICE_PORT)"
    else
        print_error "Service indisponible ou port $SERVICE_PORT fermé"
        return 1
    fi
}

# Afficher les logs
show_logs() {
    print_header "Logs du service"
    if [[ -f "$LOG_FILE" ]]; then
        tail -50 "$LOG_FILE"
    else
        print_warning "Fichier de log non trouvé: $LOG_FILE"
    fi
}

# Obtenir les statistiques
stats() {
    print_header "Statistiques du service"

    # Nombre de fichiers
    if [[ -d "$UPLOADS_DIR" ]]; then
        FILE_COUNT=$(find "$UPLOADS_DIR" -type f | wc -l)
        DIR_SIZE=$(du -sh "$UPLOADS_DIR" | cut -f1)
        echo -e "Dossier uploads: $UPLOADS_DIR"
        echo -e "Fichiers stockés: $FILE_COUNT"
        echo -e "Taille totale: $DIR_SIZE"
    fi

    echo ""
    print_header "État du service"
    curl -s http://localhost:$SERVICE_PORT/api/videos/list | \
        jq -r '.[] | "  - \(.id): \(.sender_id) → \(.status) (€\(.amount))"' 2>/dev/null || echo "  (Aucune vidéo)"
}

# Nettoyer les fichiers
cleanup() {
    print_header "Nettoyage des fichiers temporaires"

    if [[ -d "$UPLOADS_DIR" ]]; then
        # Supprimer les fichiers vides
        find "$UPLOADS_DIR" -type f -size 0 -delete
        print_success "Fichiers vides supprimés"

        # Supprimer les fichiers de plus de 90 jours
        find "$UPLOADS_DIR" -type f -mtime +90 -delete
        print_success "Fichiers expirés supprimés (90+ jours)"
    fi

    # Nettoyer les fichiers de cache
    find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$SCRIPT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Cache Python nettoyé"
}

# Sauvegarder la base de données
backup() {
    print_header "Sauvegarde de la base de données"

    BACKUP_DIR="$SCRIPT_DIR/backups"
    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/videos_db_$TIMESTAMP.sql"

    if mysqldump -u videos_user -p videos_db > "$BACKUP_FILE" 2>/dev/null; then
        print_success "Sauvegarde créée: $BACKUP_FILE"

        # Compresser
        gzip "$BACKUP_FILE"
        print_success "Sauvegarde compressée"

        # Garder que les 10 dernières
        ls -t "$BACKUP_DIR"/*.gz | tail -n +11 | xargs -r rm
    else
        print_error "Erreur lors de la sauvegarde"
        return 1
    fi
}

# Installer les dépendances
install_deps() {
    print_header "Installation des dépendances"

    if ! command -v pip &> /dev/null; then
        print_error "pip n'est pas installé"
        return 1
    fi

    pip install --upgrade pip setuptools wheel
    pip install -r "$SCRIPT_DIR/requirements.txt"

    print_success "Dépendances installées"
}

# Tester l'API
test_api() {
    print_header "Test de l'API"

    echo "1. Health check..."
    curl -s http://localhost:$SERVICE_PORT/health | jq '.' || print_error "Échec"

    echo -e "\n2. Lister les vidéos..."
    curl -s http://localhost:$SERVICE_PORT/api/videos/list | jq '.' || print_error "Échec"

    echo -e "\n3. Créer un fichier de test..."
    dd if=/dev/zero bs=1M count=5 of="$SCRIPT_DIR/test-video.mp4" 2>/dev/null

    echo -e "\n4. Upload de test..."
    RESPONSE=$(curl -s -X POST http://localhost:$SERVICE_PORT/api/videos/upload \
        -F "file=@$SCRIPT_DIR/test-video.mp4" \
        -F "sender_id=test-user" \
        -F "receiver_id=ADMIN" \
        -F "encrypted_key=test-key" \
        -F "amount=100.00")

    echo "$RESPONSE" | jq '.' || print_error "Échec"

    VIDEO_ID=$(echo "$RESPONSE" | jq -r '.video_id' 2>/dev/null)

    if [[ -n "$VIDEO_ID" ]] && [[ "$VIDEO_ID" != "null" ]]; then
        echo -e "\n5. Récupérer les détails..."
        curl -s http://localhost:$SERVICE_PORT/api/videos/$VIDEO_ID | jq '.' || print_error "Échec"

        echo -e "\n6. Supprimer..."
        curl -s -X DELETE http://localhost:$SERVICE_PORT/api/videos/$VIDEO_ID | jq '.' || print_error "Échec"

        print_success "Tests passés ✅"
    else
        print_error "Échec de l'upload de test"
    fi

    # Cleanup
    rm -f "$SCRIPT_DIR/test-video.mp4"
}

# Démarrer le service
start() {
    print_header "Démarrage du service"

    if pgrep -f "python main_upload.py" > /dev/null; then
        print_warning "Service déjà en cours d'exécution"
        return 1
    fi

    cd "$SCRIPT_DIR"
    python main_upload.py >> "$LOG_FILE" 2>&1 &

    sleep 2

    if pgrep -f "python main_upload.py" > /dev/null; then
        print_success "Service démarré (PID: $(pgrep -f 'python main_upload.py'))"
    else
        print_error "Échec du démarrage du service"
        return 1
    fi
}

# Arrêter le service
stop() {
    print_header "Arrêt du service"

    if pgrep -f "python main_upload.py" > /dev/null; then
        pkill -f "python main_upload.py"
        sleep 1
        print_success "Service arrêté"
    else
        print_warning "Service non en cours d'exécution"
    fi
}

# Redémarrer le service
restart() {
    print_header "Redémarrage du service"
    stop
    sleep 2
    start
}

# Afficher l'aide
show_help() {
    cat << EOF
${BLUE}Service Upload Vidéo - Script de Maintenance${NC}

Usage: bash maintenance.sh [command]

Commandes disponibles:
  start             Démarrer le service
  stop              Arrêter le service
  restart           Redémarrer le service
  health            Vérifier la santé du service
  logs              Afficher les logs
  stats             Afficher les statistiques
  test              Tester l'API
  cleanup           Nettoyer les fichiers temporaires
  backup            Sauvegarder la base de données
  install           Installer les dépendances
  help              Afficher cette aide

Exemples:
  bash maintenance.sh start
  bash maintenance.sh health
  bash maintenance.sh stats
  bash maintenance.sh backup

${YELLOW}Note: Certaines commandes nécessitent des permissions sudo${NC}
EOF
}

# Main
COMMAND=${1:-help}

case $COMMAND in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    health)
        health_check
        ;;
    logs)
        show_logs
        ;;
    stats)
        stats
        ;;
    test)
        test_api
        ;;
    cleanup)
        cleanup
        ;;
    backup)
        backup
        ;;
    install)
        install_deps
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Commande inconnue: $COMMAND"
        show_help
        exit 1
        ;;
esac
