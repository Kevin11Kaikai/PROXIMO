# psychiatric_scales.py 三维度阶段分析

## 📋 文件概览

这个文件实现了**心理评估量表处理系统**，包含三个核心组件，负责从原始回答到临床解释的完整流程。

```
原始回答 (Raw Responses)
    ↓
【Stage 1: 校验与标准化】
    ↓
标准分数 (Validated Scores)
    ↓
【Stage 2: 分数计算与严重度分级】
    ↓
评估结果对象 (Result Object)
    ↓
【Stage 3: 临床解释与风险评估】
    ↓
临床解释报告 (Clinical Interpretation)
```

---

## 🎯 核心组件架构

```
┌─────────────────────────────────────────────────────┐
│  1. PsychiatricScaleValidator (校验器)              │
│     - 输入: 原始文本回答                             │
│     - 输出: 标准化分数 (0-3 或 0-4)                 │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  2. AssessmentOrchestrator (编排器)                 │
│     - 输入: Persona + 回答列表                       │
│     - 输出: 完整评估结果对象 (PHQ9Result/GAD7Result)│
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  3. ClinicalInterpreter (临床解释器)                │
│     - 输入: 评估结果对象                             │
│     - 输出: 临床解释字典 (推荐、风险因素等)          │
└─────────────────────────────────────────────────────┘
```

---

## 📥 阶段 1: 输入验证与标准化 (PsychiatricScaleValidator)

### **输入维度 (Input)**

#### 1.1 原始回答输入
```python
# 输入示例
responses = [
    "0",                           # 数字形式
    "not at all",                  # 英文文本
    "several days",                # 自然语言
    "2",                           # 数字字符串
    "More than half the days",     # 混合大小写
    # ... 更多回答
]
```

**输入特点**:
- ✅ **格式多样性**: 数字、文本、混合格式
- ✅ **语言变体**: "never" / "not at all" / "0" 都表示相同含义
- ✅ **大小写不敏感**: "NEVER" 和 "never" 等价
- ⚠️ **需要鲁棒性处理**: 容忍拼写错误、同义词、格式差异

#### 1.2 量表类型参数
```python
scale_type: str  # "phq9" | "gad7" | "pss10"
question_index: int  # 题目序号 (0-indexed)
```

---

### **过程维度 (Process)**

#### Stage 1.1: 文本清理与预处理
```python
response = response.strip().lower()  # 去除空格，转为小写
```

**处理逻辑**:
1. **去除前后空格**: `"  never  "` → `"never"`
2. **统一大小写**: `"NEVER"` → `"never"`
3. **标准化输入**: 为后续匹配做准备

#### Stage 1.2: 数字提取 (优先策略)
```python
# PHQ-9/GAD-7: 提取 0-3
numbers = re.findall(r'\b[0-3]\b', response)

# PSS-10: 提取 0-4
numbers = re.findall(r'\b[0-4]\b', response)
```

**策略**:
- ✅ **正则表达式匹配**: 使用 `\b` 确保完整单词匹配
- ✅ **范围验证**: 确保数字在有效范围内
- ✅ **优先级**: 数字优先于文本解析

**示例**:
```python
"我选择 2" → 提取到 "2" → 返回 (True, 2)
"答案是3分" → 提取到 "3" → 返回 (True, 3)
```

#### Stage 1.3: 文本语义映射 (备选策略)
```python
# PHQ-9/GAD-7 映射表
score_map = {
    "not at all": 0, "never": 0, "0": 0,
    "several days": 1, "sometimes": 1, "1": 1,
    "more than half the days": 2, "often": 2, "2": 2,
    "nearly every day": 3, "always": 3, "3": 3
}

# PSS-10 映射表 (5级量表)
score_map = {
    "never": 0, "0": 0,
    "almost never": 1, "1": 1,
    "sometimes": 2, "2": 2,
    "fairly often": 3, "3": 3,
    "very often": 4, "4": 4
}
```

**映射规则**:
- ✅ **同义词支持**: "never" = "not at all" = "0"
- ✅ **部分匹配**: `"sometimes I feel..."` → 匹配到 "sometimes" → 1分
- ✅ **多语言支持**: 支持英文变体

**处理流程**:
```python
for text, score in score_map.items():
    if text in response:  # 子串匹配
        return True, score
```

#### Stage 1.4: 异常处理
```python
except Exception as e:
    logger.error(f"Error validating response: {e}")
    return False, None  # 校验失败
```

**容错机制**:
- ✅ **保守策略**: 校验失败返回 `(False, None)`
- ✅ **日志记录**: 记录错误信息便于调试
- ✅ **不中断流程**: 错误不导致程序崩溃

---

### **输出维度 (Output)**

#### 1.1 校验结果
```python
Tuple[bool, Optional[int]]
```

**输出格式**:
- ✅ **成功**: `(True, 0)` / `(True, 1)` / `(True, 2)` / `(True, 3)`
- ❌ **失败**: `(False, None)`

**输出特点**:
- ✅ **类型安全**: 使用 Tuple 明确返回类型
- ✅ **可扩展**: Optional[int] 允许 None 值
- ✅ **信息完整**: 既告知是否成功，又返回分数

---

## 📊 阶段 2: 评估编排与结果生成 (AssessmentOrchestrator)

### **输入维度 (Input)**

#### 2.1 Persona 对象
```python
persona: Persona
```

**Persona 结构**:
```python
Persona(
    baseline=PersonaBaseline(
        name="Alfred",
        baseline_phq9=2.0,
        # ... 其他基线信息
    ),
    state=PersonaState(
        persona_id="persona_alfred",
        simulation_day=7,
        last_assessment_day=0,
        # ... 当前状态
    )
)
```

**输入用途**:
- 📍 **身份标识**: `persona.state.persona_id` → 生成 assessment_id
- 📅 **时间信息**: `persona.state.simulation_day` → 记录评估日期
- 👤 **个人信息**: `persona.baseline.name` → 日志记录

#### 2.2 回答列表
```python
responses: List[str]  # PHQ-9: 9个, GAD-7: 7个, PSS-10: 10个
```

**示例**:
```python
phq9_responses = [
    "0", "1", "2", "1", "0",  # 前5题
    "1", "2", "1", "2"        # 后4题 (第9题是自杀意念)
]
```

---

### **过程维度 (Process)**

#### Stage 2.1: 批量校验与分数收集
```python
validated_scores = []
for i, response in enumerate(responses):
    is_valid, score = self.validator.validate_phq9_response(response, i)
    if is_valid and score is not None:
        validated_scores.append(score)
    else:
        logger.warning(f"Invalid response {i+1}: {response}")
        validated_scores.append(0)  # 保守回退策略
```

**处理流程**:
1. **遍历所有回答**: 逐个校验每个回答
2. **收集有效分数**: 成功校验的分数加入列表
3. **容错处理**: 无效回答使用保守值 (0分)
4. **日志记录**: 记录所有无效回答便于审查

**容错策略对比**:
- **PHQ-9/GAD-7**: 无效回答 → 0分 (最保守)
- **PSS-10**: 无效回答 → 2分 (中间值，因为PSS-10是5级量表)

#### Stage 2.2: 回答数量验证
```python
if len(validated_scores) != 9:  # PHQ-9 要求9个回答
    logger.error(f"PHQ-9 requires 9 responses, got {len(validated_scores)}")
    return None  # 返回 None 表示评估失败
```

**验证规则**:
- ✅ **PHQ-9**: 必须 9 个回答
- ✅ **GAD-7**: 必须 7 个回答
- ✅ **PSS-10**: 必须 10 个回答
- ❌ **不完整**: 返回 `None` 终止流程

#### Stage 2.3: 总分计算
```python
# PHQ-9/GAD-7: 简单累加
total_score = sum(validated_scores)

# PSS-10: 累加 + 反向计分
total_score = self.validator.calculate_pss10_score(validated_scores)
```

**PSS-10 反向计分逻辑**:
```python
# 题目 4, 5, 7, 8 (索引 3, 4, 6, 7) 需要反向计分
# 原分: 0 → 反向: 4
# 原分: 1 → 反向: 3
# 原分: 2 → 反向: 2
# 原分: 3 → 反向: 1
# 原分: 4 → 反向: 0

if i in [3, 4, 6, 7]:  # 反向计分项
    total_score += (4 - score)
else:
    total_score += score
```

**为什么需要反向计分?**
- PSS-10 的某些题目是**正向表述**（如"我能掌控我的生活"）
- 高分应该表示**低压力**，而不是高压力
- 反向计分确保所有题目方向一致：**高分 = 高压力**

#### Stage 2.4: 严重度分级
```python
severity_level = PHQ9Result.calculate_severity(total_score)
```

**分级阈值** (以 PHQ-9 为例):
```python
MINIMAL:  0-4   (< 5)
MILD:     5-9   (< 10)
MODERATE: 10-14 (< 15)
SEVERE:   15-27 (≥ 15)
```

**分级逻辑**:
```python
if total_score < 5:
    return SeverityLevel.MINIMAL
elif total_score < 10:
    return SeverityLevel.MILD
elif total_score < 15:
    return SeverityLevel.MODERATE
else:
    return SeverityLevel.SEVERE
```

#### Stage 2.5: 特殊字段提取
```python
# PHQ-9 特殊处理: 提取第 9 题 (自杀意念)
suicidal_ideation_score = validated_scores[8]  # 索引 8 = 第 9 题
```

**为什么特殊处理?**
- ✅ **临床重要性**: 自杀意念是**独立风险因子**
- ✅ **预警机制**: 即使总分不高，Item 9 ≥ 2 也需要立即关注
- ✅ **法规要求**: 医疗系统必须单独记录和评估

#### Stage 2.6: 结果对象构建
```python
result = PHQ9Result(
    assessment_id=f"{persona_id}_phq9_{simulation_day}",
    persona_id=persona.state.persona_id,
    assessment_type="phq9",
    simulation_day=persona.state.simulation_day,
    raw_responses=responses,           # 原始输入
    parsed_scores=validated_scores,    # 标准化分数
    total_score=total_score,           # 总分
    severity_level=severity_level,     # 严重度等级
    suicidal_ideation_score=validated_scores[8],  # 特殊字段
    depression_severity=severity_level
)
```

**对象特点**:
- ✅ **完整信息**: 包含原始输入和所有计算结果
- ✅ **可追溯**: assessment_id 唯一标识每次评估
- ✅ **结构化**: 使用 Pydantic 模型确保类型安全

#### Stage 2.7: 临床解释附加
```python
result.clinical_interpretation = self.interpreter.interpret_phq9_result(result)
```

**解释内容** (见 Stage 3)

---

### **输出维度 (Output)**

#### 2.1 评估结果对象
```python
PHQ9Result | GAD7Result | PSS10Result
```

**对象结构** (以 PHQ9Result 为例):
```python
PHQ9Result(
    assessment_id="persona_alfred_phq9_7",
    persona_id="persona_alfred",
    assessment_type="phq9",
    simulation_day=7,
    raw_responses=["0", "1", "2", ...],
    parsed_scores=[0, 1, 2, ...],
    total_score=12,
    severity_level=SeverityLevel.MODERATE,
    suicidal_ideation_score=1,
    depression_severity=SeverityLevel.MODERATE,
    clinical_interpretation={...}  # 见 Stage 3
)
```

**输出特点**:
- ✅ **完整性**: 包含评估的所有信息
- ✅ **可序列化**: Pydantic 模型支持 JSON 导出
- ✅ **可扩展**: 可以添加新字段不影响现有代码

---

## 🔍 阶段 3: 临床解释与风险评估 (ClinicalInterpreter)

### **输入维度 (Input)**

#### 3.1 评估结果对象
```python
result: PHQ9Result | GAD7Result | PSS10Result
```

**关键输入字段**:
```python
result.total_score          # 总分
result.severity_level       # 严重度等级
result.suicidal_ideation_score  # (仅 PHQ-9) 自杀意念分数
```

---

### **过程维度 (Process)**

#### Stage 3.1: 基础解释生成
```python
interpretation = {
    "severity_level": result.severity_level.value,  # "minimal" | "mild" | "moderate" | "severe"
    "total_score": result.total_score,
    "clinical_meaning": "",          # 临床含义描述
    "recommendations": [],           # 推荐行动
    "risk_factors": [],              # 风险因素列表
    "suicidal_risk": "low"          # (仅 PHQ-9) 自杀风险
}
```

#### Stage 3.2: 严重度解释映射

**PHQ-9 映射示例**:
```python
if severity_level == MINIMAL:
    clinical_meaning = "Minimal depressive symptoms"
    recommendations = ["Continue monitoring", "Maintain current routine"]
    
elif severity_level == MILD:
    clinical_meaning = "Mild depressive symptoms"
    recommendations = ["Consider lifestyle changes", "Monitor for worsening"]
    
elif severity_level == MODERATE:
    clinical_meaning = "Moderate depressive symptoms"
    recommendations = ["Consider professional evaluation", "Implement coping strategies"]
    
else:  # SEVERE
    clinical_meaning = "Severe depressive symptoms"
    recommendations = [
        "Immediate professional evaluation recommended",
        "Safety assessment needed"
    ]
```

**解释特点**:
- ✅ **渐进式建议**: 严重度越高，建议越紧急
- ✅ **临床标准**: 遵循 DSM-5 和临床实践指南
- ✅ **可操作**: 建议具体且可执行

#### Stage 3.3: 关键风险检测 (PHQ-9 特殊处理)

**自杀意念检查**:
```python
if result.suicidal_ideation_score >= 2:
    interpretation["suicidal_risk"] = "high"
    interpretation["risk_factors"].append("Suicidal ideation present")
    interpretation["recommendations"].insert(0, "Immediate safety assessment required")
```

**处理逻辑**:
1. **阈值判断**: Item 9 ≥ 2 (2分或3分)
2. **风险升级**: 将自杀风险标记为 "high"
3. **优先建议**: 使用 `insert(0, ...)` 将安全评估放在首位
4. **风险因素**: 添加到风险因素列表

**为什么 Item 9 ≥ 2?**
- **0分**: "完全没有" 自杀想法
- **1分**: "几天" 有自杀想法 → 需要关注
- **2分**: "超过一半天" 有自杀想法 → **高风险**
- **3分**: "几乎每天" 有自杀想法 → **极高风险**

#### Stage 3.4: 附加风险因素检测

**高严重度检查**:
```python
# PHQ-9/GAD-7
if result.total_score >= 20:
    interpretation["risk_factors"].append("High depression/anxiety severity")

# PSS-10
if result.total_score >= 25:
    interpretation["risk_factors"].append("High stress levels")
```

**风险因素用途**:
- ✅ **预警系统**: 帮助识别需要紧急干预的案例
- ✅ **决策支持**: 辅助临床医生制定治疗计划
- ✅ **数据追踪**: 用于统计分析和趋势监控

---

### **输出维度 (Output)**

#### 3.1 临床解释字典
```python
Dict[str, Any]
```

**完整输出示例** (PHQ-9, 总分 18, Item 9 = 2):
```python
{
    "severity_level": "moderate",
    "total_score": 18,
    "clinical_meaning": "Moderate depressive symptoms",
    "recommendations": [
        "Immediate safety assessment required",  # 优先 (自杀意念触发)
        "Consider professional evaluation",
        "Implement coping strategies"
    ],
    "risk_factors": [
        "Suicidal ideation present",      # Item 9 ≥ 2
        # 注意: 总分 18 < 20, 所以没有 "High depression severity"
    ],
    "suicidal_risk": "high"  # 关键风险标志
}
```

**输出特点**:
- ✅ **结构化**: 字典格式便于 JSON 序列化
- ✅ **完整**: 包含所有临床相关信息
- ✅ **可扩展**: 可以添加新字段不影响现有代码

---

## 🔄 完整数据流示例

### **端到端流程** (PHQ-9 评估)

```python
# ========== 输入 ==========
persona = Persona(...)
responses = [
    "0",                    # 第1题
    "several days",         # 第2题
    "2",                    # 第3题
    "not at all",           # 第4题
    "0",                    # 第5题
    "sometimes",            # 第6题
    "more than half the days",  # 第7题
    "1",                    # 第8题
    "2"                     # 第9题 (自杀意念) ⚠️
]

# ========== Stage 1: 校验 ==========
validated_scores = []
# 循环校验...
validated_scores = [0, 1, 2, 0, 0, 1, 2, 1, 2]

# ========== Stage 2: 计算 ==========
total_score = sum([0, 1, 2, 0, 0, 1, 2, 1, 2]) = 9
severity_level = MILD  # 9 < 10
suicidal_ideation_score = 2  # validated_scores[8]

# ========== Stage 2: 结果对象 ==========
result = PHQ9Result(
    total_score=9,
    severity_level=SeverityLevel.MILD,
    suicidal_ideation_score=2,  # ⚠️ 关键
    ...
)

# ========== Stage 3: 临床解释 ==========
clinical_interpretation = {
    "severity_level": "mild",
    "total_score": 9,
    "clinical_meaning": "Mild depressive symptoms",
    "recommendations": [
        "Immediate safety assessment required",  # ⚠️ 优先 (Item 9 = 2)
        "Consider lifestyle changes",
        "Monitor for worsening"
    ],
    "risk_factors": ["Suicidal ideation present"],  # ⚠️
    "suicidal_risk": "high"  # ⚠️
}

# ========== 输出 ==========
result.clinical_interpretation = clinical_interpretation
return result  # 完整的评估结果
```

**关键观察**:
- ⚠️ **即使总分只有 9 分 (MILD)**，但因为 Item 9 = 2，系统会触发**高风险预警**
- ✅ **安全优先**: 自杀意念检查优先于总分严重度
- ✅ **完整记录**: 所有原始数据都被保留用于审计

---

## 📊 三个阶段的总结对比

| 维度 | Stage 1: 校验 | Stage 2: 编排 | Stage 3: 解释 |
|------|--------------|--------------|--------------|
| **输入** | 原始文本回答 | Persona + 回答列表 | 评估结果对象 |
| **核心任务** | 文本 → 分数 | 分数 → 结果对象 | 结果 → 临床建议 |
| **输出** | `(bool, int)` | `Result Object` | `Dict[str, Any]` |
| **容错策略** | 返回 `None` | 保守值 (0分) | 默认建议 |
| **可扩展性** | 支持新语言/格式 | 支持新量表类型 | 支持新风险因子 |
| **性能** | O(1) 单题校验 | O(n) n个回答 | O(1) 常量时间 |

---

## 🎯 设计模式与最佳实践

### 1. **单一职责原则**
- `PsychiatricScaleValidator`: 只负责校验
- `AssessmentOrchestrator`: 只负责编排流程
- `ClinicalInterpreter`: 只负责解释

### 2. **策略模式**
- 三种量表使用相同的接口 (`validate_xxx_response`)
- 可以轻松添加新的量表类型

### 3. **容错设计**
- 多层容错: 校验失败 → 保守值 → 日志记录
- 不因单个错误中断整个流程

### 4. **可追溯性**
- 保留原始输入 (`raw_responses`)
- 唯一标识 (`assessment_id`)
- 完整日志记录

---

这个系统的设计体现了**医疗级软件**的特点：**严格、可追溯、容错、可扩展**。每个阶段都有明确的职责，数据流清晰，便于维护和调试。


