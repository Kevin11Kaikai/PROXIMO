"""
MVP Alpha 演示脚本：运行所有演示

这个脚本会依次运行所有 MVP Alpha 的演示脚本，展示完整的功能。
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

# 导入所有演示模块
import importlib.util
from pathlib import Path

def load_demo_module(module_name):
    """动态加载演示模块"""
    script_path = Path(__file__).parent / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 加载所有演示模块
demo_complete_pipeline_mod = load_demo_module("demo_complete_pipeline")
demo_session_manager_mod = load_demo_module("demo_session_manager")
demo_assessment_repo_mod = load_demo_module("demo_assessment_repo")
demo_multi_turn_conversation_mod = load_demo_module("demo_multi_turn_conversation")
demo_history_query_mod = load_demo_module("demo_history_query")


async def run_all_demos():
    """运行所有演示"""
    
    print("=" * 80)
    print("MVP Alpha 完整功能演示")
    print("=" * 80)
    print("\n本脚本将依次运行所有 MVP Alpha 的演示：")
    print("  1. 完整对话管道演示")
    print("  2. SessionManager 演示")
    print("  3. AssessmentRepo 演示")
    print("  4. 多轮对话场景演示")
    print("  5. 历史查询功能演示")
    print("=" * 80)
    
    demos = [
        ("完整对话管道", demo_complete_pipeline_mod.demo_complete_pipeline, True),
        ("SessionManager", demo_session_manager_mod.demo_session_manager, False),
        ("AssessmentRepo", demo_assessment_repo_mod.demo_assessment_repo, True),
        ("多轮对话场景", demo_multi_turn_conversation_mod.demo_multi_turn_conversation, True),
        ("历史查询功能", demo_history_query_mod.demo_history_query, True),
    ]
    
    results = []
    
    for i, (name, demo_func, is_async) in enumerate(demos, 1):
        print("\n" + "=" * 80)
        print(f"运行演示 {i}/{len(demos)}: {name}")
        print("=" * 80)
        
        try:
            if is_async:
                await demo_func()
            else:
                demo_func()
            results.append((name, True, None))
            print(f"\n✅ 演示 '{name}' 完成")
        except KeyboardInterrupt:
            print(f"\n⚠️  演示 '{name}' 被用户中断")
            results.append((name, False, "用户中断"))
            break
        except Exception as e:
            print(f"\n❌ 演示 '{name}' 失败: {e}")
            results.append((name, False, str(e)))
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 80)
    print("所有演示总结")
    print("=" * 80)
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    print(f"\n完成: {success_count}/{total_count}")
    print("\n详细结果:")
    for name, success, error in results:
        status = "✅ 成功" if success else f"❌ 失败 ({error})"
        print(f"  - {name}: {status}")
    
    print("\n" + "=" * 80)
    if success_count == total_count:
        print("🎉 所有演示成功完成！")
    else:
        print("⚠️  部分演示失败，请查看上面的错误信息")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print("\n\n[INFO] 演示被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

