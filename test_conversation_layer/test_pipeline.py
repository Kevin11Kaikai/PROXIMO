"""
Integration test for ConversationPipeline.

Tests the complete conversation pipeline with all agents.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows encoding setup
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src_new.conversation.pipeline import ConversationPipeline
from src_new.control.control_context import ControlContext


async def test_low_risk_pipeline():
    """Test pipeline with Low Risk route."""
    print("\n" + "=" * 80)
    print("测试 1: Low Risk 管道")
    print("=" * 80)
    
    pipeline = ConversationPipeline()
    user_id = "test_user_low"
    
    context = ControlContext(
        user_id=user_id,
        route="low",
        rigid_score=0.2,
        psyguard_score=0.3
    )
    
    user_message = "I've been feeling a bit stressed with school."
    
    result = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message,
        control_context=context
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   路由: {result.get('route')}")
    print(f"   Agent: {result.get('agent_result', {}).get('agent')}")
    print(f"   响应: {result.get('agent_result', {}).get('response', '')[:200]}...")
    print(f"   ✅ Low Risk 管道测试完成")


async def test_medium_risk_pipeline():
    """Test pipeline with Medium Risk route."""
    print("\n" + "=" * 80)
    print("测试 2: Medium Risk 管道")
    print("=" * 80)
    
    pipeline = ConversationPipeline()
    user_id = "test_user_medium"
    
    context = ControlContext(
        user_id=user_id,
        route="medium",
        rigid_score=0.6,
        psyguard_score=0.75
    )
    
    user_message = "I've been feeling really anxious and isolated."
    
    result = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message,
        control_context=context
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   路由: {result.get('route')}")
    print(f"   Agent: {result.get('agent_result', {}).get('agent')}")
    print(f"   状态: {result.get('agent_result', {}).get('state')}")
    print(f"   响应: {result.get('agent_result', {}).get('response', '')[:200]}...")
    print(f"   ✅ Medium Risk 管道测试完成")


async def test_high_risk_pipeline():
    """Test pipeline with High Risk route."""
    print("\n" + "=" * 80)
    print("测试 3: High Risk 管道")
    print("=" * 80)
    
    pipeline = ConversationPipeline()
    user_id = "test_user_high"
    
    context = ControlContext(
        user_id=user_id,
        route="high",
        rigid_score=1.0,
        psyguard_score=0.96
    )
    
    user_message = "I don't want to live anymore."
    
    result = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message,
        control_context=context
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   路由: {result.get('route')}")
    print(f"   Agent: {result.get('agent_result', {}).get('agent')}")
    print(f"   固定脚本: {result.get('agent_result', {}).get('fixed_script')}")
    print(f"   安全横幅: {result.get('agent_result', {}).get('safety_banner', '')[:100]}...")
    print(f"   ✅ High Risk 管道测试完成")


async def test_conversation_history():
    """Test conversation history management."""
    print("\n" + "=" * 80)
    print("测试 4: 对话历史管理")
    print("=" * 80)
    
    pipeline = ConversationPipeline()
    user_id = "test_user_history"
    
    context = ControlContext(
        user_id=user_id,
        route="low",
        rigid_score=0.2
    )
    
    # First message
    result1 = await pipeline.process_message(
        user_id=user_id,
        user_message="I'm feeling stressed.",
        control_context=context
    )
    
    # Second message (should have history)
    result2 = await pipeline.process_message(
        user_id=user_id,
        user_message="What can I do about it?",
        control_context=context
    )
    
    # Check history
    history = pipeline.get_conversation_history(user_id)
    
    print(f"   历史记录轮次: {len(history)}")
    print(f"   第一轮: {history[0].role} - {history[0].text[:50]}...")
    print(f"   第二轮: {history[1].role} - {history[1].text[:50]}...")
    print(f"   ✅ 对话历史测试完成")


async def test_clear_conversation():
    """Test clearing conversation."""
    print("\n" + "=" * 80)
    print("测试 5: 清除对话")
    print("=" * 80)
    
    pipeline = ConversationPipeline()
    user_id = "test_user_clear"
    
    context = ControlContext(
        user_id=user_id,
        route="low",
        rigid_score=0.2
    )
    
    # Add some messages
    await pipeline.process_message(
        user_id=user_id,
        user_message="Test message 1",
        control_context=context
    )
    await pipeline.process_message(
        user_id=user_id,
        user_message="Test message 2",
        control_context=context
    )
    
    # Clear
    pipeline.clear_conversation(user_id)
    
    # Check history is empty
    history = pipeline.get_conversation_history(user_id)
    
    assert len(history) == 0, "History should be empty after clear"
    
    print(f"   清除后历史记录: {len(history)} 轮次")
    print(f"   ✅ 清除对话测试完成")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("ConversationPipeline 集成测试")
    print("=" * 80)
    print("\n此脚本将测试完整的对话管道")
    print("包括：Low/Medium/High Risk 管道、历史管理")
    print("\n注意：需要 Ollama 服务运行（Low/Medium Risk）")
    print("=" * 80)
    
    await test_low_risk_pipeline()
    await test_medium_risk_pipeline()
    await test_high_risk_pipeline()
    await test_conversation_history()
    await test_clear_conversation()
    
    print("\n" + "=" * 80)
    print("集成测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

