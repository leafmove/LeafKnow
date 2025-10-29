"""
Agno模块化组件配置测试
专注于配置类和基础功能的测试，不依赖完整的agno库
"""

import unittest
import sys
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

# 添加agno_modular目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agno_modular'))

# 导入配置类
from core.agno_modular.agent_factory import AgentConfig
from core.agno_modular.mcp_factory import MCPConfig
from core.agno_modular.memory_factory import MemoryConfig
from core.agno_modular.composer import AgentSystemConfig


class TestAgentConfig(unittest.TestCase):
    """测试Agent配置类"""

    def test_agent_config_creation(self):
        """测试Agent配置创建"""
        config = AgentConfig(
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
        config = AgentConfig()

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

        config = AgentConfig(
            name="agent_with_tools",
            tools=[mock_tool1, mock_tool2]
        )

        self.assertEqual(len(config.tools), 2)
        self.assertIn(mock_tool1, config.tools)
        self.assertIn(mock_tool2, config.tools)

    def test_agent_config_memory_settings(self):
        """测试Agent配置记忆设置"""
        config = AgentConfig(
            enable_user_memories=True,
            enable_agentic_memory=True
        )

        self.assertTrue(config.enable_user_memories)
        self.assertTrue(config.enable_agentic_memory)

    def test_agent_config_session_settings(self):
        """测试Agent配置会话设置"""
        config = AgentConfig(
            session_id="test_session",
            user_id="test_user"
        )

        self.assertEqual(config.session_id, "test_session")
        self.assertEqual(config.user_id, "test_user")


class TestMCPConfig(unittest.TestCase):
    """测试MCP配置类"""

    def test_mcp_config_creation(self):
        """测试MCP配置创建"""
        config = MCPConfig(
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
        config = MCPConfig()

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
        config = MCPConfig(
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

        config = MCPConfig(
            name="filtered_mcp",
            include_tools=include_tools,
            exclude_tools=exclude_tools
        )

        self.assertEqual(config.include_tools, include_tools)
        self.assertEqual(config.exclude_tools, exclude_tools)


class TestMemoryConfig(unittest.TestCase):
    """测试记忆配置类"""

    def test_memory_config_creation(self):
        """测试记忆配置创建"""
        config = MemoryConfig(
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
        config = MemoryConfig()

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
        config = MemoryConfig(
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
        config = MemoryConfig(
            retrieval_method="agentic",
            retrieval_limit=20
        )

        self.assertEqual(config.retrieval_method, "agentic")
        self.assertEqual(config.retrieval_limit, 20)


class TestAgentSystemConfig(unittest.TestCase):
    """测试Agent系统配置类"""

    def test_system_config_creation(self):
        """测试系统配置创建"""
        agent_config = AgentConfig(name="system_agent", model="gpt-4")
        memory_config = MemoryConfig(retrieval_method="agentic")
        mcp_config = MCPConfig(name="system_mcp", server_command="test")

        system_config = AgentSystemConfig(
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
        config = AgentSystemConfig()

        self.assertIsNone(config.system_id)
        self.assertEqual(config.system_name, "agent_system")
        self.assertIsNone(config.description)
        self.assertIsInstance(config.agent_config, AgentConfig)
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
        config = AgentSystemConfig(
            use_multi_memory=True,
            memory_types=["conversation", "personal", "task"]
        )

        self.assertTrue(config.use_multi_memory)
        self.assertEqual(config.memory_types, ["conversation", "personal", "task"])

    def test_system_config_with_session(self):
        """测试系统配置会话信息"""
        config = AgentSystemConfig(
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
        valid_config = AgentConfig(
            name="valid_agent",
            model="gpt-4",
            system_prompt="有效的系统提示词"
        )
        self.assertEqual(valid_config.name, "valid_agent")

        # 最小配置
        minimal_config = AgentConfig()
        self.assertEqual(minimal_config.name, "agent")

    def test_mcp_config_validation(self):
        """测试MCP配置验证"""
        # 有效配置
        valid_config = MCPConfig(
            name="valid_mcp",
            server_command="test_command"
        )
        self.assertEqual(valid_config.name, "valid_mcp")

        # 配置超时
        timeout_config = MCPConfig(timeout=120)
        self.assertEqual(timeout_config.timeout, 120)

    def test_memory_config_validation(self):
        """测试记忆配置验证"""
        # 有效配置
        valid_config = MemoryConfig(
            model="gpt-4",
            retrieval_method="agentic"
        )
        self.assertEqual(valid_config.model, "gpt-4")
        self.assertEqual(valid_config.retrieval_method, "agentic")

    def test_system_config_validation(self):
        """测试系统配置验证"""
        agent_config = AgentConfig(name="system_agent")
        system_config = AgentSystemConfig(
            system_name="valid_system",
            agent_config=agent_config
        )
        self.assertEqual(system_config.system_name, "valid_system")
        self.assertEqual(system_config.agent_config.name, "system_agent")


class TestConfigurationSerialization(unittest.TestCase):
    """测试配置序列化"""

    def test_agent_config_to_dict(self):
        """测试Agent配置转换为字典"""
        config = AgentConfig(
            name="test_agent",
            model="gpt-4",
            system_prompt="测试提示词",
            debug_mode=True
        )

        config_dict = {
            "name": config.name,
            "model": config.model,
            "system_prompt": config.system_prompt,
            "debug_mode": config.debug_mode,
            "enable_user_memories": config.enable_user_memories
        }

        self.assertEqual(config_dict["name"], "test_agent")
        self.assertEqual(config_dict["model"], "gpt-4")
        self.assertEqual(config_dict["debug_mode"], True)

    def test_mcp_config_to_dict(self):
        """测试MCP配置转换为字典"""
        config = MCPConfig(
            name="test_mcp",
            server_command="test_command",
            timeout=60
        )

        config_dict = {
            "name": config.name,
            "server_command": config.server_command,
            "timeout": config.timeout,
            "auto_connect": config.auto_connect
        }

        self.assertEqual(config_dict["name"], "test_mcp")
        self.assertEqual(config_dict["server_command"], "test_command")
        self.assertEqual(config_dict["timeout"], 60)

    def test_memory_config_to_dict(self):
        """测试记忆配置转换为字典"""
        config = MemoryConfig(
            model="gpt-4",
            retrieval_method="agentic",
            retrieval_limit=20
        )

        config_dict = {
            "model": config.model,
            "retrieval_method": config.retrieval_method,
            "retrieval_limit": config.retrieval_limit,
            "add_memories": config.add_memories
        }

        self.assertEqual(config_dict["model"], "gpt-4")
        self.assertEqual(config_dict["retrieval_method"], "agentic")
        self.assertEqual(config_dict["retrieval_limit"], 20)

    def test_system_config_to_dict(self):
        """测试系统配置转换为字典"""
        agent_config = AgentConfig(name="system_agent")
        memory_config = MemoryConfig(retrieval_method="last_n")
        mcp_config = MCPConfig(name="system_mcp")

        system_config = AgentSystemConfig(
            system_name="test_system",
            agent_config=agent_config,
            memory_config=memory_config,
            mcp_configs=[mcp_config]
        )

        config_dict = {
            "system_name": system_config.system_name,
            "agent_name": system_config.agent_config.name,
            "memory_retrieval": system_config.memory_config.retrieval_method,
            "mcp_count": len(system_config.mcp_configs),
            "use_multi_memory": system_config.use_multi_memory
        }

        self.assertEqual(config_dict["system_name"], "test_system")
        self.assertEqual(config_dict["agent_name"], "system_agent")
        self.assertEqual(config_dict["memory_retrieval"], "last_n")
        self.assertEqual(config_dict["mcp_count"], 1)
        self.assertFalse(config_dict["use_multi_memory"])


class TestConfigurationComposition(unittest.TestCase):
    """测试配置组合"""

    def test_simple_qa_system(self):
        """测试简单问答系统配置"""
        system_config = AgentSystemConfig(
            system_name="qa_system",
            agent_config=AgentConfig(
                name="qa_agent",
                model="gpt-4",
                system_prompt="你是一个问答助手"
            ),
            memory_config=MemoryConfig(
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
        system_config = AgentSystemConfig(
            system_name="task_system",
            agent_config=AgentConfig(
                name="task_agent",
                model="gpt-4",
                show_tool_calls=True
            ),
            mcp_configs=[
                MCPConfig(name="filesystem", server_command="fs_cmd"),
                MCPConfig(name="calculator", server_command="calc_cmd")
            ]
        )

        self.assertEqual(system_config.system_name, "task_system")
        self.assertTrue(system_config.agent_config.show_tool_calls)
        self.assertEqual(len(system_config.mcp_configs), 2)

    def test_personal_assistant_system(self):
        """测试个人助理系统配置"""
        system_config = AgentSystemConfig(
            system_name="assistant_system",
            agent_config=AgentConfig(
                name="assistant",
                model="gpt-4",
                enable_user_memories=True
            ),
            memory_config=MemoryConfig(
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


def run_config_tests():
    """运行配置测试"""
    print("运行Agno模块化组件配置测试")
    print("=" * 50)

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestAgentConfig,
        TestMCPConfig,
        TestMemoryConfig,
        TestAgentSystemConfig,
        TestConfigurationValidation,
        TestConfigurationSerialization,
        TestConfigurationComposition
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("所有配置测试通过！")
        print(f"运行了 {result.testsRun} 个测试")
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_config_tests()
    sys.exit(0 if success else 1)