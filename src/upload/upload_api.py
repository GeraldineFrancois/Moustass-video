"""
API Router pour le service de upload vidéo
Endpoints exposés pour l'application frontend
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os

from upload.upload_service import (
    upload_video,
    list_videos,
    get_video_info,
    download_video,
    delete_video,
    health_check,
    get_db
)

router = APIRouter(prefix="/api/videos", tags=["Videos"])


@router.post("/upload")
async def api_upload_video(
    file: UploadFile = File(...),
    sender_id: str = Form(...),
    receiver_id: str = Form(...),
    encrypted_key: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint d'upload de vidéo
    Accepte les formats .mp4 et .ts
    """
    return await upload_video(
        file=file,
        sender_id=sender_id,
        receiver_id=receiver_id,
        encrypted_key=encrypted_key,
        amount=amount,
        db=db
    )


@router.get("/list")
async def api_list_videos(db: Session = Depends(get_db)):
    """
    Liste tous les vidéos uploadés avec leurs métadonnées
    Utilisé par le tableau dans le frontend
    """
    return await list_videos(db=db)


@router.get("/{video_id}")
async def api_get_video_info(video_id: str, db: Session = Depends(get_db)):
    """Récupère les informations détaillées d'une vidéo spécifique"""
    return await get_video_info(video_id=video_id, db=db)


@router.get("/{video_id}/download")
async def api_download_video(video_id: str, db: Session = Depends(get_db)):
    """Télécharge un fichier vidéo spécifique"""
    return await download_video(video_id=video_id, db=db)


@router.delete("/{video_id}")
async def api_delete_video(video_id: str, db: Session = Depends(get_db)):
    """Supprime une vidéo et ses données associées"""
    return await delete_video(video_id=video_id, db=db)


@router.get("/health/status")
async def api_health_check():
    """Vérification de santé du service upload"""
    return await health_check()

