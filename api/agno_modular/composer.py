"""
Agent系统组合器模块
支持动态组合Agent、MCP工具和记忆模块
"""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from uuid import uuid4

from agno.agent.agent import Agent
from agno.memory.manager import MemoryManager
from agno.models.base import Model
from agno.tools import Toolkit

from agent_factory import (
    AgentConfig,
    create_agent,
    create_qa_agent,
    create_task_agent,
    create_research_agent,
    create_creative_agent,
    create_custom_agent
)
from mcp_factory import (
    MCPConfig,
    create_mcp_tools,
    create_multi_mcp_tools
)
from memory_factory import (
    MemoryConfig,
    create_memory_manager,
    create_multi_memory_system
)


@dataclass
class AgentSystemConfig:
    """Agent系统配置类"""

    # 系统基础配置
    system_id: Optional[str] = None
    system_name: str = "agent_system"
    description: Optional[str] = None

    # Agent配置
    agent_config: AgentConfig = field(default_factory=AgentConfig)

    # MCP工具配置
    mcp_configs: List[MCPConfig] = field(default_factory=list)

    # 记忆配置
    memory_config: Optional[MemoryConfig] = None
    memory_types: Optional[List[str]] = None
    use_multi_memory: bool = False

    # 运行配置
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    debug_mode: bool = False

    # 响应配置
    response_stream: bool = False
    response_format: Optional[str] = None

    def __post_init__(self):
        """初始化后验证"""
        # 验证 system_name 是字符串类型
        if not isinstance(self.system_name, str):
            raise TypeError("system_name must be a string")

        # 验证其他字符串字段
        string_fields = ['system_id', 'description', 'user_id', 'session_id', 'response_format']
        for field_name in string_fields:
            field_value = getattr(self, field_name)
            if field_value is not None and not isinstance(field_value, str):
                raise TypeError(f"{field_name} must be a string or None")


class AgentSystem:
    """Agent系统类，包含Agent、工具和记忆管理"""

    def __init__(
        self,
        agent: Agent,
        mcp_tools: List[Union[Toolkit, "MCPTools", "MultiMCPTools"]],
        memory_managers: Union[MemoryManager, Dict[str, MemoryManager]],
        config: AgentSystemConfig
    ):
        self.agent = agent
        self.mcp_tools = mcp_tools
        self.memory_managers = memory_managers
        self.config = config
        self.system_id = config.system_id or str(uuid4())

    async def run(self, message: str, **kwargs) -> Any:
        """运行Agent系统"""
        # 添加MCP工具到Agent
        for tool in self.mcp_tools:
            if tool not in self.agent.tools:
                self.agent.tools.append(tool)

        # 设置记忆管理器
        if isinstance(self.memory_managers, MemoryManager):
            if not self.agent.memory_manager:
                self.agent.memory_manager = self.memory_managers
        elif isinstance(self.memory_managers, dict):
            # 如果是多记忆系统，使用主要的对话记忆管理器
            if "conversation" in self.memory_managers and not self.agent.memory_manager:
                self.agent.memory_manager = self.memory_managers["conversation"]

        # 设置用户ID和会话ID
        if self.config.user_id:
            kwargs["user_id"] = self.config.user_id
        if self.config.session_id:
            kwargs["session_id"] = self.config.session_id

        # 运行Agent
        if self.config.response_stream:
            return self.agent.run_stream(message, **kwargs)
        else:
            return self.agent.run(message, **kwargs)

    def add_memory(self, memory_type: str, memory_manager: MemoryManager):
        """添加记忆管理器"""
        if isinstance(self.memory_managers, dict):
            self.memory_managers[memory_type] = memory_manager

    def get_memory_manager(self, memory_type: str = "conversation") -> Optional[MemoryManager]:
        """获取指定类型的记忆管理器"""
        if isinstance(self.memory_managers, dict):
            return self.memory_managers.get(memory_type)
        elif isinstance(self.memory_managers, MemoryManager):
            # 如果是单个记忆管理器且调用的是默认参数，返回该记忆管理器
            if memory_type == "conversation":
                return self.memory_managers
            else:
                # 单个记忆管理器不支持其他类型的查询
                return None
        return None


def compose_agent_system(config: AgentSystemConfig) -> AgentSystem:
    """
    组合Agent系统

    Args:
        config: Agent系统配置

    Returns:
        组装好的AgentSystem实例
    """

    # 创建Agent
    agent = create_agent(config.agent_config)

    # 创建MCP工具
    mcp_tools = []
    if len(config.mcp_configs) == 1:
        mcp_tools.append(create_mcp_tools(config.mcp_configs[0]))
    elif len(config.mcp_configs) > 1:
        mcp_tools.append(create_multi_mcp_tools(config.mcp_configs))

    # 创建记忆管理器
    if config.use_multi_memory:
        memory_managers = create_multi_memory_system(
            model=config.agent_config.model,
            memory_types=config.memory_types,
            db=config.memory_config.db if config.memory_config else None
        )
    else:
        memory_managers = create_memory_manager(config.memory_config) if config.memory_config else None

    return AgentSystem(
        agent=agent,
        mcp_tools=mcp_tools,
        memory_managers=memory_managers,
        config=config
    )


def create_qa_system(
    model: Model,
    system_prompt: Optional[str] = None,
    mcp_configs: Optional[List[MCPConfig]] = None,
    memory_config: Optional[MemoryConfig] = None,
    **kwargs
) -> AgentSystem:
    """
    创建问答系统

    Args:
        model: AI模型
        system_prompt: 系统提示词
        mcp_configs: MCP配置列表
        memory_config: 记忆配置
        **kwargs: 其他配置

    Returns:
        问答Agent系统
    """

    # 默认问答系统配置
    if memory_config is None and kwargs.get("enable_memory", True):
        memory_config = MemoryConfig(model=model)

    system_config = AgentSystemConfig(
        system_name="qa_system",
        description="问答系统",
        agent_config=AgentConfig(
            name="qa_agent",
            model=model,
            system_prompt=system_prompt,
            tools=[],
        ),
        mcp_configs=mcp_configs or [],
        memory_config=memory_config,
        **kwargs
    )

    return compose_agent_system(system_config)


def create_task_system(
    model: Model,
    task_description: str,
    mcp_configs: Optional[List[MCPConfig]] = None,
    memory_config: Optional[MemoryConfig] = None,
    **kwargs
) -> AgentSystem:
    """
    创建任务执行系统

    Args:
        model: AI模型
        task_description: 任务描述
        mcp_configs: MCP配置列表
        memory_config: 记忆配置
        **kwargs: 其他配置

    Returns:
        任务执行Agent系统
    """

    system_config = AgentSystemConfig(
        system_name="task_system",
        description=f"任务执行系统: {task_description}",
        agent_config=AgentConfig(
            name="task_agent",
            model=model,
            system_prompt=f"你是任务执行助手，专门负责: {task_description}",
            tools=[],
        ),
        mcp_configs=mcp_configs or [],
        memory_config=memory_config,
        use_multi_memory=True,
        memory_types=["task", "context"],
        **kwargs
    )

    return compose_agent_system(system_config)


def create_research_system(
    model: Model,
    research_domain: Optional[str] = None,
    mcp_configs: Optional[List[MCPConfig]] = None,
    memory_config: Optional[MemoryConfig] = None,
    **kwargs
) -> AgentSystem:
    """
    创建研究系统

    Args:
        model: AI模型
        research_domain: 研究领域
        mcp_configs: MCP配置列表
        memory_config: 记忆配置
        **kwargs: 其他配置

    Returns:
        研究Agent系统
    """

    # 默认添加Web搜索工具
    if mcp_configs is None:
        mcp_configs = []

    system_config = AgentSystemConfig(
        system_name="research_system",
        description=f"研究系统: {research_domain or '通用研究'}",
        agent_config=AgentConfig(
            name="research_agent",
            model=model,
            system_prompt=f"你是专业的研究助手，专注于{research_domain or '通用研究'}领域",
            tools=[],
        ),
        mcp_configs=mcp_configs,
        memory_config=memory_config,
        use_multi_memory=True,
        memory_types=["research", "context", "preference"],
        **kwargs
    )

    return compose_agent_system(system_config)


def create_personal_assistant_system(
    model: Model,
    user_preferences: Optional[Dict[str, Any]] = None,
    mcp_configs: Optional[List[MCPConfig]] = None,
    **kwargs
) -> AgentSystem:
    """
    创建个人助理系统

    Args:
        model: AI模型
        user_preferences: 用户偏好
        mcp_configs: MCP配置列表
        **kwargs: 其他配置

    Returns:
        个人助理Agent系统
    """

    system_prompt = """你是一个智能个人助理，专门帮助用户处理日常事务。

    你的职责包括：
    1. 理解用户的需求和偏好
    2. 提供个性化的建议和服务
    3. 管理用户的个人信息和任务
    4. 保持对话的连贯性和一致性
    5. 学习和适应用户的习惯
    """

    if user_preferences:
        preferences_str = "\n".join([f"- {k}: {v}" for k, v in user_preferences.items()])
        system_prompt += f"\n\n用户偏好:\n{preferences_str}"

    memory_config = MemoryConfig(
        model=model,
        add_memories=True,
        update_memories=True
    )

    system_config = AgentSystemConfig(
        system_name="personal_assistant",
        description="智能个人助理系统",
        agent_config=AgentConfig(
            name="personal_assistant",
            model=model,
            system_prompt=system_prompt,
            tools=[],
            enable_user_memories=True,
        ),
        mcp_configs=mcp_configs or [],
        memory_config=memory_config,
        use_multi_memory=True,
        memory_types=["personal", "preference", "conversation", "task"],
        **kwargs
    )

    return compose_agent_system(system_config)


def create_multi_agent_system(
    agent_configs: List[AgentConfig],
    shared_mcp_configs: Optional[List[MCPConfig]] = None,
    shared_memory_config: Optional[MemoryConfig] = None,
    **kwargs
) -> List[AgentSystem]:
    """
    创建多Agent系统

    Args:
        agent_configs: Agent配置列表
        shared_mcp_configs: 共享的MCP配置
        shared_memory_config: 共享的记忆配置
        **kwargs: 其他配置

    Returns:
        Agent系统列表
    """

    systems = []
    for i, agent_config in enumerate(agent_configs):
        system_config = AgentSystemConfig(
            system_id=f"multi_agent_system_{i}",
            system_name=f"agent_system_{i}",
            description=f"多Agent系统中的第{i+1}个Agent",
            agent_config=agent_config,
            mcp_configs=shared_mcp_configs or [],
            memory_config=shared_memory_config,
            **kwargs
        )
        systems.append(compose_agent_system(system_config))

    return systems


def create_dynamic_system(
    model: Model,
    system_prompt: str,
    tools: Optional[List[Union[Toolkit, MCPConfig]]] = None,
    memory_config: Optional[MemoryConfig] = None,
    **kwargs
) -> AgentSystem:
    """
    创建动态系统，支持运行时配置

    Args:
        model: AI模型
        system_prompt: 系统提示词
        tools: 工具列表（可以是Tool或MCPConfig）
        memory_config: 记忆配置
        **kwargs: 其他配置

    Returns:
        动态Agent系统
    """

    # 分离工具和MCP配置
    mcp_configs = []
    regular_tools = []

    if tools:
        for tool in tools:
            if isinstance(tool, MCPConfig):
                mcp_configs.append(tool)
            else:
                regular_tools.append(tool)

    system_config = AgentSystemConfig(
        system_name="dynamic_system",
        description="动态配置的Agent系统",
        agent_config=AgentConfig(
            name="dynamic_agent",
            model=model,
            system_prompt=system_prompt,
            tools=regular_tools,
        ),
        mcp_configs=mcp_configs,
        memory_config=memory_config,
        **kwargs
    )

    return compose_agent_system(system_config)