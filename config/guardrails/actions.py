"""
Custom actions for NeMo Guardrails.

This module can be extended with custom Python actions if needed.
Currently, all safety logic is handled through Colang rules.
"""

from typing import Dict, Any, Optional


def check_high_risk_keywords(message: str) -> bool:
    """
    Check if message contains high-risk keywords.
    
    This is a fallback check - primary safety checks are in Colang rules.
    
    Args:
        message: User message to check
        
    Returns:
        True if high-risk keywords detected
    """
    high_risk_keywords = [
        "suicide", "kill myself", "end my life", "want to die",
        "self harm", "hurt myself", "cut myself"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in high_risk_keywords)


def get_safety_resources() -> Dict[str, Any]:
    """
    Get safety resources information.
    
    Returns:
        Dictionary with safety resources
    """
    return {
        "crisis_line": "988",
        "crisis_line_description": "US National Suicide & Crisis Lifeline (24/7)",
        "emergency_services": "Contact local emergency services",
        "support_options": [
            "Trusted adult or family member",
            "Healthcare provider",
            "School counselor",
            "Mental health professional"
        ]
    }

