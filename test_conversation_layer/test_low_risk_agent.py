"""
Test LowRiskAgent functionality.

Tests free chat with coping skills suggestions.
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
from src_new.shared.models import ConversationTurn


async def test_low_risk_basic():
    """Test basic Low Risk Agent response."""
    print("\n" + "=" * 80)
    print("测试 1: Low Risk Agent 基本响应")
    print("=" * 80)
    
    agent = LowRiskAgent()
    
    user_message = "I've been feeling a bit stressed lately with school."
    
    result = await agent.generate_response(
        user_message=user_message,
        conversation_history=None,
        rigid_score=0.2
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   响应: {result.get('response', 'N/A')[:200]}...")
    print(f"   Agent: {result.get('agent')}")
    print(f"   温度: {result.get('temperature', 'N/A')}")
    print(f"   建议应对技能: {result.get('coping_skills_suggested', False)}")
    print(f"   ✅ 基本响应测试完成")


async def test_low_risk_with_history():
    """Test Low Risk Agent with conversation history."""
    print("\n" + "=" * 80)
    print("测试 2: Low Risk Agent 带历史记录")
    print("=" * 80)
    
    agent = LowRiskAgent()
    
    history = [
        ConversationTurn(role="user", text="I'm feeling anxious about exams."),
        ConversationTurn(role="bot", text="I understand. Exam stress is common. What helps you relax?"),
        ConversationTurn(role="user", text="I like listening to music.")
    ]
    
    user_message = "But sometimes even that doesn't help."
    
    result = await agent.generate_response(
        user_message=user_message,
        conversation_history=history,
        rigid_score=0.2
    )
    
    print(f"   历史记录: {len(history)} 轮对话")
    print(f"   用户消息: {user_message}")
    print(f"   响应: {result.get('response', 'N/A')[:200]}...")
    print(f"   ✅ 历史记录测试完成")


def test_goodbye_detection():
    """Test goodbye detection."""
    print("\n" + "=" * 80)
    print("测试 3: Goodbye 检测")
    print("=" * 80)
    
    agent = LowRiskAgent()
    
    test_cases = [
        ("Thanks for your help!", True),
        ("I have to go now", True),
        ("Goodbye", True),
        ("See you later", True),
        ("I'm feeling better", False),
        ("Can you help me?", False),
    ]
    
    for message, expected in test_cases:
        result = agent.is_goodbye(message)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{message}': 预期={expected}, 实际={result}")


async def test_rigidity_adjustment():
    """Test temperature adjustment based on rigidity."""
    print("\n" + "=" * 80)
    print("测试 4: 基于 Rigidity 的温度调整")
    print("=" * 80)
    
    agent = LowRiskAgent()
    
    test_cases = [
        (0.0, 0.9),  # No rigidity -> high temperature
        (0.2, 0.74),  # Low rigidity -> slightly reduced
        (0.5, 0.5),  # Medium rigidity -> medium temperature
        (0.8, 0.26),  # High rigidity -> low temperature
    ]
    
    for rigid_score, expected_min_temp in test_cases:
        result = await agent.generate_response(
            user_message="Test message",
            conversation_history=None,
            rigid_score=rigid_score
        )
        actual_temp = result.get("temperature", 0.0)
        status = "✅" if actual_temp >= expected_min_temp else "❌"
        print(f"   {status} Rigidity={rigid_score:.1f}: 温度={actual_temp:.2f} (预期>={expected_min_temp:.2f})")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("LowRiskAgent 测试")
    print("=" * 80)
    print("\n此脚本将测试 Low Risk Agent")
    print("包括：基本响应、历史记录、Goodbye 检测、温度调整")
    print("\n注意：需要 Ollama 服务运行")
    print("=" * 80)
    
    await test_low_risk_basic()
    await test_low_risk_with_history()
    test_goodbye_detection()
    await test_rigidity_adjustment()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

