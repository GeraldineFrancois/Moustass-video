"""
Metadata Mapper - Interface avec la base de données MySQL
Enregistre et récupère les métadonnées des vidéos
"""

from sqlalchemy.orm import Session
from .models import Video, VideoStatus
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import HTTPException


class MetadataMapper:
    """Gestionnaire des métadonnées vidéo en base de données"""
    
    def __init__(self, db: Session):
        """
        Initialise le mapper avec une session DB
        
        Args:
            db: Session SQLAlchemy
        """
        self.db = db
    
    def create_video_record(
        self,
        user_id: int,
        sender_id: str,
        receiver_id: str,
        storage_path: str,
        encrypted_key: str,
        iv: str,
        amount: float,
        expiration_days: int = 60
    ) -> Video:
        """
        Crée un nouvel enregistrement vidéo en BD
        
        Args:
            user_id: ID de l'utilisateur authentifié (propriétaire)
            sender_id: ID de l'expéditeur
            receiver_id: ID du destinataire
            storage_path: Chemin de stockage du fichier
            encrypted_key: Clé AES chiffrée (RSA-3072)
            iv: Vecteur d'initialisation AES-GCM en base64
            amount: Montant en EUR
            expiration_days: Nombre de jours avant expiration (défaut: 60)
            
        Returns:
            Enregistrement Video créé
        """
        video_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=expiration_days)
        
        video = Video(
            id=video_id,
            user_id=user_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            storage_path=storage_path,
            encrypted_key=encrypted_key,
            iv=iv,
            amount=amount,
            status=VideoStatus.UPLOADED,
            created_at=now,
            expires_at=expires_at
        )
        
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        
        return video
    
    def get_video_by_id(self, video_id: str) -> Video:
        """
        Récupère une vidéo par son ID
        
        Args:
            video_id: UUID unique de la vidéo
            
        Returns:
            Enregistrement Video
            
        Raises:
            HTTPException: Si la vidéo n'existe pas
        """
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Vidéo non trouvée")
        return video
    
    def get_all_videos(self, skip: int = 0, limit: int = 100) -> list:
        """
        Récupère la liste de toutes les vidéos
        
        Args:
            skip: Nombre d'enregistrements à sauter (pagination)
            limit: Nombre maximal d'enregistrements
            
        Returns:
            Liste des vidéos
        """
        return self.db.query(Video).offset(skip).limit(limit).all()
    
    def get_videos_by_sender(self, sender_id: str) -> list:
        """
        Récupère toutes les vidéos d'un expéditeur
        
        Args:
            sender_id: ID de l'expéditeur
            
        Returns:
            Liste des vidéos
        """
        return self.db.query(Video).filter(Video.sender_id == sender_id).all()
    
    def get_videos_by_receiver(self, receiver_id: str) -> list:
        """
        Récupère toutes les vidéos reçues
        
        Args:
            receiver_id: ID du destinataire
            
        Returns:
            Liste des vidéos
        """
        return self.db.query(Video).filter(Video.receiver_id == receiver_id).all()
    
    def get_active_videos(self) -> list:
        """
        Récupère toutes les vidéos non expirées
        
        Returns:
            Liste des vidéos actives
        """
        now = datetime.now(timezone.utc)
        return self.db.query(Video).filter(
            (Video.expires_at > now) | (Video.expires_at == None)
        ).all()
    
    def update_video_status(self, video_id: str, status: VideoStatus) -> Video:
        """
        Met à jour le statut d'une vidéo
        
        Args:
            video_id: UUID de la vidéo
            status: Nouveau statut
            
        Returns:
            Vidéo mise à jour
        """
        video = self.get_video_by_id(video_id)
        video.status = status
        self.db.commit()
        self.db.refresh(video)
        return video
    
    def mark_as_downloaded(self, video_id: str) -> Video:
        """
        Marque une vidéo comme téléchargée
        
        Args:
            video_id: UUID de la vidéo
            
        Returns:
            Vidéo mise à jour
        """
        return self.update_video_status(video_id, VideoStatus.DOWNLOADED)
    
    def mark_as_verified(self, video_id: str) -> Video:
        """
        Marque une vidéo comme vérifiée
        
        Args:
            video_id: UUID de la vidéo
            
        Returns:
            Vidéo mise à jour
        """
        return self.update_video_status(video_id, VideoStatus.VERIFIED)
    
    def mark_as_expired(self, video_id: str) -> Video:
        """
        Marque une vidéo comme expirée
        
        Args:
            video_id: UUID de la vidéo
            
        Returns:
            Vidéo mise à jour
        """
        return self.update_video_status(video_id, VideoStatus.EXPIRED)
    
    def delete_video_record(self, video_id: str) -> bool:
        """
        Supprime un enregistrement vidéo de la BD
        
        Args:
            video_id: UUID de la vidéo
            
        Returns:
            True si supprimé
        """
        video = self.get_video_by_id(video_id)
        self.db.delete(video)
        self.db.commit()
        return True
    
    def to_dict(self, video: Video) -> dict:
        """
        Convertit un enregistrement Video en dictionnaire
        
        Args:
            video: Enregistrement Video
            
        Returns:
            Dictionnaire sérialisé
        """
        return {
            "id": video.id,
            "user_id": video.user_id,
            "sender_id": video.sender_id,
            "receiver_id": video.receiver_id,
            "storage_path": video.storage_path,
            "status": video.status.value,
            "is_signed": video.is_signed,
            "encrypted_key": video.encrypted_key,
            "iv": video.iv,
            "amount": float(video.amount),
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "expires_at": video.expires_at.isoformat() if video.expires_at else None,
        }
    
    def update_video_signature(self, video_id: str, signature: str) -> Video:
        """
        Met à jour la signature et le statut d'une vidéo
        
        Args:
            video_id: UUID de la vidéo
            signature: Signature B64 du hash du fichier
            
        Returns:
            Vidéo mise à jour
        """
        video = self.get_video_by_id(video_id)
        video.signature = signature
        video.is_signed = True
        video.status = VideoStatus.SIGNED
        self.db.commit()
        self.db.refresh(video)
        return video
