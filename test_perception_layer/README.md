# Perception Layer 测试指南

本文件夹包含 Perception Layer 的测试脚本。

## 📋 测试脚本列表

1. **`test_psyguard_service.py`** - PsyGUARD 服务测试
   - 测试模型加载
   - 测试风险评分功能
   - 测试阈值常量
   - 测试禁用服务行为

2. **`test_questionnaire_trigger.py`** - 问卷触发逻辑测试
   - 测试轮次计数触发
   - 测试自杀意图提前触发
   - 测试极高风险直接触发
   - 测试触发优先级顺序

3. **`test_questionnaire_mapper.py`** - 问卷映射规则测试
   - 测试 PHQ-9 分数映射
   - 测试 GAD-7 分数映射
   - 测试路由合并逻辑
   - 测试聊天内容优先级
   - 测试评估结果映射

4. **`test_perception_integration.py`** - 集成测试
   - 测试完整的 Perception Layer 工作流程
   - 测试 PsyGUARD → 问卷触发 → 问卷评估 → 路由映射

## 🚀 运行测试

### 运行单个测试

```bash
# 激活环境
conda activate PROXIMO

# 运行问卷映射测试（不需要模型）
python test_perception_layer/test_questionnaire_mapper.py

# 运行问卷触发测试（不需要模型）
python test_perception_layer/test_questionnaire_trigger.py

# 运行 PsyGUARD 服务测试（需要模型文件）
python test_perception_layer/test_psyguard_service.py

# 运行集成测试（需要模型和 Ollama）
python test_perception_layer/test_perception_integration.py
```

### 运行所有测试

```bash
# 使用 pytest（如果可用）
conda run -n PROXIMO pytest test_perception_layer/ -v

# 或逐个运行
for test in test_perception_layer/test_*.py; do
    conda run -n PROXIMO python "$test"
done
```

## 📝 前置条件

### 所有测试都需要
- PROXIMO conda 环境
- Python 3.10+
- 项目依赖已安装

### PsyGUARD 测试需要
- PsyGUARD-RoBERTa 模型文件在 `PsyGUARD-RoBERTa/` 目录
- `pytorch_model.bin` 文件存在
- PyTorch 和 transformers 已安装

### 集成测试需要
- 上述所有条件
- Ollama 服务运行（用于问卷评估）

## 🧪 测试场景

### 场景 1: 正常流程
- 5 轮对话后触发问卷
- 问卷评估 → 路由映射

### 场景 2: 提前触发
- 检测到自杀意图（PsyGUARD >= 0.80）
- 立即触发问卷

### 场景 3: 极高风险
- 检测到极高风险（PsyGUARD >= 0.95）
- 立即触发问卷并设置 High Risk

## 📊 预期结果

### 问卷映射测试
- ✅ 所有映射规则正确
- ✅ PHQ-9 Q9 特殊规则生效
- ✅ 路由合并逻辑正确
- ✅ 聊天内容优先级正确

### 问卷触发测试
- ✅ 轮次计数触发正确
- ✅ 提前触发逻辑正确
- ✅ 优先级顺序正确

### PsyGUARD 测试
- ✅ 模型加载成功（如果模型文件存在）
- ✅ 风险评分在 [0, 1] 范围内
- ✅ 阈值检测正确

## ⚠️ 注意事项

1. **模型文件**：如果 PsyGUARD 模型未加载，相关测试会被跳过
2. **Ollama 服务**：集成测试需要 Ollama 运行，否则问卷评估会失败
3. **测试数据**：测试使用模拟数据，实际使用需要真实用户输入

## 🔍 调试

如果测试失败：

1. **检查模型文件**：
   ```bash
   ls PsyGUARD-RoBERTa/pytorch_model.bin
   ```

2. **检查 Ollama 服务**：
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **查看详细错误**：
   - 测试脚本会打印详细的错误信息
   - 检查控制台输出

---

**创建日期**：2025-11-07  
**维护者**：开发团队

