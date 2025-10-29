"""
Agno模块化组件测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List

import sys
import os
# 添加agno_modular目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agno_modular'))

# 导入配置类（独立于agno框架）
from core.agno_modular.agent_factory import (
    AgentConfig
)
from core.agno_modular.mcp_factory import (
    MCPConfig
)
from core.agno_modular.memory_factory import (
    MemoryConfig
)
from core.agno_modular.composer import (
    AgentSystemConfig
)

# 只有在agno可用时才导入相关类
try:
    from core.agno.models.base import Model
    from core.agno.models.openai import OpenAIChat
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    # 创建模拟的Model类用于测试
    class Model:
        def __init__(self, model_id: str):
            self.id = model_id

# 导入工厂函数（使用相对导入）
try:
    from core.agno_modular.agent_factory import (
        create_agent,
        create_qa_agent,
        create_task_agent,
        create_custom_agent
    )
    from core.agno_modular.mcp_factory import (
        create_mcp_tools,
        create_filesystem_mcp,
        create_multi_mcp_tools
    )
    from core.agno_modular.memory_factory import (
        create_memory_manager,
        create_conversation_memory,
        create_multi_memory_system
    )
    from core.agno_modular.composer import (
        compose_agent_system,
        create_qa_system,
        create_personal_assistant_system
    )
    USE_RELATIVE_IMPORT = True
except ImportError:
    # 回退到直接导入
    try:
        from agent_factory import (
            create_agent,
            create_qa_agent,
            create_task_agent,
            create_custom_agent
        )
        from mcp_factory import (
            create_mcp_tools,
            create_filesystem_mcp,
            create_multi_mcp_tools
        )
        from memory_factory import (
            create_memory_manager,
            create_conversation_memory,
            create_multi_memory_system
        )
        from composer import (
            compose_agent_system,
            create_qa_system,
            create_personal_assistant_system
        )
        USE_RELATIVE_IMPORT = False
    except ImportError as e:
        print(f"无法导入工厂函数: {e}")
        create_agent = None
        create_qa_agent = None
        create_task_agent = None
        create_custom_agent = None
        create_mcp_tools = None
        create_filesystem_mcp = None
        create_multi_mcp_tools = None
        create_memory_manager = None
        create_conversation_memory = None
        create_multi_memory_system = None
        compose_agent_system = None
        create_qa_system = None
        create_personal_assistant_system = None


def skip_if_not_available(func):
    """装饰器：如果依赖不可用则跳过测试"""
    def wrapper(self, *args, **kwargs):
        if not AGNO_AVAILABLE and 'model' in func.__code__.co_varnames:
            self.skipTest("agno库不可用，跳过测试")
        if func.__name__.startswith('test_') and globals().get(func.__name__.replace('test_', 'create_')) is None:
            self.skipTest("工厂函数不可用，跳过测试")
        return func(self, *args, **kwargs)
    return wrapper


class TestAgentFactory(unittest.TestCase):
    """测试Agent工厂"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock(spec=Model)
        self.mock_model.id = "test-model"

    def test_create_agent_basic(self):
        """测试创建基础Agent"""
        config = AgentConfig(
            name="test_agent",
            model=self.mock_model,
            system_prompt="测试Agent"
        )

        agent = create_agent(config)

        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.model, self.mock_model)

    def test_create_qa_agent(self):
        """测试创建问答Agent"""
        agent = create_qa_agent(
            model=self.mock_model,
            system_prompt="定制问答提示词"
        )

        self.assertEqual(agent.name, "qa_agent")
        self.assertEqual(agent.model, self.mock_model)

    def test_create_task_agent(self):
        """测试创建任务Agent"""
        agent = create_task_agent(
            model=self.mock_model,
            task_description="测试任务"
        )

        self.assertEqual(agent.name, "task_agent")
        self.assertEqual(agent.model, self.mock_model)

    def test_create_custom_agent(self):
        """测试创建自定义Agent"""
        agent = create_custom_agent(
            model=self.mock_model,
            role="测试角色",
            capabilities=["能力1", "能力2"],
            constraints=["约束1"]
        )

        self.assertEqual(agent.name, "custom_测试角色")
        self.assertEqual(agent.model, self.mock_model)

    def test_agent_config_defaults(self):
        """测试Agent配置默认值"""
        config = AgentConfig()
        self.assertEqual(config.name, "agent")
        self.assertIsNone(config.model)
        self.assertFalse(config.debug_mode)


class TestMCPFactory(unittest.TestCase):
    """测试MCP工厂"""

    def test_create_mcp_tools_basic(self):
        """测试创建基础MCP工具"""
        config = MCPConfig(
            name="test_mcp",
            server_command="test-command",
            server_args=["--test"]
        )

        with patch('agno_modular.mcp_factory.MCPTools') as mock_mcp_tools:
            mock_instance = Mock()
            mock_mcp_tools.return_value = mock_instance

            result = create_mcp_tools(config)

            mock_mcp_tools.assert_called_once_with(
                name="test_mcp",
                description=None,
                server_url=None,
                server_command="test-command",
                server_args=["--test"],
                server_env={},
                include_tools=None,
                exclude_tools=None,
                timeout=30,
                max_retries=3,
                connection_check_interval=5,
                debug_mode=False,
                auto_connect=True
            )
            self.assertEqual(result, mock_instance)

    def test_create_filesystem_mcp(self):
        """测试创建文件系统MCP工具"""
        with patch('agno_modular.mcp_factory.MCPTools') as mock_mcp_tools:
            mock_instance = Mock()
            mock_mcp_tools.return_value = mock_instance

            result = create_filesystem_mcp("/test/path", name="test_fs")

            self.assertEqual(result, mock_instance)
            mock_mcp_tools.assert_called_once()

    def test_create_multi_mcp_tools(self):
        """测试创建多MCP工具"""
        config1 = MCPConfig(name="mcp1", server_command="cmd1")
        config2 = MCPConfig(name="mcp2", server_command="cmd2")

        with patch('agno_modular.mcp_factory.MultiMCPTools') as mock_multi_mcp:
            with patch('agno_modular.mcp_factory.create_mcp_tools') as mock_create:
                mock_multi_instance = Mock()
                mock_multi_mcp.return_value = mock_multi_instance
                mock_tool1 = Mock()
                mock_tool2 = Mock()
                mock_create.side_effect = [mock_tool1, mock_tool2]

                result = create_multi_mcp_tools([config1, config2])

                self.assertEqual(result, mock_multi_instance)
                self.assertEqual(mock_create.call_count, 2)
                mock_multi_instance.add_mcp_tools.assert_called()


class TestMemoryFactory(unittest.TestCase):
    """测试记忆工厂"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock(spec=Model)
        self.mock_db = Mock()

    def test_create_memory_manager_basic(self):
        """测试创建基础记忆管理器"""
        config = MemoryConfig(
            model=self.mock_model,
            db=self.mock_db,
            debug_mode=True
        )

        with patch('agno_modular.memory_factory.MemoryManager') as mock_memory_manager:
            mock_instance = Mock()
            mock_memory_manager.return_value = mock_instance

            result = create_memory_manager(config)

            mock_memory_manager.assert_called_once_with(
                model=self.mock_model,
                system_message=None,
                memory_capture_instructions=None,
                additional_instructions=None,
                db=self.mock_db,
                delete_memories=False,
                update_memories=True,
                add_memories=True,
                clear_memories=False,
                debug_mode=True
            )
            self.assertEqual(result, mock_instance)

    def test_create_conversation_memory(self):
        """测试创建对话记忆管理器"""
        with patch('agno_modular.memory_factory.MemoryManager') as mock_memory_manager:
            mock_instance = Mock()
            mock_memory_manager.return_value = mock_instance

            result = create_conversation_memory(
                model=self.mock_model,
                db=self.mock_db
            )

            self.assertEqual(result, mock_instance)
            mock_memory_manager.assert_called_once()

    def test_create_multi_memory_system(self):
        """测试创建多记忆系统"""
        with patch('agno_modular.memory_factory.MemoryManager') as mock_memory_manager:
            mock_instance1 = Mock()
            mock_instance2 = Mock()
            mock_memory_manager.side_effect = [mock_instance1, mock_instance2]

            result = create_multi_memory_system(
                model=self.mock_model,
                db=self.mock_db,
                memory_types=["conversation", "personal"]
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(len(result), 2)
            self.assertIn("conversation", result)
            self.assertIn("personal", result)


class TestComposer(unittest.TestCase):
    """测试组合器"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock(spec=Model)
        self.mock_agent = Mock()
        self.mock_memory_manager = Mock()
        self.mock_mcp_tools = Mock()

    def test_compose_agent_system_basic(self):
        """测试组合基础Agent系统"""
        agent_config = AgentConfig(
            name="test_agent",
            model=self.mock_model
        )
        memory_config = MemoryConfig(model=self.mock_model)
        mcp_config = MCPConfig(name="test_mcp", server_command="test")

        system_config = AgentSystemConfig(
            system_name="test_system",
            agent_config=agent_config,
            memory_config=memory_config,
            mcp_configs=[mcp_config]
        )

        with patch('agno_modular.composer.create_agent') as mock_create_agent:
            with patch('agno_modular.composer.create_memory_manager') as mock_create_memory:
                with patch('agno_modular.composer.create_mcp_tools') as mock_create_mcp:
                    mock_create_agent.return_value = self.mock_agent
                    mock_create_memory.return_value = self.mock_memory_manager
                    mock_create_mcp.return_value = self.mock_mcp_tools

                    result = compose_agent_system(system_config)

                    self.assertEqual(result.agent, self.mock_agent)
                    self.assertEqual(result.memory_managers, self.mock_memory_manager)
                    self.assertEqual(len(result.mcp_tools), 1)
                    self.assertEqual(result.mcp_tools[0], self.mock_mcp_tools)

    def test_create_qa_system(self):
        """测试创建问答系统"""
        with patch('agno_modular.composer.compose_agent_system') as mock_compose:
            mock_system = Mock()
            mock_compose.return_value = mock_system

            result = create_qa_system(model=self.mock_model)

            self.assertEqual(result, mock_system)
            mock_compose.assert_called_once()

    def test_create_personal_assistant_system(self):
        """测试创建个人助理系统"""
        with patch('agno_modular.composer.compose_agent_system') as mock_compose:
            mock_system = Mock()
            mock_compose.return_value = mock_system

            result = create_personal_assistant_system(
                model=self.mock_model,
                user_preferences={"language": "中文"}
            )

            self.assertEqual(result, mock_system)
            mock_compose.assert_called_once()


class TestIntegration(unittest.TestCase):
    """集成测试"""

    @patch('agno_modular.agent_factory.Agent')
    @patch('agno_modular.memory_factory.MemoryManager')
    @patch('agno_modular.mcp_factory.MCPTools')
    def test_end_to_end_system_creation(self, mock_mcp_tools, mock_memory_manager, mock_agent):
        """端到端系统创建测试"""
        # 设置mock
        mock_agent_instance = Mock()
        mock_memory_instance = Mock()
        mock_mcp_instance = Mock()

        mock_agent.return_value = mock_agent_instance
        mock_memory_manager.return_value = mock_memory_instance
        mock_mcp_tools.return_value = mock_mcp_instance

        # 创建配置
        agent_config = AgentConfig(name="integration_test", model=self.mock_model)
        memory_config = MemoryConfig(model=self.mock_model)
        mcp_config = MCPConfig(name="integration_mcp", server_command="test")

        system_config = AgentSystemConfig(
            agent_config=agent_config,
            memory_config=memory_config,
            mcp_configs=[mcp_config]
        )

        # 组合系统
        system = compose_agent_system(system_config)

        # 验证
        self.assertEqual(system.agent, mock_agent_instance)
        self.assertEqual(system.memory_managers, mock_memory_instance)
        self.assertEqual(len(system.mcp_tools), 1)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestAgentFactory,
        TestMCPFactory,
        TestMemoryFactory,
        TestComposer,
        TestIntegration
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n所有测试通过！")
    else:
        print("\n部分测试失败，请检查代码。")