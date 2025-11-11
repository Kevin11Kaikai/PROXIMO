# PROXIMO Chatbot - Quick Start Guide

## 快速开始

### 1. 环境准备

```bash
# 激活 Conda 环境
conda activate PROXIMO

# 安装依赖（如果遇到 pytest-asyncio 错误，先运行此命令更新依赖）
uv sync

# 如果 uv sync 后仍有问题，手动更新 pytest-asyncio
pip install --upgrade pytest-asyncio>=0.24.0
```

### 2. 检查服务

```bash
# 检查 Ollama 服务
python check_ollama.py

# 检查 PsyGUARD 模型
ls PsyGUARD-RoBERTa/pytorch_model.bin
```

### 3. 运行测试

```bash
# 运行所有测试
pytest test_integration/

# 运行特定层测试
pytest test_perception_layer/
pytest test_control_layer/
pytest test_conversation_layer/
```

### 4. 基本使用

```python
from src_new.conversation.pipeline import ConversationPipeline
from src_new.control.control_context import ControlContext

# 初始化 pipeline
pipeline = ConversationPipeline()

# 创建控制上下文
context = ControlContext(
    user_id="user_123",
    route="low",
    rigid_score=0.15
)

# 处理消息
result = await pipeline.process_message(
    user_id="user_123",
    user_message="I've been feeling anxious",
    control_context=context
)

print(result["response"])
```

## 目录结构

```
src_new/
├── perception/          # 风险感知层
│   ├── psyguard_service.py
│   ├── questionnaire_service.py
│   ├── questionnaire_trigger.py
│   └── questionnaire_mapper.py
├── control/             # 控制层
│   ├── risk_router.py
│   ├── route_updater.py
│   └── control_context.py
├── conversation/        # 对话层
│   ├── pipeline.py
│   ├── session_service.py
│   └── agents/
│       ├── low_risk_agent.py
│       ├── medium_risk_agent.py
│       └── high_risk_agent.py
├── safety/              # 安全层
│   ├── guardrails_service.py
│   └── safety_validator.py
├── adaptive/            # 自适应层
│   ├── feedback.py
│   └── history_service.py
└── shared/              # 共享组件
    ├── models.py
    └── utils.py
```

## 测试结构

```
test_perception_layer/   # 感知层测试
test_control_layer/      # 控制层测试
test_conversation_layer/ # 对话层测试
test_safety_layer/       # 安全层测试
test_adaptive_layer/     # 自适应层测试
test_integration/        # 集成测试
```

## 文档

- **架构文档**: `ARCHITECTURE.md`
- **PROXIMO Chatbot 说明**: `README_PROXIMO_CHATBOT.md`
- **变更日志**: `CHANGELOG.md`
- **GitHub 准备**: `GITHUB_PREPARATION.md`

## 常见问题

### Q: 运行测试时遇到 `ModuleNotFoundError: No module named 'backports'` 错误？

A: 这是因为 `pytest-asyncio` 版本过旧。解决方法：

```bash
# 更新 pytest-asyncio 到最新版本
pip install --upgrade pytest-asyncio>=0.24.0

# 或者重新同步所有依赖
uv sync
```

### Q: 如何添加新的 Agent？

A: 在 `src_new/conversation/agents/` 中创建新的 agent 类，然后在 `ConversationPipeline` 中注册。

### Q: 如何修改路由规则？

A: 修改 `src_new/control/risk_router.py` 中的路由逻辑。

### Q: 如何调整温度控制？

A: 修改 `src_new/control/risk_router.py` 中的 `_route_to_rigid_score` 方法。

### Q: 如何添加新的安全规则？

A: 在 `src_new/safety/safety_validator.py` 中添加新的验证规则。

## 下一步

1. 阅读 `ARCHITECTURE.md` 了解系统架构
2. 阅读 `README_PROXIMO_CHATBOT.md` 了解新架构特性
3. 运行集成测试了解系统行为
4. 查看文档了解各层实现细节

