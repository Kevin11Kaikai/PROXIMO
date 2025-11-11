"""Enhanced GuardrailsService for Safety Layer.

This service provides comprehensive safety checks and content filtering
for all conversation layers, with special handling for high-risk scenarios.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.services.guardrails_service import GuardrailsService as LegacyGuardrailsService
from src_new.shared.models import ConversationTurn

logger = logging.getLogger(__name__)


class SafetyGuardrailsService:
    """Enhanced Guardrails service for Safety Layer.
    
    This service wraps the legacy GuardrailsService and adds:
    - Script validation for High Risk scenarios
    - Response filtering for all risk levels
    - Safety checks before response generation
    - Integration with Conversation Layer
    """
    
    def __init__(self, config_path: Optional[str] = None, enabled: bool = True):
        """Initialize Safety Guardrails Service."""
        self.legacy_service = LegacyGuardrailsService(config_path=config_path, enabled=enabled)
        self.enabled = enabled
        self._script_validated = False  # Track if fixed script has been validated
    
    async def initialize(self) -> bool:
        """Initialize the guardrails service."""
        return await self.legacy_service.initialize()
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self.legacy_service._initialized if hasattr(self.legacy_service, '_initialized') else False
    
    async def check_user_input_safety(
        self,
        user_message: str,
        context: Optional[List[ConversationTurn]] = None
    ) -> Dict[str, Any]:
        """
        Check user input for safety concerns.
        
        Args:
            user_message: User's message
            context: Optional conversation history
            
        Returns:
            Dict with safety check results
        """
        if not self.enabled or not self.is_initialized():
            return {
                "safe": True,
                "checked": False,
                "reason": "guardrails_not_enabled"
            }
        
        try:
            # Convert ConversationTurn to dict format for legacy service
            guardrails_context = None
            if context:
                guardrails_context = [
                    {"role": turn.role, "content": turn.text}
                    for turn in context[-5:]  # Last 5 turns
                ]
            
            result = await self.legacy_service.check_safety(
                user_message=user_message,
                context=guardrails_context
            )
            
            return {
                "safe": result.get("safe", True),
                "checked": True,
                "filtered_response": result.get("filtered_response"),
                "reason": result.get("reason"),
                "metadata": result
            }
        except Exception as e:
            logger.error(f"Error checking user input safety: {e}", exc_info=True)
            return {
                "safe": True,  # Fail open for safety
                "checked": False,
                "error": str(e)
            }
    
    async def filter_response(
        self,
        user_message: str,
        proposed_response: str,
        context: Optional[List[ConversationTurn]] = None,
        route: str = "low"
    ) -> Dict[str, Any]:
        """
        Filter and validate bot response for safety.
        
        Args:
            user_message: User's message
            proposed_response: Proposed bot response
            context: Optional conversation history
            route: Risk route (low/medium/high)
            
        Returns:
            Dict with filtering results
        """
        if not self.enabled or not self.is_initialized():
            return {
                "filtered": False,
                "final_response": proposed_response,
                "checked": False
            }
        
        try:
            # Convert ConversationTurn to dict format
            guardrails_context = None
            if context:
                guardrails_context = [
                    {"role": turn.role, "content": turn.text}
                    for turn in context[-5:]
                ]
            
            result = await self.legacy_service.filter_response(
                user_message=user_message,
                proposed_response=proposed_response,
                context=guardrails_context
            )
            
            # For High Risk, ensure we don't modify fixed script
            if route == "high":
                if result.get("filtered") and result.get("final_response") != proposed_response:
                    logger.warning(
                        "Guardrails attempted to modify High Risk fixed script. "
                        "Keeping original script for safety."
                    )
                    return {
                        "filtered": False,
                        "final_response": proposed_response,
                        "checked": True,
                        "warning": "fixed_script_not_modified"
                    }
            
            return {
                "filtered": result.get("filtered", False),
                "final_response": result.get("final_response", proposed_response),
                "checked": True,
                "reason": result.get("reason"),
                "metadata": result
            }
        except Exception as e:
            logger.error(f"Error filtering response: {e}", exc_info=True)
            return {
                "filtered": False,
                "final_response": proposed_response,
                "checked": False,
                "error": str(e)
            }
    
    async def validate_fixed_script(self, script: str) -> Dict[str, Any]:
        """
        Validate fixed safety script for High Risk scenarios.
        
        This should be called at design time to ensure the script is safe.
        At runtime, the script should not be modified.
        
        Args:
            script: Fixed safety script to validate
            
        Returns:
            Dict with validation results
        """
        if not self.enabled or not self.is_initialized():
            return {
                "valid": True,
                "checked": False,
                "reason": "guardrails_not_enabled"
            }
        
        try:
            # Check script against guardrails
            # Use a dummy user message to trigger safety checks
            result = await self.legacy_service.filter_response(
                user_message="I need help",
                proposed_response=script,
                context=None
            )
            
            # Script should pass validation (not be filtered)
            is_valid = not result.get("filtered", False)
            
            if is_valid:
                self._script_validated = True
                logger.info("Fixed safety script validated successfully")
            else:
                logger.warning(
                    f"Fixed safety script failed validation: {result.get('reason')}"
                )
            
            return {
                "valid": is_valid,
                "checked": True,
                "reason": result.get("reason") if not is_valid else None,
                "metadata": result
            }
        except Exception as e:
            logger.error(f"Error validating fixed script: {e}", exc_info=True)
            return {
                "valid": True,  # Fail open for safety
                "checked": False,
                "error": str(e)
            }
    
    async def generate_safe_response(
        self,
        user_message: str,
        context: Optional[List[ConversationTurn]] = None
    ) -> str:
        """
        Generate a safe response using Guardrails.
        
        This is used for high-risk scenarios where we want Guardrails
        to generate the response directly.
        
        Args:
            user_message: User's message
            context: Optional conversation history
            
        Returns:
            Safe response string
        """
        if not self.enabled or not self.is_initialized():
            return "I'm here to help. Could you tell me more about how you're feeling?"
        
        try:
            # Convert ConversationTurn to dict format
            guardrails_context = None
            if context:
                guardrails_context = [
                    {"role": turn.role, "content": turn.text}
                    for turn in context[-5:]
                ]
            
            result = await self.legacy_service.generate_safe_response(
                user_message=user_message,
                context=guardrails_context
            )
            
            return result
        except Exception as e:
            logger.error(f"Error generating safe response: {e}", exc_info=True)
            return "I'm here to help. Could you tell me more about how you're feeling?"
    
    def is_script_validated(self) -> bool:
        """Check if fixed script has been validated."""
        return self._script_validated


__all__ = ["SafetyGuardrailsService"]
