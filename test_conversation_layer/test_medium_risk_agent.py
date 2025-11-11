"""
Test MediumRiskAgent functionality.

Tests state machine for peer support group guidance.
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

from src_new.conversation.agents.medium_risk_agent import (
    MediumRiskAgent,
    MediumRiskState
)
from src_new.shared.models import ConversationTurn


async def test_initial_suggestion():
    """Test initial peer group suggestion."""
    print("\n" + "=" * 80)
    print("测试 1: 初始建议")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_1"
    
    user_message = "I've been feeling really anxious and isolated."
    
    result = await agent.generate_response(
        user_id=user_id,
        user_message=user_message,
        conversation_history=None,
        rigid_score=0.6
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   响应: {result.get('response', 'N/A')[:200]}...")
    print(f"   状态: {result.get('state')}")
    print(f"   ✅ 初始建议测试完成")


async def test_resistance_detection():
    """Test resistance detection."""
    print("\n" + "=" * 80)
    print("测试 2: 抗拒检测")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_2"
    
    # Initial suggestion
    await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling anxious.",
        conversation_history=None,
        rigid_score=0.6
    )
    
    # User expresses privacy concern
    user_message = "I don't want to share my personal information with strangers."
    
    result = await agent.generate_response(
        user_id=user_id,
        user_message=user_message,
        conversation_history=None,
        rigid_score=0.6
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   响应: {result.get('response', 'N/A')[:200]}...")
    print(f"   状态: {result.get('state')}")
    print(f"   抗拒类型: {result.get('resistance_type')}")
    print(f"   抗拒计数: {result.get('resistance_count')}")
    print(f"   ✅ 抗拒检测测试完成")


async def test_resistance_handling():
    """Test resistance handling with multiple turns."""
    print("\n" + "=" * 80)
    print("测试 3: 抗拒处理（多轮）")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_3"
    
    # Simulate conversation
    history = []
    
    # Turn 1: Initial
    result1 = await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling down.",
        conversation_history=history,
        rigid_score=0.6
    )
    history.append(ConversationTurn(role="user", text="I'm feeling down."))
    history.append(ConversationTurn(role="bot", text=result1.get("response", "")))
    
    # Turn 2: Privacy resistance
    result2 = await agent.generate_response(
        user_id=user_id,
        user_message="I don't want to share my privacy.",
        conversation_history=history,
        rigid_score=0.6
    )
    history.append(ConversationTurn(role="user", text="I don't want to share my privacy."))
    history.append(ConversationTurn(role="bot", text=result2.get("response", "")))
    
    print(f"   轮次 1: 状态={result1.get('state')}")
    print(f"   轮次 2: 状态={result2.get('state')}, 抗拒类型={result2.get('resistance_type')}")
    print(f"   ✅ 抗拒处理测试完成")


async def test_acceptance():
    """Test user acceptance."""
    print("\n" + "=" * 80)
    print("测试 4: 用户接受")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_4"
    
    # Initial suggestion
    await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling anxious.",
        conversation_history=None,
        rigid_score=0.6
    )
    
    # User accepts
    user_message = "Yes, I'd like to join the peer support group."
    
    result = await agent.generate_response(
        user_id=user_id,
        user_message=user_message,
        conversation_history=None,
        rigid_score=0.6
    )
    
    print(f"   用户消息: {user_message}")
    print(f"   响应: {result.get('response', 'N/A')[:200]}...")
    print(f"   状态: {result.get('state')}")
    print(f"   接受: {result.get('peer_group_accepted', False)}")
    print(f"   ✅ 接受测试完成")


async def test_max_persuasion_turns():
    """Test max persuasion turns limit."""
    print("\n" + "=" * 80)
    print("测试 5: 最大说服轮次限制")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_5"
    
    history = []
    
    # Initial suggestion
    result = await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling anxious.",
        conversation_history=history,
        rigid_score=0.6
    )
    history.append(ConversationTurn(role="user", text="I'm feeling anxious."))
    history.append(ConversationTurn(role="bot", text=result.get("response", "")))
    
    # Simulate 6 resistance turns (exceeding max of 5)
    for i in range(6):
        user_message = f"I don't want to join. (turn {i+1})"
        result = await agent.generate_response(
            user_id=user_id,
            user_message=user_message,
            conversation_history=history,
            rigid_score=0.6
        )
        history.append(ConversationTurn(role="user", text=user_message))
        history.append(ConversationTurn(role="bot", text=result.get("response", "")))
        
        print(f"   轮次 {i+1}: 状态={result.get('state')}, 抗拒计数={result.get('resistance_count')}")
        
        if result.get("state") == "rejected":
            print(f"   ✅ 达到最大轮次，进入拒绝状态")
            break


async def test_reset_state():
    """Test state reset."""
    print("\n" + "=" * 80)
    print("测试 6: 状态重置")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_6"
    
    # Create some state
    await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling anxious.",
        conversation_history=None,
        rigid_score=0.6
    )
    
    # Reset
    agent.reset_state(user_id)
    
    # New conversation should start fresh
    result = await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling better now.",
        conversation_history=None,
        rigid_score=0.6
    )
    
    print(f"   重置后状态: {result.get('state')}")
    print(f"   ✅ 状态重置测试完成")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("MediumRiskAgent 测试")
    print("=" * 80)
    print("\n此脚本将测试 Medium Risk Agent 状态机")
    print("包括：初始建议、抗拒检测、抗拒处理、接受、最大轮次限制")
    print("\n注意：需要 Ollama 服务运行")
    print("=" * 80)
    
    await test_initial_suggestion()
    await test_resistance_detection()
    await test_resistance_handling()
    await test_acceptance()
    await test_max_persuasion_turns()
    await test_reset_state()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

