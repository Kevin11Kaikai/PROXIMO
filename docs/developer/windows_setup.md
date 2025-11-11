# Windows 设置指南

本指南专门为 Windows 用户提供详细的设置步骤。

## 前置要求

### 1. 安装 Docker Desktop
- 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- 确保 Docker Desktop 正在运行（系统托盘图标可见）

### 2. 安装 Git（包含 Git Bash）
- 下载并安装 [Git for Windows](https://git-scm.com/download/win)
- 安装时确保选择 "Git Bash Here" 选项

### 3. 安装 Python 虚拟环境（本地开发需要）

**选项 A: 使用 Conda（推荐）**
- 下载并安装 [Anaconda](https://www.anaconda.com/download) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- 创建项目专用的 conda 环境：

```powershell
# 创建名为 glitch_core 的 conda 环境（Python 3.12）
conda create -n glitch_core python=3.12 -y

# 激活环境
conda activate glitch_core

# 进入项目目录
cd D:\PROXIMO\glitch_core
```

**选项 B: 使用 uv（项目推荐）**
- 安装 uv: `pip install uv` 或访问 [uv 官网](https://github.com/astral-sh/uv)
- uv 会自动管理虚拟环境，无需手动创建

**选项 C: 使用 venv（Python 内置）**
```powershell
# 在项目目录下创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\Activate.ps1
```

### 4. 安装 Ollama（推荐本地安装）
- 下载并安装 [Ollama for Windows](https://ollama.ai/download/windows)
- 安装完成后，Ollama 会在后台运行（默认端口 11434）

### 5. 下载并安装模型
打开 PowerShell 或命令提示符，运行：
```powershell
ollama pull llama3.1:8b
```
这会下载约 4.7GB 的模型文件，可能需要几分钟。

## 设置步骤

### 步骤 1: 创建本地开发环境（如果需要在本地运行脚本）

**如果你只需要运行 Docker 服务，可以跳过这一步。** 但如果你需要在本地运行 Python 脚本（如 `run_simulation.py`），需要先设置本地环境。

#### 方式 A: 使用 Conda（推荐用于本地开发）

**快速方式（使用 environment.yml）:**
```powershell
# 1. 进入项目目录
cd D:\PROXIMO\glitch_core

# 2. 从配置文件创建 conda 环境
conda env create -f environment.yml

# 3. 激活环境
conda activate glitch_core

# 4. 安装项目依赖（使用 uv 或 pip）
# 选项 4a: 使用 uv（推荐，更快速）
uv sync

# 选项 4b: 使用 pip（较慢但兼容性更好）
pip install -e .
```

**手动方式:**
```powershell
# 1. 创建 conda 环境
conda create -n glitch_core python=3.12 -y

# 2. 激活环境
conda activate glitch_core

# 3. 进入项目目录
cd D:\PROXIMO\glitch_core

# 4. 安装依赖（使用 uv 或 pip）
# 选项 4a: 使用 uv（推荐，更快速）
pip install uv
uv sync

# 选项 4b: 使用 pip（较慢但兼容性更好）
pip install -e .
```

#### 方式 B: 使用 uv 自动管理虚拟环境

```powershell
# 1. 安装 uv（如果还没有）
pip install uv

# 2. 进入项目目录
cd D:\PROXIMO\glitch_core

# 3. 同步依赖（uv 会自动创建 .venv 目录）
uv sync

# 4. 激活虚拟环境（如果需要手动激活）
.venv\Scripts\Activate.ps1
```

**注意**: Docker 容器内部会自动管理环境，这里只是为本地开发脚本准备的。

### 步骤 2: 复制环境变量文件

在项目根目录下，将 `env.example` 复制为 `.env`：

**PowerShell:**
```powershell
cd D:\PROXIMO\glitch_core
Copy-Item env.example .env
```

**或使用 Git Bash:**
```bash
cd /d/PROXIMO/glitch_core
cp env.example .env
```

### 步骤 3: 验证 .env 文件

打开 `.env` 文件，确认以下设置（通常不需要修改）：
```env
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://host.docker.internal:11434
```

### 步骤 4: 使用 Git Bash 运行设置脚本

**重要**: `quick_setup.sh` 是 bash 脚本，需要在 Git Bash 中运行，不能直接在 PowerShell 运行。

1. 在项目根目录右键，选择 "Git Bash Here"
2. 运行设置命令：
```bash
make setup
```

或者手动运行：
```bash
bash scripts/quick_setup.sh
```

### 步骤 5: 启动开发环境

设置完成后，启动开发环境：

**Git Bash:**
```bash
make dev
```

**或者使用 Docker Compose 直接启动:**
```powershell
docker-compose up
```

### 步骤 6: 验证服务运行

打开浏览器访问：
- **Web 仪表板**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Redis**: localhost:6379
- **Qdrant**: http://localhost:6333
- **Ollama**: http://localhost:11434

## Windows 特定命令

### 使用 PowerShell 启动服务
```powershell
# 启动所有服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Git Bash 运行 Make 命令
```bash
# 查看所有可用命令
make help

# 启动开发环境
make dev

# 运行仿真
make sim-run

# 运行测试
make test
```

## 常见问题

### 问题 1: "make: command not found"

**解决方案**: 在 Windows 上，`make` 命令需要在 Git Bash 中使用，或者安装 [GnuWin32 Make](http://gnuwin32.sourceforge.net/packages/make.htm)

推荐：直接使用 Git Bash，它已经包含了 make 工具。

### 问题 2: "bash: scripts/quick_setup.sh: No such file or directory"

**解决方案**: 确保在项目根目录运行命令：
```bash
# 在 Git Bash 中
cd /d/PROXIMO/glitch_core
pwd  # 确认当前目录
ls scripts/quick_setup.sh  # 确认文件存在
```

### 问题 3: Docker 连接错误

**解决方案**: 
1. 确认 Docker Desktop 正在运行
2. 检查 Docker Desktop 设置中的 WSL 2 或 Hyper-V 是否已启用
3. 尝试重启 Docker Desktop

### 问题 4: Ollama 连接失败

**解决方案**:
1. 确认 Ollama 已安装并在运行（查看系统托盘）
2. 测试连接：`curl http://localhost:11434/api/tags`
3. 如果使用 Docker，确保 `.env` 中的 `OLLAMA_URL=http://host.docker.internal:11434`

### 问题 5: 端口被占用

**解决方案**: 检查并关闭占用端口的程序：
```powershell
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :6379
netstat -ano | findstr :6333

# 终止进程（替换 PID 为实际进程ID）
taskkill /PID <PID> /F
```

## 推荐的开发流程

### 方式 1: 使用 Git Bash（推荐）
```bash
# 1. 打开 Git Bash
cd /d/PROXIMO/glitch_core

# 2. 初始化环境（首次运行）
make setup

# 3. 启动开发环境
make dev

# 4. 在另一个终端运行仿真
make sim-run
```

### 方式 2: 使用 PowerShell + Docker Compose（本地开发）
```powershell
# 1. 激活 conda 环境（如果使用 conda）
conda activate glitch_core

# 或者激活 uv 虚拟环境
.venv\Scripts\Activate.ps1

# 2. 创建 .env 文件
Copy-Item env.example .env

# 3. 启动服务（后台运行）
docker-compose up -d

# 4. 等待服务就绪（约 30 秒）
Start-Sleep -Seconds 30

# 5. 设置 Ollama（需要先安装 Ollama 和下载模型）
python scripts/setup_ollama.py

# 6. 运行仿真（在本地环境运行，不在 Docker 中）
python scripts/run_simulation.py
```

**注意**: 如果使用本地 Python 环境运行脚本，需要确保：
- ✅ conda/venv 环境已激活
- ✅ 所有依赖已安装（`uv sync` 或 `pip install -e .`）
- ✅ Docker 服务（Redis、Qdrant）正在运行
- ✅ Ollama 已安装并在运行

## 验证安装

### 验证 Docker 服务
```bash
# 在 Git Bash 中
make llm-test      # 测试 LLM 连接
make test          # 运行所有测试（在 Docker 容器中）
```

### 验证本地 Python 环境（如果设置了）

```powershell
# 1. 激活环境
conda activate glitch_core
# 或
.venv\Scripts\Activate.ps1

# 2. 验证 Python 版本
python --version  # 应该是 Python 3.12

# 3. 验证依赖安装
python -c "import fastapi, redis, qdrant_client; print('✅ 依赖已安装')"

# 4. 测试本地运行脚本
python scripts/test_llm.py
```

## 两种运行模式的区别

### 模式 1: Docker 模式（推荐，用于生产）
- **运行位置**: 所有代码在 Docker 容器中运行
- **环境管理**: Docker 自动管理
- **优点**: 环境一致、隔离好、易于部署
- **缺点**: 调试稍复杂

### 模式 2: 本地开发模式（推荐，用于开发调试）
- **运行位置**: Python 脚本在本地 conda/venv 中运行
- **环境管理**: 需要手动创建和激活环境
- **优点**: 调试方便、IDE 集成好、修改代码立即生效
- **缺点**: 需要手动管理环境
- **适用场景**: 
  - 运行 `scripts/run_simulation.py`
  - 运行 `scripts/test_llm.py`
  - 本地调试和开发

**推荐工作流程**:
1. Docker 运行 Redis、Qdrant 等基础设施服务
2. 本地 conda/venv 运行 Python 脚本进行开发和调试
3. 测试时可以在 Docker 中运行完整测试套件

## 下一步

设置完成后，查看：
- [Getting Started Guide](getting-started.md) - 开发环境使用
- [API Reference](api-reference.md) - API 使用文档
- [Configuration Guide](../researcher/configuration-guide.md) - 实验配置
