import os
import sys
import platform
import traceback
import json
import pickle
import datetime
import base64
import asyncio
import threading
import time
import uuid
from threading import Thread
from typing import List, Dict, Optional, Any, Literal, Callable, Union, Coroutine
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from core.agno.db.sqlite.extended_sqlite import ExtendedSqliteDb
from core.agno.db.sqlite.config_data import AgentConfig, ToolConfig, ModelConfig
from core.agno.db.sqlite.runtime_data import RuntimeData, ReasoningStep, ToolCallRecord
from core.agno.db.schemas.memory import UserMemory as AgentMemory
from core.agno.session import AgentSession
from core.agno.db.schemas.evals import EvalRunRecord as AgentEvaluation
from core.agno.db.schemas.knowledge import KnowledgeRow as AgentKnowledge
from core.agno.utils.log import log_debug, log_error, log_info, log_warning


try:
    from core import config
    from core.utilities import filter_text, get_pil_image
    from core.agent.model import LLM_CLASS_DICT, LLM_BASEURL, LLM_BACKEND, AGENT_CLASS_DICT
    from core.agent.memory import Memory
    from core.config import IMG_PATH, PATH, ICONS, _
    from core.engine.flow_engine import TextSpeakEngine
except ImportError:
    print("未找到核心模块，虚拟默认值替代核心模块导入")
    # 虚拟默认值替代核心模块导入
    config = None
    filter_text = lambda x: x
    get_pil_image = lambda x: None
    LLM_CLASS_DICT = {}
    LLM_BASEURL = ""
    LLM_BACKEND = ""
    AGENT_CLASS_DICT = {}
    Memory = lambda agent=None: type('Memory', (), {
        'get_memory_blocks': lambda self: [],
        'connect_agent': lambda self, agent: None,
        'last_input_content': ""
    })()
    IMG_PATH = Path("./images")
    PATH = Path("./")
    ICONS = {}
    _ = lambda x: x
    TextSpeakEngine = None

class ChatEngine:
    """
    聊天引擎类，负责处理聊天逻辑，包括智能体管理、消息处理等
    集成了数据库存储功能，支持配置数据、运行数据、会话数据、记忆数据、评估数据和知识数据
    """
    def __init__(self, config_path: Optional[str] = "autobox_id.db", debug_callback: Optional[Callable] = None, user_id="default"):
        """
        初始化聊天引擎

        Args:
            config_path: 配置文件数据库路径或者数据库配置文件路径，支持sqlite、mysql、postgresql三种数据库格式
            debug_callback: 调试信息回调函数
            user_id: 用户ID
        """
        try:
            # 基础属性初始化
            self.config_path = config_path
            self.debug_callback = debug_callback
            self.user_token = user_id or str(uuid.uuid4())  # 生成默认用户令牌

            # 回调函数初始化
            self.callbacks = {}
            self.on_message_update = None
            self.on_message_stream = None
            self.on_message_complete = None
            self.on_message_image = None

            # 智能体相关初始化
            self.current_agent = None
            self.current_agent_name = None
            self.agents = {}
            self.agent_configs = {}

            # 消息相关初始化
            self.messages = []
            self.processing = False
            self.voice_enabled = False
            self.websearch_enabled = False

            # 会话相关初始化
            self.current_session_id = None
            self.sessions = []

            # 运行时数据初始化
            self.current_run_id = None
            self.runtime_data = []

            # 线程池初始化
            self.executor = ThreadPoolExecutor(max_workers=4)

            # 1. 初始化数据库连接
            self._initialize_database(config_path)

            # 2. 加载配置
            self._load_config()

            # 3. 加载智能体
            self.load_agents()

            # 4. 创建默认智能体（如果不存在）
            self._create_default_agent_if_needed()

            # 5. 初始化语音引擎（如果可用）
            if TextSpeakEngine:
                try:
                    self.voice_engine = TextSpeakEngine()
                except Exception as e:
                    log_error(f"Failed to initialize voice engine: {e}")
                    self.voice_engine = None
            else:
                self.voice_engine = None

            log_info(f"ChatEngine initialized successfully with database: {self.db_file}")

            # 触发初始化完成回调
            self._trigger_callback('session_create', {
                'agent_name': self.current_agent_name,
                'session_config': {
                    'database_path': self.db_file,
                    'user_token': self.user_token,
                    'agents_count': len(self.agents)
                }
            })

        except Exception as e:
            log_error(f"Error initializing ChatEngine: {e}")
            raise


    def __del__(self):
        """析构函数，清理资源"""
        try:
            # 停止处理中的任务
            if hasattr(self, 'processing') and self.processing:
                self.processing = False
                log_debug("Stopping processing during cleanup")

            # 清理线程池
            if hasattr(self, 'executor') and self.executor:
                try:
                    self.executor.shutdown(wait=True)
                    log_debug("Thread pool shutdown completed")
                except Exception as e:
                    log_error(f"Error shutting down thread pool: {e}")

            # 清理语音引擎
            if hasattr(self, 'voice_engine') and self.voice_engine:
                try:
                    self.voice_engine.stop()
                    log_debug("Voice engine stopped")
                except Exception as e:
                    log_error(f"Error stopping voice engine: {e}")

            # 清理数据库连接
            if hasattr(self, 'db') and self.db:
                try:
                    # 关闭数据库连接
                    if hasattr(self.db, 'Session'):
                        self.db.Session.remove()
                    log_debug("Database connections closed")
                except Exception as e:
                    log_error(f"Error closing database connections: {e}")

            log_info("ChatEngine resources cleaned up successfully")
        except Exception as e:
            log_error(f"Error during ChatEngine cleanup: {e}")

    def _register_callbacks(self,
                          # 文本对话回调
                          on_text_stream=None,           # 流式文本输出
                          on_text_complete=None,         # 完整文本输出

                          # 工具调用回调
                          on_tool_call_start=None,       # 工具调用开始
                          on_tool_call_complete=None,    # 工具调用完成
                          on_tool_call_error=None,       # 工具调用错误

                          # 记忆和知识库回调
                          on_memory_update=None,         # 记忆更新
                          on_knowledge_search=None,      # 知识搜索
                          on_knowledge_update=None,      # 知识更新

                          # 多媒体回调
                          on_image_generate=None,        # 图片生成
                          on_image_analyze=None,         # 图片分析
                          on_video_process=None,         # 视频处理
                          on_audio_process=None,         # 音频处理
                          on_file_upload=None,           # 文件上传
                          on_file_process=None,          # 文件处理

                          # 对话生命周期回调
                          on_conversation_start=None,    # 对话开始
                          on_conversation_complete=None, # 对话完成
                          on_conversation_error=None,    # 对话错误

                          # 推理过程回调
                          on_reasoning_start=None,       # 推理开始
                          on_reasoning_step=None,        # 推理步骤
                          on_reasoning_complete=None,    # 推理完成

                          # 系统事件回调
                          on_session_create=None,        # 会话创建
                          on_session_update=None,        # 会话更新
                          on_agent_switch=None,          # 智能体切换
                          on_error=None):                # 错误处理
        """
        注册标准化回调函数，支持文本对话、工具调用、记忆知识库和多媒体处理的回调

        Args:
            # 文本对话回调
            on_text_stream: 流式文本输出回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'text_stream',
                    'content': str,              # 当前文本片段
                    'is_complete': bool,        # 是否完成
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_text_complete: 完整文本输出回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'text_complete',
                    'content': str,              # 完整文本内容
                    'session_id': str,          # 会话ID
                    'metadata': Dict,           # 元数据（tokens, usage等）
                    'timestamp': int            # 时间戳
                }

            # 工具调用回调
            on_tool_call_start: 工具调用开始回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'tool_call_start',
                    'tool_name': str,           # 工具名称
                    'tool_args': Dict,          # 工具参数
                    'tool_call_id': str,        # 工具调用ID
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_tool_call_complete: 工具调用完成回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'tool_call_complete',
                    'tool_name': str,           # 工具名称
                    'tool_call_id': str,        # 工具调用ID
                    'result': Any,              # 工具执行结果
                    'execution_time': float,    # 执行时间
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_tool_call_error: 工具调用错误回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'tool_call_error',
                    'tool_name': str,           # 工具名称
                    'tool_call_id': str,        # 工具调用ID
                    'error': str,               # 错误信息
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            # 记忆和知识库回调
            on_memory_update: 记忆更新回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'memory_update',
                    'action': str,              # 操作类型 (add/update/delete)
                    'memory_id': str,           # 记忆ID
                    'content': str,             # 记忆内容
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_knowledge_search: 知识搜索回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'knowledge_search',
                    'query': str,               # 搜索查询
                    'results': List[Dict],      # 搜索结果
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_knowledge_update: 知识更新回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'knowledge_update',
                    'action': str,              # 操作类型 (add/update/delete)
                    'knowledge_id': str,        # 知识ID
                    'content': Any,             # 知识内容
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            # 多媒体回调
            on_image_generate: 图片生成回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'image_generate',
                    'status': str,              # 状态 (generating/complete/error)
                    'image_data': Any,          # 图片数据 (base64或URL)
                    'metadata': Dict,           # 图片元数据
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_image_analyze: 图片分析回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'image_analyze',
                    'status': str,              # 状态 (analyzing/complete/error)
                    'image_data': Any,          # 图片数据
                    'analysis_result': Dict,    # 分析结果
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_video_process: 视频处理回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'video_process',
                    'status': str,              # 状态 (processing/complete/error)
                    'video_data': Any,          # 视频数据
                    'processing_result': Dict,  # 处理结果
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_audio_process: 音频处理回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'audio_process',
                    'status': str,              # 状态 (processing/complete/error)
                    'audio_data': Any,          # 音频数据
                    'processing_result': Dict,  # 处理结果 (转录、分析等)
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_file_upload: 文件上传回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'file_upload',
                    'status': str,              # 状态 (uploading/complete/error)
                    'file_name': str,           # 文件名
                    'file_size': int,           # 文件大小
                    'file_type': str,           # 文件类型
                    'file_path': str,           # 文件路径
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_file_process: 文件处理回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'file_process',
                    'status': str,              # 状态 (processing/complete/error)
                    'file_path': str,           # 文件路径
                    'processing_result': Dict,  # 处理结果
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            # 对话生命周期回调
            on_conversation_start: 对话开始回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'conversation_start',
                    'session_id': str,          # 会话ID
                    'agent_name': str,          # 智能体名称
                    'user_input': str,          # 用户输入
                    'timestamp': int            # 时间戳
                }

            on_conversation_complete: 对话完成回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'conversation_complete',
                    'session_id': str,          # 会话ID
                    'agent_name': str,          # 智能体名称
                    'total_tokens': int,        # 总token数
                    'execution_time': float,    # 执行时间
                    'message_count': int,       # 消息数量
                    'timestamp': int            # 时间戳
                }

            on_conversation_error: 对话错误回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'conversation_error',
                    'session_id': str,          # 会话ID
                    'error_type': str,          # 错误类型
                    'error_message': str,       # 错误信息
                    'recovery_suggestions': List[str],  # 恢复建议
                    'timestamp': int            # 时间戳
                }

            # 推理过程回调
            on_reasoning_start: 推理开始回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'reasoning_start',
                    'session_id': str,          # 会话ID
                    'reasoning_type': str,      # 推理类型
                    'timestamp': int            # 时间戳
                }

            on_reasoning_step: 推理步骤回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'reasoning_step',
                    'step_number': int,         # 步骤编号
                    'step_content': str,        # 步骤内容
                    'step_type': str,           # 步骤类型
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            on_reasoning_complete: 推理完成回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'reasoning_complete',
                    'total_steps': int,         # 总步骤数
                    'reasoning_result': Dict,   # 推理结果
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }

            # 系统事件回调
            on_session_create: 会话创建回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'session_create',
                    'session_id': str,          # 会话ID
                    'agent_name': str,          # 智能体名称
                    'session_config': Dict,     # 会话配置
                    'timestamp': int            # 时间戳
                }

            on_session_update: 会话更新回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'session_update',
                    'session_id': str,          # 会话ID
                    'update_type': str,         # 更新类型
                    'update_data': Dict,        # 更新数据
                    'timestamp': int            # 时间戳
                }

            on_agent_switch: 智能体切换回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'agent_switch',
                    'from_agent': str,          # 原智能体名称
                    'to_agent': str,            # 目标智能体名称
                    'session_id': str,          # 会话ID
                    'switch_reason': str,       # 切换原因
                    'timestamp': int            # 时间戳
                }

            on_error: 通用错误处理回调
                参数: (event_data: Dict[str, Any])
                event_data 包含: {
                    'type': 'error',
                    'error_code': str,          # 错误代码
                    'error_message': str,       # 错误信息
                    'error_context': Dict,      # 错误上下文
                    'session_id': str,          # 会话ID
                    'timestamp': int            # 时间戳
                }
        """
        # 存储所有回调函数
        self.callbacks = {
            # 文本对话回调
            'text_stream': on_text_stream,
            'text_complete': on_text_complete,

            # 工具调用回调
            'tool_call_start': on_tool_call_start,
            'tool_call_complete': on_tool_call_complete,
            'tool_call_error': on_tool_call_error,

            # 记忆和知识库回调
            'memory_update': on_memory_update,
            'knowledge_search': on_knowledge_search,
            'knowledge_update': on_knowledge_update,

            # 多媒体回调
            'image_generate': on_image_generate,
            'image_analyze': on_image_analyze,
            'video_process': on_video_process,
            'audio_process': on_audio_process,
            'file_upload': on_file_upload,
            'file_process': on_file_process,

            # 对话生命周期回调
            'conversation_start': on_conversation_start,
            'conversation_complete': on_conversation_complete,
            'conversation_error': on_conversation_error,

            # 推理过程回调
            'reasoning_start': on_reasoning_start,
            'reasoning_step': on_reasoning_step,
            'reasoning_complete': on_reasoning_complete,

            # 系统事件回调
            'session_create': on_session_create,
            'session_update': on_session_update,
            'agent_switch': on_agent_switch,
            'error': on_error
        }


        log_debug("Standardized callbacks registered successfully")



    def _trigger_callback(self, callback_type: str, event_data: Dict[str, Any]):
        """
        触发指定类型的回调函数

        Args:
            callback_type: 回调类型 (如 'text_stream', 'tool_call_start' 等)
            event_data: 事件数据
        """
        if not hasattr(self, 'callbacks'):
            log_debug("Callbacks not initialized")
            return

        callback = self.callbacks.get(callback_type)
        if callback and callable(callback):
            try:
                # 确保事件数据包含必需字段
                if 'timestamp' not in event_data:
                    event_data['timestamp'] = int(time.time())
                if 'session_id' not in event_data:
                    event_data['session_id'] = self.current_session_id

                callback(event_data)
                log_debug(f"Triggered callback: {callback_type}")
            except Exception as e:
                log_error(f"Error in callback {callback_type}: {e}")

                # 触发错误回调
                error_callback = self.callbacks.get('error')
                if error_callback and callable(error_callback):
                    error_callback({
                        'type': 'error',
                        'error_code': 'CALLBACK_ERROR',
                        'error_message': str(e),
                        'error_context': {
                            'callback_type': callback_type,
                            'original_event': event_data
                        },
                        'session_id': self.current_session_id,
                        'timestamp': int(time.time())
                    })

    def _initialize_database(self, config_path: str):
        """
        初始化数据库连接

        Args:
            config_path: 数据库配置路径
        """
        try:
            # 设置数据库文件路径
            if config_path.endswith('.json'):
                self.db_file = config_path.replace('.json', '.db')
            else:
                self.db_file = config_path

            # 确保数据库目录存在
            db_path = Path(self.db_file)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # 初始化扩展的 SQLite 数据库
            self.db = ExtendedSqliteDb(db_file=self.db_file)

            log_info(f"Database initialized: {self.db_file}")
        except Exception as e:
            log_error(f"Error initializing database: {e}")
            raise

    def _load_config(self, secret_key=None):
        """
        加载配置数据库

        Args:
            secret_key: 加密密钥(未实现)

        Returns:
            配置字典
        """
        pass

    def _save_config(self,secret_key=None):
        """
        保存配置到数据库

        Args:
            secret_key: 加密密钥(未实现)
        """
        pass

    def _create_default_config(self):
        """创建默认Agent配置"""
        return {
            'agent_id': f"default_agent_{self.user_token}_{int(time.time())}",
            'name': 'Default Agent',
            'model_id': 'gpt-3.5-turbo',
            'model_provider': 'openai',
            'model_kwargs': {
                'temperature': 0.7,
                'max_tokens': 2000
            },
            'instructions': 'You are a helpful AI assistant. Please respond to user queries in a friendly and professional manner.',
            'tools': [],
            'knowledge': None,
            'memory': None,
            'guardrails': [],
            'metadata': {
                'type': 'text',
                'created_by': 'system',
                'description': 'Default agent created by ChatEngine'
            },
            'user_id': self.user_token,
            'status': 'active'
        }

    def _create_default_agent_if_needed(self):
        """如果不存在智能体，则创建默认智能体"""
        try:
            # 检查是否已有智能体
            agent_configs = self.db.get_agent_configs(user_id=self.user_token)

            if not agent_configs:
                # 创建默认智能体配置
                default_config = self._create_default_config()

                # 保存到数据库
                agent_config_obj = AgentConfig.from_dict(default_config)
                self.db.upsert_agent_config(agent_config_obj)

                # 保存到内存
                self.agent_configs['Default Agent'] = default_config

                # 创建智能体实例
                self.create_new_agent('Default Agent', default_config)

                # 设置为当前智能体
                self.select_agent_by_name('Default Agent')

                log_info("Created default agent: Default Agent")
            else:
                # 如果有智能体配置，选择第一个作为当前智能体
                first_config = agent_configs[0]
                config_dict = {
                    'agent_id': first_config.agent_id,
                    'name': first_config.name,
                    'model_id': first_config.model_id,
                    'model_provider': first_config.model_provider,
                    'model_kwargs': first_config.model_kwargs or {},
                    'instructions': first_config.instructions or '',
                    'tools': first_config.tools or [],
                    'knowledge': first_config.knowledge,
                    'memory': first_config.memory,
                    'guardrails': first_config.guardrails or [],
                    'metadata': first_config.metadata or {},
                    'user_id': first_config.user_id
                }

                self.agent_configs[first_config.name] = config_dict
                self.create_new_agent(first_config.name, config_dict)
                self.select_agent_by_name(first_config.name)

                log_info(f"Loaded existing agent: {first_config.name}")

        except Exception as e:
            log_error(f"Error creating default agent: {e}")
            # 即使创建默认智能体失败，也要确保有一个基本的智能体
            try:
                minimal_config = {
                    'name': 'Minimal Agent',
                    'model_id': 'gpt-3.5-turbo',
                    'model_provider': 'openai',
                    'model_kwargs': {},
                    'instructions': 'You are a helpful AI assistant.',
                    'tools': [],
                    'user_id': self.user_token
                }
                self.agent_configs['Minimal Agent'] = minimal_config
                self.create_new_agent('Minimal Agent', minimal_config)
                self.select_agent_by_name('Minimal Agent')
                log_info("Created minimal fallback agent")
            except Exception as fallback_error:
                log_error(f"Failed to create fallback agent: {fallback_error}")
                raise

    def load_agents(self):
        """加载所有智能体,如果默认为空"""
        try:
            # 从数据库加载智能体配置
            agent_configs = self.db.get_agent_configs(user_id=self.user_token)

            self.agents = {}
            self.agent_configs = {}

            for agent_config in agent_configs:
                # 转换为嵌套格式
                config_dict = {
                    'agent_id': agent_config.agent_id,
                    'name': agent_config.name,
                    'model_id': agent_config.model_id,
                    'model_provider': agent_config.model_provider,
                    'model_kwargs': agent_config.model_kwargs or {},
                    'instructions': agent_config.instructions or '',
                    'tools': agent_config.tools or [],
                    'knowledge': agent_config.knowledge,
                    'memory': agent_config.memory,
                    'guardrails': agent_config.guardrails or [],
                    'metadata': agent_config.metadata or {},
                    'user_id': agent_config.user_id
                }

                # 构建嵌套的model结构
                model_dict = {
                    'name': agent_config.model_id,
                    'provider': agent_config.model_provider,
                    'kwargs': agent_config.model_kwargs or {}
                }

                # 获取agent类型
                metadata = agent_config.metadata or {}
                agent_type = metadata.get('type', 'text') if metadata else 'text'

                # 转换为嵌套格式
                nested_config = {
                    'agent_id': agent_config.agent_id,
                    'name': agent_config.name,
                    'type': agent_type,
                    'model': model_dict if model_dict else {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                    'instructions': agent_config.instructions or '',
                    'tools': agent_config.tools or [],
                    'knowledge': agent_config.knowledge,
                    'memory': agent_config.memory,
                    'guardrails': agent_config.guardrails or [],
                    'metadata': metadata,
                    'user_id': agent_config.user_id,
                    'status': agent_config.status or 'active'
                }

                self.agent_configs[agent_config.name] = nested_config

                # 创建智能体实例（如果AGNO框架可用）
                if AGENT_CLASS_DICT and agent_type in AGENT_CLASS_DICT:
                    agent = self.create_new_agent(agent_config.name, nested_config)
                    if agent:
                        self.agents[agent_config.name] = agent

            log_info(f"Loaded {len(self.agents)} agents from database")
        except Exception as e:
            log_error(f"Error loading agents: {e}")

    def select_agent_by_name(self, agent_name):
        """
        通过名称选择智能体

        Args:
            agent_name: 智能体名称

        Returns:
            是否选择成功
        """
        pass

    def create_model_from_dict(self, model_dict):
        """
        根据字典创建model实例

        支持OpenAI、Ollama、DeepSeek、SiliconFlow、OpenRouter等Provider

        Args:
            model_dict: 包含model配置的字典，必须包含:
                - name: 模型名称
                - provider: Provider名称 (openai, ollama, deepseek, siliconflow, openrouter)
                - kwargs: 模型参数字典 (可选)

        Returns:
            model实例或None (创建失败时)

        Example:
            >>> # OpenAI模型
            >>> openai_config = {
            ...     'name': 'gpt-4',
            ...     'provider': 'openai',
            ...     'kwargs': {
            ...         'api_key': 'sk-xxx',
            ...         'temperature': 0.7,
            ...         'max_tokens': 1000
            ...     }
            ... }
            >>> model = engine.create_model_from_dict(openai_config)
            >>>
            >>> # Ollama模型
            >>> ollama_config = {
            ...     'name': 'llama3.1',
            ...     'provider': 'ollama',
            ...     'kwargs': {
            ...         'host': 'http://localhost:11434',
            ...         'temperature': 0.8
            ...     }
            ... }
            >>> model = engine.create_model_from_dict(ollama_config)
        """
        try:
            # 参数验证
            if not model_dict or not isinstance(model_dict, dict):
                log_error("model_dict必须是非空的字典")
                return None

            name = model_dict.get('name')
            provider = model_dict.get('provider', 'openai').lower()
            kwargs = model_dict.get('kwargs', {})

            if not name:
                log_error("model_dict必须包含'name'字段")
                return None

            log_debug(f"Creating model: {name} (provider: {provider})")

            # 根据provider创建对应的模型实例
            if provider == 'openai':
                return self._create_openai_model(name, kwargs)
            elif provider == 'ollama':
                return self._create_ollama_model(name, kwargs)
            elif provider == 'deepseek':
                return self._create_deepseek_model(name, kwargs)
            elif provider == 'siliconflow':
                return self._create_siliconflow_model(name, kwargs)
            elif provider == 'openrouter':
                return self._create_openrouter_model(name, kwargs)
            else:
                log_warning(f"不支持的provider: {provider}，尝试创建Mock模型")
                return self._create_mock_model(name, provider, kwargs)

        except Exception as e:
            log_error(f"创建模型失败: {e}")
            return None

    def _create_openai_model(self, name: str, kwargs: dict):
        """创建OpenAI模型实例"""
        try:
            from core.agno.models.openai.chat import OpenAIChat

            # 提取OpenAI特有的参数
            openai_params = {
                'id': name,
                'name': kwargs.get('name', 'OpenAIChat'),
                'api_key': kwargs.get('api_key'),
                'base_url': kwargs.get('base_url'),
                'organization': kwargs.get('organization'),
                'timeout': kwargs.get('timeout'),
                'max_retries': kwargs.get('max_retries'),
                'temperature': kwargs.get('temperature'),
                'max_tokens': kwargs.get('max_tokens'),
                'max_completion_tokens': kwargs.get('max_completion_tokens'),
                'top_p': kwargs.get('top_p'),
                'frequency_penalty': kwargs.get('frequency_penalty'),
                'presence_penalty': kwargs.get('presence_penalty'),
                'seed': kwargs.get('seed'),
                'stop': kwargs.get('stop'),
                'user': kwargs.get('user'),
                'extra_headers': kwargs.get('extra_headers'),
                'extra_query': kwargs.get('extra_query'),
                'extra_body': kwargs.get('extra_body'),
            }

            # 过滤掉None值
            openai_params = {k: v for k, v in openai_params.items() if v is not None}

            model = OpenAIChat(**openai_params)
            log_debug(f"Created OpenAI model: {name}")
            return model

        except ImportError:
            log_warning("OpenAI库未安装，创建Mock模型")
            return self._create_mock_model(name, 'openai', kwargs)
        except Exception as e:
            log_error(f"创建OpenAI模型失败: {e}")
            return self._create_mock_model(name, 'openai', kwargs)

    def _create_ollama_model(self, name: str, kwargs: dict):
        """创建Ollama模型实例"""
        try:
            from core.agno.models.ollama.chat import Ollama

            # 提取Ollama特有的参数
            ollama_params = {
                'id': name,
                'name': kwargs.get('name', 'Ollama'),
                'host': kwargs.get('host'),
                'timeout': kwargs.get('timeout'),
                'api_key': kwargs.get('api_key'),
                'format': kwargs.get('format'),
                'options': kwargs.get('options'),
                'keep_alive': kwargs.get('keep_alive'),
                'client_params': kwargs.get('client_params'),
            }

            # 过滤掉None值
            ollama_params = {k: v for k, v in ollama_params.items() if v is not None}

            model = Ollama(**ollama_params)
            log_debug(f"Created Ollama model: {name}")
            return model

        except ImportError:
            log_warning("Ollama库未安装，创建Mock模型")
            return self._create_mock_model(name, 'ollama', kwargs)
        except Exception as e:
            log_error(f"创建Ollama模型失败: {e}")
            return self._create_mock_model(name, 'ollama', kwargs)

    def _create_deepseek_model(self, name: str, kwargs: dict):
        """创建DeepSeek模型实例"""
        try:
            from core.agno.models.deepseek.deepseek import DeepSeek

            # 提取DeepSeek特有的参数
            deepseek_params = {
                'id': name,
                'name': kwargs.get('name', 'DeepSeek'),
                'api_key': kwargs.get('api_key'),
                'base_url': kwargs.get('base_url', 'https://api.deepseek.com'),
                'organization': kwargs.get('organization'),
                'timeout': kwargs.get('timeout'),
                'max_retries': kwargs.get('max_retries'),
                'default_headers': kwargs.get('default_headers'),
                'default_query': kwargs.get('default_query'),
                'temperature': kwargs.get('temperature'),
                'max_tokens': kwargs.get('max_tokens'),
                'top_p': kwargs.get('top_p'),
                'frequency_penalty': kwargs.get('frequency_penalty'),
                'presence_penalty': kwargs.get('presence_penalty'),
                'seed': kwargs.get('seed'),
                'stop': kwargs.get('stop'),
                'user': kwargs.get('user'),
                'extra_headers': kwargs.get('extra_headers'),
                'extra_query': kwargs.get('extra_query'),
                'extra_body': kwargs.get('extra_body'),
            }

            # 过滤掉None值
            deepseek_params = {k: v for k, v in deepseek_params.items() if v is not None}

            model = DeepSeek(**deepseek_params)
            log_debug(f"Created DeepSeek model: {name}")
            return model

        except ImportError:
            log_warning("DeepSeek库未安装，创建Mock模型")
            return self._create_mock_model(name, 'deepseek', kwargs)
        except Exception as e:
            log_error(f"创建DeepSeek模型失败: {e}")
            return self._create_mock_model(name, 'deepseek', kwargs)

    def _create_siliconflow_model(self, name: str, kwargs: dict):
        """创建SiliconFlow模型实例"""
        try:
            from core.agno.models.siliconflow.siliconflow import Siliconflow

            # 提取SiliconFlow特有的参数
            siliconflow_params = {
                'id': name,
                'name': kwargs.get('name', 'Siliconflow'),
                'api_key': kwargs.get('api_key'),
                'base_url': kwargs.get('base_url', 'https://api.siliconflow.com/v1'),
                'organization': kwargs.get('organization'),
                'timeout': kwargs.get('timeout'),
                'max_retries': kwargs.get('max_retries'),
                'default_headers': kwargs.get('default_headers'),
                'default_query': kwargs.get('default_query'),
                'temperature': kwargs.get('temperature'),
                'max_tokens': kwargs.get('max_tokens'),
                'top_p': kwargs.get('top_p'),
                'frequency_penalty': kwargs.get('frequency_penalty'),
                'presence_penalty': kwargs.get('presence_penalty'),
                'seed': kwargs.get('seed'),
                'stop': kwargs.get('stop'),
                'user': kwargs.get('user'),
                'extra_headers': kwargs.get('extra_headers'),
                'extra_query': kwargs.get('extra_query'),
                'extra_body': kwargs.get('extra_body'),
            }

            # 过滤掉None值
            siliconflow_params = {k: v for k, v in siliconflow_params.items() if v is not None}

            model = Siliconflow(**siliconflow_params)
            log_debug(f"Created SiliconFlow model: {name}")
            return model

        except ImportError:
            log_warning("SiliconFlow库未安装，创建Mock模型")
            return self._create_mock_model(name, 'siliconflow', kwargs)
        except Exception as e:
            log_error(f"创建SiliconFlow模型失败: {e}")
            return self._create_mock_model(name, 'siliconflow', kwargs)

    def _create_openrouter_model(self, name: str, kwargs: dict):
        """创建OpenRouter模型实例"""
        try:
            from core.agno.models.openrouter.openrouter import OpenRouter

            # 提取OpenRouter特有的参数
            openrouter_params = {
                'id': name,
                'name': kwargs.get('name', 'OpenRouter'),
                'api_key': kwargs.get('api_key'),
                'base_url': kwargs.get('base_url', 'https://openrouter.ai/api/v1'),
                'max_tokens': kwargs.get('max_tokens', 1024),
                'models': kwargs.get('models'),  # fallback models
            }

            # 过滤掉None值
            openrouter_params = {k: v for k, v in openrouter_params.items() if v is not None}

            model = OpenRouter(**openrouter_params)
            log_debug(f"Created OpenRouter model: {name}")
            return model

        except ImportError:
            log_warning("OpenRouter库未安装，创建Mock模型")
            return self._create_mock_model(name, 'openrouter', kwargs)
        except Exception as e:
            log_error(f"创建OpenRouter模型失败: {e}")
            return self._create_mock_model(name, 'openrouter', kwargs)

    def _create_mock_model(self, name: str, provider: str, kwargs: dict):
        """创建Mock模型实例（当对应的Provider库不可用时）"""
        class MockModel:
            def __init__(self, model_id: str, provider: str, **model_kwargs):
                self.id = model_id
                self.name = f"Mock{provider.capitalize()}Model"
                self.provider = provider.capitalize()
                self.kwargs = model_kwargs

            def __str__(self):
                return f"MockModel(id={self.id}, provider={self.provider})"

            def __repr__(self):
                return self.__str__()

            def invoke(self, *args, **kwargs):
                """模拟invoke方法"""
                return MockModelResponse(f"Mock response from {self.provider} model {self.id}")

            async def ainvoke(self, *args, **kwargs):
                """模拟ainvoke方法"""
                return MockModelResponse(f"Mock async response from {self.provider} model {self.id}")

        class MockModelResponse:
            def __init__(self, content: str):
                self.content = content

            def __str__(self):
                return self.content

        mock_model = MockModel(name, provider, **kwargs)
        log_debug(f"Created Mock model: {mock_model}")
        return mock_model

    def create_new_agent(self, agent_name, agent_dict):
        """
        根据配置创建智能体

        Args:
            agent_name: 智能体名称
            agent_dict: 智能体配置字典

        Returns:
            智能体实例
        """
        try:
            # 参数验证
            if not agent_name:
                raise ValueError("agent_name不能为空")
            if not agent_dict:
                raise ValueError("agent_dict不能为空")

            # 确保数据库已连接
            if not self.db:
                if not hasattr(self, '_initialize_database'):
                    log_warning("数据库初始化方法不存在，跳过数据库连接")
                else:
                    log_warning("数据库未连接，尝试重新连接")
                    # 这里可以尝试重新连接数据库

            # 从配置字典中提取参数
            agent_id = agent_dict.get('agent_id') or f"{agent_name}_{int(time.time())}"
            model_config = agent_dict.get('model', {})
            instructions = agent_dict.get('instructions', f"你是{agent_name}，一个有用的AI助手。")
            user_id = agent_dict.get('user_id', self.user_token)
            agent_type = agent_dict.get('type', 'text')
            tools = agent_dict.get('tools', [])
            knowledge = agent_dict.get('knowledge')
            memory = agent_dict.get('memory')
            guardrails = agent_dict.get('guardrails', [])
            metadata = agent_dict.get('metadata', {})

            # 导入AGNO Agent类
            try:
                from core.agno.agent.agent import Agent as AgnoAgent
            except ImportError:
                log_warning("无法导入AGNO框架组件，使用模拟Agent")
                return self._create_mock_agent_from_dict(agent_name, agent_dict)

            # 创建或获取模型
            model_instance = None
            if isinstance(model_config, dict):
                # 使用现有的create_model_from_dict方法
                model_instance = self.create_model_from_dict(model_config)
            elif hasattr(model_config, '__class__'):
                # 如果已经是Model实例
                model_instance = model_config
            elif isinstance(model_config, str):
                # 如果是字符串，创建基本模型配置
                model_dict = {
                    'name': model_config,
                    'provider': 'openai',
                    'kwargs': {}
                }
                model_instance = self.create_model_from_dict(model_dict)

            if model_instance is None:
                log_error("模型创建失败")
                return None

            # 构建Agent创建参数
            agent_kwargs = {
                'agent_id': agent_id,
                'model': model_instance,
                'name': agent_name,
                'instructions': instructions,
                'debug_mode': False
            }

            # 添加可选参数
            if user_id:
                agent_kwargs['user_id'] = user_id

            # 添加工具配置
            if tools:
                agent_kwargs['tools'] = tools

            # 添加记忆配置
            if memory:
                agent_kwargs['memory'] = memory

            # 添加知识库配置
            if knowledge:
                agent_kwargs['knowledge'] = knowledge

            # 添加防护栏配置
            if guardrails:
                agent_kwargs['guardrails'] = guardrails

            # 添加元数据
            if metadata:
                agent_kwargs['metadata'] = metadata

            # 如果数据库可用，添加数据库配置
            if self.db:
                try:
                    # 检查是否有相关的数据库表
                    if hasattr(self.db, 'get_agent_configs'):
                        agent_kwargs['db'] = self.db
                        log_info(f"Agent {agent_id} 将使用数据库存储")
                except Exception as db_ex:
                    log_warning(f"数据库配置检查失败: {db_ex}")

            # 创建Agent实例
            try:
                agent = AgnoAgent(**agent_kwargs)
                log_info(f"成功创建Agent: {agent_name} (ID: {agent_id})")

                # 触发Agent创建回调
                self._trigger_callback('agent_switch', {
                    'from_agent': self.current_agent_name,
                    'to_agent': agent_name,
                    'session_id': self.current_session_id,
                    'switch_reason': 'agent_creation',
                    'agent_id': agent_id
                })

                return agent

            except Exception as agent_ex:
                log_error(f"Agent实例创建失败: {agent_ex}")
                # 如果AGNO Agent创建失败，尝试创建模拟Agent
                return self._create_mock_agent_from_dict(agent_name, agent_dict)

        except Exception as e:
            log_error(f"创建Agent失败: {e}")
            return None

    def _create_mock_agent_from_dict(self, agent_name: str, agent_dict: Dict[str, Any]):
        """
        创建模拟Agent对象（当AGNO框架不可用时）

        Args:
            agent_name (str): Agent名称
            agent_dict (Dict[str, Any]): Agent配置字典

        Returns:
            Any: 模拟Agent对象
        """
        class MockAgent:
            def __init__(self, **kwargs):
                self.agent_id = kwargs.get("agent_id")
                self.name = kwargs.get("name")
                self.model = kwargs.get("model")
                self.instructions = kwargs.get("instructions")
                self.user_id = kwargs.get("user_id")
                self.agent_type = kwargs.get("type", "text")
                self.tools = kwargs.get("tools", [])
                self.knowledge = kwargs.get("knowledge")
                self.memory = kwargs.get("memory")
                self.guardrails = kwargs.get("guardrails", [])
                self.metadata = kwargs.get("metadata", {})
                self.debug_mode = kwargs.get("debug_mode", False)
                self.kwargs = kwargs

            def __str__(self):
                return f"MockAgent(id={self.agent_id}, name={self.name})"

            def __repr__(self):
                return self.__str__()

            def run(self, message, **kwargs):
                """模拟运行方法"""
                return f"Mock response from {self.name}: {message}"

        # 从配置字典中提取参数
        agent_id = agent_dict.get('agent_id') or f"{agent_name}_{int(time.time())}"
        model_config = agent_dict.get('model', {})
        instructions = agent_dict.get('instructions', f"你是{agent_name}，一个有用的AI助手。")
        user_id = agent_dict.get('user_id', self.user_token)

        # 确保agent_id存在
        if not agent_id:
            agent_id = f"mock_agent_{int(time.time())}"

        mock_agent = MockAgent(
            agent_id=agent_id,
            name=agent_name,
            model=model_config,
            instructions=instructions,
            user_id=user_id
        )

        # 设置其他属性
        mock_agent.agent_type = agent_dict.get('type', 'text')
        mock_agent.tools = agent_dict.get('tools', [])
        mock_agent.knowledge = agent_dict.get('knowledge')
        mock_agent.memory = agent_dict.get('memory')
        mock_agent.guardrails = agent_dict.get('guardrails', [])
        mock_agent.metadata = agent_dict.get('metadata', {})
        mock_agent.debug_mode = False

        log_debug(f"Created Mock Agent: {mock_agent}")
        return mock_agent
        

    def update_agent_settings(self, agent_config):
        """
        更新智能体设置

        Args:
            agent_config: 新的智能体配置字典

        Returns:
            更新后的智能体对象
        """
        pass

    def delete_agent_by_name(self, agent_name):
        """
        根据名称删除智能体

        Args:
            agent_name: 智能体名称

        Returns:
            成功与否
        """
        pass

    def get_available_models(self):
        """
        获取当前支持的model模型列表

        Returns:
            模型列表字典
        """
        pass

    def update_agent_model(self, model_dict):
        """
        更新智能体的模型，并保存

        Args:
            model_dict: 模型字典配置字典

        Returns:
            成功与否
        """
        pass


    def list_agent_session(self):
        """
        列出当前agent的历史对话列表

        Args:
            session_id: 会话列表
        """
        pass
    
    def create_new_session(self, session_id=None):
        """
        当前agent创建新的会话记录"""
        pass

    def load_agent_session(self, session_id=None):
        """
        当前agent加载智能体的历史对话

        Args:
            session_id: 会话id
        """
        pass

    def reset_agent_session(self,session_id):
        """
        重置当前智能体session_id对应的会话历史记录

        Returns:
            成功与否
        """
        pass

    def toggle_voice(self):
        """
        当前agent切换语音引擎状态

        Returns:
            新的状态
        """
        pass

    def stop_runing(self):
        """
        当前agent停止当前处理

        Returns:
            操作结果
        """
        pass

    # 知识数据管理方法
    def get_knowledge(self):
        """
        返回当前agent所掌握的知识

        Returns:
            knowledge_data_dict: 知识数据字典
        """
        pass

    # 知识数据管理方法

    def list_knowledge(self):
        """
        获取当前agent知识数据列表

        Returns:
            获取当前智能体的知识列表
        """
        pass    
    def add_knowledge(self, knowledge_data):
        """
        当前agent添加知识数据

        Args:
            knowledge_data: 知识数据

        Returns:
            添加结果knowledge_id
        """
        pass

    def get_knowledge(self, knowledge_id=None):
        """
        当前agent获取知识数据

        Args:
            knowledge_id: 知识ID，为None时获取所有知识

        Returns:
            知识数据列表
        """
        pass


    def get_agent_statistics(self):
        """
        获取当前智能体的统计信息

        Returns:
            统计信息字典
        """
        pass

    def get_database_statistics(self):
        """
        获取数据库统计信息

        Returns:
            数据库统计信息
        """
        pass
