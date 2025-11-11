# Control Layer Rigidity Control 分析文档

## 概述

Control Layer 通过 `rigid_score` (0.0-1.0) 控制对话的刚性程度，从而影响对话的灵活性和结构化程度。本文档详细分析 Input、Progress 和 Outputs。

---

## 1. INPUT（输入）

### 1.1 Perception Layer 输出

Control Layer 接收来自 Perception Layer 的以下输入：

#### 1.1.1 问卷评估结果
- **PHQ-9 分数** (`questionnaire_phq9_score`)
  - 范围：0-27
  - 用于评估抑郁严重程度
  - 特殊关注：Q9（自杀意念）分数

- **GAD-7 分数** (`questionnaire_gad7_score`)
  - 范围：0-21
  - 用于评估焦虑严重程度

#### 1.1.2 PsyGUARD 实时风险评分
- **PsyGUARD 分数** (`psyguard_score`)
  - 范围：0.0-1.0
  - 实时检测用户消息中的风险信号
  - 阈值：
    - `SUICIDE_INTENT_THRESHOLD = 0.80`：触发问卷
    - `MEDIUM_RISK_THRESHOLD = 0.70`：中等风险
    - `HIGH_RISK_DIRECT_THRESHOLD = 0.95`：直接高风险

#### 1.1.3 路由元数据
- **路由来源** (`route_source`)
  - `"questionnaire"`：基于问卷结果
  - `"chat_content"`：基于聊天内容（PsyGUARD）
  - `"legacy"`：向后兼容

---

### 1.2 输入数据结构

```python
# Perception Layer 输出示例
perception_inputs = {
    "phq9_result": {
        "total_score": 12.0,
        "parsed_scores": [1, 1, 2, 1, 1, 1, 1, 1, 0],  # Q9 = 0
    },
    "gad7_result": {
        "total_score": 10.0,
        "parsed_scores": [1, 1, 2, 1, 1, 2, 2],
    },
    "chat_risk_score": 0.75,  # PsyGUARD 实时评分
}
```

---

## 2. PROGRESS（处理过程）

### 2.1 路由决策 (RiskRouter)

#### 2.1.1 路由映射逻辑

```144:169:src_new/control/risk_router.py
    def _route_to_rigid_score(
        self,
        route: Route,
        phq9_score: float,
        gad7_score: float
    ) -> float:
        """Convert route to rigid_score (0.0 - 1.0)."""
        if route == "high":
            return 1.0
        elif route == "medium":
            # Medium risk: 0.5 - 0.75
            max_score = max(phq9_score, gad7_score)
            if max_score >= 15:
                return 0.75
            elif max_score >= 10:
                return 0.6
            else:
                return 0.5
        else:  # low
            # Low risk: 0.0 - 0.4
            max_score = max(phq9_score, gad7_score)
            if max_score >= 5:
                return 0.3
            else:
                return 0.15
```

**rigid_score 计算规则：**

| Route | 条件 | rigid_score | 说明 |
|-------|------|-------------|------|
| **High** | 任意 | `1.0` | 最高刚性，使用固定脚本 |
| **Medium** | max(PHQ-9, GAD-7) >= 15 | `0.75` | 高中等风险 |
| **Medium** | 10 <= max < 15 | `0.6` | 中等风险 |
| **Medium** | max < 10 | `0.5` | 低中等风险 |
| **Low** | max(PHQ-9, GAD-7) >= 5 | `0.3` | 低风险（有症状） |
| **Low** | max < 5 | `0.15` | 极低风险（几乎无症状） |

#### 2.1.2 聊天内容优先级

```133:142:src_new/control/risk_router.py
    def _apply_chat_priority(self, questionnaire_route: Route, chat_risk_score: float) -> Route:
        """Apply chat content priority over questionnaire route."""
        if chat_risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
            return "high"
        elif chat_risk_score >= MEDIUM_RISK_THRESHOLD:
            # Only upgrade if questionnaire route is lower
            route_priority = {"low": 1, "medium": 2, "high": 3}
            if route_priority.get(questionnaire_route, 0) < 2:
                return "medium"
        return questionnaire_route
```

**优先级规则：**
1. 聊天内容风险 > 问卷分数
2. 如果 PsyGUARD >= 0.95 → 直接 High Risk (rigid_score = 1.0)
3. 如果 PsyGUARD >= 0.70 → 升级到 Medium（如果当前是 Low）

---

### 2.2 路由更新 (RouteUpdater)

#### 2.2.1 单向升级规则

```26:58:src_new/control/route_updater.py
    @staticmethod
    def update_route(
        current_route: Route,
        new_psyguard_score: float
    ) -> Route:
        """
        Update route based on new PsyGUARD score.
        
        Args:
            current_route: Current route ("low", "medium", or "high")
            new_psyguard_score: New PsyGUARD risk score (0.0 - 1.0)
            
        Returns:
            Updated route (may be same or upgraded)
        """
        # High Risk: cannot downgrade
        if current_route == "high":
            return "high"
        
        # Direct upgrade to High (extremely high risk)
        if new_psyguard_score >= HIGH_RISK_DIRECT_THRESHOLD:
            return "high"
        
        # Low → Medium upgrade
        if current_route == "low" and new_psyguard_score >= MEDIUM_RISK_THRESHOLD:
            return "medium"
        
        # Medium: maintain (no downgrade)
        if current_route == "medium":
            return "medium"
        
        # Low: maintain if below threshold
        return current_route
```

**路由更新规则：**
- **Low → Medium**：如果 PsyGUARD >= 0.70
- **任意 → High**：如果 PsyGUARD >= 0.95
- **Medium/High 不降级**：即使 PsyGUARD 分数降低，也保持当前路由

**当路由升级时，rigid_score 也会相应更新：**
- Low (0.15-0.3) → Medium (0.5-0.75) → High (1.0)

---

### 2.3 控制上下文 (ControlContext)

#### 2.3.1 上下文数据结构

```12:54:src_new/control/control_context.py
@dataclass
class ControlContext:
    """Context for control layer decisions.
    
    Contains all information needed for routing and policy decisions.
    """
    user_id: str
    route: Route
    rigid_score: float
    guardrails_enabled: bool = True
    
    # Perception Layer outputs
    psyguard_score: Optional[float] = None
    questionnaire_phq9_score: Optional[float] = None
    questionnaire_gad7_score: Optional[float] = None
    phq9_q9_score: Optional[int] = None  # Suicidal ideation score
    
    # Routing metadata
    route_reason: Optional[str] = None
    route_source: Optional[str] = None  # "questionnaire", "chat_content", "legacy"
    
    # Timestamps
    route_established_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    
    # Additional metadata
    extras: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.route_established_at is None:
            self.route_established_at = datetime.now()
        if self.last_updated_at is None:
            self.last_updated_at = datetime.now()
    
    def update_route(self, new_route: Route, reason: Optional[str] = None):
        """Update route and timestamp."""
        if new_route != self.route:
            self.route = new_route
            self.last_updated_at = datetime.now()
            if reason:
                self.route_reason = reason
```

**ControlContext 存储：**
- `rigid_score`：当前刚性分数（传递给 Conversation Layer）
- `route`：当前路由（low/medium/high）
- 感知层输出：PsyGUARD 分数、问卷分数
- 路由元数据：路由原因、路由来源、时间戳

---

## 3. OUTPUTS（输出）

### 3.1 输出到 Conversation Layer

#### 3.1.1 ControlContext 传递

```36:78:src_new/conversation/pipeline.py
    async def process_message(
        self,
        user_id: str,
        user_message: str,
        control_context: ControlContext
    ) -> Dict[str, Any]:
        """
        Process a user message and generate response using appropriate agent.
        
        Args:
            user_id: User identifier
            user_message: User's message
            control_context: Control context with route and risk information
            
        Returns:
            Dict with agent response and metadata
        """
        try:
            # Get conversation history
            history = self.session_service.get_context(user_id)
            
            # Route to appropriate agent
            route = control_context.route
            
            if route == "high":
                agent_result = await self.high_agent.generate_response(
                    user_message=user_message,
                    conversation_history=history,
                    rigid_score=control_context.rigid_score
                )
            elif route == "medium":
                agent_result = await self.medium_agent.generate_response(
                    user_id=user_id,
                    user_message=user_message,
                    conversation_history=history,
                    rigid_score=control_context.rigid_score
                )
            else:  # low
                agent_result = await self.low_agent.generate_response(
                    user_message=user_message,
                    conversation_history=history,
                    rigid_score=control_context.rigid_score
                )
```

**输出内容：**
- `control_context.rigid_score`：传递给 Agent
- `control_context.route`：决定使用哪个 Agent

---

### 3.2 Agents 使用 rigid_score

#### 3.2.1 Temperature 调整公式

所有 Agents 使用相同的公式调整 temperature：

```65:66:src_new/conversation/agents/low_risk_agent.py
            # Adjust temperature based on rigidity
            adjusted_temp = max(0.1, self.temperature - 0.8 * rigid_score)
```

**公式：**
```
adjusted_temperature = max(0.1, base_temperature - 0.8 * rigid_score)
```

#### 3.2.2 不同 Agent 的 Base Temperature

| Agent | Base Temperature | rigid_score=0.0 | rigid_score=0.5 | rigid_score=1.0 |
|-------|------------------|-----------------|-----------------|-----------------|
| **LowRiskAgent** | 0.9 | 0.9 | 0.5 | 0.1 |
| **MediumRiskAgent** | 0.6 | 0.6 | 0.2 | 0.1 |
| **HighRiskAgent** | N/A | N/A | N/A | 固定脚本（不使用 LLM） |

#### 3.2.3 实际效果

**Low Risk Agent (base_temp=0.9):**
- `rigid_score=0.15` → `temp=0.78`（高灵活性）
- `rigid_score=0.3` → `temp=0.66`（中等灵活性）
- `rigid_score=0.5` → `temp=0.5`（较低灵活性）

**Medium Risk Agent (base_temp=0.6):**
- `rigid_score=0.5` → `temp=0.2`（半结构化）
- `rigid_score=0.6` → `temp=0.12`（更结构化）
- `rigid_score=0.75` → `temp=0.1`（高度结构化）

**High Risk Agent:**
- `rigid_score=1.0` → 不使用 LLM，直接返回固定脚本

---

## 4. 完整流程示例

### 4.1 场景：Low Risk → Medium Risk 升级

#### Step 1: 初始评估（Low Risk）
```python
# Input
phq9_score = 5.0
gad7_score = 3.0
chat_risk_score = 0.3

# Progress
route = "low"
rigid_score = 0.15  # max(5, 3) < 5 → 0.15

# Output
context = ControlContext(
    route="low",
    rigid_score=0.15,
    psyguard_score=0.3
)
# → LowRiskAgent: temp = 0.9 - 0.8 * 0.15 = 0.78 (高灵活性)
```

#### Step 2: 实时监控（检测到 Medium Risk）
```python
# Input (新消息)
new_chat_risk_score = 0.75  # PsyGUARD 检测到中等风险

# Progress
# RouteUpdater.update_route("low", 0.75) → "medium"
route = "medium"
rigid_score = 0.6  # 重新计算（max(5, 3) < 10 → 0.6）

# Output
context.update_route("medium", reason="psyguard_upgrade")
context.rigid_score = 0.6
# → MediumRiskAgent: temp = 0.6 - 0.8 * 0.6 = 0.12 (高度结构化)
```

---

### 4.2 场景：直接 High Risk

#### Step 1: 检测到极高风险
```python
# Input
phq9_score = 5.0
gad7_score = 3.0
chat_risk_score = 0.96  # PsyGUARD 检测到极高风险

# Progress
# _apply_chat_priority("low", 0.96) → "high" (优先级规则)
route = "high"
rigid_score = 1.0  # High Risk 总是 1.0

# Output
context = ControlContext(
    route="high",
    rigid_score=1.0,
    psyguard_score=0.96
)
# → HighRiskAgent: 不使用 LLM，返回固定脚本
```

---

## 5. 关键设计决策

### 5.1 为什么 rigid_score 影响 temperature？

- **Temperature 低**：响应更确定性、更结构化、更一致
- **Temperature 高**：响应更随机、更灵活、更自然

**映射关系：**
- `rigid_score ↑` → `temperature ↓` → 响应更结构化、更安全
- `rigid_score ↓` → `temperature ↑` → 响应更灵活、更自然

### 5.2 为什么使用线性公式？

```python
adjusted_temp = max(0.1, base_temp - 0.8 * rigid_score)
```

**原因：**
1. **简单直观**：线性关系易于理解和调试
2. **可预测**：rigid_score 变化直接影响 temperature
3. **安全下限**：`max(0.1, ...)` 确保 temperature 不会太低
4. **系数 0.8**：确保 rigid_score=1.0 时，temperature 接近最小值

### 5.3 为什么 High Risk 使用固定脚本？

- **安全性**：固定脚本经过严格审核，不包含风险内容
- **一致性**：所有 High Risk 用户收到相同的安全响应
- **可靠性**：不依赖 LLM，避免生成不当内容
- **合规性**：确保包含必要的安全信息（988 热线等）

---

## 6. 总结

### 6.1 Input → Progress → Output 流程

```
┌─────────────────────────────────────────────────────────┐
│ INPUT (Perception Layer)                                │
├─────────────────────────────────────────────────────────┤
│ • PHQ-9 分数 (0-27)                                     │
│ • GAD-7 分数 (0-21)                                     │
│ • PsyGUARD 实时评分 (0.0-1.0)                           │
│ • 路由元数据                                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PROGRESS (Control Layer)                                │
├─────────────────────────────────────────────────────────┤
│ 1. RiskRouter.decide_from_questionnaires()              │
│    → 计算 route (low/medium/high)                       │
│    → 计算 rigid_score (0.0-1.0)                         │
│                                                          │
│ 2. RouteUpdater.update_route() (可选)                   │
│    → 基于实时 PsyGUARD 分数更新路由                      │
│    → 重新计算 rigid_score                                │
│                                                          │
│ 3. ControlContext 存储                                   │
│    → 保存 rigid_score、route、感知层输出                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ OUTPUT (Conversation Layer)                             │
├─────────────────────────────────────────────────────────┤
│ 1. ConversationPipeline.process_message()                │
│    → 传递 control_context.rigid_score 到 Agent           │
│                                                          │
│ 2. Agent.generate_response()                             │
│    → 计算 adjusted_temp = base_temp - 0.8 * rigid_score │
│    → 使用调整后的 temperature 生成响应                    │
│                                                          │
│ 3. 最终响应                                              │
│    • Low Risk: 灵活、自然、共情                           │
│    • Medium Risk: 半结构化、引导性                        │
│    • High Risk: 固定脚本、安全优先                         │
└─────────────────────────────────────────────────────────┘
```

### 6.2 rigid_score 影响总结

| rigid_score | Temperature 影响 | 对话特性 | 适用场景 |
|-------------|-----------------|---------|---------|
| **0.0-0.2** | 高 (0.74-0.9) | 非常灵活、自然 | Low Risk（极低风险） |
| **0.3-0.4** | 中高 (0.58-0.66) | 灵活、共情 | Low Risk（有轻微症状） |
| **0.5-0.6** | 中 (0.2-0.5) | 半结构化、引导 | Medium Risk（中等风险） |
| **0.7-0.8** | 低 (0.1-0.34) | 高度结构化 | Medium Risk（高中等风险） |
| **1.0** | N/A | 固定脚本 | High Risk（极高风险） |

---

## 7. 半结构化实现详解

### 7.1 什么是"半结构化"？

**半结构化** = **结构化的流程** + **灵活的对话**

- **结构化部分**：明确的对话目标、状态机、轮次限制
- **灵活部分**：LLM 生成自然、共情的响应，而非固定脚本

### 7.2 Medium Risk Agent 的结构实现

#### 7.2.1 状态机（State Machine）详解

##### 什么是状态机？

**状态机（State Machine）**是一种编程模式，用来管理系统的不同"状态"和它们之间的转换。

**生活中的类比：**

想象你在餐厅点餐的过程：

1. **等待点餐**（初始状态）
   - 服务员问："您想点什么？"
   - 你回答："我要一份汉堡"
   - → 转换到"确认订单"状态

2. **确认订单**（处理状态）
   - 服务员问："要大份还是小份？"
   - 你回答："大份"
   - → 转换到"准备餐点"状态

3. **准备餐点**（执行状态）
   - 厨师开始制作
   - → 转换到"上菜"状态

4. **上菜**（完成状态）
   - 服务员把菜端上来
   - → 对话结束

**关键概念：**
- **状态（State）**：系统当前处于的"阶段"或"模式"
- **转换（Transition）**：从一个状态切换到另一个状态
- **触发条件（Trigger）**：导致状态转换的事件或条件

##### Medium Risk Agent 的状态机

```52:69:src_new/conversation/agents/medium_risk_agent.py
class MediumRiskState(Enum):
    """State machine states for Medium Risk Agent."""
    INITIAL_SUGGESTION = "initial_suggestion"
    DETECTING_RESISTANCE = "detecting_resistance"
    HANDLING_RESISTANCE = "handling_resistance"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROVIDING_RESOURCES = "providing_resources"


@dataclass
class MediumRiskAgentState:
    """State for Medium Risk Agent."""
    current_state: MediumRiskState = MediumRiskState.INITIAL_SUGGESTION
    resistance_count: int = 0
    detected_resistance_type: Optional[str] = None
    max_persuasion_turns: int = 5
    conversation_turns: List[Dict[str, Any]] = field(default_factory=list)
```

**6 个状态的含义：**

| 状态 | 含义 | 类比 |
|------|------|------|
| **INITIAL_SUGGESTION** | 初始建议 | 餐厅服务员第一次问："要不要试试我们的特色菜？" |
| **DETECTING_RESISTANCE** | 检测抗拒 | 服务员观察你的反应，看你是不是有顾虑 |
| **HANDLING_RESISTANCE** | 处理抗拒 | 服务员针对你的顾虑进行说服（最多 5 次） |
| **ACCEPTED** | 用户接受 | 你说："好的，我要试试" |
| **REJECTED** | 用户拒绝 | 你坚持拒绝，超过 5 次 |
| **PROVIDING_RESOURCES** | 提供资源 | 服务员说："没关系，这是我们店的名片，欢迎下次来" |

##### 状态机如何工作？（详细流程）

**步骤 1：初始化**
```python
# 用户第一次发送消息
user_message = "I've been feeling really anxious."

# Agent 创建状态对象
state = MediumRiskAgentState()
# state.current_state = INITIAL_SUGGESTION（初始状态）
# state.resistance_count = 0
# state.detected_resistance_type = None
```

**步骤 2：根据当前状态选择行为**

```129:145:src_new/conversation/agents/medium_risk_agent.py
            # State machine logic
            if state.current_state == MediumRiskState.INITIAL_SUGGESTION:
                response = await self._handle_initial_suggestion(
                    user_message, conversation_history, adjusted_temp
                )
                # Check for resistance
                resistance_type = self._detect_resistance(user_message)
                if resistance_type:
                    state.current_state = MediumRiskState.HANDLING_RESISTANCE
                    state.detected_resistance_type = resistance_type
                    state.resistance_count = 1
                else:
                    # Check if user accepts
                    if self._is_acceptance(user_message):
                        state.current_state = MediumRiskState.ACCEPTED
                    else:
                        state.current_state = MediumRiskState.DETECTING_RESISTANCE
```

**代码解释：**

1. **检查当前状态**：`if state.current_state == INITIAL_SUGGESTION`
   - 如果当前是"初始建议"状态，执行初始建议逻辑

2. **执行当前状态的行为**：`_handle_initial_suggestion(...)`
   - 调用 LLM 生成响应，建议用户加入 peer group

3. **检测触发条件**：
   - `_detect_resistance(user_message)`：检查用户是否表达抗拒
   - `_is_acceptance(user_message)`：检查用户是否接受

4. **状态转换**：
   - 如果检测到抗拒 → 转换到 `HANDLING_RESISTANCE`
   - 如果用户接受 → 转换到 `ACCEPTED`
   - 否则 → 转换到 `DETECTING_RESISTANCE`

**步骤 3：处理抗拒状态（循环最多 5 轮）**

```147:167:src_new/conversation/agents/medium_risk_agent.py
            elif state.current_state == MediumRiskState.HANDLING_RESISTANCE:
                response = await self._handle_resistance(
                    user_id, user_message, conversation_history, adjusted_temp
                )
                # Update resistance count
                state.resistance_count += 1
                
                # Check if exceeded max turns
                if state.resistance_count > state.max_persuasion_turns:
                    state.current_state = MediumRiskState.REJECTED
                    response = await self._provide_resources(
                        user_message, conversation_history, adjusted_temp
                    )
                elif self._is_acceptance(user_message):
                    state.current_state = MediumRiskState.ACCEPTED
                    response["peer_group_accepted"] = True
                else:
                    # Check for new resistance type
                    new_resistance = self._detect_resistance(user_message)
                    if new_resistance and new_resistance != state.detected_resistance_type:
                        state.detected_resistance_type = new_resistance
```

**代码解释：**

1. **进入抗拒处理状态**：
   - 使用 `PERSUASION_PROMPT` 生成针对性响应
   - 针对检测到的抗拒类型（privacy/time/stigma/doubt）进行说服

2. **增加抗拒计数**：`state.resistance_count += 1`
   - 记录已经进行了多少轮说服

3. **检查退出条件**：
   - **超过 5 轮**：`resistance_count > 5` → 转换到 `REJECTED`
   - **用户接受**：`_is_acceptance()` → 转换到 `ACCEPTED`
   - **继续说服**：保持在 `HANDLING_RESISTANCE` 状态

##### 完整的状态转换图

```
┌─────────────────────────────────────────────────────────┐
│                    INITIAL_SUGGESTION                    │
│  (初始状态：建议加入 peer group)                          │
│                                                          │
│  Bot: "我理解你的焦虑。你有没有考虑过加入一个同伴支持小组？│
│       *peer group has a moderator for safety*"          │
└─────────────────────────────────────────────────────────┘
                         ↓
          ┌──────────────┴──────────────┐
          │                             │
          ↓                             ↓
┌─────────────────────┐    ┌──────────────────────┐
│  DETECTING_RESISTANCE│    │      ACCEPTED        │
│  (检测抗拒)           │    │  (用户接受)          │
│                      │    │                      │
│  观察用户反应...       │    │  Bot: "太好了！让我  │
│                      │    │       为你介绍下一步"│
└─────────────────────┘    └──────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────┐
│                 HANDLING_RESISTANCE                      │
│  (处理抗拒：最多 5 轮)                                    │
│                                                          │
│  Round 1: "我理解你对隐私的担忧。Peer group 是匿名的..." │
│  Round 2: "你可以先观察一下，不需要立即参与..."          │
│  Round 3: "Peer group 有很多人找到了支持..."            │
│  ...                                                    │
│  Round 5: "如果你还是不确定，我可以提供其他资源..."      │
└─────────────────────────────────────────────────────────┘
          ↓
    ┌─────┴─────┐
    │           │
    ↓           ↓
┌─────────┐  ┌─────────────┐
│ ACCEPTED│  │   REJECTED   │
│(用户接受)│  │ (超过 5 轮)   │
│         │  │              │
│ 确认加入 │  │ 提供资源      │
└─────────┘  └─────────────┘
```

##### 实际对话示例（展示状态转换）

**场景：用户表达焦虑，然后表现出隐私担忧**

```
┌─────────────────────────────────────────────────────────┐
│ Turn 1: 用户发送第一条消息                                │
├─────────────────────────────────────────────────────────┤
│ 用户: "I've been feeling really anxious and isolated."  │
│                                                          │
│ [状态机检查]                                              │
│ • current_state = INITIAL_SUGGESTION                    │
│ • 执行: _handle_initial_suggestion()                    │
│ • 检测抗拒: None (没有检测到抗拒)                         │
│ • 检测接受: False (没有明确接受)                          │
│ • 状态转换: INITIAL_SUGGESTION → DETECTING_RESISTANCE   │
│                                                          │
│ Bot: "我理解你的焦虑。你有没有考虑过加入一个同伴支持小组？│
│      *peer group has a moderator for safety*"           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Turn 2: 用户表达隐私担忧                                   │
├─────────────────────────────────────────────────────────┤
│ 用户: "I don't want to share my personal information."  │
│                                                          │
│ [状态机检查]                                              │
│ • current_state = DETECTING_RESISTANCE                  │
│ • 检测抗拒: _detect_resistance() → "privacy"            │
│ • 状态转换: DETECTING_RESISTANCE → HANDLING_RESISTANCE  │
│ • resistance_count = 1                                   │
│ • detected_resistance_type = "privacy"                  │
│ • 执行: _handle_resistance() (使用 PERSUASION_PROMPT)   │
│                                                          │
│ Bot: "我理解你对隐私的担忧。Peer group 是完全匿名的，    │
│      你可以选择只分享你想分享的内容。而且有 moderator    │
│      确保安全和隐私保护。"                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Turn 3: 用户继续犹豫                                       │
├─────────────────────────────────────────────────────────┤
│ 用户: "I'm still not sure. What if people judge me?"    │
│                                                          │
│ [状态机检查]                                              │
│ • current_state = HANDLING_RESISTANCE                   │
│ • 检测抗拒: _detect_resistance() → "stigma"             │
│ • resistance_count = 2 (从 1 增加到 2)                   │
│ • detected_resistance_type = "stigma" (更新抗拒类型)     │
│ • 检查: resistance_count (2) <= max_persuasion_turns (5) │
│ • 检查接受: False                                         │
│ • 状态保持: HANDLING_RESISTANCE (继续说服)                │
│ • 执行: _handle_resistance() (针对 stigma)               │
│                                                          │
│ Bot: "我理解你担心被评判。Peer group 里的人都在经历      │
│      类似的挑战，他们更可能理解你，而不是评判你。        │
│      Moderator 也会确保环境是支持和安全的。"              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Turn 4-6: 继续说服（省略中间轮次）                         │
├─────────────────────────────────────────────────────────┤
│ ... resistance_count 增加到 3, 4, 5 ...                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Turn 7: 用户最终接受                                       │
├─────────────────────────────────────────────────────────┤
│ 用户: "Okay, I'll give it a try. I'd like to join."     │
│                                                          │
│ [状态机检查]                                              │
│ • current_state = HANDLING_RESISTANCE                   │
│ • resistance_count = 5                                   │
│ • 检测接受: _is_acceptance() → True                      │
│ • 状态转换: HANDLING_RESISTANCE → ACCEPTED               │
│ • 执行: _confirm_acceptance()                            │
│                                                          │
│ Bot: "太好了！我很高兴你想试试。让我为你介绍下一步：      │
│      1. 你会被邀请加入一个安全的小组                      │
│      2. 你可以先观察，不需要立即参与                      │
│      3. Moderator 会在那里确保每个人的安全..."            │
└─────────────────────────────────────────────────────────┘
```

##### 状态机的关键优势

1. **明确知道对话进行到哪一步**
   ```python
   # 代码可以清楚知道当前状态
   if state.current_state == HANDLING_RESISTANCE:
       # 我知道用户正在抗拒，已经说服了 N 轮
       if state.resistance_count > 5:
           # 超过限制，应该停止说服
   ```

2. **自动状态转换**
   - 不需要手动管理"现在应该做什么"
   - 状态机根据用户消息自动判断下一步

3. **确保关键步骤不遗漏**
   - 必须在 `INITIAL_SUGGESTION` 状态提及 moderator
   - 必须在 `HANDLING_RESISTANCE` 状态处理抗拒
   - 必须在 `ACCEPTED` 状态确认加入

4. **防止无限循环**
   - `resistance_count` 跟踪说服轮次
   - 超过 5 轮自动转换到 `REJECTED` 状态

##### 状态机 vs 没有状态机

**没有状态机的对话（混乱）：**
```
用户: "I'm anxious"
Bot: "要不要加入 peer group？"

用户: "I'm worried about privacy"
Bot: "要不要加入 peer group？"  # 重复同样的问题，不知道用户已经拒绝

用户: "I said I'm worried!"
Bot: "要不要加入 peer group？"  # 继续重复，没有进展
```

**有状态机的对话（有序）：**
```
[状态: INITIAL_SUGGESTION]
用户: "I'm anxious"
Bot: "要不要加入 peer group？*有 moderator 确保安全*"

[状态转换: HANDLING_RESISTANCE, resistance_count=1]
用户: "I'm worried about privacy"
Bot: "我理解你的担忧。Peer group 是匿名的..."  # 针对隐私问题回应

[状态: HANDLING_RESISTANCE, resistance_count=2]
用户: "I'm still worried"
Bot: "你可以先观察，不需要立即参与..."  # 继续说服，但策略不同

[状态转换: ACCEPTED]
用户: "Okay, I'll try"
Bot: "太好了！让我为你介绍下一步..."  # 确认加入，提供下一步
```

##### 状态机的核心代码逻辑

```python
# 伪代码：状态机的核心逻辑
def generate_response(user_message, current_state):
    # 1. 根据当前状态选择行为
    if current_state == INITIAL_SUGGESTION:
        response = suggest_peer_group(user_message)
        
        # 2. 检查触发条件
        if detect_resistance(user_message):
            # 3. 状态转换
            current_state = HANDLING_RESISTANCE
        elif detect_acceptance(user_message):
            current_state = ACCEPTED
            
    elif current_state == HANDLING_RESISTANCE:
        response = handle_resistance(user_message)
        resistance_count += 1
        
        # 2. 检查退出条件
        if resistance_count > 5:
            current_state = REJECTED
        elif detect_acceptance(user_message):
            current_state = ACCEPTED
        # 否则保持 HANDLING_RESISTANCE 状态
    
    elif current_state == ACCEPTED:
        response = confirm_acceptance(user_message)
        # 不需要转换状态，对话可以结束
        
    return response, current_state
```

**关键点：**
- **状态决定行为**：不同状态执行不同的函数
- **条件触发转换**：用户消息触发状态转换
- **状态保持信息**：`resistance_count`、`detected_resistance_type` 等

##### 状态机的核心思想（一句话总结）

**状态机就像一个"智能导航系统"：**
- 它知道"现在在哪里"（当前状态）
- 它知道"下一步该做什么"（状态对应的行为）
- 它知道"什么时候该转弯"（触发条件）
- 它知道"什么时候到达目的地"（终止状态）

**在 Medium Risk Agent 中：**
- **现在在哪里**：`state.current_state = HANDLING_RESISTANCE`
- **下一步该做什么**：调用 `_handle_resistance()` 处理抗拒
- **什么时候该转弯**：用户接受 → 转到 `ACCEPTED`，超过 5 轮 → 转到 `REJECTED`
- **什么时候到达目的地**：进入 `ACCEPTED` 或 `REJECTED` 状态

##### 如何知道当前在什么状态？

**1. 状态存储机制**

```82:94:src_new/conversation/agents/medium_risk_agent.py
    def __init__(self, llm_service: Optional[OllamaService] = None):
        """Initialize Medium Risk Agent."""
        self.llm_service = llm_service or OllamaService()
        self.temperature = 0.6  # Semi-structured
        self.max_tokens = 512
        # Per-user state storage
        self._user_states: Dict[str, MediumRiskAgentState] = {}
    
    def _get_state(self, user_id: str) -> MediumRiskAgentState:
        """Get or create state for user."""
        if user_id not in self._user_states:
            self._user_states[user_id] = MediumRiskAgentState()
        return self._user_states[user_id]
```

**关键点：**
- **每个用户独立状态**：`self._user_states[user_id]` 存储每个用户的状态
- **状态持久化**：同一个用户的多次对话共享同一状态对象
- **状态查询**：通过 `_get_state(user_id)` 获取当前用户的状态

**示例：**
```python
# 用户 A 发送消息
user_a_state = agent._get_state("user_a")
# 如果 user_a 不存在，创建新状态：
#   current_state = INITIAL_SUGGESTION
#   resistance_count = 0
#   detected_resistance_type = None

# 用户 B 发送消息（独立状态）
user_b_state = agent._get_state("user_b")
# user_b 的状态与 user_a 完全独立
```

**2. 状态检查流程**

每轮对话时，系统会：

```python
# Step 1: 获取当前用户的状态
state = self._get_state(user_id)
# state.current_state 就是当前状态！

# Step 2: 根据当前状态选择行为
if state.current_state == INITIAL_SUGGESTION:
    # 执行初始建议逻辑
elif state.current_state == HANDLING_RESISTANCE:
    # 执行抗拒处理逻辑
    # 可以访问：state.resistance_count, state.detected_resistance_type
```

##### 如何检测到抗拒？

**抗拒检测机制：关键词匹配**

```96:102:src_new/conversation/agents/medium_risk_agent.py
    def _detect_resistance(self, user_message: str) -> Optional[str]:
        """Detect resistance type from user message."""
        message_lower = user_message.lower()
        for resistance_type, keywords in RESISTANCE_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                return resistance_type
        return None
```

**关键词定义：**

```16:21:src_new/conversation/agents/medium_risk_agent.py
RESISTANCE_KEYWORDS = {
    "privacy": ["privacy", "private", "anonymous", "personal", "confidential"],
    "time": ["time", "busy", "schedule", "don't have time", "no time"],
    "stigma": ["stigma", "embarrassed", "ashamed", "judge", "judgment"],
    "doubt": ["doubt", "not sure", "don't think", "won't help", "doesn't work"]
}
```

**检测流程：**

```
用户消息: "I don't want to share my personal information"

Step 1: 转换为小写
  → "i don't want to share my personal information"

Step 2: 遍历所有抗拒类型
  → 检查 "privacy" 关键词: ["privacy", "private", "anonymous", "personal", "confidential"]
  → 发现 "personal" 在消息中！
  
Step 3: 返回抗拒类型
  → return "privacy"
```

**实际例子：**

| 用户消息 | 检测结果 | 说明 |
|---------|---------|------|
| "I don't want to share my **personal** information" | `"privacy"` | 匹配到 "personal" |
| "I'm too **busy**, I don't have **time**" | `"time"` | 匹配到 "busy" 和 "time" |
| "I'm **embarrassed** about joining" | `"stigma"` | 匹配到 "embarrassed" |
| "I'm **not sure** if it will **help**" | `"doubt"` | 匹配到 "not sure" |
| "I'm feeling better today" | `None` | 没有匹配到任何抗拒关键词 |

**检测到抗拒后的处理：**

```python
# 在 generate_response 中
resistance_type = self._detect_resistance(user_message)
if resistance_type:  # 如果检测到抗拒
    # 更新状态
    state.current_state = MediumRiskState.HANDLING_RESISTANCE
    state.detected_resistance_type = resistance_type
    state.resistance_count = 1
```

##### 如何检测用户接受？

**接受检测机制：关键词匹配**

```506:513:src_new/conversation/agents/medium_risk_agent.py
    def _is_acceptance(self, user_message: str) -> bool:
        """Check if user message indicates acceptance."""
        acceptance_keywords = [
            "yes", "okay", "ok", "sure", "I'll join", "sounds good",
            "I'd like to", "I want to", "let's do it"
        ]
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in acceptance_keywords)
```

**检测流程：**

```
用户消息: "Okay, I'll give it a try. I'd like to join."

Step 1: 转换为小写
  → "okay, i'll give it a try. i'd like to join."

Step 2: 检查接受关键词
  → 检查 "yes", "okay", "ok", "sure", "I'll join", "sounds good", ...
  → 发现 "okay" 和 "i'd like to" 都在消息中！
  
Step 3: 返回结果
  → return True
```

**实际例子：**

| 用户消息 | 检测结果 | 说明 |
|---------|---------|------|
| "**Yes**, I'll join" | `True` | 匹配到 "yes" |
| "**Okay**, I'll give it a try" | `True` | 匹配到 "okay" |
| "**Sure**, sounds good" | `True` | 匹配到 "sure" 和 "sounds good" |
| "I **want to** join" | `True` | 匹配到 "I want to" |
| "Maybe later" | `False` | 没有匹配到接受关键词 |
| "I'm not sure" | `False` | 没有匹配到接受关键词 |

##### 完整的状态检测和转换流程

**每轮对话的完整流程：**

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: 获取当前状态                                      │
├─────────────────────────────────────────────────────────┤
│ state = agent._get_state(user_id)                       │
│                                                          │
│ 结果：                                                   │
│ • state.current_state = "initial_suggestion"            │
│ • state.resistance_count = 0                            │
│ • state.detected_resistance_type = None                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: 根据当前状态执行行为                               │
├─────────────────────────────────────────────────────────┤
│ if state.current_state == INITIAL_SUGGESTION:           │
│     response = await _handle_initial_suggestion(...)    │
│                                                          │
│ 生成响应："要不要加入 peer group？*有 moderator*"        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: 检测用户消息（触发条件）                           │
├─────────────────────────────────────────────────────────┤
│ user_message = "I don't want to share my privacy"       │
│                                                          │
│ # 检测抗拒                                               │
│ resistance_type = _detect_resistance(user_message)      │
│ # → 返回 "privacy"                                       │
│                                                          │
│ # 检测接受                                               │
│ is_accepted = _is_acceptance(user_message)              │
│ # → 返回 False                                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: 状态转换                                          │
├─────────────────────────────────────────────────────────┤
│ if resistance_type:  # "privacy" != None                │
│     # 更新状态                                           │
│     state.current_state = HANDLING_RESISTANCE           │
│     state.detected_resistance_type = "privacy"          │
│     state.resistance_count = 1                          │
│                                                          │
│ 状态更新后：                                              │
│ • state.current_state = "handling_resistance"           │
│ • state.resistance_count = 1                            │
│ • state.detected_resistance_type = "privacy"            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: 下一轮对话（状态已更新）                           │
├─────────────────────────────────────────────────────────┤
│ # 用户发送下一条消息                                      │
│ user_message = "I'm still worried about privacy"        │
│                                                          │
│ # 再次获取状态（状态已更新）                               │
│ state = agent._get_state(user_id)                       │
│ # state.current_state = "handling_resistance" ✅         │
│                                                          │
│ # 根据新状态执行行为                                      │
│ if state.current_state == HANDLING_RESISTANCE:          │
│     response = await _handle_resistance(...)            │
│     state.resistance_count += 1  # 增加到 2             │
└─────────────────────────────────────────────────────────┘
```

##### 状态检测的实际代码执行

**完整示例：用户从初始状态到抗拒处理**

```python
# ========== Turn 1: 用户第一次发送消息 ==========
user_id = "user_123"
user_message_1 = "I've been feeling really anxious."

# Step 1: 获取状态（新用户，创建初始状态）
state = agent._get_state(user_id)
# state.current_state = INITIAL_SUGGESTION
# state.resistance_count = 0
# state.detected_resistance_type = None

# Step 2: 根据状态执行行为
if state.current_state == INITIAL_SUGGESTION:
    response = await agent._handle_initial_suggestion(...)
    # Bot: "我理解你的焦虑。要不要加入 peer group？*有 moderator*"

# Step 3: 检测触发条件
resistance_type = agent._detect_resistance(user_message_1)
# → None (没有检测到抗拒)

is_accepted = agent._is_acceptance(user_message_1)
# → False (没有检测到接受)

# Step 4: 状态转换
if resistance_type:  # None → False，不执行
    pass
elif is_accepted:  # False → False，不执行
    pass
else:
    state.current_state = DETECTING_RESISTANCE  # 转换状态

# ========== Turn 2: 用户表达抗拒 ==========
user_message_2 = "I don't want to share my personal information."

# Step 1: 获取状态（状态已更新）
state = agent._get_state(user_id)
# state.current_state = DETECTING_RESISTANCE  ✅
# state.resistance_count = 0
# state.detected_resistance_type = None

# Step 2: 根据状态执行行为
if state.current_state == DETECTING_RESISTANCE:
    # 继续处理...

# Step 3: 检测触发条件
resistance_type = agent._detect_resistance(user_message_2)
# → "privacy" ✅ (检测到 "personal" 关键词)

is_accepted = agent._is_acceptance(user_message_2)
# → False

# Step 4: 状态转换
if resistance_type:  # "privacy" → True ✅
    state.current_state = HANDLING_RESISTANCE  # 转换状态
    state.detected_resistance_type = "privacy"  # 记录抗拒类型
    state.resistance_count = 1  # 开始计数

# ========== Turn 3: 继续对话（状态已更新） ==========
user_message_3 = "I'm still worried."

# Step 1: 获取状态（状态已更新）
state = agent._get_state(user_id)
# state.current_state = HANDLING_RESISTANCE  ✅
# state.resistance_count = 1  ✅
# state.detected_resistance_type = "privacy"  ✅

# Step 2: 根据状态执行行为
if state.current_state == HANDLING_RESISTANCE:
    response = await agent._handle_resistance(...)
    # 使用 PERSUASION_PROMPT，针对 "privacy" 类型
    state.resistance_count += 1  # 增加到 2

# Step 3: 检测触发条件
resistance_type = agent._detect_resistance(user_message_3)
# → None (没有新的抗拒类型)

is_accepted = agent._is_acceptance(user_message_3)
# → False

# Step 4: 状态转换
if state.resistance_count > 5:  # 2 > 5 → False
    pass
elif is_accepted:  # False → False
    pass
else:
    # 保持 HANDLING_RESISTANCE 状态
    pass
```

##### 关键词检测的局限性

**当前实现：简单关键词匹配**

**优点：**
- ✅ 实现简单、快速
- ✅ 不需要 LLM，成本低
- ✅ 规则明确，易于调试

**局限性：**
- ❌ 可能漏检（用户用其他方式表达抗拒）
- ❌ 可能误检（关键词出现在其他上下文中）
- ❌ 无法理解语义（"我不确定" vs "我不确定这是不是个好主意"）

**改进方向：**
- 使用 LLM 进行语义理解
- 结合上下文判断
- 使用更复杂的 NLP 模型

##### 状态信息的存储和查询

**状态对象包含的信息：**

```python
state = MediumRiskAgentState(
    current_state = HANDLING_RESISTANCE,  # 当前状态
    resistance_count = 3,  # 已说服轮次
    detected_resistance_type = "privacy",  # 检测到的抗拒类型
    max_persuasion_turns = 5,  # 最大说服轮次
    conversation_turns = [  # 对话历史
        {"user_message": "...", "bot_response": "...", "state": "..."},
        ...
    ]
)
```

**如何查询状态信息：**

```python
# 查询当前状态
current_state = state.current_state  # "handling_resistance"

# 查询抗拒计数
count = state.resistance_count  # 3

# 查询抗拒类型
resistance_type = state.detected_resistance_type  # "privacy"

# 判断是否需要停止说服
if state.resistance_count > state.max_persuasion_turns:
    # 超过 5 轮，应该停止
    pass
```

##### 状态持久化（跨对话保持）

**重要：状态在对话过程中保持**

```python
# Turn 1
state = agent._get_state("user_123")
state.current_state = INITIAL_SUGGESTION
# 状态保存在 agent._user_states["user_123"]

# Turn 2（同一用户，不同消息）
state = agent._get_state("user_123")  # 获取同一个状态对象！
state.current_state = HANDLING_RESISTANCE  # 状态已更新
state.resistance_count = 1

# Turn 3（继续对话）
state = agent._get_state("user_123")  # 仍然是同一个状态对象
# state.resistance_count = 1  ✅ (保持之前的值)
# state.current_state = HANDLING_RESISTANCE  ✅ (保持之前的值)
```

**状态重置：**

```515:518:src_new/conversation/agents/medium_risk_agent.py
    def reset_state(self, user_id: str):
        """Reset state for a user (e.g., after conversation ends)."""
        if user_id in self._user_states:
            del self._user_states[user_id]
```

**使用场景：**
- 对话结束
- 用户开始新对话
- 需要重置状态时

#### 7.2.2 结构化 System Prompt

```24:40:src_new/conversation/agents/medium_risk_agent.py
MEDIUM_RISK_SYSTEM_PROMPT = """You are a supportive and empathetic mental health assistant for teens.

Your role in MEDIUM RISK conversations:
- Acknowledge the user's anxiety and concerns
- Suggest joining a peer support group (mention: "*peer group has a moderator for safety*")
- Handle resistance with empathy and understanding
- Address specific concerns (privacy, time, stigma, doubt)
- Confirm if the user wants to join

Guidelines:
- Be semi-structured but empathetic
- Address resistance with specific counter-arguments
- Maximum 5 persuasion turns
- If user accepts: confirm and provide next steps
- If user still resists after 5 turns: offer self-help resources

Remember: This is a medium-risk conversation, so you need to balance structure with empathy."""
```

**结构化的关键点：**
1. **明确的目标**：建议加入 peer support group
2. **必须提及的安全信息**：peer group has a moderator
3. **明确的限制**：最多 5 轮说服
4. **明确的处理规则**：处理 4 种抗拒类型（privacy, time, stigma, doubt）

#### 7.2.3 关键词检测（结构化规则）

```16:21:src_new/conversation/agents/medium_risk_agent.py
RESISTANCE_KEYWORDS = {
    "privacy": ["privacy", "private", "anonymous", "personal", "confidential"],
    "time": ["time", "busy", "schedule", "don't have time", "no time"],
    "stigma": ["stigma", "embarrassed", "ashamed", "judge", "judgment"],
    "doubt": ["doubt", "not sure", "don't think", "won't help", "doesn't work"]
}
```

**结构化检测：**
- 检测用户抗拒类型（基于关键词）
- 针对不同类型使用不同的处理策略
- 记录抗拒计数，确保不超过 5 轮

#### 7.2.4 状态驱动的响应生成

```129:183:src_new/conversation/agents/medium_risk_agent.py
            # State machine logic
            if state.current_state == MediumRiskState.INITIAL_SUGGESTION:
                response = await self._handle_initial_suggestion(
                    user_message, conversation_history, adjusted_temp
                )
                # Check for resistance
                resistance_type = self._detect_resistance(user_message)
                if resistance_type:
                    state.current_state = MediumRiskState.HANDLING_RESISTANCE
                    state.detected_resistance_type = resistance_type
                    state.resistance_count = 1
                else:
                    # Check if user accepts
                    if self._is_acceptance(user_message):
                        state.current_state = MediumRiskState.ACCEPTED
                    else:
                        state.current_state = MediumRiskState.DETECTING_RESISTANCE
                        
            elif state.current_state == MediumRiskState.HANDLING_RESISTANCE:
                response = await self._handle_resistance(
                    user_id, user_message, conversation_history, adjusted_temp
                )
                # Update resistance count
                state.resistance_count += 1
                
                # Check if exceeded max turns
                if state.resistance_count > state.max_persuasion_turns:
                    state.current_state = MediumRiskState.REJECTED
                    response = await self._provide_resources(
                        user_message, conversation_history, adjusted_temp
                    )
                elif self._is_acceptance(user_message):
                    state.current_state = MediumRiskState.ACCEPTED
                    response["peer_group_accepted"] = True
                else:
                    # Check for new resistance type
                    new_resistance = self._detect_resistance(user_message)
                    if new_resistance and new_resistance != state.detected_resistance_type:
                        state.detected_resistance_type = new_resistance
                    
            elif state.current_state == MediumRiskState.ACCEPTED:
                response = await self._confirm_acceptance(
                    user_message, conversation_history, adjusted_temp
                )
                
            elif state.current_state == MediumRiskState.REJECTED:
                response = await self._provide_resources(
                    user_message, conversation_history, adjusted_temp
                )
```

**结构化的关键机制：**
1. **状态判断**：根据当前状态选择不同的处理函数
2. **自动状态转换**：基于用户消息自动转换状态
3. **轮次限制**：`resistance_count > max_persuasion_turns` 触发状态转换
4. **不同状态的 System Prompt**：每个状态使用不同的提示词

#### 7.2.5 不同状态的 System Prompt

**初始建议状态：**
```python
MEDIUM_RISK_SYSTEM_PROMPT  # 包含：建议 peer group、提及 moderator
```

**处理抗拒状态：**
```42:49:src_new/conversation/agents/medium_risk_agent.py
PERSUASION_PROMPT = """The user has expressed resistance to joining a peer support group.

Your task:
1. Identify the specific concern (privacy, time, stigma, or doubt)
2. Provide a targeted, empathetic response addressing that concern
3. Reassure them about the peer group's safety and benefits

Be understanding but persistent (within the 5-turn limit)."""
```

**接受状态：**
```python
"The user has accepted joining the peer support group. Confirm this and provide next steps."
```

**拒绝状态：**
```python
"The user has declined joining the peer support group after multiple attempts. Provide self-help resources and support options."
```

### 7.3 半结构化的平衡

#### 结构化部分（硬性规则）
1. ✅ **状态机**：明确的对话流程
2. ✅ **轮次限制**：最多 5 轮说服
3. ✅ **关键词检测**：识别抗拒类型
4. ✅ **必须信息**：必须提及 moderator
5. ✅ **状态转换规则**：基于用户消息自动转换

#### 灵活部分（LLM 生成）
1. ✅ **自然对话**：LLM 生成共情、自然的响应
2. ✅ **上下文理解**：理解用户的具体担忧
3. ✅ **个性化回应**：针对不同抗拒类型生成不同回应
4. ✅ **语言多样性**：不重复相同的表达

### 7.4 与 Low/High Risk 的对比

| 特性 | Low Risk | Medium Risk (半结构化) | High Risk |
|------|----------|----------------------|-----------|
| **状态机** | ❌ 无 | ✅ 6 个状态 | ❌ 无（固定脚本） |
| **System Prompt** | 通用提示词 | ✅ 状态特定提示词 | ❌ 无（固定脚本） |
| **关键词检测** | ❌ 无 | ✅ 抗拒检测 | ❌ 无 |
| **轮次限制** | ❌ 无 | ✅ 5 轮说服限制 | ❌ 无 |
| **LLM 灵活性** | 高 (temp=0.9) | 中 (temp=0.6, 调整后更低) | 无 (固定脚本) |
| **对话目标** | 自由对话 | ✅ 引导加入 peer group | 提供危机热线 |

### 7.5 实现效果

**示例对话流程：**

```
[状态: INITIAL_SUGGESTION]
Bot: "我理解你的焦虑。你有没有考虑过加入一个同伴支持小组？*peer group has a moderator for safety*"

[用户: "我不想分享我的隐私"]
[检测到: privacy 抗拒]
[状态转换: HANDLING_RESISTANCE, resistance_count=1]

[状态: HANDLING_RESISTANCE]
Bot: "我理解你对隐私的担忧。Peer group 是匿名的，你可以只分享你想分享的内容。而且有 moderator 确保安全..."

[用户: "我还是不确定"]
[状态: HANDLING_RESISTANCE, resistance_count=2]
Bot: "没关系，我可以回答你的任何问题。比如，你可以先观察一下，不需要立即参与..."

[... 继续到第 5 轮或用户接受 ...]

[用户: "好吧，我想试试"]
[状态转换: ACCEPTED]
Bot: "太好了！让我为你介绍下一步..."
```

### 7.6 结构化的优势

1. **确保关键信息传递**：必须提及 moderator，确保安全
2. **控制对话方向**：引导用户加入 peer group
3. **避免无限循环**：5 轮限制防止无效说服
4. **保持一致性**：所有 Medium Risk 用户都遵循相同流程
5. **同时保持灵活性**：LLM 生成自然、个性化的响应

---

## 8. 未来改进方向

### 8.1 动态 rigid_score 调整
- 基于对话历史动态调整 rigid_score
- 考虑用户响应模式
- 实现自适应刚性控制

### 8.2 多维度刚性控制
- 不仅控制 temperature，还控制：
  - 响应长度
  - 结构化程度
  - 安全检查频率

### 8.3 个性化刚性策略
- 基于用户历史数据
- 考虑用户偏好
- 实现个性化对话策略

### 8.4 增强半结构化
- 更细粒度的状态划分
- 更智能的抗拒检测（使用 LLM 而非关键词）
- 动态调整说服策略

---

**文档版本**：1.0  
**最后更新**：2025-01-XX  
**维护者**：开发团队

