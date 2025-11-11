"""
Session manager for multi-turn conversation context.

Manages conversation history and context for each user session.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages conversation sessions and context.
    
    In-memory storage for conversation turns. Each turn is a dict with:
    - role: "user" or "bot"
    - text: message content
    - timestamp: when the turn occurred
    """
    
    # In-memory storage: {user_id: [turn1, turn2, ...]}
    _sessions: Dict[str, List[Dict[str, Any]]] = {}
    
    @classmethod
    def get_context(cls, user_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation context for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of conversation turns, each with role, text, timestamp
        """
        return cls._sessions.get(user_id, [])
    
    @classmethod
    def append_turn(
        cls,
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
        if user_id not in cls._sessions:
            cls._sessions[user_id] = []
        
        turn = {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        
        cls._sessions[user_id].append(turn)
        
        # Trim to keep last 6 turns (3 user + 3 bot messages typical)
        cls.trim(user_id, max_turns=6)
        
        logger.debug(f"Appended {role} turn for user {user_id}, total turns: {len(cls._sessions[user_id])}")
    
    @classmethod
    def trim(cls, user_id: str, max_turns: int = 6) -> None:
        """
        Trim conversation history to keep only the last N turns.
        
        Args:
            user_id: User identifier
            max_turns: Maximum number of turns to keep
        """
        if user_id in cls._sessions:
            if len(cls._sessions[user_id]) > max_turns:
                cls._sessions[user_id] = cls._sessions[user_id][-max_turns:]
                logger.debug(f"Trimmed session for user {user_id} to {max_turns} turns")
    
    @classmethod
    def clear_session(cls, user_id: str) -> None:
        """
        Clear all conversation history for a user.
        
        Args:
            user_id: User identifier
        """
        if user_id in cls._sessions:
            del cls._sessions[user_id]
            logger.debug(f"Cleared session for user {user_id}")
    
    @classmethod
    def get_recent_turns(cls, user_id: str, n: int = 6) -> List[Dict[str, Any]]:
        """
        Get the most recent N conversation turns.
        
        Args:
            user_id: User identifier
            n: Number of recent turns to return
            
        Returns:
            List of recent conversation turns
        """
        context = cls.get_context(user_id)
        return context[-n:] if len(context) > n else context

