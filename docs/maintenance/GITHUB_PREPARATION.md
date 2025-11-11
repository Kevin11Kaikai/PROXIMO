# GitHub 上传准备清单

## 📋 检查清单

### ✅ 1. 代码清理

- [x] 检查并更新 `.gitignore`
- [ ] 移除敏感信息（API keys, tokens, passwords）
- [ ] 移除临时文件和缓存
- [ ] 检查大文件（模型文件、数据库文件）
- [ ] 清理 `__pycache__` 目录

### ✅ 2. 文档准备

- [x] 创建 `README_PROXIMO_CHATBOT.md` - 新架构说明
- [ ] 更新主 `README.md` - 添加新架构说明
- [ ] 创建 `CHANGELOG.md` - 记录主要变更
- [ ] 创建 `ARCHITECTURE.md` - 详细架构文档

### ✅ 3. 配置文件

- [x] 检查 `pyproject.toml` - 依赖配置
- [x] 检查 `environment.yml` - Conda 环境
- [x] 检查 `env.example` - 环境变量示例
- [ ] 检查 `docker-compose.yml` - Docker 配置
- [ ] 检查 `Makefile` - 构建脚本

### ✅ 4. 测试和验证

- [ ] 运行所有测试确保通过
- [ ] 检查测试覆盖率
- [ ] 验证代码格式（black, ruff）
- [ ] 检查类型提示（mypy）

### ✅ 5. 敏感信息检查

- [ ] 搜索代码中的硬编码密钥
- [ ] 检查配置文件中的敏感数据
- [ ] 确保 `.env` 文件在 `.gitignore` 中
- [ ] 检查数据库文件是否被忽略

### ✅ 6. 大文件检查

- [ ] 检查模型文件大小（PsyGUARD-RoBERTa/pytorch_model.bin）
- [ ] 考虑使用 Git LFS 或外部存储
- [ ] 检查数据库文件大小
- [ ] 检查其他大型二进制文件

## 🚀 上传步骤

### Step 1: 初始化 Git 仓库（如果还没有）

```bash
# 检查 Git 状态
git status

# 如果还没有初始化
git init
```

### Step 2: 添加远程仓库

```bash
# 添加 GitHub 远程仓库
git remote add origin https://github.com/your-username/glitch_core.git

# 或者如果已经存在，更新 URL
git remote set-url origin https://github.com/your-username/glitch_core.git
```

### Step 3: 检查要提交的文件

```bash
# 查看将要提交的文件
git status

# 查看将要提交的文件列表
git add --dry-run .
```

### Step 4: 添加文件

```bash
# 添加所有文件（.gitignore 会自动排除）
git add .

# 或者选择性添加
git add src_new/
git add test_*_layer/
git add test_integration/
git add docs/
git add README_PROXIMO_CHATBOT.md
git add pyproject.toml
git add .gitignore
```

### Step 5: 提交更改

```bash
# 创建提交
git commit -m "feat: Implement PROXIMO Chatbot modular architecture

- Add five-layer architecture (Perception, Control, Conversation, Safety, Adaptive)
- Implement three specialized agents (Low, Medium, High Risk)
- Add comprehensive test suite
- Add technical documentation
- Update .gitignore for sensitive files"
```

### Step 6: 推送到 GitHub

```bash
# 推送到主分支
git push -u origin main

# 或者推送到 master 分支
git push -u origin master
```

## 📝 建议的提交信息格式

### 主要提交

```
feat: Implement PROXIMO Chatbot modular architecture

- Add Perception Layer with PsyGUARD and questionnaire services
- Add Control Layer with risk routing and rigid score system
- Add Conversation Layer with three specialized agents
- Add Safety Layer with Guardrails integration
- Add Adaptive Layer with feedback collection
- Add comprehensive test suite for all layers
- Add technical documentation
```

### 后续提交（如果需要）

```
docs: Update documentation for new architecture
test: Add integration tests for route transitions
fix: Fix temperature calculation in medium risk agent
refactor: Improve state machine implementation
```

## 🔒 安全注意事项

### 必须排除的文件

1. **环境变量文件**
   - `.env`
   - `.env.local`
   - `.env.*.local`

2. **数据库文件**
   - `data/assessments.db`
   - `*.db`
   - `*.sqlite`

3. **模型文件（如果太大）**
   - `PsyGUARD-RoBERTa/pytorch_model.bin`
   - 考虑使用 Git LFS 或外部存储

4. **密钥和证书**
   - `*.key`
   - `*.pem`
   - `*.cert`

5. **日志文件**
   - `*.log`
   - `logs/`

### 检查敏感信息

```bash
# 搜索可能的 API keys
grep -r "api_key" --include="*.py" --include="*.yaml" --include="*.yml"

# 搜索可能的密码
grep -r "password" --include="*.py" --include="*.yaml" --include="*.yml"

# 搜索可能的 tokens
grep -r "token" --include="*.py" --include="*.yaml" --include="*.yml"
```

## 📦 大文件处理

### 选项 1: 使用 Git LFS

```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.bin"
git lfs track "*.pt"
git lfs track "*.pth"

# 添加到 .gitattributes
echo "*.bin filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
```

### 选项 2: 外部存储

- 将模型文件上传到云存储（S3, Google Cloud Storage）
- 在 README 中提供下载链接
- 使用脚本自动下载模型文件

### 选项 3: 排除大文件

- 在 `.gitignore` 中排除模型文件
- 在 README 中说明如何获取模型文件
- 提供模型下载脚本

## 📚 推荐的文档结构

```
glitch_core/
├── README.md                    # 主 README
├── README_PROXIMO_CHATBOT.md   # PROXIMO Chatbot 说明
├── ARCHITECTURE.md              # 架构文档
├── CHANGELOG.md                 # 变更日志
├── CONTRIBUTING.md              # 贡献指南
├── LICENSE                      # 许可证
├── .gitignore                   # Git 忽略文件
├── pyproject.toml               # Python 项目配置
├── environment.yml              # Conda 环境
├── env.example                  # 环境变量示例
├── src_new/                     # 新架构代码
├── test_*_layer/                # 层测试
├── test_integration/            # 集成测试
└── docs/                        # 文档目录
```

## ✅ 最终检查

在推送之前，请确认：

- [ ] 所有敏感信息已移除
- [ ] 大文件已处理（LFS 或排除）
- [ ] 测试全部通过
- [ ] 文档完整且准确
- [ ] `.gitignore` 配置正确
- [ ] 提交信息清晰明确
- [ ] 代码格式正确
- [ ] 没有硬编码的配置

## 🎯 下一步

上传完成后：

1. 创建 GitHub Release
2. 添加项目标签和描述
3. 设置 GitHub Actions（如果需要 CI/CD）
4. 添加项目 Wiki（如果需要）
5. 创建 Issues 模板
6. 创建 Pull Request 模板

## 📞 需要帮助？

如果遇到问题：

1. 检查 Git 状态：`git status`
2. 查看 .gitignore 规则：`git check-ignore -v <file>`
3. 检查文件大小：`du -sh <file>`
4. 查看提交历史：`git log --oneline`

