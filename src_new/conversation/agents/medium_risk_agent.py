"""Medium Risk Agent - Semi-structured peer support group guidance with state machine."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, Literal
from enum import Enum
from dataclasses import dataclass, field

from src.services.ollama_service import OllamaService
from src_new.shared.models import ConversationTurn

logger = logging.getLogger(__name__)

# Resistance keywords
RESISTANCE_KEYWORDS = {
    "privacy": ["privacy", "private", "anonymous", "personal", "confidential"],
    "time": ["time", "busy", "schedule", "don't have time", "no time"],
    "stigma": ["stigma", "embarrassed", "ashamed", "judge", "judgment"],
    "doubt": ["doubt", "not sure", "don't think", "won't help", "doesn't work"]
}

# System prompts for different states
MEDIUM_RISK_SYSTEM_PROMPT = """You are a supportive and empathetic mental health assistant for teens.

Your role in MEDIUM RISK conversations:
- Acknowledge the user's anxiety and concerns
- Suggest joining a peer support group (mention: "*peer group has a moderator for safety*")
- Handle resistance with empathy and understanding
- Address specific concerns (privacy, time, stigma, doubt)
- Confirm if the user wants to join

Guidelines:
- Be semi-structured but empathetic
- Address resistance with specific counter-arguments
- Maximum 5 persuasion turns
- If user accepts: confirm and provide next steps
- If user still resists after 5 turns: offer self-help resources

Remember: This is a medium-risk conversation, so you need to balance structure with empathy."""

PERSUASION_PROMPT = """The user has expressed resistance to joining a peer support group.

Your task:
1. Identify the specific concern (privacy, time, stigma, or doubt)
2. Provide a targeted, empathetic response addressing that concern
3. Reassure them about the peer group's safety and benefits

Be understanding but persistent (within the 5-turn limit)."""


class MediumRiskState(Enum):
    """State machine states for Medium Risk Agent."""
    INITIAL_SUGGESTION = "initial_suggestion"
    DETECTING_RESISTANCE = "detecting_resistance"
    HANDLING_RESISTANCE = "handling_resistance"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROVIDING_RESOURCES = "providing_resources"


@dataclass
class MediumRiskAgentState:
    """State for Medium Risk Agent."""
    current_state: MediumRiskState = MediumRiskState.INITIAL_SUGGESTION
    resistance_count: int = 0
    detected_resistance_type: Optional[str] = None
    max_persuasion_turns: int = 5
    conversation_turns: List[Dict[str, Any]] = field(default_factory=list)


class MediumRiskAgent:
    """Medium Risk Agent with state machine for peer support group guidance.
    
    Behavior:
    - Suggest peer support group
    - Detect and handle resistance (privacy, time, stigma, doubt)
    - Maximum 5 persuasion turns
    - State machine: Initial → Detecting → Handling → Accepted/Rejected
    """
    
    def __init__(self, llm_service: Optional[OllamaService] = None):
        """Initialize Medium Risk Agent."""
        self.llm_service = llm_service or OllamaService()
        self.temperature = 0.6  # Semi-structured
        self.max_tokens = 512
        # Per-user state storage
        self._user_states: Dict[str, MediumRiskAgentState] = {}
    
    def _get_state(self, user_id: str) -> MediumRiskAgentState:
        """Get or create state for user."""
        if user_id not in self._user_states:
            self._user_states[user_id] = MediumRiskAgentState()
        return self._user_states[user_id]
    
    def _detect_resistance(self, user_message: str) -> Optional[str]:
        """Detect resistance type from user message."""
        message_lower = user_message.lower()
        for resistance_type, keywords in RESISTANCE_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                return resistance_type
        return None
    
    async def generate_response(
        self,
        user_id: str,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]] = None,
        rigid_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate response for medium-risk conversation with state machine.
        
        Args:
            user_id: User identifier
            user_message: User's message
            conversation_history: Previous conversation turns
            rigid_score: Rigidity score (0.0-1.0)
            
        Returns:
            Dict with response and metadata
        """
        try:
            state = self._get_state(user_id)
            
            # Adjust temperature based on rigidity
            adjusted_temp = max(0.1, self.temperature - 0.8 * rigid_score)
            
            # State machine logic
            if state.current_state == MediumRiskState.INITIAL_SUGGESTION:
                response = await self._handle_initial_suggestion(
                    user_message, conversation_history, adjusted_temp
                )
                # Check for resistance
                resistance_type = self._detect_resistance(user_message)
                if resistance_type:
                    state.current_state = MediumRiskState.HANDLING_RESISTANCE
                    state.detected_resistance_type = resistance_type
                    state.resistance_count = 1
                else:
                    # Check if user accepts
                    if self._is_acceptance(user_message):
                        state.current_state = MediumRiskState.ACCEPTED
                    else:
                        state.current_state = MediumRiskState.DETECTING_RESISTANCE
                        
            elif state.current_state == MediumRiskState.HANDLING_RESISTANCE:
                response = await self._handle_resistance(
                    user_id, user_message, conversation_history, adjusted_temp
                )
                # Update resistance count
                state.resistance_count += 1
                
                # Check if exceeded max turns
                if state.resistance_count > state.max_persuasion_turns:
                    state.current_state = MediumRiskState.REJECTED
                    response = await self._provide_resources(
                        user_message, conversation_history, adjusted_temp
                    )
                elif self._is_acceptance(user_message):
                    state.current_state = MediumRiskState.ACCEPTED
                    response["peer_group_accepted"] = True
                else:
                    # Check for new resistance type
                    new_resistance = self._detect_resistance(user_message)
                    if new_resistance and new_resistance != state.detected_resistance_type:
                        state.detected_resistance_type = new_resistance
                    
            elif state.current_state == MediumRiskState.ACCEPTED:
                response = await self._confirm_acceptance(
                    user_message, conversation_history, adjusted_temp
                )
                
            elif state.current_state == MediumRiskState.REJECTED:
                response = await self._provide_resources(
                    user_message, conversation_history, adjusted_temp
                )
                
            else:
                # Default: handle as initial suggestion
                response = await self._handle_initial_suggestion(
                    user_message, conversation_history, adjusted_temp
                )
            
            # Store turn
            state.conversation_turns.append({
                "user_message": user_message,
                "bot_response": response.get("response", ""),
                "state": state.current_state.value
            })
            
            logger.info(
                f"MediumRiskAgent: user={user_id}, state={state.current_state.value}, "
                f"resistance_count={state.resistance_count}"
            )
            
            return {
                "agent": "medium_risk",
                "response": response.get("response", ""),
                "temperature": adjusted_temp,
                "structured": True,
                "safety_banner": None,
                "state": state.current_state.value,
                "resistance_count": state.resistance_count,
                "resistance_type": state.detected_resistance_type,
                **response
            }
            
        except Exception as e:
            logger.error(f"Error in MediumRiskAgent: {e}", exc_info=True)
            return {
                "agent": "medium_risk",
                "response": "I understand this is important. Let's work through this together.",
                "error": str(e),
                "temperature": adjusted_temp if 'adjusted_temp' in locals() else self.temperature
            }
    
    async def _handle_initial_suggestion(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]],
        temperature: float
    ) -> Dict[str, Any]:
        """Handle initial peer group suggestion."""
        messages = [
            {"role": "system", "content": MEDIUM_RISK_SYSTEM_PROMPT},
        ]
        
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append({"role": turn.role, "content": turn.text})
        
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
                            "temperature": temperature,
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
                    response_text = "I understand this is important. Let's work through this together."
            except Exception as e:
                logger.warning(f"Ollama API error: {e}")
                response_text = "I understand this is important. Let's work through this together."
        
        return {"response": response_text}
    
    async def _handle_resistance(
        self,
        user_id: str,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]],
        temperature: float
    ) -> Dict[str, Any]:
        """Handle user resistance with targeted response."""
        state = self._get_state(user_id)
        resistance_type = state.detected_resistance_type or "general"
        
        messages = [
            {"role": "system", "content": PERSUASION_PROMPT},
        ]
        
        # Add context about resistance type
        context = f"The user's concern is about: {resistance_type}. Address this specifically."
        messages.append({"role": "system", "content": context})
        
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append({"role": turn.role, "content": turn.text})
        
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
                            "temperature": temperature,
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
                    response_text = "I understand this is important. Let's work through this together."
            except Exception as e:
                logger.warning(f"Ollama API error: {e}")
                response_text = "I understand this is important. Let's work through this together."
        
        return {"response": response_text, "addressing_resistance": resistance_type}
    
    async def _confirm_acceptance(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]],
        temperature: float
    ) -> Dict[str, Any]:
        """Confirm peer group acceptance and provide next steps."""
        messages = [
            {"role": "system", "content": "The user has accepted joining the peer support group. Confirm this and provide next steps."},
        ]
        
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append({"role": turn.role, "content": turn.text})
        
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
                            "temperature": temperature,
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
                    response_text = "I understand this is important. Let's work through this together."
            except Exception as e:
                logger.warning(f"Ollama API error: {e}")
                response_text = "I understand this is important. Let's work through this together."
        
        return {"response": response_text, "peer_group_accepted": True}
    
    async def _provide_resources(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]],
        temperature: float
    ) -> Dict[str, Any]:
        """Provide self-help resources when user rejects peer group."""
        messages = [
            {"role": "system", "content": "The user has declined joining the peer support group after multiple attempts. Provide self-help resources and support options."},
        ]
        
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append({"role": turn.role, "content": turn.text})
        
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
                            "temperature": temperature,
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
                    response_text = "I understand this is important. Let's work through this together."
            except Exception as e:
                logger.warning(f"Ollama API error: {e}")
                response_text = "I understand this is important. Let's work through this together."
        
        return {"response": response_text, "resources_provided": True}
    
    def _is_acceptance(self, user_message: str) -> bool:
        """Check if user message indicates acceptance."""
        acceptance_keywords = [
            "yes", "okay", "ok", "sure", "I'll join", "sounds good",
            "I'd like to", "I want to", "let's do it"
        ]
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in acceptance_keywords)
    
    def reset_state(self, user_id: str):
        """Reset state for a user (e.g., after conversation ends)."""
        if user_id in self._user_states:
            del self._user_states[user_id]


__all__ = ["MediumRiskAgent", "MediumRiskState", "MediumRiskAgentState"]
