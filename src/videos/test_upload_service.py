"""
Tests pour le service Upload Vidéo
Exécutez avec: pytest test_upload_service.py -v
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import sys

# Ajouter le chemin src
sys.path.insert(0, str(Path(__file__).parent / "src"))

from videos.upload_service import app, UPLOAD_DIR
from videos.database import Base, engine

# Créer les tables de test
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Crée les tables de test"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup après les tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


class TestHealthCheck:
    """Tests de vérification de santé"""
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestVideoUpload:
    """Tests pour l'upload de vidéo"""
    
    def test_upload_video_success(self, client):
        """Test d'upload réussi"""
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video content")
            tmp.seek(0)
            
            response = client.post(
                "/upload",
                data={
                    "sender_id": "test-sender-123",
                    "receiver_id": "ADMIN",
                    "encrypted_key": "test-encrypted-key-base64",
                    "amount": "100.50"
                },
                files={"file": ("test.mp4", tmp, "video/mp4")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "video_id" in data
            assert data["status"] == "UPLOADED"
            assert data["message"] == "Upload réussi"
    
    def test_upload_invalid_format(self, client):
        """Test avec format non autorisé"""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            tmp.write(b"invalid content")
            tmp.seek(0)
            
            response = client.post(
                "/upload",
                data={
                    "sender_id": "test-sender",
                    "receiver_id": "ADMIN",
                    "encrypted_key": "test-key",
                    "amount": "50.00"
                },
                files={"file": ("test.txt", tmp, "text/plain")}
            )
            
            assert response.status_code == 400
            assert "non autorisé" in response.json()["detail"]
    
    def test_upload_missing_field(self, client):
        """Test avec champ manquant"""
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video")
            tmp.seek(0)
            
            response = client.post(
                "/upload",
                data={
                    "sender_id": "test-sender",
                    # receiver_id manquant
                    "encrypted_key": "test-key",
                    "amount": "50.00"
                },
                files={"file": ("test.mp4", tmp, "video/mp4")}
            )
            
            # FastAPI retourne 422 pour les paramètres manquants
            assert response.status_code == 422


class TestVideoList:
    """Tests pour la liste des vidéos"""
    
    def test_list_videos_empty(self, client):
        """Test de la liste vide"""
        response = client.get("/videos")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
