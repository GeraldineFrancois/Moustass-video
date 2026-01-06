"""
Upload & Download Controller - API REST
Gère le flux binaire avec la webapp frontend
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from videos.database import SessionLocal
from videos.storage_manager import StorageManager
from videos.metadata_mapper import MetadataMapper
from videos.expiration_engine import ExpirationEngine


# Configuration
UPLOAD_DIR = "uploads"
storage = StorageManager(upload_dir=UPLOAD_DIR)

# Routeur
router = APIRouter(prefix="/api/videos", tags=["Videos"])


def get_db():
    """Dépendance pour obtenir la session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# UPLOAD CONTROLLER - Gère le flux binaire d'upload
# ============================================================================

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    sender_id: str = Form(...),
    receiver_id: str = Form(...),
    encrypted_key: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint d'upload vidéo sécurisé
    
    - Valide le format du fichier
    - Sauvegarde le binaire chiffré via Storage Manager
    - Enregistre les métadonnées via Metadata Mapper
    """
    if not file:
        raise HTTPException(status_code=400, detail="Fichier manquant")
    
    # Valider le format du fichier
    ext = storage.validate_filename(file.filename)
    
    # Lire le contenu du fichier
    file_content = await file.read()
    
    # Utiliser les composants du service
    metadata = MetadataMapper(db)
    
    try:
        # Générer l'ID vidéo et sauvegarder
        video_id = str(uuid4())
        storage_path = await storage.save_video(video_id, ext, file_content)
        
        # Enregistrer les métadonnées
        video_record = metadata.create_video_record(
            sender_id=sender_id,
            receiver_id=receiver_id,
            storage_path=str(storage_path),
            encrypted_key=encrypted_key,
            amount=amount
        )
        
        return {
            "video_id": video_record.id,
            "status": video_record.status.value,
            "message": "Upload réussi"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")


# ============================================================================
# DOWNLOAD CONTROLLER - Gère le flux binaire de téléchargement
# ============================================================================

@router.get("/{video_id}/download")
async def download_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint de téléchargement vidéo
    
    - Vérifie l'existence de la vidéo
    - Récupère le fichier via Storage Manager
    - Retourne le binaire au client
    """
    metadata = MetadataMapper(db)
    expiration = ExpirationEngine(db, storage)
    
    try:
        # Récupérer les métadonnées
        video = metadata.get_video_by_id(video_id)
        
        # Vérifier l'expiration
        if video.status.value == "EXPIRED":
            raise HTTPException(status_code=410, detail="Vidéo expirée")
        
        # Extraire l'extension du storage_path
        import os
        extension = os.path.splitext(video.storage_path)[1]
        
        # Reconstruire le chemin de manière sécurisée via StorageManager
        # Ceci utilise la validation interne _ensure_safe_path()
        from pathlib import Path
        safe_filename = f"{video_id}{extension}"
        safe_path = storage._ensure_safe_path(storage.upload_dir / safe_filename)
        
        # Vérifier que le fichier existe
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="Fichier vidéo non trouvé")
        
        # Marquer comme téléchargée
        metadata.mark_as_downloaded(video_id)
        
        # Retourner le fichier
        return FileResponse(
            path=str(safe_path),
            filename=safe_filename,
            media_type="video/mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur download: {str(e)}")


# ============================================================================
# METADATA ENDPOINTS - Gestion des métadonnées
# ============================================================================

@router.get("/list")
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Liste toutes les vidéos avec pagination"""
    metadata = MetadataMapper(db)
    videos = metadata.get_all_videos(skip=skip, limit=limit)
    return [metadata.to_dict(v) for v in videos]


@router.get("/{video_id}")
async def get_video_info(
    video_id: str,
    db: Session = Depends(get_db)
):
    """Récupère les informations détaillées d'une vidéo"""
    metadata = MetadataMapper(db)
    video = metadata.get_video_by_id(video_id)
    return metadata.to_dict(video)


# ============================================================================
# DELETION ENDPOINT
# ============================================================================

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    Supprime une vidéo (fichier + métadonnées)
    
    - Supprime le fichier du stockage
    - Supprime l'enregistrement de la BD
    """
    metadata = MetadataMapper(db)
    
    try:
        video = metadata.get_video_by_id(video_id)
        
        # Supprimer le fichier
        await storage.delete_video(video.storage_path)
        
        # Supprimer les métadonnées
        metadata.delete_video_record(video_id)
        
        return {"message": "Vidéo supprimée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur suppression: {str(e)}")


# ============================================================================
# EXPIRATION ENDPOINTS
# ============================================================================

@router.get("/{video_id}/retention")
async def get_retention_info(
    video_id: str,
    db: Session = Depends(get_db)
):
    """Récupère les informations de rétention d'une vidéo"""
    metadata = MetadataMapper(db)
    expiration = ExpirationEngine(db, storage)
    
    video = metadata.get_video_by_id(video_id)
    return expiration.get_retention_info(video)


@router.post("/{video_id}/extend-retention")
async def extend_retention(
    video_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Prolonge la date d'expiration d'une vidéo"""
    metadata = MetadataMapper(db)
    expiration = ExpirationEngine(db, storage)
    
    video = metadata.get_video_by_id(video_id)
    return expiration.extend_expiration(video, days)


@router.post("/maintenance/cleanup-expired")
async def cleanup_expired(
    delete_files: bool = True,
    db: Session = Depends(get_db)
):
    """
    Nettoie les vidéos expirées
    À appeler manuellement ou via tâche planifiée
    """
    expiration = ExpirationEngine(db, storage)
    stats = await expiration.cleanup_expired(delete_files=delete_files)
    return stats


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health/status")
async def health_check():
    """Vérification de santé du service vidéo"""
    return {
        "status": "healthy",
        "service": "video-service",
        "components": {
            "storage": "ready",
            "metadata": "ready",
            "expiration": "ready"
        }
    }

