# 增强版 Chat App 使用指南

## 概述

增强版 Chat App 是一个功能丰富的 AI 聊天应用，支持多用户管理、Agent配置管理和对话历史存储。应用支持 SQLite、MySQL 和 PostgreSQL 数据库。

## 主要功能

### 🔐 多用户支持
- 用户注册、登录、管理
- 每个用户独立的配置和数据隔离
- 支持用户信息编辑和删除

### 🤖 Agent 管理
- 支持多个 AI 模型提供商（OpenAI、Ollama、OpenRouter、Llama.cpp）
- 自定义 Agent 配置（模型参数、系统提示词等）
- Agent 的增删改查功能
- 设置默认 Agent

### 💬 智能对话
- 支持流式和非流式输出
- 对话历史记录和查看
- 实时切换不同 Agent 进行对话

### 🗄️ 数据存储
- 支持 SQLite、MySQL、PostgreSQL 数据库
- 用户配置、Agent 配置、对话历史持久化存储
- 默认使用 SQLite，数据库文件：`autobox_id.db`

## 安装和运行

### 基本要求
- Python 3.8+
- 必要的 Python 包依赖

### 数据库依赖

#### SQLite（默认）
- 无需额外安装，Python 内置支持

#### MySQL（可选）
```bash
pip install pymysql
```

#### PostgreSQL（可选）
```bash
pip install psycopg2-binary
```

### AI 模型依赖

#### OpenAI（推荐）
```bash
# 设置环境变量
export OPENAI_API_KEY="your_openai_api_key"
```

#### Ollama（可选）
```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull llama3.2:latest
```

#### OpenRouter（可选）
```bash
# 设置环境变量
export OPENROUTER_API_KEY="your_openrouter_api_key"
```

#### Llama.cpp（可选）
```bash
# 启动 llama.cpp 服务器
# 默认地址：http://127.0.0.1:8080/v1
```

## 启动应用

### 默认启动（SQLite）
```bash
python chat_app_enhanced.py
```

### 使用 MySQL 数据库
```bash
python chat_app_enhanced.py --db-type mysql --db-host localhost --db-user root --db-password your_password --db-name autobox
```

### 使用 PostgreSQL 数据库
```bash
python chat_app_enhanced.py --db-type postgresql --db-host localhost --db-user postgres --db-password your_password --db-name autobox
```

### 自定义 SQLite 路径
```bash
python chat_app_enhanced.py --db-path /path/to/your/database.db
```

## 使用指南

### 1. 用户管理
启动应用后，使用 `users` 命令进入用户管理界面：

- **查看用户列表**：显示所有用户
- **添加用户**：创建新的用户账户
- **切换用户**：在多个用户之间切换
- **编辑用户**：修改用户信息
- **删除用户**：删除用户及其数据

### 2. Agent 管理
使用 `agents` 命令进入 Agent 管理界面：

- **查看 Agent 列表**：显示当前用户的所有 Agent
- **添加 Agent**：创建新的 AI Agent 配置
- **切换 Agent**：在对话中实时切换 Agent
- **编辑 Agent**：修改 Agent 配置
- **删除 Agent**：删除不需要的 Agent
- **设置默认 Agent**：指定用户的默认 Agent

### 3. 聊天对话
直接输入消息开始对话：

- **发送消息**：输入任意文本消息
- **查看历史**：使用 `history` 命令查看对话记录
- **切换模式**：使用 `stream` 命令切换流式/非流式输出
- **退出应用**：使用 `quit` 或 `exit` 命令

## 数据库结构

### users 表
- `id`: 用户唯一标识
- `username`: 用户名
- `email`: 邮箱地址
- `created_at`: 创建时间
- `is_active`: 是否激活

### agents 表
- `id`: Agent 唯一标识
- `user_id`: 所属用户 ID
- `name`: Agent 名称
- `model_id`: 模型 ID
- `provider`: 提供商（openai, ollama, openrouter, llamacpp）
- `base_url`: API 基础 URL
- `api_key`: API 密钥
- `temperature`: 温度参数
- `max_tokens`: 最大输出令牌数
- `system_prompt`: 系统提示词
- `description`: 描述信息
- `is_local`: 是否本地模型
- `is_default`: 是否默认 Agent
- `created_at`: 创建时间
- `updated_at`: 更新时间

### conversations 表
- `id`: 消息唯一标识
- `user_id`: 用户 ID
- `agent_id`: Agent ID
- `role`: 角色（user 或 assistant）
- `content`: 消息内容
- `timestamp`: 时间戳

## 配置示例

### 创建 OpenAI Agent
```
Agent名称: GPT-4 Assistant
模型ID: gpt-4o
提供商: 1 (OpenAI)
Base URL: https://api.openai.com/v1
API Key: your_openai_api_key
Temperature: 0.7
Max Tokens: 2000
系统提示词: 你是一个专业的AI助手
描述: 基于GPT-4的专业助手
```

### 创建 Ollama Agent
```
Agent名称: 本地Llama3
模型ID: llama3.2:latest
提供商: 2 (Ollama)
Base URL: http://localhost:11434
API Key: (留空)
Temperature: 0.8
Max Tokens: 3000
系统提示词: 你是一个本地AI模型
描述: 基于Ollama的本地模型
```

## 高级用法

### 环境变量配置
```bash
# OpenAI
export OPENAI_API_KEY="your_api_key"

# OpenRouter
export OPENROUTER_API_KEY="your_api_key"

# 其他环境变量
export PYTHONPATH="${PYTHONPATH}:/path/to/your/project"
```

### 批量导入配置
可以通过数据库直接导入用户和 Agent 配置，适合企业部署。

### 备份和恢复
```bash
# 备份 SQLite 数据库
cp autobox_id.db autobox_id_backup.db

# 恢复数据库
cp autobox_id_backup.db autobox_id.db
```

## 故障排除

### 常见问题

1. **导入错误**
   - 检查 Python 版本（需要 3.8+）
   - 安装必要的依赖包

2. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接参数是否正确

3. **模型调用失败**
   - 检查 API 密钥是否设置
   - 验证网络连接
   - 确认模型名称和提供商配置

4. **Ollama 连接问题**
   - 确保 Ollama 服务正在运行
   - 检查模型是否已下载
   - 验证端口配置（默认 11434）

### 日志和调试
应用会输出详细的日志信息，帮助诊断问题。如需更详细的调试信息，可以修改代码中的日志级别。

## 开发和扩展

### 添加新的模型提供商
1. 在 `create_agent_instance` 方法中添加新的提供商支持
2. 在 Agent 配置对话框中添加新提供商选项
3. 安装相应的依赖包

### 自定义用户界面
当前使用命令行界面，可以扩展为 Web 界面或 GUI 界面。

### 数据库迁移
应用支持多数据库，可以根据需要迁移现有数据。

## 贡献和反馈

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件反馈
- 参与代码贡献

---

**注意**：请确保在使用 AI 服务时遵守相关法律法规和 API 使用条款。