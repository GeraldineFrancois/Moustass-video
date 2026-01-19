def test_password_strength():
    from src.auth import security

    assert security.validate_password_strength("Aa1!aaaa") is True
    assert security.validate_password_strength("short") is False


def test_storage_allows_webm():
    # import the module directly to avoid importing the package root which
    # can trigger DB initialization in `src/videos/__init__.py`.
    from src.videos.storage_manager import StorageManager

    assert ".webm" in StorageManager.ALLOWED_EXTENSIONS


def test_ui_upload_contains_video_accept():
    p = "src/ui/upload.html"
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "video/webm" in content or ".webm" in content


def test_init_sql_files_exist():
    import os

    assert os.path.exists("src/auth/init_database.sql")
    assert os.path.exists("src/videos/init_database.sql")
