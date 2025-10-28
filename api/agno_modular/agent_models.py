"""
Agent数据模型定义
用于Agent的持久化存储和管理
"""

from sqlmodel import (
    Field,
    SQLModel,
    Session,
    select,
    delete,
    update,
    Column,
    Enum,
    JSON
)
from sqlalchemy import Engine
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Dict, Any, Optional
from uuid import uuid4


class AgentType(str, PyEnum):
    """Agent类型枚举"""
    QA = "qa"  # 问答助手
    TASK = "task"  # 任务执行
    RESEARCH = "research"  # 研究助手
    CREATIVE = "creative"  # 创意助手
    CUSTOM = "custom"  # 自定义类型


class AgentStatus(str, PyEnum):
    """Agent状态枚举"""
    ACTIVE = "active"  # 激活状态
    INACTIVE = "inactive"  # 未激活
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


class Agent(SQLModel, table=True):
    """Agent实体表"""
    __tablename__ = "t_agents"

    # 基础字段
    id: int = Field(default=None, primary_key=True)
    agent_uuid: str = Field(unique=True, index=True)  # 唯一标识符
    name: str = Field(max_length=100, index=True)  # Agent名称
    description: Optional[str] = Field(default=None, max_length=500)  # 描述

    # 类型和状态
    agent_type: str = Field(sa_column=Column(Enum(AgentType, values_callable=lambda obj: [e.value for e in obj])))
    status: str = Field(sa_column=Column(Enum(AgentStatus, values_callable=lambda obj: [e.value for e in obj]), default=AgentStatus.ACTIVE.value))

    # 配置信息
    model_configuration_id: Optional[int] = Field(default=None, foreign_key="t_model_configurations.id", index=True)
    system_prompt: Optional[str] = Field(default=None)  # 系统提示词
    instructions: Optional[str] = Field(default=None)  # 指令
    additional_instructions: Optional[str] = Field(default=None)  # 额外指令

    # 能力和工具配置
    capabilities: List[str] = Field(default=[], sa_column=Column(JSON))  # 能力列表
    tool_names: List[str] = Field(default=[], sa_column=Column(JSON))  # 工具名称列表
    mcp_config_ids: List[int] = Field(default=[], sa_column=Column(JSON))  # MCP配置ID列表

    # 记忆配置
    enable_user_memories: bool = Field(default=False)
    enable_agentic_memory: bool = Field(default=False)
    memory_config_id: Optional[int] = Field(default=None, foreign_key="t_memory_configs.id", index=True)

    # 运行配置
    num_history_runs: int = Field(default=3)
    debug_mode: bool = Field(default=False)
    show_tool_calls: bool = Field(default=False)
    markdown: bool = Field(default=False)

    # 用户和会话关联
    user_id: Optional[int] = Field(default=None, foreign_key="t_users.id", index=True)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = Field(default=None)

    # 元数据
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class AgentConfigTemplate(SQLModel, table=True):
    """Agent配置模板表"""
    __tablename__ = "t_agent_config_templates"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    display_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    # 模板配置
    agent_type: str = Field(sa_column=Column(Enum(AgentType, values_callable=lambda obj: [e.value for e in obj])))
    system_prompt: Optional[str] = Field(default=None)
    instructions: Optional[str] = Field(default=None)
    additional_instructions: Optional[str] = Field(default=None)

    # 默认配置
    default_capabilities: List[str] = Field(default=[], sa_column=Column(JSON))
    default_tool_names: List[str] = Field(default=[], sa_column=Column(JSON))
    default_memory_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # 模板属性
    is_system: bool = Field(default=False)  # 是否为系统模板
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AgentUsageLog(SQLModel, table=True):
    """Agent使用日志表"""
    __tablename__ = "t_agent_usage_logs"

    id: int = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="t_agents.id", index=True)
    session_id: Optional[int] = Field(default=None, foreign_key="t_chat_sessions.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="t_users.id", index=True)

    # 使用信息
    input_message: str = Field(max_length=2000)  # 输入消息（截断）
    response_length: int = Field(default=0)  # 响应长度
    tool_calls_count: int = Field(default=0)  # 工具调用次数

    # 性能指标
    response_time_ms: int = Field(default=0)  # 响应时间（毫秒）
    token_usage: Optional[Dict[str, int]] = Field(default=None, sa_column=Column(JSON))  # Token使用情况

    # 结果状态
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)

    used_at: datetime = Field(default_factory=datetime.now, index=True)


class MemoryConfig(SQLModel, table=True):
    """记忆配置表"""
    __tablename__ = "t_memory_configs"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)

    # 记忆配置
    memory_type: str = Field(default="conversation")  # 记忆类型
    db_path: Optional[str] = Field(default=None)
    table_name: str = Field(default="agent_memory")

    # 功能开关
    enable_user_memories: bool = Field(default=False)
    enable_agentic_memory: bool = Field(default=False)
    enable_task_memories: bool = Field(default=False)
    enable_context_memories: bool = Field(default=False)

    # 配置参数
    max_memory_entries: int = Field(default=1000)
    retention_days: int = Field(default=30)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AgentManager:
    """Agent管理器 - 提供Agent的增删改查功能"""

    def __init__(self, engine: Engine):
        self.engine = engine

    def create_agent(
        self,
        name: str,
        agent_type: AgentType,
        model_configuration_id: Optional[int] = None,
        system_prompt: Optional[str] = None,
        instructions: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Agent:
        """创建新的Agent"""

        agent = Agent(
            agent_uuid=str(uuid4()),
            name=name,
            agent_type=agent_type.value,
            model_configuration_id=model_configuration_id,
            system_prompt=system_prompt,
            instructions=instructions,
            capabilities=capabilities or [],
            tool_names=tool_names or [],
            user_id=user_id,
            **kwargs
        )

        with Session(self.engine) as session:
            session.add(agent)
            session.commit()
            session.refresh(agent)

        return agent

    def get_agent_by_id(self, agent_id: int) -> Optional[Agent]:
        """根据ID获取Agent"""
        with Session(self.engine) as session:
            stmt = select(Agent).where(Agent.id == agent_id)
            return session.exec(stmt).first()

    def get_agent_by_uuid(self, agent_uuid: str) -> Optional[Agent]:
        """根据UUID获取Agent"""
        with Session(self.engine) as session:
            stmt = select(Agent).where(Agent.agent_uuid == agent_uuid)
            return session.exec(stmt).first()

    def get_agents_by_user(self, user_id: int, status: Optional[AgentStatus] = None) -> List[Agent]:
        """获取用户的所有Agent"""
        with Session(self.engine) as session:
            stmt = select(Agent).where(Agent.user_id == user_id)
            if status:
                stmt = stmt.where(Agent.status == status.value)
            stmt = stmt.order_by(Agent.updated_at.desc())
            return session.exec(stmt).all()

    def get_agents_by_type(self, agent_type: AgentType, status: Optional[AgentStatus] = None) -> List[Agent]:
        """根据类型获取Agent列表"""
        with Session(self.engine) as session:
            stmt = select(Agent).where(Agent.agent_type == agent_type.value)
            if status:
                stmt = stmt.where(Agent.status == status.value)
            stmt = stmt.order_by(Agent.created_at.desc())
            return session.exec(stmt).all()

    def update_agent(
        self,
        agent_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        instructions: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None,
        status: Optional[AgentStatus] = None,
        **kwargs
    ) -> Optional[Agent]:
        """更新Agent信息"""

        with Session(self.engine) as session:
            stmt = select(Agent).where(Agent.id == agent_id)
            agent = session.exec(stmt).first()

            if not agent:
                return None

            # 更新字段
            if name is not None:
                agent.name = name
            if description is not None:
                agent.description = description
            if system_prompt is not None:
                agent.system_prompt = system_prompt
            if instructions is not None:
                agent.instructions = instructions
            if capabilities is not None:
                agent.capabilities = capabilities
            if tool_names is not None:
                agent.tool_names = tool_names
            if status is not None:
                agent.status = status.value

            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(agent, key) and value is not None:
                    setattr(agent, key, value)

            agent.updated_at = datetime.now()
            session.add(agent)
            session.commit()
            session.refresh(agent)

            return agent

    def delete_agent(self, agent_id: int, soft_delete: bool = True) -> bool:
        """删除Agent"""

        with Session(self.engine) as session:
            stmt = select(Agent).where(Agent.id == agent_id)
            agent = session.exec(stmt).first()

            if not agent:
                return False

            if soft_delete:
                # 软删除：标记为已删除
                agent.status = AgentStatus.DELETED.value
                agent.updated_at = datetime.now()
                session.add(agent)
            else:
                # 硬删除：从数据库中移除
                session.delete(agent)

            session.commit()
            return True

    def activate_agent(self, agent_id: int) -> bool:
        """激活Agent"""
        return self.update_agent(agent_id, status=AgentStatus.ACTIVE) is not None

    def deactivate_agent(self, agent_id: int) -> bool:
        """停用Agent"""
        return self.update_agent(agent_id, status=AgentStatus.INACTIVE) is not None

    def archive_agent(self, agent_id: int) -> bool:
        """归档Agent"""
        return self.update_agent(agent_id, status=AgentStatus.ARCHIVED) is not None

    def update_last_used(self, agent_id: int) -> bool:
        """更新Agent最后使用时间"""
        with Session(self.engine) as session:
            stmt = update(Agent).where(Agent.id == agent_id).values(last_used_at=datetime.now())
            result = session.exec(stmt)
            session.commit()
            return result.rowcount > 0

    def search_agents(
        self,
        query: str,
        user_id: Optional[int] = None,
        agent_type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None,
        limit: int = 20
    ) -> List[Agent]:
        """搜索Agent"""

        with Session(self.engine) as session:
            stmt = select(Agent)

            # 搜索条件
            if query:
                stmt = stmt.where(
                    (Agent.name.contains(query)) |
                    (Agent.description.contains(query)) |
                    (Agent.system_prompt.contains(query))
                )

            if user_id:
                stmt = stmt.where(Agent.user_id == user_id)

            if agent_type:
                stmt = stmt.where(Agent.agent_type == agent_type.value)

            if status:
                stmt = stmt.where(Agent.status == status.value)

            # 排除已删除的Agent
            stmt = stmt.where(Agent.status != AgentStatus.DELETED.value)

            stmt = stmt.order_by(Agent.updated_at.desc()).limit(limit)
            return session.exec(stmt).all()

    def log_agent_usage(
        self,
        agent_id: int,
        input_message: str,
        response_length: int,
        response_time_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[int] = None,
        user_id: Optional[int] = None,
        tool_calls_count: int = 0,
        token_usage: Optional[Dict[str, int]] = None
    ) -> AgentUsageLog:
        """记录Agent使用日志"""

        # 截断过长的输入消息
        truncated_message = input_message[:2000] if len(input_message) > 2000 else input_message

        log = AgentUsageLog(
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            input_message=truncated_message,
            response_length=response_length,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            tool_calls_count=tool_calls_count,
            token_usage=token_usage
        )

        with Session(self.engine) as session:
            session.add(log)
            session.commit()
            session.refresh(log)

        # 更新Agent最后使用时间
        self.update_last_used(agent_id)

        return log

    def get_agent_usage_stats(self, agent_id: int, days: int = 30) -> Dict[str, Any]:
        """获取Agent使用统计"""

        with Session(self.engine) as session:
            # 计算时间范围
            start_date = datetime.now() - timedelta(days=days)

            # 查询使用记录
            stmt = select(AgentUsageLog).where(
                AgentUsageLog.agent_id == agent_id,
                AgentUsageLog.used_at >= start_date
            )
            logs = session.exec(stmt).all()

            if not logs:
                return {
                    "total_uses": 0,
                    "success_rate": 0.0,
                    "avg_response_time": 0,
                    "total_response_length": 0,
                    "daily_usage": []
                }

            # 计算统计数据
            total_uses = len(logs)
            successful_uses = sum(1 for log in logs if log.success)
            success_rate = (successful_uses / total_uses) * 100 if total_uses > 0 else 0
            avg_response_time = sum(log.response_time_ms for log in logs) / total_uses
            total_response_length = sum(log.response_length for log in logs)

            # 按日期统计使用量
            daily_usage = {}
            for log in logs:
                date_key = log.used_at.date().isoformat()
                daily_usage[date_key] = daily_usage.get(date_key, 0) + 1

            return {
                "total_uses": total_uses,
                "success_rate": round(success_rate, 2),
                "avg_response_time": round(avg_response_time, 2),
                "total_response_length": total_response_length,
                "daily_usage": [{"date": date, "count": count} for date, count in sorted(daily_usage.items())]
            }


def init_agent_tables(db_manager: 'DBManager') -> bool:
    """初始化Agent相关数据表"""

    inspector = inspect(db_manager.engine)

    with Session(db_manager.engine) as session:
        # 创建Agent表
        if not inspector.has_table(Agent.__tablename__):
            Agent.__table__.create(db_manager.engine, checkfirst=True)
            print(f"Created table {Agent.__tablename__}")

        # 创建Agent配置模板表
        if not inspector.has_table(AgentConfigTemplate.__tablename__):
            AgentConfigTemplate.__table__.create(db_manager.engine, checkfirst=True)
            print(f"Created table {AgentConfigTemplate.__tablename__}")

            # 初始化默认配置模板
            default_templates = [
                AgentConfigTemplate(
                    name="qa_assistant",
                    display_name="问答助手",
                    description="专业的问答助手，提供准确有用的回答",
                    agent_type=AgentType.QA.value,
                    system_prompt="""你是一个专业的问答助手。请根据用户的问题提供准确、有用的回答。

回答要求：
1. 准确性和相关性
2. 结构清晰，条理分明
3. 适当使用工具获取信息
4. 保持友好专业的语调""",
                    default_capabilities=["text", "reasoning"],
                    is_system=True
                ),
                AgentConfigTemplate(
                    name="research_assistant",
                    display_name="研究助手",
                    description="专业的研究助手，深入分析和整理信息",
                    agent_type=AgentType.RESEARCH.value,
                    system_prompt="""你是一个专业的研究助手。

研究要求：
1. 深入分析问题本质
2. 系统收集和整理信息
3. 严谨的逻辑推理
4. 提供有深度的见解和建议
5. 注重信息的准确性和可靠性""",
                    default_capabilities=["text", "reasoning", "web_search"],
                    is_system=True
                ),
                AgentConfigTemplate(
                    name="task_executor",
                    display_name="任务执行器",
                    description="专门执行具体任务的助手",
                    agent_type=AgentType.TASK.value,
                    system_prompt="""你是一个任务执行助手，专门负责完成指定任务。

执行要求：
1. 准确理解任务目标
2. 善用可用工具完成任务
3. 确保结果质量和准确性
4. 如遇到问题，及时寻求帮助""",
                    default_capabilities=["text", "tool_use"],
                    is_system=True
                ),
                AgentConfigTemplate(
                    name="creative_assistant",
                    display_name="创意助手",
                    description="富有创意的助手，提供多样化创意方案",
                    agent_type=AgentType.CREATIVE.value,
                    system_prompt="""你是一个专业的创意助手。

创作要求：
1. 富有创意和想象力
2. 注重原创性和艺术性
3. 考虑用户需求和偏好
4. 提供多样化的创意方案
5. 鼓励创新和突破常规""",
                    default_capabilities=["text", "reasoning"],
                    is_system=True
                )
            ]

            session.add_all(default_templates)
            session.commit()

        # 创建记忆配置表
        if not inspector.has_table(MemoryConfig.__tablename__):
            MemoryConfig.__table__.create(db_manager.engine, checkfirst=True)
            print(f"Created table {MemoryConfig.__tablename__}")

            # 初始化默认记忆配置
            default_memory_configs = [
                MemoryConfig(
                    name="conversation_memory",
                    description="对话记忆配置",
                    memory_type="conversation",
                    enable_user_memories=True,
                    enable_agentic_memory=False,
                    max_memory_entries=500,
                    retention_days=7
                ),
                MemoryConfig(
                    name="task_memory",
                    description="任务记忆配置",
                    memory_type="task",
                    enable_task_memories=True,
                    enable_context_memories=True,
                    max_memory_entries=1000,
                    retention_days=30
                )
            ]

            session.add_all(default_memory_configs)
            session.commit()

        # 创建Agent使用日志表
        if not inspector.has_table(AgentUsageLog.__tablename__):
            AgentUsageLog.__table__.create(db_manager.engine, checkfirst=True)
            print(f"Created table {AgentUsageLog.__tablename__}")

            # 创建索引
            session.exec(text(f'''
                CREATE INDEX IF NOT EXISTS idx_agent_usage_agent_id
                ON {AgentUsageLog.__tablename__} (agent_id, used_at);
            '''))
            session.exec(text(f'''
                CREATE INDEX IF NOT EXISTS idx_agent_usage_user_id
                ON {AgentUsageLog.__tablename__} (user_id, used_at);
            '''))
            session.commit()

        return True