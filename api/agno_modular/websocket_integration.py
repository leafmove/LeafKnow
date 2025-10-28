"""
WebSocket集成和反馈机制
提供实时双向通信和流式数据传输功能
"""

import asyncio
import json
import uuid
import logging
from typing import (
    Any, Dict, List, Optional, Union, Callable, Set,
    Awaitable
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from streaming_chat import StreamEvent, StreamEventType, StreamingChatManager
from streaming_generator import StreamingGenerator, GeneratorMode
from multi_provider_adapter import MultiProviderManager

logger = logging.getLogger(__name__)


class WebSocketMessageType(str, Enum):
    """WebSocket消息类型"""
    CHAT_REQUEST = "chat_request"
    CHAT_RESPONSE = "chat_response"
    STREAM_EVENT = "stream_event"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    STATUS_UPDATE = "status_update"
    USER_FEEDBACK = "user_feedback"
    SESSION_CONTROL = "session_control"


class ConnectionState(str, Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket消息结构"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: WebSocketMessageType = WebSocketMessageType.CHAT_REQUEST
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """从字典创建消息"""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            message_type=WebSocketMessageType(data.get("message_type", "chat_request")),
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            session_id=data.get("session_id"),
            user_id=data.get("user_id")
        )


class WebSocketConnection:
    """WebSocket连接管理类"""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.session_id = session_id
        self.state = ConnectionState.CONNECTING
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.active_streams: Dict[str, asyncio.Task] = {}

    async def accept_connection(self):
        """接受WebSocket连接"""
        await self.websocket.accept()
        self.state = ConnectionState.CONNECTED
        logger.info(f"WebSocket connection accepted: {self.connection_id}")

    async def send_message(self, message: WebSocketMessage) -> bool:
        """发送消息"""
        if self.state != ConnectionState.CONNECTED:
            return False

        try:
            await self.websocket.send_text(json.dumps(message.to_dict(), ensure_ascii=False))
            self.last_activity = datetime.now()
            self.message_count += 1
            self.bytes_sent += len(json.dumps(message.to_dict()))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            await self.set_error_state(str(e))
            return False

    async def receive_message(self) -> Optional[WebSocketMessage]:
        """接收消息"""
        if self.state != ConnectionState.CONNECTED:
            return None

        try:
            data = await self.websocket.receive_text()
            self.last_activity = datetime.now()
            self.message_count += 1
            self.bytes_received += len(data)

            message_data = json.loads(data)
            message = WebSocketMessage.from_dict(message_data)
            return message

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {self.connection_id}")
            await self.disconnect()
            return None
        except Exception as e:
            logger.error(f"Failed to receive message from {self.connection_id}: {e}")
            await self.set_error_state(str(e))
            return None

    async def send_stream_event(self, event: StreamEvent) -> bool:
        """发送流式事件"""
        message = WebSocketMessage(
            message_type=WebSocketMessageType.STREAM_EVENT,
            data={
                "event_type": event.event_type.value,
                "event_data": event.data,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat()
            }
        )
        return await self.send_message(message)

    async def send_error(self, error_message: str, error_code: Optional[str] = None) -> bool:
        """发送错误消息"""
        message = WebSocketMessage(
            message_type=WebSocketMessageType.ERROR,
            data={
                "error": error_message,
                "error_code": error_code,
                "timestamp": datetime.now().isoformat()
            }
        )
        return await self.send_message(message)

    async def send_status_update(self, status: Dict[str, Any]) -> bool:
        """发送状态更新"""
        message = WebSocketMessage(
            message_type=WebSocketMessageType.STATUS_UPDATE,
            data=status
        )
        return await self.send_message(message)

    async def ping(self) -> bool:
        """发送ping消息"""
        message = WebSocketMessage(
            message_type=WebSocketMessageType.PING,
            data={"timestamp": datetime.now().isoformat()}
        )
        return await self.send_message(message)

    async def pong(self) -> bool:
        """发送pong消息"""
        message = WebSocketMessage(
            message_type=WebSocketMessageType.PONG,
            data={"timestamp": datetime.now().isoformat()}
        )
        return await self.send_message(message)

    async def disconnect(self):
        """断开连接"""
        if self.state == ConnectionState.CONNECTED:
            self.state = ConnectionState.DISCONNECTING

            # 取消所有活跃的流
            for stream_id, task in self.active_streams.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            try:
                await self.websocket.close()
            except Exception:
                pass

            self.state = ConnectionState.DISCONNECTED
            logger.info(f"WebSocket connection closed: {self.connection_id}")

    async def set_error_state(self, error_message: str):
        """设置错误状态"""
        self.state = ConnectionState.ERROR
        logger.error(f"WebSocket connection error {self.connection_id}: {error_message}")

    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "active_streams": len(self.active_streams)
        }

    def add_active_stream(self, stream_id: str, task: asyncio.Task):
        """添加活跃流"""
        self.active_streams[stream_id] = task

    def remove_active_stream(self, stream_id: str):
        """移除活跃流"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(
        self,
        streaming_manager: StreamingChatManager,
        provider_manager: MultiProviderManager
    ):
        self.streaming_manager = streaming_manager
        self.provider_manager = provider_manager
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.session_connections: Dict[str, Set[str]] = defaultdict(set)
        self.message_handlers: Dict[WebSocketMessageType, List[Callable]] = defaultdict(list)
        self.connection_callbacks: List[Callable] = []

        # 心跳检测
        self.heartbeat_interval = 30.0
        self.heartbeat_task: Optional[asyncio.Task] = None

        # 统计信息
        self.total_connections = 0
        self.active_connections = 0
        self.total_messages = 0
        self.total_bytes_transferred = 0

    async def start_heartbeat(self):
        """启动心跳检测"""
        if self.heartbeat_task is None:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat(self):
        """停止心跳检测"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None

    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # 发送ping到所有连接
                for connection_id, connection in list(self.connections.items()):
                    if connection.state == ConnectionState.CONNECTED:
                        # 检查连接是否超时
                        idle_time = (datetime.now() - connection.last_activity).total_seconds()
                        if idle_time > self.heartbeat_interval * 2:
                            logger.warning(f"Connection {connection_id} timeout, disconnecting")
                            await self.remove_connection(connection_id)
                        else:
                            await connection.ping()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def add_connection(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> WebSocketConnection:
        """添加新连接"""
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id
        )

        await connection.accept_connection()

        self.connections[connection_id] = connection
        if user_id:
            self.user_connections[user_id].add(connection_id)
        if session_id:
            self.session_connections[session_id].add(connection_id)

        self.total_connections += 1
        self.active_connections += 1

        # 调用连接回调
        await self._notify_connection_callbacks("connected", connection)

        logger.info(f"New WebSocket connection added: {connection_id}")
        return connection

    async def remove_connection(self, connection_id: str):
        """移除连接"""
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]
        await connection.disconnect()

        # 从索引中移除
        if connection.user_id:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]

        if connection.session_id:
            self.session_connections[connection.session_id].discard(connection_id)
            if not self.session_connections[connection.session_id]:
                del self.session_connections[connection.session_id]

        del self.connections[connection_id]
        self.active_connections -= 1

        # 调用连接回调
        await self._notify_connection_callbacks("disconnected", connection)

        logger.info(f"WebSocket connection removed: {connection_id}")

    async def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """获取连接"""
        return self.connections.get(connection_id)

    async def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """获取用户的所有连接"""
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[cid] for cid in connection_ids if cid in self.connections]

    async def get_session_connections(self, session_id: str) -> List[WebSocketConnection]:
        """获取会话的所有连接"""
        connection_ids = self.session_connections.get(session_id, set())
        return [self.connections[cid] for cid in connection_ids if cid in self.connections]

    async def broadcast_to_user(
        self,
        user_id: str,
        message: WebSocketMessage
    ) -> int:
        """向用户的所有连接广播消息"""
        connections = await self.get_user_connections(user_id)
        success_count = 0

        for connection in connections:
            if await connection.send_message(message):
                success_count += 1

        return success_count

    async def broadcast_to_session(
        self,
        session_id: str,
        message: WebSocketMessage
    ) -> int:
        """向会话的所有连接广播消息"""
        connections = await self.get_session_connections(session_id)
        success_count = 0

        for connection in connections:
            if await connection.send_message(message):
                success_count += 1

        return success_count

    async def broadcast_to_all(self, message: WebSocketMessage) -> int:
        """向所有连接广播消息"""
        success_count = 0

        for connection in self.connections.values():
            if connection.state == ConnectionState.CONNECTED:
                if await connection.send_message(message):
                    success_count += 1

        return success_count

    def register_message_handler(
        self,
        message_type: WebSocketMessageType,
        handler: Callable[[WebSocketConnection, WebSocketMessage], Awaitable[None]]
    ):
        """注册消息处理器"""
        self.message_handlers[message_type].append(handler)

    def register_connection_callback(
        self,
        callback: Callable[[str, WebSocketConnection], Awaitable[None]]
    ):
        """注册连接回调"""
        self.connection_callbacks.append(callback)

    async def _notify_connection_callbacks(
        self,
        event_type: str,
        connection: WebSocketConnection
    ):
        """通知连接回调"""
        for callback in self.connection_callbacks:
            try:
                await callback(event_type, connection)
            except Exception as e:
                logger.error(f"Connection callback error: {e}")

    async def handle_connection(self, connection_id: str):
        """处理连接消息"""
        connection = await self.get_connection(connection_id)
        if not connection:
            return

        try:
            while connection.state == ConnectionState.CONNECTED:
                message = await connection.receive_message()
                if not message:
                    break

                self.total_messages += 1

                # 处理消息
                await self._handle_message(connection, message)

        except Exception as e:
            logger.error(f"Connection handling error for {connection_id}: {e}")
        finally:
            await self.remove_connection(connection_id)

    async def _handle_message(
        self,
        connection: WebSocketConnection,
        message: WebSocketMessage
    ):
        """处理接收到的消息"""
        handlers = self.message_handlers.get(message.message_type, [])

        if not handlers:
            # 如果没有特定处理器，发送错误消息
            await connection.send_error(f"No handler for message type: {message.message_type}")
            return

        # 调用所有处理器
        for handler in handlers:
            try:
                await handler(connection, message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                await connection.send_error(f"Handler error: {str(e)}")

    async def start_streaming_chat(
        self,
        connection: WebSocketConnection,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        generator_mode: GeneratorMode = GeneratorMode.STANDARD,
        **kwargs
    ) -> str:
        """开始流式聊天"""
        stream_id = str(uuid.uuid4())

        # 创建流式生成任务
        from streaming_generator import StreamingGeneratorFactory

        generator = StreamingGeneratorFactory.create_generator(
            mode=generator_mode,
            provider_manager=self.provider_manager
        )

        task = asyncio.create_task(
            self._stream_chat_worker(connection, stream_id, generator, messages, provider_id, **kwargs)
        )

        connection.add_active_stream(stream_id, task)

        # 发送流开始消息
        start_message = WebSocketMessage(
            message_type=WebSocketMessageType.SESSION_CONTROL,
            data={
                "action": "stream_started",
                "stream_id": stream_id,
                "generator_mode": generator_mode.value
            }
        )
        await connection.send_message(start_message)

        return stream_id

    async def _stream_chat_worker(
        self,
        connection: WebSocketConnection,
        stream_id: str,
        generator: StreamingGenerator,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        **kwargs
    ):
        """流式聊天工作器"""
        try:
            async for event in generator.generate(messages, provider_id, **kwargs):
                if connection.state != ConnectionState.CONNECTED:
                    break

                await connection.send_stream_event(event)

        except Exception as e:
            logger.error(f"Streaming chat error for {stream_id}: {e}")
            await connection.send_error(f"Streaming error: {str(e)}")
        finally:
            # 发送流结束消息
            end_message = WebSocketMessage(
                message_type=WebSocketMessageType.SESSION_CONTROL,
                data={
                    "action": "stream_finished",
                    "stream_id": stream_id
                }
            )
            await connection.send_message(end_message)

            # 清理流任务
            connection.remove_active_stream(stream_id)

    async def stop_streaming_chat(self, connection: WebSocketConnection, stream_id: str) -> bool:
        """停止流式聊天"""
        if stream_id not in connection.active_streams:
            return False

        task = connection.active_streams[stream_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        connection.remove_active_stream(stream_id)

        # 发送停止确认消息
        stop_message = WebSocketMessage(
            message_type=WebSocketMessageType.SESSION_CONTROL,
            data={
                "action": "stream_stopped",
                "stream_id": stream_id
            }
        )
        await connection.send_message(stop_message)

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "total_messages": self.total_messages,
            "user_count": len(self.user_connections),
            "session_count": len(self.session_connections),
            "connections_by_state": {
                state.value: len([c for c in self.connections.values() if c.state == state])
                for state in ConnectionState
            }
        }

    async def cleanup(self):
        """清理资源"""
        # 关闭所有连接
        for connection_id in list(self.connections.keys()):
            await self.remove_connection(connection_id)

        # 停止心跳
        await self.stop_heartbeat()

        logger.info("WebSocket manager cleaned up")


# 默认消息处理器
async def handle_chat_request(
    websocket_manager: WebSocketManager,
    connection: WebSocketConnection,
    message: WebSocketMessage
):
    """处理聊天请求"""
    data = message.data
    messages = data.get("messages", [])
    provider_id = data.get("provider_id")
    generator_mode = GeneratorMode(data.get("generator_mode", "standard"))

    if not messages:
        await connection.send_error("No messages provided")
        return

    # 开始流式聊天
    stream_id = await websocket_manager.start_streaming_chat(
        connection=connection,
        messages=messages,
        provider_id=provider_id,
        generator_mode=generator_mode,
        **data.get("kwargs", {})
    )

    logger.info(f"Started streaming chat {stream_id} for connection {connection.connection_id}")


async def handle_ping(
    websocket_manager: WebSocketManager,
    connection: WebSocketConnection,
    message: WebSocketMessage
):
    """处理ping消息"""
    await connection.pong()


async def handle_user_feedback(
    websocket_manager: WebSocketManager,
    connection: WebSocketConnection,
    message: WebSocketMessage
):
    """处理用户反馈"""
    feedback_data = message.data
    logger.info(f"Received user feedback from {connection.user_id}: {feedback_data}")

    # 这里可以实现反馈处理逻辑
    # 例如保存到数据库、发送通知等


# 便利函数
def create_websocket_manager(
    streaming_manager: StreamingChatManager,
    provider_manager: MultiProviderManager
) -> WebSocketManager:
    """创建WebSocket管理器"""
    manager = WebSocketManager(streaming_manager, provider_manager)

    # 注册默认消息处理器
    manager.register_message_handler(
        WebSocketMessageType.CHAT_REQUEST,
        lambda conn, msg: handle_chat_request(manager, conn, msg)
    )
    manager.register_message_handler(
        WebSocketMessageType.PING,
        lambda conn, msg: handle_ping(manager, conn, msg)
    )
    manager.register_message_handler(
        WebSocketMessageType.USER_FEEDBACK,
        lambda conn, msg: handle_user_feedback(manager, conn, msg)
    )

    return manager