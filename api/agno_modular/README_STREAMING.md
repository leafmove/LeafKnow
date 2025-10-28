# Agno Modular 流式对话和多厂商适配指南

本指南详细介绍了如何使用 agno_modular 模块实现多厂商模型适配、流式对话输出和 WebSocket 集成功能。

## 🎯 功能概览

### 核心特性

- ✅ **多厂商模型适配**: 支持 OpenAI、Anthropic、本地模型等多种 AI 厂商
- ✅ **流式对话输出**: 支持多种流式输出格式（SSE、WebSocket、生成器）
- ✅ **多种生成器模式**: 标准、缓冲、分块、交错、优先级等模式
- ✅ **WebSocket 集成**: 实时双向通信和反馈机制
- ✅ **Agent 集成**: 与现有的 Agent 管理系统无缝集成
- ✅ **错误处理**: 完善的错误处理和降级机制
- ✅ **性能监控**: 内置统计和性能监控功能

## 📦 组件架构

### 1. 多厂商适配器 (`multi_provider_adapter.py`)

```python
from multi_provider_adapter import (
    MultiProviderManager, ProviderConfig, ProviderType,
    register_openai_provider, register_anthropic_provider
)

# 创建管理器
manager = MultiProviderManager()

# 注册 OpenAI 提供商
await register_openai_provider(
    provider_id="openai_gpt35",
    api_key="your-api-key",
    model_name="gpt-3.5-turbo"
)

# 注册 Anthropic 提供商
await register_anthropic_provider(
    provider_id="anthropic_claude",
    api_key="your-api-key",
    model_name="claude-3-sonnet-20240229"
)

# 使用提供商进行对话
adapter = manager.get_adapter("openai_gpt35")
async for event in adapter.stream_chat(messages):
    print(event)
```

### 2. 流式对话 (`streaming_chat.py`)

```python
from streaming_chat import (
    StreamingChatManager, StreamEvent, StreamFormat,
    create_streaming_chat_response
)

# 创建流式聊天管理器
manager = StreamingChatManager(provider_manager)

# 使用标准流式输出
async for chunk in create_streaming_chat_response(
    messages=[{"role": "user", "content": "Hello"}],
    stream_format=StreamFormat.SSE
):
    print(chunk)
```

### 3. 流式生成器 (`streaming_generator.py`)

```python
from streaming_generator import (
    StreamingGeneratorFactory, GeneratorMode, GeneratorConfig,
    streaming_context
)

# 使用标准生成器
async with streaming_context(GeneratorMode.STANDARD) as generator:
    async for event in generator.generate(messages):
        print(event.data)

# 使用缓冲生成器
config = GeneratorConfig(
    mode=GeneratorMode.BUFFERED,
    buffer_size=1024,
    flush_interval=0.1
)

async with streaming_context(GeneratorMode.BUFFERED, config) as generator:
    async for event in generator.generate(messages):
        print(event.data)
```

### 4. WebSocket 集成 (`websocket_integration.py`)

```python
from websocket_integration import (
    WebSocketManager, WebSocketMessage, WebSocketMessageType
)

# 创建 WebSocket 管理器
ws_manager = WebSocketManager(streaming_manager, provider_manager)

# 添加连接
connection = await ws_manager.add_connection(
    websocket=websocket,
    user_id="user123",
    session_id="session456"
)

# 发送消息
message = WebSocketMessage(
    message_type=WebSocketMessageType.CHAT_REQUEST,
    data={"messages": [{"role": "user", "content": "Hello"}]}
)
await connection.send_message(message)
```

## 🚀 快速开始

### 1. 基础设置

```python
import asyncio
from multi_provider_adapter import get_multi_provider_manager
from streaming_chat import get_streaming_manager

async def setup():
    # 获取全局管理器
    provider_manager = get_multi_provider_manager()
    streaming_manager = get_streaming_manager()

    # 注册提供商
    await register_openai_provider(
        provider_id="openai_main",
        api_key="your-api-key",
        model_name="gpt-4"
    )

# 运行设置
asyncio.run(setup())
```

### 2. 简单流式对话

```python
async def simple_streaming_chat():
    manager = get_streaming_manager()

    messages = [
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "介绍一下Python编程语言。"}
    ]

    # 创建流式响应
    async for chunk in manager.create_session().stream_chat(
        messages=messages,
        stream_format=StreamFormat.SSE
    ):
        if chunk.startswith("data: "):
            data = json.loads(chunk[6:])
            if data.get("type") == "text-delta":
                print(data.get("content", ""), end="", flush=True)

# 运行对话
asyncio.run(simple_streaming_chat())
```

### 3. WebSocket 客户端示例

```javascript
// 前端 WebSocket 客户端
const ws = new WebSocket('ws://localhost:8000/api/streaming/ws/user123');

ws.onopen = function(event) {
    console.log('WebSocket连接已建立');

    // 发送聊天请求
    ws.send(JSON.stringify({
        message_type: 'chat_request',
        data: {
            messages: [
                {role: 'user', content: '你好！'}
            ],
            generator_mode: 'standard'
        }
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.message_type === 'stream_event') {
        const eventData = data.data;

        if (eventData.event_type === 'text-delta') {
            // 处理文本增量
            console.log(eventData.event_data.content);
        } else if (eventData.event_type === 'finish') {
            // 处理完成事件
            console.log('对话完成');
        }
    }
};
```

## 🔧 高级用法

### 1. 多厂商对比

```python
async def compare_providers():
    messages = [{"role": "user", "content": "解释什么是机器学习"}]
    providers = ["openai_gpt35", "anthropic_claude", "agno_native"]

    results = {}

    for provider_id in providers:
        response = ""
        async for chunk in streaming_manager.create_session().stream_chat(
            messages=messages,
            provider_id=provider_id
        ):
            if "text-delta" in chunk:
                response += chunk
        results[provider_id] = response

    return results
```

### 2. 自定义生成器模式

```python
from streaming_generator import StreamingGenerator

class CustomStreamingGenerator(StreamingGenerator):
    async def generate(self, messages, provider_id=None, **kwargs):
        # 自定义生成逻辑
        adapter = self.provider_manager.get_adapter(provider_id)

        # 添加自定义处理
        async for provider_event in adapter.stream_chat(messages, **kwargs):
            # 自定义事件处理
            event = self.custom_process_event(provider_event)
            yield event

    def custom_process_event(self, provider_event):
        # 自定义事件处理逻辑
        return self._convert_to_stream_event(provider_event)

# 使用自定义生成器
generator = CustomStreamingGenerator(config, provider_manager)
```

### 3. 错误处理和重试

```python
async def robust_streaming_chat(messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            async for chunk in streaming_manager.create_session().stream_chat(
                messages=messages,
                provider_id="openai_gpt35"
            ):
                yield chunk
            break
        except Exception as e:
            if attempt == max_retries - 1:
                # 最后一次尝试失败，发送错误事件
                yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'
            else:
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2 ** attempt)  # 指数退避
```

### 4. 性能优化

```python
from streaming_generator import BufferedStreamingGenerator, GeneratorConfig

# 使用缓冲模式减少网络请求
config = GeneratorConfig(
    mode=GeneratorMode.BUFFERED,
    buffer_size=512,  # 缓冲512字节
    flush_interval=0.2  # 每200ms刷新一次
)

async def optimized_streaming(messages):
    generator = BufferedStreamingGenerator(config, provider_manager)

    async for event in generator.generate(messages):
        # 事件已经过缓冲处理
        yield event
```

## 🌐 API 集成

### FastAPI 集成示例

```python
from fastapi import FastAPI
from agno_modular.streaming_api import router as streaming_router

app = FastAPI()

# 注册流式 API 路由
app.include_router(streaming_router)

# 启动事件
@app.on_event("startup")
async def startup_event():
    from agno_modular.streaming_api import on_startup
    await on_startup()

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    from agno_modular.streaming_api import on_shutdown
    await on_shutdown()
```

### API 端点使用

```bash
# 流式聊天
curl -X POST "http://localhost:8000/api/streaming/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好！"}
    ],
    "stream_format": "sse",
    "provider_id": "openai_gpt35"
  }'

# 注册提供商
curl -X POST "http://localhost:8000/api/streaming/providers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "my_openai",
    "provider_type": "openai",
    "model_name": "gpt-4",
    "api_key": "your-api-key"
  }'

# WebSocket 连接
ws://localhost:8000/api/streaming/ws/user123?session_id=session456
```

## 📊 监控和统计

### 获取系统状态

```python
async def get_system_stats():
    provider_manager = get_multi_provider_manager()
    streaming_manager = get_streaming_manager()
    websocket_manager = get_websocket_manager()

    stats = {
        "providers": await provider_manager.health_check_all(),
        "streaming": {
            "active_sessions": streaming_manager.get_active_sessions_count()
        },
        "websocket": websocket_manager.get_statistics()
    }

    return stats
```

### 自定义监控

```python
class CustomMonitor:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []

    async def monitor_streaming_chat(self, messages, **kwargs):
        start_time = time.time()
        self.request_count += 1

        try:
            async for chunk in streaming_manager.create_session().stream_chat(
                messages, **kwargs
            ):
                yield chunk
        except Exception as e:
            self.error_count += 1
            raise
        finally:
            response_time = time.time() - start_time
            self.response_times.append(response_time)

    def get_stats(self):
        return {
            "total_requests": self.request_count,
            "error_rate": self.error_count / self.request_count,
            "avg_response_time": sum(self.response_times) / len(self.response_times)
        }
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest test_integration.py -v

# 运行特定测试
pytest test_integration.py::TestMultiProviderAdapter -v

# 运行异步测试
pytest test_integration.py::TestStreamingChat::test_streaming_session -v -s
```

### 基础测试

```python
async def run_basic_tests():
    from test_integration import run_basic_tests
    await run_basic_tests()
```

## 🚨 故障排除

### 常见问题

**Q: WebSocket 连接失败**
A: 检查防火墙设置，确保端口开放，验证 WebSocket URL 正确性。

**Q: 提供商注册失败**
A: 验证 API 密钥正确性，检查网络连接，确认提供商服务可用。

**Q: 流式输出中断**
A: 检查网络稳定性，查看错误日志，确认提供商支持流式输出。

**Q: 性能问题**
A: 考虑使用缓冲模式，调整缓冲区大小，监控资源使用情况。

### 调试模式

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 启用特定模块的日志
logger = logging.getLogger('agno_modular')
logger.setLevel(logging.DEBUG)
```

## 🔮 扩展开发

### 添加新的提供商

```python
from multi_provider_adapter import BaseProviderAdapter

class CustomProviderAdapter(BaseProviderAdapter):
    async def create_model(self):
        # 实现模型创建逻辑
        pass

    async def stream_chat(self, messages, tools=None, **kwargs):
        # 实现流式聊天逻辑
        pass

    def supports_feature(self, feature):
        # 实现功能检查逻辑
        return True

# 注册自定义提供商
def register_custom_provider(manager, provider_id, config):
    adapter = CustomProviderAdapter(config)
    manager._adapters[provider_id] = adapter
```

### 添加新的生成器模式

```python
from streaming_generator import StreamingGenerator

class CustomModeGenerator(StreamingGenerator):
    async def generate(self, messages, provider_id=None, **kwargs):
        # 实现自定义生成逻辑
        pass

# 注册到工厂
StreamingGeneratorFactory._generator_map[GeneratorMode.CUSTOM] = CustomModeGenerator
```

## 📚 参考资料

- [FastAPI WebSocket 文档](https://fastapi.tiangolo.com/advanced/websockets/)
- [Server-Sent Events 规范](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Pydantic-AI 文档](https://pydantic-ai.readthedocs.io/)
- [AsyncIO 编程指南](https://docs.python.org/3/library/asyncio.html)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个模块！

## 📄 许可证

本项目采用 MIT 许可证。