"""
Agent工厂模块单元测试
测试Agent配置和创建功能
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加路径以导入agno_modular模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agno_modular'))

from core.agno_modular.agent_factory import (
    AgentConfig,
    create_agent,
    create_qa_agent,
    create_task_agent,
    create_research_agent,
    create_creative_agent,
    create_custom_agent
)


class TestAgentConfig(unittest.TestCase):
    """测试AgentConfig配置类"""

    def test_default_initialization(self):
        """测试默认初始化"""
        config = AgentConfig()

        self.assertEqual(config.name, "agent")
        self.assertIsNone(config.model)
        self.assertIsNone(config.agent_id)
        self.assertIsNone(config.system_prompt)
        self.assertIsNone(config.instructions)
        self.assertEqual(config.tools, [])
        self.assertIsNone(config.memory_manager)
        self.assertFalse(config.enable_user_memories)
        self.assertFalse(config.enable_agentic_memory)
        self.assertFalse(config.debug_mode)
        self.assertFalse(config.show_tool_calls)
        self.assertFalse(config.markdown)
        self.assertEqual(config.num_history_runs, 3)

    def test_custom_initialization(self):
        """测试自定义初始化"""
        mock_model = Mock()
        tools = [Mock(), Mock()]

        config = AgentConfig(
            name="test_agent",
            model=mock_model,
            agent_id="test_123",
            system_prompt="Test system prompt",
            instructions="Test instructions",
            tools=tools,
            debug_mode=True,
            show_tool_calls=True,
            num_history_runs=5
        )

        self.assertEqual(config.name, "test_agent")
        self.assertEqual(config.model, mock_model)
        self.assertEqual(config.agent_id, "test_123")
        self.assertEqual(config.system_prompt, "Test system prompt")
        self.assertEqual(config.instructions, "Test instructions")
        self.assertEqual(config.tools, tools)
        self.assertTrue(config.debug_mode)
        self.assertTrue(config.show_tool_calls)
        self.assertEqual(config.num_history_runs, 5)

    def test_field_types(self):
        """测试字段类型"""
        config = AgentConfig()

        # 测试基本字段类型
        self.assertIsInstance(config.name, str)
        self.assertIsInstance(config.tools, list)
        self.assertIsInstance(config.debug_mode, bool)
        self.assertIsInstance(config.show_tool_calls, bool)
        self.assertIsInstance(config.markdown, bool)
        self.assertIsInstance(config.num_history_runs, int)

    def test_mutable_default_fields(self):
        """测试可变默认字段（防止共享引用问题）"""
        config1 = AgentConfig()
        config2 = AgentConfig()

        # 修改一个配置的tools列表不应影响另一个
        config1.tools.append(Mock())
        self.assertEqual(len(config1.tools), 1)
        self.assertEqual(len(config2.tools), 0)


class TestCreateAgent(unittest.TestCase):
    """测试create_agent函数"""

    @patch('agent_factory.Agent')
    def test_create_basic_agent(self, mock_agent_class):
        """测试创建基本Agent"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_model = Mock()

        config = AgentConfig(
            name="test_agent",
            model=mock_model,
            instructions="Test instructions"
        )

        result = create_agent(config)

        # 验证Agent类被正确调用
        mock_agent_class.assert_called_once_with(
            agent_id=unittest.mock.ANY,  # UUID生成的ID
            name="test_agent",
            model=mock_model,
            instructions="Test instructions",
            additional_instructions=None,
            tools=[],
            memory_manager=None,
            enable_user_memories=False,
            enable_agentic_memory=False,
            debug_mode=False,
            show_tool_calls=False,
            markdown=False,
            num_history_runs=3,
        )

        # 验证返回的Agent实例
        self.assertEqual(result, mock_agent)

    @patch('agent_factory.Agent')
    def test_create_agent_with_custom_id(self, mock_agent_class):
        """测试使用自定义ID创建Agent"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        config = AgentConfig(
            name="test_agent",
            agent_id="custom_id_123"
        )

        result = create_agent(config)

        # 验证使用了自定义ID
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args[1]
        self.assertEqual(call_args['agent_id'], "custom_id_123")

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.Agent')
    def test_create_agent_with_system_prompt(self, mock_agent_class):
        """测试带有系统提示词的Agent创建"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        config = AgentConfig(
            name="test_agent",
            system_prompt="Custom system prompt"
        )

        result = create_agent(config)

        # 验证系统提示词被设置
        self.assertEqual(result._instructions, "Custom system prompt")

    @patch('agent_factory.Agent')
    def test_create_agent_with_all_parameters(self, mock_agent_class):
        """测试使用所有参数创建Agent"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_model = Mock()
        mock_memory_manager = Mock()
        tools = [Mock(), Mock()]

        config = AgentConfig(
            name="full_agent",
            model=mock_model,
            agent_id="full_123",
            instructions="Main instructions",
            additional_instructions="Additional instructions",
            tools=tools,
            memory_manager=mock_memory_manager,
            enable_user_memories=True,
            enable_agentic_memory=True,
            debug_mode=True,
            show_tool_calls=True,
            markdown=True,
            num_history_runs=10,
            system_prompt="System prompt"
        )

        result = create_agent(config)

        # 验证所有参数被正确传递
        mock_agent_class.assert_called_once_with(
            agent_id="full_123",
            name="full_agent",
            model=mock_model,
            instructions="Main instructions",
            additional_instructions="Additional instructions",
            tools=tools,
            memory_manager=mock_memory_manager,
            enable_user_memories=True,
            enable_agentic_memory=True,
            debug_mode=True,
            show_tool_calls=True,
            markdown=True,
            num_history_runs=10,
        )

        # 验证系统提示词
        self.assertEqual(result._instructions, "System prompt")

        self.assertEqual(result, mock_agent)


class TestSpecializedAgents(unittest.TestCase):
    """测试专用Agent创建函数"""

    @patch('agent_factory.create_agent')
    def test_create_qa_agent_default(self, mock_create_agent):
        """测试创建默认问答Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()

        result = create_qa_agent(mock_model)

        # 验证create_agent被调用
        mock_create_agent.assert_called_once()
        config = mock_create_agent.call_args[0][0]

        self.assertEqual(config.name, "qa_agent")
        self.assertEqual(config.model, mock_model)
        self.assertIn("专业的问答助手", config.system_prompt)
        self.assertEqual(config.tools, [])

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_qa_agent_custom(self, mock_create_agent):
        """测试创建自定义问答Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()
        custom_prompt = "Custom QA prompt"
        tools = [Mock(), Mock()]

        result = create_qa_agent(
            mock_model,
            system_prompt=custom_prompt,
            tools=tools,
            debug_mode=True
        )

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertEqual(config.system_prompt, custom_prompt)
        self.assertEqual(config.tools, tools)
        self.assertTrue(config.debug_mode)

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_task_agent(self, mock_create_agent):
        """测试创建任务Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()
        task_description = "分析数据并生成报告"

        result = create_task_agent(mock_model, task_description)

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertEqual(config.name, "task_agent")
        self.assertEqual(config.model, mock_model)
        self.assertIn(task_description, config.system_prompt)
        self.assertIn("任务执行助手", config.system_prompt)

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_research_agent(self, mock_create_agent):
        """测试创建研究Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()
        research_domain = "人工智能"

        result = create_research_agent(mock_model, research_domain)

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertEqual(config.name, "research_agent")
        self.assertEqual(config.model, mock_model)
        self.assertIn(research_domain, config.system_prompt)
        self.assertIn("专业的研究助手", config.system_prompt)

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_research_agent_no_domain(self, mock_create_agent):
        """测试创建无领域限制的研究Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()

        result = create_research_agent(mock_model)

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertEqual(config.name, "research_agent")
        self.assertIn("专业的研究助手", config.system_prompt)
        # 不应包含特定领域
        self.assertNotIn("专注于", config.system_prompt)

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_creative_agent(self, mock_create_agent):
        """测试创建创意Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()
        creative_domain = "音乐创作"

        result = create_creative_agent(mock_model, creative_domain)

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertEqual(config.name, "creative_agent")
        self.assertEqual(config.model, mock_model)
        self.assertIn(creative_domain, config.system_prompt)
        self.assertIn("创意助手", config.system_prompt)

        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_custom_agent(self, mock_create_agent):
        """测试创建自定义Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()
        role = "数据分析师"
        capabilities = ["数据分析", "统计建模", "可视化"]
        constraints = ["只能处理结构化数据", "不能提供医疗建议"]
        tools = [Mock()]

        result = create_custom_agent(
            mock_model,
            role=role,
            capabilities=capabilities,
            constraints=constraints,
            tools=tools
        )

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertEqual(config.name, "custom_数据分析师")
        self.assertEqual(config.model, mock_model)
        self.assertIn(role, config.system_prompt)

        # 验证能力包含
        for capability in capabilities:
            self.assertIn(capability, config.system_prompt)

        # 验证约束包含
        for constraint in constraints:
            self.assertIn(constraint, config.system_prompt)

        self.assertEqual(config.tools, tools)
        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_create_custom_agent_no_constraints(self, mock_create_agent):
        """测试创建无约束的自定义Agent"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()
        role = "助手"
        capabilities = ["问答", "翻译"]

        result = create_custom_agent(
            mock_model,
            role=role,
            capabilities=capabilities
        )

        # 验证配置
        config = mock_create_agent.call_args[0][0]
        self.assertIn(role, config.system_prompt)
        self.assertIn("主要能力", config.system_prompt)
        # 不应包含具体约束部分（虽然有"约束条件"这个词，但没有具体约束列表）
        self.assertNotIn("- ", config.system_prompt.split("约束条件：")[-1] if "约束条件：" in config.system_prompt else "")

        self.assertEqual(result, mock_agent)


class TestAgentEdgeCases(unittest.TestCase):
    """测试Agent创建的边界情况"""

    @patch('agent_factory.Agent')
    def test_empty_config(self, mock_agent_class):
        """测试空配置创建Agent"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        config = AgentConfig()
        result = create_agent(config)

        # 验证即使配置为空，Agent也能正确创建
        mock_agent_class.assert_called_once()
        self.assertEqual(result, mock_agent)

    @patch('agent_factory.Agent')
    def test_agent_with_large_tools_list(self, mock_agent_class):
        """测试包含大量工具的Agent"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        # 创建100个模拟工具
        tools = [Mock() for _ in range(100)]

        config = AgentConfig(tools=tools)
        result = create_agent(config)

        # 验证所有工具都被传递
        call_args = mock_agent_class.call_args[1]
        self.assertEqual(len(call_args['tools']), 100)
        self.assertEqual(result, mock_agent)

    @patch('agent_factory.create_agent')
    def test_specialized_agents_with_kwargs(self, mock_create_agent):
        """测试专用Agent使用kwargs参数"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_model = Mock()

        # 测试所有专用Agent都能接受额外参数
        agents = [
            create_qa_agent(mock_model, debug_mode=True, user_id="test_user"),
            create_task_agent(mock_model, "test task", debug_mode=True, user_id="test_user"),
            create_research_agent(mock_model, debug_mode=True, user_id="test_user"),
            create_creative_agent(mock_model, debug_mode=True, user_id="test_user"),
            create_custom_agent(mock_model, "test role", ["test capability"], debug_mode=True, user_id="test_user")
        ]

        # 验证所有Agent都创建成功
        for agent in agents:
            self.assertEqual(agent, mock_agent)

        # 验证每次调用都包含了debug_mode参数
        self.assertEqual(mock_create_agent.call_count, 5)
        for call in mock_create_agent.call_args_list:
            config = call[0][0]
            self.assertTrue(config.debug_mode)


if __name__ == '__main__':
    unittest.main()