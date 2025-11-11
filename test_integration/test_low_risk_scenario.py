"""
Integration test for Low Risk scenario.

Scenario A: Low Risk
- Teen engages with ChatBot and has a brief conversation
- ChatBot initiates GAD-7 assessment conversationally
- Based on responses, ChatBot assigns low risk-level
- ChatBot continues conversation, offering coping strategies
- Conversation continues until user says goodbye
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


async def test_low_risk_complete_flow():
    """Test complete Low Risk flow."""
    print("=" * 80)
    print("场景 A: Low Risk 完整流程测试")
    print("=" * 80)
    print("\n流程：")
    print("1. 用户与 ChatBot 简短对话")
    print("2. ChatBot 启动 GAD-7 评估")
    print("3. 基于评估结果，分配低风险级别")
    print("4. ChatBot 继续对话，提供应对策略")
    print("5. 用户说再见，对话结束")
    print("=" * 80)
    
    # Initialize services
    questionnaire_service = QuestionnaireService()
    psyguard_service = get_psyguard_service()
    router = RiskRouter()
    pipeline = ConversationPipeline()
    history_service = HistoryService()
    
    user_id = "test_user_low_risk"
    
    # Step 1: Initial conversation (brief chat)
    print("\n[步骤 1] 初始对话")
    print("-" * 80)
    
    user_message_1 = "I've been feeling a bit stressed lately with school."
    print(f"用户: {user_message_1}")
    
    # PsyGUARD monitoring
    psyguard_result_1 = await psyguard_service.score(user_message_1)
    psyguard_score_1 = psyguard_result_1.get("risk_score", 0.0)
    print(f"PsyGUARD 评分: {psyguard_score_1:.3f} (Low Risk)")
    
    # Step 2: Trigger questionnaire (after 5 turns or based on risk)
    print("\n[步骤 2] 触发 GAD-7 评估")
    print("-" * 80)
    
    # Simulate GAD-7 responses (low risk: scores 0-9)
    gad7_responses = ["0", "1", "0", "1", "0", "1", "0"]  # Total: 3 (Low Risk)
    
    print(f"GAD-7 回答: {gad7_responses}")
    gad7_result = await questionnaire_service.assess("gad7", gad7_responses, user_id)
    print(f"GAD-7 总分: {gad7_result.get('total_score', 0)}")
    print(f"严重程度: {gad7_result.get('severity_level', 'unknown')}")
    
    # Step 3: Route decision
    print("\n[步骤 3] 路由决策")
    print("-" * 80)
    
    routing_result = router.decide_from_questionnaires(
        phq9_result={"total_score": 0.0, "parsed_scores": [0] * 9},  # No PHQ-9 yet
        gad7_result=gad7_result,
        chat_risk_score=psyguard_score_1
    )
    
    print(f"路由: {routing_result.route}")
    print(f"Rigid Score: {routing_result.rigid_score:.3f}")
    print(f"原因: {routing_result.reason}")
    
    assert routing_result.route == "low", f"Expected 'low', got '{routing_result.route}'"
    
    # Create control context
    context = ControlContext(
        user_id=user_id,
        route=routing_result.route,
        rigid_score=routing_result.rigid_score,
        psyguard_score=psyguard_score_1,
        questionnaire_gad7_score=gad7_result.get("total_score"),
        route_reason=routing_result.reason
    )
    
    # Step 4: Continue conversation with coping strategies
    print("\n[步骤 4] 继续对话，提供应对策略")
    print("-" * 80)
    
    user_message_2 = "What can I do to feel better?"
    print(f"用户: {user_message_2}")
    
    result_2 = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message_2,
        control_context=context
    )
    
    response_2 = result_2.get("agent_result", {}).get("response", "")
    print(f"ChatBot: {response_2[:200]}...")
    print(f"Agent: {result_2.get('agent_result', {}).get('agent')}")
    
    # Check if coping skills are suggested
    coping_suggested = result_2.get("agent_result", {}).get("coping_skills_suggested", False)
    print(f"建议应对技能: {'是' if coping_suggested else '否'}")
    
    # Step 5: User says goodbye
    print("\n[步骤 5] 用户说再见")
    print("-" * 80)
    
    user_message_3 = "Thanks for your help! Goodbye."
    print(f"用户: {user_message_3}")
    
    result_3 = await pipeline.process_message(
        user_id=user_id,
        user_message=user_message_3,
        control_context=context
    )
    
    response_3 = result_3.get("agent_result", {}).get("response", "")
    print(f"ChatBot: {response_3[:200]}...")
    
    # Check if goodbye was detected
    from src_new.conversation.agents.low_risk_agent import LowRiskAgent
    low_agent = LowRiskAgent()
    is_goodbye = low_agent.is_goodbye(user_message_3)
    print(f"检测到再见: {'是' if is_goodbye else '否'}")
    
    # Step 6: Collect feedback
    print("\n[步骤 6] 收集反馈")
    print("-" * 80)
    
    feedback = history_service.collect_feedback(
        user_id=user_id,
        conversation_id="conv_low_risk",
        route="low",
        satisfaction=4,
        acceptance="accepted",
        follow_up_behavior="none"
    )
    
    print(f"反馈收集成功:")
    print(f"  满意度: {feedback.satisfaction}")
    print(f"  接受程度: {feedback.acceptance}")
    print(f"  后续行为: {feedback.follow_up_behavior}")
    
    print("\n" + "=" * 80)
    print("✅ Low Risk 场景测试完成")
    print("=" * 80)


async def main():
    """Run Low Risk scenario test."""
    try:
        await test_low_risk_complete_flow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

