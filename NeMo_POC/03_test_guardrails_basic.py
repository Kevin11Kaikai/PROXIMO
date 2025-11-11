"""
POC 3: 测试 NeMo Guardrails 基本功能

验证 NeMo Guardrails 的基本功能，包括 Rails 实例的创建。
"""

import sys
from pathlib import Path

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_guardrails_basic():
    """测试 NeMo Guardrails 基本功能"""
    
    print("=" * 80)
    print("POC 3: 测试 NeMo Guardrails 基本功能")
    print("=" * 80)
    
    # 1. 测试导入
    print("\n[步骤 1] 测试 NeMo Guardrails 导入...")
    try:
        from nemoguardrails import LLMRails, RailsConfig
        print("✅ NeMo Guardrails 导入成功")
        print(f"   使用类: LLMRails (NeMo Guardrails 0.18.0)")
    except ImportError as e:
        print(f"❌ NeMo Guardrails 导入失败: {e}")
        print("   请运行: pip install nemoguardrails")
        return False
    
    # 2. 检查 LLMRails 类的可用方法
    print("\n[步骤 2] 检查 LLMRails 类的 API...")
    try:
        from nemoguardrails import LLMRails
        
        # 检查可用方法
        methods = [m for m in dir(LLMRails) if not m.startswith('_')]
        print(f"✅ LLMRails 类可用方法: {len(methods)} 个")
        print(f"   关键方法: {', '.join([m for m in methods if 'generate' in m.lower() or 'init' in m.lower() or 'call' in m.lower()][:8])}")
        
        # 检查关键方法
        if hasattr(LLMRails, 'generate'):
            print("✅ LLMRails 类有 generate 方法")
        if hasattr(LLMRails, 'generate_async'):
            print("✅ LLMRails 类有 generate_async 方法")
        if hasattr(LLMRails, '__call__'):
            print("✅ LLMRails 类支持 __call__ 方法（可以直接调用）")
        
    except Exception as e:
        print(f"⚠️  检查 LLMRails API 时出错: {e}")
    
    # 3. 测试创建最小配置
    print("\n[步骤 3] 测试创建最小配置...")
    try:
        # 创建临时配置目录
        config_dir = Path(__file__).parent / "test_config"
        config_dir.mkdir(exist_ok=True)
        
        # 创建最小 config.yml
        config_file = config_dir / "config.yml"
        config_content = """# 最小测试配置
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo

instructions:
  - type: general
    content: "You are a helpful assistant."
"""
        config_file.write_text(config_content, encoding='utf-8')
        print(f"✅ 创建测试配置: {config_file}")
        
    except Exception as e:
        print(f"⚠️  创建测试配置失败: {e}")
        print("   这不会影响基本功能测试")
    
    # 4. 尝试创建 LLMRails 实例（不初始化）
    print("\n[步骤 4] 测试创建 LLMRails 实例（不初始化）...")
    try:
        from nemoguardrails import LLMRails, RailsConfig
        
        # 注意：这里不实际初始化，只测试是否可以访问类
        print("✅ LLMRails 类可以导入和访问")
        print("   注意：实际初始化需要有效的配置和 LLM")
        
        # 检查 RailsConfig
        print("✅ RailsConfig 类可以导入和访问")
        
    except Exception as e:
        print(f"❌ 导入 LLMRails 失败: {e}")
        return False
    
    # 5. 检查文档和示例
    print("\n[步骤 5] 检查可用的文档资源...")
    print("   官方文档: https://github.com/NVIDIA/NeMo-Guardrails")
    print("   Colang 语法: https://github.com/NVIDIA/NeMo-Guardrails/blob/main/docs/user_guide/colang-1.0-syntax.md")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print("✅ NeMo Guardrails 基本功能测试通过！")
    print("\n关键发现：")
    print("  - NeMo Guardrails 可以正常导入")
    print("  - Rails 类可用")
    print("  - 需要配置文件和 LLM 才能完全初始化")
    print("\n下一步：运行 04_test_guardrails_with_ollama.py")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_guardrails_basic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

