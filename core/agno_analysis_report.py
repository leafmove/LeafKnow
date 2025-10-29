#!/usr/bin/env python3
"""
agno库架构分析与Python实现案例
本文件详细分析agno三方库的架构、集成方式、多用户支持、流式输出等特性
并提供完整的Python实现案例
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import openai
from pydantic import BaseModel, Field


class AgnoArchitectureAnalysis:
    """agno库架构分析类"""

    def __init__(self):
        self.title = "agno三方库架构深度分析"
        self.description = "分析OpenAI模型集成、多用户会话、流式输出等核心特性"

    def analyze_model_integration(self) -> Dict[str, Any]:
        """
        分析OpenAI模型集成方式

        核心发现：
        1. 支持标准OpenAI API参数：api_key, base_url, model_id
        2. 提供灵活的客户端配置：timeout, max_retries, headers等
        3. 同步和异步双模式支持
        4. 流式和非流式响应处理
        """
        return {
            "模型集成架构": {
                "核心类": "OpenAIChat",
                "关键参数": {
                    "api_key": "API密钥，支持环境变量和直接设置",
                    "base_url": "自定义API端点，支持OpenAI兼容接口",
                    "id": "模型ID，如gpt-4o, gpt-3.5-turbo等",
                    "organization": "OpenAI组织ID（可选）",
                    "timeout": "请求超时时间",
                    "max_retries": "最大重试次数",
                    "default_headers": "自定义HTTP头",
                    "http_client": "自定义HTTP客户端"
                },
                "支持的功能": [
                    "文本生成",
                    "流式输出",
                    "工具调用",
                    "多模态输入（图片、音频、文件）",
                    "结构化输出",
                    "异步处理"
                ]
            }
        }

    def analyze_multi_user_sessions(self) -> Dict[str, Any]:
        """
        分析多用户会话并行支持

        核心发现：
        1. 基于session_id的会话隔离
        2. 支持user_id多用户区分
        3. 异步并发处理能力
        4. 会话状态持久化
        """
        return {
            "多用户会话架构": {
                "会话管理": {
                    "session_id": "唯一会话标识符",
                    "user_id": "用户标识符，支持多用户隔离",
                    "agent_id": "智能体ID",
                    "team_id": "团队ID（协作场景）",
                    "workflow_id": "工作流ID"
                },
                "并发支持": {
                    "异步处理": "支持asyncio并发",
                    "会话隔离": "每个session_id独立处理",
                    "资源管理": "内置连接池和资源限制",
                    "状态管理": "支持会话状态持久化"
                },
                "会话功能": [
                    "消息历史管理",
                    "会话摘要生成",
                    "跨会话记忆",
                    "工具调用历史",
                    "运行状态跟踪"
                ]
            }
        }

    def analyze_streaming_output(self) -> Dict[str, Any]:
        """
        分析流式对话输出机制

        核心发现：
        1. 基于generator的流式输出
        2. 支持外部流式反馈
        3. 实时事件处理
        4. 多种流式格式支持
        """
        return {
            "流式输出架构": {
                "流式机制": {
                    "同步流式": "Iterator[ModelResponse]",
                    "异步流式": "AsyncIterator[ModelResponse]",
                    "事件驱动": "基于ModelResponseEvent",
                    "增量更新": "支持内容增量更新"
                },
                "外部反馈": {
                    "WebSocket": "实时双向通信",
                    "SSE": "Server-Sent Events",
                    "HTTP流式": "标准HTTP流式响应",
                    "自定义协议": "支持自定义流式协议"
                },
                "流式内容": [
                    "文本内容流",
                    "工具调用流",
                    "多模态内容流",
                    "错误信息流",
                    "状态更新流"
                ]
            }
        }

    def analyze_input_output_formats(self) -> Dict[str, Any]:
        """
        分析输入输出格式要求

        核心发现：
        1. 支持多种输入格式：文本、图片、音频、文件
        2. 灵活的输出格式：结构化、流式、多模态
        3. 完整的消息元数据支持
        """
        return {
            "输入格式要求": {
                "消息结构": {
                    "role": "system/user/assistant/tool",
                    "content": "文本内容或结构化内容",
                    "name": "可选的消息名称",
                    "tool_calls": "工具调用信息",
                    "tool_call_id": "工具调用ID"
                },
                "多模态支持": {
                    "images": "图片输入（URL、base64、文件）",
                    "audio": "音频输入（多种格式）",
                    "videos": "视频输入",
                    "files": "文档文件输入"
                },
                "高级功能": {
                    "工具调用": "function calling支持",
                    "结构化输出": "Pydantic模型集成",
                    "流式输入": "支持流式输入处理",
                    "引用支持": "文档引用和URL引用"
                }
            },
            "输出格式规范": {
                "响应结构": {
                    "content": "生成的文本内容",
                    "role": "响应角色",
                    "tool_calls": "工具调用结果",
                    "reasoning_content": "推理过程内容",
                    "audio_output": "音频输出",
                    "metrics": "使用指标"
                },
                "元数据": {
                    "usage": "token使用统计",
                    "timing": "响应时间指标",
                    "model": "使用的模型信息",
                    "citations": "引用信息"
                }
            }
        }


class OpenAIModelIntegration:
    """OpenAI模型集成实现案例"""

    def __init__(self, api_key: str, base_url: str = None, model_id: str = "gpt-3.5-turbo"):
        """
        初始化OpenAI模型集成

        Args:
            api_key: OpenAI API密钥
            base_url: 自定义API端点
            model_id: 模型ID
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_id = model_id
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.async_client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def create_chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        创建聊天完成请求

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            API响应结果
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                **kwargs
            )
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            return {"error": str(e)}

    def create_streaming_completion(self, messages: List[Dict[str, Any]], **kwargs):
        """
        创建流式聊天完成请求

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            流式响应片段
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "finish_reason": chunk.choices[0].finish_reason,
                        "usage": chunk.usage.model_dump() if chunk.usage else None
                    }
        except Exception as e:
            yield {"error": str(e)}

    async def create_async_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        创建异步聊天完成请求

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            API响应结果
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                **kwargs
            )
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            return {"error": str(e)}

    async def create_async_streaming_completion(self, messages: List[Dict[str, Any]], **kwargs):
        """
        创建异步流式聊天完成请求

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            异步流式响应片段
        """
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "finish_reason": chunk.choices[0].finish_reason,
                        "usage": chunk.usage.model_dump() if chunk.usage else None
                    }
        except Exception as e:
            yield {"error": str(e)}


class MultiUserSessionManager:
    """多用户会话管理器"""

    def __init__(self):
        """初始化会话管理器"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, List[str]] = {}

    def create_session(self, user_id: str, agent_id: str = None) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID
            agent_id: 智能体ID

        Returns:
            会话ID
        """
        session_id = str(uuid4())

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "messages": [],
            "status": "active",
            "metadata": {}
        }

        self.sessions[session_id] = session

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息
        """
        return self.sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str, **kwargs) -> bool:
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            role: 消息角色
            content: 消息内容
            **kwargs: 其他消息属性

        Returns:
            是否添加成功
        """
        if session_id not in self.sessions:
            return False

        message = {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "created_at": int(time.time()),
            **kwargs
        }

        self.sessions[session_id]["messages"].append(message)
        self.sessions[session_id]["updated_at"] = int(time.time())

        return True

    def get_session_messages(self, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取会话消息

        Args:
            session_id: 会话ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        if session_id not in self.sessions:
            return []

        messages = self.sessions[session_id]["messages"]
        if limit:
            messages = messages[-limit:]

        return messages

    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        获取用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            会话ID列表
        """
        return self.user_sessions.get(user_id, [])

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        user_id = session["user_id"]

        del self.sessions[session_id]
        if user_id in self.user_sessions:
            self.user_sessions[user_id].remove(session_id)

        return True


class StreamingResponseHandler:
    """流式响应处理器"""

    def __init__(self):
        """初始化流式处理器"""
        self.active_streams: Dict[str, Any] = {}

    def create_stream(self, stream_id: str) -> bool:
        """
        创建流

        Args:
            stream_id: 流ID

        Returns:
            是否创建成功
        """
        if stream_id in self.active_streams:
            return False

        self.active_streams[stream_id] = {
            "id": stream_id,
            "created_at": int(time.time()),
            "chunks": [],
            "completed": False,
            "error": None
        }

        return True

    def add_chunk(self, stream_id: str, chunk: Dict[str, Any]) -> bool:
        """
        添加流数据块

        Args:
            stream_id: 流ID
            chunk: 数据块

        Returns:
            是否添加成功
        """
        if stream_id not in self.active_streams:
            return False

        self.active_streams[stream_id]["chunks"].append({
            "data": chunk,
            "timestamp": int(time.time())
        })

        return True

    def complete_stream(self, stream_id: str) -> bool:
        """
        完成流

        Args:
            stream_id: 流ID

        Returns:
            是否完成成功
        """
        if stream_id not in self.active_streams:
            return False

        self.active_streams[stream_id]["completed"] = True
        return True

    def set_stream_error(self, stream_id: str, error: str) -> bool:
        """
        设置流错误

        Args:
            stream_id: 流ID
            error: 错误信息

        Returns:
            是否设置成功
        """
        if stream_id not in self.active_streams:
            return False

        self.active_streams[stream_id]["error"] = error
        self.active_streams[stream_id]["completed"] = True

        return True

    def get_stream_chunks(self, stream_id: str) -> List[Dict[str, Any]]:
        """
        获取流数据块

        Args:
            stream_id: 流ID

        Returns:
            数据块列表
        """
        if stream_id not in self.active_streams:
            return []

        return self.active_streams[stream_id]["chunks"]

    def stream_to_external(self, stream_id: str, callback=None):
        """
        将流式输出到外部

        Args:
            stream_id: 流ID
            callback: 外部回调函数
        """
        if stream_id not in self.active_streams:
            return

        stream = self.active_streams[stream_id]

        for chunk_info in stream["chunks"]:
            chunk = chunk_info["data"]

            if callback:
                callback(chunk)
            else:
                # 默认输出到控制台
                print(f"[Stream {stream_id}] {chunk}")

    def get_stream_summary(self, stream_id: str) -> Dict[str, Any]:
        """
        获取流摘要

        Args:
            stream_id: 流ID

        Returns:
            流摘要信息
        """
        if stream_id not in self.active_streams:
            return {}

        stream = self.active_streams[stream_id]
        chunks = stream["chunks"]

        return {
            "stream_id": stream_id,
            "created_at": stream["created_at"],
            "total_chunks": len(chunks),
            "completed": stream["completed"],
            "error": stream["error"],
            "duration": int(time.time()) - stream["created_at"] if chunks else 0
        }


class AgnoIntegratedExample:
    """agno集成示例"""

    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化集成示例

        Args:
            api_key: API密钥
            base_url: API端点
        """
        self.model_integration = OpenAIModelIntegration(
            api_key=api_key,
            base_url=base_url
        )
        self.session_manager = MultiUserSessionManager()
        self.stream_handler = StreamingResponseHandler()

    def basic_chat_example(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        基础聊天示例

        Args:
            user_id: 用户ID
            message: 用户消息

        Returns:
            响应结果
        """
        # 创建或获取会话
        user_sessions = self.session_manager.get_user_sessions(user_id)
        if not user_sessions:
            session_id = self.session_manager.create_session(user_id)
        else:
            session_id = user_sessions[-1]  # 使用最新的会话

        # 添加用户消息
        self.session_manager.add_message(session_id, "user", message)

        # 获取会话历史
        messages = self.session_manager.get_session_messages(session_id)

        # 转换为OpenAI格式
        openai_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        # 调用模型
        response = self.model_integration.create_chat_completion(openai_messages)

        # 添加助手响应
        if "content" in response:
            self.session_manager.add_message(
                session_id,
                "assistant",
                response["content"],
                usage=response.get("usage", {})
            )

        return {
            "session_id": session_id,
            "response": response
        }

    def streaming_chat_example(self, user_id: str, message: str):
        """
        流式聊天示例

        Args:
            user_id: 用户ID
            message: 用户消息

        Yields:
            流式响应
        """
        # 创建会话
        session_id = self.session_manager.create_session(user_id)
        stream_id = str(uuid4())

        # 创建流
        self.stream_handler.create_stream(stream_id)

        # 添加用户消息
        self.session_manager.add_message(session_id, "user", message)

        # 获取消息历史
        messages = self.session_manager.get_session_messages(session_id)
        openai_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        # 流式调用
        for chunk in self.model_integration.create_streaming_completion(openai_messages):
            # 添加到流处理器
            self.stream_handler.add_chunk(stream_id, chunk)

            # 实时输出到外部
            yield {
                "session_id": session_id,
                "stream_id": stream_id,
                "chunk": chunk
            }

        # 完成流
        self.stream_handler.complete_stream(stream_id)

        # 收集完整响应
        full_response = ""
        for chunk_info in self.stream_handler.get_stream_chunks(stream_id):
            if "content" in chunk_info["data"]:
                full_response += chunk_info["data"]["content"]

        # 添加完整响应到会话
        self.session_manager.add_message(
            session_id,
            "assistant",
            full_response,
            stream_id=stream_id
        )

    def multi_user_parallel_example(self, users_data: List[Dict[str, str]]):
        """
        多用户并行处理示例

        Args:
            users_data: 用户数据列表，每个包含user_id和message

        Returns:
            并行处理结果
        """
        async def process_user(user_data):
            user_id = user_data["user_id"]
            message = user_data["message"]

            # 创建异步会话
            session_id = self.session_manager.create_session(user_id)

            # 添加消息
            self.session_manager.add_message(session_id, "user", message)

            # 异步调用模型
            messages = self.session_manager.get_session_messages(session_id)
            openai_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]

            response = await self.model_integration.create_async_completion(openai_messages)

            # 添加响应
            if "content" in response:
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    response["content"],
                    usage=response.get("usage", {})
                )

            return {
                "user_id": user_id,
                "session_id": session_id,
                "response": response
            }

        # 并发处理所有用户
        async def process_all_users():
            tasks = [process_user(user_data) for user_data in users_data]
            return await asyncio.gather(*tasks, return_exceptions=True)

        return asyncio.run(process_all_users())


def main():
    """主函数：演示agno库的核心功能"""

    print("=" * 80)
    print("agno库架构分析报告")
    print("=" * 80)

    # 创建分析器
    analyzer = AgnoArchitectureAnalysis()

    # 打印分析结果
    print("\n1. OpenAI模型集成分析")
    print(json.dumps(analyzer.analyze_model_integration(), ensure_ascii=False, indent=2))

    print("\n2. 多用户会话支持分析")
    print(json.dumps(analyzer.analyze_multi_user_sessions(), ensure_ascii=False, indent=2))

    print("\n3. 流式输出机制分析")
    print(json.dumps(analyzer.analyze_streaming_output(), ensure_ascii=False, indent=2))

    print("\n4. 输入输出格式分析")
    print(json.dumps(analyzer.analyze_input_output_formats(), ensure_ascii=False, indent=2))

    print("\n" + "=" * 80)
    print("Python实现案例演示")
    print("=" * 80)

    # 注意：以下代码需要有效的API密钥才能运行
    print("\n注意：以下示例需要有效的API密钥")
    print("请设置您的API密钥后运行相关示例")

    # 示例代码（注释掉，需要真实API密钥）
    example_code = '''
# 使用示例：
import os
from core.agno_analysis_report import AgnoIntegratedExample

# 初始化（请替换为您的实际API密钥）
api_key = os.getenv("OPENAI_API_KEY", "your-api-key")
base_url = "https://api.openai.com/v1"  # 或您的自定义端点

# 创建集成实例
agno_example = AgnoIntegratedExample(api_key=api_key, base_url=base_url)

# 1. 基础聊天示例
result = agno_example.basic_chat_example(
    user_id="user123",
    message="你好，请介绍一下Python编程"
)
print("基础聊天结果:", result)

# 2. 流式聊天示例
print("\\n流式聊天响应:")
for chunk in agno_example.streaming_chat_example(
    user_id="user123",
    message="请详细解释异步编程的概念"
):
    print(f"流式数据: {chunk}")

# 3. 多用户并行处理示例
users_data = [
    {"user_id": "user1", "message": "什么是机器学习？"},
    {"user_id": "user2", "message": "解释一下深度学习"},
    {"user_id": "user3", "message": "神经网络是如何工作的？"}
]

parallel_results = agno_example.multi_user_parallel_example(users_data)
print("\\n多用户并行结果:", parallel_results)

# 4. 单独使用各个组件
from core.agno_analysis_report import OpenAIModelIntegration, MultiUserSessionManager

# 模型集成
model = OpenAIModelIntegration(api_key=api_key)
messages = [
    {"role": "system", "content": "你是一个有用的AI助手"},
    {"role": "user", "content": "介绍一下人工智能"}
]
response = model.create_chat_completion(messages)
print("模型响应:", response)

# 会话管理
session_manager = MultiUserSessionManager()
session_id = session_manager.create_session("user456")
session_manager.add_message(session_id, "user", "你好")
session_manager.add_message(session_id, "assistant", "你好！我是AI助手")
messages = session_manager.get_session_messages(session_id)
print("会话消息:", messages)
'''

    print("\n📄 示例代码：")
    print(example_code)


if __name__ == "__main__":
    main()