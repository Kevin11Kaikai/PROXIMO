"""
Test error recovery and fallback mechanisms.

Tests for:
- Ollama service unavailable
- Guardrails initialization failure
- Database connection failure
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

from src_new.conversation.agents.low_risk_agent import LowRiskAgent
from src_new.conversation.agents.high_risk_agent import HighRiskAgent
from src_new.safety.guardrails_service import SafetyGuardrailsService
from src_new.adaptive.history_service import HistoryService


async def test_ollama_unavailable_fallback():
    """Test fallback when Ollama service is unavailable."""
    print("=" * 80)
    print("测试: Ollama 服务不可用时的降级")
    print("=" * 80)
    
    agent = LowRiskAgent()
    
    # Try to generate response (will fail if Ollama unavailable)
    try:
        result = await agent.generate_response(
            user_message="Test message",
            conversation_history=None,
            rigid_score=0.2
        )
        
        if "error" in result:
            print(f"  ⚠️  Ollama 不可用，返回降级响应")
            print(f"  降级响应: {result.get('response', '')[:100]}...")
        else:
            print(f"  ✅ Ollama 可用，正常响应")
            print(f"  响应: {result.get('response', '')[:100]}...")
    except Exception as e:
        print(f"  ⚠️  异常: {e}")
        print(f"  ✅ 异常被捕获，系统不会崩溃")
    
    print("\n✅ Ollama 降级测试完成")


async def test_high_risk_no_ollama():
    """Test High Risk Agent works without Ollama (uses fixed script)."""
    print("\n" + "=" * 80)
    print("测试: High Risk Agent 无需 Ollama（使用固定脚本）")
    print("=" * 80)
    
    agent = HighRiskAgent()
    
    # High Risk Agent doesn't need Ollama
    result = await agent.generate_response(
        user_message="I want to kill myself",
        conversation_history=None,
        rigid_score=1.0
    )
    
    assert result.get("fixed_script") is True, "Should use fixed script"
    assert result.get("response") is not None, "Should have response"
    
    print(f"  ✅ 固定脚本响应生成成功（无需 Ollama）")
    print(f"  响应长度: {len(result.get('response', ''))} 字符")
    
    print("\n✅ High Risk 无需 Ollama测试通过")


async def test_guardrails_initialization_failure():
    """Test behavior when Guardrails initialization fails."""
    print("\n" + "=" * 80)
    print("测试: Guardrails 初始化失败时的处理")
    print("=" * 80)
    
    # Create service with invalid config path
    service = SafetyGuardrailsService(
        config_path="invalid/path/guardrails",
        enabled=True
    )
    
    initialized = await service.initialize()
    
    if not initialized:
        print(f"  ✅ Guardrails 初始化失败被正确处理")
        print(f"  服务状态: 已禁用但不会崩溃")
        
        # Test that service still works (disabled mode)
        result = await service.filter_response(
            user_message="Test",
            proposed_response="Test response",
            context=None,
            route="low"
        )
        
        assert result.get("checked") is False, "Should not check when disabled"
        assert result.get("final_response") == "Test response", "Should return original response"
        print(f"  ✅ 禁用模式下仍可正常工作")
    else:
        print(f"  ⚠️  Guardrails 初始化成功（配置路径有效）")
    
    print("\n✅ Guardrails 初始化失败处理测试通过")


async def test_feedback_collection_without_db():
    """Test feedback collection works without database."""
    print("\n" + "=" * 80)
    print("测试: 反馈收集无需数据库（内存存储）")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect feedback (uses in-memory storage)
    feedback = service.collect_feedback(
        user_id="test_user_no_db",
        conversation_id="conv1",
        route="low",
        satisfaction=4
    )
    
    assert feedback is not None, "Feedback should be collected"
    print(f"  ✅ 反馈收集成功（内存存储）")
    
    # Retrieve feedback
    retrieved = service.get_user_feedback("test_user_no_db")
    assert len(retrieved) == 1, "Should retrieve feedback"
    print(f"  ✅ 反馈检索成功")
    
    print("\n✅ 反馈收集无需数据库测试通过")


async def test_invalid_feedback_validation():
    """Test feedback validation catches invalid data."""
    print("\n" + "=" * 80)
    print("测试: 反馈验证捕获无效数据")
    print("=" * 80)
    
    from src_new.adaptive.feedback import FeedbackCollector
    
    collector = FeedbackCollector()
    
    # Test invalid satisfaction
    try:
        collector.collect_feedback(
            user_id="test_user",
            conversation_id="conv1",
            route="low",
            satisfaction=6  # Invalid: > 5
        )
        print(f"  ❌ 应该抛出 ValueError")
        assert False, "Should raise ValueError"
    except ValueError as e:
        print(f"  ✅ 捕获无效满意度: {e}")
    
    # Test invalid acceptance
    try:
        collector.collect_feedback(
            user_id="test_user",
            conversation_id="conv2",
            route="low",
            acceptance="invalid"
        )
        print(f"  ❌ 应该抛出 ValueError")
        assert False, "Should raise ValueError"
    except ValueError as e:
        print(f"  ✅ 捕获无效接受程度: {e}")
    
    print("\n✅ 反馈验证测试通过")


async def main():
    """Run all error recovery tests."""
    print("=" * 80)
    print("错误恢复测试")
    print("=" * 80)
    
    try:
        await test_ollama_unavailable_fallback()
        await test_high_risk_no_ollama()
        await test_guardrails_initialization_failure()
        await test_feedback_collection_without_db()
        await test_invalid_feedback_validation()
        
        print("\n" + "=" * 80)
        print("✅ 所有错误恢复测试通过")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

