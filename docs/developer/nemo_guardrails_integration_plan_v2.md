# NeMo Guardrails 集成计划 v2.0（基于文档研究）

## 📋 概述

在 PROXIMO 系统中集成 NeMo Guardrails，添加 "Safety & Ethics Layer" 来增强对话系统的安全护栏能力。

**更新日期**: 2025-11-06  
**基于**: NeMo Guardrails 官方文档和最佳实践

---

## 🔍 关键发现（基于文档研究）

### 1. NeMo Guardrails 架构

- **Colang 语言**：用于定义对话流程和 Guardrails 规则
- **Rails 实例**：核心对象，管理 Guardrails 配置和执行
- **LLM 集成**：支持多种 LLM 提供者，包括通过 LangChain 集成自定义 LLM

### 2. Ollama 集成方式

**重要发现**：
- NeMo Guardrails **不直接支持 Ollama**
- 需要通过 **LangChain** 作为中间层
- LangChain 支持 Ollama，可以作为桥梁

**集成路径**：
```
NeMo Guardrails → LangChain → Ollama
```

### 3. 基本 API 使用

```python
from nemoguardrails import Rails

# 初始化
rails = Rails(config_path="config/guardrails")

# 生成响应（异步）
messages = [{"role": "user", "content": "user message"}]
response = await rails.generate_async(messages=messages)
```

---

## 📦 更新的实施阶段

### 阶段 1: 安装和配置（Phase 1）

#### 1.1 安装依赖

```bash
conda activate PROXIMO
pip install nemoguardrails
pip install langchain
pip install langchain-community  # 包含 Ollama 支持
```

**注意**：需要同时安装 LangChain 来支持 Ollama 集成。

#### 1.2 创建目录结构

```
config/
  guardrails/
    ├── config.yml          # 主配置文件
    ├── rails/              # Colang 规则文件
    │   ├── safety.co       # 安全规则（自杀、暴力等）
    │   ├── topics.co       # 话题限制
    │   ├── ethics.co       # 伦理规则
    │   └── mental_health.co # 心理健康特定规则
    └── actions.py          # 自定义动作（可选）
```

#### 1.3 配置文件设计（更新）

**config.yml**（基于 LangChain + Ollama）：
```yaml
# NeMo Guardrails 配置文件
# 使用 LangChain 作为中间层连接 Ollama

models:
  - type: main
    engine: langchain_llm
    model: ollama/qwen2.5:14b
    parameters:
      temperature: 0.7
      max_tokens: 512

# LangChain Ollama 配置
llm:
  type: langchain.llms.Ollama
  base_url: ${OLLAMA_URL}  # 从环境变量读取，默认 http://localhost:11434
  model: ${MODEL_NAME}      # 从环境变量读取，默认 qwen2.5:14b

# Rails 配置
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

# 对话配置
instructions:
  - type: general
    content: |
      You are a supportive and empathetic mental health assistant for teens.
      Always prioritize safety and provide appropriate resources when needed.
```

**注意**：实际配置格式可能需要根据 NeMo Guardrails 版本调整。在 POC 阶段需要验证。

---

### 阶段 2: 定义 Guardrails 规则（Phase 2）

#### 2.1 Colang 规则文件示例

**rails/safety.co**：
```colang
# 定义用户意图：询问自杀方法
define user ask suicide method
  "how to kill myself"
  "ways to commit suicide"
  "suicide methods"
  "how do I end my life"
  "best way to die"
  "I want to die"
  "I want to kill myself"

# 定义用户意图：表达自杀想法
define user express suicidal thoughts
  "I'm thinking about suicide"
  "I want to commit suicide"
  "I feel like ending my life"
  "I don't want to live anymore"

# 定义流程：自杀预防
define flow suicide prevention
  user ask suicide method or user express suicidal thoughts
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

**rails/topics.co**：
```colang
# 定义禁止话题：药物剂量建议
define user ask drug dosage
  "how much should I take"
  "what's the right dose"
  "how many pills"

# 定义禁止话题：违法行为
define user ask illegal activities
  "how to hack"
  "how to make drugs"
  "how to break the law"

# 定义流程：话题限制
define flow restrict topics
  user ask drug dosage or user ask illegal activities
  bot refuse inappropriate request
  stop

# 定义 Bot 响应：拒绝不当请求
define bot refuse inappropriate request
  "I can't provide information about that. I'm here to support your mental health and wellbeing. Is there something else I can help you with?"
```

**rails/ethics.co**：
```colang
# 定义 Bot 行为：非诊断性
define bot provide medical diagnosis
  "you have depression"
  "you are bipolar"
  "you need medication"

# 定义流程：伦理检查
define flow check ethics
  bot provide medical diagnosis
  bot clarify non diagnostic role
  stop

# 定义 Bot 响应：澄清非诊断角色
define bot clarify non diagnostic role
  "I'm not a medical professional and can't provide diagnoses. If you're concerned about your mental health, I encourage you to speak with a qualified healthcare provider."
```

#### 2.2 规则优先级

1. **Safety（安全）** - 最高优先级
2. **Topics（话题）** - 中等优先级
3. **Ethics（伦理）** - 基础优先级

---

### 阶段 3: 代码集成（Phase 3 - 更新）

#### 3.1 创建 GuardrailsService（更新）

**src/services/guardrails_service.py**：
```python
"""
NeMo Guardrails 服务封装

提供 Guardrails 输入检查和安全响应生成功能。
通过 LangChain 集成 Ollama 作为 LLM 后端。
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio

logger = logging.getLogger(__name__)


class GuardrailsService:
    """NeMo Guardrails 服务封装"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 Guardrails 服务
        
        Args:
            config_path: Guardrails 配置目录路径（默认: config/guardrails）
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "guardrails"
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.rails = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """
        异步初始化 Rails 实例
        
        Returns:
            True 如果初始化成功，否则 False
        """
        if self._initialized:
            return True
        
        async with self._initialization_lock:
            if self._initialized:
                return True
            
            try:
                from nemoguardrails import Rails
                from langchain_community.llms import Ollama
                from src.core.config import settings
                
                logger.info(f"Initializing NeMo Guardrails from {self.config_path}")
                
                # 创建 Ollama LLM 实例（通过 LangChain）
                ollama_llm = Ollama(
                    base_url=settings.OLLAMA_URL,
                    model=settings.MODEL_NAME,
                    temperature=0.7
                )
                
                # 初始化 Rails
                # 注意：实际 API 可能需要根据版本调整
                self.rails = Rails(
                    config_path=str(self.config_path),
                    llm=ollama_llm  # 传入 LangChain LLM 实例
                )
                
                # 异步初始化（如果支持）
                if hasattr(self.rails, 'initialize'):
                    await self.rails.initialize()
                elif hasattr(self.rails, 'load'):
                    await asyncio.to_thread(self.rails.load)
                
                self._initialized = True
                logger.info("NeMo Guardrails initialized successfully")
                return True
                
            except ImportError as e:
                logger.error(f"Failed to import NeMo Guardrails: {e}")
                logger.error("Please install: pip install nemoguardrails langchain langchain-community")
                return False
            except Exception as e:
                logger.error(f"Failed to initialize Guardrails: {e}", exc_info=True)
                return False
    
    async def check_input(
        self, 
        user_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检查用户输入，返回是否触发护栏
        
        Args:
            user_message: 用户消息
            context: 上下文信息（route, rigid_score, user_id, assessment 等）
        
        Returns:
            {
                "triggered": bool,
                "action": "blocked" | "modified" | "passed",
                "safe_response": Optional[str],
                "reason": Optional[str],
                "error": Optional[str]
            }
        """
        if not self._initialized:
            # 尝试初始化
            if not await self.initialize():
                # 降级：如果初始化失败，返回通过（但记录错误）
                logger.warning("Guardrails not initialized, allowing message through")
                return {
                    "triggered": False,
                    "action": "passed",
                    "error": "guardrails_not_initialized"
                }
        
        try:
            # 构建消息格式
            messages = [
                {"role": "user", "content": user_message}
            ]
            
            # 添加上下文（如果支持）
            config = {}
            if context:
                config["context"] = context
            
            # 调用 Rails 生成（这会触发输入检查）
            # 注意：实际 API 可能需要根据版本调整
            if hasattr(self.rails, 'generate_async'):
                result = await self.rails.generate_async(
                    messages=messages,
                    config=config
                )
            elif hasattr(self.rails, 'generate'):
                # 同步版本，在线程池中运行
                result = await asyncio.to_thread(
                    self.rails.generate,
                    messages=messages,
                    config=config
                )
            else:
                logger.error("Rails instance does not have generate or generate_async method")
                return {
                    "triggered": False,
                    "action": "passed",
                    "error": "unsupported_api"
                }
            
            # 解析结果
            return self._parse_guardrails_result(result, user_message)
            
        except Exception as e:
            logger.error(f"Guardrails check failed: {e}", exc_info=True)
            # 降级：出错时返回通过，但记录错误
            return {
                "triggered": False,
                "action": "passed",
                "error": str(e)
            }
    
    def _parse_guardrails_result(
        self, 
        result: Any, 
        original_message: str
    ) -> Dict[str, Any]:
        """
        解析 Guardrails 返回结果
        
        Args:
            result: Rails 返回的结果
            original_message: 原始用户消息
        
        Returns:
            解析后的结果字典
        """
        # 注意：实际解析逻辑需要根据 NeMo Guardrails 的实际返回格式调整
        # 这里提供通用解析逻辑
        
        try:
            # 如果结果是字符串，说明是正常响应
            if isinstance(result, str):
                # 检查是否包含安全资源提示（说明触发了护栏）
                safety_indicators = [
                    "988",
                    "suicide",
                    "safety",
                    "emergency services",
                    "healthcare provider"
                ]
                
                if any(indicator.lower() in result.lower() for indicator in safety_indicators):
                    return {
                        "triggered": True,
                        "action": "blocked",
                        "safe_response": result,
                        "reason": "safety_content_detected"
                    }
                else:
                    return {
                        "triggered": False,
                        "action": "passed",
                        "safe_response": result
                    }
            
            # 如果结果是字典，尝试解析
            elif isinstance(result, dict):
                # 检查是否有标志表明触发了护栏
                if result.get("blocked") or result.get("triggered"):
                    return {
                        "triggered": True,
                        "action": result.get("action", "blocked"),
                        "safe_response": result.get("response") or result.get("safe_response"),
                        "reason": result.get("reason")
                    }
                else:
                    return {
                        "triggered": False,
                        "action": "passed",
                        "safe_response": result.get("response")
                    }
            
            # 默认：未触发
            return {
                "triggered": False,
                "action": "passed",
                "safe_response": None
            }
            
        except Exception as e:
            logger.error(f"Error parsing Guardrails result: {e}")
            return {
                "triggered": False,
                "action": "passed",
                "error": f"parse_error: {str(e)}"
            }
    
    async def generate_safe_response(
        self, 
        user_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成安全响应（通过 Guardrails）
        
        Args:
            user_message: 用户消息
            context: 上下文信息
        
        Returns:
            安全响应文本
        """
        result = await self.check_input(user_message, context)
        
        if result.get("triggered"):
            return result.get("safe_response", "I'm here to help. How can I assist you?")
        else:
            # 如果未触发护栏，返回 None（让原有逻辑处理）
            return None
```

#### 3.2 修改 ConversationEngine（更新）

**在 `src/conversation/engine.py` 中**：

```python
# 在 ConversationEngine.__init__ 中添加
def __init__(
    self,
    llm_service: Optional[OllamaService] = None,
    repo: Optional[AssessmentRepo] = None,
    guardrails: Optional[GuardrailsService] = None  # 新增
):
    self.llm_service = llm_service or OllamaService()
    self.policies = ConversationPolicies(self.llm_service)
    self.repo = repo or AssessmentRepo()
    self.guardrails = guardrails or GuardrailsService()  # 新增

# 在 _run_policy 方法中集成
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
            "assessment": context.assessment,
            "severity": context.assessment.get("severity_level"),
            "suicidal_ideation": context.assessment.get("flags", {}).get("suicidal_ideation", False)
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
        # 我们继续使用固定脚本（更安全）
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
            "safety_banner": SAFETY_BANNER if route == Route.HIGH else None,
            "guardrails_triggered": False
        }
```

---

### 阶段 4: 日志和持久化（Phase 4 - 更新）

#### 4.1 日志记录（更新）

在 `engine.py` 的结构化日志中添加：

```python
# 在 run_pipeline 方法中
high_risk = route == Route.HIGH or assessment.get("flags", {}).get("suicidal_ideation", False)
guardrails_triggered = policy_result.get("guardrails_triggered", False) if policy_result else False

logger.info(
    "Pipeline completed",
    user_id=request.user_id,
    scale=scale,
    score=assessment.get("total_score"),
    severity=assessment.get("severity_level"),
    rigid=rigid_score,
    route=route,
    duration_ms=duration_ms,
    high_risk=high_risk,
    guardrails_triggered=guardrails_triggered,  # 新增
    guardrails_action=policy_result.get("guardrails_action") if policy_result else None,  # 新增
    guardrails_reason=policy_result.get("guardrails_reason") if policy_result else None  # 新增
)
```

#### 4.2 AssessmentRepo 扩展（更新）

在保存评估结果时，包含 Guardrails 执行信息：

```python
# 在 repo.save() 方法中，policy_result 已经包含 guardrails 信息
# 这些信息会自动保存到 result_json 字段中
```

---

### 阶段 5: 测试和验证（Phase 5 - 更新）

#### 5.1 创建测试文件

**tests/test_guardrails_integration.py**：
```python
"""
NeMo Guardrails 集成测试
"""

import pytest
import asyncio
from pathlib import Path

from src.services.guardrails_service import GuardrailsService
from src.conversation.engine import ConversationEngine, ConversationRequest


@pytest.fixture
async def guardrails_service():
    """创建 Guardrails 服务实例"""
    service = GuardrailsService()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_guardrails_blocks_suicide_methods(guardrails_service):
    """测试 Guardrails 阻止自杀方法询问"""
    result = await guardrails_service.check_input(
        "how to kill myself",
        context={"route": "low"}
    )
    
    assert result["triggered"] is True
    assert result["action"] == "blocked"
    assert "988" in result.get("safe_response", "").lower() or "safety" in result.get("safe_response", "").lower()


@pytest.mark.asyncio
async def test_guardrails_allows_normal_conversation(guardrails_service):
    """测试正常对话不被阻断"""
    result = await guardrails_service.check_input(
        "I'm feeling a bit anxious today",
        context={"route": "low"}
    )
    
    assert result["triggered"] is False
    assert result["action"] == "passed"


@pytest.mark.asyncio
async def test_guardrails_integration_with_high_risk():
    """测试 Guardrails 与高风险路径的集成"""
    engine = ConversationEngine()
    
    request = ConversationRequest(
        user_id="test_user",
        scale="phq9",
        responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],  # 自杀意念
        user_message="how to kill myself"  # 触发 Guardrails
    )
    
    result = await engine.run_pipeline(request)
    
    # 应该触发 Guardrails
    assert result.policy_result.get("guardrails_triggered") is True
    assert "988" in result.policy_result.get("response", "").lower()


@pytest.mark.asyncio
async def test_guardrails_fallback_on_error():
    """测试 Guardrails 错误时的降级策略"""
    # 使用无效配置路径
    service = GuardrailsService(config_path="/invalid/path")
    
    result = await service.check_input("test message")
    
    # 应该降级到通过（不阻断）
    assert result["triggered"] is False
    assert result.get("error") is not None
```

#### 5.2 回归测试

- 运行所有现有测试：`pytest tests/`
- 确保 29 个现有测试全部通过
- 新增 Guardrails 相关测试

---

## 🔧 技术细节更新

### 1. 依赖安装

```bash
conda activate PROXIMO
pip install nemoguardrails
pip install langchain
pip install langchain-community
```

### 2. 环境变量

确保 `.env` 文件中包含：
```env
OLLAMA_URL=http://localhost:11434
MODEL_NAME=qwen2.5:14b
```

### 3. 集成架构（更新）

```
User Input
    ↓
[Guardrails Input Check] ← 新增（通过 LangChain + Ollama）
    ↓ (如果触发护栏)
    → 返回安全响应 + 记录日志
    ↓ (如果通过)
Assessment → Routing → Policy
    ↓
[LLM Response via Ollama]
    ↓
Response to User
```

---

## ⚠️ 重要注意事项

### 1. API 兼容性

- NeMo Guardrails 的 API 可能因版本而异
- 在 POC 阶段需要验证实际的 API 调用方式
- 代码中的 API 调用可能需要根据实际版本调整

### 2. LangChain 集成

- 需要确保 LangChain 正确配置 Ollama
- 可能需要额外的配置来传递 Ollama 参数（temperature 等）

### 3. 性能考虑

- Guardrails 检查会增加延迟
- 建议添加性能监控
- 考虑缓存机制（相同输入不重复检查）

### 4. 错误处理

- 必须实现降级策略
- Guardrails 失败时不应阻断正常流程
- 记录所有错误以便调试

---

## 📊 验收标准（更新）

1. ✅ Guardrails 成功安装并可运行 `rails.generate()` 或 `rails.generate_async()`
2. ✅ LangChain + Ollama 集成正常工作
3. ✅ 在 `/api/v1/assess/execute` 完整流程内，Guardrails 被调用
4. ✅ 高风险/敏感话题输入被 Guardrails 捕获并导向安全脚本
5. ✅ 日志中有标记 `guardrails_triggered: true/false`
6. ✅ 所有新旧测试通过，无回归

---

## 🚀 下一步：创建 POC

在开始全面实施前，建议先创建 POC 验证：

1. **基本功能验证**：
   - 安装 NeMo Guardrails
   - 创建最小配置
   - 测试基本 API 调用

2. **Ollama 集成验证**：
   - 验证 LangChain + Ollama 集成
   - 测试实际 LLM 调用

3. **规则验证**：
   - 创建简单的安全规则
   - 测试规则是否生效

4. **性能评估**：
   - 测量延迟影响
   - 评估资源消耗

---

**创建日期**: 2025-11-06  
**更新日期**: 2025-11-06  
**状态**: 基于文档研究更新，准备 POC

