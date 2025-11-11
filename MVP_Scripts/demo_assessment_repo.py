"""
MVP Alpha 演示脚本：AssessmentRepo（评估仓库）

演示 AssessmentRepo 的持久化和历史查询功能：
- 保存评估结果
- 查询历史记录
- 检查是否有先前评估
- 自杀意念标志处理
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import os

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.repo import AssessmentRepo
from src.assessment.proximo_api import assess


async def demo_assessment_repo():
    """演示 AssessmentRepo 功能"""
    
    print("=" * 80)
    print("MVP Alpha 演示：AssessmentRepo（评估仓库）")
    print("=" * 80)
    print("\n本演示展示 AssessmentRepo 的核心功能：")
    print("  - 保存评估结果到 SQLite")
    print("  - 查询历史记录")
    print("  - 检查是否有先前评估")
    print("  - 自杀意念标志处理")
    print("=" * 80)
    
    # 使用临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "demo_assessments.db")
    print(f"\n[INFO] 使用临时数据库: {db_path}")
    
    repo = AssessmentRepo(db_path=db_path)
    
    # 演示 1: 保存评估
    print("\n" + "=" * 80)
    print("[演示 1] 保存评估结果")
    print("=" * 80)
    
    user_id = "demo_user_repo_001"
    
    # 执行评估
    print(f"\n[INFO] 为用户 {user_id} 执行 PHQ-9 评估...")
    assessment1 = await assess("phq9", ["0", "0", "1", "0", "1", "0", "1", "0", "0"])
    
    if assessment1.get("success"):
        print(f"[OK] 评估成功:")
        print(f"  严重度: {assessment1.get('severity_level')}")
        print(f"  总分: {assessment1.get('total_score')}")
        
        # 保存到仓库
        decision1 = {
            "route": "low",
            "rigid_score": 0.15,
            "reason": "low_risk"
        }
        policy_result1 = {
            "policy": "low",
            "response": "这是一个低风险的评估结果。"
        }
        
        await repo.save(
            user_id=user_id,
            assessment=assessment1,
            decision=decision1,
            result=policy_result1
        )
        print(f"[OK] 评估结果已保存到数据库")
    
    # 演示 2: 查询历史
    print("\n" + "=" * 80)
    print("[演示 2] 查询历史记录")
    print("=" * 80)
    
    print(f"\n[INFO] 查询用户 {user_id} 的评估历史...")
    history = await repo.history(user_id, limit=10)
    
    print(f"[OK] 找到 {len(history)} 条历史记录:")
    for i, record in enumerate(history, 1):
        print(f"\n  记录 {i}:")
        print(f"    ID: {record.get('id')}")
        print(f"    时间: {record.get('ts')}")
        print(f"    量表: {record.get('scale')}")
        print(f"    分数: {record.get('score')}")
        print(f"    严重度: {record.get('severity')}")
        print(f"    路由: {record.get('route')}")
        flags = record.get('flags', {})
        if flags.get('suicidal_ideation'):
            print(f"    ⚠️  自杀意念: {flags.get('suicidal_ideation')}")
    
    # 演示 3: 检查先前评估
    print("\n" + "=" * 80)
    print("[演示 3] 检查是否有先前评估")
    print("=" * 80)
    
    has_prior = await repo.has_prior_assessment(user_id)
    print(f"\n[INFO] 用户 {user_id} 是否有先前评估: {has_prior}")
    
    new_user_id = "demo_user_repo_002"
    has_prior_new = await repo.has_prior_assessment(new_user_id)
    print(f"[INFO] 新用户 {new_user_id} 是否有先前评估: {has_prior_new}")
    
    # 演示 4: 保存多个评估
    print("\n" + "=" * 80)
    print("[演示 4] 保存多个评估（同一用户）")
    print("=" * 80)
    
    print(f"\n[INFO] 为用户 {user_id} 执行第二次评估...")
    assessment2 = await assess("phq9", ["1", "1", "2", "2", "1", "2", "1", "2", "0"])
    
    if assessment2.get("success"):
        decision2 = {
            "route": "medium",
            "rigid_score": 0.60,
            "reason": "medium_risk"
        }
        policy_result2 = {
            "policy": "medium",
            "response": "这是一个中等风险的评估结果。"
        }
        
        await repo.save(
            user_id=user_id,
            assessment=assessment2,
            decision=decision2,
            result=policy_result2
        )
        print(f"[OK] 第二次评估已保存")
    
    # 再次查询历史
    history_updated = await repo.history(user_id, limit=10)
    print(f"\n[OK] 更新后的历史记录数量: {len(history_updated)}")
    
    # 演示 5: 高风险评估（自杀意念）
    print("\n" + "=" * 80)
    print("[演示 5] 高风险评估（自杀意念标志）")
    print("=" * 80)
    
    print(f"\n[INFO] 执行高风险评估（PHQ-9 Item 9 = 2）...")
    assessment3 = await assess("phq9", ["1", "1", "1", "1", "1", "1", "1", "1", "2"])
    
    if assessment3.get("success"):
        flags = assessment3.get("flags", {})
        print(f"[OK] 评估结果:")
        print(f"  严重度: {assessment3.get('severity_level')}")
        print(f"  总分: {assessment3.get('total_score')}")
        print(f"  自杀意念: {flags.get('suicidal_ideation')}")
        print(f"  自杀意念分数: {flags.get('suicidal_ideation_score')}")
        
        decision3 = {
            "route": "high",
            "rigid_score": 1.0,
            "reason": "hard_lock"
        }
        policy_result3 = {
            "policy": "high",
            "response": "这是高风险评估，已触发安全锁定。"
        }
        
        await repo.save(
            user_id=user_id,
            assessment=assessment3,
            decision=decision3,
            result=policy_result3
        )
        print(f"[OK] 高风险评估已保存（包含自杀意念标志）")
    
    # 查询包含自杀意念标志的历史
    print(f"\n[INFO] 查询包含自杀意念标志的历史记录...")
    history_all = await repo.history(user_id, limit=10)
    high_risk_records = [
        r for r in history_all 
        if r.get('flags', {}).get('suicidal_ideation')
    ]
    print(f"[OK] 找到 {len(high_risk_records)} 条高风险记录")
    
    # 总结
    print("\n" + "=" * 80)
    print("演示总结")
    print("=" * 80)
    print("✅ AssessmentRepo 功能演示完成！")
    print("\n核心功能验证：")
    print("  ✅ 保存评估结果到 SQLite")
    print("  ✅ 查询历史记录")
    print("  ✅ 检查是否有先前评估")
    print("  ✅ 自杀意念标志处理")
    print("  ✅ 多评估记录管理")
    print(f"\n[INFO] 临时数据库位置: {db_path}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(demo_assessment_repo())
    except KeyboardInterrupt:
        print("\n\n[INFO] 演示被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

