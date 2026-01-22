"""
Gestionnaire de stockage - Gère les fichiers vidéo sur le système de fichiers.

Ce module fournit une interface sécurisée pour lire, écrire et supprimer
les fichiers vidéo chiffrés. Il intègre une protection contre les attaques
de type "Path Traversal" (CWE-23).

Fonctionnalités :
    - Validation des extensions de fichiers autorisées
    - Protection contre les traversées de répertoire
    - Opérations asynchrones pour de meilleures performances
    - Intégration avec Docker Volume pour le stockage persistant

Auteur : Équipe Moustass Video
"""

from pathlib import Path
from typing import Set

import aiofiles
from fastapi import HTTPException


class StorageManager:
    """
    Gestionnaire de stockage sécurisé pour les fichiers vidéo.

    Cette classe encapsule toutes les opérations de système de fichiers
    et garantit que les accès se font uniquement dans le répertoire autorisé.

    Attributes:
        upload_dir: Chemin absolu du répertoire de stockage.
        ALLOWED_EXTENSIONS: Extensions de fichiers autorisées.
    """

    # Extensions vidéo autorisées (sécurité : liste blanche)
    ALLOWED_EXTENSIONS: Set[str] = {".mp4", ".ts", ".webm"}

    def __init__(self, upload_dir: str = "uploads") -> None:
        """
        Initialise le gestionnaire avec le répertoire de stockage.

        Args:
            upload_dir: Chemin relatif ou absolu du répertoire.
                        Créé automatiquement s'il n'existe pas.

        Exemple:
            >>> storage = StorageManager("/data/videos")
        """
        # Résout le chemin absolu pour éviter les ambiguïtés
        self.upload_dir = Path(upload_dir).resolve()

        # Crée le répertoire s'il n'existe pas
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # VALIDATION DES FICHIERS
    # =========================================================================

    def validate_filename(self, filename: str) -> str:
        """
        Valide le nom de fichier et extrait l'extension.

        Vérifie que :
        - Le nom de fichier n'est pas vide
        - L'extension est dans la liste blanche

        Args:
            filename: Nom du fichier uploadé par l'utilisateur.

        Returns:
            Extension du fichier (ex: ".mp4").

        Raises:
            HTTPException 400: Si le nom est vide ou le format non autorisé.

        Exemple:
            >>> ext = storage.validate_filename("video.mp4")
            >>> print(ext)
            '.mp4'
        """
        # Vérifie que le nom n'est pas vide
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Nom de fichier vide"
            )

        # Extrait l'extension en minuscules
        ext = Path(filename).suffix.lower()

        # Vérifie contre la liste blanche
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Format non autorisé. Acceptés : {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        return ext

    # =========================================================================
    # PROTECTION CONTRE LES TRAVERSÉES DE RÉPERTOIRE
    # =========================================================================

    def _ensure_safe_path(self, target: Path) -> Path:
        """
        Valide le chemin pour éviter les attaques de type Path Traversal.

        Cette méthode est critique pour la sécurité. Elle garantit que
        le chemin résolu reste à l'intérieur du répertoire autorisé.

        Args:
            target: Chemin cible à valider.

        Returns:
            Chemin résolu et validé.

        Raises:
            HTTPException 400: Si le chemin sort du répertoire autorisé.

        Exemple:
            >>> safe = storage._ensure_safe_path(Path("video.mp4"))
            >>> print(safe)
            '/uploads/video.mp4'

        Note:
            Les attaques comme "../../../etc/passwd" sont bloquées.
        """
        # Résout le chemin absolu (suit les liens symboliques)
        resolved = target.resolve()

        # Vérifie que le chemin reste dans le répertoire autorisé
        if not str(resolved).startswith(str(self.upload_dir)):
            raise HTTPException(
                status_code=400,
                detail="Chemin de fichier invalide (traversal détecté)"
            )

        return resolved

    # =========================================================================
    # OPÉRATIONS D'ÉCRITURE
    # =========================================================================

    async def save_video(
        self,
        video_id: str,
        extension: str,
        file_content: bytes
    ) -> Path:
        """
        Sauvegarde un fichier vidéo chiffré sur le disque.

        Le fichier est nommé avec l'UUID de la vidéo pour éviter
        les conflits et les problèmes de caractères spéciaux.

        Args:
            video_id: Identifiant unique (UUID) de la vidéo.
            extension: Extension du fichier (".mp4", ".ts", ".webm").
            file_content: Contenu binaire (chiffré) du fichier.

        Returns:
            Chemin complet du fichier sauvegardé.

        Raises:
            HTTPException 500: En cas d'erreur d'écriture disque.

        Exemple:
            >>> path = await storage.save_video("abc123", ".mp4", data)
            >>> print(path)
            '/uploads/abc123.mp4'
        """
        # Construit le nom de fichier sécurisé
        filename = f"{video_id}{extension}"

        # Valide le chemin contre les traversées
        storage_path = self._ensure_safe_path(self.upload_dir / filename)

        try:
            # Écrit le fichier de manière asynchrone
            async with aiofiles.open(storage_path, "wb") as f:
                await f.write(file_content)

            return storage_path

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la sauvegarde du fichier : {e}"
            )

    # =========================================================================
    # OPÉRATIONS DE LECTURE
    # =========================================================================

    async def read_video(self, storage_path: str) -> bytes:
        """
        Lit un fichier vidéo chiffré depuis le stockage.

        Args:
            storage_path: Chemin complet du fichier à lire.

        Returns:
            Contenu binaire du fichier.

        Raises:
            HTTPException 404: Si le fichier n'existe pas.
            HTTPException 500: En cas d'erreur de lecture.

        Exemple:
            >>> content = await storage.read_video("/uploads/abc123.mp4")
        """
        # Valide le chemin contre les traversées
        safe_path = self._ensure_safe_path(Path(storage_path))

        # Vérifie que le fichier existe
        if not safe_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Fichier vidéo non trouvé"
            )

        try:
            # Lit le fichier de manière asynchrone
            async with aiofiles.open(safe_path, "rb") as f:
                return await f.read()

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la lecture du fichier : {e}"
            )

    # =========================================================================
    # OPÉRATIONS DE SUPPRESSION
    # =========================================================================

    async def delete_video(self, storage_path: str) -> bool:
        """
        Supprime un fichier vidéo du stockage.

        Args:
            storage_path: Chemin complet du fichier à supprimer.

        Returns:
            True si le fichier a été supprimé, False s'il n'existait pas.

        Raises:
            HTTPException 500: En cas d'erreur de suppression.

        Exemple:
            >>> deleted = await storage.delete_video("/uploads/abc123.mp4")
            >>> print(deleted)
            True
        """
        # Valide le chemin contre les traversées
        safe_path = self._ensure_safe_path(Path(storage_path))

        try:
            if safe_path.exists():
                # Supprime le fichier de manière sécurisée
                safe_path.unlink()
                return True

            return False

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la suppression du fichier : {e}"
            )

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def get_file_size(self, storage_path: str) -> int:
        """
        Obtient la taille d'un fichier en octets.

        Args:
            storage_path: Chemin complet du fichier.

        Returns:
            Taille en bytes, ou 0 si le fichier n'existe pas.

        Exemple:
            >>> size = storage.get_file_size("/uploads/abc123.mp4")
            >>> print(f"{size / 1024:.2f} Ko")
        """
        safe_path = self._ensure_safe_path(Path(storage_path))

        if safe_path.exists():
            return safe_path.stat().st_size

        return 0

    def get_filename(self, storage_path: str) -> str:
        """
        Extrait le nom du fichier depuis un chemin complet.

        Args:
            storage_path: Chemin complet du fichier.

        Returns:
            Nom du fichier uniquement.

        Exemple:
            >>> name = storage.get_filename("/uploads/abc123.mp4")
            >>> print(name)
            'abc123.mp4'
        """
        return Path(storage_path).name
