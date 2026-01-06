"""
Service de Upload Vidéo - Point d'entrée
Lance l'API FastAPI pour le microservice de gestion vidéo
"""

import uvicorn
import sys
from pathlib import Path

# Ajoute le chemin src au PYTHONPATH
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import du service coordonnateur
from videos.upload_service import app
# Import du routeur API
from videos.upload_api import router as upload_router

# ============================================================================
# ENREGISTREMENT DES ROUTES API
# ============================================================================

# Enregistre le routeur vidéo (tous les endpoints /api/videos/*)
app.include_router(upload_router)

# ============================================================================
# CONFIGURATION ET DÉMARRAGE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  🎬 SERVICE VIDÉO - MICROSERVICE MOUSTASS")
    print("="*70)
    print("\n📦 Architecture microservice:")
    print("   ✓ Upload & Download Controller")
    print("   ✓ Storage Manager")
    print("   ✓ Metadata Mapper")
    print("   ✓ Expiration Engine")
    print("\n🚀 Démarrage du service...")
    print("   📚 Documentation API: http://localhost:8002/docs")
    print("   🌐 Interface Web: http://localhost:8002")
    print("   💾 Base de données: MySQL videos_db")
    print("="*70 + "\n")
    
    # Démarrer le serveur
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=False  # Set to True only for development
    )
    )
