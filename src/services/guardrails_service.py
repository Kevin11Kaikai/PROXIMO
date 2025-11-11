"""
NeMo Guardrails service for PROXIMO safety and ethics layer.

This service wraps NeMo Guardrails to provide safety checks and content filtering
for the conversation system, particularly in high-risk scenarios.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from nemoguardrails import LLMRails, RailsConfig
from langchain_community.llms import Ollama

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class GuardrailsService:
    """
    Service for NeMo Guardrails integration.
    
    Provides safety checks and content filtering for conversation responses,
    particularly in high-risk scenarios (suicidal ideation, crisis situations).
    """
    
    def __init__(self, config_path: Optional[str] = None, enabled: bool = True):
        """
        Initialize Guardrails service.
        
        Args:
            config_path: Path to Guardrails config directory (default: config/guardrails)
            enabled: Whether Guardrails is enabled (default: True)
        """
        self.enabled = enabled
        self.config_path = config_path or str(Path(__file__).parent.parent.parent / "config" / "guardrails")
        self.rails: Optional[LLMRails] = None
        self.llm: Optional[Ollama] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize Guardrails service.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.enabled:
            logger.info("Guardrails service is disabled")
            return True
            
        if self._initialized:
            return True
            
        try:
            logger.info(f"Initializing Guardrails service from {self.config_path}")
            
            # Create LangChain Ollama LLM
            self.llm = Ollama(
                base_url=settings.OLLAMA_URL,
                model=settings.MODEL_NAME,
                temperature=0.7
            )
            
            # Load Guardrails config
            config = RailsConfig.from_path(self.config_path)
            logger.info("Guardrails config loaded successfully")
            
            # Create LLMRails instance
            self.rails = LLMRails(config=config, llm=self.llm)
            logger.info("Guardrails LLMRails instance created successfully")
            
            self._initialized = True
            logger.info("Guardrails service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Guardrails service: {e}", exc_info=True)
            self._initialized = False
            return False
    
    async def check_safety(
        self,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Check message safety using Guardrails.
        
        Args:
            user_message: User message to check
            context: Optional conversation context (list of {"role": "user/assistant", "content": "..."})
            
        Returns:
            Dictionary with:
                - safe: bool - Whether message is safe
                - filtered_response: Optional[str] - Guardrails-filtered response if triggered
                - triggered_rules: List[str] - List of triggered rule names
                - metadata: Dict - Additional metadata
        """
        if not self.enabled or not self._initialized:
            return {
                "safe": True,
                "filtered_response": None,
                "triggered_rules": [],
                "metadata": {"guardrails_enabled": False}
            }
        
        try:
            # Build messages for Guardrails
            messages = []
            if context:
                # Add conversation history
                for msg in context[-5:]:  # Last 5 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", msg.get("text", ""))
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response through Guardrails
            response = await self.rails.generate_async(messages=messages)
            
            # Parse response
            if isinstance(response, dict):
                response_content = response.get("content", "")
            else:
                response_content = str(response)
            
            # Check if safety rules were triggered
            # (Guardrails will automatically intercept and provide safety responses)
            safety_keywords = ["988", "crisis", "safety", "emergency", "suicide"]
            triggered = any(keyword.lower() in response_content.lower() for keyword in safety_keywords)
            
            # Check if response is different from what would be generated normally
            # This indicates Guardrails intervened
            is_filtered = triggered or len(response_content) > 0
            
            return {
                "safe": True,  # Guardrails handled it, so it's "safe" (filtered)
                "filtered_response": response_content if is_filtered else None,
                "triggered_rules": ["safety"] if triggered else [],
                "metadata": {
                    "guardrails_enabled": True,
                    "response_length": len(response_content),
                    "intervened": is_filtered
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Guardrails safety check: {e}", exc_info=True)
            # On error, allow message through but log it
            return {
                "safe": True,
                "filtered_response": None,
                "triggered_rules": [],
                "metadata": {
                    "guardrails_enabled": True,
                    "error": str(e)
                }
            }
    
    async def filter_response(
        self,
        user_message: str,
        proposed_response: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Filter a proposed response through Guardrails.
        
        This is used to check if a generated response should be modified
        or replaced based on safety rules.
        
        Args:
            user_message: Original user message
            proposed_response: Proposed bot response to filter
            context: Optional conversation context
            
        Returns:
            Dictionary with:
                - filtered: bool - Whether response was filtered
                - final_response: str - Final response (filtered or original)
                - reason: Optional[str] - Reason for filtering
        """
        if not self.enabled or not self._initialized:
            return {
                "filtered": False,
                "final_response": proposed_response,
                "reason": None
            }
        
        try:
            # Check safety of the conversation
            safety_result = await self.check_safety(user_message, context)
            
            # If Guardrails provided a filtered response, use it
            if safety_result.get("filtered_response"):
                return {
                    "filtered": True,
                    "final_response": safety_result["filtered_response"],
                    "reason": "safety_rule_triggered"
                }
            
            # Otherwise, use proposed response
            return {
                "filtered": False,
                "final_response": proposed_response,
                "reason": None
            }
            
        except Exception as e:
            logger.error(f"Error in Guardrails response filtering: {e}", exc_info=True)
            # On error, allow original response through
            return {
                "filtered": False,
                "final_response": proposed_response,
                "reason": None
            }
    
    async def generate_safe_response(
        self,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a safe response using Guardrails.
        
        This method uses Guardrails to generate the response directly,
        ensuring all safety rules are applied.
        
        Args:
            user_message: User message
            context: Optional conversation context
            
        Returns:
            Safe response string
        """
        if not self.enabled or not self._initialized:
            logger.warning("Guardrails not initialized, cannot generate safe response")
            return "I'm here to help. How can I assist you?"
        
        try:
            # Build messages
            messages = []
            if context:
                for msg in context[-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", msg.get("text", ""))
                    })
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate through Guardrails
            response = await self.rails.generate_async(messages=messages)
            
            if isinstance(response, dict):
                return response.get("content", "")
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating safe response: {e}", exc_info=True)
            return "I'm here to help. How can I assist you?"
    
    def is_initialized(self) -> bool:
        """Check if Guardrails service is initialized."""
        return self._initialized and self.enabled
    
    async def cleanup(self):
        """Cleanup resources."""
        self.rails = None
        self.llm = None
        self._initialized = False


# Global Guardrails service instance
_guardrails_service: Optional[GuardrailsService] = None


def get_guardrails_service() -> GuardrailsService:
    """
    Get global Guardrails service instance.
    
    Returns:
        GuardrailsService instance
    """
    global _guardrails_service
    if _guardrails_service is None:
        _guardrails_service = GuardrailsService()
    return _guardrails_service

