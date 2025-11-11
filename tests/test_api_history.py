"""
Tests for assessment history API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.api.app import create_app
from src.storage.repo import AssessmentRepo


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    repo = AsyncMock(spec=AssessmentRepo)
    
    # Mock history data
    mock_history = [
        {
            "id": 3,
            "user_id": "test_user",
            "ts": "2025-01-01T12:00:00",
            "scale": "phq9",
            "score": 15.0,
            "severity": "moderate",
            "rigid": 0.6,
            "route": "medium",
            "flags": {},
            "preview_text": "I understand this is important..."
        },
        {
            "id": 2,
            "user_id": "test_user",
            "ts": "2025-01-01T11:00:00",
            "scale": "gad7",
            "score": 8.0,
            "severity": "mild",
            "rigid": 0.35,
            "route": "low",
            "flags": {},
            "preview_text": "I'm here to help..."
        },
        {
            "id": 1,
            "user_id": "test_user",
            "ts": "2025-01-01T10:00:00",
            "scale": "gad7",
            "score": 5.0,
            "severity": "minimal",
            "rigid": 0.15,
            "route": "low",
            "flags": {},
            "preview_text": None
        }
    ]
    
    repo.history = AsyncMock(return_value=mock_history)
    return repo


@pytest.fixture
def client(mock_repo):
    """Create test client with mocked repository."""
    # Patch AssessmentRepo to return mock
    with patch('src.api.routes.assessment.AssessmentRepo', return_value=mock_repo):
        with patch('src.api.routes.assessment.get_repo', return_value=mock_repo):
            app = create_app()
            client = TestClient(app)
            yield client


class TestAPIHistory:
    """Test assessment history API endpoint."""
    
    def test_get_history_success(self, client, mock_repo):
        """Test successful history retrieval."""
        response = client.get("/api/v1/assess/history?user_id=test_user&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test_user"
        assert data["count"] == 3
        assert len(data["history"]) == 3
        
        # Verify history structure
        history = data["history"]
        assert history[0]["id"] == 3  # Most recent first
        assert history[0]["scale"] == "phq9"
        assert history[0]["score"] == 15.0
        assert history[0]["route"] == "medium"
        
        # Verify mock was called correctly
        mock_repo.history.assert_called_once_with("test_user", limit=50)
    
    def test_get_history_with_limit(self, client, mock_repo):
        """Test history retrieval with custom limit."""
        response = client.get("/api/v1/assess/history?user_id=test_user&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 3  # Mock returns 3, but we requested 2
        # Note: The mock returns 3, but in real implementation, limit would be respected
        
        mock_repo.history.assert_called_once_with("test_user", limit=2)
    
    def test_get_history_empty_user(self, client, mock_repo):
        """Test history for user with no assessments."""
        mock_repo.history = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/assess/history?user_id=empty_user&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "empty_user"
        assert data["count"] == 0
        assert data["history"] == []
    
    def test_get_history_missing_user_id(self, client):
        """Test history endpoint without user_id (should fail)."""
        response = client.get("/api/v1/assess/history?limit=50")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_history_invalid_limit(self, client):
        """Test history endpoint with invalid limit."""
        # Limit too high (max 100)
        response = client.get("/api/v1/assess/history?user_id=test_user&limit=200")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_history_limit_zero(self, client):
        """Test history endpoint with limit=0 (should fail)."""
        response = client.get("/api/v1/assess/history?user_id=test_user&limit=0")
        
        assert response.status_code == 422  # Validation error (ge=1)
    
    def test_get_history_default_limit(self, client, mock_repo):
        """Test history endpoint with default limit."""
        response = client.get("/api/v1/assess/history?user_id=test_user")
        
        assert response.status_code == 200
        # Should use default limit of 50
        mock_repo.history.assert_called_once_with("test_user", limit=50)
    
    def test_get_history_with_suicidal_ideation_flag(self, client, mock_repo):
        """Test history includes suicidal ideation flags."""
        # Mock history with suicidal ideation
        mock_history_with_flag = [
            {
                "id": 1,
                "user_id": "test_user",
                "ts": "2025-01-01T12:00:00",
                "scale": "phq9",
                "score": 10.0,
                "severity": "mild",
                "rigid": 1.0,
                "route": "high",
                "flags": {"suicidal_ideation": True, "suicidal_ideation_score": 2},
                "preview_text": "Safety script..."
            }
        ]
        mock_repo.history = AsyncMock(return_value=mock_history_with_flag)
        
        response = client.get("/api/v1/assess/history?user_id=test_user&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["history"]) == 1
        assert data["history"][0]["flags"]["suicidal_ideation"] is True
        assert data["history"][0]["route"] == "high"


