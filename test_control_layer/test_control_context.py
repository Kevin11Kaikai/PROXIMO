"""
Test ControlContext data structure.

Tests the control context data class and its methods.
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

from src_new.control.control_context import ControlContext


def test_context_creation():
    """Test ControlContext creation."""
    print("\n" + "=" * 80)
    print("测试 1: ControlContext 创建")
    print("=" * 80)
    
    context = ControlContext(
        user_id="test_user",
        route="medium",
        rigid_score=0.6
    )
    
    assert context.user_id == "test_user"
    assert context.route == "medium"
    assert context.rigid_score == 0.6
    assert context.guardrails_enabled is True
    assert context.route_established_at is not None
    assert context.last_updated_at is not None
    
    print("   ✅ ControlContext 创建成功")
    print(f"      用户ID: {context.user_id}")
    print(f"      路由: {context.route}")
    print(f"      Rigid Score: {context.rigid_score}")


def test_context_with_perception_data():
    """Test ControlContext with perception layer data."""
    print("\n" + "=" * 80)
    print("测试 2: 包含感知层数据的 ControlContext")
    print("=" * 80)
    
    context = ControlContext(
        user_id="test_user",
        route="high",
        rigid_score=1.0,
        psyguard_score=0.95,
        questionnaire_phq9_score=18.0,
        questionnaire_gad7_score=15.0,
        phq9_q9_score=2,
        route_reason="chat_high_risk",
        route_source="questionnaire_mapper"
    )
    
    assert context.psyguard_score == 0.95
    assert context.questionnaire_phq9_score == 18.0
    assert context.phq9_q9_score == 2
    assert context.route_reason == "chat_high_risk"
    
    print("   ✅ 感知层数据正确存储")
    print(f"      PsyGUARD 分数: {context.psyguard_score}")
    print(f"      PHQ-9 分数: {context.questionnaire_phq9_score}")
    print(f"      PHQ-9 Q9: {context.phq9_q9_score}")


def test_route_update():
    """Test route update method."""
    print("\n" + "=" * 80)
    print("测试 3: 路由更新方法")
    print("=" * 80)
    
    context = ControlContext(
        user_id="test_user",
        route="low",
        rigid_score=0.2
    )
    
    original_time = context.last_updated_at
    
    # 等待一小段时间确保时间戳不同
    import time
    time.sleep(0.01)
    
    # 更新路由
    context.update_route("medium", reason="psyguard_upgrade")
    
    assert context.route == "medium"
    assert context.route_reason == "psyguard_upgrade"
    assert context.last_updated_at > original_time
    
    print("   ✅ 路由更新成功")
    print(f"      新路由: {context.route}")
    print(f"      原因: {context.route_reason}")
    print(f"      更新时间: {context.last_updated_at}")


def test_route_no_change():
    """Test route update when route doesn't change."""
    print("\n" + "=" * 80)
    print("测试 4: 路由不变的情况")
    print("=" * 80)
    
    context = ControlContext(
        user_id="test_user",
        route="medium",
        rigid_score=0.6
    )
    
    original_time = context.last_updated_at
    
    # 尝试更新为相同路由
    context.update_route("medium", reason="no_change")
    
    # 路由应该不变，但时间戳可能更新（取决于实现）
    assert context.route == "medium"
    
    print("   ✅ 路由不变时处理正确")
    print(f"      路由: {context.route}")


def test_extras_field():
    """Test extras field for additional metadata."""
    print("\n" + "=" * 80)
    print("测试 5: Extras 字段")
    print("=" * 80)
    
    context = ControlContext(
        user_id="test_user",
        route="high",
        rigid_score=1.0,
        extras={
            "conversation_turn_count": 3,
            "questionnaire_triggered": True,
            "custom_flag": "test"
        }
    )
    
    assert context.extras["conversation_turn_count"] == 3
    assert context.extras["questionnaire_triggered"] is True
    assert context.extras["custom_flag"] == "test"
    
    print("   ✅ Extras 字段正确存储")
    print(f"      额外数据: {context.extras}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("ControlContext 测试")
    print("=" * 80)
    print("\n此脚本将测试 ControlContext 数据类")
    print("包括：创建、数据存储、路由更新")
    print("=" * 80)
    
    test_context_creation()
    test_context_with_perception_data()
    test_route_update()
    test_route_no_change()
    test_extras_field()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

