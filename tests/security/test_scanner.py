"""Tests for Security Service - Path Validation."""
import pytest
from pathlib import Path
from src.security.scanner import validate_path, validate_scan_arguments


class TestPathValidation:
    """Test path validation security."""
    
    @pytest.mark.security
    def test_validate_path_safe_absolute(self, tmp_path):
        """Test validation of safe absolute path."""
        safe_path = tmp_path / "test.py"
        safe_path.write_text("print('hello')")
        
        result = validate_path(str(safe_path), base_dir=str(tmp_path))
        
        assert result is True
    
    @pytest.mark.security
    def test_validate_path_directory_traversal(self, tmp_path):
        """Test prevention of directory traversal attacks."""
        malicious_path = tmp_path / ".." / ".." / "etc" / "passwd"
        
        result = validate_path(str(malicious_path), base_dir=str(tmp_path))
        
        assert result is False
    
    @pytest.mark.security
    def test_validate_path_nonexistent(self, tmp_path):
        """Test validation of non-existent path."""
        nonexistent = tmp_path / "does_not_exist.py"
        
        result = validate_path(str(nonexistent), base_dir=str(tmp_path))
        
        assert result is False


class TestArgumentValidation:
    """Test command argument validation."""
    
    @pytest.mark.security
    @pytest.mark.parametrize("arg", [
        "src/auth",
        "src/videos/upload.py",
        "tests/test_security.py"
    ])
    def test_validate_safe_arguments(self, arg):
        """Test validation of safe arguments."""
        assert validate_scan_arguments([arg]) is True
    
    @pytest.mark.security
    @pytest.mark.parametrize("arg", [
        "; rm -rf /",
        "| cat /etc/passwd",
        "&& malicious_command",
        "`whoami`",
        "$(ls -la)"
    ])
    def test_validate_malicious_arguments(self, arg):
        """Test prevention of command injection."""
        assert validate_scan_arguments([arg]) is False
    
    @pytest.mark.security
    def test_validate_empty_arguments(self):
        """Test validation with empty arguments."""
        assert validate_scan_arguments([]) is True
    
    @pytest.mark.security
    def test_validate_multiple_safe_arguments(self):
        """Test validation with multiple safe arguments."""
        args = ["src/auth", "src/videos", "--format=json"]
        assert validate_scan_arguments(args) is True
