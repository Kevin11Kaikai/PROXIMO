# Risk Mapping 实现逻辑详细分析

本文档详细分析 `src/risk/mapping.py` 的实现逻辑，包括数据流转、算法设计和决策过程。

---

## 📋 目录

1. [整体架构](#整体架构)
2. [核心数据结构](#核心数据结构)
3. [数据流转过程](#数据流转过程)
4. [关键函数详解](#关键函数详解)
5. [算法设计](#算法设计)
6. [配置加载机制](#配置加载机制)
7. [错误处理策略](#错误处理策略)

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Risk Mapping 架构                          │
└─────────────────────────────────────────────────────────────┘

输入层
  ↓
评估结果 (assess() 输出)
  {
    "severity_level": "moderate",
    "flags": {"suicidal_ideation": False, ...}
  }
  ↓
┌─────────────────────────────────────────────────────────┐
│ 【风险映射层】src/risk/mapping.py                        │
│                                                          │
│  Stage 1: 严重度标准化                                    │
│  normalize_sev(severity) → "moderate"                   │
│                                                          │
│  Stage 2: 严重度 → 风险分数映射                           │
│  severity_to_risk("moderate") → 0.60                    │
│                                                          │
│  Stage 3: 风险分数 → Rigidness 转换                      │
│  risk_to_rigid(0.60) → 0.60                             │
│                                                          │
│  Stage 4: 危机检测（硬锁定判断）                           │
│  is_hard_lock(severity, flags) → False                  │
│                                                          │
│  Stage 5: 综合计算                                        │
│  compute_rigid_from_severity("moderate") → 0.60         │
└─────────────────────────────────────────────────────────┘
  ↓
输出层
  {
    "rigid_score": 0.60,
    "is_crisis": False
  }
```

---

## 核心数据结构

### RiskMappingConfig (dataclass)

```python
@dataclass
class RiskMappingConfig:
    severity_to_risk: Dict[str, float]  # 严重度 → 风险分数映射表
    a: float                             # 线性变换系数
    b: float                             # 线性变换截距
    crisis_item9_lock: bool              # 是否启用 Item9 硬锁定
    crisis_severity_lock: set            # 触发硬锁定的严重度级别集合
```

**设计原因**：
- ✅ **类型安全**：使用 dataclass 确保配置结构清晰
- ✅ **不可变**：配置一旦加载，不应被修改
- ✅ **易于扩展**：可以轻松添加新字段

**默认配置 (DEFAULT)**：
```python
DEFAULT = RiskMappingConfig(
    severity_to_risk={
        "minimal": 0.15,      # 最低风险
        "mild": 0.35,         # 轻度风险
        "moderate": 0.60,     # 中等风险
        "severe": 0.95,       # 严重风险
    },
    a=1.0,                    # 线性变换：rigid = 1.0 * risk + 0.0
    b=0.0,                    # 即 rigid = risk（直接映射）
    crisis_item9_lock=True,   # 启用自杀意念硬锁定
    crisis_severity_lock={"severe"},  # severe 级别触发硬锁定
)
```

**映射表设计思路**：
- 范围：0.15 - 0.95（避免极端值 0.0 和 1.0）
- 间隔：不均匀分布，严重度越高，间隔越大
- 保留空间：0.0 - 0.15 和 0.95 - 1.0 用于特殊场景

---

## 数据流转过程

### 完整流程示例

```
输入: severity = "moderate", flags = {"suicidal_ideation": False}

    ↓
【Stage 1: 严重度标准化】
normalize_sev("moderate")
    ├─ strip() → "moderate"
    ├─ lower() → "moderate"
    └─ replace(" ", "_") → "moderate"
    ↓
输出: "moderate"

    ↓
【Stage 2: 严重度 → 风险分数】
severity_to_risk("moderate", cfg)
    ├─ normalize_sev("moderate") → "moderate"
    ├─ cfg.severity_to_risk.get("moderate") → 0.60
    └─ 如果不存在，返回 cfg.severity_to_risk["moderate"] → 0.60
    ↓
输出: 0.60

    ↓
【Stage 3: 风险分数 → Rigidness】
risk_to_rigid(0.60, cfg)
    ├─ x = cfg.a * 0.60 + cfg.b
    ├─ x = 1.0 * 0.60 + 0.0 = 0.60
    ├─ max(0.0, 0.60) → 0.60
    └─ min(1.0, 0.60) → 0.60
    ↓
输出: 0.60

    ↓
【Stage 4: 危机检测】
is_hard_lock("moderate", flags, cfg)
    ├─ 检查自杀意念：
    │  ├─ flags.get("suicidal_ideation") → False
    │  ├─ flags.get("suicidal_ideation_score", 0) → 0
    │  └─ item9 = False or (0 >= 2) → False
    │  └─ cfg.crisis_item9_lock and False → False（不触发）
    │
    ├─ 检查严重度：
    │  ├─ normalize_sev("moderate") → "moderate"
    │  └─ "moderate" in {"severe"} → False（不触发）
    │
    └─ 返回 False
    ↓
输出: False

    ↓
【Stage 5: 综合计算】
compute_rigid_from_severity("moderate")
    ├─ 调用 severity_to_risk("moderate") → 0.60
    ├─ 调用 risk_to_rigid(0.60) → 0.60
    └─ 返回 0.60
    ↓
输出: 0.60
```

---

## 关键函数详解

### 1. `normalize_sev(sev: str) -> str`

**作用**：标准化严重度字符串，确保一致性

**实现逻辑**：

```python
def normalize_sev(sev: str) -> str:
    return sev.strip().lower().replace(" ", "_")
```

**处理步骤**：
1. `strip()`: 去除首尾空格
2. `lower()`: 转为小写
3. `replace(" ", "_")`: 空格替换为下划线

**示例**：
```python
normalize_sev("Minimal")        → "minimal"
normalize_sev("  MILD  ")       → "mild"
normalize_sev("moderately severe") → "moderately_severe"
```

**设计原因**：
- ✅ **容错性**：处理用户输入的大小写和空格变化
- ✅ **一致性**：确保所有严重度字符串格式统一
- ✅ **兼容性**：支持 "moderately severe" 这样的多词格式

---

### 2. `severity_to_risk(severity: str, cfg: RiskMappingConfig) -> float`

**作用**：将严重度级别映射到风险分数（0.0 - 1.0）

**实现逻辑**：

```python
def severity_to_risk(severity: str, cfg: RiskMappingConfig) -> float:
    normalized = normalize_sev(severity)
    return cfg.severity_to_risk.get(normalized, cfg.severity_to_risk["moderate"])
```

**处理流程**：

```
输入: severity = "moderate", cfg = DEFAULT

步骤 1: 标准化严重度
    normalized = normalize_sev("moderate") → "moderate"

步骤 2: 查找映射表
    cfg.severity_to_risk.get("moderate", ...)
    ├─ 如果存在 → 返回对应的风险分数 (0.60)
    └─ 如果不存在 → 返回默认值 ("moderate" 的风险分数)

步骤 3: 返回风险分数
    返回 0.60
```

**映射表**：
```python
{
    "minimal": 0.15,   # 15% 风险
    "mild": 0.35,      # 35% 风险
    "moderate": 0.60,  # 60% 风险
    "severe": 0.95,    # 95% 风险
}
```

**设计考虑**：

1. **为什么使用字典查找？**
   - ✅ O(1) 时间复杂度
   - ✅ 易于配置和修改
   - ✅ 支持任意严重度级别

2. **为什么默认值使用 "moderate"？**
   - ✅ 保守策略：未知严重度使用中等风险
   - ✅ 避免过度反应：不会误判为高风险
   - ✅ 避免遗漏：不会误判为低风险

3. **为什么分数范围是 0.15 - 0.95？**
   - ✅ 避免极端值：0.0 和 1.0 保留给特殊场景
   - ✅ 保留调整空间：可以区分更细微的风险级别
   - ✅ 符合临床实践：真实风险评估很少是 0% 或 100%

---

### 3. `risk_to_rigid(risk: float, cfg: RiskMappingConfig) -> float`

**作用**：将风险分数转换为 Rigidness 分数（通过线性变换）

**实现逻辑**：

```python
def risk_to_rigid(risk: float, cfg: RiskMappingConfig) -> float:
    x = cfg.a * float(risk) + cfg.b
    return max(0.0, min(1.0, x))
```

**数学公式**：

```
rigid_score = a * risk_score + b

其中：
- a: 线性变换系数（默认 1.0）
- b: 线性变换截距（默认 0.0）
- 结果限制在 [0.0, 1.0] 范围内
```

**处理流程**：

```
输入: risk = 0.60, cfg = DEFAULT (a=1.0, b=0.0)

步骤 1: 线性变换
    x = cfg.a * float(risk) + cfg.b
    x = 1.0 * 0.60 + 0.0
    x = 0.60

步骤 2: 下界限制
    max(0.0, 0.60) → 0.60

步骤 3: 上界限制
    min(1.0, 0.60) → 0.60

输出: 0.60
```

**设计考虑**：

1. **为什么使用线性变换？**
   - ✅ **简单直观**：易于理解和调整
   - ✅ **灵活可配**：可以通过 a 和 b 调整映射关系
   - ✅ **可扩展**：未来可以改为非线性变换

2. **为什么需要边界限制？**
   - ✅ **数值安全**：确保结果在有效范围内
   - ✅ **防止溢出**：避免计算结果超出 [0.0, 1.0]
   - ✅ **容错处理**：即使配置错误，也能保证有效输出

3. **默认配置 a=1.0, b=0.0 的含义**
   - ✅ **直接映射**：rigid_score = risk_score
   - ✅ **简化逻辑**：默认情况下不需要转换
   - ✅ **可调整**：可以通过配置文件修改变换关系

**变换示例**：

```python
# 默认配置 (a=1.0, b=0.0)
risk_to_rigid(0.60) → 0.60  # 直接映射

# 如果需要更保守的映射 (a=0.8, b=0.1)
risk_to_rigid(0.60) → 0.58  # 略微降低

# 如果需要更激进的映射 (a=1.2, b=-0.1)
risk_to_rigid(0.60) → 0.62  # 略微提高
```

---

### 4. `compute_rigid_from_severity(severity: str, cfg: Optional[RiskMappingConfig] = None) -> float`

**作用**：从严重度级别直接计算 Rigidness 分数（综合函数）

**实现逻辑**：

```python
def compute_rigid_from_severity(
    severity: str, cfg: Optional[RiskMappingConfig] = None
) -> float:
    if cfg is None:
        cfg = load_config()
    risk = severity_to_risk(severity, cfg)
    return risk_to_rigid(risk, cfg)
```

**处理流程**：

```
输入: severity = "moderate", cfg = None

步骤 1: 加载配置（如果需要）
    if cfg is None:
        cfg = load_config()  # 从配置文件加载

步骤 2: 严重度 → 风险分数
    risk = severity_to_risk("moderate", cfg)
    risk = 0.60

步骤 3: 风险分数 → Rigidness
    rigid = risk_to_rigid(0.60, cfg)
    rigid = 0.60

输出: 0.60
```

**设计考虑**：

1. **为什么提供可选参数 cfg？**
   - ✅ **灵活性**：可以传入自定义配置
   - ✅ **性能**：避免重复加载配置
   - ✅ **测试友好**：测试时可以传入测试配置

2. **为什么组合两个函数？**
   - ✅ **封装复杂性**：用户只需调用一个函数
   - ✅ **代码复用**：内部复用现有函数
   - ✅ **易于维护**：修改逻辑只需修改一处

**使用示例**：

```python
# 使用默认配置
rigid = compute_rigid_from_severity("moderate")  # 0.60

# 使用自定义配置
custom_cfg = RiskMappingConfig(...)
rigid = compute_rigid_from_severity("moderate", custom_cfg)  # 自定义结果
```

---

### 5. `is_hard_lock(severity: str, flags: Dict[str, Any], cfg: Optional[RiskMappingConfig] = None) -> bool`

**作用**：检测是否应该触发硬锁定（危机模式）

**实现逻辑**：

```python
def is_hard_lock(
    severity: str, flags: Dict[str, Any], cfg: Optional[RiskMappingConfig] = None
) -> bool:
    if cfg is None:
        cfg = load_config()
    
    # 检查自杀意念（Item 9）
    item9 = bool(
        flags.get("suicidal_ideation", False)
        or flags.get("suicidal_ideation_score", 0) >= 2
    )
    if cfg.crisis_item9_lock and item9:
        return True
    
    # 检查严重度级别
    normalized_sev = normalize_sev(severity)
    return normalized_sev in cfg.crisis_severity_lock
```

**处理流程**：

```
输入: severity = "mild", flags = {"suicidal_ideation": True}, cfg = DEFAULT

步骤 1: 加载配置（如果需要）
    cfg = load_config()

步骤 2: 检查自杀意念（Item 9）
    ├─ flags.get("suicidal_ideation", False) → True
    ├─ flags.get("suicidal_ideation_score", 0) → 0
    ├─ item9 = True or (0 >= 2) → True
    ├─ cfg.crisis_item9_lock → True
    └─ cfg.crisis_item9_lock and True → True
    ↓
    返回 True（触发硬锁定）

--- 如果 Item 9 检查未触发 ---

步骤 3: 检查严重度级别
    ├─ normalized_sev = normalize_sev(severity) → "mild"
    └─ "mild" in {"severe"} → False
    ↓
    返回 False（不触发硬锁定）
```

**设计考虑**：

1. **为什么先检查自杀意念？**
   - ✅ **优先级最高**：自杀意念是最紧急的风险
   - ✅ **安全优先**：即使严重度不高，也要触发危机模式
   - ✅ **临床实践**：符合临床风险评估标准

2. **为什么检查两个字段？**
   - ✅ **容错性**：支持不同的字段名
   - ✅ **兼容性**：适配不同的数据格式
   - ✅ **鲁棒性**：即使字段缺失也能正常工作

3. **硬锁定的设计思路**
   - ✅ **不可覆盖**：一旦触发，rigidness = 1.0
   - ✅ **安全第一**：宁可误报，不可漏报
   - ✅ **可配置**：可以通过配置禁用或调整

**触发条件优先级**：

```
优先级 1: 自杀意念（最高优先级）
    ├─ flags["suicidal_ideation"] == True
    └─ flags["suicidal_ideation_score"] >= 2

优先级 2: 严重度级别
    └─ severity in {"severe"}
```

**使用示例**：

```python
# 场景 1: 自杀意念触发硬锁定
flags = {"suicidal_ideation": True}
is_crisis = is_hard_lock("mild", flags)  # True（即使严重度是 mild）

# 场景 2: 严重度触发硬锁定
flags = {}
is_crisis = is_hard_lock("severe", flags)  # True

# 场景 3: 不触发硬锁定
flags = {"suicidal_ideation": False}
is_crisis = is_hard_lock("moderate", flags)  # False
```

---

### 6. `load_config() -> RiskMappingConfig`

**作用**：从配置文件加载风险映射配置

**实现逻辑**：

```python
def load_config() -> RiskMappingConfig:
    try:
        config = experiment_config.get_config("risk_mapping")
        if config:
            sev = config.get("severity_to_risk_score", {})
            rigid = config.get("rigid_transform", {})
            crises = config.get("crisis_rules", {})
            
            return RiskMappingConfig(
                severity_to_risk={**DEFAULT.severity_to_risk, **sev},
                a=float(rigid.get("a", DEFAULT.a)),
                b=float(rigid.get("b", DEFAULT.b)),
                crisis_item9_lock=bool(
                    crises.get("phq9_item9_flag_to_hard_lock", DEFAULT.crisis_item9_lock)
                ),
                crisis_severity_lock=set(
                    crises.get("severity_hard_lock", list(DEFAULT.crisis_severity_lock))
                ),
            )
    except Exception as e:
        logger.warning(f"Failed to load risk_mapping config, using defaults: {e}")
    
    return DEFAULT
```

**处理流程**：

```
步骤 1: 尝试加载配置
    config = experiment_config.get_config("risk_mapping")
    ├─ 如果配置文件存在 → 返回配置字典
    └─ 如果配置文件不存在 → 返回 {}

步骤 2: 提取配置项
    ├─ sev = config.get("severity_to_risk_score", {})
    ├─ rigid = config.get("rigid_transform", {})
    └─ crises = config.get("crisis_rules", {})

步骤 3: 合并默认值和配置值
    ├─ severity_to_risk = {**DEFAULT.severity_to_risk, **sev}
    │  └─ 配置文件的值覆盖默认值
    ├─ a = rigid.get("a", DEFAULT.a)
    │  └─ 如果配置中没有，使用默认值
    └─ ... (其他字段类似)

步骤 4: 返回配置对象
    return RiskMappingConfig(...)

--- 如果加载失败 ---

步骤 5: 返回默认配置
    return DEFAULT
```

**设计考虑**：

1. **为什么使用字典合并？**
   - ✅ **部分覆盖**：只需要覆盖需要修改的字段
   - ✅ **向后兼容**：新增字段不会破坏现有配置
   - ✅ **易于维护**：默认值作为基础，配置作为覆盖

2. **为什么使用 try-except？**
   - ✅ **容错性**：配置文件错误不影响程序运行
   - ✅ **降级策略**：使用默认配置作为后备
   - ✅ **日志记录**：记录错误但不中断程序

3. **配置加载优先级**
   ```
   配置文件值 > 默认值
   ```

**配置合并示例**：

```python
# 默认配置
DEFAULT.severity_to_risk = {
    "minimal": 0.15,
    "mild": 0.35,
    "moderate": 0.60,
    "severe": 0.95,
}

# 配置文件
config = {
    "severity_to_risk_score": {
        "minimal": 0.10,  # 覆盖默认值
        # mild, moderate, severe 使用默认值
    }
}

# 合并结果
merged = {
    "minimal": 0.10,      # 来自配置文件
    "mild": 0.35,         # 来自默认值
    "moderate": 0.60,     # 来自默认值
    "severe": 0.95,       # 来自默认值
}
```

---

## 算法设计

### 严重度到风险分数的映射算法

**映射表设计**：

```python
severity_to_risk = {
    "minimal": 0.15,      # 区间: [0.00, 0.15]
    "mild": 0.35,         # 区间: [0.15, 0.35]
    "moderate": 0.60,     # 区间: [0.35, 0.60]
    "severe": 0.95,       # 区间: [0.60, 0.95]
}
```

**设计思路**：

1. **非线性映射**
   - 严重度越高，风险分数增长越快
   - 符合临床实践：严重症状的风险是指数级增长的

2. **保留边界**
   - 0.0 - 0.15: 保留给特殊情况（如完全正常）
   - 0.95 - 1.0: 保留给极端情况（硬锁定使用 1.0）

3. **间隔设计**
   - minimal → mild: +0.20
   - mild → moderate: +0.25
   - moderate → severe: +0.35
   - 间隔递增，反映风险的非线性增长

### 线性变换算法

**公式**：

```
rigid_score = clamp(a * risk_score + b, 0.0, 1.0)
```

**默认参数**：
- `a = 1.0`: 直接映射
- `b = 0.0`: 无偏移

**变换示例**：

```python
# 默认配置：rigid_score = risk_score
risk_to_rigid(0.60) → 0.60

# 更保守：rigid_score = 0.8 * risk_score + 0.1
# 0.60 → 0.58（略微降低）

# 更激进：rigid_score = 1.2 * risk_score - 0.1
# 0.60 → 0.62（略微提高）
```

### 硬锁定检测算法

**检测逻辑**：

```
IF (crisis_item9_lock AND item9_flag) THEN
    RETURN True
END IF

IF (severity IN crisis_severity_lock) THEN
    RETURN True
END IF

RETURN False
```

**优先级**：
1. **自杀意念**（最高优先级）
2. **严重度级别**（次优先级）

**设计原因**：
- ✅ **安全优先**：自杀意念是最紧急的风险
- ✅ **可配置**：可以通过配置调整触发条件
- ✅ **明确清晰**：逻辑简单，易于理解和维护

---

## 配置加载机制

### 配置文件结构

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
  severity_hard_lock:
    - severe
```

### 加载流程

```
1. experiment_config.get_config("risk_mapping")
   ├─ 查找 config/experiments/risk_mapping.yaml
   ├─ 解析 YAML 文件
   └─ 返回配置字典

2. 提取配置项
   ├─ severity_to_risk_score → sev
   ├─ rigid_transform → rigid
   └─ crisis_rules → crises

3. 合并默认值和配置值
   ├─ {**DEFAULT.severity_to_risk, **sev}
   └─ 使用配置值覆盖默认值

4. 创建 RiskMappingConfig 对象
   └─ 返回配置对象
```

### 容错机制

**如果配置文件缺失或无效**：
- ✅ 返回 `DEFAULT` 配置
- ✅ 记录警告日志
- ✅ 程序继续运行

**如果配置项缺失**：
- ✅ 使用默认值
- ✅ 不中断程序
- ✅ 记录警告（如果需要）

---

## 错误处理策略

### 1. 严重度标准化错误

**场景**：输入为 `None` 或空字符串

**处理**：
```python
def normalize_sev(sev: str) -> str:
    return sev.strip().lower().replace(" ", "_")
```

**问题**：如果 `sev` 是 `None`，会抛出 `AttributeError`

**改进建议**（可选）：
```python
def normalize_sev(sev: str) -> str:
    if not sev:
        return "moderate"  # 默认值
    return sev.strip().lower().replace(" ", "_")
```

### 2. 映射查找失败

**场景**：严重度级别不在映射表中

**处理**：
```python
return cfg.severity_to_risk.get(normalized, cfg.severity_to_risk["moderate"])
```

**策略**：
- ✅ 使用 `get()` 方法，提供默认值
- ✅ 默认值使用 `"moderate"`（保守策略）
- ✅ 不会抛出异常

### 3. 配置加载失败

**场景**：配置文件不存在、格式错误、权限问题

**处理**：
```python
try:
    config = experiment_config.get_config("risk_mapping")
    # ...
except Exception as e:
    logger.warning(f"Failed to load risk_mapping config, using defaults: {e}")
    return DEFAULT
```

**策略**：
- ✅ 捕获所有异常
- ✅ 记录警告日志
- ✅ 返回默认配置
- ✅ 程序继续运行

### 4. 数值计算错误

**场景**：配置值不是数字、超出范围

**处理**：
```python
a = float(rigid.get("a", DEFAULT.a))
b = float(rigid.get("b", DEFAULT.b))
```

**策略**：
- ✅ 使用 `float()` 转换，如果失败会抛出异常（被外层 try-except 捕获）
- ✅ 提供默认值作为后备
- ✅ 边界限制在 `risk_to_rigid()` 中处理

---

## 完整使用示例

### 示例 1: 正常流程

```python
from src.risk.mapping import compute_rigid_from_severity, is_hard_lock

# 输入
severity = "moderate"
flags = {"suicidal_ideation": False}

# 计算 Rigidness
rigid = compute_rigid_from_severity(severity)
# 内部流程:
#   1. normalize_sev("moderate") → "moderate"
#   2. severity_to_risk("moderate") → 0.60
#   3. risk_to_rigid(0.60) → 0.60
# 结果: 0.60

# 检查硬锁定
is_crisis = is_hard_lock(severity, flags)
# 内部流程:
#   1. 检查自杀意念 → False
#   2. 检查严重度 → "moderate" not in {"severe"} → False
# 结果: False
```

### 示例 2: 危机场景

```python
# 输入
severity = "mild"
flags = {"suicidal_ideation": True}

# 计算 Rigidness（正常流程）
rigid = compute_rigid_from_severity(severity)  # 0.35

# 检查硬锁定
is_crisis = is_hard_lock(severity, flags)
# 内部流程:
#   1. 检查自杀意念 → True
#   2. cfg.crisis_item9_lock and True → True
#   3. 返回 True（提前返回，不检查严重度）
# 结果: True

# 注意：即使 rigid = 0.35（低风险），硬锁定也会触发
```

### 示例 3: 自定义配置

```python
from src.risk.mapping import RiskMappingConfig, compute_rigid_from_severity

# 创建自定义配置
custom_cfg = RiskMappingConfig(
    severity_to_risk={
        "minimal": 0.10,   # 更保守
        "mild": 0.30,
        "moderate": 0.50,
        "severe": 0.90,
    },
    a=0.8,  # 降低 rigidness
    b=0.1,
    crisis_item9_lock=True,
    crisis_severity_lock={"severe"},
)

# 使用自定义配置
rigid = compute_rigid_from_severity("moderate", custom_cfg)
# 内部流程:
#   1. severity_to_risk("moderate", custom_cfg) → 0.50
#   2. risk_to_rigid(0.50, custom_cfg) → 0.8 * 0.50 + 0.1 = 0.50
# 结果: 0.50（比默认配置更低）
```

---

## 性能考虑

### 时间复杂度

- `normalize_sev()`: O(n)，n 是字符串长度
- `severity_to_risk()`: O(1)，字典查找
- `risk_to_rigid()`: O(1)，简单计算
- `is_hard_lock()`: O(1)，集合查找
- `compute_rigid_from_severity()`: O(1)，组合调用

**总体复杂度**：O(1)（常数时间）

### 空间复杂度

- 配置对象：O(1)（固定大小）
- 映射表：O(k)，k 是严重度级别数量（通常 k=4）

**总体复杂度**：O(1)（常数空间）

### 优化建议

1. **配置缓存**：`load_config()` 可以缓存配置对象，避免重复加载
2. **单例模式**：可以考虑使用单例模式管理配置对象
3. **延迟加载**：只在第一次调用时加载配置

---

## 总结

### 核心设计原则

1. **分层设计**：每个函数职责单一，易于测试和维护
2. **配置驱动**：所有阈值和规则都可通过配置文件调整
3. **容错处理**：配置缺失或错误时使用默认值
4. **安全优先**：硬锁定检测优先级最高，确保不会漏报

### 关键算法

1. **严重度标准化**：处理输入格式变化
2. **字典映射**：O(1) 时间复杂度的查找
3. **线性变换**：灵活的数值转换
4. **优先级检测**：多条件判断的清晰逻辑

### 设计优势

- ✅ **模块化**：每个函数独立，易于测试
- ✅ **可配置**：所有参数都可以通过配置文件调整
- ✅ **容错性**：配置缺失或错误不影响程序运行
- ✅ **性能**：O(1) 时间复杂度，适合高频调用
- ✅ **可扩展**：易于添加新的严重度级别或检测规则

---

**编写日期**: 2025-01-XX  
**最后更新**: 2025-01-XX


