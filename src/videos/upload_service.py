"""
Upload Service - Coordonnateur de microservice vidéo
Orchestre les composants: Storage Manager, Metadata Mapper, Expiration Engine
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import aiofiles

# ⚠️ Correction : importer Session de SQLAlchemy
from sqlalchemy.orm import Session

# Modules internes du service vidéo
from .models import Video
from .upload_api import router as upload_router
from .database import Base, engine, SessionLocal


# ============================================================================
# INITIALISATION DE L'APPLICATION
# ============================================================================

app = FastAPI(
    title="Video Microservice",
    description="Service de gestion vidéo - Architecture Microservice Moustass",
    version="1.0.0"
)

# Activer CORS pour le tableau de bord admin/auth - Configuration sécurisée
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,  # Cache CORS preflight requests for 1 hour
)

# Créer les tables au démarrage
Base.metadata.create_all(bind=engine)

# Inclure les routes d'upload
app.include_router(upload_router)


# ============================================================================
# DÉPENDANCE DATABASE
# ============================================================================

def get_db():
    """Dépendance pour obtenir la session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
# NOTE: Les routes vidéo sont gérées dans upload_api.py
# Ce fichier sert uniquement d'orchestrateur principal
# ============================================================================
