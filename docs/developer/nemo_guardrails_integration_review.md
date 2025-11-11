# NeMo Guardrails 集成计划审查报告

## 📋 审查概览

本文档详细审查 NeMo Guardrails 集成计划，识别潜在问题、风险和需要确认的细节。

---

## ✅ 计划优点

1. **清晰的阶段划分**：5个阶段逻辑清晰，易于执行
2. **不破坏现有功能**：明确要求保持29个测试通过
3. **集成点选择合理**：在 Policy 执行前后添加 Guardrails 检查
4. **日志和持久化**：考虑了完整的可观测性

---

## ⚠️ 需要确认的关键问题

### 1. NeMo Guardrails 与 Ollama 的兼容性

**问题**：
- NeMo Guardrails 是否原生支持 Ollama 作为 LLM 后端？
- 如果支持，配置方式是什么？
- 如果不支持，是否需要适配层？

**建议**：
- 先验证 NeMo Guardrails 是否支持 Ollama
- 查看官方文档中的 "Custom LLM Provider" 部分
- 可能需要创建自定义 LLM 适配器

**风险**：如果 NeMo Guardrails 不支持 Ollama，可能需要：
- 使用 LangChain 作为中间层（LangChain 支持 Ollama）
- 或者创建自定义 LLM 包装器

### 2. 配置文件的正确格式

**当前计划中的配置**：
```yaml
models:
  - type: main
    engine: ollama
    model: qwen2.5:14b
```

**需要确认**：
- NeMo Guardrails 的 `config.yml` 格式是否正确？
- `engine: ollama` 是否是有效的配置项？
- 是否需要额外的配置来连接 Ollama 服务？

**建议**：
- 查阅 NeMo Guardrails 官方文档
- 查看示例配置文件
- 可能需要使用 LangChain 集成：
  ```yaml
  models:
    - type: main
      engine: langchain
      model: ollama/qwen2.5:14b
  ```

### 3. 集成点的选择

**当前计划**：在 `_run_policy` 方法中集成

**优点**：
- 集中管理，易于维护
- 所有策略都经过 Guardrails 检查

**潜在问题**：
- High Policy 已经有固定安全脚本，Guardrails 可能重复
- 性能影响：每次对话都要经过 Guardrails 检查

**建议**：
- **方案 A（推荐）**：在 `run_pipeline` 方法中，Policy 执行前检查
  - 优点：可以跳过 High Policy 的固定脚本（如果 Guardrails 已处理）
  - 缺点：需要修改更多代码
- **方案 B**：保持当前计划，但优化 High Policy 逻辑
  - 如果 Guardrails 触发，直接返回，不执行固定脚本
  - 如果 Guardrails 通过，再执行原有逻辑

### 4. 性能影响

**关注点**：
- NeMo Guardrails 会增加额外的延迟
- 每次对话都需要经过 Guardrails 检查
- 可能影响用户体验

**建议**：
- 添加性能监控
- 考虑缓存机制（相同输入不重复检查）
- 对于低风险路由，可以考虑异步检查或降低检查频率

### 5. 错误处理

**当前计划**：如果 Guardrails 失败，应该如何处理？

**建议**：
- **降级策略**：如果 Guardrails 服务不可用，回退到原有逻辑
- **日志记录**：记录所有 Guardrails 错误
- **健康检查**：定期检查 Guardrails 服务状态

---

## 🔧 技术细节审查

### 1. GuardrailsService 设计

**当前计划**：
```python
class GuardrailsService:
    async def check_input(self, user_message: str, context: dict) -> dict:
    async def generate_safe_response(self, user_message: str, context: dict) -> dict:
```

**建议改进**：
```python
class GuardrailsService:
    """NeMo Guardrails 服务封装"""
    
    def __init__(self, config_path: str):
        """初始化 Rails 实例"""
        self.config_path = Path(config_path)
        self.rails = None  # 延迟初始化
        self._initialized = False
        
    async def initialize(self) -> bool:
        """异步初始化 Rails 实例"""
        try:
            from nemoguardrails import Rails
            
            # 加载配置
            self.rails = Rails(config_path=str(self.config_path))
            await self.rails.initialize()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Guardrails: {e}")
            return False
    
    async def check_input(
        self, 
        user_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检查用户输入，返回是否触发护栏
        
        Returns:
            {
                "triggered": bool,
                "action": "blocked" | "modified" | "passed",
                "safe_response": Optional[str],
                "reason": Optional[str]
            }
        """
        if not self._initialized:
            # 降级：如果未初始化，返回通过
            return {"triggered": False, "action": "passed"}
        
        try:
            # 使用 Rails 检查输入
            result = await self.rails.generate_async(
                messages=[{"role": "user", "content": user_message}],
                config={"context": context or {}}
            )
            
            # 解析结果
            # 需要根据 NeMo Guardrails 的实际 API 调整
            return self._parse_guardrails_result(result)
            
        except Exception as e:
            logger.error(f"Guardrails check failed: {e}")
            # 降级：出错时返回通过，但记录错误
            return {"triggered": False, "action": "passed", "error": str(e)}
    
    def _parse_guardrails_result(self, result: Any) -> Dict[str, Any]:
        """解析 Guardrails 返回结果"""
        # 需要根据实际 API 实现
        pass
```

### 2. 集成到 ConversationEngine

**当前计划的问题**：
- 在 `_run_policy` 中集成，但 High Policy 已经有固定脚本
- 可能导致重复的安全处理

**改进方案**：
```python
async def _run_policy(
    self,
    route: str,
    rigid_score: float,
    context: PolicyContext
) -> Dict[str, Any]:
    """Execute policy based on route."""
    
    # 1. Guardrails 输入检查（所有路由）
    guardrails_result = await self.guardrails.check_input(
        user_message=context.user_message,
        context={
            "route": route,
            "rigid_score": rigid_score,
            "user_id": context.user_id,
            "assessment": context.assessment
        }
    )
    
    # 2. 如果触发护栏，直接返回安全响应
    if guardrails_result.get("triggered"):
        logger.warning(
            f"Guardrails triggered for user {context.user_id}: {guardrails_result.get('reason')}"
        )
        return {
            "policy": route,
            "response": guardrails_result.get("safe_response") or FIXED_SAFETY_SCRIPT,
            "guardrails_triggered": True,
            "guardrails_action": guardrails_result.get("action"),
            "guardrails_reason": guardrails_result.get("reason"),
            "safety_banner": SAFETY_BANNER,
            "fixed_script": True
        }
    
    # 3. High Policy 特殊处理
    if route == Route.HIGH:
        # High Policy 已经有固定脚本，但如果 Guardrails 通过，
        # 我们可以选择使用 Guardrails 生成的安全响应
        # 或者继续使用固定脚本（更安全）
        return await self.policies.run_high_policy(context)
    
    # 4. 正常流程：执行原有策略
    try:
        if route == Route.LOW:
            return await self.policies.run_low_policy(context)
        elif route == Route.MEDIUM:
            return await self.policies.run_medium_policy(context)
        else:
            logger.warning(f"Unknown route: {route}, defaulting to medium policy")
            return await self.policies.run_medium_policy(context)
    except Exception as e:
        logger.error(f"Error executing {route} policy: {e}", exc_info=True)
        return {
            "policy": route,
            "error": str(e),
            "response": "I'm here to help. How can I assist you?",
            "safety_banner": SAFETY_BANNER if route == Route.HIGH else None
        }
```

### 3. 配置文件结构

**建议的目录结构**：
```
config/
  guardrails/
    ├── config.yml              # 主配置文件
    ├── rails/                  # Colang 规则文件
    │   ├── safety.co           # 安全规则（自杀、暴力等）
    │   ├── topics.co           # 话题限制
    │   ├── ethics.co           # 伦理规则
    │   └── mental_health.co    # 心理健康特定规则
    └── actions.py              # 自定义动作（可选）
```

**config.yml 示例**（需要根据实际 API 调整）：
```yaml
# NeMo Guardrails 配置
# 注意：实际格式需要查阅官方文档

models:
  - type: main
    engine: langchain_llm
    model: ollama/qwen2.5:14b
    parameters:
      temperature: 0.7
      max_tokens: 512

rails:
  config:
    # 启用输入检查
    input:
      flows:
        - self check input
        - check safety
        - check topics
    
    # 启用输出检查
    output:
      flows:
        - self check output
        - check response safety

# Ollama 连接配置
llm:
  type: ollama
  base_url: ${OLLAMA_URL}  # 从环境变量读取
  model: ${MODEL_NAME}      # 从环境变量读取
```

---

## 🚨 潜在风险和缓解措施

### 风险 1: NeMo Guardrails 不支持 Ollama

**风险等级**：高

**缓解措施**：
1. 先进行概念验证（POC），验证 Ollama 集成
2. 如果不支持，使用 LangChain 作为中间层
3. 或者创建自定义 LLM 包装器

### 风险 2: 性能影响

**风险等级**：中

**缓解措施**：
1. 添加性能监控和基准测试
2. 实现缓存机制
3. 考虑异步处理或降低检查频率

### 风险 3: 与现有 High Policy 冲突

**风险等级**：中

**缓解措施**：
1. 明确优先级：Guardrails > High Policy 固定脚本
2. 如果 Guardrails 触发，直接返回，不执行 High Policy
3. 如果 Guardrails 通过，High Policy 继续使用固定脚本（更安全）

### 风险 4: 配置复杂性

**风险等级**：低

**缓解措施**：
1. 提供详细的配置文档
2. 创建配置验证工具
3. 提供默认配置和示例

---

## 📝 需要补充的细节

### 1. Colang 规则文件示例

**safety.co**（需要根据实际语法调整）：
```colang
# 定义用户意图：询问自杀方法
define user ask suicide method
  "how to kill myself"
  "ways to commit suicide"
  "suicide methods"
  "how do I end my life"
  "best way to die"

# 定义流程：自杀预防
define flow suicide prevention
  user ask suicide method
  bot provide safety resources
  stop

# 定义 Bot 响应：提供安全资源
define bot provide safety resources
  "I'm here to support you, and I want to make sure you're safe. 

Right now, the most important thing is your safety. If you're having thoughts of hurting yourself or ending your life, please reach out for immediate help:

• Call or text 988 (US National Suicide & Crisis Lifeline) - available 24/7
• If outside the US, contact your local emergency services
• Reach out to a trusted adult, friend, or healthcare provider

You don't have to go through this alone. There are people who want to help and support you.

Would you like help finding resources in your area, or would you prefer to speak with someone right now?"

# 定义检查：安全内容检查
define flow check safety
  user express suicidal thoughts
  bot provide safety resources
  stop
```

### 2. 测试用例设计

**test_guardrails_integration.py** 应该包含：

```python
async def test_guardrails_blocks_suicide_methods():
    """测试 Guardrails 阻止自杀方法询问"""
    # 测试用例

async def test_guardrails_allows_normal_conversation():
    """测试正常对话不被阻断"""
    # 测试用例

async def test_guardrails_integration_with_high_risk():
    """测试 Guardrails 与高风险路径的集成"""
    # 测试用例

async def test_guardrails_fallback_on_error():
    """测试 Guardrails 错误时的降级策略"""
    # 测试用例
```

### 3. 日志格式

**结构化日志示例**：
```python
logger.info(
    "Guardrails check completed",
    user_id=user_id,
    guardrails_triggered=True,
    guardrails_action="blocked",
    guardrails_reason="suicidal_content_detected",
    route=route,
    duration_ms=guardrails_duration
)
```

---

## ✅ 审查结论

### 计划总体评价：**良好，但需要补充细节**

### 建议的改进：

1. **先进行 POC**：验证 NeMo Guardrails 与 Ollama 的兼容性
2. **明确集成点**：在 `run_pipeline` 中集成，而不是 `_run_policy`
3. **添加降级策略**：Guardrails 失败时回退到原有逻辑
4. **性能考虑**：添加监控和缓存
5. **配置验证**：创建配置验证工具

### 下一步行动：

1. ✅ 查阅 NeMo Guardrails 官方文档，确认 Ollama 支持
2. ✅ 创建 POC 验证基本功能
3. ✅ 根据 POC 结果调整计划
4. ✅ 开始正式实施

---

**审查日期**: 2025-11-06  
**审查人**: AI Assistant  
**状态**: 待确认细节后开始实施

