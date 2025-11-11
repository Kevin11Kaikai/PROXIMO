# NeMo Guardrails 集成计划

## 📋 概述

在 PROXIMO 系统中集成 NeMo Guardrails，添加 "Safety & Ethics Layer" 来增强对话系统的安全护栏能力。

## 🎯 目标

- 与现有流程整合：Assessment → Risk Mapping → Routing → Policy → **Guardrails**
- 增强高风险、敏感话题、自杀倾向等场景的安全守护
- 不破坏现有功能（29个测试必须全部通过）

## ✅ 已完成模块（勿改动）

- `proximo.assessment.assess(...)`：量表评估模块
- `proximo/risk.mapping` → route 决策逻辑（low/medium/high）
- `proximo/conversation/policies.py`：不同风险级别策略执行
- `proximo/conversation/engine.py`：整体流程调用入口

## 📦 实施阶段

### 阶段 1: 安装和配置（Phase 1）

#### 1.1 安装 NeMo Guardrails
```bash
conda activate PROXIMO
pip install nemoguardrails
```

#### 1.2 创建目录结构
```
config/
  guardrails/
    ├── config.yml          # 主配置文件
    ├── rails/              # Colang 规则文件
    │   ├── safety.co       # 安全规则
    │   ├── topics.co       # 话题限制
    │   └── ethics.co       # 伦理规则
    └── actions.py          # 自定义动作
```

#### 1.3 配置文件设计
- `config.yml`: 指定模型、LLM 提供者（Ollama）、启用 input/output guardrails
- 与现有 Ollama 服务集成

### 阶段 2: 定义 Guardrails 规则（Phase 2）

#### 2.1 规则类别

**话题禁止**：
- 自杀方法
- 药物剂量建议
- 违法行为组织
- 暴力内容

**安全提示**：
- 检测到自杀意念 → 强制跳转 hotline script
- 检测到高风险话题 → 触发安全横幅

**角色/语言风格限制**：
- 确保机器人回复语气温和、安全、非诊断
- 禁止提供医疗建议
- 禁止提供法律建议

#### 2.2 Colang 规则文件
在 `rails/` 目录下创建 `.co` 文件，定义：
- 用户意图识别
- Bot 响应流程
- 安全检查和拦截逻辑

### 阶段 3: 代码集成（Phase 3）

#### 3.1 创建 GuardrailsService
创建 `src/services/guardrails_service.py`：
```python
class GuardrailsService:
    """NeMo Guardrails 服务封装"""
    
    def __init__(self, config_path: str):
        # 初始化 Rails 实例
        
    async def check_input(self, user_message: str, context: dict) -> dict:
        """检查用户输入，返回是否触发护栏"""
        
    async def generate_safe_response(self, user_message: str, context: dict) -> dict:
        """生成安全响应（通过 Guardrails）"""
```

#### 3.2 修改 ConversationEngine
在 `engine.py` 的 `_run_policy` 方法中：
1. **输入检查**：在调用 LLM 前，先通过 Guardrails 检查用户输入
2. **输出过滤**：如果触发护栏，使用 Guardrails 生成的安全响应
3. **High-risk 路径**：在 `route == "high"` 时，优先使用 Guardrails 检查

#### 3.3 集成点
```python
# 在 engine.py 的 _run_policy 方法中
async def _run_policy(self, route: str, rigid_score: float, context: PolicyContext):
    # 1. 输入检查（所有路由）
    guardrails_result = await self.guardrails.check_input(
        user_message=context.user_message,
        context={"route": route, "rigid_score": rigid_score}
    )
    
    # 2. 如果触发护栏，直接返回安全响应
    if guardrails_result.get("triggered"):
        return {
            "policy": route,
            "response": guardrails_result.get("safe_response"),
            "guardrails_triggered": True,
            "safety_banner": SAFETY_BANNER
        }
    
    # 3. 正常流程：执行原有策略
    # ... 原有代码 ...
    
    # 4. 输出检查（可选）
    # 如果需要对 LLM 输出也进行检查
```

### 阶段 4: 日志和持久化（Phase 4）

#### 4.1 日志记录
在结构化日志中添加：
- `guardrails_triggered: true/false`
- `guardrails_action: "blocked" | "modified" | "passed"`
- `guardrails_reason: str`

#### 4.2 AssessmentRepo 扩展
在保存评估结果时，包含 Guardrails 执行信息：
```python
{
    "guardrails_triggered": True,
    "guardrails_action": "blocked",
    "guardrails_reason": "suicidal_content_detected"
}
```

### 阶段 5: 测试和验证（Phase 5）

#### 5.1 创建测试文件
`tests/test_guardrails_integration.py`：
- 测试用户询问自杀方法 → Guardrails 拒绝并输出安全提示
- 测试正常低风险对话 → 正常流程，不受阻断
- 测试高风险对话路径中安全护栏起作用

#### 5.2 回归测试
- 确保现有 29 个测试全部通过
- 新增 Guardrails 相关测试

## 🔧 技术细节

### Guardrails 配置示例

**config.yml**:
```yaml
models:
  - type: main
    engine: ollama
    model: qwen2.5:14b
    parameters:
      temperature: 0.7

rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output
```

**rails/safety.co**:
```colang
define user ask suicide method
  "how to kill myself"
  "ways to commit suicide"
  "suicide methods"

define flow suicide prevention
  user ask suicide method
  bot provide safety resources
  stop

define bot provide safety resources
  "I'm here to support you, and I want to make sure you're safe..."
```

### 集成架构

```
User Input
    ↓
[Guardrails Input Check] ← 新增
    ↓ (如果触发护栏)
    → 返回安全响应 + 记录日志
    ↓ (如果通过)
Assessment → Routing → Policy
    ↓
[Guardrails Output Check] ← 可选
    ↓
Response to User
```

## 📊 验收标准

1. ✅ Guardrails 成功安装并可运行 `rails.generate()`
2. ✅ 在 `/api/v1/assess/execute` 完整流程内，Guardrails 被调用
3. ✅ 高风险/敏感话题输入被 Guardrails 捕获并导向安全脚本
4. ✅ 日志中有标记 `guardrails_triggered: true/false`
5. ✅ 所有新旧测试通过，无回归

## 🚀 开始实施

准备好开始实施时，按阶段顺序执行：
1. Phase 1: 安装和配置
2. Phase 2: 定义规则
3. Phase 3: 代码集成
4. Phase 4: 日志和持久化
5. Phase 5: 测试和验证

---

**创建日期**: 2025-11-06  
**状态**: 计划阶段

