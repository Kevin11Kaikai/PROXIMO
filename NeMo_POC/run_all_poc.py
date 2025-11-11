"""
运行所有 POC 脚本

依次运行所有 NeMo Guardrails POC 脚本，提供完整的验证报告。
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


async def run_all_poc():
    """运行所有 POC 脚本"""
    
    print("=" * 80)
    print("NeMo Guardrails POC - 完整验证")
    print("=" * 80)
    print("\n本脚本将依次运行所有 POC 测试：")
    print("  1. 检查安装")
    print("  2. 测试 LangChain + Ollama")
    print("  3. 测试 NeMo Guardrails 基本功能")
    print("  4. 测试 NeMo Guardrails + Ollama 集成")
    print("  5. 测试安全规则")
    print("=" * 80)
    
    # 导入所有 POC 模块
    import importlib.util
    
    def load_poc_module(module_name):
        """动态加载 POC 模块"""
        script_path = Path(__file__).parent / f"{module_name}.py"
        if not script_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    # 定义 POC 脚本
    pocs = [
        ("01_check_installation", "检查安装", False),
        ("02_test_langchain_ollama", "测试 LangChain + Ollama", True),
        ("03_test_guardrails_basic", "测试 NeMo Guardrails 基本功能", False),
        ("04_test_guardrails_with_ollama", "测试 NeMo Guardrails + Ollama 集成", True),
        ("05_test_safety_rules", "测试安全规则", True),
    ]
    
    results = []
    
    for script_name, description, is_async in pocs:
        print("\n" + "=" * 80)
        print(f"运行 POC: {description} ({script_name})")
        print("=" * 80)
        
        try:
            module = load_poc_module(script_name)
            if module is None:
                print(f"⚠️  脚本不存在: {script_name}.py")
                results.append((description, False, "脚本不存在"))
                continue
            
            # 找到主函数
            if hasattr(module, 'test_guardrails_basic'):
                func = module.test_guardrails_basic
            elif hasattr(module, 'test_langchain_ollama'):
                func = module.test_langchain_ollama
            elif hasattr(module, 'test_guardrails_with_ollama'):
                func = module.test_guardrails_with_ollama
            elif hasattr(module, 'test_safety_rules'):
                func = module.test_safety_rules
            elif hasattr(module, 'check_installation'):
                func = module.check_installation
            else:
                print(f"⚠️  找不到测试函数")
                results.append((description, False, "找不到测试函数"))
                continue
            
            # 运行测试
            if is_async:
                success = await func()
            else:
                success = func()
            
            if success:
                results.append((description, True, None))
                print(f"\n✅ POC '{description}' 完成")
            else:
                results.append((description, False, "测试失败"))
                print(f"\n❌ POC '{description}' 失败")
            
        except KeyboardInterrupt:
            print(f"\n⚠️  POC '{description}' 被用户中断")
            results.append((description, False, "用户中断"))
            break
        except Exception as e:
            print(f"\n❌ POC '{description}' 出错: {e}")
            results.append((description, False, str(e)))
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 80)
    print("所有 POC 测试总结")
    print("=" * 80)
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    print(f"\n完成: {success_count}/{total_count}")
    print("\n详细结果:")
    for description, success, error in results:
        status = "✅ 成功" if success else f"❌ 失败 ({error})"
        print(f"  - {description}: {status}")
    
    print("\n" + "=" * 80)
    if success_count == total_count:
        print("🎉 所有 POC 测试成功完成！")
        print("\n下一步：根据 POC 结果调整集成计划，开始正式实施")
    else:
        print("⚠️  部分 POC 测试失败，请查看上面的错误信息")
        print("\n建议：")
        print("  1. 检查依赖是否已安装")
        print("  2. 检查 Ollama 服务是否运行")
        print("  3. 查阅 NeMo Guardrails 官方文档确认 API")
    print("=" * 80)
    
    return success_count == total_count


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_poc())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] POC 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

