from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import aiofiles

from upload.database import SessionLocal
from upload.models import Video

app = FastAPI(title="Secure Video Upload API")

UPLOAD_DIR = Path("uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".ts"}

# ---------- DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Utils ----------
def validate_file(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Format non autorisé (.mp4, .ts uniquement)"
        )
    return ext


def ensure_safe_path(target: Path) -> Path:
    resolved = target.resolve()
    if not str(resolved).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Chemin de fichier invalide")
    return resolved

# ---------- Routes ----------
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    sender_id: str = Form(...),
    receiver_id: str = Form(...),
    encrypted_key: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    if not file:
        raise HTTPException(status_code=400, detail="Fichier manquant")

    ext = validate_file(file.filename)

    video_id = str(uuid4())
    filename = f"{video_id}{ext}"
    storage_path = ensure_safe_path(UPLOAD_DIR / filename)

    # Sauvegarde locale
    async with aiofiles.open(storage_path, "wb") as buffer:
        await buffer.write(await file.read())

    now = datetime.now(timezone.utc)

    video = Video(
        id=video_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        storage_path=str(storage_path),
        encrypted_key=encrypted_key,
        amount=amount,
        created_at=now,
        expires_at=now + timedelta(days=60)
    )

    db.add(video)
    db.commit()

    return {
        "message": "Upload réussi",
        "video_id": video_id,
        "status": "UPLOADED"
    }


@app.get("/videos")
async def list_videos(db: Session = Depends(get_db)):
    """Liste tous les vidéos uploadés"""
    videos = db.query(Video).all()
    return [
        {
            "id": v.id,
            "sender_id": v.sender_id,
            "receiver_id": v.receiver_id,
            "status": v.status.value,
            "amount": float(v.amount),
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "expires_at": v.expires_at.isoformat() if v.expires_at else None,
        }
        for v in videos
    ]


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


@app.get("/health")
async def health_check():
    """Vérification de santé du service"""
    return {"status": "healthy", "service": "upload-service"}
