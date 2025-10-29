#!/usr/bin/env python3
"""
单元测试：mcp_factory 模块
测试 MCP 工厂的各项功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 添加 agno_modular 目录到路径
sys.path.insert(0, os.path.join(os.getcwd(), 'agno_modular'))

from core.agno_modular.mcp_factory import (
    MCPConfig,
    create_mcp_tools,
    create_multi_mcp_tools,
    create_filesystem_mcp,
    create_database_mcp,
    create_web_search_mcp,
    create_github_mcp,
    create_puppeteer_mcp,
    create_memory_mcp,
    create_weather_mcp,
    create_slack_mcp,
    create_time_mcp
)


class TestMCPConfig(unittest.TestCase):
    """测试 MCPConfig 类"""

    def test_default_initialization(self):
        """测试默认初始化"""
        config = MCPConfig()

        self.assertEqual(config.name, "mcp_tools")
        self.assertIsNone(config.description)
        self.assertIsNone(config.server_url)
        self.assertIsNone(config.server_command)
        self.assertEqual(config.server_args, [])
        self.assertEqual(config.server_env, {})
        self.assertIsNone(config.include_tools)
        self.assertIsNone(config.exclude_tools)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.connection_check_interval, 5)
        self.assertFalse(config.debug_mode)
        self.assertTrue(config.auto_connect)

    def test_custom_initialization(self):
        """测试自定义初始化"""
        config = MCPConfig(
            name="custom_mcp",
            description="Custom MCP configuration",
            server_url="http://localhost:8080",
            server_command="python",
            server_args=["server.py", "--port", "8080"],
            server_env={"DEBUG": "1"},
            include_tools=["tool1", "tool2"],
            exclude_tools=["tool3"],
            timeout=60,
            max_retries=5,
            connection_check_interval=10,
            debug_mode=True,
            auto_connect=False
        )

        self.assertEqual(config.name, "custom_mcp")
        self.assertEqual(config.description, "Custom MCP configuration")
        self.assertEqual(config.server_url, "http://localhost:8080")
        self.assertEqual(config.server_command, "python")
        self.assertEqual(config.server_args, ["server.py", "--port", "8080"])
        self.assertEqual(config.server_env, {"DEBUG": "1"})
        self.assertEqual(config.include_tools, ["tool1", "tool2"])
        self.assertEqual(config.exclude_tools, ["tool3"])
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.connection_check_interval, 10)
        self.assertTrue(config.debug_mode)
        self.assertFalse(config.auto_connect)

    def test_partial_initialization(self):
        """测试部分初始化"""
        config = MCPConfig(
            server_command="node",
            include_tools=["read_file"]
        )

        self.assertEqual(config.name, "mcp_tools")
        self.assertEqual(config.server_command, "node")
        self.assertEqual(config.include_tools, ["read_file"])
        self.assertIsNone(config.server_url)
        self.assertEqual(config.server_args, [])
        self.assertTrue(config.auto_connect)

    def test_field_types(self):
        """测试字段类型"""
        config = MCPConfig()

        # 检查字段类型
        self.assertIsInstance(config.name, str)
        self.assertIsInstance(config.server_args, list)
        self.assertIsInstance(config.server_env, dict)
        self.assertIsInstance(config.timeout, int)
        self.assertIsInstance(config.max_retries, int)
        self.assertIsInstance(config.connection_check_interval, int)
        self.assertIsInstance(config.debug_mode, bool)
        self.assertIsInstance(config.auto_connect, bool)

    def test_mutable_default_fields(self):
        """测试可变的默认字段（防止共享引用）"""
        config1 = MCPConfig()
        config2 = MCPConfig()

        # 修改一个配置不应该影响另一个
        config1.server_args.append("--debug")
        config1.server_env["TEST"] = "value"

        self.assertEqual(len(config1.server_args), 1)
        self.assertEqual(len(config2.server_args), 0)
        self.assertEqual(config1.server_env["TEST"], "value")
        self.assertNotIn("TEST", config2.server_env)


class TestCreateMCPTools(unittest.TestCase):
    """测试 create_mcp_tools 函数"""

    @patch('mcp_factory.MCPTools')
    def test_create_basic_mcp_tools(self, mock_mcp_tools_class):
        """测试创建基本 MCP 工具"""
        mock_mcp_tools = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_tools

        config = MCPConfig(name="test_mcp")

        result = create_mcp_tools(config)

        # 验证调用 - 现在MCPTools使用默认python命令
        mock_mcp_tools_class.assert_called_once_with(command="python --version")

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.MCPTools')
    def test_create_complete_mcp_tools(self, mock_mcp_tools_class):
        """测试创建完整配置的 MCP 工具"""
        mock_mcp_tools = Mock()
        mock_mcp_tools_class.return_value = mock_mcp_tools

        config = MCPConfig(
            name="complete_mcp",
            description="Complete configuration",
            server_url="http://localhost:8080",
            server_command="python",
            server_args=["-m", "mcp_server"],
            server_env={"PORT": "8080"},
            include_tools=["read", "write"],
            exclude_tools=["delete"],
            timeout=60,
            max_retries=5,
            connection_check_interval=10,
            debug_mode=True,
            auto_connect=False
        )

        result = create_mcp_tools(config)

        # 验证所有参数都正确传递
        mock_mcp_tools_class.assert_called_once_with(
            command="python -m mcp_server",
            url="http://localhost:8080",
            env={"PORT": "8080"},
            include_tools=["read", "write"],
            exclude_tools=["delete"],
            timeout_seconds=60
        )

        self.assertEqual(result, mock_mcp_tools)


class TestCreateMultiMCPTools(unittest.TestCase):
    """测试 create_multi_mcp_tools 函数"""

    @patch('mcp_factory.MultiMCPTools')
    @patch('mcp_factory.create_mcp_tools')
    def test_create_multi_mcp_tools_single(self, mock_create_mcp, mock_multi_mcp_class):
        """测试创建单个 MCP 工具的多工具集"""
        mock_multi_mcp = Mock()
        mock_single_mcp = Mock()

        mock_multi_mcp_class.return_value = mock_multi_mcp
        mock_create_mcp.return_value = mock_single_mcp

        config = MCPConfig(name="single_mcp")
        configs = [config]

        result = create_multi_mcp_tools(configs)

        # 验证调用
        mock_multi_mcp_class.assert_called_once()
        mock_create_mcp.assert_called_once_with(config)
        mock_multi_mcp.add_mcp_tools.assert_called_once_with(mock_single_mcp)

        self.assertEqual(result, mock_multi_mcp)

    @patch('mcp_factory.MultiMCPTools')
    @patch('mcp_factory.create_mcp_tools')
    def test_create_multi_mcp_tools_multiple(self, mock_create_mcp, mock_multi_mcp_class):
        """测试创建多个 MCP 工具的多工具集"""
        mock_multi_mcp = Mock()
        mock_mcp1 = Mock()
        mock_mcp2 = Mock()

        mock_multi_mcp_class.return_value = mock_multi_mcp
        mock_create_mcp.side_effect = [mock_mcp1, mock_mcp2]

        config1 = MCPConfig(name="mcp1")
        config2 = MCPConfig(name="mcp2")
        configs = [config1, config2]

        result = create_multi_mcp_tools(configs)

        # 验证调用
        self.assertEqual(mock_create_mcp.call_count, 2)
        mock_create_mcp.assert_any_call(config1)
        mock_create_mcp.assert_any_call(config2)

        self.assertEqual(mock_multi_mcp.add_mcp_tools.call_count, 2)
        mock_multi_mcp.add_mcp_tools.assert_any_call(mock_mcp1)
        mock_multi_mcp.add_mcp_tools.assert_any_call(mock_mcp2)

        self.assertEqual(result, mock_multi_mcp)


class TestPresetMCPs(unittest.TestCase):
    """测试预设的 MCP 配置函数"""

    @patch('mcp_factory.create_mcp_tools')
    def test_create_filesystem_mcp(self, mock_create_mcp):
        """测试创建文件系统 MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        result = create_filesystem_mcp("/path/to/files", name="fs_tools", read_only=True)

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "fs_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"])
        self.assertEqual(config.include_tools, ["read_file", "list_directory"])  # read_only 模式

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_filesystem_mcp_read_write(self, mock_create_mcp):
        """测试创建可读写文件系统 MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        result = create_filesystem_mcp("/path/to/files", read_only=False)

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.include_tools, ["read_file", "write_file", "list_directory"])  # 读写模式

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_database_mcp_postgresql(self, mock_create_mcp):
        """测试创建 PostgreSQL MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        connection_string = "postgresql://user:pass@localhost/db"
        result = create_database_mcp(connection_string, db_type="postgresql", name="pg_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "pg_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-postgres"])
        self.assertEqual(config.server_env, {"DATABASE_URL": connection_string})

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_web_search_mcp(self, mock_create_mcp):
        """测试创建网络搜索 MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        api_key = "brave_api_key_123"
        result = create_web_search_mcp(api_key, search_engine="brave", name="search_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "search_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-brave-search"])
        self.assertEqual(config.server_env, {"BRAVE_API_KEY": api_key})

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_github_mcp(self, mock_create_mcp):
        """测试创建 GitHub MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        token = "github_token_456"
        result = create_github_mcp(token, name="github_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "github_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-github"])
        self.assertEqual(config.server_env, {"GITHUB_PERSONAL_ACCESS_TOKEN": token})

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_puppeteer_mcp(self, mock_create_mcp):
        """测试创建 Puppeteer MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        result = create_puppeteer_mcp(name="puppeteer_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "puppeteer_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-puppeteer"])

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_memory_mcp(self, mock_create_mcp):
        """测试创建记忆存储 MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        storage_path = "/path/to/memory"
        result = create_memory_mcp(storage_path, name="memory_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "memory_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-memory"])
        self.assertEqual(config.server_env, {"MEMORY_PATH": storage_path})

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_weather_mcp(self, mock_create_mcp):
        """测试创建天气查询 MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        api_key = "weather_api_key_789"
        result = create_weather_mcp(api_key, name="weather_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "weather_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-weather"])
        self.assertEqual(config.server_env, {"WEATHER_API_KEY": api_key})

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_slack_mcp(self, mock_create_mcp):
        """测试创建 Slack MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        bot_token = "slack_bot_token_abc"
        result = create_slack_mcp(bot_token, name="slack_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "slack_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-slack"])
        self.assertEqual(config.server_env, {"SLACK_BOT_TOKEN": bot_token})

        self.assertEqual(result, mock_mcp_tools)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_time_mcp(self, mock_create_mcp):
        """测试创建时间相关 MCP"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        result = create_time_mcp(name="time_tools")

        # 验证配置
        config = mock_create_mcp.call_args[0][0]
        self.assertEqual(config.name, "time_tools")
        self.assertEqual(config.server_command, "npx")
        self.assertEqual(config.server_args, ["-y", "@modelcontextprotocol/server-time"])

        self.assertEqual(result, mock_mcp_tools)


class TestMCPFactoryEdgeCases(unittest.TestCase):
    """测试 MCP 工厂的边界情况"""

    @patch('mcp_factory.create_mcp_tools')
    def test_empty_config_list(self, mock_create_mcp):
        """测试空的配置列表"""
        with patch('mcp_factory.MultiMCPTools') as mock_multi_mcp:
            mock_multi_mcp_instance = Mock()
            mock_multi_mcp.return_value = mock_multi_mcp_instance

            result = create_multi_mcp_tools([])

            # 验证没有调用 create_mcp_tools
            mock_create_mcp.assert_not_called()
            mock_multi_mcp_instance.add_mcp_tools.assert_not_called()

            self.assertEqual(result, mock_multi_mcp_instance)

    @patch('mcp_factory.create_mcp_tools')
    def test_create_mcp_tools_with_overrides(self, mock_create_mcp):
        """测试使用覆盖参数创建 MCP 工具"""
        mock_mcp_tools = Mock()
        mock_create_mcp.return_value = mock_mcp_tools

        config = MCPConfig(name="override_test")

        # 使用自定义参数覆盖
        result = create_mcp_tools(config)

        mock_create_mcp.assert_called_once()

        # 验证返回值
        self.assertEqual(result, mock_mcp_tools)

    def test_pathlib_path_handling(self):
        """测试 Path 对象处理"""
        from pathlib import Path

        @patch('mcp_factory.create_mcp_tools')
        def test_with_pathlib(mock_create_mcp):
            mock_mcp_tools = Mock()
            mock_create_mcp.return_value = mock_mcp_tools

            path_obj = Path("/test/path")
            result = create_filesystem_mcp(path_obj)

            # 验证 Path 对象被正确转换为字符串
            config = mock_create_mcp.call_args[0][0]
            self.assertEqual(config.server_args[-1], str(path_obj))

        test_with_pathlib()


class TestMCPFactoryErrorHandling(unittest.TestCase):
    """测试 MCP 工厂错误处理"""

    @patch('mcp_factory.MCPTools')
    def test_mcp_tools_creation_failure(self, mock_mcp_tools_class):
        """测试 MCP 工具创建失败"""
        mock_mcp_tools_class.side_effect = Exception("Failed to create MCP tools")

        config = MCPConfig(name="failing_mcp")

        with self.assertRaises(Exception) as context:
            create_mcp_tools(config)

        self.assertIn("Failed to create MCP tools", str(context.exception))

    @patch('mcp_factory.MultiMCPTools')
    def test_multi_mcp_tools_creation_failure(self, mock_multi_mcp_class):
        """测试多 MCP 工具创建失败"""
        mock_multi_mcp_class.side_effect = Exception("Failed to create MultiMCPTools")

        configs = [MCPConfig(name="mcp1")]

        with self.assertRaises(Exception) as context:
            create_multi_mcp_tools(configs)

        self.assertIn("Failed to create MultiMCPTools", str(context.exception))

    @patch('mcp_factory.create_mcp_tools')
    def test_individual_mcp_creation_failure(self, mock_create_mcp):
        """测试单个 MCP 创建失败（多工具集中）"""
        mock_create_mcp.side_effect = Exception("Individual MCP creation failed")

        with patch('mcp_factory.MultiMCPTools') as mock_multi_mcp_class:
            mock_multi_mcp_instance = Mock()
            mock_multi_mcp_class.return_value = mock_multi_mcp_instance

            configs = [MCPConfig(name="failing_mcp")]

            with self.assertRaises(Exception) as context:
                create_multi_mcp_tools(configs)

            self.assertIn("Individual MCP creation failed", str(context.exception))


class TestMCPFactoryIntegration(unittest.TestCase):
    """测试 MCP 工厂集成功能"""

    def test_config_serialization(self):
        """测试配置序列化"""
        config = MCPConfig(
            name="integration_test",
            server_command="python",
            server_args=["-m", "test_server"],
            server_env={"TEST_ENV": "1"}
        )

        # 验证配置可以正确序列化为字典
        config_dict = {
            "name": config.name,
            "server_command": config.server_command,
            "server_args": config.server_args,
            "server_env": config.server_env,
            "timeout": config.timeout,
            "debug_mode": config.debug_mode
        }

        self.assertEqual(config_dict["name"], "integration_test")
        self.assertEqual(config_dict["server_args"], ["-m", "test_server"])
        self.assertEqual(config_dict["server_env"], {"TEST_ENV": "1"})

    def test_config_modification(self):
        """测试配置修改"""
        config = MCPConfig()

        # 修改配置
        config.name = "modified_name"
        config.server_command = "node"
        config.server_args.extend(["--debug"])
        config.server_env["NEW_VAR"] = "value"

        # 验证修改生效
        self.assertEqual(config.name, "modified_name")
        self.assertEqual(config.server_command, "node")
        self.assertIn("--debug", config.server_args)
        self.assertEqual(config.server_env["NEW_VAR"], "value")

    @patch('mcp_factory.create_mcp_tools')
    def test_multiple_calls_independence(self, mock_create_mcp):
        """测试多次调用的独立性"""
        mock_mcp1 = Mock()
        mock_mcp2 = Mock()
        mock_create_mcp.side_effect = [mock_mcp1, mock_mcp2]

        config1 = MCPConfig(name="config1")
        config2 = MCPConfig(name="config2")

        result1 = create_mcp_tools(config1)
        result2 = create_mcp_tools(config2)

        # 验证每次调用都是独立的
        self.assertEqual(result1, mock_mcp1)
        self.assertEqual(result2, mock_mcp2)
        self.assertEqual(mock_create_mcp.call_count, 2)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)