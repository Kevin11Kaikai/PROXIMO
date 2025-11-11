"""Low Risk Agent - Free chat with coping skills suggestions."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from src.services.ollama_service import OllamaService
from src_new.shared.models import ConversationTurn

logger = logging.getLogger(__name__)

# System prompt for Low Risk Agent
LOW_RISK_SYSTEM_PROMPT = """You are a supportive and empathetic mental health assistant for teens.

Your role in LOW RISK conversations:
- Provide empathetic, natural conversation
- Suggest coping skills when appropriate (breathing exercises, journaling, mindfulness, etc.)
- Maintain a warm, understanding tone
- Continue conversation until the user says goodbye

Guidelines:
- Be conversational and flexible
- Offer practical coping strategies
- Validate the user's feelings
- Do not diagnose or provide medical advice
- End naturally when the user indicates they're done

Remember: This is a low-risk conversation, so you have high flexibility to engage naturally."""


class LowRiskAgent:
    """Low Risk Agent for free empathetic chat with coping skills.
    
    Behavior:
    - Free conversation with high flexibility
    - Suggest coping skills when appropriate
    - Continue until user says goodbye
    """
    
    def __init__(self, llm_service: Optional[OllamaService] = None):
        """Initialize Low Risk Agent."""
        self.llm_service = llm_service or OllamaService()
        self.temperature = 0.9  # High flexibility
        self.max_tokens = 512
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]] = None,
        rigid_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate empathetic response for low-risk conversation.
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation turns
            rigid_score: Rigidity score (0.0-1.0), affects temperature
            
        Returns:
            Dict with response and metadata
        """
        try:
            # Adjust temperature based on rigidity
            adjusted_temp = max(0.1, self.temperature - 0.8 * rigid_score)
            
            # Build conversation context
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system",
                "content": LOW_RISK_SYSTEM_PROMPT
            })
            
            # Add conversation history
            if conversation_history:
                for turn in conversation_history[-6:]:  # Last 6 turns
                    messages.append({
                        "role": turn.role,
                        "content": turn.text
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response using Ollama API directly
            # Build prompt from messages
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"Assistant: {msg['content']}")
            prompt_parts.append("Assistant:")
            prompt = "\n".join(prompt_parts)
            
            # Call Ollama API directly
            if not self.llm_service.is_loaded:
                await self.llm_service.load_model()
            
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(
                        f"{self.llm_service.base_url}/api/generate",
                        json={
                            "model": self.llm_service.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "num_predict": self.max_tokens,
                                "temperature": adjusted_temp,
                                "top_p": 0.9,
                                "top_k": 40,
                                "num_ctx": 2048,
                                "repeat_penalty": 1.1,
                            }
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result.get("response", "").strip()
                    else:
                        logger.warning(f"Ollama API error: {response.status_code}")
                        response_text = "I'm here to listen. How can I help you today?"
                except Exception as e:
                    logger.warning(f"Ollama API error: {e}")
                    response_text = "I'm here to listen. How can I help you today?"
            
            logger.info(f"LowRiskAgent generated response (temp={adjusted_temp:.2f})")
            
            return {
                "agent": "low_risk",
                "response": response_text,
                "temperature": adjusted_temp,
                "structured": False,
                "safety_banner": None,
                "coping_skills_suggested": self._detect_coping_skills(response_text)
            }
            
        except Exception as e:
            logger.error(f"Error in LowRiskAgent: {e}", exc_info=True)
            return {
                "agent": "low_risk",
                "response": "I'm here to listen. How can I help you today?",
                "error": str(e),
                "temperature": adjusted_temp if 'adjusted_temp' in locals() else self.temperature
            }
    
    def _detect_coping_skills(self, response: str) -> bool:
        """Detect if response suggests coping skills."""
        coping_keywords = [
            "breathing", "journal", "mindfulness", "exercise", "meditation",
            "relaxation", "coping", "strategy", "technique", "practice"
        ]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in coping_keywords)
    
    def is_goodbye(self, user_message: str) -> bool:
        """Check if user is saying goodbye."""
        goodbye_keywords = [
            "goodbye", "bye", "see you", "thanks", "thank you",
            "that's all", "done", "finished", "gotta go"
        ]
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in goodbye_keywords)


__all__ = ["LowRiskAgent"]
