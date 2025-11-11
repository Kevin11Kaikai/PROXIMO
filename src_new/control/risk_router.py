"""Risk routing utilities bridging perception outputs to conversation policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, Literal

from src_new.perception.questionnaire_mapper import QuestionnaireMapper, Route
from src_new.perception.psyguard_service import (
    MEDIUM_RISK_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD
)


@dataclass
class RiskRoutingResult:
    """Result of risk routing decision."""
    route: Route
    rigid_score: float
    reason: str
    metadata: Dict[str, Any]


class RiskRouter:
    """Risk router for mapping perception outputs to conversation routes.
    
    This router integrates:
    - Questionnaire assessment results (PHQ-9, GAD-7)
    - PsyGUARD real-time risk scores
    - Chat content priority rules
    
    Rules:
    - Chat content risk has priority over questionnaire scores
    - Questionnaire scores are mapped using QuestionnaireMapper
    - Final route is determined by combining both signals
    """
    
    def __init__(self):
        """Initialize risk router."""
        self.mapper = QuestionnaireMapper()
    
    def decide_from_assessment(
        self,
        assessment: Dict[str, Any],
        chat_risk_score: Optional[float] = None
    ) -> RiskRoutingResult:
        """
        Decide route from assessment result (legacy compatibility).
        
        This method wraps the legacy router for backward compatibility.
        
        Args:
            assessment: Assessment result from proximo_api.assess()
            chat_risk_score: Optional PsyGUARD risk score from chat content
            
        Returns:
            RiskRoutingResult with route decision
        """
        from src.conversation import router as legacy_router
        
        # Use legacy router for initial decision
        legacy_decision = legacy_router.decide_route(assessment)
        route = legacy_decision.get("route", "low")
        rigid_score = legacy_decision.get("rigid_score", 0.0)
        
        # If chat risk score is provided, apply priority rules
        if chat_risk_score is not None:
            route = self._apply_chat_priority(route, chat_risk_score)
        
        return RiskRoutingResult(
            route=route,
            rigid_score=rigid_score,
            reason=legacy_decision.get("reason", "unknown"),
            metadata=legacy_decision
        )
    
    def decide_from_questionnaires(
        self,
        phq9_result: Dict[str, Any],
        gad7_result: Dict[str, Any],
        chat_risk_score: Optional[float] = None
    ) -> RiskRoutingResult:
        """
        Decide route from questionnaire results.
        
        This is the new method that uses QuestionnaireMapper for routing.
        
        Args:
            phq9_result: PHQ-9 assessment result
            gad7_result: GAD-7 assessment result
            chat_risk_score: Optional PsyGUARD risk score from chat content
            
        Returns:
            RiskRoutingResult with route decision
        """
        # Extract scores
        phq9_score = phq9_result.get("total_score", 0.0)
        gad7_score = gad7_result.get("total_score", 0.0)
        
        # Get PHQ-9 Q9 score (suicidal ideation)
        phq9_q9_score = None
        parsed_scores = phq9_result.get("parsed_scores", [])
        if len(parsed_scores) >= 9:
            phq9_q9_score = parsed_scores[8]  # Q9 is index 8 (0-based)
        
        # Make final route decision (chat content has priority)
        route = self.mapper.final_route_decision(
            phq9_score=phq9_score,
            gad7_score=gad7_score,
            phq9_q9_score=phq9_q9_score,
            chat_risk_score=chat_risk_score
        )
        
        # Calculate rigid_score based on route
        rigid_score = self._route_to_rigid_score(route, phq9_score, gad7_score)
        
        # Determine reason
        reason = self._determine_reason(route, phq9_q9_score, chat_risk_score)
        
        return RiskRoutingResult(
            route=route,
            rigid_score=rigid_score,
            reason=reason,
            metadata={
                "phq9_score": phq9_score,
                "gad7_score": gad7_score,
                "phq9_q9_score": phq9_q9_score,
                "chat_risk_score": chat_risk_score,
                "route_source": "questionnaire_mapper"
            }
        )
    
    def _apply_chat_priority(self, questionnaire_route: Route, chat_risk_score: float) -> Route:
        """Apply chat content priority over questionnaire route."""
        if chat_risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
            return "high"
        elif chat_risk_score >= MEDIUM_RISK_THRESHOLD:
            # Only upgrade if questionnaire route is lower
            route_priority = {"low": 1, "medium": 2, "high": 3}
            if route_priority.get(questionnaire_route, 0) < 2:
                return "medium"
        return questionnaire_route
    
    def _route_to_rigid_score(
        self,
        route: Route,
        phq9_score: float,
        gad7_score: float
    ) -> float:
        """Convert route to rigid_score (0.0 - 1.0)."""
        if route == "high":
            return 1.0
        elif route == "medium":
            # Medium risk: 0.5 - 0.75
            max_score = max(phq9_score, gad7_score)
            if max_score >= 15:
                return 0.75
            elif max_score >= 10:
                return 0.6
            else:
                return 0.5
        else:  # low
            # Low risk: 0.0 - 0.4
            max_score = max(phq9_score, gad7_score)
            if max_score >= 5:
                return 0.3
            else:
                return 0.15
    
    def _determine_reason(
        self,
        route: Route,
        phq9_q9_score: Optional[int],
        chat_risk_score: Optional[float]
    ) -> str:
        """Determine reason for routing decision."""
        if phq9_q9_score is not None and phq9_q9_score >= 1:
            return "phq9_suicidal_ideation"
        elif chat_risk_score is not None and chat_risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
            return "chat_high_risk"
        elif chat_risk_score is not None and chat_risk_score >= MEDIUM_RISK_THRESHOLD:
            return "chat_medium_risk"
        elif route == "high":
            return "questionnaire_high"
        elif route == "medium":
            return "questionnaire_medium"
        else:
            return "questionnaire_low"


__all__ = ["RiskRouter", "RiskRoutingResult", "Route"]
