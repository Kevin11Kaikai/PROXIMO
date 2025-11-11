"""High-level conversation pipeline using new agents."""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from src_new.control.risk_router import RiskRouter
from src_new.control.control_context import ControlContext
from src_new.conversation.agents.low_risk_agent import LowRiskAgent
from src_new.conversation.agents.medium_risk_agent import MediumRiskAgent
from src_new.conversation.agents.high_risk_agent import HighRiskAgent
from src_new.conversation.session_service import SessionService
from src_new.shared.models import ConversationTurn

logger = logging.getLogger(__name__)


class ConversationPipeline:
    """Orchestrate conversation using new agents based on risk level.
    
    This pipeline uses the new Agent architecture:
    - LowRiskAgent: Free chat + coping skills
    - MediumRiskAgent: Semi-structured + peer support group (with state machine)
    - HighRiskAgent: Fixed script + crisis hotline
    """
    
    def __init__(self):
        """Initialize conversation pipeline."""
        self.router = RiskRouter()
        self.session_service = SessionService()
        self.low_agent = LowRiskAgent()
        self.medium_agent = MediumRiskAgent()
        self.high_agent = HighRiskAgent()
    
    async def process_message(
        self,
        user_id: str,
        user_message: str,
        control_context: ControlContext
    ) -> Dict[str, Any]:
        """
        Process a user message and generate response using appropriate agent.
        
        Args:
            user_id: User identifier
            user_message: User's message
            control_context: Control context with route and risk information
            
        Returns:
            Dict with agent response and metadata
        """
        try:
            # Get conversation history
            history = self.session_service.get_context(user_id)
            
            # Route to appropriate agent
            route = control_context.route
            
            if route == "high":
                agent_result = await self.high_agent.generate_response(
                    user_message=user_message,
                    conversation_history=history,
                    rigid_score=control_context.rigid_score
                )
            elif route == "medium":
                agent_result = await self.medium_agent.generate_response(
                    user_id=user_id,
                    user_message=user_message,
                    conversation_history=history,
                    rigid_score=control_context.rigid_score
                )
            else:  # low
                agent_result = await self.low_agent.generate_response(
                    user_message=user_message,
                    conversation_history=history,
                    rigid_score=control_context.rigid_score
                )
            
            # Append turns to session
            self.session_service.append_turn(user_id, "user", user_message)
            self.session_service.append_turn(user_id, "bot", agent_result.get("response", ""))
            
            logger.info(
                f"ConversationPipeline: user={user_id}, route={route}, "
                f"agent={agent_result.get('agent', 'unknown')}"
            )
            
            return {
                "user_id": user_id,
                "route": route,
                "agent_result": agent_result,
                "control_context": control_context
            }
            
        except Exception as e:
            logger.error(f"Error in ConversationPipeline: {e}", exc_info=True)
            return {
                "user_id": user_id,
                "route": control_context.route,
                "error": str(e),
                "agent_result": {
                    "agent": control_context.route + "_risk",
                    "response": "I'm here to help. Could you tell me more about how you're feeling?",
                    "error": str(e)
                }
            }
    
    def get_conversation_history(self, user_id: str) -> List[ConversationTurn]:
        """Get conversation history for a user."""
        return self.session_service.get_context(user_id)
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user."""
        self.session_service.clear_session(user_id)
        # Also reset Medium Risk Agent state if needed
        self.medium_agent.reset_state(user_id)


__all__ = ["ConversationPipeline"]
