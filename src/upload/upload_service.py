from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta
import os
import shutil

from database import SessionLocal
from models import Video

app = FastAPI(title="Secure Video Upload API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    storage_path = os.path.join(UPLOAD_DIR, filename)

    # Sauvegarde locale
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    now = datetime.utcnow()

    video = Video(
        id=video_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        storage_path=storage_path,
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
