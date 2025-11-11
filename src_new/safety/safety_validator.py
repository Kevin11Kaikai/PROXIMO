"""Safety validators for response content."""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

# Prohibited content patterns
PROHIBITED_PATTERNS = [
    r"how to (kill|hurt|harm) (yourself|myself)",
    r"suicide (method|way|how)",
    r"end (your|my) life",
    r"commit suicide",
    r"self-harm (method|way)",
]

# Required safety elements for High Risk responses
REQUIRED_SAFETY_ELEMENTS = [
    "988",  # Crisis hotline
    "crisis",  # Crisis keyword
    "safety",  # Safety keyword
    "help",  # Help keyword
    "emergency",  # Emergency keyword
]


class SafetyValidator:
    """Validates response content for safety compliance."""
    
    @staticmethod
    def validate_response_content(
        response: str,
        route: str = "low"
    ) -> Dict[str, Any]:
        """
        Validate response content for safety.
        
        Args:
            response: Response text to validate
            route: Risk route (low/medium/high)
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check for prohibited content
        response_lower = response.lower()
        for pattern in PROHIBITED_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                issues.append(f"Contains prohibited pattern: {pattern}")
        
        # For High Risk, check required elements
        if route == "high":
            missing_elements = []
            for element in REQUIRED_SAFETY_ELEMENTS:
                if element.lower() not in response_lower:
                    missing_elements.append(element)
            
            if missing_elements:
                issues.append(f"Missing required safety elements: {missing_elements}")
        
        is_valid = len(issues) == 0
        
        return {
            "valid": is_valid,
            "issues": issues,
            "route": route
        }
    
    @staticmethod
    def validate_fixed_script(script: str) -> Dict[str, Any]:
        """
        Validate fixed safety script.
        
        Args:
            script: Fixed script to validate
            
        Returns:
            Dict with validation results
        """
        # Check required elements
        script_lower = script.lower()
        missing_elements = []
        
        for element in REQUIRED_SAFETY_ELEMENTS:
            if element.lower() not in script_lower:
                missing_elements.append(element)
        
        # Check for prohibited content (should not be in safety script)
        has_prohibited = False
        for pattern in PROHIBITED_PATTERNS:
            if re.search(pattern, script_lower, re.IGNORECASE):
                has_prohibited = True
                break
        
        is_valid = len(missing_elements) == 0 and not has_prohibited
        
        return {
            "valid": is_valid,
            "missing_elements": missing_elements,
            "has_prohibited": has_prohibited,
            "script_length": len(script)
        }
    
    @staticmethod
    def check_user_message_safety(user_message: str) -> Dict[str, Any]:
        """
        Check user message for immediate safety concerns.
        
        Args:
            user_message: User's message
            
        Returns:
            Dict with safety check results
        """
        message_lower = user_message.lower()
        
        # Check for crisis keywords
        crisis_keywords = [
            "kill myself", "suicide", "end my life", "want to die",
            "hurt myself", "self-harm", "no point living", "no point in living",
            "don't want to live", "don't want to be alive"
        ]
        
        detected_keywords = []
        for keyword in crisis_keywords:
            if keyword in message_lower:
                detected_keywords.append(keyword)
        
        is_crisis = len(detected_keywords) > 0
        
        return {
            "is_crisis": is_crisis,
            "detected_keywords": detected_keywords,
            "requires_immediate_attention": is_crisis
        }


__all__ = ["SafetyValidator"]

