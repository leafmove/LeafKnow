"""
流式对话生成器
提供多种生成器模式，支持异步流式处理和多种输出格式
"""

import asyncio
import json
import uuid
from typing import (
    Any, Dict, List, Optional, Union, AsyncGenerator, Callable,
    Iterator, Generator, Awaitable
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from contextlib import asynccontextmanager

from streaming_chat import (
    StreamEvent, StreamEventType, StreamFormat,
    StreamingChatSession, StreamingChatManager
)
from multi_provider_adapter import MultiProviderManager

logger = logging.getLogger(__name__)


class GeneratorMode(str, Enum):
    """生成器模式"""
    STANDARD = "standard"           # 标准异步生成器
    BUFFERED = "buffered"           # 缓冲模式
    CHUNKED = "chunked"             # 分块模式
    INTERLEAVED = "interleaved"     # 交错模式
    PRIORITY = "priority"           # 优先级模式


@dataclass
class GeneratorConfig:
    """生成器配置"""
    mode: GeneratorMode = GeneratorMode.STANDARD
    buffer_size: int = 1024
    flush_interval: float = 0.1
    chunk_size: int = 100
    max_queue_size: int = 1000
    timeout: float = 30.0
    retry_attempts: int = 3
    enable_metadata: bool = True
    enable_usage_tracking: bool = True


class StreamingGenerator:
    """流式对话生成器基类"""

    def __init__(
        self,
        config: GeneratorConfig,
        provider_manager: MultiProviderManager
    ):
        self.config = config
        self.provider_manager = provider_manager
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.events_processed = 0
        self.total_tokens = 0
        self.error_count = 0

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """生成流式事件的主方法"""
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        """获取生成器统计信息"""
        return {
            "session_id": self.session_id,
            "mode": self.config.mode.value,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "events_processed": self.events_processed,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count
        }


class StandardStreamingGenerator(StreamingGenerator):
    """标准流式生成器"""

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """标准流式生成"""
        try:
            adapter = self.provider_manager.get_adapter(provider_id or "default")

            async for provider_event in adapter.stream_chat(messages, tools, **kwargs):
                event = self._convert_to_stream_event(provider_event)
                self.events_processed += 1
                yield event

        except Exception as e:
            logger.error(f"Standard generator error: {e}")
            self.error_count += 1
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e)}
            )

    def _convert_to_stream_event(self, provider_event: Dict[str, Any]) -> StreamEvent:
        """转换厂商事件为流式事件"""
        event_type = provider_event.get("type", "text-delta")

        if event_type == "text-delta":
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": provider_event.get("content", "")}
            )
        elif event_type == "finish":
            return StreamEvent(
                event_type=StreamEventType.FINISH,
                data={"reason": provider_event.get("reason", "stop")}
            )
        elif event_type == "error":
            return StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": provider_event.get("error", "Unknown error")}
            )
        else:
            return StreamEvent(
                event_type=StreamEventType.METADATA,
                data=provider_event
            )


class BufferedStreamingGenerator(StreamingGenerator):
    """缓冲流式生成器"""

    def __init__(self, config: GeneratorConfig, provider_manager: MultiProviderManager):
        super().__init__(config, provider_manager)
        self.buffer: List[StreamEvent] = []
        self.last_flush = datetime.now()

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """缓冲流式生成"""
        try:
            adapter = self.provider_manager.get_adapter(provider_id or "default")

            async for provider_event in adapter.stream_chat(messages, tools, **kwargs):
                event = self._convert_to_stream_event(provider_event)
                self.buffer.append(event)
                self.events_processed += 1

                # 检查是否需要刷新缓冲区
                if self._should_flush():
                    await self._flush_buffer()

            # 刷新剩余缓冲区
            await self._flush_buffer()

        except Exception as e:
            logger.error(f"Buffered generator error: {e}")
            self.error_count += 1
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e)}
            )

    def _should_flush(self) -> bool:
        """检查是否应该刷新缓冲区"""
        current_time = datetime.now()
        return (
            len(self.buffer) >= self.config.buffer_size or
            (current_time - self.last_flush).total_seconds() >= self.config.flush_interval
        )

    async def _flush_buffer(self):
        """刷新缓冲区"""
        if self.buffer:
            for event in self.buffer:
                yield event
            self.buffer.clear()
            self.last_flush = datetime.now()

    def _convert_to_stream_event(self, provider_event: Dict[str, Any]) -> StreamEvent:
        """转换厂商事件为流式事件"""
        # 与标准生成器相同的转换逻辑
        event_type = provider_event.get("type", "text-delta")

        if event_type == "text-delta":
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": provider_event.get("content", "")}
            )
        elif event_type == "finish":
            return StreamEvent(
                event_type=StreamEventType.FINISH,
                data={"reason": provider_event.get("reason", "stop")}
            )
        else:
            return StreamEvent(
                event_type=StreamEventType.METADATA,
                data=provider_event
            )


class ChunkedStreamingGenerator(StreamingGenerator):
    """分块流式生成器"""

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """分块流式生成"""
        try:
            adapter = self.provider_manager.get_adapter(provider_id or "default")
            current_chunk: List[StreamEvent] = []

            async for provider_event in adapter.stream_chat(messages, tools, **kwargs):
                event = self._convert_to_stream_event(provider_event)
                current_chunk.append(event)
                self.events_processed += 1

                # 检查是否达到块大小
                if len(current_chunk) >= self.config.chunk_size:
                    await self._emit_chunk(current_chunk)
                    current_chunk = []

            # 发送剩余的块
            if current_chunk:
                await self._emit_chunk(current_chunk)

        except Exception as e:
            logger.error(f"Chunked generator error: {e}")
            self.error_count += 1
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e)}
            )

    async def _emit_chunk(self, chunk: List[StreamEvent]):
        """发送事件块"""
        # 将多个事件合并为一个事件
        combined_content = ""
        for event in chunk:
            if event.event_type == StreamEventType.TEXT_DELTA:
                combined_content += event.data.get("content", "")

        if combined_content:
            yield StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": combined_content}
            )

    def _convert_to_stream_event(self, provider_event: Dict[str, Any]) -> StreamEvent:
        """转换厂商事件为流式事件"""
        event_type = provider_event.get("type", "text-delta")

        if event_type == "text-delta":
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": provider_event.get("content", "")}
            )
        else:
            return StreamEvent(
                event_type=StreamEventType.METADATA,
                data=provider_event
            )


class InterleavedStreamingGenerator(StreamingGenerator):
    """交错流式生成器 - 支持多个流的交错输出"""

    def __init__(self, config: GeneratorConfig, provider_manager: MultiProviderManager):
        super().__init__(config, provider_manager)
        self.streams: Dict[str, asyncio.Queue] = {}
        self.active_stream_ids: List[str] = []

    async def add_stream(
        self,
        stream_id: str,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ):
        """添加流"""
        if stream_id not in self.streams:
            self.streams[stream_id] = asyncio.Queue(maxsize=self.config.max_queue_size)
            self.active_stream_ids.append(stream_id)

            # 启动流处理任务
            asyncio.create_task(self._process_stream(
                stream_id, messages, provider_id, tools, **kwargs
            ))

    async def _process_stream(
        self,
        stream_id: str,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ):
        """处理单个流"""
        try:
            adapter = self.provider_manager.get_adapter(provider_id or "default")
            queue = self.streams[stream_id]

            async for provider_event in adapter.stream_chat(messages, tools, **kwargs):
                event = self._convert_to_stream_event(provider_event)
                event.data["stream_id"] = stream_id

                try:
                    await queue.put(event)
                    self.events_processed += 1
                except asyncio.QueueFull:
                    logger.warning(f"Stream {stream_id} queue is full, dropping event")

            # 发送流结束事件
            await queue.put(StreamEvent(
                event_type=StreamEventType.METADATA,
                data={"stream_id": stream_id, "status": "completed"}
            ))

        except Exception as e:
            logger.error(f"Stream {stream_id} error: {e}")
            self.error_count += 1
            try:
                await queue.put(StreamEvent(
                    event_type=StreamEventType.ERROR,
                    data={"stream_id": stream_id, "error": str(e)}
                ))
            except asyncio.QueueFull:
                pass

    async def generate(self) -> AsyncGenerator[StreamEvent, None]:
        """交错生成事件"""
        while self.active_stream_ids:
            # 轮询所有活跃的流
            for stream_id in list(self.active_stream_ids):
                queue = self.streams.get(stream_id)
                if not queue:
                    continue

                try:
                    # 非阻塞获取事件
                    event = queue.get_nowait()

                    # 检查是否为流结束事件
                    if (event.event_type == StreamEventType.METADATA and
                        event.data.get("status") == "completed"):
                        self.active_stream_ids.remove(stream_id)
                        continue

                    yield event

                except asyncio.QueueEmpty:
                    continue

            # 短暂休眠避免CPU占用过高
            await asyncio.sleep(0.01)

    def _convert_to_stream_event(self, provider_event: Dict[str, Any]) -> StreamEvent:
        """转换厂商事件为流式事件"""
        event_type = provider_event.get("type", "text-delta")

        if event_type == "text-delta":
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": provider_event.get("content", "")}
            )
        else:
            return StreamEvent(
                event_type=StreamEventType.METADATA,
                data=provider_event
            )


class PriorityStreamingGenerator(StreamingGenerator):
    """优先级流式生成器"""

    @dataclass
    class PriorityEvent:
        """带优先级的事件"""
        priority: int
        event: StreamEvent
        timestamp: datetime = field(default_factory=datetime.now)

    def __init__(self, config: GeneratorConfig, provider_manager: MultiProviderManager):
        super().__init__(config, provider_manager)
        self.priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    async def add_event(
        self,
        event: StreamEvent,
        priority: int = 0
    ):
        """添加带优先级的事件"""
        priority_event = self.PriorityEvent(priority=priority, event=event)
        await self.priority_queue.put(priority_event)

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """按优先级生成事件"""
        try:
            adapter = self.provider_manager.get_adapter(provider_id or "default")

            # 启动事件收集任务
            collection_task = asyncio.create_task(
                self._collect_events(adapter, messages, tools, **kwargs)
            )

            # 生成优先级排序的事件
            while not collection_task.done() or not self.priority_queue.empty():
                try:
                    priority_event = await asyncio.wait_for(
                        self.priority_queue.get(),
                        timeout=self.config.timeout
                    )
                    self.events_processed += 1
                    yield priority_event.event
                except asyncio.TimeoutError:
                    logger.warning("Priority queue timeout, stopping generation")
                    break

            # 确保收集任务完成
            await collection_task

        except Exception as e:
            logger.error(f"Priority generator error: {e}")
            self.error_count += 1
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e)}
            )

    async def _collect_events(
        self,
        adapter,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ):
        """收集事件并分配优先级"""
        async for provider_event in adapter.stream_chat(messages, tools, **kwargs):
            event = self._convert_to_stream_event(provider_event)
            priority = self._calculate_priority(event)

            priority_event = self.PriorityEvent(priority=priority, event=event)
            await self.priority_queue.put(priority_event)

    def _calculate_priority(self, event: StreamEvent) -> int:
        """计算事件优先级"""
        # 错误事件优先级最高
        if event.event_type == StreamEventType.ERROR:
            return 0
        # 完成事件优先级较高
        elif event.event_type == StreamEventType.FINISH:
            return 1
        # 文本事件正常优先级
        elif event.event_type == StreamEventType.TEXT_DELTA:
            return 2
        # 其他事件优先级较低
        else:
            return 3

    def _convert_to_stream_event(self, provider_event: Dict[str, Any]) -> StreamEvent:
        """转换厂商事件为流式事件"""
        event_type = provider_event.get("type", "text-delta")

        if event_type == "text-delta":
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": provider_event.get("content", "")}
            )
        else:
            return StreamEvent(
                event_type=StreamEventType.METADATA,
                data=provider_event
            )


class StreamingGeneratorFactory:
    """流式生成器工厂"""

    @staticmethod
    def create_generator(
        mode: GeneratorMode,
        config: Optional[GeneratorConfig] = None,
        provider_manager: Optional[MultiProviderManager] = None
    ) -> StreamingGenerator:
        """创建生成器实例"""
        if config is None:
            config = GeneratorConfig()

        if provider_manager is None:
            from multi_provider_adapter import get_multi_provider_manager
            provider_manager = get_multi_provider_manager()

        generator_map = {
            GeneratorMode.STANDARD: StandardStreamingGenerator,
            GeneratorMode.BUFFERED: BufferedStreamingGenerator,
            GeneratorMode.CHUNKED: ChunkedStreamingGenerator,
            GeneratorMode.INTERLEAVED: InterleavedStreamingGenerator,
            GeneratorMode.PRIORITY: PriorityStreamingGenerator,
        }

        generator_class = generator_map.get(mode)
        if not generator_class:
            raise ValueError(f"Unsupported generator mode: {mode}")

        return generator_class(config, provider_manager)


@asynccontextmanager
async def streaming_context(
    mode: GeneratorMode = GeneratorMode.STANDARD,
    config: Optional[GeneratorConfig] = None,
    provider_manager: Optional[MultiProviderManager] = None
):
    """流式生成器上下文管理器"""
    generator = StreamingGeneratorFactory.create_generator(mode, config, provider_manager)

    try:
        yield generator
    finally:
        # 清理资源
        if hasattr(generator, 'cleanup'):
            await generator.cleanup()

        logger.info(f"Streaming generator finished: {generator.get_stats()}")


# 便利函数
async def create_standard_stream(
    messages: List[Dict[str, Any]],
    provider_id: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[StreamEvent, None]:
    """创建标准流式生成器"""
    async with streaming_context(GeneratorMode.STANDARD) as generator:
        async for event in generator.generate(messages, provider_id, **kwargs):
            yield event


async def create_buffered_stream(
    messages: List[Dict[str, Any]],
    provider_id: Optional[str] = None,
    buffer_size: int = 1024,
    **kwargs
) -> AsyncGenerator[StreamEvent, None]:
    """创建缓冲流式生成器"""
    config = GeneratorConfig(
        mode=GeneratorMode.BUFFERED,
        buffer_size=buffer_size
    )

    async with streaming_context(GeneratorMode.BUFFERED, config) as generator:
        async for event in generator.generate(messages, provider_id, **kwargs):
            yield event


async def create_interleaved_stream(
    stream_configs: List[Dict[str, Any]],
    **kwargs
) -> AsyncGenerator[StreamEvent, None]:
    """创建交错流式生成器"""
    async with streaming_context(GeneratorMode.INTERLEAVED) as generator:
        # 添加多个流
        for config in stream_configs:
            await generator.add_stream(**config)

        async for event in generator.generate():
            yield event