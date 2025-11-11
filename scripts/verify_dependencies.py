"""
依赖验证脚本：确保所有关键依赖正确安装且版本兼容

这个脚本会：
1. 检查所有关键依赖的安装状态
2. 验证版本兼容性
3. 测试基本导入功能
4. 确保不会影响其他脚本的运行
"""

import sys
import importlib
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 关键依赖列表
CRITICAL_DEPENDENCIES = {
    "pydantic": ">=2.11.7",
    "pydantic_core": None,  # 自动安装
    "pydantic_settings": ">=2.10.1",
    "torch": ">=2.0.0",
    "transformers": ">=4.50.0",
    "fastapi": ">=0.116.0",
    "httpx": ">=0.28.0",
    "numpy": ">=1.20.0",
    "scikit-learn": ">=1.0.0",
}


def check_module(module_name: str, min_version: str = None) -> tuple[bool, str]:
    """检查模块是否可导入"""
    try:
        module = importlib.import_module(module_name)
        
        # 获取版本
        version = getattr(module, "__version__", "unknown")
        
        # 如果有版本要求，检查版本
        if min_version:
            from packaging import version as pkg_version
            try:
                if not pkg_version.parse(version) >= pkg_version.parse(min_version.replace(">=", "")):
                    return False, f"版本 {version} 不满足要求 {min_version}"
            except Exception:
                pass  # 如果版本比较失败，至少模块能导入
        
        return True, f"版本 {version}"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"错误: {e}"


def check_pydantic_specific():
    """特殊检查 pydantic 的 C 扩展"""
    try:
        import pydantic
        import pydantic_core
        from pydantic_core import _pydantic_core  # 这行会失败如果 C 扩展损坏
        return True, f"pydantic {pydantic.__version__}, pydantic-core {pydantic_core.__version__}"
    except ImportError as e:
        return False, f"C 扩展导入失败: {e}"
    except Exception as e:
        return False, f"错误: {e}"


def check_project_modules():
    """检查项目模块是否可以导入"""
    modules_to_check = [
        "src.assessment.proximo_api",
        "src.conversation.engine",
        "src.conversation.router",
        "src.conversation.policies",
        "src.services.ollama_service",
        "src.core.config",
    ]
    
    results = {}
    for module_name in modules_to_check:
        try:
            importlib.import_module(module_name)
            results[module_name] = (True, "OK")
        except Exception as e:
            results[module_name] = (False, str(e))
    
    return results


def main():
    """主函数"""
    print("=" * 80)
    print("PROXIMO 依赖验证脚本")
    print("=" * 80)
    
    all_passed = True
    
    # 1. 检查关键依赖
    print("\n[1] 检查关键依赖...")
    print("-" * 80)
    
    for dep_name, min_version in CRITICAL_DEPENDENCIES.items():
        # 处理模块名映射
        import_name = dep_name.replace("-", "_")
        
        ok, msg = check_module(import_name, min_version)
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {dep_name}: {msg}")
        
        if not ok:
            all_passed = False
    
    # 2. 特殊检查 pydantic
    print("\n[2] 检查 Pydantic C 扩展...")
    print("-" * 80)
    ok, msg = check_pydantic_specific()
    status = "[OK]" if ok else "[FAIL]"
    print(f"  {status} {msg}")
    if not ok:
        all_passed = False
    
    # 3. 检查项目模块
    print("\n[3] 检查项目模块...")
    print("-" * 80)
    module_results = check_project_modules()
    for module_name, (ok, msg) in module_results.items():
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {module_name}: {msg}")
        if not ok:
            all_passed = False
    
    # 4. 测试基本功能
    print("\n[4] 测试基本功能...")
    print("-" * 80)
    
    # 测试 pydantic 基本功能
    try:
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            age: int
        
        test_obj = TestModel(name="test", age=30)
        if test_obj.name == "test" and test_obj.age == 30:
            print("  [OK] Pydantic 基本功能正常")
        else:
            print("  [FAIL] Pydantic 基本功能异常")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] Pydantic 基本功能测试失败: {e}")
        all_passed = False
    
    # 测试 torch 基本功能
    try:
        import torch
        x = torch.tensor([1, 2, 3])
        if len(x) == 3:
            print(f"  [OK] PyTorch 基本功能正常 (版本: {torch.__version__})")
        else:
            print("  [FAIL] PyTorch 基本功能异常")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] PyTorch 基本功能测试失败: {e}")
        all_passed = False
    
    # 5. 总结
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    
    if all_passed:
        print("[SUCCESS] 所有依赖验证通过！")
        print("\n可以安全运行以下脚本：")
        print("  - scripts/test_conversation_pipeline.py")
        print("  - scripts/test_proximo_api.py")
        print("  - scripts/test_risk_routing.py")
        print("  - scripts/verify_risk_routing.py")
        return 0
    else:
        print("[FAIL] 部分依赖验证失败")
        print("\n建议修复步骤：")
        print("  1. 重新安装 pydantic: pip install --force-reinstall pydantic pydantic-core")
        print("  2. 重新安装所有依赖: pip install -e .")
        print("  3. 如果问题持续，检查 Python 版本兼容性")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[ERROR] 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


