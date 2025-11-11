"""
Test route transitions (Low → Medium, Medium → High).

Additional integration test for route upgrade scenarios.
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

from src_new.perception.psyguard_service import get_psyguard_service
from src_new.control.route_updater import RouteUpdater
from src_new.control.control_context import ControlContext
from src_new.conversation.pipeline import ConversationPipeline
from src_new.adaptive.history_service import HistoryService


async def test_low_to_medium_transition():
    """Test Low → Medium route transition."""
    print("=" * 80)
    print("测试: Low → Medium 路由转换")
    print("=" * 80)
    
    psyguard_service = get_psyguard_service()
    updater = RouteUpdater()
    pipeline = ConversationPipeline()
    history_service = HistoryService()
    
    user_id = "test_user_transition_lm"
    
    # Start with Low Risk
    context = ControlContext(
        user_id=user_id,
        route="low",
        rigid_score=0.2,
        psyguard_score=0.3
    )
    
    print("\n[初始状态] Low Risk")
    print(f"路由: {context.route}")
    print(f"PsyGUARD 分数: {context.psyguard_score}")
    
    # User message with increased risk
    user_message = "I'm feeling really anxious and isolated. I don't know what to do."
    print(f"\n用户: {user_message}")
    
    # PsyGUARD detects medium risk
    psyguard_result = await psyguard_service.score(user_message)
    new_psyguard_score = psyguard_result.get("risk_score", 0.0)
    print(f"新 PsyGUARD 分数: {new_psyguard_score:.3f}")
    
    # Check if should upgrade
    if updater.should_upgrade(context.route, new_psyguard_score):
        new_route = updater.get_upgrade_target(context.route, new_psyguard_score)
        context.update_route(new_route, reason="psyguard_upgrade")
        context.psyguard_score = new_psyguard_score
        print(f"\n✅ 路由升级: {context.route}")
        print(f"原因: {context.route_reason}")
        
        # Collect feedback at transition
        feedback = history_service.collect_feedback(
            user_id=user_id,
            conversation_id="conv_transition_lm",
            route="low",  # Previous route
            satisfaction=3,
            acceptance="partially"
        )
        print(f"转换反馈收集: satisfaction={feedback.satisfaction}")
    else:
        print(f"\n路由保持不变: {context.route}")
    
    print("\n" + "=" * 80)


async def test_medium_to_high_transition():
    """Test Medium → High route transition."""
    print("=" * 80)
    print("测试: Medium → High 路由转换")
    print("=" * 80)
    
    psyguard_service = get_psyguard_service()
    updater = RouteUpdater()
    pipeline = ConversationPipeline()
    history_service = HistoryService()
    
    user_id = "test_user_transition_mh"
    
    # Start with Medium Risk
    context = ControlContext(
        user_id=user_id,
        route="medium",
        rigid_score=0.6,
        psyguard_score=0.75
    )
    
    print("\n[初始状态] Medium Risk")
    print(f"路由: {context.route}")
    print(f"PsyGUARD 分数: {context.psyguard_score}")
    
    # User message with high risk
    user_message = "I'm thinking about ending my life. I don't see any point in living."
    print(f"\n用户: {user_message}")
    
    # PsyGUARD detects high risk
    psyguard_result = await psyguard_service.score(user_message)
    new_psyguard_score = psyguard_result.get("risk_score", 0.0)
    print(f"新 PsyGUARD 分数: {new_psyguard_score:.3f}")
    
    # Check if should upgrade
    if updater.should_upgrade(context.route, new_psyguard_score):
        new_route = updater.get_upgrade_target(context.route, new_psyguard_score)
        context.update_route(new_route, reason="psyguard_upgrade")
        context.psyguard_score = new_psyguard_score
        print(f"\n✅ 路由升级: {context.route}")
        print(f"原因: {context.route_reason}")
        
        # Collect feedback at transition
        feedback = history_service.collect_feedback(
            user_id=user_id,
            conversation_id="conv_transition_mh",
            route="medium",  # Previous route
            satisfaction=2,
            acceptance="rejected"
        )
        print(f"转换反馈收集: satisfaction={feedback.satisfaction}")
    else:
        print(f"\n路由保持不变: {context.route}")
    
    print("\n" + "=" * 80)


async def test_no_downgrade():
    """Test that routes don't downgrade."""
    print("=" * 80)
    print("测试: 路由不降级")
    print("=" * 80)
    
    updater = RouteUpdater()
    
    # Medium Risk with low PsyGUARD score (should not downgrade)
    context_medium = ControlContext(
        user_id="test_user_no_downgrade",
        route="medium",
        rigid_score=0.6,
        psyguard_score=0.3  # Low score
    )
    
    new_route = updater.update_route(context_medium.route, 0.3)
    print(f"Medium Risk (PsyGUARD=0.3): {new_route}")
    assert new_route == "medium", "Medium Risk should not downgrade"
    print("✅ Medium Risk 不降级")
    
    # High Risk with low PsyGUARD score (should not downgrade)
    context_high = ControlContext(
        user_id="test_user_no_downgrade",
        route="high",
        rigid_score=1.0,
        psyguard_score=0.2  # Very low score
    )
    
    new_route = updater.update_route(context_high.route, 0.2)
    print(f"High Risk (PsyGUARD=0.2): {new_route}")
    assert new_route == "high", "High Risk should not downgrade"
    print("✅ High Risk 不降级")
    
    print("\n" + "=" * 80)


async def main():
    """Run route transition tests."""
    try:
        await test_low_to_medium_transition()
        await test_medium_to_high_transition()
        await test_no_downgrade()
        
        print("\n" + "=" * 80)
        print("✅ 所有路由转换测试完成")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

