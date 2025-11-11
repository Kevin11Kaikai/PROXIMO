"""
Tests for SessionManager - multi-turn conversation context management.
"""

import pytest
from src.conversation.session_manager import SessionManager


class TestSessionManager:
    """Test SessionManager functionality."""
    
    def test_get_context_empty(self):
        """Test getting context for new user (empty)."""
        user_id = "test_user_new"
        context = SessionManager.get_context(user_id)
        assert context == []
    
    def test_append_turn_user(self):
        """Test appending user turn."""
        user_id = "test_user_1"
        SessionManager.clear_session(user_id)  # Clean start
        
        SessionManager.append_turn(user_id, "user", "Hello, I'm feeling anxious")
        
        context = SessionManager.get_context(user_id)
        assert len(context) == 1
        assert context[0]["role"] == "user"
        assert context[0]["text"] == "Hello, I'm feeling anxious"
        assert "timestamp" in context[0]
    
    def test_append_turn_bot(self):
        """Test appending bot turn."""
        user_id = "test_user_2"
        SessionManager.clear_session(user_id)
        
        SessionManager.append_turn(user_id, "bot", "I'm here to help")
        
        context = SessionManager.get_context(user_id)
        assert len(context) == 1
        assert context[0]["role"] == "bot"
        assert context[0]["text"] == "I'm here to help"
    
    def test_append_multiple_turns(self):
        """Test appending multiple turns."""
        user_id = "test_user_3"
        SessionManager.clear_session(user_id)
        
        SessionManager.append_turn(user_id, "user", "Hello")
        SessionManager.append_turn(user_id, "bot", "Hi there")
        SessionManager.append_turn(user_id, "user", "How are you?")
        
        context = SessionManager.get_context(user_id)
        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "bot"
        assert context[2]["role"] == "user"
    
    def test_trim_keeps_last_n_turns(self):
        """Test trim keeps only last N turns."""
        user_id = "test_user_4"
        SessionManager.clear_session(user_id)
        
        # Add more than 6 turns
        for i in range(10):
            role = "user" if i % 2 == 0 else "bot"
            SessionManager.append_turn(user_id, role, f"Message {i}")
        
        context = SessionManager.get_context(user_id)
        # Should be trimmed to 6 turns
        assert len(context) == 6
        # Should be the last 6 messages
        assert context[0]["text"] == "Message 4"
        assert context[5]["text"] == "Message 9"
    
    def test_trim_after_append(self):
        """Test that trim is called automatically after append."""
        user_id = "test_user_5"
        SessionManager.clear_session(user_id)
        
        # Add 8 turns (should be trimmed to 6)
        for i in range(8):
            role = "user" if i % 2 == 0 else "bot"
            SessionManager.append_turn(user_id, role, f"Turn {i}")
        
        context = SessionManager.get_context(user_id)
        assert len(context) == 6  # Auto-trimmed
    
    def test_get_recent_turns(self):
        """Test get_recent_turns returns last N turns."""
        user_id = "test_user_6"
        SessionManager.clear_session(user_id)
        
        for i in range(10):
            SessionManager.append_turn(user_id, "user", f"Msg {i}")
        
        recent = SessionManager.get_recent_turns(user_id, n=3)
        assert len(recent) == 3
        assert recent[0]["text"] == "Msg 7"
        assert recent[2]["text"] == "Msg 9"
    
    def test_clear_session(self):
        """Test clearing session."""
        user_id = "test_user_7"
        
        SessionManager.append_turn(user_id, "user", "Hello")
        assert len(SessionManager.get_context(user_id)) == 1
        
        SessionManager.clear_session(user_id)
        assert len(SessionManager.get_context(user_id)) == 0
    
    def test_multiple_users_independent(self):
        """Test that sessions for different users are independent."""
        user1 = "user_1"
        user2 = "user_2"
        
        SessionManager.clear_session(user1)
        SessionManager.clear_session(user2)
        
        SessionManager.append_turn(user1, "user", "User 1 message")
        SessionManager.append_turn(user2, "user", "User 2 message")
        
        ctx1 = SessionManager.get_context(user1)
        ctx2 = SessionManager.get_context(user2)
        
        assert len(ctx1) == 1
        assert len(ctx2) == 1
        assert ctx1[0]["text"] == "User 1 message"
        assert ctx2[0]["text"] == "User 2 message"

