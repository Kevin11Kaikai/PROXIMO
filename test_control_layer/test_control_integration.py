"""
Integration test for Control Layer.

Tests the complete Control Layer workflow:
1. Risk routing from questionnaires
2. Route updates based on PsyGUARD scores
3. ControlContext management
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

from src_new.control.risk_router import RiskRouter
from src_new.control.route_updater import RouteUpdater
from src_new.control.control_context import ControlContext
from src_new.perception.psyguard_service import get_psyguard_service


async def test_complete_control_workflow():
    """Test complete Control Layer workflow."""
    print("\n" + "=" * 80)
    print("测试: 完整 Control Layer 工作流程")
    print("=" * 80)
    
    router = RiskRouter()
    updater = RouteUpdater()
    psyguard = get_psyguard_service()
    
    # 场景 1: 初始路由决策（基于问卷）
    print("\n场景 1: 初始路由决策")
    print("-" * 80)
    
    phq9_result = {
        "total_score": 12.0,
        "parsed_scores": [1, 1, 2, 1, 1, 1, 1, 1, 1]
    }
    gad7_result = {
        "total_score": 10.0,
        "parsed_scores": [1, 1, 2, 1, 1, 2, 2]
    }
    
    routing_result = router.decide_from_questionnaires(
        phq9_result=phq9_result,
        gad7_result=gad7_result,
        chat_risk_score=None
    )
    
    print(f"  初始路由: {routing_result.route}")
    print(f"  Rigid Score: {routing_result.rigid_score:.3f}")
    print(f"  原因: {routing_result.reason}")
    
    # 创建 ControlContext
    context = ControlContext(
        user_id="test_user",
        route=routing_result.route,
        rigid_score=routing_result.rigid_score,
        questionnaire_phq9_score=phq9_result["total_score"],
        questionnaire_gad7_score=gad7_result["total_score"],
        route_reason=routing_result.reason,
        route_source="questionnaire_mapper"
    )
    
    print(f"  ✅ ControlContext 创建: route={context.route}")
    
    # 场景 2: 路由更新（Low → Medium）
    print("\n场景 2: 路由更新（Low → Medium）")
    print("-" * 80)
    
    # 模拟用户在 Low Risk 路径中，但 PsyGUARD 检测到 Medium Risk
    context.route = "low"
    context.rigid_score = 0.2
    
    user_message = "I feel so alone, no one understands me"
    psyguard_result = await psyguard.score(user_message)
    new_psyguard_score = psyguard_result.get("risk_score", 0.0)
    
    print(f"  当前路由: {context.route}")
    print(f"  新 PsyGUARD 分数: {new_psyguard_score:.3f}")
    
    # 检查是否需要升级
    if updater.should_upgrade(context.route, new_psyguard_score):
        new_route = updater.get_upgrade_target(context.route, new_psyguard_score)
        context.update_route(new_route, reason="psyguard_upgrade")
        context.psyguard_score = new_psyguard_score
        print(f"  ✅ 路由升级: {context.route}")
        print(f"     原因: {context.route_reason}")
    else:
        print(f"  ✅ 路由保持不变: {context.route}")
    
    # 场景 3: Medium 不降级
    print("\n场景 3: Medium 不降级")
    print("-" * 80)
    
    context.route = "medium"
    context.rigid_score = 0.6
    
    # 即使用户情绪好转（PsyGUARD 分数降低）
    low_risk_message = "I'm feeling better today"
    psyguard_result = await psyguard.score(low_risk_message)
    new_psyguard_score = psyguard_result.get("risk_score", 0.0)
    
    print(f"  当前路由: {context.route}")
    print(f"  新 PsyGUARD 分数: {new_psyguard_score:.3f}")
    
    updated_route = updater.update_route(context.route, new_psyguard_score)
    if updated_route != context.route:
        context.update_route(updated_route, reason="route_update")
    
    assert updated_route == "medium", "Medium 路由不应该降级"
    print(f"  ✅ Medium 路由保持不变: {updated_route}")
    
    # 场景 4: High 不降级
    print("\n场景 4: High 不降级")
    print("-" * 80)
    
    context.route = "high"
    context.rigid_score = 1.0
    
    # 即使 PsyGUARD 分数降低
    updated_route = updater.update_route(context.route, 0.3)
    
    assert updated_route == "high", "High 路由不应该降级"
    print(f"  ✅ High 路由保持不变: {updated_route}")


async def main():
    """Run integration test."""
    print("=" * 80)
    print("Control Layer 集成测试")
    print("=" * 80)
    print("\n此脚本将测试完整的 Control Layer 工作流程")
    print("包括：路由决策、路由更新、上下文管理")
    print("\n注意：")
    print("- 需要 PsyGUARD 模型文件（用于 PsyGUARD 评分）")
    print("- 如果模型未加载，将使用占位分数")
    print("=" * 80)
    
    await test_complete_control_workflow()
    
    print("\n" + "=" * 80)
    print("集成测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

