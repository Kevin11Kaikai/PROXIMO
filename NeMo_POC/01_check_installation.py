"""
POC 1: 检查 NeMo Guardrails 安装

验证 NeMo Guardrails 和相关依赖是否已正确安装。
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


def check_installation():
    """检查所有必需的包是否已安装"""
    
    print("=" * 80)
    print("POC 1: 检查 NeMo Guardrails 安装")
    print("=" * 80)
    print("\n检查必需的包...")
    
    packages = {
        "nemoguardrails": "NeMo Guardrails",
        "langchain": "LangChain",
        "langchain_community": "LangChain Community (包含 Ollama 支持)",
    }
    
    results = {}
    
    for package, description in packages.items():
        try:
            __import__(package)
            results[package] = {"installed": True, "error": None}
            print(f"✅ {package} ({description}) - 已安装")
        except ImportError as e:
            results[package] = {"installed": False, "error": str(e)}
            print(f"❌ {package} ({description}) - 未安装")
            print(f"   错误: {e}")
    
    # 检查版本信息
    print("\n" + "=" * 80)
    print("版本信息")
    print("=" * 80)
    
    try:
        import nemoguardrails
        if hasattr(nemoguardrails, '__version__'):
            print(f"NeMo Guardrails 版本: {nemoguardrails.__version__}")
        else:
            print("NeMo Guardrails: 已安装（版本未知）")
    except ImportError:
        pass
    
    try:
        import langchain
        if hasattr(langchain, '__version__'):
            print(f"LangChain 版本: {langchain.__version__}")
        else:
            print("LangChain: 已安装（版本未知）")
    except ImportError:
        pass
    
    # 总结
    print("\n" + "=" * 80)
    print("检查总结")
    print("=" * 80)
    
    all_installed = all(r["installed"] for r in results.values())
    
    if all_installed:
        print("✅ 所有必需的包已安装！")
        print("\n下一步：运行 02_test_langchain_ollama.py")
    else:
        print("❌ 部分包未安装")
        print("\n请运行以下命令安装缺失的包：")
        print("  conda activate PROXIMO")
        print("  pip install nemoguardrails")
        print("  pip install langchain")
        print("  pip install langchain-community")
    
    return all_installed


if __name__ == "__main__":
    try:
        success = check_installation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

