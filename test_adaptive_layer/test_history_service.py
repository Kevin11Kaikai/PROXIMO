"""
Test HistoryService functionality.

Tests history service for adaptive learning.
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

from src_new.adaptive.history_service import HistoryService
from src_new.adaptive.feedback import AcceptanceLevel, FollowUpBehavior


async def test_get_user_history():
    """Test getting user assessment history."""
    print("\n" + "=" * 80)
    print("测试 1: 获取用户评估历史")
    print("=" * 80)
    
    service = HistoryService()
    
    # Get history for a user (may be empty if no assessments)
    history = await service.get_user_history("test_user", limit=10)
    
    print(f"   ✅ 获取历史成功")
    print(f"      历史记录数: {len(history)}")
    if history:
        print(f"      最新记录: {history[0]}")


async def test_get_user_feedback():
    """Test getting user feedback."""
    print("\n" + "=" * 80)
    print("测试 2: 获取用户反馈")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect some feedback
    service.collect_feedback(
        user_id="test_user_feedback",
        conversation_id="conv1",
        route="low",
        satisfaction=4,
        acceptance=AcceptanceLevel.ACCEPTED.value
    )
    
    # Get feedback
    feedback = service.get_user_feedback("test_user_feedback")
    
    print(f"   ✅ 获取反馈成功")
    print(f"      反馈数: {len(feedback)}")
    if feedback:
        print(f"      最新反馈: route={feedback[0].route}, satisfaction={feedback[0].satisfaction}")


async def test_get_complete_history():
    """Test getting complete history (assessments + feedback)."""
    print("\n" + "=" * 80)
    print("测试 3: 获取完整历史")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect feedback
    service.collect_feedback(
        user_id="test_user_complete",
        conversation_id="conv1",
        route="low",
        satisfaction=4
    )
    
    # Get complete history
    complete = await service.get_user_complete_history("test_user_complete")
    
    print(f"   ✅ 获取完整历史成功")
    print(f"      用户ID: {complete['user_id']}")
    print(f"      评估数: {complete['total_assessments']}")
    print(f"      反馈数: {complete['total_feedback']}")


async def test_collect_feedback():
    """Test collecting feedback through service."""
    print("\n" + "=" * 80)
    print("测试 4: 通过服务收集反馈")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect Low Risk feedback
    feedback1 = service.collect_feedback(
        user_id="test_user_collect",
        conversation_id="conv1",
        route="low",
        satisfaction=4,
        acceptance=AcceptanceLevel.ACCEPTED.value,
        follow_up_behavior=FollowUpBehavior.NONE.value
    )
    
    # Collect High Risk feedback
    feedback2 = service.collect_feedback(
        user_id="test_user_collect",
        conversation_id="conv2",
        route="high",
        sought_help=True
    )
    
    print(f"   ✅ 收集反馈成功")
    print(f"      反馈1: route={feedback1.route}, satisfaction={feedback1.satisfaction}")
    print(f"      反馈2: route={feedback2.route}, sought_help={feedback2.sought_help}")


async def test_get_feedback_statistics():
    """Test getting feedback statistics."""
    print("\n" + "=" * 80)
    print("测试 5: 获取反馈统计")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect various feedback
    service.collect_feedback("user_stats1", "conv1", "low", satisfaction=4)
    service.collect_feedback("user_stats2", "conv2", "medium", satisfaction=3)
    service.collect_feedback("user_stats3", "conv3", "high", sought_help=True)
    
    stats = service.get_feedback_statistics()
    
    print(f"   ✅ 获取统计成功")
    print(f"      总反馈数: {stats['total_feedback']}")
    print(f"      路由分布: {stats['route_counts']}")
    print(f"      平均满意度: {stats['average_satisfaction']}")


async def test_get_route_history():
    """Test getting history by route."""
    print("\n" + "=" * 80)
    print("测试 6: 按路由获取历史")
    print("=" * 80)
    
    service = HistoryService()
    
    # Get history for different routes (may be empty)
    low_history = await service.get_route_history("low", limit=10)
    medium_history = await service.get_route_history("medium", limit=10)
    high_history = await service.get_route_history("high", limit=10)
    
    print(f"   ✅ 按路由获取历史成功")
    print(f"      Low Risk: {len(low_history)} 条")
    print(f"      Medium Risk: {len(medium_history)} 条")
    print(f"      High Risk: {len(high_history)} 条")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("HistoryService 测试")
    print("=" * 80)
    print("\n此脚本将测试历史服务")
    print("包括：历史获取、反馈收集、统计")
    print("=" * 80)
    
    await test_get_user_history()
    await test_get_user_feedback()
    await test_get_complete_history()
    await test_collect_feedback()
    await test_get_feedback_statistics()
    await test_get_route_history()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

