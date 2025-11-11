"""
Test FeedbackCollector functionality.

Tests feedback collection and statistics.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows encoding setup
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src_new.adaptive.feedback import (
    FeedbackCollector,
    FeedbackScore,
    AcceptanceLevel,
    FollowUpBehavior
)


def test_collect_low_risk_feedback():
    """Test collecting Low Risk feedback."""
    print("\n" + "=" * 80)
    print("测试 1: 收集 Low Risk 反馈")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    feedback = collector.collect_feedback(
        user_id="user1",
        conversation_id="conv1",
        route="low",
        satisfaction=4,
        acceptance=AcceptanceLevel.ACCEPTED.value,
        follow_up_behavior=FollowUpBehavior.NONE.value
    )
    
    assert feedback.route == "low"
    assert feedback.satisfaction == 4
    assert feedback.acceptance == "accepted"
    assert feedback.follow_up_behavior == "none"
    assert feedback.sought_help is None
    
    print(f"   ✅ 反馈收集成功")
    print(f"      满意度: {feedback.satisfaction}")
    print(f"      接受程度: {feedback.acceptance}")
    print(f"      后续行为: {feedback.follow_up_behavior}")


def test_collect_medium_risk_feedback():
    """Test collecting Medium Risk feedback."""
    print("\n" + "=" * 80)
    print("测试 2: 收集 Medium Risk 反馈")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    feedback = collector.collect_feedback(
        user_id="user2",
        conversation_id="conv2",
        route="medium",
        satisfaction=3,
        acceptance=AcceptanceLevel.PARTIALLY.value,
        follow_up_behavior=FollowUpBehavior.PEER_GROUP.value
    )
    
    assert feedback.route == "medium"
    assert feedback.satisfaction == 3
    assert feedback.acceptance == "partially"
    assert feedback.follow_up_behavior == "peer_group"
    
    print(f"   ✅ 反馈收集成功")
    print(f"      满意度: {feedback.satisfaction}")
    print(f"      接受程度: {feedback.acceptance}")
    print(f"      后续行为: {feedback.follow_up_behavior}")


def test_collect_high_risk_feedback():
    """Test collecting High Risk feedback."""
    print("\n" + "=" * 80)
    print("测试 3: 收集 High Risk 反馈")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    # High Risk should not have satisfaction
    feedback = collector.collect_feedback(
        user_id="user3",
        conversation_id="conv3",
        route="high",
        sought_help=True
    )
    
    assert feedback.route == "high"
    assert feedback.satisfaction is None  # High Risk does not collect satisfaction
    assert feedback.sought_help is True
    
    print(f"   ✅ 反馈收集成功")
    print(f"      满意度: {feedback.satisfaction} (High Risk 不收集)")
    print(f"      寻求帮助: {feedback.sought_help}")


def test_feedback_validation():
    """Test feedback validation."""
    print("\n" + "=" * 80)
    print("测试 4: 反馈验证")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    # Test invalid satisfaction
    try:
        collector.collect_feedback(
            user_id="user4",
            conversation_id="conv4",
            route="low",
            satisfaction=6  # Invalid: > 5
        )
        print(f"   ❌ 应该抛出 ValueError")
    except ValueError as e:
        print(f"   ✅ 捕获无效满意度: {e}")
    
    # Test invalid acceptance
    try:
        collector.collect_feedback(
            user_id="user4",
            conversation_id="conv4",
            route="low",
            acceptance="invalid"
        )
        print(f"   ❌ 应该抛出 ValueError")
    except ValueError as e:
        print(f"   ✅ 捕获无效接受程度: {e}")


def test_get_user_feedback():
    """Test getting user feedback."""
    print("\n" + "=" * 80)
    print("测试 5: 获取用户反馈")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    # Collect multiple feedback entries
    collector.collect_feedback("user5", "conv5a", "low", satisfaction=4)
    collector.collect_feedback("user5", "conv5b", "medium", satisfaction=3)
    collector.collect_feedback("user5", "conv5c", "high", sought_help=True)
    
    # Get all feedback
    feedback_list = collector.get_user_feedback("user5")
    assert len(feedback_list) == 3
    
    # Get limited feedback
    limited = collector.get_user_feedback("user5", limit=2)
    assert len(limited) == 2
    
    print(f"   ✅ 获取反馈成功")
    print(f"      总反馈数: {len(feedback_list)}")
    print(f"      限制后: {len(limited)}")


def test_get_feedback_by_route():
    """Test getting feedback by route."""
    print("\n" + "=" * 80)
    print("测试 6: 按路由获取反馈")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    # Collect feedback for different routes
    collector.collect_feedback("user6", "conv6a", "low", satisfaction=4)
    collector.collect_feedback("user6", "conv6b", "low", satisfaction=5)
    collector.collect_feedback("user7", "conv7a", "medium", satisfaction=3)
    collector.collect_feedback("user8", "conv8a", "high", sought_help=True)
    
    # Get Low Risk feedback
    low_feedback = collector.get_feedback_by_route("low")
    assert len(low_feedback) == 2
    
    # Get Medium Risk feedback
    medium_feedback = collector.get_feedback_by_route("medium")
    assert len(medium_feedback) == 1
    
    # Get High Risk feedback
    high_feedback = collector.get_feedback_by_route("high")
    assert len(high_feedback) == 1
    
    print(f"   ✅ 按路由获取反馈成功")
    print(f"      Low Risk: {len(low_feedback)}")
    print(f"      Medium Risk: {len(medium_feedback)}")
    print(f"      High Risk: {len(high_feedback)}")


def test_get_statistics():
    """Test getting feedback statistics."""
    print("\n" + "=" * 80)
    print("测试 7: 获取反馈统计")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    # Collect various feedback
    collector.collect_feedback("user9", "conv9a", "low", satisfaction=4, acceptance="accepted")
    collector.collect_feedback("user9", "conv9b", "low", satisfaction=5, acceptance="accepted")
    collector.collect_feedback("user10", "conv10a", "medium", satisfaction=3, acceptance="partially")
    collector.collect_feedback("user11", "conv11a", "high", sought_help=True)
    
    stats = collector.get_statistics()
    
    print(f"   ✅ 统计信息:")
    print(f"      总反馈数: {stats['total_feedback']}")
    print(f"      路由分布: {stats['route_counts']}")
    print(f"      平均满意度: {stats['average_satisfaction']}")
    print(f"      接受程度分布: {stats['acceptance_counts']}")
    print(f"      后续行为分布: {stats['follow_up_counts']}")
    print(f"      寻求帮助数: {stats['sought_help_count']}")


def test_feedback_to_dict():
    """Test feedback serialization."""
    print("\n" + "=" * 80)
    print("测试 8: 反馈序列化")
    print("=" * 80)
    
    collector = FeedbackCollector()
    
    feedback = collector.collect_feedback(
        user_id="user12",
        conversation_id="conv12",
        route="low",
        satisfaction=4,
        acceptance="accepted"
    )
    
    # Convert to dict
    feedback_dict = feedback.to_dict()
    
    # Convert back
    feedback_restored = FeedbackScore.from_dict(feedback_dict)
    
    assert feedback_restored.user_id == feedback.user_id
    assert feedback_restored.route == feedback.route
    assert feedback_restored.satisfaction == feedback.satisfaction
    
    print(f"   ✅ 序列化/反序列化成功")
    print(f"      原始: user={feedback.user_id}, route={feedback.route}")
    print(f"      恢复: user={feedback_restored.user_id}, route={feedback_restored.route}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("FeedbackCollector 测试")
    print("=" * 80)
    print("\n此脚本将测试反馈收集器")
    print("包括：反馈收集、验证、查询、统计")
    print("=" * 80)
    
    test_collect_low_risk_feedback()
    test_collect_medium_risk_feedback()
    test_collect_high_risk_feedback()
    test_feedback_validation()
    test_get_user_feedback()
    test_get_feedback_by_route()
    test_get_statistics()
    test_feedback_to_dict()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

