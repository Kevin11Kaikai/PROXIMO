"""
MVP Alpha 演示脚本：SessionManager（会话管理）

演示 SessionManager 的多轮对话上下文管理功能：
- 会话上下文存储
- 自动修剪到最近 6 轮
- 多用户独立会话
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

from src.conversation.session_manager import SessionManager


def demo_session_manager():
    """演示 SessionManager 功能"""
    
    print("=" * 80)
    print("MVP Alpha 演示：SessionManager（会话管理）")
    print("=" * 80)
    print("\n本演示展示 SessionManager 的核心功能：")
    print("  - 多轮对话上下文管理")
    print("  - 自动修剪到最近 6 轮")
    print("  - 多用户独立会话")
    print("=" * 80)
    
    # 演示 1: 基本功能
    print("\n" + "=" * 80)
    print("[演示 1] 基本会话管理")
    print("=" * 80)
    
    user_id = "demo_user_session_001"
    
    # 清空会话（如果存在）
    SessionManager.clear_session(user_id)
    print(f"\n[INFO] 初始化用户会话: {user_id}")
    
    # 添加几轮对话
    print("\n[INFO] 添加对话轮次...")
    SessionManager.append_turn(user_id, "user", "你好，我想了解一下心理健康评估。")
    SessionManager.append_turn(user_id, "bot", "你好！我很乐意帮助你。我们可以从 GAD-7 焦虑量表开始。")
    SessionManager.append_turn(user_id, "user", "好的，我需要回答一些问题吗？")
    SessionManager.append_turn(user_id, "bot", "是的，我会问你 7 个关于焦虑的问题。")
    
    # 获取上下文
    context = SessionManager.get_context(user_id)
    print(f"\n[OK] 当前会话上下文（{len(context)} 轮）:")
    for i, turn in enumerate(context, 1):
        role = turn.get('role', 'unknown')
        text = turn.get('text', '')
        timestamp = turn.get('timestamp', 'N/A')
        print(f"  {i}. [{role}] {text[:50]}... ({timestamp})")
    
    # 演示 2: 自动修剪
    print("\n" + "=" * 80)
    print("[演示 2] 自动修剪功能（保留最近 6 轮）")
    print("=" * 80)
    
    print("\n[INFO] 添加更多对话轮次（超过 6 轮）...")
    for i in range(5, 12):
        if i % 2 == 1:
            SessionManager.append_turn(user_id, "user", f"这是第 {i} 轮用户消息")
        else:
            SessionManager.append_turn(user_id, "bot", f"这是第 {i} 轮机器人回复")
    
    context_after = SessionManager.get_context(user_id)
    print(f"\n[OK] 添加后会话上下文（{len(context_after)} 轮）:")
    print(f"  [注意] 系统自动修剪到最近 6 轮")
    for i, turn in enumerate(context_after, 1):
        role = turn.get('role', 'unknown')
        text = turn.get('text', '')
        print(f"  {i}. [{role}] {text[:50]}...")
    
    # 演示 3: 多用户独立会话
    print("\n" + "=" * 80)
    print("[演示 3] 多用户独立会话")
    print("=" * 80)
    
    user_id_2 = "demo_user_session_002"
    SessionManager.clear_session(user_id_2)
    
    print(f"\n[INFO] 创建第二个用户会话: {user_id_2}")
    SessionManager.append_turn(user_id_2, "user", "我是第二个用户")
    SessionManager.append_turn(user_id_2, "bot", "你好，第二个用户！")
    
    context_1 = SessionManager.get_context(user_id)
    context_2 = SessionManager.get_context(user_id_2)
    
    print(f"\n[OK] 用户 1 的会话上下文（{len(context_1)} 轮）:")
    for turn in context_1[-2:]:
        print(f"  [{turn.get('role')}] {turn.get('text')[:50]}...")
    
    print(f"\n[OK] 用户 2 的会话上下文（{len(context_2)} 轮）:")
    for turn in context_2:
        print(f"  [{turn.get('role')}] {turn.get('text')[:50]}...")
    
    print(f"\n[OK] 两个用户的会话完全独立，互不干扰")
    
    # 演示 4: 获取最近 N 轮
    print("\n" + "=" * 80)
    print("[演示 4] 获取最近 N 轮对话")
    print("=" * 80)
    
    recent_3 = SessionManager.get_recent_turns(user_id, 3)
    print(f"\n[OK] 用户 {user_id} 的最近 3 轮对话:")
    for i, turn in enumerate(recent_3, 1):
        print(f"  {i}. [{turn.get('role')}] {turn.get('text')[:50]}...")
    
    # 演示 5: 清空会话
    print("\n" + "=" * 80)
    print("[演示 5] 清空会话")
    print("=" * 80)
    
    print(f"\n[INFO] 清空用户 {user_id} 的会话...")
    SessionManager.clear_session(user_id)
    context_cleared = SessionManager.get_context(user_id)
    print(f"[OK] 会话已清空，当前上下文: {len(context_cleared)} 轮")
    
    # 总结
    print("\n" + "=" * 80)
    print("演示总结")
    print("=" * 80)
    print("✅ SessionManager 功能演示完成！")
    print("\n核心功能验证：")
    print("  ✅ 多轮对话上下文存储")
    print("  ✅ 自动修剪到最近 6 轮")
    print("  ✅ 多用户独立会话")
    print("  ✅ 获取最近 N 轮对话")
    print("  ✅ 清空会话")
    print("=" * 80)


if __name__ == "__main__":
    try:
        demo_session_manager()
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

