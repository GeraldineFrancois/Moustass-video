from sqlalchemy import Column, String, Text, Enum, DECIMAL, TIMESTAMP, Integer, Boolean
from .database import Base
import enum
from datetime import datetime

class VideoStatus(enum.Enum):
    UPLOADED = "UPLOADED"
    SIGNED = "SIGNED"
    VERIFIED = "VERIFIED"
    DOWNLOADED = "DOWNLOADED"
    EXPIRED = "EXPIRED"

class Video(Base):
    __tablename__ = "videos"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(String(36), nullable=False)
    receiver_id = Column(String(36), nullable=False)
    storage_path = Column(String(255), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    iv = Column(String(24), nullable=True)  # IV AES-GCM en base64 (12 bytes)
    amount = Column(DECIMAL(15, 2), nullable=False)
    status = Column(Enum(VideoStatus, native_enum=False), default=VideoStatus.UPLOADED)
    signature = Column(Text, nullable=True)
    is_signed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    expires_at = Column(TIMESTAMP, nullable=False)
