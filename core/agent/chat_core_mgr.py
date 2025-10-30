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


