"""
Test questionnaire trigger logic.

Tests the logic for triggering questionnaires based on turn count and PsyGUARD scores.
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

from src_new.perception.questionnaire_trigger import QuestionnaireTrigger, QuestionnaireTriggerResult
from src_new.perception.psyguard_service import (
    SUICIDE_INTENT_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD
)


async def test_turn_count_trigger():
    """Test default trigger after turn threshold."""
    print("\n" + "=" * 80)
    print("测试 1: 轮次计数触发")
    print("=" * 80)
    
    trigger = QuestionnaireTrigger(turn_threshold=5)
    
    test_cases = [
        {"turn_count": 1, "should_trigger": False},
        {"turn_count": 4, "should_trigger": False},
        {"turn_count": 5, "should_trigger": True},
        {"turn_count": 6, "should_trigger": True},
        {"turn_count": 10, "should_trigger": True},
    ]
    
    for test_case in test_cases:
        result = trigger.check_trigger(test_case["turn_count"])
        expected = test_case["should_trigger"]
        actual = result.should_trigger
        
        status = "✅" if actual == expected else "❌"
        print(f"   {status} 轮次 {test_case['turn_count']}: 预期={expected}, 实际={actual}, 原因={result.reason}")


async def test_suicide_intent_trigger():
    """Test early trigger on suicide intent detection."""
    print("\n" + "=" * 80)
    print("测试 2: 自杀意图提前触发")
    print("=" * 80)
    
    trigger = QuestionnaireTrigger(turn_threshold=5)
    
    # 测试自杀意图检测（但未达到直接高风险）
    psyguard_result = {
        "risk_score": SUICIDE_INTENT_THRESHOLD + 0.05,  # 0.85
        "should_trigger_questionnaire": True,
        "should_direct_high_risk": False
    }
    
    result = trigger.check_trigger(turn_count=2, psyguard_result=psyguard_result)
    
    assert result.should_trigger, "应该触发问卷"
    assert result.reason == "suicide_intent", f"原因应该是 'suicide_intent'，实际是 '{result.reason}'"
    assert result.immediate_route is None, "不应该直接设置路由"
    
    print(f"   ✅ 轮次 2 检测到自杀意图，正确触发问卷")
    print(f"      原因: {result.reason}")


async def test_high_risk_direct_trigger():
    """Test direct high risk trigger."""
    print("\n" + "=" * 80)
    print("测试 3: 直接高风险触发")
    print("=" * 80)
    
    trigger = QuestionnaireTrigger(turn_threshold=5)
    
    # 测试极高风险（直接 High Risk）
    psyguard_result = {
        "risk_score": HIGH_RISK_DIRECT_THRESHOLD + 0.02,  # 0.97
        "should_trigger_questionnaire": True,
        "should_direct_high_risk": True
    }
    
    result = trigger.check_trigger(turn_count=1, psyguard_result=psyguard_result)
    
    assert result.should_trigger, "应该触发问卷"
    assert result.reason == "high_risk_direct", f"原因应该是 'high_risk_direct'，实际是 '{result.reason}'"
    assert result.immediate_route == "high", "应该直接设置为 High Risk"
    
    print(f"   ✅ 轮次 1 检测到极高风险，正确触发问卷并设置 High Risk")
    print(f"      原因: {result.reason}")
    print(f"      立即路由: {result.immediate_route}")


async def test_priority_order():
    """Test trigger priority order."""
    print("\n" + "=" * 80)
    print("测试 4: 触发优先级顺序")
    print("=" * 80)
    
    trigger = QuestionnaireTrigger(turn_threshold=5)
    
    # 优先级：high_risk_direct > suicide_intent > turn_count
    
    # 测试 1: 即使轮次未到，极高风险应该触发
    psyguard_high = {
        "risk_score": HIGH_RISK_DIRECT_THRESHOLD + 0.01,
        "should_trigger_questionnaire": True,
        "should_direct_high_risk": True
    }
    result1 = trigger.check_trigger(turn_count=1, psyguard_result=psyguard_high)
    assert result1.reason == "high_risk_direct", "极高风险应该优先"
    print("   ✅ 极高风险优先级最高（轮次 1 即触发）")
    
    # 测试 2: 自杀意图应该优先于轮次计数
    psyguard_suicide = {
        "risk_score": SUICIDE_INTENT_THRESHOLD + 0.01,
        "should_trigger_questionnaire": True,
        "should_direct_high_risk": False
    }
    result2 = trigger.check_trigger(turn_count=2, psyguard_result=psyguard_suicide)
    assert result2.reason == "suicide_intent", "自杀意图应该优先于轮次计数"
    print("   ✅ 自杀意图优先级高于轮次计数（轮次 2 即触发）")
    
    # 测试 3: 轮次计数作为默认触发
    result3 = trigger.check_trigger(turn_count=5, psyguard_result=None)
    assert result3.reason == "turn_count", "轮次计数应该作为默认触发"
    print("   ✅ 轮次计数作为默认触发（轮次 5 触发）")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("Questionnaire Trigger 测试")
    print("=" * 80)
    print("\n此脚本将测试问卷触发逻辑")
    print("包括：轮次计数、自杀意图检测、极高风险检测")
    print("=" * 80)
    
    await test_turn_count_trigger()
    await test_suicide_intent_trigger()
    await test_high_risk_direct_trigger()
    await test_priority_order()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

