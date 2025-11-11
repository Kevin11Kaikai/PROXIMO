# System Architecture Mapping — Multi-Agent Mental Health Chatbot

本文件将现有代码资产映射到规划中的五层架构，便于后续重构到 `src_new/`。

> 目标：在不立即移动现有文件的前提下，先明确“模块 → 层”的对应关系，并列出重构优先级。

---

## A. Perception Layer — 风险感知层

| 模块/文件 | 现有路径 | 说明 | 重构建议 |
|-----------|-----------|------|-----------|
| 问卷评估 API | `src/assessment/proximo_api.py` | 处理 PHQ-9 / GAD-7 / PSS-10 等量表评估 | 后续在 `src_new/perception/questionnaire_service.py` 中提供封装 |
| 风险配置 | `src/risk` | 风险映射、阈值配置 | 迁移到 `src_new/perception/risk_signals/` 并与 PsyGUARD 输出整合 |
| PsyGUARD-RoBERTa 推理脚本 | `PsyGUARD-RoBERTa/` | 逐句风险评分模型与工具 | 在 `src_new/perception/psyguard_service.py` 中封装模型加载与推理 |
| SessionManager 获取上下文 | `src/conversation/session_manager.py` | 为感知层提供最近的消息窗口 | 保留位置，但在新层中通过接口调用 |

**新增接口建议**：

- `RiskSignal` 协议（Protocol）定义统一输出：`risk_score: float`, `signal_type: Literal["questionnaire", "psyguard", ...]`。
- `PerceptionAggregator` 汇总多信号并输出标准化风险分（0-1）。

---

## B. Reasoning & Control Layer — 推理与控制层

| 模块/文件 | 现有路径 | 说明 | 重构建议 |
|-----------|-----------|------|-----------|
| 风险路由器 | `src/conversation/router.py` | 基于评估结果选择 LOW/MEDIUM/HIGH | 抽离到 `src_new/control/risk_router.py`，接收来自感知层的统一分数 |
| ConversationEngine（流程 orchestrator） | `src/conversation/engine.py` | 串联评估 → 路由 → 策略执行 | 逐步拆分为 `ConversationController` 与下层调用接口 |
| 规则与阈值 | `config/` + `src/risk` | 当前散落于多个文件 | 整合为 `src_new/control/policies.yaml` + `ControlConfig` 类 |

**新增接口建议**：

- `RiskRouter`：接受 `PerceptionSummary`，返回 `RiskRoute`（enum: LOW/MEDIUM/HIGH/CRISIS）。
- `ControlContext`：记录当前路由决策、用户状态、Guardrails 是否启用。

---

## C. Conversation Layer — 对话执行层

| 模块/文件 | 现有路径 | 说明 | 重构建议 |
|-----------|-----------|------|-----------|
| ConversationPolicies | `src/conversation/policies.py` | 定义不同风险级别下的回复策略 | 迁移到 `src_new/conversation/policies/`，拆分为低/中/高风险策略类 |
| SessionManager | `src/conversation/session_manager.py` | 会话上下文管理 | 保持核心实现，提供新接口给 `src_new/conversation/session_service.py` |
| MVP 演示脚本 | `MVP_Scripts/` | 展示完整流程 | 新增 `MVP_Scripts_New/`，调用 `src_new` API |

**新增接口建议**：

- `ConversationAgent` 抽象基类（`LowRiskAgent`, `MediumRiskAgent`, `HighRiskAgent`）。
- `ConversationPipeline`：封装执行流程，调用 Control Layer 决策。

---

## D. Safety & Ethics Layer — 安全与伦理层

| 模块/文件 | 现有路径 | 说明 | 重构建议 |
|-----------|-----------|------|-----------|
| GuardrailsService | `src/services/guardrails_service.py` | NeMo Guardrails 集成封装 | 移动至 `src_new/safety/guardrails_service.py`，保留向后兼容导出 |
| Guardrails 配置 | `config/guardrails/` | Colang 规则、配置文件 | 保持结构，新增 README 解释每个规则 |
| 其他过滤 | 预留 | 后续可集成 LlamaGuard 等 | 在该层添加扩展点 |

**新增接口建议**：

- `SafetyFilter` 接口：可插拔的安全过滤器链。
- `SafetyReport`：记录过滤结果、触发规则、替换响应。

---

## E. Adaptive Layer — 记忆与自适应层

| 模块/文件 | 现有路径 | 说明 | 重构建议 |
|-----------|-----------|------|-----------|
| AssessmentRepo | `src/storage/repo.py` | 持久化评估和策略结果 | 在 `src_new/adaptive/history_service.py` 中封装常用查询 |
| 结构化日志 | `src/core/logging.py` + 日志调用 | 记录用户风险、决策等 | 提供 `AdaptiveMetrics` 收集器 |
| 后续反馈机制 | 待实现 | 基于历史调整策略 | 在该层预留接口 |

**新增接口建议**：

- `AdaptiveFeedbackLoop`：根据历史风险和对话结果调整阈值或策略参数。
- `MemoryStore`：抽象 SessionManager 与 AssessmentRepo 的统一访问方式。

---

## 重构优先级与建议里程碑

1. **文档阶段（当前）**
   - 完成本映射文档✅
   - 在团队同步会议上确认分层定义和接口命名✅

2. **骨架阶段**
   - 在仓库根目录创建 `src_new/` 包结构
   - 建立 `perception/`, `control/`, `conversation/`, `safety/`, `adaptive/`, `shared/`
   - 在每个包内放置占位模块（re-export 现有实现）

3. **迁移阶段**
   - 先迁移易分离模块（GuardrailsService、RiskRouter、PsyGUARD）
   - 每迁移一步，更新 import 并运行对应测试
   - 保留旧路径的代理模块，避免一次性破坏现有接口

4. **收敛阶段**
   - 新增文档、示例脚本指向 `src_new`
   - 考虑逐步弃用旧 `src/` 中的对应模块
   - 根据反馈优化目录和命名

---

## 附录：拟定的 `src_new/` 目录草案

```
src_new/
├── __init__.py
├── perception/
│   ├── __init__.py
│   ├── psyguard_service.py
│   ├── questionnaire_service.py
│   └── signals/
│       └── __init__.py
├── control/
│   ├── __init__.py
│   ├── risk_router.py
│   └── control_context.py
├── conversation/
│   ├── __init__.py
│   ├── pipeline.py
│   ├── session_service.py
│   └── agents/
│       ├── __init__.py
│       ├── low_risk_agent.py
│       ├── medium_risk_agent.py
│       └── high_risk_agent.py
├── safety/
│   ├── __init__.py
│   ├── guardrails_service.py
│   └── filters/
│       └── __init__.py
├── adaptive/
│   ├── __init__.py
│   ├── history_service.py
│   └── feedback.py
└── shared/
    ├── __init__.py
    ├── models.py
    └── utils.py
```

> 注：上述目录为初步草案，实际落地时可根据模块耦合度和依赖顺序进行调整。

---

## 后续行动

1. **骨架实现**：在 `src_new/` 中创建上述包结构和初始占位模块。
2. **接口分层**：为每层编写接口和数据模型（使用 `pydantic` 或 `dataclasses`）。
3. **渐进迁移**：从 Guardrails 和 Risk Router 开始，逐步将逻辑迁移到新层。
4. **脚本更新**：新增 `MVP_Scripts_New/`、`scripts_new/`、`tests_new/`，调用 `src_new` API。
5. **团队准则**：未来新功能优先写到 `src_new/`，旧模块仅做维护。

---

**维护者**：开发团队  
**创建日期**：2025-11-06  
**最后更新**：2025-11-06

