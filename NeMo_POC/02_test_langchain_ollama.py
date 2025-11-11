"""
POC 2: 测试 LangChain 与 Ollama 集成

验证 LangChain 是否可以正确连接和使用 Ollama 服务。
"""

import asyncio
import sys
from pathlib import Path

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
import httpx


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
                else:
                    print(f"[WARN] 模型 '{settings.MODEL_NAME}' 不在可用模型列表中")
                    print(f"       可用模型: {model_names}")
                    return False
            else:
                return False
    except Exception as e:
        print(f"[ERROR] 连接 Ollama 失败: {e}")
        return False


async def test_langchain_ollama():
    """测试 LangChain 与 Ollama 的集成"""
    
    print("=" * 80)
    print("POC 2: 测试 LangChain 与 Ollama 集成")
    print("=" * 80)
    
    # 1. 检查 Ollama 服务
    print("\n[步骤 1] 检查 Ollama 服务连接...")
    ollama_available = await check_ollama_connection()
    
    if not ollama_available:
        print("❌ Ollama 服务不可用")
        print(f"   请确保 Ollama 正在运行: {settings.OLLAMA_URL}")
        print(f"   请确保模型已下载: ollama pull {settings.MODEL_NAME}")
        return False
    
    print(f"✅ Ollama 服务可用: {settings.OLLAMA_URL}")
    print(f"✅ 模型 '{settings.MODEL_NAME}' 已就绪")
    
    # 2. 测试 LangChain 导入
    print("\n[步骤 2] 测试 LangChain 导入...")
    try:
        from langchain_community.llms import Ollama
        print("✅ LangChain Ollama 导入成功")
    except ImportError as e:
        print(f"❌ LangChain Ollama 导入失败: {e}")
        print("   请运行: pip install langchain-community")
        return False
    
    # 3. 创建 Ollama LLM 实例
    print("\n[步骤 3] 创建 LangChain Ollama LLM 实例...")
    try:
        from langchain_community.llms import Ollama
        
        llm = Ollama(
            base_url=settings.OLLAMA_URL,
            model=settings.MODEL_NAME,
            temperature=0.7
        )
        print("✅ Ollama LLM 实例创建成功")
    except Exception as e:
        print(f"❌ 创建 Ollama LLM 实例失败: {e}")
        return False
    
    # 4. 测试基本调用
    print("\n[步骤 4] 测试基本 LLM 调用...")
    try:
        test_prompt = "Say 'Hello, this is a test' and nothing else."
        print(f"   测试提示: {test_prompt}")
        
        # 同步调用
        response = llm.invoke(test_prompt)
        print(f"✅ LLM 调用成功")
        print(f"   响应: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试异步调用（如果支持）
    print("\n[步骤 5] 测试异步 LLM 调用...")
    try:
        if hasattr(llm, 'ainvoke'):
            response = await llm.ainvoke(test_prompt)
            print(f"✅ 异步 LLM 调用成功")
            print(f"   响应: {response[:100]}...")
        else:
            print("⚠️  LLM 实例不支持异步调用（ainvoke）")
    except Exception as e:
        print(f"⚠️  异步调用失败: {e}")
        print("   这不会影响基本功能")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print("✅ LangChain 与 Ollama 集成测试通过！")
    print("\n下一步：运行 03_test_guardrails_basic.py")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_langchain_ollama())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

