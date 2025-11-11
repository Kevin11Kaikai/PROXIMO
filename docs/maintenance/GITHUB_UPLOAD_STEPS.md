# GitHub 上传步骤指南

## 📋 准备工作

### 1. 确认仓库信息

- **仓库地址**: https://github.com/Kevin11Kaikai/PROXIMO
- **仓库状态**: 已创建，只有一个 README
- **目标**: 上传 PROXIMO Chatbot 代码

### 2. 确认本地环境

```bash
# 确认当前目录
pwd
# 应该显示: D:\PROXIMO\glitch_core

# 确认 Git 已安装
git --version

# 确认 Conda 环境
conda env list
```

---

## 🚀 上传步骤

### Step 1: 初始化 Git 仓库（如果还没有）

```bash
# 检查 Git 状态
git status

# 如果显示 "not a git repository"，则初始化
git init

# 如果已经是 Git 仓库，跳过此步
```

### Step 2: 检查当前 Git 状态

```bash
# 查看当前状态
git status

# 查看当前分支
git branch

# 如果没有分支，创建 main 分支
git checkout -b main
```

### Step 3: 添加远程仓库

```bash
# 添加 GitHub 远程仓库
git remote add origin https://github.com/Kevin11Kaikai/PROXIMO.git

# 如果已经存在，先删除再添加
git remote remove origin
git remote add origin https://github.com/Kevin11Kaikai/PROXIMO.git

# 验证远程仓库
git remote -v
# 应该显示:
# origin  https://github.com/Kevin11Kaikai/PROXIMO.git (fetch)
# origin  https://github.com/Kevin11Kaikai/PROXIMO.git (push)
```

### Step 4: 检查要提交的文件

```bash
# 查看将要提交的文件（不实际添加）
git add --dry-run .

# 查看被忽略的文件
git status --ignored

# 确认以下文件被正确忽略:
# - *.db (数据库文件)
# - *.bin (模型文件)
# - .env (环境变量)
# - __pycache__/ (Python 缓存)
# - htmlcov/ (测试覆盖率报告)
```

### Step 5: 添加文件到 Git

```bash
# 方式 1: 添加所有文件（推荐，.gitignore 会自动排除）
git add .

# 方式 2: 选择性添加（如果方式 1 有问题）
git add src_new/
git add test_*_layer/
git add test_integration/
git add docs/
git add README_PROXIMO_CHATBOT.md
git add ARCHITECTURE.md
git add CHANGELOG.md
git add CONTRIBUTING.md
git add GITHUB_PREPARATION.md
git add QUICK_START_PROXIMO.md
git add .gitignore
git add .gitattributes
git add pyproject.toml
git add environment.yml
git add env.example
git add README.md
git add Makefile
git add docker-compose.yml
git add Dockerfile
```

### Step 6: 检查暂存区文件

```bash
# 查看已暂存的文件
git status

# 查看将要提交的文件列表
git diff --cached --name-only

# 确认以下重要文件已添加:
# - src_new/ (新架构代码)
# - test_*_layer/ (测试文件)
# - test_integration/ (集成测试)
# - docs/ (文档)
# - README.md (主 README)
# - .gitignore (忽略规则)
```

### Step 7: 提交更改

```bash
# 创建提交
git commit -m "feat: Implement PROXIMO Chatbot modular architecture

- Add five-layer architecture (Perception, Control, Conversation, Safety, Adaptive)
- Implement three specialized agents (Low, Medium, High Risk)
- Add comprehensive test suite for all layers
- Add technical documentation
- Add PsyGUARD-RoBERTa model download instructions
- Update .gitignore for sensitive files and large model files"
```

### Step 8: 拉取远程更改（如果有）

```bash
# 拉取远程仓库的更改（GitHub 上的 README）
git pull origin main --allow-unrelated-histories

# 如果有冲突，解决冲突后继续
# 如果没有冲突，继续下一步
```

### Step 9: 推送到 GitHub

```bash
# 推送到远程仓库
git push -u origin main

# 如果遇到错误，可能需要强制推送（谨慎使用）
# git push -u origin main --force
```

### Step 10: 验证上传

1. **访问 GitHub 仓库**: https://github.com/Kevin11Kaikai/PROXIMO
2. **检查文件**: 确认所有文件已上传
3. **检查 README**: 确认 README.md 显示正确
4. **检查 .gitignore**: 确认敏感文件被忽略

---

## 🔍 常见问题解决

### 问题 1: 文件太大无法上传

**错误信息**: `remote: error: File PsyGUARD-RoBERTa/pytorch_model.bin is 500.00 MB; this exceeds GitHub's file size limit of 100.00 MB`

**解决方案**:
```bash
# 1. 确认 .gitignore 已包含模型文件
cat .gitignore | grep "pytorch_model.bin"

# 2. 如果文件已经被添加，从 Git 中移除（但保留本地文件）
git rm --cached PsyGUARD-RoBERTa/pytorch_model.bin

# 3. 确认 .gitignore 规则
echo "PsyGUARD-RoBERTa/pytorch_model.bin" >> .gitignore

# 4. 重新提交
git add .gitignore
git commit -m "chore: Exclude model files from repository"
git push origin main
```

### 问题 2: 认证失败

**错误信息**: `remote: Permission denied (publickey)` 或 `Authentication failed`

**解决方案**:
```bash
# 方式 1: 使用 HTTPS（推荐）
git remote set-url origin https://github.com/Kevin11Kaikai/PROXIMO.git

# 方式 2: 使用 Personal Access Token
# 1. 访问: https://github.com/settings/tokens
# 2. 生成新 token
# 3. 使用 token 作为密码
git push origin main
# Username: Kevin11Kaikai
# Password: <your_token>
```

### 问题 3: 分支名称不匹配

**错误信息**: `error: src refspec main does not match any`

**解决方案**:
```bash
# 检查当前分支
git branch

# 如果显示 master，重命名为 main
git branch -M main

# 或者直接推送到 master
git push -u origin master
```

### 问题 4: 需要合并远程更改

**错误信息**: `error: failed to push some refs to 'origin'`

**解决方案**:
```bash
# 拉取远程更改
git pull origin main --rebase

# 或者
git pull origin main --allow-unrelated-histories

# 解决冲突后推送
git push origin main
```

---

## ✅ 上传后检查清单

### 1. 文件检查

- [ ] `src_new/` 目录已上传
- [ ] `test_*_layer/` 目录已上传
- [ ] `test_integration/` 目录已上传
- [ ] `docs/` 目录已上传
- [ ] `README.md` 已更新
- [ ] `.gitignore` 已配置
- [ ] `pyproject.toml` 已上传

### 2. 排除检查

- [ ] `PsyGUARD-RoBERTa/pytorch_model.bin` 未上传（大文件）
- [ ] `data/assessments.db` 未上传（数据库文件）
- [ ] `.env` 未上传（环境变量）
- [ ] `__pycache__/` 未上传（Python 缓存）
- [ ] `htmlcov/` 未上传（测试覆盖率）

### 3. 文档检查

- [ ] `README.md` 包含模型下载链接
- [ ] `README_PROXIMO_CHATBOT.md` 已上传
- [ ] `ARCHITECTURE.md` 已上传
- [ ] `CHANGELOG.md` 已上传
- [ ] `CONTRIBUTING.md` 已上传

### 4. 链接检查

- [ ] 模型下载链接正确: https://huggingface.co/qiuhuachuan/PsyGUARD-RoBERTa
- [ ] GitHub 仓库链接正确: https://github.com/Kevin11Kaikai/PROXIMO
- [ ] 所有文档链接正常

---

## 📝 完整的命令序列（一键执行）

```bash
# 1. 检查状态
git status

# 2. 添加远程仓库
git remote add origin https://github.com/Kevin11Kaikai/PROXIMO.git

# 3. 添加所有文件
git add .

# 4. 提交更改
git commit -m "feat: Implement PROXIMO Chatbot modular architecture

- Add five-layer architecture (Perception, Control, Conversation, Safety, Adaptive)
- Implement three specialized agents (Low, Medium, High Risk)
- Add comprehensive test suite
- Add technical documentation
- Add PsyGUARD-RoBERTa model download instructions"

# 5. 推送到 GitHub
git push -u origin main
```

---

## 🎯 下一步操作

### 1. 创建 GitHub Release

1. 访问: https://github.com/Kevin11Kaikai/PROXIMO/releases
2. 点击 "Create a new release"
3. 填写版本号: `v0.1.0`
4. 填写 Release 标题: `PROXIMO Chatbot v0.1.0 - Initial Release`
5. 填写描述（可以从 CHANGELOG.md 复制）
6. 发布

### 2. 添加仓库描述

1. 访问: https://github.com/Kevin11Kaikai/PROXIMO
2. 点击 "Settings"
3. 在 "About" 部分添加描述:
   - **Description**: `Controllable and Ethically Aligned Mental Health Chatbot for Adolescents`
   - **Topics**: `mental-health`, `chatbot`, `llm`, `ai-safety`, `psychology`

### 3. 添加 README 徽章（可选）

在 `README.md` 中添加徽章：
```markdown
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
```

### 4. 创建 Issues 模板（可选）

创建 `.github/ISSUE_TEMPLATE/` 目录和模板文件

---

## 📞 需要帮助？

如果遇到问题：

1. **检查 Git 状态**: `git status`
2. **查看错误信息**: 仔细阅读错误信息
3. **检查 .gitignore**: 确认规则正确
4. **查看 GitHub 文档**: https://docs.github.com/
5. **查看本文档**: `GITHUB_UPLOAD_STEPS.md`

---

## ✅ 成功标志

上传成功后，您应该能够：

1. ✅ 在 GitHub 上看到所有文件
2. ✅ README.md 正确显示
3. ✅ 模型文件链接可访问
4. ✅ 所有代码文件完整
5. ✅ 文档完整

恭喜！🎉 您的代码已成功上传到 GitHub！

