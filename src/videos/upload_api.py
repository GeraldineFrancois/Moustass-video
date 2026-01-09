"""
Upload & Download Controller - API REST
Gère le flux binaire avec la webapp frontend
Intégré avec le service d'authentification et de signature
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from .database import SessionLocal
from .storage_manager import StorageManager
from .metadata_mapper import MetadataMapper
from .expiration_engine import ExpirationEngine
from .security import get_current_user, sign_data, verify_signature
import hashlib
import os


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
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint d'upload vidéo sécurisé - AUTHENTIFICATION REQUISE
    
    - Vérifie le JWT token de l'utilisateur
    - Valide le format du fichier
    - Sauvegarde le binaire chiffré
    - Enregistre les métadonnées avec user_id
    
    Une vidéo doit être signée avant d'être lue/téléchargée par d'autres
    """
    # Vérifier l'authentification
    user_id = get_current_user(authorization)
    
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
        
        # Enregistrer les métadonnées avec user_id
        video_record = metadata.create_video_record(
            user_id=user_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            storage_path=str(storage_path),
            encrypted_key=encrypted_key,
            amount=amount
        )
        
        return {
            "video_id": video_record.id,
            "user_id": user_id,
            "status": video_record.status.value,
            "is_signed": video_record.is_signed,
            "message": "Upload réussi. Signez la vidéo avant qu'elle soit accessible."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")


# ============================================================================
# SIGNATURE CONTROLLER - Signer et vérifier les vidéos
# ============================================================================

@router.post("/{video_id}/sign")
async def sign_video(
    video_id: str,
    private_key_pem: str = Form(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Signe une vidéo avec la clé privée de l'utilisateur
    
    - Vérifie que l'utilisateur est propriétaire de la vidéo
    - Signe le hash du fichier avec sa clé privée RSA
    - Marque la vidéo comme signée (immutable)
    - Après signature, la vidéo ne peut plus être modifiée
    """
    # Vérifier l'authentification
    user_id = get_current_user(authorization)
    
    metadata = MetadataMapper(db)
    
    try:
        video = metadata.get_video_by_id(video_id)
        
        # Vérifier que l'utilisateur est propriétaire
        if video.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Vous ne pouvez signer que vos propres vidéos"
            )
        
        # Vérifier si déjà signée
        if video.is_signed:
            raise HTTPException(
                status_code=400,
                detail="Cette vidéo est déjà signée et immuable"
            )
        
        # Calculer le hash du fichier
        file_content = await storage.read_video(video.storage_path)
        file_hash = hashlib.sha256(file_content).digest()
        
        # Signer le hash
        signature_b64 = sign_data(file_hash, private_key_pem)
        
        # Mettre à jour la vidéo
        metadata.update_video_signature(video_id, signature_b64)
        
        return {
            "video_id": video_id,
            "status": "SIGNED",
            "signature": signature_b64[:50] + "...",  # Afficher partiellement
            "message": "Vidéo signée avec succès. Elle est maintenant immuable."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur signature: {str(e)}")


@router.post("/{video_id}/verify-signature")
async def verify_video_signature(
    video_id: str,
    public_key_pem: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Vérifie la signature d'une vidéo
    
    - Récupère le hash original du fichier
    - Vérifie la signature avec la clé publique fournie
    - Retourne True/False si la signature est valide
    
    Permet à quelqu'un d'autre de vérifier qu'une vidéo
    vient bien d'un utilisateur spécifique
    """
    metadata = MetadataMapper(db)
    
    try:
        video = metadata.get_video_by_id(video_id)
        
        # Vérifier si la vidéo est signée
        if not video.is_signed or not video.signature:
            raise HTTPException(
                status_code=400,
                detail="Cette vidéo n'a pas été signée"
            )
        
        # Récupérer le contenu et calculer le hash
        file_content = await storage.read_video(video.storage_path)
        file_hash = hashlib.sha256(file_content).digest()
        
        # Vérifier la signature
        is_valid = verify_signature(
            file_hash,
            video.signature,
            public_key_pem
        )
        
        return {
            "video_id": video_id,
            "is_valid": is_valid,
            "signer": "unknown" if not is_valid else "verified",
            "message": "Signature valide" if is_valid else "Signature invalide ou fichier modifié"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur vérification: {str(e)}")


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
    include_encrypted_key: bool = False,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Récupère les informations détaillées d'une vidéo"""
    metadata = MetadataMapper(db)
    video = metadata.get_video_by_id(video_id)
    data = metadata.to_dict(video)
    if include_encrypted_key:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization requise")
        get_current_user(authorization)
        data["encrypted_key"] = video.encrypted_key
        data["signature"] = video.signature
    return data


# ============================================================================
# DELETION ENDPOINT
# ============================================================================

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Supprime une vidéo (fichier + métadonnées)
    
    - Authentification requise
    - Ne peut supprimer que si propriétaire
    - Ne peut pas supprimer une vidéo signée (immuable)
    """
    # Vérifier l'authentification
    user_id = get_current_user(authorization)
    
    metadata = MetadataMapper(db)
    
    try:
        video = metadata.get_video_by_id(video_id)
        
        # Vérifier que l'utilisateur est propriétaire
        if video.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Vous ne pouvez supprimer que vos propres vidéos"
            )
        
        # Empêcher la suppression de vidéos signées
        if video.is_signed:
            raise HTTPException(
                status_code=403,
                detail="Impossible de supprimer une vidéo signée (immuable)"
            )
        
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

