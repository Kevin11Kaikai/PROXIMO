"""Session service for managing conversation sessions."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src_new.shared.models import ConversationTurn

logger = logging.getLogger(__name__)


class SessionService:
    """Manages conversation sessions and context.
    
    Wrapper around legacy SessionManager for new architecture.
    """
    
    def __init__(self):
        """Initialize session service."""
        from src.conversation.session_manager import SessionManager
        self._manager = SessionManager
    
    def get_context(self, user_id: str) -> List[ConversationTurn]:
        """
        Get conversation context for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of ConversationTurn objects
        """
        raw_context = self._manager.get_context(user_id)
        return [
            ConversationTurn(
                role=turn.get("role", "user"),
                text=turn.get("text", ""),
                timestamp=turn.get("timestamp")
            )
            for turn in raw_context
        ]
    
    def append_turn(
        self,
        user_id: str,
        role: str,
        text: str
    ) -> None:
        """
        Append a conversation turn to the session.
        
        Args:
            user_id: User identifier
            role: "user" or "bot"
            text: Message content
        """
        self._manager.append_turn(user_id, role, text)
    
    def get_recent_turns(self, user_id: str, n: int = 6) -> List[ConversationTurn]:
        """
        Get the most recent N conversation turns.
        
        Args:
            user_id: User identifier
            n: Number of recent turns to return
            
        Returns:
            List of recent ConversationTurn objects
        """
        raw_turns = self._manager.get_recent_turns(user_id, n)
        return [
            ConversationTurn(
                role=turn.get("role", "user"),
                text=turn.get("text", ""),
                timestamp=turn.get("timestamp")
            )
            for turn in raw_turns
        ]
    
    def clear_session(self, user_id: str) -> None:
        """
        Clear all conversation history for a user.
        
        Args:
            user_id: User identifier
        """
        self._manager.clear_session(user_id)


__all__ = ["SessionService"]
