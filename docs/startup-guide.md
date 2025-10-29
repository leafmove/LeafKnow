# LeafKnow 项目启动指南

## 🏗️ 项目架构概览

LeafKnow 是一个知识管理平台，采用前后端分离架构：

```
项目架构：
├── API后端 (Python FastAPI) - 运行在 60000 端口
├── 前端应用 (Tauri + React) - 桌面应用
└── 数据库 (SQLite + LanceDB) - 本地存储
```

## 📋 系统要求

### 必需软件
- **Python**: >= 3.10 ⚠️ (当前系统: 3.8.10，需要升级)
- **Node.js**: >= 18.0.0 ✅ (当前: 20.18.1)
- **Rust**: >= 1.70.0 ❌ (未安装)
- **UV**: >= 0.5.0 ✅ (当前: 0.6.13)
- **Bun**: >= 1.0.0 ❌ (未安装，可用npm替代)

### 可选软件
- **Git**: ✅ (已配置)
- **VS Code**: 推荐的IDE
- **jq**: JSON处理工具 (API脚本需要)

## 🔧 环境准备

### 1. 升级Python (重要)
当前Python版本(3.8.10)不符合要求，需要升级到3.10+：

#### Windows:
```bash
# 方法1: 从官网下载安装包
# 访问 https://www.python.org/downloads/ 下载Python 3.10+

# 方法2: 使用winget
winget install Python.Python.3.11

# 方法3: 使用Anaconda
conda install python=3.11
```

#### 验证安装:
```bash
python --version  # 应该显示 Python 3.10.x 或更高版本
python3 --version  # 应该显示 Python 3.10.x 或更高版本
```

### 2. 安装Rust
```bash
# Windows (PowerShell):
winget install Rustlang.Rust.MSVC

# 或者访问 https://rustup.rs/ 下载安装

# 验证安装:
cargo --version
```

### 3. 安装Bun (可选，推荐)
```bash
# Windows (PowerShell):
powershell -c "irm bun.sh/install.ps1 | iex"

# 或者使用npm替代 (项目中已配置npm支持)
npm install -g bun

# 验证安装:
bun --version
```

### 4. 安装jq (API脚本需要)
```bash
# Windows (PowerShell):
winget install jqlang.jq

# 或者使用Chocolatey:
choco install jq

# 验证安装:
jq --version
```

## 🚀 启动步骤

### 方式一：完整启动 (推荐)

#### 第1步：启动API后端
```bash
# 进入Core目录
cd core

# 安装Python依赖
uv sync

# 启动Core服务器 (Windows)
.\core_standalone.sh

# 或手动启动 (跨平台)
uv run main.py --port 60000 --host 127.0.0.1 --db-path "sqlite.db"

# API服务器将运行在: http://127.0.0.1:60000
```

#### 第2步：启动前端应用
```bash
# 新开一个终端，进入前端目录
cd leaf-know

# 安装Node.js依赖 (使用bun)
bun install

# 或使用npm
npm install

# 启动开发模式 (使用bun)
bun tauri dev

# 或使用npm
npm run tauri dev

# 或直接运行脚本
.\dev.sh
```

### 方式二：仅启动前端 (开发模式)
如果只想开发前端界面：

```bash
cd leaf-know
bun install
bun run dev  # 仅启动Web开发服务器
```

### 方式三：构建生产版本
```bash
# 构建前端
cd leaf-know
bun run build

# 运行构建后的应用
bun run tauri build
```

## 📁 项目文件说明

### Core后端 (`/core`)
- `main.py`: FastAPI主应用入口
- `chatsession_*.py`: 聊天会话管理
- `models_*.py`: AI模型管理
- `db_mgr.py`: 数据库管理
- `core_standalone.sh`: 一键启动脚本

### 前端应用 (`/leaf-know`)
- `src/`: React源代码
- `src-tauri/`: Tauri后端(Rust代码)
- `package.json`: Node.js依赖配置
- `dev.sh`: 开发模式启动脚本

## 🔍 启动验证

### 检查API是否正常运行
```bash
# 测试API端点
curl http://127.0.0.1:60000/health

# 或在浏览器访问
# http://127.0.0.1:60000/docs  (API文档)
```

### 检查前端是否正常运行
- Tauri应用窗口应该自动打开
- 如果没有打开，检查控制台错误信息

## 🐛 常见问题解决

### 1. Python版本不兼容
```bash
# 症状: uv sync 时出现版本错误
# 解决: 升级Python到3.13+
```

### 2. Rust未安装
```bash
# 症状: tauri dev 时提示找不到cargo
# 解决: 安装Rust工具链
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 3. 端口被占用
```bash
# 症状: API启动失败，提示端口60000被占用
# 解决: 修改端口或关闭占用进程
# Windows:
netstat -ano | findstr :60000
taskkill /PID <进程ID> /F
```

### 4. 数据库路径问题
```bash
# 症状: API启动时数据库连接失败
# 解决: 确保数据库目录存在，或修改数据库路径
mkdir -p ~/Library/Application\ Support/com.leafmove.leaf-know/
```

### 5. 前端依赖安装失败
```bash
# 症状: bun install 或 npm install 失败
# 解决: 清理缓存重新安装
rm -rf node_modules bun.lock
bun install  # 或 npm install
```

## 📱 开发工作流

### 日常开发
1. 启动API后端 (终端1)
2. 启动前端应用 (终端2)
3. 修改代码自动热重载
4. 在Tauri应用中测试功能

### 调试技巧
- API调试: 访问 `http://127.0.0.1:60000/docs`
- 前端调试: 使用F12开发者工具
- 日志查看: API启动后的终端输出

### 数据位置
- **数据库**: `~/Library/Application Support/com.leafmove.leaf-know/sqlite.db`
- **日志**: API终端输出
- **配置**: `leaf-know/src-tauri/tauri.conf.json`

## 🎯 下一步

启动成功后，你可以：
1. 探索API文档和功能
2. 查看前端界面和交互
3. 开始二次开发
4. 阅读其他协作文档

## 📞 获取帮助

如果遇到问题：
1. 查看本指南的常见问题部分
2. 检查项目的GitHub Issues
3. 联系项目维护者

---

**注意**: 这是一个复杂的全栈应用，第一次启动可能需要解决一些环境配置问题。耐心按照步骤操作，大多数问题都能解决。