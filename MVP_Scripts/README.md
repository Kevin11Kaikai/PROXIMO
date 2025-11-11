# MVP Alpha 演示脚本

本文件夹包含专门用于演示和测试 MVP Alpha 功能的 Python 脚本。

## 📋 脚本列表

### 核心演示脚本

1. **`demo_complete_pipeline.py`** - 完整对话管道演示
   - 演示完整的 MVP Alpha 流程：Assessment → Routing → Policy Execution
   - 展示低风险、中等风险、高风险（硬锁定）三种场景
   - 展示 Session Management 和 Persistence 功能

2. **`demo_session_manager.py`** - SessionManager 演示
   - 演示多轮对话上下文管理
   - 展示自动修剪到最近 6 轮的功能
   - 展示多用户独立会话

3. **`demo_assessment_repo.py`** - AssessmentRepo 演示
   - 演示评估结果的持久化
   - 展示历史记录查询
   - 展示自杀意念标志处理

4. **`demo_multi_turn_conversation.py`** - 多轮对话场景演示
   - 演示完整的多轮对话流程
   - 展示 SessionManager 和 AssessmentRepo 的集成
   - 展示上下文在对话中的传递

5. **`demo_history_query.py`** - 历史查询功能演示
   - 演示如何查询评估历史记录
   - 展示限制返回数量、查看标志等功能
   - 展示多用户数据隔离

6. **`demo_guardrails_integration.py`** - NeMo Guardrails 集成测试
   - 测试 Guardrails 服务初始化
   - 测试正常对话场景（不应触发 Guardrails）
   - 测试高风险场景（应触发 Guardrails）
   - 测试安全检查和响应过滤功能
   - 测试与 ConversationEngine 的完整集成

7. **`guardrails_demo.py`** - NeMo Guardrails FastAPI 演示应用
   - 提供 Web 界面进行实时测试
   - 测试安全检查功能
   - 测试响应过滤功能
   - 测试完整对话管道
   - 提供友好的可视化界面

### 主脚本

8. **`run_all_demos.py`** - 运行所有演示
   - 依次运行所有演示脚本
   - 提供完整的演示总结

## 🚀 使用方法

### 运行单个演示

```bash
# 使用 conda run（推荐）
conda run -n PROXIMO python MVP_Scripts/demo_complete_pipeline.py

# 或先激活环境
conda activate PROXIMO
python MVP_Scripts/demo_complete_pipeline.py
```

### 运行所有演示

```bash
conda run -n PROXIMO python MVP_Scripts/run_all_demos.py
```

### 运行 Guardrails Web 演示

```bash
# 启动 FastAPI 演示应用
conda run -n PROXIMO python MVP_Scripts/guardrails_demo.py

# 然后在浏览器中访问
# http://localhost:8001
```

**功能**：
- 🖥️ 友好的 Web 界面
- 🧪 实时测试各种场景
- 📊 可视化测试结果
- 📚 自动生成的 API 文档（/docs）

**测试指南**：
详细的测试步骤和验证方法请参考 `MVP_Scripts/GUARDRAILS_DEMO_TEST_GUIDE.md`

## 📝 演示脚本说明

### 1. demo_complete_pipeline.py

演示 MVP Alpha 的完整对话管道，包括：
- **场景 1**: 低风险场景（Minimal Severity）
- **场景 2**: 中等风险场景（Moderate Severity）
- **场景 3**: 高风险场景（硬锁定 - 自杀意念）

**功能展示**:
- Assessment（评估）
- Routing（路由决策）
- Policy Execution（策略执行）
- Session Management（会话管理）
- Persistence（持久化）

### 2. demo_session_manager.py

演示 SessionManager 的核心功能：
- 多轮对话上下文存储
- 自动修剪到最近 6 轮
- 多用户独立会话
- 获取最近 N 轮对话
- 清空会话

### 3. demo_assessment_repo.py

演示 AssessmentRepo 的持久化功能：
- 保存评估结果到 SQLite
- 查询历史记录
- 检查是否有先前评估
- 自杀意念标志处理
- 多评估记录管理

**注意**: 此脚本使用临时数据库，演示结束后会自动清理。

### 4. demo_multi_turn_conversation.py

演示完整的多轮对话场景：
- 第 1 轮：初次接触（GAD-7 默认）
- 第 2 轮：继续对话（使用会话上下文）
- 第 3 轮：再次对话（上下文自动修剪）
- 检查评估历史记录

### 5. demo_history_query.py

演示历史查询功能：
- 查询所有历史记录
- 限制返回数量
- 查看自杀意念标志
- 查看完整评估详情
- 查询不同用户的历史

## ⚙️ 环境要求

- Python 3.10+
- PROXIMO conda 环境
- 所有项目依赖已安装（运行 `uv sync`）

### Ollama 服务（可选）

部分演示需要 Ollama 服务来生成 LLM 响应。如果 Ollama 不可用，系统会自动使用回退响应，评估和路由功能仍然正常工作。

**启动 Ollama**:
```bash
ollama serve
ollama pull llama3.1:8b  # 或您配置的模型
```

## 📊 MVP Alpha 核心功能

这些演示脚本展示了 MVP Alpha 的以下核心功能：

1. ✅ **Multi-turn context management** - SessionManager
2. ✅ **Persistence & history** - AssessmentRepo with SQLite
3. ✅ **Wireframe-aligned policies** - Low/Medium/High routes
4. ✅ **Safety lock** - Fixed safety script for high-risk scenarios
5. ✅ **HTTP API** - Complete endpoints with validation
6. ✅ **Structured logging** - All requests logged with key metrics

## 🔍 与测试的区别

- **测试文件** (`tests/`): 用于自动化测试，验证功能正确性
- **演示脚本** (`MVP_Scripts/`): 用于手动演示和展示功能，更注重可读性和展示效果

## 📝 注意事项

1. **数据库**: 大部分演示使用默认数据库 `data/assessments.db`，`demo_assessment_repo.py` 使用临时数据库
2. **Ollama 服务**: 如果 Ollama 不可用，演示仍然可以运行，但会使用回退响应
3. **会话数据**: 演示脚本会创建测试会话，不会影响实际用户数据
4. **Guardrails 集成**: `demo_guardrails_integration.py` 需要 NeMo Guardrails 和 LangChain 已安装，需要 Ollama 服务运行

## 🎯 下一步

运行这些演示后，您可以：
1. 查看 `docs/developer/mvp_alpha_implementation_summary.md` 了解完整实现
2. 查看 `docs/developer/nemo_guardrails_integration_plan_v2.md` 了解 Guardrails 集成详情
3. 运行 `pytest tests/` 查看自动化测试
4. 查看 `src/api/routes/assessment.py` 了解 HTTP API 端点
5. 查看 `config/guardrails/` 了解 Guardrails 配置和规则

---

**创建日期**: 2025-01-XX  
**维护者**: 开发团队

