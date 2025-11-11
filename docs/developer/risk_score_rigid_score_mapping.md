# Risk Score and Rigid Score Mapping Guide

本文档详细回答三个核心问题：
1. 如何定义风险评分（Risk Score）？
2. 如何将风险评分映射到刚性评分（Rigid Score）？
3. 如何使用刚性评分控制聊天机器人的灵活性？

---

## 1. 如何定义风险评分（Risk Score）？

风险评分由两个主要来源组合而成：
- **PsyGUARD 实时风险评分**：基于聊天内容的实时检测
- **问卷评估评分**：基于 PHQ-9 和 GAD-7 问卷

### 1.1 PsyGUARD 风险评分

**定义：**
- 使用 PsyGUARD-RoBERTa 多标签分类模型
- 检测 11 种风险标签（自杀、自伤、攻击等）
- 返回 0.0-1.0 之间的风险分数

**风险标签：**

```python
# 高风险标签（自杀和自伤相关）
HIGH_RISK_LABEL_INDICES = [0, 1, 2, 3, 4, 7, 8, 9]
# 0: 自杀未遂
# 1: 自杀准备行为
# 2: 自杀计划
# 3: 主动自杀意图
# 4: 被动自杀意图
# 7: 自伤行为
# 8: 自伤意图
# 9: 关于自杀的探索

# 中等风险标签（攻击行为）
MEDIUM_RISK_LABEL_INDICES = [5, 6]
# 5: 用户攻击行为
# 6: 他人攻击行为
```

**风险分数计算：**

```165:197:src_new/perception/psyguard_service.py
    def _calculate_risk_score(self, predictions: torch.Tensor) -> float:
        """
        Calculate risk score from model predictions.
        
        Args:
            predictions: Binary predictions tensor (11 labels)
            
        Returns:
            Risk score in [0, 1]
        """
        # 将预测转换为列表
        pred_list = predictions[0].detach().cpu().tolist()
        
        # 检查高风险标签
        high_risk_detected = any(pred_list[i] == 1 for i in HIGH_RISK_LABEL_INDICES)
        medium_risk_detected = any(pred_list[i] == 1 for i in MEDIUM_RISK_LABEL_INDICES)
        
        # 计算风险分数
        if high_risk_detected:
            # 如果有高风险标签，计算加权分数
            high_risk_count = sum(pred_list[i] for i in HIGH_RISK_LABEL_INDICES)
            # 归一化到 [0.7, 1.0]
            risk_score = 0.7 + (high_risk_count / len(HIGH_RISK_LABEL_INDICES)) * 0.3
        elif medium_risk_detected:
            # 中等风险：0.5 - 0.7
            medium_risk_count = sum(pred_list[i] for i in MEDIUM_RISK_LABEL_INDICES)
            risk_score = 0.5 + (medium_risk_count / len(MEDIUM_RISK_LABEL_INDICES)) * 0.2
        else:
            # 低风险：0.0 - 0.5
            risk_score = 0.0
        
        # 确保在 [0, 1] 范围内
        return min(max(risk_score, 0.0), 1.0)
```

**风险分数范围：**
- **高风险**：0.7 - 1.0（检测到自杀/自伤相关标签）
- **中等风险**：0.5 - 0.7（检测到攻击行为标签）
- **低风险**：0.0 - 0.5（未检测到风险标签）

**阈值配置：**

```28:32:src_new/perception/psyguard_service.py
# 阈值配置（根据设计文档）
SUICIDE_INTENT_THRESHOLD = 0.80  # 触发问卷
HIGH_RISK_DIRECT_THRESHOLD = 0.95  # 直接 High Risk
MEDIUM_RISK_THRESHOLD = 0.70  # Medium Risk
LOW_RISK_CLEAR_THRESHOLD = 0.40  # 低风险稳定阈值
```

### 1.2 问卷评估评分

**PHQ-9（抑郁症筛查）：**
- **总分范围**：0-27
- **评分规则**：
  - 0-9：低风险
  - 10-14：中等风险
  - 15+：高风险
- **特殊规则**：Q9（自杀意念）≥ 1 → 直接高风险

**GAD-7（焦虑症筛查）：**
- **总分范围**：0-21
- **评分规则**：
  - 0-9：低风险
  - 10-14：中等风险
  - 15+：高风险

**问卷映射代码：**

```23:44:src_new/perception/questionnaire_mapper.py
    @staticmethod
    def map_phq9(phq9_score: float, phq9_q9_score: Optional[int] = None) -> Route:
        """
        Map PHQ-9 score to route.
        
        Args:
            phq9_score: Total PHQ-9 score
            phq9_q9_score: Score for question 9 (suicidal ideation)
            
        Returns:
            Route: "low", "medium", or "high"
        """
        # Special rule: Q9 (suicidal ideation) >= 1 → High
        if phq9_q9_score is not None and phq9_q9_score >= 1:
            return "high"
        
        # Standard mapping
        if phq9_score <= 9:
            return "low"
        elif phq9_score <= 14:
            return "medium"
        else:
            return "high"
```

### 1.3 综合风险评分

**优先级规则：**
1. **Chat Content 优先级最高**：如果 PsyGUARD 检测到高风险，直接覆盖问卷评分
2. **问卷评分**：如果 chat content 未检测到风险，使用问卷评分

**最终路由决策：**

```80:117:src_new/perception/questionnaire_mapper.py
    @staticmethod
    def final_route_decision(
        phq9_score: float,
        gad7_score: float,
        phq9_q9_score: Optional[int],
        chat_risk_score: Optional[float] = None
    ) -> Route:
        """
        Make final route decision considering both questionnaire and chat content.
        
        Priority: Chat content risk > Questionnaire score
        
        Args:
            phq9_score: Total PHQ-9 score
            gad7_score: Total GAD-7 score
            phq9_q9_score: PHQ-9 question 9 score (suicidal ideation)
            chat_risk_score: PsyGUARD risk score from chat content (optional)
            
        Returns:
            Final route decision
        """
        from src_new.perception.psyguard_service import (
            MEDIUM_RISK_THRESHOLD,
            HIGH_RISK_DIRECT_THRESHOLD
        )
        
        # Chat content priority (if provided)
        if chat_risk_score is not None:
            if chat_risk_score >= HIGH_RISK_DIRECT_THRESHOLD:
                return "high"
            elif chat_risk_score >= MEDIUM_RISK_THRESHOLD:
                return "medium"
        
        # Map questionnaires
        phq9_route = QuestionnaireMapper.map_phq9(phq9_score, phq9_q9_score)
        gad7_route = QuestionnaireMapper.map_gad7(gad7_score)
        
        # Combine (take higher level)
        return QuestionnaireMapper.combine_routes(phq9_route, gad7_route)
```

**示例：**

| 场景 | PHQ-9 | GAD-7 | Chat Risk | 最终路由 | 原因 |
|------|-------|-------|-----------|---------|------|
| 1 | 12 | 8 | 0.96 | `high` | Chat risk 0.96 ≥ 0.95（直接高风险） |
| 2 | 12 | 8 | 0.75 | `medium` | Chat risk 0.75 ≥ 0.70（中等风险） |
| 3 | 12 | 8 | 0.50 | `medium` | 问卷评分：PHQ-9=12 → medium |
| 4 | 6 | 5 | 0.30 | `low` | 问卷评分：PHQ-9=6, GAD-7=5 → low |
| 5 | 15 | 10 | 0.60 | `high` | 问卷评分：PHQ-9=15 → high（优先级高于 chat risk） |
| 6 | 8 | 12 | None | `medium` | 问卷评分：GAD-7=12 → medium |

---

## 2. 如何将风险评分映射到刚性评分（Rigid Score）？

**刚性评分定义：**
- **范围**：0.0 - 1.0
- **含义**：
  - 0.0：完全灵活（自由对话）
  - 1.0：完全刚性（固定脚本）
- **用途**：控制聊天机器人的对话灵活性和温度参数

### 2.1 映射规则

**路由到刚性评分的映射：**

```144:168:src_new/control/risk_router.py
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

### 2.2 映射表

| 路由 | 问卷分数 | 刚性评分 | 说明 |
|------|---------|---------|------|
| **High** | 任意 | **1.0** | 完全刚性，使用固定脚本 |
| **Medium** | ≥ 15 | **0.75** | 高刚性，严格控制 |
| **Medium** | 10-14 | **0.6** | 中等刚性，半结构化 |
| **Medium** | < 10 | **0.5** | 中等刚性，半结构化 |
| **Low** | ≥ 5 | **0.3** | 低刚性，较灵活 |
| **Low** | < 5 | **0.15** | 极低刚性，非常灵活 |

### 2.3 映射逻辑说明

**High Risk Route → Rigid Score 1.0：**
- **原因**：高风险场景必须使用固定脚本，确保安全性和一致性
- **行为**：完全禁用 LLM，使用预定义的危机干预脚本

**Medium Risk Route → Rigid Score 0.5-0.75：**
- **原因**：中等风险需要半结构化对话，平衡灵活性和安全性
- **行为**：使用状态机控制对话流程，但允许 LLM 生成个性化响应
- **分级**：根据问卷分数进一步细分（0.5/0.6/0.75）

**Low Risk Route → Rigid Score 0.0-0.4：**
- **原因**：低风险场景允许自由对话，提供最大灵活性
- **行为**：使用灵活的 LLM，根据上下文生成自然响应
- **分级**：根据问卷分数进一步细分（0.15/0.3）

### 2.4 映射示例

**示例 1：高风险场景**
```python
# 输入
route = "high"
phq9_score = 18
gad7_score = 12

# 映射
rigid_score = 1.0  # High risk → 1.0
```

**示例 2：中等风险场景（高分数）**
```python
# 输入
route = "medium"
phq9_score = 16  # ≥ 15
gad7_score = 10

# 映射
rigid_score = 0.75  # Medium risk, max_score=16 ≥ 15 → 0.75
```

**示例 3：中等风险场景（中等分数）**
```python
# 输入
route = "medium"
phq9_score = 12  # 10-14
gad7_score = 8

# 映射
rigid_score = 0.6  # Medium risk, max_score=12, 10≤12<15 → 0.6
```

**示例 4：低风险场景（有症状）**
```python
# 输入
route = "low"
phq9_score = 6  # ≥ 5
gad7_score = 4

# 映射
rigid_score = 0.3  # Low risk, max_score=6 ≥ 5 → 0.3
```

**示例 5：低风险场景（无症状）**
```python
# 输入
route = "low"
phq9_score = 3  # < 5
gad7_score = 2

# 映射
rigid_score = 0.15  # Low risk, max_score=3 < 5 → 0.15
```

---

## 3. 如何使用刚性评分控制聊天机器人的灵活性？

**核心机制：通过调整 LLM Temperature 参数**

### 3.1 Temperature 调整公式

**公式：**
```python
adjusted_temp = max(0.1, base_temp - 0.8 * rigid_score)
```

**参数说明：**
- `base_temp`：基础温度（不同 Agent 不同）
  - Low Risk Agent: 0.9
  - Medium Risk Agent: 0.6
  - High Risk Agent: 0.0（不使用 LLM）
- `rigid_score`：刚性评分（0.0 - 1.0）
- `0.8`：调整系数（控制刚性评分对温度的影响程度）
- `0.1`：最小温度（确保 LLM 不会完全确定性）

### 3.2 温度调整示例

**Low Risk Agent（base_temp = 0.9）：**

| Rigid Score | 计算 | Adjusted Temp | 灵活性 |
|------------|------|---------------|--------|
| 0.0 | max(0.1, 0.9 - 0.8 × 0.0) = 0.9 | **0.9** | 极高灵活性 |
| 0.15 | max(0.1, 0.9 - 0.8 × 0.15) = 0.78 | **0.78** | 高灵活性 |
| 0.3 | max(0.1, 0.9 - 0.8 × 0.3) = 0.66 | **0.66** | 中等灵活性 |
| 0.5 | max(0.1, 0.9 - 0.8 × 0.5) = 0.5 | **0.5** | 较低灵活性 |
| 0.75 | max(0.1, 0.9 - 0.8 × 0.75) = 0.3 | **0.3** | 低灵活性 |
| 1.0 | max(0.1, 0.9 - 0.8 × 1.0) = 0.1 | **0.1** | 极低灵活性 |

**Medium Risk Agent（base_temp = 0.6）：**

| Rigid Score | 计算 | Adjusted Temp | 灵活性 |
|------------|------|---------------|--------|
| 0.0 | max(0.1, 0.6 - 0.8 × 0.0) = 0.6 | **0.6** | 中等灵活性 |
| 0.5 | max(0.1, 0.6 - 0.8 × 0.5) = 0.2 | **0.2** | 低灵活性 |
| 0.6 | max(0.1, 0.6 - 0.8 × 0.6) = 0.12 | **0.12** | 极低灵活性 |
| 0.75 | max(0.1, 0.6 - 0.8 × 0.75) = 0.1 | **0.1** | 最小灵活性 |

**High Risk Agent（base_temp = 0.0，不使用 LLM）：**

| Rigid Score | 计算 | Adjusted Temp | 灵活性 |
|------------|------|---------------|--------|
| 1.0 | N/A（固定脚本） | **0.0** | 无灵活性（固定脚本） |

### 3.3 代码实现

**Low Risk Agent：**

```65:66:src_new/conversation/agents/low_risk_agent.py
            # Adjust temperature based on rigidity
            adjusted_temp = max(0.1, self.temperature - 0.8 * rigid_score)
```

**Medium Risk Agent：**

```126:127:src_new/conversation/agents/medium_risk_agent.py
            # Adjust temperature based on rigidity
            adjusted_temp = max(0.1, self.temperature - 0.8 * rigid_score)
```

**High Risk Agent：**

```43:75:src_new/conversation/agents/high_risk_agent.py
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationTurn]] = None,
        rigid_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate fixed safety response for high-risk conversation.
        
        Args:
            user_message: User's message (not used, but kept for API consistency)
            conversation_history: Previous conversation turns (not used)
            rigid_score: Rigidity score (always 1.0 for high risk)
            
        Returns:
            Dict with fixed response and metadata
        """
        logger.warning(
            f"HighRiskAgent: Using fixed safety script (rigid_score={rigid_score})"
        )
        
        # HIGH RISK: Always use fixed script, NO free-form LLM response
        return {
            "agent": "high_risk",
            "response": FIXED_SAFETY_SCRIPT,
            "temperature": 0.0,  # Not used (fixed script)
            "structured": True,
            "safety_banner": SAFETY_BANNER,
            "safety_priority": True,
            "fixed_script": True,
            "crisis_hotline": "988",
            "urgent_meeting_suggested": True
        }
```

### 3.4 Temperature 对 LLM 行为的影响

#### 3.4.1 Temperature 是什么？

**简单理解：Temperature 就像"创意程度"的开关**

想象 LLM 在选择下一个词时，有一个"概率分布"：
- **低 Temperature（0.0-0.3）**：LLM 更"保守"，倾向于选择概率最高的词
- **高 Temperature（0.8-1.0）**：LLM 更"大胆"，可能选择概率较低但更创新的词

**形象比喻：**
- **Temperature = 0.1**：像"严格遵循规则"的助手，总是选择最安全、最标准的回答
- **Temperature = 0.9**：像"富有创意"的朋友，可能给出意想不到但更有趣的回答

#### 3.4.2 Temperature 如何控制灵活程度？

**工作原理：**

1. **LLM 生成过程：**
   ```
   用户消息 → LLM 处理 → 生成多个候选词（每个词有概率）
   → 根据 Temperature 选择 → 输出响应
   ```

2. **Temperature 的作用：**
   - **低 Temperature**：放大高概率词的选择，缩小低概率词的选择
     - 结果：输出更确定、更一致、更可预测
   - **高 Temperature**：让所有词的选择概率更平均
     - 结果：输出更多样、更创新、更自然

**数学简化理解：**
- Temperature 就像对概率分布的"平滑"操作
- 低 Temperature = 让概率分布更"尖锐"（集中在高概率词）
- 高 Temperature = 让概率分布更"平坦"（所有词更平均）

#### 3.4.3 实际例子

**场景：用户说"我很难过"**

**低 Temperature (0.1)：**
```
LLM 候选响应：
1. "我理解你的感受。要不要聊聊发生了什么？" (概率: 0.85)
2. "我理解你的感受。有什么我可以帮助你的吗？" (概率: 0.10)
3. "我理解你的感受。要不要试试深呼吸？" (概率: 0.05)

选择结果：总是选择 #1（最安全的回答）
```

**高 Temperature (0.9)：**
```
LLM 候选响应：
1. "我理解你的感受。要不要聊聊发生了什么？" (概率: 0.35)
2. "我理解你的感受。有什么我可以帮助你的吗？" (概率: 0.30)
3. "我理解你的感受。要不要试试深呼吸？" (概率: 0.25)
4. "我理解你的感受。这听起来很困难。你愿意分享更多吗？" (概率: 0.10)

选择结果：可能选择 #1, #2, #3, 或 #4（更多样化）
```

#### 3.4.4 Temperature 范围说明

**Temperature 参数说明：**
- **Temperature = 0.0-0.3**：低温度，高确定性
  - 生成更确定、更一致的响应
  - 更适合结构化对话（Medium/High Risk）
  - 响应更可预测，但可能缺乏个性化
- **Temperature = 0.4-0.7**：中等温度
  - 平衡确定性和创造性
  - 适合半结构化对话（Medium Risk）
  - 响应既有结构又有个性
- **Temperature = 0.8-1.0**：高温度，高随机性
  - 生成更创造性、更多样化的响应
  - 更适合自由对话（Low Risk）
  - 响应更自然，但可能不够一致

**实际效果对比：**

| Rigid Score | Adjusted Temp | 对话风格 | 示例响应特征 |
|------------|---------------|---------|-------------|
| 0.0 | 0.9 | 自由对话 | "我理解你的感受。要不要试试深呼吸？或者我们可以聊聊其他事情？" |
| 0.3 | 0.66 | 灵活建议 | "我理解你的感受。我建议你试试深呼吸练习，这对缓解焦虑很有帮助。" |
| 0.6 | 0.12 | 结构化建议 | "我理解你的感受。根据你的情况，我建议你加入 peer group。这个小组有 moderator，可以提供支持。" |
| 1.0 | 0.0（固定脚本） | 固定脚本 | "I'm here to support you, and I want to make sure you're safe. Right now, the most important thing is your safety. If you're having thoughts of hurting yourself or ending your life, please reach out for immediate help: Call or text 988..." |

#### 3.4.5 为什么 Temperature 能控制灵活性？

**核心原理：**

1. **灵活性的定义：**
   - 灵活性 = 响应多样化程度
   - 高灵活性 = 每次对话可能给出不同的回答
   - 低灵活性 = 每次对话给出相似的回答

2. **Temperature 的影响：**
   - **高 Temperature** → 选择更多样 → 灵活性高
   - **低 Temperature** → 选择更确定 → 灵活性低

3. **实际应用：**
   - **Low Risk（灵活对话）**：需要高 Temperature，让对话更自然、更个性化
   - **Medium Risk（半结构化）**：需要中等 Temperature，平衡结构和灵活性
   - **High Risk（固定脚本）**：不需要 LLM，直接使用固定脚本（Temperature = 0.0）

### 3.5 完整控制流程

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: 计算风险评分                                      │
├─────────────────────────────────────────────────────────┤
│ • PsyGUARD 风险评分: 0.75 (中等风险)                     │
│ • PHQ-9 评分: 12                                         │
│ • GAD-7 评分: 8                                          │
│ • 最终路由: "medium" (chat risk 优先)                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: 映射到刚性评分                                    │
├─────────────────────────────────────────────────────────┤
│ • Route: "medium"                                        │
│ • Max Score: max(12, 8) = 12                            │
│ • Rigid Score: 0.6 (10 ≤ 12 < 15)                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: 调整 Temperature                                 │
├─────────────────────────────────────────────────────────┤
│ • Agent: MediumRiskAgent                                │
│ • Base Temp: 0.6                                         │
│ • Adjusted Temp: max(0.1, 0.6 - 0.8 × 0.6) = 0.12      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: 生成响应                                          │
├─────────────────────────────────────────────────────────┤
│ • 使用状态机控制对话流程                                  │
│ • 使用 Temperature=0.12 生成 LLM 响应                    │
│ • 响应更结构化、更一致，但仍有灵活性                      │
└─────────────────────────────────────────────────────────┘
```

### 3.6 不同场景的灵活性控制

**场景 1：低风险用户（无症状）**
- **风险评分**：PHQ-9=3, GAD-7=2, Chat Risk=0.2
- **路由**：Low
- **刚性评分**：0.15
- **Temperature**：0.78（高灵活性）
- **行为**：自由对话，自然响应，提供应对技巧建议

**场景 2：低风险用户（有轻微症状）**
- **风险评分**：PHQ-9=7, GAD-7=5, Chat Risk=0.3
- **路由**：Low
- **刚性评分**：0.3
- **Temperature**：0.66（中等灵活性）
- **行为**：灵活对话，但更倾向于提供应对技巧

**场景 3：中等风险用户（中等症状）**
- **风险评分**：PHQ-9=12, GAD-7=8, Chat Risk=0.5
- **路由**：Medium
- **刚性评分**：0.6
- **Temperature**：0.12（低灵活性）
- **行为**：半结构化对话，使用状态机，建议加入 peer group

**场景 4：中等风险用户（高症状）**
- **风险评分**：PHQ-9=16, GAD-7=12, Chat Risk=0.6
- **路由**：Medium
- **刚性评分**：0.75
- **Temperature**：0.1（极低灵活性）
- **行为**：严格控制对话，强烈建议加入 peer group

**场景 5：高风险用户（有自杀意念）**
- **风险评分**：PHQ-9 Q9=2, Chat Risk=0.96
- **路由**：High
- **刚性评分**：1.0
- **Temperature**：N/A（固定脚本）
- **行为**：使用固定危机干预脚本，提供 988 热线

---

## 总结

### 1. 风险评分定义
- **PsyGUARD 评分**：基于多标签分类模型，检测 11 种风险标签，返回 0.0-1.0 风险分数
- **问卷评分**：PHQ-9 和 GAD-7 的总分和单项分
- **综合评分**：Chat content 优先级高于问卷评分

### 2. 刚性评分映射
- **High Risk** → 1.0（完全刚性）
- **Medium Risk** → 0.5-0.75（根据问卷分数细分）
- **Low Risk** → 0.0-0.4（根据问卷分数细分）

### 3. 灵活性控制
- **公式**：`adjusted_temp = max(0.1, base_temp - 0.8 * rigid_score)`
- **High Risk**：不使用 LLM，使用固定脚本（rigid_score=1.0）
- **Medium Risk**：使用状态机 + 低温度 LLM（rigid_score=0.5-0.75）
- **Low Risk**：使用自由对话 + 高温度 LLM（rigid_score=0.0-0.4）

**核心思想：**
- **刚性评分越高** → **Temperature 越低** → **聊天机器人越刚性** → **响应越结构化、越一致**
- **刚性评分越低** → **Temperature 越高** → **聊天机器人越灵活** → **响应越自然、越个性化**

