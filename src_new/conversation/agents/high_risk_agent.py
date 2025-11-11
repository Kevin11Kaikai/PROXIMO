"""High Risk Agent - Fixed script with crisis hotline."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from src_new.shared.models import ConversationTurn

logger = logging.getLogger(__name__)

# Fixed safety script for high-risk scenarios
FIXED_SAFETY_SCRIPT = """I'm here to support you, and I want to make sure you're safe.

Right now, the most important thing is your safety. If you're having thoughts of hurting yourself or ending your life, please reach out for immediate help:

• Call or text 988 (US National Suicide & Crisis Lifeline) - available 24/7
• If outside the US, contact your local emergency services
• Reach out to a trusted adult, friend, or healthcare provider

You don't have to go through this alone. There are people who want to help and support you.

Would you like help finding resources in your area, or would you prefer to speak with someone right now?"""

SAFETY_BANNER = "If you are in immediate danger, call or text 988 (US). If outside the US, contact local emergency services."


class HighRiskAgent:
    """High Risk Agent with fixed script for crisis intervention.
    
    Behavior:
    - Must follow fixed safety script
    - No free-form conversation
    - Strongly prompt crisis hotline (988)
    - Suggest urgent meeting with provider
    """
    
    def __init__(self):
        """Initialize High Risk Agent."""
        # No LLM service needed - uses fixed script
        pass
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]] = None,
        rigid_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate fixed safety response for high-risk conversation.
        
        Args:
            user_message: User's message (not used, but kept for API consistency)
            conversation_history: Previous conversation turns (not used)
            rigid_score: Rigidity score (always 1.0 for high risk)
            
        Returns:
            Dict with fixed response and metadata
        """
        logger.warning(
            f"HighRiskAgent: Using fixed safety script (rigid_score={rigid_score})"
        )
        
        # HIGH RISK: Always use fixed script, NO free-form LLM response
        return {
            "agent": "high_risk",
            "response": FIXED_SAFETY_SCRIPT,
            "temperature": 0.0,  # Not used (fixed script)
            "structured": True,
            "safety_banner": SAFETY_BANNER,
            "safety_priority": True,
            "fixed_script": True,
            "crisis_hotline": "988",
            "urgent_meeting_suggested": True
        }
    
    def get_script(self) -> str:
        """Get the fixed safety script."""
        return FIXED_SAFETY_SCRIPT


__all__ = ["HighRiskAgent", "FIXED_SAFETY_SCRIPT", "SAFETY_BANNER"]
