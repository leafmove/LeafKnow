"""
流式对话API接口
提供RESTful API和WebSocket接口用于流式对话
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from multi_provider_adapter import get_multi_provider_manager, ProviderType
from streaming_chat import StreamFormat, create_streaming_chat_response
from streaming_generator import StreamingGeneratorFactory, GeneratorMode, GeneratorConfig
from websocket_integration import (
    WebSocketManager, WebSocketMessage, WebSocketMessageType,
    create_websocket_manager
)
from agent_manager import AgentCRUDManager

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/streaming", tags=["streaming"])

# 全局管理器实例
_websocket_manager: Optional[WebSocketManager] = None
_streaming_manager: Optional[StreamingChatManager] = None


# Pydantic模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Dict[str, Any]] = Field(..., description="聊天消息列表")
    provider_id: Optional[str] = Field(None, description="AI提供商ID")
    stream_format: StreamFormat = Field(StreamFormat.SSE, description="流式输出格式")
    generator_mode: GeneratorMode = Field(GeneratorMode.STANDARD, description="生成器模式")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    max_tokens: Optional[int] = Field(2000, description="最大token数")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具列表")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")


class AgentChatRequest(BaseModel):
    """Agent聊天请求模型"""
    agent_id: int = Field(..., description="Agent ID")
    message: str = Field(..., description="用户消息")
    provider_id: Optional[str] = Field(None, description="AI提供商ID")
    stream_format: StreamFormat = Field(StreamFormat.SSE, description="流式输出格式")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")


class MultiStreamRequest(BaseModel):
    """多流请求模型"""
    stream_configs: List[Dict[str, Any]] = Field(..., description="流配置列表")
    generator_mode: GeneratorMode = Field(GeneratorMode.INTERLEAVED, description="生成器模式")


class ProviderRegistrationRequest(BaseModel):
    """提供商注册请求"""
    provider_id: str = Field(..., description="提供商ID")
    provider_type: ProviderType = Field(..., description="提供商类型")
    model_name: str = Field(..., description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    max_tokens: int = Field(2000, description="最大token数")
    temperature: float = Field(0.7, description="温度参数")
    timeout: int = Field(60, description="超时时间")


# 依赖注入
def get_websocket_manager() -> WebSocketManager:
    """获取WebSocket管理器"""
    global _websocket_manager
    if _websocket_manager is None:
        from streaming_chat import get_streaming_manager
        _websocket_manager = create_websocket_manager(
            streaming_manager=get_streaming_manager(),
            provider_manager=get_multi_provider_manager()
        )
        # 启动心跳
        asyncio.create_task(_websocket_manager.start_heartbeat())
    return _websocket_manager


def get_streaming_manager() -> StreamingChatManager:
    """获取流式聊天管理器"""
    global _streaming_manager
    if _streaming_manager is None:
        from streaming_chat import get_streaming_manager
        _streaming_manager = get_streaming_manager()
    return _streaming_manager


# API端点
@router.post("/chat")
async def streaming_chat(
    request: ChatRequest,
    manager: StreamingChatManager = Depends(get_streaming_manager)
):
    """流式聊天接口"""

    async def generate_response():
        try:
            # 选择最佳提供商
            provider_manager = get_multi_provider_manager()
            provider_id = request.provider_id

            if provider_id is None:
                required_features = ["streaming"]
                if request.tools:
                    required_features.append("tools")
                provider_id = await provider_manager.get_best_provider_for_task(
                    "chat", required_features
                )

            # 创建生成器配置
            config = GeneratorConfig(
                mode=request.generator_mode,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            # 创建流式生成器
            generator = StreamingGeneratorFactory.create_generator(
                mode=request.generator_mode,
                config=config,
                provider_manager=provider_manager
            )

            # 生成流式响应
            async for event in generator.generate(
                messages=request.messages,
                provider_id=provider_id,
                tools=request.tools
            ):
                if request.stream_format == StreamFormat.SSE:
                    yield event.to_sse_format()
                elif request.stream_format == StreamFormat.AI_SDK_V5:
                    yield event.to_ai_sdk_v5_format()
                else:
                    yield json.dumps(event.to_websocket_format(), ensure_ascii=False)

            # 发送结束标记
            if request.stream_format in [StreamFormat.SSE, StreamFormat.AI_SDK_V5]:
                yield 'data: [DONE]\n\n'

        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            if request.stream_format == StreamFormat.SSE:
                yield f'data: {json.dumps(error_event, ensure_ascii=False)}\n\n'
            else:
                yield json.dumps(error_event, ensure_ascii=False)

    # 设置正确的媒体类型
    media_type = "text/plain; charset=utf-8"
    if request.stream_format == StreamFormat.SSE:
        media_type = "text/event-stream"

    return StreamingResponse(
        generate_response(),
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


@router.post("/chat/{agent_id}")
async def agent_streaming_chat(
    agent_id: int,
    request: AgentChatRequest,
    agent_manager: Optional[AgentCRUDManager] = None
):
    """Agent流式聊天接口"""

    async def generate_response():
        try:
            manager = get_streaming_manager()

            async for chunk in manager.stream_chat_with_agent(
                agent_id=agent_id,
                message=request.message,
                provider_id=request.provider_id,
                stream_format=request.stream_format,
                user_id=request.user_id,
                session_id=request.session_id
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Agent streaming chat error: {e}")
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            if request.stream_format == StreamFormat.SSE:
                yield f'data: {json.dumps(error_event, ensure_ascii=False)}\n\n'
            else:
                yield json.dumps(error_event, ensure_ascii=False)

    media_type = "text/event-stream"
    if request.stream_format != StreamFormat.SSE:
        media_type = "text/plain; charset=utf-8"

    return StreamingResponse(
        generate_response(),
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/multi-stream")
async def multi_streaming_chat(
    request: MultiStreamRequest,
    manager: StreamingChatManager = Depends(get_streaming_manager)
):
    """多流并发聊天接口"""

    async def generate_response():
        try:
            from streaming_generator import create_interleaved_stream

            # 创建交错流
            async for event in create_interleaved_stream(request.stream_configs):
                if isinstance(event, str):
                    yield event
                else:
                    yield json.dumps(event.to_websocket_format(), ensure_ascii=False)

            yield 'data: [DONE]\n\n'

        except Exception as e:
            logger.error(f"Multi-stream chat error: {e}")
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f'data: {json.dumps(error_event, ensure_ascii=False)}\n\n'

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/providers")
async def list_providers():
    """列出所有可用的提供商"""
    try:
        provider_manager = get_multi_provider_manager()
        providers = provider_manager.list_providers()

        return {
            "providers": providers,
            "total_count": len(providers),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/register")
async def register_provider(request: ProviderRegistrationRequest):
    """注册新的AI提供商"""
    try:
        from multi_provider_adapter import ProviderConfig

        config = ProviderConfig(
            provider_type=request.provider_type,
            model_name=request.model_name,
            api_key=request.api_key,
            base_url=request.base_url,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout=request.timeout
        )

        provider_manager = get_multi_provider_manager()
        success = await provider_manager.register_provider(request.provider_id, config)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to register provider")

        return {
            "message": "Provider registered successfully",
            "provider_id": request.provider_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/health")
async def check_providers_health():
    """检查所有提供商的健康状态"""
    try:
        provider_manager = get_multi_provider_manager()
        health_status = await provider_manager.health_check_all()

        return {
            "health_status": health_status,
            "total_providers": len(health_status),
            "healthy_providers": len([s for s in health_status.values() if s.get("status") == "healthy"]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: Optional[str] = None
):
    """WebSocket端点"""
    manager = get_websocket_manager()

    try:
        # 添加连接
        connection = await manager.add_connection(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id
        )

        logger.info(f"WebSocket connection established for user {user_id}")

        # 处理连接消息
        await manager.handle_connection(connection.connection_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await websocket.close()


@router.get("/stats")
async def get_streaming_stats():
    """获取流式对话统计信息"""
    try:
        manager = get_streaming_manager()
        websocket_manager = get_websocket_manager()

        stats = {
            "streaming_stats": {
                "active_sessions": manager.get_active_sessions_count()
            },
            "websocket_stats": websocket_manager.get_statistics(),
            "provider_stats": await get_multi_provider_manager().health_check_all(),
            "timestamp": datetime.now().isoformat()
        }

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generator-modes")
async def list_generator_modes():
    """列出可用的生成器模式"""
    return {
        "modes": [
            {
                "mode": "standard",
                "description": "标准异步生成器，直接输出流式事件"
            },
            {
                "mode": "buffered",
                "description": "缓冲模式，累积一定量数据后输出"
            },
            {
                "mode": "chunked",
                "description": "分块模式，按固定大小分块输出"
            },
            {
                "mode": "interleaved",
                "description": "交错模式，支持多个流的交错输出"
            },
            {
                "mode": "priority",
                "description": "优先级模式，按优先级排序输出事件"
            }
        ]
    }


@router.get("/stream-formats")
async def list_stream_formats():
    """列出可用的流式输出格式"""
    return {
        "formats": [
            {
                "format": "sse",
                "description": "Server-Sent Events格式，适用于HTTP流式响应"
            },
            {
                "format": "websocket",
                "description": "WebSocket格式，适用于双向实时通信"
            },
            {
                "format": "generator",
                "description": "Python生成器格式，适用于程序间调用"
            },
            {
                "format": "ai_sdk_v5",
                "description": "Vercel AI SDK v5格式，适用于前端AI SDK集成"
            }
        ]
    }


# 清理函数
async def cleanup_streaming_resources():
    """清理流式对话资源"""
    global _websocket_manager, _streaming_manager

    if _websocket_manager:
        await _websocket_manager.cleanup()
        _websocket_manager = None

    # 清理其他资源
    logger.info("Streaming resources cleaned up")


# 启动和关闭事件处理
async def on_startup():
    """应用启动时的初始化"""
    logger.info("Initializing streaming API...")
    # 这里可以添加额外的初始化逻辑


async def on_shutdown():
    """应用关闭时的清理"""
    logger.info("Shutting down streaming API...")
    await cleanup_streaming_resources()