"""
Test RouteUpdater functionality.

Tests the one-way route upgrade logic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows encoding setup
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src_new.control.route_updater import RouteUpdater
from src_new.perception.psyguard_service import (
    MEDIUM_RISK_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD
)


def test_low_to_medium_upgrade():
    """Test Low → Medium upgrade."""
    print("\n" + "=" * 80)
    print("测试 1: Low → Medium 升级")
    print("=" * 80)
    
    test_cases = [
        {"current": "low", "score": 0.3, "expected": "low"},  # 低于阈值，不升级
        {"current": "low", "score": 0.69, "expected": "low"},  # 低于阈值，不升级
        {"current": "low", "score": 0.70, "expected": "medium"},  # 达到阈值，升级
        {"current": "low", "score": 0.75, "expected": "medium"},  # 超过阈值，升级
        {"current": "low", "score": 0.94, "expected": "medium"},  # 超过阈值但未到 High
    ]
    
    for test_case in test_cases:
        result = RouteUpdater.update_route(
            test_case["current"],
            test_case["score"]
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} 当前={test_case['current']}, 分数={test_case['score']:.2f}: "
              f"预期={expected}, 实际={result}")


def test_medium_no_downgrade():
    """Test Medium route does not downgrade."""
    print("\n" + "=" * 80)
    print("测试 2: Medium 不降级")
    print("=" * 80)
    
    test_cases = [
        {"current": "medium", "score": 0.3, "expected": "medium"},  # 低于阈值，保持
        {"current": "medium", "score": 0.5, "expected": "medium"},  # 低于阈值，保持
        {"current": "medium", "score": 0.69, "expected": "medium"},  # 低于阈值，保持
        {"current": "medium", "score": 0.70, "expected": "medium"},  # 达到阈值，保持
        {"current": "medium", "score": 0.94, "expected": "medium"},  # 超过阈值但未到 High，保持
    ]
    
    for test_case in test_cases:
        result = RouteUpdater.update_route(
            test_case["current"],
            test_case["score"]
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} 当前={test_case['current']}, 分数={test_case['score']:.2f}: "
              f"预期={expected}, 实际={result}")


def test_high_no_downgrade():
    """Test High route does not downgrade."""
    print("\n" + "=" * 80)
    print("测试 3: High 不降级")
    print("=" * 80)
    
    test_cases = [
        {"current": "high", "score": 0.0, "expected": "high"},  # 最低分数，保持
        {"current": "high", "score": 0.3, "expected": "high"},  # 低风险，保持
        {"current": "high", "score": 0.5, "expected": "high"},  # 中等风险，保持
        {"current": "high", "score": 0.7, "expected": "high"},  # 高风险，保持
        {"current": "high", "score": 0.95, "expected": "high"},  # 极高风险，保持
    ]
    
    for test_case in test_cases:
        result = RouteUpdater.update_route(
            test_case["current"],
            test_case["score"]
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} 当前={test_case['current']}, 分数={test_case['score']:.2f}: "
              f"预期={expected}, 实际={result}")


def test_direct_high_upgrade():
    """Test direct upgrade to High (>= 0.95)."""
    print("\n" + "=" * 80)
    print("测试 4: 直接升级到 High (>= 0.95)")
    print("=" * 80)
    
    test_cases = [
        {"current": "low", "score": 0.95, "expected": "high"},
        {"current": "low", "score": 0.98, "expected": "high"},
        {"current": "medium", "score": 0.95, "expected": "high"},
        {"current": "medium", "score": 0.99, "expected": "high"},
    ]
    
    for test_case in test_cases:
        result = RouteUpdater.update_route(
            test_case["current"],
            test_case["score"]
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} 当前={test_case['current']}, 分数={test_case['score']:.2f}: "
              f"预期={expected}, 实际={result}")


def test_should_upgrade():
    """Test should_upgrade helper method."""
    print("\n" + "=" * 80)
    print("测试 5: should_upgrade 辅助方法")
    print("=" * 80)
    
    test_cases = [
        {"current": "low", "score": 0.3, "should_upgrade": False},
        {"current": "low", "score": 0.75, "should_upgrade": True},
        {"current": "medium", "score": 0.3, "should_upgrade": False},
        {"current": "medium", "score": 0.75, "should_upgrade": False},  # Medium 不升级到 High（除非 >= 0.95）
        {"current": "medium", "score": 0.96, "should_upgrade": True},  # 直接 High
        {"current": "high", "score": 0.3, "should_upgrade": False},
    ]
    
    for test_case in test_cases:
        result = RouteUpdater.should_upgrade(
            test_case["current"],
            test_case["score"]
        )
        expected = test_case["should_upgrade"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} 当前={test_case['current']}, 分数={test_case['score']:.2f}: "
              f"预期升级={expected}, 实际={result}")


def test_get_upgrade_target():
    """Test get_upgrade_target helper method."""
    print("\n" + "=" * 80)
    print("测试 6: get_upgrade_target 辅助方法")
    print("=" * 80)
    
    test_cases = [
        {"current": "low", "score": 0.3, "target": None},  # 不升级
        {"current": "low", "score": 0.75, "target": "medium"},  # 升级到 Medium
        {"current": "low", "score": 0.96, "target": "high"},  # 直接升级到 High
        {"current": "medium", "score": 0.3, "target": None},  # 不升级
        {"current": "medium", "score": 0.96, "target": "high"},  # 升级到 High
        {"current": "high", "score": 0.3, "target": None},  # 不升级
    ]
    
    for test_case in test_cases:
        result = RouteUpdater.get_upgrade_target(
            test_case["current"],
            test_case["score"]
        )
        expected = test_case["target"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} 当前={test_case['current']}, 分数={test_case['score']:.2f}: "
              f"预期目标={expected}, 实际={result}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("RouteUpdater 测试")
    print("=" * 80)
    print("\n此脚本将测试路由更新逻辑")
    print("包括：单向升级、不降级规则、直接 High 升级")
    print("=" * 80)
    
    test_low_to_medium_upgrade()
    test_medium_no_downgrade()
    test_high_no_downgrade()
    test_direct_high_upgrade()
    test_should_upgrade()
    test_get_upgrade_target()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

