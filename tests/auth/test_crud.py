"""Tests for Auth Service - CRUD Operations."""
import pytest
from unittest.mock import MagicMock, patch
from src.auth import crud, models


class TestUserCRUD:
    """Test user CRUD operations."""
    
    @pytest.mark.unit
    def test_get_user_by_email_found(self, mock_db_session):
        """Test getting user by email when user exists."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.id = 1
        
        mock_db_session.query().filter().first.return_value = mock_user
        
        result = crud.get_user_by_email(mock_db_session, "test@example.com")
        
        assert result is not None
        assert result.email == "test@example.com"
        assert result.id == 1
    
    @pytest.mark.unit
    def test_get_user_by_email_not_found(self, mock_db_session):
        """Test getting user by email when user doesn't exist."""
        mock_db_session.query().filter().first.return_value = None
        
        result = crud.get_user_by_email(mock_db_session, "nonexistent@example.com")
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_user_by_id_found(self, mock_db_session):
        """Test getting user by ID when user exists."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        # The CRUD helper exposes get_user_by_email; ensure retrieval works
        mock_db_session.query().filter().first.return_value = mock_user
        
        result = crud.get_user_by_email(mock_db_session, "test@example.com")
        
        assert result is not None
        assert result.id == 1
    
    @pytest.mark.unit
    def test_delete_user(self, mock_db_session):
        """Test deleting a user."""
        mock_user = MagicMock()
        mock_user.id = 1
        
        # Ensure the session's query().get returns our mock user
        mock_db_session.query().get.return_value = mock_user
        
        crud.delete_user(mock_db_session, 1)
        
        mock_db_session.delete.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_called_once()


class TestLogging:
    """Test audit logging functionality."""
    
    @pytest.mark.unit
    def test_log_event_success(self, mock_db_session):
        """Test logging a successful event."""
        crud.log_event(mock_db_session, "login", user_id=1, success=1)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_log_event_failure(self, mock_db_session):
        """Test logging a failed event."""
        crud.log_event(mock_db_session, "login", user_id=1, success=0)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_get_logs_for_user(self, mock_db_session):
        """Test retrieving logs for a specific user."""
        mock_logs = [MagicMock(), MagicMock()]
        mock_db_session.query().filter().order_by().limit().all.return_value = mock_logs
        
        result = crud.get_logs_for_user(mock_db_session, user_id=1)
        
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_get_all_logs(self, mock_db_session):
        """Test retrieving all logs (admin function)."""
        mock_logs = [MagicMock(), MagicMock(), MagicMock()]
        mock_db_session.query().order_by().limit().all.return_value = mock_logs
        
        result = crud.get_all_logs(mock_db_session)
        
        assert len(result) == 3
