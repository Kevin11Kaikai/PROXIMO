"""
Tests for AssessmentRepo - persistence and history.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from src.storage.repo import AssessmentRepo


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_assessments.db")
        repo = AssessmentRepo(db_path=db_path)
        yield repo


class TestAssessmentRepo:
    """Test AssessmentRepo functionality."""
    
    @pytest.mark.asyncio
    async def test_save_assessment(self, temp_repo):
        """Test saving an assessment."""
        user_id = "test_user_1"
        assessment = {
            "success": True,
            "scale": "phq9",
            "total_score": 12.0,
            "severity_level": "moderate",
            "flags": {"suicidal_ideation": False}
        }
        decision = {
            "route": "medium",
            "rigid_score": 0.6,
            "reason": "medium_risk"
        }
        result = {
            "policy": "medium",
            "response": "I understand this is important.",
            "temperature": 0.6
        }
        
        await temp_repo.save(user_id, assessment, decision, result)
        
        # Verify by checking history
        history = await temp_repo.history(user_id, limit=1)
        assert len(history) == 1
        assert history[0]["user_id"] == user_id
        assert history[0]["scale"] == "phq9"
        assert history[0]["score"] == 12.0
        assert history[0]["severity"] == "moderate"
        assert history[0]["route"] == "medium"
        assert history[0]["rigid"] == 0.6
    
    @pytest.mark.asyncio
    async def test_save_with_suicidal_ideation(self, temp_repo):
        """Test saving assessment with suicidal ideation flag."""
        user_id = "test_user_2"
        assessment = {
            "success": True,
            "scale": "phq9",
            "total_score": 10.0,
            "severity_level": "mild",
            "flags": {"suicidal_ideation": True, "suicidal_ideation_score": 2}
        }
        decision = {
            "route": "high",
            "rigid_score": 1.0,
            "reason": "hard_lock"
        }
        result = {
            "policy": "high",
            "response": "Safety script",
            "safety_banner": "If you are in immediate danger, call or text 988"
        }
        
        await temp_repo.save(user_id, assessment, decision, result)
        
        history = await temp_repo.history(user_id, limit=1)
        assert len(history) == 1
        assert history[0]["flags"]["suicidal_ideation"] is True
        assert history[0]["route"] == "high"
    
    @pytest.mark.asyncio
    async def test_history_multiple_records(self, temp_repo):
        """Test retrieving multiple history records."""
        user_id = "test_user_3"
        
        # Save multiple assessments
        for i in range(5):
            assessment = {
                "success": True,
                "scale": "gad7",
                "total_score": float(i * 2),
                "severity_level": "minimal" if i < 2 else "moderate",
                "flags": {}
            }
            decision = {
                "route": "low" if i < 2 else "medium",
                "rigid_score": 0.2 if i < 2 else 0.6,
                "reason": "low_risk" if i < 2 else "medium_risk"
            }
            result = {"policy": "low" if i < 2 else "medium", "response": f"Response {i}"}
            
            await temp_repo.save(user_id, assessment, decision, result)
        
        # Retrieve history
        history = await temp_repo.history(user_id, limit=10)
        assert len(history) == 5
        
        # Should be sorted by timestamp (most recent first)
        # Since we saved sequentially, last saved should be first
        assert history[0]["score"] == 8.0  # Last saved
        assert history[4]["score"] == 0.0  # First saved
    
    @pytest.mark.asyncio
    async def test_history_limit(self, temp_repo):
        """Test history limit parameter."""
        user_id = "test_user_4"
        
        # Save 10 assessments
        for i in range(10):
            assessment = {
                "success": True,
                "scale": "phq9",
                "total_score": float(i),
                "severity_level": "minimal",
                "flags": {}
            }
            decision = {"route": "low", "rigid_score": 0.2, "reason": "low_risk"}
            result = {"policy": "low", "response": f"Response {i}"}
            
            await temp_repo.save(user_id, assessment, decision, result)
        
        # Request only 5
        history = await temp_repo.history(user_id, limit=5)
        assert len(history) == 5
    
    @pytest.mark.asyncio
    async def test_has_prior_assessment(self, temp_repo):
        """Test checking if user has prior assessments."""
        user_id = "test_user_5"
        
        # Initially no assessments
        assert await temp_repo.has_prior_assessment(user_id) is False
        
        # Save one assessment
        assessment = {
            "success": True,
            "scale": "gad7",
            "total_score": 5.0,
            "severity_level": "minimal",
            "flags": {}
        }
        decision = {"route": "low", "rigid_score": 0.2, "reason": "low_risk"}
        result = {"policy": "low", "response": "Hello"}
        
        await temp_repo.save(user_id, assessment, decision, result)
        
        # Now should have prior assessment
        assert await temp_repo.has_prior_assessment(user_id) is True
    
    @pytest.mark.asyncio
    async def test_history_empty_user(self, temp_repo):
        """Test history for user with no assessments."""
        user_id = "test_user_6"
        
        history = await temp_repo.history(user_id, limit=10)
        assert len(history) == 0
        assert history == []
    
    @pytest.mark.asyncio
    async def test_save_without_result(self, temp_repo):
        """Test saving assessment without policy result."""
        user_id = "test_user_7"
        assessment = {
            "success": True,
            "scale": "pss10",
            "total_score": 15.0,
            "severity_level": "moderate",
            "flags": {}
        }
        decision = {
            "route": "medium",
            "rigid_score": 0.6,
            "reason": "medium_risk"
        }
        
        # Save without result
        await temp_repo.save(user_id, assessment, decision, None)
        
        history = await temp_repo.history(user_id, limit=1)
        assert len(history) == 1
        assert history[0]["preview_text"] is None

