# Control Layer 测试指南

本文件夹包含 Control Layer（推理与控制层）的测试脚本。

## 📋 测试脚本列表

1. **`test_risk_router.py`** - 风险路由测试
   - 测试基于问卷的路由决策
   - 测试聊天内容优先级
   - 测试向后兼容性（Legacy Assessment）
   - 测试 Rigid Score 计算

2. **`test_route_updater.py`** - 路由更新逻辑测试
   - 测试 Low → Medium 升级
   - 测试 Medium 不降级规则
   - 测试 High 不降级规则
   - 测试直接升级到 High (>= 0.95)
   - 测试辅助方法（should_upgrade, get_upgrade_target）

3. **`test_control_context.py`** - ControlContext 数据类测试
   - 测试 ControlContext 创建
   - 测试感知层数据存储
   - 测试路由更新方法
   - 测试 Extras 字段

4. **`test_control_integration.py`** - 集成测试
   - 测试完整的 Control Layer 工作流程
   - 测试路由决策 → 路由更新 → 上下文管理

## 🚀 运行测试

### 运行单个测试

```bash
# 激活环境
conda activate PROXIMO

# 运行风险路由测试
python test_control_layer/test_risk_router.py

# 运行路由更新测试
python test_control_layer/test_route_updater.py

# 运行 ControlContext 测试
python test_control_layer/test_control_context.py

# 运行集成测试（需要 PsyGUARD 模型）
python test_control_layer/test_control_integration.py
```

### 运行所有测试

```bash
# 使用 pytest（如果可用）
conda run -n PROXIMO pytest test_control_layer/ -v

# 或逐个运行
for test in test_control_layer/test_*.py; do
    conda run -n PROXIMO python "$test"
done
```

## 📝 前置条件

### 所有测试都需要
- PROXIMO conda 环境
- Python 3.10+
- 项目依赖已安装

### 集成测试需要
- PsyGUARD 模型文件（可选，如果未加载会使用占位分数）

## 🧪 测试场景

### 场景 1: 初始路由决策
- 基于问卷结果（PHQ-9 + GAD-7）进行路由
- 考虑聊天内容优先级
- 处理 PHQ-9 Q9 特殊规则

### 场景 2: 路由更新（Low → Medium）
- 用户在 Low Risk 路径
- PsyGUARD 检测到 Medium Risk (>= 0.70)
- 立即升级到 Medium

### 场景 3: Medium 不降级
- 用户在 Medium Risk 路径
- 即使用户情绪好转（PsyGUARD 分数降低）
- 仍然保持 Medium Risk

### 场景 4: High 不降级
- 用户在 High Risk 路径
- 即使 PsyGUARD 分数降低
- 必须完成固定脚本，不能降级

## 📊 预期结果

### 风险路由测试
- ✅ 问卷映射正确
- ✅ 聊天内容优先级正确
- ✅ PHQ-9 Q9 特殊规则生效
- ✅ Rigid Score 计算正确

### 路由更新测试
- ✅ 单向升级逻辑正确
- ✅ 不降级规则正确
- ✅ 直接 High 升级正确

### ControlContext 测试
- ✅ 数据存储正确
- ✅ 路由更新方法正确
- ✅ 时间戳管理正确

## ⚠️ 注意事项

1. **PHQ-9 Q9 特殊规则**：如果 PHQ-9 第9题（自杀念头）>= 1，无论总分如何，都会返回 High Risk
2. **聊天内容优先级**：如果聊天内容风险高，会覆盖问卷结果
3. **不降级规则**：Medium 和 High Risk 路径不会降级，即使 PsyGUARD 分数降低

## 🔍 调试

如果测试失败：

1. **检查路由逻辑**：
   - 确认 PHQ-9 Q9 特殊规则是否正确应用
   - 确认聊天内容优先级是否正确

2. **检查阈值**：
   - MEDIUM_RISK_THRESHOLD = 0.70
   - HIGH_RISK_DIRECT_THRESHOLD = 0.95

3. **查看详细错误**：
   - 测试脚本会打印详细的错误信息
   - 检查控制台输出

---

**创建日期**：2025-11-07  
**维护者**：开发团队

