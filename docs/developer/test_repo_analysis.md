# test_repo.py 测试分析

## 📋 测试概览

`test_repo.py` 包含 **7 个测试用例**，用于验证 `AssessmentRepo` 类的持久化和历史记录功能。`AssessmentRepo` 使用 SQLite 数据库存储评估结果、路由决策和政策执行结果。

---

## 🧪 测试用例详细分析

### 1. `test_save_assessment` - 测试保存评估记录

**目的**: 验证基本的评估记录保存功能，包括评估结果、路由决策和政策结果

**测试步骤**:
```python
user_id = "test_user_1"
assessment = {
    "success": True,
    "scale": "phq9",
    "total_score": 12.0,
    "severity_level": "moderate",
    "flags": {"suicidal_ideation": False}
}
decision = {
    "route": "medium",
    "rigid_score": 0.6,
    "reason": "medium_risk"
}
result = {
    "policy": "medium",
    "response": "I understand this is important.",
    "temperature": 0.6
}

await temp_repo.save(user_id, assessment, decision, result)
history = await temp_repo.history(user_id, limit=1)
```

**验证点**:
- ✅ 保存后历史记录数量为 1
- ✅ `user_id` 正确保存
- ✅ `scale` 为 `"phq9"`
- ✅ `score` 为 `12.0`
- ✅ `severity` 为 `"moderate"`
- ✅ `route` 为 `"medium"`
- ✅ `rigid` 为 `0.6`

**对应源码** (`repo.py:79-145`):
```python
async def save(
    self,
    user_id: str,
    assessment: Dict[str, Any],
    decision: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None
) -> None:
    # 提取字段
    scale = assessment.get("scale", "unknown")
    score = assessment.get("total_score", 0.0)
    severity = assessment.get("severity_level", "unknown")
    rigid = decision.get("rigid_score", 0.0)
    route = decision.get("route", "unknown")
    
    # 提取 flags 并序列化为 JSON
    flags = assessment.get("flags", {})
    flags_json = json.dumps(flags) if flags else None
    
    # 提取预览文本（响应前 200 字符）
    preview_text = None
    if result:
        response = result.get("response", "")
        preview_text = response[:200] if response else None
    
    # 存储完整 JSON 用于调试/分析
    assessment_json = json.dumps(assessment)
    decision_json = json.dumps(decision)
    result_json = json.dumps(result) if result else None
    
    # 插入数据库
    with self._get_connection() as conn:
        conn.execute("""
            INSERT INTO assessments (
                user_id, ts, scale, score, severity, rigid, route,
                flags_json, preview_text,
                assessment_json, decision_json, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (...))
        conn.commit()
```

**数据流**:
```
输入:
  assessment = {"scale": "phq9", "total_score": 12.0, ...}
  decision = {"route": "medium", "rigid_score": 0.6, ...}
  result = {"policy": "medium", "response": "...", ...}

处理:
  1. 提取字段: scale="phq9", score=12.0, severity="moderate", ...
  2. 序列化 JSON: flags_json='{"suicidal_ideation": false}'
  3. 提取预览: preview_text="I understand this is important."
  4. 插入数据库: INSERT INTO assessments (...)

输出:
  数据库记录:
    - user_id: "test_user_1"
    - scale: "phq9"
    - score: 12.0
    - severity: "moderate"
    - route: "medium"
    - rigid: 0.6
```

---

### 2. `test_save_with_suicidal_ideation` - 测试保存包含自杀意念标志的评估

**目的**: 验证高风险评估（包含自杀意念标志）的正确保存和 JSON 序列化

**测试步骤**:
```python
user_id = "test_user_2"
assessment = {
    "success": True,
    "scale": "phq9",
    "total_score": 10.0,
    "severity_level": "mild",
    "flags": {"suicidal_ideation": True, "suicidal_ideation_score": 2}
}
decision = {
    "route": "high",
    "rigid_score": 1.0,
    "reason": "hard_lock"
}
result = {
    "policy": "high",
    "response": "Safety script",
    "safety_banner": "If you are in immediate danger, call or text 988"
}

await temp_repo.save(user_id, assessment, decision, result)
history = await temp_repo.history(user_id, limit=1)
```

**验证点**:
- ✅ 历史记录数量为 1
- ✅ `flags["suicidal_ideation"]` 为 `True`（JSON 反序列化正确）
- ✅ `route` 为 `"high"`（高风险路由）

**对应源码** (`repo.py:103-105, 191-198`):
```python
# 保存时序列化 flags
flags = assessment.get("flags", {})
flags_json = json.dumps(flags) if flags else None

# 读取时反序列化 flags
if row["flags_json"]:
    try:
        record["flags"] = json.loads(row["flags_json"])
    except json.JSONDecodeError:
        record["flags"] = {}
else:
    record["flags"] = {}
```

**数据流**:
```
输入:
  flags = {"suicidal_ideation": True, "suicidal_ideation_score": 2}

保存:
  flags_json = '{"suicidal_ideation": true, "suicidal_ideation_score": 2}'
  → 存储到数据库 flags_json 字段

读取:
  flags_json = '{"suicidal_ideation": true, "suicidal_ideation_score": 2}'
  → json.loads() → {"suicidal_ideation": True, "suicidal_ideation_score": 2}
  → history[0]["flags"]["suicidal_ideation"] == True ✅
```

**关键点**: 验证 JSON 序列化/反序列化正确处理复杂数据结构（包括布尔值和嵌套字典）

---

### 3. `test_history_multiple_records` - 测试检索多条历史记录

**目的**: 验证可以正确保存和检索多条评估记录，并按时间戳降序排列

**测试步骤**:
```python
user_id = "test_user_3"

# 保存 5 条评估记录
for i in range(5):
    assessment = {
        "scale": "gad7",
        "total_score": float(i * 2),  # 0.0, 2.0, 4.0, 6.0, 8.0
        "severity_level": "minimal" if i < 2 else "moderate",
        "flags": {}
    }
    decision = {
        "route": "low" if i < 2 else "medium",
        "rigid_score": 0.2 if i < 2 else 0.6,
    }
    result = {"policy": "low" if i < 2 else "medium", "response": f"Response {i}"}
    
    await temp_repo.save(user_id, assessment, decision, result)

# 检索历史记录
history = await temp_repo.history(user_id, limit=10)
```

**验证点**:
- ✅ 历史记录数量为 5
- ✅ 按时间戳降序排列（最新的在前）
- ✅ `history[0]["score"] == 8.0`（最后保存的，最新的）
- ✅ `history[4]["score"] == 0.0`（最先保存的，最旧的）

**对应源码** (`repo.py:147-207`):
```python
async def history(
    self,
    user_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    with self._get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                id, user_id, ts, scale, score, severity, 
                rigid, route, flags_json, preview_text
            FROM assessments
            WHERE user_id = ?
            ORDER BY ts DESC  -- 按时间戳降序排列
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        
        # 转换为字典列表
        history = []
        for row in rows:
            record = {
                "id": row["id"],
                "user_id": row["user_id"],
                "ts": row["ts"],
                "scale": row["scale"],
                "score": row["score"],
                ...
            }
            # 反序列化 flags
            if row["flags_json"]:
                record["flags"] = json.loads(row["flags_json"])
            else:
                record["flags"] = {}
            
            history.append(record)
        
        return history
```

**数据流**:
```
保存顺序:
  i=0: score=0.0, ts=t0
  i=1: score=2.0, ts=t1
  i=2: score=4.0, ts=t2
  i=3: score=6.0, ts=t3
  i=4: score=8.0, ts=t4  (最新)

数据库查询:
  SELECT ... ORDER BY ts DESC LIMIT 10
  → 返回: [t4, t3, t2, t1, t0]  (降序)

结果:
  history[0] = {score: 8.0, ts: t4}  ← 最新
  history[1] = {score: 6.0, ts: t3}
  history[2] = {score: 4.0, ts: t2}
  history[3] = {score: 2.0, ts: t1}
  history[4] = {score: 0.0, ts: t0}  ← 最旧
```

**关键点**: 验证 SQL `ORDER BY ts DESC` 正确实现时间戳降序排列

---

### 4. `test_history_limit` - 测试历史记录限制参数

**目的**: 验证 `limit` 参数可以正确限制返回的记录数量

**测试步骤**:
```python
user_id = "test_user_4"

# 保存 10 条评估记录
for i in range(10):
    assessment = {
        "scale": "phq9",
        "total_score": float(i),
        "severity_level": "minimal",
        "flags": {}
    }
    decision = {"route": "low", "rigid_score": 0.2, "reason": "low_risk"}
    result = {"policy": "low", "response": f"Response {i}"}
    
    await temp_repo.save(user_id, assessment, decision, result)

# 请求只返回 5 条
history = await temp_repo.history(user_id, limit=5)
```

**验证点**:
- ✅ 保存了 10 条记录
- ✅ 请求 `limit=5` 时只返回 5 条记录
- ✅ 返回的是最新的 5 条记录（由于 `ORDER BY ts DESC`）

**对应源码** (`repo.py:164-172`):
```python
cursor = conn.execute("""
    SELECT 
        id, user_id, ts, scale, score, severity, 
        rigid, route, flags_json, preview_text
    FROM assessments
    WHERE user_id = ?
    ORDER BY ts DESC
    LIMIT ?  -- 限制返回数量
""", (user_id, limit))
```

**数据流**:
```
数据库中有 10 条记录:
  [记录0, 记录1, 记录2, ..., 记录9]  (按时间升序)

查询: SELECT ... ORDER BY ts DESC LIMIT 5
  → 返回最新的 5 条: [记录9, 记录8, 记录7, 记录6, 记录5]

结果:
  len(history) == 5 ✅
  history[0] = 记录9 (最新)
  history[4] = 记录5
```

**关键点**: 验证 SQL `LIMIT` 子句正确限制返回的记录数量

---

### 5. `test_has_prior_assessment` - 测试检查用户是否有历史评估

**目的**: 验证 `has_prior_assessment()` 方法可以正确判断用户是否有历史评估记录

**测试步骤**:
```python
user_id = "test_user_5"

# 初始状态：没有评估记录
assert await temp_repo.has_prior_assessment(user_id) is False

# 保存一条评估记录
assessment = {
    "success": True,
    "scale": "gad7",
    "total_score": 5.0,
    "severity_level": "minimal",
    "flags": {}
}
decision = {"route": "low", "rigid_score": 0.2, "reason": "low_risk"}
result = {"policy": "low", "response": "Hello"}

await temp_repo.save(user_id, assessment, decision, result)

# 现在应该有历史评估了
assert await temp_repo.has_prior_assessment(user_id) is True
```

**验证点**:
- ✅ 初始状态返回 `False`（没有评估记录）
- ✅ 保存一条记录后返回 `True`（有评估记录）

**对应源码** (`repo.py:209-232`):
```python
async def has_prior_assessment(self, user_id: str) -> bool:
    """
    Check if user has any prior assessments.
    
    Returns:
        True if user has prior assessments, False otherwise
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM assessments
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return row["count"] > 0 if row else False
            
    except Exception as e:
        logger.error(f"Error checking prior assessments for user {user_id}: {e}")
        return False
```

**数据流**:
```
初始状态:
  数据库: assessments 表中没有 user_id="test_user_5" 的记录
  查询: SELECT COUNT(*) FROM assessments WHERE user_id = "test_user_5"
  结果: count = 0
  返回: False ✅

保存后:
  数据库: assessments 表中有 1 条 user_id="test_user_5" 的记录
  查询: SELECT COUNT(*) FROM assessments WHERE user_id = "test_user_5"
  结果: count = 1
  返回: True ✅
```

**关键点**: 这个方法用于实现 GAD-7 首次接触流程（如果用户没有历史评估，默认启动 GAD-7 评估）

---

### 6. `test_history_empty_user` - 测试空用户的历史记录

**目的**: 验证对于没有评估记录的用户，`history()` 方法返回空列表

**测试步骤**:
```python
user_id = "test_user_6"

# 新用户，没有任何评估记录
history = await temp_repo.history(user_id, limit=10)
```

**验证点**:
- ✅ 历史记录数量为 0
- ✅ 返回空列表 `[]`

**对应源码** (`repo.py:163-207`):
```python
async def history(
    self,
    user_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    try:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT ...
                FROM assessments
                WHERE user_id = ?
                ORDER BY ts DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()  # 如果没有匹配记录，返回空列表
            
            # 转换为字典列表
            history = []
            for row in rows:  # 如果没有行，循环不执行
                ...
                history.append(record)
            
            return history  # 返回空列表 []
```

**数据流**:
```
查询:
  SELECT ... FROM assessments WHERE user_id = "test_user_6" ...
  
结果:
  rows = []  (没有匹配的记录)
  
处理:
  history = []
  for row in rows:  # 不执行
      ...
  
返回:
  history = [] ✅
  len(history) == 0 ✅
```

**关键点**: 验证边界情况处理（空结果集）

---

### 7. `test_save_without_result` - 测试保存没有政策结果的评估

**目的**: 验证可以保存评估记录，即使没有政策执行结果（`result=None`）

**测试步骤**:
```python
user_id = "test_user_7"
assessment = {
    "success": True,
    "scale": "pss10",
    "total_score": 15.0,
    "severity_level": "moderate",
    "flags": {}
}
decision = {
    "route": "medium",
    "rigid_score": 0.6,
    "reason": "medium_risk"
}

# 保存时 result=None
await temp_repo.save(user_id, assessment, decision, None)

history = await temp_repo.history(user_id, limit=1)
```

**验证点**:
- ✅ 历史记录数量为 1（保存成功）
- ✅ `preview_text` 为 `None`（因为没有 `result`，无法提取预览文本）

**对应源码** (`repo.py:107-111, 116`):
```python
# 提取预览文本（前 200 字符的响应）
preview_text = None
if result:  # 如果 result 不为 None
    response = result.get("response", "")
    preview_text = response[:200] if response else None
# 如果 result 为 None，preview_text 保持为 None

# 序列化 result
result_json = json.dumps(result) if result else None  # None 时存储 NULL
```

**数据流**:
```
输入:
  assessment = {...}
  decision = {...}
  result = None  ← 没有政策结果

处理:
  preview_text = None  (因为 result 为 None)
  result_json = None  (因为 result 为 None)

保存:
  INSERT INTO assessments (..., preview_text, result_json) 
  VALUES (..., NULL, NULL)

读取:
  history[0]["preview_text"] = None ✅
```

**关键点**: 验证可选参数处理（`result` 可以为 `None`）

---

## 🎯 测试覆盖的功能点

| 功能 | 测试用例 | 状态 |
|------|---------|------|
| 基本保存功能 | `test_save_assessment` | ✅ |
| JSON 序列化/反序列化 | `test_save_with_suicidal_ideation` | ✅ |
| 多条记录检索 | `test_history_multiple_records` | ✅ |
| 时间戳排序 | `test_history_multiple_records` | ✅ |
| 记录数量限制 | `test_history_limit` | ✅ |
| 检查历史评估 | `test_has_prior_assessment` | ✅ |
| 空用户处理 | `test_history_empty_user` | ✅ |
| 可选参数处理 | `test_save_without_result` | ✅ |

---

## 🗄️ 数据库架构

### 表结构 (`assessments`)

```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    scale TEXT NOT NULL,              -- "phq9", "gad7", "pss10"
    score REAL NOT NULL,              -- 总分
    severity TEXT NOT NULL,           -- "minimal", "mild", "moderate", "severe"
    rigid REAL NOT NULL,              -- 刚性分数 (0.0 - 1.0)
    route TEXT NOT NULL,              -- "low", "medium", "high"
    flags_json TEXT,                  -- JSON 序列化的 flags
    preview_text TEXT,                -- 响应预览（前 200 字符）
    assessment_json TEXT,             -- 完整评估 JSON（用于调试）
    decision_json TEXT,               -- 完整决策 JSON（用于调试）
    result_json TEXT                  -- 完整结果 JSON（用于调试）
)

CREATE INDEX idx_user_id_ts ON assessments(user_id, ts DESC)
```

### 索引说明

- **`idx_user_id_ts`**: 复合索引，优化按用户 ID 和时间戳查询
  - 支持快速查询特定用户的历史记录
  - 支持按时间戳降序排列（`ORDER BY ts DESC`）

---

## 🚀 如何在终端运行测试

### 方式 1: 运行整个测试文件（推荐）

```bash
# 使用 conda run（推荐，自动使用 PROXIMO 环境）
conda run -n PROXIMO pytest tests/test_repo.py -v

# 或者先激活环境
conda activate PROXIMO
pytest tests/test_repo.py -v
```

### 方式 2: 运行单个测试用例

```bash
# 运行特定的测试方法
conda run -n PROXIMO pytest tests/test_repo.py::TestAssessmentRepo::test_save_assessment -v

# 运行多个特定测试
conda run -n PROXIMO pytest tests/test_repo.py::TestAssessmentRepo::test_save_assessment tests/test_repo.py::TestAssessmentRepo::test_history_multiple_records -v
```

### 方式 3: 运行并显示详细输出

```bash
# -v: 详细输出（verbose）
# -s: 显示 print 语句输出
conda run -n PROXIMO pytest tests/test_repo.py -v -s
```

### 方式 4: 运行并显示覆盖率

```bash
# 显示测试覆盖率
conda run -n PROXIMO pytest tests/test_repo.py --cov=src.storage.repo --cov-report=term-missing
```

### 方式 5: 运行所有存储相关测试

```bash
# 运行所有包含 "repo" 的测试文件
conda run -n PROXIMO pytest tests/ -k repo -v
```

---

## 📊 预期输出示例

运行 `conda run -n PROXIMO pytest tests/test_repo.py -v` 的预期输出：

```
============================= test session starts =============================
platform win32 -- Python 3.12.12, pytest-8.4.2, pluggy-1.6.0
collected 7 items

tests/test_repo.py::TestAssessmentRepo::test_save_assessment PASSED [ 14%]
tests/test_repo.py::TestAssessmentRepo::test_save_with_suicidal_ideation PASSED [ 28%]
tests/test_repo.py::TestAssessmentRepo::test_history_multiple_records PASSED [ 42%]
tests/test_repo.py::TestAssessmentRepo::test_history_limit PASSED [ 57%]
tests/test_repo.py::TestAssessmentRepo::test_has_prior_assessment PASSED [ 71%]
tests/test_repo.py::TestAssessmentRepo::test_history_empty_user PASSED [ 85%]
tests/test_repo.py::TestAssessmentRepo::test_save_without_result PASSED [100%]

============================== 7 passed in 0.25s ==============================
```

---

## 🔍 测试设计模式

### 1. **隔离性 (Isolation)**
- 使用 `@pytest.fixture` 创建临时数据库
- 每个测试使用不同的 `user_id`，避免测试间相互影响
- 使用 `tempfile.TemporaryDirectory()` 确保测试后清理

### 2. **异步测试 (Async Testing)**
- 所有测试方法使用 `@pytest.mark.asyncio` 装饰器
- 使用 `await` 调用异步方法（`save()`, `history()`, `has_prior_assessment()`）

### 3. **边界测试 (Boundary Testing)**
- 测试空用户（`test_history_empty_user`）
- 测试可选参数（`test_save_without_result`）
- 测试记录数量限制（`test_history_limit`）

### 4. **数据完整性 (Data Integrity)**
- 验证 JSON 序列化/反序列化（`test_save_with_suicidal_ideation`）
- 验证时间戳排序（`test_history_multiple_records`）
- 验证所有字段正确保存和检索

### 5. **业务逻辑测试 (Business Logic)**
- 测试 `has_prior_assessment()` 用于 GAD-7 首次接触流程
- 测试高风险评估的正确保存（自杀意念标志）

---

## 💡 关键测试场景

### 场景 1: 首次用户评估
```python
# 新用户，没有历史评估
has_prior = await repo.has_prior_assessment("new_user")
# 预期: False

# 保存首次评估
await repo.save("new_user", assessment, decision, result)

# 现在有历史评估了
has_prior = await repo.has_prior_assessment("new_user")
# 预期: True
```

### 场景 2: 高风险评估保存
```python
# 高风险评估（包含自杀意念标志）
assessment = {
    "flags": {"suicidal_ideation": True, "suicidal_ideation_score": 2}
}
decision = {"route": "high", "rigid_score": 1.0}

await repo.save("user1", assessment, decision, result)

# 验证高风险标志正确保存
history = await repo.history("user1", limit=1)
assert history[0]["flags"]["suicidal_ideation"] is True
assert history[0]["route"] == "high"
```

### 场景 3: 历史记录查询
```python
# 保存多条评估记录
for i in range(10):
    await repo.save("user1", assessment_i, decision_i, result_i)

# 查询最近 5 条
history = await repo.history("user1", limit=5)
# 预期: 返回最新的 5 条记录，按时间戳降序排列
assert len(history) == 5
assert history[0]["ts"] > history[4]["ts"]  # 最新的在前
```

### 场景 4: 可选参数处理
```python
# 保存评估，但没有政策结果
await repo.save("user1", assessment, decision, None)

# 验证保存成功，但 preview_text 为 None
history = await repo.history("user1", limit=1)
assert len(history) == 1
assert history[0]["preview_text"] is None
```

---

## 🔗 与其他模块的集成

### 1. **与 ConversationEngine 集成**
```python
# ConversationEngine 使用 AssessmentRepo 保存评估结果
from src.storage.repo import AssessmentRepo

repo = AssessmentRepo()
await repo.save(user_id, assessment, decision, policy_result)
```

### 2. **与 GAD-7 首次接触流程集成**
```python
# 检查用户是否有历史评估
if not await repo.has_prior_assessment(user_id):
    # 首次接触，默认启动 GAD-7 评估
    scale = "gad7"
else:
    # 已有历史评估，使用用户指定的 scale
    scale = request.scale or "gad7"
```

### 3. **与 API 历史端点集成**
```python
# GET /api/v1/assess/history?user_id=...&limit=50
history = await repo.history(user_id, limit=limit)
return {"history": history}
```

---

## ✅ 总结

这 7 个测试用例全面覆盖了 `AssessmentRepo` 的核心功能：

1. ✅ **基本功能**: 保存评估记录、检索历史记录
2. ✅ **数据完整性**: JSON 序列化/反序列化、时间戳排序
3. ✅ **查询功能**: 记录数量限制、按用户 ID 查询
4. ✅ **业务逻辑**: 检查历史评估、处理可选参数
5. ✅ **边界情况**: 空用户、无结果保存

所有测试都通过，说明 `AssessmentRepo` 实现正确且稳定！🎉

---

## 📝 注意事项

1. **临时数据库**: 测试使用 `tempfile.TemporaryDirectory()` 创建临时数据库，测试结束后自动清理
2. **异步方法**: 所有数据库操作都是异步的，需要使用 `await` 调用
3. **JSON 序列化**: `flags` 字段使用 JSON 序列化存储，读取时需要反序列化
4. **时间戳排序**: 历史记录按时间戳降序排列（最新的在前），使用 SQL `ORDER BY ts DESC`
5. **索引优化**: 数据库创建了 `idx_user_id_ts` 索引，优化按用户 ID 和时间戳查询的性能


