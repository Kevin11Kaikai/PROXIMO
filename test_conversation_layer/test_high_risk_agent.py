"""
Test HighRiskAgent functionality.

Tests fixed script for crisis intervention.
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

from src_new.conversation.agents.high_risk_agent import (
    HighRiskAgent,
    FIXED_SAFETY_SCRIPT,
    SAFETY_BANNER
)


async def test_fixed_script():
    """Test fixed safety script."""
    print("\n" + "=" * 80)
    print("测试 1: 固定安全脚本")
    print("=" * 80)
    
    agent = HighRiskAgent()
    
    # Test with different user messages (should all return same script)
    test_messages = [
        "I want to kill myself",
        "I'm feeling better now",
        "Can you help me?",
    ]
    
    for user_message in test_messages:
        result = await agent.generate_response(
            user_message=user_message,
            conversation_history=None,
            rigid_score=1.0
        )
        
        assert result.get("response") == FIXED_SAFETY_SCRIPT, "Response should match fixed script"
        assert result.get("safety_banner") == SAFETY_BANNER, "Should include safety banner"
        assert result.get("fixed_script") is True, "Should flag as fixed script"
        
        print(f"   用户消息: {user_message}")
        print(f"   响应匹配: ✅")
        print(f"   安全横幅: ✅")
        print(f"   固定脚本标志: ✅")
    
    print(f"   ✅ 固定脚本测试完成")


def test_script_content():
    """Test script content requirements."""
    print("\n" + "=" * 80)
    print("测试 2: 脚本内容要求")
    print("=" * 80)
    
    required_elements = [
        "988",
        "crisis",
        "safety",
        "emergency",
        "help"
    ]
    
    script_lower = FIXED_SAFETY_SCRIPT.lower()
    
    for element in required_elements:
        found = element in script_lower
        status = "✅" if found else "❌"
        print(f"   {status} 包含 '{element}': {found}")
    
    print(f"   ✅ 脚本内容测试完成")


async def test_metadata():
    """Test response metadata."""
    print("\n" + "=" * 80)
    print("测试 3: 响应元数据")
    print("=" * 80)
    
    agent = HighRiskAgent()
    
    result = await agent.generate_response(
        user_message="Test",
        conversation_history=None,
        rigid_score=1.0
    )
    
    assert result.get("agent") == "high_risk"
    assert result.get("structured") is True
    assert result.get("safety_priority") is True
    assert result.get("crisis_hotline") == "988"
    assert result.get("urgent_meeting_suggested") is True
    
    print(f"   Agent: {result.get('agent')}")
    print(f"   结构化: {result.get('structured')}")
    print(f"   安全优先级: {result.get('safety_priority')}")
    print(f"   危机热线: {result.get('crisis_hotline')}")
    print(f"   建议紧急会面: {result.get('urgent_meeting_suggested')}")
    print(f"   ✅ 元数据测试完成")


def test_get_script():
    """Test get_script method."""
    print("\n" + "=" * 80)
    print("测试 4: get_script 方法")
    print("=" * 80)
    
    agent = HighRiskAgent()
    script = agent.get_script()
    
    assert script == FIXED_SAFETY_SCRIPT
    
    print(f"   脚本长度: {len(script)} 字符")
    print(f"   脚本匹配: ✅")
    print(f"   ✅ get_script 测试完成")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("HighRiskAgent 测试")
    print("=" * 80)
    print("\n此脚本将测试 High Risk Agent")
    print("包括：固定脚本、脚本内容、元数据")
    print("=" * 80)
    
    await test_fixed_script()
    test_script_content()
    await test_metadata()
    test_get_script()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

