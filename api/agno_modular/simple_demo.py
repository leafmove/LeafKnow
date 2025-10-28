"""
简化的Agno模块化组件演示
不依赖MCP，专注于Agent和记忆模块
"""
import sys
import os
# 添加父目录到Python路径，以便导入本地agno库
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def demo_basic_agent_creation():
    """基础Agent创建演示"""
    print("=== 基础Agent创建演示 ===")

    # 导入配置类
    from agent_factory import AgentConfig

    # 创建配置
    config = AgentConfig(
        name="demo_agent",
        system_prompt="这是一个演示Agent",
        debug_mode=True,
        instructions="提供清晰的回答"
    )

    print(f"Agent配置创建成功:")
    print(f"  名称: {config.name}")
    print(f"  系统提示词: {config.system_prompt}")
    print(f"  调试模式: {config.debug_mode}")
    print(f"  指令: {config.instructions}")

    return config


def demo_memory_config():
    """记忆配置演示"""
    print("\n=== 记忆配置演示 ===")

    from memory_factory import MemoryConfig

    # 创建记忆配置
    config = MemoryConfig(
        memory_capture_instructions="记录用户的重要信息和偏好",
        add_memories=True,
        update_memories=True,
        delete_memories=False,
        retrieval_method="last_n",
        retrieval_limit=10,
        debug_mode=True
    )

    print(f"记忆配置创建成功:")
    print(f"  添加记忆: {config.add_memories}")
    print(f"  更新记忆: {config.update_memories}")
    print(f"  删除记忆: {config.delete_memories}")
    print(f"  检索方法: {config.retrieval_method}")
    print(f"  检索限制: {config.retrieval_limit}")

    return config


def demo_system_config():
    """系统配置演示"""
    print("\n=== 系统配置演示 ===")

    from agent_factory import AgentConfig
    from memory_factory import MemoryConfig
    from composer import AgentSystemConfig

    # 创建Agent配置
    agent_config = AgentConfig(
        name="qa_agent",
        system_prompt="专业的问答助手",
        instructions="提供准确、有用的信息",
        enable_user_memories=True,
        debug_mode=False
    )

    # 创建记忆配置
    memory_config = MemoryConfig(
        memory_capture_instructions="记录对话中的重要信息",
        add_memories=True,
        update_memories=True,
        retrieval_method="agentic"
    )

    # 创建系统配置
    system_config = AgentSystemConfig(
        system_name="qa_system",
        description="问答助手系统",
        agent_config=agent_config,
        memory_config=memory_config,
        user_id="demo_user",
        session_id="demo_session",
        debug_mode=True,
        response_stream=False
    )

    print(f"系统配置创建成功:")
    print(f"  系统名称: {system_config.system_name}")
    print(f"  描述: {system_config.description}")
    print(f"  Agent名称: {system_config.agent_config.name}")
    print(f"  用户ID: {system_config.user_id}")
    print(f"  会话ID: {system_config.session_id}")
    print(f"  调试模式: {system_config.debug_mode}")
    print(f"  响应流: {system_config.response_stream}")

    return system_config


def demo_agent_variations():
    """Agent变体演示"""
    print("\n=== Agent变体演示 ===")

    from agent_factory import (
        AgentConfig
    )

    # 问答Agent配置
    qa_config = AgentConfig(
        name="qa_agent",
        system_prompt="专业编程问答助手",
        instructions="提供准确的技术解答"
    )
    print(f"问答Agent: {qa_config.name}")

    # 任务Agent配置
    task_config = AgentConfig(
        name="task_agent",
        system_prompt="任务执行助手",
        instructions="高效完成任务"
    )
    print(f"任务Agent: {task_config.name}")

    # 研究Agent配置
    research_config = AgentConfig(
        name="research_agent",
        system_prompt="研究助手",
        instructions="提供深入的研究分析"
    )
    print(f"研究Agent: {research_config.name}")

    # 自定义Agent配置
    custom_config = AgentConfig(
        name="custom_agent",
        system_prompt="数据分析师",
        instructions="确保数据准确性，保护隐私"
    )
    print(f"自定义Agent: {custom_config.name}")

    return [qa_config, task_config, research_config, custom_config]


def demo_memory_variations():
    """记忆变体演示"""
    print("\n=== 记忆变体演示 ===")

    from memory_factory import (
        MemoryConfig
    )

    # 对话记忆配置
    conv_config = MemoryConfig(
        memory_capture_instructions="记录对话的重要内容和上下文"
    )
    print(f"对话记忆: {type(conv_config).__name__}")

    # 个人信息记忆配置
    personal_config = MemoryConfig(
        memory_capture_instructions="记录用户的个人信息和偏好"
    )
    print(f"个人信息记忆: {type(personal_config).__name__}")

    # 任务记忆配置
    task_config = MemoryConfig(
        memory_capture_instructions="记录任务相关的信息和进度"
    )
    print(f"任务记忆: {type(task_config).__name__}")

    # 学习记忆配置
    learning_config = MemoryConfig(
        memory_capture_instructions="记录学习内容和进展"
    )
    print(f"学习记忆: {type(learning_config).__name__}")

    return [conv_config, personal_config, task_config, learning_config]


def demo_configuration_combinations():
    """配置组合演示"""
    print("\n=== 配置组合演示 ===")

    # 创建不同类型的Agent配置
    configs = []

    # 1. 基础问答Agent
    from agent_factory import AgentConfig
    from memory_factory import MemoryConfig
    from composer import AgentSystemConfig

    qa_system = AgentSystemConfig(
        system_name="simple_qa",
        agent_config=AgentConfig(
            name="qa_agent",
            system_prompt="简单问答助手"
        ),
        memory_config=MemoryConfig(
            add_memories=True,
            retrieval_method="last_n"
        )
    )
    configs.append(qa_system)

    # 2. 任务执行Agent
    task_system = AgentSystemConfig(
        system_name="task_executor",
        agent_config=AgentConfig(
            name="task_agent",
            system_prompt="任务执行助手",
            instructions="高效完成指定任务"
        ),
        memory_config=MemoryConfig(
            memory_capture_instructions="记录任务信息和执行结果",
            retrieval_method="agentic"
        )
    )
    configs.append(task_system)

    # 3. 个人助理Agent
    assistant_system = AgentSystemConfig(
        system_name="personal_assistant",
        agent_config=AgentConfig(
            name="assistant",
            system_prompt="个人助理",
            instructions="提供个性化的帮助和建议",
            enable_user_memories=True
        ),
        memory_config=MemoryConfig(
            memory_capture_instructions="记录用户偏好和个人信息",
            retrieval_method="agentic",
            retrieval_limit=20
        )
    )
    configs.append(assistant_system)

    # 显示配置信息
    for i, config in enumerate(configs, 1):
        print(f"\n配置 {i}: {config.system_name}")
        print(f"  Agent: {config.agent_config.name}")
        print(f"  记忆管理: {'是' if config.memory_config else '否'}")
        print(f"  用户记忆: {'是' if config.agent_config.enable_user_memories else '否'}")
        if config.memory_config:
            print(f"  检索方法: {config.memory_config.retrieval_method}")

    return configs


def demo_usage_patterns():
    """使用模式演示"""
    print("\n=== 使用模式演示 ===")

    print("模式1: 简单问答系统")
    print("- 创建基础问答Agent")
    print("- 添加简单记忆功能")
    print("- 适合日常对话场景")

    print("\n模式2: 任务执行系统")
    print("- 创建任务导向Agent")
    print("- 添加任务记忆管理")
    print("- 适合特定任务场景")

    print("\n模式3: 个人助理系统")
    print("- 创建个性化Agent")
    print("- 添加多类型记忆管理")
    print("- 适合长期用户服务")

    print("\n模式4: 专业领域系统")
    print("- 创建领域专用Agent")
    print("- 添加专业知识记忆")
    print("- 适合专业咨询场景")

    print("\n模式5: 多Agent协作系统")
    print("- 创建多个专用Agent")
    print("- 共享记忆和工具")
    print("- 适合复杂任务场景")


def run_simple_demo():
    """运行简化演示"""
    print("Agno模块化组件简化演示")
    print("=" * 50)

    try:
        # 基础演示
        demo_basic_agent_creation()
        demo_memory_config()
        demo_system_config()

        # 变体演示
        demo_agent_variations()
        demo_memory_variations()

        # 组合演示
        demo_configuration_combinations()

        # 使用模式演示
        demo_usage_patterns()

        print("\n" + "=" * 50)
        print("简化演示完成！")
        print("\n下一步:")
        print("- 安装必要的依赖: pip install agno")
        print("- 配置真实的AI模型")
        print("- 添加MCP工具支持")
        print("- 集成到实际应用中")

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_simple_demo()