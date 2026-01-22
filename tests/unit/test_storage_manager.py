"""
Tests unitaires pour le module src/videos/storage_manager.py.

Ce module teste la gestion du stockage des fichiers vidéo :
- Validation des noms de fichiers et extensions autorisées
- Protection contre les attaques path traversal
- Opérations CRUD asynchrones (save, read, delete)
- Gestion des erreurs I/O

Auteur: Équipe Moustass Video
"""

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from src.videos.storage_manager import StorageManager


# =============================================================================
# HELPERS
# =============================================================================

def _run_async(coro):
    """
    Exécute une coroutine de manière synchrone.

    Args:
        coro: Coroutine à exécuter

    Returns:
        Résultat de la coroutine
    """
    return asyncio.run(coro)


# =============================================================================
# TESTS : VALIDATION DES NOMS DE FICHIERS
# =============================================================================

def test_validate_filename_allowed_extensions(tmp_path):
    """
    Vérifie que les extensions autorisées sont acceptées.

    Extensions valides : .mp4, .webm, .ts
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    assert manager.validate_filename("video.webm") == ".webm"
    assert manager.validate_filename("clip.mp4") == ".mp4"


def test_validate_filename_empty_rejected(tmp_path):
    """Vérifie qu'un nom de fichier vide est rejeté."""
    manager = StorageManager(upload_dir=str(tmp_path))

    with pytest.raises(Exception):
        manager.validate_filename("")


def test_validate_filename_invalid_extension_rejected(tmp_path):
    """Vérifie qu'une extension non autorisée est rejetée."""
    manager = StorageManager(upload_dir=str(tmp_path))

    with pytest.raises(Exception):
        manager.validate_filename("malware.exe")

    with pytest.raises(Exception):
        manager.validate_filename("document.txt")


# =============================================================================
# TESTS : PROTECTION PATH TRAVERSAL
# =============================================================================

def test_ensure_safe_path_blocks_traversal(tmp_path):
    """
    Vérifie que les tentatives de path traversal sont bloquées.

    Empêche l'accès à des fichiers en dehors du répertoire d'upload.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    # Tentative d'échappement du répertoire
    malicious_path = Path("/tmp/evil.txt")

    with pytest.raises(Exception):
        manager._ensure_safe_path(malicious_path)


# =============================================================================
# TESTS : OPÉRATIONS CRUD (SAVE, READ, DELETE)
# =============================================================================

def test_save_read_delete_workflow(tmp_path):
    """
    Teste le workflow complet : sauvegarde, lecture, suppression.

    Vérifie que :
    - Le fichier est correctement sauvegardé
    - Le contenu lu correspond à l'original
    - La taille est correcte
    - Le nom de fichier est extrait correctement
    - La suppression fonctionne
    """
    manager = StorageManager(upload_dir=str(tmp_path))
    video_id = "vid123"
    extension = ".webm"
    content = b"hello world video content"

    async def workflow():
        # Sauvegarder
        path = await manager.save_video(video_id, extension, content)
        assert path.exists(), "Le fichier doit exister après sauvegarde"

        # Lire
        data = await manager.read_video(str(path))
        assert data == content, "Le contenu lu doit correspondre"

        # Vérifier la taille
        size = manager.get_file_size(str(path))
        assert size == len(content), "La taille doit correspondre"

        # Extraire le nom
        filename = manager.get_filename(str(path))
        assert filename == f"{video_id}{extension}"

        # Supprimer
        deleted = await manager.delete_video(str(path))
        assert deleted is True, "La suppression doit retourner True"
        assert not path.exists(), "Le fichier ne doit plus exister"

    _run_async(workflow())


# =============================================================================
# TESTS : GESTION DES ERREURS - LECTURE
# =============================================================================

def test_read_video_not_found(tmp_path):
    """
    Vérifie qu'une HTTPException 404 est levée si le fichier n'existe pas.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    async def test_case():
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await manager.read_video(str(tmp_path / "nonexistent.mp4"))

        assert exc_info.value.status_code == 404
        assert "non trouvé" in exc_info.value.detail

    _run_async(test_case())


def test_read_video_io_error(tmp_path):
    """
    Vérifie qu'une HTTPException 500 est levée en cas d'erreur I/O à la lecture.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    # Créer un fichier pour qu'il existe
    test_file = tmp_path / "test_read_err.mp4"
    test_file.write_bytes(b"dummy content")

    async def test_case():
        from fastapi import HTTPException

        with patch("src.videos.storage_manager.aiofiles.open") as mock_open:
            mock_open.side_effect = IOError("Erreur de lecture disque")

            with pytest.raises(HTTPException) as exc_info:
                await manager.read_video(str(test_file))

            assert exc_info.value.status_code == 500
            assert "lecture" in exc_info.value.detail.lower()

    _run_async(test_case())


# =============================================================================
# TESTS : GESTION DES ERREURS - SAUVEGARDE
# =============================================================================

def test_save_video_io_error(tmp_path):
    """
    Vérifie qu'une HTTPException 500 est levée en cas d'erreur I/O à l'écriture.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    async def test_case():
        from fastapi import HTTPException

        with patch("src.videos.storage_manager.aiofiles.open") as mock_open:
            mock_open.side_effect = IOError("Disque plein")

            with pytest.raises(HTTPException) as exc_info:
                await manager.save_video("vid_err", ".mp4", b"data")

            assert exc_info.value.status_code == 500
            assert "sauvegarde" in exc_info.value.detail.lower()

    _run_async(test_case())


# =============================================================================
# TESTS : GESTION DES ERREURS - SUPPRESSION
# =============================================================================

def test_delete_video_nonexistent(tmp_path):
    """
    Vérifie que la suppression d'un fichier inexistant retourne False.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    async def test_case():
        result = await manager.delete_video(str(tmp_path / "nonexistent.mp4"))
        assert result is False

    _run_async(test_case())


def test_delete_video_permission_error(tmp_path):
    """
    Vérifie qu'une HTTPException 500 est levée en cas d'erreur de permissions.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    # Créer un fichier
    test_file = tmp_path / "test_del_err.mp4"
    test_file.write_bytes(b"dummy content")

    async def test_case():
        from fastapi import HTTPException

        with patch.object(Path, "unlink") as mock_unlink:
            mock_unlink.side_effect = PermissionError("Accès refusé")

            with pytest.raises(HTTPException) as exc_info:
                await manager.delete_video(str(test_file))

            assert exc_info.value.status_code == 500
            assert "suppression" in exc_info.value.detail.lower()

    _run_async(test_case())


# =============================================================================
# TESTS : UTILITAIRES
# =============================================================================

def test_get_file_size_nonexistent(tmp_path):
    """
    Vérifie que la taille d'un fichier inexistant est 0.
    """
    manager = StorageManager(upload_dir=str(tmp_path))

    size = manager.get_file_size(str(tmp_path / "does_not_exist.mp4"))
    assert size == 0
