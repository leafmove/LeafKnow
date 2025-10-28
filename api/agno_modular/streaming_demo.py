"""
流式对话和多厂商适配演示
展示如何使用agno_modular模块进行流式对话和AI厂商适配
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模拟基础类和枚举
class AgentType(str, Enum):
    """Agent类型枚举"""
    QA = "qa"
    TASK = "task"
    RESEARCH = "research"
    CREATIVE = "creative"
    CUSTOM = "custom"

class ProviderType(str, Enum):
    """提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AGNO_NATIVE = "agno_native"

class StreamFormat(str, Enum):
    """流式输出格式"""
    SSE = "sse"
    WEBSOCKET = "websocket"
    GENERATOR = "generator"

class GeneratorMode(str, Enum):
    """生成器模式"""
    STANDARD = "standard"
    BUFFERED = "buffered"
    CHUNKED = "chunked"
    INTERLEAVED = "interleaved"

# 模拟配置类
class MockProviderConfig:
    """模拟提供商配置"""
    def __init__(self, **kwargs):
        self.provider_type = kwargs.get('provider_type', ProviderType.OPENAI)
        self.model_name = kwargs.get('model_name', 'gpt-3.5-turbo')
        self.api_key = kwargs.get('api_key')
        self.max_tokens = kwargs.get('max_tokens', 2000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.supports_streaming = kwargs.get('supports_streaming', True)

# 模拟流式事件
class StreamEvent:
    """流式事件"""
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now()
        self.event_id = str(uuid.uuid4())

    def to_sse_format(self) -> str:
        """转换为SSE格式"""
        data = {
            "type": self.event_type,
            "id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            **self.data
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# 模拟提供商适配器
class MockProviderAdapter:
    """模拟提供商适配器"""
    def __init__(self, config: MockProviderConfig):
        self.config = config
        self.provider_type = config.provider_type
        self.model_name = config.model_name

    async def stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """模拟流式聊天"""
        test_responses = {
            ProviderType.OPENAI: "这是来自OpenAI的模拟流式响应。支持实时输出和流式处理，提供高质量的对话体验。",
            ProviderType.ANTHROPIC: "这是来自Anthropic的模拟流式响应。提供深入的分析和推理能力，适合复杂任务。",
            ProviderType.AGNO_NATIVE: "这是来自Agno原生模型的模拟流式响应。本地部署，响应快速，数据安全。"
        }

        response_text = test_responses.get(self.provider_type, "这是默认的模拟响应。")

        # 模拟流式输出
        for char in response_text:
            yield {
                "type": "text-delta",
                "content": char
            }
            await asyncio.sleep(0.01)  # 模拟网络延迟

        yield {"type": "finish", "reason": "stop"}

    async def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """模拟非流式聊天完成"""
        responses = {
            ProviderType.OPENAI: "这是OpenAI的完整响应。",
            ProviderType.ANTHROPIC: "这是Anthropic的完整响应。",
            ProviderType.AGNO_NATIVE: "这是Agno原生模型的完整响应。"
        }

        return {
            "content": responses.get(self.provider_type, "默认响应"),
            "role": "assistant",
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

    def supports_feature(self, feature: str) -> bool:
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "provider": self.provider_type.value,
            "model": self.model_name,
            "response_time": 0.1,
            "timestamp": datetime.now().isoformat()
        }

# 模拟管理器类
class MockProviderManager:
    """模拟提供商管理器"""
    def __init__(self):
        self.adapters: Dict[str, MockProviderAdapter] = {}
        self.default_provider = None

    async def register_provider(self, provider_id: str, config: MockProviderConfig) -> bool:
        """注册提供商"""
        try:
            adapter = MockProviderAdapter(config)
            self.adapters[provider_id] = adapter

            if self.default_provider is None:
                self.default_provider = provider_id

            logger.info(f"Successfully registered provider: {provider_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register provider {provider_id}: {e}")
            return False

    def get_adapter(self, provider_id: Optional[str] = None) -> Optional[MockProviderAdapter]:
        """获取适配器"""
        if provider_id is None:
            provider_id = self.default_provider

        if provider_id is None or provider_id not in self.adapters:
            return None

        return self.adapters[provider_id]

    def list_providers(self) -> List[Dict[str, Any]]:
        """列出提供商"""
        providers = []
        for provider_id, adapter in self.adapters.items():
            providers.append({
                "provider_id": provider_id,
                "provider_type": adapter.provider_type.value,
                "model_name": adapter.model_name,
                "is_default": provider_id == self.default_provider
            })
        return providers

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """检查所有提供商健康状态"""
        results = {}
        for provider_id, adapter in self.adapters.items():
            try:
                results[provider_id] = await adapter.health_check()
            except Exception as e:
                results[provider_id] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        return results

# 演示函数
async def demo_provider_registration():
    """演示提供商注册"""
    print("=== 提供商注册演示 ===\n")

    # 创建管理器
    provider_manager = MockProviderManager()

    # 注册不同的提供商
    providers_to_register = [
        ("openai_gpt4", MockProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="gpt-4",
            api_key="sk-test-openai-key",
            max_tokens=4000,
            temperature=0.7,
            supports_streaming=True
        )),
        ("anthropic_claude", MockProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            model_name="claude-3-sonnet-20240229",
            api_key="sk-test-anthropic-key",
            max_tokens=4000,
            temperature=0.5,
            supports_streaming=True
        )),
        ("agno_native", MockProviderConfig(
            provider_type=ProviderType.AGNO_NATIVE,
            model_name="qwen3-vl-4b-instruct",
            max_tokens=2048,
            temperature=0.8,
            supports_streaming=True
        ))
    ]

    print("1. 注册AI提供商:")
    for provider_id, config in providers_to_register:
        success = await provider_manager.register_provider(provider_id, config)
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {provider_id}: {config.provider_type.value} - {config.model_name}")

    # 列出所有提供商
    print(f"\n2. 当前提供商列表:")
    for provider in provider_manager.list_providers():
        default_mark = " (默认)" if provider["is_default"] else ""
        print(f"  - {provider['provider_id']}: {provider['provider_type']} - {provider['model_name']}{default_mark}")

    # 健康检查
    print(f"\n3. 提供商健康检查:")
    health_status = await provider_manager.health_check_all()
    for provider_id, status in health_status.items():
        status_icon = "[OK]" if status["status"] == "healthy" else "[FAIL]"
        response_time = status.get('response_time', 0)
        print(f"  {status_icon} {provider_id}: {status['status']} (响应时间: {response_time:.2f}s)")

    return provider_manager

async def demo_basic_streaming(provider_manager: MockProviderManager):
    """演示基础流式对话"""
    print("\n=== 基础流式对话演示 ===\n")

    messages = [{"role": "user", "content": "请简单介绍一下流式对话的优势。"}]
    providers = list(provider_manager.adapters.keys())

    print("向各个提供商发送相同的请求:")
    for provider_id in providers:
        adapter = provider_manager.get_adapter(provider_id)
        if adapter:
            print(f"\n[AI] {provider_id} ({adapter.provider_type.value}) 响应:")
            print("  ", end="", flush=True)

            try:
                response_text = ""
                async for event in adapter.stream_chat(messages):
                    if event.get("type") == "text-delta":
                        content = event.get("content", "")
                        response_text += content
                        print(content, end="", flush=True)

                print(f"\n  完整响应长度: {len(response_text)} 字符")

            except Exception as e:
                print(f"\n  [ERROR] 错误: {e}")

async def demo_sse_format_output(provider_manager: MockProviderManager):
    """演示SSE格式输出"""
    print("\n=== SSE格式输出演示 ===\n")

    messages = [{"role": "user", "content": "解释什么是异步编程。"}]
    adapter = provider_manager.get_adapter()

    if not adapter:
        print("[ERROR] 没有可用的提供商")
        return

    print("SSE格式输出 (Server-Sent Events):")
    print("-" * 50)

    try:
        async for event in adapter.stream_chat(messages):
            # 创建流式事件
            stream_event = StreamEvent(
                event_type=event.get("type", "unknown"),
                data=event
            )

            # 输出SSE格式
            sse_output = stream_event.to_sse_format()
            print(sse_output.strip())

        print("data: [DONE]")  # 结束标记
        print("-" * 50)
        print("[OK] SSE格式输出完成")

    except Exception as e:
        print(f"[ERROR] SSE输出错误: {e}")

async def demo_concurrent_streaming(provider_manager: MockProviderManager):
    """演示并发流式对话"""
    print("\n=== 并发流式对话演示 ===\n")

    async def run_provider_stream(provider_id: str, messages: List[Dict[str, Any]], result_dict: dict):
        """运行单个提供商的流式对话"""
        adapter = provider_manager.get_adapter(provider_id)
        if not adapter:
            result_dict[provider_id] = {"error": "Provider not found"}
            return

        try:
            start_time = datetime.now()
            response_parts = []
            async for event in adapter.stream_chat(messages):
                if event.get("type") == "text-delta":
                    response_parts.append(event.get("content", ""))

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            result_dict[provider_id] = {
                "success": True,
                "response": "".join(response_parts),
                "length": len("".join(response_parts)),
                "response_time": response_time
            }
        except Exception as e:
            result_dict[provider_id] = {"error": str(e)}

    # 准备测试数据
    test_message = [{"role": "user", "content": "用一句话说明AI技术对未来的影响。"}]
    providers = list(provider_manager.adapters.keys())
    results = {}

    print(f"同时向 {len(providers)} 个提供商发送请求...")

    # 创建并发任务
    start_time = datetime.now()
    tasks = []
    for provider_id in providers:
        task = asyncio.create_task(run_provider_stream(provider_id, test_message, results))
        tasks.append(task)

    # 等待所有任务完成
    await asyncio.gather(*tasks)
    end_time = datetime.now()

    # 显示结果
    total_time = (end_time - start_time).total_seconds()
    print(f"\n并发响应结果 (总耗时: {total_time:.2f}s):")

    for provider_id, result in results.items():
        if "error" in result:
            print(f"  [ERROR] {provider_id}: {result['error']}")
        else:
            print(f"  [OK] {provider_id}:")
            print(f"    - 响应长度: {result['length']} 字符")
            print(f"    - 响应时间: {result['response_time']:.2f}s")
            print(f"    - 内容预览: {result['response'][:60]}...")

async def demo_error_handling(provider_manager: MockProviderManager):
    """演示错误处理"""
    print("\n=== 错误处理演示 ===\n")

    # 测试无效提供商
    print("1. 测试无效提供商:")
    try:
        invalid_adapter = provider_manager.get_adapter("invalid_provider")
        if invalid_adapter is None:
            print("  [OK] 正确处理了无效提供商")
        else:
            print("  [FAIL] 未能正确处理无效提供商")
    except Exception as e:
        print(f"  [OK] 捕获到预期错误: {e}")

    # 测试空消息
    print("\n2. 测试空消息:")
    adapter = provider_manager.get_adapter()
    if adapter:
        try:
            async for event in adapter.stream_chat([]):
                pass
            print("  [WARN] 空消息处理完成（可能需要添加验证）")
        except Exception as e:
            print(f"  [OK] 正确处理空消息错误: {e}")

    # 测试健康检查失败
    print("\n3. 模拟健康检查失败:")
    # 这里可以模拟一个失败的适配器
    class FailingAdapter:
        async def health_check(self):
            raise Exception("模拟连接失败")

    failing_provider = MockProviderManager()
    failing_provider.adapters["failing"] = FailingAdapter()

    try:
        health_status = await failing_provider.health_check_all()
        if "failing" in health_status and health_status["failing"]["status"] == "error":
            print("  [OK] 正确处理健康检查失败")
        else:
            print("  [FAIL] 未能正确处理健康检查失败")
    except Exception as e:
        print(f"  [OK] 捕获到健康检查错误: {e}")

async def demo_performance_comparison(provider_manager: MockProviderManager):
    """演示性能对比"""
    print("\n=== 性能对比演示 ===\n")

    test_messages = [
        {"role": "user", "content": "解释什么是机器学习？"},
        {"role": "user", "content": "Python有什么优势？"},
        {"role": "user", "content": "如何提高编程效率？"}
    ]

    providers = list(provider_manager.adapters.keys())
    performance_stats = {}

    print(f"性能测试 - 向每个提供商发送 {len(test_messages)} 个请求:")
    print("-" * 60)

    for provider_id in providers:
        adapter = provider_manager.get_adapter(provider_id)
        if not adapter:
            continue

        print(f"\n测试 {provider_id} ({adapter.provider_type.value}):")

        stats = {
            "total_time": 0,
            "total_chars": 0,
            "requests": 0,
            "errors": 0
        }

        for i, message in enumerate(test_messages):
            try:
                start_time = datetime.now()
                response_text = ""

                async for event in adapter.stream_chat([message]):
                    if event.get("type") == "text-delta":
                        response_text += event.get("content", "")

                end_time = datetime.now()
                request_time = (end_time - start_time).total_seconds()

                stats["total_time"] += request_time
                stats["total_chars"] += len(response_text)
                stats["requests"] += 1

                print(f"  请求 {i+1}: {request_time:.2f}s, {len(response_text)} 字符")

            except Exception as e:
                stats["errors"] += 1
                print(f"  请求 {i+1}: [ERROR] 错误 - {e}")

        if stats["requests"] > 0:
            avg_time = stats["total_time"] / stats["requests"]
            avg_chars = stats["total_chars"] / stats["requests"]

            print(f"  {provider_id} 统计:")
            print(f"    - 平均响应时间: {avg_time:.2f}s")
            print(f"    - 平均响应长度: {avg_chars:.0f} 字符")
            print(f"    - 成功率: {((stats['requests'] - stats['errors']) / stats['requests'] * 100):.1f}%")
            print(f"    - 总吞吐量: {stats['total_chars'] / stats['total_time']:.1f} 字符/秒")

            performance_stats[provider_id] = stats

    # 性能排名
    if performance_stats:
        print(f"\n性能排名 (按平均响应时间):")
        sorted_providers = sorted(performance_stats.items(),
                               key=lambda x: x[1]["total_time"] / x[1]["requests"])

        for i, (provider_id, stats) in enumerate(sorted_providers, 1):
            avg_time = stats["total_time"] / stats["requests"]
            print(f"  {i}. {provider_id}: {avg_time:.2f}s")

async def main():
    """主演示函数"""
    print("Agno Modular 流式对话和多厂商适配演示")
    print("=" * 70)

    try:
        # 1. 提供商注册和管理
        provider_manager = await demo_provider_registration()

        # 2. 基础流式对话
        await demo_basic_streaming(provider_manager)

        # 3. SSE格式输出
        await demo_sse_format_output(provider_manager)

        # 4. 并发流式对话
        await demo_concurrent_streaming(provider_manager)

        # 5. 错误处理
        await demo_error_handling(provider_manager)

        # 6. 性能对比
        await demo_performance_comparison(provider_manager)

        print("\n" + "=" * 70)
        print("所有演示完成！")
        print("\n这是一个模拟演示，展示了agno_modular模块的核心功能:")
        print("   - 多厂商AI模型适配")
        print("   - 流式对话输出")
        print("   - 并发请求处理")
        print("   - 错误处理机制")
        print("   - 性能监控对比")
        print("   - SSE格式支持")
        print("\n在实际使用中，这些功能会与真实的AI服务和数据库集成。")

    except Exception as e:
        print(f"\n演示执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())