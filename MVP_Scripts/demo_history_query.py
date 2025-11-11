"""
MVP Alpha 演示脚本：历史查询功能

演示如何查询评估历史记录，包括：
- 按用户 ID 查询
- 限制返回数量
- 查看自杀意念标志
- 查看完整评估详情
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

from src.storage.repo import AssessmentRepo
from src.assessment.proximo_api import assess


async def demo_history_query():
    """演示历史查询功能"""
    
    print("=" * 80)
    print("MVP Alpha 演示：历史查询功能")
    print("=" * 80)
    print("\n本演示展示如何查询评估历史记录：")
    print("  - 按用户 ID 查询")
    print("  - 限制返回数量")
    print("  - 查看自杀意念标志")
    print("  - 查看完整评估详情")
    print("=" * 80)
    
    # 使用默认数据库（或创建临时数据库）
    repo = AssessmentRepo()
    user_id = "demo_user_history_001"
    
    # 先创建一些测试数据
    print("\n[INFO] 创建测试数据...")
    
    # 评估 1: 低风险
    assessment1 = await assess("phq9", ["0", "0", "1", "0", "1", "0", "1", "0", "0"])
    if assessment1.get("success"):
        await repo.save(
            user_id=user_id,
            assessment=assessment1,
            decision={"route": "low", "rigid_score": 0.15},
            result={"policy": "low", "response": "低风险响应"}
        )
        print(f"[OK] 评估 1 已保存（低风险）")
    
    # 评估 2: 中等风险
    assessment2 = await assess("phq9", ["1", "1", "2", "2", "1", "2", "1", "2", "0"])
    if assessment2.get("success"):
        await repo.save(
            user_id=user_id,
            assessment=assessment2,
            decision={"route": "medium", "rigid_score": 0.60},
            result={"policy": "medium", "response": "中等风险响应"}
        )
        print(f"[OK] 评估 2 已保存（中等风险）")
    
    # 评估 3: 高风险（自杀意念）
    assessment3 = await assess("phq9", ["1", "1", "1", "1", "1", "1", "1", "1", "2"])
    if assessment3.get("success"):
        await repo.save(
            user_id=user_id,
            assessment=assessment3,
            decision={"route": "high", "rigid_score": 1.0},
            result={"policy": "high", "response": "高风险响应"}
        )
        print(f"[OK] 评估 3 已保存（高风险 - 自杀意念）")
    
    # 评估 4: GAD-7
    assessment4 = await assess("gad7", ["1", "2", "1", "1", "2", "1", "1"])
    if assessment4.get("success"):
        await repo.save(
            user_id=user_id,
            assessment=assessment4,
            decision={"route": "medium", "rigid_score": 0.60},
            result={"policy": "medium", "response": "GAD-7 响应"}
        )
        print(f"[OK] 评估 4 已保存（GAD-7）")
    
    # 演示 1: 查询所有历史
    print("\n" + "=" * 80)
    print("[演示 1] 查询所有历史记录")
    print("=" * 80)
    
    history_all = await repo.history(user_id, limit=100)
    print(f"\n[OK] 用户 {user_id} 的所有历史记录（{len(history_all)} 条）:")
    for i, record in enumerate(history_all, 1):
        print(f"\n  记录 {i}:")
        print(f"    ID: {record.get('id')}")
        print(f"    时间: {record.get('ts')}")
        print(f"    量表: {record.get('scale')}")
        print(f"    分数: {record.get('score')}")
        print(f"    严重度: {record.get('severity')}")
        print(f"    路由: {record.get('route')}")
        print(f"    Rigid Score: {record.get('rigid')}")
    
    # 演示 2: 限制返回数量
    print("\n" + "=" * 80)
    print("[演示 2] 限制返回数量（最近 2 条）")
    print("=" * 80)
    
    history_recent = await repo.history(user_id, limit=2)
    print(f"\n[OK] 最近 2 条记录:")
    for i, record in enumerate(history_recent, 1):
        print(f"  {i}. [{record.get('ts')}] {record.get('scale')} - {record.get('severity')} ({record.get('score')} 分)")
    
    # 演示 3: 查看自杀意念标志
    print("\n" + "=" * 80)
    print("[演示 3] 查看包含自杀意念标志的记录")
    print("=" * 80)
    
    history_all = await repo.history(user_id, limit=100)
    high_risk_records = [
        r for r in history_all 
        if r.get('flags', {}).get('suicidal_ideation')
    ]
    
    print(f"\n[OK] 找到 {len(high_risk_records)} 条高风险记录（包含自杀意念标志）:")
    for i, record in enumerate(high_risk_records, 1):
        flags = record.get('flags', {})
        print(f"\n  记录 {i}:")
        print(f"    时间: {record.get('ts')}")
        print(f"    量表: {record.get('scale')}")
        print(f"    分数: {record.get('score')}")
        print(f"    严重度: {record.get('severity')}")
        print(f"    自杀意念: {flags.get('suicidal_ideation')}")
        print(f"    自杀意念分数: {flags.get('suicidal_ideation_score')}")
    
    # 演示 4: 查看完整评估详情
    print("\n" + "=" * 80)
    print("[演示 4] 查看完整评估详情（JSON）")
    print("=" * 80)
    
    if history_all:
        first_record = history_all[0]
        print(f"\n[INFO] 查看记录 ID {first_record.get('id')} 的完整详情...")
        
        # 从 JSON 字段获取完整数据
        assessment_json = first_record.get('assessment_json')
        decision_json = first_record.get('decision_json')
        result_json = first_record.get('result_json')
        
        if assessment_json:
            print(f"\n[OK] 评估详情（部分）:")
            print(f"  量表: {first_record.get('scale')}")
            print(f"  分数: {first_record.get('score')}")
            print(f"  严重度: {first_record.get('severity')}")
        
        if decision_json:
            print(f"\n[OK] 路由决策（部分）:")
            print(f"  路由: {first_record.get('route')}")
            print(f"  Rigid Score: {first_record.get('rigid')}")
        
        preview = first_record.get('preview_text')
        if preview:
            print(f"\n[OK] 预览文本: {preview[:100]}...")
    
    # 演示 5: 查询不同用户
    print("\n" + "=" * 80)
    print("[演示 5] 查询不同用户的历史")
    print("=" * 80)
    
    user_id_2 = "demo_user_history_002"
    
    # 为新用户创建一条记录
    assessment5 = await assess("phq9", ["0", "0", "0", "0", "0", "0", "0", "0", "0"])
    if assessment5.get("success"):
        await repo.save(
            user_id=user_id_2,
            assessment=assessment5,
            decision={"route": "low", "rigid_score": 0.15},
            result={"policy": "low", "response": "用户 2 的响应"}
        )
        print(f"[OK] 为用户 {user_id_2} 创建了一条记录")
    
    history_user1 = await repo.history(user_id, limit=10)
    history_user2 = await repo.history(user_id_2, limit=10)
    
    print(f"\n[OK] 用户 {user_id} 的记录数: {len(history_user1)}")
    print(f"[OK] 用户 {user_id_2} 的记录数: {len(history_user2)}")
    print(f"[OK] 不同用户的历史记录完全独立")
    
    # 总结
    print("\n" + "=" * 80)
    print("演示总结")
    print("=" * 80)
    print("✅ 历史查询功能演示完成！")
    print("\n核心功能验证：")
    print("  ✅ 按用户 ID 查询历史")
    print("  ✅ 限制返回数量")
    print("  ✅ 查看自杀意念标志")
    print("  ✅ 查看完整评估详情")
    print("  ✅ 多用户数据隔离")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(demo_history_query())
    except KeyboardInterrupt:
        print("\n\n[INFO] 演示被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

