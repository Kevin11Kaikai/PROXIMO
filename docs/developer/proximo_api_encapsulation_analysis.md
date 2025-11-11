# `proximo_api.py` 封装分析：如何简化评估接口

本文档详细分析 `proximo_api.py` 中的 `assess` 函数如何封装底层的 `psychiatric_scales.py` 和 `clinical_interpreter.py`，实现从复杂到简洁的 API 设计。

---

## 📋 目录

1. [封装设计目标](#封装设计目标)
2. [核心封装函数：`assess()`](#核心封装函数assess)
3. [数据流转与调用链](#数据流转与调用链)
4. [封装层次解析](#封装层次解析)
5. [关键设计点](#关键设计点)

---

## 封装设计目标

### 问题：底层 API 的复杂性

**底层 API（`psychiatric_scales.py`）的使用方式**：
```python
# 需要手动创建 Persona 对象
from src.models.persona import Persona, PersonaBaseline, PersonaState

persona = Persona(
    baseline=PersonaBaseline(
        name="User", age=30, occupation="Unknown",
        openness=0.5, conscientiousness=0.5, ...
    ),
    state=PersonaState(
        persona_id="user_123", simulation_day=0, ...
    )
)

# 需要手动创建 Orchestrator
from src.assessment.psychiatric_scales import AssessmentOrchestrator

orchestrator = AssessmentOrchestrator()
result = await orchestrator.conduct_phq9_assessment(persona, responses)

# 结果对象复杂，需要手动提取字段
print(result.total_score)  # 需要知道对象结构
print(result.severity_level.value)  # 需要知道枚举类型
print(result.clinical_interpretation["recommendations"])  # 需要知道嵌套结构
```

**问题**：
- ❌ 需要创建复杂的 `Persona` 对象（包含很多不必要的信息）
- ❌ 需要手动管理 `AssessmentOrchestrator` 实例
- ❌ 返回的结果对象结构复杂，提取信息需要了解内部实现
- ❌ 错误处理分散，需要手动检查 `None` 和异常

### 解决方案：简洁的 API 封装

**封装后的 API（`proximo_api.py`）使用方式**：
```python
from src.assessment.proximo_api import assess

# 只需提供量表类型和回答列表
result = await assess("phq9", ["0", "1", "2", "1", "0", "2", "1", "1", "2"])

# 结果统一为字典格式，易于使用
if result["success"]:
    print(result["total_score"])  # 直接访问
    print(result["severity_level"])  # 已经是字符串
    print(result["clinical_interpretation"]["recommendations"])  # 嵌套结构清晰
    print(result["flags"]["suicidal_ideation"])  # 风险标志已提取
else:
    print(result["error"])  # 统一错误处理
```

**优势**：
- ✅ **零配置**：不需要创建 `Persona` 对象
- ✅ **自动管理**：内部使用单例模式管理 `AssessmentOrchestrator`
- ✅ **统一格式**：返回统一的字典格式，易于使用和序列化
- ✅ **错误处理**：统一的错误处理机制
- ✅ **信息提取**：自动提取关键信息（风险标志、临床建议等）

---

## 核心封装函数：`assess()`

### 函数签名

```python
async def assess(
    scale: Literal["phq9", "gad7", "pss10"],
    responses: List[str],
    persona_id: Optional[str] = None,
    simulation_day: int = 0
) -> Dict[str, Any]:
```

### 完整实现流程分析

#### Stage 1: 参数验证（封装层）

```python
# ===== 参数验证 =====
valid_scales = ["phq9", "gad7", "pss10"]
if scale not in valid_scales:
    raise ValueError(f"Invalid scale: {scale}. Must be one of {valid_scales}")

# 验证回答数量
expected_counts = {
    "phq9": 9,
    "gad7": 7,
    "pss10": 10
}
expected_count = expected_counts[scale]
if len(responses) != expected_count:
    raise ValueError(
        f"{scale.upper()} requires {expected_count} responses, "
        f"got {len(responses)}"
    )
```

**封装作用**：
- ✅ **提前验证**：在调用底层 API 之前就进行参数验证
- ✅ **清晰的错误信息**：提供具体的错误原因（量表类型、回答数量）
- ✅ **避免无效调用**：减少底层 API 的无效调用

#### Stage 2: Persona 对象创建（封装层）

```python
# ===== 创建最小 Persona 对象 =====
persona = _create_minimal_persona(persona_id)
persona.state.simulation_day = simulation_day
```

**封装作用**：
- ✅ **隐藏复杂性**：用户不需要了解 `Persona` 对象的内部结构
- ✅ **最小化配置**：只创建评估所需的最小信息
- ✅ **自动生成**：自动生成 `persona_id`（如果未提供）

**`_create_minimal_persona()` 函数**：
```python
def _create_minimal_persona(persona_id: Optional[str] = None) -> Persona:
    """创建一个最小的 Persona 对象用于评估"""
    persona_id = persona_id or f"assess_{uuid.uuid4().hex[:8]}"
    
    # 创建最小基线配置
    baseline = PersonaBaseline(
        name="Assessment User",
        age=30,
        occupation="Unknown",
        background="Assessment-only persona",
        openness=0.5,  # 默认值
        conscientiousness=0.5,
        extraversion=0.5,
        agreeableness=0.5,
        neuroticism=0.5,
        baseline_phq9=0.0,
        baseline_gad7=0.0,
        baseline_pss10=0.0
    )
    
    # 创建最小状态配置
    state = PersonaState(
        persona_id=persona_id,
        simulation_day=0,
        last_assessment_day=-1
    )
    
    return Persona(baseline=baseline, state=state)
```

#### Stage 3: 调用底层 API（封装层 → 底层）

```python
# ===== 执行评估 =====
orchestrator = _get_orchestrator()  # 单例模式

if scale == "phq9":
    result = await orchestrator.conduct_phq9_assessment(persona, responses)
elif scale == "gad7":
    result = await orchestrator.conduct_gad7_assessment(persona, responses)
elif scale == "pss10":
    result = await orchestrator.conduct_pss10_assessment(persona, responses)
```

**封装作用**：
- ✅ **统一接口**：通过 `scale` 参数统一调用不同的评估方法
- ✅ **单例管理**：使用 `_get_orchestrator()` 实现单例模式，避免重复创建

**`_get_orchestrator()` 函数**：
```python
_orchestrator = None  # 全局单例

def _get_orchestrator() -> AssessmentOrchestrator:
    """获取全局 orchestrator 实例（单例模式）"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AssessmentOrchestrator()
    return _orchestrator
```

#### Stage 4: 结果提取与格式化（封装层）

```python
if result is None:
    return {
        "success": False,
        "error": "Assessment failed - validation error or insufficient data"
    }

# ===== 提取关键信息 =====
assessment_result = {
    "success": True,
    "scale": scale,
    "total_score": result.total_score,
    "severity_level": result.severity_level.value,  # 转为字符串
    "parsed_scores": result.parsed_scores,
    "raw_responses": result.raw_responses,
}

# ===== 添加临床解释 =====
if result.clinical_interpretation:
    assessment_result["clinical_interpretation"] = result.clinical_interpretation
else:
    # 如果没有临床解释，创建一个基本的
    assessment_result["clinical_interpretation"] = {
        "severity_level": result.severity_level.value,
        "total_score": result.total_score,
        "recommendations": [],
        "risk_factors": []
    }

# ===== 提取风险标志（flags）=====
flags = {}

# PHQ-9 特殊处理
if isinstance(result, PHQ9Result):
    flags["suicidal_ideation"] = result.has_suicidal_ideation()
    flags["suicidal_ideation_score"] = result.suicidal_ideation_score
    assessment_result["suicidal_risk"] = (
        "high" if result.has_suicidal_ideation() else "low"
    )

# 严重症状标志
if scale == "phq9" or scale == "gad7":
    flags["severe_symptoms"] = result.total_score >= 20
elif scale == "pss10":
    flags["severe_symptoms"] = result.total_score >= 25

assessment_result["flags"] = flags

# ===== 添加风险级别（从临床解释中提取）=====
if result.clinical_interpretation:
    interpretation = result.clinical_interpretation
    if "suicidal_risk" in interpretation:
        assessment_result["risk_level"] = (
            "critical" if interpretation["suicidal_risk"] == "high" else "low"
        )
    elif result.total_score >= 20:
        assessment_result["risk_level"] = "high"
    elif result.total_score >= 10:
        assessment_result["risk_level"] = "moderate"
    else:
        assessment_result["risk_level"] = "low"
```

**封装作用**：
- ✅ **统一格式**：将复杂的对象结构转换为统一的字典格式
- ✅ **信息提取**：自动提取关键信息（风险标志、风险级别等）
- ✅ **类型转换**：将枚举类型转换为字符串（`result.severity_level.value`）
- ✅ **容错处理**：处理 `None` 结果和缺失的临床解释

#### Stage 5: 错误处理（封装层）

```python
except ValueError as e:
    logger.error(f"Validation error in assess(): {e}")
    return {
        "success": False,
        "error": str(e)
    }
except Exception as e:
    logger.error(f"Error in assess(): {e}", exc_info=True)
    return {
        "success": False,
        "error": f"Assessment failed: {str(e)}"
    }
```

**封装作用**：
- ✅ **统一错误格式**：所有错误都返回 `{"success": False, "error": "..."}` 格式
- ✅ **错误日志**：记录详细的错误信息（便于调试）
- ✅ **异常捕获**：捕获所有异常，避免程序崩溃

---

## 数据流转与调用链

### 完整调用链

```
用户调用
  ↓
【proximo_api.py】
  assess("phq9", responses)
    ├─ 参数验证
    ├─ 创建最小 Persona 对象
    ├─ 获取 Orchestrator 实例（单例）
    └─ 调用 orchestrator.conduct_phq9_assessment(persona, responses)
        ↓
【psychiatric_scales.py】
  AssessmentOrchestrator.conduct_phq9_assessment()
    ├─ Stage 1: 调用 validator.validate_phq9_response() [批量校验]
    ├─ Stage 2: 计算总分、严重度分级
    ├─ Stage 2: 构建 PHQ9Result 对象
    └─ Stage 3: 调用 interpreter.interpret_phq9_result() [临床解释]
        ↓
【psychiatric_scales.py】
  ClinicalInterpreter.interpret_phq9_result()
    ├─ 生成临床含义
    ├─ 生成建议列表
    ├─ 检测自杀意念风险
    └─ 返回临床解释字典
        ↓
【proximo_api.py】
  assess() 函数
    ├─ 提取关键信息
    ├─ 格式化结果
    ├─ 提取风险标志
    └─ 返回统一的字典格式
        ↓
用户接收结果
```

### 数据转换过程

#### 输入层（用户）

```python
# 用户输入：简单、直观
responses = ["0", "1", "2", "1", "0", "2", "1", "1", "2"]
result = await assess("phq9", responses)
```

#### 封装层（proximo_api.py）

```python
# 封装层：创建 Persona 对象
persona = _create_minimal_persona()  # 自动创建

# 封装层：调用底层 API
result_obj = await orchestrator.conduct_phq9_assessment(persona, responses)
# result_obj 类型: Optional[PHQ9Result]
```

#### 底层 API（psychiatric_scales.py）

```python
# AssessmentOrchestrator 内部处理：
# Stage 1: 文本标准化
validated_scores = [0, 1, 2, 1, 0, 2, 1, 1, 2]

# Stage 2: 计算总分
total_score = 10.0

# Stage 2: 严重度分级
severity_level = SeverityLevel.MILD  # 枚举类型

# Stage 2: 构建结果对象
result = PHQ9Result(
    total_score=10.0,
    severity_level=SeverityLevel.MILD,
    suicidal_ideation_score=2,
    clinical_interpretation={...}
)

# Stage 3: 生成临床解释
clinical_interpretation = {
    "severity_level": "mild",
    "recommendations": [...],
    "suicidal_risk": "high"
}
```

#### 封装层（proximo_api.py）结果格式化

```python
# 封装层：提取和格式化
assessment_result = {
    "success": True,
    "scale": "phq9",
    "total_score": 10.0,  # 直接提取
    "severity_level": "mild",  # 枚举 → 字符串
    "parsed_scores": [0, 1, 2, 1, 0, 2, 1, 1, 2],
    "flags": {
        "suicidal_ideation": True,  # 自动提取
        "suicidal_ideation_score": 2,
        "severe_symptoms": False
    },
    "suicidal_risk": "high",  # 自动提取
    "risk_level": "critical",  # 自动计算
    "clinical_interpretation": {...}  # 直接传递
}
```

#### 输出层（用户）

```python
# 用户接收：统一的字典格式
if result["success"]:
    print(result["total_score"])  # 10.0
    print(result["severity_level"])  # "mild"
    print(result["flags"]["suicidal_ideation"])  # True
    print(result["suicidal_risk"])  # "high"
```

---

## 封装层次解析

### 层次 1: 用户接口层（proximo_api.py）

**职责**：
- 提供简洁的 API 接口
- 参数验证和错误处理
- 结果格式化和信息提取

**关键函数**：
- `assess()`: 主入口函数
- `assess_sync()`: 同步版本（内部使用 `asyncio.run()`）
- `assess_phq9()`, `assess_gad7()`, `assess_pss10()`: 便捷函数

### 层次 2: 编排层（psychiatric_scales.py - AssessmentOrchestrator）

**职责**：
- 协调 Stage 1（校验）和 Stage 3（解释）
- 执行完整的评估流程
- 生成评估结果对象

**关键方法**：
- `conduct_phq9_assessment()`: 执行 PHQ-9 评估
- `conduct_gad7_assessment()`: 执行 GAD-7 评估
- `conduct_pss10_assessment()`: 执行 PSS-10 评估

### 层次 3: 校验层（psychiatric_scales.py - PsychiatricScaleValidator）

**职责**：
- 文本标准化和验证
- 数字提取和语义映射
- 容错处理

**关键方法**：
- `validate_phq9_response()`: 校验单个 PHQ-9 回答
- `validate_gad7_response()`: 校验单个 GAD-7 回答
- `validate_pss10_response()`: 校验单个 PSS-10 回答
- `calculate_pss10_score()`: 计算 PSS-10 总分（含反向计分）

### 层次 4: 解释层（psychiatric_scales.py - ClinicalInterpreter）

**职责**：
- 生成临床解释和建议
- 风险评估（自杀意念、严重症状）
- 基于严重度的建议生成

**关键方法**：
- `interpret_phq9_result()`: 生成 PHQ-9 临床解释
- `interpret_gad7_result()`: 生成 GAD-7 临床解释
- `interpret_pss10_result()`: 生成 PSS-10 临床解释

**注意**：`clinical_interpreter.py` 中的 `ClinicalInterpreter` 是一个更完整的解释器，提供：
- `assess_clinical_significance()`: 评估临床意义（需要基线数据）
- `analyze_longitudinal_trends()`: 纵向趋势分析
- `generate_clinical_summary()`: 生成临床摘要

**封装设计**：`proximo_api.py` 目前使用 `psychiatric_scales.py` 中的简化版 `ClinicalInterpreter`，因为：
- ✅ 简化版不需要基线数据（更适合独立评估场景）
- ✅ 简化版返回结果更直接（不需要复杂的临床意义评估）
- ✅ 简化版性能更好（不需要历史数据）

---

## 关键设计点

### 1. 单例模式：`_get_orchestrator()`

**设计原因**：
- `AssessmentOrchestrator` 是无状态的（只包含 validator 和 interpreter 实例）
- 避免重复创建实例，提高性能
- 减少内存占用

**实现**：
```python
_orchestrator = None  # 全局单例

def _get_orchestrator() -> AssessmentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AssessmentOrchestrator()
    return _orchestrator
```

### 2. 最小 Persona 对象：`_create_minimal_persona()`

**设计原因**：
- 用户只需要进行评估，不需要完整的 Persona 信息
- 减少用户的配置负担
- 自动生成必要的字段

**实现**：
```python
def _create_minimal_persona(persona_id: Optional[str] = None) -> Persona:
    persona_id = persona_id or f"assess_{uuid.uuid4().hex[:8]}"
    
    baseline = PersonaBaseline(
        name="Assessment User",
        age=30,
        # ... 默认值
    )
    
    state = PersonaState(
        persona_id=persona_id,
        simulation_day=0,
        last_assessment_day=-1
    )
    
    return Persona(baseline=baseline, state=state)
```

### 3. 统一结果格式：字典而非对象

**设计原因**：
- 字典易于序列化（JSON）
- 字典易于访问（`result["key"]`）
- 字典易于扩展（添加新字段）

**对比**：

```python
# 对象格式（底层）
result.total_score  # 需要知道对象结构
result.severity_level.value  # 需要知道是枚举类型
result.has_suicidal_ideation()  # 需要知道方法名

# 字典格式（封装层）
result["total_score"]  # 直接访问
result["severity_level"]  # 已经是字符串
result["flags"]["suicidal_ideation"]  # 直接访问
```

### 4. 自动信息提取：flags 和 risk_level

**设计原因**：
- 用户不需要手动从复杂对象中提取信息
- 提供统一的访问接口
- 自动计算风险级别

**实现**：
```python
# 自动提取风险标志
flags = {}
if isinstance(result, PHQ9Result):
    flags["suicidal_ideation"] = result.has_suicidal_ideation()
    flags["suicidal_ideation_score"] = result.suicidal_ideation_score

# 自动计算风险级别
if result.total_score >= 20:
    assessment_result["risk_level"] = "high"
elif result.total_score >= 10:
    assessment_result["risk_level"] = "moderate"
else:
    assessment_result["risk_level"] = "low"
```

### 5. 统一错误处理：success 标志

**设计原因**：
- 所有错误都返回统一格式
- 用户不需要捕获异常
- 错误信息清晰明确

**实现**：
```python
# 成功情况
{
    "success": True,
    "total_score": 10.0,
    ...
}

# 失败情况
{
    "success": False,
    "error": "PHQ9 requires 9 responses, got 7"
}
```

---

## 使用示例对比

### 使用底层 API（复杂）

```python
# 需要导入多个模块
from src.models.persona import Persona, PersonaBaseline, PersonaState
from src.assessment.psychiatric_scales import AssessmentOrchestrator

# 需要手动创建 Persona 对象
persona = Persona(
    baseline=PersonaBaseline(
        name="User",
        age=30,
        occupation="Unknown",
        background="Assessment",
        openness=0.5,
        conscientiousness=0.5,
        extraversion=0.5,
        agreeableness=0.5,
        neuroticism=0.5,
        baseline_phq9=0.0,
        baseline_gad7=0.0,
        baseline_pss10=0.0
    ),
    state=PersonaState(
        persona_id="user_123",
        simulation_day=0,
        last_assessment_day=-1
    )
)

# 需要手动创建 Orchestrator
orchestrator = AssessmentOrchestrator()

# 需要手动处理 None 和异常
try:
    result = await orchestrator.conduct_phq9_assessment(persona, responses)
    if result is None:
        print("Assessment failed")
    else:
        print(result.total_score)
        print(result.severity_level.value)  # 需要知道是枚举
        print(result.has_suicidal_ideation())  # 需要知道方法名
        print(result.clinical_interpretation["recommendations"])
except Exception as e:
    print(f"Error: {e}")
```

### 使用封装 API（简洁）

```python
# 只需导入一个函数
from src.assessment.proximo_api import assess

# 直接调用，无需配置
result = await assess("phq9", responses)

# 统一错误处理
if result["success"]:
    print(result["total_score"])  # 直接访问
    print(result["severity_level"])  # 已经是字符串
    print(result["flags"]["suicidal_ideation"])  # 直接访问
    print(result["clinical_interpretation"]["recommendations"])
else:
    print(result["error"])  # 统一错误格式
```

---

## 总结

### 封装的核心价值

1. **简化接口**：从复杂的对象创建和调用简化为一个函数调用
2. **隐藏复杂性**：用户不需要了解 `Persona`、`AssessmentOrchestrator` 等内部结构
3. **统一格式**：返回统一的字典格式，易于使用和序列化
4. **自动提取**：自动提取关键信息（风险标志、风险级别等）
5. **错误处理**：统一的错误处理机制

### 封装的设计原则

1. **单一职责**：`assess()` 函数只负责封装和格式化
2. **最小依赖**：只依赖 `AssessmentOrchestrator`，不直接依赖底层类
3. **向后兼容**：底层 API 保持不变，封装层可以独立演进
4. **易于扩展**：可以轻松添加新的功能（如缓存、日志等）

### 未来的扩展方向

1. **集成完整解释器**：可以选择性使用 `clinical_interpreter.py` 中的完整解释器
2. **批量评估**：支持一次评估多个量表
3. **结果缓存**：缓存评估结果，提高性能
4. **异步优化**：支持并发评估多个用户

---

**编写日期**: 2025-01-XX  
**最后更新**: 2025-01-XX


