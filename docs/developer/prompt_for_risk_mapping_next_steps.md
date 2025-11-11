# Prompt: Risk Mapping 实现进度与下一步建议

请使用这个 prompt 帮助 GPT 理解当前的 Risk Mapping 实现进度，并获取下一步建议。

---

## 📋 复制以下内容给 GPT

---

**你是一个代码架构专家，正在帮助完善 PROXIMO 项目的 Risk Mapping 和 Conversation Router 功能。请仔细阅读以下信息，理解当前实现进度，然后帮助我们设计下一步。**

## 🎯 项目背景

**PROXIMO** 是一个 AI 心理健康评估系统，需要将评估结果转换为对话路由决策。

**核心目标**：将 `assess()` 的输出（评估结果）转换为 Rigidness 分数和对话路由（low/medium/high/crisis）。

---

## ✅ 当前实现进度（已完成）

### 第一阶段：核心封装 ✅
- ✅ `proximo_api.py` 的 `assess()` 函数已完成
- ✅ 简洁的 API：`assess(scale, responses)`
- ✅ 返回统一的字典格式
- ✅ 包含完整的评估结果和风险标志

### 第二阶段：Risk Mapping ✅ **刚完成**

**已实现的功能**：

1. **配置文件** (`config/experiments/risk_mapping.yaml`)
   ```yaml
   severity_to_risk_score:
     minimal: 0.15
     mild: 0.35
     moderate: 0.60
     severe: 0.95
   
   rigid_transform:
     a: 1.0
     b: 0.0
   
   crisis_rules:
     phq9_item9_flag_to_hard_lock: true
     severity_hard_lock: ["severe"]
   ```

2. **风险映射模块** (`src/risk/mapping.py`)
   - ✅ `normalize_sev()`: 严重度标准化
   - ✅ `severity_to_risk()`: 严重度 → 风险分数映射
   - ✅ `risk_to_rigid()`: 风险分数 → Rigidness 转换（线性变换）
   - ✅ `compute_rigid_from_severity()`: 综合计算函数
   - ✅ `is_hard_lock()`: 危机检测（硬锁定判断）
   - ✅ `load_config()`: 配置加载（集成到 ExperimentConfig）

3. **对话路由模块** (`src/conversation/router.py`)
   - ✅ `decide_route()`: 根据评估结果决定对话路由
   - ✅ 支持四种路由：`low`、`medium`、`high`、`crisis`
   - ✅ 危机模式自动覆盖阈值

4. **测试覆盖** ✅
   - ✅ 单元测试：18 个（risk mapping）+ 13 个（router）
   - ✅ 集成测试：6 个（完整流程）
   - ✅ **总计：37 个测试全部通过**

**核心代码结构**：

```python
# src/risk/mapping.py
from dataclasses import dataclass

@dataclass
class RiskMappingConfig:
    severity_to_risk: Dict[str, float]  # 严重度 → 风险分数映射
    a: float  # 线性变换系数
    b: float  # 线性变换截距
    crisis_item9_lock: bool  # 是否启用 Item9 硬锁定
    crisis_severity_lock: set  # 触发硬锁定的严重度级别

def compute_rigid_from_severity(severity: str) -> float:
    """从严重度级别计算 Rigidness 分数"""
    risk = severity_to_risk(severity)  # 映射到风险分数
    return risk_to_rigid(risk)  # 转换为 Rigidness

def is_hard_lock(severity: str, flags: Dict[str, Any]) -> bool:
    """检测是否应该触发硬锁定（危机模式）"""
    # 检查自杀意念（最高优先级）
    if flags.get("suicidal_ideation") or flags.get("suicidal_ideation_score", 0) >= 2:
        return True
    # 检查严重度级别
    return normalized_sev in cfg.crisis_severity_lock
```

```python
# src/conversation/router.py
def decide_route(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """根据评估结果决定对话路由"""
    severity = assessment.get("severity_level")
    flags = assessment.get("flags", {})
    
    # 计算 Rigidness 分数
    rigid = compute_rigid_from_severity(severity)
    
    # 检查硬锁定（危机模式）
    if is_hard_lock(severity, flags):
        return {"route": "crisis", "rigid_score": 1.0, "reason": "hard_lock"}
    
    # 根据 Rigidness 阈值决定路由
    if rigid < 0.40:
        return {"route": "low", "rigid_score": rigid, "reason": "low_risk"}
    elif rigid < 0.75:
        return {"route": "medium", "rigid_score": rigid, "reason": "medium_risk"}
    else:
        return {"route": "high", "rigid_score": rigid, "reason": "high_risk"}
```

**使用示例**：

```python
from src.assessment.proximo_api import assess
from src.conversation.router import decide_route

# 1. 执行评估
assessment = await assess("phq9", ["0", "1", "2", "1", "0", "2", "1", "1", "2"])

# 2. 决定路由
route_decision = decide_route(assessment)
# 返回: {"route": "medium", "rigid_score": 0.60, "reason": "medium_risk"}

# 3. 根据路由执行相应操作
if route_decision["route"] == "crisis":
    handle_crisis_intervention()
```

---

## 📊 当前实现的关键特性

### 1. 风险映射流程

```
评估结果 (assess() 输出)
  ↓
严重度标准化 ("Moderate" → "moderate")
  ↓
严重度 → 风险分数 ("moderate" → 0.60)
  ↓
风险分数 → Rigidness (0.60 → 0.60，线性变换)
  ↓
危机检测 (检查自杀意念、严重度)
  ↓
输出: rigid_score + is_crisis
```

### 2. 对话路由逻辑

```
输入: assessment (assess() 输出)
  ↓
计算 Rigidness 分数
  ↓
检查硬锁定（危机模式）
  ├─ 如果触发 → 返回 {"route": "crisis", "rigid_score": 1.0}
  └─ 如果未触发 → 根据阈值决定路由
      ├─ rigid < 0.40 → "low"
      ├─ 0.40 <= rigid < 0.75 → "medium"
      └─ rigid >= 0.75 → "high"
  ↓
输出: {"route": "...", "rigid_score": 0.x, "reason": "..."}
```

### 3. 硬锁定机制

**触发条件**（优先级从高到低）：
1. **自杀意念**（最高优先级）
   - `flags["suicidal_ideation"] == True`
   - 或 `flags["suicidal_ideation_score"] >= 2`
2. **严重度级别**
   - `severity == "severe"`

**设计原则**：
- ✅ 安全优先：即使严重度是 mild，自杀意念也会触发 crisis
- ✅ 不可覆盖：一旦触发，rigidness = 1.0
- ✅ 可配置：可以通过配置文件调整触发条件

---

## 📁 文件结构

```
config/experiments/
└── risk_mapping.yaml              # 配置文件

src/
├── risk/
│   ├── __init__.py
│   └── mapping.py                 # 风险映射核心逻辑
└── conversation/
    ├── __init__.py
    └── router.py                  # 对话路由核心逻辑

tests/
├── test_risk_mapping.py           # 风险映射单元测试（18个测试）
├── test_router.py                 # 路由单元测试（13个测试）
└── test_risk_routing_integration.py  # 集成测试（6个测试）

scripts/
├── test_risk_routing.py           # 演示脚本
└── verify_risk_routing.py         # 验证脚本
```

---

## 🔍 当前实现的详细逻辑

### 风险映射算法

**映射表**：
```python
severity_to_risk = {
    "minimal": 0.15,      # 15% 风险
    "mild": 0.35,         # 35% 风险
    "moderate": 0.60,     # 60% 风险
    "severe": 0.95,       # 95% 风险
}
```

**线性变换**：
```python
rigid_score = clamp(a * risk_score + b, 0.0, 1.0)
# 默认: a=1.0, b=0.0（直接映射）
```

**硬锁定检测**：
```python
# 优先级 1: 自杀意念
if flags.get("suicidal_ideation") or flags.get("suicidal_ideation_score", 0) >= 2:
    return True  # 触发硬锁定

# 优先级 2: 严重度级别
if severity in {"severe"}:
    return True  # 触发硬锁定
```

### 路由决策算法

**路由阈值**：
- `rigid_score < 0.40` → `low` 路由
- `0.40 <= rigid_score < 0.75` → `medium` 路由
- `rigid_score >= 0.75` → `high` 路由
- 硬锁定触发 → `crisis` 路由（覆盖所有阈值）

---

## 🎯 当前功能状态

### ✅ 已完成的功能

1. **风险映射核心功能**
   - ✅ 严重度到风险分数的映射
   - ✅ 风险分数到 Rigidness 的转换
   - ✅ 危机检测（硬锁定）
   - ✅ 配置化（YAML 配置文件）

2. **对话路由核心功能**
   - ✅ 根据 Rigidness 分数决定路由
   - ✅ 危机模式覆盖
   - ✅ 与 `assess()` 输出完全兼容

3. **测试和验证**
   - ✅ 37 个测试全部通过
   - ✅ 单元测试覆盖核心逻辑
   - ✅ 集成测试验证完整流程

### ⚠️ 当前限制和待改进

1. **配置阈值硬编码**
   - 路由阈值（0.40, 0.75）在代码中硬编码
   - 建议：移到配置文件中

2. **缺少历史数据支持**
   - 当前只处理单次评估
   - 不支持时间序列分析（如漂移检测）

3. **缺少实际路由执行**
   - 只返回路由决策，没有实际执行路由逻辑
   - 需要实现具体的路由处理函数

4. **缺少监控和日志**
   - 没有记录路由决策的日志
   - 没有监控路由变化的机制

---

## 📝 可能的下一步方向

### 方向 1: 增强路由功能

**内容**：
- 实现具体的路由处理函数（如 `handle_crisis_route()`, `handle_low_route()`）
- 添加路由策略配置
- 实现路由执行逻辑

**示例**：
```python
def handle_route(route_decision: Dict[str, Any], assessment: Dict[str, Any]):
    """根据路由决策执行相应的处理逻辑"""
    if route_decision["route"] == "crisis":
        return handle_crisis_intervention(assessment)
    elif route_decision["route"] == "high":
        return handle_high_risk(assessment)
    # ...
```

### 方向 2: 集成存储和历史分析

**内容**：
- 存储评估结果和路由决策到 Redis/Qdrant
- 支持历史数据分析
- 实现漂移检测（与 `drift_detector.py` 集成）

**示例**：
```python
async def assess_with_storage(scale, responses, user_id):
    """评估并存储结果"""
    assessment = await assess(scale, responses)
    route = decide_route(assessment)
    
    # 存储到数据库
    await store_assessment(user_id, assessment, route)
    
    return assessment, route
```

### 方向 3: 配置化路由阈值

**内容**：
- 将路由阈值移到配置文件
- 支持动态调整阈值
- 支持 A/B 测试不同的阈值

**示例**：
```yaml
# config/experiments/risk_mapping.yaml
routing_thresholds:
  low: 0.40
  medium: 0.75
  high: 1.0  # 实际上不需要，因为 rigid >= 0.75 就是 high
```

### 方向 4: 集成到 FastAPI

**内容**：
- 创建 HTTP API 端点
- 支持实时评估和路由
- 添加 WebSocket 推送路由变化

**示例**：
```python
# src/api/routes/assessment.py
@router.post("/assess/{scale}")
async def assess_endpoint(scale: str, responses: List[str]):
    assessment = await assess(scale, responses)
    route = decide_route(assessment)
    return {"assessment": assessment, "route": route}
```

### 方向 5: 增强监控和日志

**内容**：
- 记录所有路由决策
- 实现路由变化监控
- 添加危机模式警报

**示例**：
```python
def decide_route_with_logging(assessment):
    route = decide_route(assessment)
    
    # 记录日志
    logger.info(f"Route decision: {route['route']}, reason: {route['reason']}")
    
    # 如果是危机模式，发送警报
    if route["route"] == "crisis":
        send_crisis_alert(assessment)
    
    return route
```

---

## 🔧 技术细节

### 当前实现的关键函数

**风险映射**：
- `compute_rigid_from_severity(severity) -> float`: 从严重度计算 Rigidness
- `is_hard_lock(severity, flags) -> bool`: 检测硬锁定

**对话路由**：
- `decide_route(assessment) -> Dict`: 决定对话路由

### 数据流

```
assess("phq9", responses)
  ↓
{
    "severity_level": "moderate",
    "flags": {"suicidal_ideation": False, ...},
    ...
}
  ↓
decide_route(assessment)
  ↓
compute_rigid_from_severity("moderate") → 0.60
  ↓
is_hard_lock("moderate", flags) → False
  ↓
{
    "route": "medium",
    "rigid_score": 0.60,
    "reason": "medium_risk"
}
```

### 配置系统

- 使用 `ExperimentConfig` 系统加载配置
- 配置文件：`config/experiments/risk_mapping.yaml`
- 配置缺失时使用默认值
- 支持部分覆盖（只覆盖需要修改的字段）

---

## 🎯 需要决策的问题

1. **下一步优先级**
   - 应该先实现哪个功能？
   - 是否需要先完善当前功能，还是直接扩展新功能？

2. **路由执行逻辑**
   - 是否需要实现具体的路由处理函数？
   - 不同路由应该执行什么操作？

3. **存储和历史分析**
   - 是否需要存储评估结果？
   - 是否需要实现漂移检测？

4. **API 集成**
   - 是否需要创建 HTTP API 端点？
   - 是否需要 WebSocket 实时推送？

5. **监控和日志**
   - 需要记录哪些信息？
   - 需要什么样的监控机制？

---

## 💡 请帮助分析

**基于以上信息，请帮助我：**

1. **评估当前实现**
   - 当前实现是否满足设计目标？
   - 还有哪些需要改进的地方？

2. **设计下一步**
   - 应该优先实现哪个功能？
   - 如何设计具体的实现方案？
   - 如何保持代码的简洁性和可维护性？

3. **代码优化建议**
   - 是否有性能优化空间？
   - 是否有代码结构改进空间？
   - 是否有更好的设计模式？

4. **架构建议**
   - 如何更好地组织代码？
   - 如何平衡功能的完整性和代码的简洁性？
   - 如何设计扩展接口？

5. **最佳实践**
   - 是否有行业最佳实践可以参考？
   - 如何确保代码的可测试性和可维护性？

---

## 📚 相关文档

- `docs/developer/risk_mapping_implementation_summary.md` - 实现总结
- `docs/developer/risk_mapping_logic_analysis.md` - 逻辑分析
- `docs/developer/gpt_proposal_review.md` - GPT 方案评估
- `docs/developer/proximo_api_encapsulation_analysis.md` - API 封装分析

---

## 🔍 关键代码文件

**核心实现**：
- `src/risk/mapping.py` - 风险映射核心逻辑（178 行）
- `src/conversation/router.py` - 对话路由核心逻辑（107 行）
- `config/experiments/risk_mapping.yaml` - 配置文件

**测试文件**：
- `tests/test_risk_mapping.py` - 18 个测试
- `tests/test_router.py` - 13 个测试
- `tests/test_risk_routing_integration.py` - 6 个集成测试

**演示脚本**：
- `scripts/test_risk_routing.py` - 完整使用示例
- `scripts/verify_risk_routing.py` - 快速验证

---

**请基于以上信息，提供详细的下一步建议和设计方案。**

---


