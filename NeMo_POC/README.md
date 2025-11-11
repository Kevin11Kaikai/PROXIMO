# NeMo Guardrails POC（概念验证）

本文件夹包含 NeMo Guardrails 集成的概念验证脚本，用于验证基本功能和与 Ollama 的集成。

## 📋 POC 脚本列表

### 1. `01_check_installation.py`
- 检查 NeMo Guardrails 和相关依赖是否已安装
- 验证导入是否正常

### 2. `02_test_langchain_ollama.py`
- 测试 LangChain 与 Ollama 的集成
- 验证基本的 LLM 调用功能

### 3. `03_test_guardrails_basic.py`
- 测试 NeMo Guardrails 的基本功能
- 验证 Rails 实例的创建和初始化

### 4. `04_test_guardrails_with_ollama.py`
- 测试 NeMo Guardrails 通过 LangChain 使用 Ollama
- 验证完整的集成链路

### 5. `05_test_safety_rules.py`
- 测试简单的安全规则（自杀预防）
- 验证规则是否生效

### 6. `run_all_poc.py`
- 运行所有 POC 脚本
- 提供完整的验证报告

## 🚀 使用方法

### 运行单个 POC

```bash
conda activate PROXIMO
python NeMo_POC/01_check_installation.py
```

### 运行所有 POC

```bash
conda activate PROXIMO
python NeMo_POC/run_all_poc.py
```

## 📝 注意事项

1. **环境要求**：
   - Python 3.10+
   - PROXIMO conda 环境
   - Ollama 服务运行中

2. **依赖安装**：
   ```bash
   pip install nemoguardrails
   pip install langchain
   pip install langchain-community
   ```

3. **配置要求**：
   - 确保 `.env` 文件中有 `OLLAMA_URL` 和 `MODEL_NAME`
   - 确保 Ollama 服务正在运行

## 📊 POC 目标

验证以下功能：
- ✅ NeMo Guardrails 可以正常安装和导入
- ✅ LangChain 可以与 Ollama 集成
- ✅ NeMo Guardrails 可以通过 LangChain 使用 Ollama
- ✅ 可以创建和加载 Guardrails 规则
- ✅ 安全规则可以正确触发

---

**创建日期**: 2025-11-06  
**状态**: POC 阶段

