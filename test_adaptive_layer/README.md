# Adaptive Layer 测试指南

本文件夹包含 Adaptive Layer（适应层）的测试脚本。

## 📋 测试脚本列表

1. **`test_feedback_collector.py`** - 反馈收集器测试
   - 测试收集 Low/Medium/High Risk 反馈
   - 测试反馈验证
   - 测试获取用户反馈
   - 测试按路由获取反馈
   - 测试反馈统计
   - 测试反馈序列化

2. **`test_history_service.py`** - 历史服务测试
   - 测试获取用户评估历史
   - 测试获取用户反馈
   - 测试获取完整历史（评估 + 反馈）
   - 测试通过服务收集反馈
   - 测试获取反馈统计
   - 测试按路由获取历史

3. **`test_adaptive_integration.py`** - 集成测试
   - 测试对话结束时的反馈收集
   - 测试路由转换时的反馈收集
   - 测试 High Risk 脚本结束时的反馈收集
   - 测试反馈分析（用于自适应学习）
   - 测试反馈存储和检索

## 🚀 运行测试

### 运行单个测试

```bash
# 激活环境
conda activate PROXIMO

# 运行反馈收集器测试
python test_adaptive_layer/test_feedback_collector.py

# 运行历史服务测试
python test_adaptive_layer/test_history_service.py

# 运行集成测试
python test_adaptive_layer/test_adaptive_integration.py
```

### 运行所有测试

```bash
# 使用 pytest（如果可用）
conda run -n PROXIMO pytest test_adaptive_layer/ -v

# 或逐个运行
for test in test_adaptive_layer/test_*.py; do
    conda run -n PROXIMO python "$test"
done
```

## 📝 前置条件

### 所有测试都需要
- PROXIMO conda 环境
- Python 3.10+
- 项目依赖已安装

### 历史服务测试需要
- SQLite 数据库（自动创建）
- AssessmentRepo 可用

## 🧪 测试场景

### 反馈收集
- **Low Risk**：收集满意度（1-5）、接受程度、后续行为
- **Medium Risk**：收集满意度（1-5）、接受程度、后续行为
- **High Risk**：仅收集 `sought_help`（是否寻求帮助），不收集满意度

### 反馈验证
- 满意度必须在 1-5 之间
- 接受程度必须是 accepted/partially/rejected
- 后续行为必须是 hotline/peer_group/appointment/none

### 反馈统计
- 总反馈数
- 路由分布（low/medium/high）
- 平均满意度
- 接受程度分布
- 后续行为分布
- 寻求帮助数

## 📊 预期结果

### 反馈收集器测试
- ✅ 所有风险级别的反馈收集正确
- ✅ 反馈验证正确
- ✅ 反馈查询功能正常
- ✅ 反馈统计准确

### 历史服务测试
- ✅ 历史获取功能正常
- ✅ 反馈收集和检索正常
- ✅ 统计功能正常

### 集成测试
- ✅ 对话流程中的反馈收集正常
- ✅ 路由转换时的反馈收集正常
- ✅ High Risk 特殊处理正确

## ⚠️ 注意事项

1. **High Risk 反馈**：
   - 不收集满意度评分
   - 仅收集 `sought_help`（是否联系热线/寻求帮助）

2. **反馈收集时机**：
   - 每次对话结束
   - 阶段转换时（Low→Medium, Medium→High）
   - 脚本结束（High Risk）

3. **当前阶段**：
   - 仅收集和存储反馈
   - 不做实时调整
   - 未来用于 RLHF（Reinforcement Learning from Human Feedback）

## 🔍 调试

如果测试失败：

1. **反馈验证失败**：
   - 检查满意度是否在 1-5 范围内
   - 检查接受程度和后续行为是否使用正确的枚举值

2. **历史获取失败**：
   - 检查 SQLite 数据库是否可访问
   - 检查 AssessmentRepo 是否正确初始化

3. **统计问题**：
   - 确认反馈数据已正确存储
   - 检查统计计算逻辑

---

**创建日期**：2025-11-07  
**维护者**：开发团队

