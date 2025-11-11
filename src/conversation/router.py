"""
Conversation router for deciding conversation routes based on assessment results.

This module provides functions to:
1. Convert assessment results to routing decisions
2. Determine conversation route (low/medium/high) based on rigidness score
3. Handle high-risk scenarios (hard lock maps to high route)
"""

import logging
from typing import Dict, Any

from src.risk.mapping import load_config, compute_rigid_from_severity, is_hard_lock

logger = logging.getLogger(__name__)


class Route:
    """Conversation route constants."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def decide_route(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide conversation route based on assessment results.
    
    This function takes the output from `assess()` and determines:
    - Conversation route (low/medium/high)
    - Rigidness score (0.0 - 1.0)
    - Reason for routing decision
    
    Note: Hard lock conditions (crisis scenarios) are mapped to HIGH route
    with rigid_score = 1.0.
    
    Args:
        assessment: Assessment result dictionary from `assess()` function.
                   Must contain:
                   - "severity_level" or "severity": severity level string
                   - "flags": dictionary with risk flags (optional)
                   
    Returns:
        Dictionary with routing decision:
        {
            "route": "low" | "medium" | "high",
            "rigid_score": float,  # 0.0 - 1.0
            "reason": str  # Routing reason ("low_risk", "medium_risk", "high_risk", or "hard_lock")
        }
        
    Example:
        >>> from src.assessment.proximo_api import assess
        >>> from src.conversation.router import decide_route
        >>> 
        >>> assessment = await assess("phq9", ["0", "1", "2", "1", "0", "2", "1", "1", "2"])
        >>> route_decision = decide_route(assessment)
        >>> print(route_decision["route"])  # "low", "medium", or "high"
        >>> print(route_decision["rigid_score"])  # 0.0 - 1.0
        >>> print(route_decision["reason"])  # "low_risk", "medium_risk", "high_risk", or "hard_lock"
    """
    cfg = load_config()
    
    # Extract severity level (support multiple field names for compatibility)
    sev = (
        assessment.get("severity_level")
        or assessment.get("severity")
        or "moderate"
    )
    
    flags = assessment.get("flags", {})
    
    # Compute rigidness score from severity
    rigid = compute_rigid_from_severity(sev, cfg)
    
    # Check if hard lock (high-risk scenario) should be triggered
    # Hard lock maps to HIGH route with rigid_score = 1.0
    if is_hard_lock(sev, flags, cfg):
        return {
            "route": Route.HIGH,
            "rigid_score": 1.0,
            "reason": "hard_lock",
        }
    
    # Route based on rigidness thresholds
    # These thresholds can be tuned via config if needed
    routing_thresholds = cfg.severity_to_risk  # Using severity mapping as reference
    low_threshold = 0.40
    medium_threshold = 0.75
    
    if rigid < low_threshold:
        return {
            "route": Route.LOW,
            "rigid_score": rigid,
            "reason": "low_risk",
        }
    elif rigid < medium_threshold:
        return {
            "route": Route.MEDIUM,
            "rigid_score": rigid,
            "reason": "medium_risk",
        }
    else:
        return {
            "route": Route.HIGH,
            "rigid_score": rigid,
            "reason": "high_risk",
        }

