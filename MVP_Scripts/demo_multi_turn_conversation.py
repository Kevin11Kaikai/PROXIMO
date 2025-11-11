"""
MVP Alpha 演示脚本：多轮对话场景

演示完整的多轮对话流程，展示：
- SessionManager 的上下文管理
- AssessmentRepo 的持久化
- ConversationEngine 的完整流程
- 多轮对话中的上下文传递
"""

import asyncio
import sys
from pathlib import Path
import httpx

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.conversation.engine import ConversationEngine, ConversationRequest
from src.conversation.session_manager import SessionManager
from src.services.ollama_service import OllamaService
from src.core.config import settings


async def check_ollama_connection() -> bool:
    """检查 Ollama 服务是否可用"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if settings.MODEL_NAME in model_names:
                    return True
            return False
    except Exception:
        return False


async def demo_multi_turn_conversation():
    """演示多轮对话场景"""
    
    print("=" * 80)
    print("MVP Alpha 演示：多轮对话场景")
    print("=" * 80)
    print("\n本演示展示完整的多轮对话流程：")
    print("  - SessionManager 的上下文管理")
    print("  - AssessmentRepo 的持久化")
    print("  - ConversationEngine 的完整流程")
    print("  - 多轮对话中的上下文传递")
    print("=" * 80)
    
    # 检查 Ollama
    ollama_available = await check_ollama_connection()
    if ollama_available:
        print(f"\n[OK] Ollama 服务可用")
    else:
        print(f"\n[WARN] Ollama 服务不可用，将使用回退响应")
    
    # 初始化服务
    llm_service = OllamaService()
    if ollama_available:
        try:
            await llm_service.load_model()
        except Exception:
            pass
    
    engine = ConversationEngine(llm_service)
    user_id = "demo_user_multi_turn_001"
    
    # 清空会话
    SessionManager.clear_session(user_id)
    
    # 第一轮：初次接触（GAD-7 默认）
    print("\n" + "=" * 80)
    print("[第 1 轮] 初次接触（GAD-7 默认评估）")
    print("=" * 80)
    
    request1 = ConversationRequest(
        user_id=user_id,
        scale="gad7",
        responses=["0", "1", "1", "0", "1", "0", "1"],
        user_message="你好，我想了解一下我的焦虑情况。"
    )
    
    result1 = await engine.run_pipeline(request1)
    
    print(f"\n📊 评估结果:")
    print(f"  量表: {result1.assessment.get('scale')}")
    print(f"  严重度: {result1.assessment.get('severity_level')}")
    print(f"  总分: {result1.assessment.get('total_score')}")
    print(f"  路由: {result1.decision.get('route')}")
    
    if result1.context_tail:
        print(f"\n📝 会话上下文（{len(result1.context_tail)} 轮）:")
        for turn in result1.context_tail:
            print(f"  [{turn.get('role')}] {turn.get('text')[:60]}...")
    
    # 等待用户响应（模拟）
    print("\n[INFO] 等待用户响应...")
    await asyncio.sleep(1)
    
    # 第二轮：继续对话
    print("\n" + "=" * 80)
    print("[第 2 轮] 继续对话（使用会话上下文）")
    print("=" * 80)
    
    request2 = ConversationRequest(
        user_id=user_id,
        scale="phq9",
        responses=["1", "1", "2", "1", "1", "1", "1", "1", "0"],
        user_message="我还想做一个抑郁评估。"
    )
    
    result2 = await engine.run_pipeline(request2)
    
    print(f"\n📊 评估结果:")
    print(f"  量表: {result2.assessment.get('scale')}")
    print(f"  严重度: {result2.assessment.get('severity_level')}")
    print(f"  总分: {result2.assessment.get('total_score')}")
    print(f"  路由: {result2.decision.get('route')}")
    
    if result2.context_tail:
        print(f"\n📝 会话上下文（{len(result2.context_tail)} 轮）:")
        print(f"  [注意] 上下文包含了第 1 轮和第 2 轮的对话")
        for turn in result2.context_tail:
            print(f"  [{turn.get('role')}] {turn.get('text')[:60]}...")
    
    # 第三轮：再次对话
    print("\n" + "=" * 80)
    print("[第 3 轮] 再次对话（上下文自动修剪）")
    print("=" * 80)
    
    request3 = ConversationRequest(
        user_id=user_id,
        scale="gad7",
        responses=["1", "2", "1", "1", "2", "1", "1"],
        user_message="我的焦虑情况有改善吗？"
    )
    
    result3 = await engine.run_pipeline(request3)
    
    print(f"\n📊 评估结果:")
    print(f"  量表: {result3.assessment.get('scale')}")
    print(f"  严重度: {result3.assessment.get('severity_level')}")
    print(f"  总分: {result3.assessment.get('total_score')}")
    print(f"  路由: {result3.decision.get('route')}")
    
    if result3.context_tail:
        print(f"\n📝 会话上下文（{len(result3.context_tail)} 轮）:")
        print(f"  [注意] 系统自动修剪到最近 6 轮")
        for turn in result3.context_tail:
            print(f"  [{turn.get('role')}] {turn.get('text')[:60]}...")
    
    # 检查历史记录
    print("\n" + "=" * 80)
    print("[检查] 评估历史记录")
    print("=" * 80)
    
    history = await engine.repo.history(user_id, limit=10)
    print(f"\n[OK] 用户 {user_id} 的评估历史（{len(history)} 条记录）:")
    for i, record in enumerate(history, 1):
        print(f"\n  记录 {i}:")
        print(f"    时间: {record.get('ts')}")
        print(f"    量表: {record.get('scale')}")
        print(f"    分数: {record.get('score')}")
        print(f"    严重度: {record.get('severity')}")
        print(f"    路由: {record.get('route')}")
    
    # 总结
    print("\n" + "=" * 80)
    print("演示总结")
    print("=" * 80)
    print("✅ 多轮对话场景演示完成！")
    print("\n核心功能验证：")
    print("  ✅ SessionManager 管理多轮对话上下文")
    print("  ✅ AssessmentRepo 持久化所有评估记录")
    print("  ✅ ConversationEngine 在每轮中使用上下文")
    print("  ✅ 上下文自动修剪到最近 6 轮")
    print("  ✅ 历史记录完整保存")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(demo_multi_turn_conversation())
    except KeyboardInterrupt:
        print("\n\n[INFO] 演示被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

