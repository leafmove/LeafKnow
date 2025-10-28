"""
Agent工厂模块
用于创建和配置不同类型的Agent
"""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from uuid import uuid4

from agno.agent.agent import Agent
from agno.memory.manager import MemoryManager
from agno.models.base import Model
from agno.tools import Toolkit
from agno.models.message import Message


@dataclass
class AgentConfig:
    """Agent配置类"""

    # 基础配置
    name: str = "agent"
    model: Optional[Model] = None
    agent_id: Optional[str] = None

    # 提示词配置
    system_prompt: Optional[str] = None
    instructions: Optional[str] = None
    additional_instructions: Optional[str] = None

    # 工具配置
    tools: List[Union[Toolkit, Callable]] = field(default_factory=list)

    # 记忆配置
    memory_manager: Optional[MemoryManager] = None
    enable_user_memories: bool = False
    enable_agentic_memory: bool = False

    # 会话配置
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    # 其他配置
    debug_mode: bool = False
    show_tool_calls: bool = False
    markdown: bool = False

    # 高级配置
    num_history_runs: int = 3
    reasoning_instructions: Optional[str] = None


def create_agent(config: AgentConfig) -> Agent:
    """
    创建Agent实例

    Args:
        config: Agent配置

    Returns:
        配置好的Agent实例
    """

    # 生成唯一ID
    agent_id = config.agent_id or str(uuid4())

    # 创建Agent实例
    agent = Agent(
        agent_id=agent_id,
        name=config.name,
        model=config.model,
        instructions=config.instructions,
        additional_instructions=config.additional_instructions,
        tools=config.tools,
        memory_manager=config.memory_manager,
        enable_user_memories=config.enable_user_memories,
        enable_agentic_memory=config.enable_agentic_memory,
        debug_mode=config.debug_mode,
        show_tool_calls=config.show_tool_calls,
        markdown=config.markdown,
        num_history_runs=config.num_history_runs,
    )

    # 如果有自定义系统提示词，在运行时设置
    if config.system_prompt:
        agent._instructions = config.system_prompt

    return agent


def create_qa_agent(
    model: Model,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Union[Toolkit, Callable]]] = None,
    **kwargs
) -> Agent:
    """
    创建问答专用Agent

    Args:
        model: AI模型
        system_prompt: 系统提示词
        tools: 工具列表
        **kwargs: 其他参数

    Returns:
        问答Agent实例
    """

    default_system_prompt = """你是一个专业的问答助手。请根据用户的问题提供准确、有用的回答。

    回答要求：
    1. 准确性和相关性
    2. 结构清晰，条理分明
    3. 适当使用工具获取信息
    4. 保持友好专业的语调
    """

    config = AgentConfig(
        name="qa_agent",
        model=model,
        system_prompt=system_prompt or default_system_prompt,
        tools=tools or [],
        **kwargs
    )

    return create_agent(config)


def create_task_agent(
    model: Model,
    task_description: str,
    tools: Optional[List[Union[Toolkit, Callable]]] = None,
    **kwargs
) -> Agent:
    """
    创建任务执行专用Agent

    Args:
        model: AI模型
        task_description: 任务描述
        tools: 工具列表
        **kwargs: 其他参数

    Returns:
        任务Agent实例
    """

    system_prompt = f"""你是一个任务执行助手，专门负责完成以下任务：

    任务描述：{task_description}

    执行要求：
    1. 准确理解任务目标
    2. 善用可用工具完成任务
    3. 确保结果质量和准确性
    4. 如遇到问题，及时寻求帮助
    """

    config = AgentConfig(
        name="task_agent",
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        **kwargs
    )

    return create_agent(config)


def create_research_agent(
    model: Model,
    research_domain: Optional[str] = None,
    tools: Optional[List[Union[Toolkit, Callable]]] = None,
    **kwargs
) -> Agent:
    """
    创建研究专用Agent

    Args:
        model: AI模型
        research_domain: 研究领域
        tools: 工具列表
        **kwargs: 其他参数

    Returns:
        研究Agent实例
    """

    domain_instruction = f"，专注于{research_domain}领域" if research_domain else ""

    system_prompt = f"""你是一个专业的研究助手{domain_instruction}。

    研究要求：
    1. 深入分析问题本质
    2. 系统收集和整理信息
    3. 严谨的逻辑推理
    4. 提供有深度的见解和建议
    5. 注重信息的准确性和可靠性
    """

    config = AgentConfig(
        name="research_agent",
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        **kwargs
    )

    return create_agent(config)


def create_creative_agent(
    model: Model,
    creative_domain: str = "写作",
    tools: Optional[List[Union[Toolkit, Callable]]] = None,
    **kwargs
) -> Agent:
    """
    创建创意专用Agent

    Args:
        model: AI模型
        creative_domain: 创意领域（写作、设计、音乐等）
        tools: 工具列表
        **kwargs: 其他参数

    Returns:
        创意Agent实例
    """

    system_prompt = f"""你是一个专业的{creative_domain}创意助手。

    创作要求：
    1. 富有创意和想象力
    2. 注重原创性和艺术性
    3. 考虑用户需求和偏好
    4. 提供多样化的创意方案
    5. 鼓励创新和突破常规
    """

    config = AgentConfig(
        name="creative_agent",
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        **kwargs
    )

    return create_agent(config)


def create_custom_agent(
    model: Model,
    role: str,
    capabilities: List[str],
    constraints: Optional[List[str]] = None,
    tools: Optional[List[Union[Toolkit, Callable]]] = None,
    **kwargs
) -> Agent:
    """
    创建自定义Agent

    Args:
        model: AI模型
        role: Agent角色
        capabilities: 能力列表
        constraints: 约束列表
        tools: 工具列表
        **kwargs: 其他参数

    Returns:
        自定义Agent实例
    """

    capabilities_str = "\n".join([f"- {cap}" for cap in capabilities])
    constraints_str = "\n".join([f"- {con}" for con in constraints]) if constraints else ""

    system_prompt = f"""你是{role}。

    主要能力：
    {capabilities_str}
    """

    if constraints_str:
        system_prompt += f"""

    约束条件：
    {constraints_str}
    """

    system_prompt += """

    请根据你的角色和约束条件，为用户提供专业、准确的服务。
    """

    config = AgentConfig(
        name=f"custom_{role.lower().replace(' ', '_')}",
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        **kwargs
    )

    return create_agent(config)