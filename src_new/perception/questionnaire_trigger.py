"""Questionnaire trigger logic for Perception Layer."""

from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass

from src_new.perception.psyguard_service import (
    SUICIDE_INTENT_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD
)


@dataclass
class QuestionnaireTriggerResult:
    """Result of questionnaire trigger check."""
    should_trigger: bool
    reason: str  # "turn_count", "suicide_intent", "high_risk_direct"
    immediate_route: Optional[str] = None  # "high" if should_direct_high_risk


class QuestionnaireTrigger:
    """Manages questionnaire triggering logic.
    
    Rules:
    - Default: Trigger after 5 conversation turns
    - Early trigger: If PsyGUARD detects suicide intent (>= 0.80)
    - Direct high risk: If PsyGUARD score >= 0.95, set route to "high" immediately
    """
    
    def __init__(self, turn_threshold: int = 5):
        """
        Initialize questionnaire trigger.
        
        Args:
            turn_threshold: Number of turns before default trigger (default: 5)
        """
        self.turn_threshold = turn_threshold
    
    def check_trigger(
        self,
        turn_count: int,
        psyguard_result: Optional[Dict[str, Any]] = None
    ) -> QuestionnaireTriggerResult:
        """
        Check if questionnaire should be triggered.
        
        Args:
            turn_count: Current conversation turn count
            psyguard_result: Result from PsyGUARD scoring (optional)
            
        Returns:
            QuestionnaireTriggerResult with trigger decision
        """
        # Check for direct high risk (highest priority)
        if psyguard_result and psyguard_result.get("should_direct_high_risk", False):
            return QuestionnaireTriggerResult(
                should_trigger=True,
                reason="high_risk_direct",
                immediate_route="high"
            )
        
        # Check for suicide intent (early trigger)
        if psyguard_result and psyguard_result.get("should_trigger_questionnaire", False):
            return QuestionnaireTriggerResult(
                should_trigger=True,
                reason="suicide_intent"
            )
        
        # Default trigger (after turn threshold)
        if turn_count >= self.turn_threshold:
            return QuestionnaireTriggerResult(
                should_trigger=True,
                reason="turn_count"
            )
        
        return QuestionnaireTriggerResult(
            should_trigger=False,
            reason="not_ready"
        )


__all__ = ["QuestionnaireTrigger", "QuestionnaireTriggerResult"]

