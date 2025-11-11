# Perception Layer 实现总结

**实现日期**：2025-11-07  
**状态**：✅ 已完成

---

## 📋 实现概览

Perception Layer 是五层架构的第一层，负责风险感知和评估。本层已完成以下功能：

1. ✅ **PsyGUARD 服务集成** - 实时逐句风险评分
2. ✅ **问卷触发逻辑** - 智能触发问卷评估
3. ✅ **问卷映射规则** - 将问卷分数映射到风险路由
4. ✅ **完整测试套件** - 单元测试和集成测试

---

## 🎯 核心模块

### 1. PsyGuardService (`src_new/perception/psyguard_service.py`)

**功能**：
- 加载 PsyGUARD-RoBERTa 模型
- 对用户消息进行实时风险评分
- 返回结构化风险信息（分数、标签、触发标志）

**关键特性**：
- 自动设备检测（CUDA/CPU）
- 安全的模型加载（兼容 PyTorch 版本）
- 风险分数计算（基于多标签分类结果）
- 阈值检测（自杀意图、极高风险）

**阈值配置**：
- `SUICIDE_INTENT_THRESHOLD = 0.80` - 触发问卷
- `HIGH_RISK_DIRECT_THRESHOLD = 0.95` - 直接 High Risk
- `MEDIUM_RISK_THRESHOLD = 0.70` - Medium Risk
- `LOW_RISK_CLEAR_THRESHOLD = 0.40` - 低风险稳定阈值

**API**：
```python
service = PsyGuardService()
await service.load()
result = await service.score("I'm thinking about suicide")
# result: {
#     "risk_score": 0.85,
#     "labels": ["主动自杀意图"],
#     "should_trigger_questionnaire": True,
#     "should_direct_high_risk": False
# }
```

### 2. QuestionnaireTrigger (`src_new/perception/questionnaire_trigger.py`)

**功能**：
- 管理问卷触发逻辑
- 支持三种触发方式：轮次计数、自杀意图、极高风险

**触发规则**：
1. **默认触发**：完成 5 轮对话后自动触发
2. **提前触发**：PsyGUARD 检测到自杀意图（>= 0.80）
3. **直接高风险**：PsyGUARD 检测到极高风险（>= 0.95），立即设置 High Risk

**优先级**：极高风险 > 自杀意图 > 轮次计数

**API**：
```python
trigger = QuestionnaireTrigger(turn_threshold=5)
result = trigger.check_trigger(
    turn_count=2,
    psyguard_result={"should_trigger_questionnaire": True}
)
# result.should_trigger = True
# result.reason = "suicide_intent"
```

### 3. QuestionnaireMapper (`src_new/perception/questionnaire_mapper.py`)

**功能**：
- 将问卷分数映射到风险路由（Low/Medium/High）
- 支持 PHQ-9 和 GAD-7
- 处理聊天内容优先级

**映射规则**：

**PHQ-9**：
- 0-9 → Low
- 10-14 → Medium
- 15+ → High
- **特殊规则**：第9题（自杀念头）≥ 1 → 直接 High

**GAD-7**：
- 0-9 → Low
- 10-14 → Medium
- 15+ → High

**综合规则**：
- 取 PHQ-9 和 GAD-7 中较高等级
- **聊天内容优先级**：如果聊天内容风险高，覆盖问卷结果

**API**：
```python
route = QuestionnaireMapper.final_route_decision(
    phq9_score=12,
    gad7_score=10,
    phq9_q9_score=0,
    chat_risk_score=0.85  # 聊天内容优先级更高
)
# route = "high" (因为 chat_risk_score >= 0.70)
```

### 4. QuestionnaireService (`src_new/perception/questionnaire_service.py`)

**功能**：
- 封装现有的问卷评估 API
- 提供统一的接口调用 PHQ-9/GAD-7/PSS-10 评估

**API**：
```python
service = QuestionnaireService()
result = await service.assess("phq9", ["0", "1", "2", ...])
```

---

## 🧪 测试覆盖

### 测试文件

1. **`test_psyguard_service.py`**
   - ✅ 模型加载测试
   - ✅ 风险评分测试
   - ✅ 阈值常量验证
   - ✅ 禁用服务行为测试

2. **`test_questionnaire_trigger.py`**
   - ✅ 轮次计数触发测试
   - ✅ 自杀意图提前触发测试
   - ✅ 极高风险直接触发测试
   - ✅ 触发优先级顺序测试

3. **`test_questionnaire_mapper.py`**
   - ✅ PHQ-9 映射测试（9个测试用例）
   - ✅ GAD-7 映射测试（6个测试用例）
   - ✅ 路由合并测试（7个测试用例）
   - ✅ 聊天内容优先级测试（4个测试用例）
   - ✅ 评估结果映射测试

4. **`test_perception_integration.py`**
   - ✅ 完整工作流程测试
   - ✅ 正常对话流程
   - ✅ 提前触发流程

### 测试结果

**所有测试通过** ✅
- 问卷映射测试：9/9 通过
- 问卷触发测试：所有场景通过
- 集成测试：工作流程正常

---

## 📊 工作流程

### 完整流程示例

```
用户消息: "I'm thinking about suicide"
    ↓
[PsyGUARD 评分]
    risk_score: 0.85
    should_trigger_questionnaire: True
    ↓
[问卷触发检查]
    should_trigger: True
    reason: "suicide_intent"
    ↓
[执行问卷评估]
    PHQ-9: 12 (Medium)
    GAD-7: 10 (Medium)
    PHQ-9 Q9: 2 (存在自杀念头)
    ↓
[路由映射]
    聊天内容风险: 0.85 (High)
    问卷结果: Medium (但 Q9=2 → High)
    最终路由: High (聊天内容优先级)
```

---

## 🔧 使用示例

### 基本使用

```python
from src_new.perception.psyguard_service import get_psyguard_service
from src_new.perception.questionnaire_trigger import QuestionnaireTrigger
from src_new.perception.questionnaire_service import QuestionnaireService
from src_new.perception.questionnaire_mapper import QuestionnaireMapper

# 初始化服务
psyguard = get_psyguard_service()
await psyguard.load()

trigger = QuestionnaireTrigger(turn_threshold=5)
questionnaire = QuestionnaireService()

# 逐句评分
user_message = "I'm feeling very depressed"
psyguard_result = await psyguard.score(user_message)

# 检查是否触发问卷
trigger_result = trigger.check_trigger(
    turn_count=2,
    psyguard_result=psyguard_result
)

if trigger_result.should_trigger:
    # 执行问卷评估
    phq9_result = await questionnaire.assess("phq9", responses)
    gad7_result = await questionnaire.assess("gad7", responses)
    
    # 最终路由决策
    route = QuestionnaireMapper.final_route_decision(
        phq9_score=phq9_result['total_score'],
        gad7_score=gad7_result['total_score'],
        phq9_q9_score=phq9_result['parsed_scores'][8],
        chat_risk_score=psyguard_result['risk_score']
    )
```

---

## 📝 实现细节

### 风险分数计算

PsyGUARD 模型输出 11 个标签的二进制预测。风险分数计算逻辑：

1. **高风险标签**（0,1,2,3,4,7,8,9）：自杀和自伤相关
   - 如果检测到 → 分数范围 [0.7, 1.0]

2. **中等风险标签**（5,6）：攻击行为
   - 如果检测到 → 分数范围 [0.5, 0.7]

3. **低风险**：无风险标签
   - 分数范围 [0.0, 0.5]

### 模型加载

- 自动检测设备（CUDA/CPU）
- 安全的模型权重加载（兼容不同 PyTorch 版本）
- 错误处理和降级策略

---

## ✅ 完成状态

- [x] PsyGUARD 服务实现
- [x] 问卷触发逻辑实现
- [x] 问卷映射规则实现
- [x] 问卷服务封装
- [x] 单元测试编写
- [x] 集成测试编写
- [x] 测试文档编写

---

## 🚀 下一步

Perception Layer 已完成，可以进入下一层实现：

1. **Control Layer** - 风险路由和级别调整
2. **Conversation Layer** - 三种 Agent 实现
3. **Safety Layer** - Guardrails 集成（已完成）
4. **Adaptive Layer** - 反馈收集

---

**维护者**：开发团队  
**最后更新**：2025-11-07

