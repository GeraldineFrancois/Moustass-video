"""
Expiration Engine - Surveille et gère l'expiration des vidéos
Nettoie automatiquement les fichiers et métadonnées expirées
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import Video, VideoStatus
from .storage_manager import StorageManager
import logging


logger = logging.getLogger(__name__)


class ExpirationEngine:
    """Gestionnaire de l'expiration des vidéos"""
    
    def __init__(self, db: Session, storage_manager: StorageManager):
        """
        Initialise le moteur d'expiration
        
        Args:
            db: Session SQLAlchemy
            storage_manager: Instance du gestionnaire de stockage
        """
        self.db = db
        self.storage = storage_manager
    
    def get_expired_videos(self) -> list:
        """
        Récupère toutes les vidéos expirées
        
        Returns:
            Liste des vidéos dont la date d'expiration est dépassée
        """
        now = datetime.now(timezone.utc)
        return self.db.query(Video).filter(
            (Video.expires_at <= now) & 
            (Video.status != VideoStatus.EXPIRED)
        ).all()
    
    def mark_expired(self, video: Video) -> Video:
        """
        Marque une vidéo comme expirée
        
        Args:
            video: Enregistrement vidéo
            
        Returns:
            Vidéo mise à jour
        """
        video.status = VideoStatus.EXPIRED
        self.db.commit()
        self.db.refresh(video)
        logger.info(f"Vidéo marquée comme expirée: {video.id}")
        return video
    
    async def cleanup_expired(self, delete_files: bool = True) -> dict:
        """
        Nettoie toutes les vidéos expirées
        
        Args:
            delete_files: Si True, supprime aussi les fichiers du stockage
            
        Returns:
            Statistiques du nettoyage
        """
        expired_videos = self.get_expired_videos()
        
        stats = {
            "total_expired": len(expired_videos),
            "marked_expired": 0,
            "files_deleted": 0,
            "errors": 0
        }
        
        for video in expired_videos:
            try:
                # Marquer comme expiré en BD
                self.mark_expired(video)
                stats["marked_expired"] += 1
                
                # Supprimer le fichier si demandé
                if delete_files:
                    try:
                        await self.storage.delete_video(video.storage_path)
                        stats["files_deleted"] += 1
                    except Exception as e:
                        logger.warning(f"Erreur suppression fichier {video.id}: {str(e)}")
                        stats["errors"] += 1
            except Exception as e:
                logger.error(f"Erreur nettoyage vidéo {video.id}: {str(e)}")
                stats["errors"] += 1
        
        return stats
    
    def get_retention_info(self, video: Video) -> dict:
        """
        Obtient les informations de rétention d'une vidéo
        
        Args:
            video: Enregistrement vidéo
            
        Returns:
            Dictionnaire avec infos de rétention
        """
        now = datetime.now(timezone.utc)
        
        if not video.expires_at:
            return {
                "status": "PERMANENT",
                "expires_at": None,
                "days_remaining": None,
                "is_expired": False
            }
        
        is_expired = video.expires_at <= now
        days_remaining = (video.expires_at - now).days if not is_expired else 0
        
        return {
            "status": "EXPIRING" if not is_expired else "EXPIRED",
            "expires_at": video.expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": is_expired
        }
    
    def extend_expiration(self, video: Video, days: int) -> dict:
        """
        Prolonge la date d'expiration d'une vidéo
        
        Args:
            video: Enregistrement vidéo
            days: Nombre de jours à ajouter
            
        Returns:
            Nouvelles informations de rétention
        """
        if video.expires_at:
            from datetime import timedelta
            video.expires_at = video.expires_at + timedelta(days=days)
            self.db.commit()
            self.db.refresh(video)
            logger.info(f"Expiration prolongée pour {video.id}: +{days} jours")
        
        return self.get_retention_info(video)
    
    async def schedule_cleanup(self, interval_seconds: int = 3600):
        """
        Planifie le nettoyage automatique des vidéos expirées
        À exécuter dans une tâche de fond (Celery, APScheduler, etc.)
        
        Args:
            interval_seconds: Intervalle entre les vérifications (défaut: 1h)
        """
        import asyncio
        
        while True:
            try:
                logger.info("Exécution du nettoyage des vidéos expirées...")
                stats = await self.cleanup_expired(delete_files=True)
                logger.info(f"Nettoyage terminé: {stats}")
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage: {str(e)}")
            
            await asyncio.sleep(interval_seconds)
