"""
Service de Upload Vidéo - Point d'entrée
Lance l'API FastAPI pour le service de gestion vidéo
"""

import uvicorn
import sys
from pathlib import Path
from fastapi.responses import HTMLResponse

# Ajoute le chemin src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from upload.upload_service import app
from upload.upload_api import router as upload_router

# Enregistre les routes
app.include_router(upload_router)

# Routes UI basiques
@app.get("/", response_class=HTMLResponse)
async def root():
    """Page d'accueil - Interface web d'upload"""
    # Lire le fichier upload.html
    html_path = Path(__file__).parent / "src" / "ui" / "upload.html"
    
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """
        <html>
            <body>
                <h1>Service Upload Vidéo</h1>
                <p>Interface non trouvée. Accédez à la <a href="/docs">documentation API</a></p>
            </body>
        </html>
        """


if __name__ == "__main__":
    print("🚀 Démarrage du service de Upload Vidéo...")
    print("📚 Documentation API: http://localhost:8002/docs")
    print("🔌 Service disponible sur: http://localhost:8002")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
