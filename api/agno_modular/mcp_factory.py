"""
MCP工具工厂模块
用于创建和配置MCP工具集
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

from agno.tools.mcp import MCPTools, MultiMCPTools


@dataclass
class MCPConfig:
    """MCP配置类"""

    # 基础配置
    name: str = "mcp_tools"
    description: Optional[str] = None

    # 服务器配置
    server_url: Optional[str] = None
    server_command: Optional[str] = None
    server_args: List[str] = field(default_factory=list)
    server_env: Dict[str, str] = field(default_factory=dict)

    # 工具过滤
    include_tools: Optional[List[str]] = None
    exclude_tools: Optional[List[str]] = None

    # 连接配置
    timeout: int = 30
    max_retries: int = 3
    connection_check_interval: int = 5

    # 其他配置
    debug_mode: bool = False
    auto_connect: bool = True


def create_mcp_tools(config: MCPConfig) -> MCPTools:
    """
    创建单个MCP工具集

    Args:
        config: MCP配置

    Returns:
        MCPTools实例
    """

    # 构建完整的命令
    command = None
    if config.server_command and config.server_args:
        command = f"{config.server_command} {' '.join(config.server_args)}"
    elif config.server_command:
        command = config.server_command

    # 构建参数字典，避免参数冲突
    kwargs = {}

    # MCPTools需要command或server_params，如果没有command但需要创建，提供默认值
    if command:
        kwargs['command'] = command
    elif config.server_url is None:
        # 如果既没有command也没有url，提供默认command用于测试
        # 使用更简单的命令，完全避免shell元字符
        kwargs['command'] = "python --version"

    if config.server_url is not None:
        kwargs['url'] = config.server_url
    if config.server_env:
        kwargs['env'] = config.server_env
    if config.include_tools is not None:
        kwargs['include_tools'] = config.include_tools
    if config.exclude_tools is not None:
        kwargs['exclude_tools'] = config.exclude_tools
    if config.timeout != 30:
        kwargs['timeout_seconds'] = config.timeout

    mcp_tools = MCPTools(**kwargs)

    return mcp_tools


def create_multi_mcp_tools(configs: List[MCPConfig]) -> MultiMCPTools:
    """
    创建多个MCP工具集的组合

    Args:
        configs: MCP配置列表

    Returns:
        MultiMCPTools实例
    """

    multi_mcp_tools = MultiMCPTools()

    for config in configs:
        mcp_tools = create_mcp_tools(config)
        multi_mcp_tools.add_mcp_tools(mcp_tools)

    return multi_mcp_tools


def create_filesystem_mcp(
    base_path: Union[str, Path],
    name: str = "filesystem",
    read_only: bool = False,
    **kwargs
) -> MCPTools:
    """
    创建文件系统MCP工具

    Args:
        base_path: 基础路径
        name: 工具名称
        read_only: 是否只读
        **kwargs: 其他配置

    Returns:
        文件系统MCP工具
    """

    config = MCPConfig(
        name=name,
        description=f"Filesystem access tools for {base_path}",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-filesystem", str(base_path)],
        include_tools=["read_file", "write_file", "list_directory"] if not read_only else ["read_file", "list_directory"],
        **kwargs
    )

    return create_mcp_tools(config)


def create_database_mcp(
    connection_string: str,
    db_type: str = "postgresql",
    name: str = "database",
    **kwargs
) -> MCPTools:
    """
    创建数据库MCP工具

    Args:
        connection_string: 数据库连接字符串
        db_type: 数据库类型
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        数据库MCP工具
    """

    config = MCPConfig(
        name=name,
        description=f"Database access tools for {db_type}",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-postgres"],
        server_env={"DATABASE_URL": connection_string},
        **kwargs
    )

    return create_mcp_tools(config)


def create_web_search_mcp(
    api_key: str,
    search_engine: str = "brave",
    name: str = "web_search",
    **kwargs
) -> MCPTools:
    """
    创建网络搜索MCP工具

    Args:
        api_key: API密钥
        search_engine: 搜索引擎
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        网络搜索MCP工具
    """

    config = MCPConfig(
        name=name,
        description=f"Web search tools using {search_engine}",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-brave-search"],
        server_env={"BRAVE_API_KEY": api_key},
        **kwargs
    )

    return create_mcp_tools(config)


def create_github_mcp(
    token: str,
    name: str = "github",
    **kwargs
) -> MCPTools:
    """
    创建GitHub MCP工具

    Args:
        token: GitHub token
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        GitHub MCP工具
    """

    config = MCPConfig(
        name=name,
        description="GitHub access tools",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-github"],
        server_env={"GITHUB_PERSONAL_ACCESS_TOKEN": token},
        **kwargs
    )

    return create_mcp_tools(config)


def create_puppeteer_mcp(
    name: str = "puppeteer",
    **kwargs
) -> MCPTools:
    """
    创建Puppeteer MCP工具（网页自动化）

    Args:
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        Puppeteer MCP工具
    """

    config = MCPConfig(
        name=name,
        description="Web automation tools using Puppeteer",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-puppeteer"],
        **kwargs
    )

    return create_mcp_tools(config)


def create_memory_mcp(
    storage_path: Union[str, Path],
    name: str = "memory",
    **kwargs
) -> MCPTools:
    """
    创建记忆存储MCP工具

    Args:
        storage_path: 存储路径
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        记忆存储MCP工具
    """

    config = MCPConfig(
        name=name,
        description=f"Memory storage tools at {storage_path}",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-memory"],
        server_env={"MEMORY_PATH": str(storage_path)},
        **kwargs
    )

    return create_mcp_tools(config)


def create_weather_mcp(
    api_key: str,
    name: str = "weather",
    **kwargs
) -> MCPTools:
    """
    创建天气查询MCP工具

    Args:
        api_key: 天气API密钥
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        天气查询MCP工具
    """

    config = MCPConfig(
        name=name,
        description="Weather information tools",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-weather"],
        server_env={"WEATHER_API_KEY": api_key},
        **kwargs
    )

    return create_mcp_tools(config)


def create_slack_mcp(
    bot_token: str,
    name: str = "slack",
    **kwargs
) -> MCPTools:
    """
    创建Slack MCP工具

    Args:
        bot_token: Slack bot token
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        Slack MCP工具
    """

    config = MCPConfig(
        name=name,
        description="Slack integration tools",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-slack"],
        server_env={"SLACK_BOT_TOKEN": bot_token},
        **kwargs
    )

    return create_mcp_tools(config)


def create_time_mcp(
    name: str = "time",
    **kwargs
) -> MCPTools:
    """
    创建时间相关MCP工具

    Args:
        name: 工具名称
        **kwargs: 其他配置

    Returns:
        时间MCP工具
    """

    config = MCPConfig(
        name=name,
        description="Time and date tools",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-time"],
        **kwargs
    )

    return create_mcp_tools(config)