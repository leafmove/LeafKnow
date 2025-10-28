"""
流式对话输出实现
支持多种格式的流式输出，包括SSE、WebSocket和生成器模式
"""

import asyncio
import json
import uuid
from typing import (
    Any, Dict, List, Optional, Union, AsyncGenerator, Callable,
    Iterator
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from multi_provider_adapter import MultiProviderManager, get_multi_provider_manager
from agent_manager import AgentCRUDManager

logger = logging.getLogger(__name__)


class StreamFormat(str, Enum):
    """流式输出格式"""
    SSE = "sse"  # Server-Sent Events
    WEBSOCKET = "websocket"  # WebSocket
    GENERATOR = "generator"  # Python生成器
    AI_SDK_V5 = "ai_sdk_v5"  # Vercel AI SDK v5格式


class StreamEventType(str, Enum):
    """流式事件类型"""
    TEXT_START = "text-start"
    TEXT_DELTA = "text-delta"
    TEXT_END = "text-end"

    REASONING_START = "reasoning-start"
    REASONING_DELTA = "reasoning-delta"
    REASONING_END = "reasoning-end"

    TOOL_INPUT_START = "tool-input-start"
    TOOL_INPUT_DELTA = "tool-input-delta"
    TOOL_INPUT_AVAILABLE = "tool-input-available"
    TOOL_OUTPUT_AVAILABLE = "tool-output-available"

    ERROR = "error"
    FINISH = "finish"
    METADATA = "metadata"
    USAGE = "usage"


@dataclass
class StreamEvent:
    """流式事件数据结构"""
    event_type: StreamEventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_sse_format(self) -> str:
        """转换为SSE格式"""
        data = {
            "type": self.event_type.value,
            "id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            **self.data
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def to_websocket_format(self) -> Dict[str, Any]:
        """转换为WebSocket格式"""
        return {
            "type": self.event_type.value,
            "id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }

    def to_ai_sdk_v5_format(self) -> str:
        """转换为Vercel AI SDK v5格式"""
        if self.event_type == StreamEventType.TEXT_DELTA:
            return f'data: {json.dumps({"type": "text-delta", "id": self.event_id, "delta": self.data.get("content", "")})}\n\n'
        elif self.event_type == StreamEventType.TEXT_START:
            return f'data: {json.dumps({"type": "text-start", "id": self.event_id})}\n\n'
        elif self.event_type == StreamEventType.TEXT_END:
            return f'data: {json.dumps({"type": "text-end", "id": self.event_id})}\n\n'
        elif self.event_type == StreamEventType.REASONING_DELTA:
            return f'data: {json.dumps({"type": "reasoning-delta", "id": self.event_id, "delta": self.data.get("content", "")})}\n\n'
        elif self.event_type == StreamEventType.FINISH:
            return f'data: {json.dumps({"type": "finish"})}\n\n'
        elif self.event_type == StreamEventType.ERROR:
            return f'data: {json.dumps({"type": "error", "errorText": self.data.get("error", "")})}\n\n'
        else:
            # 其他事件类型转换为通用格式
            return self.to_sse_format()


class StreamingChatSession:
    """流式对话会话"""

    def __init__(
        self,
        session_id: str,
        provider_manager: MultiProviderManager,
        agent_manager: Optional[AgentCRUDManager] = None
    ):
        self.session_id = session_id
        self.provider_manager = provider_manager
        self.agent_manager = agent_manager
        self.start_time = datetime.now()
        self.events: List[StreamEvent] = []
        self.usage_stats: Dict[str, Any] = {}

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        stream_format: StreamFormat = StreamFormat.SSE,
        **kwargs
    ) -> Union[AsyncGenerator[str, None], AsyncGenerator[Dict[str, Any], None]]:
        """流式聊天主方法"""
        try:
            # 选择最佳提供商
            if provider_id is None:
                required_features = ["streaming"]
                if tools:
                    required_features.append("tools")
                provider_id = await self.provider_manager.get_best_provider_for_task(
                    "chat", required_features
                )

            adapter = self.provider_manager.get_adapter(provider_id)

            # 发送会话开始事件
            yield self._format_event(StreamEvent(
                event_type=StreamEventType.METADATA,
                data={
                    "session_id": self.session_id,
                    "provider_id": provider_id,
                    "model_name": adapter.model_name,
                    "start_time": self.start_time.isoformat()
                }
            ), stream_format)

            # 开始流式对话
            async for event in adapter.stream_chat(messages, tools, **kwargs):
                stream_event = self._convert_provider_event(event)
                self.events.append(stream_event)

                yield self._format_event(stream_event, stream_format)

            # 发送完成事件
            finish_event = StreamEvent(
                event_type=StreamEventType.FINISH,
                data={
                    "total_events": len(self.events),
                    "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "usage": self.usage_stats
                }
            )
            self.events.append(finish_event)

            yield self._format_event(finish_event, stream_format)

            # 发送结束标记（SSE格式专用）
            if stream_format == StreamFormat.SSE or stream_format == StreamFormat.AI_SDK_V5:
                yield 'data: [DONE]\n\n'

        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            error_event = StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e)}
            )
            yield self._format_event(error_event, stream_format)

    def _convert_provider_event(self, provider_event: Dict[str, Any]) -> StreamEvent:
        """转换厂商事件为标准事件格式"""
        event_type = provider_event.get("type", "unknown")

        if event_type == "text-delta":
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data={"content": provider_event.get("content", "")}
            )
        elif event_type == "finish":
            return StreamEvent(
                event_type=StreamEventType.FINISH,
                data={"reason": provider_event.get("reason", "unknown")}
            )
        elif event_type == "error":
            return StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": provider_event.get("error", "Unknown error")}
            )
        elif event_type == "tool-call-delta":
            return StreamEvent(
                event_type=StreamEventType.TOOL_INPUT_DELTA,
                data={
                    "tool_call_id": provider_event.get("tool_call_id"),
                    "function_name": provider_event.get("function_name"),
                    "function_args": provider_event.get("function_args")
                }
            )
        else:
            # 其他未知类型
            return StreamEvent(
                event_type=StreamEventType.METADATA,
                data=provider_event
            )

    def _format_event(self, event: StreamEvent, stream_format: StreamFormat) -> Union[str, Dict[str, Any]]:
        """格式化事件为指定格式"""
        if stream_format == StreamFormat.SSE:
            return event.to_sse_format()
        elif stream_format == StreamFormat.WEBSOCKET:
            return event.to_websocket_format()
        elif stream_format == StreamFormat.AI_SDK_V5:
            return event.to_ai_sdk_v5_format()
        elif stream_format == StreamFormat.GENERATOR:
            return event
        else:
            return event.to_sse_format()


class StreamingChatManager:
    """流式对话管理器"""

    def __init__(
        self,
        provider_manager: Optional[MultiProviderManager] = None,
        agent_manager: Optional[AgentCRUDManager] = None
    ):
        self.provider_manager = provider_manager or get_multi_provider_manager()
        self.agent_manager = agent_manager
        self.active_sessions: Dict[str, StreamingChatSession] = {}

    def create_session(self, session_id: Optional[str] = None) -> StreamingChatSession:
        """创建流式对话会话"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = StreamingChatSession(
            session_id=session_id,
            provider_manager=self.provider_manager,
            agent_manager=self.agent_manager
        )

        self.active_sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[StreamingChatSession]:
        """获取会话"""
        return self.active_sessions.get(session_id)

    def remove_session(self, session_id: str) -> bool:
        """移除会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    async def stream_chat_with_agent(
        self,
        agent_id: int,
        message: str,
        session_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        stream_format: StreamFormat = StreamFormat.SSE,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Union[AsyncGenerator[str, None], AsyncGenerator[Dict[str, Any], None]]:
        """使用Agent进行流式对话"""
        if self.agent_manager is None:
            raise ValueError("Agent manager not configured")

        # 创建或获取会话
        if session_id is None:
            session = self.create_session()
        else:
            session = self.get_session(session_id)
            if session is None:
                session = self.create_session(session_id)

        # 构建消息格式
        messages = [{"role": "user", "content": message}]

        # 使用Agent的流式聊天功能
        try:
            # 如果Agent管理器支持流式输出，使用它
            if hasattr(self.agent_manager, 'stream_agent_run'):
                async for event in self.agent_manager.stream_agent_run(
                    agent_id=agent_id,
                    message=message,
                    session_id=session.session_id,
                    user_id=user_id,
                    **kwargs
                ):
                    yield self._format_agent_event(event, stream_format)
            else:
                # 降级到多厂商适配器
                async for event in session.stream_chat(
                    messages=messages,
                    provider_id=provider_id,
                    stream_format=stream_format,
                    **kwargs
                ):
                    yield event

        except Exception as e:
            logger.error(f"Agent streaming chat error: {e}")
            error_event = StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e)}
            )
            yield self._format_event(error_event, stream_format)

    def _format_agent_event(self, agent_event: Any, stream_format: StreamFormat) -> Union[str, Dict[str, Any]]:
        """格式化Agent事件"""
        # 这里需要根据实际Agent事件格式来实现
        # 暂时提供基本实现
        if isinstance(agent_event, str):
            # 如果是字符串，假设是SSE格式
            if stream_format == StreamFormat.SSE or stream_format == StreamFormat.AI_SDK_V5:
                return agent_event
            else:
                # 转换为其他格式
                try:
                    data = json.loads(agent_event.strip("data: "))
                    return StreamEvent(
                        event_type=StreamEventType(data.get("type", "metadata")),
                        data=data
                    )
                except:
                    return StreamEvent(
                        event_type=StreamEventType.TEXT_DELTA,
                        data={"content": agent_event}
                    )
        else:
            # 如果是字典或其他格式
            return agent_event

    def _format_event(self, event: StreamEvent, stream_format: StreamFormat) -> Union[str, Dict[str, Any]]:
        """格式化事件"""
        if stream_format == StreamFormat.SSE:
            return event.to_sse_format()
        elif stream_format == StreamFormat.WEBSOCKET:
            return event.to_websocket_format()
        elif stream_format == StreamFormat.AI_SDK_V5:
            return event.to_ai_sdk_v5_format()
        elif stream_format == StreamFormat.GENERATOR:
            return event
        else:
            return event.to_sse_format()

    def get_active_sessions_count(self) -> int:
        """获取活跃会话数量"""
        return len(self.active_sessions)

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话统计信息"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "start_time": session.start_time.isoformat(),
            "duration_seconds": (datetime.now() - session.start_time).total_seconds(),
            "events_count": len(session.events),
            "usage_stats": session.usage_stats
        }


# 便利函数
async def create_streaming_chat_response(
    messages: List[Dict[str, Any]],
    provider_id: Optional[str] = None,
    stream_format: StreamFormat = StreamFormat.SSE,
    **kwargs
) -> AsyncGenerator[str, None]:
    """创建流式聊天响应的便利函数"""
    manager = StreamingChatManager()
    session = manager.create_session()

    async for event in session.stream_chat(
        messages=messages,
        provider_id=provider_id,
        stream_format=stream_format,
        **kwargs
    ):
        yield event


class BufferedStreamProcessor:
    """缓冲流处理器 - 用于处理不规则的流式数据"""

    def __init__(self, buffer_size: int = 1024, flush_interval: float = 0.1):
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer: List[str] = []
        self.last_flush = datetime.now()

    async def process_stream(
        self,
        stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """处理流式数据"""
        buffer_content = ""

        async for chunk in stream:
            buffer_content += chunk

            # 检查是否需要刷新缓冲区
            current_time = datetime.now()
            should_flush = (
                len(buffer_content) >= self.buffer_size or
                (current_time - self.last_flush).total_seconds() >= self.flush_interval
            )

            if should_flush and buffer_content:
                yield buffer_content
                buffer_content = ""
                self.last_flush = current_time

        # 刷新剩余内容
        if buffer_content:
            yield buffer_content

    def reset(self):
        """重置处理器状态"""
        self.buffer.clear()
        self.last_flush = datetime.now()


class StreamAggregator:
    """流聚合器 - 用于聚合多个流式输出"""

    def __init__(self):
        self.active_streams: Dict[str, asyncio.Queue] = {}

    async def add_stream(self, stream_id: str, stream: AsyncGenerator[Dict[str, Any], None]):
        """添加流"""
        if stream_id not in self.active_streams:
            self.active_streams[stream_id] = asyncio.Queue()

        # 启动流处理任务
        asyncio.create_task(self._process_stream(stream_id, stream))

    async def _process_stream(self, stream_id: str, stream: AsyncGenerator[Dict[str, Any], None]):
        """处理单个流"""
        queue = self.active_streams[stream_id]

        try:
            async for event in stream:
                await queue.put(event)
        except Exception as e:
            await queue.put({"type": "error", "error": str(e)})
        finally:
            await queue.put({"type": "stream_end"})

    async def get_aggregated_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """获取聚合的事件"""
        while self.active_streams:
            # 轮询所有活跃的流
            for stream_id, queue in list(self.active_streams.items()):
                try:
                    # 非阻塞获取事件
                    event = queue.get_nowait()

                    if event.get("type") == "stream_end":
                        del self.active_streams[stream_id]
                    else:
                        yield {
                            **event,
                            "stream_id": stream_id,
                            "timestamp": datetime.now().isoformat()
                        }

                except asyncio.QueueEmpty:
                    continue

            # 短暂休眠避免CPU占用过高
            await asyncio.sleep(0.01)

    async def close_all(self):
        """关闭所有流"""
        for stream_id in list(self.active_streams.keys()):
            del self.active_streams[stream_id]


# 全局流式聊天管理器实例
_streaming_manager = StreamingChatManager()


def get_streaming_manager() -> StreamingChatManager:
    """获取全局流式聊天管理器实例"""
    return _streaming_manager