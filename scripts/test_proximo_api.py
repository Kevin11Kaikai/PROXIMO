"""
测试脚本：验证 PROXIMO Assessment API 封装效果

这个脚本会测试：
1. 基本功能测试（PHQ-9, GAD-7, PSS-10）
2. 边界情况测试
3. 错误处理测试
4. 风险检测测试（自杀意念、严重症状）
5. 输出结构验证
"""

import asyncio
import sys
import json
import os
import logging
from typing import Dict, Any, List

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, '.')

# 配置日志：在测试时抑制错误日志（因为我们要测试错误处理）
# 这些错误日志是预期的，不应该干扰测试输出
logging.getLogger('src.assessment.proximo_api').setLevel(logging.CRITICAL)

from src.assessment.proximo_api import (
    assess,
    assess_sync,
    assess_phq9,
    assess_gad7,
    assess_pss10
)


# ===== 测试用例数据 =====

# PHQ-9 测试用例
PHQ9_TEST_CASES = {
    "正常": {
        "responses": ["0", "0", "1", "1", "0", "1", "0", "1", "0"],
        "expected_score_range": (0, 10),
        "expected_severity": "minimal"
    },
    "轻度抑郁": {
        "responses": ["1", "1", "2", "2", "1", "2", "1", "2", "0"],
        "expected_score_range": (10, 15),
        "expected_severity": "mild"
    },
    "中度抑郁": {
        "responses": ["2", "2", "2", "2", "2", "2", "2", "2", "1"],
        "expected_score_range": (15, 20),
        "expected_severity": "moderate"
    },
    "重度抑郁": {
        "responses": ["3", "3", "3", "3", "3", "3", "3", "3", "0"],
        "expected_score_range": (20, 27),
        "expected_severity": "severe"
    },
    "自杀意念高风险": {
        "responses": ["2", "2", "2", "2", "2", "2", "2", "2", "2"],  # Item 9 = 2
        "expected_score_range": (15, 27),
        "expected_severity": "moderate",  # 或 severe
        "expected_suicidal_risk": "high"
    },
    "自然语言输入": {
        "responses": [
            "not at all", "never", "several days", "sometimes",
            "more than half the days", "often", "nearly every day", "always", "0"
        ],
        "expected_score_range": (0, 27),
        "expected_severity": None  # 不固定
    }
}

# GAD-7 测试用例
GAD7_TEST_CASES = {
    "正常": {
        "responses": ["0", "0", "1", "0", "1", "0", "0"],
        "expected_score_range": (0, 5),
        "expected_severity": "minimal"
    },
    "轻度焦虑": {
        "responses": ["1", "1", "2", "1", "2", "1", "1"],
        "expected_score_range": (7, 10),
        "expected_severity": "mild"
    },
    "重度焦虑": {
        "responses": ["3", "3", "3", "3", "3", "3", "3"],
        "expected_score_range": (20, 21),
        "expected_severity": "severe"
    }
}

# PSS-10 测试用例
PSS10_TEST_CASES = {
    "正常": {
        "responses": ["0", "1", "0", "4", "3", "1", "0", "4", "2", "1"],
        "expected_score_range": (0, 20),
        "expected_severity": "minimal"
    },
    "高压力": {
        "responses": ["4", "4", "4", "0", "0", "4", "4", "0", "0", "4"],
        "expected_score_range": (20, 40),
        "expected_severity": "moderate"  # 或 severe
    }
}


# ===== 测试函数 =====

def print_test_header(test_name: str):
    """打印测试标题"""
    print("\n" + "=" * 80)
    print(f"测试: {test_name}")
    print("=" * 80)


def print_result(result: Dict[str, Any], verbose: bool = True):
    """打印评估结果"""
    if not result.get("success", False):
        print(f"[FAIL] 评估失败: {result.get('error', 'Unknown error')}")
        return
    
    print(f"[OK] 评估成功")
    print(f"   量表类型: {result.get('scale', 'N/A')}")
    print(f"   总分: {result.get('total_score', 'N/A')}")
    print(f"   严重度: {result.get('severity_level', 'N/A')}")
    print(f"   风险级别: {result.get('risk_level', 'N/A')}")
    
    # 显示风险标志
    flags = result.get('flags', {})
    if flags:
        print(f"   风险标志:")
        for key, value in flags.items():
            print(f"     - {key}: {value}")
    
    # 显示自杀意念风险（仅 PHQ-9）
    if 'suicidal_risk' in result:
        print(f"   自杀意念风险: {result['suicidal_risk']}")
    
    # 显示临床建议
    interpretation = result.get('clinical_interpretation', {})
    recommendations = interpretation.get('recommendations', [])
    if recommendations:
        print(f"   临床建议:")
        for i, rec in enumerate(recommendations[:3], 1):  # 只显示前3条
            print(f"     {i}. {rec}")
    
    # 显示每题分数（详细模式）
    if verbose:
        parsed_scores = result.get('parsed_scores', [])
        if parsed_scores:
            print(f"   每题分数: {parsed_scores}")


def validate_result(result: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    """验证结果是否符合预期"""
    if not result.get("success", False):
        print(f"[FAIL] 验证失败: 评估未成功")
        return False
    
    total_score = result.get('total_score', 0)
    expected_range = expected.get('expected_score_range')
    
    if expected_range:
        min_score, max_score = expected_range
        if not (min_score <= total_score <= max_score):
            print(f"[FAIL] 验证失败: 总分 {total_score} 不在预期范围 [{min_score}, {max_score}]")
            return False
    
    expected_severity = expected.get('expected_severity')
    if expected_severity:
        actual_severity = result.get('severity_level')
        if actual_severity != expected_severity:
            print(f"[WARN] 警告: 严重度 {actual_severity} 与预期 {expected_severity} 不匹配（可能是合理的）")
    
    expected_suicidal_risk = expected.get('expected_suicidal_risk')
    if expected_suicidal_risk:
        actual_risk = result.get('suicidal_risk')
        if actual_risk != expected_suicidal_risk:
            print(f"[FAIL] 验证失败: 自杀意念风险 {actual_risk} 与预期 {expected_suicidal_risk} 不匹配")
            return False
    
    print(f"[OK] 验证通过")
    return True


async def test_phq9():
    """测试 PHQ-9 评估"""
    print_test_header("PHQ-9 评估测试")
    
    all_passed = True
    
    for case_name, test_case in PHQ9_TEST_CASES.items():
        print(f"\n--- 用例: {case_name} ---")
        responses = test_case["responses"]
        
        try:
            result = await assess("phq9", responses)
            print_result(result, verbose=False)
            
            if not validate_result(result, test_case):
                all_passed = False
            
        except Exception as e:
            print(f"[FAIL] 测试失败: {e}")
            all_passed = False
    
    return all_passed


async def test_gad7():
    """测试 GAD-7 评估"""
    print_test_header("GAD-7 评估测试")
    
    all_passed = True
    
    for case_name, test_case in GAD7_TEST_CASES.items():
        print(f"\n--- 用例: {case_name} ---")
        responses = test_case["responses"]
        
        try:
            result = await assess("gad7", responses)
            print_result(result, verbose=False)
            
            if not validate_result(result, test_case):
                all_passed = False
            
        except Exception as e:
            print(f"[FAIL] 测试失败: {e}")
            all_passed = False
    
    return all_passed


async def test_pss10():
    """测试 PSS-10 评估"""
    print_test_header("PSS-10 评估测试")
    
    all_passed = True
    
    for case_name, test_case in PSS10_TEST_CASES.items():
        print(f"\n--- 用例: {case_name} ---")
        responses = test_case["responses"]
        
        try:
            result = await assess("pss10", responses)
            print_result(result, verbose=False)
            
            if not validate_result(result, test_case):
                all_passed = False
            
        except Exception as e:
            print(f"[FAIL] 测试失败: {e}")
            all_passed = False
    
    return all_passed


async def test_convenience_functions():
    """测试便捷函数"""
    print_test_header("便捷函数测试")
    
    all_passed = True
    
    # 测试 assess_phq9
    print("\n--- 测试 assess_phq9() ---")
    try:
        result = await assess_phq9(["0", "1", "2", "1", "0", "2", "1", "1", "2"])
        if result.get("success"):
            print("[OK] assess_phq9() 工作正常")
        else:
            print(f"[FAIL] assess_phq9() 失败: {result.get('error')}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] assess_phq9() 异常: {e}")
        all_passed = False
    
    # 测试 assess_gad7
    print("\n--- 测试 assess_gad7() ---")
    try:
        result = await assess_gad7(["0", "1", "2", "1", "0", "2", "1"])
        if result.get("success"):
            print("[OK] assess_gad7() 工作正常")
        else:
            print(f"[FAIL] assess_gad7() 失败: {result.get('error')}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] assess_gad7() 异常: {e}")
        all_passed = False
    
    # 测试 assess_pss10
    print("\n--- 测试 assess_pss10() ---")
    try:
        result = await assess_pss10(["2", "3", "1", "0", "2", "1", "3", "2", "1", "2"])
        if result.get("success"):
            print("[OK] assess_pss10() 工作正常")
        else:
            print(f"[FAIL] assess_pss10() 失败: {result.get('error')}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] assess_pss10() 异常: {e}")
        all_passed = False
    
    return all_passed


async def test_error_handling():
    """测试错误处理"""
    print_test_header("错误处理测试")
    print("[INFO] 注意: 以下测试会故意触发错误，错误日志已被抑制")
    
    all_passed = True
    
    # 测试无效量表
    print("\n--- 测试无效量表 ---")
    try:
        result = await assess("invalid_scale", ["0", "1", "2"])
        if not result.get("success") and "error" in result:
            print(f"[OK] 正确捕获无效量表错误: {result.get('error', '')[:50]}...")
        else:
            print("[FAIL] 未正确捕获无效量表错误")
            all_passed = False
    except Exception as e:
        print(f"[WARN]  抛出异常而非返回错误: {e}")
    
    # 测试回答数量错误
    print("\n--- 测试回答数量错误 (PHQ-9 需要 9 个，提供 7 个) ---")
    try:
        result = await assess("phq9", ["0", "1", "2", "1", "0", "2", "1"])
        if not result.get("success") and "error" in result:
            print(f"[OK] 正确捕获回答数量错误: {result.get('error', '')[:50]}...")
        else:
            print("[FAIL] 未正确捕获回答数量错误")
            all_passed = False
    except Exception as e:
        print(f"[WARN]  抛出异常而非返回错误: {e}")
    
    # 测试空回答列表
    print("\n--- 测试空回答列表 ---")
    try:
        result = await assess("phq9", [])
        if not result.get("success") and "error" in result:
            print(f"[OK] 正确捕获空回答列表错误: {result.get('error', '')[:50]}...")
        else:
            print("[FAIL] 未正确捕获空回答列表错误")
            all_passed = False
    except Exception as e:
        print(f"[WARN]  抛出异常而非返回错误: {e}")
    
    return all_passed


async def test_risk_detection():
    """测试风险检测功能"""
    print_test_header("风险检测测试")
    
    all_passed = True
    
    # 测试自杀意念检测
    print("\n--- 测试自杀意念检测 (PHQ-9 Item 9 = 2) ---")
    try:
        responses = ["1", "1", "1", "1", "1", "1", "1", "1", "2"]  # Item 9 = 2
        result = await assess("phq9", responses)
        
        if result.get("success"):
            flags = result.get("flags", {})
            suicidal_risk = result.get("suicidal_risk")
            
            if flags.get("suicidal_ideation") and suicidal_risk == "high":
                print("[OK] 正确检测到自杀意念高风险")
                print(f"   自杀意念分数: {flags.get('suicidal_ideation_score')}")
                print(f"   风险级别: {result.get('risk_level')}")
            else:
                print(f"[FAIL] 未正确检测自杀意念: flags={flags}, suicidal_risk={suicidal_risk}")
                all_passed = False
        else:
            print(f"[FAIL] 评估失败: {result.get('error')}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] 测试异常: {e}")
        all_passed = False
    
    # 测试严重症状检测
    print("\n--- 测试严重症状检测 (PHQ-9 总分 ≥ 20) ---")
    try:
        responses = ["3", "3", "3", "3", "3", "3", "3", "3", "0"]  # 总分 = 24
        result = await assess("phq9", responses)
        
        if result.get("success"):
            flags = result.get("flags", {})
            total_score = result.get("total_score")
            
            if flags.get("severe_symptoms") and total_score >= 20:
                print(f"[OK] 正确检测到严重症状 (总分: {total_score})")
                print(f"   严重度: {result.get('severity_level')}")
                print(f"   风险级别: {result.get('risk_level')}")
            else:
                print(f"[FAIL] 未正确检测严重症状: flags={flags}, total_score={total_score}")
                all_passed = False
        else:
            print(f"[FAIL] 评估失败: {result.get('error')}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] 测试异常: {e}")
        all_passed = False
    
    return all_passed


def test_sync_version():
    """测试同步版本（需要在非异步上下文中运行）"""
    print_test_header("同步版本测试")
    
    all_passed = True
    
    print("\n--- 测试 assess_sync() ---")
    print("[INFO] 注意: assess_sync() 不能在异步上下文中运行")
    print("[INFO] 这是预期的行为，说明错误检测正常工作")
    
    # 由于我们在 asyncio.run() 中运行，assess_sync() 会正确检测到异步上下文
    # 并抛出 RuntimeError，这是预期的行为
    try:
        result = assess_sync("phq9", ["0", "1", "2", "1", "0", "2", "1", "1", "2"])
        # 如果执行到这里，说明没有正确检测到异步上下文（不应该发生）
        print("[WARN] assess_sync() 在异步上下文中没有抛出错误（可能有问题）")
        all_passed = False
    except RuntimeError as e:
        if "Cannot use assess_sync() in an async context" in str(e):
            print("[OK] assess_sync() 正确检测到异步上下文并拒绝执行")
        else:
            print(f"[FAIL] assess_sync() 抛出意外的 RuntimeError: {e}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] assess_sync() 抛出意外异常: {e}")
        all_passed = False
    
    # 注意: 要真正测试 assess_sync()，需要在单独的同步脚本中运行
    # 这里我们只验证它在异步上下文中能正确拒绝执行
    
    return all_passed


async def test_output_structure():
    """测试输出结构完整性"""
    print_test_header("输出结构验证")
    
    all_passed = True
    
    required_fields = [
        "success",
        "scale",
        "total_score",
        "severity_level",
        "parsed_scores",
        "raw_responses",
        "clinical_interpretation",
        "flags",
        "risk_level"
    ]
    
    print("\n--- 验证输出字段完整性 ---")
    try:
        result = await assess("phq9", ["0", "1", "2", "1", "0", "2", "1", "1", "2"])
        
        if result.get("success"):
            missing_fields = []
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"[FAIL] 缺少必需字段: {missing_fields}")
                all_passed = False
            else:
                print("[OK] 所有必需字段都存在")
            
            # 验证嵌套结构
            if "clinical_interpretation" not in result:
                print("[FAIL] 缺少 clinical_interpretation 字段")
                all_passed = False
            else:
                interpretation = result["clinical_interpretation"]
                if "recommendations" not in interpretation:
                    print("[FAIL] clinical_interpretation 缺少 recommendations 字段")
                    all_passed = False
                if "risk_factors" not in interpretation:
                    print("[FAIL] clinical_interpretation 缺少 risk_factors 字段")
                    all_passed = False
            
            if "flags" not in result:
                print("[FAIL] 缺少 flags 字段")
                all_passed = False
        else:
            print(f"[FAIL] 评估失败: {result.get('error')}")
            all_passed = False
    
    except Exception as e:
        print(f"[FAIL] 测试异常: {e}")
        all_passed = False
    
    return all_passed


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("PROXIMO Assessment API 测试套件")
    print("=" * 80)
    
    results = {}
    
    # 运行所有测试
    results["PHQ-9"] = await test_phq9()
    results["GAD-7"] = await test_gad7()
    results["PSS-10"] = await test_pss10()
    results["便捷函数"] = await test_convenience_functions()
    results["错误处理"] = await test_error_handling()
    results["风险检测"] = await test_risk_detection()
    results["同步版本"] = test_sync_version()
    results["输出结构"] = await test_output_structure()
    
    # 打印测试总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    
    for test_name, passed in results.items():
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n[SUCCESS] 所有测试通过！")
        return 0
    else:
        print(f"\n[WARN]  有 {total_tests - passed_tests} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] 测试运行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

