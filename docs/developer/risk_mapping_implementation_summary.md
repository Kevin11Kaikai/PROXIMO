# Risk Mapping + Conversation Router 实现总结

本文档总结 Risk Mapping 和 Conversation Router 的完整实现。

---

## ✅ 实现完成情况

### 已完成的功能

1. ✅ **配置文件** (`config/experiments/risk_mapping.yaml`)
   - 严重度到风险分数的映射
   - 线性变换参数（rigid_transform）
   - 危机检测规则

2. ✅ **风险映射模块** (`src/risk/mapping.py`)
   - 严重度级别 → 风险分数转换
   - 风险分数 → Rigidness 分数转换
   - 危机检测（硬锁定判断）

3. ✅ **对话路由模块** (`src/conversation/router.py`)
   - 根据评估结果决定对话路由
   - 支持四种路由：low/medium/high/crisis
   - 危机模式自动覆盖

4. ✅ **测试覆盖**
   - 单元测试：18 个（risk mapping）+ 13 个（router）
   - 集成测试：6 个（完整流程）
   - 总计：**37 个测试全部通过**

---

## 📁 创建的文件

```
config/experiments/
└── risk_mapping.yaml              # 配置文件

src/
├── risk/
│   ├── __init__.py                # 模块导出
│   └── mapping.py                 # 风险映射核心逻辑
└── conversation/
    ├── __init__.py                # 模块导出
    └── router.py                  # 对话路由核心逻辑

tests/
├── test_risk_mapping.py           # 风险映射单元测试（18个测试）
├── test_router.py                 # 路由单元测试（13个测试）
└── test_risk_routing_integration.py  # 集成测试（6个测试）

scripts/
└── test_risk_routing.py           # 演示脚本
```

---

## 🔧 核心功能

### 1. 风险映射 (`src/risk/mapping.py`)

**核心函数**：

```python
# 从严重度级别计算 Rigidness 分数
rigid_score = compute_rigid_from_severity("moderate")  # 返回 0.60

# 检查是否触发硬锁定（危机模式）
is_crisis = is_hard_lock("mild", {"suicidal_ideation": True})  # 返回 True
```

**映射规则**：
- `minimal` → 0.15
- `mild` → 0.35
- `moderate` → 0.60
- `severe` → 0.95

**硬锁定触发条件**：
1. 自杀意念标志为 True（`flags["suicidal_ideation"]`）
2. 自杀意念分数 ≥ 2（`flags["suicidal_ideation_score"] >= 2`）
3. 严重度级别为 `severe`

### 2. 对话路由 (`src/conversation/router.py`)

**核心函数**：

```python
# 根据评估结果决定路由
route_decision = decide_route(assessment)
# 返回: {"route": "low|medium|high|crisis", "rigid_score": 0.x, "reason": "..."}
```

**路由规则**：
- `rigid_score < 0.40` → **low** 路由
- `0.40 <= rigid_score < 0.75` → **medium** 路由
- `rigid_score >= 0.75` → **high** 路由（除非触发危机）
- 硬锁定触发 → **crisis** 路由（覆盖所有阈值）

---

## 📊 使用示例

### 基本使用

```python
from src.assessment.proximo_api import assess
from src.conversation.router import decide_route

# 1. 执行评估
assessment = await assess("phq9", ["0", "1", "2", "1", "0", "2", "1", "1", "2"])

if assessment["success"]:
    # 2. 决定路由
    route_decision = decide_route(assessment)
    
    print(f"Route: {route_decision['route']}")
    print(f"Rigidness Score: {route_decision['rigid_score']}")
    print(f"Reason: {route_decision['reason']}")
    
    # 3. 根据路由执行相应操作
    if route_decision["route"] == "crisis":
        handle_crisis_intervention(assessment)
    elif route_decision["route"] == "high":
        handle_high_risk(assessment)
    # ...
```

### 完整流程示例

```python
# 场景 1: 低风险
assessment = await assess("phq9", ["0", "0", "1", "0", "1", "0", "1", "0", "0"])
route = decide_route(assessment)
# 结果: {"route": "low", "rigid_score": 0.15, "reason": "low_risk"}

# 场景 2: 中等风险
assessment = await assess("phq9", ["1", "1", "2", "2", "1", "2", "1", "2", "0"])
route = decide_route(assessment)
# 结果: {"route": "medium", "rigid_score": 0.60, "reason": "medium_risk"}

# 场景 3: 危机（自杀意念）
assessment = await assess("phq9", ["1", "1", "1", "1", "1", "1", "1", "1", "2"])
route = decide_route(assessment)
# 结果: {"route": "crisis", "rigid_score": 1.0, "reason": "hard_lock"}
```

---

## ✅ 测试结果

### 测试统计

- **风险映射模块测试**: 18 个测试 ✅ 全部通过
- **路由模块测试**: 13 个测试 ✅ 全部通过
- **集成测试**: 6 个测试 ✅ 全部通过
- **总计**: **37 个测试全部通过**

### 测试覆盖

- ✅ 严重度标准化
- ✅ 严重度到风险分数映射
- ✅ 风险分数到 Rigidness 转换
- ✅ 硬锁定检测（自杀意念、严重度）
- ✅ 路由决策（所有路由类型）
- ✅ 与 `assess()` 输出的集成
- ✅ 边界情况处理

---

## 🎯 关键特性

### 1. 配置化

所有阈值和规则都可通过 `config/experiments/risk_mapping.yaml` 配置：

```yaml
severity_to_risk_score:
  minimal: 0.15
  mild: 0.35
  moderate: 0.60
  severe: 0.95

crisis_rules:
  phq9_item9_flag_to_hard_lock: true
  severity_hard_lock: ["severe"]
```

### 2. 容错处理

- 配置文件缺失时使用默认值
- 未知严重度级别默认使用 `moderate`
- 字段缺失时使用默认值

### 3. 与 `assess()` 完全兼容

- 直接接受 `assess()` 的输出
- 支持多种字段名（`severity_level` 或 `severity`）
- 自动提取 `flags` 字段

### 4. 危机检测优先级

危机模式（硬锁定）会覆盖所有阈值：
- 即使严重度是 `mild`，如果有自杀意念，也会触发 `crisis` 路由
- `severe` 严重度自动触发 `crisis` 路由

---

## 📝 API 文档

### `compute_rigid_from_severity(severity: str) -> float`

从严重度级别计算 Rigidness 分数。

**参数**:
- `severity`: 严重度级别（"minimal", "mild", "moderate", "severe"）

**返回**:
- Rigidness 分数 (0.0 - 1.0)

**示例**:
```python
rigid = compute_rigid_from_severity("moderate")  # 0.60
```

### `is_hard_lock(severity: str, flags: Dict[str, Any]) -> bool`

检查是否应该触发硬锁定（危机模式）。

**参数**:
- `severity`: 严重度级别
- `flags`: 评估标志字典（来自 `assess()` 输出）

**返回**:
- `True` 如果应该触发硬锁定，否则 `False`

**示例**:
```python
is_crisis = is_hard_lock("mild", {"suicidal_ideation": True})  # True
```

### `decide_route(assessment: Dict[str, Any]) -> Dict[str, Any]`

根据评估结果决定对话路由。

**参数**:
- `assessment`: `assess()` 函数返回的评估结果字典

**返回**:
```python
{
    "route": "low" | "medium" | "high" | "crisis",
    "rigid_score": float,  # 0.0 - 1.0
    "reason": str  # 路由原因
}
```

**示例**:
```python
assessment = await assess("phq9", [...])
route = decide_route(assessment)
# {"route": "medium", "rigid_score": 0.60, "reason": "medium_risk"}
```

---

## 🔄 完整数据流

```
用户回答
    ↓
assess("phq9", responses)
    ↓
评估结果
{
    "severity_level": "moderate",
    "flags": {"suicidal_ideation": False, ...},
    ...
}
    ↓
decide_route(assessment)
    ↓
风险映射
    ├─ severity_to_risk("moderate") → 0.60
    ├─ risk_to_rigid(0.60) → 0.60
    └─ is_hard_lock(...) → False
    ↓
路由决策
{
    "route": "medium",
    "rigid_score": 0.60,
    "reason": "medium_risk"
}
    ↓
对话策略执行
```

---

## 🎯 下一步

### 可选扩展

1. **集成到 FastAPI**
   - 创建 `/api/assess/{scale}` 端点
   - 返回评估结果和路由决策

2. **添加存储功能**
   - 存储评估历史和路由决策
   - 支持历史数据分析

3. **添加实时监控**
   - WebSocket 推送路由变化
   - 危机模式实时警报

4. **优化配置**
   - 支持动态配置更新
   - 支持 A/B 测试不同的路由阈值

---

## 📊 测试运行结果

```bash
# 运行所有测试
$ pytest tests/test_risk_mapping.py tests/test_router.py tests/test_risk_routing_integration.py -v

# 结果: 37 passed
```

**测试覆盖**:
- `src/risk/mapping.py`: 89% 覆盖率
- `src/conversation/router.py`: 96% 覆盖率

---

## ✅ 验收标准

- ✅ 新文件创建并成功导入
- ✅ 所有测试通过（37/37）
- ✅ `assess()` 函数签名和行为未改变
- ✅ 路由决策是确定性的
- ✅ 危机模式正确覆盖阈值
- ✅ 配置可通过 YAML 调整
- ✅ 配置缺失时使用默认值

---

**实现日期**: 2025-01-XX  
**测试状态**: ✅ 37/37 测试通过  
**覆盖率**: 89% (mapping) + 96% (router)


