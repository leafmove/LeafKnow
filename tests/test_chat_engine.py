"""
ChatEngine 单元测试
测试智能体配置、模型配置、工具配置功能以及数据库操作
"""

import unittest
import os
import json
import tempfile
import shutil
import time
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_engine import ChatEngine
from core.agno.db.sqlite.extended_sqlite import ExtendedSqliteDb
from core.agno.db.sqlite.config_data import AgentConfig, ToolConfig, ModelConfig
from core.agno.db.sqlite.runtime_data import RuntimeData


class TestChatEngineConfiguration(unittest.TestCase):
    """ChatEngine 配置功能测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.db_file = os.path.join(self.temp_dir, "test_chat_engine.db")

        # Mock 核心模块
        self.mock_core_modules()

        # 创建测试用的配置数据
        self.test_config = {
            "agents": {
                "test_agent": {
                    "name": "test_agent",
                    "type": "text",
                    "model": {
                        "provider": "openai",
                        "name": "gpt-3.5-turbo",
                        "kwargs": {
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    },
                    "instructions": "You are a helpful test assistant",
                    "tools": [
                        {
                            "name": "calculator",
                            "description": "Calculate mathematical expressions",
                            "function": {
                                "name": "calculate",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "expression": {"type": "string"}
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "current_agent": "test_agent",
            "voice_enabled": False,
            "websearch_enabled": False,
            "version": "1.0"
        }

        # 保存测试配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)

    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def mock_core_modules(self):
        """Mock 核心模块"""
        # Mock LLM_CLASS_DICT
        mock_llm_class = Mock()
        mock_llm_instance = Mock()
        mock_llm_instance.model_name = "gpt-3.5-turbo"
        mock_llm_instance.get_available_models.return_value = ["gpt-3.5-turbo", "gpt-4"]
        mock_llm_class.return_value = mock_llm_instance

        # Mock AGENT_CLASS_DICT
        mock_agent_class = Mock()
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = "Test response"
        mock_agent_instance.reasoning_trace = []
        mock_agent_instance.tool_calls = []
        mock_agent_instance.token_count = 100
        mock_agent_class.return_value = mock_agent_instance

        # Mock Memory
        mock_memory = Mock()
        mock_memory.clear.return_value = None

        # Mock TextSpeakEngine
        mock_voice_engine = Mock()

        # 应用 patches
        self.patches = []

        patches = [
            patch('chat_engine.LLM_CLASS_DICT', {'openai': mock_llm_class}),
            patch('chat_engine.AGENT_CLASS_DICT', {'text': mock_agent_class}),
            patch('chat_engine.Memory', return_value=mock_memory),
            patch('chat_engine.TextSpeakEngine', return_value=mock_voice_engine),
            patch('chat_engine.LLM_BASEURL', 'https://api.openai.com/v1'),
            patch('chat_engine.LLM_BACKEND', 'openai'),
            patch('chat_engine.log_info'),
            patch('chat_engine.log_error'),
            patch('chat_engine.log_debug')
        ]

        for p in patches:
            p.start()
            self.patches.append(p)

    def create_chat_engine(self, config_file=None):
        """创建 ChatEngine 实例"""
        config_path = config_file or self.config_file
        return ChatEngine(config_path=config_path, user_token="test_user")

    def test_initialization(self):
        """测试 ChatEngine 初始化"""
        engine = self.create_chat_engine()

        # 验证基础属性
        self.assertIsNotNone(engine.db)
        self.assertEqual(engine.user_token, "test_user")
        self.assertFalse(engine.processing)
        self.assertFalse(engine.voice_enabled)
        self.assertFalse(engine.websearch_enabled)

        # 验证数据库文件创建
        self.assertTrue(os.path.exists(engine.db_file))

    def test_load_config_from_file(self):
        """测试从文件加载配置"""
        engine = self.create_chat_engine()

        # 验证智能体配置加载
        self.assertIn("test_agent", engine.agent_configs)
        config = engine.agent_configs["test_agent"]

        self.assertEqual(config["name"], "test_agent")
        self.assertEqual(config["type"], "text")
        self.assertEqual(config["model"]["provider"], "openai")
        self.assertEqual(config["model"]["name"], "gpt-3.5-turbo")
        self.assertEqual(config["instructions"], "You are a helpful test assistant")
        self.assertEqual(len(config["tools"]), 1)
        self.assertEqual(config["tools"][0]["name"], "calculator")

    def test_save_config_to_database(self):
        """测试保存配置到数据库"""
        engine = self.create_chat_engine()

        # 触发保存配置
        engine.save_config()

        # 验证数据库中的配置
        agent_configs = engine.db.get_agent_configs(user_id="test_user")
        self.assertEqual(len(agent_configs), 1)

        agent_config = agent_configs[0]
        self.assertEqual(agent_config.name, "test_agent")
        self.assertEqual(agent_config.model_provider, "openai")
        self.assertEqual(agent_config.model_id, "gpt-3.5-turbo")
        self.assertEqual(agent_config.instructions, "You are a helpful test assistant")
        self.assertEqual(agent_config.user_id, "test_user")

    def test_model_configuration(self):
        """测试模型配置功能"""
        engine = self.create_chat_engine()

        # 测试获取可用模型
        mock_llm = Mock()
        mock_llm.get_available_models.return_value = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        mock_llm.model_name = "gpt-3.5-turbo"

        models, current = engine.get_available_models(mock_llm)

        self.assertEqual(len(models), 3)
        self.assertEqual(current, "gpt-3.5-turbo")

        # 测试更新模型
        engine.select_agent_by_name("test_agent")
        success = engine.update_agent_model("gpt-4")

        self.assertTrue(success)
        updated_config = engine.agent_configs["test_agent"]
        self.assertEqual(updated_config["model"]["name"], "gpt-4")

    def test_agent_configuration_crud(self):
        """测试智能体配置 CRUD 操作"""
        engine = self.create_chat_engine()

        # 测试创建智能体
        new_agent_config = {
            "name": "new_test_agent",
            "type": "text",
            "model": {
                "provider": "anthropic",
                "name": "claude-3-sonnet",
                "kwargs": {"temperature": 0.5}
            },
            "instructions": "You are a Claude test assistant"
        }

        agent = engine.create_agent("new_test_agent", new_agent_config)
        self.assertIsNotNone(agent)
        self.assertIn("new_test_agent", engine.agents)

        # 验证数据库中的配置
        agent_configs = engine.db.get_agent_configs(user_id="test_user")
        claude_config = next((ac for ac in agent_configs if ac.name == "new_test_agent"), None)
        self.assertIsNotNone(claude_config)
        self.assertEqual(claude_config.model_provider, "anthropic")
        self.assertEqual(claude_config.model_id, "claude-3-sonnet")

        # 测试更新智能体
        updated_config = new_agent_config.copy()
        updated_config["instructions"] = "Updated instructions"

        result = engine.edit_agent("new_test_agent", {"instructions": "Updated instructions"})
        self.assertTrue(result["success"])

        # 验证更新
        agent_configs = engine.db.get_agent_configs(user_id="test_user")
        updated_agent_config = next((ac for ac in agent_configs if ac.name == "new_test_agent"), None)
        self.assertEqual(updated_agent_config.instructions, "Updated instructions")

        # 测试删除智能体
        result = engine.delete_agent("new_test_agent")
        self.assertTrue(result["success"])
        self.assertNotIn("new_test_agent", engine.agents)

        # 验证软删除
        agent_configs = engine.db.get_agent_configs(user_id="test_user")
        deleted_config = next((ac for ac in agent_configs if ac.name == "new_test_agent"), None)
        self.assertIsNone(deleted_config)  # 应该被过滤掉

    def test_tool_configuration(self):
        """测试工具配置功能"""
        engine = self.create_chat_engine()

        # 测试工具配置存储
        agent_config = engine.agent_configs["test_agent"]
        tools = agent_config["tools"]

        self.assertEqual(len(tools), 1)
        tool = tools[0]

        self.assertEqual(tool["name"], "calculator")
        self.assertEqual(tool["description"], "Calculate mathematical expressions")
        self.assertIn("function", tool)
        self.assertEqual(tool["function"]["name"], "calculate")

        # 验证工具配置保存在数据库中
        agent_configs = engine.db.get_agent_configs(user_id="test_user")
        agent_config = agent_configs[0]

        saved_tools = agent_config.tools
        self.assertIsNotNone(saved_tools)
        self.assertEqual(len(saved_tools), 1)
        self.assertEqual(saved_tools[0]["name"], "calculator")

    def test_database_operations(self):
        """测试数据库操作"""
        engine = self.create_chat_engine()

        # 测试 AgentConfig 数据库操作
        agent_config = AgentConfig.from_dict({
            "agent_id": "test_db_agent",
            "name": "db_test_agent",
            "model_provider": "openai",
            "model_id": "gpt-4",
            "instructions": "Database test agent",
            "user_id": "test_user"
        })

        # 插入
        saved_config = engine.db.upsert_agent_config(agent_config)
        self.assertEqual(saved_config.agent_id, "test_db_agent")

        # 查询
        retrieved_config = engine.db.get_agent_config("test_db_agent")
        self.assertIsNotNone(retrieved_config)
        self.assertEqual(retrieved_config.name, "db_test_agent")

        # 更新
        agent_config.instructions = "Updated instructions"
        updated_config = engine.db.upsert_agent_config(agent_config)
        self.assertEqual(updated_config.instructions, "Updated instructions")

        # 列表查询
        config_list = engine.db.get_agent_configs(user_id="test_user")
        self.assertGreaterEqual(len(config_list), 1)

        # 软删除
        success = engine.db.delete_agent_config("test_db_agent")
        self.assertTrue(success)

        deleted_config = engine.db.get_agent_config("test_db_agent")
        self.assertIsNone(deleted_config)  # 软删除后查询不到

    def test_runtime_data_tracking(self):
        """测试运行数据追踪"""
        engine = self.create_chat_engine()

        # 选择智能体
        engine.select_agent_by_name("test_agent")

        # 处理消息
        with patch.object(engine.current_agent, 'run', return_value="Test response"):
            result = engine.process_message("Hello, test message", "text")

        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "Test response")
        self.assertEqual(result["type"], "text")

        # 验证运行数据保存
        runtime_data_list = engine.db.get_runtime_data_list(
            agent_id="test_agent",
            user_id="test_user"
        )

        self.assertGreater(len(runtime_data_list), 0)

        runtime_data = runtime_data_list[0]
        self.assertEqual(runtime_data.agent_id, "test_agent")
        self.assertEqual(runtime_data.user_id, "test_user")
        self.assertEqual(runtime_data.status, "completed")
        self.assertIsNotNone(runtime_data.input_data)
        self.assertIsNotNone(runtime_data.output_data)
        self.assertEqual(runtime_data.input_data["content"], "Hello, test message")
        self.assertEqual(runtime_data.output_data["content"], "Test response")

    def test_agent_selection_and_session_management(self):
        """测试智能体选择和会话管理"""
        engine = self.create_chat_engine()

        # 测试选择智能体
        success = engine.select_agent_by_name("test_agent")
        self.assertTrue(success)
        self.assertEqual(engine.current_agent_name, "test_agent")
        self.assertIsNotNone(engine.current_session_id)

        # 验证会话创建
        sessions = engine.db.get_sessions(agent_id="test_agent", user_id="test_user")
        self.assertGreater(len(sessions), 0)

        session = sessions[0]
        self.assertEqual(session.agent_id, "test_agent")
        self.assertEqual(session.user_id, "test_user")
        self.assertEqual(session.session_data["agent_name"], "test_agent")
        self.assertEqual(session.session_data["status"], "active")

    def test_multi_provider_support(self):
        """测试多供应商支持"""
        engine = self.create_chat_engine()

        # 创建多个不同供应商的智能体
        providers_config = {
            "openai_agent": {
                "name": "openai_agent",
                "type": "text",
                "model": {
                    "provider": "openai",
                    "name": "gpt-4",
                    "kwargs": {"temperature": 0.7}
                },
                "instructions": "OpenAI assistant"
            },
            "anthropic_agent": {
                "name": "anthropic_agent",
                "type": "text",
                "model": {
                    "provider": "anthropic",
                    "name": "claude-3-sonnet",
                    "kwargs": {"temperature": 0.5}
                },
                "instructions": "Anthropic assistant"
            },
            "local_agent": {
                "name": "local_agent",
                "type": "text",
                "model": {
                    "provider": "ollama",
                    "name": "llama2",
                    "kwargs": {"temperature": 0.8}
                },
                "instructions": "Local assistant"
            }
        }

        for agent_name, config in providers_config.items():
            agent = engine.create_agent(agent_name, config)
            self.assertIsNotNone(agent)

            # 验证配置保存到数据库
            agent_configs = engine.db.get_agent_configs(user_id="test_user")
            provider_config = next((ac for ac in agent_configs if ac.name == agent_name), None)
            self.assertIsNotNone(provider_config)
            self.assertEqual(provider_config.model_provider, config["model"]["provider"])
            self.assertEqual(provider_config.model_id, config["model"]["name"])

        # 验证所有配置都被保存
        all_configs = engine.db.get_agent_configs(user_id="test_user")
        self.assertGreaterEqual(len(all_configs), 3)

    def test_configuration_export_import(self):
        """测试配置导出导入功能"""
        engine = self.create_chat_engine()

        # 导出消息
        export_file = os.path.join(self.temp_dir, "exported_messages.json")

        # 添加一些测试消息
        engine.messages = [
            {"role": "user", "content": "Hello", "timestamp": int(time.time())},
            {"role": "assistant", "content": "Hi there!", "timestamp": int(time.time())}
        ]

        result = engine.export_messages(export_file)
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(export_file))

        # 验证导出文件内容
        with open(export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)

        self.assertIn("messages", exported_data)
        self.assertEqual(len(exported_data["messages"]), 2)
        self.assertEqual(exported_data["agent"], "test_agent")

        # 导入消息
        new_engine = self.create_chat_engine()
        import_result = new_engine.import_messages(export_file)
        self.assertTrue(import_result["success"])
        self.assertEqual(import_result["count"], 2)
        self.assertEqual(len(new_engine.messages), 2)

    def test_error_handling(self):
        """测试错误处理"""
        engine = self.create_chat_engine()

        # 测试选择不存在的智能体
        success = engine.select_agent_by_name("nonexistent_agent")
        self.assertFalse(success)

        # 测试更新不存在的智能体
        success = engine.update_agent_model("gpt-4")
        self.assertFalse(success)

        # 测试在不选择智能体的情况下处理消息
        engine.current_agent = None
        result = engine.process_message("Test message")
        self.assertIsNone(result)

        # 测试导入不存在的文件
        result = engine.import_messages("nonexistent_file.json")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_statistics_and_monitoring(self):
        """测试统计和监控功能"""
        engine = self.create_chat_engine()

        # 处理一些消息以生成数据
        engine.select_agent_by_name("test_agent")

        with patch.object(engine.current_agent, 'run', return_value="Test response"):
            engine.process_message("Message 1", "text")
            engine.process_message("Message 2", "text")

        # 获取智能体统计
        stats = engine.get_agent_statistics()
        self.assertIsInstance(stats, dict)

        # 获取数据库统计
        db_stats = engine.get_database_statistics()
        self.assertIsInstance(db_stats, dict)
        self.assertIn("agent_configs", db_stats)
        self.assertIn("runtime_data", db_stats)
        self.assertGreater(db_stats["agent_configs"], 0)
        self.assertGreater(db_stats["runtime_data"], 0)


class TestChatEngineIntegration(unittest.TestCase):
    """ChatEngine 集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "integration_test_config.json")

        # Mock 核心模块
        self.mock_core_modules()

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def mock_core_modules(self):
        """Mock 核心模块"""
        mock_llm_class = Mock()
        mock_llm_instance = Mock()
        mock_llm_instance.model_name = "gpt-3.5-turbo"
        mock_llm_class.return_value = mock_llm_instance

        mock_agent_class = Mock()
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = "Integration test response"
        mock_agent_class.return_value = mock_agent_instance

        mock_memory = Mock()
        mock_voice_engine = Mock()

        patches = [
            patch('chat_engine.LLM_CLASS_DICT', {'openai': mock_llm_class}),
            patch('chat_engine.AGENT_CLASS_DICT', {'text': mock_agent_class}),
            patch('chat_engine.Memory', return_value=mock_memory),
            patch('chat_engine.TextSpeakEngine', return_value=mock_voice_engine),
            patch('chat_engine.log_info'),
            patch('chat_engine.log_error'),
            patch('chat_engine.log_debug')
        ]

        for p in patches:
            p.start()

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 创建引擎
        engine = ChatEngine(
            config_path=self.config_file,
            user_token="integration_test_user"
        )

        # 创建智能体配置
        agent_config = {
            "name": "integration_agent",
            "type": "text",
            "model": {
                "provider": "openai",
                "name": "gpt-4",
                "kwargs": {"temperature": 0.7}
            },
            "instructions": "You are an integration test assistant",
            "tools": [
                {
                    "name": "web_search",
                    "description": "Search the web",
                    "function": {
                        "name": "search",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }

        # 创建智能体
        agent = engine.create_agent("integration_agent", agent_config)
        self.assertIsNotNone(agent)

        # 选择智能体
        success = engine.select_agent_by_name("integration_agent")
        self.assertTrue(success)

        # 处理消息
        result = engine.process_message("Hello, this is an integration test")
        self.assertIsNotNone(result)

        # 验证数据持久化
        agent_configs = engine.db.get_agent_configs(user_id="integration_test_user")
        self.assertGreater(len(agent_configs), 0)

        runtime_data = engine.db.get_runtime_data_list(
            agent_id="integration_agent",
            user_id="integration_test_user"
        )
        self.assertGreater(len(runtime_data), 0)

        # 导出数据
        export_file = os.path.join(self.temp_dir, "integration_export.json")
        result = engine.export_messages(export_file)
        self.assertTrue(result["success"])

        # 清理
        engine.delete_agent("integration_agent")
        self.assertTrue(engine.delete_agent("integration_agent")["success"])


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)