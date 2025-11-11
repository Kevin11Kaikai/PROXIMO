"""
Tests for conversation engine and policies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.conversation.engine import ConversationEngine, ConversationRequest, ConversationResult
from src.conversation.policies import ConversationPolicies, PolicyContext, SAFETY_BANNER
from src.conversation.router import Route


class TestConversationPolicies:
    """Test conversation policies."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        service = AsyncMock()
        service.is_loaded = True
        service.base_url = "http://localhost:11434"
        service.model_name = "llama3.1:8b"
        return service
    
    @pytest.fixture
    def policies(self, mock_llm_service):
        """Create policies instance with mock LLM service."""
        return ConversationPolicies(mock_llm_service)
    
    @pytest.fixture
    def low_context(self):
        """Create low risk context."""
        return PolicyContext(
            user_id="test_user",
            user_message="I'm feeling a bit down today",
            assessment={
                "success": True,
                "severity_level": "minimal",
                "total_score": 3.0,
                "flags": {}
            },
            route=Route.LOW,
            rigid_score=0.15
        )
    
    @pytest.fixture
    def high_context(self):
        """Create high risk context."""
        return PolicyContext(
            user_id="test_user",
            user_message="I don't see the point anymore",
            assessment={
                "success": True,
                "severity_level": "mild",
                "total_score": 10.0,
                "flags": {
                    "suicidal_ideation": True,
                    "suicidal_ideation_score": 2
                }
            },
            route=Route.HIGH,
            rigid_score=1.0
        )
    
    @pytest.mark.asyncio
    async def test_low_policy(self, policies, low_context):
        """Test low risk policy."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "I'm here to listen and support you."}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            
            result = await policies.run_low_policy(low_context)
            
            assert result["policy"] == "low"
            assert result["temperature"] == 0.9
            assert result["safety_banner"] is None
            assert result["structured"] is False
            assert "response" in result
    
    @pytest.mark.asyncio
    async def test_high_policy(self, policies, high_context):
        """Test high risk policy."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "I'm here to help. Please know that support is available."}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            
            result = await policies.run_high_policy(high_context)
            
            assert result["policy"] == "high"
            assert result["temperature"] == 0.0
            assert result["safety_banner"] == SAFETY_BANNER
            assert result["structured"] is True
            assert result["safety_priority"] is True
            assert "response" in result
    
    @pytest.mark.asyncio
    async def test_medium_policy(self, policies):
        """Test medium risk policy."""
        context = PolicyContext(
            user_id="test_user",
            user_message="I've been feeling anxious lately",
            assessment={
                "success": True,
                "severity_level": "moderate",
                "total_score": 12.0,
                "flags": {}
            },
            route=Route.MEDIUM,
            rigid_score=0.60
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "I understand this is important. Let's work through this together."}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            
            result = await policies.run_medium_policy(context)
            
            assert result["policy"] == "medium"
            assert result["temperature"] == 0.6
            assert result["safety_banner"] is None
            assert result["structured"] is True
            assert "response" in result


class TestConversationEngine:
    """Test conversation engine."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        service = AsyncMock()
        service.is_loaded = True
        service.base_url = "http://localhost:11434"
        service.model_name = "llama3.1:8b"
        return service
    
    @pytest.fixture
    def engine(self, mock_llm_service):
        """Create conversation engine."""
        return ConversationEngine(mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_pipeline_low_risk(self, engine):
        """Test complete pipeline for low risk scenario."""
        request = ConversationRequest(
            user_id="test_user",
            scale="phq9",
            responses=["0", "0", "1", "0", "1", "0", "1", "0", "0"],
            user_message="I'm feeling okay today"
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "That's good to hear. I'm here if you need to talk."}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            
            result = await engine.run_pipeline(request)
            
            assert isinstance(result, ConversationResult)
            assert result.assessment["success"] is True
            assert result.decision["route"] == Route.LOW
            assert result.policy_result is not None
            assert result.policy_result["policy"] == "low"
            assert result.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_high_risk(self, engine):
        """Test complete pipeline for high risk scenario."""
        request = ConversationRequest(
            user_id="test_user",
            scale="phq9",
            responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],  # Item 9 = 2 (suicidal ideation)
            user_message="I don't see the point anymore"
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "I'm here to help. Support is available."}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            
            result = await engine.run_pipeline(request)
            
            assert isinstance(result, ConversationResult)
            assert result.assessment["success"] is True
            assert result.decision["route"] == Route.HIGH
            assert result.decision["reason"] == "hard_lock"
            assert result.policy_result is not None
            assert result.policy_result["policy"] == "high"
            assert result.policy_result["safety_banner"] == SAFETY_BANNER
    
    @pytest.mark.asyncio
    async def test_pipeline_no_user_message(self, engine):
        """Test pipeline without user message (no policy execution)."""
        request = ConversationRequest(
            user_id="test_user",
            scale="phq9",
            responses=["0", "0", "1", "0", "1", "0", "1", "0", "0"],
            user_message=None  # No user message
        )
        
        result = await engine.run_pipeline(request)
        
        assert isinstance(result, ConversationResult)
        assert result.assessment["success"] is True
        assert result.decision["route"] == Route.LOW
        assert result.policy_result is None  # No policy execution without user message

