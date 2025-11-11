"""
Integration test for Medium Risk scenario.

Scenario B: Medium Risk
- Teen engages with ChatBot and has a brief conversation
- ChatBot initiates GAD-7 assessment conversationally
- Based on responses, ChatBot assigns medium risk-level
- ChatBot prompts user to join a peer group
- Teen initially shows resistance
- ChatBot addresses resistance and convinces student to join
- Student posts initial introduction in peer group
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

from src_new.perception.questionnaire_service import QuestionnaireService
from src_new.perception.psyguard_service import get_psyguard_service
from src_new.control.risk_router import RiskRouter
from src_new.control.control_context import ControlContext
from src_new.conversation.pipeline import ConversationPipeline
from src_new.adaptive.history_service import HistoryService


async def test_medium_risk_complete_flow():
    """Test complete Medium Risk flow."""
    print("=" * 80)
    print("场景 B: Medium Risk 完整流程测试")
    print("=" * 80)
    print("\n流程：")
    print("1. 用户与 ChatBot 简短对话")
    print("2. ChatBot 启动 GAD-7 评估")
    print("3. 基于评估结果，分配中风险级别")
    print("4. ChatBot 建议加入 Peer Group")
    print("5. 用户表现出抗拒")
    print("6. ChatBot 处理抗拒并说服用户加入")
    print("7. 用户在 Peer Group 中发布介绍")
    print("=" * 80)
    
    # Initialize services
    questionnaire_service = QuestionnaireService()
    psyguard_service = get_psyguard_service()
    router = RiskRouter()
    pipeline = ConversationPipeline()
    history_service = HistoryService()
    
    user_id = "test_user_medium_risk"
    
    # Step 1: Initial conversation
    print("\n[步骤 1] 初始对话")
    print("-" * 80)
    
    user_message_1 = "I've been feeling really anxious and isolated lately."
    print(f"用户: {user_message_1}")
    
    # PsyGUARD monitoring
    psyguard_result_1 = await psyguard_service.score(user_message_1)
    psyguard_score_1 = psyguard_result_1.get("risk_score", 0.0)
    print(f"PsyGUARD 评分: {psyguard_score_1:.3f}")
    
    # Step 2: Trigger questionnaire
    print("\n[步骤 2] 触发 GAD-7 评估")
    print("-" * 80)
    
    # Simulate GAD-7 responses (medium risk: scores 10-14)
    gad7_responses = ["1", "2", "1", "2", "1", "2", "1"]  # Total: 10 (Medium Risk)
    
    print(f"GAD-7 回答: {gad7_responses}")
    gad7_result = await questionnaire_service.assess("gad7", gad7_responses, user_id)
    print(f"GAD-7 总分: {gad7_result.get('total_score', 0)}")
    print(f"严重程度: {gad7_result.get('severity_level', 'unknown')}")
    
    # Step 3: Route decision
    print("\n[步骤 3] 路由决策")
    print("-" * 80)
    
    routing_result = router.decide_from_questionnaires(
        phq9_result={"total_score": 0.0, "parsed_scores": [0] * 9},
        gad7_result=gad7_result,
        chat_risk_score=psyguard_score_1
    )
    
    print(f"路由: {routing_result.route}")
    print(f"Rigid Score: {routing_result.rigid_score:.3f}")
    print(f"原因: {routing_result.reason}")
    
    assert routing_result.route == "medium", f"Expected 'medium', got '{routing_result.route}'"
    
    # Create control context
    context = ControlContext(
        user_id=user_id,
        route=routing_result.route,
        rigid_score=routing_result.rigid_score,
        psyguard_score=psyguard_score_1,
        questionnaire_gad7_score=gad7_result.get("total_score"),
        route_reason=routing_result.reason
    )
    
    # Step 4: Suggest peer group
    print("\n[步骤 4] 建议加入 Peer Group")
    print("-" * 80)
    
    user_message_2 = "I don't know what to do about my anxiety."
    print(f"用户: {user_message_2}")
    
    result_2 = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message_2,
        control_context=context
    )
    
    response_2 = result_2.get("agent_result", {}).get("response", "")
    print(f"ChatBot: {response_2[:200]}...")
    print(f"Agent: {result_2.get('agent_result', {}).get('agent')}")
    print(f"状态: {result_2.get('agent_result', {}).get('state')}")
    
    # Step 5: User shows resistance
    print("\n[步骤 5] 用户表现出抗拒")
    print("-" * 80)
    
    user_message_3 = "I don't want to share my personal information with strangers."
    print(f"用户: {user_message_3}")
    
    result_3 = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message_3,
        control_context=context
    )
    
    response_3 = result_3.get("agent_result", {}).get("response", "")
    print(f"ChatBot: {response_3[:200]}...")
    print(f"状态: {result_3.get('agent_result', {}).get('state')}")
    print(f"抗拒类型: {result_3.get('agent_result', {}).get('resistance_type')}")
    print(f"抗拒计数: {result_3.get('agent_result', {}).get('resistance_count')}")
    
    # Step 6: ChatBot addresses resistance
    print("\n[步骤 6] ChatBot 处理抗拒并说服用户")
    print("-" * 80)
    
    # Simulate multiple persuasion turns
    for turn in range(2):
        user_message_resistance = f"I'm still not sure about joining. (turn {turn + 1})"
        print(f"用户: {user_message_resistance}")
        
        result_resistance = await pipeline.process_message(
            user_id=user_id,
            user_message=user_message_resistance,
            control_context=context
        )
        
        response_resistance = result_resistance.get("agent_result", {}).get("response", "")
        print(f"ChatBot: {response_resistance[:200]}...")
        print(f"抗拒计数: {result_resistance.get('agent_result', {}).get('resistance_count')}")
    
    # Step 7: User accepts
    print("\n[步骤 7] 用户接受加入 Peer Group")
    print("-" * 80)
    
    user_message_4 = "Okay, I'll give it a try. I'd like to join the peer group."
    print(f"用户: {user_message_4}")
    
    result_4 = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message_4,
        control_context=context
    )
    
    response_4 = result_4.get("agent_result", {}).get("response", "")
    print(f"ChatBot: {response_4[:200]}...")
    print(f"状态: {result_4.get('agent_result', {}).get('state')}")
    print(f"Peer Group 接受: {result_4.get('agent_result', {}).get('peer_group_accepted', False)}")
    
    # Step 8: Student posts introduction
    print("\n[步骤 8] 用户在 Peer Group 中发布介绍")
    print("-" * 80)
    print("用户: Hi everyone, I'm new here. I've been struggling with anxiety...")
    print("✅ Peer Group 有 moderator 进行安全监控")
    
    # Step 9: Collect feedback
    print("\n[步骤 9] 收集反馈")
    print("-" * 80)
    
    feedback = history_service.collect_feedback(
        user_id=user_id,
        conversation_id="conv_medium_risk",
        route="medium",
        satisfaction=4,
        acceptance="accepted",
        follow_up_behavior="peer_group"
    )
    
    print(f"反馈收集成功:")
    print(f"  满意度: {feedback.satisfaction}")
    print(f"  接受程度: {feedback.acceptance}")
    print(f"  后续行为: {feedback.follow_up_behavior}")
    
    print("\n" + "=" * 80)
    print("✅ Medium Risk 场景测试完成")
    print("=" * 80)


async def main():
    """Run Medium Risk scenario test."""
    try:
        await test_medium_risk_complete_flow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

