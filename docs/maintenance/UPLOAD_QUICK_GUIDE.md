# GitHub 上传快速指南

## 🚀 快速上传步骤

### 前提条件
- ✅ 已创建 GitHub 仓库: https://github.com/Kevin11Kaikai/PROXIMO
- ✅ 本地代码已准备好
- ✅ Git 已安装

---

## 📝 执行步骤

### 1. 打开终端，进入项目目录

```bash
cd D:\PROXIMO\glitch_core
```

### 2. 检查 Git 状态

```bash
git status
```

**如果显示 "not a git repository"**，执行：
```bash
git init
git checkout -b main
```

### 3. 添加远程仓库

```bash
git remote add origin https://github.com/Kevin11Kaikai/PROXIMO.git
```

**如果已经存在**，先删除再添加：
```bash
git remote remove origin
git remote add origin https://github.com/Kevin11Kaikai/PROXIMO.git
```

### 4. 检查要提交的文件

```bash
# 查看将要提交的文件（不实际添加）
git add --dry-run .

# 确认以下文件被正确忽略（不应该出现在列表中）:
# - PsyGUARD-RoBERTa/pytorch_model.bin (模型文件)
# - data/assessments.db (数据库文件)
# - .env (环境变量)
```

### 5. 添加所有文件

```bash
git add .
```

### 6. 检查暂存区

```bash
git status
```

**确认以下重要文件已添加**：
- ✅ `src_new/` 目录
- ✅ `test_*_layer/` 目录
- ✅ `test_integration/` 目录
- ✅ `docs/` 目录
- ✅ `README.md`
- ✅ `.gitignore`

### 7. 提交更改

```bash
git commit -m "feat: Implement PROXIMO Chatbot modular architecture

- Add five-layer architecture (Perception, Control, Conversation, Safety, Adaptive)
- Implement three specialized agents (Low, Medium, High Risk)
- Add comprehensive test suite
- Add technical documentation
- Add PsyGUARD-RoBERTa model download instructions
- Update .gitignore for sensitive files"
```

### 8. 拉取远程更改（处理 GitHub 上的 README）

```bash
git pull origin main --allow-unrelated-histories
```

**如果有冲突**，解决冲突后继续。

### 9. 推送到 GitHub

```bash
git push -u origin main
```

**如果遇到认证问题**，使用 Personal Access Token：
1. 访问: https://github.com/settings/tokens
2. 生成新 token (repo 权限)
3. 使用 token 作为密码

### 10. 验证上传

访问 https://github.com/Kevin11Kaikai/PROXIMO 确认所有文件已上传。

---

## ✅ 完整命令序列（一键执行）

```bash
# 1. 进入项目目录
cd D:\PROXIMO\glitch_core

# 2. 检查/初始化 Git
git status
# 如果是新仓库: git init && git checkout -b main

# 3. 添加远程仓库
git remote add origin https://github.com/Kevin11Kaikai/PROXIMO.git

# 4. 添加所有文件
git add .

# 5. 提交更改
git commit -m "feat: Implement PROXIMO Chatbot modular architecture"

# 6. 拉取远程更改
git pull origin main --allow-unrelated-histories

# 7. 推送到 GitHub
git push -u origin main
```

---

## ⚠️ 常见问题

### 问题 1: 认证失败

**解决方案**: 使用 Personal Access Token
```bash
# 访问 https://github.com/settings/tokens 生成 token
# 推送时使用 token 作为密码
git push -u origin main
# Username: Kevin11Kaikai
# Password: <your_token>
```

### 问题 2: 文件太大

**确认 .gitignore 已包含模型文件**:
```bash
cat .gitignore | grep "pytorch_model.bin"
# 应该显示: PsyGUARD-RoBERTa/pytorch_model.bin
```

### 问题 3: 分支名称不匹配

```bash
# 检查当前分支
git branch

# 如果是 master，重命名为 main
git branch -M main
```

---

## 📋 上传后检查

访问 https://github.com/Kevin11Kaikai/PROXIMO 确认：

- [ ] 所有文件已上传
- [ ] README.md 正确显示
- [ ] 模型文件链接可访问
- [ ] 代码文件完整
- [ ] 文档完整

---

## 🎯 下一步

1. **添加仓库描述**: Settings → About → 添加描述
2. **创建 Release**: Releases → Create a new release
3. **添加 Topics**: Settings → Topics → 添加标签

---

## 📞 需要帮助？

- 详细步骤: 查看 `GITHUB_UPLOAD_STEPS.md`
- 检查清单: 查看 `UPLOAD_CHECKLIST.md`
- GitHub 文档: https://docs.github.com/

