"""
Integration test for Perception Layer.

Tests the complete Perception Layer workflow:
1. PsyGUARD scoring
2. Questionnaire triggering
3. Questionnaire assessment
4. Route mapping
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

from src_new.perception.psyguard_service import PsyGuardService, get_psyguard_service
from src_new.perception.questionnaire_trigger import QuestionnaireTrigger
from src_new.perception.questionnaire_service import QuestionnaireService
from src_new.perception.questionnaire_mapper import QuestionnaireMapper


async def test_complete_workflow():
    """Test complete Perception Layer workflow."""
    print("\n" + "=" * 80)
    print("测试: 完整 Perception Layer 工作流程")
    print("=" * 80)
    
    # 初始化服务
    psyguard = get_psyguard_service()
    trigger = QuestionnaireTrigger(turn_threshold=5)
    questionnaire = QuestionnaireService()
    
    # 场景 1: 正常对话（5 轮后触发问卷）
    print("\n场景 1: 正常对话流程")
    print("-" * 80)
    
    conversation_turns = [
        "I'm feeling a bit stressed",
        "School is really overwhelming",
        "I have a lot of homework",
        "Sometimes I feel anxious",
        "But I'm managing okay"
    ]
    
    turn_count = 0
    for i, message in enumerate(conversation_turns, 1):
        turn_count = i
        print(f"\n轮次 {i}: {message}")
        
        # PsyGUARD 评分
        psyguard_result = await psyguard.score(message)
        print(f"  PsyGUARD 分数: {psyguard_result['risk_score']:.3f}")
        
        # 检查是否触发问卷
        trigger_result = trigger.check_trigger(turn_count, psyguard_result)
        if trigger_result.should_trigger:
            print(f"  ✅ 触发问卷: {trigger_result.reason}")
            break
    
    if trigger_result.should_trigger:
        # 执行问卷评估
        print(f"\n执行问卷评估...")
        # 模拟问卷响应（实际应该从用户获取）
        phq9_responses = ["0", "0", "1", "0", "0", "1", "0", "0", "0"]
        gad7_responses = ["0", "0", "1", "0", "0", "1", "0"]
        
        phq9_result = await questionnaire.assess("phq9", phq9_responses, persona_id="test_user")
        gad7_result = await questionnaire.assess("gad7", gad7_responses, persona_id="test_user")
        
        print(f"  PHQ-9 分数: {phq9_result.get('total_score')}")
        print(f"  GAD-7 分数: {gad7_result.get('total_score')}")
        
        # 获取 PHQ-9 Q9 分数
        phq9_q9 = phq9_result.get('parsed_scores', [])[8] if len(phq9_result.get('parsed_scores', [])) > 8 else 0
        
        # 获取最新的 PsyGUARD 分数
        latest_psyguard = psyguard_result['risk_score']
        
        # 最终路由决策
        final_route = QuestionnaireMapper.final_route_decision(
            phq9_score=phq9_result.get('total_score', 0),
            gad7_score=gad7_result.get('total_score', 0),
            phq9_q9_score=phq9_q9,
            chat_risk_score=latest_psyguard
        )
        
        print(f"\n  ✅ 最终路由: {final_route}")
    
    # 场景 2: 提前触发（自杀意图）
    print("\n\n场景 2: 提前触发问卷（自杀意图检测）")
    print("-" * 80)
    
    suicide_message = "I'm thinking about ending my life"
    print(f"\n轮次 1: {suicide_message}")
    
    psyguard_result = await psyguard.score(suicide_message)
    print(f"  PsyGUARD 分数: {psyguard_result['risk_score']:.3f}")
    print(f"  检测标签: {psyguard_result['labels']}")
    
    trigger_result = trigger.check_trigger(1, psyguard_result)
    if trigger_result.should_trigger:
        print(f"  ✅ 提前触发问卷: {trigger_result.reason}")
        if trigger_result.immediate_route:
            print(f"  立即路由: {trigger_result.immediate_route}")


async def main():
    """Run integration test."""
    print("=" * 80)
    print("Perception Layer 集成测试")
    print("=" * 80)
    print("\n此脚本将测试完整的 Perception Layer 工作流程")
    print("包括：PsyGUARD 评分、问卷触发、问卷评估、路由映射")
    print("\n注意：")
    print("- 需要 PsyGUARD 模型文件")
    print("- 需要 Ollama 服务运行（用于问卷评估）")
    print("=" * 80)
    
    await test_complete_workflow()
    
    print("\n" + "=" * 80)
    print("集成测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

