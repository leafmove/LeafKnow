"""
集成测试
测试多厂商适配、流式对话和WebSocket集成的完整功能
"""

import asyncio
import json
import pytest
import logging
from typing import Dict, Any, List
from datetime import datetime

# 导入要测试的模块
from multi_provider_adapter import (
    MultiProviderManager, ProviderConfig, ProviderType,
    OpenAIProviderAdapter, AnthropicProviderAdapter
)
from streaming_chat import (
    StreamEvent, StreamEventType, StreamFormat,
    StreamingChatSession, StreamingChatManager
)
from streaming_generator import (
    StreamingGeneratorFactory, GeneratorMode, GeneratorConfig,
    StandardStreamingGenerator, BufferedStreamingGenerator
)
from websocket_integration import (
    WebSocketManager, WebSocketMessage, WebSocketMessageType,
    WebSocketConnection, ConnectionState
)

# 配置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockWebSocket:
    """模拟WebSocket连接用于测试"""

    def __init__(self):
        self.messages = []
        self.closed = False
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        self.messages.append(message)

    async def receive_text(self):
        # 模拟接收消息
        if not self.messages:
            return json.dumps({
                "message_type": "chat_request",
                "data": {"messages": [{"role": "user", "content": "Hello"}]}
            })
        return self.messages.pop(0)

    async def close(self):
        self.closed = True


class MockProviderAdapter:
    """模拟提供商适配器用于测试"""

    def __init__(self, config):
        self.config = config
        self.provider_type = config.provider_type
        self.model_name = config.model_name

    async def create_model(self):
        return self

    async def stream_chat(self, messages: List[Dict[str, Any]], tools=None, **kwargs):
        """模拟流式聊天"""
        # 模拟一些文本流式输出
        test_response = "This is a mock streaming response from the provider."
        for char in test_response:
            yield {
                "type": "text-delta",
                "content": char
            }
            await asyncio.sleep(0.01)  # 模拟延迟

        yield {"type": "finish", "reason": "stop"}

    async def chat_completion(self, messages: List[Dict[str, Any]], tools=None, **kwargs):
        """模拟非流式聊天完成"""
        return {
            "content": "Mock response from provider",
            "role": "assistant",
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

    def supports_feature(self, feature: str) -> bool:
        """模拟功能支持检查"""
        return True

    async def health_check(self) -> Dict[str, Any]:
        """模拟健康检查"""
        return {
            "status": "healthy",
            "provider": self.provider_type.value,
            "model": self.model_name,
            "response_time": 0.1,
            "timestamp": datetime.now().isoformat()
        }


class TestMultiProviderAdapter:
    """测试多厂商适配器"""

    @pytest.fixture
    def provider_manager(self):
        """创建提供商管理器"""
        return MultiProviderManager()

    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="gpt-3.5-turbo-test",
            api_key="test-key",
            max_tokens=100
        )

    @pytest.mark.asyncio
    async def test_register_provider(self, provider_manager, mock_config):
        """测试提供商注册"""
        # 模拟适配器创建
        def mock_create_adapter(config):
            return MockProviderAdapter(config)

        provider_manager._create_adapter = mock_create_adapter

        # 注册提供商
        success = await provider_manager.register_provider("test_provider", mock_config)
        assert success is True
        assert "test_provider" in provider_manager._adapters

    @pytest.mark.asyncio
    async def test_get_adapter(self, provider_manager, mock_config):
        """测试获取适配器"""
        provider_manager._create_adapter = lambda config: MockProviderAdapter(config)
        await provider_manager.register_provider("test_provider", mock_config)

        adapter = provider_manager.get_adapter("test_provider")
        assert adapter is not None
        assert isinstance(adapter, MockProviderAdapter)

    @pytest.mark.asyncio
    async def test_health_check(self, provider_manager, mock_config):
        """测试健康检查"""
        provider_manager._create_adapter = lambda config: MockProviderAdapter(config)
        await provider_manager.register_provider("test_provider", mock_config)

        health_status = await provider_manager.health_check_all()
        assert "test_provider" in health_status
        assert health_status["test_provider"]["status"] == "healthy"

    def test_list_providers(self, provider_manager, mock_config):
        """测试列出提供商"""
        adapter = MockProviderAdapter(mock_config)
        provider_manager._adapters["test_provider"] = adapter
        provider_manager._default_provider = "test_provider"

        providers = provider_manager.list_providers()
        assert len(providers) == 1
        assert providers[0]["provider_id"] == "test_provider"
        assert providers[0]["is_default"] is True


class TestStreamingChat:
    """测试流式对话"""

    @pytest.fixture
    def streaming_manager(self):
        """创建流式聊天管理器"""
        provider_manager = MultiProviderManager()
        return StreamingChatManager(provider_manager)

    @pytest.fixture
    def mock_provider(self):
        """创建模拟提供商"""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="test-model"
        )
        return MockProviderAdapter(config)

    @pytest.mark.asyncio
    async def test_streaming_session(self, streaming_manager):
        """测试流式对话会话"""
        # 创建模拟会话
        session = streaming_manager.create_session("test_session")

        assert session.session_id == "test_session"
        assert session.provider_manager is not None

    @pytest.mark.asyncio
    async def test_stream_event_conversion(self, streaming_manager):
        """测试流式事件转换"""
        session = streaming_manager.create_session("test_session")

        # 测试提供者事件转换
        provider_event = {
            "type": "text-delta",
            "content": "Hello"
        }

        stream_event = session._convert_provider_event(provider_event)
        assert stream_event.event_type == StreamEventType.TEXT_DELTA
        assert stream_event.data["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_sse_format(self):
        """测试SSE格式化"""
        event = StreamEvent(
            event_type=StreamEventType.TEXT_DELTA,
            data={"content": "Hello"}
        )

        sse_format = event.to_sse_format()
        assert sse_format.startswith("data: ")
        assert "text-delta" in sse_format
        assert "Hello" in sse_format

    @pytest.mark.asyncio
    async def test_websocket_format(self):
        """测试WebSocket格式化"""
        event = StreamEvent(
            event_type=StreamEventType.TEXT_DELTA,
            data={"content": "Hello"}
        )

        ws_format = event.to_websocket_format()
        assert isinstance(ws_format, dict)
        assert ws_format["type"] == "text-delta"
        assert ws_format["data"]["content"] == "Hello"


class TestStreamingGenerator:
    """测试流式生成器"""

    @pytest.fixture
    def generator_config(self):
        """创建生成器配置"""
        return GeneratorConfig(
            mode=GeneratorMode.STANDARD,
            buffer_size=100,
            chunk_size=50
        )

    @pytest.fixture
    def mock_provider_manager(self):
        """创建模拟提供商管理器"""
        manager = MultiProviderManager()
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="test-model"
        )
        adapter = MockProviderAdapter(config)
        manager._adapters["test"] = adapter
        manager._default_provider = "test"
        return manager

    @pytest.mark.asyncio
    async def test_standard_generator(self, generator_config, mock_provider_manager):
        """测试标准生成器"""
        generator = StandardStreamingGenerator(generator_config, mock_provider_manager)

        messages = [{"role": "user", "content": "Hello"}]
        events = []

        async for event in generator.generate(messages, "test"):
            events.append(event)

        assert len(events) > 0
        # 检查是否有文本增量事件
        text_events = [e for e in events if e.event_type == StreamEventType.TEXT_DELTA]
        assert len(text_events) > 0

    @pytest.mark.asyncio
    async def test_buffered_generator(self, generator_config, mock_provider_manager):
        """测试缓冲生成器"""
        buffered_config = GeneratorConfig(
            mode=GeneratorMode.BUFFERED,
            buffer_size=10,
            flush_interval=0.05
        )
        generator = BufferedStreamingGenerator(buffered_config, mock_provider_manager)

        messages = [{"role": "user", "content": "Hello"}]
        events = []

        async for event in generator.generate(messages, "test"):
            events.append(event)

        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_generator_factory(self, mock_provider_manager):
        """测试生成器工厂"""
        # 测试标准生成器创建
        generator = StreamingGeneratorFactory.create_generator(
            GeneratorMode.STANDARD,
            provider_manager=mock_provider_manager
        )
        assert isinstance(generator, StandardStreamingGenerator)

        # 测试缓冲生成器创建
        config = GeneratorConfig(mode=GeneratorMode.BUFFERED)
        generator = StreamingGeneratorFactory.create_generator(
            GeneratorMode.BUFFERED,
            config,
            mock_provider_manager
        )
        assert isinstance(generator, BufferedStreamingGenerator)


class TestWebSocketIntegration:
    """测试WebSocket集成"""

    @pytest.fixture
    def websocket_manager(self):
        """创建WebSocket管理器"""
        provider_manager = MultiProviderManager()
        from streaming_chat import StreamingChatManager
        streaming_manager = StreamingChatManager(provider_manager)
        return WebSocketManager(streaming_manager, provider_manager)

    @pytest.fixture
    def mock_websocket(self):
        """创建模拟WebSocket"""
        return MockWebSocket()

    @pytest.mark.asyncio
    async def test_websocket_connection_creation(self, websocket_manager, mock_websocket):
        """测试WebSocket连接创建"""
        connection = await websocket_manager.add_connection(
            websocket=mock_websocket,
            user_id="test_user",
            session_id="test_session"
        )

        assert connection.connection_id is not None
        assert connection.user_id == "test_user"
        assert connection.session_id == "test_session"
        assert connection.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_websocket_message_sending(self, websocket_manager, mock_websocket):
        """测试WebSocket消息发送"""
        connection = await websocket_manager.add_connection(
            websocket=mock_websocket,
            user_id="test_user"
        )

        message = WebSocketMessage(
            message_type=WebSocketMessageType.CHAT_RESPONSE,
            data={"content": "Hello"}
        )

        success = await connection.send_message(message)
        assert success is True
        assert len(mock_websocket.messages) > 0

    @pytest.mark.asyncio
    async def test_websocket_stream_event(self, websocket_manager, mock_websocket):
        """测试WebSocket流式事件发送"""
        connection = await websocket_manager.add_connection(
            websocket=mock_websocket,
            user_id="test_user"
        )

        event = StreamEvent(
            event_type=StreamEventType.TEXT_DELTA,
            data={"content": "Hello"}
        )

        success = await connection.send_stream_event(event)
        assert success is True

    @pytest.mark.asyncio
    async def test_websocket_manager_stats(self, websocket_manager, mock_websocket):
        """测试WebSocket管理器统计"""
        # 添加多个连接
        await websocket_manager.add_connection(mock_websocket, "user1")
        await websocket_manager.add_connection(MockWebSocket(), "user2")

        stats = websocket_manager.get_statistics()
        assert stats["total_connections"] >= 2
        assert stats["active_connections"] >= 2
        assert stats["user_count"] >= 2

    @pytest.mark.asyncio
    async def test_user_connections(self, websocket_manager, mock_websocket):
        """测试用户连接管理"""
        user_id = "test_user"

        # 为同一用户添加多个连接
        connection1 = await websocket_manager.add_connection(mock_websocket, user_id)
        connection2 = await websocket_manager.add_connection(MockWebSocket(), user_id)

        user_connections = await websocket_manager.get_user_connections(user_id)
        assert len(user_connections) == 2

        # 广播消息给用户
        message = WebSocketMessage(
            message_type=WebSocketMessageType.STATUS_UPDATE,
            data={"status": "test"}
        )

        success_count = await websocket_manager.broadcast_to_user(user_id, message)
        assert success_count == 2


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_streaming(self):
        """端到端流式对话测试"""
        # 创建组件
        provider_manager = MultiProviderManager()
        streaming_manager = StreamingChatManager(provider_manager)

        # 注册模拟提供商
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="test-model"
        )
        adapter = MockProviderAdapter(config)
        provider_manager._adapters["mock"] = adapter
        provider_manager._default_provider = "mock"

        # 创建流式对话会话
        session = streaming_manager.create_session("test_session")
        messages = [{"role": "user", "content": "Hello"}]

        # 收集响应
        response_parts = []
        event_types = []

        async for chunk in session.stream_chat(
            messages=messages,
            provider_id="mock",
            stream_format=StreamFormat.SSE
        ):
            if chunk.startswith("data: "):
                try:
                    data = json.loads(chunk[6:])
                    event_types.append(data.get("type"))
                    if data.get("type") == "text-delta":
                        response_parts.append(data.get("content", ""))
                except json.JSONDecodeError:
                    continue

        # 验证结果
        assert len(response_parts) > 0
        assert "text-delta" in event_types
        combined_response = "".join(response_parts)
        assert len(combined_response) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """错误处理测试"""
        provider_manager = MultiProviderManager()
        streaming_manager = StreamingChatManager(provider_manager)

        # 测试无效提供商
        session = streaming_manager.create_session("test_session")
        messages = [{"role": "user", "content": "Hello"}]

        error_received = False
        async for chunk in session.stream_chat(
            messages=messages,
            provider_id="invalid_provider",
            stream_format=StreamFormat.SSE
        ):
            if "error" in chunk:
                error_received = True
                break

        assert error_received

    @pytest.mark.asyncio
    async def test_concurrent_streams(self):
        """并发流测试"""
        provider_manager = MultiProviderManager()
        streaming_manager = StreamingChatManager(provider_manager)

        # 注册模拟提供商
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="test-model"
        )
        adapter = MockProviderAdapter(config)
        provider_manager._adapters["mock"] = adapter

        # 创建多个并发流
        async def run_stream(session_id: str):
            session = streaming_manager.create_session(session_id)
            messages = [{"role": "user", "content": f"Hello from {session_id}"}]
            response_parts = []

            async for chunk in session.stream_chat(
                messages=messages,
                provider_id="mock",
                stream_format=StreamFormat.SSE
            ):
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:])
                        if data.get("type") == "text-delta":
                            response_parts.append(data.get("content", ""))
                    except json.JSONDecodeError:
                        continue

            return session_id, len(response_parts)

        # 运行并发流
        tasks = [run_stream(f"session_{i}") for i in range(3)]
        results = await asyncio.gather(*tasks)

        # 验证结果
        assert len(results) == 3
        for session_id, response_length in results:
            assert response_length > 0
            assert session_id.startswith("session_")


# 运行测试的便利函数
async def run_basic_tests():
    """运行基础测试"""
    logger.info("🧪 Running basic integration tests...")

    # 测试多厂商适配器
    logger.info("Testing multi-provider adapter...")
    provider_manager = MultiProviderManager()
    config = ProviderConfig(
        provider_type=ProviderType.OPENAI,
        model_name="test-model"
    )
    adapter = MockProviderAdapter(config)
    provider_manager._adapters["test"] = adapter
    provider_manager._default_provider = "test"

    providers = provider_manager.list_providers()
    assert len(providers) == 1
    logger.info("✅ Multi-provider adapter test passed")

    # 测试流式对话
    logger.info("Testing streaming chat...")
    streaming_manager = StreamingChatManager(provider_manager)
    session = streaming_manager.create_session("test_session")
    messages = [{"role": "user", "content": "Hello"}]

    response_parts = []
    async for chunk in session.stream_chat(
        messages=messages,
        provider_id="test",
        stream_format=StreamFormat.SSE
    ):
        if chunk.startswith("data: "):
            try:
                data = json.loads(chunk[6:])
                if data.get("type") == "text-delta":
                    response_parts.append(data.get("content", ""))
            except json.JSONDecodeError:
                continue

    assert len(response_parts) > 0
    logger.info("✅ Streaming chat test passed")

    # 测试WebSocket集成
    logger.info("Testing WebSocket integration...")
    websocket_manager = WebSocketManager(streaming_manager, provider_manager)
    mock_websocket = MockWebSocket()
    connection = await websocket_manager.add_connection(
        websocket=mock_websocket,
        user_id="test_user"
    )

    message = WebSocketMessage(
        message_type=WebSocketMessageType.CHAT_RESPONSE,
        data={"content": "Hello"}
    )
    success = await connection.send_message(message)
    assert success
    logger.info("✅ WebSocket integration test passed")

    logger.info("🎉 All basic tests passed!")


if __name__ == "__main__":
    # 运行基础测试
    asyncio.run(run_basic_tests())

    # 提示如何运行完整的pytest测试
    print("\nTo run the complete test suite, use:")
    print("pytest test_integration.py -v")
    print("\nFor async tests specifically:")
    print("pytest test_integration.py::TestMultiProviderAdapter::test_register_provider -v -s")