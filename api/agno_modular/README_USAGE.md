# Agno Modular 使用指南

本指南详细说明如何使用 agno_modular 模块实现的多厂商适配、流式对话和 Agent 管理功能。

## 🎯 解决的问题

原始问题：`ModuleNotFoundError: No module named 'agno'`

## 📦 模块结构

```
agno_modular/
├── agent_models.py          # Agent 数据模型和管理器
├── agent_manager.py         # Agent CRUD 管理器
├── agent_api.py            # Agent API 接口
├── multi_provider_adapter.py # 多厂商适配器
├── streaming_chat.py        # 流式对话核心
├── streaming_generator.py   # 流式生成器
├── websocket_integration.py # WebSocket 集成
├── streaming_api.py        # 流式对话 API
├── complete_demo.py        # 完整功能演示
├── streaming_demo.py        # 流式对话演示
├── usage_examples.py       # Agent 使用示例（需要修复）
├── standalone_demo.py      # 独立配置演示
└── README.md              # 本文档
```

## 🚀 快速开始

### 1. 运行完整演示

```bash
cd /d/Workspace/LeafKnow/api
python agno_modular/complete_demo.py
```

这将演示：
- ✅ 多厂商AI模型适配
- ✅ Agent生命周期管理
- ✅ 流式对话输出
- ✅ 并发请求处理
- ✅ SSE格式流式输出
- ✅ 使用统计和性能监控

### 2. 运行流式对话演示

```bash
python agno_modular/streaming_demo.py
```

这将重点演示：
- ✅ 多厂商并发流式对话
- ✅ SSE格式输出
- ✅ 错误处理和重试机制
- ✅ 性能对比分析

### 3. 运行配置演示

```bash
python agno_modular/standalone_demo.py
```

这将演示：
- ✅ Agent配置类设计
- ✅ MCP工具配置
- ✅ 记忆管理配置
- ✅ 系统组合模式
- ✅ 配置验证和导出

## 🔧 核心功能

### 1. 多厂商适配器

支持多个 AI 提供商的统一接口：

```python
from agno_modular.complete_demo import ProviderConfig, MultiProviderManager

# 创建管理器
provider_manager = MultiProviderManager()

# 注册 OpenAI 提供商
await provider_manager.register_provider(
    "openai_main",
    ProviderConfig(
        provider_type=ProviderType.OPENAI,
        model_name="gpt-4",
        api_key="your-api-key",
        max_tokens=4000,
        temperature=0.7
    )
)

# 注册 Anthropic 提供商
await provider_manager.register_provider(
    "anthropic_claude",
    ProviderConfig(
        provider_type=ProviderType.ANTHROPIC,
        model_name="claude-3-sonnet-20240229",
        api_key="your-api-key"
    )
)

# 获取适配器并使用
adapter = provider_manager.get_adapter("openai_main")
async for event in adapter.stream_chat(messages):
    print(event.get("content", ""))
```

### 2. Agent 管理

完整的 Agent 生命周期管理：

```python
from agno_modular.complete_demo import AgentConfig, AgentManager, AgentType

# 创建管理器
agent_manager = AgentManager(provider_manager)

# 创建 Agent
qa_agent = agent_manager.create_agent(
    config=AgentConfig(
        name="Python助手",
        agent_type=AgentType.QA,
        system_prompt="你是一个专业的Python编程助手",
        capabilities=["text", "reasoning", "code_generation"]
    ),
    user_id=1
)

# 运行 Agent
response = await agent_manager.run_agent(
    agent_id=qa_agent.id,
    message="如何实现快速排序？",
    provider_id="openai_main"
)
```

### 3. 流式对话

支持多种流式输出格式：

```python
from agno_modular.complete_demo import StreamEvent

# 创建流式事件
event = StreamEvent(
    event_type="text-delta",
    data={"content": "Hello World"}
)

# 转换为SSE格式
sse_output = event.to_sse_format()
print(sse_output)
# 输出: data: {"type": "text-delta", "id": "...", "content": "Hello World", "timestamp": "..."}
```

### 4. 并发处理

高效的并发请求处理：

```python
import asyncio

async def run_concurrent_queries(provider_manager, agent_manager):
    tasks = []
    providers = ["openai_main", "anthropic_claude", "agno_native"]
    message = "简单解释什么是异步编程。"

    for provider_id in providers:
        task = agent_manager.run_agent(
            agent_id=1,  # Agent ID
            message=message,
            provider_id=provider_id
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

## 🛠️ 集成到现有项目

### 1. FastAPI 集成

```python
from agno_modular.streaming_api import router as streaming_router
from agno_modular.complete_demo import MultiProviderManager, AgentManager

app = FastAPI()

# 创建管理器实例
provider_manager = MultiProviderManager()
agent_manager = AgentManager(provider_manager)

# 注册路由
app.include_router(streaming_router)

# 启动事件
@app.on_event("startup")
async def startup_event():
    # 初始化提供商
    await provider_manager.register_provider("openai", ProviderConfig(...))
    await provider_manager.register_provider("anthropic", ProviderConfig(...))

    print("Agno Modular 初始化完成")
```

### 2. 数据库集成

要将 Agent 数据持久化，可以扩展现有的代码：

```python
# 扩展现有的 Agent 管理器
class DatabaseAgentManager(AgentManager):
    def __init__(self, db_engine, provider_manager):
        super().__init__(provider_manager)
        self.db_engine = db_engine

    def save_agent_to_db(self, agent: Agent):
        """保存Agent到数据库"""
        # 实现数据库保存逻辑
        pass

    def load_agent_from_db(self, agent_id: int) -> Agent:
        """从数据库加载Agent"""
        # 实现数据库加载逻辑
        pass
```

### 3. WebSocket 集成

```python
from fastapi import WebSocket

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data["type"] == "chat_request":
                # 处理聊天请求
                response = await agent_manager.run_agent(
                    agent_id=message_data["agent_id"],
                    message=message_data["message"]
                )

                # 流式发送响应
                await websocket.send_text(json.dumps({
                    "type": "chat_response",
                    "data": response
                }))

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {user_id}")
```

## 📊 性能特性

### 1. 异步并发

- ✅ 支持多个提供商并发请求
- ✅ 异步I/O，不阻塞主线程
- ✅ 协程池管理和资源优化

### 2. 流式输出

- ✅ 实时数据传输
- ✅ 减少首字节延迟
- ✅ 支持SSE、WebSocket、生成器多种格式

### 3. 错误处理

- ✅ 提供商连接失败重试
- ✅ 网络超时处理
- ✅ 优雅降级机制

### 4. 性能监控

- ✅ 响应时间统计
- ✅ 成功率监控
- ✅ 使用量分析

## 🔧 自定义扩展

### 1. 添加新的提供商

```python
class CustomProviderAdapter(BaseProviderAdapter):
    """自定义提供商适配器"""

    async def stream_chat(self, messages, **kwargs):
        """实现自定义流式聊天"""
        # 调用你的AI服务API
        async for chunk in your_api.stream_chat(messages):
            yield chunk

    def supports_feature(self, feature):
        """检查功能支持"""
        return feature in ["streaming", "tools"]

# 注册自定义提供商
await provider_manager.register_provider(
    "custom_llm",
    ProviderConfig(
        provider_type="custom",
        model_name="custom-model"
    )
)
```

### 2. 自定义Agent类型

```python
class CustomAgentType(str, Enum):
    CUSTOM_TYPE = "custom_type"

# 创建自定义Agent
agent = agent_manager.create_agent(
    config=AgentConfig(
        name="自定义助手",
        agent_type=AgentType.CUSTOM,
        system_prompt="你是一个自定义的AI助手",
        capabilities=["custom_capability"]
    )
)
```

### 3. 自定义流式事件

```python
class CustomStreamEvent(StreamEvent):
    """自定义流式事件"""
    def __init__(self, event_type: str, data: Dict[str, Any]):
        super().__init__(event_type, data)
        self.custom_field = data.get("custom_field")

    def to_custom_format(self):
        """转换为自定义格式"""
        return f"CUSTOM:{self.event_type}:{self.data}"
```

## 📚 最佳实践

### 1. 错误处理

```python
try:
    response = await agent_manager.run_agent(agent_id, message)
except ValueError as e:
    # 处理配置错误
    logger.error(f"Agent配置错误: {e}")
except Exception as e:
    # 处理运行时错误
    logger.error(f"Agent运行错误: {e}")
```

### 2. 资源管理

```python
# 使用上下文管理器确保资源清理
async def with_agent_session():
    agent_manager = AgentManager(provider_manager)
    try:
        # 使用Agent
        yield agent_manager
    finally:
        # 清理资源
        pass
```

### 3. 配置管理

```python
# 使用配置文件
import yaml

def load_config(config_path: str):
    with open(config_path) as f:
        return yaml.safe_load(f)

config = load_config("config.yaml")
provider_manager = MultiProviderManager()
await provider_manager.register_provider("main", ProviderConfig(**config["provider"]))
```

## 🧪 测试

### 1. 单元测试

```python
import pytest
from agno_modular.complete_demo import ProviderConfig, MultiProviderManager

@pytest.mark.asyncio
async def test_provider_registration():
    manager = MultiProviderManager()

    config = ProviderConfig(
        provider_type=ProviderType.OPENAI,
        model_name="gpt-3.5-turbo"
    )

    success = await manager.register_provider("test", config)
    assert success is True
    assert "test" in manager.adapters
```

### 2. 集成测试

```python
import pytest
from agno_modular.complete_demo import AgentManager, MultiProviderManager

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    # 创建管理器
    provider_manager = MultiProviderManager()
    agent_manager = AgentManager(provider_manager)

    # 注册提供商
    await provider_manager.register_provider("test", ProviderConfig(
        provider_type=ProviderType.OPENAI,
        model_name="gpt-3.5-turbo"
    ))

    # 创建Agent
    agent = agent_manager.create_agent(
        config=AgentConfig(
            name="测试Agent",
            agent_type=AgentType.QA
        )
    )

    # 运行Agent
    response = await agent_manager.run_agent(
        agent_id=agent.id,
        message="测试消息"
    )

    assert response is not None
    assert len(response) > 0
```

## 🔍 故障排除

### 1. 导入错误

**问题**: `ModuleNotFoundError: No module named 'agno'`

**解决方案**: 使用完整的模块路径：

```python
# 错误的导入
from agno.agent.agent import Agent

# 正确的导入
from agno_modular.complete_demo import Agent
# 或者直接使用本地的类定义
```

### 2. 连接错误

**问题**: 提供商连接失败

**解决方案**: 检查配置和网络：

```python
# 检查健康状态
health_status = await provider_manager.health_check_all()
for provider_id, status in health_status.items():
    if status["status"] != "healthy":
        print(f"Provider {provider_id} is unhealthy: {status}")
```

### 3. 流式输出问题

**问题**: 流式输出中断或延迟

**解决方案**: 检查异步实现：

```python
# 确保使用async/await
async def stream_response():
    async for chunk in adapter.stream_chat(messages):
        print(chunk)  # 避免同步阻塞
```

## 📝 更新日志

### v1.0.0 (2025-10-28)
- ✅ 初始版本发布
- ✅ 多厂商适配器架构
- ✅ Agent 管理系统
- ✅ 流式对话功能
- ✅ WebSocket 集成
- ✅ 完整演示和文档

---

## 💡 总结

agno_modular 模块提供了一个完整的多厂商AI适配和流式对话解决方案：

1. **模块化设计**: 清晰的组件分离，易于扩展
2. **异步架构**: 高性能的并发处理能力
3. **多厂商支持**: 统一接口支持多个AI提供商
4. **流式对话**: 实时数据传输和多种输出格式
5. **完整示例**: 从基础到高级的完整演示

通过本指南，你可以快速上手并集成到现有项目中，享受多厂商AI和流式对话带来的强大功能！