#!/bin/bash

# Script de démarrage du service Upload Vidéo

echo "======================================"
echo "🚀 Service Upload Vidéo - Moustass"
echo "======================================"

# Vérifier si les dépendances sont installées
echo "📦 Installation des dépendances..."
pip install -q -r requirements.txt

if [[ $? -ne 0 ]]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

# Créer le dossier d'uploads s'il n'existe pas
mkdir -p uploads
echo "📁 Dossier uploads créé"

# Vérifier les variables d'environnement
if [[ ! -f ".env" ]]; then
    echo "⚠️  Fichier .env non trouvé, créez-le avec les paramètres de base de données"
fi

# Lancer le service
echo ""
echo "✅ Démarrage du service..."
echo ""
echo "📍 API: http://localhost:8002"
echo "📚 Documentation: http://localhost:8002/docs"
echo "🌐 Interface Web: http://localhost:8002/"
echo ""

python main_upload.py
