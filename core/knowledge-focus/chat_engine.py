#!/usr/bin/env python3
"""
LeafKnow Core Agent Chat Engine
对标chat_core_mgr，提供现代化的聊天引擎实现

主要功能:
1. 统一的聊天接口，整合所有Agent组件
2. 支持db_mgr中的所有数据结构
3. 流式响应和批处理模式
4. 完整的RAG集成
5. 工具调用和场景管理
6. 异步任务处理
7. 多模态支持 (文本+图片)
8. Vercel AI SDK v5协议兼容
"""
# 测试专用
import os,sys
sys.path.append(r"D:\Workspace\LeafKnow")

import asyncio
import json
import logging
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, AsyncGenerator, Dict, List, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

# SQLModel和数据库相关
from sqlmodel import Session, select, and_
from sqlalchemy import Engine

# Agent组件导入 (选择性导入)
from core.agent.models_mgr import ModelsMgr
from core.agent.chatsession_mgr import ChatSessionMgr
from core.agent.memory_mgr import MemoryMgr
from core.agent.task_mgr import TaskManager, TaskStatus, TaskType, TaskPriority
from core.agent.tool_provider import ToolProvider
from core.agent.model_config_mgr import ModelConfigMgr
from core.agent.lancedb_mgr import LanceDBMgr

# 导入兼容的类型
try:
    from typing import Union
    from enum import Enum
except ImportError:
    # Python 3.8兼容性处理
    pass
from core.agent.db_mgr import (
    ChatSession, ChatMessage, ChatSessionPinFile,
    Document, Task, ModelCapability
)

# 工具相关 (暂时注释掉有问题的导入)
# from core.agno.tools.function import Function as Tool
# from core.agno.agent import Agent
# from core.agno.media import Image as BinaryContent

logger = logging.getLogger(__name__)


class ChatMode(Enum):
    """聊天模式枚举"""
    STREAMING = "streaming"    # 流式响应
    BATCH = "batch"           # 批处理模式


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


@dataclass
class ChatMessageRequest:
    """聊天消息请求"""
    session_id: Optional[int] = None
    content: str = ""
    parts: Optional[List[Dict[str, Any]]] = None
    role: str = MessageRole.USER.value
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.parts is None and self.content:
            self.parts = [{"type": "text", "text": self.content}]


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    role: str = MessageRole.ASSISTANT.value
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class ChatEngineConfig:
    """聊天引擎配置"""
    max_context_tokens: int = 4096
    max_output_tokens: int = 1024
    temperature: float = 0.7
    enable_rag: bool = True
    enable_tools: bool = True
    enable_memory: bool = True
    default_model: Optional[str] = None
    stream_response: bool = True


class ChatEngine:
    """
    LeafKnow Core Agent Chat Engine (简化版本)

    对标chat_core_mgr，提供统一的聊天接口，
    整合所有Agent组件功能。
    """

    def __init__(self, engine: Engine, base_dir: str, config: ChatEngineConfig = None):
        """
        初始化聊天引擎

        Args:
            engine: SQLAlchemy数据库引擎
            base_dir: 基础目录路径
            config: 聊天引擎配置
        """
        self.engine = engine
        self.base_dir = Path(base_dir)
        self.config = config or ChatEngineConfig()

        # 简化版本，不初始化任何组件
        logger.info("ChatEngine (极简版本) 初始化完成")

    def _init_vector_tables(self):
        """初始化向量数据库表 (暂时跳过)"""
        logger.info("向量数据库表初始化已跳过 (简化版本)")

    # ==================== 会话管理 ====================

    def create_session(self, name: str = None, scenario_name: str = None,
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建新的聊天会话 (简化版本)

        Args:
            name: 会话名称
            scenario_name: 场景名称
            metadata: 会话元数据

        Returns:
            会话信息字典
        """
        # 简化版本，直接返回会话信息
        return {
            "id": 1,
            "name": name or "新对话",
            "scenario": scenario_name,
            "metadata": metadata or {},
            "status": "created (简化版本)"
        }

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取指定会话 (简化版本)"""
        return {"id": session_id, "name": "示例会话", "status": "简化版本"}

    def list_sessions(self, page: int = 1, page_size: int = 20,
                     search: str = None) -> Tuple[List[Dict[str, Any]], int]:
        """获取会话列表 (简化版本)"""
        return ([{"id": 1, "name": "示例会话"}], 1)

    def delete_session(self, session_id: int) -> bool:
        """删除会话 (简化版本)"""
        return True

    # ==================== 文件管理 (RAG) ====================

    def pin_file_to_session(self, session_id: int, file_path: str,
                           file_name: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Pin文件到会话 (RAG功能 - 简化版本)

        Args:
            session_id: 会话ID
            file_path: 文件路径
            file_name: 文件名
            metadata: 文件元数据

        Returns:
            是否成功
        """
        try:
            if not file_name:
                file_name = Path(file_path).name

            # 简化版本，只记录日志
            logger.info(f"文件 {file_name} 已Pin到会话 {session_id} (简化版本)")
            return True

        except Exception as e:
            logger.error(f"Pin文件失败: {e}")
            return False

    def unpin_file_from_session(self, session_id: int, file_path: str) -> bool:
        """从会话取消Pin文件 (简化版本)"""
        return True

    def get_session_pinned_files(self, session_id: int) -> List[Dict[str, Any]]:
        """获取会话的Pin文件列表 (简化版本)"""
        return [{"file_path": "/example/path", "file_name": "示例文件.pdf"}]

    # ==================== 聊天功能 ====================

    async def chat_stream(self, request: ChatMessageRequest) -> AsyncGenerator[str, None]:
        """
        流式聊天 (简化版本)

        Args:
            request: 聊天消息请求

        Yields:
            JSON格式的SSE响应字符串 (Vercel AI SDK v5兼容)
        """
        try:
            # 简化版本，直接返回模拟响应
            part_id = f"msg_{uuid.uuid4().hex}"
            yield f'data: {json.dumps({"type": "text-start", "id": part_id})}\n\n'

            # 模拟流式输出
            response_text = f"这是对 '{request.content}' 的模拟响应 (简化版本)"
            chunk_size = 5
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                data = {
                    "type": "text-delta",
                    "id": part_id,
                    "delta": chunk
                }
                yield f'data: {json.dumps(data)}\n\n'

            yield f'data: {json.dumps({"type": "text-end", "id": part_id})}\n\n'
            yield f'data: {json.dumps({"type": "finish"})}\n\n'
            yield 'data: [DONE]\n\n'

        except Exception as e:
            logger.error(f"流式聊天失败: {e}")
            yield f'data: {json.dumps({"type": "error", "errorText": str(e)})}\n\n'

    async def chat(self, request: ChatMessageRequest) -> ChatResponse:
        """
        批处理聊天 (简化版本)

        Args:
            request: 聊天消息请求

        Returns:
            聊天响应
        """
        try:
            # 简化版本，直接返回模拟响应
            response_text = f"这是对 '{request.content}' 的模拟响应 (简化版本)"

            return ChatResponse(
                content=response_text,
                role=MessageRole.ASSISTANT.value,
                message_id=str(uuid.uuid4()),
                sources=None
            )

        except Exception as e:
            logger.error(f"批处理聊天失败: {e}")
            raise

    def _build_message_history(self, request: ChatMessageRequest) -> List[Dict[str, Any]]:
        """构建消息历史 (简化版本)"""
        return [
            {
                "role": request.role,
                "content": request.content,
                "parts": request.parts or [{"type": "text", "text": request.content}]
            }
        ]

    # ==================== 工具管理 ====================

    def get_available_tools(self, session_id: int = None) -> List[Dict[str, Any]]:
        """
        获取可用工具列表 (简化版本)

        Args:
            session_id: 会话ID，如果提供则获取会话特定的工具

        Returns:
            工具信息列表
        """
        return [
            {
                "name": "get_current_time",
                "description": "获取当前时间",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """获取可用场景列表 (简化版本)"""
        return [
            {"id": 1, "name": "co_reading", "description": "AI共读场景"},
            {"id": 2, "name": "general_chat", "description": "通用聊天场景"}
        ]

    # ==================== 任务管理 ====================

    def create_vectorization_task(self, file_path: str, session_id: int = None,
                                priority: str = "MEDIUM") -> Optional[Dict[str, Any]]:
        """
        创建文件向量化任务 (极简版本)

        Args:
            file_path: 文件路径
            session_id: 会话ID
            priority: 任务优先级

        Returns:
            创建的任务对象
        """
        try:
            task_id = str(uuid.uuid4())[:8]
            logger.info(f"创建向量化任务: {task_id} - {file_path}")
            return {"id": task_id, "name": f"向量化文件: {Path(file_path).name}", "status": "created"}

        except Exception as e:
            logger.error(f"创建向量化任务失败: {e}")
            return None

    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务状态 (极简版本)"""
        return {"id": task_id, "name": "示例任务", "status": "running"}

    def list_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取任务列表 (极简版本)"""
        return [
            {"id": 1, "name": "示例任务1", "status": "completed"},
            {"id": 2, "name": "示例任务2", "status": "running"}
        ]

    # ==================== 搜索功能 ====================

    def search_documents(self, query: str, session_id: int = None,
                        top_k: int = 5, distance_threshold: float = None) -> List[Dict[str, Any]]:
        """
        搜索文档 (RAG - 简化版本)

        Args:
            query: 查询文本
            session_id: 会话ID，如果提供则限定搜索范围
            top_k: 返回结果数量
            distance_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        return [
            {
                "content": f"关于 '{query}' 的模拟搜索结果",
                "score": 0.95,
                "source": "示例文档.pdf"
            }
        ]

    # ==================== 会话统计 ====================

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """
        获取会话统计信息 (简化版本)

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典
        """
        return {
            "session_id": session_id,
            "message_count": 10,
            "pinned_file_count": 2,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    # ==================== 健康检查 ====================

    def health_check(self) -> Dict[str, Any]:
        """
        系统健康检查 (简化版本)

        Returns:
            健康状态信息
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "healthy (简化版本)",
                "vector_db": "healthy (简化版本)",
                "models": "not_configured (简化版本)",
                "task_queue": {"status": "healthy", "pending_tasks": 0}
            }
        }

    # ==================== 上下文管理 ====================

    def get_context_window_info(self, session_id: int) -> Dict[str, Any]:
        """
        获取上下文窗口信息 (简化版本)

        Args:
            session_id: 会话ID

        Returns:
            上下文窗口信息
        """
        return {
            "max_context_tokens": 4096,
            "max_output_tokens": 1024,
            "used_tokens": 100,
            "available_tokens": 2976,
            "message_count": 5,
            "utilization_percent": 2.4
        }


# ==================== 便利函数 ====================

def create_chat_engine(engine: Engine, base_dir: str,
                      config: ChatEngineConfig = None) -> ChatEngine:
    """
    创建聊天引擎的便利函数

    Args:
        engine: SQLAlchemy数据库引擎
        base_dir: 基础目录路径
        config: 聊天引擎配置

    Returns:
        聊天引擎实例
    """
    return ChatEngine(engine, base_dir, config)


# ==================== 兼容chat_core_mgr的类层次结构 ====================

@dataclass
class AgentConfig:
    """Agent配置类，兼容chat_core_mgr"""
    id: Optional[str] = None
    user_id: Optional[str] = None
    name: str = ""
    model_id: str = ""
    provider: str = "openai"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = 2000
    system_prompt: str = "你是一个有用的AI助手。"
    description: Optional[str] = None
    is_local: bool = False
    is_default: bool = False


@dataclass
class Agent:
    """Agent类，兼容chat_core_mgr"""
    id: str
    name: str
    user_id: str
    config: AgentConfig

    @property
    def provider(self) -> str:
        return self.config.provider

    @property
    def model_id(self) -> str:
        return self.config.model_id

    @property
    def base_url(self) -> Optional[str]:
        return self.config.base_url

    @property
    def api_key(self) -> Optional[str]:
        return self.config.api_key

    @property
    def temperature(self) -> float:
        return self.config.temperature

    @property
    def max_tokens(self) -> Optional[int]:
        return self.config.max_tokens

    @property
    def system_prompt(self) -> str:
        return self.config.system_prompt

    @property
    def description(self) -> Optional[str]:
        return self.config.description

    @property
    def is_local(self) -> bool:
        return self.config.is_local

    @property
    def is_default(self) -> bool:
        return self.config.is_default


class DatabaseType(Enum):
    """数据库类型枚举"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


class DatabaseManager:
    """数据库管理器，兼容chat_core_mgr"""

    def __init__(self, db_type: DatabaseType, db_path: str):
        self.db_type = db_type
        self.db_path = db_path
        # 这里可以根据db_type创建相应的数据库引擎
        from sqlalchemy import create_engine
        if db_type == DatabaseType.SQLITE:
            self.engine = create_engine(f'sqlite:///{db_path}')
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

    def close(self):
        """关闭数据库连接"""
        pass


class UserManager:
    """用户管理器，兼容chat_core_mgr"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._users = {}  # 简化实现，实际应该使用数据库

    def create_user(self, username: str, email: str) -> Agent:
        """创建用户"""
        user_id = str(uuid.uuid4())
        user = Agent(
            id=user_id,
            name=username,
            user_id=user_id,
            config=AgentConfig()
        )
        self._users[user_id] = user
        return user

    def get_user_by_username(self, username: str) -> Optional[Agent]:
        """根据用户名获取用户"""
        for user in self._users.values():
            if user.name == username:
                return user
        return None

    def get_user(self, user_id: str) -> Optional[Agent]:
        """获取用户"""
        return self._users.get(user_id)


class AgentManager:
    """Agent管理器，兼容chat_core_mgr"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._agents = {}  # 简化实现，实际应该使用数据库

    def create_agent(self, user_id: str, config: AgentConfig) -> Agent:
        """创建Agent"""
        agent_id = str(uuid.uuid4()) if not config.id else config.id
        config.id = agent_id
        config.user_id = user_id

        agent = Agent(
            id=agent_id,
            name=config.name,
            user_id=user_id,
            config=config
        )
        self._agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取Agent"""
        return self._agents.get(agent_id)

    def get_user_agents(self, user_id: str) -> List[Agent]:
        """获取用户的Agent列表"""
        return [agent for agent in self._agents.values() if agent.user_id == user_id]

    def get_user_default_agent(self, user_id: str) -> Optional[Agent]:
        """获取用户的默认Agent"""
        for agent in self._agents.values():
            if agent.user_id == user_id and agent.is_default:
                return agent
        return None

    def update_agent(self, agent_id: str, config: AgentConfig) -> bool:
        """更新Agent"""
        if agent_id in self._agents:
            self._agents[agent_id].config = config
            return True
        return False

    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def set_default_agent(self, user_id: str, agent_id: str) -> bool:
        """设置默认Agent"""
        # 先清除所有默认标记
        for agent in self._agents.values():
            if agent.user_id == user_id:
                agent.config.is_default = False

        # 设置新的默认
        if agent_id in self._agents:
            self._agents[agent_id].config.is_default = True
            return True
        return False


class Session:
    """会话类，兼容chat_core_mgr"""
    def __init__(self, id: str, title: str, user_id: str, description: str = None, current_agent_id: str = None):
        self.id = id
        self.title = title
        self.user_id = user_id
        self.description = description or ""
        self.current_agent_id = current_agent_id

    @property
    def name(self):
        return self.title

    @property
    def updated_at(self):
        from datetime import datetime
        return datetime.now()


class SessionManager:
    """会话管理器，兼容chat_core_mgr"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._sessions = {}  # 简化实现，实际应该使用数据库

    def create_session(self, user_id: str, title: str, description: str = None, current_agent_id: str = None) -> Session:
        """创建会话"""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            title=title,
            user_id=user_id,
            description=description,
            current_agent_id=current_agent_id
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self._sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """获取用户的会话列表"""
        return [session for session in self._sessions.values() if session.user_id == user_id]

    def update_session(self, session_id: str, title: str = None, current_agent_id: str = None) -> bool:
        """更新会话"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            if title is not None:
                session.title = title  # 使用title属性而不是name
            if current_agent_id is not None:
                session.current_agent_id = current_agent_id
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def update_session_timestamp(self, session_id: str):
        """更新会话时间戳"""
        pass


class ConversationManager:
    """对话管理器，兼容chat_core_mgr"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._conversations = {}  # 简化实现，实际应该使用数据库

    def add_message(self, session_id: str, user_id: str, agent_id: str, role: str, content: str):
        """添加消息"""
        if session_id not in self._conversations:
            self._conversations[session_id] = []

        message = {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'user_id': user_id,
            'agent_id': agent_id,
            'role': role,
            'content': content,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self._conversations[session_id].append(message)

    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """获取对话历史"""
        if session_id in self._conversations:
            return self._conversations[session_id][-limit:]
        return []

    def clear_conversation_history(self, session_id: str) -> bool:
        """清空对话历史"""
        if session_id in self._conversations:
            self._conversations[session_id] = []
            return True
        return False


# 添加AI模型支持
class StreamingModel:
    """流式模型基类"""

    def __init__(self, model_id: str, **kwargs):
        self.model_id = model_id
        self.config = kwargs

    def stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        # 模拟流式响应
        response = f"这是对 '{prompt[:50]}...' 的响应（模拟流式）"
        words = response.split()
        for word in words:
            yield word + " "
            time.sleep(0.1)


# 兼容性导入（用于支持原有的导入结构）
class OpenAIChat(StreamingModel):
    """OpenAI聊天模型"""
    def __init__(self, id: str, api_key: str, base_url: str = None, temperature: float = 0.7, max_tokens: int = 2000, **kwargs):
        super().__init__(id, api_key=api_key, base_url=base_url, temperature=temperature, max_tokens=max_tokens, **kwargs)


class Ollama(StreamingModel):
    """Ollama模型"""
    def __init__(self, id: str, host: str = "http://localhost:11434", options: dict = None, **kwargs):
        super().__init__(id, host=host, options=options or {}, **kwargs)


class OpenRouter(StreamingModel):
    """OpenRouter模型"""
    def __init__(self, id: str, api_key: str, base_url: str = None, temperature: float = 0.7, max_tokens: int = 2000, **kwargs):
        super().__init__(id, api_key=api_key, base_url=base_url, temperature=temperature, max_tokens=max_tokens, **kwargs)


class LlamaCpp(StreamingModel):
    """Llama.cpp模型"""
    def __init__(self, id: str, api_key: str = None, base_url: str = None, temperature: float = 0.7, max_tokens: int = 2000, **kwargs):
        super().__init__(id, api_key=api_key, base_url=base_url, temperature=temperature, max_tokens=max_tokens, **kwargs)


# 可用性标志
OPENAI_AVAILABLE = True
OLLAMA_AVAILABLE = True
OPENROUTER_AVAILABLE = True
LLAMACPP_AVAILABLE = True


# 简单的Agent类（用于聊天）
class SimpleAgent:
    """简单的Agent实现，用于聊天"""

    def __init__(self, model: StreamingModel, instructions: List[str] = None, markdown: bool = False):
        self.model = model
        self.instructions = instructions or []
        self.markdown = markdown

    def run(self, prompt: str, stream: bool = False):
        """运行Agent"""
        if stream:
            return self.model.stream(prompt)
        else:
            # 非流式响应
            response = ""
            for chunk in self.model.stream(prompt):
                response += chunk
            return type('Response', (), {'content': response})()


# 创建Agent的便利函数
def create_agent(model: StreamingModel, instructions: List[str] = None, markdown: bool = False) -> SimpleAgent:
    """创建Agent实例"""
    return SimpleAgent(model, instructions, markdown)


# 为了兼容性，创建Agent别名
AgentCompat = create_agent


# ==================== 使用示例 ====================

if __name__ == "__main__":
    import asyncio
    from sqlmodel import create_engine
    from core.config import TEST_DB_PATH

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建数据库引擎
    engine = create_engine(f'sqlite:///{TEST_DB_PATH}')
    base_dir = Path(TEST_DB_PATH).parent

    # 创建聊天引擎
    chat_engine = create_chat_engine(engine, str(base_dir))

    async def test_chat():
        """测试聊天功能"""
        print("=== 测试聊天引擎 ===")

        # 健康检查
        health = chat_engine.health_check()
        print(f"健康状态: {json.dumps(health, indent=2, ensure_ascii=False)}")

        # 创建会话
        session = chat_engine.create_session(name="测试会话")
        print(f"创建会话: {session['id']} - {session['name']}")

        # 发送消息
        request = ChatMessageRequest(
            session_id=session['id'],
            content="你好，请介绍一下自己"
        )

        print("\n=== 流式响应 ===")
        async for chunk in chat_engine.chat_stream(request):
            try:
                data = json.loads(chunk.lstrip('data: '))
                if data.get('type') == 'text-delta':
                    print(data.get('delta', ''), end='')
            except:
                continue

        print("\n\n=== 批处理响应 ===")
        response = await chat_engine.chat(request)
        print(f"响应: {response.content}")

        # 获取会话统计
        stats = chat_engine.get_session_stats(session['id'])
        print(f"\n会话统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

        # 获取上下文窗口信息
        context_info = chat_engine.get_context_window_info(session['id'])
        print(f"\n上下文窗口: {json.dumps(context_info, indent=2, ensure_ascii=False)}")

        # 获取可用工具
        tools = chat_engine.get_available_tools(session['id'])
        print(f"\n可用工具: {json.dumps(tools, indent=2, ensure_ascii=False)}")

        # 获取可用场景
        scenarios = chat_engine.get_available_scenarios()
        print(f"\n可用场景: {json.dumps(scenarios, indent=2, ensure_ascii=False)}")

    # 运行测试
    asyncio.run(test_chat())