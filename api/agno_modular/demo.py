"""
Agno模块化组件演示脚本
展示如何使用模块化组件创建不同类型的Agent系统
"""

import asyncio
import os
import sys
from typing import List, Optional

# 添加当前目录到Python路径，支持直接运行
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 模拟导入（在实际使用中，这些是从agno导入的）
class MockModel:
    def __init__(self, id: str):
        self.id = id
        self.supports_native_structured_outputs = True
        self.supports_json_schema_outputs = True

    def response(self, messages, tools=None, functions=None, response_format=None):
        from types import SimpleNamespace
        return SimpleNamespace(content="这是模拟的响应内容")

def demo_basic_usage():
    """基础使用演示"""
    print("=== 基础使用演示 ===")

    # 注意：这里使用模拟的模型，实际使用时应该是真实的模型
    # from agno.models.openai import OpenAIChat
    # model = OpenAIChat(id="gpt-4")

    # 模拟模型
    model = MockModel("gpt-4")

    from agent_factory import create_qa_agent, AgentConfig

    # 创建问答Agent
    agent = create_qa_agent(
        model=model,
        system_prompt="你是一个专业的编程助手",
        debug_mode=True
    )

    print(f"创建的Agent: {agent.name}")
    print(f"Agent ID: {agent.agent_id}")
    print(f"使用的模型: {agent.model.id}")

    # 模拟运行
    response = agent.run("如何在Python中创建类？")
    print(f"Agent响应: {response}")


def demo_mcp_tools():
    """MCP工具演示"""
    print("\n=== MCP工具演示 ===")

    from mcp_factory import (
        create_filesystem_mcp,
        create_web_search_mcp,
        create_multi_mcp_tools
    )

    # 创建文件系统工具
    fs_tools = create_filesystem_mcp(
        base_path="/tmp",
        name="file_manager",
        read_only=False
    )

    print(f"创建文件系统工具: {fs_tools.name}")

    # 创建Web搜索工具
    web_tools = create_web_search_mcp(
        api_key="demo_key",
        search_engine="brave",
        name="web_search"
    )

    print(f"创建Web搜索工具: {web_tools.name}")

    # 创建多工具组合
    multi_tools = create_multi_mcp_tools([fs_tools, web_tools])
    print(f"创建多工具组合，包含 {len(multi_tools.mcp_tools_list)} 个工具")


def demo_memory_management():
    """记忆管理演示"""
    print("\n=== 记忆管理演示 ===")

    model = MockModel("gpt-4")

    from memory_factory import (
        create_conversation_memory,
        create_personal_memory,
        create_multi_memory_system
    )

    # 创建对话记忆管理器
    conv_memory = create_conversation_memory(model=model)
    print(f"创建对话记忆管理器: {type(conv_memory).__name__}")

    # 创建个人信息记忆管理器
    personal_memory = create_personal_memory(model=model)
    print(f"创建个人信息记忆管理器: {type(personal_memory).__name__}")

    # 创建多记忆系统
    memory_system = create_multi_memory_system(
        model=model,
        memory_types=["conversation", "personal", "task", "preference"]
    )
    print(f"创建多记忆系统，包含 {len(memory_system)} 个记忆管理器")
    print(f"记忆类型: {list(memory_system.keys())}")


def demo_system_composition():
    """系统组合演示"""
    print("\n=== 系统组合演示 ===")

    model = MockModel("gpt-4")

    from agent_factory import AgentConfig
    from mcp_factory import MCPConfig
    from memory_factory import MemoryConfig
    from composer import create_qa_system, AgentSystemConfig, compose_agent_system

    # 方法1：使用预配置系统
    qa_system = create_qa_system(
        model=model,
        system_prompt="你是一个智能问答助手",
        memory_config=MemoryConfig(model=model),
        user_id="demo_user"
    )

    print(f"创建问答系统: {qa_system.config.system_name}")
    print(f"系统ID: {qa_system.system_id}")

    # 方法2：自定义组合
    system_config = AgentSystemConfig(
        system_name="custom_system",
        description="自定义演示系统",
        agent_config=AgentConfig(
            name="custom_agent",
            model=model,
            system_prompt="自定义系统提示词"
        ),
        memory_config=MemoryConfig(model=model),
        use_multi_memory=True,
        memory_types=["conversation", "personal"],
        user_id="demo_user"
    )

    custom_system = compose_agent_system(system_config)
    print(f"创建自定义系统: {custom_system.config.system_name}")

    # 模拟运行
    response = custom_system.run("介绍一下这个系统的功能")
    print(f"系统响应: {response}")


def demo_specialized_agents():
    """专用Agent演示"""
    print("\n=== 专用Agent演示 ===")

    model = MockModel("gpt-4")

    from agent_factory import (
        create_task_agent,
        create_research_agent,
        create_creative_agent,
        create_custom_agent
    )

    # 任务Agent
    task_agent = create_task_agent(
        model=model,
        task_description="文件处理和数据分析"
    )
    print(f"创建任务Agent: {task_agent.name}")

    # 研究Agent
    research_agent = create_research_agent(
        model=model,
        research_domain="人工智能"
    )
    print(f"创建研究Agent: {research_agent.name}")

    # 创意Agent
    creative_agent = create_creative_agent(
        model=model,
        creative_domain="编程"
    )
    print(f"创建创意Agent: {creative_agent.name}")

    # 自定义Agent
    custom_agent = create_custom_agent(
        model=model,
        role="代码审查专家",
        capabilities=[
            "代码质量分析",
            "性能优化建议",
            "安全漏洞检测"
        ],
        constraints=[
            "提供建设性反馈",
            "遵循编码规范"
        ]
    )
    print(f"创建自定义Agent: {custom_agent.name}")


def demo_dynamic_configuration():
    """动态配置演示"""
    print("\n=== 动态配置演示 ===")

    model = MockModel("gpt-4")

    from composer import create_dynamic_system
    from mcp_factory import MCPConfig, create_filesystem_mcp

    # 动态创建系统
    dynamic_system = create_dynamic_system(
        model=model,
        system_prompt="灵活使用各种工具的智能助手",
        tools=[
            create_filesystem_mcp("/tmp"),
            MCPConfig(
                name="calculator",
                server_command="python",
                server_args=["-c", "print('Calculator tool')"]
            )
        ]
    )

    print(f"创建动态系统: {dynamic_system.config.system_name}")
    print(f"Agent名称: {dynamic_system.agent.name}")
    print(f"MCP工具数量: {len(dynamic_system.mcp_tools)}")

    # 添加记忆管理器
    from memory_factory import create_task_memory
    task_memory = create_task_memory(model=model)
    dynamic_system.add_memory("task", task_memory)
    print(f"添加任务记忆管理器")

    # 获取记忆管理器
    memory_manager = dynamic_system.get_memory_manager("task")
    print(f"获取任务记忆管理器: {type(memory_manager).__name__}")


async def demo_async_usage():
    """异步使用演示"""
    print("\n=== 异步使用演示 ===")

    model = MockModel("gpt-4")

    from composer import create_research_system

    # 创建研究系统
    research_system = create_research_system(
        model=model,
        research_domain="机器学习",
        response_stream=True
    )

    print(f"创建研究系统: {research_system.config.system_name}")

    # 模拟异步运行
    response = await research_system.run("研究最新的深度学习技术")
    print(f"异步响应: {response}")


def demo_config_customization():
    """配置定制演示"""
    print("\n=== 配置定制演示 ===")

    from agent_factory import AgentConfig
    from mcp_factory import MCPConfig
    from memory_factory import MemoryConfig

    # 自定义Agent配置
    custom_agent_config = AgentConfig(
        name="advanced_agent",
        system_prompt="高级AI助手",
        instructions="提供专业、准确、有用的回答",
        additional_instructions="保持友好和专业的语调",
        debug_mode=True,
        show_tool_calls=True,
        num_history_runs=5
    )

    print(f"自定义Agent配置:")
    print(f"  名称: {custom_agent_config.name}")
    print(f"  调试模式: {custom_agent_config.debug_mode}")
    print(f"  历史运行次数: {custom_agent_config.num_history_runs}")

    # 自定义MCP配置
    custom_mcp_config = MCPConfig(
        name="custom_mcp",
        timeout=60,
        max_retries=5,
        include_tools=["tool1", "tool2"],
        exclude_tools=["tool3"],
        debug_mode=True
    )

    print(f"自定义MCP配置:")
    print(f"  名称: {custom_mcp_config.name}")
    print(f"  超时: {custom_mcp_config.timeout}")
    print(f"  最大重试: {custom_mcp_config.max_retries}")

    # 自定义记忆配置
    custom_memory_config = MemoryConfig(
        add_memories=True,
        update_memories=True,
        delete_memories=False,
        retrieval_method="agentic",
        retrieval_limit=20
    )

    print(f"自定义记忆配置:")
    print(f"  添加记忆: {custom_memory_config.add_memories}")
    print(f"  检索方法: {custom_memory_config.retrieval_method}")
    print(f"  检索限制: {custom_memory_config.retrieval_limit}")


def run_demo():
    """运行所有演示"""
    print("Agno模块化组件演示")
    print("=" * 50)

    try:
        demo_basic_usage()
        demo_mcp_tools()
        demo_memory_management()
        demo_system_composition()
        demo_specialized_agents()
        demo_dynamic_configuration()
        demo_config_customization()

        # 异步演示
        print("\n" + "=" * 50)
        asyncio.run(demo_async_usage())

        print("\n" + "=" * 50)
        print("所有演示完成！")
        print("\n提示：")
        print("- 这些演示使用了模拟的模型和工具")
        print("- 实际使用时，请替换为真实的模型和配置")
        print("- 查看 examples.py 获取更多详细示例")
        print("- 查看 tests.py 了解如何测试组件")

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()