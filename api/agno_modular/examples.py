"""
Agno模块化组件使用示例
"""

import asyncio
from typing import List

from agno.models.openai import OpenAIChat

from . import (
    create_qa_agent,
    create_task_agent,
    create_research_agent,
    create_filesystem_mcp,
    create_web_search_mcp,
    create_memory_manager,
    compose_agent_system,
    create_qa_system,
    create_task_system,
    create_personal_assistant_system,
    AgentConfig,
    MCPConfig,
    MemoryConfig,
    AgentSystemConfig,
)


def example_basic_qa_agent():
    """基础问答Agent示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建问答Agent
    agent = create_qa_agent(
        model=model,
        system_prompt="你是一个专业的Python编程助手，请提供准确的编程建议。",
        debug_mode=True
    )

    # 运行Agent
    response = agent.run("如何在Python中创建一个类？")
    print(response)


def example_task_agent_with_tools():
    """带工具的任务Agent示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建文件系统MCP工具
    fs_mcp = create_filesystem_mcp(
        base_path="/tmp",
        name="file_manager",
        read_only=False
    )

    # 创建任务Agent
    agent = create_task_agent(
        model=model,
        task_description="文件管理和文本处理任务",
        tools=[fs_mcp]
    )

    # 运行Agent
    response = agent.run("请在/tmp目录下创建一个test.txt文件，并写入'Hello World'")
    print(response)


def example_agent_with_memory():
    """带记忆的Agent示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建记忆管理器
    memory_config = MemoryConfig(
        model=model,
        memory_capture_instructions="记录用户的编程偏好和经验水平",
        add_memories=True,
        update_memories=True
    )
    memory_manager = create_memory_manager(memory_config)

    # 创建Agent配置
    agent_config = AgentConfig(
        name="programming_tutor",
        model=model,
        system_prompt="你是编程导师，了解用户的编程背景并提供个性化建议。",
        memory_manager=memory_manager,
        enable_user_memories=True
    )

    # 创建Agent
    from .agent_factory import create_agent
    agent = create_agent(agent_config)

    # 运行Agent（会自动记录记忆）
    response1 = agent.run("我叫张三，是Python初学者")
    print(response1)

    response2 = agent.run("请给我一些Python学习建议")
    print(response2)


def example_qa_system():
    """完整的问答系统示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建Web搜索MCP工具
    web_mcp_config = MCPConfig(
        name="web_search",
        description="网络搜索工具",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-brave-search"],
        server_env={"BRAVE_API_KEY": "your_api_key_here"}
    )

    # 创建记忆配置
    memory_config = MemoryConfig(
        model=model,
        add_memories=True,
        update_memories=True
    )

    # 创建问答系统
    qa_system = create_qa_system(
        model=model,
        system_prompt="你是一个智能问答助手，可以搜索网络信息来回答问题。",
        mcp_configs=[web_mcp_config],
        memory_config=memory_config,
        user_id="user123"
    )

    # 运行系统
    response = qa_system.run("什么是最新的AI发展趋势？")
    print(response)


def example_personal_assistant():
    """个人助理系统示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建多个MCP工具
    fs_mcp = create_filesystem_mcp("/home/user", name="home_files")
    time_mcp = MCPConfig(
        name="time_tools",
        description="时间管理工具",
        server_command="npx",
        server_args=["-y", "@modelcontextprotocol/server-time"]
    )

    # 创建个人助理系统
    assistant_system = create_personal_assistant_system(
        model=model,
        user_preferences={
            "language": "中文",
            "timezone": "Asia/Shanghai",
            "work_style": "高效简洁"
        },
        mcp_configs=[fs_mcp, time_mcp],
        user_id="user456"
    )

    # 运行系统
    response = assistant_system.run("请帮我总结今天的工作并制定明天的计划")
    print(response)


async def example_async_system():
    """异步系统示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建研究系统
    research_system = create_research_system(
        model=model,
        research_domain="人工智能",
        memory_config=MemoryConfig(model=model)
    )

    # 异步运行
    response = await research_system.run("请研究最新的GPT模型发展")
    print(response)


def example_multi_memory_system():
    """多记忆系统示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建系统配置
    system_config = AgentSystemConfig(
        system_name="multi_memory_system",
        description="多记忆系统演示",
        agent_config=AgentConfig(
            name="multi_memory_agent",
            model=model,
            system_prompt="你是一个智能助手，使用多记忆系统来管理不同类型的信息。"
        ),
        use_multi_memory=True,
        memory_types=["personal", "task", "preference", "context"],
        user_id="user789"
    )

    # 创建系统
    system = compose_agent_system(system_config)

    # 添加个人记忆
    personal_memory = system.get_memory_manager("personal")
    if personal_memory:
        personal_memory.add_user_memory(
            memory="用户是一名软件工程师，有5年工作经验",
            user_id="user789"
        )

    # 运行系统
    response = system.run("根据我的背景，推荐一些适合的职业发展路径")
    print(response)


def example_custom_agent():
    """自定义Agent示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 创建自定义Agent
    from .agent_factory import create_custom_agent
    agent = create_custom_agent(
        model=model,
        role="数据分析师",
        capabilities=[
            "数据清洗和预处理",
            "统计分析",
            "数据可视化",
            "报告生成"
        ],
        constraints=[
            "确保数据隐私和安全",
            "使用科学的统计方法",
            "提供清晰的可视化"
        ]
    )

    # 运行Agent
    response = agent.run("请分析这组销售数据的趋势")
    print(response)


def example_dynamic_system():
    """动态系统示例"""

    # 创建模型
    model = OpenAIChat(id="gpt-4")

    # 动态创建系统
    from .composer import create_dynamic_system
    system = create_dynamic_system(
        model=model,
        system_prompt="你是一个灵活的助手，根据需要使用不同的工具。",
        tools=[
            create_filesystem_mcp("/tmp"),
            MCPConfig(
                name="calculator",
                description="计算工具",
                server_command="npx",
                server_args=["-y", "@modelcontextprotocol/server-calculator"]
            )
        ]
    )

    # 运行系统
    response = system.run("请计算1+1，并将结果保存到/tmp/result.txt")
    print(response)


def run_all_examples():
    """运行所有示例"""

    print("=== 基础问答Agent示例 ===")
    example_basic_qa_agent()

    print("\n=== 带工具的任务Agent示例 ===")
    example_task_agent_with_tools()

    print("\n=== 带记忆的Agent示例 ===")
    example_agent_with_memory()

    print("\n=== 问答系统示例 ===")
    example_qa_system()

    print("\n=== 个人助理系统示例 ===")
    example_personal_assistant()

    print("\n=== 异步系统示例 ===")
    asyncio.run(example_async_system())

    print("\n=== 多记忆系统示例 ===")
    example_multi_memory_system()

    print("\n=== 自定义Agent示例 ===")
    example_custom_agent()

    print("\n=== 动态系统示例 ===")
    example_dynamic_system()


if __name__ == "__main__":
    run_all_examples()