#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatEngine Agent Creation Test

测试ChatEngine的create_new_agent功能
验证Agent对象的创建和配置
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestChatEngineAgentCreation(unittest.TestCase):
    """测试ChatEngine Agent创建功能"""

    def setUp(self):
        """测试设置"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # 延迟导入ChatEngine，避免在模块级别导入错误
        try:
            from chat_engine import ChatEngine
            self.ChatEngine = ChatEngine
        except ImportError as e:
            self.skipTest(f"无法导入ChatEngine: {e}")

    def tearDown(self):
        """测试清理"""
        # 删除临时数据库文件
        try:
            os.unlink(self.db_path)
        except:
            pass

    def test_create_agent_with_minimal_config(self):
        """测试使用最小配置创建Agent"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 最小配置
        agent_config = {
            'agent_id': 'test_agent_001',
            'name': 'Test Agent',
            'model': {
                'name': 'gpt-3.5-turbo',
                'provider': 'openai',
                'kwargs': {}
            }
        }

        agent = engine.create_new_agent('Test Agent', agent_config)

        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'Test Agent')
        self.assertEqual(agent.agent_id, 'test_agent_001')

        print(f"✓ 最小配置创建Agent成功: {agent}")

    def test_create_agent_with_full_config(self):
        """测试使用完整配置创建Agent"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 完整配置
        agent_config = {
            'agent_id': 'test_agent_002',
            'name': 'Advanced Agent',
            'type': 'text',
            'model': {
                'name': 'gpt-4',
                'provider': 'openai',
                'kwargs': {
                    'temperature': 0.8,
                    'max_tokens': 1000
                }
            },
            'instructions': '你是一个高级AI助手，专门提供详细和专业的回答。',
            'tools': ['calculator', 'search'],
            'user_id': 'advanced_user',
            'metadata': {
                'version': '1.0',
                'description': '高级助手'
            }
        }

        agent = engine.create_new_agent('Advanced Agent', agent_config)

        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'Advanced Agent')
        self.assertEqual(agent.agent_id, 'test_agent_002')
        self.assertEqual(agent.user_id, 'advanced_user')
        self.assertIn('详细和专业的回答', agent.instructions)

        print(f"✓ 完整配置创建Agent成功: {agent}")

    def test_create_agent_with_string_model(self):
        """测试使用字符串模型配置创建Agent"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 字符串模型配置
        agent_config = {
            'agent_id': 'test_agent_003',
            'name': 'String Model Agent',
            'model': 'gpt-3.5-turbo',  # 直接使用字符串
            'instructions': '你是一个使用字符串模型配置的Agent。'
        }

        agent = engine.create_new_agent('String Model Agent', agent_config)

        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'String Model Agent')
        self.assertEqual(agent.agent_id, 'test_agent_003')

        print(f"✓ 字符串模型配置创建Agent成功: {agent}")

    def test_create_agent_with_invalid_config(self):
        """测试使用无效配置创建Agent"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 测试空名称
        with self.assertRaises(ValueError):
            engine.create_new_agent('', {'agent_id': 'test'})

        # 测试空配置
        with self.assertRaises(ValueError):
            engine.create_new_agent('Test', None)

        print("✓ 无效配置测试通过")

    def test_create_agent_auto_generate_id(self):
        """测试自动生成Agent ID"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 不提供agent_id，应该自动生成
        agent_config = {
            'name': 'Auto ID Agent',
            'model': {
                'name': 'gpt-3.5-turbo',
                'provider': 'openai'
            }
        }

        agent = engine.create_new_agent('Auto ID Agent', agent_config)

        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.agent_id)
        self.assertTrue(agent.agent_id.startswith('Auto ID Agent_'))

        print(f"✓ 自动生成ID创建Agent成功: {agent.agent_id}")

    def test_mock_agent_creation(self):
        """测试模拟Agent创建（当AGNO框架不可用时）"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 使用一个不存在的模型provider来触发Mock Agent
        agent_config = {
            'agent_id': 'mock_agent_001',
            'name': 'Mock Agent',
            'model': {
                'name': 'test-model',
                'provider': 'nonexistent-provider',
                'kwargs': {}
            }
        }

        agent = engine.create_new_agent('Mock Agent', agent_config)

        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'Mock Agent')
        self.assertEqual(agent.agent_id, 'mock_agent_001')

        # 测试Mock Agent的方法
        if hasattr(agent, 'run'):
            response = agent.run("Hello")
            self.assertIsInstance(response, str)

        print(f"✓ Mock Agent创建成功: {agent}")

    def test_agent_with_tools_and_knowledge(self):
        """测试包含工具和知识库的Agent创建"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        agent_config = {
            'agent_id': 'tool_agent_001',
            'name': 'Tool Agent',
            'model': {
                'name': 'gpt-4',
                'provider': 'openai',
                'kwargs': {}
            },
            'tools': [
                {'name': 'calculator', 'description': '数学计算'},
                {'name': 'web_search', 'description': '网络搜索'}
            ],
            'knowledge': {
                'type': 'vector_db',
                'source': 'documents'
            },
            'memory': {
                'type': 'conversation',
                'max_messages': 100
            },
            'guardrails': [
                {'type': 'content_filter', 'enabled': True}
            ]
        }

        agent = engine.create_new_agent('Tool Agent', agent_config)

        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'Tool Agent')

        print(f"✓ 包含工具和知识库的Agent创建成功: {agent}")

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ChatEngine Agent Creation Test")
    print("=" * 60)

    # 运行测试
    unittest.main(verbosity=2, exit=False)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()