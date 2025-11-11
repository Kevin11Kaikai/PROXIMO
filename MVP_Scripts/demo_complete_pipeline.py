"""
MVP Alpha 演示脚本：完整对话管道

演示完整的 MVP Alpha 流程：
1. Assessment（评估）
2. Routing（路由决策）
3. Policy Execution（策略执行）
4. Session Management（会话管理）
5. Persistence（持久化）

这个脚本展示了 MVP Alpha 的核心功能。
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


async def demo_complete_pipeline():
    """演示完整对话管道"""
    
    print("=" * 80)
    print("MVP Alpha 演示：完整对话管道")
    print("=" * 80)
    print("\n本演示展示 MVP Alpha 的完整流程：")
    print("  1. Assessment（评估）")
    print("  2. Routing（路由决策）")
    print("  3. Policy Execution（策略执行）")
    print("  4. Session Management（会话管理）")
    print("  5. Persistence（持久化）")
    print("=" * 80)
    
    # 检查 Ollama 连接
    print("\n[INFO] 检查 Ollama 服务...")
    ollama_available = await check_ollama_connection()
    
    if ollama_available:
        print(f"[OK] Ollama 服务可用: {settings.OLLAMA_URL}")
        print(f"[OK] 模型 '{settings.MODEL_NAME}' 已就绪")
    else:
        print(f"[WARN] Ollama 服务不可用，将使用回退响应")
        print(f"[INFO] 评估和路由功能仍然正常工作")
    
    # 初始化服务
    llm_service = OllamaService()
    if ollama_available:
        try:
            await llm_service.load_model()
            if llm_service.is_loaded:
                print(f"[OK] LLM 服务初始化成功")
            else:
                print(f"[WARN] LLM 服务加载失败，将使用回退响应")
        except Exception as e:
            print(f"[WARN] LLM 服务加载错误: {e}")
    
    engine = ConversationEngine(llm_service)
    
    # 场景 1: 低风险
    print("\n" + "=" * 80)
    print("[场景 1] 低风险场景（Minimal Severity）")
    print("=" * 80)
    
    request1 = ConversationRequest(
        user_id="demo_user_001",
        scale="phq9",
        responses=["0", "0", "1", "0", "1", "0", "1", "0", "0"],
        user_message="我今天感觉还好，只是有点累。"
    )
    
    result1 = await engine.run_pipeline(request1)
    
    print(f"\n📊 评估结果:")
    print(f"  严重度: {result1.assessment.get('severity_level')}")
    print(f"  总分: {result1.assessment.get('total_score')}")
    print(f"  风险级别: {result1.assessment.get('risk_level', 'N/A')}")
    
    print(f"\n🔄 路由决策:")
    print(f"  路由: {result1.decision.get('route')}")
    print(f"  Rigid Score: {result1.decision.get('rigid_score'):.2f}")
    print(f"  原因: {result1.decision.get('reason')}")
    
    if result1.policy_result:
        print(f"\n💬 策略执行结果:")
        print(f"  策略: {result1.policy_result.get('policy')}")
        print(f"  温度: {result1.policy_result.get('temperature')}")
        response_text = result1.policy_result.get('response', 'N/A')
        if len(response_text) > 150:
            print(f"  响应: {response_text[:150]}...")
        else:
            print(f"  响应: {response_text}")
        if result1.policy_result.get('error'):
            print(f"  [注意] 使用了回退响应（LLM 不可用）")
    
    if result1.context_tail:
        print(f"\n📝 会话上下文（最后 {len(result1.context_tail)} 轮）:")
        for turn in result1.context_tail[-3:]:  # 只显示最后 3 轮
            role = turn.get('role', 'unknown')
            text = turn.get('text', '')[:50]
            print(f"  {role}: {text}...")
    
    print(f"\n⏱️  耗时: {result1.duration_ms:.2f} ms")
    
    # 场景 2: 中等风险
    print("\n" + "=" * 80)
    print("[场景 2] 中等风险场景（Moderate Severity）")
    print("=" * 80)
    
    request2 = ConversationRequest(
        user_id="demo_user_002",
        scale="phq9",
        responses=["1", "1", "2", "2", "1", "2", "1", "2", "0"],
        user_message="我最近一直感到焦虑，睡眠也不好。"
    )
    
    result2 = await engine.run_pipeline(request2)
    
    print(f"\n📊 评估结果:")
    print(f"  严重度: {result2.assessment.get('severity_level')}")
    print(f"  总分: {result2.assessment.get('total_score')}")
    
    print(f"\n🔄 路由决策:")
    print(f"  路由: {result2.decision.get('route')}")
    print(f"  Rigid Score: {result2.decision.get('rigid_score'):.2f}")
    
    if result2.policy_result:
        print(f"\n💬 策略执行结果:")
        print(f"  策略: {result2.policy_result.get('policy')}")
        response_text = result2.policy_result.get('response', 'N/A')
        if len(response_text) > 150:
            print(f"  响应: {response_text[:150]}...")
        else:
            print(f"  响应: {response_text}")
    
    print(f"\n⏱️  耗时: {result2.duration_ms:.2f} ms")
    
    # 场景 3: 高风险（硬锁定 - 自杀意念）
    print("\n" + "=" * 80)
    print("[场景 3] 高风险场景（硬锁定 - 自杀意念）")
    print("=" * 80)
    print("⚠️  这是 MVP Alpha 的安全锁定机制演示")
    
    request3 = ConversationRequest(
        user_id="demo_user_003",
        scale="phq9",
        responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],  # Item 9 = 2
        user_message="我觉得没有意义了。"
    )
    
    result3 = await engine.run_pipeline(request3)
    
    print(f"\n📊 评估结果:")
    print(f"  严重度: {result3.assessment.get('severity_level')}")
    print(f"  总分: {result3.assessment.get('total_score')}")
    print(f"  自杀意念: {result3.assessment.get('flags', {}).get('suicidal_ideation')}")
    print(f"  自杀风险: {result3.assessment.get('suicidal_risk')}")
    
    print(f"\n🔄 路由决策:")
    print(f"  路由: {result3.decision.get('route')}")
    print(f"  Rigid Score: {result3.decision.get('rigid_score'):.2f}")
    print(f"  原因: {result3.decision.get('reason')}")
    print(f"  ⚠️  硬锁定已触发！")
    
    if result3.policy_result:
        print(f"\n💬 策略执行结果:")
        print(f"  策略: {result3.policy_result.get('policy')}")
        print(f"  🔒 使用固定安全脚本（无自由对话）")
        response_text = result3.policy_result.get('response', 'N/A')
        print(f"  响应: {response_text[:200]}...")
        safety_banner = result3.policy_result.get('safety_banner')
        if safety_banner:
            print(f"\n  🚨 安全横幅:")
            print(f"     {safety_banner[:100]}...")
    
    print(f"\n⏱️  耗时: {result3.duration_ms:.2f} ms")
    
    # 总结
    print("\n" + "=" * 80)
    print("演示总结")
    print("=" * 80)
    print(f"  场景 1: {result1.decision.get('route')} 路由（低风险）")
    print(f"  场景 2: {result2.decision.get('route')} 路由（中等风险）")
    print(f"  场景 3: {result3.decision.get('route')} 路由（高风险 - 硬锁定）")
    print("\n✅ MVP Alpha 核心功能演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(demo_complete_pipeline())
    except KeyboardInterrupt:
        print("\n\n[INFO] 演示被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

