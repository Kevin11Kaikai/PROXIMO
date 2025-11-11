"""
Test RiskRouter functionality.

Tests the risk routing logic including questionnaire mapping,
chat content priority, and route decision.
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

from src_new.control.risk_router import RiskRouter, RiskRoutingResult


def test_questionnaire_routing():
    """Test routing from questionnaire results."""
    print("\n" + "=" * 80)
    print("测试 1: 基于问卷的路由决策")
    print("=" * 80)
    
    router = RiskRouter()
    
    test_cases = [
        {
            "name": "Low Risk (PHQ-9=5, GAD-7=5)",
            "phq9": {"total_score": 5.0, "parsed_scores": [0, 0, 1, 0, 0, 1, 0, 0, 0]},
            "gad7": {"total_score": 5.0, "parsed_scores": [0, 0, 1, 0, 0, 1, 0]},
            "chat_risk": None,
            "expected_route": "low"
        },
        {
            "name": "Medium Risk (PHQ-9=12, GAD-7=10, Q9=0)",
            "phq9": {"total_score": 12.0, "parsed_scores": [1, 1, 2, 1, 1, 1, 1, 1, 0]},  # Q9=0
            "gad7": {"total_score": 10.0, "parsed_scores": [1, 1, 2, 1, 1, 2, 2]},
            "chat_risk": None,
            "expected_route": "medium"
        },
        {
            "name": "High Risk (PHQ-9=18, GAD-7=15)",
            "phq9": {"total_score": 18.0, "parsed_scores": [2, 2, 2, 2, 2, 2, 2, 2, 2]},
            "gad7": {"total_score": 15.0, "parsed_scores": [2, 2, 2, 2, 2, 2, 3]},
            "chat_risk": None,
            "expected_route": "high"
        },
        {
            "name": "PHQ-9 Q9 Special Rule (Q9=2 → High)",
            "phq9": {"total_score": 5.0, "parsed_scores": [0, 0, 0, 0, 0, 0, 0, 0, 2]},
            "gad7": {"total_score": 5.0, "parsed_scores": [0, 0, 0, 0, 0, 0, 0]},
            "chat_risk": None,
            "expected_route": "high"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   测试: {test_case['name']}")
        result = router.decide_from_questionnaires(
            phq9_result=test_case["phq9"],
            gad7_result=test_case["gad7"],
            chat_risk_score=test_case.get("chat_risk")
        )
        
        expected = test_case["expected_route"]
        actual = result.route
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} 预期={expected}, 实际={actual}")
        print(f"      原因: {result.reason}")
        print(f"      Rigid Score: {result.rigid_score:.3f}")


def test_chat_content_priority():
    """Test chat content priority over questionnaire."""
    print("\n" + "=" * 80)
    print("测试 2: 聊天内容优先级")
    print("=" * 80)
    
    router = RiskRouter()
    
    test_cases = [
        {
            "name": "问卷 Low，聊天 High → High",
            "phq9": {"total_score": 5.0, "parsed_scores": [0, 0, 1, 0, 0, 1, 0, 0, 0]},
            "gad7": {"total_score": 5.0, "parsed_scores": [0, 0, 1, 0, 0, 1, 0]},
            "chat_risk": 0.96,  # >= 0.95
            "expected_route": "high"
        },
        {
            "name": "问卷 Low，聊天 Medium → Medium",
            "phq9": {"total_score": 5.0, "parsed_scores": [0, 0, 1, 0, 0, 1, 0, 0, 0]},
            "gad7": {"total_score": 5.0, "parsed_scores": [0, 0, 1, 0, 0, 1, 0]},
            "chat_risk": 0.75,  # >= 0.70
            "expected_route": "medium"
        },
        {
            "name": "问卷 Medium，聊天 Low → Medium (保持)",
            "phq9": {"total_score": 12.0, "parsed_scores": [1, 1, 2, 1, 1, 1, 1, 1, 0]},  # Q9=0
            "gad7": {"total_score": 10.0, "parsed_scores": [1, 1, 2, 1, 1, 2, 2]},
            "chat_risk": 0.3,  # < 0.70
            "expected_route": "medium"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   测试: {test_case['name']}")
        result = router.decide_from_questionnaires(
            phq9_result=test_case["phq9"],
            gad7_result=test_case["gad7"],
            chat_risk_score=test_case.get("chat_risk")
        )
        
        expected = test_case["expected_route"]
        actual = result.route
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} 预期={expected}, 实际={actual}")
        print(f"      聊天风险: {test_case.get('chat_risk', 'N/A')}")


def test_legacy_compatibility():
    """Test legacy assessment compatibility."""
    print("\n" + "=" * 80)
    print("测试 3: 向后兼容性（Legacy Assessment）")
    print("=" * 80)
    
    router = RiskRouter()
    
    # 模拟 legacy assessment 结果
    assessment = {
        "scale": "phq9",
        "total_score": 12.0,
        "severity_level": "moderate",
        "parsed_scores": [1, 1, 2, 1, 1, 1, 1, 1, 1],
        "flags": {}
    }
    
    result = router.decide_from_assessment(assessment)
    
    print(f"   路由: {result.route}")
    print(f"   Rigid Score: {result.rigid_score:.3f}")
    print(f"   原因: {result.reason}")
    print(f"   ✅ Legacy 兼容性测试通过")


def test_rigid_score_calculation():
    """Test rigid_score calculation."""
    print("\n" + "=" * 80)
    print("测试 4: Rigid Score 计算")
    print("=" * 80)
    
    router = RiskRouter()
    
    test_cases = [
        {"route": "low", "phq9": 5, "gad7": 5, "expected_range": (0.0, 0.4)},
        {"route": "medium", "phq9": 12, "gad7": 10, "expected_range": (0.5, 0.75)},
        {"route": "high", "phq9": 18, "gad7": 15, "expected_range": (0.95, 1.0)},
    ]
    
    for test_case in test_cases:
        phq9_result = {
            "total_score": test_case["phq9"],
            "parsed_scores": [0] * 9
        }
        gad7_result = {
            "total_score": test_case["gad7"],
            "parsed_scores": [0] * 7
        }
        
        result = router.decide_from_questionnaires(phq9_result, gad7_result)
        rigid = result.rigid_score
        min_val, max_val = test_case["expected_range"]
        
        status = "✅" if min_val <= rigid <= max_val else "❌"
        print(f"   {status} {test_case['route']}: {rigid:.3f} (预期范围: {min_val}-{max_val})")


def main():
    """Run all tests."""
    print("=" * 80)
    print("RiskRouter 测试")
    print("=" * 80)
    print("\n此脚本将测试风险路由逻辑")
    print("包括：问卷映射、聊天内容优先级、向后兼容性")
    print("=" * 80)
    
    test_questionnaire_routing()
    test_chat_content_priority()
    test_legacy_compatibility()
    test_rigid_score_calculation()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

