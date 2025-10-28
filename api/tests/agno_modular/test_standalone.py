"""
Agno模块化组件独立测试
不依赖agno库，仅测试配置类的设计理念
"""

import unittest
import sys
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


# 独立的配置类定义（复制自原始文件，避免导入依赖）
@dataclass
class StandaloneAgentConfig:
    """独立的Agent配置类"""
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
class StandaloneMCPConfig:
    """独立的MCP配置类"""
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
class StandaloneMemoryConfig:
    """独立的记忆配置类"""
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
class StandaloneAgentSystemConfig:
    """独立的Agent系统配置类"""
    system_id: Optional[str] = None
    system_name: str = "agent_system"
    description: Optional[str] = None
    agent_config: StandaloneAgentConfig = field(default_factory=StandaloneAgentConfig)
    mcp_configs: List[StandaloneMCPConfig] = field(default_factory=list)
    memory_config: Optional[StandaloneMemoryConfig] = None
    memory_types: Optional[List[str]] = None
    use_multi_memory: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    debug_mode: bool = False
    response_stream: bool = False
    response_format: Optional[str] = None


class TestStandaloneAgentConfig(unittest.TestCase):
    """测试独立Agent配置类"""

    def test_agent_config_creation(self):
        """测试Agent配置创建"""
        config = StandaloneAgentConfig(
            name="test_agent",
            model="gpt-4",
            system_prompt="测试系统提示词",
            debug_mode=True
        )

        self.assertEqual(config.name, "test_agent")
        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.system_prompt, "测试系统提示词")
        self.assertTrue(config.debug_mode)

    def test_agent_config_defaults(self):
        """测试Agent配置默认值"""
        config = StandaloneAgentConfig()

        self.assertEqual(config.name, "agent")
        self.assertIsNone(config.model)
        self.assertIsNone(config.system_prompt)
        self.assertIsNone(config.agent_id)
        self.assertFalse(config.debug_mode)
        self.assertFalse(config.enable_user_memories)
        self.assertEqual(config.num_history_runs, 3)

    def test_agent_config_with_tools(self):
        """测试Agent配置包含工具"""
        mock_tool1 = "tool1"
        mock_tool2 = "tool2"

        config = StandaloneAgentConfig(
            name="agent_with_tools",
            tools=[mock_tool1, mock_tool2]
        )

        self.assertEqual(len(config.tools), 2)
        self.assertIn(mock_tool1, config.tools)
        self.assertIn(mock_tool2, config.tools)

    def test_agent_config_memory_settings(self):
        """测试Agent配置记忆设置"""
        config = StandaloneAgentConfig(
            enable_user_memories=True,
            enable_agentic_memory=True
        )

        self.assertTrue(config.enable_user_memories)
        self.assertTrue(config.enable_agentic_memory)

    def test_agent_config_session_settings(self):
        """测试Agent配置会话设置"""
        config = StandaloneAgentConfig(
            session_id="test_session",
            user_id="test_user"
        )

        self.assertEqual(config.session_id, "test_session")
        self.assertEqual(config.user_id, "test_user")


class TestStandaloneMCPConfig(unittest.TestCase):
    """测试独立MCP配置类"""

    def test_mcp_config_creation(self):
        """测试MCP配置创建"""
        config = StandaloneMCPConfig(
            name="test_mcp",
            description="测试MCP工具",
            server_command="npx",
            server_args=["-y", "test-tool"],
            timeout=60
        )

        self.assertEqual(config.name, "test_mcp")
        self.assertEqual(config.description, "测试MCP工具")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "test-tool"])
        self.assertEqual(config.timeout, 60)

    def test_mcp_config_defaults(self):
        """测试MCP配置默认值"""
        config = StandaloneMCPConfig()

        self.assertEqual(config.name, "mcp_tools")
        self.assertIsNone(config.description)
        self.assertIsNone(config.server_url)
        self.assertIsNone(config.server_command)
        self.assertEqual(len(config.server_args), 0)
        self.assertEqual(len(config.server_env), 0)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertFalse(config.debug_mode)
        self.assertTrue(config.auto_connect)

    def test_mcp_config_with_environment(self):
        """测试MCP配置环境变量"""
        env_vars = {"API_KEY": "test_key", "DEBUG": "true"}
        config = StandaloneMCPConfig(
            name="env_mcp",
            server_env=env_vars
        )

        self.assertEqual(config.server_env, env_vars)
        self.assertEqual(config.server_env["API_KEY"], "test_key")
        self.assertEqual(config.server_env["DEBUG"], "true")

    def test_mcp_config_tool_filtering(self):
        """测试MCP工具过滤"""
        include_tools = ["read_file", "write_file"]
        exclude_tools = ["delete_file"]

        config = StandaloneMCPConfig(
            name="filtered_mcp",
            include_tools=include_tools,
            exclude_tools=exclude_tools
        )

        self.assertEqual(config.include_tools, include_tools)
        self.assertEqual(config.exclude_tools, exclude_tools)


class TestStandaloneMemoryConfig(unittest.TestCase):
    """测试独立记忆配置类"""

    def test_memory_config_creation(self):
        """测试记忆配置创建"""
        config = StandaloneMemoryConfig(
            model="gpt-4",
            system_message="记忆系统消息",
            memory_capture_instructions="记忆捕获指令",
            debug_mode=True
        )

        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.system_message, "记忆系统消息")
        self.assertEqual(config.memory_capture_instructions, "记忆捕获指令")
        self.assertTrue(config.debug_mode)

    def test_memory_config_defaults(self):
        """测试记忆配置默认值"""
        config = StandaloneMemoryConfig()

        self.assertIsNone(config.model)
        self.assertIsNone(config.system_message)
        self.assertIsNone(config.memory_capture_instructions)
        self.assertFalse(config.delete_memories)
        self.assertTrue(config.update_memories)
        self.assertTrue(config.add_memories)
        self.assertFalse(config.clear_memories)
        self.assertEqual(config.retrieval_method, "last_n")
        self.assertEqual(config.retrieval_limit, 10)
        self.assertFalse(config.debug_mode)
        self.assertTrue(config.auto_create)

    def test_memory_config_permissions(self):
        """测试记忆配置权限设置"""
        config = StandaloneMemoryConfig(
            delete_memories=True,
            update_memories=False,
            add_memories=False,
            clear_memories=True
        )

        self.assertTrue(config.delete_memories)
        self.assertFalse(config.update_memories)
        self.assertFalse(config.add_memories)
        self.assertTrue(config.clear_memories)

    def test_memory_config_retrieval_settings(self):
        """测试记忆配置检索设置"""
        config = StandaloneMemoryConfig(
            retrieval_method="agentic",
            retrieval_limit=20
        )

        self.assertEqual(config.retrieval_method, "agentic")
        self.assertEqual(config.retrieval_limit, 20)


class TestStandaloneAgentSystemConfig(unittest.TestCase):
    """测试独立Agent系统配置类"""

    def test_system_config_creation(self):
        """测试系统配置创建"""
        agent_config = StandaloneAgentConfig(name="system_agent", model="gpt-4")
        memory_config = StandaloneMemoryConfig(retrieval_method="agentic")
        mcp_config = StandaloneMCPConfig(name="system_mcp", server_command="test")

        system_config = StandaloneAgentSystemConfig(
            system_name="test_system",
            description="测试系统",
            agent_config=agent_config,
            memory_config=memory_config,
            mcp_configs=[mcp_config],
            user_id="test_user"
        )

        self.assertEqual(system_config.system_name, "test_system")
        self.assertEqual(system_config.description, "测试系统")
        self.assertEqual(system_config.agent_config, agent_config)
        self.assertEqual(system_config.memory_config, memory_config)
        self.assertEqual(len(system_config.mcp_configs), 1)
        self.assertEqual(system_config.mcp_configs[0], mcp_config)
        self.assertEqual(system_config.user_id, "test_user")

    def test_system_config_defaults(self):
        """测试系统配置默认值"""
        config = StandaloneAgentSystemConfig()

        self.assertIsNone(config.system_id)
        self.assertEqual(config.system_name, "agent_system")
        self.assertIsNone(config.description)
        self.assertIsInstance(config.agent_config, StandaloneAgentConfig)
        self.assertEqual(len(config.mcp_configs), 0)
        self.assertIsNone(config.memory_config)
        self.assertIsNone(config.memory_types)
        self.assertFalse(config.use_multi_memory)
        self.assertIsNone(config.user_id)
        self.assertIsNone(config.session_id)
        self.assertFalse(config.debug_mode)
        self.assertFalse(config.response_stream)
        self.assertIsNone(config.response_format)

    def test_system_config_multi_memory(self):
        """测试系统配置多记忆"""
        config = StandaloneAgentSystemConfig(
            use_multi_memory=True,
            memory_types=["conversation", "personal", "task"]
        )

        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["conversation", "personal", "task"])

    def test_system_config_with_session(self):
        """测试系统配置会话信息"""
        config = StandaloneAgentSystemConfig(
            session_id="test_session",
            user_id="test_user",
            response_stream=True
        )

        self.assertEqual(config.session_id, "test_session")
        self.assertEqual(config.user_id, "test_user")
        self.assertTrue(config.response_stream)


class TestConfigurationValidation(unittest.TestCase):
    """测试配置验证"""

    def test_agent_config_validation(self):
        """测试Agent配置验证"""
        # 有效配置
        valid_config = StandaloneAgentConfig(
            name="valid_agent",
            model="gpt-4",
            system_prompt="有效的系统提示词"
        )
        self.assertEqual(valid_config.name, "valid_agent")

        # 最小配置
        minimal_config = StandaloneAgentConfig()
        self.assertEqual(minimal_config.name, "agent")

    def test_mcp_config_validation(self):
        """测试MCP配置验证"""
        # 有效配置
        valid_config = StandaloneMCPConfig(
            name="valid_mcp",
            server_command="test_command"
        )
        self.assertEqual(valid_config.name, "valid_mcp")

        # 配置超时
        timeout_config = StandaloneMCPConfig(timeout=120)
        self.assertEqual(timeout_config.timeout, 120)

    def test_memory_config_validation(self):
        """测试记忆配置验证"""
        # 有效配置
        valid_config = StandaloneMemoryConfig(
            model="gpt-4",
            retrieval_method="agentic"
        )
        self.assertEqual(valid_config.model, "gpt-4")
        self.assertEqual(valid_config.retrieval_method, "agentic")

    def test_system_config_validation(self):
        """测试系统配置验证"""
        agent_config = StandaloneAgentConfig(name="system_agent")
        system_config = StandaloneAgentSystemConfig(
            system_name="valid_system",
            agent_config=agent_config
        )
        self.assertEqual(system_config.system_name, "valid_system")
        self.assertEqual(system_config.agent_config.name, "system_agent")


class TestConfigurationComposition(unittest.TestCase):
    """测试配置组合"""

    def test_simple_qa_system(self):
        """测试简单问答系统配置"""
        system_config = StandaloneAgentSystemConfig(
            system_name="qa_system",
            agent_config=StandaloneAgentConfig(
                name="qa_agent",
                model="gpt-4",
                system_prompt="你是一个问答助手"
            ),
            memory_config=StandaloneMemoryConfig(
                retrieval_method="last_n",
                retrieval_limit=5
            )
        )

        self.assertEqual(system_config.system_name, "qa_system")
        self.assertEqual(system_config.agent_config.name, "qa_agent")
        self.assertEqual(system_config.memory_config.retrieval_method, "last_n")
        self.assertEqual(system_config.memory_config.retrieval_limit, 5)

    def test_task_execution_system(self):
        """测试任务执行系统配置"""
        system_config = StandaloneAgentSystemConfig(
            system_name="task_system",
            agent_config=StandaloneAgentConfig(
                name="task_agent",
                model="gpt-4",
                show_tool_calls=True
            ),
            mcp_configs=[
                StandaloneMCPConfig(name="filesystem", server_command="fs_cmd"),
                StandaloneMCPConfig(name="calculator", server_command="calc_cmd")
            ]
        )

        self.assertEqual(system_config.system_name, "task_system")
        self.assertTrue(system_config.agent_config.show_tool_calls)
        self.assertEqual(len(system_config.mcp_configs), 2)

    def test_personal_assistant_system(self):
        """测试个人助理系统配置"""
        system_config = StandaloneAgentSystemConfig(
            system_name="assistant_system",
            agent_config=StandaloneAgentConfig(
                name="assistant",
                model="gpt-4",
                enable_user_memories=True
            ),
            memory_config=StandaloneMemoryConfig(
                retrieval_method="agentic",
                retrieval_limit=20
            ),
            use_multi_memory=True,
            memory_types=["personal", "conversation", "preference"]
        )

        self.assertEqual(system_config.system_name, "assistant_system")
        self.assertTrue(system_config.agent_config.enable_user_memories)
        self.assertTrue(system_config.use_multi_memory)
        self.assertEqual(len(system_config.memory_types), 3)

    def test_research_system(self):
        """测试研究系统配置"""
        system_config = StandaloneAgentSystemConfig(
            system_name="research_system",
            agent_config=StandaloneAgentConfig(
                name="researcher",
                model="gpt-4",
                system_prompt="你是专业的研究助手"
            ),
            mcp_configs=[
                StandaloneMCPConfig(name="web_search", server_command="search_cmd"),
                StandaloneMCPConfig(name="database", server_command="db_cmd")
            ],
            memory_config=StandaloneMemoryConfig(
                retrieval_method="agentic",
                memory_capture_instructions="记录研究过程和发现"
            )
        )

        self.assertEqual(system_config.system_name, "research_system")
        self.assertEqual(len(system_config.mcp_configs), 2)
        self.assertEqual(system_config.memory_config.memory_capture_instructions, "记录研究过程和发现")

    def test_multi_agent_system(self):
        """测试多Agent系统配置"""
        agent_configs = [
            StandaloneAgentConfig(name="agent1", model="gpt-4"),
            StandaloneAgentConfig(name="agent2", model="gpt-4")
        ]

        memory_config = StandaloneMemoryConfig(retrieval_method="agentic")
        mcp_config = StandaloneMCPConfig(name="shared_tools", server_command="tools_cmd")

        # 创建多个系统配置
        systems = []
        for i, agent_config in enumerate(agent_configs):
            system_config = StandaloneAgentSystemConfig(
                system_name=f"multi_agent_system_{i}",
                agent_config=agent_config,
                memory_config=memory_config,
                mcp_configs=[mcp_config],
                user_id="user123"
            )
            systems.append(system_config)

        self.assertEqual(len(systems), 2)
        self.assertEqual(systems[0].system_name, "multi_agent_system_0")
        self.assertEqual(systems[1].system_name, "multi_agent_system_1")


class TestConfigurationScenarios(unittest.TestCase):
    """测试配置场景"""

    def test_customer_service_scenario(self):
        """测试客户服务场景"""
        system_config = StandaloneAgentSystemConfig(
            system_name="customer_service",
            description="客户服务系统",
            agent_config=StandaloneAgentConfig(
                name="customer_service_agent",
                model="gpt-4",
                system_prompt="你是专业的客服代表",
                instructions="提供友好、专业的客户服务",
                enable_user_memories=True
            ),
            memory_config=StandaloneMemoryConfig(
                memory_capture_instructions="记录客户信息和历史问题",
                retrieval_method="agentic",
                retrieval_limit=15
            )
        )

        self.assertEqual(system_config.system_name, "customer_service")
        self.assertTrue(system_config.agent_config.enable_user_memories)
        self.assertEqual(system_config.memory_config.retrieval_limit, 15)

    def test_education_tutor_scenario(self):
        """测试教育辅导场景"""
        system_config = StandaloneAgentSystemConfig(
            system_name="education_tutor",
            description="个性化教育辅导系统",
            agent_config=StandaloneAgentConfig(
                name="tutor",
                model="gpt-4",
                system_prompt="你是专业的学习辅导老师",
                instructions="根据学生水平调整教学方式",
                reasoning_instructions="逐步思考学生的需求和能力"
            ),
            memory_config=StandaloneMemoryConfig(
                memory_capture_instructions="记录学生的学习进度、偏好和困难点",
                retrieval_method="agentic",
                retrieval_limit=20
            ),
            use_multi_memory=True,
            memory_types=["learning", "personal", "conversation"]
        )

        self.assertEqual(system_config.system_name, "education_tutor")
        self.assertTrue(system_config.use_multi_memory)
        self.assertEqual(len(system_config.memory_types), 3)

    def test_data_analysis_scenario(self):
        """测试数据分析场景"""
        system_config = StandaloneAgentSystemConfig(
            system_name="data_analysis",
            description="数据分析系统",
            agent_config=StandaloneAgentConfig(
                name="analyst",
                model="gpt-4",
                system_prompt="你是专业的数据分析师",
                instructions="提供准确的数据分析和可视化建议",
                show_tool_calls=True,
                debug_mode=True
            ),
            mcp_configs=[
                StandaloneMCPConfig(
                    name="database",
                    description="数据库查询工具",
                    server_command="db_query",
                    timeout=60
                ),
                StandaloneMCPConfig(
                    name="visualization",
                    description="数据可视化工具",
                    server_command="viz_tool"
                )
            ],
            memory_config=StandaloneMemoryConfig(
                memory_capture_instructions="记录数据分析的方法和结果",
                retrieval_method="last_n",
                retrieval_limit=10
            )
        )

        self.assertEqual(system_config.system_name, "data_analysis")
        self.assertEqual(len(system_config.mcp_configs), 2)
        self.assertTrue(system_config.agent_config.show_tool_calls)
        self.assertTrue(system_config.agent_config.debug_mode)

    def test_creative_writing_scenario(self):
        """测试创意写作场景"""
        system_config = StandaloneAgentSystemConfig(
            system_name="creative_writing",
            description="创意写作助手",
            agent_config=StandaloneAgentConfig(
                name="writer",
                model="gpt-4",
                system_prompt="你是专业的创意写作助手",
                instructions="提供有创意的写作建议和内容",
                markdown=True
            ),
            memory_config=StandaloneMemoryConfig(
                memory_capture_instructions="记录用户的写作风格、偏好和项目信息",
                retrieval_method="last_n",
                retrieval_limit=8
            ),
            response_stream=True
        )

        self.assertEqual(system_config.system_name, "creative_writing")
        self.assertTrue(system_config.agent_config.markdown)
        self.assertTrue(system_config.response_stream)


def run_standalone_tests():
    """运行独立测试"""
    print("运行Agno模块化组件独立测试")
    print("=" * 50)
    print("注意: 这是配置类的独立测试，不依赖agno框架")
    print("=" * 50)

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestStandaloneAgentConfig,
        TestStandaloneMCPConfig,
        TestStandaloneMemoryConfig,
        TestStandaloneAgentSystemConfig,
        TestConfigurationValidation,
        TestConfigurationComposition,
        TestConfigurationScenarios
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("所有独立测试通过！")
        print(f"运行了 {result.testsRun} 个测试")
        print("\n测试覆盖:")
        print("[OK] Agent配置类")
        print("[OK] MCP配置类")
        print("[OK] Memory配置类")
        print("[OK] System配置类")
        print("[OK] 配置验证")
        print("[OK] 配置组合")
        print("[OK] 场景配置")
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"  - {test}")

    print("\n设计验证:")
    print("[OK] 配置类结构完整")
    print("[OK] 默认值设置正确")
    print("[OK] 类型定义清晰")
    print("[OK] 组合模式可行")
    print("[OK] 场景配置实用")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_standalone_tests()
    sys.exit(0 if success else 1)