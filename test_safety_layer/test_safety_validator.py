"""
Test SafetyValidator functionality.

Tests content validation and safety checks.
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

from src_new.safety.safety_validator import SafetyValidator
from src_new.conversation.agents.high_risk_agent import FIXED_SAFETY_SCRIPT


def test_validate_response_content():
    """Test response content validation."""
    print("\n" + "=" * 80)
    print("测试 1: 响应内容验证")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "安全响应（Low Risk）",
            "response": "I understand how you're feeling. Let's try some breathing exercises.",
            "route": "low",
            "expected_valid": True
        },
        {
            "name": "包含禁止内容",
            "response": "Here's how to kill yourself: ...",
            "route": "low",
            "expected_valid": False
        },
        {
            "name": "High Risk 响应（包含必需元素）",
            "response": FIXED_SAFETY_SCRIPT,
            "route": "high",
            "expected_valid": True
        },
        {
            "name": "High Risk 响应（缺少必需元素）",
            "response": "I'm here to help you.",
            "route": "high",
            "expected_valid": False
        }
    ]
    
    for test_case in test_cases:
        result = SafetyValidator.validate_response_content(
            response=test_case["response"],
            route=test_case["route"]
        )
        
        expected = test_case["expected_valid"]
        actual = result["valid"]
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} {test_case['name']}: 预期={expected}, 实际={actual}")
        if result.get("issues"):
            print(f"      问题: {result['issues']}")


def test_validate_fixed_script():
    """Test fixed script validation."""
    print("\n" + "=" * 80)
    print("测试 2: 固定脚本验证")
    print("=" * 80)
    
    result = SafetyValidator.validate_fixed_script(FIXED_SAFETY_SCRIPT)
    
    print(f"   脚本长度: {result['script_length']} 字符")
    print(f"   验证结果: {'✅ 通过' if result['valid'] else '❌ 失败'}")
    
    if result.get("missing_elements"):
        print(f"   缺少元素: {result['missing_elements']}")
    else:
        print(f"   ✅ 包含所有必需元素")
    
    if result.get("has_prohibited"):
        print(f"   ❌ 包含禁止内容")
    else:
        print(f"   ✅ 不包含禁止内容")
    
    assert result["valid"], "Fixed script should be valid"


def test_check_user_message_safety():
    """Test user message safety check."""
    print("\n" + "=" * 80)
    print("测试 3: 用户消息安全检查")
    print("=" * 80)
    
    test_cases = [
        {
            "message": "I want to kill myself",
            "expected_crisis": True
        },
        {
            "message": "I'm thinking about suicide",
            "expected_crisis": True
        },
        {
            "message": "I feel sad today",
            "expected_crisis": False
        },
        {
            "message": "Can you help me?",
            "expected_crisis": False
        },
        {
            "message": "There's no point in living anymore",
            "expected_crisis": True
        }
    ]
    
    for test_case in test_cases:
        result = SafetyValidator.check_user_message_safety(test_case["message"])
        
        expected = test_case["expected_crisis"]
        actual = result["is_crisis"]
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} '{test_case['message'][:50]}...': 预期危机={expected}, 实际={actual}")
        if result.get("detected_keywords"):
            print(f"      检测到关键词: {result['detected_keywords']}")


def test_prohibited_patterns():
    """Test prohibited pattern detection."""
    print("\n" + "=" * 80)
    print("测试 4: 禁止模式检测")
    print("=" * 80)
    
    test_cases = [
        ("Here's how to kill yourself", True),
        ("I can tell you suicide methods", True),
        ("Ways to end your life", True),
        ("How to commit suicide", True),
        ("I'm here to help you", False),
        ("Let's talk about your feelings", False),
    ]
    
    for message, should_detect in test_cases:
        result = SafetyValidator.validate_response_content(
            response=message,
            route="low"
        )
        
        detected = not result["valid"]
        status = "✅" if detected == should_detect else "❌"
        print(f"   {status} '{message[:40]}...': 预期检测={should_detect}, 实际={detected}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("SafetyValidator 测试")
    print("=" * 80)
    print("\n此脚本将测试安全验证器")
    print("包括：响应验证、固定脚本验证、用户消息检查")
    print("=" * 80)
    
    test_validate_response_content()
    test_validate_fixed_script()
    test_check_user_message_safety()
    test_prohibited_patterns()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

