# Safety Layer 测试指南

本文件夹包含 Safety Layer（安全与伦理层）的测试脚本。

## 📋 测试脚本列表

1. **`test_safety_validator.py`** - 安全验证器测试
   - 测试响应内容验证
   - 测试固定脚本验证
   - 测试用户消息安全检查
   - 测试禁止模式检测

2. **`test_guardrails_service.py`** - Guardrails 服务测试
   - 测试服务初始化
   - 测试用户输入安全检查
   - 测试响应过滤
   - 测试固定脚本验证
   - 测试 High Risk 脚本保护
   - 测试安全响应生成

3. **`test_safety_integration.py`** - 集成测试
   - 测试 Low Risk 对话 + 安全检查
   - 测试 High Risk 固定脚本保护
   - 测试危机检测
   - 测试所有路由的安全监控

## 🚀 运行测试

### 运行单个测试

```bash
# 激活环境
conda activate PROXIMO

# 运行安全验证器测试（不需要 Ollama）
python test_safety_layer/test_safety_validator.py

# 运行 Guardrails 服务测试（需要 Ollama + NeMo Guardrails）
python test_safety_layer/test_guardrails_service.py

# 运行集成测试（需要 Ollama）
python test_safety_layer/test_safety_integration.py
```

### 运行所有测试

```bash
# 使用 pytest（如果可用）
conda run -n PROXIMO pytest test_safety_layer/ -v

# 或逐个运行
for test in test_safety_layer/test_*.py; do
    conda run -n PROXIMO python "$test"
done
```

## 📝 前置条件

### 所有测试都需要
- PROXIMO conda 环境
- Python 3.10+
- 项目依赖已安装

### Guardrails 服务测试需要
- Ollama 服务运行
- NeMo Guardrails 已安装
- Guardrails 配置文件（`config/guardrails/`）

### 安全验证器测试
- **不需要** Ollama（纯逻辑测试）

## 🧪 测试场景

### 安全验证器
- **响应验证**：检查响应是否包含禁止内容或缺少必需元素
- **固定脚本验证**：验证 High Risk 固定脚本是否符合安全要求
- **用户消息检查**：检测用户消息中的危机关键词
- **禁止模式检测**：识别包含自杀方法等禁止内容的响应

### Guardrails 服务
- **初始化**：测试 Guardrails 服务是否正确初始化
- **安全检查**：测试用户输入的安全检查
- **响应过滤**：测试响应过滤功能
- **脚本保护**：确保 High Risk 固定脚本不被修改

### 集成测试
- **对话集成**：测试 Safety Layer 与 Conversation Layer 的集成
- **危机检测**：测试危机关键词检测
- **全路由监控**：测试所有风险级别的安全监控

## 📊 预期结果

### 安全验证器测试
- ✅ 响应验证正确
- ✅ 固定脚本验证通过
- ✅ 危机关键词检测正确
- ✅ 禁止模式检测正确

### Guardrails 服务测试
- ✅ 服务初始化成功（如果 Ollama 运行）
- ✅ 安全检查功能正常
- ✅ 响应过滤功能正常
- ✅ High Risk 脚本保护生效

### 集成测试
- ✅ 对话流程中安全检查正常
- ✅ High Risk 脚本不被修改
- ✅ 危机检测正确触发

## ⚠️ 注意事项

1. **High Risk 脚本保护**：
   - 固定脚本不应该被 Guardrails 修改
   - 如果检测到修改尝试，应该记录警告但保持原脚本

2. **危机检测**：
   - 检测到危机关键词时，应该立即触发安全响应
   - 不应该继续正常对话流程

3. **Guardrails 初始化**：
   - 如果 Ollama 未运行，Guardrails 服务会初始化失败
   - 测试会跳过需要 Guardrails 的部分

## 🔍 调试

如果测试失败：

1. **Guardrails 初始化失败**：
   - 检查 Ollama 服务是否运行
   - 检查 NeMo Guardrails 配置是否正确
   - 查看日志中的错误信息

2. **脚本验证失败**：
   - 检查固定脚本是否包含所有必需元素（988, crisis, safety, emergency, help）
   - 确认脚本不包含禁止内容

3. **危机检测问题**：
   - 检查危机关键词列表是否完整
   - 确认关键词匹配逻辑正确

---

**创建日期**：2025-11-07  
**维护者**：开发团队

