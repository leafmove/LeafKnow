# LeafKnow Core Agent 模块详细使用说明文档

## 概述

LeafKnow Core Agent 模块是LeafKnow知识管理应用的核心AI智能体系统，负责管理AI模型、聊天会话、记忆管理、任务处理等功能。该模块采用模块化设计，支持多种AI模型提供商，具备完整的RAG检索能力和工具调用能力。

## 架构设计

### 核心组件

1. **数据库管理器 (db_mgr.py)** - 数据库结构管理和初始化
2. **模型管理器 (models_mgr.py)** - AI模型管理和调用
3. **聊天会话管理器 (chatsession_mgr.py)** - 聊天会话和消息管理
4. **记忆管理器 (memory_mgr.py)** - 上下文记忆和token管理
5. **任务管理器 (task_mgr.py)** - 异步任务处理
6. **工具提供者 (tool_provider.py)** - 动态工具加载和管理
7. **模型配置管理器 (model_config_mgr.py)** - 模型配置和能力分配
8. **向量数据库管理器 (lancedb_mgr.py)** - 向量检索和相似度搜索
9. **多向量管理器 (multivector_mgr.py)** - 多模态向量化处理
10. **聊天核心管理器 (chat_core_mgr.py)** - 增强版聊天应用框架

## 详细模块说明

### 1. 数据库管理器 (db_mgr.py)

**功能**: 负责SQLite数据库的初始化、表结构创建和维护

**核心类**:
- `DBManager`: 数据库结构管理类
- 各种数据模型类 (Task, Document, ChatSession等)

**主要数据表**:

#### 任务相关表
- **t_tasks**: 异步任务处理
  - 字段: id, task_name, task_type, priority, status, created_at, updated_at, start_time, result, error_message, extra_data, target_file_path
  - 状态: PENDING, RUNNING, COMPLETED, FAILED, CANCELED
  - 优先级: LOW, MEDIUM, HIGH
  - 类型: SCREENING, TAGGING, MULTIVECTOR

#### 文档处理表
- **t_documents**: 原始文件信息
- **t_parent_chunks**: 父内容块 (文本、图片、表格、知识卡片)
- **t_child_chunks**: 向量化子块，用于检索

#### 聊天相关表
- **t_chat_sessions**: 聊天会话
- **t_chat_messages**: 聊天消息 (支持Vercel AI SDK v5协议)
- **t_chat_session_pin_files**: 会话Pin文件 (RAG上下文)

#### 模型相关表
- **t_model_providers**: 模型提供商配置
- **t_model_configurations**: 具体模型配置
- **t_capability_assignments**: 模型能力分配

#### 工具和场景表
- **t_tools**: 可用工具配置
- **t_scenarios**: 预设场景配置

**使用示例**:
```python
from core.agent.db_mgr import DBManager
from sqlalchemy import create_engine

engine = create_engine('sqlite:///leafknow.db')
db_manager = DBManager(engine)

# 初始化数据库结构
db_manager.init_db()
```

### 2. 模型管理器 (models_mgr.py)

**功能**: AI模型管理、调用和流式响应处理

**核心类**: `ModelsMgr`

**主要方法**:

#### 嵌入向量生成
```python
embedding = models_mgr.get_embedding("要生成嵌入的文本")
```

#### LLM标签生成
```python
tags = models_mgr.get_tags_from_llm(
    file_path="/path/to/file.pdf",
    file_summary="文件内容摘要",
    candidate_tags=["候选标签1", "候选标签2"]
)
```

#### 会话标题生成
```python
title = models_mgr.generate_session_title("用户的第一条消息")
```

#### 聊天补全
```python
messages = [
    {"role": "user", "content": "你好"}
]
response = models_mgr.get_chat_completion(messages)
```

#### 流式聊天 (Vercel AI SDK v5兼容)
```python
async for chunk in models_mgr.stream_agent_chat_v5_compatible(messages, session_id=1):
    print(chunk, end='')
```

**特性**:
- 支持多模态 (文本+图片)
- 集成RAG检索
- 工具调用支持
- Vercel AI SDK v5协议兼容
- 自动模型下载和管理

### 3. 聊天会话管理器 (chatsession_mgr.py)

**功能**: 管理聊天会话、消息存储和Pin文件功能

**核心类**: `ChatSessionMgr`

**主要方法**:

#### 会话管理
```python
# 创建会话
session = chat_mgr.create_session(name="新对话", metadata={"topic": "AI"})

# 获取会话列表
sessions, total = chat_mgr.get_sessions(page=1, page_size=20, search="AI")

# 更新会话
session = chat_mgr.update_session(session_id=1, name="更新后的名称")

# 删除会话 (软删除)
success = chat_mgr.delete_session(session_id=1)
```

#### 场景管理
```python
# 更新会话场景
session = chat_mgr.update_session_scenario(
    session_id=1,
    scenario_id=1,  # co_reading场景
    metadata={"pdf_path": "/path/to/file.pdf"}
)

# 获取场景system_prompt
prompt = tool_provider.get_session_scenario_system_prompt(session_id=1)
```

#### 消息管理
```python
# 保存消息
message = chat_mgr.save_message(
    session_id=1,
    message_id="msg_123",
    role="user",
    content="用户消息",
    parts=[{"type": "text", "text": "用户消息"}],
    sources=[{"file_path": "/path/to/file.pdf", "content": "相关内容"}]
)

# 获取消息历史
messages, total = chat_mgr.get_messages(session_id=1, page=1, page_size=30)

# 获取最近消息 (用于恢复上下文)
recent_messages = chat_mgr.get_recent_messages(session_id=1, limit=10)
```

#### Pin文件管理 (RAG功能)
```python
# Pin文件到会话
pin_file = chat_mgr.pin_file(
    session_id=1,
    file_path="/path/to/document.pdf",
    file_name="document.pdf",
    metadata={"size": 1024, "type": "pdf"}
)

# 取消Pin文件
success = chat_mgr.unpin_file(session_id=1, file_path="/path/to/document.pdf")

# 获取Pin文件列表
pinned_files = chat_mgr.get_pinned_files(session_id=1)

# 获取Pin文件对应的文档ID (用于RAG检索)
doc_ids = chat_mgr.get_pinned_document_ids(session_id=1)
```

### 4. 记忆管理器 (memory_mgr.py)

**功能**: 管理聊天上下文、token计算和消息裁剪

**核心类**: `MemoryMgr`

**主要方法**:

#### 消息裁剪
```python
# 根据token限制裁剪消息历史
messages = memory_mgr.trim_messages_to_fit(session_id=1, max_tokens=4096)
```

#### Token计算
```python
# 计算工具token数
from core.agno.tools.function import Function as Tool
tools_tokens = memory_mgr.calculate_tools_tokens(tools)

# 计算字符串token数
text_tokens = memory_mgr.calculate_string_tokens("要计算的文本")
```

### 5. 任务管理器 (task_mgr.py)

**功能**: 异步任务队列管理，支持优先级和多进程处理

**核心类**: `TaskManager`

**主要方法**:

#### 任务创建和管理
```python
# 添加任务
task = task_mgr.add_task(
    task_name="向量化文档",
    task_type=TaskType.MULTIVECTOR,
    priority=TaskPriority.HIGH,
    extra_data={"file_path": "/path/to/file.pdf"},
    target_file_path="/path/to/file.pdf"
)

# 获取下一个任务
next_task = task_mgr.get_next_task()

# 获取并锁定下一个任务 (原子操作)
locked_task = task_mgr.get_and_lock_next_task()

# 更新任务状态
success = task_mgr.update_task_status(
    task_id=1,
    status=TaskStatus.COMPLETED,
    result=TaskResult.SUCCESS
)
```

#### 任务处理
```python
# 启动任务处理线程
worker_thread = task_mgr.start_task_worker(worker_function, args=(engine,))

# 启动任务处理进程
worker_process = task_mgr.start_task_process(worker_function, args=(engine,))

# 创建进程池
pool = task_mgr.start_process_pool(num_processes=4)
```

#### 任务查询
```python
# 获取最新完成的任务
completed_task = task_mgr.get_latest_completed_task(TaskType.MULTIVECTOR)

# 获取最新运行中的任务
running_task = task_mgr.get_latest_running_task(TaskType.MULTIVECTOR)

# 检查文件是否最近被处理过
is_recent = task_mgr.is_file_recently_pinned("/path/to/file.pdf", hours=8)
```

### 6. 工具提供者 (tool_provider.py)

**功能**: 动态工具加载和管理，支持多种工具类型

**核心类**: `ToolProvider`

**工具类型**:
- **DIRECT**: 直接调用Python函数
- **CHANNEL**: 通过消息通道调用前端功能
- **MCP**: 通过模型上下文协议调用

**主要方法**:

#### 获取工具
```python
# 为会话获取工具列表
tools = tool_provider.get_tools_for_session(session_id=1)

# 获取默认工具
default_tools = tool_provider._get_default_tools()

# 获取场景预置工具
scenario_tools = tool_provider._get_scenario_tools(scenario_id=1)
```

#### 场景管理
```python
# 获取可用场景列表
scenarios = tool_provider.get_available_scenarios()

# 获取会话场景的system_prompt
system_prompt = tool_provider.get_session_scenario_system_prompt(session_id=1)
```

#### MCP工具管理
```python
# 设置MCP工具API密钥
success = tool_provider.set_mcp_tool_api_key("search_use_tavily", "your_api_key")

# 获取MCP工具API密钥
api_key = tool_provider.get_mcp_tool_api_key("search_use_tavily")
```

**预置工具**:
- `get_current_time`: 获取当前时间
- `local_file_search`: 本机文件搜索
- `multimodal_vectorize`: 多模态向量化
- `search_use_tavily`: Tavily网络搜索

### 7. 模型配置管理器 (model_config_mgr.py)

**功能**: 管理AI模型配置、提供商和能力分配

**核心类**: `ModelConfigMgr`

**主要方法**:

#### 提供商管理
```python
# 获取所有提供商
providers = model_config_mgr.get_all_provider_configs()

# 创建提供商
provider = model_config_mgr.create_provider(
    provider_type="openai",
    display_name="My OpenAI",
    base_url="https://api.openai.com/v1",
    api_key="sk-xxx",
    is_active=True
)

# 更新提供商配置
provider = model_config_mgr.update_provider_config(
    id=1,
    display_name="Updated OpenAI",
    base_url="https://api.openai.com/v1",
    api_key="sk-yyy",
    extra_data_json={},
    is_active=True
)

# 删除提供商
success = model_config_mgr.delete_provider(provider_id=1)
```

#### 模型发现
```python
# 从提供商发现模型
models = await model_config_mgr.discover_models_from_provider(provider_id=1)

# 获取提供商的模型
models = model_config_mgr.get_models_by_provider(provider_id=1)
```

#### 能力管理
```python
from core.agent.db_mgr import ModelCapability

# 获取模型能力
capabilities = model_config_mgr.get_model_capabilities(model_id=1)

# 更新模型能力
success = model_config_mgr.update_model_capabilities(
    model_id=1,
    capabilities=[ModelCapability.TEXT, ModelCapability.VISION]
)

# 分配全局能力
success = model_config_mgr.assign_global_capability_to_model(
    model_config_id=1,
    capability=ModelCapability.TEXT
)

# 获取能力对应的模型配置
model_config = model_config_mgr.get_spec_model_config(ModelCapability.TEXT)
```

#### 模型配置获取
```python
# 获取文本模型配置
text_config = model_config_mgr.get_text_model_config()

# 获取视觉模型配置
vision_config = model_config_mgr.get_vision_model_config()

# 获取结构化输出模型配置
structured_config = model_config_mgr.get_structured_output_model_config()
```

### 8. 向量数据库管理器 (lancedb_mgr.py)

**功能**: 管理LanceDB向量数据库，提供向量检索功能

**核心类**: `LanceDBMgr`

**数据结构**:
- **Tags**: 标签向量存储
- **VectorRecord**: 文档向量记录

**主要方法**:

#### 表初始化
```python
# 初始化标签表
lancedb_mgr.init_tags_table("tags")

# 初始化向量表
lancedb_mgr.init_vectors_table("vectors")
```

#### 数据添加
```python
# 添加标签
tags_data = [
    {
        "vector": [0.1, 0.2, ...],  # 向量数据
        "text": "人工智能",
        "tag_id": 1
    }
]
lancedb_mgr.add_tags(tags_data)

# 添加向量记录
vector_records = [
    {
        "vector_id": "uuid-string",
        "vector": [0.1, 0.2, ...],
        "parent_chunk_id": 1,
        "document_id": 1,
        "retrieval_content": "检索内容"
    }
]
lancedb_mgr.add_vectors(vector_records)
```

#### 向量搜索
```python
# 基于查询文本搜索 (推荐)
results = lancedb_mgr.search_by_query(
    query_text="人工智能应用",
    models_mgr=models_mgr,
    top_k=10,
    document_ids=[1, 2, 3],  # 可选：限定文档范围
    distance_threshold=0.5    # 可选：相似度阈值
)

# 基于向量搜索
results = lancedb_mgr.search_by_vector(
    query_vector=[0.1, 0.2, ...],
    top_k=10,
    filters={"document_ids": [1, 2, 3]}
)

# 标签搜索
tag_results = lancedb_mgr.search_tags(query_vector=[0.1, 0.2, ...], limit=10)
```

### 9. 聊天核心管理器 (chat_core_mgr.py)

**功能**: 增强版聊天应用框架，支持多用户、Agent管理和数据库存储

**核心类**:
- `DatabaseManager`: 数据库连接管理
- `UserManager`: 用户管理
- `AgentManager`: Agent配置管理
- `SessionManager`: 会话管理
- `ConversationManager`: 对话历史管理

**主要功能**:

#### 多数据库支持
- SQLite (默认)
- MySQL
- PostgreSQL

#### 用户管理
```python
# 创建用户
user = user_mgr.create_user(username="testuser", email="test@example.com")

# 获取用户
user = user_mgr.get_user(user_id="uuid")

# 根据用户名获取用户
user = user_mgr.get_user_by_username("testuser")

# 列出所有用户
users = user_mgr.list_users()
```

#### Agent管理
```python
# 创建Agent配置
agent = agent_mgr.create_agent(user_id="uuid", config=AgentConfig(
    name="AI助手",
    model_id="gpt-4",
    provider="openai",
    base_url="https://api.openai.com/v1",
    api_key="sk-xxx",
    temperature=0.7,
    system_prompt="你是一个有用的AI助手"
))

# 获取用户的Agent
agents = agent_mgr.get_user_agents(user_id="uuid")

# 获取默认Agent
default_agent = agent_mgr.get_user_default_agent(user_id="uuid")

# 设置默认Agent
success = agent_mgr.set_default_agent(user_id="uuid", agent_id="agent-uuid")
```

#### 会话管理
```python
# 创建会话
session = session_mgr.create_session(
    user_id="uuid",
    title="新对话",
    current_agent_id="agent-uuid"
)

# 获取用户会话
sessions = session_mgr.get_user_sessions(user_id="uuid")

# 更新会话
success = session_mgr.update_session(
    session_id="session-uuid",
    title="更新后的标题"
)
```

## 使用示例

### 完整的聊天应用初始化

```python
from sqlalchemy import create_engine
from core.agent.db_mgr import DBManager
from core.agent.models_mgr import ModelsMgr
from core.agent.chatsession_mgr import ChatSessionMgr
from core.agent.memory_mgr import MemoryMgr
from core.agent.task_mgr import TaskManager
from core.agent.tool_provider import ToolProvider
from core.agent.model_config_mgr import ModelConfigMgr
from core.agent.lancedb_mgr import LanceDBMgr

# 1. 初始化数据库引擎
engine = create_engine('sqlite:///leafknow.db')

# 2. 初始化数据库结构
db_manager = DBManager(engine)
db_manager.init_db()

# 3. 初始化各个管理器
models_mgr = ModelsMgr(engine, base_dir="/path/to/data")
chat_session_mgr = ChatSessionMgr(engine)
memory_mgr = MemoryMgr(engine)
task_mgr = TaskManager(engine)
tool_provider = ToolProvider(engine)
model_config_mgr = ModelConfigMgr(engine)
lancedb_mgr = LanceDBMgr(base_dir="/path/to/data")

# 4. 初始化向量表
lancedb_mgr.init_tags_table()
lancedb_mgr.init_vectors_table()
```

### 创建聊天会话并发送消息

```python
# 1. 创建会话
session = chat_session_mgr.create_session(name="AI对话")

# 2. Pin文件用于RAG
chat_session_mgr.pin_file(
    session_id=session.id,
    file_path="/path/to/document.pdf",
    file_name="document.pdf"
)

# 3. 构建消息
messages = [
    {
        "role": "user",
        "content": "请帮我总结这个文档的主要内容",
        "parts": [{"type": "text", "text": "请帮我总结这个文档的主要内容"}]
    }
]

# 4. 流式聊天
async for chunk in models_mgr.stream_agent_chat_v5_compatible(
    messages,
    session_id=session.id
):
    print(chunk, end='')
```

### 异步任务处理

```python
def process_document(file_path: str, task_id: int):
    """文档处理任务函数"""
    try:
        # 更新任务状态为运行中
        task_mgr.update_task_status(task_id, TaskStatus.RUNNING)

        # 执行文档处理逻辑
        # ... 文档解析、向量化等操作 ...

        # 更新任务状态为完成
        task_mgr.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            TaskResult.SUCCESS
        )
    except Exception as e:
        # 更新任务状态为失败
        task_mgr.update_task_status(
            task_id,
            TaskStatus.FAILED,
            TaskResult.FAILURE,
            str(e)
        )

# 添加任务
task = task_mgr.add_task(
    task_name="处理文档",
    task_type=TaskType.MULTIVECTOR,
    priority=TaskPriority.HIGH,
    target_file_path="/path/to/document.pdf"
)

# 启动任务处理线程
task_mgr.start_task_worker(process_document, args=(task.target_file_path, task.id))
```

## 配置说明

### 模型配置

系统支持多种AI模型提供商:

1. **OpenAI**: GPT-4, GPT-3.5-turbo等
2. **Anthropic**: Claude系列模型
3. **Google Gemini**: Gemini系列模型
4. **Ollama**: 本地模型服务
5. **LM Studio**: 本地模型服务
6. **OpenRouter**: 多模型聚合服务

### 内置模型

系统内置MLX优化的模型 (Apple Silicon):

- **视觉模型**: `mlx-community/Qwen3-VL-4B-Instruct-3bit`
- **嵌入模型**: `mlx-community/embeddinggemma-300m-4bit`

### 工具配置

系统预置了多种工具:

- `get_current_time`: 时间查询
- `local_file_search`: 本地文件搜索
- `multimodal_vectorize`: 多模态向量化
- `search_use_tavily`: 网络搜索 (需要API密钥)

### 场景配置

系统预置了应用场景:

- `co_reading`: AI共读场景，用于PDF阅读和分析

## 最佳实践

### 1. 数据库管理
- 使用WAL模式提升并发性能
- 定期清理过期任务数据
- 合理设置连接池大小

### 2. 模型管理
- 为不同能力配置专门的模型
- 合理设置token限制避免超限
- 使用模型发现功能自动获取可用模型

### 3. 任务处理
- 合理设置任务优先级
- 使用多进程处理CPU密集型任务
- 监控任务执行状态和错误

### 4. 向量检索
- 定期重建向量索引
- 合理设置相似度阈值
- 使用文档过滤提升检索精度

### 5. 工具使用
- 根据场景选择合适的工具
- 合理配置工具权限
- 监控工具调用性能

## 故障排除

### 常见问题

1. **数据库锁定**: 确保使用WAL模式，检查并发访问
2. **模型调用失败**: 检查API密钥和网络连接
3. **向量检索慢**: 检查索引状态，考虑重建索引
4. **任务处理失败**: 检查任务日志和错误信息
5. **内存不足**: 调整批处理大小，优化数据结构

### 日志调试

系统使用Python标准logging模块，可通过以下方式启用详细日志:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 扩展开发

### 添加新工具

1. 在数据库中注册工具配置
2. 实现工具函数
3. 配置工具元数据
4. 添加到场景或会话

### 添加新模型提供商

1. 实现模型适配器
2. 添加提供商配置
3. 实现模型发现逻辑
4. 配置能力映射

### 添加新场景

1. 定义场景配置
2. 设置预置工具
3. 配置系统提示词
4. 测试场景功能

## 总结

LeafKnow Core Agent模块是一个功能完整的AI智能体系统，具备以下核心特性:

- **多模型支持**: 支持主流AI模型提供商
- **RAG检索**: 完整的向量检索和文档处理流程
- **工具调用**: 灵活的工具加载和调用机制
- **异步任务**: 高效的任务队列和处理机制
- **流式响应**: Vercel AI SDK v5兼容的流式聊天
- **多模态**: 支持文本和图片的多模态处理
- **可扩展性**: 模块化设计，易于扩展新功能

通过合理配置和使用这些组件，可以构建功能强大的知识管理和AI对话应用。