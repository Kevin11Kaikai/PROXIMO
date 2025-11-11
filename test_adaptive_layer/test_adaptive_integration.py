"""
Integration test for Adaptive Layer.

Tests feedback collection integrated with conversation flow.
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


async def test_conversation_end_feedback():
    """Test feedback collection at conversation end."""
    print("\n" + "=" * 80)
    print("测试 1: 对话结束时的反馈收集")
    print("=" * 80)
    
    service = HistoryService()
    
    # Simulate Low Risk conversation end
    feedback = service.collect_feedback(
        user_id="user_end1",
        conversation_id="conv_end1",
        route="low",
        satisfaction=4,
        acceptance=AcceptanceLevel.ACCEPTED.value,
        follow_up_behavior=FollowUpBehavior.NONE.value
    )
    
    print(f"   ✅ 对话结束反馈收集成功")
    print(f"      路由: {feedback.route}")
    print(f"      满意度: {feedback.satisfaction}")
    print(f"      接受程度: {feedback.acceptance}")


async def test_route_transition_feedback():
    """Test feedback collection at route transitions."""
    print("\n" + "=" * 80)
    print("测试 2: 路由转换时的反馈收集")
    print("=" * 80)
    
    service = HistoryService()
    
    # Simulate Low → Medium transition
    feedback1 = service.collect_feedback(
        user_id="user_trans1",
        conversation_id="conv_trans1",
        route="low",
        satisfaction=3,
        acceptance=AcceptanceLevel.PARTIALLY.value
    )
    
    # Simulate Medium → High transition
    feedback2 = service.collect_feedback(
        user_id="user_trans2",
        conversation_id="conv_trans2",
        route="medium",
        satisfaction=2,
        acceptance=AcceptanceLevel.REJECTED.value
    )
    
    print(f"   ✅ 路由转换反馈收集成功")
    print(f"      转换1 (Low→Medium): route={feedback1.route}, satisfaction={feedback1.satisfaction}")
    print(f"      转换2 (Medium→High): route={feedback2.route}, satisfaction={feedback2.satisfaction}")


async def test_high_risk_script_end_feedback():
    """Test feedback collection at High Risk script end."""
    print("\n" + "=" * 80)
    print("测试 3: High Risk 脚本结束时的反馈收集")
    print("=" * 80)
    
    service = HistoryService()
    
    # High Risk only collects sought_help
    feedback = service.collect_feedback(
        user_id="user_high1",
        conversation_id="conv_high1",
        route="high",
        sought_help=True
    )
    
    print(f"   ✅ High Risk 反馈收集成功")
    print(f"      路由: {feedback.route}")
    print(f"      满意度: {feedback.satisfaction} (High Risk 不收集)")
    print(f"      寻求帮助: {feedback.sought_help}")


async def test_feedback_analysis():
    """Test feedback analysis for adaptive learning."""
    print("\n" + "=" * 80)
    print("测试 4: 反馈分析（用于自适应学习）")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect various feedback
    service.collect_feedback("user_analysis1", "conv1", "low", satisfaction=5, acceptance="accepted")
    service.collect_feedback("user_analysis2", "conv2", "low", satisfaction=4, acceptance="accepted")
    service.collect_feedback("user_analysis3", "conv3", "medium", satisfaction=3, acceptance="partially")
    service.collect_feedback("user_analysis4", "conv4", "high", sought_help=True)
    
    # Get statistics
    stats = service.get_feedback_statistics()
    
    # Get user complete history
    complete = await service.get_user_complete_history("user_analysis1")
    
    print(f"   ✅ 反馈分析成功")
    print(f"      总反馈数: {stats['total_feedback']}")
    print(f"      平均满意度: {stats['average_satisfaction']}")
    print(f"      用户完整历史: {complete['total_feedback']} 条反馈")


async def test_feedback_storage():
    """Test feedback storage and retrieval."""
    print("\n" + "=" * 80)
    print("测试 5: 反馈存储和检索")
    print("=" * 80)
    
    service = HistoryService()
    
    # Collect feedback
    feedback1 = service.collect_feedback(
        user_id="user_storage",
        conversation_id="conv1",
        route="low",
        satisfaction=4
    )
    
    # Retrieve feedback
    retrieved = service.get_user_feedback("user_storage")
    
    assert len(retrieved) == 1
    assert retrieved[0].user_id == feedback1.user_id
    assert retrieved[0].satisfaction == feedback1.satisfaction
    
    print(f"   ✅ 存储和检索成功")
    print(f"      存储: user={feedback1.user_id}, satisfaction={feedback1.satisfaction}")
    print(f"      检索: user={retrieved[0].user_id}, satisfaction={retrieved[0].satisfaction}")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("Adaptive Layer 集成测试")
    print("=" * 80)
    print("\n此脚本将测试 Adaptive Layer 的集成")
    print("包括：对话结束反馈、路由转换反馈、High Risk 反馈、反馈分析")
    print("=" * 80)
    
    await test_conversation_end_feedback()
    await test_route_transition_feedback()
    await test_high_risk_script_end_feedback()
    await test_feedback_analysis()
    await test_feedback_storage()
    
    print("\n" + "=" * 80)
    print("集成测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

