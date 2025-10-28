"""
完整的集成示例
演示如何使用agno_modular进行多厂商适配、流式对话和WebSocket集成
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入所有必要的模块
from multi_provider_adapter import (
    MultiProviderManager, ProviderConfig, ProviderType,
    register_openai_provider, register_anthropic_provider, register_agno_provider
)
from streaming_chat import StreamingChatManager, StreamFormat
from streaming_generator import (
    StreamingGeneratorFactory, GeneratorMode, streaming_context
)
from websocket_integration import (
    WebSocketManager, WebSocketMessage, WebSocketMessageType
)
from agent_manager import AgentCRUDManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiProviderStreamingIntegration:
    """多厂商流式对话集成示例"""

    def __init__(self):
        self.provider_manager = MultiProviderManager()
        self.streaming_manager = StreamingChatManager(self.provider_manager)
        self.websocket_manager = None  # 将在需要时创建
        self.agent_manager = None  # 将在需要时创建

    async def initialize_providers(self):
        """初始化多个AI厂商"""
        logger.info("Initializing AI providers...")

        # 注册OpenAI提供商
        openai_success = await register_openai_provider(
            provider_id="openai_gpt35",
            api_key="your-openai-api-key",  # 替换为实际的API密钥
            model_name="gpt-3.5-turbo",
            max_tokens=2000,
            temperature=0.7
        )
        logger.info(f"OpenAI provider registration: {'Success' if openai_success else 'Failed'}")

        # 注册Anthropic提供商
        anthropic_success = await register_anthropic_provider(
            provider_id="anthropic_claude",
            api_key="your-anthropic-api-key",  # 替换为实际的API密钥
            model_name="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.5
        )
        logger.info(f"Anthropic provider registration: {'Success' if anthropic_success else 'Failed'}")

        # 注册Agno原生提供商
        agno_success = await register_agno_provider(
            provider_id="agno_native",
            model_name="qwen3-vl-4b-instruct",
            max_tokens=2048,
            temperature=0.8,
            supports_streaming=True,
            supports_tools=True
        )
        logger.info(f"Agno provider registration: {'Success' if agno_success else 'Failed'}")

        # 设置默认提供商
        if openai_success:
            self.provider_manager.set_default_provider("openai_gpt35")

        # 检查所有提供商的健康状态
        health_status = await self.provider_manager.health_check_all()
        logger.info("Provider health status:")
        for provider_id, status in health_status.items():
            logger.info(f"  {provider_id}: {status['status']}")

    async def basic_streaming_example(self):
        """基础流式对话示例"""
        logger.info("\n=== Basic Streaming Example ===")

        messages = [
            {"role": "system", "content": "你是一个有用的AI助手。"},
            {"role": "user", "content": "请用中文介绍一下人工智能的发展历史。"}
        ]

        # 使用默认提供商进行流式对话
        logger.info("Starting streaming chat with default provider...")
        response_text = ""

        async for chunk in self.streaming_manager.create_session().stream_chat(
            messages=messages,
            stream_format=StreamFormat.SSE
        ):
            if chunk.startswith("data: "):
                try:
                    data = json.loads(chunk[6:])  # 移除 "data: " 前缀
                    if data.get("type") == "text-delta":
                        content = data.get("content", "")
                        response_text += content
                        print(content, end="", flush=True)
                    elif data.get("type") == "finish":
                        print("\n\nStreaming completed!")
                        break
                except json.JSONDecodeError:
                    continue

        logger.info(f"Full response length: {len(response_text)} characters")

    async def multi_provider_comparison(self):
        """多厂商对比示例"""
        logger.info("\n=== Multi-Provider Comparison Example ===")

        messages = [
            {"role": "user", "content": "解释什么是机器学习，并给出一个简单的例子。"}
        ]

        providers = ["openai_gpt35", "anthropic_claude", "agno_native"]
        results = {}

        for provider_id in providers:
            try:
                logger.info(f"Testing provider: {provider_id}")
                response_text = ""

                async for chunk in self.streaming_manager.create_session().stream_chat(
                    messages=messages,
                    provider_id=provider_id,
                    stream_format=StreamFormat.SSE
                ):
                    if chunk.startswith("data: "):
                        try:
                            data = json.loads(chunk[6:])
                            if data.get("type") == "text-delta":
                                response_text += data.get("content", "")
                        except json.JSONDecodeError:
                            continue

                results[provider_id] = response_text
                logger.info(f"Provider {provider_id} response length: {len(response_text)}")

            except Exception as e:
                logger.error(f"Provider {provider_id} error: {e}")
                results[provider_id] = f"Error: {str(e)}"

        # 输出对比结果
        logger.info("\n=== Provider Comparison Results ===")
        for provider_id, response in results.items():
            logger.info(f"\n{provider_id}:")
            logger.info(f"  Length: {len(response)} characters")
            logger.info(f"  Preview: {response[:200]}...")

    async def advanced_generator_modes(self):
        """高级生成器模式示例"""
        logger.info("\n=== Advanced Generator Modes Example ===")

        messages = [
            {"role": "user", "content": "写一个简短的故事，包含以下元素：冒险、魔法、友谊"}
        ]

        # 标准模式
        logger.info("1. Standard mode:")
        async with streaming_context(GeneratorMode.STANDARD) as generator:
            async for event in generator.generate(messages):
                if event.event_type.value == "text-delta":
                    print(event.data.get("content", ""), end="", flush=True)
        print("\n")

        # 缓冲模式
        logger.info("2. Buffered mode:")
        from streaming_generator import GeneratorConfig
        config = GeneratorConfig(
            mode=GeneratorMode.BUFFERED,
            buffer_size=50,  # 缓冲50个字符
            flush_interval=0.2  # 每0.2秒刷新一次
        )

        async with streaming_context(GeneratorMode.BUFFERED, config) as generator:
            async for event in generator.generate(messages):
                if event.event_type.value == "text-delta":
                    print(event.data.get("content", ""), end="", flush=True)
        print("\n")

        # 分块模式
        logger.info("3. Chunked mode:")
        chunk_config = GeneratorConfig(
            mode=GeneratorMode.CHUNKED,
            chunk_size=100  # 每100个字符为一块
        )

        async with streaming_context(GeneratorMode.CHUNKED, chunk_config) as generator:
            chunk_count = 0
            async for event in generator.generate(messages):
                if event.event_type.value == "text-delta":
                    chunk_count += 1
                    content = event.data.get("content", "")
                    print(f"Chunk {chunk_count}: {content}")
        print("\n")

    async def websocket_simulation(self):
        """WebSocket模拟示例"""
        logger.info("\n=== WebSocket Simulation Example ===")

        # 创建WebSocket管理器
        self.websocket_manager = WebSocketManager(
            self.streaming_manager,
            self.provider_manager
        )

        # 模拟WebSocket连接
        class MockWebSocket:
            def __init__(self):
                self.messages = []
                self.closed = False

            async def accept(self):
                pass

            async def send_text(self, message: str):
                self.messages.append(message)
                # 模拟处理消息
                try:
                    data = json.loads(message)
                    if data.get("message_type") == "stream_event":
                        event_data = data.get("data", {})
                        if event_data.get("event_type") == "text-delta":
                            content = event_data.get("event_data", {}).get("content", "")
                            print(content, end="", flush=True)
                except:
                    pass

            async def receive_text(self):
                # 模拟接收聊天请求
                return json.dumps({
                    "message_type": "chat_request",
                    "data": {
                        "messages": [
                            {"role": "user", "content": "用WebSocket发送消息的优势是什么？"}
                        ],
                        "generator_mode": "standard"
                    }
                })

            async def close(self):
                self.closed = True

        # 创建模拟连接
        mock_websocket = MockWebSocket()
        connection = await self.websocket_manager.add_connection(
            websocket=mock_websocket,
            user_id="test_user",
            session_id="test_session"
        )

        logger.info(f"Created mock connection: {connection.connection_id}")

        # 处理消息
        print("WebSocket response: ", end="", flush=True)
        await self.websocket_manager.handle_connection(connection.connection_id)
        print("\n")

        # 获取统计信息
        stats = self.websocket_manager.get_statistics()
        logger.info(f"WebSocket statistics: {stats}")

    async def agent_integration_example(self):
        """Agent集成示例"""
        logger.info("\n=== Agent Integration Example ===")

        # 注意：这里需要实际的数据库连接和Agent管理器
        # 以下代码为模拟示例
        try:
            # 模拟创建Agent
            agent_id = 1  # 假设这是已存在的Agent ID

            messages = [
                {"role": "user", "content": "作为一个Python助手，请解释什么是装饰器"}
            ]

            logger.info(f"Running agent {agent_id} with streaming...")

            # 使用Agent进行流式对话
            response_text = ""
            async for chunk in self.streaming_manager.stream_chat_with_agent(
                agent_id=agent_id,
                message=messages[0]["content"],
                stream_format=StreamFormat.SSE
            ):
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:])
                        if data.get("type") == "text-delta":
                            content = data.get("content", "")
                            response_text += content
                            print(content, end="", flush=True)
                        elif data.get("type") == "finish":
                            print("\n\nAgent streaming completed!")
                            break
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Agent response length: {len(response_text)} characters")

        except Exception as e:
            logger.error(f"Agent integration error: {e}")
            logger.info("Note: Agent integration requires proper database setup")

    async def performance_test(self):
        """性能测试"""
        logger.info("\n=== Performance Test Example ===")

        messages = [
            {"role": "user", "content": "简单回答：1+1等于多少？"}
        ]

        # 测试不同提供商的响应时间
        providers = ["openai_gpt35", "anthropic_claude", "agno_native"]
        performance_results = {}

        for provider_id in providers:
            try:
                start_time = datetime.now()
                response_text = ""
                events_processed = 0

                async for chunk in self.streaming_manager.create_session().stream_chat(
                    messages=messages,
                    provider_id=provider_id,
                    stream_format=StreamFormat.SSE
                ):
                    if chunk.startswith("data: "):
                        try:
                            data = json.loads(chunk[6:])
                            events_processed += 1
                            if data.get("type") == "text-delta":
                                response_text += data.get("content", "")
                        except json.JSONDecodeError:
                            continue

                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()

                performance_results[provider_id] = {
                    "response_time": response_time,
                    "events_processed": events_processed,
                    "response_length": len(response_text),
                    "events_per_second": events_processed / response_time if response_time > 0 else 0
                }

            except Exception as e:
                performance_results[provider_id] = {"error": str(e)}

        # 输出性能结果
        logger.info("Performance Test Results:")
        for provider_id, result in performance_results.items():
            if "error" in result:
                logger.info(f"  {provider_id}: Error - {result['error']}")
            else:
                logger.info(f"  {provider_id}:")
                logger.info(f"    Response time: {result['response_time']:.2f}s")
                logger.info(f"    Events processed: {result['events_processed']}")
                logger.info(f"    Response length: {result['response_length']}")
                logger.info(f"    Events/sec: {result['events_per_second']:.2f}")

    async def error_handling_example(self):
        """错误处理示例"""
        logger.info("\n=== Error Handling Example ===")

        messages = [
            {"role": "user", "content": "测试错误处理"}
        ]

        # 测试无效提供商
        logger.info("1. Testing invalid provider:")
        try:
            async for chunk in self.streaming_manager.create_session().stream_chat(
                messages=messages,
                provider_id="invalid_provider",
                stream_format=StreamFormat.SSE
            ):
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:])
                        if data.get("type") == "error":
                            logger.info(f"Received error: {data.get('data', {}).get('error')}")
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.info(f"Caught exception: {e}")

        # 测试空消息
        logger.info("2. Testing empty messages:")
        try:
            async for chunk in self.streaming_manager.create_session().stream_chat(
                messages=[],
                stream_format=StreamFormat.SSE
            ):
                pass
        except Exception as e:
            logger.info(f"Caught exception for empty messages: {e}")

    async def run_all_examples(self):
        """运行所有示例"""
        logger.info("🚀 Starting Multi-Provider Streaming Integration Examples")

        try:
            # 初始化提供商
            await self.initialize_providers()

            # 运行各种示例
            await self.basic_streaming_example()
            await self.multi_provider_comparison()
            await self.advanced_generator_modes()
            await self.websocket_simulation()
            await self.agent_integration_example()
            await self.performance_test()
            await self.error_handling_example()

            logger.info("✅ All examples completed successfully!")

        except Exception as e:
            logger.error(f"❌ Example execution failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    integration = MultiProviderStreamingIntegration()
    await integration.run_all_examples()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())