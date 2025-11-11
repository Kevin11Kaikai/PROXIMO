"""
Test PsyGUARD service integration.

Tests the PsyGUARD-RoBERTa model loading and risk scoring functionality.
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

from src_new.perception.psyguard_service import (
    PsyGuardService,
    get_psyguard_service,
    SUICIDE_INTENT_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    LOW_RISK_CLEAR_THRESHOLD
)


async def test_psyguard_initialization():
    """Test PsyGUARD service initialization."""
    print("\n" + "=" * 80)
    print("测试 1: PsyGUARD 服务初始化")
    print("=" * 80)
    
    try:
        service = PsyGuardService()
        print(f"✅ PsyGuardService 创建成功")
        print(f"   模型路径: {service.model_path}")
        print(f"   设备: {service.device}")
        print(f"   启用状态: {service.enabled}")
        
        # 尝试加载模型
        print("\n   正在加载模型...")
        result = await service.load()
        
        if result:
            print("✅ 模型加载成功")
            print(f"   加载状态: {service.is_loaded()}")
        else:
            print("⚠️  模型加载失败（可能是模型文件不存在或环境问题）")
            print("   这不会影响其他测试，但 PsyGUARD 功能将不可用")
        
        return service
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_risk_scoring(service: PsyGuardService):
    """Test risk scoring with various messages."""
    print("\n" + "=" * 80)
    print("测试 2: 风险评分功能")
    print("=" * 80)
    
    if not service.is_loaded():
        print("⚠️  模型未加载，跳过评分测试")
        return
    
    test_cases = [
        {
            "name": "正常消息",
            "message": "I'm feeling a bit anxious today, but I'm managing.",
            "expected_range": (0.0, LOW_RISK_CLEAR_THRESHOLD)
        },
        {
            "name": "中等风险消息",
            "message": "I feel so alone, no one understands me.",
            "expected_range": (MEDIUM_RISK_THRESHOLD - 0.2, MEDIUM_RISK_THRESHOLD + 0.2)
        },
        {
            "name": "自杀意图消息",
            "message": "I'm thinking about ending my life.",
            "expected_range": (SUICIDE_INTENT_THRESHOLD, 1.0)
        },
        {
            "name": "极高风险消息",
            "message": "I have a plan to kill myself and I'm going to do it soon.",
            "expected_range": (HIGH_RISK_DIRECT_THRESHOLD, 1.0)
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   测试: {test_case['name']}")
        print(f"   消息: {test_case['message']}")
        
        try:
            result = await service.score(test_case['message'])
            
            print(f"   风险分数: {result['risk_score']:.3f}")
            print(f"   检测标签: {result['labels']}")
            print(f"   触发问卷: {result['should_trigger_questionnaire']}")
            print(f"   直接高风险: {result['should_direct_high_risk']}")
            
            # 验证阈值
            risk_score = result['risk_score']
            if risk_score >= SUICIDE_INTENT_THRESHOLD:
                if not result['should_trigger_questionnaire']:
                    print("   ⚠️  应该触发问卷但未触发")
                else:
                    print("   ✅ 正确触发问卷")
            
            if risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
                if not result['should_direct_high_risk']:
                    print("   ⚠️  应该是直接高风险但未标记")
                else:
                    print("   ✅ 正确标记为直接高风险")
            
        except Exception as e:
            print(f"   ❌ 评分失败: {e}")
            import traceback
            traceback.print_exc()


async def test_thresholds():
    """Test threshold constants."""
    print("\n" + "=" * 80)
    print("测试 3: 阈值常量验证")
    print("=" * 80)
    
    print(f"   自杀意图阈值: {SUICIDE_INTENT_THRESHOLD}")
    print(f"   直接高风险阈值: {HIGH_RISK_DIRECT_THRESHOLD}")
    print(f"   中等风险阈值: {MEDIUM_RISK_THRESHOLD}")
    print(f"   低风险清除阈值: {LOW_RISK_CLEAR_THRESHOLD}")
    
    # 验证阈值顺序
    assert HIGH_RISK_DIRECT_THRESHOLD > SUICIDE_INTENT_THRESHOLD, "直接高风险阈值应该大于自杀意图阈值"
    assert SUICIDE_INTENT_THRESHOLD > MEDIUM_RISK_THRESHOLD, "自杀意图阈值应该大于中等风险阈值"
    assert MEDIUM_RISK_THRESHOLD > LOW_RISK_CLEAR_THRESHOLD, "中等风险阈值应该大于低风险清除阈值"
    
    print("   ✅ 阈值顺序正确")


async def test_disabled_service():
    """Test disabled service behavior."""
    print("\n" + "=" * 80)
    print("测试 4: 禁用服务行为")
    print("=" * 80)
    
    service = PsyGuardService(enabled=False)
    result = await service.score("I'm thinking about suicide")
    
    assert result['risk_score'] == 0.0, "禁用服务应该返回 0.0"
    assert not result['should_trigger_questionnaire'], "禁用服务不应该触发问卷"
    assert result['enabled'] is False, "应该标记为禁用"
    
    print("   ✅ 禁用服务行为正确")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("PsyGUARD Service 测试")
    print("=" * 80)
    print("\n此脚本将测试 PsyGUARD 服务的初始化和风险评分功能")
    print("\n注意：")
    print("- 需要 PsyGUARD-RoBERTa 模型文件在 PsyGUARD-RoBERTa/ 目录")
    print("- 如果模型未加载，部分测试将被跳过")
    print("=" * 80)
    
    # 测试阈值
    await test_thresholds()
    
    # 测试初始化
    service = await test_psyguard_initialization()
    
    # 测试评分
    if service:
        await test_risk_scoring(service)
    
    # 测试禁用服务
    await test_disabled_service()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

