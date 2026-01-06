"""
Storage Manager - Gère l'interaction avec le système de fichiers
Interface avec Docker Volume pour lire/écrire les données chiffrées
"""

from pathlib import Path
import aiofiles
from fastapi import HTTPException


class StorageManager:
    """Gestionnaire de stockage sécurisé des fichiers vidéo"""
    
    ALLOWED_EXTENSIONS = {".mp4", ".ts"}
    
    def __init__(self, upload_dir: str = "uploads"):
        """
        Initialise le gestionnaire de stockage
        
        Args:
            upload_dir: Répertoire de stockage (Docker Volume recommandé)
        """
        self.upload_dir = Path(upload_dir).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_filename(self, filename: str) -> str:
        """
        Valide le nom de fichier et retourne l'extension
        
        Args:
            filename: Nom du fichier uploadé
            
        Returns:
            Extension du fichier (.mp4, .ts)
            
        Raises:
            HTTPException: Si le format n'est pas autorisé
        """
        if not filename:
            raise HTTPException(status_code=400, detail="Nom de fichier vide")
        
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Format non autorisé. Acceptés: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        return ext
    
    def _ensure_safe_path(self, target: Path) -> Path:
        """
        Valide le chemin pour éviter les traversals
        
        Args:
            target: Chemin cible
            
        Returns:
            Chemin résolu et validé
            
        Raises:
            HTTPException: Si le chemin est en dehors du répertoire autorisé
        """
        resolved = target.resolve()
        if not str(resolved).startswith(str(self.upload_dir)):
            raise HTTPException(
                status_code=400, 
                detail="Chemin de fichier invalide (traversal détecté)"
            )
        return resolved
    
    async def save_video(self, video_id: str, extension: str, file_content: bytes) -> Path:
        """
        Sauvegarde un fichier vidéo chiffré
        
        Args:
            video_id: ID unique du UUID
            extension: Extension du fichier (.mp4, .ts)
            file_content: Contenu binaire du fichier
            
        Returns:
            Chemin complet du fichier sauvegardé
            
        Raises:
            HTTPException: En cas d'erreur d'écriture
        """
        filename = f"{video_id}{extension}"
        storage_path = self._ensure_safe_path(self.upload_dir / filename)
        
        try:
            async with aiofiles.open(storage_path, "wb") as f:
                await f.write(file_content)
            return storage_path
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la sauvegarde du fichier: {str(e)}"
            )
    
    async def read_video(self, storage_path: str) -> bytes:
        """
        Lit un fichier vidéo chiffré depuis le stockage
        
        Args:
            storage_path: Chemin du fichier à lire
            
        Returns:
            Contenu binaire du fichier
            
        Raises:
            HTTPException: Si le fichier n'existe pas ou erreur de lecture
        """
        safe_path = self._ensure_safe_path(Path(storage_path))
        
        if not safe_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Fichier vidéo non trouvé"
            )
        
        try:
            async with aiofiles.open(safe_path, "rb") as f:
                return await f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la lecture du fichier: {str(e)}"
            )
    
    async def delete_video(self, storage_path: str) -> bool:
        """
        Supprime un fichier vidéo du stockage
        
        Args:
            storage_path: Chemin du fichier à supprimer
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            HTTPException: En cas d'erreur
        """
        safe_path = self._ensure_safe_path(Path(storage_path))
        
        try:
            if safe_path.exists():
                safe_path.unlink()  # Suppression sécurisée
                return True
            return False
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la suppression du fichier: {str(e)}"
            )
    
    def get_file_size(self, storage_path: str) -> int:
        """
        Obtient la taille d'un fichier en octets
        
        Args:
            storage_path: Chemin du fichier
            
        Returns:
            Taille du fichier en bytes
        """
        safe_path = self._ensure_safe_path(Path(storage_path))
        if safe_path.exists():
            return safe_path.stat().st_size
        return 0
    
    def get_filename(self, storage_path: str) -> str:
        """
        Extrait le nom du fichier du chemin complet
        
        Args:
            storage_path: Chemin du fichier
            
        Returns:
            Nom du fichier
        """
        return Path(storage_path).name
