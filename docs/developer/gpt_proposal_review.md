# GPT 方案评估与改进建议

本文档评估 GPT 提供的下一步方案，并提供改进建议以适配当前项目结构。

---

## 📊 方案评估

### ✅ 优点

1. **模块化设计**：清晰分离职责（配置、风险映射、路由）
2. **保持 `assess()` 不变**：符合要求
3. **可配置**：使用 YAML 配置文件
4. **可测试**：提供了单元测试
5. **容错机制**：配置文件缺失时使用默认值

### ⚠️ 需要调整的问题

#### 问题 1: 路径结构不匹配

**GPT 方案**：
```python
proximo/config/risk_mapping.yml
proximo/risk/mapping.py
proximo/conversation/router.py
```

**项目实际结构**：
```
src/
config/experiments/
```

**需要调整**：
- 使用 `src/` 作为根目录
- 配置文件放在 `config/experiments/` 或创建新目录
- 导入路径使用 `from src.risk.mapping import ...`

#### 问题 2: 严重度级别不匹配

**GPT 方案使用**：
```yaml
severity_to_risk_score:
  minimal: 0.15
  mild: 0.35
  moderate: 0.60
  moderately_severe: 0.80  # ⚠️ 项目中没有这个级别
  severe: 0.95
```

**项目实际级别**（`SeverityLevel` 枚举）：
```python
MINIMAL = "minimal"
MILD = "mild"
MODERATE = "moderate"
SEVERE = "severe"  # 没有 "moderately_severe"
```

**需要调整**：移除 `moderately_severe`，只使用项目实际存在的级别

#### 问题 3: flags 字段名不匹配

**GPT 方案检查**：
```python
flags.get("phq9_item9")  # ⚠️ 实际字段名是 "suicidal_ideation"
```

**`assess()` 实际返回**：
```python
flags = {
    "suicidal_ideation": True,  # ✅ 实际字段名
    "suicidal_ideation_score": 2,
    "severe_symptoms": False
}
```

**需要调整**：使用 `flags.get("suicidal_ideation")` 而不是 `flags.get("phq9_item9")`

#### 问题 4: 配置加载方式

**GPT 方案**：直接使用文件路径加载 YAML

**项目实际**：使用 `ExperimentConfig` 系统加载配置

**建议**：
- 可以创建新配置文件，但考虑集成到现有的 `ExperimentConfig` 系统
- 或者保持独立，但使用项目标准的配置目录结构

---

## 🔧 改进后的方案

### 1. 调整后的文件结构

```
config/
└── experiments/
    └── risk_mapping.yaml  # 新增配置文件

src/
├── risk/
│   ├── __init__.py
│   └── mapping.py  # 新增风险映射模块
└── conversation/
    ├── __init__.py
    └── router.py  # 新增对话路由模块

tests/
├── test_risk_mapping.py  # 新增测试
└── test_router.py  # 新增测试
```

### 2. 调整后的配置文件

```yaml
# config/experiments/risk_mapping.yaml

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
  severity_hard_lock: ["severe"]  # 移除 moderately_severe
```

### 3. 调整后的风险映射模块

```python
# src/risk/mapping.py

from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import yaml

from src.core.experiment_config import experiment_config

@dataclass
class RiskMappingConfig:
    severity_to_risk: Dict[str, float]
    a: float
    b: float
    crisis_item9_lock: bool
    crisis_severity_lock: set

DEFAULT = RiskMappingConfig(
    severity_to_risk={
        "minimal": 0.15,
        "mild": 0.35,
        "moderate": 0.60,
        "severe": 0.95
    },
    a=1.0,
    b=0.0,
    crisis_item9_lock=True,
    crisis_severity_lock={"severe"},
)

def load_config() -> RiskMappingConfig:
    """从配置文件加载风险映射配置"""
    try:
        # 尝试从 experiment_config 加载
        config = experiment_config.get_config("risk_mapping")
        if config:
            sev = config.get("severity_to_risk_score", {})
            rigid = config.get("rigid_transform", {})
            crises = config.get("crisis_rules", {})
            
            return RiskMappingConfig(
                severity_to_risk={**DEFAULT.severity_to_risk, **sev},
                a=float(rigid.get("a", DEFAULT.a)),
                b=float(rigid.get("b", DEFAULT.b)),
                crisis_item9_lock=bool(crises.get("phq9_item9_flag_to_hard_lock", True)),
                crisis_severity_lock=set(crises.get("severity_hard_lock", ["severe"])),
            )
    except Exception:
        pass
    
    # 如果加载失败，返回默认值
    return DEFAULT

def normalize_sev(sev: str) -> str:
    """标准化严重度字符串"""
    return sev.strip().lower().replace(" ", "_")

def severity_to_risk(severity: str, cfg: RiskMappingConfig) -> float:
    """将严重度级别转换为风险分数"""
    normalized = normalize_sev(severity)
    return cfg.severity_to_risk.get(normalized, cfg.severity_to_risk["moderate"])

def risk_to_rigid(risk: float, cfg: RiskMappingConfig) -> float:
    """将风险分数转换为 rigidness 分数"""
    x = cfg.a * float(risk) + cfg.b
    return max(0.0, min(1.0, x))

def compute_rigid_from_severity(severity: str, cfg: RiskMappingConfig | None = None) -> float:
    """从严重度级别计算 rigidness 分数"""
    if cfg is None:
        cfg = load_config()
    risk = severity_to_risk(severity, cfg)
    return risk_to_rigid(risk, cfg)

def is_hard_lock(severity: str, flags: Dict[str, Any], cfg: RiskMappingConfig | None = None) -> bool:
    """检查是否应该触发硬锁定（危机模式）"""
    if cfg is None:
        cfg = load_config()
    
    # 检查自杀意念（使用实际的字段名）
    item9 = bool(flags.get("suicidal_ideation") or flags.get("suicidal_ideation_score", 0) >= 2)
    if cfg.crisis_item9_lock and item9:
        return True
    
    # 检查严重度级别
    normalized_sev = normalize_sev(severity)
    return normalized_sev in cfg.crisis_severity_lock
```

### 4. 调整后的对话路由模块

```python
# src/conversation/router.py

from typing import Dict, Any
from src.risk.mapping import load_config, compute_rigid_from_severity, is_hard_lock

class Route:
    """对话路由常量"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRISIS = "crisis"

def decide_route(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据评估结果决定对话路由
    
    Args:
        assessment: `assess()` 函数返回的评估结果字典
        
    Returns:
        包含路由信息的字典：
        {
            "route": "low" | "medium" | "high" | "crisis",
            "rigid_score": float,  # 0.0 - 1.0
            "reason": str  # 路由原因
        }
    """
    cfg = load_config()
    
    # 提取严重度级别（支持多种字段名）
    sev = (
        assessment.get("severity_level") or 
        assessment.get("severity") or 
        "moderate"
    )
    
    flags = assessment.get("flags", {})
    rigid = compute_rigid_from_severity(sev, cfg)
    
    # 检查是否需要硬锁定（危机模式）
    if is_hard_lock(sev, flags, cfg):
        return {
            "route": Route.CRISIS,
            "rigid_score": 1.0,
            "reason": "hard_lock"
        }
    
    # 根据 rigidness 分数决定路由
    if rigid < 0.40:
        return {
            "route": Route.LOW,
            "rigid_score": rigid,
            "reason": "low_risk"
        }
    elif rigid < 0.75:
        return {
            "route": Route.MEDIUM,
            "rigid_score": rigid,
            "reason": "medium_risk"
        }
    else:
        return {
            "route": Route.HIGH,
            "rigid_score": rigid,
            "reason": "high_risk"
        }
```

### 5. 调整后的测试

```python
# tests/test_risk_mapping.py

import pytest
from src.risk.mapping import (
    DEFAULT,
    compute_rigid_from_severity,
    is_hard_lock,
    normalize_sev
)

def test_normalize_severity():
    """测试严重度标准化"""
    assert normalize_sev("minimal") == "minimal"
    assert normalize_sev("Minimal") == "minimal"
    assert normalize_sev("moderately severe") == "moderately_severe"

def test_mapping_defaults():
    """测试默认映射值"""
    assert abs(compute_rigid_from_severity("minimal", DEFAULT) - 0.15) < 1e-9
    assert abs(compute_rigid_from_severity("mild", DEFAULT) - 0.35) < 1e-9
    assert abs(compute_rigid_from_severity("moderate", DEFAULT) - 0.60) < 1e-9
    assert abs(compute_rigid_from_severity("severe", DEFAULT) - 0.95) < 1e-9

def test_hard_lock_item9():
    """测试自杀意念硬锁定"""
    # 使用实际的字段名
    assert is_hard_lock("mild", {"suicidal_ideation": True}, DEFAULT) is True
    assert is_hard_lock("mild", {"suicidal_ideation_score": 2}, DEFAULT) is True
    assert is_hard_lock("mild", {"suicidal_ideation": False}, DEFAULT) is False

def test_hard_lock_severity():
    """测试严重度硬锁定"""
    assert is_hard_lock("severe", {}, DEFAULT) is True
    assert is_hard_lock("moderate", {}, DEFAULT) is False
    assert is_hard_lock("mild", {}, DEFAULT) is False
```

```python
# tests/test_router.py

import pytest
from src.conversation.router import decide_route, Route

def make_assessment(sev: str, flags: dict = None):
    """创建测试用的评估结果"""
    return {
        "severity_level": sev,
        "flags": flags or {},
        "success": True
    }

def test_routes_by_rigid_thresholds():
    """测试根据 rigidness 阈值路由"""
    assert decide_route(make_assessment("minimal"))["route"] == Route.LOW
    assert decide_route(make_assessment("mild"))["route"] == Route.LOW
    assert decide_route(make_assessment("moderate"))["route"] == Route.MEDIUM
    assert decide_route(make_assessment("severe"))["route"] == Route.HIGH

def test_crisis_overrides():
    """测试危机模式覆盖"""
    # 自杀意念触发危机模式
    r = decide_route(make_assessment("mild", {"suicidal_ideation": True}))
    assert r["route"] == Route.CRISIS
    assert r["rigid_score"] == 1.0
    assert r["reason"] == "hard_lock"
    
    # 严重度触发危机模式
    r = decide_route(make_assessment("severe", {}))
    assert r["route"] == Route.CRISIS
    assert r["rigid_score"] == 1.0

def test_router_with_actual_assess_output():
    """测试与实际 assess() 输出格式的兼容性"""
    # 模拟 assess() 的实际输出
    assessment = {
        "success": True,
        "scale": "phq9",
        "total_score": 15.0,
        "severity_level": "moderate",
        "flags": {
            "suicidal_ideation": False,
            "suicidal_ideation_score": 0,
            "severe_symptoms": False
        },
        "clinical_interpretation": {...}
    }
    
    result = decide_route(assessment)
    assert "route" in result
    assert "rigid_score" in result
    assert "reason" in result
    assert result["route"] in [Route.LOW, Route.MEDIUM, Route.HIGH, Route.CRISIS]
```

---

## 📝 集成到 ExperimentConfig 系统（可选）

如果想要与项目现有的配置系统集成，可以：

### 1. 在 `experiment_config.py` 中添加配置加载

```python
# src/core/experiment_config.py

def load_all_configs(self) -> bool:
    config_files = [
        "clinical_thresholds.yaml",
        "drift_detection.yaml",
        "personality_drift.yaml",
        "simulation_timing.yaml",
        "mechanistic_analysis.yaml",
        "risk_mapping.yaml",  # 新增
    ]
    # ...
```

### 2. 在 `risk/mapping.py` 中使用

```python
def load_config() -> RiskMappingConfig:
    try:
        config = experiment_config.get_config("risk_mapping")
        # ...
    except Exception:
        return DEFAULT
```

---

## ✅ 使用示例

```python
# 使用示例
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
        # 触发危机干预流程
        handle_crisis_intervention(assessment)
    elif route_decision["route"] == "high":
        # 高风险管理
        handle_high_risk(assessment)
    # ...
```

---

## 📊 总结

### GPT 方案评估

| 方面 | 评价 | 说明 |
|------|------|------|
| 设计思路 | ✅ 优秀 | 模块化、可测试、可配置 |
| 路径结构 | ⚠️ 需调整 | 需要适配 `src/` 结构 |
| 字段匹配 | ⚠️ 需调整 | 需要匹配实际的 `assess()` 输出 |
| 配置系统 | ⚠️ 需调整 | 建议集成到 `ExperimentConfig` |
| 严重度级别 | ⚠️ 需调整 | 移除不存在的 `moderately_severe` |

### 改进建议优先级

1. **高优先级**（必须调整）：
   - ✅ 修正路径结构（`src/` 而不是 `proximo/`）
   - ✅ 修正字段名（`suicidal_ideation` 而不是 `phq9_item9`）
   - ✅ 移除 `moderately_severe` 级别

2. **中优先级**（建议调整）：
   - ⚠️ 集成到 `ExperimentConfig` 系统
   - ⚠️ 添加更多错误处理
   - ⚠️ 添加日志记录

3. **低优先级**（可选）：
   - 📝 添加类型提示改进
   - 📝 添加文档字符串
   - 📝 添加更多边界情况测试

---

## 🎯 建议

**总体评价**：GPT 的方案设计思路很好，但需要根据项目实际情况进行调整。

**建议**：
1. ✅ **采用 GPT 的设计思路**（模块化、可配置、可测试）
2. ✅ **应用上述改进**（路径、字段名、严重度级别）
3. ✅ **保持与项目现有结构一致**（使用 `src/`、集成 `ExperimentConfig`）
4. ✅ **添加更多测试**（特别是与实际 `assess()` 输出的集成测试）

---

**编写日期**: 2025-01-XX  
**最后更新**: 2025-01-XX


