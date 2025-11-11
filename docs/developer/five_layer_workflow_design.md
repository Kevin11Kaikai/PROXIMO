# 五层架构工作流程设计文档

本文档详细定义了五层架构（Perception → Control → Conversation → Safety → Adaptive）的完整工作流程、决策规则和边界条件。

**创建日期**：2025-11-07  
**状态**：设计阶段，待实现

---

## 📋 核心流程概述

### 完整对话流程

```
用户对话
    ↓
[Perception Layer] 逐句情绪评分（PsyGUARD）
    ↓
[判断] 是否出现明显自杀意图？
    ├─ 是 → 立即触发问卷（GAD-7 + PHQ-9）
    └─ 否 → 继续对话，累计到 5 轮后触发问卷
    ↓
[Perception Layer] 问卷评估 → Risk Score
    ↓
[Control Layer] 风险映射 → Low/Medium/High Route
    ↓
[Conversation Layer] 根据 Route 选择 Agent
    ├─ Low → 自由聊 + Coping Skills
    ├─ Medium → 半结构化 + Peer Support Group
    └─ High → 固定脚本 + Crisis Hotline
    ↓
[Safety Layer] Guardrails 实时监控
    ↓
[Adaptive Layer] 收集反馈（满意度、接受度、后续行为）
```

---

## 🔍 详细规则定义

### 1. 风险更新节奏（Perception Layer）

#### 1.1 逐句情绪评分（PsyGUARD）

**规则**：
- **所有对话轮次**都要进行逐句情绪评分
- 包括进入 Low/Medium Risk 路径后的对话
- 每轮对话后立即计算风险分数

**实现**：
```python
# 伪代码
for each user_message in conversation:
    psyguard_score = await psyguard_service.score(user_message)
    current_risk = aggregate_risk(psyguard_score, questionnaire_score)
```

#### 1.2 问卷触发条件

**规则**：
- **默认**：完成 5 轮对话后自动触发问卷（GAD-7 + PHQ-9）
- **提前触发**：如果 PsyGUARD 检测到明显的自杀意图（阈值待定），立即触发问卷，不等 5 轮

**实现**：
```python
# 已确认的阈值
SUICIDE_INTENT_THRESHOLD = 0.80
HIGH_RISK_DIRECT_THRESHOLD = 0.95

if psyguard_score >= HIGH_RISK_DIRECT_THRESHOLD:
    # 极高风险，直接进入 High Risk，仍需要问卷确认
    trigger_questionnaire_immediately()
    route = "high"  # 提前设置
elif psyguard_score >= SUICIDE_INTENT_THRESHOLD:
    trigger_questionnaire_immediately()
elif conversation_turn_count >= 5:
    trigger_questionnaire()
```

#### 1.3 风险级别调整规则（单向升级）

**规则**：
- **升级规则**：如果当前在 Low Risk 路径，检测到 Medium Risk → 立即切换到 Medium Risk 路径
- **降级规则**：如果当前在 Medium Risk 路径，检测到 Low Risk → **仍然保持 Medium Risk 路径**，不降级
- **High Risk**：一旦进入 High Risk，必须完成固定脚本，不能降级

**实现**：
```python
# 已确认的阈值
MEDIUM_RISK_THRESHOLD = 0.70
HIGH_RISK_DIRECT_THRESHOLD = 0.95

def update_route(current_route, new_psyguard_score):
    if current_route == "high":
        return "high"  # 不能降级
    elif new_psyguard_score >= HIGH_RISK_DIRECT_THRESHOLD:
        return "high"  # 极高风险，直接升级
    elif current_route == "low" and new_psyguard_score >= MEDIUM_RISK_THRESHOLD:
        return "medium"  # 升级
    elif current_route == "medium" and new_psyguard_score < MEDIUM_RISK_THRESHOLD:
        return "medium"  # 不降级，保持
    return current_route
```

---

### 2. 问卷结果与实时评分的融合

#### 2.1 问卷评估优先级

**规则**：
- 问卷是**单独的一次评估**，不直接与逐句评分融合
- 问卷结果主要用于**初始路由决策**（Control Layer）
- 后续的风险调整主要依赖**逐句 PsyGUARD 评分**

#### 2.2 冲突处理：问卷 vs 聊天内容

**规则**：
- **优先级**：聊天内容很危险 > 问卷得分偏低
- 如果问卷得分显示 Low Risk，但聊天内容检测到 High Risk → **以聊天内容为准**

**实现**：
```python
# 已确认的阈值
MEDIUM_RISK_THRESHOLD = 0.70
HIGH_RISK_DIRECT_THRESHOLD = 0.95

def final_risk_decision(phq9_score, gad7_score, phq9_q9_score, chat_risk_score):
    # 聊天内容优先级更高
    if chat_risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
        return "high"
    elif chat_risk_score >= MEDIUM_RISK_THRESHOLD:
        return "medium"
    # 如果聊天内容风险低，才参考问卷
    return map_questionnaire_to_route(phq9_score, gad7_score, phq9_q9_score)
```

---

### 3. Chatbot 自由度控制（Conversation Layer）

#### 3.1 三种 Agent 对应关系

| Risk Level | Agent 类型 | 自由度 | 策略内容 |
|------------|-----------|--------|----------|
| **Low Risk** | `LowRiskAgent` | 最高 | 自由聊 + Coping Skills 建议 |
| **Medium Risk** | `MediumRiskAgent` | 中等 | 半结构化 + Peer Support Group 引导 |
| **High Risk** | `HighRiskAgent` | 最低 | 固定脚本 + Crisis Hotline 强制提示 |

#### 3.2 各 Agent 行为定义

**Low Risk Agent**：
- 行为：继续自由对话，提供应对策略（Coping Skills）
- 结束条件：用户说再见（goodbye）
- 示例响应："我理解你的感受。我们可以试试深呼吸或者写日记来缓解压力，你觉得哪个方法更适合你？"

**Medium Risk Agent**：
- 行为：引导用户加入 Peer Support Group
- 处理抵抗：如果用户表现出抗拒，Chatbot 需要：
  1. 识别抗拒原因（关键词：privacy / time / stigma / doubt）
  2. 针对性地解释和说服（最多 5 轮）
  3. 最终引导用户加入或提供自助资源
- **状态机**：
  - 初始建议 → 检测抗拒 → 处理抗拒（最多 5 轮）→ 接受/拒绝
  - 接受：进入"加入 Peer Group"状态，存储反馈
  - 拒绝（5 轮后）：提供自助资源或结束并记录
- 示例流程：
  ```
  Bot: "你觉得加入一个同龄人支持小组怎么样？"
  User: "我不想和陌生人聊天..."  # 检测到 "privacy" 相关抗拒
  Bot: "我理解你的担心。这个小组是匿名的，而且都是和你经历类似的人，他们可能更能理解你..."
  ```

**High Risk Agent**：
- 行为：**必须执行固定脚本**
- 脚本内容：
  1. 强烈提示用户拨打 Crisis Hotline（988）
  2. 建议安排紧急会面（urgent meeting with provider）
  3. 提供安全资源信息
- **不允许偏离脚本**

---

### 4. Safety Layer 与 High Risk 的关系

#### 4.1 Guardrails 监控范围

**规则**：
- Guardrails **时刻监控所有对话**（无论风险级别）
- 确保 Chatbot 响应符合安全与伦理标准

#### 4.2 High Risk 脚本执行规则

**规则**：
- High Risk 路径下，**必须按固定脚本逐句执行**
- 如果 Guardrails 发现脚本需要调整 → **不允许替换句子**
- Guardrails 的作用是**确保脚本本身是安全的**，而不是修改脚本

**实现逻辑**：
```python
# 伪代码
if route == "high":
    script = get_fixed_crisis_script()
    # Guardrails 检查脚本是否安全（在脚本设计阶段）
    if not guardrails.validate_script(script):
        raise SafetyError("Crisis script failed safety check")
    # 执行时严格按照脚本
    response = script.get_next_line()
    # Guardrails 再次检查（双重保险）
    response = guardrails.filter_response(response)  # 但不会改变脚本内容
```

**设计原则**：
- 固定脚本应该在**设计阶段**就通过 Guardrails 验证
- 运行时 Guardrails 只做**二次确认**，不修改内容

---

### 5. Adaptive Layer 反馈收集

#### 5.1 反馈内容维度

**规则**：收集以下三个维度的反馈

1. **满意度评分**（Satisfaction Score）
   - 范围：1-5 分
   - 问题："你对这次对话的满意度如何？"

2. **接受建议程度**（Acceptance）
   - 类型：布尔值或分类（接受/部分接受/拒绝）
   - 问题："你是否接受了 Chatbot 的建议？"

3. **后续行为**（Follow-up Behavior）
   - 类型：分类（已联系热线/已加入小组/已预约会面/无行动）
   - 问题："你后续采取了什么行动？"

#### 5.2 反馈存储与使用

**规则**：
- 存储为 `feedback_score` 字段
- **当前阶段**：仅收集和存储，不做实时调整
- **未来用途**：为 RLHF（Reinforcement Learning from Human Feedback）做准备

**数据结构**：
```python
@dataclass
class FeedbackScore:
    # 通用字段
    timestamp: datetime
    user_id: str
    conversation_id: str
    route: str  # "low" / "medium" / "high"
    
    # Low/Medium Risk 路径的反馈
    satisfaction: Optional[int] = None  # 1-5，High Risk 不收集
    acceptance: Optional[str] = None  # "accepted" / "partially" / "rejected"
    follow_up_behavior: Optional[str] = None  # "hotline" / "peer_group" / "appointment" / "none"
    
    # High Risk 路径的特殊反馈
    sought_help: Optional[bool] = None  # 是否联系热线/寻求帮助
```

**收集时机**：
- 每次对话结束
- 阶段转换时（Low→Medium, Medium→High）
- 脚本结束（High Risk）
- **High Risk 路径**：仅记录 `sought_help`，不询问满意度

---

## 🔄 完整流程示例

### 场景 1：正常流程（5 轮后触发问卷）

```
Turn 1: User: "I'm feeling a bit stressed"
  → PsyGUARD: 0.3 (Low)
  → Route: 未确定（等待问卷）

Turn 2-4: 继续对话，逐句评分

Turn 5: User: "School is really overwhelming"
  → PsyGUARD: 0.4 (Low)
  → 触发问卷（GAD-7 + PHQ-9）
  → Questionnaire Score: 8 (Mild)
  → Route: Low Risk

Turn 6+: LowRiskAgent 接管
  → 提供 Coping Skills
  → 继续自由对话
  → 逐句 PsyGUARD 监控
  → 用户说 goodbye → 结束
```

### 场景 2：提前触发问卷（检测到自杀意图）

```
Turn 1: User: "I'm feeling okay"
  → PsyGUARD: 0.2 (Low)

Turn 2: User: "I'm thinking about ending my life"
  → PsyGUARD: 0.9 (High - 自杀意图)
  → **立即触发问卷**（不等 5 轮）
  → Questionnaire Score: 15 (Moderate)
  → Route: High Risk（以聊天内容为准）

Turn 3+: HighRiskAgent 接管
  → 执行固定脚本
  → 强制提示拨打 988
  → Guardrails 监控（不修改脚本）
```

### 场景 3：风险升级（Low → Medium）

```
Turn 1-5: 正常对话
  → 触发问卷
  → Route: Low Risk

Turn 6: LowRiskAgent 自由对话
  → PsyGUARD: 0.3 (Low)

Turn 7: User: "I feel so alone, no one understands"
  → PsyGUARD: 0.6 (Medium)
  → **立即升级到 Medium Risk**
  → 切换到 MediumRiskAgent
  → 引导加入 Peer Support Group

Turn 8+: MediumRiskAgent 接管
  → 即使用户情绪好转（PsyGUARD 降到 0.3）
  → **仍然保持 Medium Risk**（不降级）
  → 继续引导加入小组
```

---

## 📊 决策树总结

### 问卷触发决策树

```
对话轮次
  ├─ PsyGUARD > 自杀意图阈值？
  │   └─ 是 → 立即触发问卷
  └─ 否 → 轮次 >= 5？
      └─ 是 → 触发问卷
```

### 风险路由决策树

```
问卷完成
  ├─ 聊天内容风险 >= High？
  │   └─ 是 → High Risk（固定脚本）
  ├─ 聊天内容风险 >= Medium？
  │   └─ 是 → Medium Risk（Peer Support）
  └─ 否 → 参考问卷分数
      └─ 映射到 Low/Medium/High
```

### 风险级别调整决策树

```
当前 Route + 新 PsyGUARD 分数
  ├─ Low + PsyGUARD >= Medium？
  │   └─ 是 → 升级到 Medium
  ├─ Medium + PsyGUARD < Medium？
  │   └─ 是 → 保持 Medium（不降级）
  └─ High？
      └─ 保持 High（不能降级）
```

---

## 🎯 实现优先级

### Phase 1: 核心流程（必须实现）

1. ✅ Perception Layer：逐句 PsyGUARD 评分
2. ✅ Perception Layer：问卷触发逻辑（5 轮或提前触发）
3. ✅ Control Layer：风险路由（问卷 + 聊天内容优先级）
4. ✅ Control Layer：风险级别调整（单向升级）
5. ✅ Conversation Layer：三种 Agent 实现
6. ✅ Safety Layer：Guardrails 监控（High Risk 脚本保护）

### Phase 2: 增强功能（后续实现）

1. Medium Risk Agent 的"说服流程"状态机
2. Adaptive Layer 反馈收集界面
3. Feedback Score 存储和查询
4. RLHF 数据准备

---

## ✅ 技术细节（已确认）

### 1. PsyGUARD 阈值设置

| 阈值类型 | 数值 | 用途 |
|---------|------|------|
| **自杀意图触发问卷** | 0.80 | 检测到自杀意图时立即触发问卷 |
| **高危直接进入固定脚本** | 0.95 | 极高风险，直接进入 High Risk 路径 |
| **Medium Risk 阈值** | 0.70 | 达到此分数触发 Medium Risk 路径 |
| **低风险清除阈值** | 0.40 | 用于稳定监测，低于此值视为低风险 |

**实现逻辑**：
```python
SUICIDE_INTENT_THRESHOLD = 0.80  # 触发问卷
HIGH_RISK_DIRECT_THRESHOLD = 0.95  # 直接 High Risk
MEDIUM_RISK_THRESHOLD = 0.70  # Medium Risk
LOW_RISK_CLEAR_THRESHOLD = 0.40  # 低风险稳定阈值
```

### 2. 问卷映射规则

#### PHQ-9 映射规则

| 分数范围 | Route | 特殊规则 |
|---------|-------|---------|
| 0-9 | Low | - |
| 10-14 | Medium | - |
| 15+ | High | - |
| 任意分数 | High | **第9题 ≥ 1（存在自杀念头）→ 直接 High** |

#### GAD-7 映射规则

| 分数范围 | Route |
|---------|-------|
| 0-9 | Low |
| 10-14 | Medium |
| 15+ | High |

#### 综合规则

1. **取两者中较高等级**：如果 PHQ-9 是 Medium，GAD-7 是 Low → 最终 Route = Medium
2. **聊天内容优先级**：如果问卷显示 Low，但聊天内容检测到 High → **以聊天内容为准（High）**

**实现逻辑**：
```python
def map_questionnaire_to_route(phq9_score, gad7_score, phq9_q9_score):
    # 特殊规则：PHQ-9 第9题（自杀念头）
    if phq9_q9_score >= 1:
        return "high"
    
    # 分别映射
    phq9_route = map_phq9(phq9_score)
    gad7_route = map_gad7(gad7_score)
    
    # 取较高等级
    route_priority = {"low": 1, "medium": 2, "high": 3}
    return max(phq9_route, gad7_route, key=lambda x: route_priority[x])
```

### 3. Medium Risk Agent 状态机

#### 抗拒关键词识别

**关键词列表**：
- `privacy` - 隐私担忧
- `time` - 时间问题
- `stigma` - 污名化担忧
- `doubt` - 怀疑/不信任

**识别逻辑**：
```python
RESISTANCE_KEYWORDS = ["privacy", "time", "stigma", "doubt"]

def detect_resistance(user_message: str) -> bool:
    message_lower = user_message.lower()
    return any(keyword in message_lower for keyword in RESISTANCE_KEYWORDS)
```

#### 说服流程规则

- **最大说服轮次**：5 回合
- **状态转换**：
  - 若接受 → 进入"加入 Peer Group"状态，存储反馈
  - 若仍拒绝（5 轮后）→ 进入"提供自助资源"或"结束并记录"状态

**状态机设计**：
```python
class MediumRiskAgentState:
    INITIAL = "initial"  # 初始建议
    ADDRESSING_RESISTANCE = "addressing"  # 处理抗拒
    PROVIDING_RESOURCES = "resources"  # 提供自助资源
    PEER_GROUP_JOINED = "joined"  # 已加入小组
    ENDED = "ended"  # 结束
```

### 4. 反馈收集时机

#### 收集触发条件

**反馈在以下时机收集**：
1. **每次对话结束**后
2. **阶段转换时**：
   - Low → Medium
   - Medium → High
   - 脚本结束（High Risk 路径）

#### High Risk 路径特殊规则

- **仅记录**："是否联系热线/寻求帮助"
- **不询问**：满意度评分（避免在危机时刻增加负担）

**实现逻辑**：
```python
def should_collect_feedback(route: str, route_changed: bool, script_ended: bool) -> bool:
    if route == "high" and script_ended:
        return True  # 但只收集"是否寻求帮助"
    if route_changed:
        return True  # 阶段转换
    # 其他情况在对话结束时收集
    return True

def collect_feedback(route: str) -> Dict[str, Any]:
    if route == "high":
        return {
            "sought_help": bool,  # 是否联系热线/寻求帮助
            # 不包含 satisfaction
        }
    else:
        return {
            "satisfaction": int,  # 1-5
            "acceptance": str,
            "follow_up_behavior": str,
        }
```

---

## 📝 下一步行动

### ✅ 已完成：技术细节确认

所有阈值、映射规则、状态机设计和反馈收集时机已确认，文档已更新。

### 🚀 可以开始实现

1. **实现 Perception Layer**：
   - PsyGUARD 服务集成（阈值：0.80/0.95/0.70/0.40）
   - 问卷触发逻辑（5 轮或提前触发）
   - 问卷映射规则（PHQ-9/GAD-7，特殊规则：第9题）

2. **实现 Control Layer**：
   - 风险路由（问卷 + 聊天内容优先级）
   - 风险级别调整（单向升级，阈值：0.70）

3. **实现 Conversation Agents**：
   - LowRiskAgent（自由聊 + Coping Skills）
   - MediumRiskAgent（状态机：抗拒识别、5 轮说服流程）
   - HighRiskAgent（固定脚本）

4. **实现 Safety Layer**：
   - Guardrails 监控（High Risk 脚本保护）

5. **实现 Adaptive Layer**：
   - 反馈收集（时机：对话结束、阶段转换、脚本结束）
   - High Risk 特殊处理（仅记录 sought_help）

6. **测试完整流程**：使用上述三个场景进行端到端测试

---

**维护者**：开发团队  
**最后更新**：2025-11-07

