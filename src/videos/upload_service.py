"""
Upload Service - Coordonnateur de microservice vidéo
Orchestre les composants: Storage Manager, Metadata Mapper, Expiration Engine
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import aiofiles

# ⚠️ Correction : importer Session de SQLAlchemy
from sqlalchemy.orm import Session

# Tes modules internes
from auth.database import get_db
from upload.upload_service import ensure_safe_path
from videos.models import Video
from .upload_api import router as upload_router
from .database import Base, engine


# ============================================================================
# INITIALISATION DE L'APPLICATION
# ============================================================================

app = FastAPI(
    title="Video Microservice",
    description="Service de gestion vidéo - Architecture Microservice Moustass",
    version="1.0.0"
)

# Créer les tables au démarrage
Base.metadata.create_all(bind=engine)

# Inclure les routes d'upload
app.include_router(upload_router)


# ============================================================================
# ROUTES UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Page d'accueil - Interface web d'upload"""
    html_path = Path(__file__).parent.parent / "ui" / "upload.html"
    
    if html_path.exists():
        async with aiofiles.open(html_path, "r", encoding="utf-8") as f:
            return await f.read()
    else:
        return """
        <html>
            <head>
                <title>Video Service</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h1>🎬 Service Upload Vidéo</h1>
                <p>Service de microservice pour la gestion sécurisée de vidéos.</p>
                <h2>Accès aux ressources:</h2>
                <ul>
                    <li><a href="/docs">Documentation API Swagger</a></li>
                    <li><a href="/redoc">Documentation ReDoc</a></li>
                    <li><a href="/openapi.json">OpenAPI Schema</a></li>
                </ul>
                <h2>Composants du service:</h2>
                <ul>
                    <li>✅ Upload & Download Controller</li>
                    <li>✅ Storage Manager</li>
                    <li>✅ Metadata Mapper</li>
                    <li>✅ Expiration Engine</li>
                </ul>
            </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """Vérification de santé simple"""
    return {
        "status": "healthy",
        "service": "video-microservice",
        "version": "1.0.0"
    }


# ============================================================================
# ÉVÉNEMENTS DE DÉMARRAGE/ARRÊT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Événement au démarrage du service"""
    print("🎬 Service Vidéo - Démarrage...")
    print("📦 Composants chargés:")
    print("   ✓ Upload & Download Controller")
    print("   ✓ Storage Manager")
    print("   ✓ Metadata Mapper")
    print("   ✓ Expiration Engine")
    print("📚 Documentation: /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement à l'arrêt du service"""
    print("🎬 Service Vidéo - Arrêt en cours...")


# ============================================================================
# ROUTES VIDÉO
# ============================================================================

@app.get("/videos/{video_id}")
async def get_video_info(video_id: str, db: Session = Depends(get_db)):
    """Récupère les infos d'une vidéo"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vidéo non trouvée")
    
    return {
        "id": video.id,
        "sender_id": video.sender_id,
        "receiver_id": video.receiver_id,
        "status": video.status.value,
        "amount": float(video.amount),
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "expires_at": video.expires_at.isoformat() if video.expires_at else None,
    }


@app.get("/videos/{video_id}/download")
async def download_video(video_id: str, db: Session = Depends(get_db)):
    """Télécharge une vidéo"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vidéo non trouvée")
    
    safe_path = ensure_safe_path(Path(video.storage_path))

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Fichier vidéo non trouvé")
    
    return FileResponse(
        path=safe_path,
        filename=safe_path.name,
        media_type="video/mp4"
    )


@app.delete("/videos/{video_id}")
async def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Supprime une vidéo"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vidéo non trouvée")
    
    # Supprime le fichier
    safe_path = ensure_safe_path(Path(video.storage_path))
    if safe_path.exists():
        safe_path.unlink()
    
    # Supprime la base de données
    db.delete(video)
    db.commit()
    
    return {"message": "Vidéo supprimée avec succès"}
