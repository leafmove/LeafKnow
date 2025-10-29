"""
Agno模块化组件工厂函数测试
测试工厂函数的创建和配置功能
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加agno_modular目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agno_modular'))

# 导入配置类
from core.agno_modular.agent_factory import AgentConfig
from core.agno_modular.mcp_factory import MCPConfig
from core.agno_modular.memory_factory import MemoryConfig
from core.agno_modular.composer import AgentSystemConfig


class TestAgentFactory(unittest.TestCase):
    """测试Agent工厂函数"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock()
        self.mock_model.id = "gpt-4"

    @patch('agent_factory.Agent')
    def test_create_agent_basic(self, mock_agent_class):
        """测试创建基础Agent"""
        # 设置mock
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        # 创建配置
        config = AgentConfig(
            name="test_agent",
            model=self.mock_model,
            system_prompt="测试系统提示词"
        )

        # 导入并测试工厂函数
        from core.agno_modular.agent_factory import create_agent
        result = create_agent(config)

        # 验证
        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent_instance)

    @patch('agent_factory.Agent')
    def test_create_qa_agent(self, mock_agent_class):
        """测试创建问答Agent"""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        from core.agno_modular.agent_factory import create_qa_agent
        result = create_qa_agent(
            model=self.mock_model,
            system_prompt="定制问答提示词"
        )

        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent_instance)

    @patch('agent_factory.Agent')
    def test_create_task_agent(self, mock_agent_class):
        """测试创建任务Agent"""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        from core.agno_modular.agent_factory import create_task_agent
        result = create_task_agent(
            model=self.mock_model,
            task_description="测试任务"
        )

        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent_instance)

    @patch('agent_factory.Agent')
    def test_create_research_agent(self, mock_agent_class):
        """测试创建研究Agent"""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        from core.agno_modular.agent_factory import create_research_agent
        result = create_research_agent(
            model=self.mock_model,
            research_domain="人工智能"
        )

        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent_instance)

    @patch('agent_factory.Agent')
    def test_create_creative_agent(self, mock_agent_class):
        """测试创建创意Agent"""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        from core.agno_modular.agent_factory import create_creative_agent
        result = create_creative_agent(
            model=self.mock_model,
            creative_domain="编程"
        )

        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent_instance)

    @patch('agent_factory.Agent')
    def test_create_custom_agent(self, mock_agent_class):
        """测试创建自定义Agent"""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        from core.agno_modular.agent_factory import create_custom_agent
        result = create_custom_agent(
            model=self.mock_model,
            role="测试角色",
            capabilities=["能力1", "能力2"],
            constraints=["约束1"]
        )

        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent_instance)


class TestMCPFactory(unittest.TestCase):
    """测试MCP工厂函数"""

    @patch('mcp_factory.MCPTools')
    def test_create_mcp_tools(self, mock_mcp_tools_class):
        """测试创建MCP工具"""
        mock_mcp_instance = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_instance

        config = MCPConfig(
            name="test_mcp",
            server_command="test-command",
            server_args=["--test"]
        )

        from core.agno_modular.mcp_factory import create_mcp_tools
        result = create_mcp_tools(config)

        mock_mcp_tools_class.assert_called_once()
        self.assertEqual(result, mock_mcp_instance)

    @patch('mcp_factory.MCPTools')
    def test_create_filesystem_mcp(self, mock_mcp_tools_class):
        """测试创建文件系统MCP工具"""
        mock_mcp_instance = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_instance

        from core.agno_modular.mcp_factory import create_filesystem_mcp
        result = create_filesystem_mcp("/test/path", name="test_fs")

        mock_mcp_tools_class.assert_called_once()
        self.assertEqual(result, mock_mcp_instance)

    @patch('mcp_factory.MCPTools')
    def test_create_database_mcp(self, mock_mcp_tools_class):
        """测试创建数据库MCP工具"""
        mock_mcp_instance = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_instance

        from core.agno_modular.mcp_factory import create_database_mcp
        result = create_database_mcp(
            connection_string="test_db_url",
            db_type="postgresql"
        )

        mock_mcp_tools_class.assert_called_once()
        self.assertEqual(result, mock_mcp_instance)

    @patch('mcp_factory.MCPTools')
    def test_create_web_search_mcp(self, mock_mcp_tools_class):
        """测试创建Web搜索MCP工具"""
        mock_mcp_instance = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_instance

        from core.agno_modular.mcp_factory import create_web_search_mcp
        result = create_web_search_mcp(
            api_key="test_key",
            search_engine="brave"
        )

        mock_mcp_tools_class.assert_called_once()
        self.assertEqual(result, mock_mcp_instance)

    @patch('mcp_factory.MultiMCPTools')
    @patch('mcp_factory.create_mcp_tools')
    def test_create_multi_mcp_tools(self, mock_create_mcp, mock_multi_mcp_class):
        """测试创建多MCP工具"""
        mock_mcp1 = Mock()
        mock_mcp2 = Mock()
        mock_create_mcp.side_effect = [mock_mcp1, mock_mcp2]

        mock_multi_instance = Mock()
        mock_multi_mcp_class.return_value = mock_multi_instance

        config1 = MCPConfig(name="mcp1", server_command="cmd1")
        config2 = MCPConfig(name="mcp2", server_command="cmd2")

        from core.agno_modular.mcp_factory import create_multi_mcp_tools
        result = create_multi_mcp_tools([config1, config2])

        self.assertEqual(mock_create_mcp.call_count, 2)
        mock_multi_mcp_class.assert_called_once()
        self.assertEqual(result, mock_multi_instance)

    @patch('mcp_factory.MCPTools')
    def test_create_github_mcp(self, mock_mcp_tools_class):
        """测试创建GitHub MCP工具"""
        mock_mcp_instance = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_instance

        from core.agno_modular.mcp_factory import create_github_mcp
        result = create_github_mcp(token="test_token")

        mock_mcp_tools_class.assert_called_once()
        self.assertEqual(result, mock_mcp_instance)


class TestMemoryFactory(unittest.TestCase):
    """测试记忆工厂函数"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock()
        self.mock_db = Mock()

    @patch('memory_factory.MemoryManager')
    def test_create_memory_manager(self, mock_memory_manager_class):
        """测试创建记忆管理器"""
        mock_memory_instance = Mock()
        mock_memory_manager_class.return_value = mock_memory_instance

        config = MemoryConfig(
            model=self.mock_model,
            debug_mode=True
        )

        from core.agno_modular.memory_factory import create_memory_manager
        result = create_memory_manager(config)

        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_instance)

    @patch('memory_factory.MemoryManager')
    def test_create_conversation_memory(self, mock_memory_manager_class):
        """测试创建对话记忆管理器"""
        mock_memory_instance = Mock()
        mock_memory_manager_class.return_value = mock_memory_instance

        from core.agno_modular.memory_factory import create_conversation_memory
        result = create_conversation_memory(
            model=self.mock_model,
            db=self.mock_db
        )

        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_instance)

    @patch('memory_factory.MemoryManager')
    def test_create_personal_memory(self, mock_memory_manager_class):
        """测试创建个人信息记忆管理器"""
        mock_memory_instance = Mock()
        mock_memory_manager_class.return_value = mock_memory_instance

        from core.agno_modular.memory_factory import create_personal_memory
        result = create_personal_memory(
            model=self.mock_model,
            db=self.mock_db
        )

        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_instance)

    @patch('memory_factory.MemoryManager')
    def test_create_task_memory(self, mock_memory_manager_class):
        """测试创建任务记忆管理器"""
        mock_memory_instance = Mock()
        mock_memory_manager_class.return_value = mock_memory_instance

        from core.agno_modular.memory_factory import create_task_memory
        result = create_task_memory(
            model=self.mock_model,
            db=self.mock_db
        )

        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_instance)

    @patch('memory_factory.MemoryManager')
    def test_create_learning_memory(self, mock_memory_manager_class):
        """测试创建学习记忆管理器"""
        mock_memory_instance = Mock()
        mock_memory_manager_class.return_value = mock_memory_instance

        from core.agno_modular.memory_factory import create_learning_memory
        result = create_learning_memory(
            model=self.mock_model,
            db=self.mock_db
        )

        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_instance)

    @patch('memory_factory.MemoryManager')
    def test_create_preference_memory(self, mock_memory_manager_class):
        """测试创建偏好记忆管理器"""
        mock_memory_instance = Mock()
        mock_memory_manager_class.return_value = mock_memory_instance

        from core.agno_modular.memory_factory import create_preference_memory
        result = create_preference_memory(
            model=self.mock_model,
            db=self.mock_db
        )

        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_instance)

    @patch('memory_factory.MemoryManager')
    def test_create_multi_memory_system(self, mock_memory_manager_class):
        """测试创建多记忆系统"""
        mock_memory1 = Mock()
        mock_memory2 = Mock()
        mock_memory_manager_class.side_effect = [mock_memory1, mock_memory2]

        from core.agno_modular.memory_factory import create_multi_memory_system
        result = create_multi_memory_system(
            model=self.mock_model,
            db=self.mock_db,
            memory_types=["conversation", "personal"]
        )

        self.assertEqual(mock_memory_manager_class.call_count, 2)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn("conversation", result)
        self.assertIn("personal", result)


class TestComposer(unittest.TestCase):
    """测试组合器函数"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock()
        self.mock_agent = Mock()
        self.mock_memory_manager = Mock()
        self.mock_mcp_tools = Mock()

    @patch('composer.create_agent')
    @patch('composer.create_memory_manager')
    @patch('composer.create_mcp_tools')
    def test_compose_agent_system(self, mock_create_mcp, mock_create_memory, mock_create_agent):
        """测试组合Agent系统"""
        mock_create_agent.return_value = self.mock_agent
        mock_create_memory.return_value = self.mock_memory_manager
        mock_create_mcp.return_value = self.mock_mcp_tools

        agent_config = AgentConfig(name="test_agent", model=self.mock_model)
        memory_config = MemoryConfig(model=self.mock_model)
        mcp_config = MCPConfig(name="test_mcp", server_command="test")

        system_config = AgentSystemConfig(
            system_name="test_system",
            agent_config=agent_config,
            memory_config=memory_config,
            mcp_configs=[mcp_config]
        )

        from core.agno_modular.composer import compose_agent_system, AgentSystem
        with patch.object(AgentSystem, '__init__', return_value=None):
            result = compose_agent_system(system_config)

        mock_create_agent.assert_called_once_with(agent_config)
        mock_create_memory.assert_called_once_with(memory_config)
        mock_create_mcp.assert_called_once_with(mcp_config)

    @patch('composer.compose_agent_system')
    def test_create_qa_system(self, mock_compose):
        """测试创建问答系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        from core.agno_modular.composer import create_qa_system
        result = create_qa_system(model=self.mock_model)

        mock_compose.assert_called_once()
        self.assertEqual(result, mock_system)

    @patch('composer.compose_agent_system')
    def test_create_task_system(self, mock_compose):
        """测试创建任务系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        from core.agno_modular.composer import create_task_system
        result = create_task_system(
            model=self.mock_model,
            task_description="测试任务"
        )

        mock_compose.assert_called_once()
        self.assertEqual(result, mock_system)

    @patch('composer.compose_agent_system')
    def test_create_research_system(self, mock_compose):
        """测试创建研究系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        from core.agno_modular.composer import create_research_system
        result = create_research_system(
            model=self.mock_model,
            research_domain="AI"
        )

        mock_compose.assert_called_once()
        self.assertEqual(result, mock_system)

    @patch('composer.compose_agent_system')
    def test_create_personal_assistant_system(self, mock_compose):
        """测试创建个人助理系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        from core.agno_modular.composer import create_personal_assistant_system
        result = create_personal_assistant_system(
            model=self.mock_model,
            user_preferences={"language": "中文"}
        )

        mock_compose.assert_called_once()
        self.assertEqual(result, mock_system)

    @patch('composer.compose_agent_system')
    def test_create_dynamic_system(self, mock_compose):
        """测试创建动态系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        from core.agno_modular.composer import create_dynamic_system
        result = create_dynamic_system(
            model=self.mock_model,
            system_prompt="动态系统提示词"
        )

        mock_compose.assert_called_once()
        self.assertEqual(result, mock_system)


class TestIntegrationFactory(unittest.TestCase):
    """集成工厂测试"""

    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock()

    @patch('composer.create_agent')
    def test_end_to_end_qa_system(self, mock_create_agent):
        """端到端问答系统测试"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        from core.agno_modular.composer import create_qa_system
        qa_system = create_qa_system(
            model=self.mock_model,
            system_prompt="测试问答系统"
        )

        mock_create_agent.assert_called_once()
        self.assertIsNotNone(qa_system)

    @patch('composer.compose_agent_system')
    def test_end_to_end_multi_agent_system(self, mock_compose):
        """端到端多Agent系统测试"""
        mock_systems = [Mock(), Mock()]
        mock_compose.side_effect = mock_systems

        from core.agno_modular.composer import create_multi_agent_system
        agent_configs = [
            AgentConfig(name="agent1"),
            AgentConfig(name="agent2")
        ]

        result = create_multi_agent_system(agent_configs=agent_configs)

        self.assertEqual(mock_compose.call_count, 2)
        self.assertEqual(len(result), 2)


def run_factory_tests():
    """运行工厂函数测试"""
    print("运行Agno模块化组件工厂函数测试")
    print("=" * 50)

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestAgentFactory,
        TestMCPFactory,
        TestMemoryFactory,
        TestComposer,
        TestIntegrationFactory
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("所有工厂函数测试通过！")
        print(f"运行了 {result.testsRun} 个测试")
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_factory_tests()
    sys.exit(0 if success else 1)