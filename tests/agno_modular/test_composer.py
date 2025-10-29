#!/usr/bin/env python3
"""
单元测试：composer 模块
测试 Agent 系统组合器的各项功能
"""

import sys
import os
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 添加 agno_modular 目录到路径
sys.path.insert(0, os.path.join(os.getcwd(), 'agno_modular'))

from core.agno_modular.composer import (
    AgentSystem,
    AgentSystemConfig,
    compose_agent_system,
    create_qa_system,
    create_task_system,
    create_research_system,
    create_personal_assistant_system,
    create_multi_agent_system,
    create_dynamic_system
)
from core.agno_modular.agent_factory import AgentConfig
from core.agno_modular.mcp_factory import MCPConfig
from core.agno_modular.memory_factory import MemoryConfig


class TestAgentSystem(unittest.TestCase):
    """测试 AgentSystem 类"""

    def setUp(self):
        """测试前准备"""
        self.mock_agent = Mock()
        self.mock_mcp_tools = []
        self.mock_memory_manager = Mock()
        self.config = AgentSystemConfig(
            system_id="test_system",
            user_id="test_user",
            session_id="test_session"
        )

    def test_agent_system_initialization(self):
        """测试 AgentSystem 初始化"""
        system = AgentSystem(
            agent=self.mock_agent,
            mcp_tools=self.mock_mcp_tools,
            memory_managers=self.mock_memory_manager,
            config=self.config
        )

        self.assertEqual(system.agent, self.mock_agent)
        self.assertEqual(system.mcp_tools, self.mock_mcp_tools)
        self.assertEqual(system.memory_managers, self.mock_memory_manager)
        self.assertEqual(system.config, self.config)
        self.assertEqual(system.system_id, "test_system")

    def test_agent_system_auto_generate_id(self):
        """测试自动生成系统 ID"""
        config = AgentSystemConfig()  # 没有 system_id
        system = AgentSystem(
            agent=self.mock_agent,
            mcp_tools=self.mock_mcp_tools,
            memory_managers=self.mock_memory_manager,
            config=config
        )

        # 应该自动生成一个 UUID
        self.assertIsNotNone(system.system_id)
        self.assertNotEqual(system.system_id, "")

    def test_add_memory_manager(self):
        """测试添加记忆管理器"""
        memory_managers = {}
        system = AgentSystem(
            agent=self.mock_agent,
            mcp_tools=self.mock_mcp_tools,
            memory_managers=memory_managers,
            config=self.config
        )

        mock_memory = Mock()
        system.add_memory("task", mock_memory)

        self.assertEqual(memory_managers["task"], mock_memory)

    def test_get_memory_manager_dict(self):
        """测试获取记忆管理器（字典类型）"""
        memory_managers = {
            "conversation": Mock(),
            "task": Mock()
        }
        system = AgentSystem(
            agent=self.mock_agent,
            mcp_tools=self.mock_mcp_tools,
            memory_managers=memory_managers,
            config=self.config
        )

        conversation_memory = system.get_memory_manager("conversation")
        task_memory = system.get_memory_manager("task")
        non_existent_memory = system.get_memory_manager("non_existent")

        self.assertEqual(conversation_memory, memory_managers["conversation"])
        self.assertEqual(task_memory, memory_managers["task"])
        self.assertIsNone(non_existent_memory)

    def test_get_memory_manager_single(self):
        """测试获取记忆管理器（单个类型）"""
        from memory_factory import MemoryManager

        # 创建一个继承自MemoryManager的Mock对象
        memory_manager = Mock(spec=MemoryManager)
        system = AgentSystem(
            agent=self.mock_agent,
            mcp_tools=self.mock_mcp_tools,
            memory_managers=memory_manager,
            config=self.config
        )

        result = system.get_memory_manager()
        self.assertEqual(result, memory_manager)

    def test_get_memory_manager_none(self):
        """测试获取不存在的记忆管理器"""
        system = AgentSystem(
            agent=self.mock_agent,
            mcp_tools=self.mock_mcp_tools,
            memory_managers={},
            config=self.config
        )

        result = system.get_memory_manager("non_existent")
        self.assertIsNone(result)


class TestAgentSystemRun(unittest.TestCase):
    """测试 AgentSystem 运行功能"""

    def setUp(self):
        """测试前准备"""
        self.mock_agent = Mock()
        self.mock_mcp_tool = Mock()
        self.mock_memory_manager = Mock()
        self.config = AgentSystemConfig(
            user_id="test_user",
            session_id="test_session",
            response_stream=False
        )

    def test_run_without_mcp_tools(self):
        """测试不使用 MCP 工具的运行"""
        # 模拟 agent - 使用 AsyncMock 处理异步方法
        mock_agent = AsyncMock()
        mock_agent.tools = []
        mock_agent.memory_manager = None

        # 使用 AsyncMock 的 return_value 设置同步返回值
        mock_agent.run.return_value = "Test response"

        system = AgentSystem(
            agent=mock_agent,
            mcp_tools=[],
            memory_managers=None,
            config=self.config
        )

        # 运行异步方法
        result = asyncio.run(system.run("Test message"))

        self.assertEqual(result, "Test response")
        mock_agent.run.assert_called_once_with("Test message", user_id="test_user", session_id="test_session")

    def test_run_with_mcp_tools(self):
        """测试使用 MCP 工具的运行"""
        # 模拟 agent - 使用 AsyncMock 处理异步方法
        mock_agent = AsyncMock()
        mock_agent.tools = []
        mock_agent.memory_manager = None
        mock_agent.run.return_value = "Test response"

        # 模拟 MCP 工具
        mock_mcp_tool = Mock()
        mock_mcp_tool.__hash__ = Mock(return_value=1)  # 使其可哈希

        system = AgentSystem(
            agent=mock_agent,
            mcp_tools=[mock_mcp_tool],
            memory_managers=None,
            config=self.config
        )

        # 运行异步方法
        result = asyncio.run(system.run("Test message"))

        # 验证 MCP 工具被添加到 agent
        self.assertIn(mock_mcp_tool, mock_agent.tools)
        self.assertEqual(result, "Test response")

    def test_run_with_memory_manager(self):
        """测试使用记忆管理器的运行"""
        # 模拟 agent - 使用 AsyncMock 处理异步方法
        mock_agent = AsyncMock()
        mock_agent.tools = []
        mock_agent.memory_manager = None
        mock_agent.run.return_value = "Test response"

        # 模拟记忆管理器
        mock_memory_manager = Mock()

        system = AgentSystem(
            agent=mock_agent,
            mcp_tools=[],
            memory_managers=mock_memory_manager,
            config=self.config
        )

        # 运行异步方法
        result = asyncio.run(system.run("Test message"))

        # 验证记忆管理器被设置到 agent
        self.assertEqual(mock_agent.memory_manager, mock_memory_manager)
        self.assertEqual(result, "Test response")

    def test_run_with_multi_memory_system(self):
        """测试使用多记忆系统的运行"""
        # 模拟 agent - 使用 AsyncMock 处理异步方法
        mock_agent = AsyncMock()
        mock_agent.tools = []
        mock_agent.memory_manager = None
        mock_agent.run.return_value = "Test response"

        # 模拟多记忆系统
        memory_managers = {
            "conversation": Mock(),
            "task": Mock()
        }

        system = AgentSystem(
            agent=mock_agent,
            mcp_tools=[],
            memory_managers=memory_managers,
            config=self.config
        )

        # 运行异步方法
        result = asyncio.run(system.run("Test message"))

        # 验证对话记忆管理器被设置到 agent
        self.assertEqual(mock_agent.memory_manager, memory_managers["conversation"])
        self.assertEqual(result, "Test response")

    def test_run_streaming_response(self):
        """测试流式响应"""
        # 模拟 agent - 使用 AsyncMock 处理异步方法
        mock_agent = AsyncMock()
        mock_agent.tools = []
        mock_agent.memory_manager = None
        mock_agent.run_stream.return_value = "Stream response"

        config = AgentSystemConfig(
            user_id="test_user",
            session_id="test_session",
            response_stream=True
        )

        system = AgentSystem(
            agent=mock_agent,
            mcp_tools=[],
            memory_managers=None,
            config=config
        )

        # 运行异步方法
        result = asyncio.run(system.run("Test message"))

        # 验证使用了流式响应
        self.assertEqual(result, "Stream response")
        mock_agent.run_stream.assert_called_once_with("Test message", user_id="test_user", session_id="test_session")

    def test_run_no_user_session_config(self):
        """测试没有用户和会话配置的运行"""
        # 模拟 agent - 使用 AsyncMock 处理异步方法
        mock_agent = AsyncMock()
        mock_agent.tools = []
        mock_agent.memory_manager = None
        mock_agent.run.return_value = "Test response"

        config = AgentSystemConfig()  # 没有设置 user_id 和 session_id

        system = AgentSystem(
            agent=mock_agent,
            mcp_tools=[],
            memory_managers=None,
            config=config
        )

        # 运行异步方法
        result = asyncio.run(system.run("Test message"))

        # 验证没有传递用户和会话参数
        mock_agent.run.assert_called_once_with("Test message")
        self.assertEqual(result, "Test response")


class TestComposeAgentSystem(unittest.TestCase):
    """测试 compose_agent_system 函数"""

    @patch('composer.create_agent')
    @patch('composer.create_mcp_tools')
    @patch('composer.create_memory_manager')
    def test_compose_basic_system(self, mock_create_memory, mock_create_mcp, mock_create_agent):
        """测试组合基本系统"""
        # 设置模拟对象
        mock_agent = Mock()
        mock_mcp_tools = Mock()
        mock_memory_manager = Mock()

        mock_create_agent.return_value = mock_agent
        mock_create_mcp.return_value = mock_mcp_tools
        mock_create_memory.return_value = mock_memory_manager

        agent_config = AgentConfig(name="test_agent")
        mcp_config = MCPConfig(name="test_mcp")
        memory_config = MemoryConfig()

        config = AgentSystemConfig(
            agent_config=agent_config,
            mcp_configs=[mcp_config],
            memory_config=memory_config
        )

        system = compose_agent_system(config)

        # 验证调用
        mock_create_agent.assert_called_once_with(agent_config)
        mock_create_mcp.assert_called_once_with(mcp_config)
        mock_create_memory.assert_called_once_with(memory_config)

        # 验证系统
        self.assertEqual(system.agent, mock_agent)
        self.assertEqual(system.mcp_tools, [mock_mcp_tools])
        self.assertEqual(system.memory_managers, mock_memory_manager)
        self.assertEqual(system.config, config)

    @patch('composer.create_agent')
    @patch('composer.create_multi_mcp_tools')
    @patch('composer.create_multi_memory_system')
    def test_compose_multi_system(self, mock_create_memory, mock_create_mcp, mock_create_agent):
        """测试组合多系统"""
        # 设置模拟对象
        mock_agent = Mock()
        mock_mcp_tools = Mock()
        mock_memory_managers = {"conversation": Mock(), "task": Mock()}

        mock_create_agent.return_value = mock_agent
        mock_create_mcp.return_value = mock_mcp_tools
        mock_create_memory.return_value = mock_memory_managers

        agent_config = AgentConfig(name="test_agent")
        mcp_configs = [MCPConfig(name="mcp1"), MCPConfig(name="mcp2")]
        memory_config = MemoryConfig()

        config = AgentSystemConfig(
            agent_config=agent_config,
            mcp_configs=mcp_configs,
            memory_config=memory_config,
            use_multi_memory=True,
            memory_types=["conversation", "task"]
        )

        system = compose_agent_system(config)

        # 验证调用
        mock_create_agent.assert_called_once_with(agent_config)
        mock_create_mcp.assert_called_once_with(mcp_configs)
        mock_create_memory.assert_called_once_with(
            model=agent_config.model,
            memory_types=["conversation", "task"],
            db=memory_config.db
        )

        # 验证系统
        self.assertEqual(system.agent, mock_agent)
        self.assertEqual(system.mcp_tools, [mock_mcp_tools])
        self.assertEqual(system.memory_managers, mock_memory_managers)

    @patch('composer.create_agent')
    def test_compose_no_memory(self, mock_create_agent):
        """测试不使用记忆的系统"""
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        config = AgentSystemConfig(
            agent_config=AgentConfig(name="test_agent"),
            mcp_configs=[]
        )

        system = compose_agent_system(config)

        # 验证系统
        self.assertEqual(system.agent, mock_agent)
        self.assertEqual(system.mcp_tools, [])
        self.assertIsNone(system.memory_managers)


class TestSystemCreators(unittest.TestCase):
    """测试各种系统创建器函数"""

    @patch('composer.compose_agent_system')
    def test_create_qa_system(self, mock_compose):
        """测试创建问答系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        mock_model = Mock()
        mcp_config = MCPConfig(name="qa_mcp")
        memory_config = MemoryConfig()

        system = create_qa_system(
            model=mock_model,
            system_prompt="QA system prompt",
            mcp_configs=[mcp_config],
            memory_config=memory_config,
            user_id="qa_user"
        )

        # 验证配置
        config = mock_compose.call_args[0][0]
        self.assertEqual(config.system_name, "qa_system")
        self.assertEqual(config.description, "问答系统")
        self.assertEqual(config.agent_config.name, "qa_agent")
        self.assertEqual(config.agent_config.model, mock_model)
        self.assertEqual(config.agent_config.system_prompt, "QA system prompt")
        self.assertEqual(config.mcp_configs, [mcp_config])
        self.assertEqual(config.memory_config, memory_config)
        self.assertEqual(config.user_id, "qa_user")

    @patch('composer.compose_agent_system')
    def test_create_task_system(self, mock_compose):
        """测试创建任务系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        mock_model = Mock()
        task_description = "Process data analysis tasks"

        system = create_task_system(
            model=mock_model,
            task_description=task_description,
            memory_config=None
        )

        # 验证配置
        config = mock_compose.call_args[0][0]
        self.assertEqual(config.system_name, "task_system")
        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["task", "context"])
        self.assertIn("Process data analysis tasks", config.agent_config.system_prompt)

    @patch('composer.compose_agent_system')
    def test_create_research_system(self, mock_compose):
        """测试创建研究系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        mock_model = Mock()
        research_domain = "Machine Learning"

        system = create_research_system(
            model=mock_model,
            research_domain=research_domain,
            mcp_configs=None
        )

        # 验证配置
        config = mock_compose.call_args[0][0]
        self.assertEqual(config.system_name, "research_system")
        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["research", "context", "preference"])
        self.assertIn("Machine Learning", config.description)

    @patch('composer.compose_agent_system')
    def test_create_personal_assistant_system(self, mock_compose):
        """测试创建个人助理系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        mock_model = Mock()
        user_preferences = {"language": "Chinese", "timezone": "Asia/Shanghai"}

        system = create_personal_assistant_system(
            model=mock_model,
            user_preferences=user_preferences
        )

        # 验证配置
        config = mock_compose.call_args[0][0]
        self.assertEqual(config.system_name, "personal_assistant")
        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["personal", "preference", "conversation", "task"])
        self.assertIsNotNone(config.memory_config)

    @patch('composer.compose_agent_system')
    def test_create_multi_agent_system(self, mock_compose):
        """测试创建多 Agent 系统"""
        mock_systems = [Mock(), Mock(), Mock()]
        mock_compose.side_effect = mock_systems

        agent_configs = [
            AgentConfig(name="agent1"),
            AgentConfig(name="agent2"),
            AgentConfig(name="agent3")
        ]
        shared_mcp_config = MCPConfig(name="shared_mcp")

        systems = create_multi_agent_system(
            agent_configs=agent_configs,
            shared_mcp_configs=[shared_mcp_config],
            shared_memory_config=MemoryConfig()
        )

        # 验证创建了 3 个系统
        self.assertEqual(len(systems), 3)
        self.assertEqual(mock_compose.call_count, 3)

        # 验证每个系统的配置
        for i, call in enumerate(mock_compose.call_args_list):
            config = call[0][0]
            self.assertEqual(config.system_id, f"multi_agent_system_{i}")
            self.assertEqual(config.agent_config.name, f"agent{i + 1}")

    @patch('composer.compose_agent_system')
    def test_create_dynamic_system(self, mock_compose):
        """测试创建动态系统"""
        mock_system = Mock()
        mock_compose.return_value = mock_system

        mock_model = Mock()
        system_prompt = "Dynamic system prompt"
        regular_tool = Mock()  # 假设这是一个常规工具
        mcp_config = MCPConfig(name="dynamic_mcp")

        system = create_dynamic_system(
            model=mock_model,
            system_prompt=system_prompt,
            tools=[regular_tool, mcp_config]
        )

        # 验证配置
        config = mock_compose.call_args[0][0]
        self.assertEqual(config.system_name, "dynamic_system")
        self.assertEqual(config.agent_config.name, "dynamic_agent")
        self.assertEqual(config.agent_config.model, mock_model)
        self.assertEqual(config.agent_config.system_prompt, system_prompt)
        self.assertEqual(config.mcp_configs, [mcp_config])


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    @patch('composer.create_agent')
    def test_agent_creation_failure(self, mock_create_agent):
        """测试 Agent 创建失败"""
        mock_create_agent.side_effect = Exception("Agent creation failed")

        config = AgentSystemConfig(agent_config=AgentConfig())

        with self.assertRaises(Exception):
            compose_agent_system(config)

    @patch('composer.create_mcp_tools')
    def test_mcp_creation_failure(self, mock_create_mcp):
        """测试 MCP 工具创建失败"""
        mock_create_mcp.side_effect = Exception("MCP creation failed")

        config = AgentSystemConfig(
            agent_config=AgentConfig(),
            mcp_configs=[MCPConfig()]
        )

        with self.assertRaises(Exception):
            compose_agent_system(config)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)