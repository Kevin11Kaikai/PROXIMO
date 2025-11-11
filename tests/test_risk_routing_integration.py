"""
Integration tests for risk mapping and conversation routing with assess() output.
"""

import pytest
import asyncio
from src.assessment.proximo_api import assess
from src.conversation.router import decide_route, Route


class TestRiskRoutingIntegration:
    """Integration tests for assess() → route decision flow."""
    
    @pytest.mark.asyncio
    async def test_low_risk_flow(self):
        """Test complete flow for low risk assessment."""
        # Low risk: minimal severity
        assessment = await assess("phq9", ["0", "0", "1", "0", "1", "0", "1", "0", "0"])
        
        assert assessment["success"] is True
        assert assessment["severity_level"] == "minimal"
        
        # Decide route
        route_decision = decide_route(assessment)
        assert route_decision["route"] == Route.LOW
        assert route_decision["rigid_score"] < 0.40
        assert route_decision["reason"] == "low_risk"
    
    @pytest.mark.asyncio
    async def test_medium_risk_flow(self):
        """Test complete flow for medium risk assessment."""
        # Medium risk: moderate severity
        assessment = await assess("phq9", ["1", "1", "2", "2", "1", "2", "1", "2", "0"])
        
        assert assessment["success"] is True
        assert assessment["severity_level"] == "moderate"
        
        # Decide route
        route_decision = decide_route(assessment)
        assert route_decision["route"] == Route.MEDIUM
        assert 0.40 <= route_decision["rigid_score"] < 0.75
        assert route_decision["reason"] == "medium_risk"
    
    @pytest.mark.asyncio
    async def test_high_risk_hard_lock_suicidal_ideation(self):
        """Test complete flow for high risk scenario (hard lock - suicidal ideation)."""
        # Hard lock: mild severity but suicidal ideation → maps to HIGH route
        assessment = await assess("phq9", ["1", "1", "1", "1", "1", "1", "1", "1", "2"])
        
        assert assessment["success"] is True
        assert assessment["flags"]["suicidal_ideation"] is True
        assert assessment["suicidal_risk"] == "high"
        
        # Decide route
        route_decision = decide_route(assessment)
        assert route_decision["route"] == Route.HIGH
        assert route_decision["rigid_score"] == 1.0
        assert route_decision["reason"] == "hard_lock"
    
    @pytest.mark.asyncio
    async def test_high_risk_hard_lock_severe_severity(self):
        """Test complete flow for high risk scenario (hard lock - severe severity)."""
        # Hard lock: severe severity → maps to HIGH route
        assessment = await assess("phq9", ["3", "3", "3", "3", "3", "3", "3", "3", "0"])
        
        assert assessment["success"] is True
        assert assessment["severity_level"] == "severe"
        
        # Decide route
        route_decision = decide_route(assessment)
        assert route_decision["route"] == Route.HIGH
        assert route_decision["rigid_score"] == 1.0
        assert route_decision["reason"] == "hard_lock"
    
    @pytest.mark.asyncio
    async def test_gad7_routing(self):
        """Test routing with GAD-7 assessment."""
        assessment = await assess("gad7", ["1", "1", "2", "1", "2", "1", "1"])
        
        assert assessment["success"] is True
        
        route_decision = decide_route(assessment)
        assert route_decision["route"] in [Route.LOW, Route.MEDIUM, Route.HIGH]
        assert "rigid_score" in route_decision
        assert "reason" in route_decision
    
    @pytest.mark.asyncio
    async def test_pss10_routing(self):
        """Test routing with PSS-10 assessment."""
        assessment = await assess("pss10", ["2", "3", "1", "0", "2", "1", "3", "2", "1", "2"])
        
        assert assessment["success"] is True
        
        route_decision = decide_route(assessment)
        assert route_decision["route"] in [Route.LOW, Route.MEDIUM, Route.HIGH]
        assert "rigid_score" in route_decision
        assert "reason" in route_decision

