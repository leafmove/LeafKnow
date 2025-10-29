#!/usr/bin/env python3
"""
增强版Agno AI聊天应用
支持多用户、Agent管理、Model管理，数据库存储配置
支持SQLite、MySQL、PostgreSQL数据库
"""

import asyncio
import json
import os
import sys
import subprocess
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, AsyncGenerator, Dict, List, Any, TYPE_CHECKING, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

# 数据库相关导入
try:
    import psycopg2
    from psycopg2 import sql
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


# 数据库类型枚举
class DatabaseType(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


@dataclass
class UserConfig:
    """用户配置类"""
    username: str
    email: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class AgentConfig:
    """Agent配置类"""
    user_id: str
    name: str
    model_id: str
    provider: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = 2000
    system_prompt: str = "你是一个有用的AI助手，请用简洁明了的语言回答问题。"
    description: str = ""
    is_local: bool = False
    is_default: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SessionConfig:
    """会话配置类"""
    user_id: str
    title: str
    description: Optional[str] = None
    current_agent_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_type: DatabaseType = DatabaseType.SQLITE,
                 db_path: str = "autobox_id.db",
                 host: str = None, port: int = None,
                 username: str = None, password: str = None,
                 database: str = None):
        self.db_type = db_type
        self.db_path = Path(db_path) if db_type == DatabaseType.SQLITE else None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.connection = None
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        if self.db_type == DatabaseType.SQLITE:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        elif self.db_type == DatabaseType.MYSQL:
            if not PYMYSQL_AVAILABLE:
                raise ImportError("pymysql未安装，请运行: pip install pymysql")
            self.connection = pymysql.connect(
                host=self.host or 'localhost',
                port=self.port or 3306,
                user=self.username or 'root',
                password=self.password or '',
                database=self.database or 'autobox',
                charset='utf8mb4'
            )
        elif self.db_type == DatabaseType.POSTGRESQL:
            if not PSYCOPG2_AVAILABLE:
                raise ImportError("psycopg2未安装，请运行: pip install psycopg2-binary")
            self.connection = psycopg2.connect(
                host=self.host or 'localhost',
                port=self.port or 5432,
                user=self.username or 'postgres',
                password=self.password or '',
                database=self.database or 'autobox'
            )

        self.create_tables()

    def create_tables(self):
        """创建数据表"""
        cursor = self.connection.cursor()

        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        # Agent配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                model_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                base_url TEXT,
                api_key TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER,
                system_prompt TEXT DEFAULT '你是一个有用的AI助手，请用简洁明了的语言回答问题。',
                description TEXT,
                is_local BOOLEAN DEFAULT FALSE,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE (user_id, name)
            )
        ''')

        # 会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                current_agent_id TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (current_agent_id) REFERENCES agents (id) ON DELETE SET NULL
            )
        ''')

        # 对话历史表（添加session_id支持）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                role TEXT NOT NULL,  -- 'user' or 'assistant'
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
        ''')

        # 为现有数据库添加session_id列（如果不存在）
        try:
            cursor.execute("ALTER TABLE conversations ADD COLUMN session_id TEXT")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        except:
            # 列可能已存在，忽略错误
            pass

        self.connection.commit()
        cursor.close()

    def get_connection(self):
        """获取数据库连接"""
        if self.connection is None:
            self.init_database()
        return self.connection

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: tuple = (), fetch: bool = False, fetch_all: bool = False):
        """执行查询"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if fetch:
                if fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                conn.commit()
                return result
            else:
                conn.commit()
                return cursor.rowcount if cursor.rowcount is not None else 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


class UserManager:
    """用户管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_user(self, username: str, email: str = None) -> UserConfig:
        """创建用户"""
        user_id = str(uuid.uuid4())
        query = '''
            INSERT INTO users (id, username, email, created_at, is_active)
            VALUES (?, ?, ?, ?, ?)
        '''
        params = (user_id, username, email, datetime.now(), True)

        self.db.execute_query(query, params)
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> Optional[UserConfig]:
        """获取用户"""
        query = 'SELECT * FROM users WHERE id = ? AND is_active = ?'
        row = self.db.execute_query(query, (user_id, True), fetch=True)
        if row:
            return UserConfig(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                created_at=datetime.fromisoformat(row['created_at']),
                is_active=bool(row['is_active'])
            )
        return None

    def get_user_by_username(self, username: str) -> Optional[UserConfig]:
        """根据用户名获取用户"""
        query = 'SELECT * FROM users WHERE username = ? AND is_active = ?'
        row = self.db.execute_query(query, (username, True), fetch=True)
        if row:
            return UserConfig(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                created_at=datetime.fromisoformat(row['created_at']),
                is_active=bool(row['is_active'])
            )
        return None

    def list_users(self) -> List[UserConfig]:
        """列出所有用户"""
        query = 'SELECT * FROM users WHERE is_active = ? ORDER BY created_at DESC'
        rows = self.db.execute_query(query, (True,), fetch=True, fetch_all=True)
        if not rows:
            return []
        return [UserConfig(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                created_at=datetime.fromisoformat(row['created_at']),
                is_active=bool(row['is_active'])
            ) for row in rows]

    def update_user(self, user_id: str, username: str = None, email: str = None) -> bool:
        """更新用户信息"""
        updates = []
        params = []

        if username:
            updates.append("username = ?")
            params.append(username)
        if email:
            updates.append("email = ?")
            params.append(email)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(user_id)

        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        affected_rows = self.db.execute_query(query, tuple(params))
        return affected_rows > 0

    def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        query = 'UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?'
        affected_rows = self.db.execute_query(query, (False, datetime.now(), user_id))
        return affected_rows > 0


class AgentManager:
    """Agent配置管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_agent(self, user_id: str, config: AgentConfig) -> AgentConfig:
        """创建Agent配置"""
        agent_id = config.id or str(uuid.uuid4())
        query = '''
            INSERT INTO agents (id, user_id, name, model_id, provider, base_url, api_key,
                               temperature, max_tokens, system_prompt, description,
                               is_local, is_default, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            agent_id, user_id, config.name, config.model_id, config.provider,
            config.base_url, config.api_key, config.temperature, config.max_tokens,
            config.system_prompt, config.description, config.is_local, config.is_default,
            datetime.now(), datetime.now()
        )

        self.db.execute_query(query, params)
        return self.get_agent(agent_id)

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置"""
        query = 'SELECT * FROM agents WHERE id = ?'
        row = self.db.execute_query(query, (agent_id,), fetch=True)
        if row:
            return AgentConfig(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                model_id=row['model_id'],
                provider=row['provider'],
                base_url=row['base_url'],
                api_key=row['api_key'],
                temperature=float(row['temperature']),
                max_tokens=row['max_tokens'],
                system_prompt=row['system_prompt'],
                description=row['description'],
                is_local=bool(row['is_local']),
                is_default=bool(row['is_default']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None

    def get_user_agents(self, user_id: str) -> List[AgentConfig]:
        """获取用户的所有Agent"""
        query = 'SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC'
        rows = self.db.execute_query(query, (user_id,), fetch=True, fetch_all=True)
        if not rows:
            return []
        return [AgentConfig(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                model_id=row['model_id'],
                provider=row['provider'],
                base_url=row['base_url'],
                api_key=row['api_key'],
                temperature=float(row['temperature']),
                max_tokens=row['max_tokens'],
                system_prompt=row['system_prompt'],
                description=row['description'],
                is_local=bool(row['is_local']),
                is_default=bool(row['is_default']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ) for row in rows]

    def get_user_default_agent(self, user_id: str) -> Optional[AgentConfig]:
        """获取用户的默认Agent"""
        query = 'SELECT * FROM agents WHERE user_id = ? AND is_default = ?'
        row = self.db.execute_query(query, (user_id, True), fetch=True)
        if row:
            return AgentConfig(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                model_id=row['model_id'],
                provider=row['provider'],
                base_url=row['base_url'],
                api_key=row['api_key'],
                temperature=float(row['temperature']),
                max_tokens=row['max_tokens'],
                system_prompt=row['system_prompt'],
                description=row['description'],
                is_local=bool(row['is_local']),
                is_default=bool(row['is_default']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None

    def update_agent(self, agent_id: str, config: AgentConfig) -> bool:
        """更新Agent配置"""
        query = '''
            UPDATE agents
            SET name = ?, model_id = ?, provider = ?, base_url = ?, api_key = ?,
                temperature = ?, max_tokens = ?, system_prompt = ?, description = ?,
                is_local = ?, is_default = ?, updated_at = ?
            WHERE id = ?
        '''
        params = (
            config.name, config.model_id, config.provider, config.base_url, config.api_key,
            config.temperature, config.max_tokens, config.system_prompt, config.description,
            config.is_local, config.is_default, datetime.now(), agent_id
        )

        affected_rows = self.db.execute_query(query, params)
        return affected_rows > 0

    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        query = 'DELETE FROM agents WHERE id = ?'
        affected_rows = self.db.execute_query(query, (agent_id,))
        return affected_rows > 0

    def set_default_agent(self, user_id: str, agent_id: str) -> bool:
        """设置默认Agent"""
        # 先清除该用户的其他默认Agent
        clear_query = 'UPDATE agents SET is_default = ? WHERE user_id = ? AND id != ?'
        self.db.execute_query(clear_query, (False, user_id, agent_id))

        # 设置新的默认Agent
        set_query = 'UPDATE agents SET is_default = ?, updated_at = ? WHERE user_id = ? AND id = ?'
        affected_rows = self.db.execute_query(set_query, (True, datetime.now(), user_id, agent_id))
        return affected_rows > 0


class SessionManager:
    """会话管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_session(self, user_id: str, title: str, description: str = None, current_agent_id: str = None) -> SessionConfig:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        query = '''
            INSERT INTO sessions (id, user_id, title, description, current_agent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (session_id, user_id, title, description, current_agent_id, datetime.now(), datetime.now())
        self.db.execute_query(query, params)
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Optional[SessionConfig]:
        """获取会话"""
        query = 'SELECT * FROM sessions WHERE id = ?'
        row = self.db.execute_query(query, (session_id,), fetch=True)
        if row:
            return SessionConfig(
                id=row['id'],
                user_id=row['user_id'],
                title=row['title'],
                description=row['description'],
                current_agent_id=row['current_agent_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None

    def get_user_sessions(self, user_id: str) -> List[SessionConfig]:
        """获取用户的所有会话"""
        query = 'SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC'
        rows = self.db.execute_query(query, (user_id,), fetch=True, fetch_all=True)
        if not rows:
            return []
        return [SessionConfig(
                id=row['id'],
                user_id=row['user_id'],
                title=row['title'],
                description=row['description'],
                current_agent_id=row['current_agent_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ) for row in rows]

    def update_session(self, session_id: str, title: str = None, description: str = None, current_agent_id: str = None) -> bool:
        """更新会话信息"""
        updates = []
        params = []

        if title:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if current_agent_id:
            updates.append("current_agent_id = ?")
            params.append(current_agent_id)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(session_id)

        query = f'UPDATE sessions SET {", ".join(updates)} WHERE id = ?'
        affected_rows = self.db.execute_query(query, tuple(params))
        return affected_rows > 0

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        query = 'DELETE FROM sessions WHERE id = ?'
        affected_rows = self.db.execute_query(query, (session_id,))
        return affected_rows > 0

    def update_session_timestamp(self, session_id: str) -> bool:
        """更新会话最后活动时间"""
        query = 'UPDATE sessions SET updated_at = ? WHERE id = ?'
        affected_rows = self.db.execute_query(query, (datetime.now(), session_id))
        return affected_rows > 0


class ConversationManager:
    """对话历史管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_message(self, session_id: str, user_id: str, agent_id: str, role: str, content: str) -> str:
        """添加消息到对话历史"""
        message_id = str(uuid.uuid4())
        query = '''
            INSERT INTO conversations (id, session_id, user_id, agent_id, role, content)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (message_id, session_id, user_id, agent_id, role, content)
        self.db.execute_query(query, params)
        return message_id

    def add_message_legacy(self, user_id: str, agent_id: str, role: str, content: str) -> str:
        """添加消息到对话历史（兼容旧版本，不使用session_id）"""
        message_id = str(uuid.uuid4())
        query = '''
            INSERT INTO conversations (id, user_id, agent_id, role, content)
            VALUES (?, ?, ?, ?, ?)
        '''
        params = (message_id, user_id, agent_id, role, content)
        self.db.execute_query(query, params)
        return message_id

    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """获取会话的对话历史"""
        query = '''
            SELECT role, content, timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        rows = self.db.execute_query(query, (session_id, limit), fetch=True, fetch_all=True)
        if not rows:
            return []
        return [{"role": row['role'], "content": row['content'], "timestamp": row['timestamp']} for row in rows]

    def get_conversation_history_legacy(self, user_id: str, agent_id: str, limit: int = 50) -> List[Dict]:
        """获取对话历史（兼容旧版本）"""
        query = '''
            SELECT role, content, timestamp
            FROM conversations
            WHERE user_id = ? AND agent_id = ? AND session_id IS NULL
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        rows = self.db.execute_query(query, (user_id, agent_id, limit), fetch=True, fetch_all=True)
        if not rows:
            return []
        return [{"role": row['role'], "content": row['content'], "timestamp": row['timestamp']} for row in rows]

    def clear_conversation_history(self, session_id: str = None, user_id: str = None, agent_id: str = None) -> bool:
        """清除对话历史"""
        if session_id:
            query = 'DELETE FROM conversations WHERE session_id = ?'
            params = (session_id,)
        elif user_id and agent_id:
            query = 'DELETE FROM conversations WHERE user_id = ? AND agent_id = ? AND session_id IS NULL'
            params = (user_id, agent_id)
        elif user_id:
            query = 'DELETE FROM conversations WHERE user_id = ? AND session_id IS NULL'
            params = (user_id,)
        else:
            return False

        affected_rows = self.db.execute_query(query, params)
        return affected_rows > 0


# 安全的导入函数
def safe_import(module_path, class_name, error_message=None):
    """安全导入模块和类"""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError, TypeError) as e:
        if error_message:
            print(f"[警告] {error_message}")
        else:
            print(f"[警告] 无法导入 {module_path}.{class_name}: {str(e)}")
        return None

# Agno imports
Agent = safe_import("core.agno.agent", "Agent")
OpenAIChat = safe_import("core.agno.models.openai", "OpenAIChat")
OPENAI_AVAILABLE = OpenAIChat is not None

# 尝试导入各种模型支持
OpenRouter = safe_import("core.agno.models.openrouter", "OpenRouter", "openrouter支持不可用")
OPENROUTER_AVAILABLE = OpenRouter is not None

Ollama = safe_import("core.agno.models.ollama", "Ollama", "ollama库未安装，Ollama模型功能不可用")
OLLAMA_AVAILABLE = Ollama is not None

# llama.cpp 模型支持
LlamaCpp = safe_import("core.agno.models.llama_cpp", "LlamaCpp", "llama.cpp库未安装或Python版本不兼容，LlamaCpp模型功能不可用")
LLAMACPP_AVAILABLE = LlamaCpp is not None


class EnhancedChatApp:
    """增强版AI聊天应用"""

    def __init__(self):
        # 初始化数据库
        self.db_manager = DatabaseManager(DatabaseType.SQLITE, "autobox_id.db")
        self.user_manager = UserManager(self.db_manager)
        self.agent_manager = AgentManager(self.db_manager)
        self.session_manager = SessionManager(self.db_manager)
        self.conversation_manager = ConversationManager(self.db_manager)

        # 当前用户、Agent和会话
        self.current_user_id = None
        self.current_agent_id = None
        self.current_session_id = None

        # 应用设置
        self.use_streaming = True

        # 初始化
        self._init_default_data()

    def _init_default_data(self):
        """初始化默认数据"""
        # 创建默认用户（如果不存在）
        default_user = self.user_manager.get_user_by_username("default")
        if not default_user:
            default_user = self.user_manager.create_user("default", "default@autobox.com")

        self.current_user_id = default_user.id

        # 为默认用户创建默认Agent（如果不存在）
        default_agents = self.agent_manager.get_user_agents(default_user.id)
        if not default_agents:
            # OpenAI GPT-4o-mini
            openai_config = AgentConfig(
                user_id=default_user.id,
                name="OpenAI GPT-4o-mini",
                model_id="gpt-4o-mini",
                provider="openai",
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY") or "your_api_key_here",
                description="OpenAI的GPT-4o mini模型，适合一般对话",
                is_default=True
            )
            self.agent_manager.create_agent(default_user.id, openai_config)

            # Ollama 模型（如果可用）
            if OLLAMA_AVAILABLE:
                ollama_config = AgentConfig(
                    user_id=default_user.id,
                    name="Ollama Default",
                    model_id="llama3.2:latest",
                    provider="ollama",
                    base_url="http://localhost:11434",
                    is_local=True,
                    description="本地Ollama模型"
                )
                self.agent_manager.create_agent(default_user.id, ollama_config)

            # Llama.cpp 模型（如果可用）
            if LLAMACPP_AVAILABLE:
                llama_config = AgentConfig(
                    user_id=default_user.id,
                    name="Llama.cpp Local",
                    model_id="local-model",
                    provider="llamacpp",
                    base_url="http://127.0.0.1:8080/v1",
                    is_local=True,
                    description="本地Llama.cpp服务器模型"
                )
                self.agent_manager.create_agent(default_user.id, llama_config)

        # 设置当前Agent
        current_agent = self.agent_manager.get_user_default_agent(default_user.id)
        if current_agent:
            self.current_agent_id = current_agent.id

        # 创建默认会话（如果不存在）
        user_sessions = self.session_manager.get_user_sessions(default_user.id)
        if not user_sessions:
            # 创建默认会话
            default_session = self.session_manager.create_session(
                default_user.id,
                "默认会话",
                "默认的对话会话",
                self.current_agent_id
            )
            self.current_session_id = default_session.id
        else:
            # 使用最近的会话
            self.current_session_id = user_sessions[0].id
            # 更新会话的当前Agent
            if self.current_agent_id:
                self.session_manager.update_session(self.current_session_id, current_agent_id=self.current_agent_id)

    def create_agent_instance(self, config: AgentConfig):
        """根据配置创建模型实例"""
        try:
            if config.provider == "openai":
                if not OPENAI_AVAILABLE:
                    raise ImportError("OpenAI库未安装")

                if not config.api_key or config.api_key == "your_api_key_here":
                    print(f"[错误] OpenAI API密钥未设置或使用默认值")
                    return None

                return OpenAIChat(
                    id=config.model_id,
                    api_key=config.api_key,
                    base_url=config.base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

            elif config.provider == "ollama":
                if not OLLAMA_AVAILABLE:
                    raise ImportError("Ollama库未安装")

                options = {
                    "temperature": config.temperature,
                }
                if config.max_tokens:
                    options["num_predict"] = config.max_tokens

                return Ollama(
                    id=config.model_id,
                    host=config.base_url,
                    options=options,
                )

            elif config.provider == "openrouter":
                if not OPENROUTER_AVAILABLE:
                    raise ImportError("OpenRouter支持不可用")

                return OpenRouter(
                    id=config.model_id,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    base_url=config.base_url,
                )

            elif config.provider == "llamacpp":
                if not LLAMACPP_AVAILABLE:
                    raise ImportError("llama.cpp支持不可用")

                return LlamaCpp(
                    id=config.model_id,
                    api_key=config.api_key or "not-required",
                    base_url=config.base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

            else:
                raise ValueError(f"不支持的提供商: {config.provider}")

        except Exception as e:
            print(f"[错误] 创建模型实例失败: {str(e)}")
            return None

    def get_current_agent(self):
        """获取当前Agent实例"""
        if not self.current_agent_id:
            return None

        agent_config = self.agent_manager.get_agent(self.current_agent_id)
        if not agent_config:
            return None

        return self.create_agent_instance(agent_config)

    def user_management_menu(self) -> bool:
        """用户管理菜单"""
        print("\n" + "=" * 60)
        print("用户管理")
        print("=" * 60)

        users = self.user_manager.list_users()
        current_user = self.user_manager.get_user(self.current_user_id)

        print(f"当前用户: {current_user.username} ({current_user.id})")
        print("\n用户列表:")
        for i, user in enumerate(users, 1):
            current_mark = " [当前]" if user.id == self.current_user_id else ""
            print(f"{i:2d}. {user.username}{current_mark} ({user.email})")

        print(f"{len(users)+1:2d}. 添加用户")
        print(f"{len(users)+2:2d}. 切换用户")
        print(f"{len(users)+3:2d}. 编辑用户")
        print(f"{len(users)+4:2d}. 删除用户")
        print("0. 返回")

        try:
            choice = input("\n请选择操作: ").strip()
            choice_num = int(choice)

            if choice_num == 0:
                return False
            elif 1 <= choice_num <= len(users):
                # 切换用户
                selected_user = users[choice_num - 1]
                self.current_user_id = selected_user.id
                # 更新当前Agent
                current_agent = self.agent_manager.get_user_default_agent(selected_user.id)
                if current_agent:
                    self.current_agent_id = current_agent.id
                else:
                    self.current_agent_id = None
                print(f"[OK] 已切换到用户: {selected_user.username}")
                return True
            elif choice_num == len(users) + 1:
                # 添加用户
                self.add_user_dialog()
                return True
            elif choice_num == len(users) + 2:
                # 切换用户
                self.switch_user_dialog()
                return True
            elif choice_num == len(users) + 3:
                # 编辑用户
                self.edit_user_dialog()
                return True
            elif choice_num == len(users) + 4:
                # 删除用户
                self.delete_user_dialog()
                return True
            else:
                print("[错误] 无效选择")
                return True
        except ValueError:
            print("[错误] 请输入有效数字")
            return True

    def add_user_dialog(self):
        """添加用户对话框"""
        print("\n添加新用户")
        print("-" * 30)

        username = input("用户名: ").strip()
        if not username:
            print("[错误] 用户名不能为空")
            return

        # 检查用户名是否已存在
        existing_user = self.user_manager.get_user_by_username(username)
        if existing_user:
            print("[错误] 用户名已存在")
            return

        email = input("邮箱 (可选): ").strip() or None

        try:
            new_user = self.user_manager.create_user(username, email)
            print(f"[OK] 用户已创建: {new_user.username}")

            # 询问是否切换到新用户
            switch = input("是否切换到新用户? (y/n): ").strip().lower()
            if switch == 'y':
                self.current_user_id = new_user.id
                # 更新当前Agent
                current_agent = self.agent_manager.get_user_default_agent(new_user.id)
                if current_agent:
                    self.current_agent_id = current_agent.id
                else:
                    self.current_agent_id = None
                print(f"[OK] 已切换到用户: {new_user.username}")
        except Exception as e:
            print(f"[错误] 创建用户失败: {str(e)}")

    def switch_user_dialog(self):
        """切换用户对话框"""
        print("\n切换用户")
        print("-" * 30)

        if not self.current_user_id:
            print("[错误] 当前没有选择用户")
            return

        users = self.user_manager.list_users()
        other_users = [u for u in users if u.id != self.current_user_id]

        if not other_users:
            print("[错误] 没有其他用户")
            return

        print("选择要切换的用户:")
        for i, user in enumerate(other_users, 1):
            print(f"{i}. {user.username} ({user.email})")

        try:
            choice = int(input("选择用户编号: ")) - 1
            if 0 <= choice < len(other_users):
                selected_user = other_users[choice]
                self.current_user_id = selected_user.id
                # 更新当前Agent
                current_agent = self.agent_manager.get_user_default_agent(selected_user.id)
                if current_agent:
                    self.current_agent_id = current_agent.id
                else:
                    self.current_agent_id = None
                print(f"[OK] 已切换到用户: {selected_user.username}")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def edit_user_dialog(self):
        """编辑用户对话框"""
        print("\n编辑用户")
        print("-" * 30)

        users = self.user_manager.list_users()
        if not users:
            print("[错误] 没有用户")
            return

        print("选择要编辑的用户:")
        for i, user in enumerate(users, 1):
            current_mark = " [当前]" if user.id == self.current_user_id else ""
            print(f"{i}. {user.username}{current_mark} ({user.email})")

        try:
            choice = int(input("选择用户编号: ")) - 1
            if 0 <= choice < len(users):
                selected_user = users[choice]

                new_username = input(f"新用户名 [{selected_user.username}]: ").strip() or selected_user.username
                new_email = input(f"新邮箱 [{selected_user.email}]: ").strip() or selected_user.email

                if new_username == selected_user.username and new_email == selected_user.email:
                    print("[提示] 没有修改")
                    return

                if self.user_manager.update_user(selected_user.id, new_username, new_email):
                    print(f"[OK] 用户已更新: {new_username}")
                else:
                    print("[错误] 更新用户失败")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def delete_user_dialog(self):
        """删除用户对话框"""
        print("\n删除用户")
        print("-" * 30)
        print("⚠️  警告：此操作将删除用户及其所有配置和对话历史")

        users = self.user_manager.list_users()
        if not users:
            print("[错误] 没有用户")
            return

        # 不允许删除当前用户
        other_users = [u for u in users if u.id != self.current_user_id]
        if not other_users:
            print("[错误] 没有其他用户可删除")
            return

        print("选择要删除的用户:")
        for i, user in enumerate(other_users, 1):
            print(f"{i}. {user.username} ({user.email})")

        try:
            choice = int(input("选择用户编号: ")) - 1
            if 0 <= choice < len(other_users):
                selected_user = other_users[choice]

                confirm = input(f"确认删除用户 {selected_user.username}? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    if self.user_manager.delete_user(selected_user.id):
                        print(f"[OK] 用户已删除: {selected_user.username}")
                    else:
                        print("[错误] 删除用户失败")
                else:
                    print("[提示] 操作已取消")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def agent_management_menu(self) -> bool:
        """Agent管理菜单"""
        print("\n" + "=" * 60)
        print("Agent管理")
        print("=" * 60)

        current_user = self.user_manager.get_user(self.current_user_id)
        agents = self.agent_manager.get_user_agents(current_user.id)
        current_agent = self.agent_manager.get_agent(self.current_agent_id) if self.current_agent_id else None

        print(f"当前用户: {current_user.username}")
        if current_agent:
            print(f"当前Agent: {current_agent.name} ({current_agent.provider})")
        else:
            print("当前Agent: 未设置")

        print("\nAgent列表:")
        for i, agent in enumerate(agents, 1):
            current_mark = " [当前]" if agent.id == self.current_agent_id else ""
            default_mark = " [默认]" if agent.is_default else ""
            local_mark = " [本地]" if agent.is_local else ""
            print(f"{i:2d}. {agent.name}{current_mark}{default_mark}{local_mark} ({agent.provider}: {agent.model_id})")

        print(f"{len(agents)+1:2d}. 添加Agent")
        print(f"{len(agents)+2:2d}. 切换Agent")
        print(f"{len(agents)+3:2d}. 编辑Agent")
        print(f"{len(agents)+4:2d}. 删除Agent")
        print(f"{len(agents)+5:2d}. 设置默认Agent")
        print("0. 返回")

        try:
            choice = input("\n请选择操作: ").strip()
            choice_num = int(choice)

            if choice_num == 0:
                return False
            elif 1 <= choice_num <= len(agents):
                # 切换Agent
                selected_agent = agents[choice_num - 1]
                self.current_agent_id = selected_agent.id
                print(f"[OK] 已切换到Agent: {selected_agent.name}")
                return True
            elif choice_num == len(agents) + 1:
                # 添加Agent
                self.add_agent_dialog()
                return True
            elif choice_num == len(agents) + 2:
                # 切换Agent
                self.switch_agent_dialog()
                return True
            elif choice_num == len(agents) + 3:
                # 编辑Agent
                self.edit_agent_dialog()
                return True
            elif choice_num == len(agents) + 4:
                # 删除Agent
                self.delete_agent_dialog()
                return True
            elif choice_num == len(agents) + 5:
                # 设置默认Agent
                self.set_default_agent_dialog()
                return True
            else:
                print("[错误] 无效选择")
                return True
        except ValueError:
            print("[错误] 请输入有效数字")
            return True

    def add_agent_dialog(self):
        """添加Agent对话框"""
        print("\n添加新Agent")
        print("-" * 30)

        current_user = self.user_manager.get_user(self.current_user_id)

        name = input("Agent名称: ").strip()
        if not name:
            print("[错误] Agent名称不能为空")
            return

        # 检查名称是否已存在
        existing_agents = self.agent_manager.get_user_agents(current_user.id)
        if any(agent.name == name for agent in existing_agents):
            print("[错误] Agent名称已存在")
            return

        model_id = input("模型ID: ").strip()
        if not model_id:
            print("[错误] 模型ID不能为空")
            return

        print("\n支持的提供商:")
        providers = []
        if OPENAI_AVAILABLE:
            providers.append("openai")
        if OLLAMA_AVAILABLE:
            providers.append("ollama")
        if OPENROUTER_AVAILABLE:
            providers.append("openrouter")
        if LLAMACPP_AVAILABLE:
            providers.append("llamacpp")

        for i, provider in enumerate(providers, 1):
            print(f"{i}. {provider}")

        if not providers:
            print("[错误] 没有可用的模型提供商")
            return

        try:
            provider_choice = int(input("选择提供商: ")) - 1
            if 0 <= provider_choice < len(providers):
                provider = providers[provider_choice]
            else:
                print("[错误] 无效选择")
                return
        except ValueError:
            print("[错误] 请输入有效数字")
            return

        base_url = input("Base URL (可选): ").strip() or None
        api_key = input("API Key (可选): ").strip() or None

        try:
            temperature = float(input("Temperature [0.7]: ").strip() or "0.7")
            max_tokens = int(input("Max Tokens [2000]: ").strip() or "2000")
        except ValueError:
            print("[错误] 参数格式错误，使用默认值")
            temperature = 0.7
            max_tokens = 2000

        system_prompt = input(f"系统提示词 [默认]: ").strip() or "你是一个有用的AI助手，请用简洁明了的语言回答问题。"
        description = input("Agent描述 (可选): ").strip() or ""

        is_local = provider in ["ollama", "llamacpp"]

        # 检查是否是第一个Agent（自动设为默认）
        is_default = len(existing_agents) == 0

        try:
            new_config = AgentConfig(
                user_id=current_user.id,
                name=name,
                model_id=model_id,
                provider=provider,
                base_url=base_url,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                description=description,
                is_local=is_local,
                is_default=is_default
            )

            new_agent = self.agent_manager.create_agent(current_user.id, new_config)
            print(f"[OK] Agent已创建: {new_agent.name}")

            # 如果是第一个Agent或用户选择，自动切换
            if is_default or input("是否切换到新Agent? (y/n): ").strip().lower() == 'y':
                self.current_agent_id = new_agent.id
                print(f"[OK] 已切换到Agent: {new_agent.name}")

        except Exception as e:
            print(f"[错误] 创建Agent失败: {str(e)}")

    def edit_agent_dialog(self):
        """编辑Agent对话框"""
        print("\n编辑Agent")
        print("-" * 30)

        current_user = self.user_manager.get_user(self.current_user_id)
        agents = self.agent_manager.get_user_agents(current_user.id)

        if not agents:
            print("[错误] 没有Agent")
            return

        print("选择要编辑的Agent:")
        for i, agent in enumerate(agents, 1):
            current_mark = " [当前]" if agent.id == self.current_agent_id else ""
            default_mark = " [默认]" if agent.is_default else ""
            print(f"{i}. {agent.name}{current_mark}{default_mark}")

        try:
            choice = int(input("选择Agent编号: ")) - 1
            if 0 <= choice < len(agents):
                selected_agent = agents[choice]

                print(f"\n编辑Agent: {selected_agent.name}")
                print("-" * 20)

                new_name = input(f"名称 [{selected_agent.name}]: ").strip() or selected_agent.name
                new_model_id = input(f"模型ID [{selected_agent.model_id}]: ").strip() or selected_agent.model_id
                new_base_url = input(f"Base URL [{selected_agent.base_url}]: ").strip() or selected_agent.base_url
                new_api_key = input(f"API Key [已设置]: ").strip() or selected_agent.api_key

                try:
                    new_temperature = float(input(f"Temperature [{selected_agent.temperature}]: ").strip() or str(selected_agent.temperature))
                    new_max_tokens = int(input(f"Max Tokens [{selected_agent.max_tokens}]: ").strip() or str(selected_agent.max_tokens))
                except ValueError:
                    print("[错误] 参数格式错误，保持原值")
                    new_temperature = selected_agent.temperature
                    new_max_tokens = selected_agent.max_tokens

                new_system_prompt = input(f"系统提示词 [{selected_agent.system_prompt[:50]}...]: ").strip() or selected_agent.system_prompt
                new_description = input(f"描述 [{selected_agent.description}]: ").strip() or selected_agent.description

                if (new_name == selected_agent.name and
                    new_model_id == selected_agent.model_id and
                    new_base_url == selected_agent.base_url and
                    new_api_key == selected_agent.api_key and
                    new_temperature == selected_agent.temperature and
                    new_max_tokens == selected_agent.max_tokens and
                    new_system_prompt == selected_agent.system_prompt and
                    new_description == selected_agent.description):
                    print("[提示] 没有修改")
                    return

                # 创建更新的配置
                updated_config = AgentConfig(
                    id=selected_agent.id,
                    user_id=selected_agent.user_id,
                    name=new_name,
                    model_id=new_model_id,
                    provider=selected_agent.provider,
                    base_url=new_base_url,
                    api_key=new_api_key,
                    temperature=new_temperature,
                    max_tokens=new_max_tokens,
                    system_prompt=new_system_prompt,
                    description=new_description,
                    is_local=selected_agent.is_local,
                    is_default=selected_agent.is_default
                )

                if self.agent_manager.update_agent(selected_agent.id, updated_config):
                    print(f"[OK] Agent已更新: {new_name}")
                else:
                    print("[错误] 更新Agent失败")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def delete_agent_dialog(self):
        """删除Agent对话框"""
        print("\n删除Agent")
        print("-" * 30)
        print("⚠️  警告：此操作将删除Agent及其所有对话历史")

        current_user = self.user_manager.get_user(self.current_user_id)
        agents = self.agent_manager.get_user_agents(current_user.id)

        if len(agents) <= 1:
            print("[错误] 至少需要保留一个Agent")
            return

        # 不允许删除当前Agent
        other_agents = [a for a in agents if a.id != self.current_agent_id]
        if not other_agents:
            print("[错误] 无法删除唯一的Agent")
            return

        print("选择要删除的Agent:")
        for i, agent in enumerate(other_agents, 1):
            print(f"{i}. {agent.name} ({agent.provider}: {agent.model_id})")

        try:
            choice = int(input("选择Agent编号: ")) - 1
            if 0 <= choice < len(other_agents):
                selected_agent = other_agents[choice]

                confirm = input(f"确认删除Agent {selected_agent.name}? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    if self.agent_manager.delete_agent(selected_agent.id):
                        print(f"[OK] Agent已删除: {selected_agent.name}")

                        # 如果删除的是默认Agent，设置另一个为默认
                        if selected_agent.is_default:
                            remaining_agents = self.agent_manager.get_user_agents(current_user.id)
                            if remaining_agents:
                                first_agent = remaining_agents[0]
                                self.agent_manager.set_default_agent(current_user.id, first_agent.id)
                                print(f"[提示] 已设置 {first_agent.name} 为默认Agent")
                    else:
                        print("[错误] 删除Agent失败")
                else:
                    print("[提示] 操作已取消")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def set_default_agent_dialog(self):
        """设置默认Agent对话框"""
        print("\n设置默认Agent")
        print("-" * 30)

        current_user = self.user_manager.get_user(self.current_user_id)
        agents = self.agent_manager.get_user_agents(current_user.id)

        if not agents:
            print("[错误] 没有Agent")
            return

        current_default = None
        print("选择默认Agent:")
        for i, agent in enumerate(agents, 1):
            if agent.is_default:
                current_default = agent
            current_mark = " [当前默认]" if agent.is_default else ""
            current_mark += " [当前Agent]" if agent.id == self.current_agent_id else ""
            print(f"{i}. {agent.name}{current_mark}")

        try:
            choice = int(input("选择Agent编号: ")) - 1
            if 0 <= choice < len(agents):
                selected_agent = agents[choice]

                if selected_agent.id == current_default.id if current_default else None:
                    print("[提示] 该Agent已经是默认Agent")
                    return

                if self.agent_manager.set_default_agent(current_user.id, selected_agent.id):
                    print(f"[OK] 已设置 {selected_agent.name} 为默认Agent")
                else:
                    print("[错误] 设置失败")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def session_management_menu(self) -> bool:
        """会话管理菜单"""
        print("\n" + "=" * 60)
        print("会话管理")
        print("=" * 60)

        current_user = self.user_manager.get_user(self.current_user_id)
        sessions = self.session_manager.get_user_sessions(current_user.id)
        current_session = self.session_manager.get_session(self.current_session_id) if self.current_session_id else None

        print(f"当前用户: {current_user.username}")
        if current_session:
            current_agent = self.agent_manager.get_agent(current_session.current_agent_id) if current_session.current_agent_id else None
            agent_name = current_agent.name if current_agent else "未设置"
            print(f"当前会话: {current_session.title} (Agent: {agent_name})")
        else:
            print("当前会话: 未设置")

        print("\n会话列表:")
        for i, session in enumerate(sessions, 1):
            current_mark = " [当前]" if session.id == self.current_session_id else ""
            current_agent = self.agent_manager.get_agent(session.current_agent_id) if session.current_agent_id else None
            agent_name = current_agent.name if current_agent else "未设置"
            print(f"{i:2d}. {session.title}{current_mark} (Agent: {agent_name})")

        print(f"{len(sessions)+1:2d}. 新建会话")
        print(f"{len(sessions)+2:2d}. 切换会话")
        print(f"{len(sessions)+3:2d}. 编辑会话")
        print(f"{len(sessions)+4:2d}. 删除会话")
        print("0. 返回")

        try:
            choice = input("\n请选择操作: ").strip()
            choice_num = int(choice)

            if choice_num == 0:
                return False
            elif 1 <= choice_num <= len(sessions):
                # 切换会话
                selected_session = sessions[choice_num - 1]
                self.current_session_id = selected_session.id
                # 更新当前Agent
                if selected_session.current_agent_id:
                    self.current_agent_id = selected_session.current_agent_id
                print(f"[OK] 已切换到会话: {selected_session.title}")
                return True
            elif choice_num == len(sessions) + 1:
                # 新建会话
                self.create_session_dialog()
                return True
            elif choice_num == len(sessions) + 2:
                # 切换会话
                self.switch_session_dialog()
                return True
            elif choice_num == len(sessions) + 3:
                # 编辑会话
                self.edit_session_dialog()
                return True
            elif choice_num == len(sessions) + 4:
                # 删除会话
                self.delete_session_dialog()
                return True
            else:
                print("[错误] 无效选择")
                return True
        except ValueError:
            print("[错误] 请输入有效数字")
            return True

    def create_session_dialog(self):
        """创建新会话对话框"""
        print("\n创建新会话")
        print("-" * 30)

        current_user = self.user_manager.get_user(self.current_user_id)

        title = input("会话标题: ").strip()
        if not title:
            print("[错误] 会话标题不能为空")
            return

        # 检查标题是否已存在
        existing_sessions = self.session_manager.get_user_sessions(current_user.id)
        if any(session.title == title for session in existing_sessions):
            print("[错误] 会话标题已存在")
            return

        description = input("会话描述 (可选): ").strip() or None

        # 选择Agent
        agents = self.agent_manager.get_user_agents(current_user.id)
        if not agents:
            print("[错误] 没有可用的Agent")
            return

        print("\n选择会话Agent:")
        for i, agent in enumerate(agents, 1):
            default_mark = " [默认]" if agent.is_default else ""
            print(f"{i}. {agent.name}{default_mark} ({agent.provider}: {agent.model_id})")

        try:
            agent_choice = int(input("选择Agent编号: ")) - 1
            if 0 <= agent_choice < len(agents):
                selected_agent = agents[agent_choice]
            else:
                print("[错误] 无效选择")
                return
        except ValueError:
            print("[错误] 请输入有效数字")
            return

        try:
            new_session = self.session_manager.create_session(
                current_user.id,
                title,
                description,
                selected_agent.id
            )
            print(f"[OK] 会话已创建: {new_session.title}")

            # 询问是否切换到新会话
            switch = input("是否切换到新会话? (y/n): ").strip().lower()
            if switch == 'y':
                self.current_session_id = new_session.id
                self.current_agent_id = selected_agent.id
                print(f"[OK] 已切换到会话: {new_session.title}")

        except Exception as e:
            print(f"[错误] 创建会话失败: {str(e)}")

    def switch_session_dialog(self):
        """切换会话对话框"""
        print("\n切换会话")
        print("-" * 30)

        if not self.current_session_id:
            print("[错误] 当前没有选择会话")
            return

        current_user = self.user_manager.get_user(self.current_user_id)
        sessions = self.session_manager.get_user_sessions(current_user.id)
        other_sessions = [s for s in sessions if s.id != self.current_session_id]

        if not other_sessions:
            print("[错误] 没有其他会话")
            return

        print("选择要切换的会话:")
        for i, session in enumerate(other_sessions, 1):
            current_agent = self.agent_manager.get_agent(session.current_agent_id) if session.current_agent_id else None
            agent_name = current_agent.name if current_agent else "未设置"
            print(f"{i}. {session.title} (Agent: {agent_name})")

        try:
            choice = int(input("选择会话编号: ")) - 1
            if 0 <= choice < len(other_sessions):
                selected_session = other_sessions[choice]
                self.current_session_id = selected_session.id
                # 更新当前Agent
                if selected_session.current_agent_id:
                    self.current_agent_id = selected_session.current_agent_id
                print(f"[OK] 已切换到会话: {selected_session.title}")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def edit_session_dialog(self):
        """编辑会话对话框"""
        print("\n编辑会话")
        print("-" * 30)

        current_user = self.user_manager.get_user(self.current_user_id)
        sessions = self.session_manager.get_user_sessions(current_user.id)

        if not sessions:
            print("[错误] 没有会话")
            return

        print("选择要编辑的会话:")
        for i, session in enumerate(sessions, 1):
            current_mark = " [当前]" if session.id == self.current_session_id else ""
            print(f"{i}. {session.title}{current_mark}")

        try:
            choice = int(input("选择会话编号: ")) - 1
            if 0 <= choice < len(sessions):
                selected_session = sessions[choice]

                new_title = input(f"新标题 [{selected_session.title}]: ").strip() or selected_session.title
                new_description = input(f"新描述 [{selected_session.description}]: ").strip() or selected_session.description

                # 选择Agent
                agents = self.agent_manager.get_user_agents(current_user.id)
                if not agents:
                    print("[错误] 没有可用的Agent")
                    return

                print("\n选择会话Agent:")
                current_agent = self.agent_manager.get_agent(selected_session.current_agent_id) if selected_session.current_agent_id else None
                current_agent_index = agents.index(current_agent) if current_agent and current_agent in agents else 0

                for i, agent in enumerate(agents, 1):
                    default_mark = " [默认]" if agent.is_default else ""
                    current_mark = " [当前]" if agent.id == selected_session.current_agent_id else ""
                    print(f"{i}. {agent.name}{default_mark}{current_mark}")

                try:
                    agent_choice = int(input(f"选择Agent编号 [{current_agent_index + 1}]: ") or str(current_agent_index + 1)) - 1
                    if 0 <= agent_choice < len(agents):
                        selected_agent = agents[agent_choice]
                    else:
                        print("[错误] 无效选择")
                        return
                except ValueError:
                    print("[错误] 请输入有效数字")
                    return

                if (new_title == selected_session.title and
                    new_description == selected_session.description and
                    selected_agent.id == selected_session.current_agent_id):
                    print("[提示] 没有修改")
                    return

                if self.session_manager.update_session(selected_session.id, new_title, new_description, selected_agent.id):
                    print(f"[OK] 会话已更新: {new_title}")

                    # 如果编辑的是当前会话，更新当前Agent
                    if selected_session.id == self.current_session_id:
                        self.current_agent_id = selected_agent.id
                else:
                    print("[错误] 更新会话失败")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def delete_session_dialog(self):
        """删除会话对话框"""
        print("\n删除会话")
        print("-" * 30)
        print("⚠️  警告：此操作将删除会话及其所有对话历史")

        current_user = self.user_manager.get_user(self.current_user_id)
        sessions = self.session_manager.get_user_sessions(current_user.id)

        if len(sessions) <= 1:
            print("[错误] 至少需要保留一个会话")
            return

        # 不允许删除当前会话
        other_sessions = [s for s in sessions if s.id != self.current_session_id]
        if not other_sessions:
            print("[错误] 无法删除唯一的会话")
            return

        print("选择要删除的会话:")
        for i, session in enumerate(other_sessions, 1):
            current_agent = self.agent_manager.get_agent(session.current_agent_id) if session.current_agent_id else None
            agent_name = current_agent.name if current_agent else "未设置"
            print(f"{i}. {session.title} (Agent: {agent_name})")

        try:
            choice = int(input("选择会话编号: ")) - 1
            if 0 <= choice < len(other_sessions):
                selected_session = other_sessions[choice]

                confirm = input(f"确认删除会话 {selected_session.title}? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    if self.session_manager.delete_session(selected_session.id):
                        print(f"[OK] 会话已删除: {selected_session.title}")
                    else:
                        print("[错误] 删除会话失败")
                else:
                    print("[提示] 操作已取消")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def switch_agent_in_session(self):
        """在当前会话中切换Agent"""
        if not self.current_session_id:
            print("[错误] 当前没有选择会话")
            return

        current_user = self.user_manager.get_user(self.current_user_id)
        agents = self.agent_manager.get_user_agents(current_user.id)

        if not agents:
            print("[错误] 没有可用的Agent")
            return

        print("\n切换会话Agent")
        print("-" * 30)

        current_session = self.session_manager.get_session(self.current_session_id)
        print(f"当前会话: {current_session.title}")

        current_agent = self.agent_manager.get_agent(self.current_agent_id) if self.current_agent_id else None
        print(f"当前Agent: {current_agent.name if current_agent else '未设置'}")

        print("\n选择新的Agent:")
        for i, agent in enumerate(agents, 1):
            current_mark = " [当前]" if agent.id == self.current_agent_id else ""
            default_mark = " [默认]" if agent.is_default else ""
            print(f"{i}. {agent.name}{current_mark}{default_mark} ({agent.provider}: {agent.model_id})")

        try:
            choice = int(input("选择Agent编号: ")) - 1
            if 0 <= choice < len(agents):
                selected_agent = agents[choice]

                # 更新会话的当前Agent
                if self.session_manager.update_session(self.current_session_id, current_agent_id=selected_agent.id):
                    self.current_agent_id = selected_agent.id
                    print(f"[OK] 已切换到Agent: {selected_agent.name}")
                else:
                    print("[错误] 切换Agent失败")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def chat_non_streaming(self, user_prompt: str) -> str:
        """非流式聊天"""
        agent = self.get_current_agent()
        if not agent:
            return "[错误] 没有可用的Agent"

        try:
            agent_instance = self.create_agent_instance(agent)
            if not agent_instance:
                return "[错误] 创建模型实例失败"

            agent_obj = Agent(
                model=agent_instance,
                instructions=[agent.system_prompt],
                markdown=True,
            )

            response = agent_obj.run(user_prompt)
            return response.content if response.content else "抱歉，我没有收到有效回复。"
        except Exception as e:
            return f"[错误] 聊天失败: {str(e)}"

    def chat_streaming(self, user_prompt: str):
        """流式聊天"""
        agent = self.get_current_agent()
        if not agent:
            yield "[错误] 没有可用的Agent"
            return

        try:
            agent_instance = self.create_agent_instance(agent)
            if not agent_instance:
                yield "[错误] 创建模型实例失败"
                return

            agent_obj = Agent(
                model=agent_instance,
                instructions=[agent.system_prompt],
                markdown=True,
            )

            for chunk in agent_obj.run(user_prompt, stream=True):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"[错误] 流式聊天失败: {str(e)}"

    def _print_streaming_response(self, user_prompt: str):
        """打印流式响应"""
        for chunk in self.chat_streaming(user_prompt):
            print(chunk, end="", flush=True)
        print()  # 换行

    def interactive_chat(self):
        """交互式聊天界面"""
        print("=" * 60)
        print("增强版 Agno AI聊天应用")
        print("支持多用户、会话管理、Agent管理、数据库存储")
        print("=" * 60)

        # 检查并初始化
        if not self.current_user_id:
            print("[错误] 没有当前用户")
            return

        current_user = self.user_manager.get_user(self.current_user_id)
        print(f"当前用户: {current_user.username}")

        if not self.current_session_id:
            print("[错误] 没有当前会话")
            return

        current_session = self.session_manager.get_session(self.current_session_id)
        print(f"当前会话: {current_session.title}")

        if not self.current_agent_id:
            print("[错误] 没有当前Agent")
            return

        current_agent = self.agent_manager.get_agent(self.current_agent_id)
        print(f"当前Agent: {current_agent.name}")

        # 聊天循环
        print("\n=== 开始聊天 ===")
        print("命令:")
        print("  'users' - 用户管理")
        print("  'sessions' - 会话管理")
        print("  'agents' - Agent管理")
        print("  'switch-agent' - 在当前会话中切换Agent")
        print("  'current' - 查看当前会话信息")
        print("  'history' - 查看对话历史")
        print("  'stream' - 切换流式/非流式模式")
        print("  'quit' 或 'exit' - 退出")

        while True:
            try:
                # 获取当前会话和Agent信息
                current_session = self.session_manager.get_session(self.current_session_id)
                current_agent = self.agent_manager.get_agent(self.current_agent_id)

                user_input = input(f"\n[{current_session.title}] [{current_agent.name}]: ").strip()

                if user_input.lower() in ['quit', 'exit']:
                    print("再见!")
                    break
                elif user_input.lower() == 'users':
                    # 用户管理
                    while self.user_management_menu():
                        pass
                    continue
                elif user_input.lower() == 'sessions':
                    # 会话管理
                    while self.session_management_menu():
                        pass
                    continue
                elif user_input.lower() == 'agents':
                    # Agent管理
                    while self.agent_management_menu():
                        pass
                    continue
                elif user_input.lower() == 'switch-agent':
                    # 在当前会话中切换Agent
                    self.switch_agent_in_session()
                    continue
                elif user_input.lower() == 'current':
                    # 查看当前会话信息
                    self.show_current_session_info()
                    continue
                elif user_input.lower() == 'history':
                    # 查看对话历史
                    self.show_conversation_history()
                    continue
                elif user_input.lower() == 'stream':
                    self.use_streaming = not self.use_streaming
                    mode = "流式" if self.use_streaming else "非流式"
                    print(f"已切换到{mode}模式")
                    continue
                elif not user_input:
                    continue

                # 保存到对话历史（使用会话ID）
                self.conversation_manager.add_message(
                    self.current_session_id,
                    self.current_user_id,
                    self.current_agent_id,
                    "user",
                    user_input
                )

                # 更新会话最后活动时间
                self.session_manager.update_session_timestamp(self.current_session_id)

                print("AI: ", end="", flush=True)

                if self.use_streaming:
                    # 流式输出
                    try:
                        full_response = ""
                        for chunk in self.chat_streaming(user_input):
                            print(chunk, end="", flush=True)
                            full_response += chunk
                        print()  # 换行

                        # 保存AI回复到历史
                        if full_response.strip():
                            self.conversation_manager.add_message(
                                self.current_session_id,
                                self.current_user_id,
                                self.current_agent_id,
                                "assistant",
                                full_response.strip()
                            )
                    except KeyboardInterrupt:
                        print("\n[用户中断]")
                    except Exception as e:
                        print(f"\n[错误] {str(e)}")
                else:
                    # 非流式输出
                    try:
                        response = self.chat_non_streaming(user_input)
                        print(response)

                        # 保存AI回复到历史
                        if response.strip() and not response.startswith("[错误]"):
                            self.conversation_manager.add_message(
                                self.current_session_id,
                                self.current_user_id,
                                self.current_agent_id,
                                "assistant",
                                response.strip()
                            )
                    except KeyboardInterrupt:
                        print("\n[用户中断]")
                    except Exception as e:
                        print(f"[错误] {str(e)}")

            except KeyboardInterrupt:
                print("\n使用 'quit' 退出程序")
            except Exception as e:
                print(f"[错误] {str(e)}")

        # 关闭数据库连接
        self.db_manager.close()

    def show_current_session_info(self):
        """显示当前会话信息"""
        print("\n" + "=" * 60)
        print("当前会话信息")
        print("=" * 60)

        current_user = self.user_manager.get_user(self.current_user_id)
        current_session = self.session_manager.get_session(self.current_session_id)
        current_agent = self.agent_manager.get_agent(self.current_agent_id)

        print(f"用户: {current_user.username}")
        print(f"会话: {current_session.title}")
        if current_session.description:
            print(f"描述: {current_session.description}")
        print(f"创建时间: {current_session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"最后更新: {current_session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Agent: {current_agent.name} ({current_agent.provider}: {current_agent.model_id})")

        # 显示对话历史统计
        history = self.conversation_manager.get_conversation_history(self.current_session_id, 1000)
        message_count = len(history)
        user_messages = len([m for m in history if m["role"] == "user"])
        ai_messages = len([m for m in history if m["role"] == "assistant"])

        print(f"\n对话统计:")
        print(f"  总消息数: {message_count}")
        print(f"  用户消息: {user_messages}")
        print(f"  AI回复: {ai_messages}")

    def show_conversation_history(self):
        """显示对话历史"""
        print("\n" + "=" * 60)
        print("对话历史")
        print("=" * 60)

        if not self.current_session_id:
            print("[错误] 没有选择当前会话")
            return

        current_session = self.session_manager.get_session(self.current_session_id)
        current_agent = self.agent_manager.get_agent(self.current_agent_id)

        print(f"会话: {current_session.title}")
        print(f"Agent: {current_agent.name}")
        print("-" * 60)

        history = self.conversation_manager.get_conversation_history(self.current_session_id, 20)

        if not history:
            print("暂无对话历史")
            return

        for i, message in enumerate(history, 1):
            role_icon = "👤" if message["role"] == "user" else "🤖"
            timestamp = message.get("timestamp", "")
            if timestamp:
                try:
                    # 尝试解析时间戳
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    else:
                        time_str = str(timestamp)
                except:
                    time_str = str(timestamp)
            else:
                time_str = ""

            content = message['content'][:100] + ('...' if len(message['content']) > 100 else '')
            if time_str:
                print(f"{i:2d}. [{time_str}] {role_icon} {content}")
            else:
                print(f"{i:2d}. {role_icon} {content}")

            if i % 10 == 0:  # 每10条暂停一次
                input("\n按回车键继续...")

        print(f"\n共显示 {len(history)} 条消息")

    def cleanup(self):
        """清理资源"""
        try:
            self.db_manager.close()
        except:
            pass


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="增强版Agno AI聊天应用")
    parser.add_argument("--db-type", choices=["sqlite", "mysql", "postgresql"],
                       default="sqlite", help="数据库类型")
    parser.add_argument("--db-path", default="autobox_id.db", help="SQLite数据库路径")
    parser.add_argument("--db-host", default="localhost", help="数据库主机")
    parser.add_argument("--db-port", type=int, default=5432, help="数据库端口")
    parser.add_argument("--db-user", default="postgres", help="数据库用户名")
    parser.add_argument("--db-password", default="", help="数据库密码")
    parser.add_argument("--db-name", default="autobox", help="数据库名称")

    args = parser.parse_args()

    # 根据参数设置数据库类型
    db_type_map = {
        "sqlite": DatabaseType.SQLITE,
        "mysql": DatabaseType.MYSQL,
        "postgresql": DatabaseType.POSTGRESQL
    }

    db_type = db_type_map[args.db_type]

    app = EnhancedChatApp()

    try:
        app.interactive_chat()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序异常: {str(e)}")
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()