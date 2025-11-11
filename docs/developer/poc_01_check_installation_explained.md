# 01_check_installation.py 代码详解

> **文件路径**: `NeMo_POC/01_check_installation.py`  
> **目的**: 验证 NeMo Guardrails 和相关依赖是否已正确安装  
> **阶段**: POC 阶段第一步 - 环境验证  
> **难度**: ⭐ (入门级)

---

## 📋 目录

1. [脚本概述](#1-脚本概述)
2. [代码结构](#2-代码结构)
3. [逐行代码讲解](#3-逐行代码讲解)
4. [执行流程](#4-执行流程)
5. [输出示例](#5-输出示例)
6. [常见问题](#6-常见问题)
7. [知识点总结](#7-知识点总结)

---

## 1. 脚本概述

### 1.1 为什么需要这个脚本？

在开始集成 NeMo Guardrails 之前，我们需要确保：
- ✅ Python 环境正确配置
- ✅ 所有必需的包已安装
- ✅ 版本兼容性检查

**类比**：就像开车前检查油、水、轮胎 - 这是 POC 阶段的"开车前检查"。

### 1.2 这个脚本做什么？

```
检查任务：
├── 1. 检查 nemoguardrails 是否已安装
├── 2. 检查 langchain 是否已安装
├── 3. 检查 langchain_community 是否已安装
├── 4. 显示已安装包的版本信息
└── 5. 提供安装指令（如果缺失）
```

### 1.3 预期结果

**成功场景**：
```
✅ nemoguardrails (NeMo Guardrails) - 已安装
✅ langchain (LangChain) - 已安装
✅ langchain_community (LangChain Community) - 已安装

NeMo Guardrails 版本: 0.18.0
LangChain 版本: 0.1.0

✅ 所有必需的包已安装！
```

**失败场景**：
```
❌ nemoguardrails (NeMo Guardrails) - 未安装
   错误: No module named 'nemoguardrails'

请运行以下命令安装缺失的包：
  conda activate PROXIMO
  pip install nemoguardrails
```

---

## 2. 代码结构

### 2.1 整体结构

```python
# 1. 文档字符串和导入
"""POC 1: 检查 NeMo Guardrails 安装"""
import sys
from pathlib import Path

# 2. Windows 编码设置（兼容性处理）
if sys.platform == 'win32':
    # 设置 UTF-8 编码

# 3. 项目路径配置
sys.path.insert(0, str(Path(__file__).parent.parent))

# 4. 核心函数
def check_installation():
    """检查所有必需的包是否已安装"""
    # 4.1 检查包是否已安装
    # 4.2 显示版本信息
    # 4.3 输出总结

# 5. 主入口
if __name__ == "__main__":
    # 运行检查并处理异常
```

### 2.2 函数调用关系

```
main (if __name__ == "__main__")
  ↓
check_installation()
  ├── __import__(package)  [检查每个包]
  ├── print()              [输出结果]
  └── return all_installed [返回状态]
```

---

## 3. 逐行代码讲解

### 3.1 文档字符串和基础导入

```python
"""
POC 1: 检查 NeMo Guardrails 安装

验证 NeMo Guardrails 和相关依赖是否已正确安装。
"""
```

**讲解**：
- Python 文档字符串（docstring），描述脚本用途
- POC = Proof of Concept（概念验证）
- 这是 POC 系列的第一个脚本

```python
import sys
from pathlib import Path
```

**讲解**：
- `sys`：系统相关功能（平台检测、路径管理、退出码）
- `pathlib.Path`：面向对象的文件路径操作（比 `os.path` 更现代）

### 3.2 Windows 编码兼容性处理

```python
# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**为什么需要这段代码？**

**问题**：
- Windows 默认使用 GBK 编码（中文系统）
- Python 脚本中有中文字符（如 "已安装"、"未安装"）
- 直接运行会出现 `UnicodeEncodeError`

**示例错误**：
```
UnicodeEncodeError: 'gbk' codec can't encode character '\u2713' in position 0
```

**解决方案**：
```python
if sys.platform == 'win32':  # 检测是否是 Windows
    import io
    
    # 将标准输出包装为 UTF-8 编码
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,      # 原始字节流
        encoding='utf-8',        # 使用 UTF-8 编码
        errors='replace'         # 无法编码的字符用 '?' 替换
    )
    
    # 同样处理标准错误输出
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding='utf-8',
        errors='replace'
    )
```

**关键点**：
- `sys.platform == 'win32'`：只在 Windows 上执行
- `errors='replace'`：即使有无法编码的字符也不会崩溃
- Linux/Mac 默认 UTF-8，不需要这段代码

### 3.3 项目路径配置

```python
# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**为什么需要这段代码？**

**问题**：
```
NeMo_POC/01_check_installation.py  ← 当前脚本
src/core/config.py                  ← 需要导入的模块

直接 import src.core.config 会失败：
ModuleNotFoundError: No module named 'src'
```

**解决方案**：
```python
# 路径解析
__file__                    # → d:\PROXIMO\glitch_core\NeMo_POC\01_check_installation.py
Path(__file__)              # → Path 对象
Path(__file__).parent       # → d:\PROXIMO\glitch_core\NeMo_POC
Path(__file__).parent.parent # → d:\PROXIMO\glitch_core （项目根目录）

# 添加到 sys.path（Python 模块搜索路径）
sys.path.insert(0, str(Path(__file__).parent.parent))

# 现在可以导入项目模块了
from src.core.config import settings  # ✅ 成功
```

**关键点**：
- `sys.path.insert(0, ...)`：插入到最前面（优先级最高）
- 而不是 `sys.path.append(...)`：避免被其他路径覆盖

### 3.4 核心函数：check_installation()

#### 3.4.1 函数签名和打印标题

```python
def check_installation():
    """检查所有必需的包是否已安装"""
    
    print("=" * 80)
    print("POC 1: 检查 NeMo Guardrails 安装")
    print("=" * 80)
    print("\n检查必需的包...")
```

**讲解**：
- `"=" * 80`：创建 80 个等号的分隔线（视觉上更清晰）
- `\n`：空行（增加可读性）

**输出效果**：
```
================================================================================
POC 1: 检查 NeMo Guardrails 安装
================================================================================

检查必需的包...
```

#### 3.4.2 定义需要检查的包

```python
packages = {
    "nemoguardrails": "NeMo Guardrails",
    "langchain": "LangChain",
    "langchain_community": "LangChain Community (包含 Ollama 支持)",
}
```

**讲解**：
- 使用字典存储：`{包名: 描述}`
- **为什么需要这三个包？**
  - `nemoguardrails`：核心框架
  - `langchain`：LangChain 基础库
  - `langchain_community`：包含 Ollama 集成（LangChain 社区扩展）

**依赖关系**：
```
NeMo Guardrails
    ↓ (需要)
LangChain
    ↓ (需要)
LangChain Community
    ↓ (包含)
Ollama 集成
```

#### 3.4.3 检查每个包是否已安装

```python
results = {}

for package, description in packages.items():
    try:
        __import__(package)
        results[package] = {"installed": True, "error": None}
        print(f"✅ {package} ({description}) - 已安装")
    except ImportError as e:
        results[package] = {"installed": False, "error": str(e)}
        print(f"❌ {package} ({description}) - 未安装")
        print(f"   错误: {e}")
```

**逐行讲解**：

**1. 初始化结果字典**
```python
results = {}  # 存储每个包的检查结果
```

**2. 遍历每个包**
```python
for package, description in packages.items():
    # package: "nemoguardrails"
    # description: "NeMo Guardrails"
```

**3. 使用 `__import__()` 检查**
```python
try:
    __import__(package)  # 尝试导入包
```

**为什么用 `__import__()` 而不是 `import`？**

```python
# ❌ 不能这样写（语法错误）
import package  # 这会尝试导入名为 "package" 的模块

# ✅ 正确的动态导入
__import__(package)  # 动态导入变量中的模块名

# 等价于：
import nemoguardrails  # 如果 package == "nemoguardrails"
```

**4. 记录成功结果**
```python
results[package] = {"installed": True, "error": None}
print(f"✅ {package} ({description}) - 已安装")
```

**5. 捕获导入错误**
```python
except ImportError as e:
    # ImportError: 模块不存在时触发
    results[package] = {"installed": False, "error": str(e)}
    print(f"❌ {package} ({description}) - 未安装")
    print(f"   错误: {e}")
```

**实际例子**：

**成功场景**：
```python
# 如果 nemoguardrails 已安装
__import__("nemoguardrails")  # ✅ 成功
# 输出：
# ✅ nemoguardrails (NeMo Guardrails) - 已安装
```

**失败场景**：
```python
# 如果 nemoguardrails 未安装
__import__("nemoguardrails")  # ❌ 抛出 ImportError
# 输出：
# ❌ nemoguardrails (NeMo Guardrails) - 未安装
#    错误: No module named 'nemoguardrails'
```

#### 3.4.4 检查版本信息

```python
print("\n" + "=" * 80)
print("版本信息")
print("=" * 80)

try:
    import nemoguardrails
    if hasattr(nemoguardrails, '__version__'):
        print(f"NeMo Guardrails 版本: {nemoguardrails.__version__}")
    else:
        print("NeMo Guardrails: 已安装（版本未知）")
except ImportError:
    pass
```

**逐行讲解**：

**1. 尝试导入并检查版本**
```python
try:
    import nemoguardrails
```

**2. 检查是否有 `__version__` 属性**
```python
if hasattr(nemoguardrails, '__version__'):
    # hasattr(对象, 属性名) → 检查对象是否有该属性
    print(f"NeMo Guardrails 版本: {nemoguardrails.__version__}")
```

**为什么要检查 `hasattr`？**

**问题**：不是所有 Python 包都有 `__version__` 属性

```python
# 标准做法（有版本号）
import requests
print(requests.__version__)  # → "2.28.1"

# 有些包没有版本号
import some_package
print(some_package.__version__)  # ❌ AttributeError
```

**解决方案**：
```python
if hasattr(nemoguardrails, '__version__'):
    # 有版本号 → 显示
    print(f"版本: {nemoguardrails.__version__}")
else:
    # 没有版本号 → 显示"版本未知"
    print("已安装（版本未知）")
```

**3. 静默处理导入错误**
```python
except ImportError:
    pass  # 如果导入失败，不做任何事（已经在前面报告过了）
```

**同样的逻辑应用到 LangChain**：
```python
try:
    import langchain
    if hasattr(langchain, '__version__'):
        print(f"LangChain 版本: {langchain.__version__}")
    else:
        print("LangChain: 已安装（版本未知）")
except ImportError:
    pass
```

#### 3.4.5 输出总结并返回结果

```python
print("\n" + "=" * 80)
print("检查总结")
print("=" * 80)

all_installed = all(r["installed"] for r in results.values())

if all_installed:
    print("✅ 所有必需的包已安装！")
    print("\n下一步：运行 02_test_langchain_ollama.py")
else:
    print("❌ 部分包未安装")
    print("\n请运行以下命令安装缺失的包：")
    print("  conda activate PROXIMO")
    print("  pip install nemoguardrails")
    print("  pip install langchain")
    print("  pip install langchain-community")

return all_installed
```

**逐行讲解**：

**1. 检查是否所有包都已安装**
```python
all_installed = all(r["installed"] for r in results.values())
```

**拆解这行代码**：

```python
# results 的结构：
results = {
    "nemoguardrails": {"installed": True, "error": None},
    "langchain": {"installed": True, "error": None},
    "langchain_community": {"installed": False, "error": "..."}
}

# results.values() → 所有值（字典列表）
results.values()
# → [{"installed": True, ...}, {"installed": True, ...}, {"installed": False, ...}]

# r["installed"] for r in results.values() → 生成器表达式
# → True, True, False

# all(...) → 检查是否全部为 True
all_installed = all([True, True, False])  # → False
all_installed = all([True, True, True])   # → True
```

**`all()` 函数解释**：
```python
all([True, True, True])   # → True  (全部为 True)
all([True, False, True])  # → False (有一个 False)
all([False, False, False]) # → False (全部为 False)
all([])                   # → True  (空列表返回 True)
```

**2. 根据结果输出不同信息**

**成功场景**：
```python
if all_installed:
    print("✅ 所有必需的包已安装！")
    print("\n下一步：运行 02_test_langchain_ollama.py")
```

**失败场景**：
```python
else:
    print("❌ 部分包未安装")
    print("\n请运行以下命令安装缺失的包：")
    print("  conda activate PROXIMO")
    print("  pip install nemoguardrails")
    print("  pip install langchain")
    print("  pip install langchain-community")
```

**为什么提供完整的安装命令？**
- 用户友好：直接复制粘贴即可
- 减少错误：避免用户安装错误的包

**3. 返回检查结果**
```python
return all_installed  # True 或 False
```

### 3.5 主入口

```python
if __name__ == "__main__":
    try:
        success = check_installation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**逐行讲解**：

**1. Python 主入口惯用模式**
```python
if __name__ == "__main__":
    # 只有直接运行脚本时才执行
    # 如果被其他模块导入，不会执行
```

**示例**：
```python
# 直接运行
$ python 01_check_installation.py
# → __name__ == "__main__"  ✅ 执行

# 作为模块导入
from NeMo_POC import 01_check_installation
# → __name__ == "01_check_installation"  ❌ 不执行
```

**2. 异常处理**
```python
try:
    success = check_installation()  # 运行检查
    sys.exit(0 if success else 1)   # 设置退出码
```

**退出码（Exit Code）解释**：
```python
sys.exit(0)  # 成功（Unix/Linux 惯例）
sys.exit(1)  # 失败（非零表示错误）

# 在 Shell 中可以检查
$ python 01_check_installation.py
$ echo $?  # Linux/Mac: 显示退出码
# → 0 (成功) 或 1 (失败)

$ python 01_check_installation.py; echo $LASTEXITCODE  # Windows PowerShell
```

**为什么需要退出码？**
- CI/CD 流水线依赖退出码判断成功/失败
- Shell 脚本可以根据退出码做决策

```bash
# 示例：Shell 脚本
python 01_check_installation.py
if [ $? -eq 0 ]; then
    echo "检查通过，继续下一步"
    python 02_test_langchain_ollama.py
else
    echo "检查失败，停止"
    exit 1
fi
```

**3. 捕获所有其他异常**
```python
except Exception as e:
    print(f"\n\n[ERROR] 发生错误: {e}")
    import traceback
    traceback.print_exc()  # 打印完整的异常堆栈
    sys.exit(1)            # 以失败状态退出
```

**`traceback.print_exc()` 解释**：

**没有 traceback**：
```
[ERROR] 发生错误: division by zero
```

**有 traceback**：
```
[ERROR] 发生错误: division by zero
Traceback (most recent call last):
  File "01_check_installation.py", line 95, in <module>
    success = check_installation()
  File "01_check_installation.py", line 42, in check_installation
    result = 1 / 0  # 示例错误
ZeroDivisionError: division by zero
```

**好处**：
- 快速定位错误位置
- 了解错误发生的调用链
- 便于调试

---

## 4. 执行流程

### 4.1 流程图

```
开始
  ↓
设置 Windows UTF-8 编码（如果需要）
  ↓
添加项目路径到 sys.path
  ↓
调用 check_installation()
  ↓
打印标题
  ↓
遍历每个包 ──┐
  ↓          │
尝试导入包   │ (循环)
  ↓          │
记录结果     │
  ↓ ─────────┘
打印版本信息
  ↓
检查是否全部安装
  ↓
   ┌─────────────┐
   │ 全部安装?    │
   └─────────────┘
     Yes ↓   ↓ No
  输出成功  输出失败+安装指令
     ↓       ↓
  返回 True  返回 False
     ↓       ↓
  sys.exit(0)  sys.exit(1)
     ↓
   结束
```

### 4.2 详细执行步骤

**步骤 1: 初始化**
```python
# Windows UTF-8 设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(...)

# 项目路径
sys.path.insert(0, project_root)
```

**步骤 2: 检查包**
```python
for package in ["nemoguardrails", "langchain", "langchain_community"]:
    try:
        __import__(package)  # 尝试导入
        ✅ 成功 → 记录 {"installed": True}
    except ImportError:
        ❌ 失败 → 记录 {"installed": False}
```

**步骤 3: 检查版本**
```python
import nemoguardrails
if hasattr(nemoguardrails, '__version__'):
    print(f"版本: {nemoguardrails.__version__}")
```

**步骤 4: 总结**
```python
all_installed = all([True, True, True])  # 示例：全部安装

if all_installed:
    print("✅ 所有包已安装")
    return True
else:
    print("❌ 部分包未安装")
    print("安装命令：...")
    return False
```

**步骤 5: 退出**
```python
success = check_installation()
sys.exit(0 if success else 1)
```

---

## 5. 输出示例

### 5.1 成功场景（所有包已安装）

```
================================================================================
POC 1: 检查 NeMo Guardrails 安装
================================================================================

检查必需的包...
✅ nemoguardrails (NeMo Guardrails) - 已安装
✅ langchain (LangChain) - 已安装
✅ langchain_community (LangChain Community (包含 Ollama 支持)) - 已安装

================================================================================
版本信息
================================================================================
NeMo Guardrails 版本: 0.18.0
LangChain 版本: 0.1.0

================================================================================
检查总结
================================================================================
✅ 所有必需的包已安装！

下一步：运行 02_test_langchain_ollama.py
```

**退出码**: 0 (成功)

### 5.2 失败场景（部分包未安装）

```
================================================================================
POC 1: 检查 NeMo Guardrails 安装
================================================================================

检查必需的包...
❌ nemoguardrails (NeMo Guardrails) - 未安装
   错误: No module named 'nemoguardrails'
✅ langchain (LangChain) - 已安装
✅ langchain_community (LangChain Community (包含 Ollama 支持)) - 已安装

================================================================================
版本信息
================================================================================
LangChain 版本: 0.1.0

================================================================================
检查总结
================================================================================
❌ 部分包未安装

请运行以下命令安装缺失的包：
  conda activate PROXIMO
  pip install nemoguardrails
  pip install langchain
  pip install langchain-community
```

**退出码**: 1 (失败)

### 5.3 异常场景（脚本执行错误）

```
================================================================================
POC 1: 检查 NeMo Guardrails 安装
================================================================================

检查必需的包...


[ERROR] 发生错误: [Errno 2] No such file or directory: 'config.yml'
Traceback (most recent call last):
  File "01_check_installation.py", line 95, in <module>
    success = check_installation()
  File "01_check_installation.py", line 42, in check_installation
    with open("config.yml") as f:  # 示例错误
FileNotFoundError: [Errno 2] No such file or directory: 'config.yml'
```

**退出码**: 1 (失败)

---

## 6. 常见问题

### 问题 1: Windows 中文乱码

**症状**：
```
���� nemoguardrails (NeMo Guardrails) - �Ѱ�װ
```

**原因**：
- Windows 默认 GBK 编码
- UTF-8 字符无法正确显示

**解决方案**：
```python
# 脚本已包含此代码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

**额外方案**：
```bash
# 设置 PowerShell 为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 或者在 Python 运行前
$env:PYTHONIOENCODING="utf-8"
python 01_check_installation.py
```

### 问题 2: ModuleNotFoundError: No module named 'src'

**症状**：
```python
from src.core.config import settings
ModuleNotFoundError: No module named 'src'
```

**原因**：
- 当前工作目录不在项目根目录
- Python 找不到 `src` 模块

**解决方案**：
```python
# 脚本已包含此代码
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**手动调试**：
```python
# 查看当前 sys.path
import sys
print(sys.path)

# 手动添加项目根目录
sys.path.insert(0, "d:\\PROXIMO\\glitch_core")
```

### 问题 3: 所有包都未安装

**症状**：
```
❌ nemoguardrails - 未安装
❌ langchain - 未安装
❌ langchain_community - 未安装
```

**原因**：
- 使用了错误的 Python 环境
- 包安装在不同的环境中

**解决方案**：
```bash
# 1. 检查当前环境
conda info --envs

# 2. 激活 PROXIMO 环境
conda activate PROXIMO

# 3. 验证 Python 路径
which python  # Linux/Mac
where python  # Windows

# 4. 安装包
pip install nemoguardrails langchain langchain-community

# 5. 再次运行
python 01_check_installation.py
```

### 问题 4: ImportError: DLL load failed

**症状** (Windows)：
```
ImportError: DLL load failed while importing _sqlite3
```

**原因**：
- 缺少系统依赖
- Conda 环境问题

**解决方案**：
```bash
# 重新创建环境
conda deactivate
conda env remove -n PROXIMO
conda create -n PROXIMO python=3.10
conda activate PROXIMO
pip install nemoguardrails langchain langchain-community
```

---

## 7. 知识点总结

### 7.1 Python 基础知识点

| 知识点 | 代码示例 | 说明 |
|--------|----------|------|
| **文档字符串** | `"""This is a docstring"""` | 模块、函数说明 |
| **条件导入** | `if sys.platform == 'win32': ...` | 平台特定代码 |
| **动态导入** | `__import__(package_name)` | 根据字符串导入 |
| **生成器表达式** | `(x for x in list)` | 内存高效的迭代 |
| **内置函数 all()** | `all([True, True, False])` | 检查全部为真 |
| **异常处理** | `try...except...` | 错误处理 |
| **主入口** | `if __name__ == "__main__":` | 脚本入口点 |
| **退出码** | `sys.exit(0)` | 进程退出状态 |

### 7.2 文件路径操作

```python
# 老式方法（os.path）
import os
project_root = os.path.dirname(os.path.dirname(__file__))

# 现代方法（pathlib）
from pathlib import Path
project_root = Path(__file__).parent.parent

# pathlib 的优势
project_root / "src" / "config.py"  # → Path 对象（自动处理分隔符）
os.path.join(project_root, "src", "config.py")  # → 字符串（需要手动处理）
```

### 7.3 编码处理最佳实践

```python
# 1. 文件读写使用 UTF-8
with open("file.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 2. 标准输出使用 UTF-8（Windows）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 3. 环境变量设置
export PYTHONIOENCODING=utf-8  # Linux/Mac
$env:PYTHONIOENCODING="utf-8"  # Windows PowerShell
```

### 7.4 包管理最佳实践

```python
# 1. 检查包是否已安装
try:
    import package_name
except ImportError:
    print("Package not installed")

# 2. 检查版本
import package_name
print(package_name.__version__)

# 3. 列出已安装包
pip list

# 4. 冻结依赖
pip freeze > requirements.txt

# 5. 安装依赖
pip install -r requirements.txt
```

### 7.5 脚本设计模式

**好的 POC 脚本应该**：
- ✅ 单一职责（只做一件事）
- ✅ 清晰的输出（成功/失败一目了然）
- ✅ 友好的错误信息（告诉用户如何修复）
- ✅ 正确的退出码（便于自动化）
- ✅ 异常处理（不会崩溃）
- ✅ 平台兼容性（Windows/Linux/Mac）

---

## 8. 与其他 POC 脚本的关系

```
POC 验证流程：

01_check_installation.py  ← 当前脚本
  ↓ [检查依赖]
  ✅ 所有包已安装
  ↓
02_test_langchain_ollama.py
  ↓ [测试 LangChain + Ollama]
  ✅ 集成正常
  ↓
03_test_guardrails_basic.py
  ↓ [测试基本 Guardrails 功能]
  ✅ 功能正常
  ↓
04_test_guardrails_with_ollama.py
  ↓ [测试完整集成]
  ✅ 集成成功
  ↓
05_test_safety_rules.py
  ↓ [测试安全规则]
  ✅ 规则生效
  ↓
🎉 POC 验证完成，可以开始正式集成！
```

---

## 9. 实践建议

### 9.1 如何运行

```bash
# 方法 1: 直接运行
cd d:\PROXIMO\glitch_core
python NeMo_POC\01_check_installation.py

# 方法 2: 使用相对路径
cd NeMo_POC
python 01_check_installation.py

# 方法 3: 在 Python 中运行
python
>>> exec(open("NeMo_POC/01_check_installation.py").read())
```

### 9.2 如何调试

```python
# 添加调试输出
def check_installation():
    print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
    print(f"[DEBUG] sys.path: {sys.path}")
    print(f"[DEBUG] Python 版本: {sys.version}")
    
    # 原有代码...
```

### 9.3 如何扩展

```python
# 添加更多包检查
packages = {
    "nemoguardrails": "NeMo Guardrails",
    "langchain": "LangChain",
    "langchain_community": "LangChain Community",
    "fastapi": "FastAPI (Web 框架)",  # 新增
    "httpx": "HTTPX (HTTP 客户端)",   # 新增
}

# 添加详细版本检查
def check_detailed_versions():
    import pkg_resources
    for package in packages.keys():
        try:
            version = pkg_resources.get_distribution(package).version
            print(f"{package}: {version}")
        except Exception:
            print(f"{package}: 未安装")
```

---

**总结**: `01_check_installation.py` 是一个简单但实用的依赖检查脚本，它确保在开始 NeMo Guardrails 集成之前，所有必需的包都已正确安装。通过清晰的输出和友好的错误提示，它大大降低了后续开发中的环境问题。

---

**相关文档**：
- [NeMo Guardrails 集成分析](./nemo_guardrails_integration_analysis.md)
- [02_test_langchain_ollama.py 讲解](./poc_02_test_langchain_ollama_explained.md)（待创建）
- [POC 测试指南](./nemo_guardrails_testing_guide.md)
