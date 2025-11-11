"""
Unit tests for PROXIMO Assessment API.
"""

import pytest
import asyncio
from src.assessment.proximo_api import assess, assess_sync, assess_phq9, assess_gad7, assess_pss10


class TestProximoAPI:
    """Test PROXIMO Assessment API."""
    
    @pytest.mark.asyncio
    async def test_assess_phq9_valid(self):
        """Test PHQ-9 assessment with valid responses."""
        responses = [
            "0", "not at all", "several days", "2",
            "2", "1", "1", "2", "2"  # 9 responses
        ]
        
        result = await assess("phq9", responses)
        
        assert result["success"] is True
        assert result["scale"] == "phq9"
        assert "total_score" in result
        assert "severity_level" in result
        assert "parsed_scores" in result
        assert "clinical_interpretation" in result
        assert "flags" in result
        assert len(result["parsed_scores"]) == 9
    
    @pytest.mark.asyncio
    async def test_assess_phq9_with_suicidal_ideation(self):
        """Test PHQ-9 assessment with suicidal ideation (Item 9 = 2)."""
        responses = [
            "0", "0", "1", "1",
            "1", "1", "1", "1", "2"  # Item 9 = 2 (high risk)
        ]
        
        result = await assess("phq9", responses)
        
        assert result["success"] is True
        assert result["flags"]["suicidal_ideation"] is True
        assert result["flags"]["suicidal_ideation_score"] == 2
        assert result["suicidal_risk"] == "high"
        assert result["risk_level"] == "critical"
        assert "Immediate safety assessment required" in result["clinical_interpretation"]["recommendations"][0]
    
    @pytest.mark.asyncio
    async def test_assess_gad7_valid(self):
        """Test GAD-7 assessment with valid responses."""
        responses = [
            "0", "1", "2", "1", "0", "2", "1"  # 7 responses
        ]
        
        result = await assess("gad7", responses)
        
        assert result["success"] is True
        assert result["scale"] == "gad7"
        assert len(result["parsed_scores"]) == 7
        assert result["total_score"] == 7  # 0+1+2+1+0+2+1
    
    @pytest.mark.asyncio
    async def test_assess_pss10_valid(self):
        """Test PSS-10 assessment with valid responses."""
        responses = [
            "2", "3", "1", "0", "2", "1", "3", "2", "1", "2"  # 10 responses
        ]
        
        result = await assess("pss10", responses)
        
        assert result["success"] is True
        assert result["scale"] == "pss10"
        assert len(result["parsed_scores"]) == 10
    
    def test_assess_sync_phq9(self):
        """Test synchronous assess_sync function."""
        responses = [
            "0", "not at all", "several days", "2",
            "2", "1", "1", "2", "2"
        ]
        
        result = assess_sync("phq9", responses)
        
        assert result["success"] is True
        assert result["scale"] == "phq9"
    
    @pytest.mark.asyncio
    async def test_assess_invalid_scale(self):
        """Test assessment with invalid scale name."""
        responses = ["0", "1", "2"]
        
        result = await assess("invalid_scale", responses)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_assess_wrong_response_count(self):
        """Test assessment with wrong number of responses."""
        responses = ["0", "1", "2"]  # PHQ-9 needs 9 responses
        
        result = await assess("phq9", responses)
        
        assert result["success"] is False
        assert "error" in result
        assert "requires 9 responses" in result["error"]
    
    @pytest.mark.asyncio
    async def test_assess_phq9_convenience_function(self):
        """Test convenience function assess_phq9."""
        responses = [
            "0", "not at all", "several days", "2",
            "2", "1", "1", "2", "2"
        ]
        
        result = await assess_phq9(responses)
        
        assert result["success"] is True
        assert result["scale"] == "phq9"
    
    @pytest.mark.asyncio
    async def test_assess_gad7_convenience_function(self):
        """Test convenience function assess_gad7."""
        responses = ["0", "1", "2", "1", "0", "2", "1"]
        
        result = await assess_gad7(responses)
        
        assert result["success"] is True
        assert result["scale"] == "gad7"
    
    @pytest.mark.asyncio
    async def test_assess_pss10_convenience_function(self):
        """Test convenience function assess_pss10."""
        responses = ["2", "3", "1", "0", "2", "1", "3", "2", "1", "2"]
        
        result = await assess_pss10(responses)
        
        assert result["success"] is True
        assert result["scale"] == "pss10"
    
    @pytest.mark.asyncio
    async def test_assess_phq9_severe_symptoms(self):
        """Test PHQ-9 assessment with severe symptoms (total_score >= 20)."""
        responses = [
            "3", "3", "3", "3", "3", "3", "3", "3", "0"  # 24分，但 Item 9 = 0
        ]
        
        result = await assess("phq9", responses)
        
        assert result["success"] is True
        assert result["total_score"] == 24
        assert result["severity_level"] == "severe"
        assert result["flags"]["severe_symptoms"] is True
        assert result["risk_level"] == "high"  # 因为总分 >= 20，但 Item 9 = 0，所以不是 critical


