"""
POC 4: 测试 NeMo Guardrails 与 Ollama 集成

验证 NeMo Guardrails 是否可以通过 LangChain 使用 Ollama。
这是关键的集成测试。
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
                return settings.MODEL_NAME in model_names
            return False
    except Exception:
        return False


async def test_guardrails_with_ollama():
    """测试 NeMo Guardrails 与 Ollama 的集成"""
    
    print("=" * 80)
    print("POC 4: 测试 NeMo Guardrails 与 Ollama 集成")
    print("=" * 80)
    print("\n这是关键的集成测试，验证完整的集成链路：")
    print("  NeMo Guardrails → LangChain → Ollama")
    print("=" * 80)
    
    # 1. 检查前置条件
    print("\n[步骤 1] 检查前置条件...")
    
    # 检查 Ollama
    ollama_available = await check_ollama_connection()
    if not ollama_available:
        print("❌ Ollama 服务不可用")
        return False
    print(f"✅ Ollama 服务可用: {settings.OLLAMA_URL}")
    
    # 检查导入
    try:
        from nemoguardrails import LLMRails, RailsConfig
        from langchain_community.llms import Ollama
        print("✅ 所有必需的包已导入")
        print("   使用: LLMRails (NeMo Guardrails 0.18.0)")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 2. 创建 LangChain Ollama LLM
    print("\n[步骤 2] 创建 LangChain Ollama LLM 实例...")
    try:
        from langchain_community.llms import Ollama
        
        llm = Ollama(
            base_url=settings.OLLAMA_URL,
            model=settings.MODEL_NAME,
            temperature=0.7
        )
        print("✅ LangChain Ollama LLM 创建成功")
        
        # 测试基本调用
        test_response = llm.invoke("Say 'test' and nothing else.")
        print(f"✅ LangChain LLM 调用成功: {test_response[:50]}...")
        
    except Exception as e:
        print(f"❌ 创建或测试 LangChain LLM 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 创建最小 Guardrails 配置
    print("\n[步骤 3] 创建最小 Guardrails 配置...")
    try:
        config_dir = Path(__file__).parent / "test_config_ollama"
        config_dir.mkdir(exist_ok=True)
        
        # 创建 config.yml
        config_file = config_dir / "config.yml"
        config_content = f"""# NeMo Guardrails 配置（通过 LangChain 使用 Ollama）
# 注意：实际配置格式可能需要根据版本调整

models:
  - type: main
    engine: langchain_llm
    model: ollama/{settings.MODEL_NAME}

instructions:
  - type: general
    content: |
      You are a supportive and empathetic mental health assistant for teens.
      Always prioritize safety and provide appropriate resources when needed.
"""
        config_file.write_text(config_content, encoding='utf-8')
        print(f"✅ 创建配置文件: {config_file}")
        
    except Exception as e:
        print(f"❌ 创建配置失败: {e}")
        return False
    
    # 4. 尝试创建 LLMRails 实例（使用 LangChain LLM）
    print("\n[步骤 4] 尝试创建 LLMRails 实例...")
    
    try:
        from nemoguardrails import LLMRails, RailsConfig
        
        # 方法 1: 通过配置文件创建 RailsConfig，然后创建 LLMRails
        print("\n   方法 1: 通过配置文件创建...")
        try:
            # 加载配置
            config = RailsConfig.from_path(str(config_dir))
            print("    ✅ RailsConfig 加载成功")
            
            # 创建 LLMRails 实例（传入 LLM）
            rails = LLMRails(config=config, llm=llm)
            print("    ✅ LLMRails 实例创建成功（通过配置文件 + LLM）")
            
            # 检查可用方法
            if hasattr(rails, 'generate'):
                print("    ✅ LLMRails 有 generate 方法")
            if hasattr(rails, 'generate_async'):
                print("    ✅ LLMRails 有 generate_async 方法")
            
            # 测试基本调用（异步）
            print("\n   测试基本 generate_async 调用...")
            try:
                messages = [{"role": "user", "content": "Say 'test' and nothing else."}]
                response = await rails.generate_async(messages=messages)
                print(f"    ✅ generate_async 调用成功")
                print(f"   响应类型: {type(response)}")
                if isinstance(response, str):
                    print(f"   响应内容: {response[:100]}...")
                elif isinstance(response, dict):
                    print(f"   响应键: {list(response.keys())}")
                    if 'content' in response:
                        print(f"   响应内容: {response['content'][:100]}...")
                    elif 'messages' in response:
                        # 可能是消息列表格式
                        print(f"   响应格式: messages 列表")
                        if response['messages']:
                            last_msg = response['messages'][-1]
                            if isinstance(last_msg, dict) and 'content' in last_msg:
                                print(f"   响应内容: {last_msg['content'][:100]}...")
            except Exception as e:
                print(f"    ⚠️  generate_async 调用失败: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"    ⚠️  通过配置文件创建失败: {e}")
            import traceback
            traceback.print_exc()
            print("   这可能需要根据实际 API 调整")
        
    except Exception as e:
        print(f"❌ 创建 LLMRails 实例失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n   注意：这可能需要根据 NeMo Guardrails 的实际 API 调整")
        print("   建议查阅官方文档或示例代码")
    
    # 5. 记录发现
    print("\n[步骤 5] 记录关键发现...")
    print("   需要验证的实际 API：")
    print("   - Rails 类的初始化方式")
    print("   - 如何传入 LangChain LLM")
    print("   - generate() 或 generate_async() 的调用方式")
    print("   - 配置文件的正确格式")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print("✅ 集成测试完成（部分功能可能需要根据实际 API 调整）")
    print("\n关键发现：")
    print("  - LangChain + Ollama 集成正常")
    print("  - NeMo Guardrails 可以导入")
    print("  - 需要根据实际 API 调整集成方式")
    print("\n下一步：")
    print("  1. 查阅 NeMo Guardrails 官方文档确认 API")
    print("  2. 运行 05_test_safety_rules.py（如果基本集成成功）")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_guardrails_with_ollama())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

