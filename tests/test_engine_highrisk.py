"""
Tests for ConversationEngine high-risk scenarios.

Tests that high-risk scenarios trigger:
- Fixed safety script (no free-form chat)
- Safety banner
- Hard lock routing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.conversation.engine import ConversationEngine, ConversationRequest
from src.conversation.router import Route
from src.conversation.policies import SAFETY_BANNER, FIXED_SAFETY_SCRIPT
from src.storage.repo import AssessmentRepo
from src.services.ollama_service import OllamaService


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    repo = AsyncMock(spec=AssessmentRepo)
    repo.has_prior_assessment = AsyncMock(return_value=False)
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = AsyncMock(spec=OllamaService)
    service.is_loaded = True
    return service


@pytest.fixture
def engine(mock_llm_service, mock_repo):
    """Create conversation engine with mocked dependencies."""
    return ConversationEngine(llm_service=mock_llm_service, repo=mock_repo)


class TestEngineHighRisk:
    """Test high-risk scenario handling."""
    
    @pytest.mark.asyncio
    async def test_high_risk_suicidal_ideation(self, engine, mock_repo):
        """Test high-risk scenario with suicidal ideation (Item 9 = 2)."""
        request = ConversationRequest(
            user_id="test_user_high_1",
            scale="phq9",
            responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],  # Item 9 = 2 (suicidal ideation)
            user_message="I don't see the point anymore"
        )
        
        result = await engine.run_pipeline(request)
        
        # Verify assessment
        assert result.assessment["success"] is True
        assert result.assessment["flags"]["suicidal_ideation"] is True
        assert result.assessment["suicidal_risk"] == "high"
        
        # Verify routing
        assert result.decision["route"] == Route.HIGH
        assert result.decision["rigid_score"] == 1.0
        assert result.decision["reason"] == "hard_lock"
        
        # Verify policy result
        assert result.policy_result is not None
        assert result.policy_result["policy"] == "high"
        assert result.policy_result["safety_banner"] == SAFETY_BANNER
        assert result.policy_result["fixed_script"] is True
        # Verify fixed safety script is used (not LLM-generated)
        assert result.policy_result["response"] == FIXED_SAFETY_SCRIPT
        assert "988" in result.policy_result["response"]
        
        # Verify persistence
        mock_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_high_risk_severe_severity(self, engine, mock_repo):
        """Test high-risk scenario with severe severity."""
        request = ConversationRequest(
            user_id="test_user_high_2",
            scale="phq9",
            responses=["3", "3", "3", "3", "3", "3", "3", "3", "0"],  # Severe severity (score 24)
            user_message="I can't function anymore"
        )
        
        result = await engine.run_pipeline(request)
        
        # Verify assessment
        assert result.assessment["success"] is True
        assert result.assessment["severity_level"] == "severe"
        assert result.assessment["total_score"] == 24.0
        
        # Verify routing (severe triggers hard lock)
        assert result.decision["route"] == Route.HIGH
        assert result.decision["rigid_score"] == 1.0
        assert result.decision["reason"] == "hard_lock"
        
        # Verify policy result
        assert result.policy_result is not None
        assert result.policy_result["policy"] == "high"
        assert result.policy_result["safety_banner"] == SAFETY_BANNER
        assert result.policy_result["fixed_script"] is True
        assert result.policy_result["response"] == FIXED_SAFETY_SCRIPT
    
    @pytest.mark.asyncio
    async def test_high_risk_no_free_chat(self, engine, mock_repo):
        """Test that high-risk scenarios do NOT use free-form LLM chat."""
        request = ConversationRequest(
            user_id="test_user_high_3",
            scale="phq9",
            responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],  # Item 9 = 2
            user_message="I want to end it all"
        )
        
        result = await engine.run_pipeline(request)
        
        # Verify fixed script is used (not LLM-generated)
        assert result.policy_result["fixed_script"] is True
        assert result.policy_result["response"] == FIXED_SAFETY_SCRIPT
        
        # Verify LLM was NOT called for high-risk policy
        # (The policy should use fixed script, not call LLM)
        # Note: We can't easily verify this without mocking policies,
        # but we can verify the response is the fixed script
    
    @pytest.mark.asyncio
    async def test_high_risk_safety_banner_always_present(self, engine, mock_repo):
        """Test that safety banner is always present for high-risk scenarios."""
        request = ConversationRequest(
            user_id="test_user_high_4",
            scale="phq9",
            responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],
            user_message="I'm in crisis"
        )
        
        result = await engine.run_pipeline(request)
        
        # Verify safety banner is present
        assert result.policy_result["safety_banner"] == SAFETY_BANNER
        assert SAFETY_BANNER in result.policy_result["safety_banner"]
        assert "988" in result.policy_result["safety_banner"]
    
    @pytest.mark.asyncio
    async def test_high_risk_context_tail(self, engine, mock_repo):
        """Test that context tail is returned for high-risk scenarios."""
        request = ConversationRequest(
            user_id="test_user_high_5",
            scale="phq9",
            responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],
            user_message="I need help"
        )
        
        result = await engine.run_pipeline(request)
        
        # Verify context tail is present
        assert result.context_tail is not None
        assert isinstance(result.context_tail, list)
        # Should have user message and bot response
        assert len(result.context_tail) >= 2
        # Last turn should be bot response
        assert result.context_tail[-1]["role"] == "bot"
        assert result.context_tail[-1]["text"] == FIXED_SAFETY_SCRIPT

