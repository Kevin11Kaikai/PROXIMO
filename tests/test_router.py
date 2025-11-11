"""
Tests for conversation router module.
"""

import pytest
from src.conversation.router import decide_route, Route


def make_assessment(sev: str, flags: dict = None, **kwargs):
    """Create a test assessment dictionary."""
    assessment = {
        "success": True,
        "severity_level": sev,
        "flags": flags or {},
        **kwargs,
    }
    return assessment


class TestRouteDecision:
    """Test route decision logic."""
    
    def test_route_low_minimal(self):
        """Test low route for minimal severity."""
        assessment = make_assessment("minimal")
        result = decide_route(assessment)
        assert result["route"] == Route.LOW
        assert result["rigid_score"] < 0.40
        assert result["reason"] == "low_risk"
    
    def test_route_low_mild(self):
        """Test low route for mild severity."""
        assessment = make_assessment("mild")
        result = decide_route(assessment)
        assert result["route"] == Route.LOW
        assert result["rigid_score"] < 0.40
        assert result["reason"] == "low_risk"
    
    def test_route_medium_moderate(self):
        """Test medium route for moderate severity."""
        assessment = make_assessment("moderate")
        result = decide_route(assessment)
        assert result["route"] == Route.MEDIUM
        assert 0.40 <= result["rigid_score"] < 0.75
        assert result["reason"] == "medium_risk"
    
    def test_route_high_severe(self):
        """Test high route for severe severity (triggers hard lock)."""
        # Severe severity triggers hard lock, which maps to HIGH route
        assessment = make_assessment("severe", flags={})
        result = decide_route(assessment)
        assert result["route"] == Route.HIGH
        assert result["rigid_score"] == 1.0
        assert result["reason"] == "hard_lock"
    
    def test_route_high_hard_lock_suicidal_ideation(self):
        """Test high route triggered by suicidal ideation (hard lock)."""
        assessment = make_assessment("mild", flags={"suicidal_ideation": True})
        result = decide_route(assessment)
        assert result["route"] == Route.HIGH
        assert result["rigid_score"] == 1.0
        assert result["reason"] == "hard_lock"
    
    def test_route_high_hard_lock_severe_severity(self):
        """Test high route triggered by severe severity (hard lock)."""
        assessment = make_assessment("severe", flags={})
        result = decide_route(assessment)
        assert result["route"] == Route.HIGH
        assert result["rigid_score"] == 1.0
        assert result["reason"] == "hard_lock"
    
    def test_route_high_hard_lock_item9_score(self):
        """Test high route triggered by suicidal ideation score >= 2 (hard lock)."""
        assessment = make_assessment("mild", flags={"suicidal_ideation_score": 2})
        result = decide_route(assessment)
        assert result["route"] == Route.HIGH
        assert result["rigid_score"] == 1.0
        assert result["reason"] == "hard_lock"
    
    def test_route_output_structure(self):
        """Test that route decision has correct structure."""
        assessment = make_assessment("moderate")
        result = decide_route(assessment)
        
        assert "route" in result
        assert "rigid_score" in result
        assert "reason" in result
        assert result["route"] in [Route.LOW, Route.MEDIUM, Route.HIGH]
        assert 0.0 <= result["rigid_score"] <= 1.0
        assert isinstance(result["reason"], str)
    
    def test_route_compatibility_severity_field(self):
        """Test compatibility with 'severity' field name."""
        assessment = {
            "success": True,
            "severity": "moderate",  # Using 'severity' instead of 'severity_level'
            "flags": {},
        }
        result = decide_route(assessment)
        assert result["route"] == Route.MEDIUM


class TestRouterWithActualAssessOutput:
    """Test router with actual assess() output format."""
    
    def test_router_with_phq9_result(self):
        """Test router with PHQ-9 assessment result."""
        # Simulate actual assess() output
        assessment = {
            "success": True,
            "scale": "phq9",
            "total_score": 15.0,
            "severity_level": "moderate",
            "parsed_scores": [1, 2, 2, 2, 1, 2, 2, 2, 1],
            "raw_responses": ["1", "2", "2", "2", "1", "2", "2", "2", "1"],
            "flags": {
                "suicidal_ideation": False,
                "suicidal_ideation_score": 1,
                "severe_symptoms": False,
            },
            "suicidal_risk": "low",
            "risk_level": "moderate",
            "clinical_interpretation": {
                "recommendations": ["Consider professional evaluation"],
                "risk_factors": [],
            },
        }
        
        result = decide_route(assessment)
        assert result["route"] == Route.MEDIUM
        assert "rigid_score" in result
        assert "reason" in result
    
    def test_router_with_hard_lock_scenario(self):
        """Test router with hard lock scenario (suicidal ideation maps to HIGH)."""
        assessment = {
            "success": True,
            "scale": "phq9",
            "total_score": 12.0,
            "severity_level": "mild",
            "flags": {
                "suicidal_ideation": True,
                "suicidal_ideation_score": 2,
                "severe_symptoms": False,
            },
            "suicidal_risk": "high",
            "risk_level": "critical",
        }
        
        result = decide_route(assessment)
        assert result["route"] == Route.HIGH
        assert result["rigid_score"] == 1.0
        assert result["reason"] == "hard_lock"
    
    def test_router_with_severe_severity(self):
        """Test router with severe severity (triggers hard lock, maps to HIGH)."""
        assessment = {
            "success": True,
            "scale": "phq9",
            "total_score": 24.0,
            "severity_level": "severe",
            "flags": {
                "suicidal_ideation": False,
                "suicidal_ideation_score": 0,
                "severe_symptoms": True,
            },
            "suicidal_risk": "low",
            "risk_level": "high",
        }
        
        result = decide_route(assessment)
        assert result["route"] == Route.HIGH
        assert result["rigid_score"] == 1.0
        assert result["reason"] == "hard_lock"


class TestRouteThresholds:
    """Test routing thresholds."""
    
    def test_threshold_boundaries(self):
        """Test route boundaries."""
        # Test just below low threshold
        assessment = make_assessment("mild")  # rigid_score ~0.35
        result = decide_route(assessment)
        assert result["route"] == Route.LOW
        
        # Test just above low threshold
        # moderate severity gives ~0.60, which is between 0.40 and 0.75
        assessment = make_assessment("moderate")
        result = decide_route(assessment)
        assert result["route"] == Route.MEDIUM
        
        # Test high route (would need severity that gives > 0.75)
        # But severe triggers hard lock, which maps to HIGH route
        # This is expected behavior - severe should trigger hard lock → HIGH route

