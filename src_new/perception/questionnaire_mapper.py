"""Questionnaire score mapping to risk routes."""

from __future__ import annotations

from typing import Dict, Any, Optional, Literal


Route = Literal["low", "medium", "high"]


class QuestionnaireMapper:
    """Maps questionnaire scores to risk routes.
    
    Rules:
    - PHQ-9: 0-9 → Low, 10-14 → Medium, 15+ → High
    - PHQ-9 Q9 (suicidal ideation) >= 1 → Direct High
    - GAD-7: 0-9 → Low, 10-14 → Medium, 15+ → High
    - Combined: Take higher level
    - Chat content priority: If chat risk is high, override questionnaire
    """
    
    @staticmethod
    def map_phq9(phq9_score: float, phq9_q9_score: Optional[int] = None) -> Route:
        """
        Map PHQ-9 score to route.
        
        Args:
            phq9_score: Total PHQ-9 score
            phq9_q9_score: Score for question 9 (suicidal ideation)
            
        Returns:
            Route: "low", "medium", or "high"
        """
        # Special rule: Q9 (suicidal ideation) >= 1 → High
        if phq9_q9_score is not None and phq9_q9_score >= 1:
            return "high"
        
        # Standard mapping
        if phq9_score <= 9:
            return "low"
        elif phq9_score <= 14:
            return "medium"
        else:
            return "high"
    
    @staticmethod
    def map_gad7(gad7_score: float) -> Route:
        """
        Map GAD-7 score to route.
        
        Args:
            gad7_score: Total GAD-7 score
            
        Returns:
            Route: "low", "medium", or "high"
        """
        if gad7_score <= 9:
            return "low"
        elif gad7_score <= 14:
            return "medium"
        else:
            return "high"
    
    @staticmethod
    def combine_routes(phq9_route: Route, gad7_route: Route) -> Route:
        """
        Combine PHQ-9 and GAD-7 routes (take higher level).
        
        Args:
            phq9_route: Route from PHQ-9
            gad7_route: Route from GAD-7
            
        Returns:
            Combined route (higher level)
        """
        route_priority = {"low": 1, "medium": 2, "high": 3}
        return max(phq9_route, gad7_route, key=lambda x: route_priority[x])
    
    @staticmethod
    def final_route_decision(
        phq9_score: float,
        gad7_score: float,
        phq9_q9_score: Optional[int],
        chat_risk_score: Optional[float] = None
    ) -> Route:
        """
        Make final route decision considering both questionnaire and chat content.
        
        Priority: Chat content risk > Questionnaire score
        
        Args:
            phq9_score: Total PHQ-9 score
            gad7_score: Total GAD-7 score
            phq9_q9_score: PHQ-9 question 9 score (suicidal ideation)
            chat_risk_score: PsyGUARD risk score from chat content (optional)
            
        Returns:
            Final route decision
        """
        from src_new.perception.psyguard_service import (
            MEDIUM_RISK_THRESHOLD,
            HIGH_RISK_DIRECT_THRESHOLD
        )
        
        # Chat content priority (if provided)
        if chat_risk_score is not None:
            if chat_risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
                return "high"
            elif chat_risk_score >= MEDIUM_RISK_THRESHOLD:
                return "medium"
        
        # Map questionnaires
        phq9_route = QuestionnaireMapper.map_phq9(phq9_score, phq9_q9_score)
        gad7_route = QuestionnaireMapper.map_gad7(gad7_score)
        
        # Combine (take higher level)
        return QuestionnaireMapper.combine_routes(phq9_route, gad7_route)
    
    @staticmethod
    def map_assessment_result(assessment: Dict[str, Any]) -> Route:
        """
        Map assessment result to route.
        
        Args:
            assessment: Assessment result from proximo_api.assess()
            
        Returns:
            Route decision
        """
        scale = assessment.get("scale", "")
        total_score = assessment.get("total_score", 0.0)
        
        # Get PHQ-9 Q9 score if available
        phq9_q9_score = None
        if scale == "phq9":
            parsed_scores = assessment.get("parsed_scores", [])
            if len(parsed_scores) >= 9:
                phq9_q9_score = parsed_scores[8]  # Q9 is index 8 (0-based)
        
        # For now, we only have one scale at a time
        # In the future, we might have both PHQ-9 and GAD-7
        if scale == "phq9":
            return QuestionnaireMapper.map_phq9(total_score, phq9_q9_score)
        elif scale == "gad7":
            return QuestionnaireMapper.map_gad7(total_score)
        else:
            # Default to low for unknown scales
            return "low"


__all__ = ["QuestionnaireMapper", "Route"]

