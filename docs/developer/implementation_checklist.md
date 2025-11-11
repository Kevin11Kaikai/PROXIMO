# 五层架构实现检查清单

基于 `five_layer_workflow_design.md` 的详细规则，本文档提供实现检查清单。

**创建日期**：2025-11-07  
**状态**：准备实现

---

## ✅ 技术细节确认状态

- [x] PsyGUARD 阈值设置（0.80/0.95/0.70/0.40）
- [x] 问卷映射规则（PHQ-9/GAD-7，第9题特殊规则）
- [x] Medium Risk Agent 状态机（抗拒关键词、5 轮说服）
- [x] 反馈收集时机（对话结束、阶段转换、脚本结束）

---

## 📋 实现检查清单

### Phase 1: Perception Layer

#### PsyGUARD 服务集成
- [ ] 实现 `PsyGuardService.score()` 方法
- [ ] 配置阈值常量：
  - [ ] `SUICIDE_INTENT_THRESHOLD = 0.80`
  - [ ] `HIGH_RISK_DIRECT_THRESHOLD = 0.95`
  - [ ] `MEDIUM_RISK_THRESHOLD = 0.70`
  - [ ] `LOW_RISK_CLEAR_THRESHOLD = 0.40`
- [ ] 实现逐句评分逻辑（所有对话轮次）
- [ ] 集成 PsyGUARD-RoBERTa 模型加载

#### 问卷触发逻辑
- [ ] 实现对话轮次计数
- [ ] 实现提前触发条件（PsyGUARD >= 0.80）
- [ ] 实现默认触发条件（5 轮后）
- [ ] 实现问卷评估调用（GAD-7 + PHQ-9）

#### 问卷映射规则
- [ ] 实现 PHQ-9 映射（0-9→Low, 10-14→Medium, 15+→High）
- [ ] 实现 PHQ-9 第9题特殊规则（≥1 → High）
- [ ] 实现 GAD-7 映射（0-9→Low, 10-14→Medium, 15+→High）
- [ ] 实现综合规则（取较高等级）
- [ ] 实现聊天内容优先级逻辑

---

### Phase 2: Control Layer

#### 风险路由
- [ ] 实现 `RiskRouter.decide()` 方法
- [ ] 实现问卷结果映射
- [ ] 实现聊天内容优先级判断
- [ ] 返回 `RiskRoutingResult`（route, rigid_score, metadata）

#### 风险级别调整
- [ ] 实现 `update_route()` 方法
- [ ] 实现升级规则（Low → Medium，阈值 0.70）
- [ ] 实现不降级规则（Medium 不降级）
- [ ] 实现 High Risk 锁定（不能降级）
- [ ] 实现极高风险直接升级（≥0.95 → High）

#### Control Context
- [ ] 实现 `ControlContext` 数据类
- [ ] 记录用户状态、路由决策、Guardrails 启用状态

---

### Phase 3: Conversation Layer

#### Low Risk Agent
- [ ] 实现 `LowRiskAgent.respond()` 方法
- [ ] 实现自由对话逻辑
- [ ] 实现 Coping Skills 建议
- [ ] 实现 goodbye 检测和结束逻辑

#### Medium Risk Agent
- [ ] 实现状态机（INITIAL → ADDRESSING → RESOURCES/JOINED → ENDED）
- [ ] 实现抗拒关键词检测（privacy / time / stigma / doubt）
- [ ] 实现说服流程（最多 5 轮）
- [ ] 实现接受/拒绝处理
- [ ] 实现自助资源提供逻辑

#### High Risk Agent
- [ ] 实现固定脚本加载
- [ ] 实现脚本逐句执行
- [ ] 实现 Crisis Hotline 提示（988）
- [ ] 实现紧急会面建议
- [ ] 确保不允许偏离脚本

#### Session Service
- [ ] 封装 SessionManager 访问
- [ ] 提供对话历史查询接口

---

### Phase 4: Safety Layer

#### Guardrails 集成
- [ ] 确保 Guardrails 时刻监控所有对话
- [ ] 实现 High Risk 脚本安全验证（设计阶段）
- [ ] 实现运行时二次确认（不修改脚本内容）
- [ ] 记录 Guardrails 使用情况

---

### Phase 5: Adaptive Layer

#### 反馈收集
- [ ] 实现 `FeedbackScore` 数据类
- [ ] 实现反馈收集触发逻辑：
  - [ ] 对话结束时收集
  - [ ] 阶段转换时收集（Low→Medium, Medium→High）
  - [ ] 脚本结束时收集（High Risk）
- [ ] 实现 High Risk 特殊处理（仅记录 `sought_help`）
- [ ] 实现反馈存储（AssessmentRepo 或新表）

#### History Service
- [ ] 封装 AssessmentRepo 常用查询
- [ ] 提供历史记录访问接口

---

### Phase 6: Pipeline 集成

#### Conversation Pipeline
- [ ] 实现完整的五层流程串联
- [ ] 实现逐句 PsyGUARD 评分
- [ ] 实现问卷触发和评估
- [ ] 实现风险路由和级别调整
- [ ] 实现 Agent 选择和响应生成
- [ ] 实现 Guardrails 监控
- [ ] 实现反馈收集

#### 错误处理
- [ ] PsyGUARD 服务失败时的降级策略
- [ ] 问卷评估失败时的处理
- [ ] Guardrails 失败时的处理
- [ ] Agent 响应生成失败时的处理

---

### Phase 7: 测试

#### 单元测试
- [ ] Perception Layer 测试（PsyGUARD、问卷触发、映射规则）
- [ ] Control Layer 测试（路由、级别调整）
- [ ] Conversation Agents 测试（三种 Agent）
- [ ] Safety Layer 测试（Guardrails 监控）
- [ ] Adaptive Layer 测试（反馈收集）

#### 集成测试
- [ ] 场景 1：正常流程（5 轮后触发问卷）
- [ ] 场景 2：提前触发问卷（检测到自杀意图）
- [ ] 场景 3：风险升级（Low → Medium）
- [ ] 场景 4：High Risk 固定脚本执行
- [ ] 场景 5：Medium Risk 说服流程（接受/拒绝）

#### 端到端测试
- [ ] 完整对话流程测试
- [ ] 多轮对话测试
- [ ] 风险级别转换测试
- [ ] 反馈收集测试

---

## 🎯 实现优先级

### 第一优先级（核心功能）
1. Perception Layer：PsyGUARD 集成和问卷触发
2. Control Layer：风险路由和级别调整
3. Conversation Layer：三种 Agent 基础实现
4. Pipeline：完整流程串联

### 第二优先级（增强功能）
1. Medium Risk Agent 状态机完善
2. Safety Layer Guardrails 集成
3. Adaptive Layer 反馈收集

### 第三优先级（优化和扩展）
1. 错误处理和降级策略完善
2. 性能优化
3. RLHF 数据准备

---

## 📝 实现注意事项

1. **阈值配置**：所有阈值应该放在配置文件中，便于调整
2. **日志记录**：每个关键决策点都要记录日志
3. **数据持久化**：风险评估、路由决策、反馈都要持久化
4. **向后兼容**：新实现应该与现有 `src/` 代码兼容
5. **测试驱动**：先写测试，再实现功能

---

**维护者**：开发团队  
**最后更新**：2025-11-07

