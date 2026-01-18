import asyncio
import os
from pathlib import Path
import pytest


from src.videos.storage_manager import StorageManager


def test_validate_filename_allowed(tmp_path):
    sm = StorageManager(upload_dir=str(tmp_path))
    assert sm.validate_filename("video.webm") == ".webm"
    with pytest.raises(Exception):
        sm.validate_filename("")
    with pytest.raises(Exception):
        sm.validate_filename("file.txt")


def test_ensure_safe_path_traversal(tmp_path):
    sm = StorageManager(upload_dir=str(tmp_path))
    # Attempt to escape upload_dir
    outside = Path("/tmp/evil.txt")
    with pytest.raises(Exception):
        sm._ensure_safe_path(outside)


def test_save_read_delete_and_size(tmp_path):
    sm = StorageManager(upload_dir=str(tmp_path))
    video_id = "vid123"
    ext = ".webm"
    content = b"hello world"

    async def _flow():
        path = await sm.save_video(video_id, ext, content)
        assert path.exists()
        data = await sm.read_video(str(path))
        assert data == content
        size = sm.get_file_size(str(path))
        assert size == len(content)
        name = sm.get_filename(str(path))
        assert name == f"{video_id}{ext}"
        deleted = await sm.delete_video(str(path))
        assert deleted is True

    asyncio.run(_flow())
