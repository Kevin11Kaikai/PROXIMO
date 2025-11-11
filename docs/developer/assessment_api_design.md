# Assessment API 设计分析

## 代码结构分析

### ✅ 你的分析是准确的！

## 核心组件位置

### A. `src/assessment/psychiatric_scales.py` - 量表与打分

#### 1. **PsychiatricScaleValidator** - 校验器
```python
validate_phq9_response(response: str, question_index: int) -> Tuple[bool, Optional[int]]
validate_gad7_response(response: str, question_index: int) -> Tuple[bool, Optional[int]]
validate_pss10_response(response: str, question_index: int) -> Tuple[bool, Optional[int]]
```

**功能**:
- ✅ 自然语言到分值的映射（"完全没有" → 0, "几天" → 1, "超过一半天" → 2, "几乎每天" → 3）
- ✅ 鲁棒性处理（同义词、大小写、数字提取）
- ✅ 范围验证（PHQ-9/GAD-7: 0-3, PSS-10: 0-4）

#### 2. **AssessmentOrchestrator** - 编排器
```python
async def conduct_phq9_assessment(persona: Persona, responses: List[str]) -> Optional[PHQ9Result]
async def conduct_gad7_assessment(persona: Persona, responses: List[str]) -> Optional[GAD7Result]
async def conduct_pss10_assessment(persona: Persona, responses: List[str]) -> Optional[PSS10Result]
```

**流程**:
1. 对每个回答进行校验 → 得到 0-3 分
2. 累加得到 `total_score`
3. 依据阈值映射严重度（`calculate_severity()`）
4. 提取特殊字段（PHQ-9 Item 9 → `suicidal_ideation_score`）
5. 生成结构化结果对象

#### 3. **结果数据结构**

**PHQ9Result**:
```python
- total_score: int (0-27)
- severity_level: SeverityLevel (MINIMAL/MILD/MODERATE/SEVERE)
- suicidal_ideation_score: int (0-3)  # Item 9, 索引 8
- parsed_scores: List[int]  # 每题分数
- raw_responses: List[str]  # 原始回答
- clinical_interpretation: Dict[str, Any]  # 临床解释
```

**重要方法**:
```python
PHQ9Result.has_suicidal_ideation() -> bool  # suicidal_ideation_score >= 2
PHQ9Result.calculate_severity(total_score: float) -> SeverityLevel
```

### B. `src/assessment/clinical_interpreter.py` - 临床解释与预警

#### 1. **ClinicalInterpreter**（完整版）

**核心方法**:
```python
assess_clinical_significance(
    current_result: AssessmentResult,
    baseline_result: Optional[AssessmentResult] = None,
    previous_results: Optional[List[AssessmentResult]] = None
) -> Dict[str, Any]
```

**风险评估**:
- ✅ **自杀意念监测**: 检查 `result.suicidal_ideation_score >= 2`
- ✅ **严重度阈值**: PHQ-9 ≥20, GAD-7 ≥20, PSS-10 ≥25
- ✅ **快速恶化**: 一周内增加 ≥10 分
- ✅ **风险等级**: critical / high / moderate / low

**输出结构**:
```python
{
    "risk_level": "critical|high|moderate|low",
    "risk_factors": ["suicidal_ideation", "severe_symptoms", ...],
    "suicidal_risk": bool,
    "clinical_recommendations": [...],
    "monitoring_priority": "immediate|urgent|elevated|routine"
}
```

## ⚠️ 需要注意的细节

### 1. 两个 ClinicalInterpreter 类

**问题**: 
- `psychiatric_scales.py` 中有一个简化版的 `ClinicalInterpreter`
- `clinical_interpreter.py` 中有完整版的 `ClinicalInterpreter`

**解决方案**:
- 导入时已做别名处理（见 `__init__.py`）
- **建议封装时使用 `clinical_interpreter.py` 中的完整版**

### 2. Persona 依赖

**当前设计**:
```python
AssessmentOrchestrator.conduct_phq9_assessment(persona: Persona, responses: List[str])
```

**封装建议**:
```python
# 简化接口，不需要完整的 Persona 对象
def assess(scale: str, responses: List[str], **kwargs) -> AssessmentResult:
    # 只需要评估 ID 和基本信息
    # persona_id = kwargs.get("persona_id", "unknown")
    # simulation_day = kwargs.get("simulation_day", 0)
```

### 3. 自杀意念检查（Item 9）

**位置**: `validated_scores[8]` （第 9 题，0-indexed）

**阈值**: `≥ 2` 视为高风险

**检查点**:
1. `PHQ9Result.has_suicidal_ideation()` 
2. `ClinicalInterpreter._assess_risk_level()` 
3. `config/experiments/clinical_thresholds.yaml`: `phq9_item_9_threshold: 2`

## 封装建议

### 目标接口

```python
# proximo/assessment/__init__.py
from proximo.assessment.assess import assess

result = assess(
    scale="phq9",
    responses=["0", "1", "2", "1", "0", "1", "2", "1", "2"],  # 9 个回答
    persona_id="persona_001",  # 可选
    simulation_day=7  # 可选
)

# 结果访问
result.total_score  # 总分
result.severity_level  # 严重度
result.suicidal_ideation_score  # Item 9 分数
result.has_suicidal_ideation()  # 是否触发自杀意念
result.clinical_interpretation  # 临床解释
```

### 实现路径

```python
# proximo/assessment/assess.py
from src.assessment.psychiatric_scales import (
    PsychiatricScaleValidator,
    AssessmentOrchestrator
)
from src.assessment.clinical_interpreter import ClinicalInterpreter
from src.models.persona import Persona, PersonaBaseline, PersonaState

async def assess(
    scale: str,
    responses: List[str],
    persona_id: str = "unknown",
    simulation_day: int = 0,
    **kwargs
) -> AssessmentResult:
    """统一的评估接口"""
    
    # 创建最小化的 Persona 对象（如果不需要完整功能）
    # 或者重构 AssessmentOrchestrator 使其不依赖 Persona
    
    orchestrator = AssessmentOrchestrator()
    clinical_interpreter = ClinicalInterpreter()
    
    # 创建临时 Persona（仅用于评估）
    minimal_persona = create_minimal_persona(persona_id, simulation_day)
    
    # 根据 scale 类型调用对应方法
    if scale.lower() == "phq9":
        result = await orchestrator.conduct_phq9_assessment(minimal_persona, responses)
    elif scale.lower() == "gad7":
        result = await orchestrator.conduct_gad7_assessment(minimal_persona, responses)
    elif scale.lower() == "pss10":
        result = await orchestrator.conduct_pss10_assessment(minimal_persona, responses)
    else:
        raise ValueError(f"Unknown scale: {scale}")
    
    # 添加完整风险评估（如果提供了基线或历史数据）
    if "baseline_result" in kwargs or "previous_results" in kwargs:
        clinical_assessment = clinical_interpreter.assess_clinical_significance(
            result,
            baseline_result=kwargs.get("baseline_result"),
            previous_results=kwargs.get("previous_results", [])
        )
        result.clinical_assessment = clinical_assessment
    
    return result
```

### 安全检查层（Proximo Safety Layer）

```python
def check_critical_risks(result: PHQ9Result) -> Dict[str, Any]:
    """检查关键风险，触发安全协议"""
    
    alerts = []
    
    # 1. 自杀意念检查（Item 9）
    if result.has_suicidal_ideation():
        alerts.append({
            "type": "suicidal_ideation",
            "severity": "critical",
            "item": 9,
            "score": result.suicidal_ideation_score,
            "action": "trigger_cssrs_protocol"  # 切换到 C-SSRS
        })
    
    # 2. 严重度检查
    if result.severity_level == SeverityLevel.SEVERE:
        alerts.append({
            "type": "severe_symptoms",
            "severity": "high",
            "total_score": result.total_score,
            "action": "immediate_clinical_referral"
        })
    
    # 3. 快速恶化检查（需要历史数据）
    # ...
    
    return {
        "has_critical_risk": len(alerts) > 0,
        "alerts": alerts,
        "next_action": alerts[0]["action"] if alerts else "continue_monitoring"
    }
```

## 总结

### ✅ 你的分析准确点

1. ✅ **psychiatric_scales.py** 确实包含校验器、编排器和基本解释器
2. ✅ **clinical_interpreter.py** 包含完整的风险评估和预警
3. ✅ **Item 9 自杀意念监测**在多个位置实现（阈值 ≥2）
4. ✅ **流程**: 校验 → 打分 → 严重度 → 解释
5. ✅ **结果对象**结构清晰（PHQ9Result, GAD7Result, PSS10Result）

### ⚠️ 需要注意

1. ⚠️ **两个 ClinicalInterpreter** - 使用完整版（clinical_interpreter.py）
2. ⚠️ **Persona 依赖** - 可能需要创建最小化 Persona 或重构接口
3. ⚠️ **异步接口** - 当前都是 async，封装时需要考虑

### 🎯 封装建议

1. **简化接口**: `assess(scale, responses)` 不强制需要完整 Persona
2. **安全层**: 立即检查 `has_suicidal_ideation()`，触发 C-SSRS 协议
3. **统一返回**: 所有量表返回统一的结果接口
4. **可选增强**: 支持基线对比、趋势分析等高级功能

你的分析方向完全正确！🎉

