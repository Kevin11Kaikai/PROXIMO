"""
Run all integration tests.

This script runs all integration tests and provides a summary report.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows encoding setup
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Test scripts to run
TEST_SCRIPTS = [
    "test_low_risk_scenario.py",
    "test_medium_risk_scenario.py",
    "test_high_risk_scenario.py",
    "test_route_transitions.py",
    "test_boundary_cases.py",
    "test_error_recovery.py",
    "test_safety_monitoring.py",
]


def run_test(script_name: str) -> tuple[bool, str]:
    """Run a test script and return success status and output."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        return False, f"Script not found: {script_name}"
    
    try:
        # Set UTF-8 encoding for Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid characters instead of failing
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        success = result.returncode == 0
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = stdout + stderr
        
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 5 minutes"
    except Exception as e:
        return False, f"Error running test: {str(e)}"


def main():
    """Run all integration tests."""
    print("=" * 80)
    print("整体集成测试 - 运行所有测试")
    print("=" * 80)
    print(f"\n将运行 {len(TEST_SCRIPTS)} 个测试脚本\n")
    
    results = {}
    
    for script in TEST_SCRIPTS:
        print(f"\n{'=' * 80}")
        print(f"运行: {script}")
        print("=" * 80)
        
        success, output = run_test(script)
        results[script] = {"success": success, "output": output}
        
        if success:
            print(f"✅ {script} - 通过")
        else:
            print(f"❌ {script} - 失败")
            if output:
                # Show first 500 chars, handle encoding issues
                try:
                    output_preview = output[:500]
                except:
                    output_preview = str(output)[:500]
                print(f"输出:\n{output_preview}...")
            else:
                print(f"输出: (无输出)")
    
    # Summary
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r["success"])
    failed = len(results) - passed
    
    print(f"\n总测试数: {len(results)}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    
    print("\n详细结果:")
    for script, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {script}")
    
    if failed > 0:
        print("\n失败的测试:")
        for script, result in results.items():
            if not result["success"]:
                print(f"  ❌ {script}")
                # Show error summary
                try:
                    output_lines = result["output"].split("\n")
                except:
                    output_lines = str(result["output"]).split("\n")
                
                error_lines = [line for line in output_lines 
                              if line and ("Error" in line or "失败" in line or "AssertionError" in line)]
                if error_lines:
                    try:
                        error_msg = error_lines[0][:100]
                    except:
                        error_msg = str(error_lines[0])[:100] if error_lines else "Unknown error"
                    print(f"     错误: {error_msg}")
    
    print("\n" + "=" * 80)
    
    # Exit with error code if any tests failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

