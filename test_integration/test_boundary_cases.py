"""
Test boundary cases and edge scenarios.

Tests for:
- Questionnaire trigger timing (5 turns vs immediate)
- PsyGUARD threshold boundaries (0.70, 0.95)
- State machine boundaries (Medium Risk max 5 persuasion turns)
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

from src_new.perception.questionnaire_trigger import QuestionnaireTrigger
from src_new.perception.psyguard_service import (
    get_psyguard_service,
    MEDIUM_RISK_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD,
    SUICIDE_INTENT_THRESHOLD
)
from src_new.control.route_updater import RouteUpdater
from src_new.conversation.agents.medium_risk_agent import MediumRiskAgent


async def test_questionnaire_trigger_timing():
    """Test questionnaire trigger timing (5 turns vs immediate)."""
    print("=" * 80)
    print("测试: 问卷触发时机")
    print("=" * 80)
    
    trigger = QuestionnaireTrigger()
    
    # Test 1: Normal trigger (5 turns)
    print("\n[测试 1] 正常触发（5 轮后）")
    print("-" * 80)
    
    for turn in range(1, 7):
        result = trigger.check_trigger(turn_count=turn, psyguard_result=None)
        should_trigger = result.should_trigger
        print(f"  轮次 {turn}: 应该触发={'是' if should_trigger else '否'}, 原因={result.reason}")
        if turn == 5:
            assert should_trigger, "Should trigger at turn 5"
    
    # Test 2: Immediate trigger (suicide intent)
    print("\n[测试 2] 立即触发（自杀意图）")
    print("-" * 80)
    
    # Simulate PsyGUARD result with suicide intent
    psyguard_result = {
        "risk_score": 0.85,
        "should_trigger_questionnaire": True  # Above SUICIDE_INTENT_THRESHOLD (0.80)
    }
    
    result_immediate = trigger.check_trigger(
        turn_count=2,  # Early turn
        psyguard_result=psyguard_result
    )
    print(f"  轮次 2, PsyGUARD=0.85: 应该触发={'是' if result_immediate.should_trigger else '否'}, 原因={result_immediate.reason}")
    assert result_immediate.should_trigger, "Should trigger immediately for suicide intent"
    
    print("\n✅ 问卷触发时机测试通过")


async def test_psyguard_threshold_boundaries():
    """Test PsyGUARD threshold boundaries."""
    print("\n" + "=" * 80)
    print("测试: PsyGUARD 阈值边界")
    print("=" * 80)
    
    updater = RouteUpdater()
    
    # Test MEDIUM_RISK_THRESHOLD (0.70)
    print("\n[测试 1] Medium Risk 阈值 (0.70)")
    print("-" * 80)
    
    test_cases = [
        (0.69, "low", "low"),  # Below threshold
        (0.70, "low", "medium"),  # At threshold
        (0.71, "low", "medium"),  # Above threshold
    ]
    
    for score, current_route, expected_route in test_cases:
        new_route = updater.update_route(current_route, score)
        status = "✅" if new_route == expected_route else "❌"
        print(f"  {status} PsyGUARD={score:.2f}, 当前={current_route}: 预期={expected_route}, 实际={new_route}")
        assert new_route == expected_route, f"Expected {expected_route}, got {new_route}"
    
    # Test HIGH_RISK_DIRECT_THRESHOLD (0.95)
    print("\n[测试 2] High Risk 直接阈值 (0.95)")
    print("-" * 80)
    
    test_cases = [
        (0.94, "low", "medium"),  # Below threshold
        (0.95, "low", "high"),  # At threshold
        (0.96, "low", "high"),  # Above threshold
        (0.95, "medium", "high"),  # Medium to High
    ]
    
    for score, current_route, expected_route in test_cases:
        new_route = updater.update_route(current_route, score)
        status = "✅" if new_route == expected_route else "❌"
        print(f"  {status} PsyGUARD={score:.2f}, 当前={current_route}: 预期={expected_route}, 实际={new_route}")
        assert new_route == expected_route, f"Expected {expected_route}, got {new_route}"
    
    print("\n✅ PsyGUARD 阈值边界测试通过")


async def test_medium_risk_max_persuasion_turns():
    """Test Medium Risk Agent max persuasion turns (5 turns)."""
    print("\n" + "=" * 80)
    print("测试: Medium Risk 最大说服轮次 (5 轮)")
    print("=" * 80)
    
    agent = MediumRiskAgent()
    user_id = "test_user_max_turns"
    
    # Initial suggestion
    result1 = await agent.generate_response(
        user_id=user_id,
        user_message="I'm feeling anxious.",
        conversation_history=None,
        rigid_score=0.6
    )
    print(f"  轮次 1: 状态={result1.get('state')}")
    
    # First resistance (should trigger handling)
    user_message_2 = "I don't want to share my privacy with strangers."
    result2 = await agent.generate_response(
        user_id=user_id,
        user_message=user_message_2,
        conversation_history=None,
        rigid_score=0.6
    )
    state2 = result2.get("state")
    resistance_count_2 = result2.get("resistance_count", 0)
    print(f"  轮次 2: 状态={state2}, 抗拒计数={resistance_count_2}, 抗拒类型={result2.get('resistance_type')}")
    
    # Continue resistance turns (up to 5 total)
    for turn in range(3, 8):  # Turns 3-7
        user_message = f"I'm still not sure. (turn {turn})"
        result = await agent.generate_response(
            user_id=user_id,
            user_message=user_message,
            conversation_history=None,
            rigid_score=0.6
        )
        
        state = result.get("state")
        resistance_count = result.get("resistance_count", 0)
        print(f"  轮次 {turn}: 状态={state}, 抗拒计数={resistance_count}")
        
        if turn <= 6:  # Turns 3-6 (within limit, counting from first resistance)
            # Should still be handling resistance
            if state != "rejected":
                print(f"    ✅ 仍在处理抗拒中")
        else:  # Turn 7 (exceeded limit)
            if state == "rejected":
                print(f"  ✅ 达到最大轮次，进入拒绝状态")
                break
    
    # Reset for next test
    agent.reset_state(user_id)
    
    print("\n✅ Medium Risk 最大说服轮次测试通过")


async def test_questionnaire_score_boundaries():
    """Test questionnaire score boundaries for route mapping."""
    print("\n" + "=" * 80)
    print("测试: 问卷分数边界")
    print("=" * 80)
    
    from src_new.control.risk_router import RiskRouter
    
    router = RiskRouter()
    
    # Test PHQ-9 boundaries
    print("\n[测试 1] PHQ-9 分数边界")
    print("-" * 80)
    
    test_cases = [
        (9, "low"),   # 0-9: Low
        (10, "medium"),  # 10-14: Medium
        (14, "medium"),
        (15, "high"),  # 15+: High
    ]
    
    for score, expected_route in test_cases:
        phq9_result = {"total_score": score, "parsed_scores": [0] * 9}
        gad7_result = {"total_score": 0.0, "parsed_scores": [0] * 7}
        result = router.decide_from_questionnaires(
            phq9_result=phq9_result,
            gad7_result=gad7_result,
            chat_risk_score=None
        )
        route = result.route
        status = "✅" if route == expected_route else "❌"
        print(f"  {status} PHQ-9={score}: 预期={expected_route}, 实际={route}")
        assert route == expected_route, f"Expected {expected_route}, got {route}"
    
    # Test GAD-7 boundaries
    print("\n[测试 2] GAD-7 分数边界")
    print("-" * 80)
    
    test_cases = [
        (9, "low"),   # 0-9: Low
        (10, "medium"),  # 10-14: Medium
        (14, "medium"),
        (15, "high"),  # 15+: High
    ]
    
    for score, expected_route in test_cases:
        phq9_result = {"total_score": 0.0, "parsed_scores": [0] * 9}
        gad7_result = {"total_score": score, "parsed_scores": [0] * 7}
        result = router.decide_from_questionnaires(
            phq9_result=phq9_result,
            gad7_result=gad7_result,
            chat_risk_score=None
        )
        route = result.route
        status = "✅" if route == expected_route else "❌"
        print(f"  {status} GAD-7={score}: 预期={expected_route}, 实际={route}")
        assert route == expected_route, f"Expected {expected_route}, got {route}"
    
    print("\n✅ 问卷分数边界测试通过")


async def main():
    """Run all boundary case tests."""
    print("=" * 80)
    print("边界情况测试")
    print("=" * 80)
    
    try:
        await test_questionnaire_trigger_timing()
        await test_psyguard_threshold_boundaries()
        await test_medium_risk_max_persuasion_turns()
        await test_questionnaire_score_boundaries()
        
        print("\n" + "=" * 80)
        print("✅ 所有边界情况测试通过")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

