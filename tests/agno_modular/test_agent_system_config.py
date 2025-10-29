#!/usr/bin/env python3
"""
单元测试：AgentSystemConfig 类
测试 Agent 系统配置的各项功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 添加 agno_modular 目录到路径
sys.path.insert(0, os.path.join(os.getcwd(), 'agno_modular'))

from core.agno_modular.composer import AgentSystemConfig
from core.agno_modular.agent_factory import AgentConfig
from core.agno_modular.mcp_factory import MCPConfig
from core.agno_modular.memory_factory import MemoryConfig


class TestAgentSystemConfig(unittest.TestCase):
    """测试 AgentSystemConfig 类"""

    def setUp(self):
        """测试前准备"""
        self.basic_config = AgentSystemConfig()

    def test_default_initialization(self):
        """测试默认初始化"""
        config = AgentSystemConfig()

        self.assertEqual(config.system_name, "agent_system")
        self.assertIsNone(config.system_id)
        self.assertIsNone(config.description)
        self.assertIsInstance(config.agent_config, AgentConfig)
        self.assertEqual(config.mcp_configs, [])
        self.assertIsNone(config.memory_config)
        self.assertFalse(config.use_multi_memory)
        self.assertIsNone(config.user_id)
        self.assertIsNone(config.session_id)
        self.assertFalse(config.debug_mode)
        self.assertFalse(config.response_stream)

    def test_custom_initialization(self):
        """测试自定义初始化"""
        agent_config = AgentConfig(name="test_agent")
        mcp_config = MCPConfig(name="test_mcp")
        memory_config = MemoryConfig()

        config = AgentSystemConfig(
            system_id="test_system",
            system_name="custom_system",
            description="Test system",
            agent_config=agent_config,
            mcp_configs=[mcp_config],
            memory_config=memory_config,
            user_id="test_user",
            session_id="test_session",
            debug_mode=True,
            response_stream=True
        )

        self.assertEqual(config.system_id, "test_system")
        self.assertEqual(config.system_name, "custom_system")
        self.assertEqual(config.description, "Test system")
        self.assertEqual(config.agent_config.name, "test_agent")
        self.assertEqual(len(config.mcp_configs), 1)
        self.assertEqual(config.mcp_configs[0].name, "test_mcp")
        self.assertEqual(config.memory_config, memory_config)
        self.assertEqual(config.user_id, "test_user")
        self.assertEqual(config.session_id, "test_session")
        self.assertTrue(config.debug_mode)
        self.assertTrue(config.response_stream)

    def test_multi_memory_configuration(self):
        """测试多记忆系统配置"""
        config = AgentSystemConfig(
            use_multi_memory=True,
            memory_types=["conversation", "task", "context"]
        )

        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["conversation", "task", "context"])

    def test_single_mcp_config(self):
        """测试单个 MCP 配置"""
        mcp_config = MCPConfig(
            name="filesystem",
            server_command="python",
            server_args=["server.py"]
        )

        config = AgentSystemConfig(mcp_configs=[mcp_config])

        self.assertEqual(len(config.mcp_configs), 1)
        self.assertEqual(config.mcp_configs[0].name, "filesystem")

    def test_multiple_mcp_configs(self):
        """测试多个 MCP 配置"""
        mcp_configs = [
            MCPConfig(name="filesystem", server_command="python", server_args=["fs.py"]),
            MCPConfig(name="database", server_command="python", server_args=["db.py"]),
            MCPConfig(name="web", server_url="http://localhost:8080")
        ]

        config = AgentSystemConfig(mcp_configs=mcp_configs)

        self.assertEqual(len(config.mcp_configs), 3)
        self.assertEqual(config.mcp_configs[0].name, "filesystem")
        self.assertEqual(config.mcp_configs[1].name, "database")
        self.assertEqual(config.mcp_configs[2].name, "web")

    def test_empty_mcp_configs(self):
        """测试空的 MCP 配置列表"""
        config = AgentSystemConfig(mcp_configs=[])
        self.assertEqual(config.mcp_configs, [])

    def test_response_format_configuration(self):
        """测试响应格式配置"""
        config = AgentSystemConfig(response_format="json")
        self.assertEqual(config.response_format, "json")

        config2 = AgentSystemConfig(response_format=None)
        self.assertIsNone(config2.response_format)

    def test_system_id_generation(self):
        """测试系统 ID 生成"""
        config1 = AgentSystemConfig()
        config2 = AgentSystemConfig()

        # 如果没有提供 system_id，应该使用默认值或生成一个
        self.assertIsNone(config1.system_id)
        self.assertIsNone(config2.system_id)

    def test_debug_mode_flag(self):
        """测试调试模式标志"""
        config = AgentSystemConfig(debug_mode=True)
        self.assertTrue(config.debug_mode)

        config = AgentSystemConfig(debug_mode=False)
        self.assertFalse(config.debug_mode)

    def test_response_stream_flag(self):
        """测试响应流标志"""
        config = AgentSystemConfig(response_stream=True)
        self.assertTrue(config.response_stream)

        config = AgentSystemConfig(response_stream=False)
        self.assertFalse(config.response_stream)

    def test_field_types(self):
        """测试字段类型"""
        config = AgentSystemConfig()

        # 检查字段类型
        self.assertIsInstance(config.system_name, str)
        self.assertIsInstance(config.mcp_configs, list)
        self.assertIsInstance(config.use_multi_memory, bool)
        self.assertIsInstance(config.debug_mode, bool)
        self.assertIsInstance(config.response_stream, bool)

    def test_mutable_default_fields(self):
        """测试可变的默认字段（防止共享引用）"""
        config1 = AgentSystemConfig()
        config2 = AgentSystemConfig()

        # 修改一个配置不应该影响另一个
        config1.mcp_configs.append(MCPConfig(name="test"))
        self.assertEqual(len(config1.mcp_configs), 1)
        self.assertEqual(len(config2.mcp_configs), 0)

    def test_complex_configuration(self):
        """测试复杂配置"""
        agent_config = AgentConfig(
            name="complex_agent",
            system_prompt="Complex agent",
            enable_user_memories=True
        )

        mcp_configs = [
            MCPConfig(
                name="primary_mcp",
                include_tools=["tool1", "tool2"],
                exclude_tools=["tool3"]
            ),
            MCPConfig(
                name="secondary_mcp",
                timeout=60,
                debug_mode=True
            )
        ]

        memory_config = MemoryConfig(
            model=Mock(),  # 使用正确的参数
            add_memories=True,
            update_memories=True
        )

        config = AgentSystemConfig(
            system_id="complex_system",
            system_name="complex_system_name",
            description="A complex system configuration",
            agent_config=agent_config,
            mcp_configs=mcp_configs,
            memory_config=memory_config,
            memory_types=["conversation", "episodic", "semantic"],
            use_multi_memory=True,
            user_id="complex_user",
            session_id="complex_session",
            debug_mode=True,
            response_stream=True,
            response_format="structured"
        )

        # 验证所有配置都正确设置
        self.assertEqual(config.system_id, "complex_system")
        self.assertEqual(config.system_name, "complex_system_name")
        self.assertEqual(config.description, "A complex system configuration")
        self.assertEqual(config.agent_config.name, "complex_agent")
        self.assertEqual(config.agent_config.system_prompt, "Complex agent")
        self.assertTrue(config.agent_config.enable_user_memories)

        self.assertEqual(len(config.mcp_configs), 2)
        self.assertEqual(config.mcp_configs[0].name, "primary_mcp")
        self.assertEqual(config.mcp_configs[0].include_tools, ["tool1", "tool2"])
        self.assertEqual(config.mcp_configs[0].exclude_tools, ["tool3"])
        self.assertEqual(config.mcp_configs[1].name, "secondary_mcp")
        self.assertEqual(config.mcp_configs[1].timeout, 60)
        self.assertTrue(config.mcp_configs[1].debug_mode)

        self.assertTrue(config.memory_config.add_memories)
        self.assertTrue(config.memory_config.update_memories)

        self.assertEqual(config.memory_types, ["conversation", "episodic", "semantic"])
        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.user_id, "complex_user")
        self.assertEqual(config.session_id, "complex_session")
        self.assertTrue(config.debug_mode)
        self.assertTrue(config.response_stream)
        self.assertEqual(config.response_format, "structured")

    def test_configuration_validation(self):
        """测试配置验证"""
        # 测试基本配置验证
        with self.assertRaises(Exception):
            # 传入无效类型应该引发错误
            AgentSystemConfig(system_name=123)  # 应该是字符串

        # 测试可选字段可以为 None
        config = AgentSystemConfig(
            system_id=None,
            description=None,
            memory_config=None,
            user_id=None,
            session_id=None,
            response_format=None
        )

        self.assertIsNone(config.system_id)
        self.assertIsNone(config.description)
        self.assertIsNone(config.memory_config)
        self.assertIsNone(config.user_id)
        self.assertIsNone(config.session_id)
        self.assertIsNone(config.response_format)


class TestAgentSystemConfigIntegration(unittest.TestCase):
    """测试 AgentSystemConfig 与其他模块的集成"""

    def test_agent_config_integration(self):
        """测试与 AgentConfig 的集成"""
        agent_config = AgentConfig(
            name="integration_agent",
            system_prompt="Integration test agent"
        )

        config = AgentSystemConfig(
            agent_config=agent_config
        )

        # 验证集成配置
        self.assertEqual(config.agent_config.name, "integration_agent")
        self.assertEqual(config.agent_config.system_prompt, "Integration test agent")

    def test_mcp_config_integration(self):
        """测试与 MCPConfig 的集成"""
        mcp_config = MCPConfig(
            name="integration_mcp",
            server_command="python",
            server_args=["-m", "mcp_server"],
            include_tools=["read", "write"],
            timeout=30
        )

        config = AgentSystemConfig(mcp_configs=[mcp_config])

        # 验证集成配置
        self.assertEqual(len(config.mcp_configs), 1)
        self.assertEqual(config.mcp_configs[0].name, "integration_mcp")
        self.assertEqual(config.mcp_configs[0].server_command, "python")
        self.assertEqual(config.mcp_configs[0].server_args, ["-m", "mcp_server"])
        self.assertEqual(config.mcp_configs[0].include_tools, ["read", "write"])
        self.assertEqual(config.mcp_configs[0].timeout, 30)

    def test_memory_config_integration(self):
        """测试与 MemoryConfig 的集成"""
        memory_config = MemoryConfig(
            model=Mock(),  # 使用正确的参数
            add_memories=True,
            update_memories=False
        )

        config = AgentSystemConfig(
            memory_config=memory_config,
            use_multi_memory=True,
            memory_types=["conversation", "task"]
        )

        # 验证集成配置
        self.assertTrue(config.memory_config.add_memories)
        self.assertFalse(config.memory_config.update_memories)
        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["conversation", "task"])


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)