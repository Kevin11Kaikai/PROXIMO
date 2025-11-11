# Conversation Layer 实现总结

**实现日期**：2025-11-07  
**状态**：✅ 已完成

---

## 📋 实现概览

Conversation Layer 是五层架构的第三层，负责对话执行。本层已完成以下功能：

1. ✅ **LowRiskAgent** - 自由对话 + 应对技能建议
2. ✅ **MediumRiskAgent** - 半结构化 + Peer Support Group（带状态机）
3. ✅ **HighRiskAgent** - 固定脚本 + Crisis Hotline
4. ✅ **ConversationPipeline** - 对话管道（路由到对应 Agent）
5. ✅ **SessionService** - 会话管理服务
6. ✅ **完整测试套件** - 单元测试和集成测试

---

## 🎯 核心模块

### 1. LowRiskAgent (`src_new/conversation/agents/low_risk_agent.py`)

**功能**：
- 自由、共情的对话
- 建议应对技能（breathing, journaling, mindfulness 等）
- 高灵活性（temperature = 0.9）
- 继续对话直到用户说再见

**关键特性**：
- 基于 Rigidity 调整温度
- 检测应对技能建议
- Goodbye 检测

**API**：
```python
agent = LowRiskAgent()

result = await agent.generate_response(
    user_message="I'm feeling stressed.",
    conversation_history=history,
    rigid_score=0.2
)
# result.response = "I understand. Let's try some breathing exercises..."
# result.coping_skills_suggested = True
```

### 2. MediumRiskAgent (`src_new/conversation/agents/medium_risk_agent.py`)

**功能**：
- 建议加入 Peer Support Group
- 检测和处理抗拒（privacy, time, stigma, doubt）
- 状态机管理（初始 → 检测 → 处理 → 接受/拒绝）
- 最多 5 轮说服

**状态机**：
1. **INITIAL_SUGGESTION** - 初始建议
2. **DETECTING_RESISTANCE** - 检测抗拒
3. **HANDLING_RESISTANCE** - 处理抗拒（最多 5 轮）
4. **ACCEPTED** - 用户接受
5. **REJECTED** - 用户拒绝（5 轮后）
6. **PROVIDING_RESOURCES** - 提供自助资源

**抗拒关键词**：
- **privacy**: privacy, private, anonymous, personal, confidential
- **time**: time, busy, schedule, don't have time
- **stigma**: stigma, embarrassed, ashamed, judge, judgment
- **doubt**: doubt, not sure, don't think, won't help

**API**：
```python
agent = MediumRiskAgent()

result = await agent.generate_response(
    user_id="user123",
    user_message="I don't want to share my privacy.",
    conversation_history=history,
    rigid_score=0.6
)
# result.state = "handling_resistance"
# result.resistance_type = "privacy"
# result.resistance_count = 1
```

### 3. HighRiskAgent (`src_new/conversation/agents/high_risk_agent.py`)

**功能**：
- 使用固定安全脚本
- 强烈提示 Crisis Hotline (988)
- 建议紧急会面
- 不允许自由对话

**固定脚本内容**：
- 安全提示
- 988 热线信息
- 紧急服务联系方式
- 资源提供

**API**：
```python
agent = HighRiskAgent()

result = await agent.generate_response(
    user_message="I want to kill myself",
    conversation_history=None,
    rigid_score=1.0
)
# result.response = FIXED_SAFETY_SCRIPT
# result.fixed_script = True
# result.safety_banner = "If you are in immediate danger..."
# result.crisis_hotline = "988"
```

### 4. ConversationPipeline (`src_new/conversation/pipeline.py`)

**功能**：
- 根据 ControlContext 路由到对应 Agent
- 管理对话历史
- 集成 SessionService

**工作流程**：
```
User Message
    ↓
ControlContext (route: low/medium/high)
    ↓
Route to Agent:
    - Low → LowRiskAgent
    - Medium → MediumRiskAgent
    - High → HighRiskAgent
    ↓
Agent Response
    ↓
Save to SessionService
```

**API**：
```python
pipeline = ConversationPipeline()

result = await pipeline.process_message(
    user_id="user123",
    user_message="I'm feeling anxious.",
    control_context=context  # ControlContext with route="medium"
)
# result.route = "medium"
# result.agent_result.agent = "medium_risk"
# result.agent_result.state = "initial_suggestion"
```

### 5. SessionService (`src_new/conversation/session_service.py`)

**功能**：
- 管理对话会话
- 获取对话历史
- 追加对话轮次
- 清除会话

**API**：
```python
service = SessionService()

# 获取历史
history = service.get_context("user123")

# 追加轮次
service.append_turn("user123", "user", "Hello")
service.append_turn("user123", "bot", "Hi there!")

# 清除会话
service.clear_session("user123")
```

---

## 🧪 测试覆盖

### 测试文件

1. **`test_low_risk_agent.py`**
   - ✅ 基本响应测试
   - ✅ 带历史记录的对话
   - ✅ Goodbye 检测
   - ✅ 温度调整

2. **`test_medium_risk_agent.py`**
   - ✅ 初始建议
   - ✅ 抗拒检测
   - ✅ 抗拒处理（多轮）
   - ✅ 用户接受
   - ✅ 最大轮次限制
   - ✅ 状态重置

3. **`test_high_risk_agent.py`**
   - ✅ 固定脚本测试
   - ✅ 脚本内容要求
   - ✅ 元数据测试
   - ✅ get_script 方法

4. **`test_pipeline.py`**
   - ✅ Low/Medium/High Risk 管道
   - ✅ 对话历史管理
   - ✅ 清除对话

### 测试结果

**所有测试通过** ✅
- Low Risk Agent：所有场景通过
- Medium Risk Agent：状态机正确工作
- High Risk Agent：固定脚本正确
- 集成测试：管道工作正常

---

## 📊 工作流程

### 完整流程示例

```
[Control Layer 输出]
    route = "medium"
    rigid_score = 0.6
    psyguard_score = 0.75
    ↓
[ConversationPipeline.process_message()]
    路由到 MediumRiskAgent
    ↓
[MediumRiskAgent.generate_response()]
    状态机：INITIAL_SUGGESTION
    生成建议加入 Peer Group 的响应
    ↓
[用户响应：抗拒]
    "I don't want to share my privacy"
    ↓
[MediumRiskAgent 检测抗拒]
    状态机：HANDLING_RESISTANCE
    resistance_type = "privacy"
    resistance_count = 1
    ↓
[生成针对性响应]
    处理隐私担忧
    ↓
[保存到 SessionService]
    对话历史更新
```

---

## 🔧 使用示例

### 基本使用

```python
from src_new.conversation.pipeline import ConversationPipeline
from src_new.control.control_context import ControlContext

# 初始化
pipeline = ConversationPipeline()

# 创建控制上下文
context = ControlContext(
    user_id="user123",
    route="medium",
    rigid_score=0.6,
    psyguard_score=0.75
)

# 处理消息
result = await pipeline.process_message(
    user_id="user123",
    user_message="I've been feeling really anxious.",
    control_context=context
)

# 获取响应
response = result["agent_result"]["response"]
agent = result["agent_result"]["agent"]
state = result["agent_result"].get("state")  # For Medium Risk
```

### Medium Risk Agent 状态管理

```python
from src_new.conversation.agents.medium_risk_agent import MediumRiskAgent

agent = MediumRiskAgent()

# 处理多轮对话
for i in range(3):
    result = await agent.generate_response(
        user_id="user123",
        user_message=f"User message {i}",
        conversation_history=history,
        rigid_score=0.6
    )
    print(f"State: {result['state']}, Resistance: {result.get('resistance_count', 0)}")

# 重置状态（对话结束后）
agent.reset_state("user123")
```

---

## ✅ 完成状态

- [x] LowRiskAgent 实现
- [x] MediumRiskAgent 实现（带状态机）
- [x] HighRiskAgent 实现
- [x] ConversationPipeline 实现
- [x] SessionService 实现
- [x] 单元测试编写
- [x] 集成测试编写
- [x] 测试文档编写

---

## 🚀 下一步

Conversation Layer 已完成，可以进入下一层实现：

1. **Safety Layer** - Guardrails 集成（已完成）
2. **Adaptive Layer** - 反馈收集和适应

---

**维护者**：开发团队  
**最后更新**：2025-11-07

