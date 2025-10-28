"""
独立的Agno模块化组件演示
不依赖agno框架，仅演示配置类的设计理念
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


@dataclass
class AgentConfig:
    """Agent配置类"""
    name: str = "agent"
    model: Optional[str] = None
    agent_id: Optional[str] = None
    system_prompt: Optional[str] = None
    instructions: Optional[str] = None
    additional_instructions: Optional[str] = None
    tools: List[Any] = field(default_factory=list)
    enable_user_memories: bool = False
    enable_agentic_memory: bool = False
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    debug_mode: bool = False
    show_tool_calls: bool = False
    markdown: bool = False
    num_history_runs: int = 3
    reasoning_instructions: Optional[str] = None


@dataclass
class MCPConfig:
    """MCP配置类"""
    name: str = "mcp_tools"
    description: Optional[str] = None
    server_url: Optional[str] = None
    server_command: Optional[str] = None
    server_args: List[str] = field(default_factory=list)
    server_env: Dict[str, str] = field(default_factory=dict)
    include_tools: Optional[List[str]] = None
    exclude_tools: Optional[List[str]] = None
    timeout: int = 30
    max_retries: int = 3
    connection_check_interval: int = 5
    debug_mode: bool = False
    auto_connect: bool = True


@dataclass
class MemoryConfig:
    """记忆管理配置类"""
    model: Optional[str] = None
    system_message: Optional[str] = None
    memory_capture_instructions: Optional[str] = None
    additional_instructions: Optional[str] = None
    delete_memories: bool = False
    update_memories: bool = True
    add_memories: bool = True
    clear_memories: bool = False
    retrieval_method: str = "last_n"
    retrieval_limit: int = 10
    debug_mode: bool = False
    auto_create: bool = True


@dataclass
class AgentSystemConfig:
    """Agent系统配置类"""
    system_id: Optional[str] = None
    system_name: str = "agent_system"
    description: Optional[str] = None
    agent_config: AgentConfig = field(default_factory=AgentConfig)
    mcp_configs: List[MCPConfig] = field(default_factory=list)
    memory_config: Optional[MemoryConfig] = None
    memory_types: Optional[List[str]] = None
    use_multi_memory: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    debug_mode: bool = False
    response_stream: bool = False
    response_format: Optional[str] = None


def demo_agent_configurations():
    """Agent配置演示"""
    print("=== Agent配置演示 ===")

    # 基础Agent配置
    basic_agent = AgentConfig(
        name="basic_agent",
        model="gpt-4",
        system_prompt="你是一个基础的AI助手"
    )
    print(f"基础Agent: {basic_agent.name}, 模型: {basic_agent.model}")

    # 问答Agent配置
    qa_agent = AgentConfig(
        name="qa_agent",
        model="gpt-4",
        system_prompt="你是一个专业的问答助手",
        instructions="提供准确、有用的信息",
        enable_user_memories=True,
        debug_mode=True
    )
    print(f"问答Agent: {qa_agent.name}, 启用用户记忆: {qa_agent.enable_user_memories}")

    # 任务Agent配置
    task_agent = AgentConfig(
        name="task_agent",
        model="gpt-4",
        system_prompt="你是一个任务执行助手",
        reasoning_instructions="请逐步思考并执行任务",
        show_tool_calls=True
    )
    print(f"任务Agent: {task_agent.name}, 显示工具调用: {task_agent.show_tool_calls}")

    return [basic_agent, qa_agent, task_agent]


def demo_mcp_configurations():
    """MCP配置演示"""
    print("\n=== MCP配置演示 ===")

    # 文件系统MCP配置
    fs_mcp = MCPConfig(
        name="filesystem",
        description="文件系统访问工具",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        include_tools=["read_file", "write_file", "list_directory"]
    )
    print(f"文件系统MCP: {fs_mcp.name}, 工具数量: {len(fs_mcp.include_tools or [])}")

    # Web搜索MCP配置
    web_mcp = MCPConfig(
        name="web_search",
        description="网络搜索工具",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-brave-search"],
        server_env={"BRAVE_API_KEY": "your_api_key_here"},
        timeout=60
    )
    print(f"Web搜索MCP: {web_mcp.name}, 超时: {web_mcp.timeout}秒")

    # 数据库MCP配置
    db_mcp = MCPConfig(
        name="database",
        description="数据库访问工具",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-postgres"],
        server_env={"DATABASE_URL": "postgresql://..."},
        max_retries=5
    )
    print(f"数据库MCP: {db_mcp.name}, 最大重试: {db_mcp.max_retries}")

    return [fs_mcp, web_mcp, db_mcp]


def demo_memory_configurations():
    """记忆配置演示"""
    print("\n=== 记忆配置演示 ===")

    # 对话记忆配置
    conv_memory = MemoryConfig(
        model="gpt-4",
        memory_capture_instructions="记录对话中的重要信息和上下文",
        retrieval_method="last_n",
        retrieval_limit=10
    )
    print(f"对话记忆: 检索方法={conv_memory.retrieval_method}, 限制={conv_memory.retrieval_limit}")

    # 个人信息记忆配置
    personal_memory = MemoryConfig(
        model="gpt-4",
        memory_capture_instructions="记录用户的个人信息和偏好",
        system_message="你是个人信息管理助手",
        retrieval_method="agentic"
    )
    print(f"个人信息记忆: 检索方法={personal_memory.retrieval_method}")

    # 任务记忆配置
    task_memory = MemoryConfig(
        model="gpt-4",
        memory_capture_instructions="记录任务相关的信息和进度",
        add_memories=True,
        update_memories=True,
        retrieval_method="first_n",
        retrieval_limit=5
    )
    print(f"任务记忆: 添加={task_memory.add_memories}, 更新={task_memory.update_memories}")

    return [conv_memory, personal_memory, task_memory]


def demo_system_configurations():
    """系统配置演示"""
    print("\n=== 系统配置演示 ===")

    # 简单问答系统
    qa_system = AgentSystemConfig(
        system_name="qa_system",
        description="简单问答系统",
        agent_config=AgentConfig(
            name="qa_agent",
            model="gpt-4",
            system_prompt="你是一个问答助手"
        ),
        memory_config=MemoryConfig(
            retrieval_method="last_n",
            retrieval_limit=5
        ),
        user_id="user123"
    )
    print(f"问答系统: {qa_system.system_name}, 用户: {qa_system.user_id}")

    # 任务执行系统
    task_system = AgentSystemConfig(
        system_name="task_system",
        description="任务执行系统",
        agent_config=AgentConfig(
            name="task_agent",
            model="gpt-4",
            system_prompt="你是一个任务执行助手",
            show_tool_calls=True
        ),
        mcp_configs=[
            MCPConfig(name="filesystem", server_command="fs_command"),
            MCPConfig(name="calculator", server_command="calc_command")
        ],
        memory_config=MemoryConfig(
            memory_capture_instructions="记录任务执行过程和结果"
        )
    )
    print(f"任务系统: {task_system.system_name}, MCP工具数: {len(task_system.mcp_configs)}")

    # 个人助理系统
    assistant_system = AgentSystemConfig(
        system_name="personal_assistant",
        description="个人助理系统",
        agent_config=AgentConfig(
            name="assistant",
            model="gpt-4",
            system_prompt="你是用户的个人助理",
            enable_user_memories=True
        ),
        memory_config=MemoryConfig(
            retrieval_method="agentic",
            retrieval_limit=20
        ),
        use_multi_memory=True,
        memory_types=["personal", "conversation", "preference", "task"]
    )
    print(f"个人助理系统: {assistant_system.system_name}, 多记忆: {assistant_system.use_multi_memory}")
    print(f"记忆类型: {assistant_system.memory_types}")

    return [qa_system, task_system, assistant_system]


def demo_combination_patterns():
    """组合模式演示"""
    print("\n=== 组合模式演示 ===")

    patterns = {
        "简单问答": {
            "agent": AgentConfig(name="qa", model="gpt-4"),
            "memory": MemoryConfig(retrieval_method="last_n"),
            "tools": []
        },

        "任务执行": {
            "agent": AgentConfig(name="task", model="gpt-4", show_tool_calls=True),
            "memory": MemoryConfig(retrieval_method="agentic"),
            "tools": [MCPConfig(name="fs"), MCPConfig(name="calc")]
        },

        "个人助理": {
            "agent": AgentConfig(name="assistant", model="gpt-4", enable_user_memories=True),
            "memory": MemoryConfig(retrieval_method="agentic", retrieval_limit=20),
            "tools": [MCPConfig(name="calendar"), MCPConfig(name="notes")]
        },

        "研究助手": {
            "agent": AgentConfig(name="researcher", model="gpt-4"),
            "memory": MemoryConfig(retrieval_method="agentic"),
            "tools": [MCPConfig(name="web_search"), MCPConfig(name="database")]
        }
    }

    for pattern_name, config in patterns.items():
        print(f"\n{pattern_name}模式:")
        print(f"  Agent: {config['agent'].name}")
        print(f"  记忆检索: {config['memory'].retrieval_method}")
        print(f"  工具数量: {len(config['tools'])}")
        if config['tools']:
            tool_names = [tool.name for tool in config['tools']]
            print(f"  工具列表: {tool_names}")

    return patterns


def demo_usage_scenarios():
    """使用场景演示"""
    print("\n=== 使用场景演示 ===")

    scenarios = {
        "客户服务": {
            "description": "处理客户咨询和问题",
            "agent": {
                "name": "customer_service",
                "system_prompt": "你是专业的客服代表",
                "enable_user_memories": True
            },
            "memory": {
                "memory_capture_instructions": "记录客户信息和历史问题",
                "retrieval_method": "agentic"
            }
        },

        "教育辅导": {
            "description": "提供个性化学习辅导",
            "agent": {
                "name": "tutor",
                "system_prompt": "你是专业的学习辅导老师",
                "instructions": "根据学生水平调整教学方式"
            },
            "memory": {
                "memory_capture_instructions": "记录学生的学习进度和偏好",
                "retrieval_method": "agentic",
                "retrieval_limit": 15
            }
        },

        "数据分析": {
            "description": "执行数据分析和可视化任务",
            "agent": {
                "name": "analyst",
                "system_prompt": "你是专业的数据分析师",
                "show_tool_calls": True
            },
            "tools": [
                {"name": "database", "description": "数据库查询"},
                {"name": "visualization", "description": "数据可视化"}
            ]
        },

        "创意写作": {
            "description": "协助创意写作和内容生成",
            "agent": {
                "name": "writer",
                "system_prompt": "你是专业的创意写作助手",
                "instructions": "提供有创意的写作建议"
            },
            "memory": {
                "memory_capture_instructions": "记录用户的写作风格和偏好",
                "retrieval_method": "last_n"
            }
        }
    }

    for scenario_name, config in scenarios.items():
        print(f"\n{scenario_name}:")
        print(f"  描述: {config['description']}")
        print(f"  Agent: {config['agent']['name']}")
        if 'memory' in config:
            memory_config = config['memory']
            print(f"  记忆策略: {memory_config.get('retrieval_method', '无')}")
        if 'tools' in config:
            print(f"  工具: {[tool['name'] for tool in config['tools']]}")

    return scenarios


def demo_configuration_validation():
    """配置验证演示"""
    print("\n=== 配置验证演示 ===")

    def validate_agent_config(config: AgentConfig) -> List[str]:
        """验证Agent配置"""
        issues = []
        if not config.name:
            issues.append("Agent名称不能为空")
        if not config.model:
            issues.append("必须指定AI模型")
        if not config.system_prompt and not config.instructions:
            issues.append("应该提供系统提示词或指令")
        return issues

    def validate_system_config(config: AgentSystemConfig) -> List[str]:
        """验证系统配置"""
        issues = []
        if not config.system_name:
            issues.append("系统名称不能为空")
        if not config.agent_config:
            issues.append("必须提供Agent配置")

        # 验证Agent配置
        agent_issues = validate_agent_config(config.agent_config)
        for issue in agent_issues:
            issues.append(f"Agent配置错误: {issue}")

        return issues

    # 测试有效配置
    valid_config = AgentSystemConfig(
        system_name="test_system",
        agent_config=AgentConfig(
            name="test_agent",
            model="gpt-4",
            system_prompt="测试Agent"
        )
    )

    issues = validate_system_config(valid_config)
    print(f"有效配置验证: {'通过' if not issues else f'失败 - {issues}'}")

    # 测试无效配置
    invalid_config = AgentSystemConfig(
        system_name="",  # 空名称
        agent_config=AgentConfig(
            name="",
            model="",  # 空模型
            system_prompt=""
        )
    )

    issues = validate_system_config(invalid_config)
    print(f"无效配置验证: 发现 {len(issues)} 个问题")
    for issue in issues:
        print(f"  - {issue}")


def demo_configuration_export():
    """配置导出演示"""
    print("\n=== 配置导出演示 ===")

    # 创建示例配置
    system_config = AgentSystemConfig(
        system_name="example_system",
        description="示例系统配置",
        agent_config=AgentConfig(
            name="example_agent",
            model="gpt-4",
            system_prompt="示例Agent",
            enable_user_memories=True
        ),
        mcp_configs=[
            MCPConfig(name="example_tool", server_command="example")
        ],
        memory_config=MemoryConfig(
            retrieval_method="agentic",
            retrieval_limit=10
        )
    )

    # 导出为字典
    config_dict = {
        "system": {
            "name": system_config.system_name,
            "description": system_config.description,
            "user_id": system_config.user_id
        },
        "agent": {
            "name": system_config.agent_config.name,
            "model": system_config.agent_config.model,
            "system_prompt": system_config.agent_config.system_prompt,
            "enable_user_memories": system_config.agent_config.enable_user_memories
        },
        "tools": [
            {
                "name": tool.name,
                "command": tool.server_command
            } for tool in system_config.mcp_configs
        ],
        "memory": {
            "retrieval_method": system_config.memory_config.retrieval_method,
            "retrieval_limit": system_config.memory_config.retrieval_limit
        } if system_config.memory_config else None
    }

    print("配置导出为JSON格式:")
    import json
    print(json.dumps(config_dict, indent=2, ensure_ascii=False))

    return config_dict


def run_standalone_demo():
    """运行独立演示"""
    print("Agno模块化组件独立演示")
    print("=" * 50)
    print("注意: 这是配置类的设计演示，不包含实际的Agent实现")
    print("=" * 50)

    try:
        # 运行各项演示
        demo_agent_configurations()
        demo_mcp_configurations()
        demo_memory_configurations()
        demo_system_configurations()
        demo_combination_patterns()
        demo_usage_scenarios()
        demo_configuration_validation()
        demo_configuration_export()

        print("\n" + "=" * 50)
        print("独立演示完成！")
        print("\n设计要点:")
        print("1. 模块化配置: Agent、MCP工具、记忆管理分离")
        print("2. 灵活组合: 支持不同场景的配置组合")
        print("3. 类型安全: 使用dataclass确保配置完整性")
        print("4. 易于扩展: 简单的结构便于添加新功能")
        print("5. 配置验证: 内置验证确保配置正确性")

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_standalone_demo()