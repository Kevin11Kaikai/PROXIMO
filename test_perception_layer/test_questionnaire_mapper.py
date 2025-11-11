"""
Test questionnaire mapping logic.

Tests the mapping of PHQ-9 and GAD-7 scores to risk routes.
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

from src_new.perception.questionnaire_mapper import QuestionnaireMapper, Route


def test_phq9_mapping():
    """Test PHQ-9 score mapping."""
    print("\n" + "=" * 80)
    print("测试 1: PHQ-9 分数映射")
    print("=" * 80)
    
    test_cases = [
        {"score": 5, "q9": 0, "expected": "low"},
        {"score": 9, "q9": 0, "expected": "low"},
        {"score": 10, "q9": 0, "expected": "medium"},
        {"score": 14, "q9": 0, "expected": "medium"},
        {"score": 15, "q9": 0, "expected": "high"},
        {"score": 20, "q9": 0, "expected": "high"},
        # 特殊规则：Q9 >= 1 → High
        {"score": 5, "q9": 1, "expected": "high"},
        {"score": 5, "q9": 2, "expected": "high"},
        {"score": 5, "q9": 3, "expected": "high"},
    ]
    
    for test_case in test_cases:
        result = QuestionnaireMapper.map_phq9(
            test_case["score"],
            test_case.get("q9")
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} PHQ-9={test_case['score']}, Q9={test_case.get('q9', 'N/A')}: 预期={expected}, 实际={result}")


def test_gad7_mapping():
    """Test GAD-7 score mapping."""
    print("\n" + "=" * 80)
    print("测试 2: GAD-7 分数映射")
    print("=" * 80)
    
    test_cases = [
        {"score": 5, "expected": "low"},
        {"score": 9, "expected": "low"},
        {"score": 10, "expected": "medium"},
        {"score": 14, "expected": "medium"},
        {"score": 15, "expected": "high"},
        {"score": 20, "expected": "high"},
    ]
    
    for test_case in test_cases:
        result = QuestionnaireMapper.map_gad7(test_case["score"])
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} GAD-7={test_case['score']}: 预期={expected}, 实际={result}")


def test_combine_routes():
    """Test route combination logic."""
    print("\n" + "=" * 80)
    print("测试 3: 路由合并（取较高等级）")
    print("=" * 80)
    
    test_cases = [
        {"phq9": "low", "gad7": "low", "expected": "low"},
        {"phq9": "low", "gad7": "medium", "expected": "medium"},
        {"phq9": "medium", "gad7": "low", "expected": "medium"},
        {"phq9": "medium", "gad7": "medium", "expected": "medium"},
        {"phq9": "low", "gad7": "high", "expected": "high"},
        {"phq9": "high", "gad7": "low", "expected": "high"},
        {"phq9": "high", "gad7": "high", "expected": "high"},
    ]
    
    for test_case in test_cases:
        result = QuestionnaireMapper.combine_routes(
            test_case["phq9"],
            test_case["gad7"]
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} PHQ-9={test_case['phq9']}, GAD-7={test_case['gad7']}: 预期={expected}, 实际={result}")


def test_chat_content_priority():
    """Test chat content priority over questionnaire."""
    print("\n" + "=" * 80)
    print("测试 4: 聊天内容优先级")
    print("=" * 80)
    
    from src_new.perception.psyguard_service import (
        MEDIUM_RISK_THRESHOLD,
        HIGH_RISK_DIRECT_THRESHOLD
    )
    
    test_cases = [
        # 问卷 Low，聊天 High → High
        {
            "phq9": 5, "gad7": 5, "q9": 0,
            "chat_risk": HIGH_RISK_DIRECT_THRESHOLD + 0.01,
            "expected": "high"
        },
        # 问卷 Low，聊天 Medium → Medium
        {
            "phq9": 5, "gad7": 5, "q9": 0,
            "chat_risk": MEDIUM_RISK_THRESHOLD + 0.01,
            "expected": "medium"
        },
        # 问卷 Medium，聊天 Low → Medium（问卷结果）
        {
            "phq9": 12, "gad7": 10, "q9": 0,
            "chat_risk": 0.3,
            "expected": "medium"
        },
        # 问卷 High，聊天 Low → High（问卷结果）
        {
            "phq9": 18, "gad7": 15, "q9": 0,
            "chat_risk": 0.3,
            "expected": "high"
        },
    ]
    
    for test_case in test_cases:
        result = QuestionnaireMapper.final_route_decision(
            phq9_score=test_case["phq9"],
            gad7_score=test_case["gad7"],
            phq9_q9_score=test_case.get("q9"),
            chat_risk_score=test_case.get("chat_risk")
        )
        expected = test_case["expected"]
        status = "✅" if result == expected else "❌"
        print(f"   {status} PHQ-9={test_case['phq9']}, GAD-7={test_case['gad7']}, "
              f"Chat={test_case.get('chat_risk', 'N/A')}: 预期={expected}, 实际={result}")


def test_assessment_result_mapping():
    """Test mapping from assessment result dictionary."""
    print("\n" + "=" * 80)
    print("测试 5: 评估结果映射")
    print("=" * 80)
    
    # PHQ-9 测试
    phq9_assessment = {
        "scale": "phq9",
        "total_score": 12.0,
        "parsed_scores": [1, 1, 2, 1, 1, 1, 1, 1, 2]  # Q9 = 2
    }
    result = QuestionnaireMapper.map_assessment_result(phq9_assessment)
    # Q9 = 2 >= 1, 应该返回 "high"
    assert result == "high", f"PHQ-9 Q9=2 应该返回 'high'，实际是 '{result}'"
    print(f"   ✅ PHQ-9 (score=12, Q9=2): {result}")
    
    # GAD-7 测试
    gad7_assessment = {
        "scale": "gad7",
        "total_score": 10.0,
        "parsed_scores": [1, 1, 2, 1, 1, 2, 2]
    }
    result = QuestionnaireMapper.map_assessment_result(gad7_assessment)
    assert result == "medium", f"GAD-7 score=10 应该返回 'medium'，实际是 '{result}'"
    print(f"   ✅ GAD-7 (score=10): {result}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("Questionnaire Mapper 测试")
    print("=" * 80)
    print("\n此脚本将测试问卷分数映射逻辑")
    print("包括：PHQ-9 映射、GAD-7 映射、路由合并、聊天内容优先级")
    print("=" * 80)
    
    test_phq9_mapping()
    test_gad7_mapping()
    test_combine_routes()
    test_chat_content_priority()
    test_assessment_result_mapping()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

